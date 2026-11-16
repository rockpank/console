---
task: B-027
role: qa-engineer
verdict: 通過
date: 2026-11-17
round: 1
---

# B-027 QA 報告（第 1 輪）：金流回報解析異常補測

範圍：worktree `worktrees/B-027/teacher-crm/`（分支 `t-B-027`，未 commit），以 `COMPOSE_PROJECT_NAME=teacher-crm-b-027` 執行。
沒有可瀏覽行為，不開預覽站。未改動 worktree 內任何檔案（反轉驗證全在 scratchpad 副本）。

## 1. 品質關卡（自己實際執行的輸出）

| 關卡 | 結果 |
|---|---|
| `make lint` | `All checks passed!`、`190 files already formatted` |
| `make test-fast` | `325 passed in 2.25s` |
| `make test`（未提供 `JOTFORM_API_KEY`） | `2 failed, 919 passed`；失敗僅 `tests/db/test_jotform_sync_command.py` 的兩項（見第 4 節 P-1） |
| `make test`（`JOTFORM_API_KEY=fake-test-key`） | `921 passed in 72.24s`（基線 903 + 新增 18 = 921，相符） |
| `make manage cmd="check"` | `System check identified no issues (0 silenced).` |
| `make manage cmd="makemigrations --check --dry-run"` | `No changes detected` |
| `make coverage`（提供假金鑰） | `921 passed`；`TOTAL 4178 100 98%`（≥ 95% 通過）；`gateways/newebpay.py 65 0 100%`；`gateways/ecpay.py 49 0 100%`（兩檔 missing 欄皆空，原缺的 100、102-103、111-112 與 98-99 已覆蓋）。未提供金鑰時工程師實測為 97%，差異來自上述兩個失敗測試 |
| `make codemap-check` | `OK code map 是最新的（tree a9c604355f72，265 檔）`，無 STALE |
| `validate_artifacts.py all --package 008-fix-gateway-callback-parse-tests` | `quickfix.md`、`tasks.md` 皆 OK |

## 2. 驗收標準逐條驗證（依 quickfix.md「驗收」與三個切片）

| # | 標準 | 驗證方式與結果 | 判定 |
|---|---|---|---|
| 1 | BE-SVC-01：藍新簽章有效但內容異常拋 `InvalidCallback`，解析類訊息含「無法解析」、金額類含「金額」 | 讀碼：9 組參數（Result 非 JSON 字串、字串 JSON 缺 MerchantOrderNo、Result 為數字、缺 Result、解密後非 JSON、Amt 非數字／帶小數／空字串／null）；簽章以真實 `aes_encrypt`＋`trade_sha` 計算，無任何 mock；`pytest.raises(InvalidCallback)` 並斷言訊息關鍵字。實跑全綠 | 通過 |
| 2 | BE-SVC-02：綠界缺 `MerchantTradeNo`／`TradeAmt`、TradeAmt 非數字／帶小數／空字串，訊息含「欄位」 | 5 組參數；先改壞欄位再以真實 `check_mac_value` 重算檢查碼；實跑全綠 | 通過 |
| 3 | BE-API-01：對專案 A 端點送簽章有效的異常回報 → 400；A 的訂單（狀態、paid_amount）、付款嘗試（trade_no、狀態、gateway_trade_no）、Payment 筆數不變；**B 專案資料不變** | `snapshot()` 對 A、B 各取前後快照並 `assert snapshot(project_a, …) == before_a`、`assert snapshot(project_b, …) == before_b`；A、B 各有獨立設定、訂單與刷卡付款嘗試（4 種參數化：綠界缺 TradeAmt／非數字、藍新 Result 非 JSON／Amt 非數字）；真實 PostgreSQL、無 mock。另有前置斷言確認送出前 A 為 PENDING／0／CREATED，避免空轉 | 通過 |
| 4 | 覆蓋率：newebpay missing 不含 100、102-103、111-112；ecpay 不含 98-99；整體 ≥ 95% | 見第 1 節：兩檔皆 100%、整體 98% | 通過 |
| 5 | lint／check／makemigrations／codemap-check／validate_artifacts | 見第 1 節，全過 | 通過 |
| 6 | `make test` 903 只增不減；新增測試全綠 | 提供假金鑰 921 passed（+18）；`make test-fast` 325 passed | 通過 |
| 7 | diff 只含本套件與兩個新測試檔；無產品碼、既有測試、model、migration 變更；無真實金鑰、無 skip／xfail | `git diff HEAD -- src tests` 無差異（`src/` 零變更、既有測試檔零變更）；`git status` 顯示 tests 下只有兩個新檔（`??`）；`grep -E "skip|xfail|importorskip|mock|patch|monkeypatch"` 兩個新檔皆無命中；金鑰為 repo 既有測試用的假值與綠界官方公開測試商店資料；`tasks.md` 無未勾選項目（`[ ]` 數量 0） | 通過（`docs/code_map/` 有變更，見下方備註） |

