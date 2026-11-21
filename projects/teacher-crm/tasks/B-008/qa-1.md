verdict: 通過

# B-008 QA 第 1 輪（specs/010-send-revalidation）

## 實測（worktree，COMPOSE_PROJECT_NAME=b-008，假 JOTFORM_API_KEY，未讀 .env、未 down）
| 項目 | 結果 |
|---|---|
| pytest tests/unit tests/db | 991 通過、0 失敗（基線 903，+88），243 秒 |
| 覆蓋率 | 97.60%（門檻 95%）；notifications.py 99%（未覆蓋 223, 332, 352） |
| ruff check／format --check | 乾淨／196 檔已格式化 |
| manage.py check | 無問題 |
| makemigrations --check --dry-run | No changes detected |
| code_map.py check | OK（最新） |
| make test-fast（純邏輯無 DB，SC-004） | 未單獨執行；unit 測試已含「send_check 不 import django」斷言且在整套中通過 |

## 審視
(a) test_staff_can_retry_failed_message：只在建立學員前把場次日期改為 today+3（3 行新增），斷言未動。重驗以真實今天判斷場次已結束，固定 2026-11-07 在今天（2026-11-17）已過期，改動合理（FR-001 的直接後果）；斷言未弱化。
(b) _skip_stale_pending：對應 FR-001「殘留未發送的下一輪」與 testplan BE-SVC-04/05，只掃本專案 pending、前提不成立才標略過，成立者留給原流程，不與 FR-002/003/009 衝突；屬規格範圍內（impl-notes 已揭露）。小提醒：略過時於 sync 開頭執行，早於 missing_intro 之後才跑，沒問題。
(c) testplan 切片抽查：測試檔未以案例 ID 標註（grep ID 僅部分命中），改以內容比對：SVC-01/02/03 對應 tests/unit/test_send_check.py（參數化、原因常數、不 import django）；SVC-07 對應 test_send_retry_concurrency（Barrier）；SVC-09/10 對應 test_send_follow_up_loop（4 項）；SVC-11/FR-005 對應 test_send_payment_reminder_dedupe（並行、跨日、時區邊界）；API-11 對應 test_send_skip_reasons_page（7 種原因、無個資）。均有實質測試，無 skip／xfail。

## 缺陷
無阻擋／高／中。低：測試未帶 testplan 案例 ID，追溯性較差（建議在 docstring 補 ID，非必要）。

## 規格疑義
無新增。已知限制（重送認領後中斷會停 PENDING、並行輸家 flash 文字）為 plan 已列殘餘風險，非本輪缺陷。

## 結論
通過。依據：全套 991 通過、覆蓋率 97.6%、品質關卡全綠，三項審視無問題。
