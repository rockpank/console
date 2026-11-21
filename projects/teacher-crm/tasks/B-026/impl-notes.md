---
status: done
tests: 通過
---

# B-026 實作筆記

- 完成：T001–T010（tasks.md 已勾選）。
- `src/crm/orders.py`：新增共用常數 `CONCURRENT_DUPLICATE_MESSAGE`；`create_order` 在交易區塊外捕捉 `IntegrityError`，轉成 `OrderError`。
- `src/crm/attendance.py`：`check_in_early` 捕捉 `IntegrityError` 轉 `AttendanceError`；`register_walk_in` 捕捉 `IntegrityError` 與 `OrderError`（來自 `ensure_intro_order`）轉 `AttendanceError`。三處訊息共用同一常數；交易整體回滾，失敗方不留部分寫入。
- 測試：`tests/db/test_concurrent_duplicate_friendly_error.py`（7 個：3 個併發、1 個併發參數化多一例、3 個序列重複維持原訊息）。
- 併發做法：兩條真實執行緒、`transaction=True`；把「先查」檢查包一層（查完後等柵欄，取得舊結果），確保兩邊都通過檢查再寫入，結果確定。連跑 3 次皆穩定。
- 先紅證據：修正前 4 個併發測試失敗，原因為 `IntegrityError`（unique_registration_per_session 等），與 quickfix 預期相符。

## 驗證（實際輸出）
- ruff check：All checks passed；ruff format --check：223 files already formatted
- manage.py check：no issues；makemigrations --check --dry-run：No changes detected
- pytest tests/unit tests/db：1301 passed，1 warning；覆蓋率 98.17%（門檻 95%）

## 假設與限制
- 端點層（`project_order_create` 等）未另寫併發端點測試；views 既有錯誤呈現路徑未動。
- `create_order` 的 `IntegrityError` 也涵蓋 order_no 重複（Jotform 路徑），一律顯示友善訊息。
- 未跑 `make codemap`／`codemap-check`（任務未授權手改、本機無 make）；改碼後建議調度者代跑。
- validate_artifacts 未執行（未動 spec 產物，僅勾選 tasks.md）。

## 第 2 輪（fix）：資安 M-1／M-2／M-3

變更檔案：`src/crm/orders.py`、`src/crm/attendance.py`、`tests/db/test_concurrent_duplicate_friendly_error.py`、`specs/045-fix-concurrent-duplicate-friendly-error/tasks.md`（追加 T011、T012 並勾選）。未動 views／model／migration／jotform／code_map。

- **M-1**：`register_walk_in` 不再捕捉 `OrderError`。`orders.py` 新增 `ConcurrentOrderError(OrderError)`，只有 `create_order` 撞到已知唯一約束時才拋；`register_walk_in` 只把這個子類轉成 `AttendanceError`，其餘 `OrderError`（專案不一致等）原樣往外拋、行為與 B-026 前相同。views 未動。
- **M-2**：新增 `constraint_name(exc)`（讀 `exc.__cause__.diag.constraint_name`，psycopg／PostgreSQL）與 `is_concurrent_duplicate(exc, operation, project_id)`。白名單：`unique_student_per_project`、`unique_registration_per_session`、`unique_active_order_per_student_product`、`unique_attendance_per_session_student`。不在白名單（含 order_no 撞號的 `crm_order_order_no_key`、取不到名稱）一律 `raise` 原例外。轉換時 `logger.warning("併發重複操作被擋下：operation=… constraint=… project=…")`，只含操作、約束名、專案 id。依據：併發測試（真實 PostgreSQL）實際取得 `unique_` 開頭約束名並寫入日誌，測試以 caplog 驗證且不含姓名／電話／金額。
- **M-3（只確認，未改 jotform）**：`jotform/registration.py::_book` 在 `transaction.atomic()` 內呼叫 `find_active_order(...) or create_order(student, intro, order_no=submission_id)`，呼叫端（`_book`、`process_submission`、`resolve`、views、management command）沒有 `except IntegrityError`／`except OrderError`，不會吞例外。order_no 撞號時 `create_order` 現在不在白名單，原樣重拋 `IntegrityError`（與 B-026 前相同）；其他併發落敗拋 `ConcurrentOrderError`（OrderError）。兩者都向外傳播，外層 `atomic()` 回滾（含 JotformSubmission 紀錄）。判定無問題。既有行為：此類例外在 jotform_return 仍是 500（B-026 前即如此，非本任務範圍）。
- 測試：新增 6 個（含參數化共 6 案例組）：日誌無個資、walk-in 非併發 OrderError 維持（2 個）、create_order 的 order_no 撞號重拋 IntegrityError、walk-in／early 無關 IntegrityError 重拋。原 7 個併發＋序列測試仍綠。誠實註記：新測試是在實作之後補寫，未先跑出紅燈（舊程式 (a)(b) 顯然會紅，未實測）。

驗證（實際輸出）：ruff check All checks passed；ruff format --check 223 files already formatted；`python src/manage.py check` no issues；makemigrations --check --dry-run No changes detected；併發測試檔連跑 3 次皆 13 passed；pytest tests/unit tests/db：1307 passed, 1 warning（指令 exit 0，覆蓋率門檻通過；覆蓋率百分比數字未截取到）。

## 第 3 輪（QA 第 2 輪 D-1，使用者裁示 A：只補測試）

變更（產品碼零新增差異；src/ 差異僅第 1、2 輪既有的 attendance.py、orders.py）：
- `tests/db/test_concurrent_duplicate_friendly_error.py`：匯入 `ConcurrentOrderError`；建單併發測試加 `assert isinstance(errors[0], ConcurrentOrderError)`；新增 `test_walk_in_converts_concurrent_order_error_to_attendance_error`（monkeypatch `ensure_intro_order` 拋 `ConcurrentOrderError`，斷言拋 `AttendanceError` 且訊息含「重新整理」、未建學員）。
- `specs/045-fix-concurrent-duplicate-friendly-error/tasks.md`：追加 T013（BE-API-05）並勾選。

暫時破壞證明會紅（皆已還原，`cmp` 與備份一致）：
- (E) orders.py 第 131 行改拋一般 `OrderError`：`E AssertionError: assert False + where False = isinstance(OrderError('同一筆資料剛剛已被另一位操作者處理，請重新整理頁面確認目前狀態'), ConcurrentOrderError)`；`FAILED test_concurrent_create_order_loses_with_friendly_order_error`，1 failed, 13 passed。
- (I) 拿掉 register_walk_in 的 `except ConcurrentOrderError` 區塊：`E crm.orders.ConcurrentOrderError: 請重新整理`；`FAILED test_walk_in_converts_concurrent_order_error_to_attendance_error`，1 failed, 13 passed。

驗證輸出：
- 該測試檔 3 次：14 passed ×3。
- `ruff check src tests`：All checks passed；`ruff format --check src tests`：223 files already formatted。（整個 repo 的 ruff 另有 `.claude/skills/_shared/tests/` 等既有問題：1 個 F401、6 檔待格式化，與本任務無關，未動。）
- 全套 `pytest`：1310 passed（含 tests/ 全部）；`pytest tests/unit tests/db --cov`：1308 passed，總覆蓋率 98.18%（>= 95%），attendance.py 100%、orders.py 100%。
