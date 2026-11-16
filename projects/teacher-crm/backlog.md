# Backlog：teacher-crm

> 由 `pm` 依 `assessment/` 四份報告建立與排序（2026-11-13），`project-manager` 更新「狀態」欄。
> 基線：master（HEAD `eb0a518`，工作樹乾淨，903 測試通過、覆蓋率 97%、品質關卡全綠；見 `assessment/quality.md`）。
> 規格套件編號從 `005` 起，由展開該項目的 `pm` 依序指定，本表不預先配號。
> 狀態欄註記（2026-11-17，`project-manager`）：B-004、B-005、B-027 資安與 QA 皆通過，標「完成」；狀態詞彙（待辦／規劃中／開發中／資安／QA／完成／擱置）沒有「待合併」一詞，故在括號註明「已 commit 於分支 t-<任務>，待使用者合併」。使用者合併前，與其重疊的後續項目仍不得開工（見 `work-plan.md`）。分支未 push、未合併。

來源縮寫：`sec`＝`assessment/security.md`（H／M／L 編號）；`arch`＝`assessment/architecture.md`（F／A／D／Q 編號）；`qa`＝`assessment/quality.md`（§4「補測 #n」、§5 規格疑義）；`ux`＝`assessment/ux.md`（UX-nn 或章節）。

## 本表建立時的核對（我自己讀過原始檔確認的事項）

| 項目 | 結果 |
|---|---|
| UX-01 | **確認屬實**：`project_student_edit.html:2` 的 `{% block title %}` 沒有關閉，標籤區（第 3–29 行）落在 `<title>` 內，第 30 行的 `{% endblock %}` 才關掉 title，`{% block content %}` 到第 31 行才開始。 |
| UX-02 | **確認屬實**：`project_follow_ups.html:35` 與 `:45` 都是 `<h2>待邀請出席…`。 |
| 現場報名「已現場收款」預設勾選 | **確認屬實**：`project_attendance.html:91` `<input type="checkbox" name="paid" checked>`（`ux` §2.3 提及，沒有 UX 編號，本表編為 B-006）。 |
| 發送重驗是否需要新狀態 | `OutboundMessage.Status.SKIPPED` 已存在（`models.py:499`），B-008 不必為此新增狀態。是否需新欄位記原因，展開時由 architect 確認。 |
| UX-16「加 CI 檢查舊稱」 | **已存在**：`tests/unit/test_wording.py` 已掃描 `src/crm` 的樣板與 Python 字串（排除 docstring、`retagging.py`、migrations）。所以 B-039 不新增檢查，只修用語與 docstring；資料庫內資料是否含舊稱仍待 Q13。 |
| `pay.html` 未提交變更 | 已隨 `eb0a518` 提交；`ux` 以「待定稿」為由保留的 UX-09 排程限制已解除。 |

## 共通規則（適用每個項目）

**共通回歸範圍（每項交付都必須維持）**：`make lint`、`make test`（903 項不得變少或被改弱）、`make manage cmd="check"`、`make manage cmd="makemigrations --check --dry-run"`、覆蓋率 ≥ 95%、`make codemap-check` 無 STALE；憲法 10 條 MUST（尤其 #4 隔離、#5 伺服器端權限、#8 金額整數與機密不回顯、#9 通知冪等）；公開端點既有驗簽與冪等；任何新功能附「A 專案讀不到 B 專案」測試。各項「不得改變」只列該項特有的，不重複本段。

**路線判準（依 `profile.md` 與 `/quickfix` Rule 1）**：快速路線須同時成立：1–3 個預期行為、不改 `models.py`（含欄位、型別、約束、`choices`、`on_delete`）、不新增 URL／頁面／外部整合／排程、不改權限規則、不推翻既有 FR。表中標「快速（候選）」＝依本表判斷符合，但最終由 `/quickfix` Phase 1 資格判定，不符即轉完整路線。

**路線的限制**：工程師遇到前置產物缺失就停（`engineer-rules.md` §1）；標「待決：Qx」的項目在使用者回答前，不得進入 `/specify`／`/quickfix` 之後的實作。

## 建議先做（前 5 項）

排序依據：高風險資安與涉及金額者優先（嚴重度），其次價值高、成本低、風險低。前 5 項都不需要使用者先回答才能開始（B-003 需要一個外部確認動作，見下）。

| 順位 | ID | 標題 | 理由 |
|---|---|---|---|
| 1 | **B-001** | 設定預設改為「失敗即拒絕」＋compose 傳參＋啟動檢查（sec H-1） | 整體資安結論「不通過」的兩個高風險之一；預設值公開 → 付款連結可偽造、金流／LINE 憑證形同明文。修法是設定面，無資料變更。**使用者要另做的運維動作**（確認正式環境是否曾以預設值運作；若是，輪替 SECRET_KEY 並重新輸入各專案金流／LINE 憑證）見 Q7。 |
| 2 | **B-002** | 假金流付款繞過（sec H-2） | 另一個高風險：持付款連結者可不付錢變成已付款並佔位。與 B-001 同一位工程師依序做（都動 `settings.py`、`forms.py`），B-002 本身符合快速路線，半天內可完成。 |
| 3 | **B-003** | 金流「失敗」通知把付款嘗試鎖成終態（sec M-4） | 涉及金額：失敗通知先到、成功通知後到時，學員被扣款但訂單不入帳，且金流端已停止重送。**先確認再動工**：由使用者向綠界／藍新確認「同一商店訂單編號失敗後可否重試」（Q8）；確認前可先寫重現測試。本項目不依賴其他項目，確認後屬快速路線候選。 |
| 4 | **B-004** | 學員編輯頁標籤區被塞進 `<title>`（ux UX-01） | 我已讀檔確認：標籤功能在畫面上完全消失，連帶切斷「改期」標籤入口（每月 1–5 號改期 SOP）。成本 S（補一個 `{% endblock %}` 與搬移區塊）、風險低、價值高。 |
| 5 | **B-008** | 發送前條件重驗＋完款提醒去重（憲法 MUST 10；arch F-3／A-2、sec M-8） | 憲法 MUST 落差，直接影響客戶體驗（已付款者仍收到付款提醒、已報進階者仍被追售）。規則由憲法已定義，不需使用者決定；`SKIPPED` 狀態已存在，預期不改 model。成本 M。 |

第 6–8 順位的「順手快贏」（同為樣板小修，與 B-004 同一位工程師接續做，成本都是 S）：B-005（追售名單重複段落）、B-006（現場報名預設勾選已收款，涉及金額記錄）、B-007（錯誤訊息被畫成綠色成功條）。

## 項目

> ID 順序＝同層級內的建議優先序（資安／金額／憲法落差在前，結構性重構在最後）。
> 「依賴」欄：`待決：Qx`＝需使用者先回答（見「待使用者決定」）；`B-xxx`＝需先完成的項目；`衝突：…`＝與其他項目共用檔案，不可平行。

