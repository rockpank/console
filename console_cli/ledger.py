"""用量帳本：每個子代理結束記一筆、每次停下來等使用者回答記一筆，供「每輪覆盤」（流程優化師）彙總。

為什麼要有它：以前各角色的 token、工具呼叫、重工、等使用者的次數只散落在對話裡，要靠調度者憑印象加總，
覆盤沒有可信的數字。帳本是 runtime/round-ledger.jsonl（一行一筆 JSON，不進版控、不含對話內容與祕密）。

兩種紀錄：
- agent：一個子代理跑完一次。欄位 project、task、round（輪的名稱，如 "B-011 實作 r3"、"批次 25 規劃"）、stage、role、
  tokens、calls（工具呼叫）、duration_ms（可空）、budget（工具呼叫預算，可空）、outcome（ok／blocked／fail／pass）、
  rework（這次是不是為了重做先前階段）、note。
- wait：調度者停下來等使用者回答一次。欄位 project、task、round、reason。

只記數字與短標籤；note／reason 請寫成一句話，不放個資與祕密。
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from .config import Config
from .util import ConsoleError

LEDGER_FILE = "round-ledger.jsonl"
OUTCOMES = ("ok", "blocked", "fail", "pass")


def path(cfg: Config) -> Path:
    return cfg.runtime_dir / LEDGER_FILE


def _int(value, name: str, *, optional: bool = False):
    if value is None:
        if optional:
            return None
        raise ConsoleError(f"{name} 必填")
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ConsoleError(f"{name} 必須是 0 以上的整數")
    return value


def add(cfg: Config, kind: str, *, now: float | None = None, **fields) -> dict:
    """附加一筆。型別不對就拒絕，不默默修正。回傳寫入的紀錄。"""
    if kind not in ("agent", "wait"):
        raise ConsoleError("kind 必須是 agent 或 wait")
    rec: dict = {"ts": round(time.time() if now is None else now, 3), "kind": kind,
                 "project": str(fields.get("project") or ""), "task": str(fields.get("task") or ""),
                 "round": str(fields.get("round") or "")}
    if not rec["task"] or not rec["round"]:
        raise ConsoleError("task 與 round 必填")
    if kind == "agent":
        for key in ("stage", "role"):
            if not fields.get(key):
                raise ConsoleError(f"{key} 必填")
            rec[key] = str(fields[key])
        rec["tokens"] = _int(fields.get("tokens"), "tokens")
        rec["calls"] = _int(fields.get("calls"), "calls")
        rec["duration_ms"] = _int(fields.get("duration_ms"), "duration_ms", optional=True)
        rec["budget"] = _int(fields.get("budget"), "budget", optional=True)
        outcome = fields.get("outcome") or "ok"
        if outcome not in OUTCOMES:
            raise ConsoleError(f"outcome 必須是 {'／'.join(OUTCOMES)}")
        rec["outcome"] = outcome
        rec["rework"] = bool(fields.get("rework"))
    else:
        if not fields.get("reason"):
            raise ConsoleError("reason 必填")
        rec["reason"] = str(fields["reason"])
    if fields.get("note"):
        rec["note"] = str(fields["note"])[:200]
    p = path(cfg)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    os.chmod(p, 0o600)
    return rec


def load(cfg: Config) -> list[dict]:
    """讀全部紀錄；壞行略過（帳本是輔助資料，不能因為一行壞掉讓覆盤失敗）。"""
    try:
        lines = path(cfg).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(rec, dict) and rec.get("kind") in ("agent", "wait"):
            out.append(rec)
    return out


def _stats(recs: list[dict]) -> dict:
    agents = [r for r in recs if r["kind"] == "agent"]
    waits = [r for r in recs if r["kind"] == "wait"]
    tokens = sum(r.get("tokens", 0) for r in agents)
    rework = sum(r.get("tokens", 0) for r in agents if r.get("rework"))
    over = [r for r in agents if r.get("budget") and r.get("calls", 0) > r["budget"]]
    return {"agents": len(agents), "tokens": tokens, "calls": sum(r.get("calls", 0) for r in agents),
            "duration_ms": sum(r["duration_ms"] for r in agents if isinstance(r.get("duration_ms"), int)),
            "rework_tokens": rework, "rework_pct": round(100 * rework / tokens, 1) if tokens else 0.0,
            "blocked": sum(1 for r in agents if r.get("outcome") == "blocked"),
            "failed": sum(1 for r in agents if r.get("outcome") == "fail"),
            "over_budget": len(over), "waits": len(waits)}


def summarize(recs: list[dict]) -> dict:
    """彙總：總計、依輪、依階段、依角色、最貴的 5 筆、等使用者的原因。"""
    def group(key):
        out: dict[str, list[dict]] = {}
        for r in recs:
            if r["kind"] == "agent" or key == "round":
                out.setdefault(str(r.get(key, "")), []).append(r)
        return {k: _stats(v) for k, v in out.items()}
    agents = [r for r in recs if r["kind"] == "agent"]
    first = min((r["ts"] for r in recs), default=0)
    ordered_rounds = sorted({r["round"] for r in recs}, key=lambda n: min(x["ts"] for x in recs if x["round"] == n))
    by_round = group("round")
    return {"total": _stats(recs), "rounds": {n: by_round[n] for n in ordered_rounds},
            "by_stage": group("stage"), "by_role": group("role"),
            "costliest": [{k: r.get(k) for k in ("task", "round", "stage", "role", "tokens", "calls", "outcome", "rework")}
                          for r in sorted(agents, key=lambda r: -r.get("tokens", 0))[:5]],
            "waits": [{"round": r["round"], "task": r["task"], "reason": r["reason"]} for r in recs if r["kind"] == "wait"],
            "since": first}


def select(recs: list[dict], *, task: str = "", round_name: str = "", since: float = 0.0) -> list[dict]:
    return [r for r in recs if (not task or r.get("task") == task) and (not round_name or r.get("round") == round_name)
            and r.get("ts", 0) >= since]


DUE_TOKENS = 300_000     # 距上次覆盤累積到這麼多 token 就該派優化師
DUE_WAITS = 2            # 距上次覆盤停下來等使用者達到這麼多次


def due(recs: list[dict], *, tokens: int = DUE_TOKENS, waits: int = DUE_WAITS) -> dict:
    """該不該派流程優化師覆盤（使用者 2026-11-19 選：每輪調度者輕量覆盤，觸發條件才派優化師）。

    以最後一筆 stage=review 的紀錄為界，只看它之後的紀錄。觸發條件任一成立：有失敗或卡住、超出工具呼叫預算、
    停下來等使用者 >= waits 次、累積 token >= tokens。回傳 {"due": bool, "reasons": [...], "since": {...統計}}。"""
    last = max((r["ts"] for r in recs if r["kind"] == "agent" and r.get("stage") == "review"), default=0.0)
    recent = [r for r in recs if r["ts"] > last and not (r["kind"] == "agent" and r.get("stage") == "review")]
    st = _stats(recent)
    reasons = []
    if st["failed"] or st["blocked"]:
        reasons.append(f"失敗 {st['failed']}／卡住 {st['blocked']}")
    if st["over_budget"]:
        reasons.append(f"超出工具呼叫預算 {st['over_budget']} 次")
    if st["waits"] >= waits:
        reasons.append(f"停下來等使用者 {st['waits']} 次（≥{waits}）")
    if st["tokens"] >= tokens:
        reasons.append(f"累積 {st['tokens'] // 1000}k tokens（≥{tokens // 1000}k）")
    return {"due": bool(reasons), "reasons": reasons, "since": st}


def _k(n: int) -> str:
    return f"{n / 1000:.0f}k" if n >= 1000 else str(n)


def render(summary: dict) -> str:
    t = summary["total"]
    mins = t["duration_ms"] / 60000
    lines = [f"總計：{t['agents']} 次子代理、{_k(t['tokens'])} tokens、{t['calls']} 次工具呼叫、累計耗時 {mins:.0f} 分（只計有記錄的）",
             f"重工：{_k(t['rework_tokens'])} tokens（{t['rework_pct']}%）｜卡住 {t['blocked']} 次｜失敗 {t['failed']} 次｜"
             f"超出工具呼叫預算 {t['over_budget']} 次｜停下來等使用者 {t['waits']} 次", "", "各輪："]
    for name, s in summary["rounds"].items():
        lines.append(f"  {name}：{_k(s['tokens'])} tok／{s['calls']} 呼叫／重工 {s['rework_pct']}%／等使用者 {s['waits']} 次")
    lines += ["", "依階段（tokens／次數）："]
    for name, s in sorted(summary["by_stage"].items(), key=lambda kv: -kv[1]["tokens"]):
        lines.append(f"  {name}：{_k(s['tokens'])}／{s['agents']}")
    lines += ["", "最貴的 5 筆："]
    for r in summary["costliest"]:
        lines.append(f"  {_k(r['tokens'])}／{r['calls']} 呼叫　{r['round']}　{r['stage']}（{r['role']}）{r['outcome']}{' 重工' if r['rework'] else ''}")
    if summary["waits"]:
        lines += ["", "停下來等使用者："]
        lines += [f"  {w['round']}（{w['task']}）：{w['reason']}" for w in summary["waits"]]
    return "\n".join(lines)
