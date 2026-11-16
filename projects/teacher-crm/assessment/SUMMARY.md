# teacher-crm 現況評估摘要

- 彙整日期：2026-11-13　彙整者：project-manager
- 彙整依據：同目錄四份報告 `architecture.md`、`quality.md`、`security.md`、`ux.md`，以及 `../profile.md`。
- 原則：只引用報告內容，未自行補充未經查證的發現。引用格式「報告 §章節／編號」，例如 security.md H-1。
- 版本基線：profile 登錄時記載的 12 項未提交變更（004 Jotform 報名付款收尾），評估期間已由使用者提交（`25cb607`、`606e744`、`eb0a518`），工作樹乾淨，HEAD `eb0a518`（quality.md 頭部、security.md §0）。本摘要以此為準。
- 存檔說明：專案管理員 agent 無法直接寫入本檔，內容由調度者依其回報全文原樣存檔（經使用者同意）。

## 1. 整體健康度：有風險

**理由**：程式本身的品質基線很穩：本機實測 lint、903 項測試、`check`、`makemigrations --check`、codemap 全過，行覆蓋率 97%，無失敗、無跳過（quality.md §1、§6）。授權、專案隔離、金流驗簽與冪等、XSS／SQL 注入防護也被架構與資安兩份報告評為紮實（architecture.md §9、security.md §8）。風險集中在三處：
1. 資安結論為「不通過（修復後複審）」，有 2 項高風險未修（H-1 設定預設不安全且 compose 不傳入機密、H-2 假金流可繞過付款），另有 9 項中風險（security.md 頭部、§8）。
2. 架構報告列出 4 項高嚴重度落差：每日通知與追售未排程、名額無鎖、重送通知不重驗發送條件、刪學員連帶硬刪財務紀錄（architecture.md F-1 至 F-4）。
3. UX 報告有一項確定性缺陷：學員編輯頁的標籤區被誤塞進 `<title>`，可能使標籤與改期入口在畫面上消失（ux.md UX-01，靜態閱讀結論，待實機確認）。

未列為「受阻」的原因：沒有任何測試失敗或品質關卡不過；風險可以靠修補處理，且 H-1 的實際嚴重度取決於正式環境如何啟動（見第 5 節 U1）。若 U1 的答案是「曾以預設值對公網運作」，security.md H-1 要求輪替 SECRET_KEY 並重新輸入全部金流與 LINE 憑證，視為已外洩，則優先序應整體上調。

資安規則提醒：在 H-1、H-2 修復並複審通過前，與其相關的任何 backlog 項目不得標為完成。

## 2. 評估基線（quality.md §1，HEAD `eb0a518`，工作樹乾淨）

| 項目 | 結果 |
|---|---|
| `make test-fast` | 通過：311 passed，2.9 秒（不需 DB） |
| `make test` | 通過：903 passed、0 failed、0 skipped、0 xfail，76 秒（單元 311 + 資料庫 592） |
| `make lint` | 通過（ruff check 全過；188 個檔案格式正確） |
| `make manage cmd="check"` | 通過，0 issues |
| `makemigrations --check --dry-run` | 通過，No changes detected |
| `make coverage` | 總覆蓋率 97%（4178 敘述、107 未覆蓋）；CI 門檻 95%。`make coverage` 本身不帶門檻，只有 CI 會擋 |
| `make codemap-check` | 通過（263 檔，無 STALE） |
| `validate_artifacts.py all`（001、003、004） | 通過，附警示：003、004 的 models 使用 CASCADE 需確認有說明理由；004 integration-plan 有 3 個 `[NEEDS CLARIFICATION]` 未關閉 |
| `make test-integration` | **未執行**（需使用者授權，會連真實外部服務） |
| 分支覆蓋率 | **未啟用**（`pyproject.toml` 無 `branch = true`），97% 僅為行覆蓋，實際分支覆蓋未知 |
| 依賴漏洞掃描 `pip-audit` | **未執行**（工具不存在、不得對外查詢；security.md §6） |
| 既有失敗 | 無 |

測試規模：792 個測試函式，pytest 展開 903 項；另有 `tests/integration` 2 項（僅綠界測試站，未執行）。

## 3. 各面向最重要發現

### 3.1 架構（architecture.md）