| ID | 類型 | 標題 | 來源 | 價值 | 成本 | 風險 | 依賴 | 路線 | 狀態 |
|---|---|---|---|---|---|---|---|---|---|
| B-001 | 資安 | 設定預設改為失敗即拒絕、compose 傳入機密、啟動檢查、移除加密金鑰退回 SECRET_KEY | sec H-1；arch F-8、F-9（前半）、D-5、A-6（前半） | 高 | M | 中（預設值改變；開發／CI／既有部署需明確提供變數） | 待決：Q7（運維確認，不阻擋程式修改）；衝突：settings.py、crypto.py、compose.yaml | 完整（涉及 settings、crypto、compose、CI、`.env.example` 多個介面；可用精簡 spec） | 待辦 |
| B-002 | 資安 | 假金流在 `FAKE_GATEWAY_ENABLED` 關閉時不可用，且要求非空 HashKey | sec H-2 | 高 | S | 低 | 依序在 B-001 後（同一位工程師）；衝突：settings.py、forms.py、checkout.py | 快速（候選）：3 個預期行為、不改 model | 待辦 |
| B-003 | 缺陷 | 金流失敗通知不得把付款嘗試鎖成終態（先失敗後成功要能入帳） | sec M-4；qa 補測 #3（並行與重複通知測試，相關） | 高 | S–M | 中（金額；改狀態機） | 待決：Q8；衝突：checkout.py（與 B-013、B-030） | 快速（候選）：單一狀態機行為、不改 model；若現行 FR 明定「失敗為終態」則是改 FR，轉完整 | 待辦 |
| B-004 | 缺陷 | 學員編輯頁標籤區落在 `<title>` 內，補閉合並搬到內容區 | ux UX-01 | 高 | S | 低 | 衝突：project_student_edit.html（與 B-007） | 快速（候選）：單一樣板、不改 model | 完成（已 commit 於分支 t-B-004，待使用者合併） |
| B-005 | 缺陷 | 追售名單「待邀請出席」整段重複 | ux UX-02 | 高 | S | 低 | 衝突：project_follow_ups.html（與 B-007）；說明文字部分待決：Q11（不阻擋去重） | 快速（候選） | 完成（已 commit 於分支 t-B-005，待使用者合併） |
| B-006 | 缺陷 | 現場報名「已現場收款」不得預設勾選 | ux §2.3（`project_attendance.html:91`） | 中高 | S | 低（若 TEST_LIST／規格明定預設勾選則為改規格，展開時 pm 查證） | 衝突：project_attendance.html（與 B-046） | 快速（候選） | 待辦 |
| B-007 | 缺陷 | 訊息元件統一：錯誤不再畫成綠色成功條、`role` 正確、補 warning／info 樣式 | ux UX-03、UX-05 | 高 | S | 低–中（約 20 個樣板同時改；訊息漏顯或重複顯示） | 在 B-004、B-005、B-006 之後；衝突：base.html 與約 20 個樣板（與 B-041、B-042、B-043、B-051、B-054 同一位工程師序列） | 快速（候選）：行為單一（訊息呈現）、不改 model | 待辦 |
| B-008 | 補完 | 對外發送前重新檢查條件（憲法 MUST 10）：重送、`PENDING` 殘留、迴圈中被停止、完款提醒連點去重 | arch F-3、A-2、D-3、F-11（第 2 項）；sec M-8 | 高 | M | 低–中（改既有發送流程；若需新欄位記錄略過原因則動 model） | 衝突：line/notifications.py（與 B-011、B-032、B-055 序列：先 B-008）；若需新欄位排入 model 通道 | 完整（多個發送路徑、多故事；僅修 `retry_message` 單一路徑時可轉快速） | 待辦 |
| B-009 | 資安 | LINE webhook 驗簽在 channel secret 為空時必須失敗；非 LINE 模式不處理外部事件 | sec L-1 | 中 | S | 低 | 衝突：domain/line.py、views.py（小範圍） | 快速（候選） | 待辦 |
| B-010 | 補完 | 有收款紀錄的學員不得被刪除（保住財務紀錄） | arch F-4、A-3、D-4；sec M-5（後半） | 高 | S（禁止刪除）／M（軟刪除或 `PROTECT`，需 migration） | 中 | 待決：Q3；衝突：views.py、models.py（僅 PROTECT／軟刪除方案） | 禁止刪除且不改 model → 快速（候選）；改 FK／軟刪除 → 完整 | 待辦 |
| B-011 | 補完 | 每日 job 納入內建排程（課前通知、結束場次與追售），含漏跑補發與設定頁狀態 | arch F-1、A-1、D-1；arch F-11（JobRun）；sec 資訊（scheduler raw SQL 註解） | 高 | M | 中（改變發送時機；部署端 cron 可能雙跑，唯一約束可擋） | 待決：Q2；B-008（先做發送重驗）；衝突：scheduler.py、line/notifications.py | 完整（新增排程工作；含 `/clarify`：執行時間、時區、補發窗口） | 待辦 |
| B-012 | 補完 | 場次名額規則釐清並以資料庫鎖落實，所有報名路徑口徑一致 | arch F-2、A-4、D-2；sec M-6；qa 補測 #3 | 高 | M–L | 中高（涉及付款流程與 Jotform 時序，改錯會擋住正當付款；新增 `session_full` 原因會改 `choices` → migration） | 待決：Q1；model 通道；衝突：jotform/registration.py、importer.py、attendance.py、rescheduling.py、orders.py、domain/jotform_options.py、dashboard.py、views.py | 完整（先 `/clarify`） | 待辦 |
| B-013 | 補完 | 付款待處理清單：「已扣款未入帳」與「轉帳待對帳」進儀表板待辦／異常與付款頁篩選 | arch A-5、D-14、§4.2（SITEMAP 付款段缺口）；ux UX-11 | 高 | M | 低 | 待決：Q10（確認入帳的角色邊界）；B-003（同動 checkout.py，先做）；衝突：dashboard.py、domain/dashboard.py、project_payments.html、views.py（與 B-040、B-048、B-049） | 完整（新增異常項、篩選與按鈕行為，跨多個故事） | 待辦 |
| B-014 | 資安 | 公開端點與登入入口濫用防護：`jotform_return`／`jotform_webhook`／`pay_page` POST 節流、轉帳回報與付款嘗試上限、登入失敗鎖定、`/admin/` 不公開 | sec M-1（建議 1）、M-3（節流與 /admin/）、L-2；arch A-7、F-8 | 高 | M | 低–中（節流參數太嚴會擋到正常學員） | 衝突：settings.py（cache 設定）、views.py、urls.py；若採資料庫計數表 → 動 model（建議改用 DB cache 的 `createcachetable`，不產生 migration，由 architect 定） | 完整（新機制、多個入口） | 待辦 |
| B-015 | 資安 | `jotform_return` 流程收斂：不認得的提交不打外部、request 內不再 `sleep` 重試、已有訂單的導向仍受時效或二次驗證約束 | sec M-1（建議 2–4）；arch F-5 | 中高 | M | 中（改 004 既定行為；可能影響學員導向體驗） | 待決：Q18；B-014（共用節流機制，先做）；衝突：jotform/registration.py、views.py（與 B-012、B-057） | 完整（改 004 的 FR，先 `/clarify`） | 待辦 |
| B-016 | 資安 | 正式環境部署硬化：production 啟動方式（gunicorn、不含 dev 依賴、非 root）、LOGGING、cookie／HTTPS／HSTS／代理標頭、連結一律以 `SITE_BASE_URL` 組出、`check --deploy` 進 CI | sec M-2、L-6；arch F-8、A-6（後半） | 高（上線前必備） | M | 低–中（部署行為改變） | 待決：Q7；B-001；衝突：settings.py、Dockerfile、compose.yaml、ci.yml、views.py（僅兩行 `build_absolute_uri`） | 完整（新增執行環境與設定） | 待辦 |
| B-017 | 資安 | 加密金鑰管理：`MultiFernet` 輪替、重新加密 command、解密失敗不再 500 | sec L-5；arch F-9、A-9、D-7 | 中 | M | 中（弄錯會讓既有憑證不可解；需備份與演練） | B-001（先做；同動 crypto.py）；衝突：crypto.py、views.py（`pay_page`、`line_webhook`） | 完整（新增 command） | 待辦 |
| B-018 | 資安 | 依賴與供應鏈：`cryptography` 升版、CI 加 `pip-audit`、ruff 加入 `S` 規則 | sec M-9、§6；arch（requirements 僅三項） | 中 | S–M | 低–中（升版需全測；`S` 規則可能掃出既有問題） | 待決：Q19（掃描需可連網環境，不得自行對外查詢）；衝突：requirements.txt、ci.yml、pyproject.toml | 快速（候選，僅升版與規則）；新增 CI 工作流屬 001 規格範圍 → 該部分轉完整 | 待辦 |
| B-019 | 資安 | 成員管理補完：停用／啟用成員、重設密碼、（視範圍）改角色 | sec M-3（後半）；ux §2.6、待釐清 3 | 中高 | M | 低 | 待決：Q12；衝突：views.py（manage_members）、forms.py | 完整（新增操作與頁面） | 待辦 |
| B-020 | 資安 | LINE 綁定強化：第二因子或嘗試次數限制，失敗回覆統一 | sec M-7 | 中 | M–L | 中（改學員綁定流程，是產品決策） | 待決：Q9；model 通道（若新增綁定碼）；衝突：line/service.py、models.py | 完整（`/clarify` 先行） | 待辦 |
| B-021 | 資安 | 專案停用後，公開入口與排程不再運作 | sec L-7 | 中 | M | 中（停用語意若誤判會停掉營運中專案） | 待決：Q17；衝突：views.py、scheduler.py、line/notifications.py、jotform/sync.py | 完整（跨多個入口與排程；改變行為語意） | 待辦 |
| B-022 | 資安 | 機器對機器端點回應統一與標頭硬化：統一回應、`no-store`、CSP、webhook 密鑰不進存取日誌 | sec L-3、L-8 | 低–中 | S–M | 低–中（CSP 可能擋到內嵌 script；密鑰移標頭需 Jotform 支援） | 衝突：views.py、base.html、settings.py | 完整（多介面）；僅統一回應一項可拆成快速 | 待辦 |
| B-023 | 資安 | 講師可見付款頁範圍收斂（若使用者決定限制） | arch Q4、§3 F-6；sec §3 #5（講師可見付款清單與末五碼） | 中 | S | 低 | 待決：Q4；衝突：domain/permissions.py、views.py | 改權限規則 → 完整（`/quickfix` Rule 1-4 不符） | 待辦 |
| B-024 | 補完 | 財務操作者稽核：`Payment.created_by`，收款、退款、取消、刪除、價格與金流設定異動留操作者 | arch F-8、A-8、D-6；sec M-5（前半） | 中高 | M | 低（加可為空的欄位） | model 通道（第一位）；衝突：models.py、orders.py、views.py | 完整（改 model） | 待辦 |
| B-025 | 補完 | 名單匯入加檔案大小與列數上限，超長欄位給友善錯誤 | sec L-4 | 低–中 | S | 低 | 衝突：importer.py、views.py（單一區段） | 快速（候選） | 待辦 |
| B-026 | 缺陷 | 現場報名、提前報到、建立訂單的併發重複操作回友善訊息而非 500 | arch F-11（第 1 項）；sec §4 競態（`create_order` 先查再建） | 中 | S | 低 | 衝突：attendance.py、orders.py（與 B-012） | 快速（候選） | 待辦 |
| B-027 | 補完 | 補測：金流回報解析異常路徑（藍新／綠界） | qa 補測 #1 | 高 | S | 低 | — | 快速（候選，僅補測；若測出缺陷則另開缺陷項） | 完成（已 commit 於分支 t-B-027，待使用者合併） |
| B-028 | 補完 | 補測：金額與前端課／金流設定驗證（訂金、價格、藍新 HashKey／IV、人工建單無前端課費用） | qa 補測 #4 | 高 | S | 低 | — | 快速（候選，僅補測） | 待辦 |
| B-029 | 補完 | 補測：專案隔離守門——缺口路由的跨專案測試＋`Registration/Order/Payment/Attendance` 專案一致性巡檢測試 | qa 補測 #2；arch F-6、D-10、A-12（後半）；憲法 MUST 4 | 高 | M | 低 | — | 快速（候選，僅補測）；若加定期資料健檢 command 則另列為建議 S2 | 待辦 |
| B-030 | 補完 | 補測：並行測試（改期搶最後名額、同筆付款通知重複送達、同時兩次確認收款、連點完款提醒） | qa 補測 #3；arch D-13、A-12（前半） | 中高 | M | 低 | 建議與 B-012 同期（名額相關案例在 B-012 完成後補）；B-003、B-008 完成後補對應案例 | 完整（需 testplan 設計）；單一案例補洞可快速 | 待辦 |
| B-031 | 補完 | 補測：webhook 建單 → LINE 綁定 → 付款提醒串接（004 FR-018） | qa 補測 #5 | 中高 | M | 低 | B-008（發送流程若已改，案例以改後為準） | 快速（候選，僅補測） | 待辦 |
| B-032 | 補完 | 補測：LINE 外送路徑（重試上限、無設定重送、付款提醒略過／失敗計數、非法 webhook body、停用帳號重綁、手動綁定衝突） | qa 補測 #6 | 中高 | S–M | 低 | B-008、B-009（先完成，避免補了舊行為） | 快速（候選，僅補測） | 待辦 |
| B-033 | 補完 | 補測：排程指令非法參數、同日有開始時間的前後場次判斷、略過已處理提交、立即同步無金鑰／無表單提示 | qa 補測 #8、#9、#10 | 中 | S | 低 | — | 快速（候選，僅補測） | 待辦 |
| B-034 | 優化 | 啟用分支覆蓋率並量新基線；`make coverage` 帶與 CI 一致的門檻 | qa 補測 #7、§5 第 2 點 | 中高 | S | 低（啟用後總覆蓋可能低於 95%，**不得為過關降低門檻**） | 衝突：pyproject.toml、Makefile、ci.yml（與 B-018） | 快速（候選） | 待辦 |
| B-035 | 補完 | integration 層擴充（藍新測試站、Jotform 真實行為、LINE `get_quota`／push） | qa 補測 #11；arch Q6 | 中 | L | 中（連真實外部服務） | 待決：Q6（需使用者授權與測試帳號，工程師不得自行執行 `make test-integration`） | 完整 | 待辦 |
| B-036 | 重構 | 測試衛生：`test_jotform_session_hooks.py:98` 的 `sync_form` monkeypatch 改為 fake client 注入例外 | qa 補測 #13、§2 憲法 2 | 低 | S | 低 | 衝突：該測試檔 | 快速（候選） | 待辦 |
| B-037 | 文件 | 規格狀態欄與 SITEMAP 校正（001／003／004 狀態、002 撤回標記、公開端點清單、已做／未做標示、錯字、CASCADE 理由說明、`TDD_PROGRESS`／`TEST_LIST` 標示歷史與重複標題） | arch §4.1、§4.2、A-13、D-12、F-11（末項）；qa §5 第 1、3 點、§3 TEST_LIST；qa §1（validate 警示） | 中 | S | 無 | 部分待決：Q5（四個缺頁標「做」或「不做」）；與 B-038 同由 pm 處理，序列 | 快速（文件、不改 model） | 待辦 |
| B-038 | 文件 | 004 收尾：關閉 integration-plan 3 個 `[NEEDS CLARIFICATION]`、`JOTFORM_TIMEZONE` 預設值回寫規格、`origins.py` CSRF 來源補規格段落、NFR-001／SC 上線後監控項 | arch §4.1（004 列）、F-5；qa §1、§3（004）、§5 第 1、4 點；sec §0 | 中 | S–M | 低 | 待決：Q6；B-035（真實實測結果） | 快速（文件）；若實測改變 FR → 轉完整（`/specify` 修訂 004） | 待辦 |
| B-039 | 補完 | 用語統一：側欄／頁面／提示的名稱互相對得上、角色名不外洩英文、動詞統一、docstring 舊稱、`NT$` 千分位 | ux UX-16、§3.2、§3.1 | 中（憲法要求） | S | 低 | 待決：Q13（資料庫舊稱查詢，不阻擋程式碼用語修正）；衝突：project_nav.py、多個樣板、views.py（docstring 與一行字串） | 快速（候選）；動導覽文字不改權限 | 待辦 |
| B-040 | 優化 | 危險／不可逆操作統一確認：通用確認頁、`.btn.danger`，涵蓋入帳、退款、取消、完成點名、停用專案、略過報名、移出場次、停止追售 | ux UX-04、§2.2、§2.3 | 高 | M | 中（新增確認流程；動金額操作） | 待決：Q10；B-007；衝突：views.py、project_payments.html、多個樣板（與 B-013、B-048） | 完整（新增確認頁面與多個 view 行為） | 待辦 |
| B-041 | 優化 | 手機版共用版面：專案側欄收合、表格溢出統一包裹 | ux UX-07、UX-08 | 高 | S | 低 | 衝突：base.html（序列於 B-007 後）、project_students／products／jotform_submissions／detail 等表格樣板 | 快速（候選，純 CSS／樣板） | 待辦 |
| B-042 | 優化 | 防連點與處理中狀態（表單送出後按鈕停用） | ux UX-17 | 中 | S | 低（需保持後端冪等） | 衝突：base.html | 快速（候選） | 待辦 |
| B-043 | 優化 | 無障礙補強：跳到主內容、`:focus-visible`、輸入框邊框對比、暗色危險鈕對比、`.btn.link` 點擊區、`scope`、複製按鈕 `aria-live` | ux UX-18、§4.1 | 中 | S–M | 低 | 衝突：base.html、多個樣板 | 完整（超過 3 個預期行為；可拆成數個快速項） | 待辦 |
| B-044 | 優化 | 自訂 403／404／500 頁（含學員端失效付款連結的中文簡化版） | ux UX-10、§4.3 | 中 | S | 低 | 衝突：urls.py（handler）、新樣板 | 快速（候選）；若被判為「新增頁面」則完整 | 待辦 |
| B-045 | 優化 | 學員付款頁：選轉帳才顯示轉帳資訊與末五碼、按鈕文案隨選擇切換、前端驗證、錯誤指向欄位、防連點 | ux UX-09 | 高 | M | 中（對外收款頁；改互動） | B-014（`pay_page` 節流）、B-042、B-044；衝突：pay.html、views.py（`pay_page`） | 完整（多個互動行為；`pay.html` 已提交，不再有進行中變更限制） | 待辦 |
| B-046 | 優化 | 當天點名的手機版：卡片列、點名後回到原位置、提前參加與臨時報名收合 | ux UX-06、§2.3 | 高 | M | 低–中 | 待決：Q16；B-041、B-006；衝突：project_attendance.html、views.py（redirect 錨點） | 完整（view 層錨點＋版面） | 待辦 |
| B-047 | 優化 | 空狀態有下一步、建專案後導向、唯讀角色說明 | ux UX-12、§2.1、§2.5 | 中 | S | 低 | B-041、B-051（空狀態元件）；衝突：多個樣板（students、sessions、payments、manage_projects 等） | 快速（候選） | 待辦 |
| B-048 | 優化 | 付款對帳動作欄收斂：主動作＋「更多」、付款連結複製 | ux UX-13 | 中 | M | 低 | B-013、B-040（同動 project_payments.html，序列） | 完整 | 待辦 |
| B-049 | 優化 | 儀表板重排：今日待辦置前、異常獨立並著警示色、專案列表異常徽章 | ux UX-21、§2.5 | 中 | S–M | 低 | B-013（同動 dashboard，序列）；待決：Q14（`?date=` 標示） | 完整（涉及 view／domain） | 待辦 |
| B-050 | 優化 | 專案設定完成度指引卡 | ux UX-14、§2.1 | 中 | M | 低 | 衝突：views.py（`project_detail`）、project_detail.html（與 B-049） | 完整 | 待辦 |
| B-051 | 優化 | 設計系統收斂（一）：token（間距、字級、狀態色、focus）、元件類別（`.btn.danger`、`.table-wrap`、`.form-actions`、textarea／checkbox 樣式、`.badge` 取代 `.role` 挪用）；樣板行內 style 隨改隨清 | ux UX-15 | 中 | M（定義）＋隨需求替換 | 低 | 衝突：base.html（序列於 B-007、B-041、B-042、B-043）；設計規範文件位置由 uiux-designer 於 `/ui-plan` 決定 | 完整（設計系統屬 `/ui-plan`，由 `uiux-designer`） | 待辦 |
| B-052 | 優化 | 設計系統收斂（二）：共用 `_field.html`（必填標記、`help_text`、錯誤 `aria-describedby`、checkbox 分支），逐頁改用；登入頁顯示欄位錯誤 | ux UX-19、§4.1、§1.4（表單） | 中 | M | 低 | B-051；衝突：約 12 個樣板 | 完整 | 待辦 |
| B-053 | 優化 | 列表分頁與篩選、儀表板載入量：學員／付款／報名紀錄分頁，學員標籤篩選（SITEMAP 要求），場次狀態與分組，通知紀錄 200 筆截斷提示，儀表板不再全量載入、重複成員查詢精簡 | ux UX-20、§2.1；arch F-10（儀表板列）、F-11（分頁、`visible_to` 重複查詢）、§6 瓶頸 1 | 中 | L | 中（動多個列表與儀表板查詢） | B-013、B-049（同動 dashboard）；衝突：views.py、dashboard.py、多個樣板 | 完整（建議展開時再拆 2–3 個 package） | 待辦 |
| B-054 | 優化 | 導覽一致性：麵包屑統一、頂欄目前頁樣式 | ux UX-22、§1.4（導覽） | 低 | S | 低 | 衝突：base.html、多個樣板 | 快速（候選） | 待辦 |
| B-055 | 優化 | request 內外部呼叫改為 outbox：request 只建立 `PENDING`，由排程發送 | arch F-7、A-10（前半）、§6 瓶頸 3 | 中 | M–L | 中（互動由「立即看結果」變「稍後顯示」） | 待決：Q7（急迫度）；B-008、B-011；衝突：line/notifications.py、views.py | 完整（需 UIUX 與 pm 共同確認） | 待辦 |
| B-056 | 補完 | SITEMAP 原定頁面：學員詳情彙整頁、跨專案總覽（及其獨立權限）、金流回報紀錄頁、排程時間規則設定——僅限使用者確認「仍要做」者 | arch §4.2、A-14、Q5 | 中 | M–L | 低 | 待決：Q5；B-013（金流回報紀錄頁與待處理清單邊界）；衝突：views.py、permissions（跨專案總覽） | 完整（`/specify`＋`/ui-plan`） | 待辦 |
| B-057 | 優化 | 放寬 Jotform `OTHER_SESSION` 規則（只比對未結束場次） | arch F-5、A-15 | 中 | S | 中（可能把重複報名自動建單） | 待決：Q20；需先蒐集 `JotformSubmission.reason` 分佈；衝突：jotform/registration.py（與 B-012、B-015） | 完整（改 004 的 FR，先 `/clarify`） | 待辦 |
| B-058 | 重構 | Jotform 傳輸層抽成共用模組（解除 `jotform/client.py` 對 `line/client.py` 的依賴） | arch F-1.2（觀察 2）、D-9、A-11（附帶） | 低 | S | 低 | 衝突：jotform/client.py、line/client.py | 快速（候選，純搬移、行為不變）；若被判非 bug 不適用則走精簡完整路線 | 待辦 |
| B-059 | 重構 | `ProjectForm.save`、`MemberForm.save` 的建立邏輯下沉到服務層 | arch F-10（forms 列）、D-8 | 低 | S | 低 | 在 B-002、B-019 之後；衝突：forms.py | 精簡完整路線（純重構，以 tasks 清單） | 待辦 |
| B-060 | 重構 | `views.py` 拆成 `views/` 套件（純搬移、行為不變）；業務判斷下沉服務層 | arch F-10、A-11、D-8 | 中 | M | 低（行為不變；大量衝突） | **排在所有碰 views.py／urls.py 的項目之後**（見「檔案與 model 衝突」）；之後必須 `make codemap` | 精簡完整路線（單一 package，tasks 清單；不適用快速路線，因非 bug 修正） | 待辦 |

