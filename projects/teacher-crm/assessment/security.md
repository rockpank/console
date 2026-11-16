# teacher-crm 資安稽核報告（全面稽核模式）

- 稽核日期：2026-11-13
- 稽核對象：`/Users/Park/Site/teacher-crm`（master，HEAD `eb0a518`）
- 稽核方式：靜態唯讀審查。未連線任何外部服務、未執行測試、未讀取 `.env`。
- **整體結論：不通過（修復後複審）**。有 2 項高風險未修，其中 H-1、H-2 都是「預設值不安全」型問題，修法成本低。

## 0. 工作樹狀態說明

登錄時（profile.md）記錄的 12 項未提交變更，在本次稽核時**已全部提交**，工作樹乾淨。對應提交如下，本報告所有位置都以 HEAD 為準：

| 提交 | 內容 | 與本報告的關係 |
|---|---|---|
| `25cb607` | 新增 `src/config/origins.py`、settings 的 CSRF 來源 | 見 §4、M-2 |
| `606e744` | Jotform 時區與未知提交處理（`client.py`、`registration.py`、`compose.yaml`） | 見 M-1 |
| `eb0a518` | 付款頁顯示轉帳資訊（`pay.html`） | 無發現，`transfer_instructions` 已由樣板自動轉義 |

沒有發現位於「未提交變更」中的問題。

## 1. 審查範圍與方法

**基準文件**：`specs/constitution.md`（#4、#5、#8、#9、#10、交易內不得呼叫外部服務、資源鎖、raw SQL 註解）、`specs/SITEMAP.md` 的角色與可見範圍、`docs/code_map/routes.md`（約 70 個入口）、`docs/code_map/models.md`。

**實際讀過的程式**：`src/config/{settings,origins,urls}.py`、`src/crm/{views,forms,models,access,orders,checkout,paylinks,crypto,importer,attendance,attendance_tags,rescheduling,tagging,followups,reports,context_processors,scheduler}.py`、`gateways/*`、`line/{client,service,notifications}.py`、`jotform/{client,service,sync,registration}.py`、`domain/{permissions,line,payments,roster,jotform_submission,jotform_options,privacy,tags}.py`、management commands、全部會處理外部輸入的樣板（`pay*.html`、`fake_checkout.html`、`jotform_notice.html`、`login.html`、`project_reports.html`）、`compose.yaml`、`Dockerfile`、`.env.example`、`requirements*.txt`、CI workflow。另查 `git log` 與 `git log -S` 確認機密沒有進過版控。

**靜態搜尋**：`|safe`、`mark_safe`、`autoescape`、`raw(`、`.extra(`、`cursor`、`eval/exec/pickle/subprocess/yaml.load`、`select_for_update`、`csrf_exempt`、`logging`。

### 未涵蓋／未執行

- **依賴漏洞掃描：未執行**。本機沒有 `pip-audit`（也沒有 bandit、safety），不可對外查詢漏洞資料庫。只做了人工版本範圍檢查（見 §6）。
- 未做動態測試（沒有啟動應用程式、沒有送請求）；所有「可被利用」的判斷來自讀碼。
- 未審 `tests/`、`specs/` 內容細節，只用來交叉確認行為（例如 `tests/db/test_jotform_return.py` 確認「已有訂單的提交編號可重複導向」是刻意設計）。
- 未審實際部署環境（反向代理、TLS、WAF、實際環境變數）。**這是最大的盲點**：H-1 的嚴重度取決於正式環境到底怎麼啟動，見該項說明。
- 真實金流／LINE／Jotform 的實際行為（例如綠界失敗通知後是否允許同單重試）依官方文件推論，標為「待確認」。

## 2. 發現清單（依嚴重度）

嚴重：無。

### 高

#### H-1　設定預設「失敗時開放」，且 compose 沒有把機密傳進容器

