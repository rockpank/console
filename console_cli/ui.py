"""本機視覺化介面：`bin/console ui`。

只綁 127.0.0.1，用標準庫的 http.server。看板的單位是「專案＋任務」：
  - 任務清單來自 projects/<專案>/backlog.md 的「狀態」欄，加上 projects/<專案>/tasks/<任務>/ 的交接檔
    與 worktrees/<任務>/<專案>/ 是否存在（進度的單一事實來源仍是 backlog.md／status.md，這裡只讀）；
  - 擱置與排序存在 runtime/queue.json（介面自己的狀態，不碰專案文件）；
  - 建立對話只在背景開一個 tmux session（dev-<任務>），裡面啟動 claude 並帶入 /dispatch 指令，不會開任何視窗；
    要互動時按卡片的「開指令視窗」，才用 wt.exe 開一個終端機分頁接上去；
  - 卡片可以「關閉對話」（結束 tmux session）或「移除」（關閉對話並從看板隱藏，不刪任何檔案）。
介面也不會自動開瀏覽器（WSL 下用 explorer.exe 開網址會跳出檔案總管），只印網址。

安全：Host 檢查（擋 DNS rebinding）、每次啟動隨機 token（擋跨站請求）、POST 一律要 JSON＋token；
要執行的指令只由伺服器端依白名單組出（專案別名須是已有工作區的專案、任務代號須通過 parse_task 並存在於
backlog 或已有交接檔），自由文字只有「裁示」與「新需求」，會先過遮蔽、壓成單行、限長。用量監控（/api/usage，
`usage.py`）只讀對話紀錄裡的 usage 數字與 statusline 快照；額度達門檻時 launch／launch_batch 會拒絕高耗 token 的
動作（HEAVY_ACTIONS），只有 POST /api/guard 能暫時解除。不讀 config/env、config/console.env、
config/mask_terms.txt 的內容（遮蔽詞檔由 mask 模組載入，這裡不碰）。
"""
from __future__ import annotations

import json
import os
import re
import secrets
import shlex
import shutil
import subprocess
import tempfile
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import mask, registry, usage, util
from .config import ROOT, Config
from .util import ConsoleError, parse_task, say

PAGE = ROOT / "templates" / "ui" / "dashboard.html"
DEFAULT_PORT = 8765
SESSION_PREFIX = "dev-"
MAIN_FLOW = ["規劃中", "開發中", "資安", "QA", "完成"]        # backlog「狀態」欄的順序（待辦、擱置不在流程內）
ACTIVE_STATUS = {"規劃中", "開發中", "資安", "QA"}            # backlog 標了這些就算進行中，即使還沒有交接檔
STALE_AFTER_SECONDS = 24 * 3600
_REASON_MAX = 100
_RULING_MAX = 300
_REQUEST_MAX = 300
_BODY_MAX = 4096
_ORDER_MAX = 200
_BATCH_MAX = 10          # 一次最多派幾個 backlog 項目
_BACKLOG_MAX = 300       # 待辦清單最多顯示幾列
_SITE_URL = re.compile(r"http://(?:localhost|127\.0\.0\.1):\d{2,5}(?:/[A-Za-z0-9._~\-/]*)?")
_BATCH_SESSION = re.compile(r"^" + SESSION_PREFIX + r"[A-Za-z0-9_-]+-b\d{6}$")


# ---------------------------------------------------------------- 檔案讀取

def _frontmatter(path: Path, keys: tuple[str, ...]) -> dict[str, str]:
    """只取指定鍵的短值（檔頭 --- 之間的 key: value），其餘一律不讀進來。"""
    try:
        lines = path.read_text(encoding="utf-8")[:6000].splitlines()
    except OSError:
        return {}
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, str] = {}
    for line in lines[1:60]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if sep and key.strip() in keys:
            out[key.strip()] = value.strip()[:40]
    return out


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts).astimezone().isoformat(timespec="seconds")


def projects_with_workspace(cfg: Config) -> list[str]:
    """有 projects/<別名>/profile.md 的專案（_template 之類底線開頭的不算）。"""
    root = cfg.projects_dir
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir()
                  if p.is_dir() and not p.name.startswith(("_", ".")) and (p / "profile.md").is_file())


def _task_dir(cfg: Config, project: str, task: str) -> Path:
    return cfg.projects_dir / project / "tasks" / task