類型：缺陷 / 補完 / 優化 / 重構 / 資安 / 文件
成本：S（半天內）/ M（1–3 天）/ L（更久）
路線：依 profile 的路線判準（完整 / 快速）

### 項目數量統計

共 60 項：資安 13（B-001、002、009、014–023）、缺陷 6（B-003–007、026）、補完 17（B-008、010–013、024、025、027–033、035、039、056）、優化 18（B-034、040–055、057）、重構 4（B-036、058、059、060）、文件 2（B-037、038）。

逐項清點：資安＝B-001、002、009、014、015、016、017、018、019、020、021、022、023；缺陷＝B-003、004、005、006、007、026；補完＝B-008、010、011、012、013、024、025、027、028、029、030、031、032、033、035、039、056；優化＝B-034、040–055（16 項）、057；重構＝B-036、058、059、060；文件＝B-037、038。合計 13＋6＋17＋18＋4＋2＝60。

## 待使用者決定

下表是開工前需要使用者回答的問題。**Q1–Q7 來自 `architecture.md` §8（編號沿用）；Q8–Q20 由本 backlog 從 security、ux、quality 的「待確認／待釐清」整理而來**。回答前，標「待決」的項目不得進入實作。

| # | 問題 | 來源 | 影響項目 |
|---|---|---|---|
| Q1 | 場次名額：「已報名人數」還是「已付款人數」占名額？允許超收嗎（目前實際允許並事後告警）？現場報名、提前報到是否永遠不受限（目前是）？不受限的話要在規格或憲法註記為例外嗎？ | arch Q1 | B-012、B-030（名額案例）、B-026（部分） |
| Q2 | 部署上 `send_line_notifications`、`process_finished_sessions` 目前由誰在跑（主機 cron、手動、還是沒人跑）？每日要幾點跑？漏跑一天後是否要補發？補發最多回溯幾天？ | arch Q2 | B-011、B-055（部分） |
| Q3 | 已有收款的學員可否被刪除？期望「禁止」「軟刪除（封存）」還是「允許但留稽核紀錄」？ | arch Q3 | B-010（決定快速或完整、是否動 model）、B-024（刪除稽核範圍） |
| Q4 | 講師是否應看到付款頁（訂單金額、付款狀態、轉帳末五碼）？目前講師可唯讀。 | arch Q4；sec §3 #5 | B-023 |
| Q5 | SITEMAP 的「跨專案總覽」「學員詳情頁」「排程時間規則設定」「金流回報紀錄頁」仍要做，還是正式列為不做？ | arch Q5 | B-056、B-037（文件寫法）、B-013（邊界） |
| Q6 | `JOTFORM_TIMEZONE` 預設 `America/New_York` 是否為最終決定（要回寫規格 004）？004 上線前以真實 Jotform 實測的項目（導向與 webhook 實際欄位、免費方案、答案形狀、時區、藍新編號限制）是否已完成？是否授權之後執行真實連線測試並提供測試帳號？ | arch Q6；qa §1、補測 #11 | B-038、B-035、B-037 |
| Q7 | 是否已有正式環境？流量與專案數量？**曾否以預設值運作**（預設 SECRET_KEY、DEBUG 開、假金流開）？若是，需視為已外洩並輪替 SECRET_KEY、重新輸入各專案金流與 LINE 憑證；前面是否有 HTTPS 反向代理（`25cb607` 暗示有 ngrok／負載平衡器）？ | arch Q7；sec H-1 第 4 點、M-2 | B-001（運維動作）、B-016、B-017（重新加密）、B-055 |
| Q8 | 綠界、藍新對「同一商店訂單編號失敗後重試」的實際行為：失敗通知之後，同單號是否還會送成功通知？（由使用者向金流商確認或授權沙盒驗證） | sec M-4（待確認） | B-003、B-013（長時間 CREATED 的異常判斷）、B-030 |
| Q9 | LINE 綁定要採用哪種方式強化：報名時產生的一次性綁定碼、嘗試次數限制，還是維持姓名＋電話（接受風險）？失敗回覆文字是否統一？ | sec M-7 | B-020 |
| Q10 | 行政專員可否做轉帳確認入帳、退款、取消訂單？（SITEMAP 第 6 節仍待確認；目前以 `EDIT_DATA`／`MANAGE_REFUNDS` 區分，樣板另有 `can_refund`。）待辦區是否也要顯示給行政專員？ | ux 待釐清 1 | B-013、B-040、B-048 |
| Q11 | 追售名單的「待邀請出席」這區預期動作是什麼？現在只列名單沒有按鈕——是功能缺口（要加動作）還是純資訊（只補說明）？ | ux 待釐清 2 | B-005（說明文字部分；去重不受影響） |
| Q12 | 成員管理只能新增、不能停用、改角色、重設密碼——要補嗎？要補到什麼範圍（僅停用／加重設密碼／加改角色）？離職人員目前只能改資料庫。 | ux 待釐清 3；sec M-3 | B-019 |
| Q13 | 資料庫中是否仍有含「銷講」「初階課程」「第一階段」的學員標籤名稱、場次標題或自訂通知範本？（需有權限者唯讀查詢；工程師不得讀 `.env` 或自行連正式庫。） | ux 待釐清 4 | B-039（資料修正需另行決定是否納入） |
| Q14 | `?date=YYYY-MM-DD` 覆寫「今天」的參數在正式環境是否保留？若保留，畫面要標示「目前檢視日期」。 | ux 待釐清 5 | B-049 |
| Q15 | 付款頁與提示頁（`pay_return.html`、`jotform_notice.html`）說「請聯絡客服」，要不要補客服聯絡方式與品牌？內容由誰提供？ | ux 待釐清 6 | B-045（文案）、B-044（404 頁導引） |
| Q16 | 現場點名是否主要用手機？決定 B-046 做到卡片列，還是只做橫向可捲動。 | ux 待釐清 7 | B-046、B-041 |
| Q17 | 專案「停用」的語意是什麼：只是從內部畫面隱藏，還是要停止營運（付款頁、金流／LINE／Jotform 入口與排程全部停）？ | sec L-7 | B-021 |
| Q18 | 004 的既定設計「已有訂單的提交編號可重複導向、不再檢查時效」是否保留？要改成「仍檢查時效」或「須姓名＋電話後 4 碼」嗎？不認得的提交編號是否改為「查無，不打 Jotform」（需 webhook 先建佔位列）？ | sec M-1（建議 2、4）；arch F-5 | B-015 |
| Q19 | 是否授權在可連網環境執行 `pip-audit`（會連漏洞資料庫，非業務外部服務），並由誰執行、結果回補到 backlog？ | sec §1、M-9、§6 | B-018 |
| Q20 | 是否放寬 Jotform `OTHER_SESSION`（只比對未結束場次）？是否同意先蒐集一段時間的待人工原因分佈再決定？ | arch F-5、A-15 | B-057 |

另：`ux` 待釐清 8（`pay.html` 未提交變更）已解除（見本檔開頭核對表），`B-045` 不受限。

## 檔案與 model／migration 衝突，與建議的平行批次

