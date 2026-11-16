"""個資掃描：給「個資守門員」用。

掃描三個來源：工單資料夾裡由角色寫的報告、worktree 相對起點的新增行（含未提交與未追蹤檔）、
起點之後的 commit 訊息。只回報「哪裡、哪一類」與**遮蔽後**的片段，絕不印出命中的原文。
規則與 mask.py 相同，只能抓格式固定的個資；自由文字的客戶名稱要靠 config/mask_terms.txt。
"""
from __future__ import annotations

import re
from pathlib import Path

from . import mask
from .config import Config
from .util import ConsoleError, run, say

_REPORT_SUFFIXES = {".md", ".json", ".txt"}
_SKIP_NAMES = {"masked.md"}          # console 已遮蔽
_SKIP_DIRS = {"attachments"}         # 附件另有遮蔽流程
_MAX_FILE_BYTES = 1_000_000
_EXCERPT = 100
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

Hit = tuple[str, int, list[str], str]  # (來源, 行號, 類別, 遮蔽後片段)


def added_lines(diff_text: str):
    """解析 `git diff --unified=0`，產生 (路徑, 新檔行號, 內容)；只含新增行。"""
    path, lineno = None, 0
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            target = line[4:]
            path = None if target == "/dev/null" else (target[2:] if target.startswith("b/") else target)
        elif line.startswith("@@"):
            m = _HUNK.match(line)
            lineno = int(m.group(1)) if m else 0
        elif line.startswith("+") and not line.startswith("+++") and path:
            yield path, lineno, line[1:]
            lineno += 1


def scan_lines(source: str, lines) -> list[Hit]:
    hits: list[Hit] = []
    for no, text in lines:
        cats = mask.detect(text)
        if cats:
            hits.append((source, no, cats, mask.mask_text(text).strip()[:_EXCERPT]))
    return hits


def _text_of(path: Path) -> str | None:
    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    return data.decode("utf-8", errors="replace")


def scan_ticket_files(ticket_dir: Path) -> tuple[int, list[Hit]]:
    """掃描 _ticket/ 下角色寫的報告（不含 masked.md、附件、站點資訊）。"""
    root = ticket_dir / "_ticket"
    hits: list[Hit] = []
    count = 0
    if not root.exists():
        return 0, hits
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if (not path.is_file() or path.suffix not in _REPORT_SUFFIXES or path.name in _SKIP_NAMES
                or path.name.startswith("site-") or _SKIP_DIRS & set(rel.parts)):
            continue
        text = _text_of(path)
        if text is None:
            continue
        count += 1
        hits += scan_lines(f"_ticket/{rel}", enumerate(text.splitlines(), 1))
    return count, hits


def scan_worktree(path: Path, start: str) -> tuple[int, list[Hit]]:
    """掃描 worktree 相對 start 的新增行、未追蹤檔、start 之後的 commit 訊息。"""
    hits: list[Hit] = []
    sources = 0
    diff = run(["git", "-c", "core.quotepath=false", "-C", path, "diff", "--unified=0", "--no-color",
                "--no-ext-diff", start, "--"], mutating=False).stdout
    by_file: dict[str, list[tuple[int, str]]] = {}
    for rel, no, text in added_lines(diff):
        by_file.setdefault(rel, []).append((no, text))
    for rel, lines in by_file.items():
        sources += 1
        hits += scan_lines(rel, lines)

    untracked = run(["git", "-c", "core.quotepath=false", "-C", path, "ls-files", "-o", "--exclude-standard"],
                    mutating=False).stdout.splitlines()
    for rel in untracked:
        text = _text_of(path / rel)
        if text is None:
            continue
        sources += 1
        hits += scan_lines(rel, enumerate(text.splitlines(), 1))

    log = run(["git", "-C", path, "log", "--format=%h%x00%B%x1e", f"{start}..HEAD"], mutating=False).stdout
    for entry in filter(str.strip, log.split("\x1e")):
        short, _, body = entry.strip("\n").partition("\0")
        sources += 1
        hits += scan_lines(f"commit {short.strip()}", enumerate(body.splitlines(), 1))
    return sources, hits


def scan_ticket(cfg: Config, ticket: str, aliases: list[str]) -> int:
    mask.load_terms(cfg.mask_terms_file)
    say("（只列位置、類別與遮蔽後片段；命中原文不會顯示）")
    total_sources, all_hits = 0, []

    count, hits = scan_ticket_files(cfg.ticket_dir(ticket))
    total_sources += count
    all_hits += hits

    for alias in aliases:
        proj = cfg.project(alias)
        path = cfg.worktree_path(ticket, alias)
        if not path.exists():
            raise ConsoleError(f"[{alias}] 沒有 worktree：{path}")
        start = f"{proj.get('remote', 'origin')}/{proj.get('base_branch', 'dev')}"
        if run(["git", "-C", path, "rev-parse", "--verify", "-q", start], check=False, mutating=False).returncode != 0:
            raise ConsoleError(f"[{alias}] 找不到起點 {start}，無法界定要掃描的變更範圍")
        count, hits = scan_worktree(path, start)
        total_sources += count
        all_hits += [(f"{alias}:{src}", no, cats, ex) for src, no, cats, ex in hits]

    for src, no, cats, excerpt in all_hits:
        say(f"{src}:{no}  {''.join(cats)}  {excerpt}")
    say(f"掃描 {total_sources} 個來源，疑似 {len(all_hits)} 處")
    return 1 if all_hits else 0
