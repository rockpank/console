# 工作計畫：teacher-crm

> 維護者：`project-manager`（切分模式；批次 1 收尾由更新模式標記完成）。最後更新：2026-11-17。批次 1 共三條平行線（B-004、B-005、B-027）；另附「執行佇列」（整份 backlog 的接續順序與衝突鏈）。不開 worktree、不寫程式。
> 依據：`backlog.md`（B-004、B-005 列與項目說明）、`profile.md` 路線判準、`.agents/skills/quickfix/RULES.md` Rule 1，以及對目標 repo 的唯讀確認（`project_student_edit.html`、`project_follow_ups.html`、`views.py` 對應 view、`tests/db/test_manual_tags.py`、`tests/db/test_student_edit.py`、`tests/db/test_follow_ups_page.py`、`docs/code_map/templates.md`、`routes.md`）。

## 批次

| 批次 | 任務（批內可平行） | 說明 |
|---|---|---|
| 1（**完成，2026-11-17**） | B-004、B-005、B-027（第三條線，見「任務 B-027」；與前兩者檔案完全不重疊：只動 `tests/`，無樣板、無產品碼） | 以下為 B-004、B-005 的原切分說明；B-027 為純補測，檔案範圍見其任務段。批內平行數 3（上限）。兩任務可平行（各自 worktree、各自 `COMPOSE_PROJECT_NAME`）。理由：(1) 檔案完全不重疊：B-004 只動 `project_student_edit.html`＋`tests/db/test_manual_tags.py`（及可能的 `tests/db/test_student_edit.py`），B-005 只動 `project_follow_ups.html`＋`tests/db/test_follow_ups_page.py`；(2) 兩者都不動 `models.py`／migrations、`views.py`、`urls.py`、`settings.py`、`base.html`；(3) 兩者都無依賴、無待決（Q）阻擋；(4) 唯一共同點是 backlog 標的「與 B-007 衝突」，B-007 排在兩者之後、本批不含；(5) 兩者交付後各自需 `make codemap`（樣板行數變動），但產生物更新在合併時以最後一次 `make codemap` 為準，不在平行期間互相依賴。批內平行數 2（≤ 3 上限）。 |

**批次 1 完成紀錄（2026-11-17）**：三任務資安、QA 皆通過，各自 commit 於自己的分支，未 push、未合併。

| 任務 | 分支／commit | 規格 | 資安／QA | 測試（提供 `JOTFORM_API_KEY` 假值時） |
|---|---|---|---|---|
| B-004 | `t-B-004`（80cf8a4） | `specs/006-fix-student-edit-tags-in-title/` | 通過／通過 | 906 通過（基線 903＋3） |
| B-005 | `t-B-005`（a8738aa） | `specs/007-fix-follow-ups-duplicate-invite-section/` | 通過／通過 | 903 通過（調整既有測試，數量不變） |
| B-027 | `t-B-027`（6dcb9a6） | `specs/008-fix-gateway-callback-parse-tests/` | 通過／通過 | 921 通過（基線 903＋18） |

未提供該金鑰時 `make test` 各有 2 個既有失敗（P-1，與三任務無關，見 `status.md`）。commit 編號取自調度者回報，未在本次另行查證。批次 1 完成後依使用者指示暫停開新 worktree，待合併後依下方「執行佇列」補位。兩個預覽站（B-004 `:8100`、B-005 `:8101`）仍在執行，待使用者驗收後以 `bin/console site rm <任務> -p teacher-crm` 停。

注意（合併階段）：`docs/code_map/` 為產生物，兩條分支各自 `make codemap` 後合併可能在同一份 `templates.md`／`manifest.json` 衝突；合併者於合併完成後重跑一次 `make codemap` 取代手動解衝突（不手改地圖）。

## 任務 B-004

| 欄位 | 內容 |
|---|---|
| 任務代號 | `B-004`（worktree `worktrees/B-004/teacher-crm/`，分支 `t-B-004`） |
| 標題 | 學員編輯頁標籤區落在 `<title>` 內，補閉合並搬到內容區 |
| 路線 | **快速路線**（`/quickfix` → `/implement`），資格逐條核對如下 |
| 依賴 | 無 |
| 規格編號 | **006**。套件名建議 `specs/006-fix-student-edit-tags-in-title/`（`quickfix.md`＋`tasks.md`，命名依 quickfix 命名判準 `<NNN>-fix-<slug>`）。**註：backlog 寫「從 005 起」，但目標 repo 已存在 `specs/005-secure-config-defaults/`（B-001 的產物，未確認其是否已提交），故 B-004 配 006；其餘任務之後請從 007 起配號。** |
| 工程師／角色 | pm（`/quickfix`）→ engineer（`/implement`）→ security-reviewer（輕量，確認權限與跨專案行為未變）→ qa-engineer |

### 路線判定：快速（確認，非僅「候選」）

