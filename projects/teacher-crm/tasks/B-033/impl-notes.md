---
status: done
tests: 失敗（2 個既有失敗，與本任務無關；新增 13 個全綠）
---

# B-033 補測 impl-notes

完成：T001–T010（BE-TASK-01、BE-API-01、BE-API-02、Gate），tasks.md 已全數勾 [X]，validate_artifacts 通過。

## 變更檔案（皆新增）
- tests/db/test_command_argument_errors.py（5 案例）
- tests/db/test_attendance_same_day_sessions.py（3）
- tests/db/test_jotform_processed_and_sync_guards.py（5）
- specs/020-fix-test-gaps-commands-guards/tasks.md（勾選）
- docs/code_map/*（make codemap 產生）
src、model、conftest、test_gateway_settings.py 無變更。

## 實際輸出
- 新 3 檔：13 passed。
- 「不會先紅」驗證：暫以複本改預期值（錯誤訊息、in/not in、False/True、404/200、提示文字），13 個案例全部轉紅，複本已刪除。
- ruff check / format --check：All checks passed、191 files already formatted。
- 全套 tests/unit tests/db：914 passed、2 failed；總覆蓋率 97%（>=95%）。
  - 新覆蓋率：process_jotform_submissions 100%、process_finished_sessions 95%（僅 22 行正常路徑未覆蓋）、attendance.py 99%（剩 21）、registration.py 99%（剩 142,178）。
- 2 個失敗：tests/db/test_jotform_sync_command.py::test_a_renamed_question_is_found_again_and_the_write_is_retried_once、::test_when_the_session_question_cannot_be_found_again_the_form_waits_for_the_admin。單獨執行也失敗、不引用本任務檔案、src 無變更，判定為既有問題（未在乾淨基線 checkout 另跑，屬推論）。建議新 backlog 項目調查（可能與環境或測試順序／日期有關）。
- manage check：no issues；makemigrations --check --dry-run：No changes detected；codemap update 後 codemap-check：OK。
- 未跑 integration；JOTFORM_API_KEY 以命令列假值提供（compose 另有 platform_key fixture 自行設定）。

## 假設
- 同日無開始時間的場次比 id，行為固定於現行實作。
- 提交已處理案例以 DISMISSED、ORDERED 兩種狀態參數化。
