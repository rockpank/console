---
verdict: 通過
---
# B-006 資安審查（輪次 1，輕量）
範圍：project_attendance.html 拿掉 paid checkbox 的 checked；測試、specs、code_map 變更。
- 後端未變：views.py:1395/1400 以 POST paid == "on" 判斷，未勾 = 未收款（fail-safe 預設）。無後端行為變更。
- 預設改為不勾選：降低誤記已收款風險，金額記錄正確性只會更保守；價格來自伺服器端 intro，非客戶端傳入。
- 權限／專案隔離（MUST 4、5、8）：本次未觸及任何 view、查詢或權限邏輯。
- 測試與 specs、code_map 僅文件／測試，無機敏資料。
發現：無嚴重／高／中；資訊：無。
