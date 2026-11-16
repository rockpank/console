# teacher-crm UX 評估

評估日期：2026-11-13　角色：UIUX 設計師（UX 評估模式，唯讀）
Repo：`/Users/Park/Site/teacher-crm`（純 Django template，無前端框架）

## 0. 範圍、方法與限制

- 盤點對象：`src/crm/templates/` 全部 34 個樣板（`crm/*.html` 33 個 + `registration/login.html`）、`base.html` 內嵌 CSS、`forms.py`／`context_processors.py`／`domain/project_nav.py`／`dashboard.py`／`views.py` 中影響畫面文案與狀態的部分。
- 方法：靜態閱讀樣板與 view，依角色走過核心任務。**未實機渲染、未用瀏覽器或螢幕閱讀器測試**；對比值為依色碼手算的估值，行動版問題為依 CSS 與版面結構推論。凡需實機確認者標「待驗證」。
- 靜態資源：`src/` 下**沒有任何 .css/.js/圖片**，`settings.py` 只有 `STATIC_URL = "static/"`，沒有 `STATIC_ROOT`／`STATICFILES_DIRS`。全部樣式為 `base.html:7-96` 的單一內嵌 `<style>`，唯一的 JS 是 `project_reports.html:39-50` 的複製按鈕、`pay_redirect.html:12` 的自動送出，以及 4 處 `onclick="this.select()"`、1 處 `onsubmit="return confirm(...)"`。
- 未提交變更：`crm/pay.html` 是使用者進行中的變更之一。我讀的是**工作樹版本**（我這次沒有 Bash 工具，無法 `git diff` 對照已提交版本），下面 pay.html 的行號以工作樹為準，工程師動工前請先與使用者確認該檔是否已定稿，不要與其收尾衝突。其餘樣板未列在未提交清單內。
- 憲法關聯：`specs/constitution.md:38`「使用者可見文字 MUST 沿用統一用語（例如「前端課」），不得混用舊稱」。

## 1. 現況設計系統（從 base.html 還原）

### 1.1 色彩 token（`base.html:8-21`，含 `prefers-color-scheme: dark` 自動切換，無手動切換開關）

| token | 亮色 | 暗色 | 用途 |
|---|---|---|---|
| `--bg` | #f5f6f8 | #12151c | 頁面底、輸入框底、徽章底 |
| `--surface` | #fff | #1b202b | 卡片、導覽 |
| `--text` | #1d2330 | #e8ebf2 | 內文 |
| `--muted` | #667085 | #9aa3b5 | 次要文字 |
| `--line` | #e3e6ec | #2b3242 | 邊框、分隔線 |
| `--primary` / `--primary-text` | #2457c5 / #fff | #6c97f0 / #0d1220 | 主色、主按鈕 |
| `--danger(-bg)` | #b42318 / #fdecec | #ff9b92 / #3a1a1a | 錯誤、危險 |
| `--ok(-bg)` | #1a7f4b / #e8f5ee | #6fd6a0 / #16301f | 成功 |

缺口：沒有 **warning、info** 語意色；沒有 hover／active／disabled 狀態 token；沒有 focus ring token。

手算對比（WCAG AA 文字 4.5:1、非文字 3:1）：

| 組合 | 估值 | 判定 |
|---|---|---|
| `--muted` 在 `--surface` / `--bg`（亮） | 約 5.0 / 4.6 | 過，但 `--bg` 上已逼近下限 |
| `--primary` 在白底（亮）、白字在 `--primary` | 約 6.5 | 過 |
| `--danger` 在 `--danger-bg`（亮） | 約 5.7 | 過 |
| `--ok` 在 `--ok-bg`（亮） | 約 4.5 | 剛好壓線 |
| **白字在暗色 `--danger`（#ff9b92）** | 約 2.0 | **不過**（`confirm_delete.html:9`） |
| **輸入框／選單邊框 `--line` 對 `--bg`／`--surface`（亮）** | 約 1.2 | **不過 1.4.11 非文字 3:1**（`base.html:48,61,68`） |

### 1.2 字型與字級

- 字型：`system-ui, -apple-system, "PingFang TC", "Noto Sans TC", sans-serif`，內文 16px／行高 1.6（`base.html:23-24`）。
- 實際用到的字級：h1 22px（`base.html:33`）、h2 在**兩種寫法**：多數頁面行內 `font-size: 17px`（約 14 處），但 `project_detail.html:14,20,29`、`project_follow_ups.html:16,35,45,56,73`、`project_jotform_settings.html:40`、`project_front_course.html` 等用**瀏覽器預設 h2（約 24px，比 h1 還大）**。其他：統計數字 28px、徽章／側欄標題／統計標籤 12–13px、說明小字 13–14px（行內 `font-size: 13px`、`<small>` 共約 25 處）。
- 沒有字級階層 token，全靠散落的行內值。

### 1.3 間距、圓角、陰影、斷點

- 間距：沒有 token。實際值有 2/4/6/8/10/12/14/16/24/28/32/40/48px 混用；`.card` 內距 16px；區塊間距靠每個樣板行內 `style="margin-bottom: 16px|24px|12px|8px"`。行內 `style=` 共 **133 處、26 個檔案**。
- 版面：`main` 單欄 max-width 760px；有專案側欄時 `.shell.with-nav` max-width 1080px、側欄 220px（`base.html:32,76-77`）。
- 圓角：卡片／列表項 12px、按鈕／輸入 8px、徽章 999px；**無陰影**（靠 1px 邊框分層）。
- 斷點：只有一個 `@media (max-width: 760px)`（`base.html:90-94`），只處理側欄堆疊。表格與表單行為沒有其他斷點。
- 對齊 hack：inline-form 的按鈕用 `style="margin-top: 28px"` 去對齊旁邊含 label 的輸入框，共 **11 處**（payments、students、reports、manage_*、notifications、reschedule、jotform_submissions…）；label 換行或行動版折行時會錯位。
- 全形空白「　」被當版面間距，散見於 attendance、follow_ups、session_detail 等，行動版折行位置不可控。