- 位置：`src/config/settings.py:8`（SECRET_KEY 預設 `dev-insecure-secret-key`）、`:9`（`DJANGO_DEBUG` 預設 `"1"`）、`:11`（`FIELD_ENCRYPTION_KEY` 預設空字串，`src/crm/crypto.py:13` 退回 SECRET_KEY）、`:13`（`FAKE_GATEWAY_ENABLED` 預設開）；`compose.yaml:17-27`（app 與 scheduler 的 environment 只傳 `DJANGO_ALLOWED_HOSTS`、`SITE_BASE_URL`、`JOTFORM_*`，**沒有** `DJANGO_SECRET_KEY`、`DJANGO_DEBUG`、`FIELD_ENCRYPTION_KEY`、`FAKE_GATEWAY_ENABLED`、`DJANGO_CSRF_TRUSTED_ORIGINS`，也沒有 `env_file`）；`Dockerfile:16`（`runserver`）。
- 說明：以 repo 內提供的方式（`docker compose up`）啟動，應用程式永遠使用寫死在原始碼裡的 SECRET_KEY、`DEBUG=True`、金鑰加密使用同一把公開字串、假金流開啟。`.env.example` 寫了這些變數，但 compose 不會把它們傳進去（compose 只會用 `.env` 做 `${}` 替換，且只替換上面列出的那幾個）。沒有任何啟動檢查會在「DEBUG 開著且 host 非 localhost」或「用預設金鑰」時拒絕啟動。commit `25cb607` 的說明提到 ngrok／負載平衡器，表示這個服務有被放到公網 HTTPS 後面。
- 利用情境：
  1. 付款連結 token 用 `django.core.signing`（`src/crm/paylinks.py:10`）以 SECRET_KEY 簽章。金鑰公開 → 任何人可為任意整數 `order_id` 偽造 token，逐一走訪 `/pay/<token>/`，取得所有專案、所有訂單的遮罩姓名、課程、金額、付款狀態，並可對任意訂單建立 `TransferClaim`、發起付款嘗試。
  2. `GatewayConfig`、`LineConfig` 的加密欄位（金流 HashKey/HashIV、LINE channel secret、access token）用「SECRET_KEY 的 SHA256」當 Fernet 金鑰。金鑰公開 → 資料庫備份、快照、SQL 注入以外的任何唯讀洩漏，都等於明文（違反憲法 #8「金流金鑰與 LINE 憑證 MUST 加密儲存」的實質意義）。
  3. `DEBUG=True` 對公網：未處理的例外會輸出完整除錯頁（程式碼片段、SQL、請求內容、設定值；Django 會遮蔽名稱含 KEY/SECRET/TOKEN 的設定，但區域變數與請求資料不遮蔽）。
  4. 假金流開啟（見 H-2）。
- 修復建議：
  1. `settings.py` 改成必填：`SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]`；`DEBUG` 預設 `False`（只有明確設為 `1` 才開）；`FIELD_ENCRYPTION_KEY` 必填且不得與 SECRET_KEY 相同（移除 `crypto.py:13` 的退回）；`FAKE_GATEWAY_ENABLED` 預設 `False`。開發與 CI 的值改由 `.env.example`／workflow 明確提供（CI 規格 001 本來就寫明了測試用假值）。
  2. 加一個啟動檢查（`config/settings.py` 或 `AppConfig.ready`）：`DEBUG` 為真且 `ALLOWED_HOSTS` 含非本機名稱時直接拒絕啟動；或在 Django `check` 框架註冊 deploy check，並把 `manage.py check --deploy` 納入 CI。
  3. `compose.yaml` 加 `env_file: .env`（或逐項傳入上述變數），並把「開發用」與「正式用」compose 分開：正式版用 gunicorn（或 uWSGI）、不掛載原始碼目錄、不發佈資料庫埠。
  4. **待確認**：實際對外環境是否另有部署方式、是否已用 `.env` 以外的方式注入環境變數。若已確認正式環境使用了強隨機的 SECRET_KEY 與 FIELD_ENCRYPTION_KEY 且 DEBUG 關閉，H-1 可降為「中」（仍需改預設值）；若曾以預設值運作過，**必須輪替 SECRET_KEY 與重新輸入所有金流／LINE 金鑰**（並視為已外洩）。

#### H-2　假金流可讓持有付款連結的人「免費付款」（付款繞過）

- 位置：`src/crm/views.py:954-1012`（`_fake_attempt_or_error`、`fake_checkout`、`fake_complete`，皆 `@csrf_exempt`、免登入）；`src/crm/forms.py:313-357`（`GatewaySettingsForm` 無論 `FAKE_GATEWAY_ENABLED` 為何都開放選「假金流」，且假金流不要求 HashKey）；`src/crm/models.py:297`（`provider` 預設 `fake`）；`src/crm/checkout.py:74-75`（`simulated` 檢查只擋綠界的 `SimulatePaid`，假金流永遠 `simulated=False`）；`src/config/settings.py:13`（預設開）。
- 說明：`fake_complete` 的流程是「驗證表單簽章 → **由伺服器自己用 HashKey 產生一份簽好章的付款成功通知** → 呼叫 `handle_gateway_callback`」。表單簽章（`trade_no`、`amount`）本來就由伺服器在 `build_checkout` 時交給瀏覽器，所以任何走完付款頁的人都拿得到有效簽章，再自己 POST `result=paid` 到 `/fake-gateway/complete/`，訂單即記為「金流」已收款，標籤、LINE 通知、點名流程全部照「已付款」走。
- 成立條件：專案的金流設定 `provider=fake` 且 `enabled=True`，並且 `FAKE_GATEWAY_ENABLED` 為真（預設為真，且 compose 不會關掉，見 H-1）。選項在 admin 的付款設定畫面第一個，容易誤選。
- 次要問題：選假金流時 `hash_key` 可為空字串，HMAC 金鑰為空；若此時用 Jotform 建的訂單（`trade_no` 為「提交編號＋序號字元」，可預測，`jotform/registration` 與 `domain/jotform_submission.py:attempt_trade_no`），任何人可直接偽造 `/gateway/notify/<project_id>/` 的成功通知（`checkout.py:handle_gateway_callback` 不看 `FAKE_GATEWAY_ENABLED`）。
- 利用情境：學員（或收到付款連結的任何人）在「誤設為假金流」的正式專案按「信用卡」→ 在模擬頁按「模擬付款成功」→ 不付錢就變成已付款，並佔位場次。
- 修復建議：
  1. 表單層：`FAKE_GATEWAY_ENABLED` 為假時，`GatewaySettingsForm.provider` 不提供 `fake`，且 `gateway_for` / `get_gateway` 在設定為假時拒絕建立 `FakeGateway`（連 `gateway_notify` 也一併擋）。
  2. 假金流一律要求非空 HashKey（至少 32 字元隨機）。
  3. `settings.py` 預設關閉（見 H-1），只在開發 `.env` 與測試設定開啟。
  4. 在 `handle_gateway_callback` 對 `provider == fake` 且非沙盒的設定直接拒絕（與綠界 `simulated` 一樣的邏輯）。
  5. 加測試：`FAKE_GATEWAY_ENABLED=False` 時，`/gateway/notify/` 對 fake 設定回 400。

