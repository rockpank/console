status: done
tests: 1365 passed（pytest tests/unit tests/db --cov=src --cov-fail-under=95，覆蓋率 98.23%；login.py 100%、throttle.py 99%）；ruff check／format --check 乾淨；manage.py check 無問題；makemigrations --check 無變更
progress: T001–T165 全部完成（第 3 輪：US3、US4、Phase 7）；殘留：_wip/draft 未能移除（見第 3 輪風險）

## 第 0 步：清理
- (a) 草稿原樣備份到 `specs/044-public-endpoint-rate-limit/_wip/draft/`：`settings.py.patch`、`Makefile.patch`、`views.py.patch`、`conftest.py.patch`＋`conftest.py.full`、`throttle.py`、`test_throttle_{cache,jotform,login,pay}.py`、`throttle_helpers.py`。
- (b) 用 `git show HEAD:<路徑> > <路徑>` 還原 settings.py、Makefile、views.py、tests/db/conftest.py；移除 src/crm/throttle.py 與 tests/db 下 5 個 throttle 檔（皆已備份）。未用 checkout／reset／stash／clean。
- (c) 還原後 `git status` 只剩 `?? specs/044-public-endpoint-rate-limit/`。基線（HEAD、JOTFORM_API_KEY=fake、--create-db）：**1294 passed**，覆蓋率 98%。**與派工單「不少於 1301」不符**：HEAD 實際為 1294，請調度者更正基準（本輪結束 1311 = 1294 + 17 個新測試）。
- 草稿只當參考，產品碼與測試都重寫，未整份貼回。

## 變更檔案
- `src/config/settings.py`：新增 `CACHES`（`default` 明確寫為 LocMem，因為定義 CACHES 後 Django 要求 default，內容等同內建預設；`throttle` = DatabaseCache、`crm_throttle`、MAX_ENTRIES 20000、CULL_FREQUENCY 3）。
- `Makefile`：`migrate` 目標後追加 `createcachetable`。README／compose／Dockerfile 無 migrate 字樣可追加（grep 無命中），未改；部署端的啟動指令需有人加 `createcachetable`（見風險）。
- `src/crm/throttle.py`（新）：`LIMITS`（含 `ATTEMPT_OPEN_WINDOW_MINUTES=30`）、`now()`、`client_ip()`、`hit()`（固定窗，1 讀 1 寫）、`redirect_rejection`／`webhook_bad_token_rejection`／`webhook_project_rejection`（含日誌 `crm.throttle`、429 提示頁、純文字 429＋Retry-After）。
- `src/crm/views.py`：`from crm import throttle`；`jotform_return`、`jotform_webhook` 各加薄呼叫。
- `tests/db/conftest.py`：autouse `throttle_cache`（LocMem＋每測試前 clear）、`fixed_clock`、`broken_throttle_cache`、`database_throttle_cache`。
- `tests/db/throttle_helpers.py`（新）：`BrokenCache`、`CountingCache`、Jotform 商店 helper、付款頁／回報／嘗試／使用者／平台管理頁 helper（FX-6～FX-9，供 US2～US4 使用）。
- `tests/db/test_throttle_jotform.py`、`tests/db/test_throttle_cache.py`（新）。
- `specs/044-…/tasks.md`：T001–T054 勾選。

## 實作決策（揭露）
- 停用專案（`Project.is_active=False`）與不存在的專案：不節流、維持原回應（api-plan 與 BE-API-11）。通知入口「無 JotformForm」視為找不到，不計次。
- 計數鍵：REDIRECT／WEBHOOK_BAD_TOKEN＝來源＋專案；WEBHOOK_PROJECT＝專案；鍵為 sha256 前 32 碼。
- BE-API-04／17 的「Jotform 呼叫數」：同一提交編號重送時既有流程不再呼叫 Jotform（已處理），所以改為「第 N 次以新提交編號驗證不呼叫／恢復後呼叫」；BE-17 斷言為讀寫各 1～2 次且與累計次數無關。
- fail-open（快取例外放行）屬 Phase 7 的 BE-API-12，本輪**未做**：目前快取表不存在或後端故障會 500，**部署前必須先 createcachetable，且 Phase 7 完成前不可上線**。

