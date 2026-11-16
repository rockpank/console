"""用量監控：紀錄去重與增量讀取、額度視窗、快照、告警、statusline 掛鉤。全是合成資料，不碰真實紀錄。"""
import json
import os
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from console_cli import usage  # noqa: E402

SID = "11111111-aaaa-bbbb-cccc-222222222222"
SID2 = "33333333-aaaa-bbbb-cccc-444444444444"
NOW = 1_800_000_000.0   # 固定「現在」，讓視窗邊界可預期


def iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def line(obj: dict) -> str:
    return json.dumps(obj, separators=(",", ":"))   # 跟 Claude Code 一樣是緊湊 JSON


def assistant(rid, mid, ts, session=SID, inp=10, cc=100, cr=1000, out=50, model="claude-test-1", sidechain=False):
    return line({"type": "assistant", "requestId": rid, "sessionId": session, "isSidechain": sidechain,
                 "timestamp": iso(ts), "message": {"id": mid, "model": model, "role": "assistant",
                 "usage": {"input_tokens": inp, "cache_creation_input_tokens": cc, "cache_read_input_tokens": cr,
                           "output_tokens": out}}})


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "projects"
        self.proj = self.root / "-some-project"
        self.proj.mkdir(parents=True)
        self.runtime = Path(self.tmp.name) / "runtime"
        self.file = self.proj / f"{SID}.jsonl"

    def write(self, *lines, path=None, mode="w"):
        with open(path or self.file, mode, encoding="utf-8") as fh:
            fh.write("".join(l + "\n" for l in lines))
        self.touch(path or self.file)

    @staticmethod
    def touch(path):
        os.utime(path, (NOW, NOW))   # 測試用固定的「現在」，檔案時間要對得上，否則會被當成太舊而跳過

    def index(self):
        idx = usage.Index(self.root)
        idx.refresh(NOW)
        return idx

    def view(self, idx=None, cfg=None):
        return usage.summarize(idx or self.index(), cfg or {}, self.runtime, now=NOW)


class IndexTests(Base):
    def test_duplicate_lines_of_one_response_count_once(self):
        # 同一則回覆的每個內容區塊都會寫一行，usage 重複；串流中途的行 output 較小，取最大
        self.write(assistant("r1", "m1", NOW - 60, out=10), assistant("r1", "m1", NOW - 59, out=50),
                   assistant("r1", "m1", NOW - 58, out=50), assistant("r2", "m2", NOW - 30, out=7))
        records, _, _ = self.index().snapshot()
        self.assertEqual(len(records), 2)
        self.assertEqual(sorted(r[6] for r in records), [7, 50])

    def test_incremental_and_partial_last_line(self):
        self.write(assistant("r1", "m1", NOW - 60))
        idx = self.index()
        self.assertEqual(len(idx.snapshot()[0]), 1)
        with open(self.file, "a", encoding="utf-8") as fh:   # 新增一行，但最後一行還沒寫完
            fh.write(assistant("r2", "m2", NOW - 50) + "\n" + assistant("r3", "m3", NOW - 40)[:30])
        self.touch(self.file)
        idx.refresh(NOW)
        self.assertEqual(len(idx.snapshot()[0]), 2)           # 不完整的行不處理，也不報錯
        with open(self.file, "a", encoding="utf-8") as fh:
            fh.write(assistant("r3", "m3", NOW - 40)[30:] + "\n")
        self.touch(self.file)
        idx.refresh(NOW)
        self.assertEqual(len(idx.snapshot()[0]), 3)

    def test_truncated_file_is_reread(self):
        self.write(assistant("r1", "m1", NOW - 60), assistant("r2", "m2", NOW - 50))
        idx = self.index()
        self.write(assistant("r9", "m9", NOW - 10))
        idx.refresh(NOW)
        self.assertIn(("r9", "m9"), idx.records)

    def test_subagent_usage_counts_toward_parent_session_and_not_context(self):
        sub = self.proj / SID / "subagents"
        sub.mkdir(parents=True)
        self.write(assistant("r1", "m1", NOW - 100, cr=2000))
        self.write(assistant("r2", "m2", NOW - 50, session="agent-own-id", cr=9_000_000, sidechain=True),
                   path=sub / "agent-abc.jsonl")
        records, _, _ = self.index().snapshot()
        self.assertEqual({r[1] for r in records}, {SID})      # 以資料夾的 session 為準
        view = self.view()
        self.assertEqual(view["sessions"][0]["ctx_tokens"], 10 + 100 + 2000)   # context 只看主對話
        self.assertEqual(view["sessions"][0]["tokens_5h"], 2 * (10 + 100 + 50))  # 用量兩邊都算（不含快取讀取）

    def test_synthetic_error_messages_have_no_usage(self):
        self.write(assistant("r1", "m1", NOW - 60, model="<synthetic>"))
        self.assertEqual(self.index().snapshot()[0], [])

    def test_only_dev_titles_are_kept(self):
        self.write(line({"type": "custom-title", "customTitle": "dev-3382", "sessionId": SID}),
                   line({"type": "custom-title", "customTitle": "某客戶的薪資問題", "sessionId": SID2}),
                   assistant("r1", "m1", NOW - 60), assistant("r2", "m2", NOW - 50, session=SID2))
        view = self.view()
        names = {s["name"] for s in view["sessions"]}
        self.assertEqual(names, {"dev-3382", "其他對話 33333333"})
        self.assertNotIn("薪資", json.dumps(view, ensure_ascii=False))   # 別的標題可能含需求內容，絕不外流

    def test_no_message_content_in_view(self):
        secret = "員工A123456789的薪資是五萬"
        self.write(line({"type": "user", "sessionId": SID, "message": {"role": "user", "content": secret}}),
                   assistant("r1", "m1", NOW - 60))
        self.assertNotIn(secret, json.dumps(self.view(), ensure_ascii=False))


