"""單元測試（不碰真實 Redmine、docker、資料庫）：python3 -m unittest discover -s tests"""
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import subprocess  # noqa: E402
from datetime import datetime, timedelta  # noqa: E402

from console_cli import envfile, login, redmine, scan, site, status  # noqa: E402
from console_cli.config import Config  # noqa: E402
from console_cli.mask import detect, load_terms, mask_text  # noqa: E402
from console_cli.util import ConsoleError, parse_task, parse_ticket, split_projects  # noqa: E402

# 以下全是假資料
FAKE_ID, FAKE_PHONE, FAKE_MAIL, FAKE_AMOUNT = "A123456789", "0912-345-678", "someone@example.com", "NT$ 50,000"
FAKE_CUSTOMER = "測試客戶股份有限公司"


class _FakeCake(BaseHTTPRequestHandler):
    """模擬 Cake 登入：GET 登入頁、POST checkMfa、POST 登入（成功轉址到首頁）。"""
    mfa = False
    error_text = True  # 失敗時是否帶應用程式的「帳號/密碼錯誤」訊息
    USER, PASSWORD = "fake-user", "fake-pass-not-real"

    def log_message(self, *args):
        pass

    def _send(self, code, body="", headers=()):
        self.send_response(code)
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body.encode())

    def do_GET(self):
        if self.path.startswith("/femas/Accounts/login"):
            self._send(200, '<form id="loginForm"></form>', [("Set-Cookie", "sid=abc; path=/")])
        elif self.path == "/femas/Users/home":
            if "auth=1" in (self.headers.get("Cookie") or ""):
                self._send(200, "<html>home</html>")
            else:
                self._send(302, "", [("Location", "/femas/Accounts/login")])
        else:
            self._send(404)

    def do_POST(self):
        from urllib.parse import parse_qs
        form = parse_qs(self.rfile.read(int(self.headers.get("Content-Length", 0))).decode())
        if self.path.endswith("/checkMfa"):
            self._send(200, json.dumps({"isMfa": 1 if _FakeCake.mfa else 0}))
        elif self.path.endswith("/Accounts/login"):
            good = (form.get("data[Account][username]") == [self.USER]
                    and form.get("data[Account][passwd]") == [self.PASSWORD])
            if good:
                self._send(302, "", [("Location", "/femas/Users/home"), ("Set-Cookie", "auth=1; path=/")])
            else:
                msg = "<div>帳號/密碼錯誤 (密碼大小寫不同)</div>" if _FakeCake.error_text else ""
                self._send(200, '<form id="loginForm"></form>' + msg)
        else:
            self._send(404)


class LoginCheckTests(unittest.TestCase):
    def setUp(self):
        _FakeCake.mfa = False
        _FakeCake.error_text = True
        self.server = HTTPServer(("127.0.0.1", 0), _FakeCake)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.port = self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def _check(self, user, password):
        return login.check_login("local-r1.example.test", self.port, "/femas/", user, password, tls=False)

    def test_success(self):
        ok, detail = self._check(_FakeCake.USER, _FakeCake.PASSWORD)
        self.assertTrue(ok, detail)

    def test_wrong_password_fails_without_leaking(self):
        ok, detail = self._check(_FakeCake.USER, "wrong-secret-xyz")
        self.assertFalse(ok)
        self.assertIn("帳號／密碼錯誤", detail)
        for secret in ("wrong-secret-xyz", _FakeCake.USER, _FakeCake.PASSWORD):
            self.assertNotIn(secret, detail)

    def test_still_on_login_page_without_app_message(self):
        _FakeCake.error_text = False
        ok, detail = self._check(_FakeCake.USER, "wrong-secret-xyz")
        self.assertFalse(ok)
        self.assertIn("仍在登入頁", detail)

    def test_mfa_account_is_rejected(self):
        _FakeCake.mfa = True
        ok, detail = self._check(_FakeCake.USER, _FakeCake.PASSWORD)
        self.assertFalse(ok)
        self.assertIn("MFA", detail)

    def test_connection_error(self):
        self.server.shutdown()
        self.server.server_close()
        ok, detail = self._check("u", "p")
        self.assertFalse(ok)
        self.assertIn("連線錯誤", detail)
        self.server = HTTPServer(("127.0.0.1", 0), _FakeCake)  # 讓 tearDown 能正常關閉
        threading.Thread(target=self.server.serve_forever, daemon=True).start()


