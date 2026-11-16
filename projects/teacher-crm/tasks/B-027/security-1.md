---
task: B-027
role: security-reviewer
verdict: 通過
date: 2026-11-17
round: 1
---

# B-027 資安審查（第 1 輪）：藍新／綠界回報解析異常補測

範圍：worktree `worktrees/B-027/teacher-crm/`（分支 t-B-027，未 commit）的變更。
- `tests/unit/test_gateway_callback_parse_errors.py`（140 行）
- `tests/db/test_gateway_notify_invalid_payload.py`（150 行）
- `specs/008-fix-gateway-callback-parse-tests/`（quickfix.md、tasks.md）
- `docs/code_map/*`（`make codemap` 產生物）

方法：全文閱讀兩個測試檔；對照受測的 `src/crm/gateways/newebpay.py`、`ecpay.py`、`checkout.py:70-110`、`views.py:852-859`；以 `git status`／`git diff -- src` 確認產品碼變更；grep 測試內的金鑰常數、mock、print／log／環境變數處理。

結論：未發現嚴重或高風險問題。有 2 項低風險建議（測試強度），不阻擋。

## 逐項結論

### ① 金鑰、HashKey、憑證、真實姓名／金額：通過（附低風險備註）

- 藍新：商店代號 `MS12345678`、HashKey 為 `1234…` 連號 32 字元、HashIV 為 `1234…` 連號 16 字元（`test_gateway_callback_parse_errors.py:14-16`、`test_gateway_notify_invalid_payload.py:20-24`）。明顯是假值，且與既有 `tests/unit/test_newebpay_gateway.py` 等檔使用的是同一組。
- 綠界：商店代號 `3002607` 與 HashKey／HashIV（`test_gateway_callback_parse_errors.py:19-21`、`test_gateway_notify_invalid_payload.py:19`）是綠界官方文件公開的沙箱測試資料，並非本專案的真實商店資料。這組值已存在於既有 `tests/unit/test_ecpay_gateway.py`、`tests/integration/test_ecpay_stage.py`、`tests/db/test_provider_flows.py` 等，新檔沒有引入新的外洩面。
  - 低風險備註：這串字元長得像真實金鑰，日後若導入 secret scanner（目前 CI 與 Makefile 內沒有）可能出現誤報。新檔沒有加註「官方公開沙箱值」。見 F-2。
- 沒有人名、身分證、電話、真實金額。金額 1500 是整數假值，單號 `T0001`、`26102517220001` 是假資料，專案名稱「專案甲」「專案乙」。學員資料由 `make_student` 產生，沿用既有慣例。
- 沒有讀取 `.env`，也沒有從環境變數取得金鑰。

### ② 憲法 MUST 2、4、7、8、9：通過

- MUST 2（真實資料庫、不 mock 業務函式）：兩檔 grep 無 `mock`、`patch`、`monkeypatch`。DB 測試走真實 PostgreSQL、Django `client`、真實的 `pay_page` 流程（`test_gateway_notify_invalid_payload.py:49-52`）、`create_order`、`GatewayConfig.set_hash_key`／`set_hash_iv`（`:39-41`）。`parse_callback`、`handle_gateway_callback` 都沒有被替換。
- MUST 4（專案隔離）：`:135-148` 建立專案 A、B 各一組設定、訂單、付款嘗試，只打 A 的端點，前後比對 B 的快照。見 ③ 的備註。
- MUST 7（外部服務 fake）：沒有任何對外連線。`pay_page` 只組表單，不發送請求。我 grep `views.py`／`checkout.py` 沒有 `requests`、`urlopen`、`httpx`。沒有新增 integration 測試。
- MUST 8（整數金額、機密）：金額用整數（`attempt.amount`、`str(attempt.amount)`），沒有 float。字串 `"1500.5"` 只作為「應被拒絕」的輸入。測試沒有 print、log、capsys，沒有把金鑰寫入任何輸出。
- MUST 9（驗簽）：每個案例都用 `aes_encrypt`、`trade_sha`、`check_mac_value` 以測試金鑰真實計算簽章（`unit:32-41`、`:101-118`；`db:55-90`），沒有替換驗簽。

### ③ 斷言是否真的驗證安全性質：通過（2 項低風險建議）

我逐案手動追蹤了產品碼分支，確認每個參數都落在預期分支：