def _status_word(cell: str) -> str:
    """狀態欄可能寫成「待辦（待決：Q3）」或加粗；只取第一個詞。"""
    m = re.match(r"[^\s（(：:,，;；*`]+", cell.replace("*", "").replace("`", "").strip())
    return m.group(0) if m else ""


def parse_backlog(path: Path) -> dict[str, dict]:
    """讀 backlog.md 第一張含「ID」與「狀態」欄的表，回傳 {任務代號: 列}。讀不到或格式不符就回空表。"""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    rows: dict[str, dict] = {}
    cols: dict[str, int] | None = None
    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            if rows:
                break          # 表結束
            cols = None        # 還沒讀到任何列：這張表不是要找的，繼續找下一張
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if cols is None:
            if "ID" in cells and "狀態" in cells:
                cols = {name: i for i, name in enumerate(cells)}
            continue
        if set("".join(cells)) <= set("-: "):
            continue           # 分隔列
        try:
            code = cells[cols["ID"]].replace("*", "").replace("`", "").strip()
            code = parse_task(code)
        except (ConsoleError, IndexError):
            continue
        get = lambda name: cells[cols[name]] if name in cols and cols[name] < len(cells) else ""  # noqa: E731
        raw_status = get("狀態")
        rows[code] = {
            "id": code, "kind": get("類型")[:20], "title": get("標題")[:120], "route": get("路線")[:30],
            "cost": get("成本")[:12], "deps": get("依賴")[:80], "status": _status_word(raw_status),
            "undecided": "待決" in raw_status or "待決" in get("依賴"),
        }
    return rows


def _queue_file(cfg: Config) -> Path:
    return cfg.runtime_dir / "queue.json"


def load_queue(cfg: Config) -> dict:
    try:
        data = json.loads(_queue_file(cfg).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}

    def ok(code) -> bool:
        try:
            parse_task(str(code))
            return True
        except ConsoleError:
            return False

    tasks = data.get("tasks") if isinstance(data.get("tasks"), dict) else {}
    tasks = {str(k): v for k, v in tasks.items() if ok(k) and isinstance(v, dict)}
    order = [str(t) for t in data.get("order", []) if ok(t)] if isinstance(data.get("order"), list) else []
    removed = data.get("removed") if isinstance(data.get("removed"), dict) else {}
    removed = {str(k): v for k, v in removed.items() if ok(k) and isinstance(v, dict)}
    return {"order": order, "tasks": tasks, "removed": removed}