class WindowTests(Base):
    def test_block_starts_on_the_hour_and_ends_after_five_hours(self):
        base = NOW - NOW % 3600
        block = usage.current_block([base + 1500, base + 3000], base + 4000)
        self.assertEqual(block, (base, base + 5 * 3600))

    def test_new_block_after_gap_and_none_when_expired(self):
        base = NOW - NOW % 3600
        old, new = base - 6 * 3600 + 100, base + 100
        self.assertEqual(usage.current_block([old, new], new + 10)[0], base)
        self.assertIsNone(usage.current_block([old], base))             # 已過期
        self.assertIsNone(usage.current_block([], base))

    def test_estimate_percent_from_config_limits(self):
        self.write(assistant("r1", "m1", NOW - 600, inp=0, cc=0, cr=500_000, out=1000))   # 快取讀取不計入
        v = self.view(cfg={"usage": {"five_hour_tokens": 2000, "weekly_tokens": 4000}})
        q5, q7 = v["quotas"]
        self.assertEqual((q5["source"], q5["pct"], q5["used_tokens"]), ("estimate", 50.0, 1000))
        self.assertEqual(q7["pct"], 25.0)

    def test_no_limit_and_no_snapshot_gives_no_percent(self):
        self.write(assistant("r1", "m1", NOW - 600))
        q5 = self.view()["quotas"][0]
        self.assertIsNone(q5["pct"])
        self.assertGreater(q5["used_tokens"], 0)

    def test_snapshot_overrides_estimate_and_newest_wins(self):
        self.write(assistant("r1", "m1", NOW - 600))
        older = {"session": SID, "at": NOW - 120, "five_hour": {"pct": 10.0, "resets_at": NOW + 3600}}
        newer = {"session": SID2, "at": NOW - 30, "five_hour": {"pct": 93.0, "resets_at": NOW + 1800}}
        usage.write_snapshot(self.runtime, older)
        usage.write_snapshot(self.runtime, newer)
        q5 = self.view(cfg={"usage": {"five_hour_tokens": 10**9}})["quotas"][0]
        self.assertEqual((q5["source"], q5["pct"], q5["data_age"]), ("statusline", 93.0, 30))
        self.assertEqual(q5["resets_at"], NOW + 1800)

    def test_expired_snapshot_window_is_ignored(self):
        usage.write_snapshot(self.runtime, {"session": SID, "at": NOW - 60, "five_hour": {"pct": 99.0, "resets_at": NOW - 1}})
        self.assertIsNone(self.view()["quotas"][0]["pct"])


