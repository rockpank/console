"""常駐駐列自動派工：進行中的任務少於「駐列數」，且 5 小時額度低於門檻（預設 70%），就請專案管理員從 backlog 挑還沒完成的項目補派。

駐列數與啟用開關在 `bin/console ui` 的「自動派工」面板設定（存 runtime/auto-settings.json，優先於 config 的預設）。
佔用駐列的是看板上「進行中」的任務（group = run：非擱置、非完成、非等你裁示），加上剛派出、還沒全部出現在看板的名額
（LAUNCH_GRACE 內）。等你裁示的任務不佔駐列，但裁示後接續處理時可能暫時超過駐列數。

挑項目的是專案管理員，不是程式，也不需要使用者先把項目放進任何清單：程式只判斷「該不該派、派幾個、派哪個專案」，
派出 `/dispatch <專案> --auto <N> --go`，由 project-manager 從 backlog 狀態「待辦」的項目依優先序挑 N 項，
自動排除「待決」、依賴未滿足、與進行中任務檔案範圍或 model／migration 重疊的項目（見 .claude/skills/dispatch）。
程式只在該專案 backlog 至少有一項「待辦且無待決」時才派，免得白花額度。

安全設計（改動前先想清楚）：
- 預設關閉（`[autodispatch] enabled = false`），要使用者明確開。
- 5 小時額度必須有 statusline 快照、且不是「可能已過時」才算；算不出來＝不派（fail-closed，和 ui._guard 相反：
  這裡是主動花額度，不確定就不花）。
- 額度保護（usage.guard）暫停中不派；兩次派工間隔至少 cooldown。同專案可並行多個批次對話，
  靠 `/dispatch --go` 在已有未完成批次時「追加為新批次、不重排既有任務」（見 .claude/skills/dispatch）。
- 一批最多 batch_size 項；`--go` 略過計畫確認閘門（否則無人值守會卡住）。
  QA（含安全檢查；標資安加派者另加資安）閘門與「不 push、不 commit」規則照舊，結果仍是待使用者驗收的分支。
- 派過一次、局面沒變就不再派（2026-11-19，流程檢視發現：專案管理員常因依賴未合併、檔案衝突而一項都挑不出，
  舊版冷卻後又派，24 小時空轉耗掉百萬 token）：每次派工記下該專案的「局面指紋」＝backlog 每項的（狀態、是否待決）＋
  遠端 origin/<base> 的提交＋該專案進行中的任務。下次評估時指紋一樣，代表專案管理員看過同一份局面、挑不出新的，
  不再派；專案管理員真的挑到項目時 backlog 狀態會變，使用者合併並 push、回答待決、任務完成也會讓指紋改變。
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import time
from pathlib import Path

from . import ui, usage, util
from .config import Config
from .util import ConsoleError

DEFAULTS = {"enabled": False, "below_percent": 70.0, "batch_size": 3, "interval": 300, "cooldown": 1800, "slots": 3}
SLOTS_MAX = 10
LAUNCH_GRACE = 1800      # 剛派出的項目在這段時間內，即使還沒出現在看板也算佔用駐列（秒）
SETTINGS_FILE = "auto-settings.json"
STATE_FILE = "auto-dispatch-state.json"
LOG_FILE = "auto-dispatch.log"
_wake = threading.Event()   # 介面改了設定就叫醒背景執行緒，不必等下一個 interval


def settings(cfg: Config) -> dict:
    out = dict(DEFAULTS)
    section = cfg.raw.get("autodispatch", {})
    if isinstance(section, dict):
        if isinstance(section.get("enabled"), bool):
            out["enabled"] = section["enabled"]
        for key in ("below_percent", "batch_size", "interval", "cooldown"):
            v = section.get(key)
            if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
                out[key] = v
        slots = section.get("slots")
        if isinstance(slots, int) and not isinstance(slots, bool) and slots >= 0:
            out["slots"] = slots
    override = _read(cfg.runtime_dir / SETTINGS_FILE, {})    # 介面設定優先於 config
    if isinstance(override.get("enabled"), bool):
        out["enabled"] = override["enabled"]
    if isinstance(override.get("slots"), int) and not isinstance(override["slots"], bool) and override["slots"] >= 0:
        out["slots"] = override["slots"]
    out["below_percent"] = min(float(out["below_percent"]), 100.0)
    out["batch_size"] = max(1, min(int(out["batch_size"]), ui._BATCH_MAX))
    out["interval"] = max(30, int(out["interval"]))
    out["cooldown"] = int(out["cooldown"])
    out["slots"] = max(0, min(int(out["slots"]), SLOTS_MAX))
    return out


def save_settings(cfg: Config, *, enabled=None, slots=None) -> dict:
    """介面用：改啟用開關與駐列數（只存這兩項）。型別不對就拒絕，不默默修正。"""
    current = _read(cfg.runtime_dir / SETTINGS_FILE, {})
    if enabled is not None:
        if not isinstance(enabled, bool):
            raise ConsoleError("enabled 必須是 true／false")
        current["enabled"] = enabled
    if slots is not None:
        if isinstance(slots, bool) or not isinstance(slots, int) or not 0 <= slots <= SLOTS_MAX:
            raise ConsoleError(f"駐列數必須是 0～{SLOTS_MAX} 的整數")
        current["slots"] = slots
    _write(cfg.runtime_dir / SETTINGS_FILE, {k: current[k] for k in ("enabled", "slots") if k in current})
    _wake.set()
    return settings(cfg)


def _read(path: Path, default):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default
    return data if isinstance(data, type(default)) else default


def _write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".auto-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    os.chmod(path, 0o600)


def _log(cfg: Config, message: str, now: float) -> None:
    path = cfg.runtime_dir / LOG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))} {message}\n")
    os.chmod(path, 0o600)


def occupancy(cfg: Config, live: set[str], now: float, tasks: list[dict] | None = None) -> dict:
    """目前佔用幾個駐列：看板上進行中的任務＋剛派出、還沒全部出現在看板的名額。

    派工時不知道專案管理員會挑哪些項目，所以記「派出幾個名額、當時該專案有幾個進行中」：
    之後該專案進行中的任務多出幾個，就代表幾個名額已經出現在看板，不再另外算。"""
    tasks = ui.collect(cfg, live) if tasks is None else tasks
    running = [(t["project"], t["task"]) for t in tasks if t["group"] == "run"]
    run_by_project: dict[str, int] = {}
    for project, _ in running:
        run_by_project[project] = run_by_project.get(project, 0) + 1
    state = _read(cfg.runtime_dir / STATE_FILE, {})
    pending: list[tuple[str, int]] = []
    for batch in state.get("launched", []):
        if not isinstance(batch, dict) or now - batch.get("at", 0) >= LAUNCH_GRACE:
            continue
        project, count, baseline = batch.get("project", ""), batch.get("count"), batch.get("baseline")
        if project not in cfg.projects or not isinstance(count, int) or not isinstance(baseline, int):
            continue
        left = count - max(0, run_by_project.get(project, 0) - baseline)
        if left > 0:
            pending.append((project, left))
    return {"running": running, "pending": pending, "count": len(running) + sum(n for _, n in pending),
            "by_project": run_by_project}


def ready_items(cfg: Config, project: str) -> list[str]:
    """backlog 內「待辦且沒有待決」的項目（專案管理員挑項目的候選；程式只用來判斷值不值得派）。"""
    backlog = ui.parse_backlog(cfg.projects_dir / project / "backlog.md")
    return [c for c, row in backlog.items() if row["status"] == "待辦" and not row["undecided"]]


def _origin_head(cfg: Config, project: str) -> str:
    """專案遠端 base 分支目前的提交（本機的 origin/<base>，不連網）；讀不到就回空字串。"""
    conf = cfg.projects.get(project, {})
    repo = conf.get("repo")
    if not repo:
        return ""
    try:
        res = util.run(["git", "-C", repo, "rev-parse", f"origin/{conf.get('base_branch', 'master')}"],
                       check=False, mutating=False, timeout=5)
    except Exception:  # noqa: BLE001 — 讀不到只是少一個變化訊號，不影響派工判斷
        return ""
    return res.stdout.strip() if res.returncode == 0 else ""


def fingerprint(cfg: Config, project: str, tasks: list[dict]) -> str:
    """局面指紋：專案管理員挑項目時依據的東西有沒有變。內容見模組說明。"""
    backlog = ui.parse_backlog(cfg.projects_dir / project / "backlog.md")
    rows = sorted((code, row["status"], bool(row["undecided"])) for code, row in backlog.items())
    running = sorted(t["task"] for t in tasks if t["project"] == project and t["group"] == "run")
    raw = json.dumps([rows, _origin_head(cfg, project), running], ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def evaluate(cfg: Config, view: dict, live: set[str], now: float, tasks: list[dict] | None = None) -> dict:
    """純判斷（不開對話）：回傳 {"go": bool, "reason": str, "project": str, "count": 要請專案管理員挑幾項, ...}。"""
    conf = settings(cfg)
    no = lambda reason: {"go": False, "reason": reason, "project": "", "count": 0}  # noqa: E731
    if not conf["enabled"]:
        return no("未啟用（[autodispatch] enabled = false）")
    q5 = next((q for q in view["quotas"] if q["key"] == "five_hour"), None)
    if not q5 or q5["pct"] is None or q5["source"] != "statusline":
        return no("沒有 5 小時額度的 statusline 快照，不派")
    if q5["stale"]:
        return no("5 小時額度數據可能已過時，不派")
    if q5["pct"] >= conf["below_percent"]:
        return no(f"5 小時額度已用 {q5['pct']:.0f}%，未低於 {conf['below_percent']:.0f}%")
    if view["guard"]["paused"]:
        return no("額度保護暫停中")
    state = _read(cfg.runtime_dir / STATE_FILE, {})
    last = state.get("last_at", 0)
    if now - last < conf["cooldown"]:
        return no(f"距上次派工未滿 {conf['cooldown'] // 60} 分鐘")
    tasks = ui.collect(cfg, live) if tasks is None else tasks
    occ = occupancy(cfg, live, now, tasks)
    used = occ["count"]
    free = conf["slots"] - used
    if free <= 0:
        return no(f"駐列已滿（{used}／{conf['slots']}）")
    seen = state.get("fingerprints", {}) if isinstance(state.get("fingerprints"), dict) else {}
    settled: list[str] = []
    for project in cfg.projects:
        ready = ready_items(cfg, project)
        if not ready:
            continue
        fp = fingerprint(cfg, project, tasks)
        if seen.get(project) == fp:
            settled.append(project)
            continue
        return {"go": True, "reason": f"駐列 {used}／{conf['slots']}、5 小時額度 {q5['pct']:.0f}% < {conf['below_percent']:.0f}%",
                "project": project, "count": min(free, conf["batch_size"], len(ready)), "candidates": ready,
                "baseline": occ["by_project"].get(project, 0), "fingerprint": fp}
    if settled:
        return no(f"{'、'.join(settled)}：上次請專案管理員挑過後局面沒有變（backlog 狀態、遠端 base 提交、進行中任務都一樣），"
                  f"再派也挑不出新的；有變化才會再派")
    return no(f"沒有可派的項目（backlog 沒有「待辦」且無「待決」的項目）；駐列 {used}／{conf['slots']}")


def tick(cfg: Config, now: float | None = None) -> dict:
    """做一次檢查，條件成立就派一批。回傳 evaluate 的結果（派出時多一個 session）。"""
    now = time.time() if now is None else now
    if not settings(cfg)["enabled"]:        # 執行緒一律常駐：未啟用時不必讀用量與對話
        return {"go": False, "reason": "未啟用", "project": "", "count": 0}
    view = usage.view(cfg)
    live = ui.list_sessions()
    decision = evaluate(cfg, view, live, now)
    if not decision["go"]:
        return decision
    res = ui.launch_batch(cfg, decision["project"], [], go=True, auto=decision["count"])
    prev = _read(cfg.runtime_dir / STATE_FILE, {})
    old = [b for b in prev.get("launched", []) if isinstance(b, dict) and now - b.get("at", 0) < LAUNCH_GRACE]
    fps = dict(prev.get("fingerprints", {})) if isinstance(prev.get("fingerprints"), dict) else {}
    fps[decision["project"]] = decision["fingerprint"]
    launched = old + [{"project": decision["project"], "count": decision["count"],
                       "baseline": decision["baseline"], "at": now}]
    _write(cfg.runtime_dir / STATE_FILE, {"last_at": now, "project": decision["project"],
                                          "count": decision["count"], "launched": launched[-20:],
                                          "fingerprints": fps})
    decision["session"] = res["session"]
    _log(cfg, f"派工 {decision['project']} 請專案管理員挑 {decision['count']} 項（{decision['reason']}）→ {res['session']}", now)
    return decision


def status(cfg: Config, now: float | None = None) -> dict:
    """給介面看的狀態：設定、駐列佔用、可派的待辦項目、現在會不會派（與原因）。"""
    now = time.time() if now is None else now
    live = ui.list_sessions()
    tasks = ui.collect(cfg, live)
    conf = settings(cfg)
    occ = occupancy(cfg, live, now, tasks)
    try:
        decision = evaluate(cfg, usage.view(cfg, live), live, now, tasks)
    except Exception as exc:  # noqa: BLE001 — 讀不到額度等：照實顯示，不讓面板壞掉
        decision = {"go": False, "reason": f"判斷失敗：{type(exc).__name__}", "project": "", "count": 0}
    state = _read(cfg.runtime_dir / STATE_FILE, {})
    return {"enabled": conf["enabled"], "slots": conf["slots"], "slots_max": SLOTS_MAX,
            "below_percent": conf["below_percent"], "occupied": occ["count"],
            "running": [f"{p}/{t}" for p, t in occ["running"]], "pending": [f"{p}（{n} 個名額）" for p, n in occ["pending"]],
            "ready": {p: ready_items(cfg, p) for p in cfg.projects if ready_items(cfg, p)},
            "will_dispatch": decision["go"], "reason": decision["reason"],
            "next": {"project": decision["project"], "count": decision["count"]} if decision["go"] else None,
            "last": {"at": state.get("last_at"), "project": state.get("project", ""), "count": state.get("count", 0)}
            if state.get("last_at") else None}


def start_background(cfg: Config) -> threading.Thread:
    """在 `bin/console ui` 裡起背景執行緒。一律啟動（介面隨時可以開關）；未啟用時只是空轉。
    每次檢查出錯只記 log，不中斷；設定每圈重讀，介面改了設定會立刻叫醒。"""
    def loop():
        while True:
            try:
                tick(cfg)
            except Exception as exc:  # noqa: BLE001
                try:
                    _log(cfg, f"檢查失敗：{type(exc).__name__}: {exc}", time.time())
                except OSError:
                    pass
            _wake.wait(settings(cfg)["interval"])
            _wake.clear()

    thread = threading.Thread(target=loop, name="auto-dispatch", daemon=True)
    thread.start()
    return thread