def _save_queue(cfg: Config, queue: dict) -> None:
    path = _queue_file(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".queue-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(queue, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    os.chmod(path, 0o600)


def _clean_text(cfg: Config, text: str, limit: int) -> str:
    mask.load_terms(cfg.mask_terms_file)
    return " ".join(mask.mask_text(str(text)).split())[:limit]


def set_hold(cfg: Config, task: str, hold: bool, reason: str = "") -> dict:
    task = parse_task(task)
    queue = load_queue(cfg)
    if hold:
        queue["tasks"][task] = {
            "hold": True,
            "reason": _clean_text(cfg, reason, _REASON_MAX),
            "since": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
    else:
        queue["tasks"].pop(task, None)
    _save_queue(cfg, queue)
    return queue


def _is_removed(queue: dict, task: str, updated: str) -> bool:
    """已從看板移除，且之後交接檔沒再更新過。一更新（有人重新派工）就自動回到看板。"""
    mark = queue["removed"].get(task)
    return mark is not None and mark.get("updated") == updated


def _unremove(cfg: Config, task: str) -> None:
    queue = load_queue(cfg)
    if queue["removed"].pop(task, None) is not None:
        _save_queue(cfg, queue)


def _updated(cfg: Config, project: str, task: str) -> str:
    """交接檔中最新的修改時間（ISO）；沒有任何交接檔就回空字串。"""
    d = _task_dir(cfg, project, task)
    try:
        times = [p.stat().st_mtime for p in d.glob("*") if p.is_file()]
    except OSError:
        times = []
    return _iso(max(times)) if times else ""


def close_sessions(*, task: str = "", session: str = "") -> list[str]:
    """結束 tmux 對話：給任務就關它的對話；給名稱就只關那一個（必須是現存的 dev- 對話）。"""
    live = list_sessions()
    if task:
        name = session_name(task)
        targets = [name] if name in live else []
    elif session in live:
        targets = [session]
    else:
        raise ConsoleError("找不到這個對話（可能已經關掉了）")
    for name in targets:
        util.run(["tmux", "kill-session", "-t", f"={name}"], check=False, timeout=5)
    return targets


def remove_task(cfg: Config, project: str, task: str) -> dict:
    """關閉對話並從看板隱藏。不動 backlog、worktree、分支與交接檔（要刪請用 bin/console wt rm）。"""
    project, task = _check_project(cfg, project), parse_task(task)
    closed = close_sessions(task=task)
    queue = load_queue(cfg)
    queue["removed"][task] = {"at": datetime.now().astimezone().isoformat(timespec="seconds"),
                              "updated": _updated(cfg, project, task)}
    queue["tasks"].pop(task, None)  # 擱置紀錄一併清掉
    queue["order"] = [t for t in queue["order"] if t != task]
    _save_queue(cfg, queue)
    return {"closed": closed, "hidden": True}


def set_order(cfg: Config, order: list) -> dict:
    seen: list[str] = []
    for item in order[:_ORDER_MAX]:
        task = parse_task(str(item))
        if task not in seen:
            seen.append(task)
    queue = load_queue(cfg)
    queue["order"] = seen
    _save_queue(cfg, queue)
    return queue


# ---------------------------------------------------------------- 看板資料

def _pipeline(stage: str, base: str | None, escalated: bool) -> list[dict]:
    """主流程各階段的狀態：done／current／blocked（已升級停在這）／todo。"""
    if stage == "完成":
        return [{"stage": s, "state": "done"} for s in MAIN_FLOW]
    if stage not in MAIN_FLOW:
        return [{"stage": s, "state": "todo"} for s in MAIN_FLOW]
    anchor = base if escalated and base in MAIN_FLOW else stage
    pos, state = MAIN_FLOW.index(anchor), "blocked" if escalated else "current"
    return [{"stage": s, "state": "done" if i < pos else state if i == pos else "todo"}
            for i, s in enumerate(MAIN_FLOW)]


def _report_role(td: Path, key: str, label: str, pattern: str, ok_words: set[str]) -> dict:
    reports = sorted(td.glob(pattern))
    if not reports:
        return {"key": key, "label": label, "state": "todo", "detail": ""}
    fm = _frontmatter(reports[-1], ("verdict", "status"))
    verdict = fm.get("verdict") or fm.get("status") or ""
    bad = bool(verdict) and verdict not in ok_words
    return {"key": key, "label": label, "state": "warn" if bad else "done",
            "detail": f"{len(reports)}輪・{verdict}" if verdict else f"{len(reports)}份"}


def _roles(cfg: Config, project: str, task: str) -> list[dict]:
    td = _task_dir(cfg, project, task)
    roles = [{"key": "worktree", "label": "worktree",
              "state": "done" if cfg.worktree_path(task, project).is_dir() else "todo", "detail": ""}]
    impl = td / "impl-notes.md"
    if impl.exists():
        fm = _frontmatter(impl, ("status", "tests"))
        roles.append({"key": "engineer", "label": "工程師", "state": "blocked" if fm.get("status") == "blocked" else "done",
                      "detail": f"測試{fm['tests']}" if fm.get("tests") else ""})
    else:
        roles.append({"key": "engineer", "label": "工程師", "state": "todo", "detail": ""})
    if any(td.glob("security-*.md")):  # 資安只在任務標「資安加派」時才有；平常不顯示，避免永遠停在待辦
        roles.append(_report_role(td, "security", "資安審查（加派）", "security-*.md", {"通過", "pass", "ok"}))
    roles.append(_report_role(td, "qa", "QA 驗證", "qa-*.md", {"通過", "pass", "ok"}))
    return roles


def _infer_stage(td: Path, has_worktree: bool) -> str:
    """沒有 backlog 狀態可看時，由交接檔推斷階段。"""
    if any(td.glob("qa-*.md")):
        return "QA"
    if any(td.glob("security-*.md")):
        return "資安"
    if (td / "impl-notes.md").exists():
        return "開發中"
    return "規劃中"


def _stage_of(row: dict | None, td: Path, has_worktree: bool) -> str:
    inferred = _infer_stage(td, has_worktree)
    status = (row or {}).get("status", "")
    if status == "完成":
        return "完成"
    if status in ACTIVE_STATUS:      # backlog 與交接檔取較後面的階段（PM 更新可能落後）
        return max(status, inferred, key=MAIN_FLOW.index)
    return inferred


def _actions(stage: str, hold: bool, escalation: dict | None) -> list[dict]:
    """依狀態決定主要按鈕；指令本身由伺服器在 launch 時組，這裡只給 id 與標籤。"""
    acts: list[dict] = []
    if stage == "完成":
        pass
    elif escalation is not None:
        quota = escalation.get("kind") == "額度保護"
        acts.append({"id": "resume", "label": "額度已重置，繼續" if quota else "送出裁示並繼續", "primary": True,
                     "ruling": not quota})
    else:
        acts.append({"id": "resume", "label": "接續處理", "primary": True})
    acts.append({"id": "chat", "label": "只建對話"})
    if hold:
        acts = [a for a in acts if a["id"] == "chat"]  # 擱置中不主動推進
    return acts


def _escalation(cfg: Config, project: str, task: str) -> dict | None:
    path = _task_dir(cfg, project, task) / "escalation.md"
    if not path.exists():
        return None
    fm = _frontmatter(path, ("kind", "resume_at", "resolved"))
    return None if fm.get("resolved", "").lower() == "true" else fm


def _site_url(cfg: Config, project: str, task: str) -> str:
    """console 為這個任務開的預覽站網址（runtime/sites.json）。只接受本機 http 網址，其他一律當沒有。"""
    try:
        url = str(registry.load(cfg).get(registry.key(task, project), {}).get("url", ""))
    except (OSError, ValueError, AttributeError):
        return ""
    return url if _SITE_URL.fullmatch(url) else ""


def _task_view(cfg: Config, project: str, task: str, row: dict | None, queue: dict,
               sessions: set[str], now: datetime) -> dict:
    td = _task_dir(cfg, project, task)
    has_wt = cfg.worktree_path(task, project).is_dir()
    stage = _stage_of(row, td, has_wt)
    esc = _escalation(cfg, project, task)
    updated = _updated(cfg, project, task)
    try:
        stale = stage != "完成" and bool(updated) and (now - datetime.fromisoformat(updated)).total_seconds() > STALE_AFTER_SECONDS
    except ValueError:
        stale = False

    hold_info = queue["tasks"].get(task) or {}
    hold = bool(hold_info.get("hold"))
    badges = []
    if esc is not None:
        badges.append({"text": "額度保護暫停" if esc.get("kind") == "額度保護" else "需你裁示",
                       "kind": "warn" if esc.get("kind") == "額度保護" else "alert"})
    if stage == "完成":
        badges.append({"text": "待你驗收合併" if has_wt else "已完成", "kind": "ok"})
    if (row or {}).get("undecided"):
        badges.append({"text": "有待決事項", "kind": "warn"})
    if stale:
        badges.append({"text": "久未動", "kind": "muted"})
    if row is None:
        badges.append({"text": "不在 backlog", "kind": "muted"})

    group = "hold" if hold else "done" if stage == "完成" else "need" if esc is not None else "run"
    files = []
    try:
        files = sorted(({"name": p.name, "at": _iso(p.stat().st_mtime)} for p in td.glob("*") if p.is_file()),
                       key=lambda f: f["at"], reverse=True)[:12]
    except OSError:
        pass
    return {
        "task": task,
        "project": project,
        "title": (row or {}).get("title", ""),
        "kind": (row or {}).get("kind", ""),
        "route": (row or {}).get("route", ""),
        "stage": stage,
        "updated": updated,
        "files": files,
        "site_url": _site_url(cfg, project, task),
        "pipeline": _pipeline(stage, (esc or {}).get("resume_at"), esc is not None),
        "roles": _roles(cfg, project, task),
        "badges": badges,
        "group": group,
        "hold": hold,
        "hold_reason": hold_info.get("reason", ""),
        "hold_since": hold_info.get("since", ""),
        "session": session_name(task) in sessions,
        "actions": _actions(stage, hold, esc),
    }


def _task_codes(cfg: Config, project: str, backlog: dict[str, dict]) -> list[str]:
    """進行中的任務代號：backlog 標了進行中階段，或已有交接檔／worktree。"""
    codes = {c for c, r in backlog.items() if r["status"] in ACTIVE_STATUS}
    tasks_root = cfg.projects_dir / project / "tasks"
    if tasks_root.is_dir():
        codes |= {p.name for p in tasks_root.iterdir() if p.is_dir()}
    if cfg.worktree_root.is_dir():
        codes |= {p.parent.name for p in cfg.worktree_root.glob(f"*/{project}") if p.is_dir()}
    out = []
    for c in sorted(codes):
        try:
            out.append(parse_task(c))
        except ConsoleError:
            continue   # 資料夾名稱不是合法任務代號（例如隱藏資料夾）
    return out


def collect(cfg: Config, sessions: set[str] | None = None, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now().astimezone()
    sessions = sessions or set()
    queue = load_queue(cfg)
    views = []
    for project in projects_with_workspace(cfg):
        backlog = parse_backlog(cfg.projects_dir / project / "backlog.md")
        for task in _task_codes(cfg, project, backlog):
            if _is_removed(queue, task, _updated(cfg, project, task)):
                continue
            views.append(_task_view(cfg, project, task, backlog.get(task), queue, sessions, now))
    order = {t: i for i, t in enumerate(queue["order"])}
    rank = {"run": 0, "need": 0, "done": 1, "hold": 2}
    views.sort(key=lambda v: (rank[v["group"]], order.get(v["task"], len(order)),
                              0 if v["group"] == "need" else 1, v["project"], v["task"]))
    return views


def backlog_view(cfg: Config, active: set[tuple[str, str]]) -> list[dict]:
    """每個專案的 backlog 概況與「待辦」清單，給介面勾選後派工。active＝已在看板上的 (專案, 任務)。"""
    out = []
    for project in projects_with_workspace(cfg):
        rows = parse_backlog(cfg.projects_dir / project / "backlog.md")
        counts: dict[str, int] = {}
        for r in rows.values():
            counts[r["status"] or "未標"] = counts.get(r["status"] or "未標", 0) + 1
        items = [{**r, "known": (project, r["id"]) in active} for r in rows.values() if r["status"] == "待辦"]
        out.append({"project": project, "counts": counts, "total": len(rows), "items": items[:_BACKLOG_MAX]})
    return out


# ---------------------------------------------------------------- 開對話（tmux + wt.exe）

def session_name(task: str) -> str:
    return f"{SESSION_PREFIX}{parse_task(task)}"


def attach_command(name: str) -> str:
    """給人貼進終端機的接上指令。`=名稱` 要加引號：zsh 會把未加引號、字首為 `=` 的字當 equals expansion。"""
    return f"tmux attach-session -t '={name}'"


def tools_available() -> dict[str, bool]:
    return {name: shutil.which(exe) is not None for name, exe in
            (("tmux", "tmux"), ("wt", "wt.exe"), ("claude", "claude"))}


def list_sessions() -> set[str]:
    if not shutil.which("tmux"):
        return set()
    result = util.run(["tmux", "list-sessions", "-F", "#{session_name}"], check=False, mutating=False, timeout=5)
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip().startswith(SESSION_PREFIX)}


HEAVY_ACTIONS = {"dispatch", "resume"}  # 會大量耗 token 的動作（chat 只是開空對話，不算）


def _guard(cfg: Config) -> dict:
    """額度保護狀態（用量達門檻就暫停高耗 token 的動作）。算不出來就當沒暫停：保護失靈不該反過來擋住工作。"""
    try:
        return usage.view(cfg)["guard"]
    except Exception:  # noqa: BLE001 — 讀不到紀錄、設定壞掉等，一律放行
        return {"paused": False, "breached": False, "overridden": False, "reasons": [], "until": None, "override_until": None}


def guard_message(g: dict) -> str:
    when = f"，預計 {usage._clock(g['until'])} 重置" if g.get("until") else ""
    return ("額度保護：" + "、".join(g["reasons"]) + when + "。已暫停高耗 token 的動作（派工、接續處理）；"
            "真的要執行，請在用量面板按「暫時解除暫停」。")


def check_guard(cfg: Config) -> None:
    g = _guard(cfg)
    if g["paused"]:
        raise ConsoleError(guard_message(g))


def _check_project(cfg: Config, project: str) -> str:
    if project not in projects_with_workspace(cfg):
        known = "、".join(projects_with_workspace(cfg)) or "（無）"
        raise ConsoleError(f"沒有這個專案的工作區：{project}。已有：{known}（先 /onboard）")
    return project


def _known_task(cfg: Config, project: str, task: str) -> bool:
    return (task in parse_backlog(cfg.projects_dir / project / "backlog.md")
            or _task_dir(cfg, project, task).is_dir() or cfg.worktree_path(task, project).is_dir())


def build_prompt(cfg: Config, action: str, project: str, task: str, ruling: str = "") -> str | None:
    """組出要送進 claude 的指令；action 不在白名單就拒絕。"""
    if action == "chat":
        return None
    if action == "dispatch":
        return f"/dispatch {project} {task}"
    if action == "resume":
        text = _clean_text(cfg, ruling, _RULING_MAX) if ruling else ""
        return f"/dispatch resume {project} {task}" + (f" {text}" if text else "")
    raise ConsoleError(f"未知動作：{action}")


def _start_session(cfg: Config, name: str, prompt: str | None, *, task: str = "") -> dict:
    claude = shutil.which("claude") or "claude"
    shell_cmd = shlex.join([claude, "-n", name] + ([prompt] if prompt else []))
    result = {"task": task, "session": name, "prompt": prompt or "", "attach": attach_command(name),
              "manual": f"cd {shlex.quote(str(ROOT))} && {shell_cmd}", "created": False, "existing": False, "message": ""}
    if not shutil.which("tmux"):
        result["message"] = "這台機器沒有 tmux，請複製『手動指令』到新終端機貼上"
        return result
    existing = util.run(["tmux", "has-session", "-t", f"={name}"], check=False, mutating=False, timeout=5)
    if existing.returncode == 0:
        result["existing"] = True
        result["message"] = "已有這個對話（沒有重送指令）"
    else:
        util.run(["tmux", "new-session", "-d", "-s", name, "-c", str(ROOT), shell_cmd], timeout=10)
        result["created"] = True
        result["message"] = "已在背景開新對話（沒有開視窗）"
    return result


def launch(cfg: Config, project: str, task: str, action: str, *, ruling: str = "") -> dict:
    """在背景建立（或找到既有的）tmux 對話。不開任何視窗；要互動請用 open_window。"""
    project, task = _check_project(cfg, project), parse_task(task)
    if not _known_task(cfg, project, task):
        raise ConsoleError(f"{project} 沒有任務 {task}（不在 backlog、也沒有交接檔或 worktree）")
    prompt = build_prompt(cfg, action, project, task, ruling)
    if action in HEAVY_ACTIONS:
        check_guard(cfg)  # 額度達門檻：拒絕（輸入有誤的錯誤優先；已有的對話與其他操作不受影響）
    _unremove(cfg, task)  # 重新派工的任務回到看板
    return _start_session(cfg, session_name(task), prompt, task=task)


def launch_batch(cfg: Config, project: str, tasks: list, *, request: str = "", go: bool = False, auto: int = 0) -> dict:
    """為勾選的 backlog 項目（或一段新需求）開**一個** /dispatch 對話，由專案管理員切分批次。

    `auto=N`（自動派工用）：不指定項目，改請專案管理員從 backlog「待辦」項目挑 N 項（`/dispatch <專案> --auto N --go`），
    與勾選項目、新需求三擇一，且一律帶 --go。先全部驗證再動手；只在背景建對話，不開視窗。
    """
    project = _check_project(cfg, project)
    if auto:
        if tasks or request:
            raise ConsoleError("自動挑選與勾選項目、新需求請擇一")
        if isinstance(auto, bool) or not isinstance(auto, int) or not 1 <= auto <= _BATCH_MAX:
            raise ConsoleError(f"自動挑選的項目數必須是 1～{_BATCH_MAX} 的整數")
        if not go:
            raise ConsoleError("自動挑選一律帶 --go（無人值守不能停在計畫確認）")
    if tasks and request:
        raise ConsoleError("勾選項目與新需求請擇一")
    if auto:
        arg = f"--auto {auto}"
    elif request:
        text = _clean_text(cfg, request, _REQUEST_MAX)
        if not text:
            raise ConsoleError("新需求是空的")
        arg = text
    else:
        unique: list[str] = []
        for raw in tasks:
            code = parse_task(str(raw))
            if code not in unique:
                unique.append(code)
        if not unique:
            raise ConsoleError("沒有勾選任何項目，也沒有填新需求")
        if len(unique) > _BATCH_MAX:
            raise ConsoleError(f"一次最多派 {_BATCH_MAX} 個項目，目前勾了 {len(unique)} 個")
        backlog = parse_backlog(cfg.projects_dir / project / "backlog.md")
        missing = [c for c in unique if c not in backlog]
        if missing:
            raise ConsoleError(f"不在 {project} 的 backlog：{', '.join(missing)}")
        arg = ",".join(unique)
        for c in unique:
            _unremove(cfg, c)
    check_guard(cfg)  # 一次派工就會開多個 worktree 與角色，最耗 token：額度達門檻整批拒絕
    name = f"{SESSION_PREFIX}{project}-b{datetime.now().strftime('%H%M%S')}"
    return _start_session(cfg, name, f"/dispatch {project} {arg}" + (" --go" if go else ""))


def open_window(task: str) -> dict:
    """用 wt.exe 開一個終端機分頁接上既有的對話。對話不存在就拒絕（不在這裡建立）。"""
    task = parse_task(task)
    name = session_name(task)
    result = {"task": task, "session": name, "opened": False, "attach": attach_command(name), "message": ""}
    if not shutil.which("tmux"):
        raise ConsoleError("這台機器沒有 tmux")
    if util.run(["tmux", "has-session", "-t", f"={name}"], check=False, mutating=False, timeout=5).returncode != 0:
        raise ConsoleError("這個任務目前沒有對話（可能已關閉），請先建立")
    wt = shutil.which("wt.exe")
    if not wt:
        result["message"] = "找不到 wt.exe，請在終端機執行『接上指令』"
        return result
    cmd = [wt, "-w", "0", "new-tab", "--title", task, "wsl.exe"]
    if os.environ.get("WSL_DISTRO_NAME"):
        cmd += ["-d", os.environ["WSL_DISTRO_NAME"]]
    # --exec：不經 wsl 的預設 shell。zsh 會把字首 `=` 當 equals expansion，用 `--` 會得到「zsh:1: dev-x not found」。
    cmd += ["--exec", "tmux", "attach-session", "-t", f"={name}"]
    subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)
    result.update(opened=True, message="已開指令視窗")
    return result


# ---------------------------------------------------------------- HTTP 伺服器

class Handler(BaseHTTPRequestHandler):
    server_version = "console-ui"
    cfg: Config
    token: str
    port: int

    def log_message(self, fmt, *args):  # 網址帶 token，不寫存取記錄
        pass

    # --- 共用
    def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8") -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: dict) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def _host_ok(self) -> bool:
        return self.headers.get("Host", "") in (f"127.0.0.1:{self.port}", f"localhost:{self.port}")

    def _token_ok(self) -> bool:
        return secrets.compare_digest(self.headers.get("X-Console-Token", ""), self.token)

    # --- 路由
    def do_GET(self):
        if not self._host_ok():
            return self._json(403, {"error": "host"})
        url = urlparse(self.path)
        if url.path == "/":
            if not secrets.compare_digest(parse_qs(url.query).get("k", [""])[0], self.token):
                return self._send(403, "請用 bin/console ui 印出的網址開啟（要帶 ?k=…）".encode("utf-8"),
                                  "text/plain; charset=utf-8")
            html = PAGE.read_text(encoding="utf-8").replace("__TOKEN__", self.token)
            return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
        if url.path == "/api/tasks":
            if not self._token_ok():
                return self._json(403, {"error": "token"})
            sessions = list_sessions()
            tasks = collect(self.cfg, sessions)
            active = {(t["project"], t["task"]) for t in tasks}
            return self._json(200, {
                "now": datetime.now().astimezone().isoformat(timespec="seconds"),
                "tasks": tasks,
                "backlog": backlog_view(self.cfg, active),
                "tools": tools_available(),
                "projects": projects_with_workspace(self.cfg),
                "orphans": sorted(s for s in sessions if not self._known(s, {t["task"] for t in tasks})),
            })
        if url.path == "/api/usage":
            if not self._token_ok():
                return self._json(403, {"error": "token"})
            return self._json(200, {"ok": True, **usage.view(self.cfg, list_sessions())})
        if url.path == "/api/auto":
            if not self._token_ok():
                return self._json(403, {"error": "token"})
            from . import autodispatch
            return self._json(200, {"ok": True, **autodispatch.status(self.cfg)})
        self._json(404, {"error": "not found"})

    @staticmethod
    def _known(session: str, tasks: set[str]) -> bool:
        return session[len(SESSION_PREFIX):] in tasks or bool(_BATCH_SESSION.match(session))

    def do_POST(self):
        try:
            length = max(int(self.headers.get("Content-Length", "0")), 0)
        except ValueError:
            length = 0
        raw = self.rfile.read(min(length, 1 << 20))  # 先讀完再回應，免得拒絕時用戶端遇到連線重設
        if not self._host_ok():
            return self._json(403, {"error": "host"})
        origin = self.headers.get("Origin")
        if origin and origin not in (f"http://127.0.0.1:{self.port}", f"http://localhost:{self.port}"):
            return self._json(403, {"error": "origin"})
        if not self._token_ok() or "application/json" not in self.headers.get("Content-Type", ""):
            return self._json(403, {"error": "token"})
        if length > _BODY_MAX:
            return self._json(413, {"error": "too large"})
        try:
            body = json.loads(raw or b"{}")
            if not isinstance(body, dict):
                raise ValueError
        except (ValueError, json.JSONDecodeError):
            return self._json(400, {"error": "bad json"})
        try:
            if self.path == "/api/queue":
                if "order" in body:
                    set_order(self.cfg, body["order"] if isinstance(body["order"], list) else [])
                else:
                    set_hold(self.cfg, str(body.get("task", "")), bool(body.get("hold")), str(body.get("reason", "")))
                return self._json(200, {"ok": True})
            if self.path == "/api/launch":
                res = launch(self.cfg, str(body.get("project", "")), str(body.get("task", "")),
                             str(body.get("action", "")), ruling=str(body.get("ruling", "")))
                return self._json(200, {"ok": True, **res})
            if self.path == "/api/terminal":
                return self._json(200, {"ok": True, **open_window(str(body.get("task", "")))})
            if self.path == "/api/close":
                closed = close_sessions(task=str(body.get("task", "")), session=str(body.get("session", "")))
                return self._json(200, {"ok": True, "closed": closed})
            if self.path == "/api/remove":
                return self._json(200, {"ok": True, **remove_task(self.cfg, str(body.get("project", "")),
                                                                   str(body.get("task", "")))})
            if self.path == "/api/guard":   # 只有介面能解除（角色沒有指令可以解除）
                g = _guard(self.cfg)
                if bool(body.get("override")) and not g["breached"]:
                    raise ConsoleError("目前額度沒有達門檻，不需要解除")
                usage.set_override(self.cfg.runtime_dir, bool(body.get("override")), until=g.get("until"))
                return self._json(200, {"ok": True, "guard": _guard(self.cfg)})
            if self.path == "/api/auto":   # 自動派工：啟用開關與駐列數（介面設定，存 runtime）
                from . import autodispatch
                conf = autodispatch.save_settings(self.cfg, enabled=body.get("enabled"), slots=body.get("slots"))
                return self._json(200, {"ok": True, "enabled": conf["enabled"], "slots": conf["slots"]})
            if self.path == "/api/launch-batch":
                tasks = body.get("tasks")
                res = launch_batch(self.cfg, str(body.get("project", "")), tasks if isinstance(tasks, list) else [],
                                   request=str(body.get("request", "")))
                return self._json(200, {"ok": True, **res})
        except ConsoleError as exc:
            return self._json(400, {"ok": False, "error": str(exc)})
        self._json(404, {"error": "not found"})


def make_server(cfg: Config, port: int, token: str) -> ThreadingHTTPServer:
    handler = type("BoundHandler", (Handler,), {"cfg": cfg, "token": token, "port": port})
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    handler.port = server.server_address[1]  # port=0 時填入實際埠號（測試用）
    return server


def serve(cfg: Config, port: int = DEFAULT_PORT) -> int:
    token = secrets.token_urlsafe(16)
    try:
        server = make_server(cfg, port, token)
    except OSError as exc:
        raise ConsoleError(f"無法在 127.0.0.1:{port} 開啟介面：{exc}") from exc
    url = f"http://127.0.0.1:{server.server_address[1]}/?k={token}"
    usage.warm_up()  # 用量監控第一次要讀幾百 MB 的對話紀錄，先在背景讀好
    from . import autodispatch   # 延後載入：autodispatch 會 import ui
    autodispatch.start_background(cfg)   # 一律常駐；是否派工由介面的「自動派工」面板（或 config）決定
    conf = autodispatch.settings(cfg)
    if conf["enabled"]:
        say(f"自動派工已啟用：駐列 {conf['slots']} 個、5 小時額度低於 {conf['below_percent']:.0f}% 時，有空位就請專案管理員從 backlog 挑待辦項目補派（bin/console auto status）")
    say(f"中控台介面：{url}")
    say("（只在本機；不會自動開瀏覽器，請自己開上面的網址。Ctrl+C 結束；對話開在 tmux，結束介面不會關掉它們。）")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
