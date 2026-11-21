---
status: done
tests: 通過
---
# B-025 impl-notes

- T001–T010 完成（TDD：RED 5 失敗 → GREEN）。tasks.md 已回寫 [X]。
- 變更：`src/crm/domain/roster.py`（MAX_ROWS=5000、MAX_NAME_LENGTH=100、MAX_ADDRESS_LENGTH=255、csv.Error 友善錯誤）、`src/crm/views.py`（MAX_IMPORT_BYTES=2MB，讀入前檢查 file.size）、新增 `tests/db/test_import_limits.py`（9 則）、`docs/code_map/*`（make codemap 產生）、`specs/016-import-size-limits/tasks.md`。
- 額外：單一欄位超過 csv 模組 131072 字元上限原本會 500，已改為「欄位內容過長或格式不正確」友善錯誤（測試覆蓋）。
- 列數超限只回報一筆錯誤（行號為第 5001 筆資料列）。
- 品質關卡（make 不存在，改用 docker compose，COMPOSE_PROJECT_NAME=b-025）：ruff check 通過、ruff format 189 檔乾淨、manage check 無問題、makemigrations --check 無變更、pytest unit+db 912 passed、覆蓋率 97%（roster.py 100%）、codemap-check OK。
- 範圍：動到 roster.py，已超出 work-plan 原列檔案，需調度者確認。
