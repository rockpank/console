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

from console_cli import status, worktree  # noqa: E402
from console_cli.config import Config  # noqa: E402
from console_cli.util import ConsoleError  # noqa: E402


def git(path, *args):
    return subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, text=True).stdout.strip()


def commit(path, name):
    (Path(path) / name).write_text(name, encoding="utf-8")
    git(path, "add", name)
    git(path, "commit", "-q", "-m", f"add {name}")
    return git(path, "rev-parse", "HEAD")


class MarkerLifecycleTests(PriorBase):
    def advance(self, branch, name):
        git(self.repo, "checkout", "-q", branch)
        head = commit(self.repo, name)
        git(self.repo, "checkout", "-q", "dev")
        return head

    def test_marker_kept_within_a_round_and_replaced_for_a_new_round(self):
        first = self.local_branch("r-10", "a.txt")
        self.add("10")
        self.remove("10")
        self.advance("r-10", "b.txt")  # 同一輪內 down 之後分支又前進
        self.add("10")
        self.assertEqual(self.marker("10")["head"], first)  # 沿用，本輪起點不變
        self.assertIn("沿用既有標記", self.output)

        self.remove("10")
        status.set_status(self.cfg, "10", "待人工交付", projects=["p"])  # 上一輪已結束 → 新的一輪
        newer = self.advance("r-10", "c.txt")
        self.add("10")
        self.assertEqual(self.marker("10")["head"], newer)
        self.assertEqual(self.marker("10")["previous_stage"], "待人工交付")

    def test_dry_run_writes_nothing(self):
        from console_cli import util
        self.local_branch("r-11", "a.txt")
        util.set_dry_run(True)
        self.addCleanup(util.set_dry_run, False)
        self.add("11")
        self.assertIsNone(self.marker("11"))
        self.assertFalse(self.cfg.worktree_path("11", "p").exists())
        self.assertIn("dry-run", self.output)


