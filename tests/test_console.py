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

from console_cli import envfile  # noqa: E402
from console_cli.config import Config  # noqa: E402
from console_cli.mask import detect, load_terms, mask_text  # noqa: E402
from console_cli.util import ConsoleError, parse_task, parse_ticket, split_projects  # noqa: E402

# 以下全是假資料
FAKE_ID, FAKE_PHONE, FAKE_MAIL, FAKE_AMOUNT = "A123456789", "0912-345-678", "someone@example.com", "NT$ 50,000"
FAKE_CUSTOMER = "測試客戶股份有限公司"


class ParseTests(unittest.TestCase):
    def test_ticket_forms(self):
        for raw in ("4059", "r-4059", "#4059", " R-4059 "):
            self.assertEqual(parse_ticket(raw), "4059")

    def test_ticket_rejects(self):
        for raw in ("", "abc", "0", "-1", "r-", "40a9", "4059; rm -rf /"):
            with self.assertRaises(ConsoleError):
                parse_ticket(raw)

    def test_task_codes(self):
        self.assertEqual(parse_task("B-017"), "B-017")
        self.assertEqual(parse_task(" N-3 "), "N-3")
        self.assertEqual(parse_task("r-4059"), "4059")   # 數字沿用工單的寫法
        self.assertEqual(parse_task("#12"), "12")

    def test_task_rejects(self):
        for raw in ("", "-x", ".hidden", "a..b", "a.b", "a b", "B/017", "x.lock", "x.", "0", "a;rm", "A" * 41, "B-017\n--force"):
            with self.assertRaises(ConsoleError, msg=repr(raw)):
                parse_task(raw)

    def test_split_projects(self):
        self.assertEqual(split_projects(["a", "b,c", " d "]), ["a", "b", "c", "d"])
        self.assertEqual(split_projects(None), [])


class MaskTests(unittest.TestCase):
    def test_masks_formats(self):
        text = f"身分證 {FAKE_ID} 電話 {FAKE_PHONE} 信箱 {FAKE_MAIL} 薪資 {FAKE_AMOUNT} 帳號 1234567890123"
        masked = mask_text(text)
        for secret in (FAKE_ID, FAKE_PHONE, FAKE_MAIL, "50,000", "1234567890123"):
            self.assertNotIn(secret, masked)

    def test_keeps_normal_text(self):
        self.assertEqual(mask_text("員工編號 E0123 請假 3 天"), "員工編號 E0123 請假 3 天")

    def test_company_and_title_heuristics(self):
        masked = mask_text(f"{FAKE_CUSTOMER} 的王先生與陳經理回報")
        for secret in (FAKE_CUSTOMER, "王先生", "陳經理"):
            self.assertNotIn(secret, masked)

    def test_user_terms_file(self):
        with tempfile.TemporaryDirectory() as d:
            terms = Path(d) / "terms.txt"
            terms.write_text("# 註解\nFooBarCo\n", encoding="utf-8")
            self.assertEqual(load_terms(terms), 1)
            self.assertNotIn("foobarco", mask_text("report from FOOBARCO site").lower())
        self.assertEqual(load_terms(Path("/nonexistent/terms.txt")), 0)
        self.assertEqual(mask_text("report from FOOBARCO site"), "report from FOOBARCO site")