- 藍新（`unit:59-81`，對應 `newebpay.py:96-103`、`:109-112`）：
  - 非 JSON 字串、字串 JSON 缺 `MerchantOrderNo`、`Result` 為數字、缺 `Result`、解密後非 JSON，分別是 `ValueError`、`KeyError`、`TypeError`、`KeyError`、`ValueError`，訊息都含「無法解析」。
  - `Amt` 為 `"abc"`、`"1500.5"`、`""`、`None`，分別是 `ValueError`、`ValueError`、`ValueError`、`TypeError`，訊息為「金額格式不正確」。
- 綠界（`unit:121-127`，對應 `ecpay.py:95-99`）：
  - 缺 `MerchantTradeNo` 或 `TradeAmt` 是 `KeyError`，`TradeAmt` 為 `"abc"`、`"1500.5"`、`""` 是 `ValueError`，訊息為「回報欄位缺漏或格式不正確」。
- 訊息關鍵字斷言（`unit:94`、`:140`）能區分失敗原因。簽章失敗的訊息（「檢查碼不符」「TradeSha 不符」「缺少欄位 …」「商店代號不符」）不含「無法解析」「金額」。唯一的例外是綠界簽章缺漏類訊息，同樣不含「欄位」以外的混淆：「缺少檢查碼」不含「欄位」。所以測試不會因為簽章算錯而「碰巧」通過。
- `pytest.raises(InvalidCallback)` 搭配 `as raised` 後在 `with` 區塊外斷言訊息，寫法正確，不是永遠為真。
- DB 測試（`db:129-150`）斷言 400，並比對 A 專案前後快照與 B 專案前後快照。快照包含訂單狀態與 `paid_amount`、付款嘗試的 `trade_no`／`status`／`gateway_trade_no`、`Payment` 筆數（`:93-104`）。`:149-150` 另外確認送出前是「待付款、0 元、已建立」，避免快照比對在空資料上成立。檢查項目對應 `handle_gateway_callback` 在 `parse_callback` 拋錯時不進入入帳交易（`checkout.py:73`），行為一致。
- F-1（低）：DB 測試只斷言狀態碼 400 與資料不變，沒有斷言 400 的「原因」（回應本文）。若日後簽章輔助函式壞掉、單號查不到或設定載入失敗，也會回 400 且資料不變，測試仍綠，變成驗不到「解析異常」本身。單元測試已用訊息關鍵字覆蓋這點，端點層補一行 `assert "無法解析" in response.content.decode()`（藍新）、`"欄位"`／`"金額"`（綠界）就能閉合。
- F-2（低）：隔離測試中 A、B 專案共用同一組金鑰與商店代號（`CREDENTIALS[provider]`），因此「B 專案設定被誤用於 A」這類錯誤無法被偵測。這已是本任務目標之外（目標是「A 端點收到異常回報不影響 B 資料」，測試確實驗證了這點）。若要加強，B 專案可使用不同的假金鑰。屬可選。

### ④ 是否放寬、繞過或改變產品碼：通過

- `git diff -- src` 零輸出；`git status --short` 中 `src/` 沒有任何變更（包含未追蹤檔）。
- 變更僅含 2 個新測試檔、`specs/008-…/`、`docs/code_map/*` 的產生物更新。code_map 的 diff 只是樹雜湊、檔案數、行數與測試對照的新增，內容與新增測試檔相符，沒有其他變更。
- 補充：quickfix.md「驗收」寫「沒有 `docs/code_map/` 變更」，與實際（有 `make codemap` 產物）不一致。這是任務指示許可的結果，屬文件用語落差，不涉安全。
- 沒有 skip、xfail、`pytest.mark.skip`、放寬的容差。

### ⑤ 密鑰與日誌輸出處理：通過

- 兩個測試檔都沒有 print、logging、caplog、capsys、環境變數讀取。金鑰只存在於模組常數，並只作為函式參數傳入，沒有輸出。失敗時 pytest 顯示的參數 id 是情境名稱（如 `amount-is-not-a-number`），不含金鑰。
- `InvalidCallback` 訊息不含簽章或金鑰，端點回應本文也只是訊息字串（`views.py:858`）。

## 發現清單