### 1.4 元件現況與不一致

| 元件 | 現況 | 不一致／缺口 |
|---|---|---|
| 按鈕 | `.btn`（主）、`.btn.secondary`（外框）、`.btn.link`（無框） | 沒有 danger 變體、沒有 disabled／loading；`confirm_delete.html:9` 以行內 style 自製紅鈕；`.btn.link` padding 0，點擊區只有文字高度（約 26px）；表單內動詞混用：新增／建立／儲存／更新／登記／確認（例：`project_sessions.html:33,41` 標題「新增場次」按鈕「建立場次」；`manage_members.html:6,14`） |
| 表單 | `.field`（label 在上、grid gap 6px） | `.field input` 有樣式，**`textarea` 沒有**（場次注意事項、通知範本、轉帳資訊、贈品備註為瀏覽器預設外觀）；`.field input` 套到 **checkbox**（付款設定「啟用線上刷卡」「沙盒」、LINE「啟用」）會被加 padding／邊框／grid 對齊而變形（`project_payment_settings.html:15-23`、`project_line_settings.html:19-27`）；沒有必填標記；`help_text` 不渲染（`models.py:159,162` 的「訂金（選填）」「備註，例如贈品」在 `project_products.html:48-54` 的 `{% for field in form %}` 迴圈中被丟掉）；`.copybox` 定義了沒人用，LINE 設定的 webhook 輸入框用行內 style |
| 表格 | 全域 `table`，`th/td` 左對齊、10px 8px | 有 `overflow-x: auto` 包裹的只有 attendance、payments、notifications；其餘 8 張表沒有（見 4.2）；沒有 `<caption>`／`scope="col"`；數字欄未靠右 |
| 狀態標籤 | `.badge`（+`.ok`/`.bad`）、`.role`（原為「角色徽章」） | 同一件事兩套：`project_session_detail.html:30`、`project_jotform_*` 用 `.badge`；`project_attendance.html:35-39`、`project_payments.html:54-56` 用 `.role` + 行內 `style="color: var(--ok)"`。`.role` 被挪用成通用狀態標籤，名稱與用途不符。只有 ok/bad/中性，沒有 warning |
| 提示訊息 | `.alert.error`／`.alert.ok` | 沒有 warning／info。**資訊性提醒也用紅色 error**：`project_line_settings.html:15`（LINE 尚未實測）、`project_payment_settings.html:10`（藍新未驗證）、`fake_checkout.html:6`（開發用頁）。`role` 屬性混亂：錯誤訊息用 `role="status"`（`project_sessions.html:9` 等約 20 處），應為 `alert` |
| Flash 訊息 | 各樣板自己寫 `{% for message in messages %}` | **約 20 個樣板各抄一份**，且兩種版本：能分辨 error（`sessions/attendance/payments/students/products/reschedule/front_course/jotform_*/notifications/session_detail`）與一律綠色（見 UX-03） |
| 導覽 | 頂欄（品牌、系統管理、帳號、角色、登出）+ 專案左側欄（依權限分 5 組，`project_nav.py:76-108`）+ 麵包屑 + 系統管理分頁 tabs | 麵包屑格式不一：有的「所有專案 / 專案」（sessions、payments…）、有的「專案 / 場次」（session_detail、attendance，少了「所有專案」）、project_detail 是「← 所有專案」；有側欄後麵包屑大半重複。頂欄 `nav a` 沒有 hover／目前頁樣式 |
| 對話框 | **無**。危險操作只有：獨立確認頁（`confirm_delete.html`，僅場次／學員刪除）與 1 處原生 `confirm()`（Jotform 移除連結） | 兩種確認機制並存且樣式不同；其餘危險操作完全沒確認（見 UX-04） |
| 空狀態 | `.card.empty`（置中、灰字） | 一致的外觀，但**幾乎都只有一句陳述，沒有下一步動作**（見 UX-12） |
| 載入狀態 | 無 | 同步 Jotform、重送通知、金流導向等耗時動作沒有處理中提示或防連點 |
| 錯誤頁 | 無自訂 403/404/500 樣板（`src/` 內無 handler、無 `404.html`） | 見 UX-10 |
| 統計卡 | `.stats`／`.stat` | 只用在 project_detail；一致 |
| 清單項 | `.list a.item`、`.list li.card` | 兩種寫法並存（連結列 vs 卡片列），follow_ups／reschedule／jotform_settings 的 `.list` 內放 `<span class="item">`（不可點卻有同樣外觀） |

## 2. 核心任務走查（依角色）

角色來源：`models.py:53-57`（系統管理員／行政管理者／行政專員／講師）與 `specs/SITEMAP.md` P0。權限由 `project_nav.py` 的 `NavPermissions` 決定哪些選單項出現。

### 2.1 admin：建專案、設定、場次

路徑與步驟數：
1. 頂欄「系統管理」→「專案」分頁 →填 4 欄（名稱、講師團隊、前端課名稱、費用）→「新增專案」（`manage_projects.html:4-26`）。成功後只有綠色一行訊息，**沒有「前往此專案」連結**，專案名稱在下方表格也不是連結（`manage_projects.html:34`）。
2. 回頂欄品牌 → 我的專案 → 點專案 → 側欄「授權管理」勾選人員（行政專員要被授權才看得到）。
3. 側欄「付款設定」「LINE 設定」「Jotform 報名表」（連結 + 選擇姓名題／電話題 + 複製導向網址與 Webhook 貼到 Jotform）。至少 3 頁、約 12 個欄位，且**沒有「專案設定完成度」指引**，使用者要自己記得有哪幾項。注意 `project_front_course.html:11` 說「每個專案都必須有前端課」，但建專案表單已要求填前端課，這個「缺前端課」警告只會出現在舊資料。
4. 側欄「場次」→ 清單下方的「新增場次」表單（`project_sessions.html:30-43`）。表單位於清單**之後**，場次多時要捲到底才能新增；每個月要建多場，沒有「複製場次」。

