"""工單進度狀態：worktrees/<工單>/_ticket/status.json。

階段轉換由 /dispatch 透過 `bin/console status <工單> --set <階段>` 寫入，角色不手寫 JSON；
`bin/console status`（不帶工單）列出全部工單的進度，給專案管理員與使用者看。
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from . import mask
from .config import Config
from .util import ConsoleError, say

STAGES = ["待讀取", "已讀取", "分析中", "已裁決", "待spec", "實作中", "審查中", "個資掃描",
          "待人工交付", "已升級", "已釋放"]
SEVERITIES = ["低", "中", "高"]
FINISHED = {"待人工交付", "已釋放"}
STALE_AFTER = timedelta(hours=24)
_NOTE_MAX = 200


def status_file(cfg: Config, ticket: str) -> Path:
    return cfg.ticket_dir(ticket) / "_ticket" / "status.json"


def _now() -> datetime:
    return datetime.now().astimezone()


def load(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as exc:
        raise ConsoleError(f"status.json 讀取失敗：{path}（{exc}）") from exc
    return data if isinstance(data, dict) else None


def set_status(cfg: Config, ticket: str, stage: str, *, severity: str | None = None,
               note: str = "", projects: list[str] | None = None, now: datetime | None = None,
               reset_severity: bool = False) -> dict:
    if stage not in STAGES:
        raise ConsoleError(f"未知階段：{stage}。可用：{'、'.join(STAGES)}")
    if severity is not None and severity not in SEVERITIES:
        raise ConsoleError(f"未知嚴重度：{severity}。可用：{'、'.join(SEVERITIES)}")
    mask.load_terms(cfg.mask_terms_file)
    path = status_file(cfg, ticket)
    data = load(path) or {"ticket": ticket, "history": []}
    stamp = (now or _now()).isoformat(timespec="seconds")
    note = mask.mask_text(note).replace("\n", " ").strip()[:_NOTE_MAX]  # 備註也過一次遮蔽
    data.update(ticket=ticket, stage=stage, updated=stamp)
    if projects:
        data["projects"] = projects
    if reset_severity:  # 開新一輪（bin/console reopen）：上一輪的嚴重度不帶過來
        data.pop("severity", None)
    if severity is not None:
        data["severity"] = severity
    data.setdefault("history", []).append({"stage": stage, "at": stamp, "note": note})
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".status-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    say(f"工單 {ticket}：{stage}" + (f"（嚴重度 {data['severity']}）" if data.get("severity") else ""))
    return data


def show(cfg: Config, ticket: str) -> None:
    data = load(status_file(cfg, ticket))
    if not data:
        say(f"工單 {ticket}：尚無狀態紀錄")
        return
    say(f"工單 {ticket}：{data.get('stage', '?')}  嚴重度 {data.get('severity', '—')}  更新 {data.get('updated', '?')}")
    for item in data.get("history", []):
        say(f"  {item.get('at', '?')}  {item.get('stage', '?')}  {item.get('note', '')}".rstrip())


def _row(data: dict, now: datetime) -> tuple:
    stage = data.get("stage", "?")
    try:
        updated = datetime.fromisoformat(data["updated"])
        stale = stage not in FINISHED and now - updated > STALE_AFTER
    except (KeyError, ValueError):
        stale = False
    last = (data.get("history") or [{}])[-1].get("note", "")
    return (
        0 if stage == "已升級" else 1,  # 需要使用者處理的排最前
        str(data.get("ticket", "?")),
        ",".join(data.get("projects", [])) or "—",
        stage + ("（久未動）" if stale else ""),
        data.get("severity", "—"),
        data.get("updated", "—"),
        last,
    )


def list_all(cfg: Config, now: datetime | None = None) -> list[tuple]:
    now = now or _now()
    rows = []
    root = cfg.worktree_root
    if root.exists():
        for path in sorted(root.glob("*/_ticket/status.json")):
            data = load(path)
            if data:
                rows.append(_row(data, now))
    rows.sort(key=lambda r: (r[0], r[1]))
    if not rows:
        say("（目前沒有工單進度紀錄）")
        return rows
    say(f"{'工單':<8}{'專案':<12}{'階段':<14}{'嚴重度':<8}{'更新':<27}備註")
    for _, ticket, proj, stage, sev, updated, note in rows:
        say(f"{ticket:<8}{proj:<12}{stage:<14}{sev:<8}{updated:<27}{note}")
    return rows
