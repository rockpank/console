"""介面（console_cli/ui.py）測試：不碰真實 tmux、wt.exe、docker。"""
import json
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from console_cli import ui, usage  # noqa: E402
from console_cli.config import Config  # noqa: E402
from console_cli.util import ConsoleError  # noqa: E402

_REAL_GUARD = ui._guard   # 測試 fail-open 時要呼叫真的（UiBase 會把 ui._guard 換掉）
NOT_PAUSED = {"paused": False, "breached": False, "overridden": False, "reasons": [], "until": None, "override_until": None}
PAUSED = {"paused": True, "breached": True, "overridden": False, "reasons": ["5 小時額度已用 93%"],
          "until": time.time() + 3600, "override_until": None}

# 以下全是假資料
FAKE_AMOUNT = "NT$ 50,000"
BACKLOG = """# Backlog：demo

| ID | 類型 | 標題 | 來源 | 成本 | 依賴 | 路線 | 狀態 |
|---|---|---|---|---|---|---|---|
| B-001 | 資安 | 設定預設改為失敗即拒絕 | sec H-1 | M | 待決：Q7 | 完整 | 待辦 |
| B-002 | 缺陷 | 標籤區落在 title 內 | ux | S | 無 | 快速 | 開發中 |
| B-003 | 補完 | 發送前重驗 | arch | M | 無 | 完整 | **待辦**（待決：Q3） |
| B-004 | 缺陷 | 已經做完的項目 | ux | S | 無 | 快速 | 完成 |
| B-005 | 優化 | 暫緩的項目 | ux | S | 無 | 快速 | 擱置 |

## 別的段落

| ID | 標題 | 狀態 |
|---|---|---|
| X-1 | 不該被讀到的第二張表 | 開發中 |
"""


def _done(returncode=0, stdout=""):
    return mock.Mock(returncode=returncode, stdout=stdout, stderr="")


class UiBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.cfg = Config({"console": {"worktree_root": str(root / "wt"), "runtime_dir": str(root / "runtime"),
                                       "projects_dir": str(root / "projects")},
                           "projects": {"demo": {}}})
        self.ws = root / "projects" / "demo"
        self.ws.mkdir(parents=True)
        (self.ws / "profile.md").write_text("# demo\n", encoding="utf-8")
        (self.ws / "backlog.md").write_text(BACKLOG, encoding="utf-8")
        (root / "projects" / "_template").mkdir()
        (root / "projects" / "_template" / "profile.md").write_text("x", encoding="utf-8")
        mock.patch.object(ui, "_guard", return_value=NOT_PAUSED).start()   # 不讀真實用量，結果才不會隨你當下的額度變
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        self.tmp.cleanup()

    def task_dir(self, task):
        d = self.ws / "tasks" / task
        d.mkdir(parents=True, exist_ok=True)
        return d

    def view(self, task, now=None):
        return next(v for v in ui.collect(self.cfg, now=now) if v["task"] == task)


class BacklogTests(UiBase):
    def test_reads_first_table_only_and_normalizes_status(self):
        rows = ui.parse_backlog(self.ws / "backlog.md")
        self.assertEqual(list(rows), ["B-001", "B-002", "B-003", "B-004", "B-005"])   # 第二張表不讀
        self.assertEqual(rows["B-003"]["status"], "待辦")                              # 加粗與括號註記都去掉
        self.assertTrue(rows["B-003"]["undecided"])
        self.assertTrue(rows["B-001"]["undecided"])                                    # 依賴欄寫了待決
        self.assertFalse(rows["B-002"]["undecided"])
        self.assertEqual(rows["B-002"]["route"], "快速")

    def test_missing_or_malformed_backlog_is_empty(self):
        self.assertEqual(ui.parse_backlog(self.ws / "nope.md"), {})
        (self.ws / "backlog.md").write_text("沒有表格\n| a | b |\n|---|---|\n| 1 | 2 |\n", encoding="utf-8")
        self.assertEqual(ui.parse_backlog(self.ws / "backlog.md"), {})

    def test_rows_with_invalid_ids_are_skipped(self):
        (self.ws / "backlog.md").write_text("| ID | 標題 | 狀態 |\n|---|---|---|\n| B-1; ls | x | 待辦 |\n| B-2 | y | 待辦 |\n",
                                            encoding="utf-8")
        self.assertEqual(list(ui.parse_backlog(self.ws / "backlog.md")), ["B-2"])

    def test_backlog_view_lists_only_pending_and_flags_known(self):
        bv = ui.backlog_view(self.cfg, {("demo", "B-001")})[0]
        self.assertEqual(bv["project"], "demo")
        self.assertEqual(bv["counts"], {"待辦": 2, "開發中": 1, "完成": 1, "擱置": 1})
        self.assertEqual([(i["id"], i["known"]) for i in bv["items"]], [("B-001", True), ("B-003", False)])

    def test_template_and_projects_without_profile_are_not_listed(self):
        (self.ws.parent / "noprofile").mkdir()
        self.assertEqual(ui.projects_with_workspace(self.cfg), ["demo"])