備註（規格與實況不符，低）：quickfix 驗收寫「沒有……`docs/code_map/` 變更」且「通常不需 `make codemap`」，但實況新增兩個測試檔後地圖需更新（6 個產生檔變動：`INDEX.md`、`manifest.json`、`modules/src.crm.gateways.md`、`modules/src.crm.md`、`modules/tests.db.md`、`modules/tests.unit.md`）。這是 `make codemap` 產生物（專案 CLAUDE.md 規定地圖要與程式碼一起提交，CI 會檢查），不是手改；我不判為驗收未達，但請調度者在合併時知悉，且與 B-004／B-005 合併時依 work-plan 於合併後重跑 `make codemap`。我未驗證「不更新地圖會 STALE」（驗證需改動 worktree，未做），僅依專案規則與 codemap-check 輸出判斷。

## 3. 新測試「真的在測東西」：反轉／變異驗證

方式：在 scratchpad 建立 `src`、`tests`、`pyproject.toml` 的副本（`/private/tmp/claude-502/-Users-Park-Site-console/30f819db-ce92-4e93-9eaa-8247f858c0fe/scratchpad/mut-m1` … `mut-m9`），用 `docker run` 掛載副本、連 b-027 的資料庫容器執行新增的兩個測試檔。副本未改前先跑過：`18 passed`。每個變異只在副本改一處。

| 變異（皆在副本） | 預期 | 實際 |
|---|---|---|
| m1 藍新金額 `except (ValueError, TypeError)` 拿掉 `TypeError` | `amount-is-null` 變紅 | `1 failed, 17 passed`（`amount-is-null`） |
| m2 綠界 `int(data["TradeAmt"])` 改 `int(float(...))` | `amount-has-decimals` 變紅 | `1 failed, 17 passed`（`amount-has-decimals`） |
| m3 綠界 `except (KeyError, ValueError)` 拿掉 `KeyError` | 缺欄位案例變紅 | `3 failed`（單元 `trade-no-is-missing`、`amount-is-missing`；端點 `ecpay-amount-missing`） |
| m4 藍新解析 `except` 拿掉 `TypeError` | `result-is-a-number` 變紅 | `1 failed, 17 passed`（`result-is-a-number`） |
| m5 `gateway_notify` 400 改 200 | 端點 4 案例全紅 | `4 failed, 14 passed` |
| m6 `handle_gateway_callback` 在解析前把「其他專案（B）」的付款嘗試 `gateway_trade_no` 改掉（A 不變） | 只有 B 的不變斷言能抓到，端點 4 案例全紅 | `4 failed, 14 passed`：證明 B 專案不變斷言有效，不是只靠 A 的斷言 |
| m7 解析前把 A 的付款嘗試 `gateway_trade_no` 改掉 | A 快照斷言抓到 | `4 failed, 14 passed` |
| m8 端點測試把「綠界 TradeAmt 非數字」改送有效回報 | 400 預期失敗 | `1 failed, 3 passed`（確認 400 來自異常內容，不是別的原因） |
| m9 端點測試把「藍新 Result 非 JSON」改送有效回報 | 同上 | `1 failed, 3 passed` |

