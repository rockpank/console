---
verdict: 通過
round: 1
---
# B-032 資安輕量審查（round 1）

範圍：worktrees/B-032/teacher-crm 相對 base 的變更。新增 tests/db/test_line_outbound_paths.py、tests/db/test_line_binding_edge_cases.py、specs/031-*、docs/code_map。src/ 無變更（git diff -- src 為空）。

## 發現
無嚴重／高／中風險。

- 測資：全為假資料（0912345678、0911000001 等明顯假號碼、假 LINE user id 如 U-edge-1、假名）；SECRET 取自 line_helpers 測試常數，未見真實金鑰／token／email。grep 未命中真實格式個資。
- 外連：僅用 FakeLineClient 與 Django test client，無 requests／urlopen／socket；pay link 只組字串比對。
- 簽章：測試涵蓋缺 header 與錯誤簽章（400 "invalid signature"、DB 無變動、無回覆），非 JSON／陣列 body 簽章後回 400；未把不安全行為固化。
- 跨專案隔離：B 專案 unfollow 不影響 A；bind view 拒絕他專案學員、他專案 issue 回 404 且資料不變。斷言皆為「拒絕」方向，無固化越權。
- 未弱化既有防護：未見 monkeypatch 關閉驗簽或權限。
- 資訊（低）：BE-API-05 停用設定回 200 且不處理，屬現行行為特徵化，合理。

## 未涵蓋／限制
- 重跑測試：未執行。環境無 pytest（python3 -m pytest: No module named pytest），且測試需 PostgreSQL；結論以靜態審查 diff 為準。
- 僅讀兩支測試的大部分內容；test_line_outbound_paths.py 只讀 225-285 行與 grep 掃描，其餘靠關鍵字掃描。
- 依賴掃描：未執行（本變更未動依賴）。

結論：通過。