class CollectTests(UiBase):
    def test_only_active_tasks_become_cards(self):
        self.assertEqual([v["task"] for v in ui.collect(self.cfg)], ["B-002"])   # 只有「開發中」；待辦／完成／擱置沒有交接檔就不上看板

    def test_task_with_files_or_worktree_shows_up_whatever_the_backlog_says(self):
        self.task_dir("B-001")
        self.cfg.worktree_path("B-005", "demo").mkdir(parents=True)
        self.task_dir("N-3")
        self.assertEqual({v["task"] for v in ui.collect(self.cfg)}, {"B-001", "B-002", "B-005", "N-3"})
        self.assertIn({"text": "不在 backlog", "kind": "muted"}, self.view("N-3")["badges"])

    def test_stage_takes_the_later_of_backlog_and_files(self):
        td = self.task_dir("B-002")
        self.assertEqual(self.view("B-002")["stage"], "開發中")        # backlog 說開發中
        (td / "security-1.md").write_text("---\nverdict: 通過\n---\n", encoding="utf-8")
        self.assertEqual(self.view("B-002")["stage"], "資安")          # 交接檔更後面（PM 的狀態可能落後）
        (td / "qa-1.md").write_text("---\nverdict: 通過\n---\n", encoding="utf-8")
        v = self.view("B-002")
        self.assertEqual(v["stage"], "QA")
        self.assertEqual([p["state"] for p in v["pipeline"]], ["done", "done", "done", "current", "todo"])

    def test_done_task_is_marked_for_acceptance_when_worktree_exists(self):
        self.cfg.worktree_path("B-004", "demo").mkdir(parents=True)
        v = self.view("B-004")
        self.assertEqual((v["stage"], v["group"]), ("完成", "done"))
        self.assertIn({"text": "待你驗收合併", "kind": "ok"}, v["badges"])
        self.assertEqual({p["state"] for p in v["pipeline"]}, {"done"})
        self.assertEqual([a["id"] for a in v["actions"]], ["chat"])   # 完成的任務不再有高耗動作

    def test_escalation_blocks_the_pipeline_and_offers_resume_with_ruling(self):
        td = self.task_dir("B-002")
        (td / "escalation.md").write_text("---\ntask: B-002\nresume_at: 資安\n---\n內文", encoding="utf-8")
        v = self.view("B-002")
        self.assertEqual(v["group"], "need")
        self.assertIn({"text": "需你裁示", "kind": "alert"}, v["badges"])
        self.assertEqual([p["state"] for p in v["pipeline"]], ["done", "done", "blocked", "todo", "todo"])
        resume = next(a for a in v["actions"] if a["id"] == "resume")
        self.assertTrue(resume["ruling"])

    def test_quota_pause_is_a_warning_without_ruling_box(self):
        td = self.task_dir("B-002")
        (td / "escalation.md").write_text("---\nkind: 額度保護\nresume_at: 開發中\n---\n", encoding="utf-8")
        v = self.view("B-002")
        self.assertIn({"text": "額度保護暫停", "kind": "warn"}, v["badges"])
        resume = next(a for a in v["actions"] if a["id"] == "resume")
        self.assertFalse(resume.get("ruling"))

    def test_resolved_escalation_no_longer_needs_the_user(self):
        td = self.task_dir("B-002")
        (td / "escalation.md").write_text("---\nresume_at: 資安\nresolved: true\n---\n", encoding="utf-8")
        self.assertEqual(self.view("B-002")["group"], "run")

    def test_roles_reflect_reports(self):
        td = self.task_dir("B-002")
        (td / "impl-notes.md").write_text("---\nstatus: done\ntests: 通過\n---\n", encoding="utf-8")
        (td / "security-1.md").write_text("---\nverdict: 需修正\n---\n", encoding="utf-8")
        (td / "security-2.md").write_text("---\nverdict: 通過\n---\n", encoding="utf-8")
        (td / "qa-1.md").write_text("---\nverdict: 失敗\n---\n", encoding="utf-8")
        roles = {r["key"]: r for r in self.view("B-002")["roles"]}
        self.assertEqual((roles["engineer"]["state"], roles["engineer"]["detail"]), ("done", "測試通過"))
        self.assertEqual((roles["security"]["state"], roles["security"]["detail"]), ("done", "2輪・通過"))   # 看最新一輪
        self.assertEqual((roles["qa"]["state"], roles["qa"]["detail"]), ("warn", "1輪・失敗"))
        self.assertEqual(roles["worktree"]["state"], "todo")

    def test_blocked_engineer(self):
        (self.task_dir("B-002") / "impl-notes.md").write_text("---\nstatus: blocked\n---\n", encoding="utf-8")
        roles = {r["key"]: r for r in self.view("B-002")["roles"]}
        self.assertEqual(roles["engineer"]["state"], "blocked")

    def test_stale_badge_after_a_day(self):
        self.task_dir("B-002")
        (self.task_dir("B-002") / "impl-notes.md").write_text("x", encoding="utf-8")
        later = datetime.now().astimezone() + timedelta(hours=30)
        self.assertIn({"text": "久未動", "kind": "muted"}, self.view("B-002", now=later)["badges"])
        self.assertNotIn({"text": "久未動", "kind": "muted"}, self.view("B-002")["badges"])

    def test_frontmatter_reads_only_requested_keys(self):
        f = self.task_dir("B-002") / "r.md"
        f.write_text("---\nverdict: 通過\nsecret: 不該讀到\n---\n", encoding="utf-8")
        self.assertEqual(ui._frontmatter(f, ("verdict",)), {"verdict": "通過"})

    def test_junk_directory_names_are_ignored(self):
        self.task_dir(".hidden")
        self.task_dir("a b")
        self.assertEqual([v["task"] for v in ui.collect(self.cfg)], ["B-002"])