| quickfix Rule 1 條件 | 判定 | 依據 |
|---|---|---|
| 1. 可寫成 1–3 個預期行為 | 成立 | 預期行為 3 個：(a) `<title>` 只含「編輯學員｜專案名」；(b) 標籤區（標籤清單、新增標籤、標籤紀錄）與訊息顯示在頁面本體；(c) 在該頁新增「改期」標籤後改期頁可見該學員（既有行為，由測試固定） |
| 2. 不改 `models.py` | 成立 | 純樣板修正，view 已提供 `tags`、`tag_events` 等 context，不需動 |
| 3. 不新增 URL／頁面／外部整合／排程 | 成立 | 沿用既有 `project_student_edit`、`project_student_tag_add`、`project_student_tag_remove` 三條路由 |
| 4. 不改權限規則 | 成立 | `EDIT_DATA` 判定維持；講師仍 403 |
| 5. 不推翻既有 FR | 成立 | 實作不符預期（標籤功能在畫面消失），屬「實作不符」而非改 FR；`/quickfix` Phase 1 若查到規格明定別處再議（現行無對應 FR，「對應需求」寫「現行行為：…」並引用 backlog 說明） |

### 檔案範圍（唯讀確認結果）

| 類別 | 檔案 | 動作 |
|---|---|---|
| 樣板 | `src/crm/templates/crm/project_student_edit.html`（58 行） | 第 2 行 `{% block title %}` 補 `{% endblock %}`，標題只留「編輯學員｜{{ project.name }}」；原第 3–29 行（標籤 `<h2>`、`messages` 迴圈、標籤卡片、標籤紀錄）搬進 `{% block content %}` 內；原第 30 行多餘的 `{% endblock %}` 移除。放置位置（編輯表單前或後、與「改期紀錄」的相對順序）由 `/quickfix` 決定，建議表單之後、「改期紀錄」之前 |
| 測試 | `tests/db/test_manual_tags.py`（Modify：既有 `test_student_edit_page_shows_tags_and_tag_history` 第 139–141 行的斷言因為字串剛好在 `<title>` 內而「偶然通過」，需 ALIGN 成斷言出現在頁面本體）；`tests/db/test_student_edit.py`（Add：`<title>` 內容斷言，可併入同檔或擇一，由 `/quickfix` 切片決定） | 只改測試檔，不降低門檻、不加 skip |
| view／urls／models／migration | `views.py`、`urls.py`、`models.py` | **不動**（`project_student_edit` 為 views.py L430–448，僅唯讀確認其 context 含 `tags`、`tag_events`） |
| 共用檔 | `base.html`（`{% block title %}` 在第 6 行、`{% block content %}` 在第 128 行） | **不動**（只唯讀確認區塊名稱） |
| 地圖 | `docs/code_map/` | 不手改；交付後 `make codemap`（樣板行數 58 變動，可能 STALE），再 `make codemap-check` |

### 注意（給 `/quickfix` 與工程師）

- 原第 4 行的 `messages` 迴圈也在 `<title>` 內：標籤新增／移除後的成功與錯誤訊息，目前在此頁同樣看不到。搬到本體後，`messages` 為一次性消耗，須確認同一頁面**只渲染一次**（`base.html` 若已渲染 messages 則不可重複；請先查 `base.html` 再決定是否保留該迴圈）。這點是 B-007（訊息元件統一）的相鄰範圍，B-004 只負責「不重複、不遺失」，不處理綠色／錯誤樣式。
- 「編輯學員」表單 POST 成功後會 redirect 到學員列表並帶成功訊息（既有行為，不動）。
- `test_wording.py` 會掃描樣板用語：搬動區塊時用語維持原樣（含「標籤」，不引入舊稱）。

### 驗收標準

1. 以行政角色 GET 學員編輯頁：`<title>` 只含「編輯學員｜專案名」，不含「標籤」「新增標籤」「標籤紀錄」；頁面本體（`<title>` 之外）含「標籤」「新增標籤」「標籤紀錄」。以解析 HTML 或擷取 `<title>…</title>` 與 `<body>` 分段斷言，不能只做整頁子字串比對（整頁比對正是舊測試偶然通過的原因）。
2. 在該頁以 POST 新增「改期」標籤成功（導回編輯頁），重新 GET 後標籤出現在本體；改期頁（`project_reschedule`）可看到該學員。
3. 渲染測試斷言「新增標籤」出現在頁面本體；講師 GET／POST 編輯頁仍為 403。
4. 標籤新增或移除後導回編輯頁，成功／錯誤訊息在頁面上恰好出現一次。
5. 共通回歸：`make lint`、`make test`（903 項不得變少或被改弱）、`make manage cmd="check"`、`make manage cmd="makemigrations --check --dry-run"`（必須無遷移）、覆蓋率 ≥ 95%、`make codemap` 後 `make codemap-check` 無 STALE。

### 不得改變的既有行為

- `project_student_tag_add`／`project_student_tag_remove` 的 POST 端點、權限（`EDIT_DATA`）與跨專案 404（`test_tag_changes_of_other_project_return_404` 等既有測試維持）。
- 付款相關標籤由系統管理、不可手動新增或移除（頁面上的說明文字保留）。
- 學員編輯表單的欄位、驗證（電話正規化、同專案同姓名電話重複）與儲存行為；儲存後導向學員列表。
- 「改期紀錄」區塊內容與既有測試（`test_student_edit_page_shows_reschedule_history`）。
- 講師看不到編輯連結、編輯頁 403；A 專案成員讀不到 B 專案學員（404）。
- 憲法 MUST 4／5：專案隔離與伺服器端權限不受影響（本修正不新增資料存取）。

## 任務 B-005

