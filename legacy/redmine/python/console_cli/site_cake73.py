"""站點管理（driver: cake73；command 通用 driver 在 site_cmd.py）：為 worktree 建立可連線測試的 Apache vhost 與資料庫。

流程：播種被 git 忽略的設定與 vendor → 複製 saas 庫並改寫設定 → 產生 vhost → configtest／graceful → 連線測試。
vhost 檔寫在 runtime/apache-sites/，由 apache_test 容器以 IncludeOptional 載入。
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import envfile, login, registry, site_cmd, util
from .config import Config
from .util import ConsoleError, run, say, warn

_SAAS_RE = re.compile(r"(var\s+\$saas\s*=\s*array\(.*?'database'\s*=>\s*')([^']+)(')", re.S)
_DB_NAME_RE = re.compile(r"^[A-Za-z0-9_]{1,64}$")
_ERROR_MARKERS = re.compile(r"Fatal error|Parse error|Call to undefined|SQLSTATE|Missing Database Table", re.I)


# ----------------------------------------------------------------- docker / mysql

def _docker(cfg: Config, *args, check=True, mutating=True, input=None):
    return run(["docker", *args], check=check, mutating=mutating, input=input)


def _mounts(container: str) -> set[str]:
    out = run(["docker", "inspect", "-f", "{{json .Mounts}}", container], mutating=False).stdout
    return {m["Destination"] for m in json.loads(out)}


def check_mounts(cfg: Config) -> list[str]:
    """回傳缺少的掛載說明；空 list 代表齊全。"""
    d = cfg.docker
    problems = []
    for container, needed in (
        (d["apache_container"], [d["worktree_mount"], d["sites_mount"]]),
        (d["php_container"], [d["worktree_mount"]]),
    ):
        try:
            have = _mounts(container)
        except ConsoleError as exc:
            problems.append(f"容器 {container} 無法檢查：{str(exc).splitlines()[0]}")
            continue
        problems += [f"容器 {container} 缺少掛載 {n}" for n in needed if n not in have]
    return problems


def _mysql(cfg: Config, sql: str, *, mutating: bool = True) -> str:
    script = 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql -uroot -N -e "$1"'
    return _docker(cfg, "exec", cfg.docker["mysql_container"], "sh", "-c", script, "_", sql, mutating=mutating).stdout


def _check_db_name(name: str) -> str:
    if not _DB_NAME_RE.match(name):
        raise ConsoleError(f"資料庫名稱不合法：{name!r}")
    return name


def _db_exists(cfg: Config, name: str) -> bool:
    _check_db_name(name)
    out = _mysql(cfg, f"select schema_name from information_schema.schemata where schema_name='{name}'", mutating=False)
    return name in out.split()


def _clone_db(cfg: Config, src: str, dst: str) -> None:
    _check_db_name(src), _check_db_name(dst)
    _mysql(cfg, f"create database `{dst}` character set utf8mb4 collate utf8mb4_unicode_ci")
    script = (
        'export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"; '
        f"mysqldump -uroot --single-transaction --routines --triggers {src} | mysql -uroot {dst}"
    )
    try:
        _docker(cfg, "exec", cfg.docker["mysql_container"], "bash", "-o", "pipefail", "-c", script)
    except ConsoleError:
        _mysql(cfg, f"drop database if exists `{dst}`")  # 只清掉自己剛建的空庫
        raise


# ----------------------------------------------------------------- seed / config

def read_saas_db(config_text: str) -> str:
    match = _SAAS_RE.search(config_text)
    if not match:
        raise ConsoleError("db_config 內找不到 $saas 的 'database' 設定")
    return match.group(2)


def patch_saas_db(config_text: str, new_name: str) -> str:
    return _SAAS_RE.sub(lambda m: f"{m.group(1)}{new_name}{m.group(3)}", config_text, count=1)


def _seed(site: dict, dest: Path) -> None:
    seed_root = Path(site["seed_from"])
    if not seed_root.is_dir():
        raise ConsoleError(f"seed_from 不存在：{seed_root}")
    copied = 0
    for rel in site.get("seed_ignored", []):
        out = run(["git", "-C", seed_root, "ls-files", "--others", "--ignored", "--exclude-standard", "-z", "--", rel],
                  mutating=False).stdout
        for name in filter(None, out.split("\0")):
            if ".bak" in Path(name).name:
                continue
            src, dst = seed_root / name, dest / name
            if dst.exists():
                continue
            copied += 1
            if not util.DRY_RUN:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
    for rel in site.get("seed_dirs", []):
        src, dst = seed_root / rel, dest / rel
        if dst.exists() or not src.is_dir():
            continue
        say(f"  複製目錄 {rel}")
        if not util.DRY_RUN:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst, symlinks=True)
    for rel in site.get("tmp_dirs", []):
        target = dest / rel
        if not util.DRY_RUN:
            target.mkdir(parents=True, exist_ok=True)
            for p in [target, *[q for q in target.rglob("*") if q.is_dir()]]:
                try:
                    p.chmod(0o777)
                except PermissionError:
                    warn(f"無法 chmod 0777：{p}")
    say(f"  播種：複製 {copied} 個被忽略的設定檔")


# ----------------------------------------------------------------- site add / rm / test

def _site_note(cfg: Config, ticket: str, alias: str) -> Path:
    """給專案端 session 讀的站點資訊：worktrees/<工單>/_ticket/site-<別名>.txt"""
    return cfg.ticket_dir(ticket) / "_ticket" / f"site-{alias}.txt"


def _reload_apache(cfg: Config) -> None:
    container = cfg.docker["apache_container"]
    test = _docker(cfg, "exec", container, "apachectl", "configtest", check=False, mutating=False)
    output = (test.stdout + test.stderr).strip()
    if test.returncode != 0 or "Syntax OK" not in output:
        raise ConsoleError(f"Apache configtest 失敗，未重新載入：\n{output}")
    _docker(cfg, "exec", container, "apachectl", "graceful")


def add_site(cfg: Config, ticket: str, alias: str) -> dict:
    proj = cfg.project(alias)
    site = proj.get("site")
    if not site:
        raise ConsoleError(f"專案 {alias} 沒有 [site] 設定，只能建立 worktree")
    driver = site.get("driver")
    if driver == "command":
        return site_cmd.add_site(cfg, ticket, alias)
    if driver != "cake73":
        raise ConsoleError(f"不支援的 site driver：{driver}（有 cake73、command）")
    if not ticket.isdigit():
        raise ConsoleError("cake73 driver 只支援數字工單號（網址與資料庫名稱由它產生）")
    path = cfg.worktree_path(ticket, alias)
    if not path.exists() and not util.DRY_RUN:
        raise ConsoleError(f"worktree 不存在：{path}（先執行 console wt add {ticket} -p {alias}）")

    problems = check_mounts(cfg)
    if problems:
        message = "docker 掛載尚未就緒：\n  " + "\n  ".join(problems) + "\n請見 README「docker 一次性設定」。"
        if util.DRY_RUN:
            warn(message)
        else:
            raise ConsoleError(message)

    say(f"[{alias}] 建立站點 ...")
    _seed(site, path)

    # 資料庫：複製 seed 的 saas 庫；主庫沿用
    seed_cfg = Path(site["seed_from"]) / site["db_config"]
    src_db = read_saas_db(seed_cfg.read_text(encoding="utf-8"))
    new_db = _check_db_name(site["saas_db_pattern"].format(ticket=ticket))
    db_created = False
    if _db_exists(cfg, new_db):
        say(f"  資料庫 {new_db} 已存在，沿用（不重新複製）")
    else:
        say(f"  複製資料庫 {src_db} → {new_db}")
        _clone_db(cfg, src_db, new_db)
        db_created = True
    dest_cfg = path / site["db_config"]
    if not util.DRY_RUN:
        text = dest_cfg.read_text(encoding="utf-8")
        if read_saas_db(text) != new_db:
            dest_cfg.write_text(patch_saas_db(text, new_db), encoding="utf-8")
        if read_saas_db(dest_cfg.read_text(encoding="utf-8")) != new_db:
            raise ConsoleError(f"改寫 {dest_cfg} 失敗")
    say(f"  已將 {site['db_config']} 的 saas 庫指向 {new_db}")

    # vhost
    host = cfg.site_host(ticket)
    docroot = f"{cfg.docker['worktree_mount']}/{ticket}/{alias}"
    template = cfg.resolve(site["vhost_template"]).read_text(encoding="utf-8")
    values = {
        "ticket": ticket, "project": alias, "host": host, "docroot": docroot,
        "ssl_cert": cfg.sites["ssl_cert"], "ssl_key": cfg.sites["ssl_key"], "php_fpm": site["php_fpm"],
    }
    for k, v in values.items():
        template = template.replace("{{" + k + "}}", v)
    vhost_file = cfg.sites_dir / f"r{ticket}-{alias}.conf"
    if not util.DRY_RUN:
        cfg.sites_dir.mkdir(parents=True, exist_ok=True)
        vhost_file.write_text(template, encoding="utf-8")
    say(f"  vhost：{vhost_file}")
    try:
        _reload_apache(cfg)
    except ConsoleError:
        if not util.DRY_RUN:
            vhost_file.unlink(missing_ok=True)
        raise

    entry = {
        "ticket": ticket, "project": alias, "host": host, "url": cfg.site_url(ticket),
        "saas_db": new_db, "db_created": db_created, "vhost_file": str(vhost_file),
    }
    if not util.DRY_RUN:
        data = registry.load(cfg)
        previous = data.get(registry.key(ticket, alias), {})
        entry["db_created"] = db_created or previous.get("db_created", False)
        data[registry.key(ticket, alias)] = entry
        registry.save(cfg, data)
        note = _site_note(cfg, ticket, alias)
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(
            f"工單 #{ticket} / {alias} 測試站點\n"
            f"網址：{entry['url']}\n"
            f"hosts（瀏覽器用，Windows）：127.0.0.1 {host}\n"
            f"saas 資料庫：{new_db}（主庫沿用 seed 設定）\n"
            f"worktree：{path}\n",
            encoding="utf-8",
        )
    say(f"[{alias}] 站點：{entry['url']}")
    say(f"  瀏覽器連線需要 hosts 一行：127.0.0.1 {host}（Windows：C:\\Windows\\System32\\drivers\\etc\\hosts）")
    return entry


def test_site(cfg: Config, ticket: str, alias: str) -> bool:
    entry = registry.load(cfg).get(registry.key(ticket, alias))
    if not entry:
        raise ConsoleError(f"沒有 {ticket}/{alias} 的站點紀錄（先執行 console site add）")
    if entry.get("driver") == "command":
        return site_cmd.test_site(cfg, ticket, alias)
    d, host, port = cfg.docker, entry["host"], cfg.sites["https_port"]
    results: list[tuple[str, bool | None, str]] = []

    docroot = f"{d['worktree_mount']}/{ticket}/{alias}/index.php"
    r = run(["docker", "exec", d["php_container"], "test", "-f", docroot], check=False, mutating=False)
    results.append(("php 容器看得到程式碼", r.returncode == 0, docroot))

    r = run(["docker", "exec", d["apache_container"], "test", "-f",
             f"{d['sites_mount']}/{Path(entry['vhost_file']).name}"], check=False, mutating=False)
    results.append(("apache 已載入 vhost 檔", r.returncode == 0, Path(entry["vhost_file"]).name))

    db = entry["saas_db"]
    try:
        count = _mysql(cfg, f"select count(*) from information_schema.tables where table_schema='{db}'",
                       mutating=False).strip()
        results.append(("saas 資料庫可連線", count.isdigit() and int(count) > 0, f"{db}（{count} 張表）"))
    except ConsoleError as exc:
        results.append(("saas 資料庫可連線", False, str(exc).splitlines()[0]))

    with tempfile.NamedTemporaryFile() as body:
        curl = subprocess.run(
            ["curl", "-sk", "-L", "--max-redirs", "3", "-m", "40", "--resolve", f"{host}:{port}:127.0.0.1",
             "-o", body.name, "-w", "%{http_code} %{url_effective}",
             f"https://{host}:{port}{cfg.sites.get('test_path', '/')}"],
            capture_output=True, text=True,
        )
        status = curl.stdout.strip().split(" ", 1)[0] if curl.stdout else "000"
        text = Path(body.name).read_text(encoding="utf-8", errors="replace")[:200_000]
    marker = _ERROR_MARKERS.search(text)
    results.append(("HTTPS 回應", status == "200" and not marker,
                    f"HTTP {status}" + (f"，頁面含錯誤字樣：{marker.group(0)}" if marker else "")))

    login_cfg = cfg.project(alias)["site"].get("login")
    if login_cfg:
        results.append(_login_result(cfg, ticket, alias, login_cfg, host, port))

    ok = all(passed is not False for _, passed, _ in results)  # None = 略過，不算失敗
    say(f"站點測試 {ticket}/{alias}  {entry['url']}")
    for name, passed, detail in results:
        label = "略過" if passed is None else ("OK" if passed else "失敗")
        say(f"  [{label}] {name}：{detail}")
    return ok


def _login_result(cfg: Config, ticket: str, alias: str, login_cfg: dict, host: str, port: int):
    """用 worktree 內的測試帳號環境檔登入一次。帳密只在記憶體，不印出；沒提供就略過。"""
    name = "測試帳號登入"
    creds_path = cfg.worktree_path(ticket, alias) / login_cfg["creds_file"]
    try:
        values = envfile.parse(creds_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return (name, None, f"未提供（worktree 內沒有 {login_cfg['creds_file']}；填好 config/env 後執行 console env sync {ticket}）")
    user, password = values.get(login_cfg["username_key"], ""), values.get(login_cfg["password_key"], "")
    if not user or not password:
        return (name, None, f"未提供（{login_cfg['username_key']}／{login_cfg['password_key']} 未填）")
    ok, detail = login.check_login(
        host, port, cfg.sites.get("test_path", "/"), user, password,
        login_path=login_cfg.get("login_path", "Accounts/login"),
        mfa_path=login_cfg.get("mfa_check_path", "Accounts/checkMfa"),
    )
    return (name, ok, detail)


def remove_site(cfg: Config, ticket: str, alias: str, *, drop_db: bool = False) -> None:
    data = registry.load(cfg)
    entry = data.get(registry.key(ticket, alias))
    if not entry:
        say(f"[{alias}] 沒有站點紀錄：{ticket}/{alias}")
        return
    if entry.get("driver") == "command":
        return site_cmd.remove_site(cfg, ticket, alias, drop_db=drop_db)
    vhost = Path(entry["vhost_file"])
    if not util.DRY_RUN:
        vhost.unlink(missing_ok=True)
    _reload_apache(cfg)
    say(f"[{alias}] 已移除 vhost 並重新載入 Apache")
    if drop_db:
        if entry.get("db_created"):
            _mysql(cfg, f"drop database if exists `{_check_db_name(entry['saas_db'])}`")
            say(f"[{alias}] 已刪除資料庫 {entry['saas_db']}")
        else:
            warn(f"資料庫 {entry['saas_db']} 不是 console 建立的，未刪除")
    else:
        say(f"[{alias}] 資料庫 {entry['saas_db']} 保留（要刪請加 --drop-db）")
    if not util.DRY_RUN:
        data.pop(registry.key(ticket, alias))
        registry.save(cfg, data)
        _site_note(cfg, ticket, alias).unlink(missing_ok=True)


def list_sites(cfg: Config) -> None:
    data = registry.load(cfg)
    if not data:
        say("（目前沒有站點）")
        return
    for entry in sorted(data.values(), key=site_cmd.sort_key):
        extra = f"埠 {entry['port']}" if entry.get("driver") == "command" else f"saas={entry['saas_db']}"
        say(f"{entry['ticket']:<8}{entry['project']:<14}{entry['url']}  {extra}")