class QueueTests(UiBase):
    def setUp(self):
        super().setUp()
        for t in ("B-001", "B-003"):
            self.task_dir(t)

    def test_hold_masks_reason_and_sorts_last(self):
        ui.set_hold(self.cfg, "B-001", True, f"等使用者確認 {FAKE_AMOUNT}\n第二行")
        views = ui.collect(self.cfg)
        self.assertEqual([v["task"] for v in views], ["B-002", "B-003", "B-001"])
        held = views[-1]
        self.assertTrue(held["hold"])
        self.assertEqual(held["group"], "hold")
        self.assertNotIn("50,000", held["hold_reason"])
        self.assertNotIn("\n", held["hold_reason"])
        self.assertEqual([a["id"] for a in held["actions"]], ["chat"])  # 擱置中不主動推進
        ui.set_hold(self.cfg, "B-001", False)
        self.assertEqual([v["task"] for v in ui.collect(self.cfg)], ["B-001", "B-002", "B-003"])

    def test_order_is_respected_and_validated(self):
        ui.set_order(self.cfg, ["B-003", "B-001", "B-003"])
        self.assertEqual([v["task"] for v in ui.collect(self.cfg)], ["B-003", "B-001", "B-002"])
        with self.assertRaises(ConsoleError):
            ui.set_order(self.cfg, ["B-003; rm -rf /"])

    def test_corrupt_queue_file_is_ignored(self):
        self.cfg.runtime_dir.mkdir(parents=True)
        (self.cfg.runtime_dir / "queue.json").write_text("{壞掉", encoding="utf-8")
        self.assertEqual(len(ui.collect(self.cfg)), 3)

    def test_junk_entries_in_queue_file_are_dropped(self):
        self.cfg.runtime_dir.mkdir(parents=True)
        (self.cfg.runtime_dir / "queue.json").write_text(
            json.dumps({"order": ["B-1", "x; ls", 5], "tasks": {"B-1": {"hold": True}, "../x": {}}, "removed": "bad"}),
            encoding="utf-8")
        q = ui.load_queue(self.cfg)
        self.assertEqual(q["order"], ["B-1", "5"])
        self.assertEqual(list(q["tasks"]), ["B-1"])
        self.assertEqual(q["removed"], {})


class PromptTests(UiBase):
    def test_whitelist_and_shapes(self):
        p = ui.build_prompt
        self.assertEqual(p(self.cfg, "dispatch", "demo", "B-001"), "/dispatch demo B-001")
        self.assertEqual(p(self.cfg, "resume", "demo", "B-001"), "/dispatch resume demo B-001")
        self.assertIsNone(p(self.cfg, "chat", "demo", "B-001"))
        for bad in ("rm", "", "dispatch; ls", "reopen", "spec"):   # reopen／spec 是 Redmine 時代的動作，已移除
            with self.assertRaises(ConsoleError):
                p(self.cfg, bad, "demo", "B-001")

    def test_ruling_is_masked_single_line_and_capped(self):
        out = ui.build_prompt(self.cfg, "resume", "demo", "B-001", f"採 A\n金額 {FAKE_AMOUNT}\n" + "字" * 500)
        self.assertNotIn("50,000", out)
        self.assertNotIn("\n", out)
        self.assertTrue(out.startswith("/dispatch resume demo B-001 採 A"))
        self.assertLessEqual(len(out), len("/dispatch resume demo B-001 ") + 300)