| 欄位 | 內容 |
|---|---|
| 任務代號 | `B-005`（worktree `worktrees/B-005/teacher-crm/`，分支 `t-B-005`） |
| 標題 | 追售名單「待邀請出席」整段重複，刪除重複的一份 |
| 路線 | **快速路線**（`/quickfix` → `/implement`），資格逐條核對如下 |
| 依賴 | 無（backlog 依賴欄僅有「衝突：project_follow_ups.html（與 B-007）」與「說明文字部分待決：Q11（不阻擋去重）」；B-007 不在本批，Q11 屬範圍外，見下） |
| 規格編號 | **007**。套件名建議 `specs/007-fix-follow-ups-duplicate-invite-section/`（`quickfix.md`＋`tasks.md`，命名依 `<NNN>-fix-<slug>`） |
| 工程師／角色 | pm（`/quickfix`）→ engineer（`/implement`）→ security-reviewer（輕量，確認權限與跨專案行為未變）→ qa-engineer |

### 為何選 B-005，與被排除的主要候選

選擇依據（對照調度者的 5 項條件）：

| 條件 | B-005 |
|---|---|
| 1. 與 B-004 檔案不重疊 | 成立：只動 `project_follow_ups.html`＋`tests/db/test_follow_ups_page.py`；B-004 動 `project_student_edit.html`＋`tests/db/test_manual_tags.py`。backlog 標的衝突對象僅 B-007 |
| 2. 不動 model／共用熱點 | 成立：純樣板；`views.py` 的 `project_follow_ups`（L1427–1440，`to_invite` 在 L1434）只唯讀確認、不改 |
| 3. 無待決阻擋、不需外部服務 | 成立：Q11 只影響「說明文字（這群人該做什麼）」，backlog 明記「不在本項、不阻擋去重」；本任務**不新增任何說明文字** |
| 4. 依賴 | 無未完成前置項目 |
| 5. 快速、價值高、S、低風險 | 成立：backlog 價值高、成本 S、風險低；刪除樣板中完全相同的 10 行 |

被排除的候選：

| 候選 | 排除理由 |
|---|---|
| B-006（現場報名「已現場收款」不得預設勾選） | **不是缺陷而是現行規格**：`specs/TEST_LIST.md:901` 明定「預設勾選『已現場收款』」，且既有測試 `tests/db/test_attendance_pages.py:314` 斷言 `name="paid" checked`；修改等於改 FR（`/quickfix` Rule 1-5 不符，需 `/clarify` 或規格修訂，並涉及金額記錄）。backlog 亦註明「若有則屬改規格，需回報調度者」。建議另行請使用者決定 |
| B-007（訊息元件統一） | backlog 標與 B-004 衝突（base.html 與約 20 個樣板）；約 20 檔，也不屬 S |
| B-027／B-028／B-033／B-036（補測、測試衛生） | 檔案不重疊且可平行，但屬補測／衛生類，價值次於缺陷修正；B-027／B-028 若測出缺陷會轉出新項目，結果不確定，不利「這輪完成並可驗證」。列為後續批次候選 |
| B-009、B-025、B-026 | 需動 `views.py`／`importer.py`／`orders.py` 等共用或業務檔，違反條件 2 |
| B-002、B-003、B-001 | 動 `settings.py`／`checkout.py`／`forms.py`；B-003 另待 Q8 |
| B-037 | 動 `specs/`，且部分待決 Q5；與 B-001 產生的 `specs/005-*` 區域可能碰撞，且序列於 B-038（pm 同一人） |
| B-044 | 動 `urls.py` 與新增樣板，屬共用熱點 |

### 路線判定：快速（確認，非僅「候選」）

| quickfix Rule 1 條件 | 判定 | 依據 |
|---|---|---|
| 1. 可寫成 1–3 個預期行為 | 成立 | 預期行為 2 個：(a) 追售名單頁「待邀請出席（N）」標題與名單只出現一次；(b) 「追售中」「進階未完款」「已停止」區塊與按鈕維持原樣 |
| 2. 不改 `models.py` | 成立 | 純樣板；view 與 `students_to_invite(project)`（`followups.py`）不動 |
| 3. 不新增 URL／頁面／外部整合／排程 | 成立 | 沿用既有 `project_follow_ups` 路由 |
| 4. 不改權限規則 | 成立 | 講師唯讀、行政專員以上可停止追售與提醒完款，維持不變 |
| 5. 不推翻既有 FR | 成立 | TEST_LIST L979／L982 規定追售頁顯示追售中、待邀請出席、進階未完款、已停止四類名單，各一份；重複是實作瑕疵（複製貼上），去重後符合 FR。`/quickfix` Phase 1 若發現不同，再議 |

### 檔案範圍（唯讀確認結果）

| 類別 | 檔案 | 動作 |
|---|---|---|
| 樣板 | `src/crm/templates/crm/project_follow_ups.html`（84 行） | 刪除第 45–54 行（與第 35–44 行逐字相同的第二份「待邀請出席」`<h2>`＋名單／空狀態）；其餘不動。第 9 行 `messages` 迴圈、第 10 行說明文字、第 13 行警示樣式皆**不動**（屬 B-007／Q11 範圍） |
| 測試 | `tests/db/test_follow_ups_page.py`（Modify／Add） | 新增渲染斷言：`content.count("待邀請出席") == 1`（以整頁 `<h2>` 出現次數斷言）；既有 `test_follow_ups_page_lists_absent_students_to_invite`（L54–65）以 `content.split("待邀請出席")[1]` 取段落，去重後該段會一路延伸到頁尾而非只到重複的第二個標題，需 ALIGN：改以「待邀請出席」到「進階未完款」之間的區段斷言，維持「缺席者在、到場者不在」意圖。只改測試檔，不降低門檻、不加 skip |
| view／urls／models／migration | `views.py`、`urls.py`、`models.py`、`followups.py` | **不動** |
| 共用檔 | `base.html`、`_line_state.html` | **不動**（`_line_state.html` 只被唯讀引用） |
| 地圖 | `docs/code_map/` | 不手改；交付後 `make codemap`（樣板 84 行變動，可能 STALE），再 `make codemap-check` |

