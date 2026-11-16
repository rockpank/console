"""讀取 config/console.env（KEY=VALUE，不經 shell 執行）。

- 已存在的環境變數優先，不覆蓋；兩邊都有且值不同時記錄為 conflict，由 doctor 提示。
- 空值（例如剛從 .example 複製、還沒填）視為未設定。
- 檔案若本人以外可讀（權限 & 0o077），標記 insecure。
- 絕不印出任何值。
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

_KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass
class EnvInfo:
    exists: bool = False
    insecure: bool = False
    from_file: set[str] = field(default_factory=set)   # 這次由檔案提供的變數名
    conflicts: set[str] = field(default_factory=set)   # 檔案與環境變數都有但值不同


def parse(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        key, sep, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or not _KEY_RE.fullmatch(key):
            continue
        if len(value) >= 2 and value[0] in "\"'" and value[-1] == value[0]:
            value = value[1:-1]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
        values[key] = value
    return values


_ASSIGN_RE = re.compile(r"^(\s*(?:export\s+)?)([A-Za-z_][A-Za-z0-9_]*)\s*=")


def render_with_overrides(text: str, overrides: dict[str, str]) -> str:
    """保留原檔的註解與其他行，只替換指定 key 的值；原檔沒有的 key 附加在最後。"""
    remaining = dict(overrides)
    out = []
    for raw in text.splitlines():
        m = _ASSIGN_RE.match(raw)
        if m and m.group(2) in remaining:
            out.append(f"{m.group(1)}{m.group(2)}={remaining.pop(m.group(2))}")
        else:
            out.append(raw)
    out += [f"{key}={value}" for key, value in remaining.items()]
    return "\n".join(out) + "\n"


def load(path: Path, environ=None) -> EnvInfo:
    environ = os.environ if environ is None else environ
    info = EnvInfo()
    try:
        st = path.stat()
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return info
    info.exists = True
    info.insecure = bool(st.st_mode & 0o077)
    for key, value in parse(text).items():
        if value == "":
            continue
        if key in environ:
            if environ[key] != value:
                info.conflicts.add(key)
            continue
        environ[key] = value
        info.from_file.add(key)
    return info