class AlertTests(Base):
    def alerts(self, pct5=None, **kw):
        if pct5 is not None:
            usage.write_snapshot(self.runtime, {"session": SID2, "at": NOW - 5, "five_hour": {"pct": pct5, "resets_at": NOW + 600}})
        return self.view(**kw)["alerts"]

    def test_threshold_is_inclusive_and_levels(self):
        self.assertEqual(self.alerts(89.9), [])
        warn = self.alerts(90.0)
        self.assertEqual([(a["level"], a["id"].split(":")[0]) for a in warn], [("warn", "quota")])
        crit = self.alerts(100.0)
        self.assertEqual(crit[0]["level"], "crit")

    def test_custom_threshold(self):
        usage.write_snapshot(self.runtime, {"session": SID2, "at": NOW - 5, "five_hour": {"pct": 80.0, "resets_at": NOW + 600}})
        self.assertEqual(len(self.view(cfg={"usage": {"alert_percent": 75}})["alerts"]), 1)
        self.assertEqual(self.view()["alerts"], [])

    def test_alert_id_is_stable_within_one_window(self):
        a = self.alerts(95.0)[0]["id"]
        b = self.alerts(97.0)[0]["id"]
        self.assertEqual(a, b)   # 同一個視窗內不會一直重複通知

    def test_context_alert_needs_a_trusted_window_size(self):
        # 沒有快照也沒有明確設定：就算算出 99% 也不告警（上限是猜的）
        self.write(line({"type": "custom-title", "customTitle": "dev-5", "sessionId": SID}),
                   assistant("r1", "m1", NOW - 60, inp=0, cc=0, cr=199_000))
        v = self.view()
        self.assertFalse(v["sessions"][0]["ctx_known"])
        self.assertEqual(v["alerts"], [])
        # 使用者明確設定上限 → 可告警
        v = self.view(cfg={"usage": {"context_window": 200_000}})
        self.assertTrue(v["sessions"][0]["ctx_known"])
        self.assertEqual([a["id"] for a in v["alerts"]], [f"ctx:{SID[:8]}"])
        self.assertIn("dev-5", v["alerts"][0]["title"])

    def test_context_alert_from_snapshot_and_only_for_live_sessions(self):
        self.write(line({"type": "custom-title", "customTitle": "dev-5", "sessionId": SID}),
                   assistant("r1", "m1", NOW - 60, inp=0, cc=0, cr=500_000))
        usage.write_snapshot(self.runtime, {"session": SID, "at": NOW - 10, "ctx_pct": 95.0, "ctx_size": 1_000_000})
        self.assertEqual(len(self.view()["alerts"]), 1)
        # 閒置超過 30 分鐘的對話不告警
        self.write(line({"type": "custom-title", "customTitle": "dev-5", "sessionId": SID}),
                   assistant("r1", "m1", NOW - 3 * 3600, inp=0, cc=0, cr=500_000))
        self.assertEqual(self.view()["alerts"], [])

    def test_rate_limit_rejection_alerts_until_snapshot_shows_recovery(self):
        reject = line({"type": "assistant", "timestamp": iso(NOW - 300), "isApiErrorMessage": True,
                       "message": {"id": "e1", "model": "<synthetic>", "usage": {"input_tokens": 0, "output_tokens": 0}},
                       "quotaLimits": {"status": "rejected", "rateLimitType": "five_hour", "resetsAt": NOW + 3000}})
        self.write(reject)   # 這行同時是 assistant＋usage＋quotaLimits：不能被當成一般用量行吃掉
        v = self.view()
        self.assertEqual([a["level"] for a in v["alerts"]], ["crit"])
        self.assertTrue(v["limits"][0]["active"])
        # 事件之後出現更新的快照、且 5 小時視窗沒滿 → 已恢復
        usage.write_snapshot(self.runtime, {"session": SID2, "at": NOW - 10, "five_hour": {"pct": 4.0, "resets_at": NOW + 9000}})
        v = self.view()
        self.assertEqual(v["alerts"], [])
        self.assertFalse(v["limits"][0]["active"])

    def test_unknown_view_keys(self):
        v = self.view()
        for key in ("quotas", "sessions", "tasks", "hourly", "models", "limits", "alerts", "alert_percent"):
            self.assertIn(key, v)
        self.assertEqual(len(v["hourly"]["tokens"]), 24)


