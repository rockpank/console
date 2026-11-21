status: done
tests: 通過

# B-008 實作紀錄（specs/010-send-revalidation）

- 完成：T001–T081 全部勾選。
- 結果：`pytest tests/unit tests/db` 991 通過（基線 903，+88）；覆蓋率 98%（notifications.py 99%、send_check.py 100%）；ruff check／format 乾淨；`manage.py check` 無問題；`makemigrations --check --dry-run` 無變更；`code_map.py check` OK（已用 update 重產）。
- 變更：`src/crm/domain/send_check.py`（新）、`src/crm/line/notifications.py`、`src/crm/views.py`（僅 flash 文字）、`tests/unit/test_send_check.py`、`tests/db/{send_check_helpers,test_send_revalidation,test_send_follow_up_loop,test_send_retry_concurrency,test_send_payment_reminder_dedupe,test_send_skip_reasons_page}.py`、`tests/db/test_notifications_page.py`（僅一處，見下）、`docs/code_map/`（產生物）、`specs/010-send-revalidation/tasks.md`（勾選）。未動 model／migration／conftest。

## 與規格的差異／假設（需調度者知悉）
1. 既有測試 `test_staff_can_retry_failed_message` 用固定日期 2026-11-07 的場次；重驗以真實今天判斷「場次已結束」，該測試在 2026-11-17 起會被正確略過而變紅。只改了該測試的 fixture（場次日期改為今天+3），斷言未動。其餘既有測試未改。
2. 殘留 pending（BE-SVC-04/05）：原 `_send` 只處理「今天的收件人」，已移出場次／已付款者不會被撿到，因此在 `sync_notifications` 開頭加 `_skip_stale_pending`：掃專案內 pending 訊息，前提失效者標略過（計入 summary.skipped）；仍成立者留給原流程，以舊文字送出。
3. 追售類優先順序：不在場次 > 已報名進階 > 已停止追售（已報進階者通常同時被自動停止，原因以「已報名進階課程」較有資訊量）。
4. 重送 `attempts`：略過時保留原次數；要實際發送才歸零（避免略過紀錄的次數被改寫）。
5. 完款提醒：移除「先排除今天已提醒」的預篩，一律在學員列鎖內查重；已提醒者計 `skipped` 與新欄位 `SyncSummary.already_reminded`，一鍵提醒 flash 在有已提醒時加「其中 N 位今天已提醒過，不重複發送。」。同學員多張 partial 單只提醒一次。
6. 重送 flash：略過顯示「已略過，未重送：<原因>」。
7. 側記：BE-SVC-01/03、DB 各切片的測試與實作為批次撰寫（先寫整批測試確認 RED：21＋11 個失敗，再實作轉綠），非逐切片單跑；護欄型切片（BE-API-04/05/06/07、BE-CMD-01、BE-SVC-13 部分、未綁定／已封鎖順序）首次即綠，記為「已滿足」，未改產品碼。

## 已知限制
- 重送認領後程序中斷：session 為空的完款提醒會停在 PENDING（plan 已列殘餘風險）。
- 並行重送的輸家 flash 會顯示「重送仍然失敗：待發送」（僅文字，未加分支）。
- `attendance_tags._stop`、`followups.stop_follow_up` 仍為無鎖寫入（範圍外）。