### 注意（給 `/quickfix` 與工程師）

- 重複的兩段完全相同，刪哪一份都可；建議保留第 35–44 行（第一份），使區塊順序為「追售中 → 待邀請出席 → 進階未完款 → 已停止」。
- Q11（「待邀請出席」預期動作與說明文字）**不在本任務**：不新增說明文字、不新增按鈕；若 `/quickfix` 覺得需要補說明，屬範圍外，回報調度者另開項目。
- `test_wording.py` 會掃描樣板用語：刪除重複段落不引入新字串。
- 與 B-004 平行期間，B-005 不得碰 `project_student_edit.html`、`tests/db/test_manual_tags.py`、`tests/db/test_student_edit.py`。

### 驗收標準

1. 以行政角色 GET 追售名單頁：整頁「待邀請出席（N）」標題只出現一次（`content.count("待邀請出席") == 1`），名單（或「沒有待邀請的學員。」）只出現一份；N 為 `to_invite` 的人數。
2. 「待邀請出席」區塊內容：未出席學員（帶「未出席前端課」標籤者）在名單內、到場學員不在；以「待邀請出席」與下一個標題「進階未完款」之間的區段斷言。
3. 「追售中」「進階未完款」「已停止」區塊的標題、名單與「停止追售」「提醒完款」按鈕維持原樣（既有測試全部維持，不改弱）。
4. 講師 GET 仍可看（唯讀、無按鈕）；A 專案成員讀不到 B 專案追售頁（404，沿用既有測試）。
5. 共通回歸：`make lint`、`make test`（903 項不得變少或被改弱；可增加）、`make manage cmd="check"`、`make manage cmd="makemigrations --check --dry-run"`（必須無遷移）、覆蓋率 ≥ 95%、`make codemap` 後 `make codemap-check` 無 STALE。

### 不得改變的既有行為

- 名單內容與排序（`active_follow_ups`、`students_to_invite`、`stopped_follow_ups` 與 `unsettled` 的結果與順序）。
- `project_follow_up_stop`（停止追售）與 `project_follow_up_remind`（提醒完款）的端點、權限（行政專員以上；講師唯讀）、同日不重複發送。
- 追售頁的 LINE 綁定狀態顯示、沒點名警示（`no_roll_call`）、說明文字與 `messages` 顯示。
- 憲法 MUST 4／5：專案隔離與伺服器端權限不受影響（本修正不新增資料存取）。

## 任務 B-027

| 欄位 | 內容 |
|---|---|
| 任務代號 | `B-027`（worktree `worktrees/B-027/teacher-crm/`，分支 `t-B-027`） |
| 標題 | 補測：金流回報（藍新／綠界）解析異常路徑一律 `InvalidCallback`、端點 400、訂單與付款嘗試狀態不變 |
| 路線 | **快速路線（候選）**（`/quickfix` → `/implement`）。純補測、不改產品碼、不改 model；最終由 `/quickfix` Phase 1 判資格，若判定「補測不屬 quickfix 範圍」則轉精簡完整路線（tasks 清單），規格編號不變 |
| 依賴 | 無（backlog 依賴欄為「—」） |
| 規格編號 | **008**。套件名建議 `specs/008-test-gateway-callback-parse-errors/`（`quickfix.md`＋`tasks.md`，`<NNN>-<slug>`；補測類是否沿用 `fix-` 前綴由 `/quickfix` 決定） |
| 工程師／角色 | pm（`/quickfix`）→ engineer（`/implement`）→ security-reviewer（輕量：確認金流驗簽與冪等未被動到，且測試無真實金鑰）→ qa-engineer |

### 為何選 B-027（第三條線）

| 條件 | B-027 |
|---|---|
| 與 B-004、B-005 檔案不重疊 | 成立：只動 `tests/unit/`（兩個金流測試檔）與 `tests/db/` 新檔；B-004 動 `project_student_edit.html`＋`tests/db/test_manual_tags.py`（可能含 `test_student_edit.py`），B-005 動 `project_follow_ups.html`＋`tests/db/test_follow_ups_page.py` |
| 不動 model／migration、共用熱點 | 成立：不動 `models.py`、`views.py`、`urls.py`、`settings.py`、`checkout.py`、`base.html`、任何產品碼 |
| 無待決 Q、無未完成依賴、不需外部服務或授權 | 成立：測試只用輸入字串與假金鑰，不連真實綠界／藍新 |
| 快速、價值高、S、低風險 | 成立：backlog 價值高、成本 S、風險低；且屬金額／驗簽路徑的測試缺口（憲法 MUST 8、9），純加測試，回歸風險最小 |

被排除的其他不衝突候選：B-028（價值高、S，但補的是 `forms.py` 驗證，其測試與 B-002（改 `GatewaySettingsForm`）可能同改 `tests/db/test_gateway_settings.py`，留待佇列）；B-033（價值中）；B-036（價值低）；B-029（成本 M，範圍大，宜獨佔一條線時再做）；B-058（價值低、重構）。

