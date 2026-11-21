---
verdict: 通過
task: B-026
reviewer: security-reviewer
round: 1
---

# B-026 資安審查（第 1 輪）

範圍：src/crm/attendance.py、src/crm/orders.py、tests/db/test_concurrent_duplicate_friendly_error.py、specs/045-*（git diff origin/master + 未追蹤檔）。方法：讀 diff、呼叫端（views、jotform/registration）與 models 唯一約束；未執行測試與依賴掃描（未執行）；未讀 .env。

## 結論
無嚴重／高風險。以下皆為中／低，只記錄不阻擋。

## 發現

### M-1（中）register_walk_in 把所有 OrderError 一律轉成「重複操作」訊息
位置：src/crm/attendance.py:162（`except (IntegrityError, OrderError)`）。
register_walk_in 內的 OrderError 來源不只併發：create_order 的「已有訂單」「課程與學員不屬於同一專案」，以及 mark_order_paid→record_payment 的「訂單已取消」「金額檢查失敗」（orders.py:141/144）。這些真實資料問題（例如已取消訂單、專案設定錯誤）會被誤報成「剛剛已被另一位操作者處理」，櫃台人員重新整理後看不到原因，且對帳上難以察覺。屬可用性／可診斷性問題，非越權。
建議：只捕捉 IntegrityError；OrderError 原樣往上拋（其訊息本來就是給行政人員看的友善文字），或在 create_order 內拋專用子類別（如 ConcurrentDuplicateError）再只捕捉它。

### M-2（中）IntegrityError 一律視為併發重複，且未記錄
位置：attendance.py（check_in_early、register_walk_in）、orders.py create_order 的 except。
任何約束失敗（NOT NULL、其他 unique 如 order_no、trade_no、unique_student_per_project 以外的）都被轉為同一訊息，原例外只用 `from exc` 串接，沒有 logger 記錄，營運端看不到真正原因。
建議：捕捉後 `logger.warning(..., exc_info=True)`（不要記個資：姓名／電話），或檢查約束名稱（`exc.__cause__.diag.constraint_name`，PostgreSQL）只對已知唯一約束轉友善訊息，其餘重新拋出。

### M-3（中，待確認）Jotform 路徑的 order_no 衝突行為改變
位置：orders.py create_order（order_no=submission_id，由 jotform/registration.py:104 呼叫）。
原本 order_no 撞號（unique）時 IntegrityError 向上冒出，Jotform 處理流程能看到例外並走重試／人工；現在變成 OrderError。jotform 模組內沒有針對 OrderError 的 except（grep 無），所以仍會往外傳、外層 transaction 照常回滾（內層 atomic 是 savepoint，狀態一致），不會被默默吞掉；但例外型別變了，若外層（views／重試任務）以 IntegrityError 或特定型別判斷，行為可能不同，且訊息變成「另一位操作者處理」，與提交編號重複（可能是重送或對帳問題）無關。外層已有 select_for_update 鎖定同一 submission 記錄，正常重送會走「ORDERED 直接沿用」，故實際撞號機率低。
建議：確認 jotform 呼叫端對例外的處理（待確認）；對 order_no 衝突另寫日誌，或在有傳入 order_no 時不轉換。

### L-1（低）交易一致性：通過
三條路徑的 `transaction.atomic()` 都在 try 內，例外離開區塊時整體回滾，無半成品訂單／報名／出席；create_order 在 Jotform 外層交易內為 savepoint，回滾範圍正確。_record 使用 get_or_create，其內部 IntegrityError 被 get_or_create 自行處理。

### L-2（低）訊息洩漏：通過
CONCURRENT_DUPLICATE_MESSAGE 為固定中文字串，不含例外內容、SQL、約束名稱或個資；例外只以 `from exc` 保留於 traceback，未傳到使用者。

### L-3（低）跨專案隔離：通過
diff 未更動任何 project 過濾、`_check_project` 或 `for_project` 查詢；create_order 的專案一致檢查保留在 try 之前。測試資料為假資料，無祕密／真實個資。

### L-4（低）check_in_early 的 except 僅含 IntegrityError，範圍合理
但同樣受 M-2 影響（任何約束失敗皆顯示為併發訊息）。

## 建議處理順序
M-1、M-2 可在本任務順手修（改動小）；M-3 確認後再決定。皆不阻擋合併。