### 規則（來自 `engineer-rules.md` §5）

- 同一個 spec package 內序列；不同 package 可平行，**前提是檔案範圍不重疊**。
- **同一時間只允許一位工程師改 `models.py`／migrations**；有 model 變更的 package 排前面。
- `settings.py`、`urls.py`、`views.py`、`models.py` 等共用檔案要由調度者先排程。

### 可能動 model／migration 的項目（「model 通道」，一次一位，按此順序）

| 順序 | 項目 | 動 model 的條件 |
|---|---|---|
| 1 | B-024 | 確定動（`Payment.created_by`） |
| 2 | B-012 | 新增 `session_full` 原因會改 `JotformSubmission.reason` 的 `choices` → migration；也可能需要名額相關欄位（展開時由 architect 確認） |
| 3 | B-010 | 僅在 Q3 選「軟刪除」或 `Order.student` 改 `PROTECT` 時；選「禁止刪除」則不動 |
| 4 | B-020 | 若採一次性綁定碼 |
| 備註 | B-008、B-014、B-019 | 預期不動 model；若展開時發現需要（記錄略過原因欄位、節流計數表、首次改密碼旗標），改排入此通道。B-014 建議用 DB cache（`createcachetable`）避免 migration |

### 共用檔案熱點

| 檔案 | 觸及項目 | 排程建議 |
|---|---|---|
| `views.py`（1592 行） | 幾乎全部 | 同一時間只讓一位工程師改；**B-060 最後做**，期間凍結其他 views.py 變更；完成後 `make codemap` |
| `settings.py` | B-001、B-002、B-014、B-016、B-017、B-021 | B-001 → B-002 → 其餘序列 |
| `crypto.py` | B-001、B-017 | B-001 先 |
| `checkout.py` | B-002、B-003、B-013、B-030 | B-002 → B-003 → B-013 |
| `line/notifications.py` | B-008、B-011、B-032、B-055 | B-008 → B-011 → B-032 → B-055，同一位工程師最佳 |
| `jotform/registration.py` | B-012、B-015、B-057 | B-012 → B-015 → B-057 |
| `base.html` | B-007、B-041、B-042、B-043、B-051、B-054 | 同一位前端樣板工程師序列 |
| `project_payments.html` | B-013、B-040、B-048 | B-013 → B-040 → B-048 |
| `dashboard.py`／`domain/dashboard.py` | B-013、B-049、B-053 | B-013 → B-049 → B-053 |
| `forms.py` | B-002、B-019、B-059 | B-002 → B-019 → B-059 |
| `pay.html`／`pay_page` | B-014、B-042、B-044、B-045 | B-014、B-042、B-044 之後才做 B-045 |
| `ci.yml`、`pyproject.toml` | B-016、B-018、B-034 | 序列 |

### 建議的批次（供調度者派工；最終由使用者挑選）

**批次 0：先確認（非工程，可立即進行）**：向使用者取得 Q7（運維與是否輪替）、Q8（金流商行為）、Q2、Q3、Q1 的回答；Q4、Q9、Q10、Q12、Q17、Q18 可稍後。

**批次 1：互不撞檔，可平行（4 條通道）**
- **通道 A（設定、金流）**：B-001 → B-002 →（Q8 確認後）B-003。
- **通道 B（前端樣板，一位工程師）**：B-004 → B-005 → B-006 → B-007 → B-041 → B-042 → B-044。base.html 與多個樣板在此通道內序列處理。
- **通道 C（測試，一位工程師）**：B-027、B-028、B-029、B-033、B-036，最後 B-034（影響 CI 門檻，量測後再定）。只動 `tests/` 與 `pyproject.toml`，與通道 A、B 無重疊；若測出缺陷，開新 backlog 項目，不順手修。
- **通道 D（文件，pm）**：B-037（Q5 部分延後）、B-038（等 Q6）。只動 `specs/`，與程式無重疊。
- **model 通道**（可與上面並行，因 A–C 不動 model）：B-024。

**批次 2：依賴批次 1 或需先決定**
- **通道 E（通知，同一位工程師）**：B-008 → B-011（待 Q2）→ B-032。
- **通道 F**：B-013（待 Q10；在 B-003 後）；B-014 → B-015（待 Q18）。
- **views.py 小修**（序列，與 F 錯開）：B-009、B-025、B-026、B-010（待 Q3）、B-039。
- **model 通道**：B-012（待 Q1；在 B-024 之後）→ B-010（若需 model）→ B-020（待 Q9）。B-012 完成後補 B-030、B-031。

**批次 3：流程與體驗優化、上線硬化**
B-016、B-017、B-018、B-019、B-021、B-022、B-023；B-040、B-045、B-046、B-047、B-048、B-049、B-050、B-043、B-051、B-052、B-053；B-055、B-056、B-057、B-035。依通道規則分組，仍遵守上表序列。

**批次 4：結構性收尾（凍結期）**
B-058、B-059 可先行（不動 views.py）；**B-060 最後單獨進行**，此時不得有任何工程師修改 `views.py`／`urls.py`。完成後 `make codemap`、跑全部品質關卡。

## 建議（待使用者決定是否採納）

以下是評估報告提出但**不屬於「補完現有規格、憲法、驗收標準」範圍**的新功能想法，不納入 backlog；使用者決定採納後再轉為項目走完整路線。

| # | 想法 | 來源 |
|---|---|---|
| S1 | 定期資料健檢 management command（專案一致性巡檢，B-029 的測試版之外再加上線後掃描） | arch F-6 |
| S2 | LINE webhook 以 `webhookEventId` 去重（目前重送只會重複回覆，不改狀態，風險低） | arch §2 #9 |
| S3 | `JobRun` 失敗時外送告警（LINE／email 給管理員）；目前只在設定頁顯示 | arch F-11 |
| S4 | 上線後監控：Jotform 延遲、付款頁 5 秒內可見（004 NFR-001、SC-001、SC-004 目前無監控項） | qa §3（004）、§5 第 4 點 |
| S5 | 測試名稱帶 testplan 案例編號（機器可追溯，新功能起適用，不回補舊測試） | qa 補測 #12 |
| S6 | 場次「複製」功能（每月建多場） | ux §2.1 |
| S7 | 付款連結可個別撤銷（現為 30 天簽章、無法撤銷） | sec §2 資訊 |
| S8 | 全站稽核紀錄（超出 B-024 的財務範圍：所有設定與資料異動留操作者） | arch F-8 |

## 項目說明

> 每項：問題描述、來源與位置、驗收標準（可由 QA 直接驗證）、不得改變的既有行為。行號為評估時（HEAD `eb0a518`）的位置，展開時請以程式碼地圖與實際檔案為準。
> 凡「測試」一詞，皆指依憲法的真實 PostgreSQL 測試（`tests/db`）或純邏輯單元測試（`tests/unit`），不 mock ORM 或自家業務函式。

### B-001　設定預設改為失敗即拒絕、compose 傳入機密、啟動檢查

- **問題**：`settings.py:8` `SECRET_KEY` 預設為公開字串、`:9` `DEBUG` 預設開、`:11` `FIELD_ENCRYPTION_KEY` 預設空且 `crypto.py:13` 退回以 `SECRET_KEY` 加密、`:13` `FAKE_GATEWAY_ENABLED` 預設開；`compose.yaml:17-27` 沒有把這些變數傳進容器；沒有任何啟動檢查。以 repo 提供的方式啟動就是「公開金鑰、除錯頁、假金流」。付款連結（簽章 token）可被偽造、金流與 LINE 憑證加密形同明文。
- **來源**：sec H-1；arch F-8、F-9（前半）、D-5、A-6（前半）。
- **驗收標準**：
  1. 沒有提供 `DJANGO_SECRET_KEY` 時，非測試環境載入設定即失敗，錯誤訊息指出缺哪個變數且不含任何值。
  2. `DJANGO_DEBUG` 未設時為關閉。
  3. 非 DEBUG 下 `FIELD_ENCRYPTION_KEY` 缺失或與 `SECRET_KEY` 相同 → 拒絕啟動；`crypto.py` 不再退回 `SECRET_KEY`。
  4. `FAKE_GATEWAY_ENABLED` 未設時為關閉。
  5. `compose.yaml` 的 app 與 scheduler 兩個服務都傳入上述變數與 `DJANGO_CSRF_TRUSTED_ORIGINS`（`env_file` 或逐項），且 repo 中沒有任何真實值。
  6. `DEBUG` 為真且 `ALLOWED_HOSTS` 含非本機名稱 → `manage.py check` 報錯／拒絕啟動。
  7. 開發與 CI 以明確提供的測試用假值運行，903 項測試仍全數通過；`tests/unit/test_ci_workflows.py`、`test_compose_scheduler` 等對設定檔的斷言隨設定調整，**不得靠移除斷言過關**。
  8. `.env.example` 每個變數有說明且為佔位符。
- **不得改變**：以相同金鑰加密的既有資料仍可解密；付款連結 token 格式與 30 天有效期；`ALLOWED_HOSTS` 預設（`localhost,127.0.0.1`）；`origins.py` 的 CSRF 來源推導；本機 `make` 流程在複製 `.env.example` 後可用。
- **運維（非程式，需使用者）**：確認正式環境是否曾以預設值運作（Q7）；若是，輪替 `SECRET_KEY` 並重新輸入各專案金流與 LINE 憑證，視為已外洩。工程師不得讀取或修改 `.env`。

### B-002　假金流在關閉時不可用

- **問題**：`views.py:954-1012` 的 `fake_checkout`／`fake_complete`（免登入、`csrf_exempt`）會由伺服器自己簽出「付款成功」通知；`GatewaySettingsForm` 無論旗標都開放選「假金流」且不要求 HashKey；`checkout.py:74-75` 的 `simulated` 檢查只擋綠界。持有付款連結者可免費變成已付款並佔位。選假金流且 HashKey 為空時，用 Jotform 建的訂單交易編號可預測，可直接偽造 `/gateway/notify/<project_id>/` 成功通知。
- **來源**：sec H-2。
- **驗收標準**：
  1. `FAKE_GATEWAY_ENABLED=False` 時，付款設定表單的供應商選項不含「假金流」。
  2. 同條件下，專案若已設為 `provider=fake`：`get_gateway`／`gateway_for` 拒絕建立 `FakeGateway`；付款頁顯示「付款設定需重新設定」友善訊息，不出現 500；`/gateway/notify/<project_id>/` 回 400 且訂單狀態、付款紀錄不變；`/fake-gateway/complete/` 不會使任何訂單入帳。
  3. `FAKE_GATEWAY_ENABLED=True` 時，假金流設定的 HashKey 為空會被表單拒絕（至少 32 字元，沿用 sec 建議值）。
  4. 以上皆有測試，包含 A 專案設定不影響 B 專案。
- **不得改變**：旗標開啟時，開發／測試的假金流完整流程（模擬頁 → 模擬付款成功 → 入帳 → 標籤）；綠界、藍新的驗簽、冪等、`simulated` 檢查；已設定的綠界／藍新設定。
- **運維**：上線前請有權限者唯讀確認有哪些專案目前為 `provider=fake`（工程師不得連正式庫）。

### B-003　金流失敗通知不得把付款嘗試鎖成終態

- **問題**：`checkout.py:94-104`：`attempt.status != CREATED` 即回 `DUPLICATE`；失敗通知把狀態設為 `FAILED`。若同一商店訂單編號失敗後持卡人重試成功，成功通知會回 ack（金流停止重送）卻不入帳，學員被扣款、訂單仍未付款。
- **來源**：sec M-4。
- **驗收標準**（Q8 確認供應商行為後定稿）：
  1. 同一 `trade_no`：驗簽通過的失敗通知先到、成功通知後到 → 訂單入帳恰好一次，金額核對仍生效，`PaymentAttempt` 結果為已付款。
  2. 失敗通知重複送達 → 無副作用，不重複發訊。
  3. 成功之後再收到失敗通知 → 忽略，不得把已付款回退。
  4. 成功通知金額與嘗試金額不符 → 仍拒絕／進入 `UNAPPLIED`。
  5. 以上測試放 `tests/db`；若涉及同時到達，另附 `transaction=True` 並行案例（可併入 B-030）。
- **不得改變**：重複成功通知只入帳一次（憲法 #9）；驗簽、商店代號、單號、金額核對；`UNAPPLIED` 分支；Jotform 交易編號 36 次上限；沙盒「模擬付款」在正式模式被拒。

### B-004　學員編輯頁標籤區落在 `<title>` 內

