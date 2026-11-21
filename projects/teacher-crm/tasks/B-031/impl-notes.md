---
status: done
tests: 通過
---

# B-031 impl-notes：補測 Jotform webhook 建單 → LINE 綁定 → 付款提醒串接

## 完成項目
- T001–T007 全部完成（`tasks.md` 已回寫 `[X]`）。BE-API-01（串接主流程）、BE-API-02（跨專案隔離）。
- validate：`validate_artifacts.py quickfix|tasks --package 030-...` 皆 OK，未需修改 quickfix／tasks 格式。

## 變更檔案（worktree `worktrees/B-031/teacher-crm/`）
- 新增 `tests/db/test_webhook_to_line_payment_reminder.py`（2 個測試）
- 新增 `specs/030-fix-test-webhook-line-reminder-flow/`（quickfix.md、tasks.md，tasks 已勾選）
- `make codemap` 產生物：`docs/code_map/INDEX.md`、`manifest.json`、`modules/src.crm.line.md`、`modules/src.crm.md`、`modules/tests.db.md`
- 未動 `src/`、conftest、`line_helpers.py`、`jotform_helpers.py`。

## 驗證（實際輸出，docker compose run --rm app，COMPOSE_PROJECT_NAME=b-031，假 JOTFORM_API_KEY 只在命令列）
- 新測試：`2 passed in 2.81s`
- 特徵化「紅燈」確認：暫時把預期改錯（user id、訊息種類、token 不等於 B 訂單改為相等），兩個測試皆失敗（`['U-wang'] == ['U-wrong']`），還原後 `2 passed`。
- 全套 `pytest tests/unit tests/db --cov=src`：`1236 passed, 1 warning`；覆蓋率 TOTAL 98%（≥95%）。
- `ruff check src tests`：All checks passed；`ruff format --check src tests`：217 files already formatted。
- `manage.py check`：no issues；`makemigrations --check --dry-run`：No changes detected。
- `code_map.py check`：新增檔後一度 STALE，執行 `code_map.py update` 後 `OK ... tree 4dfe166f1d81（292 檔）`。
- 基線測試數未另跑，以 1236 − 2 = 1234 推算。
- 無 skip／xfail。

## 與規格差異／假設
- 以 `fake_line` fixture 取代 build_client，`sync_notifications` 不傳 client（走 monkeypatch 的 `build_client`），與 quickfix 的 `sync_notifications(project, date, fake_line)` 等價。
- 測試檔 import `label_of` 自 `test_jotform_webhook.py`（唯讀沿用，非 B-032 檔）。
- B 專案以 `create_order` 建未付款訂單；只對 A 專案跑 `sync_notifications`。

## 缺陷發現
- 無；未測出產品缺陷，不需另開 backlog。

## 已知限制
- 未跑 `make test-integration`（規則禁止）。
