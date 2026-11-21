"""用量帳本（console_cli/ledger.py）測試。"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from console_cli import ledger  # noqa: E402
from console_cli.config import Config  # noqa: E402
from console_cli.util import ConsoleError  # noqa: E402


class LedgerBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Config({"console": {"runtime_dir": str(Path(self.tmp.name) / "runtime"),
                                       "projects_dir": str(Path(self.tmp.name) / "projects")}, "projects": {}})

    def tearDown(self):
        self.tmp.cleanup()

    def agent(self, now, **kw):
        base = dict(project="demo", task="B-1", round="R1", stage="implement", role="engineer", tokens=1000, calls=10)
        base.update(kw)
        return ledger.add(self.cfg, "agent", now=now, **base)


class AddTests(LedgerBase):
    def test_agent_and_wait_are_appended_as_json_lines(self):
        self.agent(1.0, budget=20, outcome="pass", note="一句話")
        ledger.add(self.cfg, "wait", now=2.0, project="demo", task="B-1", round="R1", reason="問使用者 Q1")
        recs = ledger.load(self.cfg)
        self.assertEqual([r["kind"] for r in recs], ["agent", "wait"])
        self.assertEqual((recs[0]["tokens"], recs[0]["budget"], recs[0]["outcome"]), (1000, 20, "pass"))
        self.assertFalse(recs[0]["rework"])

    def test_rejects_wrong_types_and_missing_fields_instead_of_fixing_them(self):
        bad = [dict(tokens="12"), dict(tokens=-1), dict(tokens=True), dict(calls=None), dict(outcome="done"),
               dict(stage=""), dict(role=""), dict(task=""), dict(round=""), dict(duration_ms=1.5), dict(budget=-3)]
        for kw in bad:
            with self.assertRaises(ConsoleError, msg=str(kw)):
                self.agent(1.0, **kw)
        with self.assertRaises(ConsoleError):
            ledger.add(self.cfg, "wait", project="demo", task="B-1", round="R1", reason="")
        with self.assertRaises(ConsoleError):
            ledger.add(self.cfg, "other", task="B-1", round="R1")
        self.assertEqual(ledger.load(self.cfg), [])        # 被拒的一筆都沒寫進去

    def test_note_is_truncated_and_broken_lines_are_skipped_on_load(self):
        self.agent(1.0, note="x" * 500)
        with ledger.path(self.cfg).open("a", encoding="utf-8") as fh:
            fh.write("不是 JSON\n{\"kind\": \"agent\"\n[1,2]\n{\"kind\": \"unknown\"}\n")
        recs = ledger.load(self.cfg)
        self.assertEqual(len(recs), 1)
        self.assertEqual(len(recs[0]["note"]), 200)

    def test_missing_ledger_file_is_just_empty(self):
        self.assertEqual(ledger.load(self.cfg), [])
        self.assertEqual(ledger.summarize([])["total"]["tokens"], 0)


class SummaryTests(LedgerBase):
    def fill(self):
        self.agent(1.0, tokens=1000, calls=10, budget=20, duration_ms=60_000)
        self.agent(2.0, tokens=3000, calls=30, budget=20, outcome="blocked", rework=True, duration_ms=120_000)   # 超預算、重工
        self.agent(3.0, round="R2", stage="qa", role="qa-engineer", tokens=2000, calls=5, outcome="fail")
        ledger.add(self.cfg, "wait", now=4.0, project="demo", task="B-1", round="R1", reason="Q1 要使用者決定")
        ledger.add(self.cfg, "wait", now=5.0, project="demo", task="B-2", round="R2", reason="第 2 輪失敗升級")

    def test_totals_rework_over_budget_blocked_and_waits(self):
        self.fill()
        t = ledger.summarize(ledger.load(self.cfg))["total"]
        self.assertEqual((t["agents"], t["tokens"], t["calls"]), (3, 6000, 45))
        self.assertEqual((t["rework_tokens"], t["rework_pct"]), (3000, 50.0))
        self.assertEqual((t["blocked"], t["failed"], t["over_budget"], t["waits"]), (1, 1, 1, 2))
        self.assertEqual(t["duration_ms"], 180_000)         # 沒有耗時的那筆不計

    def test_rounds_keep_first_seen_order_and_count_their_own_waits(self):
        self.fill()
        rounds = ledger.summarize(ledger.load(self.cfg))["rounds"]
        self.assertEqual(list(rounds), ["R1", "R2"])
        self.assertEqual((rounds["R1"]["tokens"], rounds["R1"]["waits"]), (4000, 1))
        self.assertEqual((rounds["R2"]["tokens"], rounds["R2"]["waits"]), (2000, 1))

    def test_by_stage_and_role_and_costliest_ignore_waits(self):
        self.fill()
        s = ledger.summarize(ledger.load(self.cfg))
        self.assertEqual(s["by_stage"]["implement"]["tokens"], 4000)
        self.assertEqual(s["by_role"]["qa-engineer"]["agents"], 1)
        self.assertEqual([c["tokens"] for c in s["costliest"]], [3000, 2000, 1000])
        self.assertEqual(len(s["waits"]), 2)

    def test_select_filters_by_task_round_and_time(self):
        self.fill()
        recs = ledger.load(self.cfg)
        self.assertEqual(len(ledger.select(recs, task="B-2")), 1)
        self.assertEqual(len(ledger.select(recs, round_name="R1")), 3)
        self.assertEqual(len(ledger.select(recs, since=3.0)), 3)

    def test_render_mentions_every_number_a_review_needs(self):
        self.fill()
        text = ledger.render(ledger.summarize(ledger.load(self.cfg)))
        for needle in ("3 次子代理", "6k tokens", "重工：3k tokens（50.0%）", "超出工具呼叫預算 1 次",
                       "停下來等使用者 2 次", "R1：", "R2：", "Q1 要使用者決定", "第 2 輪失敗升級"):
            self.assertIn(needle, text)

    def test_zero_tokens_does_not_divide_by_zero(self):
        self.agent(1.0, tokens=0, calls=0, rework=True)
        self.assertEqual(ledger.summarize(ledger.load(self.cfg))["total"]["rework_pct"], 0.0)


class DueTests(LedgerBase):
    def due(self, **kw):
        return ledger.due(ledger.load(self.cfg), **kw)

    def test_quiet_small_round_is_not_due(self):
        self.agent(1.0, tokens=50_000, calls=10, budget=20)
        d = self.due()
        self.assertFalse(d["due"])
        self.assertEqual(d["reasons"], [])

    def test_each_trigger_alone_makes_it_due(self):
        self.agent(1.0, outcome="fail")
        self.assertIn("失敗 1", self.due()["reasons"][0])

    def test_blocked_over_budget_waits_and_tokens_are_triggers(self):
        cases = [dict(outcome="blocked"), dict(calls=30, budget=20), dict(tokens=300_000)]
        for kw in cases:
            with tempfile.TemporaryDirectory() as tmp:
                cfg = Config({"console": {"runtime_dir": tmp, "projects_dir": tmp}, "projects": {}})
                base = dict(project="demo", task="B-1", round="R1", stage="implement", role="engineer", tokens=1000, calls=10)
                base.update(kw)
                ledger.add(cfg, "agent", now=1.0, **base)
                self.assertTrue(ledger.due(ledger.load(cfg))["due"], kw)

    def test_one_wait_is_normal_two_are_a_trigger(self):
        ledger.add(self.cfg, "wait", now=1.0, project="demo", task="B-1", round="R1", reason="Q1")
        self.assertFalse(self.due()["due"])
        ledger.add(self.cfg, "wait", now=2.0, project="demo", task="B-1", round="R1", reason="Q2")
        self.assertTrue(self.due()["due"])

    def test_a_review_record_resets_the_window(self):
        self.agent(1.0, outcome="fail", tokens=400_000)
        self.assertTrue(self.due()["due"])
        self.agent(2.0, stage="review", role="process-optimizer", tokens=27_000, calls=6)
        d = self.due()
        self.assertFalse(d["due"])
        self.assertEqual(d["since"]["agents"], 0)          # 覆盤本身不算進下一個視窗
        self.agent(3.0, tokens=1000)
        self.assertEqual(self.due()["since"]["agents"], 1)


if __name__ == "__main__":
    unittest.main()