### 中

#### M-1　`/jotform/return/<project_id>/` 免登入、無節流，可耗盡共用 Jotform API 額度並製造待處理垃圾；提交編號等同持有付款連結的憑證

- 位置：`src/crm/views.py:1491-1507`；`src/crm/jotform/registration.py:209-297`（`process_submission`，每次最多呼叫 Jotform 3 次並 `sleep` 1 秒，見 `REDIRECT_ATTEMPTS`、`_sleep`）；`src/crm/jotform/client.py:157-170`（`_explain_rejection` 在失敗時還會多打一次 `/user`）；`registration.py:181-206`（`_retry_later` 會以攻擊者提供的數字建立 `JotformSubmission` 佔位列）。
- 說明：這個端點只要求「1 到 19 位純數字的提交編號」（`domain/jotform_submission.py:is_order_number`，這道檢查有效擋住了路徑注入，是優點），不需要 token 也沒有速率限制，每次請求會用平台共用的 `JOTFORM_API_KEY` 呼叫 Jotform（查無此提交時為 2 次）。`jotform_webhook` 的註解（`models.py:625`）明白寫了「避免任意人消耗共用的 API 額度」，但導向入口沒有同樣保護。
- 利用情境：
  1. 對任意 project_id 與隨機數字持續請求 → 耗盡 Jotform 帳號額度（Jotform 低階方案日額度不高；實際額度**待確認**）→ 所有專案的場次同步、報名建單都進入「暫時失敗」，每筆提交落到補處理佇列，達 `JOTFORM_RETRY_LIMIT` 後變成「待人工」，行政人員的待處理清單被攻擊者灌滿（失敗類型會建立 `JotformSubmission` 列，見 `_retry_later`）。
  2. 每個請求在 runserver／同步 worker 上佔用約 1–3 秒（含 `sleep`），少量連線即可讓網站無法服務。
  3. 提交編號是 bearer 憑證：訂單一旦建立，`process_submission` 對已知提交直接回傳訂單，**不再檢查導向時效**（`registration.py:220-222`；測試 `test_entering_again_goes_to_the_same_order…` 證實是設計意圖）。知道（或猜到）編號者可取得付款頁。Jotform 提交編號是 18–19 位、帶時間成分的數字，是否可列舉**待確認**。付款頁內容有遮罩姓名、課程、金額、狀態，並可送出轉帳回報，影響有限，但屬於不必要的暴露。
- 修復建議：
  1. 對 `jotform_return` 與 `jotform_webhook` 加速率限制（以 IP＋專案，例如每分鐘 10 次；可用 DB 或快取計數，因為沒有 Redis，可先用 `django.core.cache` 的 LocMem／DB cache）。
  2. 導向入口改成「由 Jotform 在網址帶一個只有 webhook 與表單擁有者知道的簽章」，或要求提交編號必須已存在於本系統（由 webhook 先建立佔位列）才會呼叫 Jotform；不認得的編號直接顯示「找不到」，不呼叫外部。
  3. 把 `sleep` 重試改成「回傳『處理中』頁面，交給補處理排程」，不要在請求執行緒內等待。
  4. 已有訂單的提交，導向時仍檢查時效，或改成要求姓名＋電話後 4 碼才給付款頁。

#### M-2　Cookie、HTTPS、HSTS 與代理設定缺漏