class ReopenRoundTests(PriorBase):
    """bin/console reopen：驗收後開新一輪。"""

    def td(self, ticket):
        d = self.cfg.ticket_dir(ticket) / "_ticket"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def finished_ticket(self, ticket, *, severity="低"):
        """前一輪完整跑完的工單：有交接檔、狀態待人工交付。"""
        td = self.td(ticket)
        for name in ("summary.md", "masked.md", "decision.md", "escalation.md", "implementation.md", "review-1.md", "pii-1.md"):
            (td / name).write_text(name, encoding="utf-8")
        (td / "analysis").mkdir(exist_ok=True)
        (td / "analysis" / "minimal.md").write_text("m", encoding="utf-8")
        (td / "attachments").mkdir(exist_ok=True)
        (td / "attachments" / "a.txt").write_text("att", encoding="utf-8")
        (td / "site-p.txt").write_text("site", encoding="utf-8")
        status.set_status(self.cfg, ticket, "待人工交付", severity=severity, projects=["p"])

    def reopen(self, ticket, **kw):
        from console_cli import reopen
        with contextlib.redirect_stdout(io.StringIO()) as out, \
                mock.patch.object(reopen, "warn", side_effect=self.warned.append):
            result = reopen.reopen_ticket(self.cfg, ticket, **kw)
        self.output = out.getvalue()
        return result

    def stage(self, ticket):
        return status.load(status.status_file(self.cfg, ticket))

    def test_archives_previous_round_and_marks_new_start(self):
        from console_cli import reopen
        self.local_branch("r-20", "a.txt")
        path = self.add("20")
        first_head = self.marker("20")["head"]
        round1_head = commit(path, "round1.txt")  # 前一輪在 worktree 內提交的成果
        self.finished_ticket("20")  # worktree 保留著，驗證「worktree 還在」的情況

        self.assertEqual(self.reopen("20"), 2)

        td = self.td("20")
        r1 = td / "round-1"
        for name in ("summary.md", "decision.md", "escalation.md", "implementation.md", "review-1.md", "pii-1.md",
                     "prior-p.json", "masked.md"):
            self.assertTrue((r1 / name).exists(), name)
        self.assertTrue((r1 / "analysis" / "minimal.md").exists())
        for name in ("summary.md", "decision.md", "escalation.md", "implementation.md", "review-1.md", "pii-1.md"):
            self.assertFalse((td / name).exists(), f"{name} 應已搬走")
        self.assertFalse((td / "analysis").exists())
        self.assertTrue((td / "masked.md").exists())  # 複製留底，原檔仍在等重新抓取覆蓋
        self.assertTrue((td / "attachments" / "a.txt").exists())  # 附件留在原處
        self.assertTrue((td / "site-p.txt").exists())
        self.assertEqual(json.loads((r1 / "prior-p.json").read_text(encoding="utf-8"))["head"], first_head)
        new = self.marker("20")
        self.assertEqual((new["head"], new["previous_stage"]), (round1_head, "待人工交付"))
        data = self.stage("20")
        self.assertEqual(data["stage"], "待讀取")
        self.assertNotIn("severity", data)
        self.assertIn("第 2 輪", data["history"][-1]["note"])
        self.assertEqual(reopen.round_number(self.cfg, "20"), 2)
        self.assertEqual(git(path, "status", "--porcelain"), "")  # worktree 沒被動到

    def test_second_reopen_is_round_three(self):
        from console_cli import reopen
        self.local_branch("r-21", "a.txt")
        self.finished_ticket("21")
        self.assertEqual(self.reopen("21"), 2)
        (self.td("21") / "decision.md").write_text("round2", encoding="utf-8")
        status.set_status(self.cfg, "21", "待人工交付", projects=["p"])
        self.assertEqual(self.reopen("21"), 3)
        self.assertEqual((self.td("21") / "round-2" / "decision.md").read_text(encoding="utf-8"), "round2")
        self.assertEqual((self.td("21") / "round-1" / "decision.md").read_text(encoding="utf-8"), "decision.md")
        self.assertEqual(reopen.round_number(self.cfg, "21"), 3)

    def test_refuses_unfinished_or_unknown_ticket_without_touching_anything(self):
        status.set_status(self.cfg, "22", "分析中", projects=["p"])
        (self.td("22") / "decision.md").write_text("x", encoding="utf-8")
        with self.assertRaises(ConsoleError) as ctx:
            self.reopen("22")
        self.assertIn("分析中", str(ctx.exception))
        self.assertTrue((self.td("22") / "decision.md").exists())
        self.assertEqual(self.stage("22")["stage"], "分析中")
        with self.assertRaises(ConsoleError):
            self.reopen("23")  # 完全沒有進度紀錄

    def test_dirty_worktree_refuses_before_moving_anything(self):
        self.local_branch("r-24", "a.txt")
        path = self.add("24")
        self.finished_ticket("24")
        (path / "wip.txt").write_text("未提交", encoding="utf-8")
        with self.assertRaises(ConsoleError) as ctx:
            self.reopen("24")
        self.assertIn("未提交", str(ctx.exception))
        self.assertTrue((self.td("24") / "decision.md").exists())
        self.assertFalse((self.td("24") / "round-1").exists())
        self.assertEqual(self.stage("24")["stage"], "待人工交付")

    def test_without_worktree_marker_is_written_and_kept_by_next_up(self):
        head = self.local_branch("r-25", "a.txt")
        self.finished_ticket("25")
        self.reopen("25")
        self.assertEqual(self.marker("25")["head"], head)
        self.assertEqual(self.stage("25")["stage"], "待讀取")
        git(self.repo, "checkout", "-q", "r-25")
        advanced = commit(self.repo, "later.txt")  # 之後分支又前進
        git(self.repo, "checkout", "-q", "dev")
        self.assertNotEqual(advanced, head)
        self.add("25")
        self.assertEqual(git(self.cfg.worktree_path("25", "p"), "rev-parse", "HEAD"), advanced)
        self.assertEqual(self.marker("25")["head"], head)
        self.assertIn("沿用既有標記", self.output)

    def test_no_branch_anywhere_still_reopens_with_warning(self):
        self.finished_ticket("26")
        self.reopen("26")
        self.assertIsNone(self.marker("26"))
        self.assertEqual(self.stage("26")["stage"], "待讀取")
        self.assertTrue(any("找不到分支" in w for w in self.warned))

    def test_remote_check_failure_aborts_before_moving(self):
        self.local_branch("r-27", "a.txt")
        self.finished_ticket("27")
        real = worktree.run

        def fake(cmd, **kw):
            if "ls-remote" in cmd:
                return subprocess.CompletedProcess(cmd, 128, "", "network down")
            return real(cmd, **kw)

        with mock.patch.object(worktree, "run", side_effect=fake):
            with self.assertRaises(ConsoleError):
                self.reopen("27")
        self.assertTrue((self.td("27") / "decision.md").exists())
        self.assertEqual(self.stage("27")["stage"], "待人工交付")

    def test_dry_run_changes_nothing(self):
        from console_cli import util
        self.local_branch("r-28", "a.txt")
        self.finished_ticket("28")
        util.set_dry_run(True)
        self.addCleanup(util.set_dry_run, False)
        self.reopen("28")
        self.assertTrue((self.td("28") / "decision.md").exists())
        self.assertFalse((self.td("28") / "round-1").exists())
        self.assertEqual(self.stage("28")["stage"], "待人工交付")
        self.assertIsNone(self.marker("28"))
        self.assertIn("dry-run", self.output)

