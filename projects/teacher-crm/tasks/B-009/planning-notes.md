---
status: done
route: 快速路線（符合，範圍收斂）
package: specs/013-fix-line-webhook-empty-secret/
validate_artifacts: 未執行（pm 無 Bash 工具，需調度者或下一角色執行）
---

# B-009 規劃備註

- 產出（worktree 內）：`specs/013-fix-line-webhook-empty-secret/quickfix.md`、`tasks.md`；2 個切片（BE-API-01 單元、BE-API-02 webhook）。
- 資格：2 個預期行為、不改 model、不新增 URL、不改權限、不推翻 FR；符合快速路線。
- 檔案範圍：`src/crm/domain/line.py`、（必要時）`src/crm/views.py` 的 `line_webhook`；測試 `tests/unit/test_line_domain.py`（新增案例）、新檔 `tests/db/test_line_webhook_empty_secret.py`。`setup_line(project, secret="")` 已可用，不需改 `line_helpers.py`、conftest。不動 `forms.py`、model、urls、settings、crypto。
- 預期只需改 `verify_signature` 一處即可讓兩個切片轉綠；RED 順序須先寫兩測再修（tasks 依賴段已寫）。

## 待釐清（需使用者決定）

backlog B-009 驗收含「非 LINE 模式的專案不處理外部事件並回 400」。現行假 LINE 模式（`mode=fake`，`setup_line` 預設）有 secret 且簽章有效時就是正常綁定流程，`test_line_binding.py` 約 20 個測試都走這條，而 backlog「不得改變」要求既有有效簽章綁定流程不變。兩者互相矛盾。本規劃採「僅以 secret 為空為判準」（假 LINE 且 secret 空也被擋）。若使用者要求假 LINE 模式一律 400，須改 `setup_line` 預設與大量測試，且是第二個行為，建議轉完整路線（編號 013 不變）並先決定。

## 其他

- 未讀 `.env`、未 commit。
- 未動 `forms.py`；`forms.py:438-443`（僅 LINE 模式才檢查 secret）不改，B-002 序列無衝突。