class LaunchTests(UiBase):
    def setUp(self):
        super().setUp()
        self.popen = mock.patch.object(ui.subprocess, "Popen").start()
        self.addCleanup(mock.patch.stopall)

    def _which(self, have):
        return mock.patch.object(ui.shutil, "which", side_effect=lambda n: f"/bin/{n}" if n in have else None)

    def test_creates_session_in_background_without_opening_a_window(self):
        calls = []

        def fake_run(cmd, **kw):
            calls.append(cmd)
            return _done(1 if cmd[1] == "has-session" else 0)

        with self._which({"tmux", "wt.exe", "claude"}), mock.patch.object(ui.util, "run", side_effect=fake_run):
            res = ui.launch(self.cfg, "demo", "B-002", "resume", ruling="採 A")
        new = next(c for c in calls if c[1] == "new-session")
        self.assertEqual(new[new.index("-s") + 1], "dev-B-002")
        self.assertEqual(new[new.index("-c") + 1], str(ui.ROOT))
        self.assertIn("/dispatch resume demo B-002 採 A", new[-1])
        self.assertTrue(new[-1].startswith("/bin/claude -n dev-B-002"))
        self.assertTrue(res["created"] and not res["existing"])
        self.assertEqual((res["task"], res["session"]), ("B-002", "dev-B-002"))
        self.assertNotIn("opened", res)
        self.popen.assert_not_called()  # 即使有 wt.exe 也不開視窗

    def test_existing_session_is_not_resent(self):
        calls = []
        with self._which({"tmux", "wt.exe", "claude"}), \
                mock.patch.object(ui.util, "run", side_effect=lambda c, **k: calls.append(c) or _done(0)):
            res = ui.launch(self.cfg, "demo", "B-002", "resume", ruling="不該再送")
        self.assertTrue(res["existing"] and not res["created"])
        self.assertFalse(any(c[1] == "new-session" for c in calls))

    def test_no_tmux_returns_manual_command(self):
        with self._which({"claude"}), mock.patch.object(ui.util, "run") as run:
            res = ui.launch(self.cfg, "demo", "B-002", "dispatch")
        run.assert_not_called()
        self.assertIn("沒有 tmux", res["message"])
        self.assertIn("claude -n dev-B-002", res["manual"])
        self.assertIn("/dispatch demo B-002", res["manual"])

    def test_chat_has_no_prompt(self):
        with self._which({"tmux", "claude"}), mock.patch.object(ui.util, "run", return_value=_done(1)):
            res = ui.launch(self.cfg, "demo", "B-002", "chat")
        self.assertEqual(res["prompt"], "")

    def test_rejects_unknown_project_task_and_action(self):
        for args in (("nope", "B-002", "dispatch"), ("demo", "B-999", "dispatch"), ("demo", "B-002; ls", "dispatch"),
                     ("demo", "B-002", "reopen"), ("_template", "B-002", "dispatch")):
            with self.assertRaises(ConsoleError, msg=str(args)), mock.patch.object(ui.util, "run") as run:
                ui.launch(self.cfg, *args)
            run.assert_not_called()

    def test_task_with_only_a_worktree_can_be_launched(self):
        self.cfg.worktree_path("N-3", "demo").mkdir(parents=True)
        with self._which({"tmux", "claude"}), mock.patch.object(ui.util, "run", return_value=_done(1)):
            self.assertTrue(ui.launch(self.cfg, "demo", "N-3", "resume")["created"])

    def test_list_sessions_filters_prefix(self):
        out = "dev-B-002\nother\ndev-demo-b101500\nfemas-4059\n"
        with self._which({"tmux"}), mock.patch.object(ui.util, "run", return_value=_done(0, out)):
            self.assertEqual(ui.list_sessions(), {"dev-B-002", "dev-demo-b101500"})

    def test_relaunch_restores_a_removed_task(self):
        self.task_dir("B-002")
        with self._which({"tmux"}), mock.patch.object(ui, "list_sessions", return_value=set()), \
                mock.patch.object(ui.util, "run", return_value=_done(0)):
            ui.remove_task(self.cfg, "demo", "B-002")
        self.assertEqual(ui.collect(self.cfg), [])
        with self._which({"tmux", "claude"}), mock.patch.object(ui.util, "run", return_value=_done(1)):
            ui.launch(self.cfg, "demo", "B-002", "resume")
        self.assertEqual([v["task"] for v in ui.collect(self.cfg)], ["B-002"])


class LaunchBatchTests(UiBase):
    def setUp(self):
        super().setUp()
        self.calls = []

        def fake_run(cmd, **kw):
            self.calls.append(cmd)
            return _done(1 if cmd[1] == "has-session" else 0)

        mock.patch.object(ui.util, "run", side_effect=fake_run).start()
        mock.patch.object(ui.shutil, "which", side_effect=lambda n: f"/bin/{n}").start()
        self.addCleanup(mock.patch.stopall)

    def new_cmd(self):
        return next(c for c in self.calls if c[1] == "new-session")

    def test_one_dispatch_conversation_for_all_picked_items(self):
        res = ui.launch_batch(self.cfg, "demo", ["B-001", "B-003", "B-001"])
        self.assertEqual(res["prompt"], "/dispatch demo B-001,B-003")   # 去重、一個對話、由專案管理員切分
        self.assertTrue(res["created"])
        self.assertRegex(res["session"], r"^dev-demo-b\d{6}$")
        self.assertEqual(len([c for c in self.calls if c[1] == "new-session"]), 1)

    def test_free_text_request(self):
        res = ui.launch_batch(self.cfg, "demo", [], request=f"學員清單可依日期排序\n金額 {FAKE_AMOUNT}")
        self.assertTrue(res["prompt"].startswith("/dispatch demo 學員清單可依日期排序"))
        self.assertNotIn("50,000", res["prompt"])
        self.assertNotIn("\n", res["prompt"])

    def test_auto_pick_asks_the_project_manager_to_choose(self):
        res = ui.launch_batch(self.cfg, "demo", [], go=True, auto=3)
        self.assertEqual(res["prompt"], "/dispatch demo --auto 3 --go")

    def test_auto_pick_validation(self):
        bad = ({"auto": 3, "go": False}, {"auto": 11, "go": True}, {"auto": -1, "go": True},
               {"auto": True, "go": True}, {"auto": 2.5, "go": True},
               {"auto": 2, "go": True, "tasks": ["B-001"]}, {"auto": 2, "go": True, "request": "需求"})
        for kw in bad:
            kw = dict(kw)
            tasks = kw.pop("tasks", [])
            with self.assertRaises(ConsoleError, msg=str(kw)):
                ui.launch_batch(self.cfg, "demo", tasks, **kw)
        self.assertEqual(self.calls, [])

    def test_validates_everything_before_starting_anything(self):
        for tasks, request in ((["B-001", "Z-9"], ""), ([], ""), (["B-001"], "也有需求"), (["B-1; ls"], ""),
                               ([f"B-{i}" for i in range(11)], ""), ([], "   ")):
            with self.assertRaises(ConsoleError, msg=str((tasks, request))):
                ui.launch_batch(self.cfg, "demo", tasks, request=request)
        with self.assertRaises(ConsoleError):
            ui.launch_batch(self.cfg, "nope", ["B-001"])
        self.assertEqual(self.calls, [])

    def test_batch_is_refused_as_a_whole_when_paused(self):
        with mock.patch.object(ui, "_guard", return_value=PAUSED):
            with self.assertRaises(ConsoleError) as cm:
                ui.launch_batch(self.cfg, "demo", ["B-001"])
        self.assertIn("額度保護", str(cm.exception))
        self.assertEqual(self.calls, [])


