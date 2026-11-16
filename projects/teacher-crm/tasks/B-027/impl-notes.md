---
task: B-027
role: engineer
status: done
tests: 失敗
date: 2026-11-17
---

# B-027 實作筆記（engineer）

`tests: 失敗` 只因 `make test` 有 2 個基線就紅、與本任務無關的失敗（見下）；新增的 18 個測試全綠，沒有因本任務新增的失敗。

## 變更檔案（worktree `worktrees/B-027/teacher-crm/`，分支 `t-B-027`，未 commit）

- 新增 `tests/unit/test_gateway_callback_parse_errors.py`（BE-SVC-01、BE-SVC-02，14 案例）
- 新增 `tests/db/test_gateway_notify_invalid_payload.py`（BE-API-01，4 案例）
- 修改 `specs/008-fix-gateway-callback-parse-tests/tasks.md`：只把 T001–T010 回寫為 `[X]`
- 由 `make codemap` 產生（非手改）：`docs/code_map/INDEX.md`、`manifest.json`、`modules/src.crm.gateways.md`、`modules/src.crm.md`、`modules/tests.db.md`、`modules/tests.unit.md`。quickfix 預期「通常不需 make codemap」，但新增測試檔後 codemap 判為過期，依 engineer-rules §4 已更新。
- 沒有任何產品碼、既有測試、model、migration 變更；無 skip／xfail；無 mock（藍新用真實 AES／TradeSha，綠界用真實 CheckMacValue，DB 測試用真實 PostgreSQL）。

## 案例

- 藍新（解析類，訊息含「無法解析」）：Result 為非 JSON 字串、Result 為 JSON 字串但缺 MerchantOrderNo、Result 為數字、缺 Result、解密後不是 JSON；（金額類，訊息含「金額」）：Amt 非數字字串、帶小數字串、空字串、null。
- 綠界（訊息含「欄位」）：缺 MerchantTradeNo、缺 TradeAmt、TradeAmt 為非數字、帶小數、空字串；每案例改壞欄位後重算檢查碼。
- 端點（參數化 4 種：綠界缺 TradeAmt／TradeAmt 非數字、藍新 Result 非 JSON／Amt 非數字）：專案 A、B 各一組設定、訂單、刷卡付款嘗試；對 A 的端點送簽章有效的異常回報 → 400；A 與 B 的訂單（狀態、paid_amount）、付款嘗試（單號、狀態、gateway_trade_no）、Payment 筆數前後快照相同。

## 紅燈（已綠覆蓋率補強）／反轉驗證

三個切片皆「一寫就綠」（`tdd/RULES.md` §RED已綠 Rule 2），以暫時反轉確認映射正確後刪除暫存副本（原檔未動）：

- 單元：把預期訊息關鍵字全換成不存在字串 → `14 failed`；把預期例外改成 `KeyError`（即預期不是 InvalidCallback）→ `14 failed`；原檔 `14 passed`。
- 端點：預期狀態碼改 200 → `4 failed`；改送有效回報 → 4 案例皆 `assert 200 == 400` 失敗；原檔 `4 passed`。

## 品質關卡實際輸出

- `make lint`：`All checks passed!`、`190 files already formatted`
- `make test-fast`：`325 passed`
- `make test`：`2 failed, 919 passed`。失敗為基線已知兩項：`tests/db/test_jotform_sync_command.py::test_a_renamed_question_is_found_again_and_the_write_is_retried_once`、`::test_when_the_session_question_cannot_be_found_again_the_form_waits_for_the_admin`（未動）。基線 903 通過 + 本次 +18 = 921，與 919 通過 + 2 失敗相符。
- `make manage cmd="check"`：`System check identified no issues (0 silenced).`
- `make manage cmd="makemigrations --check --dry-run"`：`No changes detected`
- `make coverage`：整體 `TOTAL 4178 112 97%`；`gateways/newebpay.py` 65 行 0 missing 100%（原 92%）；`gateways/ecpay.py` 49 行 0 missing 100%（原 96%）。同樣有上述 2 個失敗（測試失敗不影響覆蓋率門檻判定；門檻 95% 通過）。
- `make codemap` 後 `make codemap-check`：`OK code map 是最新的（tree a9c604355f72，265 檔）`，無 STALE。
- `validate_artifacts.py all --package 008-fix-gateway-callback-parse-tests`：quickfix.md、tasks.md 皆 OK。

## 發現（另立項目建議）

1. **藍新 Amt 為 JSON 浮點數時被無聲截斷**（`gateways/newebpay.py` `int(result.get("Amt", 0))`）：Amt 為 `1500.5`（JSON 數字）會變成 1500 而不拋錯；字串形式 `"1500.5"` 則會被拒絕（已測）。與憲法 MUST 8 精神（金額禁 float）不一致。未寫成測試、未修。建議另開缺陷項。
2. 藍新 Amt 缺漏時預設為 0（`result.get("Amt", 0)`），失敗通知不帶金額是預期；但成功通知缺 Amt 會得到金額 0，之後由 `handle_gateway_callback` 的金額核對擋下（400「金額與付款嘗試不符」）。屬縱深防禦成立的現況，僅供知悉，未列為缺陷。
3. backlog 驗收文字「Result 字串形式 JSON 一律 InvalidCallback」與實際程式不同（合法 JSON 字串會正常解析），L100 改由「字串但非 JSON」「字串 JSON 缺 MerchantOrderNo」案例覆蓋；與 pm 在 quickfix 待釐清事項的解讀一致，未另測合法字串 Result 的正向案例。

## 假設與殘餘風險

- 「空值」解讀為空字串與 JSON null 兩種都測（藍新）。
- BE-API-01 的專案 B 資料不變是對「打 A 端點」的快照確認；以 B 單號打 A 端點不在範圍。
- 測試以 docker 容器內單檔 pytest 輔助驗證（Makefile 無單檔目標），未改 Makefile。
- `make test` 的 2 個紅燈在基線即存在，非本任務造成，也未驗證其成因。
- `docs/code_map/` 有變更（產生物），合併時若與 B-004／B-005 衝突，依 work-plan 於合併後重跑 `make codemap`。