- 位置：`src/config/settings.py`（整份沒有 `SESSION_COOKIE_SECURE`、`CSRF_COOKIE_SECURE`、`SECURE_SSL_REDIRECT`、`SECURE_HSTS_SECONDS`、`SECURE_PROXY_SSL_HEADER`、`SESSION_COOKIE_AGE`／閒置逾時、`SECURE_CONTENT_TYPE_NOSNIFF` 以外的任何強化）。
- 說明：在 HTTPS 代理後面（`25cb607` 的情境）Django 看到的是 http，`request.is_secure()` 為假：工作階段與 CSRF cookie 不帶 `Secure`，可被降級／混合內容攔截；`request.build_absolute_uri` 產出的付款連結與給金流的 `notify_url`／`return_url`（`views.py:705`、`:935-936`）會是 `http://`，與排程使用 `SITE_BASE_URL` 組出的連結（`line/notifications.py:_order_pay_link`）不一致。`CSRF_TRUSTED_ORIGINS` 的處理（`origins.py`）本身正確，只信任設定的對外網址，沒有萬用字元。
- 修復建議：正式環境設定 `SESSION_COOKIE_SECURE=True`、`CSRF_COOKIE_SECURE=True`、`SECURE_HSTS_SECONDS`（先 1 天再拉長）、`SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO","https")`（僅在確定前面是會覆寫該標頭的受信代理時）、`SESSION_COOKIE_AGE` 縮短（例如 12 小時）、`SECURE_REFERRER_POLICY="same-origin"`；全部以環境變數控制，並把 `manage.py check --deploy` 放進 CI。付款連結統一用 `SITE_BASE_URL` 組出，不用 Host 標頭。

#### M-3　登入沒有暴力破解防護，且沒有停用帳號的途徑；`/admin/` 仍然公開

- 位置：`src/crm/urls.py:13-17`（標準 `LoginView`，無節流／鎖定）；`src/crm/forms.py:88-133`（`MemberForm` 只能建立成員）、`views.py:220-231`（`manage_members` 無停用／刪除／重設密碼）；`src/config/urls.py:5` 與 `src/crm/admin.py`（空檔）。
- 說明：帳號與密碼可無限次嘗試；`CommonPasswordValidator` 以外沒有其他防線，且初始密碼由 admin 設定、沒有強制首次變更。離職行政人員、卸任講師無法在應用程式內停用（`is_active` 沒有任何畫面可改），只能改資料庫。`/admin/` 路由仍啟用（`create_admin` 建立的是一般使用者，不是 superuser，所以平常打不進去，但一旦有人用 `createsuperuser` 建帳號就會暴露一個無節流、無第二因素的管理入口）。
- 利用情境：針對 admin 帳號的密碼猜測；離職者保有存取專案資料（含學員姓名、電話、住址、付款）的權限。
- 修復建議：登入節流（以帳號＋IP 計數，連續失敗 5 次鎖 15 分鐘，可用 DB 表實作，不引入新服務）；`manage_members` 增加「停用」操作（`user.is_active=False`，並讓 `visible_to` 與登入同時失效）與重設密碼；若不使用 `/admin/` 就從 `config/urls.py` 移除（或限制來源 IP）；admin 密碼最小長度提高到 12。

#### M-4　金流「失敗」通知會把付款嘗試永久鎖成失敗，之後同一筆的成功通知會被當成重複而丟棄（待確認，涉及金額）

- 位置：`src/crm/checkout.py:94-104`（`attempt.status != CREATED` 即回傳 `DUPLICATE`；失敗通知時設 `FAILED`）。
- 說明：冪等設計本身正確（`select_for_update`、狀態機、驗簽、核對 `trade_no`、金額、商店代號，重複通知只處理一次，符合憲法 #9）。問題在「失敗是終態」：綠界／藍新的信用卡頁允許持卡人在同一個商店訂單編號下失敗後重試。若失敗通知先到、之後同單號的成功通知才到，成功通知會回 `1|OK`／`OK`（金流停止重送），但本系統不入帳——學員被扣款、訂單仍是未付款。
- 修復建議：失敗通知只記錄 `last_failure`，保持 `CREATED`（或允許 `FAILED → PAID` 的轉換，且仍然核對金額）；`UNAPPLIED` 同樣保留人工處理入口。補測試：先失敗後成功。向綠界／藍新確認同單號重試行為。

#### M-5　收款、退款、刪除缺少操作者紀錄；刪除學員會連帶刪除收款帳本

- 位置：`src/crm/models.py:231-250`（`Payment` 無 `created_by`）、`:199-210`（`Order.student` `on_delete=CASCADE`）、`:237`（`Payment.order` CASCADE）；`src/crm/views.py:745-767`（確認入帳，行政專員即可）、`:466-481`（`project_student_delete`，警語只說會刪報名）。
- 說明：任何有 `EDIT_DATA` 的人（含行政專員）可把訂單記為已收款（`mark_order_paid` / `record_payment`），系統不記錄是誰、也沒有第二人確認，之後無法稽核「誰把這張單標成已付」。管理者刪除學員時，所有訂單、收款、退款、付款嘗試、轉帳回報一起被刪除，財務紀錄消失，畫面警語沒有提到。憲法 #6 要求付款狀態以本系統為單一事實來源，帳本被刪除會破壞這點。
- 修復建議：`Payment` 加 `created_by`（FK，SET_NULL）與 `source`，並在 `record_payment`/`refund_order`/`cancel_order` 傳入 `request.user`；有「已收款」訂單的學員不得刪除（改為封存旗標），或把 `Order.student`／`Payment.order` 改成 `PROTECT`；刪除確認畫面列出將被刪除的訂單與收款筆數。

