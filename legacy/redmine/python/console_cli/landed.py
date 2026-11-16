"""已併入偵測：重派的工單，成果可能早就在 base（dev）上，只剩些微調整。`bin/console landed <工單> [-p 專案]`

只收集「證據」，不下結論；結論由分析師對照程式碼現況判斷。寫 `_ticket/landed-<專案>.json`（只有這個指令會寫）：
- `branch_merged`：r-<工單> 分支的提交都已是 base 的祖先（一般 merge）。
- `branch_patch_equivalent`：分支每個提交都在 base 找得到內容相同的提交（rebase／cherry-pick）。
- `base_commits`／`base_files`：base 上提交訊息提到這張工單號碼的提交數與涉及的檔案（只取檔名與短 hash，
  **不取提交主旨**，主旨可能夾帶客戶名稱）。
- `last_landed_at`：base 上最新一個提到本工單的提交時間；工單留言晚於這個時間的，才是「併入之後的新要求」。
- `level`：`merged`（base 上有提到工單的提交，且分支已整個併入）／`mentioned`（有提到工單的提交，但分支沒併入或不存在）／`none`（沒有提到工單的提交；空分支也算 none）。

squash merge 會讓前兩項都是 false，所以另外用工單號碼比對 base 的提交訊息補強；比對不到不代表沒併入，
所以 `none` 時會刪掉舊檔，流程照常走完整路徑。
"""
from __future__ import annotations

import json
import re
from datetime import datetime

from . import util, worktree
from .config import Config
from .util import run, say

MAX_COMMITS = 50
MAX_FILES = 40


def _pattern(prefix: str, ticket: str) -> str:
    """提交訊息中的工單寫法：#4059、r-4059、redmine 4059；後面不可再接數字（避免 #40591 誤中）。"""
    return rf"(#|{re.escape(prefix)}|redmine[ #_-]*){re.escape(ticket)}([^0-9]|$)"


def _lines(out: str) -> list[str]:
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def landed_file(cfg: Config, ticket: str, alias: str):
    return cfg.ticket_dir(ticket) / "_ticket" / f"landed-{alias}.json"


def detect(cfg: Config, ticket: str, alias: str, *, fetch: bool = True) -> dict:
    proj = cfg.project(alias)
    repo = worktree._repo(cfg, alias)
    remote, base = proj.get("remote", "origin"), proj.get("base_branch", "dev")
    prefix = proj.get("branch_prefix", "r-")
    start = f"{remote}/{base}"
    if fetch:
        run(["git", "-C", repo, "fetch", remote, base], timeout=300)
    if not worktree._ref_exists(repo, start):
        raise util.ConsoleError(f"找不到起點 {start}（可去掉 --no-fetch 先 fetch）")

    prior = worktree.check_prior(cfg, ticket, alias, repo=repo, fetch=fetch)
    merged = equivalent = False
    if prior["source"]:
        head = prior["head"]
        merged = run(["git", "-C", repo, "merge-base", "--is-ancestor", head, start],
                     check=False, mutating=False).returncode == 0
        if not merged:
            cherry = _lines(run(["git", "-C", repo, "cherry", start, head], check=False, mutating=False).stdout)
            equivalent = bool(cherry) and all(ln.startswith("-") for ln in cherry)

    hashes = _lines(run(["git", "-C", repo, "rev-list", "--extended-regexp", "--regexp-ignore-case",
                         f"--grep={_pattern(prefix, ticket)}", f"--max-count={MAX_COMMITS}", start],
                        check=False, mutating=False).stdout)
    files: list[str] = []
    last_at = ""
    if hashes:
        last_at = run(["git", "-C", repo, "log", "--no-walk", "--format=%cI", hashes[0]],
                      check=False, mutating=False).stdout.strip()   # 只取時間，用來分辨哪些留言是併入之後才寫的
        # --format= 讓 log 不輸出任何訊息文字，只剩檔名
        names = run(["git", "-C", repo, "log", "--no-walk", "--format=", "--name-only", *hashes],
                    check=False, mutating=False).stdout
        files = sorted(set(_lines(names)))

    # 沒有任何提交提到工單號時一律算 none：空分支（從 base 切出、還沒有自己的提交）本來就是 base 的祖先，
    # 光靠「分支已併入」會把它誤判成已併入。
    level = "none" if not hashes else "merged" if (merged or equivalent) and prior["source"] else "mentioned"
    return {
        "ticket": ticket, "project": alias, "branch": prior["branch"], "base_ref": start, "level": level,
        "branch_exists": bool(prior["source"]), "branch_head": prior["head"][:9] if prior["head"] else "",
        "branch_merged": merged, "branch_patch_equivalent": equivalent,
        "base_commits": len(hashes), "last_landed_at": last_at, "base_commit_ids": [h[:9] for h in hashes[:10]],
        "base_files": files[:MAX_FILES], "base_files_truncated": len(files) > MAX_FILES,
        "base_head": run(["git", "-C", repo, "rev-parse", start], mutating=False).stdout.strip()[:9],
    }


def record(cfg: Config, ticket: str, alias: str, *, fetch: bool = True) -> dict:
    info = detect(cfg, ticket, alias, fetch=fetch)
    path = landed_file(cfg, ticket, alias)
    if info["level"] == "none":
        if path.exists() and not util.DRY_RUN:
            path.unlink()
        say(f"[{alias}] 未偵測到已併入 {info['base_ref']} 的成果，照完整流程走")
        return info
    summary = (f"[{alias}] 疑似已併入 {info['base_ref']}（{info['level']}）："
               f"分支{'已' if info['branch_merged'] or info['branch_patch_equivalent'] else '未'}併入、"
               f"base 上提到本工單的提交 {info['base_commits']} 個、涉及 {len(info['base_files'])} 個檔案")
    if util.DRY_RUN:
        say(f"[dry-run] {summary}；會寫入 {path.name}")
        return info
    path.parent.mkdir(parents=True, exist_ok=True)
    data = dict(info, at=datetime.now().astimezone().isoformat(timespec="seconds"))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    say(summary)
    say(f"[{alias}] 已寫入 {path.name}（涉及檔案清單在檔內；請分析師先對照現況找出「還差什麼」）")
    return info