問題：入口分散、無完成度指引（UX-14）；建完專案沒有導向（UX-12）；場次列表缺「狀態」（SITEMAP 要求「日期、地點、方式、狀態」，`project_sessions.html:12-25` 只有人數與已付款，沒有已結束／額滿／已過期標示）。

### 2.2 行政管理者／行政專員：報名、付款、對帳

學員路徑（pay.html，免登入）：Jotform 送出 → `jotform_return`（錯誤情境有 `jotform_notice.html` 五種提示，文案良好）→ `/pay/<token>/` 選「付款金額」→「付款方式」（信用卡／轉帳）→ 填末五碼 →「確認付款方式」→ 金流（`pay_redirect.html` 自動送出）或 `pay_transfer_done.html`。3 次互動，步驟本身精簡，但 pay.html 有表單層問題（UX-09）。

行政對帳：側欄「付款對帳」→ 篩選（課程／狀態／編號，預設「全部狀態」，無分頁）→ 找到訂單 → 在最後一欄（行動作區）看到「學員回報轉帳」提示 → **手動把末五碼抄進「備註」** → 按「確認入帳」（`project_payments.html:71-88`）。問題：
- 待對帳的轉帳回報只以最後一欄內的小提示呈現，**沒有「待對帳」專屬清單或狀態篩選**（SITEMAP 要求「轉帳人工對帳（待對帳清單 → 確認入帳）」）；儀表板待辦也沒有「N 筆待對帳」。
- 「確認入帳」「退款」「取消訂單」都**無確認**，且按鈕外觀同為次要按鈕（見 UX-04）。
- 一列塞入「付款連結輸入框 + 金額 + 備註 + 確認入帳 + 退款金額 + 備註 + 退款 + 取消訂單」，行動作區過密（UX-13）。
- Jotform 報名紀錄（待人工處理）有側欄徽章數字（`context_processors.py:42-44`），這點做得好；但「略過」不可復原卻無確認（`project_jotform_submissions.html:54`）。

### 2.3 行政專員／講師：當天點名

路徑：側欄「場次」→ 點場次 → 「當天點名」→ 每位學員按「到場」／「未出席」→ 「完成點名」。步驟不多，但：
- **每按一次整頁重新載入並回到頁首**（`views.py:1313-1314` 以 `redirect` 回同頁，無錨點），名單超過一屏時每點一人都要重新捲動找位置（UX-06）。
- 行動版（現場最可能用手機）：側欄堆疊在最上方佔數屏高度、表格含 5 欄且動作欄有 3 顆按鈕，只能橫向捲動才按得到（UX-06）。
- 「完成點名」按鈕旁文字只說「未點名者標為未出席」，但 `views.py:1413-1423` 還會**結束場次並啟動追售**（訊息「開始追售 N 位學員」是事後才告知），沒有事前確認（UX-04）。
- 「臨時報名登記」的「已現場收款」checkbox **預設勾選**（`project_attendance.html:91`），漏看就會把未收款記成已付款；金額相關預設值不應預勾。
- 講師進入點名頁是唯讀（`can_edit` 為 false）：整個登記區消失但**沒有任何說明**為何無法點名（UX-12 無權限狀態）。
- 「提前參加」下拉選單項內含學員姓名、電話、其餘報名場次的長字串（`project_attendance.html:74`），行動版會被截斷。

### 2.4 行政專員：追售名單

`project_follow_ups.html`：
- 「待邀請出席」整段**重複渲染兩次**（`:35-44` 與 `:45-54`），畫面上會看到兩個相同標題與相同名單（UX-02）。
- 「待邀請出席」只列名單，**頁面沒說明這些人該做什麼、也沒有行動按鈕**；「追售中」有「停止追售」、「進階未完款」有「提醒完款」，唯獨這一區沒有動作也沒有說明。
- 「停止追售」無確認（`:25`）；DAY1/3/7 的進度只顯示「第 N 天」，沒有「下一次發送日／已發送」資訊。
- 此頁 flash 一律綠色（`:9`）。
- 頁首說明（`:10`）以「追售」稱呼，與整站一致；與標題「追售名單」一致。

### 2.5 儀表板／每日待辦（所有行政角色）

- 專案列表（`project_list.html:12`）只顯示「待辦 N　異常 M」兩個灰字數字，異常不分色、不是連結（整列才是連結），無法在列表上判斷哪個專案有急事。
- 專案總覽（`project_detail.html`）：順序為「統計三卡 → 今日待辦／異常提醒 → 即將開課場次」。**待辦（每日第一件事）排在統計之後**；異常提醒與待辦放在同一張卡內，異常沒有警示色或圖示，與待辦外觀相同（皆 `.list a.item`）。待辦項只有一句文字，沒有日期／急迫度標示。
- 講師沒有待辦區（`show_dashboard` 僅 `can_edit_data`），但看到的是同一個頁面，只是少了區塊，沒有說明。
- 即將開課表格 6 欄無橫向捲動包裹（`:31`）。
- `?date=` 參數可覆寫「今天」（`views.py:133,153`），屬除錯／測試用途但在正式畫面無任何標示（若有人帶了日期，畫面看不出來）。

### 2.6 系統管理（admin）

- 專案表格的「更新」「停用／啟用」兩個表單並排在同一格，**「停用」無確認**，停用後的影響（誰看不到什麼）沒有說明（`manage_projects.html:48-51`）。
- `manage_base.html:9` 的 flash 一律 ok 樣式，但 `views.py:243` 會送 `messages.error` → 錯誤被畫成綠色成功條（UX-03）。
- 成員頁只能新增、不能編輯／停用／重設密碼（功能缺口，非本次 UX 重點，列入待釐清）。

## 3. 用語一致性

### 3.1「前端課」vs 舊稱「銷講」