#### M-6　憲法「有限資源以資料庫鎖保護」：場次人數上限只有改期有鎖，Jotform 報名、CSV 匯入、現場報名都不檢查也不鎖

- 位置：`src/crm/rescheduling.py:21`（有鎖，且檢查上限）；`src/crm/jotform/registration.py:84-120`（`_book`）、`src/crm/importer.py:23-41`、`src/crm/attendance.py:116`（`register_walk_in`，皆不檢查 `capacity`，也不鎖 `Session`）。
- 說明：場次上限目前只靠 Jotform 選項「依已付款人數下架額滿場次」（`domain/jotform_options.py:110`）與看板的「超過上限」異常提示。報名本身沒有上限；表單選項更新有延遲（排程 60 秒），在這段時間內多人同時送出同一額滿場次，全部會建立報名與訂單並進入付款，付款後即超收。憲法流程關卡明文要求以資料庫鎖保護。
- 修復建議：`_book` 內先 `Session.objects.select_for_update()` 鎖住場次，再用「已付款＋待付款有效報名」計算是否額滿；額滿則轉為待人工（新增原因 `session_full`）。現場報名與匯入若確定不受限（`check_in_early` 已明寫「不受人數上限限制」），請在憲法或規格中記下例外。

#### M-7　LINE 綁定只憑「姓名＋電話」，且回覆可被用來探測學員是否存在

- 位置：`src/crm/line/service.py:93-120`（`_bind_from_text`）、`:10-17`（不同回覆訊息）。
- 說明：任何加了官方帳號的人，只要知道某學員的姓名與電話，就能先綁定成功；真正的學員之後只會收到「這位學員已綁定其他 LINE 帳號」。綁定成功者會收到該學員的上課通知與付款提醒（含簽章付款連結，`notifications.py:_pay_link`）。此外，「查無符合」、「已綁定其他 LINE」、「已綁定完成」三種回覆可判斷某姓名＋電話是否存在於該專案（學員名單外洩的探測管道）。
- 修復建議：綁定改成需要第二因子（例如報名時產生的一次性綁定碼放在付款頁或報名完成頁）；至少對同一 `line_user_id` 限制嘗試次數（`BindingIssue` 已有紀錄可計數），並統一失敗回覆文字。這是產品決策，建議由 PM 評估。

#### M-8　憲法 #10：重送失敗訊息不會在發送當下重新檢查條件

- 位置：`src/crm/line/notifications.py:232-241`（`retry_message` 直接以舊的 `message.text` 重送）、`:106-123`（`_send` 對已存在且為 `PENDING` 的訊息也直接投遞）；對照 `_run_follow_ups` 與 `_plan` 在建立訊息當下有檢查，這部分合規。
- 說明：先前發送失敗的「追售」或「完款提醒」訊息，行政人員稍後按「重送」時，即使學員已報名進階課程（追售應已停止）或已付清（提醒不再需要），仍會用舊文字（含舊付款連結）發出。這是「不得只依排程當時的判斷」的直接違反。
- 修復建議：`_deliver` 開頭依 `message.kind` 重新檢查：追售類須確認對應 `FollowUp` 仍為進行中；付款提醒須確認訂單仍為未付清；課前通知須確認學員仍報名該場次且場次未結束；不符就標記 `SKIPPED`。補「重送時學員已完款」的測試。

#### M-9　依賴：未執行掃描；`cryptography~=43.0` 把版本鎖在已知有 CVE 的主線

- 位置：`requirements.txt:3`。
- 說明：`~=43.0` 等於 `>=43.0,<44`，最高只會安裝 43.0.x。據我所知，該主線打包的 OpenSSL 受 CVE-2024-12797 影響（修於 44.0.1）；此 CVE 影響 TLS 用戶端的 RFC 7250 原始公鑰，與本系統使用方式（Fernet、AES-CBC）關聯很低，但仍屬於「無法自動取得安全更新」的版本鎖定。`pip-audit` 未執行，無法確認其他已知漏洞，**請在可連網環境執行並補記結果**。另外沒有鎖定檔（lockfile／雜湊），Dockerfile 在正式映像也安裝了 dev 依賴（`requirements-dev.txt`：pytest、ruff…）。
- 修復建議：把 `cryptography` 放寬為 `~=44.0` 以上（或目前最新主線）並跑 `make test`；CI 加 `pip-audit -r requirements.txt` 步驟；Dockerfile 改為多階段，正式映像只裝 `requirements.txt`，用 `pip-compile --generate-hashes` 產生鎖定檔；`pyproject.toml` 的 ruff 規則加入 `S`（bandit 類規則）。

### 低

