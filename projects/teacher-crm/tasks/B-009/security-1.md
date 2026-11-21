---
verdict: 通過
---
# B-009 資安審查（sec L-1，輕量）

範圍：src/crm/domain/line.py 的 verify_signature、src/crm/views.py:1161 line_webhook、新增測試與 specs/013-*（唯讀）。

- 空 secret：`if not channel_secret or not signature: return False`，空 secret 與空 HMAC key 簽出的內容不再通過。line_webhook 在驗簽失敗時回 400，早於任何事件處理。
- 比較：仍用 hmac.compare_digest（常數時間），未改動。
- 有效簽章流程不變：只多一個前置條件，非空 secret 的 HMAC-SHA256+base64 路徑原樣。
- 跨專案：webhook 以 URL 的 project_id 取該專案 LineConfig.channel_secret，A 專案 secret 簽的內容打 B 專案，HMAC 不符被拒。若 B 的 secret 為空也一律拒絕。
- 錯誤訊息：固定 "invalid signature"／400，不含 secret、不區分原因。
- 測試：test_line_domain 新增空 secret 單元測試；tests/db/test_line_webhook_empty_secret.py 驗 400、無回覆、不建立 LineAccount。
- 未執行：此環境無 pytest，測試未實際跑（以讀碼確認 helper 行為）；請 QA 實跑。
- 附帶觀察（資訊，非本任務）：secret 空時 webhook 永遠 400，屬預期（fail-closed）。

結論：通過，無新增發現。
