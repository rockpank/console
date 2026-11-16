"""worktree 建立流程的「先檢查是否處理過」測試。

用暫存目錄裡的真 git（bare 遠端＋本機 clone＋另一個 clone 代表別人推上去的分支），
不碰真實專案 repo、Redmine、docker。
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from console_cli import worktree  # noqa: E402
from console_cli.config import Config  # noqa: E402
from console_cli.util import ConsoleError  # noqa: E402


def git(path, *args):
    return subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, text=True).stdout.strip()


def commit(path, name):
    (Path(path) / name).write_text(name, encoding="utf-8")
    git(path, "add", name)
    git(path, "commit", "-q", "-m", f"add {name}")
    return git(path, "rev-parse", "HEAD")


class PriorBase(unittest.TestCase):
    def setUp(self):
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com", "GIT_COMMITTER_NAME": "t",
               "GIT_COMMITTER_EMAIL": "t@example.com", "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.origin, self.repo, self.other = root / "origin.git", root / "clone", root / "other"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "dev", str(self.origin)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "dev", str(self.repo)], check=True)
        git(self.repo, "remote", "add", "origin", str(self.origin))
        self.dev = commit(self.repo, "base.txt")
        git(self.repo, "push", "-q", "origin", "dev")
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.other)], check=True)
        git(self.other, "checkout", "-q", "dev")
        self.cfg = Config({
            "console": {"worktree_root": str(root / "wt"), "runtime_dir": str(root / "rt")},
            "projects": {"p": {"repo": str(self.repo), "remote": "origin", "base_branch": "dev"}},
        })
        self.warned: list[str] = []
        warn = mock.patch.object(worktree, "warn", side_effect=self.warned.append)
        warn.start()
        self.addCleanup(warn.stop)

    def add(self, ticket, **kw):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            path = worktree.add_worktree(self.cfg, ticket, "p", **kw)
        self.output = out.getvalue()
        return path

    def remove(self, ticket):
        with contextlib.redirect_stdout(io.StringIO()):
            worktree.remove_worktree(self.cfg, ticket, "p")

    def local_branch(self, name, *files):
        """在 clone 內建立本機分支 name 並提交 files，回到 dev；回傳分支最新提交。"""
        git(self.repo, "checkout", "-q", "-b", name, "dev")
        head = None
        for f in files:
            head = commit(self.repo, f)
        git(self.repo, "checkout", "-q", "dev")
        return head

    def remote_branch(self, name, *files):
        """在另一個 clone 建立分支並推到遠端（代表別人／別台機器的成果）。"""
        git(self.other, "checkout", "-q", "-B", name, "origin/dev")
        head = None
        for f in files:
            head = commit(self.other, f)
        git(self.other, "push", "-q", "origin", name)
        git(self.other, "checkout", "-q", "dev")
        return head


class FreshTicketTests(PriorBase):
    def test_new_task_branches_from_base(self):
        path = self.add("1")
        self.assertEqual(git(path, "rev-parse", "HEAD"), self.dev)
        self.assertEqual(git(path, "branch", "--show-current"), "t-1")
        self.assertNotIn("處理過", self.output)
        self.assertEqual(self.warned, [])


class BranchReuseTests(PriorBase):
    def test_local_branch_is_reused(self):
        head = self.local_branch("t-2", "a.txt")
        path = self.add("2")
        self.assertEqual(git(path, "branch", "--show-current"), "t-2")
        self.assertEqual(git(path, "rev-parse", "HEAD"), head)  # 沒被重設到起點
        self.assertIn("這個任務處理過：本機已有分支", self.output)
        self.assertEqual(self.warned, [])

    def test_remote_only_branch_becomes_tracking_local_branch(self):
        head = self.remote_branch("t-3", "b.txt", "c.txt")
        self.assertEqual(subprocess.run(["git", "-C", str(self.repo), "rev-parse", "-q", "--verify", "refs/heads/t-3"],
                                        capture_output=True).returncode, 1)  # 本機原本沒有
        path = self.add("3")
        self.assertEqual(git(path, "rev-parse", "HEAD"), head)
        self.assertEqual(git(path, "rev-parse", "--abbrev-ref", "t-3@{upstream}"), "origin/t-3")
        self.assertIn("遠端已有分支", self.output)

    def test_local_behind_remote_warns_and_never_moves_branch(self):
        self.local_branch("t-4")  # 本機分支停在 dev（沒有新提交）
        self.remote_branch("t-4", "a.txt")  # 遠端的 t-4 比它多一個提交 → 本機落後 1
        path = self.add("4")
        self.assertEqual(git(path, "rev-parse", "HEAD"), self.dev)  # 仍在舊位置，沒被快轉
        self.assertTrue(any("落後遠端" in w and "--ff-only" in w for w in self.warned))

    def test_diverged_branch_warns(self):
        self.local_branch("t-5", "local.txt")
        self.remote_branch("t-5", "remote.txt")
        path = self.add("5")
        self.assertEqual(git(path, "log", "-1", "--format=%s"), "add local.txt")
        self.assertTrue(any("分岔" in w for w in self.warned))

    def test_no_fetch_only_sees_local_knowledge(self):
        self.remote_branch("t-6", "x.txt")
        path = self.add("6", fetch=False)  # 沒問遠端，本機也沒有追蹤資料 → 視為沒處理過（--no-fetch 的限制）
        self.assertEqual(git(path, "rev-parse", "HEAD"), self.dev)

    def test_unknown_remote_state_is_fatal_not_treated_as_fresh(self):
        real = worktree.run

        def fake(cmd, **kw):
            if "ls-remote" in cmd:
                return subprocess.CompletedProcess(cmd, 128, "", "network down")
            return real(cmd, **kw)

        with mock.patch.object(worktree, "run", side_effect=fake):
            with self.assertRaises(ConsoleError) as ctx:
                self.add("9")
        self.assertIn("無法確認遠端", str(ctx.exception))
        self.assertFalse(self.cfg.worktree_path("9", "p").exists())
        self.assertEqual(subprocess.run(["git", "-C", str(self.repo), "rev-parse", "-q", "--verify", "refs/heads/t-9"],
                                        capture_output=True).returncode, 1)  # 沒有偷偷開出新分支


if __name__ == "__main__":
    unittest.main()