## 紅燈證據
- 基線後、實作前跑新測試：14 個案例中 **9 failed、1 error、5 passed**（失敗原因＝端點未節流／`client_ip` 不存在；error＝我的 autouse fixture 在 teardown 清空 DatabaseCache 時 DB 已關，已修）。
- 首跑即綠的 5 個特徵案例（BE-API-01、04、06、09、11）以「暫時破壞再還原」證明會紅（還原後 diff 確認無殘留）：
  - BE-01：REDIRECT 59 → 失敗 `test_the_60th_redirect…`
  - BE-04：REDIRECT 30 → 失敗 `test_fifty_people…`
  - BE-06：WEBHOOK_BAD_TOKEN 19 → 失敗 `test_a_wrong_secret_up_to_the_20th…`
  - BE-09：正確密鑰也計入來源錯誤計數 → 失敗 `test_correct_secret_notifications…`
  - BE-11：移除 `is_active` 判斷 → 失敗 `test_missing_or_inactive…`
- **流程偏離**：BE-API-16、BE-API-18、JOURNEY-01 的測試是在 throttle.py 已含文案／429 之後才寫（我先把 US1 的產品碼一次寫完，而非逐切片交錯），因此屬首跑即綠；以破壞驗證：文案加上「（20 次）」→ BE-16 失敗；窗口永不歸零 → BE-03、BE-18 失敗。其餘切片的 RED→GREEN 是以批次（先寫全部測試、跑紅、再寫實作）而非一個切片一輪完成；REFACTOR 步驟無需修改（T011 等已勾選，無行為整理）。
- 另：全套基線與紅燈驗證期間，我曾在背景全套測試執行中修改 settings.py／conftest，基線數字（1294）取自測試啟動前已載入的程式，未受影響。

## 實際測試輸出
- `pytest tests/unit tests/db --cov=src --cov-fail-under=95 -p no:cacheprovider -q --create-db`：`1311 passed, 1 warning in 339.87s`；`Total coverage: 98.19%`；`src/crm/throttle.py` 98%（未涵蓋 1 行為 `Rule` 之外的分支）。
- `ruff check src tests`：All checks passed；`ruff format --check src tests`：226 files already formatted。
- `manage.py check`：no issues；`makemigrations --check --dry-run`：No changes detected；`createcachetable --dry-run` 輸出 CREATE TABLE "crm_throttle"（表不在 migration 體系）。
- `make codemap` 未跑（本機無 make；`docs/code_map/` 由合併者重跑）。

## 風險與待辦
- 本輪額外建立了一個 compose 專案 `b-014-lint`（只為 lint 重跑，含一個網路、一個 volume、一個映像）；依規定未執行 `docker compose down`，需要時請調度者透過 `bin/console` 清理。
- ruff 在 settings.py 已格式化；`tasks.md` 結尾換行未變。
- 下一輪（US2）：付款頁節流、`TransferClaim`／`PaymentAttempt` 計數與 30 分鐘窗；FX-6～FX-9 helper 已備好但未被實際測試驗證，US2 起以實測為準。


---

# 第 2 輪（US2：T055–T103）

## 變更檔案
- `src/crm/throttle.py`：`pay_post_rejection`（PAY_POST，鍵＝來源＋訂單，驗證連結有效後才呼叫）、`record_transfer_claim`＋`ClaimOutcome`（Order 列鎖內先去重再判上限）、`ensure_attempt_room`＋`AttemptsFull`（時間窗內進行中嘗試上限）；`_notice_response` 加可選 heading／text。
- `src/crm/views.py`：`pay_page` 僅加：POST 後呼叫節流、轉帳改呼叫 `record_transfer_claim`、信用卡路徑包 `transaction.atomic`（鎖 Order → `start_checkout` → `ensure_attempt_room`）；新增 `from django.db import transaction`、移除已不用的 `TransferClaim` import。
- `tests/db/test_throttle_pay_page.py`（新，18 案例＋JOURNEY-02）、`tests/db/test_throttle_pay_concurrency.py`（新，3 案例）、`tests/db/throttle_helpers.py`（加 `make_pay_project`、`transfer_post`、`card_post`、`template_names`、常數 IP_A／IP_B／BUSY／CLAIM_FULL／ATTEMPT_FULL）。
- `specs/044-…/tasks.md`：T055–T103 勾選（49 項）。未動 models／migrations／forms／pay.html／urls／settings。`_wip` 未動。

