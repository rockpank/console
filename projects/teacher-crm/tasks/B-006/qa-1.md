---
verdict: 通過
round: 1
---
# B-006 QA 第 1 輪（042-fix-onsite-paid-default-unchecked）

環境：worktree B-006，docker compose run 等效 make，COMPOSE_PROJECT_NAME=b-006-qa，命令列假 JOTFORM_API_KEY；未讀不建 .env、未 down、未 commit。

| 項目 | 實際結果 | 通過 |
|---|---|---|
| pytest tests/unit tests/db | 903 passed（197.78s） | 是 |
| ruff check src tests | All checks passed | 是 |
| ruff format --check | 188 files already formatted | 是 |
| codemap-check | OK，最新（tree 988ba3018e33），無 STALE | 是 |
| 變更範圍 | src 僅 project_attendance.html 一行（移除 checked）；無 models/views/URL 變動 | 是 |
| TEST_LIST 901、909 行 | 皆改為預設不勾選、收款後自行勾選；與樣板、測試敘述一致 | 是 |
| 預設不勾選測試 | test_attendance_page_walk_in_form_shows_price_and_collect_checkbox 斷言含 name="paid" 且不含 checked，通過 | 是 |
| 勾選送出記已收款（現場收款） | 既有 test_walk_in_payment_shows_as_on_site_payment_in_payments_page，隨全套通過 | 是 |
| 不勾選送出不記收款 | 既有 test_staff_can_register_unpaid_walk_in_via_post，隨全套通過 | 是 |
| 權限／專案隔離 | 既有測試隨全套通過，views 未動 | 是 |
| 預覽站（8101）手動操作 | 僅確認 HTTP 302 可達；未登入建資料，**未執行**手動勾選流程，以上述測試補驗 | 未執行 |

缺陷：無。規格疑義：無。
備註：未執行 make coverage（impl-notes 稱 97%，本輪未複驗）。
