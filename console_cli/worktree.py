"""worktree 管理：worktrees/<任務>/<專案別名>/，分支 <branch_prefix><任務>（預設 t-），起點 <remote>/<base_branch>。

不 checkout base 分支（它可能已被別的 worktree 占用），改用 fetch 後從遠端分支開新分支。
建立前先檢查這個任務是否處理過：本機或遠端已有同名分支就直接用那個分支（不從起點另開同名分支）；
兩邊都沒有才從起點開新分支。絕不 push、不 force、不刪分支。
"""
from __future__ import annotations

import hashlib
import json
import os
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
    start = _pick_start(repo, alias, remote, base, start)

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
    _remind_git_identity(repo, alias)
    return path


def _remind_git_identity(repo: Path, alias: str) -> None:
    """repo 沒設 git 身分時只提示一行（不自動設定、不失敗）。"""
    for key in ("user.name", "user.email"):
        if not run(["git", "-C", repo, "config", key], check=False, mutating=False).stdout.strip():
            say(f"[{alias}] 提醒：repo 未設 git 身分（{key}），commit 會失敗；merge-manager 會沿用歷史作者設本地設定")
            return


def _pick_start(repo: Path, alias: str, remote: str, base: str, remote_ref: str) -> str:
    """起點：本機 base 分支「完全包含」遠端 base 且領先時，用本機 base，否則用遠端 base。

    使用者在本機合併、不 push 的情況下，遠端 base 會落後；從遠端開會讓新任務缺少已合併的程式。
    本機 base 與遠端分岔（遠端有本機沒有的提交）時不猜，沿用遠端並警告。只讀 ref，不 checkout、不移動任何分支。
    """
    if not _ref_exists(repo, f"refs/heads/{base}"):
        return remote_ref
    local = run(["git", "-C", repo, "rev-parse", f"refs/heads/{base}"], mutating=False).stdout.strip()
    remote_head = run(["git", "-C", repo, "rev-parse", remote_ref], mutating=False).stdout.strip()
    if local == remote_head:
        return remote_ref
    local_has_remote = run(["git", "-C", repo, "merge-base", "--is-ancestor", remote_head, local],
                           mutating=False, check=False).returncode == 0
    if local_has_remote:
        ahead = run(["git", "-C", repo, "rev-list", "--count", f"{remote_ref}..{base}"], mutating=False).stdout.strip()
        say(f"[{alias}] 本機 {base} 領先 {remote_ref} {ahead} 個提交（已合併但未推送），改以本機 {base} 為起點")
        return base
    if run(["git", "-C", repo, "merge-base", "--is-ancestor", local, remote_head], mutating=False, check=False).returncode == 0:
        return remote_ref  # 本機只是落後遠端，不是分岔
    warn(f"[{alias}] 本機 {base} 與 {remote_ref} 分岔（遠端有本機沒有的提交），仍以 {remote_ref} 為起點；請先處理分岔")
    return remote_ref


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


def foreign_or_unwritable(path: Path, limit: int = 5) -> list[str]:
    """worktree 內不屬於目前使用者、或不可寫的檔案／目錄（不跟隨 symlink；最多回傳 limit 個）。
    容器以 root 建出的檔案會讓 git worktree remove 做到一半失敗，所以移除前先掃。"""
    found: list[str] = []
    uid = os.getuid()

    def bad(p: str) -> bool:
        try:
            st = os.lstat(p)
        except OSError:
            return True
        if os.path.islink(p):
            return st.st_uid != uid
        return st.st_uid != uid or not os.access(p, os.W_OK)

    for root, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            full = os.path.join(root, name)
            if bad(full):
                found.append(full)
                if len(found) >= limit:
                    return found
    return found


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
    bad = foreign_or_unwritable(path)
    if bad:
        raise ConsoleError(
            f"[{alias}] worktree 內有不屬於目前使用者或不可寫的檔案，未移除任何東西：{path}\n"
            + "\n".join(f"  {b}" for b in bad)
            + "\n請在容器內清理或請有權限者處理後重試；不要半移除。")
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