### 檔案範圍（唯讀確認結果）

| 類別 | 檔案 | 動作 |
|---|---|---|
| 單元測試 | `tests/unit/test_newebpay_gateway.py`、`tests/unit/test_ecpay_gateway.py`（既有，現有 `parse_callback` 驗簽與正常路徑測試） | Add：新增案例；若 `/quickfix` 判斷新檔較佳，可改放新檔（如 `tests/unit/test_gateway_callback_parse_errors.py`），**不得改動既有案例**。涵蓋：藍新 `Result` 為字串 JSON／內容無法解析（`newebpay.py` 約 L100、L102–103）、金額非數字（約 L111–112）；綠界缺欄位或欄位格式不正確（`ecpay.py` 約 L98–99）。行號為評估時位置，以現況為準 |
| 資料庫測試 | **新檔** `tests/db/test_gateway_notify_invalid_payload.py`（建議；避免與 `tests/db/test_provider_flows.py`、`test_checkout.py` 重疊，B-002、B-003 之後會改這些檔） | Add：至少一個端點案例，對 `/gateway/notify/<project_id>/` 送上述異常回報 → 400，`Order`、`PaymentAttempt`、`Payment` 狀態不變；另加「A 專案端點收到異常回報不影響 B 專案訂單」（憲法 MUST 4） |
| 產品碼／model／migration | `gateways/*.py`、`checkout.py`、`views.py`、`models.py` | **不動**（`views.py` L857 `except InvalidCallback` 僅唯讀確認）。若測出缺陷：不順手修，回報調度者另開 backlog 缺陷項 |
| 地圖 | `docs/code_map/` | 不手改；僅加測試通常不需 `make codemap`，交付時仍跑 `make codemap-check` 確認無 STALE |

### 驗收標準

1. 藍新：`Result` 為字串形式 JSON、內容無法解析、金額非數字、缺必要欄位，各有一個 `tests/unit` 案例，皆拋 `InvalidCallback`；綠界：缺欄位或欄位格式不正確（如金額非數字）案例亦然。
2. 至少一個 `tests/db` 端點案例：異常回報 → HTTP 400，訂單狀態、付款嘗試狀態、付款紀錄筆數皆與送出前相同。
3. 跨專案案例：對 A 專案端點送異常回報，B 專案資料不變。
4. `gateways/newebpay.py`、`gateways/ecpay.py` 上述分支覆蓋率達 100%（以 `make coverage` 的 missing 行確認，記錄於回報）。
5. 測試資料全為假資料與假金鑰；不出現真實商店代號、金鑰；不 skip／xfail。
6. 共通回歸：`make lint`、`make test`（903 項不得變少或被改弱；應增加）、`make manage cmd="check"`、`make manage cmd="makemigrations --check --dry-run"`、覆蓋率 ≥ 95%（預期上升）、`make codemap-check` 無 STALE。

### 不得改變的既有行為

- 既有驗簽、商店代號核對、金額核對與冪等行為（只加測試，不改產品碼）；所有既有測試不修改、不刪減。
- 重複成功通知只入帳一次（憲法 #9）；`UNAPPLIED` 分支；模擬付款在正式模式被拒。

### 注意

- 與 B-003（失敗通知鎖終態，待 Q8）的測試檔分開：本任務新測試放新檔，B-003 之後改 `tests/db/test_checkout.py`／`test_provider_flows.py` 時不會與它衝突。
- B-004、B-005 平行期間，B-027 不得碰 `project_student_edit.html`、`project_follow_ups.html` 與它們的測試檔。

## 執行佇列（整份 backlog）

> 依使用者指示：批次 1 完成後暫停開新 worktree，待使用者合併並決定後再補位。

> 範圍：backlog 全部 60 項，扣除批次 1 的 B-004、B-005、B-027，其餘 57 項。分類結果：a 可自動執行 31 項、b 需使用者決定／授權 21 項、c 依賴未完成 5 項（31＋21＋5＝57）。依據：`backlog.md` 項目表的「依賴」「路線」欄、「待使用者決定」Q1–Q20、「檔案與 model／migration 衝突」一節；檔案範圍為粗估（依 backlog 文字，未通讀程式），實際以各任務 `/quickfix`、`/system-analyze` 的結果為準。
> 規格編號：從 009 起，只替 a 類預留；b、c 類於解除後從 042 起接續配號。完整路線可能拆成多個套件者已註明預留數。B-001 的 `specs/005-secure-config-defaults/` 已存在（含 spec、plan、checklist），進度與是否已提交**未確認**，列為既有編號不另配。
> 通則：每個任務開工前執行 `usage --guard`（額度達標即暫停，不自行解除）；每個任務各自 worktree 與 `COMPOSE_PROJECT_NAME`；所有任務都會 `make codemap`，`docs/code_map/` 合併衝突一律由合併者重跑 `make codemap`，不視為檔案衝突；b、c 類不得自動進入實作。

### a. 可自動執行（依建議順序）

「model」欄：否＝預期不動 `models.py`／migration；是＝佔用 model 通道（一次一個任務）。「衝突／序列」中的「需等 X 被合併」＝在使用者合併 X 之前不得開工。

