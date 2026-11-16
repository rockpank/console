"""回頭調整：驗收後要再調整的工單，開新一輪。`bin/console reopen <工單> [-p 專案]`

做四件事（都不刪任何東西）：
1. 前一輪的交接檔封存到 `_ticket/round-<N>/`（摘要、裁決、分析、審查、個資報告、升級報告、舊的回頭調整標記；
   遮蔽後的工單複製一份）。附件留在原處，重新抓工單時會一併更新。
2. 為既有分支寫新的 `prior-<專案>.json`，本輪起點 ＝ 分支目前的提交（worktree 還在也一樣）。
3. 階段退回「待讀取」，嚴重度清掉：要重新抓 Redmine 才讀得到驗收後的新留言，所以不是「已讀取」。
4. 歷程補一筆說明（`status.json` 仍只經由 `status.set_status` 寫入）。

只有「待人工交付／已釋放」的工單能開新一輪；進行中的請用 /dispatch resume。
worktree 有未提交變更就整個拒絕（前一輪成果得在分支提交上，本輪起點才算得準），拒絕時什麼都不動。
"""
from __future__ import annotations

import shutil
from pathlib import Path

from . import status, util, worktree
from .config import Config
from .util import ConsoleError, say, warn

MOVE_NAMES = ["summary.md", "decision.md", "escalation.md", "implementation.md", "analysis"]
MOVE_GLOBS = ["review-*.md", "pii-*.md", "prior-*.json", "landed-*.json"]
COPY_NAMES = ["masked.md"]  # 重新抓工單會覆蓋它，所以複製留底而不是搬走


def _ticket_dir(cfg: Config, ticket: str) -> Path:
    return cfg.ticket_dir(ticket) / "_ticket"


def round_number(cfg: Config, ticket: str) -> int:
    """目前是第幾輪：已封存的 round-N 最大號加一（沒封存過就是第 1 輪）。"""
    nums = [int(p.name[6:]) for p in _ticket_dir(cfg, ticket).glob("round-*") if p.is_dir() and p.name[6:].isdigit()]
    return max(nums, default=0) + 1


def reopen_ticket(cfg: Config, ticket: str, aliases: list[str] | None = None, *, fetch: bool = True) -> int:
    """開新一輪，回傳新一輪的編號。"""
    data = status.load(status.status_file(cfg, ticket))
    if not data:
        raise ConsoleError(f"工單 {ticket} 沒有進度紀錄，不是回頭調整；請直接用 /dispatch {ticket}")
    stage = data.get("stage", "?")
    if stage not in status.FINISHED:
        raise ConsoleError(f"工單 {ticket} 目前階段是「{stage}」，只有{'、'.join(sorted(status.FINISHED))}可以開新一輪；"
                           "進行中的請用 /dispatch resume。")
    aliases = aliases or [str(p) for p in data.get("projects", [])]
    if not aliases:
        raise ConsoleError(f"工單 {ticket} 沒有專案紀錄，請用 -p 指定專案別名")
    for alias in aliases:
        cfg.project(alias)  # 未登錄的別名先擋

    # 先全部檢查（會碰網路的也先做），任何一項不過就什麼都不動
    for alias in aliases:
        worktree.ensure_clean(cfg, ticket, alias, "開新一輪")
    priors = {alias: worktree.check_prior(cfg, ticket, alias, fetch=fetch) for alias in aliases}

    td = _ticket_dir(cfg, ticket)
    archived = round_number(cfg, ticket)
    new_round = archived + 1
    dest = td / f"round-{archived}"
    if dest.exists():
        raise ConsoleError(f"{dest} 已存在，請先自行確認（console 不覆蓋封存檔）")
    moves = [td / n for n in MOVE_NAMES if (td / n).exists()] + [p for g in MOVE_GLOBS for p in sorted(td.glob(g))]
    copies = [td / n for n in COPY_NAMES if (td / n).exists()]
    say(f"工單 {ticket}：第 {archived} 輪交接檔 → {dest.name}/（{'、'.join(p.name for p in moves + copies) or '無檔案'}）")
    if util.DRY_RUN:
        say("[dry-run] 不搬檔")
    else:
        dest.mkdir(parents=True)
        for p in moves:
            shutil.move(str(p), str(dest / p.name))
        for p in copies:
            shutil.copy2(p, dest / p.name)

    for alias, prior in priors.items():
        if prior["source"]:
            worktree.record_prior(cfg, ticket, alias, prior, replace=True)
        else:
            warn(f"[{alias}] 本機與遠端都找不到分支 {prior['branch']}，沒有可沿用的前一輪成果；"
                 f"下次 `bin/console up` 會從 {prior['base_ref']} 開新分支")

    note = f"回頭調整：第 {new_round} 輪開始（前一輪封存於 {dest.name}）"
    if util.DRY_RUN:
        say(f"[dry-run] 階段 → 待讀取，備註：{note}")
    else:
        status.set_status(cfg, ticket, "待讀取", note=note, projects=aliases, reset_severity=True)
    say(f"下一步：/dispatch {ticket}（從階段 1 重新讀工單；前一輪的檔案只當背景）")
    return new_round
