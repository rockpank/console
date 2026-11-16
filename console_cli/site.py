"""預覽站：為任務 worktree 開一個可瀏覽的站點（driver = "command"，通用）。

舊的 cake73 driver（CakePHP＋Apache vhost）已移到 legacy/redmine/python/console_cli/site_cake73.py。

不綁特定框架：由 console.toml 的 `[projects.<別名>.site]` 描述「怎麼準備、怎麼啟動、怎麼停」的指令清單，
console 負責配一個不衝突的連接埠、把 `{port}` 等占位符代進去、記錄在 runtime/sites.json、連線測試。

指令一律是「字串陣列」（不經 shell），占位符：{task} {project} {name} {port} {path} {url}。
  name  ＝ 小寫的 `<專案>-<任務>`，可當 docker compose 專案名稱 / 容器名稱（隔離各任務的容器與資料庫）
  path  ＝ worktree 的主機路徑；指令都在這個目錄下執行
  prepare  啟動前執行（例如 migrate），失敗就中止
  start    啟動站點（要能在背景執行並立刻返回，例如 `docker compose run -d …`），失敗就中止
  stop     停止站點；失敗不中止（可能本來就沒在跑）
  purge    `--drop-db` 時在 stop 之後再執行（例如 `docker compose down -v` 連資料庫 volume 一起清掉）
  env      額外環境變數（值也可用占位符），不放祕密
"""
from __future__ import annotations

import re
import socket
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from . import registry, util
from .config import Config
from .util import ConsoleError, run, say, warn

_PLACEHOLDER = re.compile(r"\{(task|project|name|port|path|url)\}")
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")
_ERROR_MARKERS = re.compile(r"Traceback \(most recent call last\)|Server Error \(500\)|OperationalError|ProgrammingError|Fatal error", re.I)
DEFAULTS = {"port_base": 8100, "port_max": 8199, "url": "http://localhost:{port}/", "health_path": "/",
            "health_timeout": 90, "health_status_max": 399}


def _render(value: str, ctx: dict) -> str:
    return _PLACEHOLDER.sub(lambda m: str(ctx[m.group(1)]), str(value))


def _commands(site: dict, key: str) -> list[list[str]]:
    cmds = site.get(key, [])
    if not isinstance(cmds, list) or not all(isinstance(c, list) and c and all(isinstance(a, str) for a in c) for c in cmds):
        raise ConsoleError(f"[site] {key} 必須是「字串陣列的清單」，例如 [[\"docker\", \"compose\", \"down\"]]（不經 shell）")
    return cmds


def site_name(project: str, task: str) -> str:
    name = re.sub(r"[^a-z0-9_-]", "-", f"{project}-{task}".lower())
    if not _NAME_RE.match(name):
        raise ConsoleError(f"無法由專案 {project}／任務 {task} 產生合法的站點名稱：{name!r}")
    return name


def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def allocate_port(site: dict, registry_data: dict, *, exclude_key: str = "") -> int:
    """port_base～port_max 中第一個「沒被其他站點登記、本機也沒人占用」的埠。"""
    lo, hi = int(site.get("port_base", DEFAULTS["port_base"])), int(site.get("port_max", DEFAULTS["port_max"]))
    taken = {int(e["port"]) for k, e in registry_data.items() if k != exclude_key and e.get("port")}
    for port in range(lo, hi + 1):
        if port not in taken and _port_free(port):
            return port
    raise ConsoleError(f"{lo}–{hi} 的連接埠都用完了（先 console down 掉不用的站點，或在 [site] 調大 port_max）")


def _context(cfg: Config, task: str, alias: str, site: dict, port: int) -> dict:
    ctx = {"task": task, "project": alias, "name": site_name(alias, task), "port": port,
           "path": str(cfg.worktree_path(task, alias)), "url": ""}
    ctx["url"] = _render(site.get("url", DEFAULTS["url"]), ctx)
    return ctx


def _env(site: dict, ctx: dict) -> dict:
    env = site.get("env", {})
    if not isinstance(env, dict):
        raise ConsoleError("[site] env 必須是表格（key = \"value\"）")
    return {str(k): _render(v, ctx) for k, v in env.items()}


def _run_all(cmds: list[list[str]], ctx: dict, env: dict, *, check: bool, label: str) -> None:
    for argv in cmds:
        rendered = [_render(a, ctx) for a in argv]
        say(f"  {label}：{' '.join(rendered)}")
        run(rendered, cwd=ctx["path"], env=env, check=check)


def _note_file(cfg: Config, alias: str, task: str) -> Path:
    return cfg.projects_dir / alias / "tasks" / task / "site.txt"


def _site_conf(cfg: Config, alias: str) -> dict:
    site = cfg.project(alias).get("site")
    if not site:
        raise ConsoleError(f"專案 {alias} 沒有 [site] 設定，只能建立 worktree（見 CLAUDE.md「預覽站」）")
    if site.get("driver") != "command":
        raise ConsoleError(f"不支援的 site driver：{site.get('driver')}（目前只有 command；cake73 已移到 legacy/）")
    return site


