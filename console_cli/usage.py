"""用量監控：彙整 Claude Code 的 token 用量，達門檻就告警。

資料來源（都在本機，只讀數字）：
1. 對話紀錄 `~/.claude/projects/**/*.jsonl`：每則回覆的 usage、時間、sessionId、模型，以及對話名稱
   （只認 `dev-<任務>` 這種名稱）。**不讀、不存任何對話內容。** 同一則回覆的 usage 會在紀錄裡重複寫入，
   所以用 (requestId, message.id) 去重；subagent 的用量在 `<session>/subagents/` 下，一併計入。
2. statusline 快照 `runtime/usage/<session>.json`：Claude Code 的 statusline 會把方案額度（5 小時／每週的
   百分比與重置時間）和 context 填滿程度餵給 `bin/usage-statusline`，由它寫成快照。這是本機唯一拿得到
   「方案額度百分比」的來源；沒有快照（沒開 statusline、或不是 Pro/Max 訂閱）就退回用 config 的上限估算。

額度的「估算」只算 輸入＋快取寫入＋輸出（不含快取讀取）；方案實際怎麼加權沒有公開，所以只當參考。
"""
from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"
HORIZON = 8 * 86400            # 只看最近 8 天（比週視窗多一天）
BLOCK = 5 * 3600               # 5 小時視窗
WEEK = 7 * 86400
LIVE_WINDOW = 30 * 60          # 這段時間內有動靜才算「進行中」的對話（context 告警只看這些）
SNAPSHOT_FRESH = 15 * 60       # 快照多久內算新鮮
SNAPSHOT_KEEP = 3 * 86400
_SESSION_NAME = re.compile(r"^dev-([A-Za-z0-9][A-Za-z0-9_-]{0,63})$")
_SESSION_ID = re.compile(r"^[0-9A-Za-z-]{8,64}$")

DEFAULTS = {
    "alert_percent": 90,       # 達這個百分比就告警
    "five_hour_tokens": 0,     # 5 小時視窗的 token 上限（估算用）；0＝未設定
    "weekly_tokens": 0,        # 每週的 token 上限（估算用）；0＝未設定
    "context_window": 200_000, # 單一對話的 context 上限；沒有快照時，只有你明確設定才會拿來告警
}


def settings(cfg_raw: dict | None) -> dict:
    """合併 config/console.toml 的 [usage] 與預設值；壞值退回預設。"""
    out = {**DEFAULTS, "context_window_explicit": False}
    section = (cfg_raw or {}).get("usage", {})
    if isinstance(section, dict):
        for key, default in DEFAULTS.items():
            value = section.get(key, default)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
                out[key] = value
        windows = section.get("context_windows")
        if isinstance(windows, dict):
            out["context_windows"] = {str(k): int(v) for k, v in windows.items()
                                      if isinstance(v, (int, float)) and v > 0}
        out["context_window_explicit"] = "context_window" in section and out["context_window"] > 0
    if not 1 <= out["alert_percent"] <= 100:
        out["alert_percent"] = DEFAULTS["alert_percent"]
    return out


# ---------------------------------------------------------------- 對話紀錄索引（增量讀取）

def _epoch(iso: str) -> float:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except (ValueError, AttributeError):
        return 0.0