- **使用者可見文字（樣板、forms 的 label、models 的 choices 顯示名、dashboard／reports／LINE 訊息的字串）：未發現「銷講」。** `models.py:151` 顯示名為「前端課」，`retagging.py` 已有舊標籤改名對照。
- 殘留位置（皆非使用者可見，但容易在日後被複製進畫面）：
  - Docstring：`views.py:1291,1319`、`orders.py:50,59,90,99,130`、`reports.py:51`、`line/notifications.py:54`（註解）。
  - Migration 歷史：`migrations/0005_...py:21` 的 choices 標籤「第一階段（銷講報名）」，以及 `0017`、`retagging.py` 的舊標籤對照表（這是資料遷移需要，應保留）。
  - 規格文件：`specs/SITEMAP.md` 通篇仍寫「銷講」（規格非使用者可見）。
- 風險點（待驗證）：資料庫裡既有的 `StudentTag.name`、場次標題、`MessageTemplate` 自訂內容若仍含「銷講」，畫面會原樣顯示。`retagging` 只處理兩個標籤名稱；需用實際資料庫查一次（唯讀 SQL）。
- 另有「第一階段」（docstring 與 `models.py` 以前的名稱）與「前端課」混用於程式註解；建議一併統一用語表（見 UX-16）。

### 3.2 其他用語不一致（使用者可見）

| 位置 | 問題 |
|---|---|
| `project_notifications.html:12` 說「請先到「課程與費用」」 | 側欄沒有這個名稱；實際是「前端課費用」（`project_nav.py:82`）。 |
| `project_nav.py:87` 群組「進階課程」→「課程費用與贈品」；`project_products.html:9` h1「進階課程費用」；`project_front_course.html:10` 提到「在「進階課程」」；`project_products.html:10` 提到「在「前端課」」 | 同一個頁面有三種名字（課程費用與贈品／進階課程費用／進階課程），互相指稱的名字也對不上側欄。 |
| `project_jotform_settings.html:24`「只有 admin 可以」；`project_notifications.html:15`「請 admin 到」；`project_jotform_settings.html:11`「JOTFORM_API_KEY」「scheduler 服務」 | 角色顯示名在頂欄是「系統管理員」（`models.py:54`），內文卻寫英文 `admin`；工程用詞外洩給行政人員。 |
| 動詞：新增／建立／儲存／更新／登記／確認 | 同類操作按鈕名稱不統一（`project_sessions.html:33,41`、`manage_members.html:6,14`、`project_students` 搜尋 vs 篩選）。 |
| `views.py:947`「已收 NT$ {order.paid_amount}」 | 其他處皆用 `intcomma` 千分位，此處沒有。 |
| 頂欄「系統管理」vs 麵包屑「所有專案」vs 品牌「課程行政系統」 | 品牌連結指向專案列表，頁面標題為「我的專案」，麵包屑稱「所有專案」，三個名字。 |
| 「授權管理」（側欄）vs SITEMAP「專案授權」；「付款對帳」vs「付款」 | 可接受，但建議建立用語表固定。 |

## 4. 其他 UX 與無障礙問題

### 4.1 無障礙

- **標籤**：多數欄位有 `<label for>`；表格內聯表單用 `aria-label`（良好，如 `project_payments.html:84,86,94,95`）。缺口：
  - 登入頁只顯示 `non_field_errors`（`login.html:8`），欄位層級錯誤不顯示；無 `autofocus`、`autocomplete` 由 form 決定（待驗證）。
  - `project_payments.html:79` 等唯讀輸入框的 `onclick="this.select()"` 只有滑鼠行為，鍵盤使用者 Tab 進入時不會自動全選，也沒有「複製」按鈕。
  - 必填欄位沒有視覺或 `aria-required` 提示；多處 `required` 只靠瀏覽器原生泡泡。
  - 欄位錯誤（`{{ field.errors }}`）沒有用 `aria-describedby` 連到欄位，`aria-invalid` 沒設。
  - checkbox 在 `.field`（grid）中 label 與 input 分行。
- **鍵盤與焦點**：沒有自訂 `:focus-visible`，依賴瀏覽器預設外框（沒被關掉，但在暗色 `--bg` 或主色按鈕上可見度不一）；沒有「跳到主要內容」連結——每頁要先 Tab 過頂欄加最多 15 個側欄連結。表單驗證失敗後焦點沒有移到錯誤摘要（pay.html 的 `role="alert"` 會朗讀，良好）。
- **目標大小**：`.btn.link`（取消、重送、移出場次、移除標籤「×」、取消訂單）點擊區約 26px 高、「×」更小（`project_student_edit.html:10`），低於觸控建議 44px，WCAG 2.2 的 24px 勉強過。
- **語意**：錯誤訊息誤用 `role="status"`（見 1.4）；表格沒有 `scope`、`caption`；`<h2>` 階層正確但視覺尺寸不一致；狀態文字有文字本體不靠顏色單獨傳達（良好，如到場／未出席／已付款）。
- **對比**：見 1.1，兩處確定不過（暗色危險按鈕白字、輸入框邊框），`--ok` 在綠底壓線。
- **動態內容**：複製成功只改按鈕文字（`project_reports.html:45`），沒有 `aria-live`；`navigator.clipboard` 在非 HTTPS 或權限被拒時 promise 失敗沒有處理，使用者無回饋。

### 4.2 行動裝置

- 側欄在 ≤760px 變成頁面**最上方**的 2–3 欄連結網格（`base.html:90-94`，約 15 個連結 + 5 個群組標題），每頁都要先捲過它才看到內容。
- 表格沒有橫向捲動包裹：`project_detail.html:31`（6 欄）、`project_session_detail.html:25`（5–6 欄）、`project_students.html:18`（7 欄）、`project_products.html:14`（含更新表單 5 欄）、`project_jotform_submissions.html:27`（**8 欄**）、`manage_projects.html:28`、`manage_members.html:16`。`<table>` 寬度 100% 但內容撐開時整頁會橫向溢出，或欄位被壓成逐字斷行。
- 有包裹的三張表（attendance、payments、notifications）要橫向捲才碰得到動作欄。
- 內聯表單用 `flex-wrap` + `flex: 1 1 220px`（良好），但 `margin-top: 28px` 的按鈕對齊在折行後會錯位。
- 公開付款頁（pay.html、pay_*.html）是單欄 760px max-width，行動友善；radio 區塊以 `padding: 6px 0` 的整行 label 作觸控區（約 37px，可接受）。