class GuardTests(UiBase):
    """額度達門檻 → 拒絕高耗 token 的動作；其他操作不受影響。"""

    def paused(self):
        return mock.patch.object(ui, "_guard", return_value=PAUSED)

    def test_heavy_actions_are_refused_and_nothing_is_started(self):
        self.assertEqual(ui.HEAVY_ACTIONS, {"dispatch", "resume"})
        for action in ("dispatch", "resume"):
            with self.paused(), mock.patch.object(ui.util, "run") as run, mock.patch.object(ui.shutil, "which", return_value="/bin/x"):
                with self.assertRaises(ConsoleError, msg=action) as cm:
                    ui.launch(self.cfg, "demo", "B-002", action)
            self.assertIn("額度保護", str(cm.exception))
            self.assertIn("5 小時額度已用 93%", str(cm.exception))
            self.assertIn("暫時解除", str(cm.exception))
            run.assert_not_called()   # 連 tmux 都沒碰

    def test_chat_is_not_blocked(self):
        with self.paused(), mock.patch.object(ui.util, "run", return_value=_done(0)), \
                mock.patch.object(ui.shutil, "which", return_value="/bin/x"):
            res = ui.launch(self.cfg, "demo", "B-002", "chat")        # 開空對話，不會自己耗 token
        self.assertTrue(res["existing"] or res["created"])

    def test_not_paused_launches_normally(self):
        with mock.patch.object(ui.util, "run", return_value=_done(1)) as run, mock.patch.object(ui.shutil, "which", return_value="/bin/x"):
            res = ui.launch(self.cfg, "demo", "B-002", "dispatch")
        self.assertTrue(res["created"])
        self.assertTrue(any(c.args[0][1] == "new-session" for c in run.call_args_list))

    def test_bad_input_error_wins_over_guard(self):
        with self.paused():
            with self.assertRaises(ConsoleError) as cm:
                ui.launch(self.cfg, "demo", "abc;", "dispatch")
        self.assertNotIn("額度保護", str(cm.exception))

    def test_guard_fails_open_when_usage_cannot_be_computed(self):
        with mock.patch.object(ui.usage, "view", side_effect=OSError("讀不到紀錄")):
            g = _REAL_GUARD(self.cfg)
        self.assertFalse(g["paused"])   # 保護失靈不該反過來擋住工作

    def test_message_mentions_reset_time(self):
        msg = ui.guard_message(PAUSED)
        self.assertIn("預計", msg)
        self.assertIn("重置", msg)


class AttachCommandTests(unittest.TestCase):
    def test_attach_command_survives_zsh(self):
        """給人貼的指令要能在 zsh 原樣執行：未加引號的 =名稱 會被展開成「找不到指令」。"""
        import shutil
        import subprocess
        zsh = shutil.which("zsh")
        if not zsh:
            self.skipTest("沒有 zsh")
        cmd = ui.attach_command("dev-B-5").replace("tmux", "echo", 1)
        out = subprocess.run([zsh, "-c", cmd], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), "attach-session -t =dev-B-5")


class OpenWindowTests(UiBase):
    def setUp(self):
        super().setUp()
        self.popen = mock.patch.object(ui.subprocess, "Popen").start()
        self.addCleanup(mock.patch.stopall)

    def _which(self, have):
        return mock.patch.object(ui.shutil, "which", side_effect=lambda n: f"/bin/{n}" if n in have else None)

    def test_opens_wt_tab_attached_to_existing_session(self):
        with self._which({"tmux", "wt.exe"}), mock.patch.object(ui.util, "run", return_value=_done(0)) as run:
            res = ui.open_window("B-5")
        self.assertEqual(run.call_args[0][0], ["tmux", "has-session", "-t", "=dev-B-5"])
        argv = self.popen.call_args[0][0]
        self.assertEqual(argv[0], "/bin/wt.exe")
        self.assertEqual(argv[-5:], ["--exec", "tmux", "attach-session", "-t", "=dev-B-5"])
        # 不能用 `--`：wsl 會經預設 shell（zsh）執行，`=dev-B-5` 會被當 equals expansion 而失敗
        self.assertNotIn("--", argv)
        self.assertTrue(res["opened"])

    def test_never_creates_a_session(self):
        with self._which({"tmux", "wt.exe"}), mock.patch.object(ui.util, "run", return_value=_done(1)) as run:
            with self.assertRaises(ConsoleError):
                ui.open_window("B-5")
        self.assertFalse(any(c.args[0][1] == "new-session" for c in run.call_args_list))
        self.popen.assert_not_called()

    def test_without_wt_gives_attach_command(self):
        with self._which({"tmux"}), mock.patch.object(ui.util, "run", return_value=_done(0)):
            res = ui.open_window("B-5")
        self.assertFalse(res["opened"])
        self.assertEqual(res["attach"], "tmux attach-session -t '=dev-B-5'")
        self.popen.assert_not_called()

    def test_rejects_bad_input(self):
        with self._which({"tmux", "wt.exe"}):
            with self.assertRaises(ConsoleError):
                ui.open_window("B-5; ls")
        with self._which(set()):
            with self.assertRaises(ConsoleError):
                ui.open_window("B-5")
        self.popen.assert_not_called()