class Index:
    """增量掃描對話紀錄：記住每個檔讀到哪，之後只讀新增的部分。執行緒安全。"""

    def __init__(self, root: Path | None = None, horizon: int = HORIZON):
        self.root = Path(root) if root else PROJECTS_DIR
        self.horizon = horizon
        self._lock = threading.Lock()
        self._offsets: dict[str, int] = {}
        # (requestId, message.id) -> [ts, session, model, input, cache_create, cache_read, output, sidechain]
        self.records: dict[tuple[str, str], list] = {}
        self.titles: dict[str, str] = {}              # sessionId -> dev-<任務>
        self.limits: list[dict] = []                  # 被限流的事件
        self._limit_seen: set[tuple] = set()
        self.loaded = False

    def _files(self):
        yield from self.root.glob("*/*.jsonl")
        yield from self.root.glob("*/*/subagents/*.jsonl")

    def refresh(self, now: float | None = None) -> None:
        now = time.time() if now is None else now
        with self._lock:
            for path in self._files():
                try:
                    st = path.stat()
                except OSError:
                    continue
                key = str(path)
                if st.st_mtime < now - self.horizon:
                    self._offsets.pop(key, None)
                    continue
                offset = self._offsets.get(key, 0)
                if st.st_size < offset:      # 檔案被截短或換掉
                    offset = 0
                if st.st_size == offset:
                    continue
                try:
                    with open(path, "rb") as fh:
                        fh.seek(offset)
                        chunk = fh.read()
                except OSError:
                    continue
                end = chunk.rfind(b"\n")
                if end < 0:                  # 最後一行還沒寫完，下次再讀
                    continue
                self._offsets[key] = offset + end + 1
                self._ingest(chunk[:end + 1], path)
            cutoff = now - self.horizon
            if len(self.records) > 1000:
                self.records = {k: v for k, v in self.records.items() if v[0] >= cutoff}
            self.loaded = True

    def _session_of(self, path: Path, obj: dict) -> str:
        if path.parent.name == "subagents":  # <project>/<session>/subagents/agent-x.jsonl
            return path.parent.parent.name
        return str(obj.get("sessionId") or path.stem)

    def _ingest(self, chunk: bytes, path: Path) -> None:
        in_subagents = path.parent.name == "subagents"
        for raw in chunk.split(b"\n"):
            if not raw:
                continue
            if b'"quotaLimits"' in raw:      # 這行同時也是 type=assistant（合成的錯誤訊息），所以不能用 elif
                self._add_limit(raw)
            if b'"usage"' in raw and b'"type":"assistant"' in raw:
                self._add_usage(raw, path, in_subagents)
            elif b'"custom-title"' in raw:
                self._add_title(raw, path)

    def _add_usage(self, raw: bytes, path: Path, in_subagents: bool) -> None:
        try:
            obj = json.loads(raw)
            msg = obj["message"]
            usage = msg["usage"]
        except (ValueError, KeyError, TypeError):
            return
        model = str(msg.get("model") or "")
        if not isinstance(usage, dict) or model.startswith("<"):   # <synthetic> 是錯誤訊息，沒有用量
            return
        key = (str(obj.get("requestId") or ""), str(msg.get("id") or obj.get("uuid") or ""))
        nums = [int(usage.get(k) or 0) for k in
                ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")]
        ts = _epoch(str(obj.get("timestamp") or ""))
        old = self.records.get(key)
        if old:   # 串流中的重複行：每個欄位取較大者
            for i, n in enumerate(nums):
                old[3 + i] = max(old[3 + i], n)
            old[0] = min(old[0], ts) if old[0] and ts else (old[0] or ts)
        else:
            self.records[key] = [ts, self._session_of(path, obj), model, *nums,
                                 bool(obj.get("isSidechain")) or in_subagents]

    def _add_title(self, raw: bytes, path: Path) -> None:
        try:
            obj = json.loads(raw)
        except ValueError:
            return
        name = str(obj.get("customTitle") or "")
        if _SESSION_NAME.match(name):        # 其他名稱可能含需求內容，一律不保留
            self.titles[self._session_of(path, obj)] = name

    def _add_limit(self, raw: bytes) -> None:
        try:
            obj = json.loads(raw)
            quota = obj["quotaLimits"]
        except (ValueError, KeyError, TypeError):
            return
        if not isinstance(quota, dict) or quota.get("status") != "rejected":
            return
        event = {"ts": _epoch(str(obj.get("timestamp") or "")), "type": str(quota.get("rateLimitType") or "?"),
                 "resets_at": float(quota.get("resetsAt") or 0)}
        key = (event["ts"], event["type"])
        if key not in self._limit_seen:
            self._limit_seen.add(key)
            self.limits.append(event)

    def snapshot(self) -> tuple[list[list], dict[str, str], list[dict]]:
        with self._lock:
            return list(self.records.values()), dict(self.titles), list(self.limits)


# ---------------------------------------------------------------- statusline 快照

def snapshot_dir(runtime_dir: Path) -> Path:
    return Path(runtime_dir) / "usage"


def _num(value, lo=0.0, hi=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value < lo or (hi is not None and value > hi):
        return None
    return float(value)


def extract_snapshot(payload: dict, now: float) -> dict | None:
    """從 statusline 的 stdin JSON 只挑數字欄位；不帶路徑、工作目錄、對話內容。"""
    session = str(payload.get("session_id") or "")
    if not _SESSION_ID.match(session):
        return None
    model = payload.get("model")
    model_id = str(model.get("id") if isinstance(model, dict) else model or "")[:80]
    ctx = payload.get("context_window") if isinstance(payload.get("context_window"), dict) else {}
    snap: dict = {"session": session, "model": model_id, "at": now,
                  "ctx_pct": _num(ctx.get("used_percentage"), 0, 1000), "ctx_size": _num(ctx.get("context_window_size"), 1)}
    limits = payload.get("rate_limits") if isinstance(payload.get("rate_limits"), dict) else {}
    for key in ("five_hour", "seven_day"):
        win = limits.get(key)
        if isinstance(win, dict):
            pct, reset = _num(win.get("used_percentage"), 0, 1000), _num(win.get("resets_at"), 1)
            if pct is not None:
                snap[key] = {"pct": pct, "resets_at": reset}
    return snap


def write_snapshot(runtime_dir: Path, snap: dict) -> None:
    folder = snapshot_dir(runtime_dir)
    folder.mkdir(parents=True, exist_ok=True)
    os.chmod(folder, 0o700)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".snap-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(snap, fh)
    os.chmod(tmp, 0o600)
    target = folder / f"{snap['session']}.json"
    os.replace(tmp, target)   # 原子替換：讀的人不會讀到寫一半
    cutoff = time.time() - SNAPSHOT_KEEP      # 清理看的是檔案 mtime，所以用真實時鐘比（不是快照內的時間）
    for old in folder.glob("*.json"):
        try:
            if old != target and old.stat().st_mtime < cutoff:   # 絕不清掉剛寫的這份
                old.unlink()
        except OSError:
            pass


def read_snapshots(runtime_dir: Path) -> list[dict]:
    out = []
    for path in snapshot_dir(runtime_dir).glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and isinstance(data.get("at"), (int, float)):
            out.append(data)
    return out


def statusline_text(snap: dict, alert_percent: float) -> str:
    """給 Claude Code 狀態列顯示的一行字。"""
    parts = []
    for key, label in (("five_hour", "5h"), ("seven_day", "7d")):
        if key in snap:
            parts.append(f"{label} {snap[key]['pct']:.0f}%")
    if snap.get("ctx_pct") is not None:
        parts.append(f"ctx {snap['ctx_pct']:.0f}%")
    hot = any(snap.get(k, {}).get("pct", 0) >= alert_percent for k in ("five_hour", "seven_day")) \
        or (snap.get("ctx_pct") or 0) >= alert_percent
    return ("⚠ " if hot else "") + " · ".join(parts)


# ---------------------------------------------------------------- 彙整

def _weighted(rec) -> int:
    return rec[3] + rec[4] + rec[6]          # 輸入＋快取寫入＋輸出（不含快取讀取）


def current_block(stamps: list[float], now: float) -> tuple[float, float] | None:
    """5 小時視窗（比照 ccusage）：從第一則訊息的整點開始，滿 5 小時或中斷 5 小時就換新的一塊。"""
    start = end = last = None
    for ts in sorted(s for s in stamps if s):
        if start is None or ts >= end or ts - last >= BLOCK:
            start = ts - ts % 3600
            end = start + BLOCK
        last = ts
    if start is None or now >= end or now - last >= BLOCK:
        return None
    return start, end


def _window(snaps: list[dict], key: str, now: float, data_at) -> dict | None:
    """所有快照裡「數據最新」且還沒過重置時間的那個視窗（額度是帳號層級的，哪個對話回報都該一樣）。

    注意：不能用快照的寫入時間排序。statusline 在快取過期等事件也會重跑，但 `rate_limits` 永遠是該對話
    「最後一次 API 回應」時的值；閒置的對話會一直把舊值（例如 14:05 的 100%）寫成新快照，蓋掉較新的數字。
    所以每份快照的數據時間＝該對話最後一次回應的時間（見 summarize 的 data_at）。
    """
    best = None
    for snap in snaps:
        win = snap.get(key)
        if not win or (win.get("resets_at") and win["resets_at"] <= now):
            continue
        at = data_at(snap)
        if best is None or (at, snap["at"]) > (best[0], best[2]):
            best = (at, win, snap["at"])
    return None if best is None else {**best[1], "at": best[0]}


def _label(session: str, titles: dict[str, str]) -> tuple[str, str]:
    """(顯示名稱, 任務)。非 dev- 對話只顯示代號，不顯示任何標題。"""
    name = titles.get(session, "")
    m = _SESSION_NAME.match(name)
    if m:
        return name, m.group(1)
    return "其他對話 " + session[:8], ""


def summarize(index: Index, cfg_raw: dict | None, runtime_dir: Path, now: float | None = None,
              live_sessions: set[str] | None = None) -> dict:
    now = time.time() if now is None else now
    conf = settings(cfg_raw)
    threshold = float(conf["alert_percent"])
    records, titles, limits = index.snapshot()
    snaps = read_snapshots(runtime_dir)
    live_sessions = live_sessions or set()

    by_session: dict[str, list] = defaultdict(list)
    for r in records:
        by_session[r[1]].append(r)
    last_response = {sid: max(r[0] for r in recs) for sid, recs in by_session.items()}

    def data_at(snap: dict) -> float:
        """這份快照的數據是什麼時候的：該對話最後一次回應（寫入時間之後的回應還沒反映進來，所以取較小者）。"""
        last = last_response.get(snap["session"])
        return min(snap["at"], last) if last else snap["at"]

    snap5 = _window(snaps, "five_hour", now, data_at)
    snap7 = _window(snaps, "seven_day", now, data_at)
    # 視窗：有快照就用快照給的真實重置時間倒推；沒有才用紀錄推算（兩者可能差好幾個小時）
    if snap5 and snap5.get("resets_at"):
        block, block_src = (snap5["resets_at"] - BLOCK, snap5["resets_at"]), "statusline"
    else:
        block, block_src = current_block([r[0] for r in records], now), "estimate"
    week_start = snap7["resets_at"] - WEEK if snap7 and snap7.get("resets_at") else now - WEEK
    in_block = [r for r in records if block and block[0] <= r[0] < block[1]]
    week = [r for r in records if week_start <= r[0] <= now]
    day = [r for r in records if r[0] >= now - 86400]

    def quota(key: str, label: str, snap: dict | None, used: int, limit: float, start: float | None, est_reset: float | None) -> dict:
        out = {"key": key, "label": label, "used_tokens": used, "limit_tokens": limit or None, "pct": None,
               "source": None, "resets_at": est_reset, "window_start": start, "data_age": None, "stale": False}
        if snap:
            age = max(0, int(now - snap["at"]))
            out.update(pct=round(snap["pct"], 1), source="statusline", resets_at=snap.get("resets_at") or est_reset,
                       data_age=age, stale=age > SNAPSHOT_FRESH)
        elif limit:
            out.update(pct=round(used / limit * 100, 1), source="estimate")
        return out

    quotas = [
        quota("five_hour", "5 小時額度", snap5, sum(map(_weighted, in_block)), conf["five_hour_tokens"],
              block[0] if block else None, block[1] if block else None),
        quota("seven_day", "每週額度", snap7, sum(map(_weighted, week)), conf["weekly_tokens"], week_start,
              snap7["resets_at"] if snap7 and snap7.get("resets_at") else None),
    ]

    # 每個對話：最後一則主對話回覆的 context 大小。快照只要是在該對話最後一次回應「之後」寫的就有效
    # （對話閒置多久都一樣：context 只在回應時才會變）。
    fresh = {s["session"]: s for s in snaps if s["at"] >= last_response.get(s["session"], 0) - 2}
    model_peak: dict[str, int] = defaultdict(int)     # 各模型觀察到的最大 context，用來推測上限
    for r in records:
        model_peak[r[2]] = max(model_peak[r[2]], r[3] + r[4] + r[5])
    sessions = []
    for sid, recs in by_session.items():
        last_ts = max(r[0] for r in recs)
        if last_ts < now - 86400:
            continue
        main = [r for r in recs if not r[7]] or recs
        latest = max(main, key=lambda r: r[0])
        used = latest[3] + latest[4] + latest[5]
        snap = fresh.get(sid)
        snap_size = (snap or {}).get("ctx_size")
        by_model = conf.get("context_windows", {}).get(latest[2])
        # 上限的可信度：快照 > 使用者在 config 明確設定 > 推測。推測只用來畫進度條，不拿來告警，
        # 否則上限猜錯（例如實際是 1M 卻當 200k）就會天天誤報。
        known = bool(snap_size or by_model or conf["context_window_explicit"])
        size = snap_size or by_model or (conf["context_window"] if known else
                                         (1_000_000 if model_peak.get(latest[2], 0) > conf["context_window"] else conf["context_window"]))
        pct = snap["ctx_pct"] if snap and snap.get("ctx_pct") is not None else used / size * 100
        name, task = _label(sid, titles)
        sessions.append({
            "session": sid[:8], "name": name, "task": task, "model": latest[2], "ctx_tokens": used,
            "ctx_size": int(size), "ctx_pct": round(pct, 1), "ctx_source": "statusline" if snap else "estimate",
            "ctx_known": known,
            "last": last_ts, "live": now - last_ts <= LIVE_WINDOW, "tmux": name in live_sessions,
            "tokens_5h": sum(_weighted(r) for r in recs if block and r[0] >= block[0]),
            "tokens_24h": sum(_weighted(r) for r in recs if r[0] >= now - 86400),
        })
    sessions.sort(key=lambda s: -s["last"])

    tasks: dict[str, dict] = {}
    for s in sessions:
        key = s["task"] or "other"
        t = tasks.setdefault(key, {"task": s["task"], "tokens_5h": 0, "tokens_24h": 0, "tokens_7d": 0,
                                  "ctx_max": 0.0, "sessions": 0})
        t["tokens_5h"] += s["tokens_5h"]
        t["tokens_24h"] += s["tokens_24h"]
        t["ctx_max"] = max(t["ctx_max"], s["ctx_pct"] if s["live"] else 0)
        t["sessions"] += 1
    for sid, recs in by_session.items():
        key = _label(sid, titles)[1] or "other"
        if key in tasks:
            tasks[key]["tokens_7d"] += sum(_weighted(r) for r in recs if r[0] >= now - WEEK)

    hour0 = int(now // 3600) - 23
    hourly = [0] * 24
    for r in day:
        i = int(r[0] // 3600) - hour0
        if 0 <= i < 24:
            hourly[i] += _weighted(r)
    models: dict[str, int] = defaultdict(int)
    for r in day:
        models[r[2]] += _weighted(r)

    def still_limited(event: dict) -> bool:
        if event["resets_at"] <= now:
            return False
        for snap in snaps:   # 事件之後「數據」更新、且該視窗沒滿（或已換成別的視窗）→ 已恢復
            win = snap.get(event["type"])
            if win and data_at(snap) > event["ts"] and (
                    win["pct"] < 100 or abs((win.get("resets_at") or 0) - event["resets_at"]) > 60):
                return False
        return True

    recent_limits = sorted((e for e in limits if e["ts"] >= now - 86400), key=lambda e: -e["ts"])[:5]
    for e in recent_limits:
        e["active"] = still_limited(e)
    result = {
        "now": now, "alert_percent": threshold, "configured": bool(conf["five_hour_tokens"] or conf["weekly_tokens"]),
        "quotas": quotas,
        "block": ({"start": block[0], "end": block[1], "messages": len(in_block), "source": block_src,
                   "cache_read": sum(r[5] for r in in_block)} if block else None),
        "sessions": sessions[:20], "tasks": sorted(tasks.values(), key=lambda t: -t["tokens_24h"]),
        "hourly": {"start": (hour0) * 3600, "tokens": hourly},
        "models": sorted(({"model": m, "tokens": t} for m, t in models.items()), key=lambda x: -x["tokens"]),
        "limits": [{"at": e["ts"], "type": e["type"], "resets_at": e["resets_at"], "active": e["active"]}
                   for e in recent_limits],
        "records": len(records), "loaded": index.loaded,
    }
    result["alerts"] = alerts(result)
    result["guard"] = guard(result, runtime_dir)
    return result


def alerts(view: dict) -> list[dict]:
    """告警清單。id 穩定，介面靠它避免同一個告警一直跳通知。"""
    out: list[dict] = []
    now, threshold = view["now"], view["alert_percent"]
    for e in view["limits"]:
        if e["active"] and e["at"] >= now - 6 * 3600:
            out.append({"id": f"limited:{e['type']}:{int(e['resets_at'])}", "level": "crit",
                        "title": "額度已被限流（HTTP 429）", "detail": f"{e['type']} 視窗被拒絕，預計 {_clock(e['resets_at'])} 重置"})
            break
    for q in view["quotas"]:
        if q["pct"] is not None and q["pct"] >= threshold:
            reset = f"，{_clock(q['resets_at'])} 重置" if q["resets_at"] else ""
            out.append({"id": f"quota:{q['key']}:{int(q['resets_at'] or 0)}", "level": "crit" if q["pct"] >= 100 else "warn",
                        "title": f"{q['label']}已用 {q['pct']:.0f}%", "detail": f"達到 {threshold:.0f}% 門檻{reset}"})
    for s in view["sessions"]:
        if s["live"] and s["ctx_known"] and s["ctx_pct"] >= threshold:
            out.append({"id": f"ctx:{s['session']}", "level": "warn", "title": f"{s['name']} 的 context 已用 {s['ctx_pct']:.0f}%",
                        "detail": "快要自動壓縮或爆掉，建議收尾或開新對話"})
    return out


# ---------------------------------------------------------------- 額度保護：達門檻就暫停高耗 token 的動作

GUARD_FILE = "usage-guard.json"
OVERRIDE_MAX = 5 * 3600          # 手動解除最久維持多久（到額度重置或這個時間，取較早者）


def guard(view: dict, runtime_dir: Path, now: float | None = None) -> dict:
    """額度（5 小時／每週）達門檻、或正被限流 → 暫停高耗 token 的動作。context 告警不算（那只影響單一對話）。

    使用者在介面按「暫時解除」會寫 runtime/usage-guard.json（只有介面能寫；角色不該、也沒有指令能解除）。
    """
    now = view["now"] if now is None else now
    reasons, until = [], 0.0
    for q in view["quotas"]:
        if q["pct"] is not None and q["pct"] >= view["alert_percent"]:
            reasons.append(f"{q['label']}已用 {q['pct']:.0f}%")
            until = max(until, q["resets_at"] or 0)
    for e in view["limits"]:
        if e["active"] and e["at"] >= now - 6 * 3600:
            reasons.append("額度已被限流（HTTP 429）")
            until = max(until, e["resets_at"])
            break
    override = read_override(runtime_dir, now)
    breached = bool(reasons)
    return {"paused": breached and not override, "breached": breached, "overridden": breached and bool(override),
            "reasons": reasons, "until": until or None, "override_until": override or None}


def read_override(runtime_dir: Path, now: float) -> float:
    try:
        until = float(json.loads((Path(runtime_dir) / GUARD_FILE).read_text(encoding="utf-8"))["override_until"])
    except (OSError, ValueError, KeyError, TypeError):
        return 0.0
    return until if until > now else 0.0


def set_override(runtime_dir: Path, on: bool, until: float | None = None, now: float | None = None) -> float:
    """暫時解除（on=True，維持到 until，最久 OVERRIDE_MAX）或恢復暫停（on=False）。回傳生效的截止時間（0＝沒有）。"""
    now = time.time() if now is None else now
    path = Path(runtime_dir) / GUARD_FILE
    if not on:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return 0.0
    end = min(until or now + OVERRIDE_MAX, now + OVERRIDE_MAX)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".guard-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump({"override_until": end, "set_at": now}, fh)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return end


def _clock(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).astimezone().strftime("%m/%d %H:%M")


# ---------------------------------------------------------------- 全域索引（介面與 CLI 共用）

_INDEX: Index | None = None
_INDEX_LOCK = threading.Lock()


def shared_index() -> Index:
    global _INDEX
    with _INDEX_LOCK:
        if _INDEX is None:
            _INDEX = Index()
        return _INDEX


def warm_up() -> None:
    """在背景先讀一遍紀錄（第一次要讀幾百 MB），介面開起來就不用等。"""
    threading.Thread(target=lambda: shared_index().refresh(), daemon=True, name="usage-warmup").start()


def view(cfg, live_sessions: set[str] | None = None) -> dict:
    index = shared_index()
    index.refresh()
    return summarize(index, cfg.raw, cfg.runtime_dir, live_sessions=live_sessions)


# ---------------------------------------------------------------- statusline 入口與文字報表

def statusline_run(raw: str, cfg_raw: dict | None, runtime_dir: Path, now: float | None = None) -> str:
    """statusline 掛鉤：存快照、回傳要顯示在狀態列的一行字。壞輸入回傳空字串。"""
    try:
        payload = json.loads(raw)
    except ValueError:
        return ""
    snap = extract_snapshot(payload, time.time() if now is None else now) if isinstance(payload, dict) else None
    if not snap:
        return ""
    write_snapshot(runtime_dir, snap)
    return statusline_text(snap, settings(cfg_raw)["alert_percent"])


def fmt_tokens(n: float) -> str:
    n = float(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(int(n))


def render_text(view: dict) -> str:
    """給 `bin/console usage` 印的文字報表。"""
    lines = [f"用量監控（告警門檻 {view['alert_percent']:.0f}%）", ""]
    for q in view["quotas"]:
        if q["pct"] is None:
            pct = "未設定上限，無法算百分比"
        else:
            src = ("statusline，數據 %d 分鐘前%s" % (q["data_age"] // 60, "，可能已過時" if q["stale"] else "")
                   if q["source"] == "statusline" else "依 config 上限估算")
            pct = f"{q['pct']:.0f}%（{src}）"
        reset = f"，{_clock(q['resets_at'])} 重置" if q["resets_at"] else ""
        lines.append(f"{q['label']:<8} {pct}；估算已用 {fmt_tokens(q['used_tokens'])} tokens{reset}")
    if view["sessions"]:
        lines += ["", "對話 context："]
        for s in view["sessions"][:10]:
            flag = "進行中" if s["live"] else "閒置"
            note = "" if s["ctx_known"] else "（上限為推測，不告警）"
            lines.append(f"  {s['name']:<22} {s['ctx_pct']:5.1f}%  {fmt_tokens(s['ctx_tokens'])}/{fmt_tokens(s['ctx_size'])}  {flag}{note}")
    if view["tasks"]:
        lines += ["", "各任務用量（tokens，不含快取讀取）：", f"  {'任務':<8} {'5 小時':>8} {'24 小時':>8} {'7 天':>8}"]
        for t in view["tasks"][:10]:
            lines.append(f"  {t['task'] if t['task'] else '其他':<8} {fmt_tokens(t['tokens_5h']):>8} "
                         f"{fmt_tokens(t['tokens_24h']):>8} {fmt_tokens(t['tokens_7d']):>8}")
    g = view["guard"]
    if g["paused"]:
        lines += ["", "⏸ 額度保護：已暫停高耗 token 的動作（派工、接續處理）— " + "、".join(g["reasons"]) +
                  (f"；預計 {_clock(g['until'])} 重置" if g["until"] else "")]
    elif g["overridden"]:
        lines += ["", f"額度保護已由使用者暫時解除，到 {_clock(g['override_until'])}（{'、'.join(g['reasons'])}）"]
    if view["limits"]:
        lines += ["", f"近 24 小時被限流 {len(view['limits'])} 次，最近一次 {_clock(view['limits'][0]['at'])}"]
    lines.append("")
    if view["alerts"]:
        lines += [("‼ " if a["level"] == "crit" else "⚠ ") + f"{a['title']}：{a['detail']}" for a in view["alerts"]]
    else:
        lines.append("沒有告警")
    return "\n".join(lines)