1. **F-1（高）每日 LINE 通知、結束場次、追售沒有登錄排程**：`registered_jobs()` 只有 2 個 Jotform job，專案內找不到 `send_line_notifications`、`process_finished_sessions` 的排程或 cron 說明；通知以精確日數判斷，漏跑一天該階段永遠補不回（architecture.md F-1、A-1、D-1）。實際部署有無主機 cron 本次無法確認。
2. **F-2（高）場次名額：憲法要求 DB 鎖，現況只有改期有鎖**：Jotform 建單、CSV 匯入、現場報名、提前報到、人工 resolve 都不鎖也不檢查上限；「額滿」有兩套口徑（報名數 vs 已付款數）；付款入帳這個消耗名額的動作無鎖（architecture.md F-2、A-4、D-2）。
3. **F-3（高）憲法 MUST 10 在重送與待發訊息路徑未落實**：`_deliver`／`retry_message` 直接重送舊文字，學員已付款或已報進階仍會收到付款提醒或追售（architecture.md F-3、A-2、D-3）。
4. **F-4（高）刪除學員會硬刪訂單與收款紀錄**：`Order.student`、`Payment.order` 為 CASCADE，金流端與銀行帳上仍有紀錄；刪除人也無稽核（architecture.md F-4、A-3、D-4）。
5. **F-8（中）可維運性空白**：不安全預設值、`runserver`、無 LOGGING／SECURE_*、無登入失敗限制、財務操作無操作者稽核（architecture.md F-8、A-6、A-8、D-5、D-6）。另 D-14：`PaymentAttempt.UNAPPLIED`（已扣款但無法入帳）沒有待辦或告警，中高優先（architecture.md §5、A-5）。

### 3.2 品質（quality.md）

1. **基線良好、無失敗**：見第 2 節；測試風格守規（無 ORM mock、純邏輯與資料庫分層正確）（quality.md §2、§6）。
2. **金流回報解析的異常路徑未覆蓋**：`gateways/newebpay.py` 92%（100、102-103、111-112）、`gateways/ecpay.py` 96%（98-99）；補測建議 #1（高價值、成本 S）（quality.md §1 表、§4 #1）。
3. **跨專案隔離測試有路由缺口**：`session_import`、`session_delete`、`attendance walk_in／close`、`front_course`、`message_templates`、`line_settings`、LINE webhook（A 專案 secret 打 B）、服務層 `attendance._check_project`（attendance.py:21，整個防護分支從未被執行）（quality.md §2 缺口表、§4 #2）。
4. **鎖與冪等缺並行測試**：真實並行測試只有 2 處（Jotform 導向 vs 通知、排程諮詢鎖）；改期超收、付款通知重複送達都只以序列方式測（quality.md §2、§4 #3）。
5. **真實外部行為與分支覆蓋率沒有驗證**：004 的 Jotform 導向／通知實際欄位、免費方案、答案形狀、時區完全無自動化驗證，commit `606e744` 已出現同類修正；另未啟用分支覆蓋率（quality.md §3、§4 #7、#11）。

### 3.3 資安（security.md）

1. **H-1（高）設定預設「失敗時開放」**：SECRET_KEY 有寫死預設值、`DEBUG` 預設開、`FIELD_ENCRYPTION_KEY` 退回 SECRET_KEY（等於實質上未加密）、`FAKE_GATEWAY_ENABLED` 預設開，且 `compose.yaml` 不把這些機密傳進容器。簽章付款連結 token 也依賴 SECRET_KEY，金鑰公開即可偽造任意訂單的付款連結。修法成本低（半天內，security.md §7）。
2. **H-2（高）假金流付款繞過**：`fake_complete` 公開、免登入，持有付款連結者可自行送出「付款成功」；`GatewaySettingsForm` 不論旗標都可選假金流。成立條件為專案金流設定 `provider=fake` 且旗標開（預設開）。
3. **M-1（中）`/jotform/return/` 免登入、無節流**：每次請求最多 3 次 Jotform API 呼叫並 `sleep`，可耗盡共用額度、佔滿 worker、灌滿待處理清單；已有訂單的提交編號不再檢查時效。
4. **M-4（中，涉及金額，待確認）金流「失敗」通知把付款嘗試永久鎖成失敗**：之後同單號的成功通知被當成重複丟棄，學員被扣款但訂單仍未付款。
5. **M-2、M-3（中，security.md §7 列為上線前必做）**：Cookie／HTTPS／HSTS／代理設定缺漏；登入無暴力破解防護、無停用帳號途徑、`/admin/` 仍公開。
   其餘中風險 M-5（收款無操作者紀錄、刪學員刪帳本）、M-6（名額鎖）、M-8（重送不重驗）與架構重疊，見 4.1；M-7（LINE 綁定只憑姓名＋電話）、M-9（`cryptography~=43.0`、pip-audit 未跑）見 security.md。