class LoginResultSkipTests(unittest.TestCase):
    def test_skipped_when_creds_missing_or_empty(self):
        with tempfile.TemporaryDirectory() as d:
            cfg = Config({"console": {"worktree_root": d}, "sites": {"test_path": "/femas/"}})
            (Path(d) / "9" / "p").mkdir(parents=True)
            login_cfg = {"creds_file": "e2e.env", "username_key": "U", "password_key": "P"}
            name, passed, detail = site._login_result(cfg, "9", "p", login_cfg, "h", 1)
            self.assertIsNone(passed)
            self.assertIn("未提供", detail)
            (Path(d) / "9" / "p" / "e2e.env").write_text("U=someone\nP=\n", encoding="utf-8")
            self.assertIsNone(site._login_result(cfg, "9", "p", login_cfg, "h", 1)[1])


class DbConfigTests(unittest.TestCase):
    SAMPLE = """class DATABASE_CONFIG {
    var $default = array(
        'host' => 'mysql57',
        'database' => 'main_db',
    );
    var $saas = array(
        'host' => 'mysql57',
        'database' => 'saas_old',
    );
}"""

    def test_read_and_patch_only_saas(self):
        self.assertEqual(site.read_saas_db(self.SAMPLE), "saas_old")
        patched = site.patch_saas_db(self.SAMPLE, "saas_r1")
        self.assertEqual(site.read_saas_db(patched), "saas_r1")
        self.assertIn("'main_db'", patched)

    def test_db_name_validation(self):
        with self.assertRaises(ConsoleError):
            site._check_db_name("x`; drop database y; --")


class _FakeRedmine(BaseHTTPRequestHandler):
    seen_keys = []
    list_paths = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        _FakeRedmine.seen_keys.append(self.headers.get("X-Redmine-API-Key"))
        if self.path.startswith("/issues.json"):
            _FakeRedmine.list_paths.append(self.path)
            offset = int(self.path.split("offset=")[1].split("&")[0]) if "offset=" in self.path else 0
            everything = [
                {"id": 7, "subject": f"{FAKE_CUSTOMER} 的 {FAKE_ID} 請假計算錯誤", "tracker": {"name": "Bug"},
                 "status": {"name": "新建"}, "priority": {"name": "高"}, "updated_on": "2026-11-10T08:00:00Z",
                 "project": {"id": 3, "name": FAKE_CUSTOMER}, "assigned_to": {"id": 1, "name": "王小明"}},
                {"id": 9, "subject": "報表欄位順序", "tracker": {"name": "功能"}, "status": {"name": "處理中"},
                 "priority": {"name": "一般"}, "updated_on": "2026-11-09T08:00:00Z", "project": {"id": 4, "name": "x"}},
            ]
            body = json.dumps({"issues": everything[offset:offset + 1], "total_count": 2}).encode()
        elif self.path.startswith("/issues/7.json"):
            host = f"http://127.0.0.1:{self.server.server_port}"
            issue = {"issue": {
                "id": 7, "subject": f"{FAKE_CUSTOMER} 的 {FAKE_ID} 請假計算錯誤",
                "description": f"員工聯絡 {FAKE_PHONE} / {FAKE_MAIL}，補償 {FAKE_AMOUNT}",
                "tracker": {"name": "Bug"}, "status": {"name": "新建"}, "priority": {"name": "一般"},
                "project": {"id": 3, "name": FAKE_CUSTOMER}, "author": {"id": 11, "name": "王小明"},
                "custom_fields": [{"name": "客戶名稱", "value": FAKE_CUSTOMER}, {"name": "版本", "value": "7.3"}],
                "journals": [{"user": {"id": 12, "name": "李小華"}, "notes": f"已確認 {FAKE_ID}",
                              "details": [{"property": "attr", "name": "status_id", "old_value": "1", "new_value": "2"}]}],
                "attachments": [
                    {"id": 1, "filename": f"{FAKE_CUSTOMER}.log", "filesize": 30, "content_type": "text/plain",
                     "content_url": f"{host}/attachments/download/1/x.log"},
                    {"id": 2, "filename": "截圖.png", "filesize": 4, "content_type": "image/png",
                     "content_url": f"{host}/attachments/download/2/x.png"},
                    {"id": 3, "filename": "evil.txt", "filesize": 4, "content_type": "text/plain",
                     "content_url": "http://example.invalid/steal.txt"},
                    {"id": 4, "filename": "壞掉.log", "filesize": 4, "content_type": "text/plain",
                     "content_url": f"{host}/attachments/download/4/x.log"},  # 下載會回 500
                ]}}
            body = json.dumps(issue).encode()
        elif self.path.startswith("/attachments/download/1/"):
            body = f"user {FAKE_ID} phone {FAKE_PHONE}".encode()
        elif self.path.startswith("/attachments/download/2/"):
            body = b"\x89PNG"
        elif self.path.startswith("/attachments/download/4/"):
            self.send_response(500)
            self.end_headers()
            return
        else:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(body)


