---
status: done
tests: 未執行
---

# B-029 規劃備註（pm，/quickfix）

- 套件：`specs/019-fix-project-isolation-guard/`（worktree 內），含 `quickfix.md`（3 切片：BE-API-01 路由＋webhook、BE-SVC-01 `_check_project`、BE-SVC-02 一致性巡檢）與 `tasks.md`（T001-T011）。
- 驗證：`validate_artifacts.py all --package ...` **未執行**（規劃角色無 Bash）；已對照驗證器規則人工檢查（切片 3 個、案例欄位齊全、每切片有任務鏈、有 ACCEPTANCE-GATE、無 spec.md）。請調度者代跑。
- 規模警示：參數化展開約 25 個測試函式，超過約 10 的門檻。切片數合規，但建議調度者裁示是否轉完整路線（編號 019 不變）；若維持快速路線，不需新增共用 fixture（全寫在各自新檔）。
- 新增測試檔（皆新增）：`tests/db/test_project_isolation_routes.py`、`tests/db/test_line_webhook_cross_project.py`、`tests/db/test_attendance_cross_project.py`、`tests/db/test_project_consistency.py`、`tests/unit/test_attendance_check_project.py`。不動 src、model、conftest。
- 決策：每路由含對照組（本專案同請求非 404）避免權限不足造成假通過；巡檢器以 `apps.get_models()` 動態掃描並含負向自證；補測預期一開始即綠，紅燈即缺陷、另開項目不修。不以暫改 src 做突變驗證。
- 注意：`register_walk_in` 不呼叫 `_check_project`（以 session.project 建學員），其隔離靠路由的 `_session_or_404`，已在 BE-API-01 覆蓋。
- crypto：webhook 案例用 `setup_line`（加密 channel secret）；B-001 合併後若需金鑰，命令列提供假值，不寫進檔案。
- 調度者裁示（2026-11-17）：規模警示（約 25 個測試函式）維持快速路線，不轉完整路線。理由：純新增測試檔、不動 src／model／conftest、低風險。
- 驗證器修正：`quickfix.md` 第 81 行原「不是 mock ORM」觸發禁止項，已改寫為「測試一律使用真實物件與真實資料庫資料」，範圍與切片不變。
- 無待釐清事項。