class StaleSnapshotTests(Base):
    """真實發生過的 bug：閒置對話的 statusline 在快取過期等事件會重跑，把「最後一次回應」時的舊額度
    （14:05 的 100%）寫成新快照，蓋掉別的對話較新的數字（30%），面板就在兩者之間亂跳。"""

    def setUp(self):
        super().setUp()
        self.idle = self.proj / f"{SID}.jsonl"     # 這個對話 2 小時前最後一次回應（那時額度是 100%）
        self.busy = self.proj / f"{SID2}.jsonl"    # 這個對話 1 分鐘前才回應（額度已經重置、只剩 30%）
        self.write(assistant("r1", "m1", NOW - 7200, session=SID), path=self.idle)
        self.write(assistant("r2", "m2", NOW - 60, session=SID2, inp=10, cc=100, out=50), path=self.busy)

    def test_idle_session_rewriting_old_numbers_does_not_win(self):
        reset_old, reset_new = NOW - 3600, NOW + 17000
        # busy 先寫（30%），idle 後寫（舊的 100%，但寫入時間較新）
        usage.write_snapshot(self.runtime, {"session": SID2, "at": NOW - 50, "five_hour": {"pct": 30.0, "resets_at": reset_new}})
        usage.write_snapshot(self.runtime, {"session": SID, "at": NOW - 5, "five_hour": {"pct": 100.0, "resets_at": NOW + 600}})
        q5 = self.view()["quotas"][0]
        self.assertEqual((q5["pct"], q5["resets_at"]), (30.0, reset_new))
        self.assertEqual(q5["data_age"], 60)            # 數據是 1 分鐘前的回應，不是 5 秒前的寫入
        self.assertEqual(self.view()["alerts"], [])
        self.assertFalse(self.view()["guard"]["breached"])

    def test_window_tokens_follow_the_real_window_not_the_guessed_block(self):
        reset = NOW + 3 * 3600                              # 真實視窗：reset-5h .. reset
        usage.write_snapshot(self.runtime, {"session": SID2, "at": NOW - 50, "five_hour": {"pct": 30.0, "resets_at": reset}})
        v = self.view()
        self.assertEqual(v["block"]["source"], "statusline")
        self.assertEqual((v["block"]["start"], v["block"]["end"]), (reset - 5 * 3600, reset))
        # 視窗是 NOW-2h..NOW+3h：2 小時前那則（NOW-7200）剛好在邊界上（含），1 分鐘前那則在內 → 兩則都算
        self.assertEqual(v["quotas"][0]["used_tokens"], 2 * (10 + 100 + 50))
        usage.write_snapshot(self.runtime, {"session": SID2, "at": NOW - 40, "five_hour": {"pct": 30.0, "resets_at": reset + 3600}})
        self.assertEqual(self.view()["quotas"][0]["used_tokens"], 160)   # 視窗往後挪 1 小時：舊那則掉出去

    def test_stale_flag_when_newest_data_is_old(self):
        self.write(assistant("r1", "m1", NOW - 7200, session=SID), path=self.idle)
        self.busy.unlink()
        usage.write_snapshot(self.runtime, {"session": SID, "at": NOW - 5, "five_hour": {"pct": 100.0, "resets_at": NOW + 600}})
        q5 = self.view()["quotas"][0]
        self.assertTrue(q5["stale"])                        # 數據是 2 小時前的，要標出來
        self.assertEqual(q5["data_age"], 7200)

    def test_context_snapshot_valid_if_written_after_last_response_even_when_idle(self):
        usage.write_snapshot(self.runtime, {"session": SID, "at": NOW - 7000, "ctx_pct": 33.0, "ctx_size": 1_000_000})
        s = {x["session"]: x for x in self.view()["sessions"]}[SID[:8]]
        self.assertEqual((s["ctx_source"], s["ctx_pct"], s["ctx_known"]), ("statusline", 33.0, True))

    def test_context_snapshot_older_than_last_response_is_ignored(self):
        usage.write_snapshot(self.runtime, {"session": SID2, "at": NOW - 3600, "ctx_pct": 10.0, "ctx_size": 1_000_000})
        s = {x["session"]: x for x in self.view()["sessions"]}[SID2[:8]]
        self.assertEqual(s["ctx_source"], "estimate")       # 快照比最後一次回應舊，不能代表現在

    def test_limit_event_recovered_by_newer_data_even_if_other_snapshot_rewritten_later(self):
        reject = line({"type": "assistant", "timestamp": iso(NOW - 3000), "isApiErrorMessage": True,
                       "message": {"id": "e1", "model": "<synthetic>", "usage": {"input_tokens": 0, "output_tokens": 0}},
                       "quotaLimits": {"status": "rejected", "rateLimitType": "five_hour", "resetsAt": NOW + 900}})
        self.write(rejection := reject, assistant("r1", "m1", NOW - 7200, session=SID), path=self.idle)
        usage.write_snapshot(self.runtime, {"session": SID, "at": NOW - 5, "five_hour": {"pct": 100.0, "resets_at": NOW + 900}})
        usage.write_snapshot(self.runtime, {"session": SID2, "at": NOW - 50, "five_hour": {"pct": 30.0, "resets_at": NOW + 17000}})
        self.assertFalse(self.view()["limits"][0]["active"])
        self.assertEqual(self.view()["alerts"], [])


