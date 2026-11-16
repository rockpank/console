"""讀取 config/console.toml。"""
from __future__ import annotations

import tomllib
from pathlib import Path

from .util import ConsoleError

ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "config" / "console.toml"


def _path(value: str) -> Path:
    p = Path(value)
    return p if p.is_absolute() else ROOT / p


class Config:
    def __init__(self, raw: dict):
        self.raw = raw
        console = raw.get("console", {})
        self.worktree_root = _path(console.get("worktree_root", "worktrees"))
        self.runtime_dir = _path(console.get("runtime_dir", "runtime"))
        self.projects_dir = _path(console.get("projects_dir", "projects"))   # 專案工作區 projects/<專案>/
        self.default_projects = list(console.get("default_projects", []))
        self.projects = raw.get("projects", {})

    @property
    def mask_terms_file(self) -> Path:
        """使用者自填的遮蔽詞（客戶名稱等），不進版控；看板的裁示／需求／擱置原因會用它遮蔽。"""
        return ROOT / "config" / "mask_terms.txt"

    @property
    def sites_registry(self) -> Path:
        return self.runtime_dir / "sites.json"

    def project(self, alias: str) -> dict:
        if alias not in self.projects:
            known = ", ".join(sorted(self.projects)) or "（無）"
            raise ConsoleError(f"未登錄的專案別名：{alias}。已登錄：{known}（見 config/console.toml）")
        return self.projects[alias]

    def worktree_path(self, task: str, alias: str) -> Path:
        return self.worktree_root / task / alias

    def resolve(self, value: str) -> Path:
        return _path(value)


def load() -> Config:
    try:
        with CONFIG_FILE.open("rb") as fh:
            return Config(tomllib.load(fh))
    except FileNotFoundError as exc:
        raise ConsoleError(f"找不到設定檔：{CONFIG_FILE}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConsoleError(f"設定檔格式錯誤：{exc}") from exc
