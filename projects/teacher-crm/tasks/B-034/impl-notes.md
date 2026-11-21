---
status: done
tests: 通過（新增與 CI 契約測試 12 passed）；全量有 2 個既有失敗，與本任務無關
---

# B-034 實作筆記

- T001–T008 已勾選。validate_artifacts 通過。
- 變更：pyproject.toml（`[tool.coverage.run]` 加 `branch = true`）、Makefile（coverage 加 `--cov-fail-under=95`）、新檔 tests/unit/test_coverage_settings.py（2 測）、specs/021-*/tasks.md 勾選、docs/code_map 由 `scripts/code_map.py update` 產生。ci.yml 未改（已是 95）。
- RED 證據：兩測在改設定前 2 failed；GREEN 後 test_coverage_settings + test_ci_workflows 12 passed。
- 新基線（分支，tests/unit tests/db）：TOTAL 4178 stmts / 119 miss / 948 branch / 52 partial = 96.55%，門檻 95% 通過，不需補測。
- 全量：903 passed, 2 failed（tests/db/test_jotform_sync_command.py 兩測）。不帶 --cov 單獨跑同樣失敗，與本變更無關（既有紅燈，需另立 backlog）。因此 `make coverage` 目前會因這兩測回傳非 0。
- lint：ruff check / format --check 通過。