class EnvFileTests(unittest.TestCase):
    def test_parse_formats(self):
        text = (
            "# 註解\n\nA=1\nexport B=two\nC=\"quoted value\"\nD='single'\n"
            "E=plain # 行尾註解\nF=\nbad key=1\n=novalue\nG=a#b\n"
        )
        self.assertEqual(
            envfile.parse(text),
            {"A": "1", "B": "two", "C": "quoted value", "D": "single", "E": "plain", "F": "", "G": "a#b"},
        )

    def test_does_not_expand_or_execute(self):
        self.assertEqual(envfile.parse("X=$(echo hi)\nY=$HOME\n"), {"X": "$(echo hi)", "Y": "$HOME"})

    def test_load_semantics(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "console.env"
            f.write_text("K1=file1\nK2=file2\nK3=\nK4=same\n", encoding="utf-8")
            f.chmod(0o600)
            env = {"K2": "from-env", "K4": "same"}
            info = envfile.load(f, env)
            self.assertEqual(env["K1"], "file1")          # 檔案補上缺的
            self.assertEqual(env["K2"], "from-env")       # 環境變數優先
            self.assertNotIn("K3", env)                   # 空值視為未設定
            self.assertEqual(info.from_file, {"K1"})
            self.assertEqual(info.conflicts, {"K2"})      # 同名同值不算衝突
            self.assertFalse(info.insecure)
            f.chmod(0o644)
            self.assertTrue(envfile.load(f, {}).insecure)

    def test_missing_file(self):
        info = envfile.load(Path("/nonexistent/console.env"), {})
        self.assertFalse(info.exists)


class SeedEnvFilesTests(unittest.TestCase):
    def setUp(self):
        import subprocess
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.wt_root = root / "wt"
        wt = self.wt_root / "55" / "p"
        wt.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(wt)], check=True)
        (wt / ".gitignore").write_text(".env\nemma/tests/e2e/.env\n", encoding="utf-8")
        self.wt = wt
        self.src = root / "e2e.env"
        self.src.write_text("# 註解\nE2E_BASE_URL=https://old.example/femas\nE2E_USERNAME=fake-user\n", encoding="utf-8")
        self.src.chmod(0o600)
        self.cfg = Config({
            "console": {"worktree_root": str(self.wt_root)},
            "projects": {"p": {"env_files": [
                {"source": str(self.src), "target": "emma/tests/e2e/.env", "set": {"E2E_BASE_URL": "http://localhost:8100/"}},
            ]}},
        })

    def tearDown(self):
        self.tmp.cleanup()

    def test_copy_override_and_perms(self):
        from console_cli import worktree
        worktree.seed_env_files(self.cfg, "55", "p")
        target = self.wt / "emma/tests/e2e/.env"
        lines = target.read_text(encoding="utf-8").splitlines()
        self.assertIn("E2E_BASE_URL=http://localhost:8100/", lines)
        self.assertNotIn("E2E_BASE_URL=https://old.example/femas", lines)
        self.assertIn("E2E_USERNAME=fake-user", lines)
        self.assertIn("# 註解", lines)
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_no_overwrite_unless_asked(self):
        from console_cli import worktree
        worktree.seed_env_files(self.cfg, "55", "p")
        target = self.wt / "emma/tests/e2e/.env"
        target.write_text("E2E_USERNAME=edited\n", encoding="utf-8")
        worktree.seed_env_files(self.cfg, "55", "p")
        self.assertEqual(target.read_text(encoding="utf-8"), "E2E_USERNAME=edited\n")
        worktree.seed_env_files(self.cfg, "55", "p", overwrite=True)
        self.assertIn("fake-user", target.read_text(encoding="utf-8"))

    def test_refuses_non_ignored_target(self):
        from console_cli import worktree
        self.cfg.projects["p"]["env_files"][0]["target"] = "not_ignored.env"
        worktree.seed_env_files(self.cfg, "55", "p")
        self.assertFalse((self.wt / "not_ignored.env").exists())

    def test_missing_source_is_skipped(self):
        from console_cli import worktree
        self.src.unlink()
        worktree.seed_env_files(self.cfg, "55", "p")
        self.assertFalse((self.wt / "emma/tests/e2e/.env").exists())

    def test_render_with_overrides_appends_missing_key(self):
        out = envfile.render_with_overrides("A=1\n# B=old\n", {"B": "new"})
        self.assertEqual(out, "A=1\n# B=old\nB=new\n")


class DetectTests(unittest.TestCase):
    def test_detect_returns_labels_not_text(self):
        found = detect(f"{FAKE_MAIL} {FAKE_ID} {FAKE_AMOUNT}")
        self.assertEqual(set(found), {"[EMAIL]", "[ID]", "[AMOUNT]"})
        for label in found:
            for secret in (FAKE_MAIL, FAKE_ID, "50,000"):
                self.assertNotIn(secret, label)

    def test_detect_clean_text(self):
        self.assertEqual(detect("員工編號 E0123 請假 3 天"), [])
        self.assertEqual(detect(None), [])

    def test_detect_user_terms(self):
        with tempfile.TemporaryDirectory() as d:
            terms = Path(d) / "terms.txt"
            terms.write_text("FooBarCo\n", encoding="utf-8")
            load_terms(terms)
            self.assertEqual(detect("from foobarco"), ["[已遮蔽]"])
        load_terms(Path("/nonexistent/terms.txt"))


def _git(path, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "-C", str(path), *args],
                   check=True, capture_output=True, text=True)


class FingerprintTests(unittest.TestCase):
    def test_detects_every_kind_of_change(self):
        from console_cli import worktree
        with tempfile.TemporaryDirectory() as d:
            cfg = Config({"console": {"worktree_root": d}})
            repo = cfg.worktree_path("7", "p")
            repo.mkdir(parents=True)
            _git(repo, "init", "-q")
            (repo / "a.txt").write_text("one\n", encoding="utf-8")
            _git(repo, "add", ".")
            _git(repo, "commit", "-q", "-m", "base")
            seen = [worktree.fingerprint(cfg, "7", "p")]
            self.assertEqual(seen[0], worktree.fingerprint(cfg, "7", "p"), "沒變動時指紋要穩定")

            (repo / "a.txt").write_text("two\n", encoding="utf-8")               # 改追蹤檔
            seen.append(worktree.fingerprint(cfg, "7", "p"))
            (repo / "new.txt").write_text("x\n", encoding="utf-8")               # 新增未追蹤檔
            seen.append(worktree.fingerprint(cfg, "7", "p"))
            (repo / "new.txt").write_text("y\n", encoding="utf-8")               # 只改未追蹤檔內容
            seen.append(worktree.fingerprint(cfg, "7", "p"))
            _git(repo, "add", ".")
            _git(repo, "commit", "-q", "-m", "more")                             # commit
            seen.append(worktree.fingerprint(cfg, "7", "p"))
            self.assertEqual(len(set(seen)), len(seen), "每一種變動都要讓指紋改變")
            with self.assertRaises(ConsoleError):
                worktree.fingerprint(cfg, "7", "missing")