| 編號 | 位置 | 說明與建議 |
|---|---|---|
| L-1 | `src/crm/domain/line.py:27-32`、`views.py:1165-1167`、`forms.py:438-443` | LINE webhook 驗簽在 channel secret 為空字串時仍會用空金鑰做 HMAC，任何人都能簽。「假 LINE」模式可在沒有 secret 的情況下啟用（表單只在 LINE 模式要求 secret），此時可偽造綁定事件（寫入攻擊者指定的 `line_user_id`）。建議 `verify_signature` 對空 secret 直接回 `False`，並讓 `line_webhook` 對非 LINE 模式一律不處理外部事件。 |
| L-2 | `views.py:917-919`（`TransferClaim.objects.create`）、`checkout.py:51-55`（`start_checkout`） | 付款頁（只需連結 token）可無限建立轉帳回報與付款嘗試，沒有節流與去重；行政人員的付款畫面會被灌滿。建議同一訂單未處理的回報最多 N 筆（同金額同末五碼去重）、同一訂單進行中的嘗試最多 N 筆。 |
| L-3 | `views.py:857-858`、`:1164`（先 404 再驗簽） | 公開端點對外回傳內部錯誤文字（「這個專案還沒有付款設定」、「查無付款單號」等），並以 404／400 區分專案是否存在、是否設定 LINE。資訊量小，建議統一回傳 400 無內文，錯誤原因只寫應用程式日誌（不含金鑰與完整 payload）。 |
| L-4 | `views.py:341`（`form.cleaned_data["file"].read()`）、`importer.py` | 名單匯入沒有檔案大小與列數上限，整個檔案讀入記憶體（僅限行政專員以上，影響為自損式 DoS）。建議限制 2 MB／5000 列；匯入的 `name`、`address` 超過欄位長度會造成資料庫例外而非友善錯誤，請在解析階段檢查。 |
| L-5 | `src/crm/crypto.py` | 沒有金鑰輪替機制（可用 `MultiFernet`）；金鑰不符時 `DecryptionError` 沒有被接住，會讓 `pay_page`（`card_available` → `gateway_for`）與 `line_webhook` 直接 500。建議接住並顯示「付款設定需重新輸入」。 |
| L-6 | `Dockerfile` | 以 root 執行、`runserver`、映像含測試與 lint 依賴、`compose.yaml` 掛載整個原始碼目錄並把 8000 埠開在所有介面。屬於 H-1 的部署面補充。 |
| L-7 | `models.py:20-31`（只有 `visible_to` 看 `is_active`） | 專案「停用」後，內部畫面對非 admin 隱藏，但公開入口（付款頁、`gateway_notify`、`line_webhook`、`jotform_return`／webhook、排程同步與發送）仍照常運作。若「停用」的語意是停止營運，請在這些入口與排程查詢加上 `project.is_active`。 |
| L-8 | 全站 | 沒有 CSP；登入後的頁面（含個資）沒有 `Cache-Control: no-store`；`jotform_webhook` 的密鑰在網址路徑中，會進入反向代理與 runserver 的存取日誌。建議加 `Content-Security-Policy`（目前無外部腳本，只有兩段內嵌 script，可用 nonce）、對個資頁加 `never_cache`，並把 webhook 密鑰改放標頭（若 Jotform 不支援，至少設定日誌遮罩）。 |

### 資訊

- 憲法 raw SQL 規定：唯一的 raw SQL 是 `src/crm/scheduler.py:27` 的 PostgreSQL 諮詢鎖，模組開頭的文件字串已說明原因，可視為合規；建議在該行加一行註解以符合「在程式註解說明」的字面要求。
- 付款連結（簽章 token）有效 30 天、無法單獨撤銷；訂單取消／退款後頁面只顯示狀態，不會允許付款，風險可接受。
- 本系統沒有 CORS 設定（未安裝 corsheaders），預設即同源，無發現。

## 3. 憲法安全條文逐條驗證