### 4.3 回饋、錯誤與空狀態

- **成功回饋**普遍良好：幾乎每個 POST 都有 flash 訊息，文案具體（「已將「X」移出此場次」）。
- **錯誤回饋**：表單驗證錯誤用 `{{ field.errors }}`（unstyled `<ul class="errorlist">`，有紅字），頁面頂端沒有錯誤摘要；多數動作錯誤用 flash。pay.html 錯誤以單一 `role="alert"` 條顯示、無欄位層級標示。
- **空狀態**：外觀一致，但缺下一步（UX-12）。
- **無權限／找不到**：沒有自訂樣板，使用者看到 Django 預設的英文「Forbidden／Not Found」純文字頁（`PermissionDenied` 與 `Http404` 多處使用，如 `views.py:166,185,866`）。學員點到失效付款連結（`InvalidPayToken` → 404）也是同一個英文空白頁。
- **載入狀態／防連點**：無。「立即同步」（`project_jotform_settings.html:78`）、「確認入帳」、「退款」、「確認付款方式」連按會送出多次請求。
- **分頁**：學員、付款、報名紀錄、場次列表都沒有分頁或每頁上限（通知紀錄在 `views.py:1240` 靜默截斷 200 筆且畫面沒說）。資料量增加後頁面會變慢、變長。

## 5. 改善建議（供 PM 轉 backlog）

編號 UX-xx；優先度依：確定的缺陷／資料風險 P1，高頻流程體驗 P2，系統性收斂 P3。價值 H/M/L，成本 S（約半天內）/M（1–3 天）/L（>3 天）。

### P1：確定的缺陷與誤操作風險

**UX-01　學員編輯頁的標籤區被塞進 `<title>`，畫面上看不到**
- 位置：`project_student_edit.html:2`（`{% block title %}` 開了沒關）、`:30`（`{% endblock %}` 實際關掉的是 title）、`:31`（`{% block content %}` 才開始）。
- 問題：第 2–30 行（標籤清單、新增標籤表單、標籤紀錄）全部落在 `<title>` 區塊內，瀏覽器把它當標題文字，頁面本體看不到任何標籤功能。連帶地，改期處理的空狀態指示「在學員編輯頁幫學員加上「改期」標籤」（`project_reschedule.html:69`）**在畫面上做不到**，改期流程（SOP 每月 1–5 號）的入口被切斷；標籤相關 view（`views.py:1017,1032`）仍在，只是畫面無入口。（靜態閱讀可確定，建議以實際渲染與既有測試 `tests/db` 雙重確認；若測試只打 POST 端點，就不會發現。）
- 建議：在第 2 行補上 `{% endblock %}`，把第 3–29 行（標籤區）移到 `{% block content %}` 內「編輯表單之後、改期紀錄之前」；補一條渲染測試（回應含「新增標籤」）。
- 價值 H　成本 S

**UX-02　追售名單「待邀請出席」整段重複**
- 位置：`project_follow_ups.html:35-44` 與 `:45-54`。
- 問題：兩段完全相同，畫面上出現兩個相同標題與名單，使用者以為有兩批人。
- 建議：刪除其中一段；另在標題旁補一句說明（這群人要做什麼、何時會進入追售）。
- 價值 H　成本 S

**UX-03　錯誤訊息被畫成綠色成功條，且 role 用錯**
- 位置：一律綠色：`manage_base.html:9`、`project_follow_ups.html:9`、`project_access.html:10-12`、`project_line_settings.html:10`、`project_message_templates.html:10`、`project_payment_settings.html:11`（共 6 個樣板）。已實際會發生：`views.py:243`（更新專案失敗 `messages.error`）顯示在 `manage_base`。誤用 `role="status"` 的約 20 處（如 `project_sessions.html:9`）。
- 問題：錯誤看起來像成功，使用者以為儲存成功；螢幕閱讀器對錯誤只做禮貌朗讀。
- 建議：新增 `crm/_messages.html`（依 `message.tags` 決定 `.alert.error` 加 `role="alert"` 或 `.alert.ok` 加 `role="status"`，並預留 `warning`／`info`），在 `base.html` 的 `<main>` 開頭統一 include，移除所有樣板自帶的迴圈（約 20 處）。同時消除「同一功能多種寫法」。
- 價值 H　成本 S

**UX-04　危險／不可逆操作缺確認**
- 位置與現況：
  - 無確認：確認入帳／退款／取消訂單 `project_payments.html:87,96,103`；停用專案 `manage_projects.html:50`；完成點名（會結束場次並啟動追售）`project_attendance.html:64`；移出場次 `project_session_detail.html:36`；停止追售 `project_follow_ups.html:25`；略過 Jotform 報名 `project_jotform_submissions.html:54`；建立報名與訂單 `:50`；移除標籤「×」`project_student_edit.html:10`。
  - 已有確認但機制不一：刪除場次／學員走獨立確認頁（`confirm_delete.html`，用行內 style 自製紅鈕；暗色模式白字在 `#ff9b92` 約 2:1 對比不足）；移除 Jotform 連結用原生 `confirm()`（`project_jotform_settings.html:81`）。
- 問題：涉及金額與不可復原的動作一鍵就送出；確認方式有三種。
- 建議：定一條規則寫入設計系統「互動規範」：金額（入帳、退款、取消）、不可復原（略過、刪除、結束場次、停用專案）必須確認，確認文案要寫出對象與後果（「確定退款 NT$ 3,000 給 王小明？此動作會記錄一筆退款。」「完成點名後場次將結束，N 位未點名者標為未出席，並開始追售 M 位學員。」）。純 template 做法：在 `.btn` 系統加 `.btn.danger` 變體（用 token 取代行內 style，並修正暗色文字色）；統一採用 `<dialog>` 或既有「獨立確認頁」其一——建議優先擴充 `confirm_delete.html` 為通用 `confirm_action.html`（零 JS、可無障礙、行動版友善），金額類動作可用小段漸進增強 JS 加 `data-confirm`（無 JS 時退回直送，因此後端應仍可接受）。可逆動作（標籤移除）以「復原」訊息取代確認即可。
- 價值 H　成本 M