### 3.4 UX（ux.md，靜態閱讀）

1. **UX-01（P1）學員編輯頁標籤區被塞進 `<title>` 區塊**：`project_student_edit.html:2-30`，畫面本體看不到標籤功能，連帶使改期流程入口（`project_reschedule.html:69` 指示「到學員編輯頁加上改期標籤」）在畫面上做不到。ux.md 自己註明需實機渲染與既有測試雙重確認。
2. **UX-04（P1）危險／不可逆操作缺確認**：確認入帳、退款、取消訂單、停用專案、完成點名（會結束場次並啟動追售）、略過 Jotform 報名等一鍵送出；已有的確認機制又有三種。
3. **UX-03、UX-02（P1，成本 S）**：6 個樣板把錯誤訊息畫成綠色成功條（已實際會發生於 `views.py:243` → `manage_base.html`）；追售名單「待邀請出席」整段重複渲染兩次。
4. **UX-06、UX-07、UX-08（P2）現場點名在手機上難用**：側欄堆在內容前、表格橫向溢出、每按一次整頁重載回頁首；「臨時報名」的「已現場收款」預設勾選。
5. **UX-09（P2）學員付款頁**：轉帳資訊與末五碼欄無論選哪種方式都顯示、末五碼僅後端驗證、無防連點、失效連結顯示 Django 預設英文 404（另見 UX-10）。UX-11：轉帳對帳要手抄末五碼、無「待對帳」入口。

## 4. 跨報告對照

### 4.1 重複或互相印證

| 主題 | 各報告內容 | 結論 |
|---|---|---|
| 名額鎖 | architecture F-2／D-2／A-4；security M-6；quality §2「並行測試偏弱」、§4 #3 | 三份都指向同一缺口：只有改期有 `select_for_update`，其他報名路徑無鎖，且並行無測試 |
| 重送通知不重驗（MUST 10） | architecture F-3／A-2；security M-8 | 同一處程式（`notifications.py` `_deliver`／`retry_message`）、同一建議（依 kind 重新檢查、不符標 `SKIPPED`） |
| 設定硬化與金鑰 | architecture F-8／F-9／A-6／A-9／D-5／D-7；security H-1、M-2、L-5、L-6 | 兩份都指出不安全預設值、`runserver`、無 SECURE_*／LOGGING、加密金鑰退回 SECRET_KEY、無輪替；建議都是非 DEBUG 時必填與啟動檢查，architecture 建議與資安修補合併規劃 |
| 刪學員連帶刪財務紀錄、無稽核 | architecture F-4／D-4／D-6／A-3／A-8；security M-5；quality §1（validate 警示 003、004 的 CASCADE 需確認有說明理由） | 三份獨立指出；都建議有收款即禁止刪除或改 `PROTECT`，並加 `Payment.created_by` |
| Jotform 導向／公開端點濫用 | architecture F-5、F-8（`pay_page` 可無限建立 `TransferClaim`）；security M-1、L-2 | 都指出無速率限制；architecture A-7、security M-1 建議以 DB／cache 計數，並把 `sleep` 重試移出 request |
| request 內同步外部呼叫 | architecture F-7；security M-1（請求執行緒內 `sleep`） | 都建議改由 scheduler 補處理；architecture A-10 為較大改動 |
| 登入無節流 | architecture F-8；security M-3；ux.md 待釐清 3（成員只能新增、不能停用） | 帳號停用、重設密碼的缺口被兩個面向同時看到 |
| 已扣款未入帳 | architecture D-14／A-5（`UNAPPLIED` 無待辦、告警）；security M-4（失敗後成功被丟棄）；quality §4 #1（金流回報解析異常未覆蓋） | 金流對帳風險由三個面向從不同角度指出，宜合併規劃 |
| 專案隔離靠慣例 | architecture F-6／D-10（DB 層無一致性約束）；security §3 #4 弱點（同上）；quality §2 缺口表 | 三份一致：目前程式面無 IDOR，但缺機制守門；quality 提供具體缺測路由，architecture 建議加一致性巡檢測試 |
| 並行測試缺口 | architecture D-13／A-12；quality §4 #3 | 一致 |
| 文件落差 | architecture §4.1（規格狀態欄、SITEMAP 過期）；quality §5（004 狀態「草稿」、002 撤回仍提 Google）；ux.md §3.1（SITEMAP 通篇仍寫「銷講」） | 一致；architecture A-13 為成本 S 的快速路線項目 |
| 真實 Jotform 行為、時區 | architecture F-5（`JOTFORM_TIMEZONE` 程式與規格 004 不一致）；quality §3（004 最大外部假設風險、`606e744`）、§1（3 個 `[NEEDS CLARIFICATION]`） | 一致：上線前實測項目沒有驗收紀錄 |
| 專案「停用」語意 | security L-7（停用後公開入口與排程仍運作）；ux.md §2.6、UX-04（停用無確認、影響未說明） | 屬於同一個產品語意問題的兩側 |
| 待對帳／金流回報頁 | architecture §4.2（缺金流 webhook 紀錄、待處理清單）；ux.md UX-11（無待對帳入口） | 同一缺口 |

