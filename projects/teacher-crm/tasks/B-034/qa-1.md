verdict: 通過

# B-034 QA 第 1 輪（specs/021-branch-coverage-and-threshold）

## diff 檢查（git diff HEAD，worktree）
- pyproject.toml：[tool.coverage.run] 新增 `branch = true`，omit 保留。通過
- Makefile coverage：加 `--cov-fail-under=95`；.github/workflows/ci.yml:66 已是 95，兩者一致。通過
- tests/unit/test_coverage_settings.py（新增 2 測）：驗 branch=true 與 omit、Makefile 與 CI 門檻相同且 >=95。內容合理，非空斷言。通過
- src/ 無變更；code_map 已同步更新。

## 全量重跑（docker compose run --rm app，COMPOSE_PROJECT_NAME=b-034，tests/unit + tests/db，--cov=src）
- 903 passed、2 failed（221.9s）
- 總覆蓋率（含分支）：97%（4178 stmts／119 miss；948 branch／52 partial）>= 95，門檻可過
- 較低檔案：jotform/sync.py 79%、process_finished_sessions 83%、process_jotform_submissions 88%、line/service 90%、gateways/base 90%（仍不影響總門檻，列為後續補測候選）

## 失敗項
- tests/db/test_jotform_sync_command.py::test_a_renamed_question_is_found_again_and_the_write_is_retried_once
- tests/db/test_jotform_sync_command.py::test_when_the_session_question_cannot_be_found_again_the_form_waits_for_the_admin
- 輸出顯示「平台尚未設定 Jotform 金鑰，略過同步」。以 `-e JOTFORM_API_KEY=fake-key` 重跑該檔：11 passed。
- 判斷：環境缺假金鑰造成，既有失敗，與本任務無關（本任務未動 src，也未改既有測試）。未另開 master 對照（不動工作樹；diff 證明無相關變更）。

## 未執行
- tests/integration（依指示不跑）。ruff/lint 未跑（不在要求範圍）。

## 缺陷：無