| 序 | ID | 路線 | 預期檔案範圍 | model | 規格編號 | 衝突／序列 |
|---|---|---|---|---|---|---|
| 1 | B-001 | 完整（精簡 spec） | `settings.py`、`crypto.py`、`compose.yaml`、`ci.yml`、`.env.example`、設定與 CI 相關測試 | 否 | 005（既有） | 設定鏈首位：與 B-002、B-014、B-017、B-022、B-034 衝突。Q7 運維動作不阻擋程式修改 |
| 2 | B-002 | 快速 | `forms.py`（`GatewaySettingsForm`）、`checkout.py`／`get_gateway`、`views.py`（`fake_checkout`／`fake_complete`）、`settings.py`（旗標讀取）、對應測試 | 否 | 009 | 需等 B-001 被合併（設定鏈）；與 B-003（b）、B-009（`forms.py`）衝突；佔 views.py 通道 |
| 3 | B-008 | 完整 | `line/notifications.py`、新增 domain 純函式、通知頁樣板、`tests/unit`＋`tests/db` | 預期否；若需新欄位記略過原因 → 佔 model 通道，**需等 B-024 被合併**後再開 | 010 | 通知鏈首位：B-008 → B-032 → B-031（→ B-011、B-055，b 類）；不碰 `views.py` 時可與 B-024 並行 |
| 4 | B-024 | 完整 | `models.py`、`migrations/`、`orders.py`、`views.py`（收款、退款、取消）、付款頁樣板、`forms.py` | **是（model 通道第一位）** | 011 | 佔 model 通道與 views.py 通道；與 B-026（`orders.py`）、B-042（付款頁樣板，條件式）、B-012／B-010／B-020（b 類，model 序列）衝突 |
| 5 | B-007 | 快速（候選） | `base.html`＋約 20 個樣板（**含 B-004、B-005 動過的 `project_student_edit.html`、`project_follow_ups.html`**） | 否 | 012 | **需等 B-004、B-005 被合併**；base.html 鏈首位。backlog 原寫「在 B-006 之後」，B-006 現為待決（見 b），改為先做 B-007，B-006 解除後再接 |
| 6 | B-009 | 快速（候選） | `domain/line.py`、`views.py`（`line_webhook`）、`forms.py`（LINE 模式設定） | 否 | 013 | views.py 通道；`forms.py` 與 B-002 衝突 |
| 7 | B-014 | 完整 | `settings.py`（cache）、`views.py`（`jotform_return`／`jotform_webhook`／`pay_page`、登入）、`urls.py`、可能 `createcachetable`（不產生 migration） | 預期否（若 architect 改採計數表 → 佔 model 通道） | 014 | 需等 B-001（settings）；views.py／urls.py 通道；為 B-045、B-015（b）的前置 |
| 8 | B-017 | 完整 | `crypto.py`、`views.py`（`pay_page`、`line_webhook`）、新增 management command | 否 | 015 | 需等 B-001（`crypto.py`）；views.py 通道 |
| 9 | B-025 | 快速（候選） | `importer.py`、`views.py`（匯入單一區段） | 否 | 016 | views.py 通道 |
| 10 | B-026 | 快速（候選） | `attendance.py`、`orders.py`、對應測試 | 否 | 017 | `orders.py` 需等 B-024 被合併；與 B-012（b）序列 |
| 11 | B-028 | 快速（補測） | `tests/`（表單驗證、人工建單無前端課費用；新測試放新檔） | 否 | 018 | 無產品檔衝突；新檔以避開 B-002 可能改動的 `tests/db/test_gateway_settings.py` |
| 12 | B-029 | 快速（補測，成本 M，可拆兩包） | `tests/`（缺口路由跨專案、專案一致性巡檢；新檔） | 否 | 019 | 無檔案衝突；測出缺陷另開項，不順手修 |
| 13 | B-033 | 快速（補測） | `tests/`（management command 參數、同日場次、已處理提交、立即同步提示） | 否 | 020 | 無檔案衝突 |
| 14 | B-034 | 快速（候選） | `pyproject.toml`、`Makefile`、`ci.yml`、`tests/unit/test_ci_workflows.py`（只增不減） | 否 | 021 | 需等 B-001 被合併（`ci.yml`）；與 B-016、B-018（b）序列；若啟用分支覆蓋後低於 95%，先補測，不得降門檻 |
| 15 | B-036 | 快速（候選） | `tests/db/test_jotform_session_hooks.py` | 否 | 022 | 無檔案衝突 |
| 16 | B-058 | 快速（候選；被判非 bug 則精簡完整） | `jotform/client.py`、`line/client.py`、新增共用傳輸模組 | 否 | 023 | 無熱點衝突（不碰 `notifications.py`）；之後 `make codemap` |
| 17 | B-037 | 快速（文件） | `specs/` 各套件狀態欄、`SITEMAP.md`、`TEST_LIST.md`、`TDD_PROGRESS.md` | 否 | 不配（純文件） | 只做不依賴 Q5 的部分（四個缺頁標「做／不做」延後）；與 B-038（b）同由 pm 序列；若 B-006 解除後改 `TEST_LIST.md` 需序列 |
| 18 | B-039 | 快速（候選） | `project_nav.py`、多個樣板、`views.py`（docstring 與一行字串） | 否 | 024 | **需等 B-004、B-005、B-007 被合併**；base.html／樣板鏈與 views.py 通道 |
| 19 | B-041 | 快速（候選） | `base.html`、`project_students`／`products`／`jotform_submissions`／`detail` 等表格樣板 | 否 | 025 | 需等 B-007 被合併；base.html 鏈 |
| 20 | B-042 | 快速（候選） | `base.html`（共用處理中腳本）、少數表單樣板（`project_jotform_settings`、付款相關） | 否 | 026 | base.html 鏈；若 `/quickfix` 確認未動 `project_payments.html`，可與 B-024 同時；否則需等 B-024 被合併 |
| 21 | B-044 | 快速（候選；被判新增頁面則完整） | `urls.py`（handler）、新 `403/404/500.html`、`views.py`（`pay_page` 失效連結簡化頁） | 否 | 027 | views.py／urls.py 通道；Q15（客服文案）不阻擋，先用中性文字 |
| 22 | B-022 | 完整（「統一回應」可拆快速） | `views.py`、`base.html`、`settings.py`、CSP 設定 | 否 | 028–029（預留 2） | 需等 B-001；views.py 通道與 base.html 鏈；webhook 密鑰移標頭需 Jotform 支援，該部分若無法確認則排除並回報 |
| 23 | B-031 | 快速（補測） | `tests/`（webhook 建單 → LINE 綁定 → 付款提醒串接） | 否 | 030 | 需等 B-008 被合併（避免補舊行為） |
| 24 | B-032 | 快速（補測） | `tests/`（LINE 外送路徑） | 否 | 031 | 需等 B-008、B-009 被合併 |
| 25 | B-050 | 完整 | `views.py`（`project_detail`）、`project_detail.html` | 否 | 032 | views.py 通道；與 B-049（b）序列 |
| 26 | B-043 | 完整（超過 3 個行為，可拆 2–3 包） | `base.html`、多個樣板、登入頁 | 否 | 033–035（預留 3） | base.html 鏈；需等 B-007、B-041、B-042 被合併 |
| 27 | B-051 | 完整（`/ui-plan` 由 uiux-designer） | `base.html`、設計 token、元件類別、樣板行內 style | 否 | 036–037（預留 2） | base.html 鏈；需等 B-007、B-041、B-042、B-043 被合併 |
| 28 | B-054 | 快速（候選） | `base.html`、多個樣板（麵包屑、頂欄） | 否 | 038 | base.html 鏈 |
| 29 | B-047 | 快速（候選） | 多個樣板（students、sessions、payments、manage_projects 等） | 否 | 039 | 需等 B-041、B-051 被合併 |
| 30 | B-052 | 完整 | 共用 `_field.html`、約 12 個樣板、登入頁 | 否 | 040 | 需等 B-051 被合併 |
| 31 | B-045 | 完整 | `pay.html`、`views.py`（`pay_page`） | 否 | 041 | 需等 B-014、B-042、B-044 被合併；Q15 文案不阻擋，先用中性文字 |

