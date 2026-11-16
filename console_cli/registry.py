"""runtime/sites.json：記錄 console 建立的站點（工單 × 專案 → 網址、資料庫、vhost 檔）。"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .config import Config


def load(cfg: Config) -> dict:
    try:
        return json.loads(cfg.sites_registry.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def save(cfg: Config, data: dict) -> None:
    cfg.runtime_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(cfg.sites_registry) + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, cfg.sites_registry)


def key(ticket: str, alias: str) -> str:
    return f"{ticket}/{alias}"
