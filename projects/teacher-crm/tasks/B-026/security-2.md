---
verdict: 通過
task: B-026
reviewer: security-reviewer
round: 2
---

# B-026 資安審查（第 2 輪）

範圍：git diff origin/master 的 src/crm/attendance.py、src/crm/orders.py，以及呼叫端 views.py、checkout.py、jotform/registration.py、jotform/sync.py。方法：讀 diff 與 grep 全 src/ 的 OrderError 捕捉處。未執行測試與依賴掃描（未執行）；未讀 .env。

## 結論
第 1 輪的 M-1、M-2、M-3 皆已解決。無嚴重或高風險，無新增中風險。

## 上一輪發現驗證

- **M-1 已解決。** `register_walk_in` 只捕捉 `ConcurrentOrderError`。該例外只在 `create_order` 的 `except IntegrityError` 分支、且約束名稱在白名單時拋出。已取消訂單、金額失敗、專案不一致、「已經有這個課程的訂單」等其他 `OrderError` 都原樣往外拋。
  - `ConcurrentOrderError` 是 `OrderError` 子類，現有的 `except OrderError` 仍會接到它：views.py 739、769、802、817、939 與 checkout.py 111。這些處理器接到它時只會多顯示固定友善訊息（views 把 error 顯示給使用者）。checkout.py 111 是金流回呼入帳（`record_payment`），不會呼叫 `create_order`，行為不變。
- **M-2 已解決。** `is_concurrent_duplicate` 只在約束名稱屬於四個白名單時回 True，否則呼叫端一律 `raise` 重新拋出。`order_no` 撞號與其他 IntegrityError 都不會被轉成友善訊息。
  - `constraint_name` 用 `getattr(exc.__cause__, "diag", None)` 再 `getattr(..., "constraint_name", None)`。在非 PostgreSQL 或取不到時得到 None，`None not in 白名單`，所以回 False 並重新拋出，不會吞掉例外（fail-closed）。
  - 日誌只含 operation、constraint、project id，不含姓名、電話、金額、訂單編號。
- **M-3 已解決。** `_book` 在 `transaction.atomic()` 內呼叫 `create_order`。`create_order` 內層的 atomic 是 savepoint，IntegrityError 在內層回滾後轉成 `ConcurrentOrderError`。該例外往外傳出 `_book` 的 atomic，外層交易整體回滾，包含 JotformSubmission、Student 與 Registration 的寫入。
  - registration.py 與 sync.py 沒有捕捉 OrderError 或 IntegrityError。sync.py 的 `except Exception` 只包 `sync_form`，與 `_book` 無關。因此例外沒有被吞掉。

## 其他檢查
- 交易回滾：`check_in_early` 與 `register_walk_in` 的 try 都包在 `transaction.atomic()` 外層，捕捉發生在區塊離開、回滾之後，無半成品。
- 錯誤訊息：固定字串 `CONCURRENT_DUPLICATE_MESSAGE`，不含內部資訊；`raise ... from exc` 只保留在內部 `__cause__`，不輸出到使用者。
- 專案隔離：未改動任何查詢範圍，`create_order` 的專案一致檢查在前，未削弱。
- 無祕密或真實個資。

## 發現（低，僅記錄）
- **L-1（低）：** Jotform 導向與通知的 `_book` 併發落敗時，現在拋 `ConcurrentOrderError`（先前為 IntegrityError），呼叫端沒有捕捉，所以對使用者仍是 500，只是例外型別不同。`_book` 以 `select_for_update` 鎖定提交紀錄，實際上很難觸發，且資料一致。如要友善化，建議另開 backlog，不在本任務擴大範圍。
- **L-2（低）：** `constraint_name` 依賴 psycopg 的 `diag` 屬性。若日後換驅動或約束被改名，白名單會失效，退化為原本的 500（fail-closed，安全）。建議測試保留約束名稱斷言。