- **問題**：`project_student_edit.html:2` 的 `{% block title %}` 沒有閉合，第 3–29 行（標籤清單、新增標籤、標籤紀錄）都在 `<title>` 內，畫面看不到；`project_reschedule.html:69` 指示「在學員編輯頁加上『改期』標籤」，實際做不到。
- **來源**：ux UX-01（已讀檔確認）。
- **驗收標準**：
  1. 以行政角色 GET 學員編輯頁：`<title>` 只含「編輯學員｜專案名」；主體含「標籤」「新增標籤」「標籤紀錄」。
  2. 在該頁新增「改期」標籤成功，改期頁可看到該學員。
  3. 渲染測試斷言「新增標籤」出現在頁面本體；講師仍被拒絕編輯。
- **不得改變**：`tag add/remove` 的 POST 端點、權限與跨專案 404；付款相關標籤由系統管理、不可手動；學員編輯表單欄位與儲存行為。

### B-005　追售名單「待邀請出席」整段重複

- **問題**：`project_follow_ups.html:35-44` 與 `:45-54` 完全相同。
- **來源**：ux UX-02（已讀檔確認）。
- **驗收標準**：頁面只出現一次「待邀請出席（N）」標題與一份名單；「追售中」「進階未完款」區塊與其按鈕不變；渲染測試以標題出現次數斷言。
- **不得改變**：名單內容與排序、停止追售與提醒完款的行為與權限。
- **備註**：說明文字（這群人該做什麼）待 Q11，不在本項。

### B-006　現場報名「已現場收款」不得預設勾選

- **問題**：`project_attendance.html:91` 的 checkbox 預設 `checked`，漏看就把未收款記成已付款。
- **來源**：ux §2.3（已讀檔確認）。
- **驗收標準**：GET 點名頁，臨時報名表單的 `paid` 初始未勾選；勾選送出 → 建立已付款訂單（沿用）；未勾 → 未付款訂單；渲染測試斷言 `checked` 不存在。
- **不得改變**：臨時報名的其他欄位與驗證、報名與標籤結果、權限。
- **展開時注意**：pm 查 `specs/TEST_LIST.md` 是否明定預設勾選；若有，屬改規格，需回報調度者。

### B-007　訊息元件統一

- **問題**：約 20 個樣板各自 `{% for message in messages %}`；`manage_base.html:9`、`project_follow_ups.html:9`、`project_access.html:10-12`、`project_line_settings.html:10`、`project_message_templates.html:10`、`project_payment_settings.html:11` 一律綠色，`views.py:243` 的 `messages.error` 已實際被畫成成功條；錯誤誤用 `role="status"`；`project_line_settings.html:15`、`project_payment_settings.html:10`、`project_jotform_settings.html:41`、`fake_checkout.html:6` 的資訊性提醒用紅色 error；缺 warning／info 樣式。
- **來源**：ux UX-03、UX-05。
- **驗收標準**：
  1. 任何頁面的 `messages.error` 以 `.alert.error` 且 `role="alert"` 顯示；success 以 `.alert.ok` 且 `role="status"`。
  2. 新增 `warning`、`info` 樣式（亮／暗兩組文字對背景 ≥ 4.5:1），上述四處資訊性提醒改用之。
  3. 訊息顯示只在 `base.html` 一處渲染；每個訊息只出現一次，不遺漏。
  4. 測試：觸發 `views.py:243` 的失敗路徑，頁面含 `alert error`。
- **不得改變**：各 view 發出的訊息文案與時機；沒有訊息時不多出空容器；既有頁面其他版面。

### B-008　對外發送前重新檢查條件

- **問題**：`notifications.py:158-180` `_deliver` 只檢查綁定與封鎖；`:232-240` `retry_message` 直接以建立當時的文字重送；`:106-120` `PENDING` 殘留訊息直接沿用舊文字；`:92-103` 追售迴圈用開頭載入的 `FollowUp`，迴圈期間被人工停止仍會發；`:243-282` 完款提醒當日去重靠查詢，`session` 為 NULL 時唯一約束不適用，連點兩次或兩人同時按可能重複發送。已付款或已報進階者仍收到付款提醒或追售。
- **來源**：arch F-3、A-2、D-3、F-11（第 2 項）；sec M-8。
- **驗收標準**：
  1. 重送追售類訊息：學員已報進階或追售已停止 → 狀態標為 `SKIPPED`，**不呼叫** LINE client。
  2. 重送完款提醒：訂單已付清或已取消 → `SKIPPED`。
  3. 重送／投遞課前通知：學員已不在該場次或場次已結束 → `SKIPPED`。
  4. `PENDING` 殘留訊息下一輪投遞前同樣重驗。
  5. 追售迴圈逐位重取 `FollowUp` 狀態，迴圈期間被停止者不發。
  6. 重驗規則為 domain 純函式（不匯入 Django），`tests/unit` 無資料庫可跑。
  7. 同一訂單同一日「提醒完款」連按兩次或並行兩個請求，只產生一則訊息（並行測試 `transaction=True`）。
  8. 略過原因可在通知頁看到（若現有欄位不足需 architect 確認是否新增欄位，則排入 model 通道）。
- **不得改變**：條件仍成立時，失敗訊息可重送且內容不變；重試上限（3 次）與額度耗盡短路；`OutboundMessage` 既有唯一約束；排程路徑正常發送的對象與內容；LINE 額度提示。

### B-009　LINE webhook 空 secret

- **問題**：`domain/line.py:27-32` 驗簽在 channel secret 為空時仍以空金鑰計算，任何人可簽；「假 LINE」模式可在無 secret 下啟用，外部事件可偽造綁定。
- **來源**：sec L-1（位置 `views.py:1165-1167`、`forms.py:438-443`）。
- **驗收標準**：`verify_signature(secret="")` 回 `False`（`tests/unit`）；`line_webhook` 對 secret 為空或非 LINE 模式的專案不處理外部事件並回 400；用有效 secret 簽章的請求仍成功處理。
- **不得改變**：既有有效簽章的綁定流程；A 專案 secret 簽的內容打 B 專案被拒；`replyToken` 行為。

### B-010　有收款紀錄的學員不得被刪除

- **問題**：`views.py:467-481` 刪除學員只有確認頁，警語只說報名會一併刪除；`models.py:200`（`Order.student` CASCADE）、`:237`（`Payment.order` CASCADE）使所有訂單、收款、付款嘗試、轉帳回報被硬刪，金流與銀行帳上仍有紀錄，破壞單一事實來源與稽核。
- **來源**：arch F-4、A-3、D-4；sec M-5（後半）。
- **驗收標準**（Q3 定稿；以下為「禁止刪除」方案）：
  1. 學員有任何 `Payment` 或 `PaymentAttempt` → 確認頁顯示不可刪除與原因，POST 在伺服器端被拒，學員、訂單、收款全部保留。
  2. 無收款紀錄者可照舊刪除，確認頁列出將被刪除的報名與訂單筆數。
  3. 跨專案 404；講師與行政專員被拒（沿用 `DELETE_DATA`）。
  4. 若 Q3 選軟刪除或 `PROTECT`：另列 migration 驗收，排入 model 通道。
- **不得改變**：`DELETE_DATA` 僅 admin／行政管理者；場次刪除流程；無收款學員的刪除結果。

### B-011　每日 job 納入內建排程

- **問題**：`scheduler.py:74-85` 只登錄兩個 Jotform job；`send_line_notifications`（課前 3／2／1 天通知）與 `process_finished_sessions`（結束場次、啟動追售）沒有排程、沒有說明，是否每天跑取決於部署端是否另設 cron，專案內無法驗證。通知以「今天 ± 精確天數」判斷，漏跑一天則該階段永遠補不回來。
- **來源**：arch F-1、A-1、D-1、F-11（JobRun）；sec §2 資訊（scheduler raw SQL 註解）。
- **驗收標準**：
  1. `registered_jobs()` 包含兩個 job，每日定時（時間與時區依 `/clarify`）；每次執行寫 `JobRun`。
  2. 同一天重跑不重複發送（沿用唯一約束與狀態）。
  3. 補發：以固定時鐘測試「漏跑一天後下一次執行」補發「應發而未發」且仍符合發送條件的課前通知與追售，超出補發窗口者不補。
  4. 設定頁顯示兩個 job 的最後執行與是否過期（沿用 `JobRun.is_stale`）。
  5. 單一 job 失敗或逾時不影響其他 job。
  6. `scheduler.py` 的 raw SQL（advisory lock）補逐處註解說明原因。
  7. 全程使用 fake LINE，不連真實服務。
- **不得改變**：advisory lock 保證單一執行者；Jotform 兩個 job 的節奏與行為；T-3／2／1 與 D1／3／7 的規則與通知內容；發送前重驗（B-008 的成果）。
- **部署注意**：啟用前確認並停掉既有主機 cron，避免雙跑（唯一約束可擋重複，但仍應避免）。

### B-012　場次名額規則與資料庫鎖

- **問題**：憲法要求有限資源以資料庫鎖保護，現只有 `rescheduling.py:20-30` 鎖 `Session` 並以報名人數檢查；`importer.py:25-36`、`jotform/registration.py:84-122 _book`、`attendance.py:116-152 register_walk_in`、`:80-113 check_in_early`、`registration.py:129-157 resolve` 都不鎖、不檢查。額滿有兩套口徑：改期用報名數，Jotform 選項（`domain/jotform_options.py:110`、每 60 秒同步）與儀表板（`domain/dashboard.py:108-110`）用已付款數，`views.py:1076`、`overview.py:48` 剩餘名額口徑又不同。最後幾席同時報名或付款可超收，系統只事後告警。
- **來源**：arch F-2、A-4、D-2；sec M-6；qa 補測 #3。
- **驗收標準**（依 Q1 回答；通用部分如下）：
  1. 名額規則（占名額的是報名還是付款、是否允許超收、哪些路徑例外）寫入規格，並於憲法有例外時由使用者決定是否修訂（工程師不得改憲法）。
  2. 受規則約束的建立報名／入帳路徑，先 `select_for_update` 鎖 `Session` 再檢查；兩個並行請求搶最後一席，只有一個成功（`transaction=True` 測試）。
  3. 改期、Jotform 選項、儀表板異常、場次詳情、總覽使用同一個「額滿／剩餘」定義（單一函式）。
  4. 額滿時 Jotform 自動建單轉為待人工，原因 `session_full`，待處理清單可見。
  5. 跨專案隔離測試。
- **不得改變**：`rescheduling` 既有鎖與結果；`check_in_early`「不受人數上限限制」，除非 Q1 另有決定；Jotform 提交列鎖去重；訂單編號＝提交編號。

### B-013　付款待處理清單

- **問題**：金流已扣款但訂單無法入帳時（`checkout.py:103-107`），只在 `PaymentAttempt.UNAPPLIED` 記錄，沒有待辦或告警；轉帳回報只以付款頁最後一欄的小提示呈現，沒有「待對帳」篩選、儀表板也沒有項目，行政人員要手抄末五碼進備註。SITEMAP 的付款段要求「轉帳人工對帳（待對帳清單 → 確認入帳）」與金流回報紀錄。
- **來源**：arch A-5、D-14、§4.2（付款列）；ux UX-11、§2.2。
- **驗收標準**：
  1. 專案儀表板待辦／異常出現「N 筆已扣款未入帳」與「N 筆轉帳待對帳」，各自連到付款頁對應篩選；N=0 時不顯示。
  2. 付款頁狀態篩選新增「待對帳」「已扣款未入帳」，結果正確。
  3. 轉帳回報旁有「依此核對入帳」，預填金額與末五碼（備註），確認入帳後該回報不再列為待對帳。
  4. 長時間停在 `CREATED` 的付款嘗試列為異常（閾值於 `/clarify` 定）。
  5. 權限依 Q10；講師看不到待處理清單；跨專案隔離測試。
- **不得改變**：`record_payment` 為付款的唯一定義；確認入帳、退款、取消的流程與權限；「已付款」判定（`paid_intro_student_ids`）；金流回報冪等。
- **邊界**：獨立的「金流回報紀錄頁」是否要做屬 Q5／B-056，不在本項。

### B-014　公開端點與登入入口濫用防護

- **問題**：`jotform_return`（`views.py:1491-1507`）免登入、`csrf_exempt`、無節流，每次用共用 `JOTFORM_API_KEY` 呼叫 Jotform 最多 3 次並 `sleep`，可耗盡共用額度、佔滿 worker、以攻擊者提供的數字建立 `JotformSubmission` 佔位列灌滿待處理清單；`pay_page` POST（`views.py:917-919`）可無限建立 `TransferClaim` 與付款嘗試；登入無失敗鎖定；`/admin/`（`config/urls.py:5`）仍公開。
- **來源**：sec M-1（建議 1）、M-3（節流與 `/admin/`）、L-2；arch A-7、F-8。
- **驗收標準**：
  1. 同一來源 IP＋專案對 `jotform_return`／`jotform_webhook` 超過上限（N，`/clarify` 定）→ 429，**不呼叫** Jotform、不建 `JotformSubmission`。
  2. 同一訂單未處理的 `TransferClaim` 超過上限被拒，同金額同末五碼去重；進行中的付款嘗試超過上限被拒。
  3. 同帳號＋IP 連續失敗 5 次鎖 15 分鐘，鎖定期間正確密碼也被拒，期滿恢復（固定時鐘測試）。
  4. `/admin/` 不再公開（移除路由或限制來源）。
  5. 不引入新服務；機制於多 worker 下有效（architect 於 plan 定案，避免 LocMem 不共享的陷阱）。
  6. 一般速率的正常使用不被擋。
