"""Redmine 工單讀取：只輸出去識別化後的內容。

- 金鑰只從環境變數讀取，不印出、不寫檔。
- 原始 JSON 不落地；落地的只有遮蔽後的 masked.md 與附件。
- 專案名稱、使用者名稱一律改用 id；含客戶資料的自訂欄位整個捨棄。
- 文字類附件另存遮蔽版；圖片／PDF／Office 等無法自動遮蔽，只列清單，不自動讀取。
"""
from __future__ import annotations

import json
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import status as local_status
from .config import Config
from .mask import SENSITIVE_FIELD_NAMES, load_terms, mask_text
from .util import ConsoleError, say, warn

TEXT_EXTS = {"txt", "md", "csv", "log", "json", "sql", "php", "html", "xml", "ini", "yml", "yaml", "tsv"}
MAX_ATTACHMENT_BYTES = 50 * 1024 * 1024
MAX_MASKED_TEXT_BYTES = 200 * 1024


def _api_key(cfg: Config) -> str:
    env_name = cfg.redmine.get("api_key_env", "REDMINE_API_KEY")
    key = os.environ.get(env_name, "")
    if not key:
        raise ConsoleError(
            f"找不到 {env_name}。請在 config/console.env 填入 {env_name}=金鑰"
            "（從 config/console.env.example 複製，並 chmod 600）；或直接貼上去識別化後的工單內容。"
        )
    return key


