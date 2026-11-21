---
resume_at: 開發中
resolved: true
---

# 升級：B-011 —— 範圍擴大：jotform/sync.py 的 sync_all 加排序

- 條件：協議第 4 節第 6 條（超出 work-plan 檔案範圍）。
- 原因：全套測試中 `tests/db/test_jotform_sync_command.py::test_an_invalid_key_stops_automatic_retries_for_that_form_only` 順序相依、時有時無。根因（工程師二分，讀碼推論）：既有 `src/crm/jotform/sync.py::sync_all` 的查詢沒有 ORDER BY，測試隱含假設先建的表單先處理；B-011 新增的 `test_daily_job_status_page.py` 多寫入再回滾一批 JotformForm，改變了 PostgreSQL 回傳順序。

## 人工裁示

使用者裁示（2026-11-19）：選 A——B-011 順手在 `sync_all` 的查詢加 `.order_by("id")`（只此一行產品碼，行為不變，只讓處理順序確定），並加一個會先紅的回歸測試。已核准的範圍擴大僅限 `src/crm/jotform/sync.py` 這一處與其測試，不得趁機改其他 jotform 程式。