## 決策與偏差（揭露）
- **429 頁**：沿用 `jotform_notice.html`（依調度者指示），heading「付款頁送出太頻繁」、text「請求過於頻繁，請稍後再試。」。testplan BE-API-60 寫的是「既有 messages／錯誤區塊」（pay.html），與調度者指示不同，Phase 7 做 BE-60 時需裁示。
- **上限被拒狀態碼 200**（依 api-plan API-PAY-03/04），用 pay.html 既有 error 區塊顯示說明；重複回報回與首次相同的完成頁。
- **嘗試上限「先建立再檢查」**：原本先檢查再建立，結果既有測試 `test_jotform_gateway_numbers::test_after_36_attempts…`（36 筆 created 預期「請聯絡客服」）紅了。為保留既有 36 次上限優先且不改既有測試，改為在同一交易內 `start_checkout` 後計「時間窗內 created（含新建）> 3」就丟 `AttemptsFull` 回滾。語意等同「已有 3 筆即擋」。`start_checkout` 自身也鎖 Order，所以信用卡併發即使拿掉 views 的鎖也仍受保護（見下）。
- 窗口用 `timezone.now()`（DB 時間，與 `PaymentAttempt.created_at` 同源），不用 `throttle.now()`（測試的假時鐘只管快取計數）。
- 併發測試以回應內容判斷頁面：Django 測試 client 的 `response.templates` 是全域訊號，多執行緒會互相污染（第一次跑出現假失敗，已修）。
- `FakeCheckoutExit`（FX-7）未被使用：以 `pay_redirect` 內容／樣板判斷是否導向金流，金流轉送在測試中為既有假金流，無需替身。
- 既有 REFACTOR 步（T057 等）無行為整理需求，直接勾選。

## 紅燈證據（逐組先紅後綠，未事後補測）
- 組 A（BE-20/21/22/31/35）：實作前 5 failed、1 passed（BE-22 特徵案例）。其中 BE-21／31 的首次紅有兩個是我測試 URL 構造錯（404／301），修測試後才是對的原因（429 缺失）；GREEN 後 6 passed。BE-22 破壞證明：PAY_POST 限額改 2 → 5 failed（含 BE-22）。BE-31 為特徵案例，未另做破壞驗證。
- 組 B（BE-23/24/25/26/32）：實作前 3 failed（23 去重、25 上限、26 收斂）、8 passed。BE-24 破壞（去掉 resolved=False 過濾）→ BE-24 紅；BE-32 破壞（鍵不含訂單）→ BE-32 紅；還原後綠。
- 組 C（BE-27/28/29/30）：實作前 3 failed／14 passed（BE-28、30a、30b 首跑即綠為特徵案例）；先做無時間窗的 GREEN → BE-30 兩案例紅（正確原因）→ 加時間窗後 34 passed。破壞：計入所有 status → BE-28 紅；窗口改 5 分鐘 → BE-29、BE-30(c) 紅。
- 組 D（BE-33/34，併發）：**這組測試是在列鎖已存在（組 B/C 的 GREEN 內）後才寫，首跑即綠**，以「暫時移除 `select_for_update`」證明會紅：3 個併發測試全紅，還原後 3 passed（每案例 12 輪）。
- JOURNEY-02：組合驗收，首跑即綠（組成切片皆已綠）。

## 實際測試輸出
- 全套 `pytest tests/unit tests/db --cov=src --cov-fail-under=95 -p no:cacheprovider -q --create-db`：**1332 passed**（第 1 輪 1311 + 21），`Total coverage: 98.20%`，345s。中途一次全套曾有 1 failed（36 次上限既有測試，已依上述決策修正，之後重跑全綠）。
- `ruff check src tests`：All checks passed；`ruff format --check src tests`：228 files already formatted；`manage.py check`：no issues；`makemigrations --check --dry-run`：No changes detected。
- 只用 compose 專案 `b-014`（lint 用 `--no-deps`）；未跑 `docker compose down`；`make codemap` 未跑（本機無 make）。

