---
verdict: 通過
---

# B-008 資安審查（第 1 輪）

範圍：worktree 相對 origin/master 的 `src/crm/domain/send_check.py`（新檔）、`src/crm/line/notifications.py`、`src/crm/views.py`，以及規格 specs/010。方法是靜態閱讀，沒有重跑測試，也沒有讀 .env。

## 無嚴重／高風險發現

- **重驗無法繞過**：`_deliver` 是所有發送的唯一出口，涵蓋同步發送、重送、完款提醒，都在 `push_text` 之前呼叫 `skip_reason`。
- **重驗用的事實有專案隔離**：`_gather_facts` 的每個查詢都帶 `project_id`，用的是 `message.project_id`，不是使用者輸入。
- **重送入口的授權正確**：`project_notification_retry` 有 `_project_or_404`、`Action.EDIT_DATA`，查訊息用 `for_project`，只收 POST。跨專案取不到訊息。
- **認領與提醒的競態有處理**：
  - 重送：`select_for_update` 加狀態轉換在 `atomic` 內，只有一個並行請求能把 FAILED 轉成 PENDING，沒搶到的直接返回。
  - 完款提醒：鎖學員列，在鎖內重讀訂單並查當天是否已提醒，才建立訊息。外部 LINE 呼叫在交易提交之後，沒有拿著鎖做網路 I/O。
  - 追售：停止時用條件式 `update`，不會覆蓋人工停止。
- **略過原因不洩漏個資**：`error` 欄內容是 `send_check` 的固定中文字串，沒有姓名、LINE ID 或金額。已用 `[:300]` 截斷。
- **沒有金鑰進入程式、日誌或訊息**：LINE 的 token 仍然只透過 `line_service.build_client`。

## 低／中風險（不擋）

1. **低**：`notifications.py` 的 `_deliver` 第 1 次重驗到實際 `push_text` 之間沒有鎖，存在極小的 TOCTOU 窗口。
   - 窗口內前提變更，仍可能多發 1 則。
   - 規格未要求更強保證，LINE 的 retry key 在 24 小時內也會去重。
   - 建議：維持現狀並在文件註明。
2. **低**：`retry_message` 認領成 PENDING 後，若處理程序在 `_finish` 前崩潰，訊息會停在 PENDING。
   - `_skip_stale_pending` 只會略過前提不成立者，前提成立的 PENDING 要靠「正常流程」才會被處理。
   - 重送入口只收 FAILED，所以這則訊息使用者無法手動重送。
   - 建議：確認 sync 對殘留 PENDING 的處理路徑。必要時在 `_skip_stale_pending` 或排程補一條「逾時的 PENDING 轉回 FAILED」。
3. **低**：`_create_reminder` 在鎖內建立訊息後、交付前若崩潰，當天不會再補提醒。這是失敗時偏安全的行為（寧可少發），可接受。
4. **低**：`retry_message` 呼叫 `_gather_facts` 時沒有傳 `today`，退回 `timezone.localdate()`。sync 傳進來的是專案的 `today`，兩邊若時區不一致，「場次已結束」在日界附近可能判斷不同。建議重送也傳專案本地日期。
5. **低**：`skip_reason` 對未知 kind 回傳 None（不攔截）。日後新增種類若沒補重驗規則，就會被直接發送。建議加一則測試，要求所有 kind 都有明確歸類。
6. **資訊**：追售類的 `in_session` 只檢查 `session_id is not None`，沒有確認 Registration 仍在，與規格「只看場次是否還在」一致。
7. **資訊**：`str(error)` 的 LineApiError 內容會寫進 `error` 欄並顯示在 UI。這是既有行為，不屬於本次變更。範圍外未審 LineApiError 內容是否含回應本文。

## 未涵蓋

- 沒有執行測試或依賴掃描。
- 沒有實際在 PostgreSQL 上驗證 `select_for_update` 的行為，只做靜態審查。
- `OutboundMessage.objects.for_project` 的實作、sync 中 `_send` 的去重邏輯屬既有程式，未逐行審。

結論：通過。上列低風險項目記入 status.md「事後可瀏覽」。