### 4.2 互相矛盾或口徑不一

1. **MUST 10（發送前再檢查）三種判定**：architecture 判「違反（部分）」（§2 #10）、security 判「部分符合」（§3）、quality 判「符合」，引用的是排程路徑的測試（quality.md §2）。事實層一致（排程路徑有檢查、手動重送與 `PENDING` 殘留沒有），差在判定範圍；quality 的「符合」不涵蓋重送路徑，不應被引用為已合規。
2. **專案隔離與權限的判定**：architecture 將 MUST 4 判「部分／未保護」、MUST 5 判「部分」（§2 #4、#5）；security 兩條都判「符合」（§3）。差異來自標準不同（機制性保護 vs 現有程式有無漏洞），兩者並不互斥。
3. **假金流風險評級**：architecture 認為 `fake_checkout`／`fake_complete` 有簽章與 `provider == "fake"` 守門「風險受限」（F-8）；security 評為高，指出簽章本來就由伺服器交給走完付款頁的人，可自行完成付款（H-2）。以 security 的逐行分析為準較合理，但此分歧需要工程師在修補前確認。
4. **金流冪等評級**：architecture 判 `checkout.py:70-110` 符合（§2 #9、§9）；security 同處發現失敗為終態的缺口（M-4，且標「待確認」）。差異在是否考慮「同單號失敗後重試」；該事實需向綠界／藍新確認（security M-4）。
5. **同一問題的嚴重度標度不同**：名額鎖（architecture F-2 高 vs security M-6 中）、重送不重驗（F-3 高 vs M-8 中）、刪學員（F-4 高 vs M-5 中）、設定硬化（architecture F-8 中 vs security H-1 高）。兩份報告的嚴重度標準不同（架構以憲法與營運影響、資安以可利用性），PM 排序時請以「兩份取較高」處理，並留意不要重複計為多個獨立項目。
6. **Jotform 提交編號可否列舉**：architecture F-5 稱提交編號為連號大整數、同帳號下單調遞增，可能被猜到相鄰編號；security M-1 稱為 18–19 位、帶時間成分，是否可列舉「待確認」。兩者口徑不同，結論為「未確認」。
7. **講師可見付款資料的解讀**：architecture Q4 認為 SITEMAP 只明說「學員資料不遮蔽」，是否該讓講師看付款頁需 PM 確認；security §3 #5 則寫「講師可唯讀看到付款清單與轉帳末五碼，這是 SITEMAP 明定的設計」。兩份對同一份 SITEMAP 的讀法不同，需使用者確認（見 U5）。
8. **憲法 2（禁止 mock）**：architecture 判「符合」，只提 `monkeypatch` 用於外部 client、`_sleep`、getpass（§2 #2）；quality 發現 1 處例外：`tests/db/test_jotform_session_hooks.py:98` 以 monkeypatch 取代自家函式 `sync_form`，列為低嚴重度（§2、§4 #13）。以 quality 為準（已 grep 全 tests）。
9. **標籤功能是否存在**：architecture §4.2 將「標籤」列為「有」（在學員頁 `tags/add|remove`），quality §2 列有標籤路由的跨專案測試；ux UX-01 則判斷標籤區在畫面上看不到。三者可同時為真（路由與 POST 測試存在，但畫面入口損壞），但 UX-01 尚未經實機渲染，結論為「待驗證」。
10. **名額修法位置建議不同**：architecture A-4 建議在付款入帳（`record_payment`）鎖 `Session` 並提示，或維持軟上限並將憲法註記為例外；security M-6 建議在 `_book` 鎖場次並以「已付款＋待付款有效報名」計算額滿。兩者的前提都是 Q1（名額卡在報名或付款）尚未決定。
11. **TEST_LIST 數字**：architecture F-11 稱 `TDD_PROGRESS`／`TEST_LIST` 的數字（660 項）與現況不符；quality §3 稱 TEST_LIST 640 項已勾選、與 tests 無明顯脫節。660 與 640 是否為同一份檔案的數字，報告未說明，標為「未確認」；兩者都同意這兩個檔案為舊流程產物。
12. **評估期間未提交變更的過時敘述**：architecture 以 [WIP] 標記未提交檔案（含 `settings.py`、`registration.py`、`origins.py`），並將 `JOTFORM_TIMEZONE` 預設 `America/New_York` 視為與規格 004 不一致；ux.md 讀取的是 `pay.html` 的工作樹版本（無法 `git diff`）。這些變更現已提交（`eb0a518`、`606e744`、`25cb607`），security 與 quality 以 HEAD 為準。architecture 與 ux 引用的行號與檔案內容是否與 HEAD 完全一致，兩份報告都未重驗，標為「未確認」。ux.md 待釐清 8（pay.html 變更內容與完成時間）與 architecture §7.1 的先決條件（使用者先提交 WIP）已因提交而解除。

