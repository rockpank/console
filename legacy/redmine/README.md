# legacy/redmine：Redmine 工單時代的程式與文件（已停用）

2026-11-17 起中控台改成「專案＋任務」的快速開發流程，下列內容移到這裡，**不再被載入或測試**：

| 位置 | 內容 |
|---|---|
| `agents/`、`skills/`、`docs/` | 五個 ticket-* 角色、舊 `/dispatch`、`/redmine-ticket` 技能、舊協議與維護條目 |
| `python/console_cli/` | `redmine.py`、`scan.py`（個資掃描）、`status.py`、`reopen.py`、`landed.py`、`login.py`、`site_cake73.py`（cake73 站點 driver） |
| `python/tests/` | 上述模組的測試 |
| `python/templates/` | cake73 的 Apache vhost 樣板、專案端 `redmine-ticket` 技能樣板 |
| `python/config/` | 被移出的 `[redmine]`／`[docker]`／`[sites]`／`[projects.emmasrc*]` 設定片段、`console.env.example` |
| `runtime/` | 舊站點的 vhost 檔與 sites.json 紀錄 |

還原方法：把 `python/console_cli/*.py` 放回 `console_cli/`（`site_cake73.py` 要接回 `site.py` 的 driver 分派）、設定片段貼回 `config/console.toml`、測試放回 `tests/`。**已刪除的祕密檔**（2026-11-17，依使用者指示）：`config/console.env`（Redmine 金鑰）；emmasrc 的專案環境檔本來就不在這份拷貝裡。還原時需要自行重建（範本 `python/config/console.env.example`）。`config/mask_terms.txt` 保留，仍由遮蔽使用。