def add_site(cfg: Config, task: str, alias: str) -> dict:
    site = _site_conf(cfg, alias)
    path = cfg.worktree_path(task, alias)
    if not path.is_dir() and not util.DRY_RUN:
        raise ConsoleError(f"worktree 不存在：{path}（先執行 console wt add {task} -p {alias}）")
    prepare, start, stop = _commands(site, "prepare"), _commands(site, "start"), _commands(site, "stop")
    if not start:
        raise ConsoleError(f"專案 {alias} 的 [site] 沒有 start 指令")

    data = registry.load(cfg)
    key = registry.key(task, alias)
    previous = data.get(key)
    port = int(previous["port"]) if previous and previous.get("port") else allocate_port(site, data, exclude_key=key)
    ctx = _context(cfg, task, alias, site, port)
    env = _env(site, ctx)

    say(f"[{alias}] 建立預覽站（任務 {task}，埠 {port}）...")
    if previous:
        say(f"  已有站點紀錄：先停掉再重啟（沿用埠 {port}）")
        _run_all(stop, ctx, env, check=False, label="停止")
    _run_all(prepare, ctx, env, check=True, label="準備")
    _run_all(start, ctx, env, check=True, label="啟動")

    entry = {"ticket": task, "task": task, "project": alias, "driver": "command", "name": ctx["name"], "port": port,
             "url": ctx["url"], "worktree": str(path), "started_at": datetime.now().astimezone().isoformat(timespec="seconds")}
    if not util.DRY_RUN:
        data[key] = entry
        registry.save(cfg, data)
        note = _note_file(cfg, alias, task)
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(f"任務 {task} / {alias} 預覽站\n網址：{ctx['url']}\nworktree：{path}\n"
                        f"停止：bin/console site rm {task} -p {alias}（資料庫 volume 保留；要清掉加 --drop-db）\n", encoding="utf-8")
    say(f"[{alias}] 預覽站：{ctx['url']}")
    return entry


def _fetch(url: str, timeout: float = 5.0) -> tuple[int, str]:
    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):  # 302 本身就代表伺服器有回應（例如導向登入頁），不跟隨
            return None

    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(url, timeout=timeout) as resp:
            return resp.status, resp.read(200_000).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(200_000).decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError, TimeoutError):
        return 0, ""


def wait_healthy(url: str, timeout: float, *, fetch=None, sleep=None, clock=None) -> tuple[int, str]:
    import time
    fetch, sleep, clock = fetch or _fetch, sleep or time.sleep, clock or time.monotonic   # 預設值要在呼叫時才取，測試才換得掉 _fetch
    deadline = clock() + timeout
    status, body = fetch(url)
    while status == 0 and clock() < deadline:   # 還沒開始回應（容器啟動中）才重試；有回應就立刻判定
        sleep(2)
        status, body = fetch(url)
    return status, body


def test_site(cfg: Config, task: str, alias: str) -> bool:
    entry = registry.load(cfg).get(registry.key(task, alias))
    if not entry:
        raise ConsoleError(f"沒有 {task}/{alias} 的站點紀錄（先執行 console site add）")
    site = _site_conf(cfg, alias)
    url = entry["url"].rstrip("/") + "/" + str(site.get("health_path", DEFAULTS["health_path"])).lstrip("/")
    status, body = wait_healthy(url, float(site.get("health_timeout", DEFAULTS["health_timeout"])))
    limit = int(site.get("health_status_max", DEFAULTS["health_status_max"]))
    marker = _ERROR_MARKERS.search(body)
    ok = 0 < status <= limit and not marker
    detail = "沒有回應" if status == 0 else f"HTTP {status}" + (f"，頁面含錯誤字樣：{marker.group(0)}" if marker else "")
    say(f"站點測試 {task}/{alias}  {entry['url']}")
    say(f"  [{'OK' if ok else '失敗'}] 預覽站回應：{detail}")
    if status == 0:
        say("  提示：容器可能還在建置或啟動，稍後再執行 console site test；或 docker compose logs 查看。")
    return ok


def remove_site(cfg: Config, task: str, alias: str, *, drop_db: bool = False) -> None:
    data = registry.load(cfg)
    key = registry.key(task, alias)
    entry = data.get(key)
    if not entry:
        say(f"[{alias}] 沒有站點紀錄：{task}/{alias}")
        return
    if entry.get("driver") != "command":
        raise ConsoleError(f"{task}/{alias} 是舊 driver（{entry.get('driver', 'cake73')}）建的站點，已不支援；請用 legacy/redmine/python 的版本處理")
    site = _site_conf(cfg, alias)
    ctx = _context(cfg, task, alias, site, int(entry["port"]))
    env = _env(site, ctx)
    _run_all(_commands(site, "stop"), ctx, env, check=False, label="停止")
    if drop_db:
        _run_all(_commands(site, "purge"), ctx, env, check=False, label="清除")
        say(f"[{alias}] 已停止並清除資料")
    else:
        say(f"[{alias}] 已停止預覽站（資料保留；要清除請加 --drop-db）")
    if not util.DRY_RUN:
        data.pop(key)
        registry.save(cfg, data)
        _note_file(cfg, alias, task).unlink(missing_ok=True)


def _sort_key(entry: dict) -> tuple:
    t = str(entry.get("task") or entry.get("ticket"))
    return (0, int(t), entry["project"]) if t.isdigit() else (1, t, entry["project"])


def list_sites(cfg: Config) -> None:
    data = registry.load(cfg)
    if not data:
        say("（目前沒有預覽站）")
        return
    for entry in sorted(data.values(), key=_sort_key):
        legacy = entry.get("driver") != "command"
        extra = "舊 driver（cake73，已不支援）" if legacy else f"埠 {entry['port']}"
        say(f"{entry['ticket']:<8}{entry['project']:<14}{entry['url']}  {extra}")