## 5. 需要使用者拍板的問題

整併自 architecture.md §8 Q1–Q7、ux.md §7 待釐清、security.md 各項「待確認」、quality.md §5 疑義。已去除重複，來源標於括號內。

| # | 問題 | 為什麼要決定 | 不決定會卡住 |
|---|---|---|---|
| U1 | 是否有正式（對外）環境？如何部署與注入環境變數？是否曾以預設值（`DEBUG`、公開 SECRET_KEY、假金流）對公網運作？目前流量與專案數量？有無專案金流設定為 `provider=fake`？（architecture Q7；security H-1 待確認 1、H-2 成立條件） | 決定 H-1 是否可降為中，或必須輪替金鑰並視為已外洩；也決定硬化與 outbox 的急迫度與是否需要反向代理、多程序 | H-1、H-2、M-2、M-3 的急迫度；A-6、A-9、A-10；金鑰輪替作業；L-6 |
| U2 | `send_line_notifications`、`process_finished_sessions` 現在由誰在跑（主機 cron、手動、未跑）？每日執行時間與時區？漏跑是否要補發、補發窗口多長？（architecture Q2） | 現行 cron 若存在，登錄進 `registered_jobs()` 時須避免重複觸發；補發窗口是業務規則 | A-1／F-1／D-1；與 A-2 同動 `notifications.py`，兩者排序依賴此答案 |
| U3 | 場次名額語意：以「已報名人數」還是「已付款人數」占名額？允許超收嗎（目前實際允許並事後告警）？現場報名、提前報到、CSV 匯入是否永遠不受限（`check_in_early` 已寫明不受限）？若為受控例外，是否同意在憲法或規格註記？（architecture Q1；security M-6） | 憲法字面要求 DB 鎖，現況與 SITEMAP 決策（額滿＝已付款 ≥ 上限）不同；改錯會擋住正當付款 | A-4／F-2／M-6／D-2；並行測試（A-12、quality #3）的案例設計；Jotform 選項下架判斷口徑 |
| U4 | 已有收款（或付款嘗試）的學員可否被刪除？期望「禁止」「軟刪除」或「允許但留稽核紀錄」？操作者稽核（`Payment.created_by`、操作紀錄）要做到什麼程度？（architecture Q3；security M-5） | 屬業務與財務稽核規則；影響是否改 FK／新增欄位（完整路線）或僅禁止刪除（快速路線） | A-3／F-4／D-4／M-5；A-8／D-6 |
| U5 | 角色權限邊界：(a) 講師是否該看到付款頁（金額與付款狀態）？(b) 行政專員可否確認轉帳入帳、退款、取消訂單（SITEMAP 第 6 節仍待確認；security 權限矩陣目前為入帳 `EDIT_DATA`、退款與取消 `MANAGE_REFUNDS`）？（architecture Q4；ux 待釐清 1；security §3 #5、§5） | 兩份報告對 SITEMAP 的解讀不同（見 4.2 第 7 點）；(b) 決定確認文案與按鈕可見性 | architecture F-6／Q4 相關檢查；UX-04、UX-13 的文案與按鈕；M-5 的稽核設計 |
| U6 | SITEMAP 中「跨專案總覽」「學員詳情彙整頁」「排程時間規則設定」「金流 webhook 紀錄／待對帳頁」仍要做，還是正式列為不做？「待邀請出席」區預期動作是什麼（只是資訊，或需要按鈕）？（architecture Q5；ux 待釐清 2；architecture §4.2） | 這些是 SITEMAP 原計畫但實作缺漏，不決定就無法區分「缺陷」與「不做」；SITEMAP 也要據此校正 | A-14、A-13、UX-11、UX-02 的說明文字、UX-21 |
| U7 | 成員管理：只能新增、不能停用／改角色／重設密碼，是否為已知缺口、是否要補？`/admin/` 是否保留？（ux 待釐清 3；security M-3） | 離職或卸任者無法在應用程式內失去存取權；屬產品與資安決策 | security M-3 的帳號停用部分（登入節流本身可先做） |
| U8 | 專案「停用」的語意：只是隱藏，還是停止營運（連公開付款頁、金流通知、LINE webhook、Jotform 導向、排程同步與發送一併停止）？（security L-7；ux §2.6） | 兩種語意的程式改動與停用前的確認文案完全不同 | L-7；UX-04 中「停用專案」的確認內容 |
| U9 | `JOTFORM_TIMEZONE` 以 `America/New_York` 為預設是否為最終決定、要否回寫規格 004？004 上線前 Jotform 實測五項（SITEMAP:269）／3 個 `[NEEDS CLARIFICATION]` 是否已完成、是否要補真實帳號實測？是否同意把 004、003、001 規格狀態欄更新？NFR-001／SC-001／SC-004 是否補上線後監控項目？（architecture Q6；quality §5 1、4、§3） | 規格狀態欄無人維護，無法判斷哪些已完成；004 最大外部假設風險目前零自動化驗證 | A-13；quality #11；F-5 的後續 `/clarify`；004 的收尾驗收 |
| U10 | 是否授權執行 `make test-integration`，並提供 Jotform（與藍新）測試帳號供 integration 擴充？（quality §1、§4 #11） | 護欄規定須使用者授權；現僅綠界 2 項 | 004 真實行為驗證、integration 層擴充 |
| U11 | LINE 綁定的產品方式：維持姓名＋電話，或改成一次性綁定碼等第二因子？失敗回覆文字是否統一？（security M-7，已註明為產品決策） | 現行綁定可被知道姓名與電話者搶先綁定，並可探測學員是否存在 | M-7（需 PM 評估後才能動工） |
| U12 | 金流失敗通知後同單號重試的實際行為：是否由使用者向綠界／藍新確認，或同意依官方文件查證？（security M-4 待確認） | 失敗是否為終態決定 `checkout.py` 狀態機要不要改；涉及金額 | M-4；A-5（`UNAPPLIED` 處理）；補「先失敗後成功」測試 |
| U13 | 是否同意在可連網環境執行 `pip-audit`（或在 CI 加定期工作）？`cryptography` 是否同意升級主線並跑全測試？（security M-9、§6） | 依賴漏洞掃描尚未做；工具不存在且評估不得對外查詢 | M-9；依賴面風險是否有其他未知項 |
| U14 | 品質門檻政策：是否啟用分支覆蓋率並重設門檻？是否要求本機 `make coverage` 也帶 `--cov-fail-under`？（quality §4 #7、§5 2） | 憲法寫「維持專案約定門檻」，但本機不擋；97% 只是行覆蓋 | quality #7；高風險區（權限、金額）的真實覆蓋度判斷 |
| U15 | UX 小項：(a) 現場點名是否主要用手機（決定 UX-06 做到卡片列或僅可捲動）；(b) `?date=` 參數是否保留於正式環境（保留則須標示檢視日期）；(c) 付款頁與通知頁是否要加客服聯絡方式；(d) 是否要唯讀查詢資料庫中含「銷講」的標籤、場次標題、通知範本（需有權限者）（ux 待釐清 4–7） | 影響 UX 項目的範圍與設計；(d) 為憲法用語 MUST 的資料面確認 | UX-06、UX-21（`?date=`）、UX-09／`pay_return.html`、UX-16 |