## 風險與待辦
- fail-open（快取不可用放行，含付款頁 POST 分支）仍屬 Phase 7 BE-API-12；目前快取故障會讓付款頁 POST 500，Phase 7 前不可上線，部署前需 `createcachetable`。
- 轉帳回報 20 次收斂測試每次換來源位址；單一來源 10 次/10 分鐘的上限同時作用。
- 付款頁 429 用新 heading 文案，BE-API-60／61 需對照。


---

# 第 3 輪（US3、US4、Phase 7：T104–T165）

## 變更檔案
- `src/crm/login.py`（新）：`ThrottledLoginForm(LoginForm)`；`src/crm/urls.py` 僅改 `authentication_form=` 與 import；`src/crm/forms.py` 未動。
- `src/crm/throttle.py`：登入鎖定（`login_locked`／`record_login_failure`／`clear_login_failures`／`log_login_locked`，帳號 `strip().lower()` 後與來源成鍵；失敗計數固定窗 900 秒；鎖定到期時刻存值並以 `now()` 比對，鎖定期間不寫任何鍵）；`_fail_open` 裝飾器套在 `hit` 與三個登入函式（快取出錯放行、寫 `throttle backend unavailable` 警告，只記例外類別）。
- `src/config/urls.py`：移除 admin import 與 `admin/` 路由（INSTALLED_APPS 不動、無 migration；使用者裁示 Q1）。
- 測試：`tests/db/test_login_lockout.py`（BE-40～48＋JOURNEY-03）、`tests/db/test_admin_removed.py`（BE-50～53、BE-CMD-02）、`tests/db/test_throttle_cache.py`（BE-CMD-01、BE-12 兩輪、BE-13、BE-14）、`tests/db/test_throttle_pay_page.py`（BE-60）、`tests/db/test_throttle_regression.py`（BE-61）；`tests/db/throttle_helpers.py` 的 `BrokenCache` 補 `__init__(location, params)`（原本無法被 Django 建立）。
- `tests/db/conftest.py` 確認只有一組 autouse（throttle_cache）與 fixed_clock／broken_throttle_cache／database_throttle_cache，無重複；本輪未改。
- `specs/044-…/tasks.md`：T001–T165 全勾。

## 紅燈證據
- BE-40：第 5 次無鎖定訊息（失敗原因對）。BE-41：`TEACHER1`／`Teacher1` 可繞過（空白由表單欄位先 strip，該案例首跑即綠）。BE-42：假時鐘前進後仍鎖（鎖定用真時鐘）。BE-43：成功未清計數。BE-47：窗口不過期。BE-50／51：/admin/ 回 302／200。BE-14：缺登入鎖定日誌。BE-12：`ConnectionError` 造成 500。
- 首跑即綠的特徵案例：BE-44、45、46、48、52、53、BE-CMD-01／02、BE-60、BE-61、JOURNEY-03/04。破壞驗證：BE-44（鍵去掉來源）→ 紅；BE-12／12b／13（`_fail_open` 不捕捉）→ 全紅；BE-61（移除每測試前 clear）→ test_b 紅；其餘（45、46、48、52、53、60）未做破壞驗證。
- **流程偏離（誠實揭露）**：BE-12 的 GREEN 同時把 `_fail_open` 套到登入函式，所以 BE-13 與缺表案例首跑即綠（以破壞驗證補證）；BE-41 的 GREEN 與 BE-42 之間無獨立重構步（REFACTOR 皆無行為整理，直接勾選）。
- 一度因 sed 誤刪 `call_command` import 與 BE-14 測試用錯 `make_pay_token` 簽名而紅，皆為測試自身筆誤，已修。

## 決策與風險
- 429 提示頁沿用 `jotform_notice.html`（依調度者先前指示）；BE-API-60 testplan 寫「既有 messages／錯誤區塊（pay.html）」，兩者不同：本輪 BE-60 只斷言文案與無門檻數字，未斷言「頁面其他區塊與正常 POST 失敗頁相同」。需調度者／QA 裁示。
- `_wip/draft/` 想移除但 `rm` 被安全檢查擋下（相對路徑 glob），**未移除**；該目錄含 `WINDOW=None` 舊草稿，請調度者或使用者執行 `rm -r specs/044-public-endpoint-rate-limit/_wip` 後再合併。
- 部署前仍需 `createcachetable`（fail-open 已讓缺表不致 500，但防護不生效）。`make codemap` 未跑（無 make），由合併者重跑。