def _open(cfg: Config, url: str, insecure: bool, timeout: int = 30):
    # Redmine 前面的伺服器會對預設的 Python-urllib UA 回 403，所以明確帶一個通用 UA（不含任何個人資訊）。
    request = urllib.request.Request(
        url, headers={"X-Redmine-API-Key": _api_key(cfg), "User-Agent": "femashr-console/1.0"}
    )
    context = ssl._create_unverified_context() if insecure else ssl.create_default_context()
    try:
        return urllib.request.urlopen(request, timeout=timeout, context=context)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise ConsoleError(
                f"Redmine 回 {exc.code}：金鑰無效或無權限。請確認 config/console.env 的 REDMINE_API_KEY，或直接貼上工單內容。"
            ) from exc
        if exc.code == 404:
            raise ConsoleError("Redmine 回 404：找不到這張工單（或無權限檢視）。") from exc
        raise ConsoleError(f"Redmine 回 HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLError):
            raise ConsoleError(
                f"憑證驗證失敗（{exc.reason}）。請先向使用者確認，同意後才可加 --insecure；預設不關閉驗證。"
            ) from exc
        raise ConsoleError(f"無法連線 Redmine：{exc.reason}") from exc


def _safe_ext(filename: str) -> str:
    ext = Path(filename).suffix.lstrip(".").lower()
    return ext if re.fullmatch(r"[a-z0-9]{1,8}", ext) else "bin"


def _field(value) -> str:
    return mask_text(str(value)) if value not in (None, "") else "（空）"


def render_markdown(issue: dict, attachments_info: list[dict]) -> str:
    lines = [f"# #{issue['id']} {mask_text(issue.get('subject'))}", ""]
    meta = [
        ("追蹤標籤", (issue.get("tracker") or {}).get("name")),
        ("狀態", (issue.get("status") or {}).get("name")),
        ("優先權", (issue.get("priority") or {}).get("name")),
        ("專案", f"project#{(issue.get('project') or {}).get('id', '?')}"),
        ("建立", issue.get("created_on")),
        ("更新", issue.get("updated_on")),
        ("提出者", f"user#{(issue.get('author') or {}).get('id', '?')}"),
    ]
    lines += [f"- {name}：{value}" for name, value in meta if value]

    dropped = []
    kept = []
    for cf in issue.get("custom_fields") or []:
        name = str(cf.get("name", ""))
        if SENSITIVE_FIELD_NAMES.search(name):
            dropped.append(name)
        elif cf.get("value") not in (None, "", []):
            kept.append(f"- {mask_text(name)}：{_field(cf.get('value'))}")
    if kept:
        lines += ["", "## 自訂欄位", *kept]
    if dropped:
        lines += ["", f"（已略去 {len(dropped)} 個可能含客戶資料的自訂欄位）"]

    lines += ["", "## 描述", "", mask_text(issue.get("description")) or "（無）"]

    journals = issue.get("journals") or []
    if journals:
        lines += ["", "## 歷程"]
    for index, journal in enumerate(journals, 1):
        who = f"user#{(journal.get('user') or {}).get('id', '?')}"
        private = "（私人備註）" if journal.get("private_notes") else ""
        lines += ["", f"### {index}. {who} {journal.get('created_on', '')}{private}"]
        for detail in journal.get("details") or []:
            label = mask_text(str(detail.get("name", "")))
            if detail.get("property") == "attachment":
                lines.append(f"- 附件變更：{label}")
                continue
            old, new = _field(detail.get("old_value")), _field(detail.get("new_value"))
            lines.append(f"- {label}：{old[:200]} → {new[:200]}")
        notes = mask_text(journal.get("notes"))
        if notes:
            lines += ["", notes]

    lines += ["", "## 附件"]
    if not attachments_info:
        lines.append("（無）")
    else:
        lines += ["", "| id | 類型 | 大小 | 檔名（已遮蔽） | 本機檔 | 處理 |", "|---|---|---|---|---|---|"]
        for a in attachments_info:
            lines.append(
                f"| {a['id']} | {a['content_type']} | {a['size']} | {a['name']} | {a['file']} | {a['status']} |"
            )
    return "\n".join(lines) + "\n"


LIST_PAGE = 100
LIST_MAX = 300
_SUBJECT_MAX = 60


def list_assigned(cfg: Config, *, insecure: bool = False) -> tuple[list[dict], int]:
    """分派給金鑰擁有者、尚未結案的工單（依優先權、更新時間排序）。回傳 (工單, 伺服器回報的總數)。"""
    base = cfg.redmine["base_url"].rstrip("/")
    issues: list[dict] = []
    total = 0
    while len(issues) < LIST_MAX:
        query = urllib.parse.urlencode({
            "assigned_to_id": "me", "status_id": "open", "sort": "priority:desc,updated_on:desc",
            "limit": LIST_PAGE, "offset": len(issues),
        })
        with _open(cfg, f"{base}/issues.json?{query}", insecure) as resp:
            data = json.load(resp)
        page = data.get("issues") or []
        issues += page
        total = int(data.get("total_count", len(issues)))
        if not page or len(issues) >= total:
            break
    return issues, total


def summarize_issues(cfg: Config, issues: list[dict]) -> list[dict]:
    """把 list_assigned 的結果整理成去識別化的摘要（CLI 清單與介面共用，遮蔽只在這一處）。

    只留系統欄位、project 的 id 與遮蔽後的主旨；專案名稱、提單人、被分派者等人名一律不帶出。
    local_stage 是本機 status.json 的階段，沒處理過為空字串。
    """
    load_terms(cfg.mask_terms_file)
    rows = []
    for issue in issues:
        local = local_status.load(local_status.status_file(cfg, str(issue["id"]))) or {}
        rows.append({
            "id": str(issue["id"]),
            "tracker": (issue.get("tracker") or {}).get("name", "?"),
            "status": (issue.get("status") or {}).get("name", "?"),
            "priority": (issue.get("priority") or {}).get("name", "?"),
            "updated": (issue.get("updated_on") or "")[:10],
            "project_id": str((issue.get("project") or {}).get("id", "?")),
            "subject": mask_text(issue.get("subject")).replace("\n", " ").strip()[:_SUBJECT_MAX],
            "local_stage": str(local.get("stage", "")),
        })
    return rows


def render_list(cfg: Config, issues: list[dict], total: int) -> list[str]:
    """一張一行。只輸出系統欄位、project#id 與遮蔽後的主旨；專案名稱、人名一律不輸出。"""
    lines = []
    for row in summarize_issues(cfg, issues):
        lines.append(" | ".join([
            f"#{row['id']}", row["tracker"], row["status"], row["priority"],
            row["updated"] or "—",
            f"project#{row['project_id']}",
            f"本機:{row['local_stage'] or '—'}",
            row["subject"],
        ]))
    shown = f"（只顯示前 {len(issues)} 張）" if total > len(issues) else ""
    lines.append(f"共 {total} 張待處理{shown}")
    return lines


def fetch_ticket(cfg: Config, ticket: str, *, insecure: bool = False, download: bool = True) -> Path:
    base = cfg.redmine["base_url"].rstrip("/")
    load_terms(cfg.mask_terms_file)
    url = f"{base}/issues/{ticket}.json?include=journals,attachments"
    with _open(cfg, url, insecure) as resp:
        issue = json.load(resp)["issue"]

    out_dir = cfg.ticket_dir(ticket) / "_ticket"
    att_dir = out_dir / "attachments"
    out_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(out_dir, 0o700)

    base_host = urllib.parse.urlparse(base).netloc
    infos: list[dict] = []
    for att in issue.get("attachments") or []:
        ext = _safe_ext(att.get("filename", ""))
        info = {
            "id": att["id"],
            "content_type": att.get("content_type", "?"),
            "size": att.get("filesize", 0),
            "name": f"（檔名已隱藏，副檔名 .{ext}）",  # 檔名常含客戶名稱，不輸出
            "file": "—",
            "status": "未下載",
        }
        infos.append(info)
        if not download:
            continue
        content_url = att.get("content_url", "")
        if urllib.parse.urlparse(content_url).netloc != base_host:
            info["status"] = "略過（下載網址不在 Redmine 主機）"
            warn(f"附件 {att['id']} 的下載網址主機與 Redmine 不同，已略過")
            continue
        if int(att.get("filesize") or 0) > MAX_ATTACHMENT_BYTES:
            info["status"] = "略過（超過 50 MB）"
            continue
        att_dir.mkdir(parents=True, exist_ok=True)
        target = att_dir / f"att{att['id']}.{ext}"
        try:  # 附件常是用不到的客戶檔案：單一附件下載失敗只略過，不讓整張工單讀不進來
            with _open(cfg, content_url, insecure, timeout=120) as resp:
                data = resp.read(MAX_ATTACHMENT_BYTES + 1)
            target.write_bytes(data)
        except (ConsoleError, OSError):
            info["status"] = "略過（下載失敗，不影響工單內容）"
            warn(f"附件 {att['id']} 下載失敗，已略過")
            continue
        os.chmod(target, 0o600)
        info["file"] = str(target.relative_to(cfg.ticket_dir(ticket)))
        if ext in TEXT_EXTS:
            masked = mask_text(data[:MAX_MASKED_TEXT_BYTES].decode("utf-8", errors="replace"))
            masked_path = att_dir / f"att{att['id']}.masked.txt"
            masked_path.write_text(masked, encoding="utf-8")
            os.chmod(masked_path, 0o600)
            info["file"] = str(masked_path.relative_to(cfg.ticket_dir(ticket)))
            info["status"] = "文字類：已產生遮蔽版，可讀"
        else:
            info["status"] = "二進位：未自動讀取（不影響流程；分析真的需要時再請使用者提供重點）"

    md_path = out_dir / "masked.md"
    md_path.write_text(render_markdown(issue, infos), encoding="utf-8")
    os.chmod(md_path, 0o600)

    text_ok = sum(1 for i in infos if i["status"].startswith("文字類"))
    binary = sum(1 for i in infos if i["status"].startswith("二進位"))
    say(f"工單 #{ticket} 已讀取（去識別化版）：{md_path}")
    say(f"附件共 {len(infos)} 個：文字類遮蔽版 {text_ok} 個，二進位未讀 {binary} 個（不影響流程）")
    return md_path