- **不得改變**：登入成功流程與 `next` 驗證；付款頁 token 驗證；已存在提交可重複進入同一訂單（Q18 另決）；webhook 的網址密鑰驗證。

### B-015　`jotform_return` 流程收斂

- **問題**：不認得的提交編號仍會打 Jotform（含 `_explain_rejection` 多打一次 `/user`）；請求內 `sleep(1)` 重試佔用 worker（`registration.py:173-178,238-250`）；已有訂單的提交編號再次進入不檢查時效（`registration.py:220-222`），提交編號等於持有付款連結的憑證，且可能被列舉（待確認）。
- **來源**：sec M-1（建議 2–4）；arch F-5。
- **驗收標準**（Q18 定稿後再細化）：
  1. 本系統不認得的提交編號：顯示「找不到／處理中」，不呼叫 Jotform。
  2. 請求執行緒內不再 `sleep` 重試；暫時失敗交補處理排程，使用者看到「處理中」頁。
  3. 已有訂單的提交依 Q18 結果（檢查時效或二次驗證）才給付款頁。
  4. 補處理（`process_jotform_submissions`）結果與既有一致；五種提示頁面文案不變。
- **不得改變**：`_book` 以提交列鎖去重；訂單編號＝提交編號；webhook 回查不採信通知內容；失敗不顯示錯誤頁。

### B-016　正式環境部署硬化

- **問題**：`Dockerfile:15-16` 以 `runserver`、root、含 dev 依賴；compose 掛載原始碼並開放 8000 與資料庫埠；無 `LOGGING`；無 `SESSION_COOKIE_SECURE`／`CSRF_COOKIE_SECURE`／HSTS／`SECURE_PROXY_SSL_HEADER`；付款連結與金流 `notify_url`／`return_url` 以 `build_absolute_uri` 產生（`views.py:705,935`），在 HTTPS 代理後會是 `http://`，與排程使用 `SITE_BASE_URL` 的連結不一致。
- **來源**：sec M-2、L-6；arch F-8、A-6（後半）。
- **驗收標準**：
  1. 提供 production 啟動方式（gunicorn；`requirements.txt` 含之），映像不含 `requirements-dev.txt`、非 root，production compose 不掛載原始碼、不發佈資料庫埠。
  2. 非 DEBUG 時 session／CSRF cookie 為 `Secure`，HSTS（秒數由環境變數控制）、`SECURE_PROXY_SSL_HEADER`（僅在明確設定時啟用）、`SESSION_COOKIE_AGE`、`SECURE_REFERRER_POLICY` 生效，皆有測試。
  3. `LOGGING` 設定存在，測試證明金鑰與個資不入日誌。
  4. 付款連結與 `notify_url`／`return_url` 一律以 `SITE_BASE_URL` 組出，與排程產生的連結一致。
  5. `manage.py check --deploy` 納入 CI 且無 warning（或列出已接受的例外與理由）。
- **不得改變**：本機開發與 `make test` 流程；`origins.py` 的 CSRF 來源推導；既有登入工作階段行為。

### B-017　加密金鑰管理

- **問題**：`crypto.py` 單一 Fernet，無輪替，金鑰一換所有憑證不可解；解密失敗（`DecryptionError`）未被接住，`pay_page`（`card_available` → `gateway_for`）與 `line_webhook` 會直接 500。
- **來源**：sec L-5；arch F-9、A-9、D-7。
- **驗收標準**：
  1. 支援多把金鑰（新金鑰加密、任一舊金鑰解密）。
  2. 提供重新加密 command：冪等、有 dry-run、不印明文，執行後以新金鑰可解全部憑證。
  3. 解密失敗：付款頁顯示「付款設定需重新輸入」，`line_webhook` 回 400，皆不 500，日誌不含金鑰。
  4. 測試包含：舊金鑰資料在新增金鑰後仍可解；缺金鑰時的錯誤行為。
- **不得改變**：以相同金鑰加密的既有資料可解；密文相容 Fernet；憑證在畫面不回顯。

### B-018　依賴與供應鏈

- **問題**：`requirements.txt:3` `cryptography~=43.0` 鎖在已知 CVE 主線（CVE-2024-12797，本系統使用方式關聯低）；無鎖定檔；`pip-audit` 未執行；Dockerfile 安裝 dev 依賴；ruff 未啟用 `S` 規則。
- **來源**：sec M-9、§6。
- **驗收標準**：`cryptography` 升至支援修補的主線且 `make test` 全過、有升版理由（憲法：依賴變更需理由）；CI 有獨立的 `pip-audit -r requirements.txt` 定期工作；ruff `S` 規則啟用且既有違規已修或逐行附理由；`pip-audit` 實際執行結果記回 backlog。
- **不得改變**：Django `~=5.2`、`psycopg` 版本範圍；現有 CI 關卡與 `tests/unit/test_ci_workflows.py` 斷言（只增不減）。
- **限制**：`pip-audit` 需連網，不得由工程師自行對外查詢，待 Q19。

### B-019　成員管理補完

- **問題**：`manage_members` 只能新增；離職者無法在應用程式內停用（`is_active` 沒有畫面可改）、無重設密碼；初始密碼由 admin 設定且無強制變更。
- **來源**：sec M-3（後半）；ux §2.6、待釐清 3。
- **驗收標準**（範圍依 Q12）：admin 可停用／啟用成員；停用者無法登入，`visible_to` 回空；admin 可重設密碼；（若含）可改角色；非 admin 一律 403；提權限制（`can_grant_project_access`）不變；測試含跨專案與角色矩陣。
- **不得改變**：建立成員流程；專案授權規則；停用不刪除既有資料與紀錄（`marked_by`、`TagEvent` 等）。

### B-020　LINE 綁定強化

- **問題**：`line/service.py:93-120` 只憑「姓名＋電話」綁定，知情者可先綁定並收到該學員的通知與付款連結；三種回覆文字可探測學員是否存在。
- **來源**：sec M-7。
- **驗收標準**（Q9 定稿後細化）：綁定需第二因子或同一 `line_user_id` 嘗試上限（以 `BindingIssue` 計數）；「查無」「已綁定其他」回覆不可區分；真學員用正確方式綁定成功；測試含冒綁與探測情境。
- **不得改變**：既有已綁定帳號不受影響；封鎖／解除封鎖處理；`BindingIssue` 人工綁定流程（衝突時的處理）。

### B-021　專案停用後的公開入口與排程

- **問題**：只有 `visible_to`（`models.py:20-31`）看 `is_active`；付款頁、`gateway_notify`、`line_webhook`、`jotform_return`／webhook、排程同步與發送在專案停用後仍運作。
- **來源**：sec L-7。
- **驗收標準**（Q17 定稿後細化）：依語意，停用專案的公開入口回一致的「已停用」回應，排程的同步與發送查詢排除停用專案；重新啟用後恢復；測試含啟用與停用兩種狀態。
- **不得改變**：停用不刪資料；啟用專案的行為；`visible_to` 現行行為。

### B-022　機器對機器端點回應統一與標頭硬化

- **問題**：公開端點回傳內部錯誤文字並以 404／400 區分專案存在與否（`views.py:857-858,1164`）；登入後含個資的頁面沒有 `Cache-Control: no-store`；無 CSP；`jotform_webhook` 密鑰在網址路徑，會進存取日誌。
- **來源**：sec L-3、L-8。
- **驗收標準**：`gateway_notify`、`line_webhook`、`jotform_webhook` 失敗統一回 400 無內文，原因進日誌（不含金鑰與完整 payload）；`pay_page` 等學員會看到的頁面維持友善訊息；含個資頁面帶 `no-store`；CSP 啟用（內嵌 script 用 nonce）且複製按鈕、自動送出頁仍可用；webhook 密鑰遮罩或移至標頭（以 Jotform 能否支援為準，先查實測結果）。
- **不得改變**：驗簽與冪等；學員端錯誤提示頁的文案；跨專案防護。

### B-023　講師可見付款頁範圍

- **問題**：講師可唯讀進 `project_payments`（`views.py:677-720`），看到金額、付款狀態與轉帳末五碼。SITEMAP 只明說「學員資料不遮蔽」。
- **來源**：arch Q4、F-6（§3 #5）；sec §3 #5。
- **驗收標準**（Q4 定稿）：若決定限制，講師對付款頁（含轉帳回報）回 403，側欄不顯示；其他角色不變；伺服器端判定，非只隱藏按鈕。若決定維持現狀，關閉本項並在 SITEMAP 註記。
- **不得改變**：講師對學員、場次、點名的唯讀權限；付款連結只給有 `EDIT_DATA` 者。

### B-024　財務操作者稽核

- **問題**：`Payment`（`models.py:231-250`）無 `created_by`；確認入帳、退款、取消、刪除、改價格、改金流設定都沒有操作者紀錄，無法稽核「誰把這張單標成已付」。
- **來源**：arch F-8、A-8、D-6；sec M-5（前半）。
- **驗收標準**：`Payment` 新增可為空的 `created_by`（FK，`SET_NULL`）與來源；`record_payment`／`refund_order`／`cancel_order` 傳入 `request.user`；付款頁顯示操作者；金流回報建立者為空、來源為金流；舊資料為空不報錯；migration 可前進與回退；`makemigrations --check` 乾淨；操作紀錄的涵蓋範圍（刪除、價格、金流設定）於 `/clarify` 定。
- **不得改變**：金額計算與整數規則；`record_payment` 單一入口；付款狀態判定；對帳畫面既有欄位。

### B-025　名單匯入上限

- **問題**：`views.py:341` 整檔讀入記憶體，無大小與列數上限；`name`、`address` 超長會造成資料庫例外而非友善錯誤。
- **來源**：sec L-4。
- **驗收標準**：超過 2 MB 或 5000 列（沿用 sec 建議值，可於展開時調整）→ 友善錯誤、不建立任何資料；超長欄位以逐列錯誤訊息呈現而非 500；合法檔案結果不變。
- **不得改變**：既有匯入規則（重複、部分失敗的處理）；權限（行政專員以上）；跨專案隔離。

### B-026　併發重複操作的友善處理

- **問題**：`register_walk_in`（`attendance.py:123-128`）、`check_in_early`（`:86`）「先檢查再建立」無鎖，兩人同時操作撞唯一約束回 500；`create_order` 同樣先查再建。
- **來源**：arch F-11（第 1 項）；sec §4 競態。
- **驗收標準**：並行（`transaction=True`）兩個相同請求：只建一筆資料，另一個得到友善訊息而非 500；序列重複操作行為不變。
- **不得改變**：唯一約束本身；現場報名與提前報到的結果、標籤與出席狀態。

### B-027　補測：金流回報解析異常

- **問題**：`gateways/newebpay.py:100,102-103,111-112`、`ecpay.py:98-99` 未被覆蓋（`Result` 為字串 JSON、內容無法解析、金額非數字、缺欄位）。
- **來源**：qa 補測 #1。
- **驗收標準**：上述輸入一律產生 `InvalidCallback`，端點回 400，**訂單與付款嘗試狀態不變**；測試放 `tests/unit`（純邏輯）加至少一個 `tests/db` 端點案例；兩個檔案該段覆蓋率達 100%。
- **不得改變**：既有驗簽與冪等行為；產品碼（若測出缺陷，另開缺陷項，不順手修）。

### B-028　補測：金額與設定驗證

- **問題**：`forms.py:222,243,246,251,356` 與 `jotform/registration.py:142` 未覆蓋（訂金 ≥ 價格／≤ 0、第二個前端課、藍新 HashKey／IV 長度、人工建單時專案沒有前端課費用）。
- **來源**：qa 補測 #4。
- **驗收標準**：各驗證各有一個測試，錯誤時不寫入資料、顯示明確訊息；金額一律整數。
- **不得改變**：產品碼（發現缺陷另開項）。

### B-029　補測：專案隔離守門