## 6. 評估的限制

- **architect 與 uiux-designer 沒有 Bash，只做靜態閱讀**：architecture.md 沒有通讀全部程式、沒有執行 `git status`／`make codemap-check`／`make test`／`make lint`，並行與效能結論均為讀碼推論，標「推論」（architecture.md §0）；ux.md 未實機渲染、未用瀏覽器或螢幕閱讀器測試，對比值為依色碼手算、行動版問題為依 CSS 推論，標「待驗證」者需實機確認（ux.md §0）。
- **security 為靜態唯讀審查**：未啟動應用程式、未送請求，所有「可被利用」的判斷來自讀碼；未審實際部署環境（反向代理、TLS、WAF、實際環境變數），這是最大盲點（security.md §1）；金流等外部行為依官方文件推論，標「待確認」。
- **`pip-audit` 未執行**（工具不存在，不得對外查詢）；只做人工版本範圍檢查（security.md §6、M-9）。
- **`make test-integration` 未執行**（需使用者授權，會連真實外部服務），因此真實 ECPay、藍新、Jotform、LINE 行為沒有任何自動化驗證（quality.md §1）。
- **UX 為靜態閱讀**：UX-01 等結論尚未經渲染驗證；UX-09 讀的是 `pay.html` 工作樹版本，與現已提交的 `eb0a518` 是否一致未經比對。
- **分支覆蓋率未啟用**：97% 僅行覆蓋（quality.md §1）。
- **評估時點不一致**：architecture 與 ux 撰寫時工作樹仍有未提交變更（只讀得到工作樹）；quality 與 security 以乾淨的 HEAD `eb0a518` 執行或審查。architecture 與 ux 所引行號請於動工前對照 HEAD 重驗（見 4.2 第 12 點）。
- **未讀取任何禁區檔案**：四份報告皆聲明未讀取 `.env`、`.pytest_cache`、`manifest.json`。

