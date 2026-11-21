---
status: done
tests: 通過
---

# B-032 impl-notes：補測 LINE 外送路徑與綁定邊界（規格 031）

worktree：`/home/user/web/console/worktrees/B-032/teacher-crm/`（分支 t-B-032，未 commit）

## 完成

- tasks.md T001–T098 全部標 `[X]`（含 BE-API-02：實測 `[]` body 回 400，與 spec 相符）。
- 新增 `tests/db/test_line_outbound_paths.py`（US1–US3，BE-SVC-01~14，16 個測試案例）。
- 新增 `tests/db/test_line_binding_edge_cases.py`（US4–US6，BE-API-01~12、BE-SVC-15~17，17 個測試案例）。
- 沒動 `src/`、conftest、`line_helpers.py`；只以唯讀方式匯入 `helpers`、`line_helpers`、`notify_helpers`、`send_check_helpers`。
- `docs/code_map/` 以 `scripts/code_map.py update` 更新（新增兩檔與測試連結）。

## 驗證（實際輸出）

- `validate_artifacts.py tasks --package 031-test-line-outbound-paths`：OK（附註 1 個 `[NEEDS CLARIFICATION]` 字樣，為 tasks.md「Clarification Isolation」段落文字，非實際待澄清）。
- 新測試：33 passed（首次即綠，不改產品碼）。
- RED：以 AST 對每個測試的每一個 assert 各產生一個「取反」變體（共 121 個，暫存檔事後已刪除），121 個全部失敗、0 個意外通過。
- 全套（tests/unit + tests/db）：基線 1234 passed → 現在 1267 passed（+33），0 failed；覆蓋率 TOTAL 98%（4314 行、69 未覆蓋）。
- `ruff check src tests`：All checks passed；`ruff format --check src tests`：218 files already formatted。
- `scripts/code_map.py check`：OK（tree 2630a4c0cc72，293 檔）。
- 基線無原本即紅的項目。

## 假設與差異

- `retry_message` 只認領 FAILED 訊息，故 US1/US2 的「待重送訊息」使用 FAILED 變體（attempts 依案例設 1 或 3），而非 testplan FX-pending-message 的 PENDING。BE-SVC-04 則使用 PENDING，經 `sync_notifications`（課前 3 天階段）觀測。
- 付款提醒的「同日」去重以真實 `timezone.localdate()` 為準（`created_at` 為當下時間），不使用寫死日期。
- BE-API-09 額外斷言 B 專案帳號確實被停用，作為「事件有被處理」的對照。
- 「旅程」(JOURNEY-01~06) 以同檔全部測試一起執行驗收；無獨立測試函式。

## 已知限制／缺陷

- 未測出任何產品缺陷，無需另開 backlog。
- 未跑 `make test-integration`、`makemigrations --check`（無 model 變更）。
- docker 以 `COMPOSE_PROJECT_NAME=b-032` 執行；假 `JOTFORM_API_KEY` 僅在命令列提供。基線全套與新測試不可同時跑（共用 test_crm 資料庫），已序列執行。
