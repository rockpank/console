"""console 指令列入口。用法見 README.md 或 `bin/console --help`。"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import config as config_mod
from . import autodispatch, ledger, site, ui, usage, util, worktree
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


def cmd_auto(cfg, args) -> int:
    if args.action == "once":
        d = autodispatch.tick(cfg)
        print(("已派工：" + d["project"] + " 請專案管理員挑 " + str(d["count"]) + " 項 → " + d["session"]) if d["go"] else "不派：" + d["reason"])
    else:
        conf = autodispatch.settings(cfg)
        print(f"啟用：{'是' if conf['enabled'] else '否'}　駐列 {conf['slots']}　門檻：5 小時額度 < {conf['below_percent']:.0f}%　每批 {conf['batch_size']} 項　"
              f"檢查間隔 {conf['interval']}s　冷卻 {conf['cooldown']}s")
        for project in cfg.projects:
            ready = autodispatch.ready_items(cfg, project)
            if ready:
                print(f"可挑的待辦 {project}（{len(ready)}）：{', '.join(ready[:12])}{' …' if len(ready) > 12 else ''}")
        d = autodispatch.evaluate(cfg, usage.view(cfg), ui.list_sessions(), __import__("time").time())
        print(("現在會派：" + d["project"] + " 請專案管理員挑 " + str(d["count"]) + " 項") if d["go"] else "現在不會派：" + d["reason"])
    return 0


def cmd_ledger(cfg, args) -> int:
    if args.action == "report":
        since = 0.0
        if args.since:
            try:
                since = __import__("time").mktime(__import__("time").strptime(args.since, "%Y-%m-%d"))
            except ValueError:
                raise ConsoleError("--since 格式為 YYYY-MM-DD") from None
        summary = ledger.summarize(ledger.select(ledger.load(cfg), task=args.task or "", round_name=args.round or "", since=since))
        print(json.dumps(summary, ensure_ascii=False, indent=2) if args.json else ledger.render(summary))
        return 0
    if args.action == "due":
        d = ledger.due(ledger.load(cfg))
        st = d["since"]
        print(("該派優化師：是（" + "；".join(d["reasons"]) + "）") if d["due"] else "該派優化師：否（輕量覆盤即可）")
        print(f"距上次覆盤：{st['agents']} 次子代理、{st['tokens'] // 1000}k tokens、重工 {st['rework_pct']}%、等使用者 {st['waits']} 次")
        return 0
    if args.action == "wait":
        rec = ledger.add(cfg, "wait", project=args.project, task=args.task, round=args.round, reason=args.reason)
    else:
        rec = ledger.add(cfg, "agent", project=args.project, task=args.task, round=args.round, stage=args.stage, role=args.role,
                         tokens=args.tokens, calls=args.calls, duration_ms=args.ms, budget=args.budget,
                         outcome=args.outcome, rework=args.rework, note=args.note)
    say(f"已記錄：{rec['kind']} {rec['task']}／{rec['round']}")
    return 0


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

    a = sub.add_parser("auto", help="自動派工：5 小時額度低於門檻、駐列有空位時，請專案管理員從 backlog 挑待辦項目補派 /dispatch").add_subparsers(dest="action", required=True)
    a.add_parser("status", parents=[common], help="設定、可挑的待辦與現在會不會派").set_defaults(func=cmd_auto)
    a.add_parser("once", parents=[common], help="立刻檢查一次，條件成立就派").set_defaults(func=cmd_auto)

    lg = sub.add_parser("ledger", help="用量帳本：記錄每個子代理與每次等使用者，供每輪覆盤彙總").add_subparsers(dest="action", required=True)
    for name, text in (("agent", "記錄一個子代理跑完一次"), ("wait", "記錄一次停下來等使用者回答")):
        p = lg.add_parser(name, help=text)
        p.add_argument("--project", default="", help="專案別名")
        p.add_argument("--task", required=True, help="任務代號")
        p.add_argument("--round", required=True, help="輪的名稱，例如 'B-011 實作 r3'")
        if name == "agent":
            p.add_argument("--stage", required=True, help="階段：specify／system-analyze／testplan／tasks／implement／security／qa／fix …")
            p.add_argument("--role", required=True, help="角色：pm／architect／engineer／qa-engineer／security-reviewer／project-manager …")
            p.add_argument("--tokens", type=int, required=True, help="該次子代理回報的 tokens")
            p.add_argument("--calls", type=int, required=True, help="工具呼叫次數")
            p.add_argument("--ms", type=int, default=None, help="耗時（毫秒，可省略）")
            p.add_argument("--budget", type=int, default=None, help="工具呼叫預算（可省略）")
            p.add_argument("--outcome", default="ok", choices=ledger.OUTCOMES)
            p.add_argument("--rework", action="store_true", help="這次是為了重做先前階段（格式返工、衝突重工等）")
            p.add_argument("--note", default="", help="一句話說明（不放個資與祕密）")
        else:
            p.add_argument("--reason", required=True, help="為什麼停下來等使用者（一句話）")
        p.set_defaults(func=cmd_ledger)
    lg.add_parser("due", help="距上次覆盤是否達到觸發條件（失敗／卡住、超預算、等使用者 ≥2 次、累積 ≥300k token）").set_defaults(func=cmd_ledger)
    p = lg.add_parser("report", help="彙總：總計、各輪趨勢、依階段、最貴 5 筆、等使用者的原因")
    p.add_argument("--task", default="", help="只看某任務")
    p.add_argument("--round", default="", help="只看某一輪")
    p.add_argument("--since", default="", help="只看這天（YYYY-MM-DD）之後")
    p.add_argument("--json", action="store_true", help="輸出 JSON")
    p.set_defaults(func=cmd_ledger)

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