class GuardTests(Base):
    def put(self, pct5=None, pct7=None, resets5=None):
        snap = {"session": SID2, "at": NOW - 10}
        if pct5 is not None:
            snap["five_hour"] = {"pct": pct5, "resets_at": resets5 or NOW + 3600}
        if pct7 is not None:
            snap["seven_day"] = {"pct": pct7, "resets_at": NOW + 86400}
        usage.write_snapshot(self.runtime, snap)

    def test_pauses_at_threshold_for_either_window(self):
        self.put(pct5=89.9, pct7=10)
        self.assertFalse(self.view()["guard"]["paused"])
        self.put(pct5=90.0)
        g = self.view()["guard"]
        self.assertTrue(g["paused"])
        self.assertEqual((g["reasons"], g["until"]), (["5 小時額度已用 90%"], NOW + 3600))
        self.put(pct5=10, pct7=95)
        self.assertEqual(self.view()["guard"]["reasons"], ["每週額度已用 95%"])

    def test_context_alert_alone_does_not_pause(self):
        self.write(line({"type": "custom-title", "customTitle": "dev-5", "sessionId": SID}),
                   assistant("r1", "m1", NOW - 60, inp=0, cc=0, cr=500_000))
        usage.write_snapshot(self.runtime, {"session": SID, "at": NOW - 10, "ctx_pct": 99.0, "ctx_size": 1_000_000})
        v = self.view()
        self.assertEqual(len(v["alerts"]), 1)               # 有 context 告警
        self.assertFalse(v["guard"]["breached"])            # 但那只影響單一對話，不暫停整條流程

    def test_active_rate_limit_pauses(self):
        self.write(line({"type": "assistant", "timestamp": iso(NOW - 60), "isApiErrorMessage": True,
                         "message": {"id": "e1", "model": "<synthetic>", "usage": {"input_tokens": 0, "output_tokens": 0}},
                         "quotaLimits": {"status": "rejected", "rateLimitType": "five_hour", "resetsAt": NOW + 900}}))
        g = self.view()["guard"]
        self.assertTrue(g["paused"])
        self.assertIn("限流", g["reasons"][0])

    def test_override_lifts_pause_until_expiry_and_is_capped(self):
        self.put(pct5=95.0, resets5=NOW + 20 * 3600)
        until = usage.set_override(self.runtime, True, until=NOW + 20 * 3600, now=NOW)
        self.assertEqual(until, NOW + usage.OVERRIDE_MAX)    # 最久 5 小時，就算額度要 20 小時後才重置
        g = self.view()["guard"]
        self.assertEqual((g["paused"], g["overridden"], g["breached"]), (False, True, True))
        # 過期後恢復暫停
        usage.set_override(self.runtime, True, until=NOW - 1, now=NOW - 10)   # 截止時間已過
        os.utime(self.runtime / usage.GUARD_FILE)
        self.assertTrue(usage.guard({**self.view(), "now": NOW + 99999}, self.runtime)["paused"])
        usage.set_override(self.runtime, False)
        self.assertTrue(self.view()["guard"]["paused"])
        self.assertFalse((self.runtime / usage.GUARD_FILE).exists())

    def test_override_file_is_private_and_garbage_is_ignored(self):
        usage.set_override(self.runtime, True, now=NOW)
        self.assertEqual(oct((self.runtime / usage.GUARD_FILE).stat().st_mode & 0o777), "0o600")
        (self.runtime / usage.GUARD_FILE).write_text("{壞掉")
        self.assertEqual(usage.read_override(self.runtime, NOW), 0.0)

    def test_nothing_to_guard_without_any_quota_data(self):
        g = self.view()["guard"]
        self.assertEqual((g["paused"], g["breached"], g["reasons"]), (False, False, []))