class LandedTests(PriorBase):
    """已併入偵測：只收集證據，不取提交主旨。"""

    def landed(self, ticket="7"):
        from console_cli import landed
        with contextlib.redirect_stdout(io.StringIO()):
            info = landed.record(self.cfg, ticket, "p")
        f = landed.landed_file(self.cfg, ticket, "p")
        return info, (json.loads(f.read_text(encoding="utf-8")) if f.exists() else None)

    def push_dev(self):
        git(self.repo, "push", "-q", "origin", "dev")

    def test_nothing_landed_writes_no_file(self):
        info, data = self.landed()
        self.assertEqual(info["level"], "none")
        self.assertIsNone(data)

    def test_empty_branch_is_not_landed(self):
        git(self.repo, "branch", "r-7", "dev")
        info, data = self.landed()
        self.assertEqual(info["level"], "none")
        self.assertIsNone(data)

    def test_branch_merged_into_base(self):
        self.local_branch("r-7", "a.txt")
        git(self.repo, "merge", "-q", "--no-ff", "r-7", "-m", "merge #7")
        self.push_dev()
        info, data = self.landed()
        self.assertEqual(info["level"], "merged")
        self.assertTrue(data["branch_merged"])

    def test_squash_merge_found_by_ticket_number_in_message(self):
        self.local_branch("r-7", "a.txt")
        (self.repo / "b.txt").write_text("b", encoding="utf-8")
        git(self.repo, "add", "b.txt")
        git(self.repo, "commit", "-q", "-m", "fix thing (#7)")
        self.push_dev()
        info, data = self.landed()
        self.assertEqual(info["level"], "mentioned")
        self.assertEqual(data["base_files"], ["b.txt"])
        self.assertNotIn("fix thing", json.dumps(data))   # 不含提交主旨

    def test_ticket_number_prefix_not_confused(self):
        (self.repo / "c.txt").write_text("c", encoding="utf-8")
        git(self.repo, "add", "c.txt")
        git(self.repo, "commit", "-q", "-m", "other work #70 and r-17")
        self.push_dev()
        info, _ = self.landed("7")
        self.assertEqual(info["level"], "none")

    def test_stale_file_removed_when_nothing_found(self):
        from console_cli import landed
        p = landed.landed_file(self.cfg, "7", "p")
        p.parent.mkdir(parents=True)
        p.write_text("{}", encoding="utf-8")
        self.landed()
        self.assertFalse(p.exists())


if __name__ == "__main__":
    unittest.main()
