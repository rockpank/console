---
status: done
---

# B-033 規劃備註（pm，快速路線）

- 套件：`specs/020-fix-test-gaps-commands-guards/`（worktree 內），產出 `quickfix.md`、`tasks.md`；3 個切片 + 1 個 Gate。
- 新測試檔（皆新增、不與他任務同名）：`tests/db/test_command_argument_errors.py`、`tests/db/test_attendance_same_day_sessions.py`、`tests/db/test_jotform_processed_and_sync_guards.py`。
- 驗證：`validate_artifacts.py` 未執行（本角色無 Bash）；請調度者或工程師開工前跑 `python3 .agents/skills/_shared/validate_artifacts.py all --package 020-fix-test-gaps-commands-guards`。
- 因補測性質，TDD-RED 預期「直接綠」；已在切片註明，若紅燈即為缺陷，列新 backlog，不改 src。
- 依賴 fixture：`tests/db/conftest.py` 的 `platform_key`、`fake_jotform` 只讀取不改；B-001 若改名或移動需通知。
- 建議：work-plan 目前 B-033 只在執行佇列有一列，建議補一個任務條目（規格 020、只新增 3 個測試檔、無 src／conftest／migration、批內可與 B-028／B-029 並行）。
- 未改 work-plan、backlog、src。