class SummaryTests(Base):
    def test_per_task_totals_and_hourly_series(self):
        self.write(line({"type": "custom-title", "customTitle": "dev-5", "sessionId": SID}),
                   line({"type": "custom-title", "customTitle": "dev-6", "sessionId": SID2}),
                   assistant("r1", "m1", NOW - 60, out=50), assistant("r2", "m2", NOW - 120, out=50, session=SID2))
        v = self.view()
        by = {t["task"]: t for t in v["tasks"]}
        self.assertEqual(set(by), {"5", "6"})
        self.assertEqual(by["5"]["tokens_24h"], 160)
        self.assertEqual(sum(v["hourly"]["tokens"]), 320)
        self.assertEqual(v["models"][0]["model"], "claude-test-1")


class SettingsTests(unittest.TestCase):
    def test_defaults_and_bad_values(self):
        self.assertEqual(usage.settings(None)["alert_percent"], 90)
        bad = usage.settings({"usage": {"alert_percent": 0, "five_hour_tokens": -5, "weekly_tokens": "x"}})
        self.assertEqual((bad["alert_percent"], bad["five_hour_tokens"], bad["weekly_tokens"]), (90, 0, 0))
        self.assertEqual(usage.settings({"usage": {"alert_percent": 150}})["alert_percent"], 90)
        self.assertEqual(usage.settings({"usage": {"alert_percent": 75}})["alert_percent"], 75)

    def test_context_window_explicit_flag(self):
        self.assertFalse(usage.settings({})["context_window_explicit"])
        self.assertFalse(usage.settings({"usage": "壞掉的設定"})["context_window_explicit"])   # 型別不對也不能壞
        self.assertTrue(usage.settings({"usage": {"context_window": 1_000_000}})["context_window_explicit"])