class FetchTicketTests(unittest.TestCase):
    def setUp(self):
        self.server = HTTPServer(("127.0.0.1", 0), _FakeRedmine)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Config({
            "console": {"worktree_root": self.tmp.name},
            "redmine": {"base_url": f"http://127.0.0.1:{self.server.server_port}", "api_key_env": "CONSOLE_TEST_KEY"},
        })
        os.environ["CONSOLE_TEST_KEY"] = "test-key-not-real"

    def tearDown(self):
        self.server.shutdown()
        self.tmp.cleanup()
        os.environ.pop("CONSOLE_TEST_KEY", None)

    def test_fetch_is_deidentified_and_safe(self):
        md_path = redmine.fetch_ticket(self.cfg, "7")
        everything = "".join(p.read_text(errors="replace") for p in md_path.parent.rglob("*")
                             if p.is_file() and p.suffix in (".md", ".txt") and "masked" in p.name)
        for secret in (FAKE_ID, FAKE_PHONE, FAKE_MAIL, "50,000", FAKE_CUSTOMER, "王小明", "李小華"):
            self.assertNotIn(secret, everything, f"洩漏：{secret}")
        self.assertIn("project#3", everything)
        self.assertIn("user#11", everything)
        self.assertIn("已略去 1 個", everything)
        masked_att = md_path.parent / "attachments" / "att1.masked.txt"
        self.assertTrue(masked_att.exists())
        self.assertFalse((md_path.parent / "attachments" / "att3.txt").exists(), "不得下載非 Redmine 主機的附件")
        self.assertIn("二進位：未自動讀取", everything)
        self.assertEqual(oct(md_path.stat().st_mode & 0o777), "0o600")
        self.assertEqual(set(_FakeRedmine.seen_keys), {"test-key-not-real"})

    def test_one_failed_attachment_does_not_block_the_ticket(self):
        """用不到的附件下載失敗（HTTP 500）時，工單本身與其他附件照常讀進來。"""
        md_path = redmine.fetch_ticket(self.cfg, "7")
        text = md_path.read_text(encoding="utf-8")
        self.assertIn("略過（下載失敗", text)
        self.assertTrue((md_path.parent / "attachments" / "att1.masked.txt").exists())
        self.assertFalse(list((md_path.parent / "attachments").glob("att4.*")))
        self.assertNotIn("需使用者確認", text)  # 二進位附件只標示未讀，不要求人處理

    def test_list_assigned_is_deidentified_and_paginates(self):
        _FakeRedmine.list_paths.clear()
        status.set_status(self.cfg, "9", "實作中")
        issues, total = redmine.list_assigned(self.cfg)
        self.assertEqual((len(issues), total), (2, 2))  # 假伺服器每頁只回 1 張，要翻頁才拿得到 2 張
        self.assertEqual(len(_FakeRedmine.list_paths), 2)
        for q in ("assigned_to_id=me", "status_id=open"):
            self.assertIn(q, _FakeRedmine.list_paths[0])
        text = "\n".join(redmine.render_list(self.cfg, issues, total))
        for secret in (FAKE_ID, FAKE_CUSTOMER, "王小明"):
            self.assertNotIn(secret, text, f"洩漏：{secret}")
        self.assertIn("#7 | Bug | 新建 | 高 | 2026-11-10 | project#3 | 本機:— |", text)
        self.assertIn("#9 | 功能 | 處理中 | 一般 | 2026-11-09 | project#4 | 本機:實作中 | 報表欄位順序", text)
        self.assertIn("共 2 張待處理", text)

    def test_summarize_issues_keeps_only_deidentified_fields(self):
        status.set_status(self.cfg, "9", "分析中")
        issues, _ = redmine.list_assigned(self.cfg)
        rows = redmine.summarize_issues(self.cfg, issues)
        self.assertEqual([r["id"] for r in rows], ["7", "9"])
        self.assertEqual(rows[0]["project_id"], "3")
        self.assertEqual((rows[0]["tracker"], rows[0]["status"], rows[0]["priority"], rows[0]["updated"]),
                         ("Bug", "新建", "高", "2026-11-10"))
        self.assertEqual((rows[0]["local_stage"], rows[1]["local_stage"]), ("", "分析中"))
        self.assertEqual(rows[1]["subject"], "報表欄位順序")
        text = json.dumps(rows, ensure_ascii=False)
        for secret in (FAKE_ID, FAKE_CUSTOMER, "王小明"):
            self.assertNotIn(secret, text, f"洩漏：{secret}")
        self.assertEqual(set(rows[0]), {"id", "tracker", "status", "priority", "updated", "project_id", "subject", "local_stage"})

    def test_missing_key(self):
        os.environ.pop("CONSOLE_TEST_KEY")
        with self.assertRaises(ConsoleError) as ctx:
            redmine.fetch_ticket(self.cfg, "7")
        self.assertIn("CONSOLE_TEST_KEY", str(ctx.exception))

    def test_not_found(self):
        with self.assertRaises(ConsoleError):
            redmine.fetch_ticket(self.cfg, "8")


