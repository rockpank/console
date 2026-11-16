"""worktree 管理：worktrees/<任務>/<專案別名>/，分支 <branch_prefix><任務>（預設 t-），起點 <remote>/<base_branch>。

不 checkout base 分支（它可能已被別的 worktree 占用），改用 fetch 後從遠端分支開新分支。
建立前先檢查這個任務是否處理過：本機或遠端已有同名分支就直接用那個分支（不從起點另開同名分支）；
兩邊都沒有才從起點開新分支。絕不 push、不 force、不刪分支。
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from . import envfile, registry, util
from .config import Config
from .util import ConsoleError, run, say, warn

_FINGERPRINT_MAX_FILE = 2_000_000  # 超過就只納入大小，不讀內容


def _repo(cfg: Config, alias: str) -> Path:
    repo = Path(cfg.project(alias)["repo"])
    if not (repo / ".git").exists():
        raise ConsoleError(f"專案 {alias} 的 repo 不是 git 目錄：{repo}")
    return repo


def _worktrees_of(repo: Path) -> list[dict]:
    out = run(["git", "-C", repo, "worktree", "list", "--porcelain"], mutating=False).stdout
    items, cur = [], {}
    for line in out.splitlines():
        if not line:
            if cur:
                items.append(cur)
            cur = {}
            continue
        key, _, value = line.partition(" ")
        cur[key] = value
    if cur:
        items.append(cur)
    return items


def add_worktree(cfg: Config, ticket: str, alias: str, *, fetch: bool = True) -> Path:
    proj = cfg.project(alias)
    repo = _repo(cfg, alias)
    remote, base = proj.get("remote", "origin"), proj.get("base_branch", "dev")
    branch = f"{proj.get('branch_prefix', 't-')}{ticket}"
    path = cfg.worktree_path(ticket, alias)

    if path.exists():
        current = run(["git", "-C", path, "branch", "--show-current"], mutating=False, check=False).stdout.strip()
        say(f"[{alias}] 已存在：{path}（分支 {current or '?'}），略過建立")
        return path

    for wt in _worktrees_of(repo):
        if wt.get("branch") == f"refs/heads/{branch}":
            raise ConsoleError(f"分支 {branch} 已在另一處檢出：{wt['worktree']}。請先處理該處，console 不會搶分支。")

    if fetch:
        say(f"[{alias}] git fetch {remote} {base} ...")
        run(["git", "-C", repo, "fetch", remote, base], timeout=300)
    start = f"{remote}/{base}"
    if not _ref_exists(repo, start):
        raise ConsoleError(f"找不到起點 {start}（可去掉 --no-fetch 先 fetch）")

    # 先檢查這個任務是否處理過：本機或遠端已有同名分支就直接用它，不從起點另開同名新分支
    prior = check_prior(cfg, ticket, alias, repo=repo, fetch=fetch)

    if not util.DRY_RUN:
        path.parent.mkdir(parents=True, exist_ok=True)
    if prior["source"] == "local":
        say(f"[{alias}] 這個任務處理過：本機已有分支 {branch}（{prior['head'][:9]}，領先 {start} {prior['commits_ahead_of_base']} 個提交），"
            "直接用它建立 worktree（不重設分支）")
        run(["git", "-C", repo, "worktree", "add", path, branch])
    elif prior["source"] == "remote":
        say(f"[{alias}] 這個任務處理過：遠端已有分支 {remote}/{branch}（{prior['head'][:9]}，領先 {start} {prior['commits_ahead_of_base']} 個提交），"
            "從它建立本機分支與 worktree")
        run(["git", "-C", repo, "worktree", "add", "--track", "-b", branch, path, f"{remote}/{branch}"])
    else:
        run(["git", "-C", repo, "worktree", "add", "--no-track", "-b", branch, path, start])
    say(f"[{alias}] worktree：{path}（分支 {branch}，{'沿用既有分支' if prior['source'] else '起點 ' + start}）")

    _report_divergence(alias, branch, remote, prior)
    _post_create(cfg, proj, ticket, alias, path)
    return path


def _ref_exists(repo: Path, ref: str) -> bool:
    return run(["git", "-C", repo, "rev-parse", "--verify", "-q", ref], check=False, mutating=False).returncode == 0


def check_prior(cfg: Config, ticket: str, alias: str, *, repo: Path | None = None, fetch: bool = True) -> dict:
    """這個任務是否處理過：看本機分支、遠端分支。

    fetch=True 時先用 ls-remote 問遠端有沒有同名分支（有才 fetch 那一個分支）；
    --no-fetch 只看本機已有的遠端追蹤資料。回傳的 source 是 "local"／"remote"／None。
    """
    proj = cfg.project(alias)
    repo = repo or _repo(cfg, alias)
    remote, base = proj.get("remote", "origin"), proj.get("base_branch", "dev")
    branch = f"{proj.get('branch_prefix', 't-')}{ticket}"
    start, remote_ref = f"{remote}/{base}", f"refs/remotes/{remote}/{branch}"

    if fetch:
        found = run(["git", "-C", repo, "ls-remote", "--exit-code", "--heads", remote, branch],
                    check=False, mutating=False, timeout=120)
        if found.returncode == 0:
            say(f"[{alias}] 遠端 {remote} 已有分支 {branch}，fetch ...")
            run(["git", "-C", repo, "fetch", remote, branch], timeout=300)
        elif found.returncode != 2:  # 2＝遠端沒有這個分支；其他是連線或權限問題，不能當成「沒處理過」
            detail = (found.stderr or found.stdout or "").strip()
            raise ConsoleError(f"[{alias}] 無法確認遠端 {remote} 有沒有分支 {branch}（結束碼 {found.returncode}）：{detail}\n"
                               "請確認網路與憑證，或加 --no-fetch 只看本機。")

    local, has_remote = _ref_exists(repo, f"refs/heads/{branch}"), _ref_exists(repo, remote_ref)
    source = "local" if local else "remote" if has_remote else None
    head = ""
    ahead_of_base, ahead_remote, behind_remote = 0, None, None
    if source:
        head = run(["git", "-C", repo, "rev-parse", f"refs/heads/{branch}" if local else remote_ref],
                   mutating=False).stdout.strip()
        ahead_of_base = int(run(["git", "-C", repo, "rev-list", "--count", f"{start}..{head}"], mutating=False).stdout.strip() or 0)
        if local and has_remote:
            left, right = run(["git", "-C", repo, "rev-list", "--left-right", "--count",
                               f"refs/heads/{branch}...{remote_ref}"], mutating=False).stdout.split()
            ahead_remote, behind_remote = int(left), int(right)
    return {
        "ticket": ticket, "project": alias, "branch": branch, "source": source, "head": head,
        "base_ref": start, "commits_ahead_of_base": ahead_of_base,
        "ahead_of_remote": ahead_remote, "behind_remote": behind_remote,
    }


def _report_divergence(alias: str, branch: str, remote: str, prior: dict) -> None:
    behind, ahead = prior["behind_remote"], prior["ahead_of_remote"]
    if not behind:
        return
    if ahead:
        warn(f"[{alias}] 本機 {branch} 與遠端 {remote}/{branch} 已分岔（本機多 {ahead}、遠端多 {behind} 個提交）。"
             "console 不會自動合併，請自行決定怎麼處理後再開工。")
    else:
        warn(f"[{alias}] 本機 {branch} 落後遠端 {remote}/{branch} {behind} 個提交，目前 worktree 是舊的。"
             f"請在 worktree 內自行 `git merge --ff-only {remote}/{branch}` 後再開工（console 不會動分支）。")


def seed_env_files(cfg: Config, ticket: str, alias: str, *, overwrite: bool = False) -> None:
    """把 config/env/<專案>/ 底下的環境檔複製進 worktree（權限 600）。

    - 來源不存在：略過並提示（不是錯誤）。
    - 目標已存在：預設不覆蓋（--overwrite 才覆蓋）。
    - 目標必須是 git 忽略的路徑，否則拒絕，避免祕密被 commit。
    - set 內的值原樣覆寫同名的鍵（不做占位符代換）。
    - 不印出任何值。
    """
    proj = cfg.project(alias)
    entries = proj.get("env_files", [])
    path = cfg.worktree_path(ticket, alias)
    if not entries:
        return
    if not path.exists():
        say(f"[{alias}] （worktree 尚未建立）略過環境檔複製")
        return
    for entry in entries:
        rel, src = entry["target"], cfg.resolve(entry["source"])
        dst = path / rel
        if not src.exists():
            say(f"[{alias}] 略過 {rel}：來源不存在 {entry['source']}（範本：{entry['source']}.example）")
            continue
        if dst.exists() and not overwrite:
            say(f"[{alias}] {rel} 已存在，略過（要覆蓋請加 --overwrite）")
            continue
        if run(["git", "-C", path, "check-ignore", "-q", rel], check=False, mutating=False).returncode != 0:
            warn(f"[{alias}] 拒絕寫入 {rel}：不是 git 忽略的路徑，可能被 commit")
            continue
        if src.stat().st_mode & 0o077:
            warn(f"[{alias}] 來源 {entry['source']} 對本人以外可讀，請 chmod 600")
        values = {str(k): str(v) for k, v in entry.get("set", {}).items()}
        text = envfile.render_with_overrides(src.read_text(encoding="utf-8"), values)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.touch(mode=0o600)
        dst.chmod(0o600)
        dst.write_text(text, encoding="utf-8")
        say(f"[{alias}] 已建立 {rel}（來源 {entry['source']}；自動覆寫：{', '.join(values) or '無'}）")


def _post_create(cfg: Config, proj: dict, ticket: str, alias: str, path: Path) -> None:
    if not path.exists():  # dry-run
        say(f"[{alias}] （dry-run）略過 skip-worktree 與環境檔複製")
        return
    for rel in proj.get("skip_worktree", []):
        files = run(["git", "-C", path, "ls-files", "-z", "--", rel], mutating=False).stdout
        if files:
            run(["git", "-C", path, "update-index", "--skip-worktree", "-z", "--stdin"], input=files)
            say(f"[{alias}] 已將 {rel}/ 標記為 skip-worktree（不追蹤、不 commit）")

    seed_env_files(cfg, ticket, alias)


def ensure_removable(cfg: Config, ticket: str, alias: str) -> None:
    """有未提交變更或未追蹤檔案就拒絕（被 .gitignore 忽略的檔案不算）。
    down 在拆站點、刪資料庫之前先呼叫，避免拆到一半才被 git 擋下。"""
    path = cfg.worktree_path(ticket, alias)
    if not path.exists():
        return
    dirty = dirty_count(path)
    if dirty:
        raise ConsoleError(
            f"[{alias}] worktree 有 {dirty} 個未提交或未追蹤的檔案，未移除任何東西：{path}\n"
            "請先 commit、搬走或自行處理（console 不使用 --force）。"
        )


def dirty_count(path: Path) -> int:
    """未提交或未追蹤的檔案數（被 .gitignore 忽略的不算）。"""
    out = run(["git", "-C", path, "status", "--porcelain"], mutating=False).stdout.strip()
    return len(out.splitlines()) if out else 0


def remove_worktree(cfg: Config, ticket: str, alias: str) -> None:
    repo = _repo(cfg, alias)
    path = cfg.worktree_path(ticket, alias)
    if not path.exists():
        say(f"[{alias}] 沒有 worktree：{path}")
        return
    # 不用 --force：有未提交變更時 git 會拒絕，避免弄丟工作
    run(["git", "-C", repo, "worktree", "remove", path])
    branch = f"{cfg.project(alias).get('branch_prefix', 't-')}{ticket}"
    say(f"[{alias}] 已移除 worktree：{path}（分支 {branch} 保留，需要的話自行刪除）")


def fingerprint(cfg: Config, ticket: str, alias: str) -> str:
    """工作樹指紋（唯讀）：HEAD、狀態、對 HEAD 的差異、未追蹤檔內容。
    dispatch 在唯讀角色（審查、驗證）前後各取一次，不一致代表有人改了工作樹。"""
    path = cfg.worktree_path(ticket, alias)
    if not path.exists():
        raise ConsoleError(f"[{alias}] 沒有 worktree：{path}")
    h = hashlib.sha256()
    h.update(run(["git", "-C", path, "rev-parse", "HEAD"], mutating=False).stdout.encode())
    h.update(run(["git", "-C", path, "status", "--porcelain", "--untracked-files=all"], mutating=False).stdout.encode())
    h.update(run(["git", "-C", path, "diff", "HEAD"], mutating=False).stdout.encode())
    untracked = run(["git", "-C", path, "ls-files", "-o", "--exclude-standard", "-z"], mutating=False).stdout
    for rel in sorted(filter(None, untracked.split("\0"))):
        h.update(rel.encode())
        try:
            size = (path / rel).stat().st_size
            h.update(str(size).encode())
            if size <= _FINGERPRINT_MAX_FILE:
                h.update((path / rel).read_bytes())
        except OSError:
            pass
    return h.hexdigest()


def list_worktrees(cfg: Config) -> None:
    root = cfg.worktree_root
    sites = registry.load(cfg)
    rows = []
    if root.exists():
        for ticket_dir in sorted(p for p in root.iterdir() if p.is_dir()):
            for wt in sorted(p for p in ticket_dir.iterdir() if p.is_dir() and p.name != "_ticket"):
                branch = run(["git", "-C", wt, "branch", "--show-current"], check=False, mutating=False).stdout.strip()
                dirty = run(["git", "-C", wt, "status", "--porcelain", "--untracked-files=no"],
                            check=False, mutating=False).stdout.strip()
                site = sites.get(registry.key(ticket_dir.name, wt.name), {}).get("url", "—")
                rows.append((ticket_dir.name, wt.name, branch or "?", f"{len(dirty.splitlines())} 檔" if dirty else "乾淨", site))
    if not rows:
        say("（目前沒有 worktree）")
        return
    say(f"{'任務':<8}{'專案':<14}{'分支':<12}{'未提交':<8}站點")
    for row in rows:
        say(f"{row[0]:<8}{row[1]:<14}{row[2]:<12}{row[3]:<8}{row[4]}")
