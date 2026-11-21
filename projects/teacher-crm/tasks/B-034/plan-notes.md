---
status: done
---

# B-034 快速路線規劃

- 資格判定：5 條全符合（設定檔變更、2 個預期行為、不改 model／URL／權限／FR）。走快速路線。
- 產物（worktree 內）：`specs/021-branch-coverage-and-threshold/quickfix.md`、`tasks.md`（2 切片 BE-SVC-01／02、T001–T008）。
- 設計：pyproject `[tool.coverage.run]` 加 `branch = true`；Makefile `coverage` 加 `--cov-fail-under=95`；ci.yml 已有同值，預期不需改。新測放新檔 `tests/unit/test_coverage_settings.py`，不改 `test_ci_workflows.py` 既有斷言。
- 若分支覆蓋率使總數 < 95%：只新增測試檔補足；補不動則回報調度者，不降門檻。
- 未執行：本角色無 Bash，未跑 `validate_artifacts.py`（quickfix／tasks）與基線量測。工程師開工前先跑驗證腳本與 `docker compose run`（`COMPOSE_PROJECT_NAME=b-034`）量測。
- 已對照驗證器規則人工檢查：必要章節、案例欄位、SLICE 對應、ACCEPTANCE-GATE、切片數 ≤ 3。