| 編號 | 嚴重度 | 位置 | 依據 | 建議 |
|---|---|---|---|---|
| F-1 | 低 | `tests/db/test_gateway_notify_invalid_payload.py:146` | 只斷言狀態碼 400，其他原因的 400 也會讓測試通過 | 加斷言回應本文含對應關鍵字（「無法解析」「欄位」「金額」）；可作為下輪小修，不阻擋 |
| F-2 | 低 | 兩檔 ECPAY 常數（`unit:19-21`、`db:19`） | 綠界公開沙箱值看起來像真實金鑰，且未註明 | 註解已有（unit 檔標明官方公開），db 檔未標；建議同樣加一行註解；未來若導入 secret scanner 需加白名單。不阻擋 |
| F-3 | 資訊 | `db:19-25`、`:135-136` | A、B 專案共用同一組金鑰，無法偵測跨專案設定誤用 | 可選：B 專案用不同假金鑰 |

沒有嚴重或高風險發現。

## 另立項目建議：藍新 `Amt` 為 JSON 浮點數時 `int()` 無聲截斷

評估：**低（資訊偏低）**，不構成可被利用的金額繞過，建議另立低優先項目（防禦性強化）。

實測（本機 Python 唯讀驗算）：
- `int(1500.9)` → `1500`，不報錯（`newebpay.py:110` 對 JSON 數值直接 `int()`；字串 `"1500.5"` 會被拒絕，兩者不一致）。
- 另外 `int(True)` → `1`、`int("1_500")` → `1500` 也會被接受。
- **`Amt` 為 `1e999`（JSON 解析成 `inf`）時 `int()` 拋 `OverflowError`，而 `newebpay.py:111` 只捕捉 `ValueError`、`TypeError`**，會往上變成未處理例外，端點回 HTTP 500 而不是 400（實測 `OverflowError`）。這是我在審查中順帶發現，測試未涵蓋。

利用性與影響：
1. 回報內容須通過 TradeSha 驗簽（需 HashKey），攻擊者在不知道金鑰的情況下無法構造任何 `Amt` 值；只有藍新本身或持有金鑰者能送出。
2. 入帳金額取自伺服器端的 `attempt.amount`（`checkout.py:99`），不是回報的 `Amt`；`result.amount` 只用於「與付款嘗試金額相等」的核對（`:86`），而且只在成功通知時核對。所以截斷最多讓 `1500.9` 被視為 `1500` 而通過核對，不會多入帳或少入帳。
3. 藍新實際回報的 `Amt` 是整數或字串整數，浮點數在正常流程不會出現。
4. 風險情境僅限：金鑰外洩後的偽造通知（此時攻擊者本來就能偽造任何金額）；或藍新格式變動時的「無聲吃掉小數」讓金額核對變鬆。

建議（另立，不在 B-027）：
- 在金額解析前先拒絕非整數型別：`if isinstance(raw, bool) or (isinstance(raw, float) and not raw.is_integer())` 拒絕；字串以 `str.isdigit()`／`fullmatch(r"\d+")` 驗證（同時排除 `1_500`、全形數字）。
- 捕捉 `OverflowError`，讓異常金額一律是 `InvalidCallback`（HTTP 400）而不是 500。
- 先補一個「先紅」的測試（Amt 為 `1500.9`、`true`、`1e999`），再修產品碼；綠界 `TradeAmt` 的 `int(str)` 同理可用同一個驗證函式（`ecpay.py:97` 只捕捉 `KeyError`、`ValueError`，字串輸入不會 OverflowError，但 `"1_500"` 同樣被接受）。
- 這個行為在 B-027 quickfix 已列為「本案例不驗證」並待釐清，補測本任務正確地沒有固化這個現象（沒有任何測試斷言它「應被接受」），之後修正不會與本任務的測試衝突。

## 未能驗證之處

- 未實際執行新測試。我只靠逐行比對產品碼推演每個案例的例外類型與訊息；執行結果（`make test-fast`、`make test`、覆蓋率）以 engineer 與 QA 的回報為準。理由：DB 測試需要 Docker，且本次要求唯讀，不寫入快取。
- 未檢查 `docs/code_map/` 以外的 CI 設定是否有 secret scanner（grep `.github`、`Makefile` 無相關字樣，僅此而已）。
- 綠界 `3002607` 組合確為官方公開沙箱資料，是依專案既有測試與註解（`unit:18`）所述，我沒有連線官方文件驗證。
- 範圍外既有問題（例如失敗通知不核對金額）不在本次審查，沒有列為發現。

## 結論

**通過。** 兩個新測試檔沒有真實機密、沒有違反憲法 MUST 2／4／7／8／9、斷言能實際驗證「驗簽通過但內容異常即拒絕、400、狀態不變、A/B 隔離」，且 `src/` 零變更。F-1、F-2、F-3 為低風險或資訊，可在後續小修時處理，不阻擋合併。另立項目建議見上節。