## 7. 建議先做什麼（僅為建議，由使用者決定）

排序依嚴重度與價值，並考量互相依賴與檔案衝突（architecture §7.1 提示：`views.py` 幾乎被所有項目觸及，A-11 重構宜在其他項目收斂後再做，不要交錯）。

1. **先回答 U1（部署現況）**：不需寫程式，卻決定整份清單的急迫度；若曾以預設值對公網運作，優先輪替金鑰（security H-1 待確認 4）。
2. **H-1 + H-2 合併處理，並與 A-6／A-9 一併規劃**（security §7 估算半天內可完成預設值與假金流修補；architecture A-6、A-9）：修復後需複審；與 `settings.py`、`crypto.py`、`compose.yaml`、`forms.py` 有關，宜由同一位工程師處理。
3. **低成本、獨立、可平行的缺陷與補測**：UX-01、UX-02、UX-03、UX-10、UX-05（ux.md §6 第一批，成本皆 S；UX-01 先實機確認）；quality 補測 #1（金流回報解析異常）、#2（跨專案隔離測試）、#4（金額驗證）（quality §6）；A-13 文件校正（成本 S，需先有 U9）。
4. **上線前必做的資安項目**：M-2（Cookie／HTTPS／HSTS）、M-3（登入節流，帳號停用部分待 U7）、M-1（`jotform_return` 節流與外部呼叫）、M-4（金流失敗後成功；先有 U12）。可與 A-7、A-5（未入帳待辦）合併規劃。
5. **需使用者決策後才能開工的憲法落差項目**：A-1（排程落地，待 U2）、A-2／M-8（重送發送前重驗；與 A-1 同動 `notifications.py`，宜同一人依序做）、A-3／M-5（刪學員保護，待 U4）、A-4／M-6（名額，待 U3；並行測試 A-12／quality #3 最好先行或同步）。
6. **結構性與長尾項目最後處理**：A-11（`views.py` 拆分）、A-10（outbox、分頁）、A-14、UX 第三、四批（UX-09 待確認 `pay.html` 與 U15）。

**到此停下，由使用者挑要做哪些項目**；backlog 轉換由 `pm` 依本摘要與四份報告進行，狀態追蹤另由調度者派 `project-manager` 更新 `status.md`。