### b. 需使用者決定或授權才能做（21 項）

| ID | 卡在 | 一句話 |
|---|---|---|
| B-003 | Q8 | 需向綠界／藍新確認同單號失敗後可否重試，確認前不得改狀態機（可先寫重現測試）。 |
| B-006 | 新決定（無 Q 編號） | 「已現場收款」預設勾選是現行規格（`TEST_LIST.md:901`、`test_attendance_pages.py:314`），改它等於改規格，且涉及金額記錄，需使用者拍板。 |
| B-010 | Q3 | 要「禁止刪除」「軟刪除」還是「允許但留稽核」，決定快速或完整與是否動 model。 |
| B-011 | Q2（且需 B-008） | 每日排程由誰跑、幾點、漏跑補發回溯幾天。 |
| B-012 | Q1 | 名額計算口徑與是否允許超收，需 `/clarify` 先答。 |
| B-013 | Q10（且需 B-003） | 行政專員可否確認入帳、退款、取消，及待辦區顯示給誰。 |
| B-015 | Q18（且需 B-014） | 004 既定的「已有訂單可重複導向」是否保留（改 004 的 FR）。 |
| B-016 | Q7（且需 B-001） | 部署形態（HTTPS 代理、正式環境）尚未確認完整，Q7 只部分回覆。 |
| B-018 | Q19 | 需授權在可連網環境執行 `pip-audit` 並指定執行者。 |
| B-019 | Q12 | 成員管理要補到什麼範圍（停用／重設密碼／改角色）。 |
| B-020 | Q9 | LINE 綁定強化方式（一次性綁定碼、次數限制或維持現狀）是產品決策。 |
| B-021 | Q17 | 專案「停用」是隱藏還是停止營運，語意未定。 |
| B-023 | Q4 | 講師是否仍可看付款頁（改權限規則）。 |
| B-035 | Q6（授權） | 需使用者授權與測試帳號才能連真實外部服務，工程師不得自行跑 `make test-integration`。 |
| B-038 | Q6（且需 B-035） | 需真實 Jotform 實測結果與 `JOTFORM_TIMEZONE` 是否為最終決定。 |
| B-040 | Q10（且需 B-007） | 同 Q10，確認流程涉及誰能做入帳／退款。 |
| B-046 | Q16（且需 B-041、B-006） | 現場點名是否主要用手機，決定卡片列或僅橫向捲動。 |
| B-049 | Q14（且需 B-013） | `?date=` 覆寫「今天」的參數是否保留。 |
| B-055 | Q7（且需 B-008、B-011） | outbox 的急迫度與互動由「立即」變「稍後」需產品確認。 |
| B-056 | Q5 | SITEMAP 四個原定頁面「做」或「不做」。 |
| B-057 | Q20 | 是否放寬 `OTHER_SESSION`，並先蒐集待人工原因分佈。 |