**UX-05　`.alert.error` 被拿來顯示資訊性提醒；缺 warning／info**
- 位置：`project_line_settings.html:15`、`project_payment_settings.html:10`、`fake_checkout.html:6`、`project_jotform_settings.html:41`。
- 問題：「尚未實測」「開發用頁」與真正的錯誤同樣紅色，警示失效。
- 建議：設計系統新增 `--warning(-bg)`、`--info(-bg)` token 與 `.alert.warning`／`.alert.info`；亮／暗兩組都要過 4.5:1。
- 價值 M　成本 S

### P2：高頻流程體驗

**UX-06　當天點名在手機上難用（最常在現場用的畫面）**
- 位置：`project_attendance.html:27-55`（表格）、`views.py:1313-1314`（redirect 無錨點）、`base.html:90-94`（側欄堆疊）。
- 問題：(1) 手機要先捲過整個側欄；(2) 5 欄表格要橫向捲動才按得到「到場／未出席」；(3) 每按一次整頁重載回到頁首，名單長時每人都重新找位置；(4) 「提前參加」下拉選項過長。
- 建議：行動版將每位學員改成一張「卡片列」（姓名＋電話＋狀態標籤在上，按鈕在下且按鈕列滿版、≥44px）——純 CSS：`@media (max-width: 760px) { table, tbody, tr, td { display: block } }` 配 `data-label`；POST 後 redirect 帶 `#row-{student.id}`（view 層 1 行）並在列上加 `id`；頂部統計列改為 2×4 格，摘要置頂 sticky 顯示「實到／已報名」。在可見性上，把「臨時報名」「提前參加」折疊為 `<details>`。需在實機上驗證。
- 價值 H　成本 M

**UX-07　專案側欄在手機堆在內容之前**
- 位置：`base.html:90-94,115-125`。
- 建議：行動版把側欄收為 `<details class="sidenav-toggle"><summary>選單（目前：場次）</summary>…</details>`（純 HTML，不需 JS，鍵盤與讀屏皆可用），預設收合；桌面維持現狀。
- 價值 H　成本 S

**UX-08　表格行動版溢出**
- 位置：`project_detail.html:31`、`project_session_detail.html:25`、`project_students.html:18`、`project_products.html:14`、`project_jotform_submissions.html:27`、`manage_projects.html:28`、`manage_members.html:16`。
- 建議：不要逐檔補 `style="overflow-x:auto"`，改在 CSS 以 `.card:has(> table)`／新增 `.table-wrap` 類別統一處理，並在 `th` 加 `scope="col"`；欄數最多的 jotform_submissions（8 欄）與 payments（動作欄過寬）改用 UX-06 的卡片列模式。
- 價值 M　成本 S（統一包裹）

**UX-09　學員付款頁（pay.html，註：工作樹未提交變更）**
- 位置：`pay.html:28-45`、`pay_return.html`、`pay_transfer_done.html`、`views.py:947`。
- 問題：
  1. 無論選信用卡或轉帳，「轉帳資訊」卡（`:35-40`）與「末五碼」欄（`:41-44`）**永遠顯示**；選信用卡的人看到無關欄位，選轉帳的人要自己判斷「選擇轉帳時才填」。
  2. 送出鈕固定「確認付款方式」（`:45`），學員不知道按下後是跳去刷卡還是記錄轉帳；金額區塊與按鈕之間沒有總額摘要。
  3. 末五碼只在後端驗證（`views.py:914`），前端沒有 `pattern`／`required`，錯誤訊息出在頁首大紅條，沒有指向欄位。
  4. 沒有防連點；信用卡路徑連按可能建立多筆付款嘗試（`start_checkout`，交易編號有 36 次上限）。
  5. 單一選項時仍顯示 radio（`options` 只有一項）；`pay_return.html` 沒有「下一步」（例如「返回／聯絡方式」），`views.py:947` 金額無千分位。
  6. 失效連結（`views.py:866`）顯示 Django 預設英文 404。
- 建議：以 radio 的 `:checked` 搭配相鄰兄弟選擇器，或 5 行 JS，只在選「轉帳」時顯示轉帳資訊＋末五碼欄（無 JS 時全部顯示）並設 `required`、`pattern="[0-9]{5}"`、`inputmode="numeric"`；按鈕文案隨選擇切換為「前往刷卡付款」／「送出轉帳回報」；加 `data-submit-once`（見 UX-17）；錯誤以欄位旁文字＋`aria-describedby`；公開頁面自訂中文 404（UX-10）。pay.html 目前有使用者未提交變更，待其定稿後再改。
- 價值 H（對外頁面、關乎收款）　成本 M

**UX-10　沒有自訂 403／404／500 頁（無權限狀態、學員端失效連結）**
- 位置：全站；`views.py:166,185,866` 等 `PermissionDenied`／`Http404`；`src/` 內無 `403.html`、`404.html`、`500.html`。
- 問題：行政人員點到未授權專案、學員點到過期付款連結，都看到英文純文字頁，沒有導引。
- 建議：新增 `templates/403.html`、`404.html`、`500.html`（沿用 `base.html` 的 `.card.empty`）：403「你沒有權限查看這個頁面，請聯絡你的行政管理者」附回「我的專案」；404（公開付款頁用簡化版，不含導覽）；500「發生錯誤，請稍後再試」。
- 價值 M　成本 S

**UX-11　轉帳對帳要手抄末五碼，且沒有「待對帳」入口**
- 位置：`project_payments.html:71-88`；`dashboard.py`／`domain/dashboard.py`（待辦與異常皆無此項）。
- 問題：學員回報的金額與末五碼只顯示成提示，行政要手動抄進「備註」再按「確認入帳」；無法一眼找出待對帳的訂單。
- 建議：(1) 篩選新增「待對帳（有未核對回報）」；(2) 在回報提示旁提供「依此核對入帳」按鈕，預填金額與備註（末五碼）；(3) 儀表板待辦新增「N 筆轉帳待對帳」。(3) 涉及 domain 邏輯，需 PM 評估規格（見待釐清）。
- 價值 H　成本 M