def _git(path, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-C", str(path), *args],
                   check=True, capture_output=True, text=True)


class ScanTests(unittest.TestCase):
    def test_added_lines_parsing(self):
        diff = (
            "diff --git a/a.php b/a.php\n--- a/a.php\n+++ b/a.php\n@@ -1,0 +5,2 @@\n+one\n+two\n"
            "@@ -9 +12 @@\n-old\n+new\n"
            "diff --git a/gone.php b/gone.php\n--- a/gone.php\n+++ /dev/null\n@@ -1 +0,0 @@\n-x\n"
        )
        self.assertEqual(list(scan.added_lines(diff)), [("a.php", 5, "one"), ("a.php", 6, "two"), ("a.php", 12, "new")])

    def test_worktree_scan_never_prints_originals(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            _git(repo, "init", "-q")
            (repo / "a.txt").write_text("hello\n", encoding="utf-8")
            _git(repo, "add", ".")
            _git(repo, "commit", "-q", "-m", "base")
            start = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                                   check=True).stdout.strip()
            (repo / "a.txt").write_text(f"hello\nmail {FAKE_MAIL}\n", encoding="utf-8")
            (repo / "new.txt").write_text(f"id {FAKE_ID}\nclean\n", encoding="utf-8")
            (repo / "bin.dat").write_bytes(b"\0" + FAKE_ID.encode())
            _git(repo, "add", "a.txt")
            _git(repo, "commit", "-q", "-m", f"fix: 給 {FAKE_PHONE} 的修正")
            sources, hits = scan.scan_worktree(repo, start)
        self.assertEqual(sources, 3)  # a.txt 新增行、new.txt、commit 訊息；二進位略過
        flat = repr(hits)
        for secret in (FAKE_MAIL, FAKE_ID, FAKE_PHONE):
            self.assertNotIn(secret, flat)
        self.assertEqual({(src, tuple(cats)) for src, _, cats, _ in hits},
                         {("a.txt", ("[EMAIL]",)), ("new.txt", ("[ID]",)), (hits[-1][0], ("[PHONE]",))})
        self.assertTrue(any(src.startswith("commit ") for src, *_ in hits))

    def test_ticket_files_skip_masked_and_attachments(self):
        with tempfile.TemporaryDirectory() as d:
            ticket_dir = Path(d)
            t = ticket_dir / "_ticket"
            (t / "attachments").mkdir(parents=True)
            (t / "masked.md").write_text(FAKE_MAIL, encoding="utf-8")
            (t / "attachments" / "att1.masked.txt").write_text(FAKE_MAIL, encoding="utf-8")
            (t / "site-emmasrc.txt").write_text(FAKE_MAIL, encoding="utf-8")
            (t / "decision.md").write_text(f"ok\n{FAKE_ID}\n", encoding="utf-8")
            count, hits = scan.scan_ticket_files(ticket_dir)
        self.assertEqual(count, 1)
        self.assertEqual([(src, no) for src, no, *_ in hits], [("_ticket/decision.md", 2)])


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = Config({"console": {"worktree_root": self.tmp.name}})

    def tearDown(self):
        self.tmp.cleanup()

    def test_set_and_history(self):
        status.set_status(self.cfg, "7", "已讀取", projects=["emmasrc"])
        data = status.set_status(self.cfg, "7", "已裁決", severity="中", note=f"聯絡 {FAKE_MAIL}")
        self.assertEqual(data["stage"], "已裁決")
        self.assertEqual(data["severity"], "中")
        self.assertEqual(data["projects"], ["emmasrc"])
        self.assertEqual([h["stage"] for h in data["history"]], ["已讀取", "已裁決"])
        self.assertNotIn(FAKE_MAIL, json.dumps(data, ensure_ascii=False))

    def test_rejects_unknown_values(self):
        with self.assertRaises(ConsoleError):
            status.set_status(self.cfg, "7", "亂寫")
        with self.assertRaises(ConsoleError):
            status.set_status(self.cfg, "7", "已讀取", severity="極高")
        self.assertFalse(status.status_file(self.cfg, "7").exists())

    def test_list_orders_escalated_first_and_flags_stale(self):
        old = datetime.now().astimezone() - timedelta(hours=30)
        status.set_status(self.cfg, "1", "實作中", now=old)
        status.set_status(self.cfg, "2", "已升級", severity="高", note="動到薪資計算")
        status.set_status(self.cfg, "3", "待人工交付", now=old)
        rows = status.list_all(self.cfg)
        self.assertEqual([r[1] for r in rows], ["2", "1", "3"])
        self.assertIn("久未動", rows[1][3])
        self.assertNotIn("久未動", rows[2][3])  # 已完成的不算


if __name__ == "__main__":
    unittest.main()