class CloseAndRemoveTests(UiBase):
    def setUp(self):
        super().setUp()
        self.task_dir("B-001")
        self.run = mock.patch.object(ui.util, "run", return_value=_done(0)).start()
        self.sessions = mock.patch.object(ui, "list_sessions", return_value={"dev-B-001", "dev-B-002"}).start()
        self.addCleanup(mock.patch.stopall)

    def killed(self):
        return [c.args[0][-1] for c in self.run.call_args_list if c.args[0][1] == "kill-session"]

    def test_close_by_task_kills_only_that_session(self):
        self.assertEqual(ui.close_sessions(task="B-001"), ["dev-B-001"])
        self.assertEqual(self.killed(), ["=dev-B-001"])

    def test_close_by_task_without_session_is_a_noop(self):
        self.sessions.return_value = set()
        self.assertEqual(ui.close_sessions(task="B-001"), [])
        self.assertEqual(self.killed(), [])

    def test_close_by_name_only_for_live_dev_sessions(self):
        self.assertEqual(ui.close_sessions(session="dev-B-002"), ["dev-B-002"])
        for bad in ("not-ours", "femas-1", ""):
            with self.assertRaises(ConsoleError):
                ui.close_sessions(session=bad)

    def test_remove_hides_card_closes_session_and_deletes_nothing(self):
        (self.task_dir("B-001") / "impl-notes.md").write_text("x", encoding="utf-8")
        wt = self.cfg.worktree_path("B-001", "demo")
        wt.mkdir(parents=True)
        res = ui.remove_task(self.cfg, "demo", "B-001")
        self.assertEqual(res["closed"], ["dev-B-001"])
        self.assertNotIn("B-001", [v["task"] for v in ui.collect(self.cfg)])
        self.assertTrue((self.ws / "tasks" / "B-001" / "impl-notes.md").exists())   # 交接檔與 worktree 都還在
        self.assertTrue(wt.is_dir())

    def test_removed_task_returns_when_handoff_files_change(self):
        f = self.task_dir("B-001") / "impl-notes.md"
        f.write_text("x", encoding="utf-8")
        ui.remove_task(self.cfg, "demo", "B-001")
        self.assertNotIn("B-001", [v["task"] for v in ui.collect(self.cfg)])
        time.sleep(1.1)   # mtime 以秒為單位
        f.write_text("y", encoding="utf-8")
        self.assertIn("B-001", [v["task"] for v in ui.collect(self.cfg)])

    def test_remove_rejects_unknown_project_or_bad_code(self):
        for args in (("nope", "B-001"), ("demo", "B-001; ls")):
            with self.assertRaises(ConsoleError):
                ui.remove_task(self.cfg, *args)

    def test_remove_clears_hold_and_order(self):
        ui.set_hold(self.cfg, "B-001", True, "x")
        ui.set_order(self.cfg, ["B-001", "B-002"])
        ui.remove_task(self.cfg, "demo", "B-001")
        q = ui.load_queue(self.cfg)
        self.assertNotIn("B-001", q["tasks"])
        self.assertEqual(q["order"], ["B-002"])


class ServeTests(UiBase):
    def test_serve_never_opens_a_browser_or_explorer(self):
        fake = mock.Mock(server_address=("127.0.0.1", 9))
        fake.serve_forever.side_effect = KeyboardInterrupt
        with mock.patch.object(ui, "make_server", return_value=fake), mock.patch.object(ui.usage, "warm_up") as warm, \
                mock.patch.object(ui.subprocess, "Popen") as popen, \
                mock.patch.object(ui.shutil, "which", return_value="/bin/explorer.exe"), \
                mock.patch.object(ui, "say") as say:
            self.assertEqual(ui.serve(self.cfg, port=0), 0)
        popen.assert_not_called()
        warm.assert_called_once()   # 啟動時在背景暖機用量索引
        self.assertFalse(hasattr(ui, "webbrowser"))
        self.assertTrue(any("http://127.0.0.1:9/?k=" in c.args[0] for c in say.call_args_list))  # 網址有印出來
        fake.server_close.assert_called_once()


class NoRedmineTests(unittest.TestCase):
    """看板不再有任何 Redmine 功能。"""

    def test_module_and_page_have_no_redmine(self):
        src = Path(ui.__file__).read_text(encoding="utf-8")
        page = ui.PAGE.read_text(encoding="utf-8")
        for text in (src, page):
            self.assertNotIn("redmine", text.lower())
            self.assertNotIn("/redmine-ticket", text)
        self.assertFalse(hasattr(ui, "redmine"))
        self.assertFalse(hasattr(ui, "assigned_view"))
        self.assertFalse(hasattr(ui, "redmine_base"))
        self.assertNotIn("__REDMINE__", page)


