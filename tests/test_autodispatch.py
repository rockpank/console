"""自動派工（console_cli/autodispatch.py）測試：不碰 tmux、真實用量。"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from console_cli import autodispatch as ad, ui  # noqa: E402
from console_cli.config import Config  # noqa: E402

BACKLOG = """| ID | 類型 | 標題 | 依賴 | 狀態 |
|---|---|---|---|---|
| B-001 | 缺陷 | a | 無 | 待辦 |
| B-002 | 缺陷 | b | 無 | 待辦 |
| B-003 | 缺陷 | c | 待決：Q1 | 待辦 |
| B-004 | 缺陷 | d | 無 | 完成 |
| B-005 | 缺陷 | e | 無 | 待辦 |
| B-006 | 缺陷 | f | 無 | 待辦 |
"""


def view(pct=50.0, source="statusline", stale=False, paused=False):
    return {"quotas": [{"key": "five_hour", "pct": pct, "source": source, "stale": stale}],
            "guard": {"paused": paused}}


class AutoBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "projects" / "demo").mkdir(parents=True)
        (root / "projects" / "demo" / "backlog.md").write_text(BACKLOG, encoding="utf-8")
        (root / "projects" / "demo" / "profile.md").write_text("# demo\n", encoding="utf-8")
        self.cfg = Config({"console": {"runtime_dir": str(root / "runtime"), "projects_dir": str(root / "projects")},
                           "projects": {"demo": {}}, "autodispatch": {"enabled": True}})

    def tearDown(self):
        self.tmp.cleanup()

    def ev(self, v, live=(), now=10_000.0):
        return ad.evaluate(self.cfg, v, set(live), now)


class EvaluateTests(AutoBase):
    def test_below_threshold_asks_pm_to_pick_without_any_queue(self):
        d = self.ev(view(40))
        self.assertTrue(d["go"])
        self.assertEqual((d["project"], d["count"]), ("demo", 3))                    # min(空位 3, 每批 3, 可挑 4)
        self.assertEqual(d["candidates"], ["B-001", "B-002", "B-005", "B-006"])      # 略過待決、已完成

    def test_nothing_ready_never_dispatches(self):
        only_blocked = ("| ID | 類型 | 標題 | 依賴 | 狀態 |\n|---|---|---|---|---|\n"
                        "| B-003 | 缺陷 | c | 待決：Q1 | 待辦 |\n| B-004 | 缺陷 | d | 無 | 完成 |\n")
        (self.cfg.projects_dir / "demo" / "backlog.md").write_text(only_blocked, encoding="utf-8")   # 只剩待決、已完成
        d = self.ev(view(10))
        self.assertFalse(d["go"])
        self.assertIn("沒有可派的項目", d["reason"])

    def test_ready_items_skip_undecided_and_not_todo(self):
        self.assertEqual(ad.ready_items(self.cfg, "demo"), ["B-001", "B-002", "B-005", "B-006"])

    def test_at_or_above_threshold_waits(self):
        self.assertFalse(self.ev(view(70))["go"])
        self.assertFalse(self.ev(view(85))["go"])
        self.assertTrue(self.ev(view(69.9))["go"])

    def test_unknown_or_stale_or_estimated_quota_never_dispatches(self):
        self.assertFalse(self.ev(view(None))["go"])
        self.assertFalse(self.ev(view(10, source="estimate"))["go"])
        self.assertFalse(self.ev(view(10, stale=True))["go"])
        self.assertFalse(self.ev({"quotas": [], "guard": {"paused": False}})["go"])

    def test_guard_paused_blocks(self):
        self.assertFalse(self.ev(view(10, paused=True))["go"])

    def test_disabled_by_default(self):
        self.cfg.raw["autodispatch"] = {}
        self.assertFalse(self.ev(view(10))["go"])

    def test_batch_session_alone_no_longer_blocks(self):
        # 同專案可並行：不再因為有 dev-<專案>-b… 對話就擋，改看駐列佔用
        self.assertTrue(self.ev(view(10), live=["dev-demo-b101010"])["go"])


class SlotTests(AutoBase):
    def run_task(self, code, **kw):
        td = self.cfg.projects_dir / "demo" / "tasks" / code
        td.mkdir(parents=True, exist_ok=True)
        (td / "impl-notes.md").write_text("---\nstatus: done\n---\n", encoding="utf-8")
        if kw.get("escalated"):
            (td / "escalation.md").write_text("---\nresume_at: 開發中\n---\n", encoding="utf-8")

    def test_items_limited_by_free_slots(self):
        self.cfg.raw["autodispatch"]["slots"] = 3
        self.run_task("B-100")                         # 一個進行中 → 剩 2 個空位
        d = self.ev(view(10))
        self.assertEqual(d["count"], 2)

    def test_full_slots_never_dispatch(self):
        self.cfg.raw["autodispatch"]["slots"] = 2
        self.run_task("B-100")
        self.run_task("B-101")
        d = self.ev(view(10))
        self.assertFalse(d["go"])
        self.assertIn("駐列已滿（2／2）", d["reason"])

    def test_zero_slots_never_dispatch(self):
        self.cfg.raw["autodispatch"]["slots"] = 0
        self.assertFalse(self.ev(view(10))["go"])

    def test_escalated_and_held_tasks_free_their_slot(self):
        self.cfg.raw["autodispatch"]["slots"] = 1
        self.run_task("B-100", escalated=True)         # 等你裁示：不佔駐列
        self.assertTrue(self.ev(view(10))["go"])

    def test_slot_frees_when_task_finishes(self):
        self.cfg.raw["autodispatch"]["slots"] = 1
        self.run_task("B-100")
        self.assertFalse(self.ev(view(10))["go"])
        (self.cfg.projects_dir / "demo" / "backlog.md").write_text(
            BACKLOG.replace("| B-004 | 缺陷 | d | 無 | 完成 |", "| B-004 | 缺陷 | d | 無 | 完成 |\n| B-100 | 缺陷 | x | 無 | 完成 |"),
            encoding="utf-8")
        self.assertTrue(self.ev(view(10))["go"])       # 完成了，空位出來

    def test_just_launched_slots_count_until_grace_ends(self):
        self.cfg.raw["autodispatch"]["slots"] = 3
        ad._write(self.cfg.runtime_dir / ad.STATE_FILE,
                  {"last_at": 0, "launched": [{"project": "demo", "count": 2, "baseline": 0, "at": 9_000.0}]})
        self.assertEqual(self.ev(view(10), now=10_000.0)["count"], 1)    # 佔 2 個、剩 1 個
        self.assertEqual(self.ev(view(10), now=9_000.0 + ad.LAUNCH_GRACE + 1)["count"], 3)

    def test_launched_slots_are_not_double_counted_once_tasks_show_on_board(self):
        self.cfg.raw["autodispatch"]["slots"] = 4
        ad._write(self.cfg.runtime_dir / ad.STATE_FILE,
                  {"last_at": 0, "launched": [{"project": "demo", "count": 2, "baseline": 0, "at": 9_000.0}]})
        self.run_task("B-100")                       # 派出的 2 個名額已有 1 個出現在看板
        occ = ad.occupancy(self.cfg, set(), 10_000.0)
        self.assertEqual((len(occ["running"]), occ["pending"], occ["count"]), (1, [("demo", 1)], 2))
        self.run_task("B-101")
        self.run_task("B-102")                       # 多於派出的名額：不會變負數
        self.assertEqual(ad.occupancy(self.cfg, set(), 10_000.0)["count"], 3)

    def test_baseline_ignores_tasks_already_running_before_launch(self):
        self.cfg.raw["autodispatch"]["slots"] = 4
        self.run_task("B-100")                       # 派工前就在跑
        ad._write(self.cfg.runtime_dir / ad.STATE_FILE,
                  {"last_at": 0, "launched": [{"project": "demo", "count": 2, "baseline": 1, "at": 9_000.0}]})
        self.assertEqual(ad.occupancy(self.cfg, set(), 10_000.0)["count"], 3)    # 1 進行中 + 2 名額


class RuntimeSettingsTests(AutoBase):
    def test_ui_settings_override_config(self):
        self.cfg.raw["autodispatch"] = {"enabled": False, "slots": 5}
        ad.save_settings(self.cfg, enabled=True, slots=2)
        conf = ad.settings(self.cfg)
        self.assertEqual((conf["enabled"], conf["slots"]), (True, 2))

    def test_save_settings_rejects_bad_values(self):
        for bad in (-1, ad.SLOTS_MAX + 1, 2.5, "3", True):
            with self.assertRaises(ad.ConsoleError):
                ad.save_settings(self.cfg, slots=bad)
        with self.assertRaises(ad.ConsoleError):
            ad.save_settings(self.cfg, enabled="yes")

    def test_corrupt_runtime_file_falls_back_to_config(self):
        (self.cfg.runtime_dir).mkdir(parents=True, exist_ok=True)
        (self.cfg.runtime_dir / ad.SETTINGS_FILE).write_text("{壞掉", encoding="utf-8")
        self.assertEqual(ad.settings(self.cfg)["slots"], ad.DEFAULTS["slots"])

    def test_save_wakes_background_loop(self):
        ad._wake.clear()
        ad.save_settings(self.cfg, slots=1)
        self.assertTrue(ad._wake.is_set())
        ad._wake.clear()

    def test_tick_does_nothing_when_disabled(self):
        ad.save_settings(self.cfg, enabled=False)
        with mock.patch.object(ad.usage, "view") as v, mock.patch.object(ad.ui, "launch_batch") as lb:
            d = ad.tick(self.cfg, 10_000.0)
        self.assertFalse(d["go"])
        v.assert_not_called()
        lb.assert_not_called()

    def test_status_reports_occupancy_and_reason(self):
        ad.save_settings(self.cfg, slots=2)
        with mock.patch.object(ad.usage, "view", return_value=view(40)), mock.patch.object(ad.ui, "list_sessions", return_value=set()):
            st = ad.status(self.cfg, 10_000.0)
        self.assertEqual((st["slots"], st["occupied"], st["will_dispatch"]), (2, 0, True))
        self.assertEqual(st["next"], {"project": "demo", "count": 2})
        self.assertEqual(st["ready"]["demo"][0], "B-001")
        self.assertNotIn("queue", st)

    def test_settings_clamped(self):
        self.cfg.raw["autodispatch"] = {"enabled": True, "batch_size": 99, "interval": 1, "below_percent": 500}
        conf = ad.settings(self.cfg)
        self.assertEqual((conf["batch_size"], conf["interval"], conf["below_percent"]), (ui._BATCH_MAX, 30, 100.0))
        self.cfg.raw["autodispatch"] = {"slots": 999}
        self.assertEqual(ad.settings(self.cfg)["slots"], ad.SLOTS_MAX)


class TickTests(AutoBase):
    def run_tick(self, now):
        with mock.patch.object(ad.usage, "view", return_value=view(30)), \
             mock.patch.object(ad.ui, "list_sessions", return_value=set()), \
             mock.patch.object(ad.ui, "launch_batch", return_value={"session": "dev-demo-b1"}) as lb:
            return ad.tick(self.cfg, now), lb

    def test_dispatch_asks_pm_with_go_and_cools_down(self):
        d, lb = self.run_tick(10_000.0)
        self.assertTrue(d["go"])
        lb.assert_called_once_with(self.cfg, "demo", [], go=True, auto=3)    # 不指定項目：由專案管理員挑
        d2, lb2 = self.run_tick(10_100.0)           # 冷卻中
        self.assertFalse(d2["go"])
        lb2.assert_not_called()
        d3, lb3 = self.run_tick(10_000.0 + 1801)     # 冷卻與寬限都過了，但局面沒變：專案管理員看過了，不再派
        self.assertFalse(d3["go"])
        self.assertIn("局面沒有變", d3["reason"])
        lb3.assert_not_called()

    def settle(self):
        """派一次，並讓冷卻與寬限都過去。"""
        self.run_tick(10_000.0)
        return 10_000.0 + 1801

    def test_unchanged_situation_is_never_relaunched_however_often_it_ticks(self):
        later = self.settle()
        for i in range(5):
            d, lb = self.run_tick(later + i * 3600)
            self.assertFalse(d["go"])
            lb.assert_not_called()

    def test_relaunch_when_pm_picked_items_so_backlog_changed(self):
        later = self.settle()
        picked = BACKLOG.replace("| B-001 | 缺陷 | a | 無 | 待辦 |", "| B-001 | 缺陷 | a | 無 | 規劃中 |")
        (self.cfg.projects_dir / "demo" / "backlog.md").write_text(picked, encoding="utf-8")
        d, lb = self.run_tick(later)
        self.assertTrue(d["go"])
        lb.assert_called_once()

    def test_relaunch_when_a_blocking_question_is_answered(self):
        later = self.settle()
        answered = BACKLOG.replace("| 待決：Q1 | 待辦 |", "| 無 | 待辦 |")
        (self.cfg.projects_dir / "demo" / "backlog.md").write_text(answered, encoding="utf-8")
        d, lb = self.run_tick(later)
        self.assertTrue(d["go"])
        lb.assert_called_once()

    def test_relaunch_when_the_remote_base_moves_after_a_merge_and_push(self):
        later = self.settle()
        with mock.patch.object(ad, "_origin_head", return_value="newcommit"):
            d, lb = self.run_tick(later)
        self.assertTrue(d["go"])
        lb.assert_called_once()

    def test_relaunch_when_a_running_task_finishes(self):
        later = self.settle()
        before = ad.fingerprint(self.cfg, "demo", [{"project": "demo", "task": "B-001", "group": "run"}])
        after = ad.fingerprint(self.cfg, "demo", [])
        self.assertNotEqual(before, after)

    def test_a_nothing_picked_launch_after_a_change_settles_again(self):
        """變了就派一次；專案管理員這次又挑不出來（backlog 沒再變）→ 之後不再派，一次變化最多浪費一次。"""
        later = self.settle()
        with mock.patch.object(ad, "_origin_head", return_value="newcommit"):
            d, _ = self.run_tick(later)
            self.assertTrue(d["go"])
            d2, lb2 = self.run_tick(later + 1801)
        self.assertFalse(d2["go"])
        lb2.assert_not_called()

    def test_fingerprints_are_kept_per_project_in_state(self):
        self.settle()
        state = ad._read(self.cfg.runtime_dir / ad.STATE_FILE, {})
        self.assertEqual(list(state["fingerprints"]), ["demo"])
        self.assertEqual(len(state["fingerprints"]["demo"]), 16)

    def test_missing_or_broken_repo_only_loses_one_change_signal(self):
        self.cfg.raw["projects"]["demo"] = {"repo": "/nonexistent/path", "base_branch": "master"}
        self.assertEqual(ad._origin_head(self.cfg, "demo"), "")
        self.assertEqual(len(ad.fingerprint(self.cfg, "demo", [])), 16)

    def test_tick_records_launch_so_slots_stay_taken(self):
        self.run_tick(10_000.0)
        state = ad._read(self.cfg.runtime_dir / ad.STATE_FILE, {})
        self.assertEqual((state["launched"][0]["project"], state["launched"][0]["count"], state["launched"][0]["baseline"]),
                         ("demo", 3, 0))

    def test_queue_api_is_gone(self):
        for name in ("queue_add", "queue_remove", "load_queue", "QUEUE_FILE"):
            self.assertFalse(hasattr(ad, name), name)


if __name__ == "__main__":
    unittest.main()