另外：沒有永遠為真的斷言（單元測試每案例檢查例外型別與訊息關鍵字；端點測試的快照比對在資料真的被改時會變紅，見 m6、m7）；沒有 skip／xfail／mock。

小觀察（不列缺陷）：端點測試只斷言 `status_code == 400`，沒有斷言回應內容的原因（理論上換成「金額與付款嘗試不符」之類別的 400 也會綠）。解析原因由單元測試以訊息關鍵字鎖定，端點層由 m8、m9 證明異常內容確實是 400 的原因，因此風險低；若要加強可在端點測試加斷言回應文字含「無法解析」「欄位」「金額」，價值低、成本 S。

## 4. 既有問題（另立項目，不影響 verdict）

**P-1（同 B-004 qa-1 的 P-1）：`tests/db/test_jotform_sync_command.py` 兩項在沒有 `JOTFORM_API_KEY` 環境變數時必失敗。**

- 受影響：`test_a_renamed_question_is_found_again_and_the_write_is_retried_once`、`test_when_the_session_question_cannot_be_found_again_the_form_waits_for_the_admin`。
- 本環境複核：此 worktree 沒有 `.env`，`compose.yaml` 以 `${JOTFORM_API_KEY:-}` 傳入；不提供變數時 `make test` 為 `2 failed, 919 passed`，失敗輸出含「平台尚未設定 Jotform 金鑰，略過同步。」；`export JOTFORM_API_KEY=fake-test-key` 後同一個 `make test` 為 `921 passed`。結論與 B-004 qa-1 一致：根因是兩測試依賴容器環境變數，而非日期；本任務未動這兩個測試或其產品碼（`src/`、既有測試零變更），與本任務無關。
- 建議（另立項目）：兩測試改用 `platform_key` fixture 或設定 `settings.JOTFORM_API_KEY`；價值中、成本 S。在修正前，任何沒有 `.env` 的 worktree 跑 `make test` 都會有這 2 個失敗，工程師 impl-notes 的 `tests: 失敗` 即源於此。

## 5. 缺陷清單

無（本任務造成的失敗為 0；驗收標準全部達成）。

## 6. 無法驗證之處／殘餘風險

- 「不更新 `docs/code_map/` 就會 STALE」未驗證（見第 2 節備註）。
- 全套 `make test` 是在提供假 `JOTFORM_API_KEY` 的條件下取得全綠；預設環境下的 2 個失敗屬 P-1。
- 藍新 `Amt` 為 JSON 浮點數（如 1500.5）被 `int()` 無聲截成 1500，與憲法 MUST 8 精神不一致：工程師已列為發現、quickfix 明列為不驗證範圍，我未自行測試、未列為本任務缺陷；建議調度者另開缺陷項（由讀碼確認 `int(result.get("Amt", 0))` 對 float 不拋錯）。這類屬金額輸入驗證，轉資安工程師評估亦合理，但僅在無法確定外部金流是否會送 JSON 數字金額時才有實際影響（回報有簽章保護，且之後有金額與付款嘗試核對）。
- 變異驗證用的是 b-027 的資料庫容器（新增測試只在 test 資料庫內操作）；scratchpad 的 `mut-m*` 目錄與 `qa-b027` 副本未清理。
- 無預覽站、無網頁操作（本任務不含可瀏覽行為）。

## 7. 結論

**通過。** 18 個新測試全綠，涵蓋三個切片與驗收標準（含「A 打端點、A 與 B 專案資料不變」的斷言）；`src/` 與既有測試零變更；覆蓋率 98%、兩個閘道檔 100%；9 組變異驗證證明測試會在行為被破壞時變紅；各品質關卡通過（`make test` 的 2 個失敗是既有 P-1，與本任務無關）。