- **問題**：`project_session_import`、`project_session_delete`、`project_attendance_walk_in`、`project_attendance_close`、`project_front_course`、`project_message_templates`、`project_line_settings`、`line_webhook`（A 的 secret 打 B）、服務層 `attendance._check_project`（`attendance.py:21`）缺跨專案測試；`Registration/Order/Payment/Attendance` 的 `project` 與 `student.project`／`session.project` 一致性無守門。
- **來源**：qa 補測 #2；arch F-6、D-10、A-12（後半）；憲法 MUST 4。
- **驗收標準**：上述每個入口有「以 A 專案成員身分打 B 專案資源 → 404／拒絕、B 資料不變」測試；新增一組巡檢測試，掃描帶 `project` 的 model，斷言上述一致性（建立資料與服務層路徑產生的資料皆通過）；`attendance.py:21` 覆蓋。
- **不得改變**：產品碼；現有跨專案測試。

### B-030　補測：並行

- **問題**：並行測試只有 Jotform 導向與排程鎖兩處；改期搶最後名額、同一付款通知同時送兩次、同時兩次「確認收款」、連點完款提醒都只以序列驗證。
- **來源**：qa 補測 #3；arch D-13、A-12（前半）。
- **驗收標準**：沿用 `test_jotform_webhook.py` 的 `transaction=True` + Barrier 樣式，各案例斷言「恰好一次入帳／發送／成功」。名額相關案例在 B-012 後補，通知相關在 B-008 後補，付款回報在 B-003 後補。
- **不得改變**：產品碼；測試不得 skip／xfail。

### B-031　補測：webhook 建單 → LINE 付款提醒

- **問題**：004 FR-018 目前僅文字宣稱「既有測試涵蓋」，沒有測試把 webhook 建立的訂單串到 LINE 綁定與付款提醒。
- **來源**：qa 補測 #5、§3（004 FR-018）。
- **驗收標準**：一條串接測試：webhook 建單 → 學員綁定 LINE → 觸發付款提醒 → fake LINE 收到含付款連結的訊息；以 `FakeLineClient`，不連真實服務。
- **不得改變**：產品碼；既有測試。

### B-032　補測：LINE 外送路徑

- **問題**：`notifications.py:180,236,278-281`、`service.py:30,38,94-95,114`、`views.py:1170-71` 未覆蓋。
- **來源**：qa 補測 #6。
- **驗收標準**：重試上限後標失敗；無設定時重送；付款提醒略過與失敗計數；非法 webhook body 回 400；重新綁定停用中的帳號；手動綁定衝突；皆以 fake client 驗。
- **不得改變**：產品碼。

### B-033　補測：排程指令參數、同日場次判斷、已處理提交

- **問題**：四個 management command 的 `--date`／`--now` 錯誤分支（`process_finished_sessions` 84%、`process_jotform_submissions` 88%）、`attendance.py:61,72`、`views.py:1575`／`registration.py:165,178`、`views.py:580-582` 未覆蓋。
- **來源**：qa 補測 #8、#9、#10。
- **驗收標準**：非法格式、缺時區 → `CommandError`；同日有開始時間時前後場次判斷正確；略過已被處理的提交不改狀態；立即同步無金鑰／無表單時顯示提示。
- **不得改變**：產品碼。

### B-034　分支覆蓋率與門檻一致

- **問題**：`pyproject.toml` 未啟用 `branch = true`，97% 僅為行覆蓋；`make coverage` 不帶門檻，只有 CI 擋 95%，憲法寫「維持在約定門檻以上」。
- **來源**：qa 補測 #7、§5 第 2 點。
- **驗收標準**：啟用分支覆蓋率並記錄新基線；`make coverage` 與 CI 使用同一門檻；若分支覆蓋率使總數低於 95%，先補測或另設分支門檻於現值，**不得降低既有門檻**。
- **不得改變**：CI 既有關卡與 `test_ci_workflows` 斷言（只增不減）。

### B-035　integration 擴充

- **問題**：integration 僅 ECPay 測試站 2 項；藍新、Jotform 真實行為（004 三項上線前實測）、LINE `get_quota`／push 完全沒有自動化。
- **來源**：qa 補測 #11、§3（004 最大外部假設風險）；arch Q6。
- **驗收標準**：各外部服務至少一個 integration 測試，只放 `tests/integration`，無法連線時 `skip`（沿用現行模式），日常 `make test` 不執行。
- **不得改變**：日常測試只用 fake（憲法 #7）。
- **限制**：需使用者授權與測試帳號，工程師不得自行執行 `make test-integration`。

### B-036　測試衛生

- **問題**：`tests/db/test_jotform_session_hooks.py:98` 以 `monkeypatch.setattr("crm.jotform.sync.sync_form", boom)` 取代自家業務函式，嚴格讀憲法 #2 屬灰色地帶。
- **來源**：qa 補測 #13、§2。
- **驗收標準**：改為在 `FakeJotformClient` 注入例外，測試意圖（同步失敗不影響場次異動）與結果不變；全測試仍通過。
- **不得改變**：產品碼。

### B-037　規格狀態欄與 SITEMAP 校正

- **問題**：001／003／004 狀態欄仍為「草稿」但皆已實作；`SITEMAP.md` 第 1、3 節未標示 Google 表單整合已撤回，與第 7 節矛盾；缺公開端點清單（`/pay/<token>/`、`/fake-gateway/*`、`/jotform/return|webhook`、`/projects/<id>/jotform/*`、`front-course`、`products`）；通篇仍用「銷講」；「JOSTFOTM」錯字；`TEST_LIST.md` 第 15 節標題重複；`TDD_PROGRESS.md`、`TEST_LIST.md` 數字與現況不符；validate 警示 003、004 的 models 用 CASCADE 缺說明理由。
- **來源**：arch §4.1、§4.2、A-13、D-12、F-11（末項）；qa §1、§3（TEST_LIST）、§5 第 1、3 點。
- **驗收標準**：三份規格狀態欄反映現況；SITEMAP 標示已做／未做／已撤回，Google 整合標為撤回，補公開端點清單，修正用語與錯字；`TDD_PROGRESS`／`TEST_LIST` 頂部標示為歷史紀錄；CASCADE 理由補在 003／004；`validate_artifacts.py all` 對 001、003、004 無新增錯誤。
- **不得改變**：程式碼與測試；憲法（不得修改）；規格 FR 內容（僅改狀態與說明）。
- **注意**：「四個缺頁標做或不做」依 Q5。

### B-038　004 收尾

- **問題**：`integration-plan.md` 有 3 個 `[NEEDS CLARIFICATION]`（上線前以真實 Jotform 實測）未關閉；`JOTFORM_TIMEZONE` 預設程式為 `America/New_York`，規格與任務寫 `Asia/Taipei`；`origins.py`（CSRF 來源由 `SITE_BASE_URL` 推導）沒有對應規格段落；NFR-001／SC-001／SC-004 無上線後監控項。
- **來源**：arch §4.1（004 列）、F-5；qa §1、§3、§5 第 1、4 點；sec §0。
- **驗收標準**：三項 `[NEEDS CLARIFICATION]` 以實測結果關閉（或明列為未決並附原因）；規格回寫 `JOTFORM_TIMEZONE` 最終決定；補 `origins.py` 規格段落；補上線後監控項（或標明不做）；validate 警示消除。
- **不得改變**：程式碼；已通過的測試。
- **限制**：真實 Jotform 實測需使用者授權（Q6、B-035）。

### B-039　用語統一

- **問題**：`project_notifications.html:12` 說「課程與費用」，側欄實為「前端課費用」；`project_nav.py:87` 群組「課程費用與贈品」、`project_products.html:9`「進階課程費用」、`project_front_course.html:10`「進階課程」三種名稱互指不一；內文寫英文 `admin`、`JOTFORM_API_KEY`、`scheduler 服務`（`project_jotform_settings.html:11,24`、`project_notifications.html:15`）而頂欄角色名為「系統管理員」；動詞新增／建立／儲存／更新／登記／確認混用；`views.py:947` 金額無千分位；docstring 殘留「銷講」「第一階段」（`views.py:1291,1319`、`orders.py:50,59,90,99,130`、`reports.py:51`）。
- **來源**：ux UX-16、§3.1、§3.2。
- **驗收標準**：建立一份用語表（前端課、進階課程、追售、待對帳、系統管理員、動詞用法）；上述樣板與導覽文字對得上側欄名稱；使用者可見文字不出現英文 `admin` 與環境變數名稱；`views.py:947` 使用千分位；docstring 與註解改為「前端課」；`tests/unit/test_wording.py` 仍通過（已存在，不新增檢查）。
- **不得改變**：權限、路由名稱、側欄分組結構；資料庫中的既有資料（Q13 另決）；`retagging.py` 與 migrations 的舊稱對照。

### B-040　危險操作統一確認

- **問題**：無確認：確認入帳／退款／取消訂單（`project_payments.html:87,96,103`）、停用專案（`manage_projects.html:50`）、完成點名（會結束場次並啟動追售，`project_attendance.html:64`）、移出場次、停止追售、略過 Jotform 報名、建立報名與訂單；確認機制三種並存（獨立確認頁、原生 `confirm()`、無）；`confirm_delete.html:9` 自製紅鈕暗色模式對比不足。
- **來源**：ux UX-04、§2.2、§2.3。
- **驗收標準**：
  1. 規則寫入設計系統互動規範：金額（入帳、退款、取消）與不可復原（略過、刪除、完成點名、停用專案）必須確認，文案含對象與後果（例：退款金額與學員姓名；完成點名將結束場次、N 位未點名標為未出席、開始追售 M 位）。
  2. 通用確認頁（零 JS）供上述操作使用；可逆操作（移除標籤）以復原訊息取代確認。
  3. `.btn.danger` 取代行內紅鈕，暗色文字對比 ≥ 4.5:1。
  4. 後端行為：未經確認的直接 POST 的處理方式於 `/specify` 明定（確認頁的 POST 才執行）。
  5. 權限判定仍在伺服器端；確認頁跨專案 404。
- **不得改變**：各操作的權限、金額計算與結果；場次與學員刪除既有確認頁的行為；點名後的狀態與追售啟動結果。

### B-041　手機版共用版面

- **問題**：`base.html:90-94` 側欄在 ≤760px 堆在內容之前（約 15 個連結、5 個群組標題）；7 張表（`project_detail.html:31`、`project_session_detail.html:25`、`project_students.html:18`、`project_products.html:14`、`project_jotform_submissions.html:27`、`manage_projects.html:28`、`manage_members.html:16`）無橫向捲動包裹。
- **來源**：ux UX-07、UX-08、§4.2。
- **驗收標準**：窄螢幕側欄預設收合（`<details>` 或等效純 HTML），標示目前頁；桌面版不變；表格以統一的 `.table-wrap` 包裹並加 `th scope="col"`；實機（或瀏覽器模擬 375px）無整頁橫向溢出。「實機驗證」標待驗證，QA 以瀏覽器模擬為準並註明。
- **不得改變**：桌面版版面；側欄依權限只顯示可用項目與 `aria-current`；Jotform 報名紀錄徽章。

### B-042　防連點與處理中狀態

- **問題**：「立即同步」（`project_jotform_settings.html:78`）、「確認入帳」「退款」、「確認付款方式」連按會送出多次請求；無處理中提示。
- **來源**：ux UX-17、§4.3。
- **驗收標準**：表單送出後 `button[type=submit]` 停用並顯示「處理中…」；無 JS 時退回直接送出（後端仍冪等）；驗證連按兩次只產生一次結果。
- **不得改變**：後端冪等行為；表單驗證失敗時按鈕應可重新使用。

### B-043　無障礙補強

- **問題**：無「跳到主要內容」；無 `:focus-visible`；輸入框邊框對比約 1.2（需 3:1）；暗色危險鈕白字對比約 2.0；`.btn.link` 點擊區約 26px；表格無 `scope`；複製成功無 `aria-live`、clipboard 失敗無回饋；登入頁只顯示 `non_field_errors`。
- **來源**：ux UX-18、§4.1。
- **驗收標準**：逐項對應：跳轉連結可用 Tab 到達；焦點可見；輸入框邊框對比 ≥ 3:1；暗色危險鈕對比 ≥ 4.5:1；`.btn.link` 高度 ≥ 32px（行動版 44px）；`th scope="col"`；複製結果有 `aria-live` 且失敗時提示；登入頁顯示欄位錯誤。對比值以工具實測記錄，不以估值通過。
- **不得改變**：視覺風格與配色主調；既有 `aria-label` 與 `role`。

### B-044　自訂 403／404／500 頁

- **問題**：`src/` 內無 `403.html`、`404.html`、`500.html`；`PermissionDenied`／`Http404`（`views.py:166,185,866` 等）顯示英文純文字頁；學員點到過期付款連結（`InvalidPayToken` → 404）也是英文空白頁。
- **來源**：ux UX-10、§4.3。
- **驗收標準**：403（含導引回「我的專案」與「請聯絡你的行政管理者」）、404、500 使用 `base.html` 風格的中文頁；公開付款頁的失效連結用不含導覽的簡化 404，含客服方式（Q15 決定內容）；測試以未授權與失效 token 請求斷言內容與狀態碼不變。
- **不得改變**：HTTP 狀態碼；權限與驗證邏輯；不洩漏專案是否存在的資訊量。