**UX-12　空狀態沒有下一步、建專案後無導向、無權限無說明**
- 位置：`project_sessions.html:28`、`project_students.html:42`、`project_payments.html:116`、`project_session_detail.html:46`、`manage_projects.html:34,59`、`project_attendance.html`（講師唯讀無說明）、`project_detail.html`（講師少了待辦區無說明）。
- 問題：空狀態只有一句陳述；admin 建完專案沒有「前往專案」連結，專案名稱在管理表格不是連結。
- 建議：空狀態元件規格＝標題＋一句說明＋主要動作（例：「還沒有場次」→「新增第一個場次」按鈕錨點到表單；學員空→「匯入名單」）；有唯讀限制時顯示一行 `.alert.info`「你的角色可以查看，不能修改」；`manage_projects.html:34` 專案名稱連到專案頁。
- 價值 M　成本 S

**UX-13　付款對帳的動作欄過密**
- 位置：`project_payments.html:64-109`。
- 問題：單列最多同時出現付款連結、入帳（含金額）、退款（含金額＋備註）、取消訂單，四種動作用相同次要按鈕外觀，只有色彩以外的區分都沒有。
- 建議：動作欄改為主動作（依狀態：待收→「確認入帳」；已付→無）＋「更多」`<details>`（退款、取消訂單，標 danger）；付款連結旁加「複製」按鈕（重用 reports 的複製腳本，抽成共用 `_copy.js` include）。
- 價值 M　成本 M

**UX-14　新專案沒有設定完成度指引**
- 位置：`project_detail.html`、`project_nav.py:100-106`。
- 問題：一個專案要正常運作至少需完成：授權、前端課費用、付款設定、LINE 設定、Jotform 連結＋姓名／電話題確認、至少一個場次，分散在 5 個側欄項目；缺哪項只有在各頁自己的小警示（如 `project_front_course.html:11`、`project_notifications.html:11`）。
- 建議：在專案總覽（admin／行政管理者可見）加「設定進度」清單卡（每項狀態徽章＋連結）；全部完成後自動隱藏。
- 價值 M　成本 M（需 view 彙整狀態）

### P3：系統性收斂（設計系統）

**UX-15　把內嵌 CSS 與行內 style 收斂為設計系統**
- 位置：`base.html:7-96`；全站 133 處行內 `style=`（26 檔）。
- 問題：沒有 token（間距、字級、狀態色）、同一件事多種寫法（h2 兩種尺寸、`.badge` vs `.role`、flash 兩版、`margin-top: 28px` 對齊 hack 11 處）；textarea／checkbox 沒樣式；沒有 hover／focus／disabled 狀態。
- 建議（沿用純 Django template，不引新框架、不改視覺風格）：
  1. 不須設 `STATIC_ROOT`：把 CSS 拆成 `templates/crm/_styles.css`，在 `base.html` 以 `{% include %}` 引入 `<style>`，維持單檔部署；若日後要快取再改 static。
  2. 補 token：`--space-1..6`（4/8/12/16/24/32）、`--font-sm/md/lg/xl`（13/16/18/22）、`--radius-sm/md`（8/12）、`--warning/--info`、`--focus`。
  3. 補元件：`.btn.danger`、`.btn:disabled`、`.btn.sm`、`.stack`／`.cluster`（取代行內 margin）、`.h2` 統一 18px、`.badge.warn/.info`、`.form-actions`（取代 28px 對齊 hack：inline-form 改 `align-items: end`）、`.table-wrap`、`textarea`／`select`／checkbox 樣式、`.field-help`（渲染 `help_text`）。
  4. 將 `.role` 改回只用於角色，狀態一律 `.badge`。
  5. 逐步清除行內 style，每次改一個樣板時順手處理，不做一次性大改。
- 價值 M　成本 L（可分批；先做 token 與元件定義 S–M，樣板替換隨需求）

**UX-16　用語表與統一**
- 位置：見第 3.2 節。
- 建議：在設計系統「文案規範」建立用語表（前端課／進階課程／追售／待對帳／系統管理員；動詞：新增＝建立新紀錄、儲存＝保存表單、更新＝就地修改）；修正 `project_notifications.html:12`、`project_nav.py:87`、`project_products.html:9-10`、`project_front_course.html:10`、`project_jotform_settings.html:24,11`、`project_notifications.html:15` 的名稱；Docstring 與註解中的「銷講」「第一階段」順手改為「前端課」（`views.py:1291,1319`、`orders.py`、`reports.py:51`），並加一條測試或 CI grep 檢查「使用者可見字串不得含『銷講』」（憲法 MUST，目前無自動檢查）。另唯讀查詢既有資料庫是否仍有含「銷講」的標籤／範本。
- 價值 M（憲法要求）　成本 S

**UX-17　防連點與處理中狀態**
- 位置：`project_jotform_settings.html:78`、`project_payments.html:87,96`、`pay.html:45`、`project_attendance.html`（完成點名）。
- 建議：`base.html` 加 10 行共用 JS：表單 `submit` 時把 `button[type=submit]` 設為 `disabled` 並改為「處理中…」；對「立即同步」等耗時動作尤其重要。後端仍須保持冪等。
- 價值 M　成本 S

**UX-18　無障礙補強（一次做）**
- 位置：`base.html`。
- 建議：(1) 補「跳到主要內容」連結並給 `<main id="main">`；(2) 全域 `:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px }`；(3) 輸入框邊框改為滿足 3:1 的 `--border-strong`（亮約 #8a93a6）並保留 `--line` 作分隔；(4) `confirm_delete` 紅鈕改 `.btn.danger`，暗色用深色字或較深的紅底；(5) `.btn.link` 加 `min-height: 32px; padding: 4px 8px`（行動版 44px）；(6) 表單錯誤加 `aria-describedby`／`aria-invalid`（可由共用 `_field.html` partial 一次處理，見 UX-19）；(7) 複製按鈕結果加 `aria-live="polite"` 並處理 clipboard 失敗；(8) `th scope="col"`。
- 價值 M　成本 S–M

