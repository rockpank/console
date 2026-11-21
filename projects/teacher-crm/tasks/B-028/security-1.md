verdict: 通過

# B-028 資安審查 第 1 輪

範圍：worktree 相對 origin/master。新增 tests/unit/test_form_amount_validation.py、tests/db/test_amount_validation_pages.py、specs/018-.../（quickfix.md、tasks.md），並更新 docs/code_map 6 個檔。

結果（皆為靜態唯讀檢查）：
- src／model／tests/conftest.py／tests/db/test_gateway_settings.py：變更為零（git status／diff 確認）。
- 沒有弱化既有斷言：既有測試檔未修改，只新增檔案。
- 藍新 HashKey／IV 測試值是 "k"*32、"v"*16 這類重複字元的明顯假值，沒有真實金鑰、token、密碼。
- 沒有 requests／urllib／httpx／socket／subprocess／環境變數／檔案讀取，也沒有真實外部連線。
- 沒有真實個資（無 email、電話、身分證格式字串）。
- specs 文件只有欄位名稱與長度規則，沒有祕密值。
- 測試有檢查回應不回顯祕密，這是正向的做法。
- 未讀 .env。

發現：無（嚴重／高／中／低皆 0）。
