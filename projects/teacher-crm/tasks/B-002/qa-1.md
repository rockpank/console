---
verdict: 通過
round: 1
---

# B-002 QA 第 1 輪（動態驗證重跑）

依據：specs/009-fix-fake-gateway-when-disabled/{quickfix.md,tasks.md}、backlog B-002。以 diff 與重跑為準，不採信 impl-notes。
環境：worktree `worktrees/B-002/teacher-crm`，`COMPOSE_PROJECT_NAME=b-002-qa`，`docker compose run --rm app …`，假 JOTFORM_API_KEY 只在命令列，未讀 .env，未 down／commit／stash／reset。序列執行。無預覽站，功能驗證以自動化測試補驗。

## 基線與靜態檢查（全部實跑）

| 項目 | 結果 |
|---|---|
| pytest tests/unit tests/db | 1245 passed, 1 warning（既有 naive datetime 警告，與本任務無關），280.8s |
| tests/db/test_fake_gateway_disabled.py（新） | 11 passed |
| ruff check src tests | All checks passed |
| ruff format --check src tests | 217 files already formatted |
| python src/manage.py check | no issues |
| makemigrations --check --dry-run | No changes detected |
| codemap-check（python3 scripts/code_map.py check） | OK，code map 為最新（292 檔） |

## 功能驗證（對應 test_fake_gateway_disabled.py，皆實跑通過）

| 情境 | 預期 | 結果 |
|---|---|---|
| 旗標關：設定頁選項 | 不含「假金流」，仍有綠界／藍新 | 通過 |
| 旗標關：POST provider=fake | 被拒（200 重顯表單、不建立 GatewayConfig） | 通過 |
| 旗標關：gateway_for／card_available | 拒絕（GatewayNotConfigured／False） | 通過 |
| 旗標關：付款頁 | 400 + 「付款設定需重新設定」 | 通過 |
| 旗標關：notify | 400，訂單仍 PENDING、paid_amount 0、attempt 仍 CREATED | 通過 |
| 旗標關：complete | 404 | 通過 |
| A 專案 fake 不影響 B 專案 | B 的 gateway_for 正常、付款頁 200 含信用卡 | 通過 |
| 旗標開：設定頁含假金流、gateway_for 回 FakeGateway | 通過 | 通過 |
| 旗標開：HashKey 空／31 位元組被拒 | 200 + 訊息含 HashKey、不存檔 | 通過（參數化） |
| 旗標開：32 字元 | 302、加密存放 | 通過 |
| 旗標開：已存金鑰留空 | 沿用 | 通過 |
| 未啟用（enabled 關）不檢查 HashKey | 302 | 通過 |
| 其他 card_available 為 False 情境文案不變 | views.py 僅在「config 已啟用且為 fake 且旗標關」改文案，其餘維持「這個專案目前沒有開放信用卡付款」；既有 test_pay_page::test_pay_page_hides_card_option_without_enabled_gateway 等通過 | 通過 |

備註：「其他情境文案不變」是 diff 閱讀加既有測試通過，新測試檔沒有專門斷言舊文案（見建議）。

## 測試前置例外（docs/agent-protocol.md 第 8 節）— 結論：認可，四項皆成立

(a) 以 `git diff -- tests` 逐行檢視：test_checkout／test_jotform_gateway_numbers／test_pay_page／test_payments_search 各只多 `pytestmark = pytest.mark.usefixtures("fake_gateway_enabled")` 兩行（含空行）；test_gateway_settings 除 pytestmark 外只有 HASH_KEY 常數及其取代。新增／刪除／弱化斷言：無（斷言行數相同、型態相同，只有比對常數改變）。diff 中無 skip／xfail。`tests/db/conftest.py` 在 git status 中未被修改（`fake_gateway_enabled` fixture 為既有、非 autouse）。
(b) test_gateway_settings.py 的 6 處比對值（`set_hash_key`、`not in raw[0]`、refresh 後相等、儲存後相等、留空沿用相等、頁面不含）加上 `form_data` 預設值，全為 `"KEY-SECRET-123"` 取代為 `HASH_KEY = "KEY-SECRET-1234567890-ABCDEFGHIJ"`；逐字計算長度 32。`not in` 類斷言仍有意義（取代後的值同樣不得出現在密文／頁面）。純常數取代，無其他變動。
(c) 抽查：暫時刪除五個檔案的 pytestmark 行（先備份到 scratchpad），跑這五檔：23 failed, 29 passed。分佈：test_checkout 12、test_gateway_settings 5、test_pay_page 3、test_jotform_gateway_numbers 2、test_payments_search 1，合計 23，與工程師主張的「23 個既有測試原本會紅」完全吻合，證明前置設定有必要。已還原；還原後 `git status --short` 與 `git diff` 雜湊與實驗前完全一致。（紅燈原因為旗標關閉下 gateway_for／表單拒絕 fake，符合預期，非其他缺陷。）另：未被這五檔涵蓋的其他測試檔，在完整套件 1245 passed 下沒有紅燈，故無遺漏檔。
(d) 第 (1) 條「原本會紅」：本輪以「移除前置設定後在新 src 下實測紅燈」驗證，未用基線 checkout（不 stash／reset）；等價成立。

## 缺陷清單

無阻擋／高／中缺陷。

## 低風險觀察（非缺陷）

1. L-1：HashKey 長度以 `len(key.encode())`（位元組）計，spec 驗收說「字元」；全形字元會以較少字元數通過。與任務指示的「位元組」一致，僅提醒規格措辭。
2. L-2：新測試檔未對「旗標開且 provider 非 fake、card_available 為 False」逐一斷言舊文案，目前靠既有 test_pay_page 覆蓋。建議補一個小斷言（成本很低、價值中低）。
3. 作業事項：`docs/code_map/*` 有變更（產生檔，codemap-check 通過）；src 範圍僅 checkout.py、forms.py、views.py，與切片相符。

## 規格疑義

無。

## 結論：通過

依據：完整套件 1245 全綠、新測試 11 綠、lint／format／check／migrations／codemap 全過；功能矩陣全部通過；測試前置例外四項皆成立且 23 紅燈數實測吻合。限制：無預覽站，端到端以自動化測試（Django test client）補驗。

工具呼叫：9／45