**UX-19　表單渲染抽成共用 partial**
- 位置：約 12 個樣板重複 `{% for field in form %}…label/field/errors…{% endfor %}`（`project_sessions.html:34-40`、`project_session_edit.html:11-17`、`project_student_edit.html:42-48`、`project_products.html:48-54`、`manage_members.html:7-13`、`project_line_settings.html:19-27`、`project_payment_settings.html:15-23`…）。
- 問題：`help_text` 不顯示、必填無標記、錯誤無 `aria-describedby`、checkbox 變形，要在每個檔重複修。
- 建議：新增 `crm/_field.html`（`{% include "crm/_field.html" with field=field %}`，渲染 label＋必填標記＋說明＋錯誤＋ aria 屬性，checkbox 走另一分支）；各頁逐步改用。
- 價值 M　成本 M

**UX-20　列表分頁與清單篩選補齊**
- 位置：`project_students.html`（SITEMAP 要求「搜尋／標籤篩選」，現只有搜尋）、`project_payments.html`、`project_jotform_submissions.html`、`project_sessions.html`（未分「即將／已結束」）、`views.py:1240`（通知紀錄靜默截斷 200 筆）。
- 建議：先為學員／付款／報名紀錄加 Django `Paginator`（每頁 50）與標籤篩選；場次列表分「即將開課」「已結束」並加狀態徽章（已結束／額滿）；截斷處顯示「僅顯示最近 200 筆」。
- 價值 M　成本 M

**UX-21　儀表板重排**
- 位置：`project_detail.html:7-27`、`project_list.html:12`。
- 建議：「今日待辦」置於統計卡之前；異常提醒獨立一張卡並用 `.alert.warning` 風格與圖示文字（「異常」）；待辦項附日期／類型標籤（課前 3 天／當天…）；專案列表上的異常數以 `.badge.bad` 顯示、待辦以 `.badge` 顯示，一眼辨識優先專案；講師看不到待辦時顯示說明。
- 價值 M　成本 S–M

**UX-22　導覽一致性**
- 位置：`base.html:100-111`（頂欄）、各頁麵包屑。
- 建議：麵包屑統一為「所有專案 / 專案名 / 區段 / 目前頁」並在有側欄的頁面精簡為只顯示上層（避免與側欄重複）；頂欄「系統管理」加目前頁樣式；單一專案使用者登入後可直接導到該專案（`views.py:131`，可選）。
- 價值 L　成本 S

## 6. 建議實作順序（給 PM）

1. 第一批（缺陷，都是 S）：UX-01、UX-02、UX-03、UX-10、UX-05、UX-16 的用語修正。
2. 第二批（誤操作與核心流程）：UX-04（先做通用確認頁＋`.btn.danger`）、UX-07、UX-08、UX-06、UX-17、UX-18。
3. 第三批（流程優化）：UX-09（待 pay.html 定稿）、UX-11、UX-12、UX-21、UX-13。
4. 第四批（收斂）：UX-15、UX-19、UX-20、UX-14、UX-22；UX-15 的 token 與元件定義建議在第二批之前就先寫進 `design/DESIGN_SYSTEM.md`（需使用者要求才由我撰寫，本次僅評估）。

涉及 view／domain 的項目（UX-06 錨點、UX-11、UX-14、UX-20、UX-21）走專案的「完整路線」（`/specify` 起）；純樣板／CSS 的項目（UX-01、02、03、05、07、08、10、17、18）符合「快速路線」資格（不改 model、單一行為）。以上由 PM 依 profile 判定。

## 7. 待釐清事項

1. 行政專員可否做轉帳入帳確認、退款、取消訂單？（`SITEMAP.md` 第 6 節仍待確認；樣板以 `can_edit`／`can_refund` 區分，但退款／取消的角色邊界會影響 UX-04、UX-13 的確認文案與按鈕可見性。）
2. 「待邀請出席」這一區在追售流程中的預期動作是什麼？目前只列名單、沒有按鈕，是功能缺口還是純資訊？（影響 UX-02 說明文字）
3. 成員管理只能新增、不能停用／改角色／重設密碼，是否已知缺口？（本次未列入建議）
4. 學員資料庫中是否仍有含「銷講」的標籤名稱、場次標題或自訂通知範本？需有權限者唯讀查詢確認（UX-16）。
5. `?date=YYYY-MM-DD` 覆寫「今天」的參數（`views.py:133,153`）是否保留在正式環境？若保留，畫面應標示「目前檢視日期」。
6. 學員付款頁是否要加品牌／客服聯絡方式（`pay_return.html`、`jotform_notice.html` 目前只說「請聯絡客服」卻沒有給聯絡方式）？
7. 手機使用情境的優先程度：現場點名是否主要用手機？決定 UX-06 要做到卡片列還是只做可捲動。
8. `pay.html` 的未提交變更內容與完成時間，確認後才排 UX-09。

## 8. 做得好的地方（保留）

- 每個 POST 都有具體文案的成功回饋；`jotform_notice.html` 五種情境的訊息清楚、語氣友善。
- 表格內聯表單有 `aria-label`；統計與狀態以文字標示不單靠顏色；`pay.html` 以 `fieldset/legend` 分組 radio、`role="alert"`。
- 側欄依權限只顯示可用項目、以 `aria-current="page"` 標示目前頁，並對「Jotform 報名紀錄」顯示待處理徽章。
- 刪除場次／學員有獨立確認頁並說明後果；Jotform 設定與 LINE／付款設定「密鑰儲存後不回顯、留白＝沿用」的模式清楚。
- 暗色模式隨系統切換、`<html lang="zh-Hant">`、`viewport` 與頁面標題（`{% block title %}`）都齊備。
