---
verdict: 通過
round: 1
---

# B-002 資安審查（H-2 假金流閘門）第 1 輪

## 範圍與方法
審查 worktree `worktrees/B-002/teacher-crm` 相對 master 的 diff：`checkout.py`、`forms.py`、`views.py`、5 個既有測試、新測試 `tests/db/test_fake_gateway_disabled.py`、conftest fixture。以靜態閱讀與 grep 為準。

未涵蓋：測試重跑**未執行**。docker 存在，但 `docker compose run` 因 daemon 網路位址池耗盡失敗（all predefined address pools have been fully subnetted），尚未修復（非程式問題）。未讀 .env、compose 內旗標實際值。

## 入口逐一檢查（旗標 FAKE_GATEWAY_ENABLED 關閉時）
| 入口 | 結果 |
|---|---|
| 設定頁 POST（forms.py:337-351, 370） | provider choices 過濾掉 fake，直接 POST `fake` 會在欄位層 invalid；`_clean_fake` 還有第二層拒絕。通過 |
| 付款頁（views.py:930-935 → `card_available` → `gateway_for`） | `gateway_for` 在 fake+旗標關時拋 `GatewayNotConfigured`，`card_available` 回 False，回 400，不建立 attempt。通過 |
| `gateway_notify`（views.py:859） | 經 `handle_gateway_callback` → `gateway_for`（checkout.py:80），在驗簽前就拒絕，400。通過 |
| `fake_checkout`／`fake_complete` | `_fake_attempt_or_error` 旗標關即 404；且 `fake_complete` 最終也走 `handle_gateway_callback` 被擋（縱深防禦）。通過 |
| 跨專案 | 判斷以該專案的 `GatewayConfig.provider` 為準，ecpay／newebpay 專案不受影響；新測試有涵蓋。通過 |

所有進入 `get_gateway` 的路徑只有 `gateway_for` 一處，閘門單點且位置正確。

## HashKey 長度檢查
- 以 `len(key.encode())` 計位元組，UTF-8 多位元組字元不會被低估，符合預期。
- CharField 預設 strip，全空白會變空字串，被視為「未提供」，無法以空白繞過。
- 已存金鑰沿用：留空且已有金鑰則通過（設計如此）。

## 發現
- L-1（低）forms.py:376-381：沿用既有金鑰時不檢查其長度，歷史上存入的短 HashKey（< 32）可繼續啟用。僅在旗標開啟（開發／測試環境）時才相關，對 H-2 無影響。建議：沿用時以 `config.hash_key` 解密後同樣檢查，或記為已知限制。
- L-2（資訊）長度檢查只擋太短，不檢查熵（例如 32 個相同字元可通過）。限於旗標開啟環境，可接受。
- I-1（資訊）新文案「付款設定需重新設定，請聯絡行政人員」／「付款設定需重新設定」只透露設定需處理，未洩漏旗標、供應商、金鑰或內部路徑。通過。公開付款頁會間接顯示該專案曾設定過 fake，風險可忽略。
- I-2（資訊）`gateway_notify` 回應文字會把 `GatewayNotConfigured` 訊息回給公開呼叫者，此次訊息為固定字串，無洩漏。

## 既有測試改動
- 5 個檔案僅加 `pytestmark = usefixtures("fake_gateway_enabled")`，是明確開啟旗標的前置設定；全域 autouse fixture 把測試基準設為旗標關閉（與正式預設一致），方向正確。
- test_gateway_settings.py 僅把測試金鑰換成 32 字元常數 `HASH_KEY`，所有斷言（加密儲存、不在輸出出現等）都保留，未弱化。
- 沒有把不安全行為固化：旗標關閉的拒絕行為有獨立新測試。
- 待確認：未修改的其他測試若仍使用 fake 設定，會因基準關閉而失敗；需在可用環境重跑整個測試套件確認（未執行）。

## 結論
verdict: 通過。無嚴重／高／中風險發現；L-1 建議列入 backlog。條件：合併前須在可用環境完整重跑測試套件（目前「未執行」）。
