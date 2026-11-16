"""console 指令列入口。用法見 README.md 或 `bin/console --help`。"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import config as config_mod
from . import site, ui, usage, util, worktree
from .util import ConsoleError, parse_task, say, split_projects


def _projects(cfg, args) -> list[str]:
    aliases = split_projects(args.project) or cfg.default_projects
    if not aliases:
        raise ConsoleError("沒有指定專案：請用 -p <別名>，或在 config 設定 default_projects")
    for alias in aliases:
        cfg.project(alias)  # 驗證別名
    return aliases


def cmd_projects(cfg, args) -> int:
    for alias, proj in cfg.projects.items():
        marker = "預覽站" if proj.get("site") else "僅 worktree"
        default = "（預設）" if alias in cfg.default_projects else ""
        say(f"{alias:<14}{marker:<10}{proj.get('description', '')}{default}")
        say(f"{'':<14}repo={proj['repo']}  起點={proj.get('remote', 'origin')}/{proj.get('base_branch', 'dev')}")
    return 0


def cmd_wt_add(cfg, args) -> int:
    ticket = parse_task(args.task)
    for alias in _projects(cfg, args):
        worktree.add_worktree(cfg, ticket, alias, fetch=not args.no_fetch)
    return 0


def cmd_wt_rm(cfg, args) -> int:
    ticket = parse_task(args.task)
    for alias in _projects(cfg, args):
        worktree.remove_worktree(cfg, ticket, alias)
    return 0


def cmd_wt_list(cfg, args) -> int:
    worktree.list_worktrees(cfg)
    return 0


def cmd_wt_fingerprint(cfg, args) -> int:
    ticket = parse_task(args.task)
    for alias in _projects(cfg, args):
        say(f"{alias} {worktree.fingerprint(cfg, ticket, alias)}")
    return 0


def cmd_env_sync(cfg, args) -> int:
    ticket = parse_task(args.task)
    for alias in _projects(cfg, args):
        worktree.seed_env_files(cfg, ticket, alias, overwrite=args.overwrite)
    return 0


def cmd_site_add(cfg, args) -> int:
    ticket = parse_task(args.task)
    for alias in _projects(cfg, args):
        site.add_site(cfg, ticket, alias)
    return 0


def cmd_site_test(cfg, args) -> int:
    ticket = parse_task(args.task)
    ok = all([site.test_site(cfg, ticket, alias) for alias in _projects(cfg, args)])
    return 0 if ok else 1


def cmd_site_rm(cfg, args) -> int:
    ticket = parse_task(args.task)
    for alias in _projects(cfg, args):
        site.remove_site(cfg, ticket, alias, drop_db=args.drop_db)
    return 0


def cmd_site_list(cfg, args) -> int:
    site.list_sites(cfg)
    return 0


def cmd_up(cfg, args) -> int:
    """worktree + 站點 + 連線測試。沒有 [site] 設定的專案只建 worktree。"""
    ticket = parse_task(args.task)
    ok = True
    for alias in _projects(cfg, args):
        worktree.add_worktree(cfg, ticket, alias, fetch=not args.no_fetch)
        if not cfg.project(alias).get("site"):
            say(f"[{alias}] 沒有 [site] 設定，略過站點")
            continue
        site.add_site(cfg, ticket, alias)
        if not util.DRY_RUN:
            ok = site.test_site(cfg, ticket, alias) and ok
    return 0 if ok else 1


def cmd_down(cfg, args) -> int:
    ticket = parse_task(args.task)
    aliases = _projects(cfg, args)
    for alias in aliases:  # 先全部檢查，任何一個不能移除就什麼都不動
        worktree.ensure_removable(cfg, ticket, alias)
    for alias in aliases:
        site.remove_site(cfg, ticket, alias, drop_db=args.drop_db)
        worktree.remove_worktree(cfg, ticket, alias)
    return 0


def cmd_ui(cfg, args) -> int:
    return ui.serve(cfg, port=args.port)


def cmd_usage(cfg, args) -> int:
    view = usage.view(cfg, ui.list_sessions())
    if args.guard:   # 給 /dispatch 在高耗 token 的階段開始前問：結束碼 3＝已暫停，0＝可以繼續
        g = view["guard"]
        if g["paused"]:
            print(ui.guard_message(g) + " 請勿自行解除（只有使用者能在介面解除）。")
            return 3
        print("額度保護：未暫停" + ("（使用者已暫時解除）" if g["overridden"] else ""))
        return 0
    if args.json:
        print(json.dumps(view, ensure_ascii=False, indent=2))
    else:
        print(usage.render_text(view))
    return 1 if args.check and view["alerts"] else 0   # --check：有告警就回 1，方便排程或腳本判斷


def cmd_doctor(cfg, args) -> int:
    problems = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal problems
        problems += 0 if ok else 1
        say(f"[{'OK' if ok else '失敗'}] {name}{('：' + detail) if detail else ''}")

    check("git", bool(shutil.which("git")))
    check("tmux（看板開背景對話用）", bool(shutil.which("tmux")))
    check("claude", bool(shutil.which("claude")))
    wants_docker = any(proj.get("site") for proj in cfg.projects.values())
    if wants_docker or shutil.which("docker"):
        check("docker", bool(shutil.which("docker")))
        if shutil.which("docker"):
            r = util.run(["docker", "info", "--format", "{{.ServerVersion}}"], check=False, mutating=False, timeout=30)
            check("docker 服務執行中", r.returncode == 0, r.stdout.strip() if r.returncode == 0 else "docker daemon 沒有回應")
    for alias, proj in cfg.projects.items():
        check(f"專案 {alias} 的 repo", (Path(proj["repo"]) / ".git").exists(), proj["repo"])
        check(f"專案 {alias} 的工作區 projects/{alias}/profile.md", (cfg.projects_dir / alias / "profile.md").is_file(),
              "" if (cfg.projects_dir / alias / "profile.md").is_file() else "先執行 /onboard")
        site_conf = proj.get("site")
        if site_conf:
            ok = site_conf.get("driver") == "command" and bool(site_conf.get("start"))
            check(f"專案 {alias} 的預覽站設定（driver = command 且有 start）", ok)
    for alias, proj in cfg.projects.items():
        for entry in proj.get("env_files", []):
            src = cfg.resolve(entry["source"])
            label = f"專案環境檔來源 {entry['source']} → {entry['target']}"
            if not src.exists():
                say(f"[略過] {label}：尚未提供（範本：{entry['source']}.example）")
            else:
                check(label + " 權限僅限本人", not (src.stat().st_mode & 0o077),
                      "請 chmod 600" if src.stat().st_mode & 0o077 else "")
    return 0 if problems == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-n", "--dry-run", action="store_true", help="只列出會執行的變更指令，不執行")
    proj = argparse.ArgumentParser(add_help=False)
    proj.add_argument("-p", "--project", action="append", metavar="別名", help="專案別名，可重複或逗號分隔；預設見 config")

    parser = argparse.ArgumentParser(prog="console", description="快速開發中控台：專案、任務 worktree、預覽站、看板")
    sub = parser.add_subparsers(dest="group", required=True)

    sub.add_parser("doctor", parents=[common], help="檢查環境").set_defaults(func=cmd_doctor)
    sub.add_parser("projects", parents=[common], help="列出已登錄專案").set_defaults(func=cmd_projects)

    w = sub.add_parser("wt", help="worktree").add_subparsers(dest="action", required=True)
    p = w.add_parser("add", parents=[common, proj], help="建立任務 worktree 與 <branch_prefix><任務> 分支（已有同名分支就沿用）")
    p.add_argument("task", metavar="任務")
    p.add_argument("--no-fetch", action="store_true", help="不先 git fetch，直接用本機的遠端追蹤分支")
    p.set_defaults(func=cmd_wt_add)
    p = w.add_parser("rm", parents=[common, proj], help="移除 worktree（有未提交變更時拒絕）")
    p.add_argument("task", metavar="任務")
    p.set_defaults(func=cmd_wt_rm)
    w.add_parser("list", parents=[common], help="列出所有 worktree").set_defaults(func=cmd_wt_list)
    p = w.add_parser("fingerprint", parents=[proj], help="印出工作樹指紋（唯讀；前後比對有沒有被改動）")
    p.add_argument("task", metavar="任務")
    p.set_defaults(func=cmd_wt_fingerprint)

    e = sub.add_parser("env", help="專案環境檔").add_subparsers(dest="action", required=True)
    p = e.add_parser("sync", parents=[common, proj], help="把 config/env/<專案>/ 的環境檔複製進既有 worktree")
    p.add_argument("task", metavar="任務")
    p.add_argument("--overwrite", action="store_true", help="目標已存在時也覆蓋")
    p.set_defaults(func=cmd_env_sync)

    s = sub.add_parser("site", help="預覽站").add_subparsers(dest="action", required=True)
    p = s.add_parser("add", parents=[common, proj], help="為任務 worktree 開預覽站（prepare + start，配一個空的埠）")
    p.add_argument("task", metavar="任務")
    p.set_defaults(func=cmd_site_add)
    p = s.add_parser("test", parents=[common, proj], help="預覽站連線測試")
    p.add_argument("task", metavar="任務")
    p.set_defaults(func=cmd_site_test)
    p = s.add_parser("rm", parents=[common, proj], help="停止預覽站")
    p.add_argument("task", metavar="任務")
    p.add_argument("--drop-db", action="store_true", help="一併清除資料（執行設定中的 purge 指令，例如 docker compose down -v）")
    p.set_defaults(func=cmd_site_rm)
    s.add_parser("list", parents=[common], help="列出預覽站").set_defaults(func=cmd_site_list)

    p = sub.add_parser("ui", help="本機視覺化介面：看各專案任務與角色進度、從 backlog 派工、擱置／排序／移除、建立對話（背景執行）、按鈕開指令視窗（不會自動開瀏覽器，只印網址）")
    p.add_argument("--port", type=int, default=ui.DEFAULT_PORT)
    p.set_defaults(func=cmd_ui)

    p = sub.add_parser("usage", help="token 用量：方案額度（5 小時／每週）、各對話 context、各任務用量；達門檻告警（唯讀）")
    p.add_argument("--json", action="store_true", help="輸出 JSON")
    p.add_argument("--check", action="store_true", help="有告警就以結束碼 1 結束")
    p.add_argument("--guard", action="store_true", help="額度保護：已暫停高耗 token 的動作就以結束碼 3 結束，否則 0（只印一行）")
    p.set_defaults(func=cmd_usage)

    p = sub.add_parser("up", parents=[common, proj], help="worktree + 預覽站 + 連線測試")
    p.add_argument("task", metavar="任務")
    p.add_argument("--no-fetch", action="store_true")
    p.set_defaults(func=cmd_up)
    p = sub.add_parser("down", parents=[common, proj], help="停止預覽站並移除 worktree")
    p.add_argument("task", metavar="任務")
    p.add_argument("--drop-db", action="store_true")
    p.set_defaults(func=cmd_down)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    util.set_dry_run(getattr(args, "dry_run", False))
    try:
        cfg = config_mod.load()
        return args.func(cfg, args)
    except ConsoleError as exc:
        print(f"錯誤：{exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("已中斷", file=sys.stderr)
        return 130