### c. 依賴未完成（5 項）

| ID | 依賴 | 說明 |
|---|---|---|
| B-030 | B-012（名額案例）、B-003（付款回報案例）、B-008（通知案例） | 三組案例各在對應項目完成後補；上游皆在 b 或需合併，故整項暫不開。 |
| B-048 | B-013、B-040 | 與兩者同動 `project_payments.html`，序列於後，兩者皆在 b。 |
| B-053 | B-013、B-049 | 同動 dashboard，序列於後，兩者皆在 b；建議展開時再拆 2–3 包。 |
| B-059 | B-002、B-019 | 在兩者之後（同動 `forms.py`）；B-019 在 b。 |
| B-060 | 所有動 `views.py`／`urls.py` 的項目 | 必須最後單獨做，期間凍結其他 views.py 變更；完成後 `make codemap`、跑全部品質關卡。 |

### 在使用者尚未合併任何分支的前提下

規則：已完成但未合併的任務所占檔案，之後與它重疊的任務不能開工；`views.py`、`settings.py`、`base.html`、`models.py` 一律視為整檔占用（保守，不以 hunk 判斷）。

**彼此檔案不衝突、可連續自動做完（約 9 項確定＋1 項條件式，加批次 1 的 3 項，共約 13 項）**，建議接續順序（任一條線完成就取下一個，額度保護優先）：

1. B-001（設定鏈）
2. B-008（通知鏈；若 architect 確認需新欄位，改排在 B-024 被合併之後）
3. B-024（model 通道與 views.py 通道的唯一占用者）
4. B-028、B-029、B-033、B-036（純補測，新檔，互不重疊）
5. B-058（兩個 client 檔）
6. B-037（只做不依賴 Q5 的部分）
7. 條件式：B-042（僅在 `/quickfix` 確認未動付款頁樣板時；但做了它，base.html 鏈其餘全部要等合併）

model 通道：整段時間只有 B-024 一個任務；B-012、B-010、B-020（b）與條件式的 B-008 都排在它被合併之後。

**因與已完成項目重疊而必須等合併的最大衝突鏈**（每鏈未合併前只能做鏈首一項）：

| 鏈 | 成員（a 類）；b／c 類另註 | 說明 |
|---|---|---|
| V：`views.py`／`orders.py`／`urls.py`（最大） | B-024、B-002、B-009、B-014、B-017、B-025、B-026、B-044、B-022、B-039、B-050、B-045（12 項）；b／c：B-010、012、013、015、016、019、020、021、023、040、046、049、053、055、056、057，終點 B-060 | 本批僅 B-024 先做；其餘每合併一項才能開下一項（若不合併，最多一項） |
| T：`base.html`／共用樣板 | B-007、B-039、B-041、B-042、B-043、B-051、B-054、B-047、B-052、B-022（10 項；加上 B-004、B-005 的樣板為 B-007 的前置） | B-007 要等 B-004、B-005 合併；條件式 B-042 可先做但會鎖住其餘 |
| C：`settings.py`／`crypto.py`／`ci.yml` | B-001、B-002、B-014、B-017、B-022、B-034（6 項）；b：B-016、B-018 | 本批僅 B-001；B-002 起全部等 B-001 合併 |
| N：`line/notifications.py`＋其補測 | B-008、B-032、B-031（3 項）；b：B-011、B-055 | 本批僅 B-008；B-031、B-032 為補測但依賴改後行為，必須等合併 |
| M：model 通道 | B-024（a）；b：B-012、B-010、B-020；條件式 B-008 | 一次一個 |
| S：`specs/` 與 `TEST_LIST.md` | B-037（a）；b：B-006、B-038 | 文件鏈，序列於 pm |

備註：(1) 若調度者可使用「疊分支」（`t-<後項>` 由未合併的 `t-<前項>` 開出）則鏈內可繼續往下做，但合併順序必須與疊的順序一致，且 B-004／B-005／B-027 之外的任務是否允許這樣做需使用者同意（目前 `bin/console wt add` 以起點分支開，未確認支援）；本計畫預設**不疊**。(2) 條件式與「預期否」的 model 判斷，在各任務 `/system-analyze`／`/quickfix` 後若改變，調度者須重排。

## 需要使用者決定

最多 5 項（其餘見上方 b 類表）：

1. **合併時機**：批次 1（B-004、B-005、B-027）完成並通過資安與 QA 後，請使用者合併；B-007 → B-039／B-041 起的樣板鏈、以及 views.py／設定鏈後續項目都在等合併。合併越晚，可自動做完的項目上限越低（約 13 項）。
2. **B-001 的現況**：repo 已有 `specs/005-secure-config-defaults/`，是否為 B-001 的進行中產物、是否已提交（影響佇列第 1 項與設定鏈）。
3. **B-006**：「已現場收款」預設勾選是規格而非缺陷，要不要改規格（影響 B-046）。
4. **一次回答可解鎖最多的 Q**：Q10（B-013、B-040、B-048、B-049、B-053）、Q1（B-012、B-030）、Q8（B-003）、Q3（B-010）、Q2（B-011、B-055）。
5. **是否允許「疊分支」以突破合併等待**（見上方備註 1）。

提醒（不阻擋）：規格編號 005 已被 B-001 占用，B-004＝006、B-005＝007、B-027＝008，佇列從 009 起；B-004 段落內「其餘任務請從 007 起配號」為舊文字，以本節為準。