| 條文 | 結果 | 證據與落差 |
|---|---|---|
| #4 專案隔離 | **符合（程式面）** | 所有業務 model 都有 `project` FK（`models.md`：Student、Session、Registration、Product、Order、Payment、StudentTag、TagEvent、PaymentAttempt、TransferClaim、Reschedule、LineAccount、BindingIssue、MessageTemplate、OutboundMessage、Attendance、FollowUp、JotformSubmission；`JotformForm` 一對一專案、`JotformSessionOption` 經 form）。所有 view 先經 `_project_or_404` → `Project.objects.visible_to(user)`，再以 `for_project(project)` 取子資料；逐一核對了所有含 `*_id` 路徑參數的 view（session、student、registration、order、product、follow_up、submission、issue、message、tag），皆有專案範圍過濾，未發現 IDOR。建立訂單、改期、點名、匯入都有「同專案」檢查（`orders.py:create_order`、`rescheduling.py`、`attendance.py:_check_project`）。有跨專案測試（`tests/db/test_project_scope.py` 等）。**弱點**：資料庫層沒有強制「子資料與父資料同一專案」的約束（例如 `Registration.project` 與 `Session.project`），目前完全仰賴程式紀律，建議之後加複合外鍵或檢查約束。 |
| #5 伺服器端權限 | **符合** | 每個專案 view 都在伺服器端檢查（`_require(request, project, Action.X)` 或 `can_perform_on`）；平台管理走 `platform_admin_required`；無 Membership 的使用者 `visible_to` 回空、`can_perform_on` 回假（預設拒絕）。權限矩陣見 §5。管理者授權他人時，只能授權「自己看得到的專案」且只能授權行政專員（`can_grant_project_access`），沒有提權路徑。注意講師可唯讀看到學員完整資料、付款清單與轉帳末五碼，這是 SITEMAP 明定的設計。 |
| #8 金額與機密 | **部分符合** | 金額：模型皆 `PositiveIntegerField`，無 float；付款金額一律由伺服器依訂單算出（`payment_options`），不信任瀏覽器數字。機密：Fernet 加密儲存、表單 `PasswordInput(render_value=False)`、畫面只顯示「已設定」；`.env` 未被追蹤、歷史中從未出現（`git log --all --diff-filter=A` 只有 `.env.example`）；日誌與錯誤訊息未發現印出金鑰（Jotform／LINE 金鑰只放在 HTTP 標頭）。**落差**：加密金鑰退回 SECRET_KEY 且預設為公開字串（H-1），等於實質上未加密。 |
| #9 驗簽與冪等 | **大致符合** | 綠界 CheckMacValue（SHA256、`hmac.compare_digest`、核對商店代號、金額）、藍新 TradeSha＋AES（同上）、LINE `X-Line-Signature`（`compare_digest`）、Jotform 網址密鑰（`compare_digest`）。金流冪等：`PaymentAttempt` 鎖列＋狀態機＋`UNIQUE trade_no`＋訂單鎖，重複通知回 ack 但不重複入帳。**落差**：M-4（失敗後成功被丟棄）、L-1（空 secret）、H-2（假金流）。LINE 事件沒有以 `webhookEventId` 去重，但各事件處理本身可重複執行（綁定、封鎖、`BindingIssue` 去重），結果等價，視為可接受。 |
| #10 發送前再檢查 | **部分符合** | 排程路徑在發送當下重新計算收件人與條件（`_plan`、`_run_follow_ups`，`_deliver` 檢查綁定與封鎖）。**落差**：M-8（手動重送與 `PENDING` 殘留訊息）。 |
| 交易內不得呼叫外部服務 | **符合** | `checkout.py` 的 `atomic` 區塊內無外部呼叫；Jotform 查詢在交易外、查回後才進交易（`registration.py` 開頭註解與實作一致）；LINE 推播在交易外；`sync_project_best_effort` 在 view 儲存後呼叫並吞掉例外。 |
| 資源鎖 | **部分符合** | 訂單、付款嘗試、Jotform 提交、改期目標場次都有 `select_for_update`；場次人數上限只有改期受保護（M-6）。 |
| ORM／raw SQL | **符合** | 無 `raw`、`extra`、字串組 SQL；唯一 `cursor.execute` 為參數化的諮詢鎖。 |

## 4. 外部整合與 Django 設定摘要

| 項目 | 結果 |
|---|---|
| ECPay／NewebPay 回報 | 驗簽、商店代號、單號、金額、冪等皆有（M-4 為失敗重試落差）。沙盒「模擬付款」在正式模式被拒（`checkout.py:74`）。 |
| 金額竄改 | 學員端只送選項代碼（`full`/`deposit`）與方式，金額由伺服器決定；回報金額與嘗試金額不符即拒絕。 |
| 重放 | 已處理的通知重送無副作用；LINE `replyToken` 一次性；導向入口見 M-1。 |
| SSRF | 對外請求目標都由常數決定（`api.line.me`、`JOTFORM_API_BASE`、金流網址常數）；使用者輸入只進路徑片段且已驗證：Jotform 表單網址只取純數字編號並限制網域（`parse_form_id`），提交編號限純數字 ≤19 位。無 SSRF。 |
| Jotform 輸入處理 | 通知內容一律不採信，只取編號再回頭查詢；專案歸屬以表單編號核對（`WRONG_FORM` 當作找不到）；問題見 M-1。 |
| XSS | 全部樣板使用自動轉義，沒有 `|safe`、`mark_safe`、`autoescape off`；內嵌 script 只讀取頁面元素文字。無發現。 |
| CSRF | `CsrfViewMiddleware` 啟用；`csrf_exempt` 只用在金流通知、LINE／Jotform webhook、假金流與 `jotform_return`（皆為外部呼叫入口，各有其驗證方式，見 H-2、M-1）。`origins.py` 只信任 `SITE_BASE_URL` 的來源與環境變數補充項，無萬用字元，無發現。 |
| 開放式轉址 | `fake_complete` 的 `return_url` 以 `url_has_allowed_host_and_scheme` 驗證；登入 `next` 使用 Django 內建驗證。無發現。 |
| ALLOWED_HOSTS | 預設 `localhost,127.0.0.1`（安全預設），正式需設定；`build_absolute_uri` 依賴它防 Host 標頭污染。 |
| 檔案匯入 | 只接受 CSV 文字解析，不寫入磁碟、不執行；無 CSV 公式注入風險（系統沒有匯出 CSV）。上限問題見 L-4。 |
| 競態 | 訂單、付款、通知冪等設計良好；缺口為 M-6。`create_order` 先查再建，併發時依賴唯一約束（會變成 500 而非資料錯誤）。 |
| `.env` | 未被 git 追蹤（`git ls-files` 只有 `.env.example`），`.gitignore` 已列；`.env.example` 的 `change-me` 值屬佔位符。內容未讀取。 |

