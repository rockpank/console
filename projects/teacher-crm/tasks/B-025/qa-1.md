verdict: 通過

# B-025 QA 第 1 輪

範圍：worktree `worktrees/B-025/teacher-crm`（分支 t-B-025）相對 origin/master 的變更。
變更檔：`src/crm/domain/roster.py`、`src/crm/views.py`、新增 `tests/db/test_import_limits.py`、`specs/016-import-size-limits/`、code_map（工具產生）。無 models／migration 變更。
環境：docker compose run（COMPOSE_PROJECT_NAME=b-025，JOTFORM_API_KEY 假值）。未讀 .env、未連外部服務。預覽站未啟動（未執行），以測試驗證。

## 實際指令結果

| 關卡 | 結果 |
|---|---|
| ruff check src tests | All checks passed |
| ruff format --check | 189 files already formatted |
| pytest tests/unit tests/db --cov=src | 912 passed（基線 903，新增 9）；TOTAL 97%（門檻 95）；roster.py 100%；views.py 98%（未覆蓋行 243、586… 皆非本次變更） |
| manage.py check | no issues |
| makemigrations --check --dry-run | No changes detected |
| codemap-check | OK，最新（264 檔） |

## 驗收對照（diff 與測試檔自行審閱）

| 驗收標準 | 實作 | 測試 | 結果 |
|---|---|---|---|
| 大於 2 MB 以 file.size 在讀入前拒絕，友善錯誤含 2 MB，不建資料 | views.py MAX_IMPORT_BYTES | test_file_over_2mb_is_rejected_without_creating_data；恰 2 MB 接受 | 通過 |
| 超過 5000 列拒絕（空白列不計），恰 5000 可匯入 | roster.py MAX_ROWS | test_5001_rows_rejected_and_5000_accepted、test_blank_rows_do_not_count | 通過 |
| 姓名 >100、住址 >255 逐列錯誤，整批不匯入，不 500；邊界值照常匯入 | roster.py | test_overlong_name_and_address_reported_per_row、test_name_100_and_address_255、多重錯誤 | 通過 |
| 單一超大欄位（csv 模組上限）友善錯誤 | csv.Error 捕捉 | test_single_huge_field | 通過 |
| 合法檔案結果不變 | 錯誤判斷改為 len(errors)==error_count，語意與原 `name and valid phone` 等價 | 既有匯入測試全數通過 | 通過 |
| 跨專案隔離／權限不變 | 未改 | test_other_project_member_cannot_import_into_session | 通過 |

## 缺陷

無。

## 備註（低，非缺陷）

- 超過 5000 列時只回報單一錯誤並提前結束，不列出其前面各列的其他錯誤；符合規格「顯示友善錯誤」。
- 2 MB 檢查依 `file.size`；Django 上傳處理會先行接收檔案，故保護僅限於不整檔讀入記憶體解析，符合規格文字。
- 預覽站端到端：未執行。

## 結論

通過。所有品質關卡通過，驗收標準皆有對應測試且重跑通過。
