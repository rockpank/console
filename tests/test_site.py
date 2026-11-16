"""通用站點 driver（console_cli/site.py）測試：不碰真實 docker、不開網路連線。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from console_cli import registry, site, ui, util  # noqa: E402
from console_cli.config import Config  # noqa: E402
from console_cli.util import ConsoleError  # noqa: E402

SITE = {
    "driver": "command", "port_base": 8100, "port_max": 8102, "url": "http://localhost:{port}/", "health_timeout": 1,
    "env": {"COMPOSE_PROJECT_NAME": "{name}", "SITE_BASE_URL": "http://localhost:{port}"},
    "prepare": [["docker", "compose", "run", "--rm", "app", "migrate"]],
    "start": [["docker", "compose", "run", "-d", "--name", "{name}-web", "-p", "{port}:8000", "app"]],
    "stop": [["docker", "rm", "-f", "{name}-web"], ["docker", "compose", "down"]],
    "purge": [["docker", "compose", "down", "-v"]],
}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.cfg = Config({"console": {"worktree_root": str(root / "wt"), "runtime_dir": str(root / "rt"),
                                       "projects_dir": str(root / "projects")},
                           "projects": {"demo": {"site": dict(SITE)}}})
        self.wt = self.cfg.worktree_path("B-017", "demo")
        self.wt.mkdir(parents=True)
        self.calls = []

        def fake_run(cmd, **kw):
            self.calls.append((list(map(str, cmd)), kw))
            return mock.Mock(returncode=0, stdout="", stderr="")

        mock.patch.object(site, "run", side_effect=fake_run).start()
        mock.patch.object(site, "_port_free", return_value=True).start()
        self.addCleanup(mock.patch.stopall)
        self.addCleanup(self.tmp.cleanup)

    def argvs(self):
        return [c[0] for c in self.calls]


class HelperTests(unittest.TestCase):
    def test_name_is_lowercase_compose_safe(self):
        self.assertEqual(site.site_name("teacher-crm", "B-017"), "teacher-crm-b-017")
        self.assertEqual(site.site_name("Shop", "N_3"), "shop-n_3")

    def test_render_replaces_only_known_placeholders(self):
        ctx = {"task": "B-1", "project": "p", "name": "p-b-1", "port": 8100, "path": "/w", "url": "u"}
        self.assertEqual(site._render("{port}:8000 ${HOME} {other}", ctx), "8100:8000 ${HOME} {other}")

    def test_commands_must_be_string_lists(self):
        for bad in ("docker ps", ["docker ps"], [[]], [["a", 1]]):
            with self.assertRaises(ConsoleError):
                site._commands({"start": bad}, "start")
        self.assertEqual(site._commands({}, "stop"), [])

    def test_allocate_skips_registered_and_busy_ports(self):
        reg = {"a/x": {"port": 8100}, "b/x": {"port": 8101}}
        with mock.patch.object(site, "_port_free", side_effect=lambda p: p != 8102):
            with self.assertRaises(ConsoleError):
                site.allocate_port({"port_base": 8100, "port_max": 8102}, reg)
        with mock.patch.object(site, "_port_free", return_value=True):
            self.assertEqual(site.allocate_port({"port_base": 8100, "port_max": 8105}, reg), 8102)
            # 自己的紀錄不算占用（重啟沿用同一個埠）
            self.assertEqual(site.allocate_port({"port_base": 8100, "port_max": 8105}, reg, exclude_key="a/x"), 8100)

    def test_wait_healthy_retries_only_while_no_response(self):
        seq = iter([(0, ""), (0, ""), (200, "ok")])
        t = [0.0]
        status, _ = site.wait_healthy("u", 10, fetch=lambda u: next(seq), sleep=lambda s: t.__setitem__(0, t[0] + s),
                                          clock=lambda: t[0])
        self.assertEqual(status, 200)
        self.assertEqual(t[0], 4.0)
        # 有回應（即使是 500）就立刻判定，不重試
        calls = []
        status, _ = site.wait_healthy("u", 10, fetch=lambda u: calls.append(1) or (500, ""), sleep=lambda s: 1 / 0)
        self.assertEqual((status, len(calls)), (500, 1))
        # 一直沒回應：到時限就放棄
        t = [0.0]
        status, _ = site.wait_healthy("u", 5, fetch=lambda u: (0, ""), sleep=lambda s: t.__setitem__(0, t[0] + s),
                                          clock=lambda: t[0])
        self.assertEqual(status, 0)


class AddSiteTests(Base):
    def test_prepare_then_start_in_worktree_with_env_and_port(self):
        entry = site.add_site(self.cfg, "B-017", "demo")
        self.assertEqual(entry["port"], 8100)
        self.assertEqual(entry["url"], "http://localhost:8100/")
        self.assertEqual(self.argvs(), [
            ["docker", "compose", "run", "--rm", "app", "migrate"],
            ["docker", "compose", "run", "-d", "--name", "demo-b-017-web", "-p", "8100:8000", "app"]])
        for _, kw in self.calls:
            self.assertEqual(kw["cwd"], str(self.wt))
            self.assertEqual(kw["env"], {"COMPOSE_PROJECT_NAME": "demo-b-017", "SITE_BASE_URL": "http://localhost:8100"})
        self.assertEqual(registry.load(self.cfg)["B-017/demo"]["port"], 8100)
        note = (Path(self.tmp.name) / "projects" / "demo" / "tasks" / "B-017" / "site.txt").read_text(encoding="utf-8")
        self.assertIn("http://localhost:8100/", note)

    def test_second_task_gets_next_port(self):
        self.cfg.worktree_path("B-018", "demo").mkdir(parents=True)
        site.add_site(self.cfg, "B-017", "demo")
        self.assertEqual(site.add_site(self.cfg, "B-018", "demo")["port"], 8101)

    def test_readd_stops_first_and_keeps_the_port(self):
        site.add_site(self.cfg, "B-017", "demo")
        self.calls.clear()
        entry = site.add_site(self.cfg, "B-017", "demo")
        self.assertEqual(entry["port"], 8100)
        self.assertEqual(self.argvs()[0], ["docker", "rm", "-f", "demo-b-017-web"])
        self.assertEqual(self.argvs()[2][:3], ["docker", "compose", "run"])
        # 停止失敗不中止（check=False）
        self.assertFalse(self.calls[0][1]["check"])
        self.assertTrue(self.calls[2][1]["check"])

    def test_missing_worktree_start_or_bad_config(self):
        with self.assertRaises(ConsoleError):
            site.add_site(self.cfg, "B-999", "demo")
        self.cfg.projects["demo"]["site"]["start"] = []
        with self.assertRaises(ConsoleError):
            site.add_site(self.cfg, "B-017", "demo")
        self.assertEqual(self.calls, [])

    def test_failed_start_leaves_no_registry_entry(self):
        site.run.side_effect = ConsoleError("docker 掛了")
        with self.assertRaises(ConsoleError):
            site.add_site(self.cfg, "B-017", "demo")
        self.assertEqual(registry.load(self.cfg), {})

    def test_cake73_driver_is_gone(self):
        self.cfg.projects["demo"]["site"] = {"driver": "cake73"}
        with self.assertRaises(ConsoleError) as cm:
            site.add_site(self.cfg, "1", "demo")
        self.assertIn("legacy", str(cm.exception))

    def test_project_without_site_section(self):
        self.cfg.projects["demo"].pop("site")
        with self.assertRaises(ConsoleError):
            site.add_site(self.cfg, "B-017", "demo")

    def test_unknown_driver(self):
        self.cfg.projects["demo"]["site"] = {"driver": "nope"}
        with self.assertRaises(ConsoleError):
            site.add_site(self.cfg, "B-017", "demo")


class TestAndRemoveTests(Base):
    def setUp(self):
        super().setUp()
        site.add_site(self.cfg, "B-017", "demo")
        self.calls.clear()

    def test_healthy(self):
        with mock.patch.object(site, "_fetch", return_value=(302, "")):
            self.assertTrue(site.test_site(self.cfg, "B-017", "demo"))      # 302 導向登入頁＝伺服器有回應

    def test_server_error_or_traceback_fails(self):
        with mock.patch.object(site, "_fetch", return_value=(500, "")):
            self.assertFalse(site.test_site(self.cfg, "B-017", "demo"))
        with mock.patch.object(site, "_fetch", return_value=(200, "Traceback (most recent call last):")):
            self.assertFalse(site.test_site(self.cfg, "B-017", "demo"))
        with mock.patch.object(site, "_fetch", return_value=(0, "")):
            self.assertFalse(site.test_site(self.cfg, "B-017", "demo"))

    def test_legacy_entry_cannot_be_removed_or_tested_by_the_new_driver(self):
        registry.save(self.cfg, {"4059/demo": {"ticket": "4059", "project": "demo", "url": "https://x/", "saas_db": "s"}})
        with self.assertRaises(ConsoleError):
            site.remove_site(self.cfg, "4059", "demo")

    def test_no_record(self):
        with self.assertRaises(ConsoleError):
            site.test_site(self.cfg, "B-999", "demo")

    def test_remove_keeps_data_by_default(self):
        site.remove_site(self.cfg, "B-017", "demo")
        self.assertEqual(self.argvs(), [["docker", "rm", "-f", "demo-b-017-web"], ["docker", "compose", "down"]])
        self.assertEqual(registry.load(self.cfg), {})
        self.assertFalse((Path(self.tmp.name) / "projects" / "demo" / "tasks" / "B-017" / "site.txt").exists())

    def test_drop_db_also_purges(self):
        site.remove_site(self.cfg, "B-017", "demo", drop_db=True)
        self.assertEqual(self.argvs()[-1], ["docker", "compose", "down", "-v"])

    def test_remove_without_record_is_a_noop(self):
        site.remove_site(self.cfg, "B-404", "demo")
        self.assertEqual(self.calls, [])


class ListAndBoardTests(Base):
    def test_list_handles_mixed_codes(self):
        registry.save(self.cfg, {
            "4059/emmasrc": {"ticket": "4059", "project": "emmasrc", "url": "https://x/", "saas_db": "saas_r4059"},
            "B-017/demo": {"ticket": "B-017", "task": "B-017", "project": "demo", "driver": "command", "port": 8100,
                           "url": "http://localhost:8100/"}})
        with mock.patch.object(site, "say") as say:
            site.list_sites(self.cfg)
        lines = [c.args[0] for c in say.call_args_list]
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("4059"))   # 數字排前面
        self.assertIn("舊 driver", lines[0])

    def test_board_shows_only_local_http_site_urls(self):
        (Path(self.tmp.name) / "projects" / "demo").mkdir(parents=True)
        (Path(self.tmp.name) / "projects" / "demo" / "profile.md").write_text("x", encoding="utf-8")
        for url, expected in (("http://localhost:8100/", "http://localhost:8100/"), ("http://127.0.0.1:8101", "http://127.0.0.1:8101"),
                              ("https://evil.example/", ""), ("javascript:alert(1)", ""), ("http://localhost:80/\" onclick=", "")):
            registry.save(self.cfg, {"B-017/demo": {"url": url}})
            self.assertEqual(ui._site_url(self.cfg, "demo", "B-017"), expected, url)
        registry.save(self.cfg, {})
        self.assertEqual(ui._site_url(self.cfg, "demo", "B-017"), "")


class RunEnvTests(unittest.TestCase):
    def test_env_is_layered_on_top_of_environment_and_printed_in_dry_run(self):
        out = util.run(["python3", "-c", "import os;print(os.environ['X_TEST'], 'PATH' in os.environ)"], env={"X_TEST": "1"})
        self.assertEqual(out.stdout.strip(), "1 True")
        util.set_dry_run(True)
        try:
            with mock.patch.object(util, "say") as say:
                util.run(["echo", "hi"], env={"A": "b c"})
            self.assertEqual(say.call_args.args[0], "[dry-run] A='b c' echo hi")
        finally:
            util.set_dry_run(False)


if __name__ == "__main__":
    unittest.main()