## 5. 路由授權矩陣（逐一核對 `routes.md`）

角色：A＝admin、M＝行政管理者、S＝行政專員、I＝講師。「可見專案」＝`visible_to`（A 全部；M/S 被授權且啟用的專案；I 所屬團隊專案且啟用）。

| 入口 | 驗證／授權 | 結論 |
|---|---|---|
| `/accounts/login/`、`/accounts/logout/` | 公開；登出為 POST | 無節流（M-3） |
| `/`、`/projects/`、`/projects/<id>/`、sessions、session detail、students、attendance（檢視）、follow-ups、reschedule（檢視）、products（檢視）、front-course（檢視）、payments（檢視） | 登入＋可見專案 | 講師可唯讀（符合 SITEMAP）；付款連結只給有 `EDIT_DATA` 者（`views.py:703`） |
| import、student edit、registration remove、tag add/remove、order create/confirm、reschedule confirm、line issue bind、notifications（檢視／retry）、reports、attendance mark/early/walk-in/close、follow-up stop/remind、jotform settings／sync／submissions／resolve／dismiss | 登入＋可見專案＋`EDIT_DATA`（A/M/S） | 符合；講師被拒 |
| session create/edit | `CHANGE_SESSION_CAPACITY`（A/M） | 符合 |
| session／student delete | `DELETE_DATA`（A/M） | 符合；見 M-5 |
| product create/edit | `MANAGE_PRICING`（A/M） | 符合 |
| order refund／cancel | `MANAGE_REFUNDS`（A/M） | 符合 |
| message templates | `MANAGE_MESSAGES`（A/M） | 符合 |
| payment-settings、line-settings、jotform connect／question／fields／remove | `CONFIGURE_INTEGRATIONS`（僅 A） | 符合 |
| `/projects/<id>/access/` | `can_manage_access`（A/M） | 符合；無提權 |
| `/manage/*`（teams、projects、members、toggle、edit） | `platform_admin_required`（僅 A）；修改類為 POST | 符合 |
| `/gateway/notify/<id>/` | 公開；驗簽＋單號＋金額 | 見 M-4、H-2 |
| `/pay/<token>/`、`/pay/<token>/return/` | 公開；簽章 token（30 天） | 受 H-1（金鑰）影響 |
| `/fake-gateway/checkout/`、`/complete/` | 公開；表單簽章＋旗標 | **H-2** |
| `/line/webhook/<id>/` | 公開；HMAC 驗簽 | L-1 |
| `/jotform/return/<id>/` | 公開；無驗證 | **M-1** |
| `/jotform/webhook/<id>/<token>/` | 公開；網址密鑰（常數時間比對） | L-8 |
| `/admin/` | Django 內建 | M-3 |

## 6. 依賴稽核結果

- `pip-audit`：**未執行**（工具不存在，且不得對外查詢）。
- 人工檢查：`Django~=5.2`（5.2 LTS 主線，可取得安全修補，OK）、`psycopg[binary]~=3.2`、`cryptography~=43.0`（見 M-9）、dev：`pytest~=8.3`、`pytest-django~=4.9`、`pytest-cov~=6.0`、`ruff~=0.8`、`pyyaml~=6.0`。專案沒有前端套件與外部 CDN 腳本。
- 建議在 CI 增加定期（外部服務 workflow 之外另開）`pip-audit` 工作。

## 7. 優先修復順序（給 PM 轉 backlog）

1. **H-1**（預設值與 compose 傳參）＋ **H-2**（假金流）：一起做，半天內可完成；做完要輪替金鑰並重新輸入各專案金流／LINE 憑證。
2. **M-2**（cookie／HTTPS／HSTS）、**M-3**（登入節流與停用帳號）：上線前必做。
3. **M-1**（jotform_return 節流與外部呼叫）、**M-4**（金流失敗後成功）：涉及金額與可用性。
4. **M-5、M-6、M-8**：憲法落差，需要規格決策後走完整路線（M-5 會動 model）。
5. **M-7**（LINE 綁定）需先由 PM 決策綁定方式；**M-9** 與低風險項目併入一般維護。

## 8. 結論

**不通過（修復後複審）。** 存在 2 項高風險（H-1 預設不安全設定且部署檔不傳入機密；H-2 假金流付款繞過）、9 項中風險。應用程式本身的授權、專案隔離、驗簽與冪等、XSS／SQL 注入防護做得紮實，主要風險集中在「部署預設值」「公開入口的濫用防護」與「少數憲法條文的落差」。H-1、H-2 修復並經複審後，若 M-1 到 M-4 也處理完，可改為「通過（附低風險追蹤）」。

---
稽核者：資安管控工程師（security-reviewer）。本報告未包含任何真實機密值。