### B-045　學員付款頁互動

- **問題**：`pay.html:28-45` 不論選信用卡或轉帳，轉帳資訊卡與末五碼欄都顯示；送出鈕固定「確認付款方式」；末五碼只在後端驗證；無防連點（信用卡連按可能建立多筆付款嘗試，交易編號有 36 次上限）；單一選項仍顯示 radio；`pay_return.html` 無下一步；`views.py:947` 金額無千分位。
- **來源**：ux UX-09。
- **驗收標準**：選轉帳才顯示轉帳資訊與末五碼欄（無 JS 時全部顯示），末五碼 `required`、`pattern="[0-9]{5}"`、`inputmode="numeric"`；按鈕文案隨選擇為「前往刷卡付款」／「送出轉帳回報」；錯誤顯示於欄位旁並以 `aria-describedby` 關聯；連按只送出一次；單一選項不顯示 radio；金額顯示千分位；後端驗證仍存在。
- **不得改變**：金額由伺服器依訂單決定（只接收選項代碼）；付款連結驗證與 30 天有效期；姓名遮罩；信用卡導向與轉帳回報的後端結果；`pay_redirect.html` 自動送出。

### B-046　當天點名手機版

- **問題**：手機上要先捲過整個側欄；5 欄表格需橫向捲動才按得到「到場／未出席」；每次點名整頁重載回頁首（`views.py:1313-1314`）；「提前參加」下拉選項過長被截斷；講師唯讀無說明。
- **來源**：ux UX-06、§2.3。
- **驗收標準**：窄螢幕每位學員顯示為卡片列，按鈕列滿版、高度 ≥ 44px；點名後回到該學員列（錨點）；摘要置頂顯示「實到／已報名」；臨時報名與提前參加以 `<details>` 收合；講師看到「你的角色可以查看，不能修改」說明。
- **不得改變**：點名結果與權限（講師唯讀）；完成點名結束場次與追售啟動行為；桌面版表格。

### B-047　空狀態、建專案導向、唯讀說明

- **問題**：空狀態只有一句陳述、沒有下一步；admin 建完專案沒有「前往專案」連結，管理表格內專案名稱不是連結；講師唯讀（點名頁、專案總覽缺待辦區）沒有說明。
- **來源**：ux UX-12、§2.1、§2.5。
- **驗收標準**：空狀態元件＝標題＋一句說明＋主要動作（例：場次空 → 「新增第一個場次」錨到表單；學員空 → 「匯入名單」）；建專案成功訊息含前往專案的連結，管理表格專案名稱可點；唯讀頁面顯示 info 提示。
- **不得改變**：各頁既有內容與權限；訊息文案其他部分。

### B-048　付款對帳動作欄收斂

- **問題**：`project_payments.html:64-109` 單列最多同時有付款連結、入帳、退款、取消，四種動作同樣外觀；付款連結沒有複製按鈕。
- **來源**：ux UX-13。
- **驗收標準**：依訂單狀態呈現主動作；退款與取消收進「更多」並標 danger；付款連結旁有「複製」；各動作的權限與可見性與現況一致。
- **不得改變**：入帳、退款、取消的後端行為、金額與權限；B-040 的確認流程。

### B-049　儀表板重排

- **問題**：`project_detail.html:7-27` 待辦排在統計之後，異常與待辦同卡同外觀；待辦項只有一句文字；專案列表異常數是灰字、不分色；講師看不到待辦區也無說明；`?date=` 正式畫面無標示。
- **來源**：ux UX-21、§2.5；Q14。
- **驗收標準**：今日待辦置於統計卡之前；異常獨立一張卡，使用 warning 樣式與文字「異常」；待辦項有類型標籤（例：課前 3 天／當天）；專案列表異常以 `.badge.bad`、待辦以 `.badge` 顯示；講師顯示說明；`?date=` 若保留則顯示「目前檢視日期」。
- **不得改變**：待辦與異常的計算結果（domain 邏輯）、權限、統計數字。

### B-050　專案設定完成度指引

- **問題**：一個專案要正常運作需完成授權、前端課費用、付款設定、LINE 設定、Jotform 連結與姓名／電話題、至少一個場次，分散在 5 個側欄項目，只有各頁小警示。
- **來源**：ux UX-14、§2.1。
- **驗收標準**：專案總覽（admin／行政管理者）顯示設定進度清單，每項有狀態徽章與連結；全部完成後隱藏；各狀態判定有測試；跨專案隔離。
- **不得改變**：各設定頁的行為與權限；`project_front_course.html` 既有警示。

### B-051　設計系統收斂（一）：token 與元件

- **問題**：`base.html:7-96` 單一內嵌樣式，無間距、字級、狀態色、focus token；133 處行內 `style=`（26 檔）；h2 兩種尺寸；`.badge` 與 `.role` 並用；textarea 與 checkbox 無樣式；11 處 `margin-top: 28px` 對齊 hack。
- **來源**：ux UX-15、§1。
- **驗收標準**：定義 token（間距、字級、圓角、warning／info、focus）與元件類別（`.btn.danger`／`:disabled`／`.sm`、`.table-wrap`、`.form-actions`、textarea／checkbox、`.field-help`、`.badge.warn/.info`）；`.role` 只用於角色；設計規範文件位置依 profile／`/ui-plan` 慣例（展開時由 uiux-designer 決定，產物放 `specs/<pkg>/system-analyze/ui/`）；每次改樣板順手清除行內 style，不做一次性大改；視覺風格不變（前後截圖比對）。
- **不得改變**：既有視覺風格、暗色模式；沒有新框架或靜態檔管線（沿用純 template）。

### B-052　設計系統收斂（二）：共用表單 partial

- **問題**：約 12 個樣板重複 `{% for field in form %}`；`help_text` 不顯示（`project_products.html:48-54` 丟掉「訂金（選填）」「備註」說明）、無必填標記、錯誤無 `aria-describedby`、checkbox 變形（`project_payment_settings.html:15-23`、`project_line_settings.html:19-27`）。
- **來源**：ux UX-19、§1.4（表單）、§4.1。
- **驗收標準**：新增 `_field.html`，渲染 label、必填標記、說明、錯誤與 aria 屬性，checkbox 走另一分支；逐頁改用；渲染測試證明 `help_text` 出現、必填有標記。
- **不得改變**：表單欄位、驗證與儲存行為；既有表單的 POST 欄位名稱。

### B-053　列表分頁、篩選與載入量

- **問題**：學員、付款、報名紀錄無分頁；SITEMAP 要求學員「搜尋／標籤篩選」，現只有搜尋；場次列表缺狀態（已結束／額滿）與分組；通知紀錄在 `views.py:1240` 靜默截斷 200 筆；`project_list` 逐專案跑 `build_dashboard`、`session_facts` 載入專案全部場次與報名；頁面有 3 次以上重複的成員／專案查詢。
- **來源**：ux UX-20、§2.1；arch F-10（儀表板列）、F-11、§6 瓶頸 1。
- **驗收標準**：三個列表每頁 50 筆並保留篩選條件；學員可依標籤篩選；場次列表分「即將開課」「已結束」並有狀態徽章；截斷處顯示「僅顯示最近 200 筆」；儀表板查詢量不再隨歷史場次線性增長（以查詢數測試斷言）；重複的成員／專案查詢減少（查詢數測試）。
- **不得改變**：各列表的資料內容、權限與跨專案隔離；既有搜尋行為；儀表板統計數字。
- **備註**：展開時建議拆成 2–3 個 package（分頁篩選／場次狀態／效能）。

### B-054　導覽一致性

- **問題**：麵包屑格式不一（「所有專案 / 專案」、「專案 / 場次」、「← 所有專案」）；有側欄後多半與側欄重複；頂欄「系統管理」無目前頁樣式；品牌、頁面標題、麵包屑對「專案列表」三種名稱。
- **來源**：ux UX-22、§1.4（導覽）、§3.2。
- **驗收標準**：麵包屑統一為「所有專案 / 專案名 / 區段 / 目前頁」，有側欄頁精簡為上層；頂欄目前頁有樣式；專案列表名稱一致。
- **不得改變**：路由、權限、側欄結構。

### B-055　request 內外部呼叫改為 outbox

- **問題**：一鍵發完款提醒（`views.py:1456-1465`）、重送（`:1264-1279`）、通知頁 render 時 `get_quota`（`:1255`）、場次異動後同步 Jotform（`:277,391,413`）、立即同步（`:574-593`）、導向（`:1497-1502`）都在 request 內同步外部呼叫；Dockerfile 以 `runserver` 單程序，大量發送會佔住請求。
- **來源**：arch F-7、A-10（前半）、§6 瓶頸 3。
- **驗收標準**（展開時由 architect 與 uiux 細化）：request 只建立 `OutboundMessage(PENDING)`，由排程發送；使用者看到「已排入發送」與之後的結果狀態；發送結果與失敗重送沿用；測試以 fake LINE 驗證。
- **不得改變**：發送內容、額度保護、冪等與重送；憲法 MUST 10（發送前重驗，依 B-008）；交易內不呼叫外部。
- **限制**：互動模式改變，需使用者確認接受「稍後顯示」（Q7）。

### B-056　SITEMAP 原定頁面（僅限仍要做者）

- **問題**：SITEMAP 規劃但未實作：跨專案總覽（獨立權限，`permissions.py` 無對應 Action）、學員詳情彙整頁（付款、改期、標籤歷程、追售發送紀錄）、金流回報（webhook）紀錄頁、專案設定的排程時間規則（目前寫死 T-3/2/1 與 D1/3/7）。
- **來源**：arch §4.2、A-14、Q5。
- **驗收標準**：待 Q5 回答後逐頁以 `/specify` 定義；本項在 Q5 之前不得展開；回答為「不做」者由 B-037 在 SITEMAP 標註。
- **不得改變**：既有權限矩陣與路由。

### B-057　放寬 `OTHER_SESSION` 規則

- **問題**：`registration.py:277-283`：學員在專案內有任一其他場次報名（含已結束場次）就轉人工，而 `Registration` 在場次結束後不會清除，實務上改期或重新報名持續製造人工負擔。
- **來源**：arch F-5、A-15。
- **驗收標準**（Q20 定稿並有資料支持後）：只比對未結束場次；已結束場次的舊報名不再觸發人工；測試含改期、重複報名、舊場次沒到後重新報名；重複報名不被誤自動建單。
- **不得改變**：004 其他四種人工原因；提交去重；同名同電話沿用學員。

### B-058　Jotform 傳輸層共用模組

- **問題**：`jotform/client.py:137` 為了 `urllib_transport` 匯入 `crm.line.client`，Jotform 依賴 LINE 模組。
- **來源**：arch §1.2（重點觀察 2）、D-9、A-11（附帶）。
- **驗收標準**：傳輸層抽到共用模組（如 `crm/http.py`）；Jotform 與 LINE 都從共用模組匯入，兩者互不依賴；行為與逾時值不變；`make codemap` 後無 STALE。
- **不得改變**：兩個 client 的對外介面、可注入傳輸層、fake 實作、`TIMEOUT_SECONDS`；測試全數通過且不被修改以遷就（僅匯入路徑）。

### B-059　表單內的建立邏輯下沉

- **問題**：`forms.py:68-78` `ProjectForm.save`、`:126-133` `MemberForm.save` 在 form 內建立多個物件。
- **來源**：arch F-10（forms 列）、D-8。
- **驗收標準**：建立邏輯移到服務層函式，form 只負責驗證；專案與成員建立結果（含團隊、授權、預設前端課）與現行一致；測試通過。
- **不得改變**：表單欄位與驗證、成功與失敗的訊息、權限。

### B-060　`views.py` 拆成套件

- **問題**：`views.py` 1592 行、約 60 個 view、匯入 30+ 模組，承載 8 個功能域；`project_reschedule_confirm`（`:1092-1131`）、`project_payments`（`:677-720`）、`project_session_detail`（`:298-328`）含業務判斷與組裝。
- **來源**：arch F-10、A-11、D-8。
- **驗收標準**：依功能域拆成 `views/` 套件，`urls.py` 的路由名稱與路徑不變；純搬移，測試**不修改**（僅匯入路徑除外）即全數通過；上述含業務判斷的 view 把判斷下沉服務層（可拆為後續步驟）；`make codemap` 後無 STALE。
- **不得改變**：所有 URL、權限判定、回應內容、messages；任何行為。
- **排程**：必須排在所有動 `views.py`／`urls.py` 的項目之後，執行期間凍結其他 views.py 變更。