class StatuslineTests(unittest.TestCase):
    PAYLOAD = {
        "session_id": SID, "model": {"id": "claude-test-1", "display_name": "x"},
        "cwd": "/should/not/be/saved", "transcript_path": "/should/not/be/saved", "workspace": {"current_dir": "/nope"},
        "context_window": {"used_percentage": 42.3, "context_window_size": 1_000_000, "current_usage": {"input_tokens": 5}},
        "rate_limits": {"five_hour": {"used_percentage": 91.5, "resets_at": NOW + 3600},
                        "seven_day": {"used_percentage": 40, "resets_at": NOW + 86400}},
    }

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.runtime = Path(self.tmp.name)

    def test_only_numeric_fields_are_stored(self):
        snap = usage.extract_snapshot(self.PAYLOAD, NOW)
        self.assertEqual(set(snap), {"session", "model", "at", "ctx_pct", "ctx_size", "five_hour", "seven_day"})
        self.assertNotIn("should/not", json.dumps(snap))

    def test_bad_session_id_rejected(self):
        for bad in ("../../etc/passwd", "a/b", "", "x" * 100, None, 5):
            self.assertIsNone(usage.extract_snapshot({**self.PAYLOAD, "session_id": bad}, NOW), bad)

    def test_bad_numbers_are_dropped(self):
        payload = {**self.PAYLOAD, "rate_limits": {"five_hour": {"used_percentage": "lots", "resets_at": -1}}}
        snap = usage.extract_snapshot(payload, NOW)
        self.assertNotIn("five_hour", snap)

    def test_run_writes_private_file_and_returns_text(self):
        text = usage.statusline_run(json.dumps(self.PAYLOAD), {}, self.runtime, now=NOW)
        self.assertEqual(text, "⚠ 5h 92% · 7d 40% · ctx 42%")
        path = self.runtime / "usage" / f"{SID}.json"
        self.assertEqual(oct(path.stat().st_mode & 0o777), "0o600")
        self.assertEqual(usage.read_snapshots(self.runtime)[0]["session"], SID)

    def test_no_warning_mark_below_threshold(self):
        payload = {**self.PAYLOAD, "rate_limits": {"five_hour": {"used_percentage": 10, "resets_at": NOW + 5}}}
        self.assertEqual(usage.statusline_run(json.dumps(payload), {}, self.runtime, now=NOW), "5h 10% · ctx 42%")

    def test_garbage_input_is_harmless(self):
        for raw in ("", "not json", "[]", "null", '{"session_id": "../x"}'):
            self.assertEqual(usage.statusline_run(raw, {}, self.runtime, now=NOW), "")
        self.assertFalse((self.runtime / "usage").exists())

    def test_old_snapshots_are_cleaned_up(self):
        usage.statusline_run(json.dumps(self.PAYLOAD), {}, self.runtime, now=NOW)
        old = self.runtime / "usage" / "old-session-id.json"
        old.write_text("{}")
        long_ago = time.time() - 10 * 86400            # 清理用真實時鐘比檔案 mtime
        os.utime(old, (long_ago, long_ago))
        usage.statusline_run(json.dumps({**self.PAYLOAD, "session_id": SID2}), {}, self.runtime, now=NOW + 1)
        self.assertFalse(old.exists())

    def test_corrupt_snapshot_is_skipped(self):
        folder = self.runtime / "usage"
        folder.mkdir()
        (folder / "bad.json").write_text("{not json")
        self.assertEqual(usage.read_snapshots(self.runtime), [])


class FormatTests(unittest.TestCase):
    def test_fmt_tokens(self):
        self.assertEqual([usage.fmt_tokens(n) for n in (0, 999, 1500, 2_500_000)], ["0", "999", "2k", "2.5M"])

    def test_render_text_has_alerts_and_no_content(self):
        view = {"alert_percent": 90, "now": NOW, "limits": [], "sessions": [], "tasks": [],
                "quotas": [{"key": "five_hour", "label": "5 小時額度", "pct": 95.0, "source": "statusline", "data_age": 60,
                            "stale": False, "used_tokens": 5000, "resets_at": NOW + 600}],
                "guard": {"paused": True, "breached": True, "overridden": False, "reasons": ["5 小時額度已用 95%"],
                          "until": NOW + 600, "override_until": None},
                "alerts": [{"id": "x", "level": "warn", "title": "5 小時額度已用 95%", "detail": "達到 90% 門檻"}]}
        text = usage.render_text(view)
        self.assertIn("95%", text)
        self.assertIn("⚠ 5 小時額度已用 95%", text)
        self.assertIn("⏸ 額度保護", text)


if __name__ == "__main__":
    unittest.main()