class ServerTests(UiBase):
    TOKEN = "tok-for-tests"

    def setUp(self):
        super().setUp()
        self.server = ui.make_server(self.cfg, 0, self.TOKEN)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        mock.patch.object(ui, "list_sessions", return_value=set()).start()
        self.addCleanup(mock.patch.stopall)

    def req(self, path, *, method="GET", body=None, headers=None):
        h = {"X-Console-Token": self.TOKEN, "Host": f"127.0.0.1:{self.port}"}
        if body is not None:
            h["Content-Type"] = "application/json"
        h.update(headers or {})
        h = {k: v for k, v in h.items() if v is not None}
        r = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", method=method, headers=h,
                                   data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(r) as resp:
                return resp.status, resp.read().decode()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode()

    def test_page_needs_key_and_embeds_token(self):
        self.assertEqual(self.req("/")[0], 403)
        code, html = self.req(f"/?k={self.TOKEN}")
        self.assertEqual(code, 200)
        self.assertIn(self.TOKEN, html)
        self.assertNotIn("__TOKEN__", html)

    def test_tasks_api_requires_token_and_host(self):
        self.assertEqual(self.req("/api/tasks", headers={"X-Console-Token": "wrong"})[0], 403)
        self.assertEqual(self.req("/api/tasks", headers={"Host": "evil.example:80"})[0], 403)
        code, body = self.req("/api/tasks")
        data = json.loads(body)
        self.assertEqual(code, 200)
        self.assertEqual([t["task"] for t in data["tasks"]], ["B-002"])
        self.assertEqual(data["projects"], ["demo"])
        self.assertEqual([i["id"] for i in data["backlog"][0]["items"]], ["B-001", "B-003"])
        self.assertEqual(self.req("/api/tickets")[0], 404)               # 舊路徑已移除
        self.assertEqual(self.req("/api/redmine/assigned")[0], 404)

    def test_auto_api_settings_and_queue(self):
        self.assertEqual(self.req("/api/auto", headers={"X-Console-Token": "wrong"})[0], 403)
        self.assertEqual(self.req("/api/auto", method="POST", body={"slots": 2}, headers={"X-Console-Token": "wrong"})[0], 403)
        code, body = self.req("/api/auto", method="POST", body={"enabled": True, "slots": 2})
        self.assertEqual((code, json.loads(body)["slots"], json.loads(body)["enabled"]), (200, 2, True))
        for bad in ({"slots": 99}, {"slots": "x"}, {"enabled": "yes"}):
            code, body = self.req("/api/auto", method="POST", body=bad)
            self.assertEqual(code, 400, bad)
        self.assertEqual(self.req("/api/auto-queue", method="POST", body={"project": "demo", "tasks": ["B-001"]})[0], 404)   # 佇列已移除
        from console_cli import autodispatch
        with mock.patch.object(autodispatch.usage, "view", return_value={
                "quotas": [{"key": "five_hour", "pct": 10, "source": "statusline", "stale": False}], "guard": {"paused": False}}):
            code, body = self.req("/api/auto")
        data = json.loads(body)
        self.assertEqual((code, data["slots"], data["enabled"], data["occupied"]), (200, 2, True, 1))   # B-002 進行中
        self.assertEqual(data["running"], ["demo/B-002"])

    def test_orphan_sessions(self):
        sessions = {"dev-B-002", "dev-demo-b101500", "dev-gone"}
        with mock.patch.object(ui, "list_sessions", return_value=sessions):
            data = json.loads(self.req("/api/tasks")[1])
        self.assertEqual(data["orphans"], ["dev-gone"])   # 已知任務與批次對話不算孤兒

    def test_usage_api_needs_token_and_returns_numbers_only(self):
        from console_cli import usage as usage_mod
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        proj = Path(tmp.name) / "p" / "-x"
        proj.mkdir(parents=True)
        secret = "客戶的薪資內容"
        (proj / "sid-1.jsonl").write_text(json.dumps(
            {"type": "user", "sessionId": "sid-1", "message": {"role": "user", "content": secret}}) + "\n", encoding="utf-8")
        idx = usage_mod.Index(Path(tmp.name) / "p")
        with mock.patch.object(usage_mod, "shared_index", return_value=idx):
            self.assertEqual(self.req("/api/usage", headers={"X-Console-Token": "wrong"})[0], 403)
            self.assertEqual(self.req("/api/usage", headers={"Host": "evil.example:80"})[0], 403)
            code, body = self.req("/api/usage")
        self.assertEqual(code, 200)
        data = json.loads(body)
        self.assertTrue(data["ok"])
        for key in ("quotas", "sessions", "tasks", "hourly", "models", "limits", "alerts", "alert_percent"):
            self.assertIn(key, data)
        self.assertNotIn(secret, body)

    def test_guard_override_api(self):
        body = {"override": True}
        self.assertEqual(self.req("/api/guard", method="POST", body=body, headers={"X-Console-Token": "x"})[0], 403)
        code, text = self.req("/api/guard", method="POST", body=body)      # 沒達門檻：不需要解除
        self.assertEqual(code, 400)
        self.assertIn("不需要解除", json.loads(text)["error"])
        with mock.patch.object(ui, "_guard", return_value=PAUSED):         # 達門檻：寫入解除檔
            code, text = self.req("/api/guard", method="POST", body=body)
        self.assertEqual(code, 200)
        self.assertGreater(usage.read_override(self.cfg.runtime_dir, time.time()), time.time())
        code, _ = self.req("/api/guard", method="POST", body={"override": False})   # 恢復暫停
        self.assertEqual(code, 200)
        self.assertEqual(usage.read_override(self.cfg.runtime_dir, time.time()), 0.0)

    def test_post_rules(self):
        ok = {"task": "B-002", "hold": True, "reason": "等釐清"}
        self.assertEqual(self.req("/api/queue", method="POST", body=ok, headers={"X-Console-Token": "x"})[0], 403)
        self.assertEqual(self.req("/api/queue", method="POST", body=ok, headers={"Origin": "http://evil.example"})[0], 403)
        self.assertEqual(self.req("/api/queue", method="POST", body=ok, headers={"Content-Type": "text/plain"})[0], 403)
        self.assertEqual(self.req("/api/queue", method="POST", body={"task": "B-1; ls", "hold": True})[0], 400)
        self.assertEqual(self.req("/api/queue", method="POST", body=ok)[0], 200)
        self.assertTrue(ui.collect(self.cfg)[0]["hold"])
        bad = {"project": "demo", "task": "B-002", "action": "rm -rf"}
        self.assertEqual(self.req("/api/launch", method="POST", body=bad)[0], 400)
        self.assertEqual(self.req("/api/nope", method="POST", body={})[0], 404)

    def test_launch_endpoint(self):
        fake = {"created": True, "existing": False, "message": "ok", "task": "B-002", "session": "dev-B-002"}
        body = {"project": "demo", "task": "B-002", "action": "resume", "ruling": "採 A"}
        with mock.patch.object(ui, "launch", return_value=fake) as launch:
            code, text = self.req("/api/launch", method="POST", body=body)
        self.assertEqual(code, 200)
        launch.assert_called_once_with(self.cfg, "demo", "B-002", "resume", ruling="採 A")
        self.assertTrue(json.loads(text)["ok"])

    def test_launch_batch_endpoint(self):
        ok = {"tasks": ["B-001", "B-003"], "project": "demo"}
        self.assertEqual(self.req("/api/launch-batch", method="POST", body=ok, headers={"X-Console-Token": "x"})[0], 403)
        self.assertEqual(self.req("/api/launch-batch", method="POST", body=ok, headers={"Origin": "http://evil.example"})[0], 403)
        self.assertEqual(self.req("/api/launch-batch", method="POST", body={"tasks": "B-001", "project": "demo"})[0], 400)  # 不是陣列
        self.assertEqual(self.req("/api/launch-batch", method="POST", body={"tasks": ["B-1; ls"], "project": "demo"})[0], 400)
        fake = {"created": True, "existing": False, "message": "已開新對話", "attach": "a", "manual": "m", "session": "s", "prompt": "p"}
        with mock.patch.object(ui, "launch_batch", return_value=fake) as lb:
            code, body = self.req("/api/launch-batch", method="POST", body=ok)
        self.assertEqual(code, 200)
        lb.assert_called_once_with(self.cfg, "demo", ["B-001", "B-003"], request="")

    def test_terminal_close_remove_endpoints(self):
        for path, body in (("/api/terminal", {"task": "B-002"}), ("/api/close", {"task": "B-002"}),
                           ("/api/remove", {"project": "demo", "task": "B-002"})):
            self.assertEqual(self.req(path, method="POST", body=body, headers={"X-Console-Token": "x"})[0], 403, path)
            self.assertEqual(self.req(path, method="POST", body=body, headers={"Origin": "http://evil.example"})[0], 403, path)
        self.assertEqual(self.req("/api/terminal", method="POST", body={"task": "B-2; ls"})[0], 400)
        self.assertEqual(self.req("/api/close", method="POST", body={"session": "not-ours"})[0], 400)
        self.assertEqual(self.req("/api/close", method="POST", body={})[0], 400)
        self.assertEqual(self.req("/api/remove", method="POST", body={"project": "demo", "task": "x;"})[0], 400)
        self.assertEqual(self.req("/api/remove", method="POST", body={"project": "nope", "task": "B-002"})[0], 400)

        with mock.patch.object(ui, "open_window", return_value={"ok": True, "opened": True}) as ow:
            code, _ = self.req("/api/terminal", method="POST", body={"task": "B-002"})
        self.assertEqual(code, 200)
        ow.assert_called_once_with("B-002")

        with mock.patch.object(ui, "list_sessions", return_value={"dev-B-002"}), \
                mock.patch.object(ui.util, "run", return_value=_done(0)):
            code, body = self.req("/api/remove", method="POST", body={"project": "demo", "task": "B-002"})
        self.assertEqual((code, json.loads(body)["closed"]), (200, ["dev-B-002"]))
        self.assertEqual(json.loads(self.req("/api/tasks")[1])["tasks"], [])   # 看板上已看不到

    def test_post_body_limit(self):
        code, _ = self.req("/api/queue", method="POST", body={"task": "B-002", "reason": "x" * 9000})
        self.assertEqual(code, 413)


if __name__ == "__main__":
    unittest.main()
