"""共用小工具：指令執行（支援 dry-run）、訊息輸出、例外。"""
from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys

DRY_RUN = False


class ConsoleError(Exception):
    """可預期的錯誤；main 會印出訊息並以非 0 結束。"""


def set_dry_run(value: bool) -> None:
    global DRY_RUN
    DRY_RUN = value


def say(msg: str = "") -> None:
    print(msg, flush=True)


def warn(msg: str) -> None:
    print(f"警告：{msg}", file=sys.stderr, flush=True)


def run(cmd, *, cwd=None, input=None, check=True, mutating=True, timeout=None, env=None) -> subprocess.CompletedProcess:
    """執行指令。mutating=True 的指令在 dry-run 時只印出不執行。

    env：額外的環境變數（疊在目前環境上）。絕不把金鑰放進 cmd 或 env；錯誤訊息會原文帶出指令與輸出，
    dry-run 也會印出 env 的名稱與值。
    """
    cmd = [str(c) for c in cmd]
    if DRY_RUN and mutating:
        say("[dry-run] " + "".join(f"{k}={shlex.quote(str(v))} " for k, v in (env or {}).items()) + shlex.join(cmd))
        return subprocess.CompletedProcess(cmd, 0, "", "")
    full_env = {**os.environ, **{k: str(v) for k, v in env.items()}} if env else None
    try:
        result = subprocess.run(cmd, cwd=cwd, input=input, text=True, capture_output=True, timeout=timeout, env=full_env)
    except subprocess.TimeoutExpired as exc:
        raise ConsoleError(f"指令逾時（{timeout} 秒）：{shlex.join(cmd)}") from exc
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise ConsoleError(f"指令失敗（結束碼 {result.returncode}）：{shlex.join(cmd)}\n{detail}")
    return result


def split_projects(values) -> list[str]:
    """-p a -p b,c  ->  [a, b, c]"""
    out: list[str] = []
    for value in values or []:
        out.extend(part.strip() for part in value.split(",") if part.strip())
    return out


def parse_ticket(value: str) -> str:
    """接受 4059、r-4059、#4059，回傳純數字字串；其他一律拒絕。"""
    raw = value.strip().lstrip("#")
    if raw.lower().startswith("r-"):
        raw = raw[2:]
    if not raw.isdigit() or int(raw) <= 0:
        raise ConsoleError(f"工單號碼必須是正整數（可寫 4059、r-4059、#4059），收到：{value!r}")
    return str(int(raw))


_TASK_CODE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,39}")


def parse_task(value: str) -> str:
    """任務代號：worktree 目錄名與分支名的一部分（分支 <branch_prefix><代號>）。

    純數字照 parse_ticket 正規化（4059、r-4059）；其他接受 `B-017`、`N-3` 這類代號：
    英數開頭，只含英數與 _ -，最長 40 字（不含 `.`：tmux 對話名稱會把 `.` 換掉，對不上）。
    """
    raw = value.strip().lstrip("#")
    if raw.lower().startswith("r-") and raw[2:].isdigit():
        return parse_ticket(raw)
    if raw.isdigit():
        return parse_ticket(raw)
    if not _TASK_CODE.fullmatch(raw):
        raise ConsoleError(f"任務代號只能是英數開頭、含英數與 _ -、最長 40 字（例：B-017、N-3、4059），收到：{value!r}")
    return raw
