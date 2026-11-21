# 專案狀態總表：teacher-crm

> 維護者：`project-manager`（部分由調度者代寫）。最後更新：2026-11-21（**最新計數，以此為準：共 61 項＝已合併並 push 23＋完成待合併 1（B-014）＋待辦 37＋規劃中 0＋開發中 0＋擱置 0；2026-11-21 B-039 已合併、master 8 個提交已 push（8e4f73f..418249d，origin/master＝master），B-011、B-026、B-002、B-007、B-031、B-032、B-034、B-037 一併更正為已合併，依 merge-plan 與調度者 git 核對；本檔較早段落的 22／60／待合併 8 等數字皆為當時紀錄**；前次：B-014 完成待合併，見「B-014 收尾（批次 25）」；前次 2026-11-18：14 項已合併並 push 到 origin/master，合併後全套驗證 lint／check／無待產生 migration、1234 測試通過、覆蓋率 98.17%（給 JOTFORM_API_KEY 假值；P-1 既有 2 失敗不變），code_map 已重產；批次 25 自動挑選 B-011、B-014、B-026 標「規劃中」；`worktrees/V-1` 因 docker root 檔案刪不掉，待使用者自行清除；本次重算：B-002 依 security-1／qa-1 檔頭 `verdict: 通過`（round 1）與 escalation `resolved: true` 標完成待合併；B-004／005／027 依 merge-plan 查證更正為已合併；前次：B-031、B-032 標完成待合併；全表計數改依 backlog 狀態欄逐列重數，見「Backlog 進度」。前次更新：master 已併入 t-B-001、006、008、009、025、028、029、033、036、042、058 共 11 條分支，其 worktree 已清理、分支保留；內文計數一律以下方「Backlog 進度」為準。下文批次收尾段落中「未 commit／待合併」為當時紀錄，現況以本次更新為準）

## 整體健康度

**有風險**（非受阻）。24 項完成（23 項已合併進 master 並 push；1 項待使用者合併：B-014，worktree 未 commit），皆有資安「通過」與 QA「通過」報告（逐項核對 `tasks/<任務>/security-1.md`、`qa-1.md` 檔頭 `verdict: 通過`）；完成項沒有未結的資安高／嚴重風險或 QA 失敗。風險來源：資安高風險 H-2（B-002）已修並通過資安／QA（待合併，合併前仍屬未進 master）、合併 B-002 後其他分支的 fake 測試可能轉紅（見風險段）、4 項架構高嚴重度落差；14 條分支已合併並 push（合併後全套驗證與 code_map 重產已完成，見上；「11 條分支未 commit」「合併成本累積」風險已解除；換自產金鑰仍屬使用者運維）。品質基線：提供 `JOTFORM_API_KEY` 假值時全套測試通過；未提供時有 2 個既有失敗（P-1，與各任務無關；B-042 impl-notes 另報 2 個失敗，QA 重跑未重現，見事後可瀏覽第 41 項）。依據：`assessment/SUMMARY.md`、`tasks/*/{impl-notes,security-1,qa-1}.md`。

## 階段總覽

| 階段 | 狀態 | 產出 |
|---|---|---|
| 接手登錄 | 完成 | `profile.md`、`engineer-rules.md` |
| 現況評估 | 完成 | `assessment/{architecture,quality,security,ux}.md`、`SUMMARY.md` |
| backlog | 完成（待使用者排序與挑選） | `backlog.md`（61 項） |
| 改善執行 | **現況（2026-11-21）：24 項完成＝23 項已合併並 push＋1 項待合併（B-014）；待辦 37；規劃中 0**。以下為較早紀錄：22 項完成（含待合併 8 項：B-002、B-007、B-014、B-026、B-031、B-032、B-034、B-037）；規劃中 1 項（B-011，批次 25）；其中 14 項已合併進 master 並 push（B-001、B-004、B-005、B-006、B-008、B-009、B-025、B-027、B-028、B-029、B-033、B-036、B-042、B-058；B-004／005／027 依 merge-plan 與 master reflog 於 2026-11-18 核對為已合併，僅存在於 origin 分支），B-001 等 11 條 worktree 已清理、分支保留；8 項完成待使用者合併（B-002、B-007、B-014、B-026、B-031、B-032、B-034、B-037；分支 `t-<任務>`）；0 項開發中。四份升級檔（`tasks/B-001|B-002|B-006|B-008/escalation.md`）檔頭皆 `resolved: true`（B-002 依協議第 8 節「測試前置例外」化解，QA 已認可四項） | `work-plan.md`；三分支 `t-B-004`（80cf8a4）、`t-B-005`（a8738aa）、`t-B-027`（6dcb9a6）已合併（reflog 核對）；14 條已合併分支的 worktree 已清除 |

**環境（2026-11-17）**：中控台已搬到 `/home/user/web/`。批次 1 的 worktree 與預覽站在本機不存在；三分支在 origin 上未合併。**Docker 已可用**（先前「本機無 Docker」的升級已解除，依 `tasks/B-001/impl-notes.md`）。本機**無 `make`**，改用等效的 `docker compose run --rm [--no-deps] app <指令>`（lint、test、manage check）；compose v5 專案名須**小寫**（`COMPOSE_PROJECT_NAME=b-001`，`B-001` 不被接受）。同一任務不可同時兩個寫入者；DB 測試用不同專案名（共用 test DB，並行會出 setup ERROR）。`.claude/settings.json` 已由使用者改為新路徑（調度者已核對三處）。

批次 1 任務明細：

| 任務 | 內容 | 規格 | 資安／QA | 分支狀態 |
|---|---|---|---|---|
| B-004 | 學員編輯頁標籤區移出 `<title>`、搬到內容區 | `specs/006-fix-student-edit-tags-in-title/` | 通過／通過 | 已合併進 master（merge-plan 查證，僅存在於 origin 分支）；預覽站在本機不存在 |
| B-005 | 追售名單「待邀請出席」去重 | `specs/007-fix-follow-ups-duplicate-invite-section/` | 通過／通過 | 已合併進 master（merge-plan 查證，僅存在於 origin 分支）；預覽站在本機不存在 |
| B-027 | 補測：藍新／綠界回報解析異常（新增 18 個測試，`newebpay.py`、`ecpay.py` 覆蓋率 100%，產品碼零變更） | `specs/008-fix-gateway-callback-parse-tests/` | 通過／通過 | 已合併進 master（merge-plan 查證，僅存在於 origin 分支） |

commit 編號取自調度者回報，未另行查證。

## Backlog 進度

共 61 項（2026-11-21 依 `backlog.md` 狀態欄重算並與 merge-plan／調度者 git 事實核對，新增 B-061；本節為準，下方舊段落為當時紀錄）：完成 24（已合併並 push 23＋待合併 1：B-014）、開發中 0、待辦 37、規劃中 0、資安／QA 0、擱置 0；合計 24＋37＝61。狀態詞彙沒有「待合併」，完成項在狀態欄註明合併狀態；已合併者 backlog 狀態欄寫「已合併（已 push；…）」。
註：本次 backlog 狀態更正（B-002、007、011、026、031、032、034、037、039）依 merge-plan 的 `merge-base --is-ancestor` 紀錄與調度者回報；本角色無 Bash，未能自行重跑 `git branch --merged master`。

| 階段 | 數量 |
|---|---|
| 待辦 | 37 |
| 規劃中 | 0（B-011 已合併） |
| 已升級 | 0（B-014 的 escalation 已 `resolved: true`，B-014 已完成；2026-11-21） |
| 開發中 | 0 |
| 資安／QA | 0 |
| 完成 | 24（已合併並 push 23＋待合併 1：B-014；下表分類為 2026-11-18 舊紀錄，其「待合併」八項除 B-014 外現皆已合併） |
| 擱置 | 0（B-006 先前同日曾擱置，已由使用者裁示選 A 取代，現已完成） |

完成項分類（交接檔檔頭核對：security-1、qa-1 `verdict: 通過`；19 項皆齊全、無缺報告）：

| 類別 | 任務 | 備註 |
|---|---|---|
| 完成待合併（8；B-014、B-026、B-037 見各收尾段） | B-002、B-007、B-014、B-026、B-031、B-032、B-034、B-037 | B-002：分支 t-B-002，規格 009，資安／QA 第 1 輪通過（qa-1 已覆寫，先前環境阻擋失敗不算輪次），escalation resolved（協議第 8 節測試前置例外，QA 認可四項），合併須知見風險段；B-007：分支 t-B-007（未 commit），規格 012；B-031：分支 t-B-031，規格 030（資安／QA 第 1 輪通過）；B-032：分支 t-B-032，規格 031（資安／QA 第 1 輪通過，qa-1 檔頭 `verdict: 通過`）；B-034：分支 t-B-034，規格 021 |
| 已合併（B-004、B-005、B-027 已更正） | B-004、B-005、B-027 | 2026-11-18 核對 master reflog 已合併；先前「待合併」過時；B-027 impl-notes `tests: 失敗`＝缺金鑰時 P-1 的 2 個既有失敗 |
| 已合併（11；worktree 已清理，分支保留） | B-001、B-006、B-008、B-009、B-025、B-028、B-029、B-033、B-036、B-042、B-058 | 分支 `t-<任務>` 已併入 master。B-009 仍僅 secret 為空範圍，「非 LINE 模式一律 400」未做（事後可瀏覽第 11 項）。檔頭註記：B-033 impl-notes `tests: 失敗`（P-1 的 2 個既有失敗，QA 通過）；B-042 impl-notes `tests: 失敗`（2 個 jotform_sync 失敗，QA 重跑未重現，qa-1 通過）；B-042 資安為靜態審查 |

依類型（2026-11-18 舊紀錄，數量已過時；現況以上方「Backlog 進度」為準：待辦 37、規劃中 1）：資安 10、缺陷 2（B-003、026）、補完 9（B-010～013、024、030、035、039、056）、優化 16、重構 2（B-059、060）、文件 2。已完成 19（14 項已合併進 master，5 項 B-002／007／031／032／034 待合併）：資安 3（B-001、B-002、B-009）、缺陷 4（B-004、B-005、B-006、B-007）、補完 8（B-008、B-025、B-027、B-028、B-029、B-031、B-032、B-033）、優化 2（B-034、B-042）、重構 2（B-036、B-058）。合計 10＋2＋9＋16＋2＋2＋19＝60。

本批（2026-11-17）同時開發上限經使用者放寬為 5 條（協議第 3 節例外，僅本次）；實際進行 5 條：B-001、B-009、B-028、B-029、B-033；另 B-006 於同批完成（規格 042，快速路線，資安通過／QA 通過，903 通過、覆蓋率 97% 為 engineer 自報、QA 未複驗；變更檔：`project_attendance.html`、`specs/TEST_LIST.md`、`tests/db/test_attendance_pages.py`、`specs/042-fix-onsite-paid-default-unchecked/`、`docs/code_map`（產生物）；依 `tasks/B-006/{impl-notes,security-1,qa-1}.md`）。

本批明細（依各任務 `impl-notes`／`security-1`／`qa-1`）：

| 任務 | 規格 | 測試 | 資安／QA | 備註 |
|---|---|---|---|---|
| B-009 | 013 | 905 通過、覆蓋率 97% | 通過／通過 | 僅 channel secret 為空；「非 LINE 模式一律 400」未做（事後可瀏覽第 11 項） |
| B-028 | 018 | 942 通過（+39）、98% | 通過／通過 | 只新增 2 個測試檔；未測出缺陷 |
| B-029 | 019 | 961 通過（+58）、97% | 通過／通過 | 只新增 5 個測試檔；未測出缺陷；維持快速路線（調度者裁示，約 25→58 個測試函式） |
| B-033 | 020 | 916 通過（+13）、98%（QA，提供假金鑰） | 通過／通過 | 只新增 3 個測試檔，無 migration；impl-notes 檔頭記「失敗」＝缺金鑰時 P-1 的 2 個既有失敗，QA 已印證 |

B-009 明細：LINE webhook 空 channel secret 驗簽必須失敗（sec L-1）；規格 `specs/013-fix-line-webhook-empty-secret/`（沿用預留編號）；快速路線；分支 `t-B-009`，**已合併進 master**，worktree 已清理。實際只改 `src/crm/domain/line.py`（`verify_signature` 加 `not channel_secret` 守衛，views.py 未改）＋新增 unit 案例與 `tests/db/test_line_webhook_empty_secret.py`；RED 修前實測（unit 回 True、webhook 回 200）。資安：通過（無新增發現）；QA：通過（905 通過、0 失敗、覆蓋率 97.44%、ruff 乾淨）。範圍僅 secret 為空，見「事後可瀏覽」第 11 項。依據：`tasks/B-009/{impl-notes,security-1,qa-1}.md`。

B-025：**完成，已合併進 master**，worktree 已清理（快速路線，spec 016，分支 `t-B-025`；912 通過（基線 903，+9）、覆蓋率 97%、roster.py 100%；資安通過／QA 通過；變更：`src/crm/domain/roster.py`、`src/crm/views.py`、`tests/db/test_import_limits.py`、`specs/016-import-size-limits/`、codemap；無 model／migration）。依據：`tasks/B-025/{impl-notes,security-1,qa-1}.md`。

建議先做（來自 backlog，尚未經使用者確認）：B-001 設定預設改失敗即拒絕、B-002 假金流管制、B-003 金流失敗鎖終態（先確認 Q8）、B-008 發送前條件重驗。（B-004 已完成。）

## 批次 4 收尾（B-008、B-036，2026-11-17）

| 任務 | 分支／worktree | 規格 | 結果 | 資安／QA | 狀態 |
|---|---|---|---|---|---|
| B-008 發送前重驗 | `t-B-008`，`worktrees/B-008/teacher-crm/` | 010 | 991 通過（基線 903，+88）、覆蓋率 97.60%；不動 model／migration | 通過／通過 | 完成，**已合併**，worktree 已清理 |
| B-036 測試衛生 | `t-B-036`（worktree 已清理） | 022 | 903 通過 | 通過／通過 | 完成，**已合併** |

依據：`tasks/B-008|B-036/{impl-notes,security-1,qa-1}.md`。`tasks/B-008/escalation.md`（worktree 先前有來源不明變更）檔頭現為 `resolved: true`（2026-11-18 核對）；裁示內容未在本檔記載。計數見「Backlog 進度」。

### 事後可瀏覽（批次 4）

| # | 嚴重度 | 內容 | 來源 |
|---|---|---|---|
| 28 | 中（非使用者拍板的假設） | B-008 三項假設：A-1 完款提醒每學員每日去重（比原 spec 嚴）；A-2 課前 1 天不重驗已付款；A-3 被停止追售者不建立訊息。皆未經使用者拍板，合併前請確認 | B-008 impl-notes |
| 29 | 低 | B-008 低風險：(a) 重送認領成 PENDING 後程序崩潰會卡 PENDING，且重送入口只收 FAILED；(b) 重送未傳 today，日界可能不一致；(c) 重驗到發送有極小 TOCTOU 窗口（LINE retry key 24 小時內去重）；(d) 並行重送輸家 flash 文字為「重送仍然失敗：待發送」；(e) 未在 PostgreSQL 驗證 `select_for_update` 並行（QA 以全套測試通過為準） | B-008 impl-notes、security-1、qa-1 |
| 30 | 低 | B-008 改了既有測試 `test_staff_can_retry_failed_message` 的場次日期（今天+3），斷言未動；QA 認為合理（固定日期 2026-11-07 已過期） | B-008 impl-notes、qa-1 |
| 31 | 低 | B-008 新增 `_skip_stale_pending`（sync 開頭掃殘留 pending）；QA 認為在 FR-001 範圍內 | B-008 impl-notes、qa-1 |
| 32 | 低 | B-036：本機全專案 `ruff check .` 有 22 個既有錯誤，不在本任務範圍（QA 未重跑） | B-036 qa-1 |
| 33 | 資訊（環境） | 兩任務本機無 make，改用 `docker compose run` | 兩任務 notes |
| 34 | 低 | B-008 測試未帶 testplan 案例 ID，追溯性較差（非必要） | B-008 qa-1 |

**建議立項（待 pm，我不改 backlog 項目內容）**：新增缺陷項「重送認領成 PENDING 後崩潰會卡 PENDING，且重送入口只收 FAILED」（規格需另配號；不在 B-008 擴大範圍；與 B-011／B-032／B-055 同動 `line/notifications.py`，需序列）。第 29 項 (b) 可一併。

## 批次 5 收尾（B-058，2026-11-17）

| 任務 | 分支／worktree | 規格 | 結果 | 資安／QA | 狀態 |
|---|---|---|---|---|---|
| B-058 Jotform 傳輸層共用模組 | `t-B-058`，`worktrees/B-058/teacher-crm/` | 023（精簡完整路線；/quickfix 判快速資格不符而轉） | 905 通過（基線 903＋2 新案例）、覆蓋率 97%；變更：`src/crm/http.py`（新）、`line/client.py`、`jotform/client.py`、`tests/unit/test_line_transport.py`＋`specs/023`＋codemap | 通過／通過 | 完成，**已合併**，worktree 已清理 |

依據：`tasks/B-058/{plan-notes,tasks-notes,testplan-notes,impl-notes,security-1,qa-1}.md`。計數見「Backlog 進度」。

B-008 升級（worktree 有來源不明未提交變更）：`tasks/B-008/escalation.md` 檔頭現為 `resolved: true`。

事後可瀏覽（批次 5）：第 35 項（低）B-058 的 Jotform 預設 transport 路徑無測試涵蓋（新測試僅涵蓋 LINE 傳輸）。

### 覆盤（批次 5）

- 上一批調整有沒有效：未驗證（本批未針對上一批流程調整做對照）。
- 這批新缺點：快速資格判定對純重構必定不符，auto 挑選時應直接標精簡完整路線並預先授權 qa 寫 Keep／Modify testplan；pm／security 角色無 Bash，validate 與測試重跑要調度者代跑；本機無 pytest，資安無法重跑測試。
- 下一批要改：(1) 挑選純重構項時直接標精簡完整路線並預授權 qa testplan；(2) 調度者在 pm／security 階段前先備好 validate 與測試結果。
- 工具呼叫（實際／預算）：pm 規劃 8／25＋9／10＋5／10、qa testplan 8／25、engineer 16／80、security 3／20、qa 12／30、自動挑選 pm 5／25，無超支。

## 批次 6 收尾（B-025，2026-11-17）

B-025 名單匯入上限：完成，未 commit（見上方 B-025 段）。

### 事後可瀏覽（批次 6）

| # | 嚴重度 | 內容 | 來源 |
|---|---|---|---|
| 36 | 低 | 資安 L-1：電話格式錯誤訊息回顯原值（`電話格式不正確：{值}`），僅回應放大、無 XSS；建議截斷約 30 字（可選） | B-025 security-1 |
| 37 | 低（資訊） | 資安 L-2：2 MB 檢查在 Django 收完上傳之後；請求體上限應由反向代理（如 nginx client_max_body_size）設定，屬部署層 | B-025 security-1 |
| 38 | 資訊 | 預覽站未啟動，以測試驗證（端到端未執行） | B-025 qa-1 |
| 39 | 資訊 | `roster.py` 為範圍追加（原 work-plan 未列、pm 判定必動），已由調度者確認 | B-025 impl-notes |
| 40 | 低 | 與未合併的 B-008 於 `views.py` 不同區段（B-008 僅 flash 文字），合併者確認無衝突 | work-plan 批次 6 |

### 覆盤（批次 6）

- 上一批調整有沒有效：未驗證（本批無對照證據；批次 5 的兩項改法未見於 B-025 notes）。
- 這批新缺點：pm 無 Bash 無法跑 validate，由調度者代跑；engineer 本機無 make，改用 docker compose run；資安無 pytest／DB 環境，未能跑測試（僅以 python 直接呼叫解析器驗證）。
- 下一批要改：(1) 調度者在 pm 與資安階段前備好 validate 與測試結果；(2) 資安階段附上 QA 或 engineer 的測試輸出供引用。
- 工具呼叫（實際／預算）：pm 16／25、project-manager 規劃 9／25、engineer 29／80、資安 4／20、QA 8／30，無超支。

## 批次 7 收尾（B-042，2026-11-17）

| 任務 | 分支／worktree | 規格 | 結果 | 資安／QA | 狀態 |
|---|---|---|---|---|---|
| B-042 防連點與處理中狀態 | `t-B-042`，`worktrees/B-042/teacher-crm/` | 026 | QA 908 通過；變更為 base.html 全站事件委派 script＋測試 | 通過（靜態審查，環境無 pytest）／通過 | 完成，**已合併**，worktree 已清理 |

依據：`tasks/B-042/{pm-notes,impl-notes,security-1,qa-1}.md`。base.html 鏈：B-007、B-041、B-043、B-051、B-054 須等本項合併。

### 事後可瀏覽（批次 7）

| # | 嚴重度 | 內容 | 來源 |
|---|---|---|---|
| 41 | 中（未驗證） | 工程師回報 2 個 jotform_sync 失敗，QA 重跑未重現；根因未驗證，疑間歇或環境差異（與 P-1 缺金鑰是否同源未確認） | impl-notes、qa-1 |
| 42 | 中（未自動化） | 瀏覽器連點停用與 bfcache 返回還原按鈕狀態未自動化，需人工驗收 | qa-1 |
| 43 | 低（限制） | 連結式送出與 JS `form.submit()` 不受保護（後端冪等仍是最終防線） | qa-1、security-1 |
| 44 | 低 | tasks.md 的 [X] 未回寫 | qa-1 |
| 45 | 資訊（前瞻） | 日後若導入 CSP，base.html 的 inline script 需 nonce 或外移 | security-1 |
| 46 | 資訊 | 資安為靜態審查（環境無 pytest）；host 無 make 與 pytest | security-1 |

### 覆盤（批次 7）

- 上一批調整有沒有效：未驗證（批次 6 提的「調度者先備好 validate 與測試輸出」在本批 notes 未見對照證據）。
- 這批新缺點：pm 超支（26／25），因 validator 案例 ID 只認 BE-API／SVC／CMD／TASK、FE-E2E、JOURNEY，用 BE-VIEW 命名改了兩輪；host 無 make 與 pytest，資安僅能靜態審查。
- 下一批要改：(1) quickfix 的 pm 提示預先寫明案例 ID 命名限制（BE-API／SVC／CMD／TASK、FE-E2E、JOURNEY）；(2) 資安階段附上 QA／engineer 測試輸出供引用（沿用批次 6 未落實項）。流程檔本次未改（未動即無需備份）。
- 工具呼叫（實際／預算）：pm 26／25（超支）、engineer 16／80、資安 5／20、QA 8／30、project-manager 6／25（挑選階段）。

## 批次 13 收尾（B-007，2026-11-18；本次自動派工實際只做 B-007）

| 任務 | 分支 | 規格 | 結果 | 資安／QA | 狀態 |
|---|---|---|---|---|---|
| B-007 訊息元件統一 | `t-B-007` | 012 | 915 通過、覆蓋率 97% | 通過（security-1）／通過（qa-1） | 完成，未 commit，待使用者合併；預覽站 http://localhost:8100/ 仍開著，停用請 `bin/console site rm B-007 -p teacher-crm` |

驗證限制：預覽站僅確認 302，UI 未實際操作。B-002、B-031、B-032 由另一個自動派工（dev-teacher-crm-b104717）同時開 worktree 處理，本次未派；work-plan 因此有兩份「批次 13」。

**批次 13 進度（2026-11-18 更新，依檔頭）**：B-007 完成待合併；B-031 完成待合併（資安／QA 第 1 輪通過）；B-032 完成待合併（資安／QA 第 1 輪通過）；B-002 已完成待合併（資安／QA 第 1 輪通過，escalation resolved）。批次 13 三項（B-002／031／032）：3 完成。

### 事後可瀏覽（批次 13）

| # | 嚴重度 | 內容 | 來源 |
|---|---|---|---|
| 47 | 低 | jotform 設定頁 localhost 提醒維持 `role="alert"`（規格寫 note，QA 判合理）；建議規格註明例外 | qa-1 |
| 48 | 低 | `project_access.html` 殘留空 `{% if messages %}{% endif %}` | B-007 驗證 |
| 49 | 低（非本任務範圍） | 既有 `.alert.ok` 亮色對比 4.48，略低於 4.5 | B-007 驗證 |
| 50 | 資訊 | `worktrees/V-1/` 用途不明 | 調度者回報 |
| 51 | 低 | B-002 資安 L-1：`forms.py:376-381` 沿用既有已存金鑰時不檢查長度，歷史短 HashKey（< 32）可繼續啟用；僅旗標開啟（開發／測試環境）相關，對 H-2 無影響。建議沿用時解密後同樣檢查，或記為已知限制 | B-002 security-1 |
| 52 | 資訊 | B-002 資安 L-2：長度檢查只擋太短、不檢查熵（32 個相同字元可通過）；限旗標開啟環境，可接受 | B-002 security-1 |
| 53 | 低 | B-002 QA 觀察 1：HashKey 長度以 UTF-8 位元組計，規格寫「字元」，全形字元會以較少字數通過 | B-002 qa-1 |
| 54 | 低 | B-002 QA 觀察 2：新測試未逐一斷言「旗標開且非 fake 時 `card_available` 為 False」的舊文案 | B-002 qa-1 |

### 覆盤（批次 13）

- 上一批調整有沒有效：有。批次 12 起以 master reflog 核對合併狀態，本批據以發現 B-004／005／027 已合併（證據：work-plan 批次 13 與 reflog）。
- 這批新缺點：多個自動派工並行時，work-plan 批次號重複（兩份批次 13）、挑選重疊（B-002／B-031 同被兩邊挑到）。
- 下一批要改：派工前先核對既有 worktree 與 `runtime/auto-dispatch.log`，再挑選。
- 工具呼叫（實際／預算）：pm 22／25、engineer 24／80、資安 3／20、QA 12／30、本次規劃 pm 12／25。

## 批次 14 收尾（B-034，2026-11-18）

| 任務 | 分支 | 規格 | 結果 | 資安／QA | 狀態 |
|---|---|---|---|---|---|
| B-034 分支覆蓋率與門檻一致 | `t-B-034` | 021 | 新增 2 測；全量 903 通過、2 失敗（P-1，缺假金鑰；加 `JOTFORM_API_KEY` 假值該檔 11 全過）；總覆蓋率（含分支）96.55%（engineer）／97%（QA，4178 stmts／119 miss、948 branch／52 partial），門檻 95% 可過、無須補測 | 通過／通過 | 完成但尚待使用者合併 |

變更：`pyproject.toml`（`branch = true`）、`Makefile`（coverage 加 `--cov-fail-under=95`，與 `ci.yml` 一致，ci.yml 未改）、新檔 `tests/unit/test_coverage_settings.py`、specs/021、code_map；`src/` 無變更。驗證限制：QA 未跑 lint（engineer 稱 ruff check／format 通過，未經 QA 複驗）；`tests/integration` 未跑。依據：`tasks/B-034/{impl-notes,security-1,qa-1}.md`。

- 另立項建議：(a) 讓 `tests/db/test_jotform_sync_command.py` 兩測不依賴真實金鑰（P-1，即事後可瀏覽第 1 項；目前 `make coverage` 因此兩測會回非 0）；(b) 低覆蓋補測候選：`jotform/sync.py` 79%、`process_finished_sessions` 83%、`process_jotform_submissions` 88%、`line/service` 90%、`gateways/base` 90%（QA 列為候選，不影響門檻）。
- 未動 B-002、B-031、B-032 狀態（有未解 escalation，待使用者裁示）。

### 覆盤（批次 14）

- 上一批調整有沒有效：有。批次 13 提出「派工前先核對既有 worktree 與 auto-dispatch.log 再挑選」，本批挑選明確排除 B-002／B-031／B-032／B-007 且未與之重疊（證據：work-plan 批次 14 自動挑選紀錄）。
- 這批新缺點：P-1 兩個既有失敗使 `make coverage` 在無假金鑰時回非 0，門檻改動無法端到端驗證；QA 未跑 lint，lint 結果僅 engineer 自報。
- 下一批要改：(1) 立項修 P-1，讓測試自備金鑰；(2) QA 指令清單納入 ruff check／format --check。
- 工具呼叫（實際／預算）：pm 9／25、engineer 12／80、資安 5／20、QA 5／30、plan 階段 pm 挑選 9／25。

## B-002／B-031／B-032 進度（2026-11-18，依各任務檔頭；dev-teacher-crm-b104717）

| 任務 | 階段 | 依據 |
|---|---|---|
| B-002 假金流管制 | 資安通過、QA 通過（均第 1 輪；qa-1 已覆寫，上一版環境阻擋失敗不算輪次）；完成，分支 t-B-002（規格 009）待合併。升級已 resolved（協議第 8 節測試前置例外，QA 認可四項）；H-2 已修 | `tasks/B-002/{security-1,qa-1}.md` 檔頭 `verdict: 通過`；`escalation.md` `resolved: true` |
| B-031 補測 webhook→LINE 付款提醒 | 資安通過、QA 通過（均第 1 輪）；完成，分支 t-B-031 待合併 | `tasks/B-031/{security-1,qa-1}.md` 檔頭 `verdict: 通過` |
| B-032 補測 LINE 外送路徑 | 資安通過、QA 通過（均第 1 輪）；完成，分支 t-B-032（規格 031）待合併 | `tasks/B-032/{security-1,qa-1}.md` 檔頭 `verdict: 通過` |

## 自動派工（事實，來自調度者回報與 `runtime/auto-dispatch.log`，不推測）

- 看板「自動派工」已啟用，駐列 4；由專案管理員從 `backlog.md` 待辦挑項目補派。
- `runtime/auto-dispatch.log` 顯示 2026-11-17 19:xx 至 2026-11-18 08:06 共多次派工。
- tmux 目前有 6 個 `dev-teacher-crm-b…` 對話。
- 本次重算時 `backlog.md` 無開發中項目（B-002 已完成待合併）；`work-plan.md` 批次 8（2026-11-18）記「沒有可挑的項目」；批次 17（本次，0 項）見 work-plan。

## 批次 21 收尾（B-037，2026-11-18）

| 任務 | 分支 | 結果 | 資安／QA | 狀態 |
|---|---|---|---|---|
| B-037 規格狀態欄與 SITEMAP 校正 | `t-B-037` | 純文件（specs／SITEMAP）；測試未執行（impl-notes `tests: 未執行`，validate_artifacts 已跑） | 通過／通過（第 1 輪） | 完成（待使用者合併）；backlog 已標「完成（待使用者合併）」 |

計數：完成 20（已合併 14＋待合併 6：B-002、B-007、B-031、B-032、B-034、B-037），待辦 40，共 60（上方「Backlog 進度」表尚為 19／41，以本段為準）。依據：`tasks/B-037/{impl-notes,security-1,qa-1}.md`。

### 事後可瀏覽（批次 21）

| # | 嚴重度 | 內容 | 來源 |
|---|---|---|---|
| 55 | 低（QA 缺陷 D1，未修、不阻擋） | worktree 的 `specs/SITEMAP.md` 約第 283 行替換出錯，應為「上文原誤植的「JOSTFOTM」即此服務 Jotform」 | B-037 qa-1 |
| 56 | 低（驗收放寬） | 規劃驗收「CASCADE 警示消失」做不到：`validate_artifacts.py` 只要 python block 含 `on_delete=models.CASCADE` 就警示；驗收已放寬 | B-037 notes |
| 57 | 中（待使用者決定） | SITEMAP 標題「銷講課程行政系統」是否改為「前端課程行政系統」 | B-037 |
| 58 | 低（合併留意） | `specs/TEST_LIST.md` 與 B-006 同檔，合併留意順序 | work-plan |
| 59 | 資訊 | 規格 004 的 3 個 `[NEEDS CLARIFICATION]` 屬 B-038 保留，本項未處理 | B-037 |

### 覆盤（批次 21）

- 上一批調整有沒有效：未驗證（批次 22 前無對照證據）。
- 這批新缺點：B-037 在批次 20 被挑但從未開工，worktree 空轉，批次 21 重新挑中才實作。
- 下一批要改：(1) 挑選後核對任務是否真的開工（`tasks/<任務>/` 與 worktree），未開工者在下批前清掉或接續；(2) 驗收條件寫成 validator 實際能達成的形式。
- 工具呼叫（實際／預算）：自動挑選 PM 8／25、規劃 pm 16／25、engineer 6／50、資安 5／20、QA 5／30，皆未超支。

### B-026 收尾（批次 25，2026-11-18）

B-026 完成待使用者合併（分支 `t-B-026`，規格 045，快速路線）；backlog 狀態欄為準。無 escalation；impl-notes done、tests 通過；security-1、qa-1 `verdict: 通過`（第 1 輪；全套 1301 通過、覆蓋率 98.17%）。變更（未 commit）：`src/crm/attendance.py`、`src/crm/orders.py`、新增 `tests/db/test_concurrent_duplicate_friendly_error.py`、`specs/045-fix-concurrent-duplicate-friendly-error/`；`views.py` 未動。

### 事後可瀏覽（批次 25：B-026）

| # | 嚴重度 | 內容 | 來源 |
|---|---|---|---|
| 60 | 中（資安 M-1） | `register_walk_in` 把所有 `OrderError` 一律轉成「重複操作」訊息，會掩蓋已取消訂單等真實問題 | B-026 security-1 |
| 61 | 中（資安 M-2） | `IntegrityError` 一律視為併發重複，且未記錄日誌 | B-026 security-1 |
| 62 | 中（資安 M-3） | Jotform 路徑 `order_no` 撞號時，例外型別由 `IntegrityError` 變 `OrderError`，呼叫端是否妥善處理：待確認 | B-026 security-1 |
| 63 | 低（QA L-1） | 無 view 層案例 | B-026 qa-1 |
| 64 | 低（QA L-2） | `make codemap-check` 未執行，合併收尾需確認（本機無 make，需等效指令） | B-026 qa-1 |

另立項建議（pm 風格簡列，不擴大 B-026 範圍，**尚未進 backlog**，待使用者同意由 pm 立項）：
- 缺陷（中）：`register_walk_in` 只應把真正的併發重複轉友善訊息，其餘 `OrderError`（如已取消訂單）須保留原訊息（M-1）。
- 缺陷（中）：`IntegrityError` 需區分重複來源並記錄日誌（M-2）。
- 缺陷（中）：確認 Jotform 呼叫端對 `order_no` 撞號改拋 `OrderError` 的處理，補測（M-3）。
建議三項合併為一個 backlog 項，與 B-012 同檔（`orders.py`）須序列。

### 覆盤（批次 25：B-026）

- 上一批調整有沒有效：未驗證（無對照證據）。
- 這批新缺點：快速路線一輪過，但錯誤處理過寬（一律轉訊息）等 3 項中風險留待事後，驗收條件未要求「只轉真重複」。
- 下一批要改：(1) 錯誤處理類任務的驗收條件寫明「不得吞掉非目標例外、須記日誌」；(2) 收尾前確認 codemap-check 以等效指令實跑。
- 工具呼叫：本次更新 PM 預算 20，見回覆末行。

### B-014 收尾（批次 25，2026-11-21）

B-014 公開端點與登入入口濫用防護：**完成，待使用者合併**（分支 `t-B-014`，worktree `worktrees/B-014/teacher-crm`，規格 044，完整路線）。依據：`tasks/B-014/security-1.md`、`qa-1.md` 檔頭 `verdict: 通過`（皆第 1 輪）；`impl-notes.md` status: done（T001～T165 全勾；全套 1365 passed、覆蓋率 98.23%）；`escalation.md` `resolved: true`（調度者對同 worktree 衝突與 30 分鐘時間窗的裁示，使用者 2026-11-20 回覆「繼續」確認）。work-plan 已標完成。

### 事後可瀏覽（批次 25：B-014）

| # | 嚴重度 | 內容 | 來源 |
|---|---|---|---|
| 65 | 中（待使用者確認部署方式） | 節流／鎖定只取 `REMOTE_ADDR`；若部署在反向代理後且 B-016 未上線，所有訪客共用代理 IP，單一攻擊者即可 DoS 正常學員 | B-014 security-1 |
| 66 | 低 | 快取計數非原子，會少計；鎖定期間正確密碼也拒絕（刻意設計） | B-014 security-1／qa-1 |
| 67 | 低 | 快取失效 fail-open 時防護不生效；建議對 `backend_unavailable` 日誌告警 | B-014 security-1 |
| 68 | 低 | `django.contrib.admin` 仍在 `INSTALLED_APPS`，可後續清理 | B-014 security-1 |
| 69 | 低 | BE-API-52／53 只涵蓋 3 個平台管理頁 | B-014 qa-1 |
| 70 | 低 | BE-API-60 的 429 頁沿用 `jotform_notice`，testplan 文字寫 `pay.html` 錯誤區塊；建議對齊文字 | B-014 qa-1 |
| 71 | 中（部署前必做） | 部署前必須執行 `createcachetable`（採 DB cache，無 migration） | B-014 impl-notes |
| 72 | 低（需使用者動手） | `specs/044-…/_wip/` 舊草稿目錄需使用者手動移除（工具擋 rm） | B-014 impl-notes |

### 覆盤（批次 25：B-014）

- 上一批調整有沒有效：未驗證（本批無對照證據）。
- 這批新缺點：同一 worktree 被兩個調度者同時派工，造成 pm 重編任務被擋、工程師 blocked 一輪；pm／architect 無 Bash，驗證器需調度者代跑，tasks 驗證器兩度 FAIL。工具呼叫（實際／預算）：工程師 70／80、QA 16／30、資安 4／20、pm 9／30、QA 同步 4／20，無超支。
- 下一批要改：(1) 自動派工挑項目前檢查該任務是否已有 escalation 或他人 session 正在做；(2) 規劃角色交付前要求調度者預跑驗證器，或在 prompt 明列驗證規則。流程檔本次未改。

## 批次 28 收尾（B-039 用語統一，2026-11-21）

**更新（2026-11-21，批次 28 已合併並已 push）**：B-039 已 commit、`merge --no-ff` 進 teacher-crm master，程式碼地圖已重產並 commit；master 8 個提交已 push（8e4f73f..418249d，origin/master＝master）。預覽站 8100／8101 已停止。計數見檔頭與「Backlog 進度」：61 項、已合併並 push 23、待合併 1（B-014）、待辦 37、規劃中 0。

**待使用者處理（需提權，非一般決定）**：t-B-007、t-B-039 的 worktree 目錄含 root 擁有的 docker 檔案（.coverage、.pytest_cache、.ruff_cache），`bin/console wt rm` 回 Permission denied（`git worktree` 已半移除）。請以 sudo 刪除 `worktrees/B-007/teacher-crm`、`worktrees/B-039/teacher-crm` 目錄後，在 teacher-crm repo 執行 `git worktree prune`；分支保留。（舊的 `worktrees/V-1` 同因。）

（以下為批次 28 當時紀錄）B-039 完成待合併（分支 `t-B-039`，規格 046，快速路線）。

- 依據：`tasks/B-039/impl-notes.md`（status: done、tests: 通過；1441 passed、覆蓋率 98.19%、lint／check／無待產生 migration 皆過）、`tasks/B-039/qa-1.md`（verdict: 通過，第 1 輪）。資安加派＝否，故無 `security-*.md`，為新流程預期，非缺漏。
- 範圍：側欄「進階課程費用」、動詞統一（新增／儲存）、角色名與設定名不外洩英文、`NT$` 千分位、docstring 舊稱、新增 `docs/wording.md`；「前端課／後端課」標示依使用者裁示範圍外，改列 backlog B-061。

事後可瀏覽（低風險／待辦）：
1. QA 重跑時 `tests/db/test_jotform_sync_command.py` 2 項在沒有 `JOTFORM_API_KEY` 的容器會失敗（既有測試與環境耦合，即 P-1）；建議另開 backlog，讓測試自己設定 settings（尚未立項）。
2. `orders.py` docstring 有「前端課課程」贅字。
3. 「建立訂單」（`project_payments.html`）「會建立學員」（`project_attendance.html`）兩處用語未統一，待 pm 決定（另有測試註解引用「建立訂單」）。
4. 「前端課／後端課」標示：已立 B-061（來源 Q13；動 UI 走完整路線；可能占 model 通道）。
5. `docs/code_map` 為 STALE，合併者需重跑 `python3 scripts/code_map.py update`。
6. 與 B-040、B-041 在樣板上可能衝突，需序列合併。

工具呼叫（實際／預算）：pm 24／25、pm 補修 14／23、engineer 43／80、qa-engineer 16／40，無超支。

### 覆盤（批次 28：B-039）

- 上一批調整有沒有效：有。本輪首次用新流程（QA 含安全檢查、資安僅加派）：QA 單人 16 呼叫／約 45k tokens，無資安報告，第 1 輪驗收通過。
- 這批新缺點：pm 沒有 Bash、無法跑驗證器，quickfix 切片編號兩輪才過，重工約 16%。
- 下一批要改：pm 的 prompt 先附驗證器 CASE_ID 規則，或由調度者在 pm 回報後立刻跑驗證。

## 事後可瀏覽（批次 1 的低／中風險與另立項目建議）

以下皆不阻擋批次 1 的合併。**目前都未進 backlog**（我不改 backlog 項目內容）；建議使用者挑選後由 `pm` 立項，並由 `pm` 配規格編號（009 起已預留給佇列，新項目請另配）。

| # | 嚴重度 | 內容 | 來源 | 建議 |
|---|---|---|---|---|
| 1 | 中（測試隔離，影響所有無 `.env` 的 worktree／CI） | **P-1**：`tests/db/test_jotform_sync_command.py` 的 `test_a_renamed_question_is_found_again_and_the_write_is_retried_once`、`test_when_the_session_question_cannot_be_found_again_the_form_waits_for_the_admin` 缺 `JOTFORM_API_KEY` 環境變數必失敗（輸出含「平台尚未設定 Jotform 金鑰，略過同步」）。**非日期問題**：同日期下提供假金鑰即全過；B-004 與 B-005 impl-notes 推測的「寫死日期」不成立，請勿往那個方向修。根因是兩測試沒用 `tests/db/conftest.py` 的 `platform_key`／`fake_jotform` fixture、也沒設 `settings.JOTFORM_API_KEY` | B-004 qa-1、B-005 qa-1、B-027 qa-1 | 另立項目（成本 S）：讓測試自行設定金鑰；修正前，profile 的「903 通過」基線需註明要有金鑰變數，且合併前不要把這 2 個失敗誤判為批次 1 造成 |
| 2 | 低（資安評為資訊偏低；金額相關，建議另立缺陷項） | **藍新 `Amt` 異常值**：`newebpay.py` 對 JSON 浮點數 `int()` 無聲截斷（`1500.5` 變 1500，字串 `"1500.5"` 卻會被拒，兩者不一致，與憲法 MUST 8 精神不符）；`Amt` 為 `1e999`（解析成 inf）時 `int()` 拋 `OverflowError`，而程式只捕捉 `ValueError`、`TypeError`，使端點回 **500 而非 400**；資安另列 `int(True)`＝1、`"1_500"` 被接受（綠界 `TradeAmt` 的 `"1_500"` 同理）。不構成可被利用的繞過：需先通過驗簽，入帳金額取自伺服器端 `attempt.amount`，`Amt` 只用於相等核對 | B-027 impl-notes 發現 1、security-1「另立項目建議」 | 另立缺陷項：金額解析前拒絕非整數型別、改用 `fullmatch(r"\d+")`、捕捉 `OverflowError`；先補「先紅」測試（`1500.9`、`true`、`1e999`）再修產品碼。B-027 的測試未固化這些現象，修正不會與之衝突 |
| 3 | 低 | **B-004 S-2**：沒有測試斷言標籤新增／移除表單含 `csrfmiddlewaretoken`（Django test client 預設不強制 CSRF，日後有人拿掉 `{% csrf_token %}` 測試不會失敗） | B-004 security-1 | 補一行斷言或用 `Client(enforce_csrf_checks=True)` 的 POST 測試 |
| 4 | 低（外觀） | **B-004 D-1**：標籤卡片的 `<p>` 內含 `<form>`，瀏覽器重組出兩個空 `<p></p>`，標籤列上方多一小段空白；無功能影響、無巢狀 form。僅在桌面寬度（1000px）以 headless Chrome 目視，未測手機寬度與 Safari／Firefox | B-004 qa-1、security-1、impl-notes | 把外殼改成 `<div>`；可併入 B-007 或後續樣板整理（B-007 本來就要動這個樣板） |
| 5 | 資訊 | **B-005**：跨專案隔離測試只驗證頁面 404 與停止 404，沒有直接斷言本專案頁面不含他專案學員姓名（待邀請名單隔離僅由 `for_project` 保證） | B-005 security-1 I-2 | 可併入 B-029（隔離守門補測）；不另立 |
| 6 | 資訊 | **B-005**：追售名單頁對講師角色顯示學員電話（既有行為、屬需求，非本次引入） | B-005 security-1 I-1 | 若要最小揭露，與 B-023（講師可見範圍）一併評估 |
| 7 | 低 | **B-027 F-1**：端點測試（`tests/db/test_gateway_notify_invalid_payload.py`）只斷言狀態碼 400、不看原因，其他原因的 400 也會綠；解析原因由單元測試以訊息關鍵字鎖定，QA 的變異驗證（m8、m9）已證明異常內容確為 400 的原因 | B-027 security-1 F-1、qa-1 | 補斷言回應文字含「無法解析」「欄位」「金額」（價值低、成本 S），可併入下一次動該檔時 |
| 8 | 低／資訊 | **B-027 F-2、F-3**：綠界官方公開沙箱值在 `tests/db` 新檔未註明（`tests/unit` 新檔已註明），日後若導入 secret scanner 需加白名單；隔離測試中 A、B 專案共用同一組假金鑰，偵測不到「B 專案設定被誤用於 A」 | B-027 security-1 | 加一行註解；B 專案改用不同假金鑰（可選） |
| 9 | 資訊（文件落差） | B-027 的 `specs/008-…/quickfix.md` 驗收寫「沒有 `docs/code_map/` 變更、通常不需 `make codemap`」，實況新增測試檔後地圖需更新（6 個產生檔，由 `make codemap` 產生，非手改）；backlog 驗收文字「`Result` 字串形式 JSON 一律 `InvalidCallback`」與實際程式不同（合法 JSON 字串會正常解析），實作已改以「字串但非 JSON」「字串 JSON 缺 `MerchantOrderNo`」案例覆蓋，與 pm 的解讀一致 | B-027 qa-1、impl-notes | 僅知悉；日後 quickfix 範本可提醒「新增測試檔也會動 code map」 |
| 10 | 資訊 | 藍新成功通知缺 `Amt` 時預設為 0，之後由 `handle_gateway_callback` 的金額核對擋下（400）；縱深防禦成立，不列缺陷 | B-027 impl-notes 發現 2 | 無 |
| 11 | 中（待使用者決定） | **B-009 範圍矛盾**：backlog B-009 驗收「非 LINE 模式一律 400」與「既有有效簽章綁定流程不得改變」互相矛盾（假 LINE 模式下以有效簽章走綁定流程，若一律 400 就會被改變）。本次只做空 secret；**假 LINE 模式一律 400 未做，待使用者決定** | B-009 impl-notes | 建議另立 backlog 項（由 `pm` 立項並配規格編號）處理假 LINE 模式 |
| 12 | 資訊（環境） | compose 專案名必須小寫（`COMPOSE_PROJECT_NAME=b-009`，大寫任務代號不被接受）；本機無 `make`，改用 `docker compose run` 執行等價指令（lint、test、manage check） | B-009 impl-notes | 之後任務沿用；`make` 目標在本機無法直接使用 |
| 13 | 低 | **B-028**：`forms.py:251`（`ProductForm.validate_constraints` 空覆寫）實際不會被執行、無法覆蓋；第二個前端課只有表單層案例，缺 HTTP 頁面層案例 | B-028 impl-notes、qa-1 | 另立低優先項：評估移除空覆寫；之後補一個 POST `project_front_course` 在已有前端課時的頁面層案例 |
| 14 | 資訊（待 pm 判斷） | **B-029 資安建議**：以下路由在隔離測試未見：`pay_page`、`pay_return`、`fake_checkout`、`fake_complete`、`jotform_return`、`manage_members`／`manage_teams`／`manage_projects`、`project_list`／`project_detail`。公開端點可能本不以專案 ID 隔離，未確認是否真有缺口 | B-029 security-1 | 由 `pm` 判斷是否真有缺口再立項；不阻擋合併 |
| 15 | 資訊（文件落差，已更正） | B-029：engineer 稱「code map `src.crm.md` 原有落差」不成立；QA 比對後該檔變動只是 `tests:` 反向連結（因新測試檔），src 無變動 | B-029 qa-1 | 無 |
| 16 | 中（環境清理，待授權） | 各角色以 `docker compose run` 起的測試資料庫容器尚在執行（`b-0xx-db-1`、`b-0xx-qa-db-1`）；依規定角色不執行 `docker compose down` | 各任務 qa-1 | 待使用者授權清理（或由調度者決定收尾） |
| 17 | 中（安全衛生） | `config/env/teacher-crm/.env` 檔案權限對他人可讀（調度者回報；角色未讀內容，本人未另行查證） | 調度者回報 | 建議使用者自行 `chmod 600` |
| 18 | 低 | P-1 再印證：B-033 qa-1 在 worktree 無金鑰時 `tests/db/test_jotform_sync_command.py` 2 failed／9 passed，給假值全過；origin/master 基線同樣如此（git archive 匯出驗證） | B-033 qa-1 | 同第 1 項（另立項、讓測試自備金鑰） |
| 19 | 低（驗證缺口） | **B-006 預覽站未實際操作**：QA 時預覽站僅確認 HTTP 302，未登入手動操作，以測試補驗；預覽站已於 2026-11-18 停止（見風險段）；使用者驗收時需重開站或直接檢視分支，目視現場報名頁「已現場收款」預設不勾選 | B-006 qa-1 | 驗收時目視確認 |
| 20 | 低（驗證缺口） | **B-006 覆蓋率未複驗**：903 通過、覆蓋率 97% 為 engineer 自報，QA 未複驗覆蓋率 | B-006 impl-notes、qa-1 | 合併後全套跑一次確認 |
| 21 | 中（待使用者確認） | **B-006 worktree 內有來源不明的 `.env`**（`worktrees/B-006/teacher-crm/`）；角色未讀取，是否為 `.env.example` 副本或含真實值未確認（與 B-001 同型） | B-006 worktree | 請使用者確認來源；勿提交，確認前不要複製出該 worktree |
| 22 | 低（B-001 資安 L-1） | `ALLOWED_HOSTS` 解析未 strip 空白 | B-001 security-1 | 另立低優先項 |
| 23 | 低（B-001 資安 L-2） | 公開值黑名單無長度檢查，CI 假值在 DEBUG=0 不會被擋 | B-001 security-1 | 另立低優先項 |
| 24 | 低（B-001 資安 L-3） | DEBUG=0 允許 `*`，不在本任務範圍 | B-001 security-1 | 知悉；上線硬化（B-016）時評估 |
| 25 | 資訊（B-001 QA 備註） | worktree 的 `.env` 金鑰在 DEBUG=0 被判佔位值，合併後須換自產金鑰；`DJANGO_ALLOWED_HOSTS` 空字串得 `['']`（原有行為） | B-001 qa-1 | 合併後處理 |
| 26 | 資訊（B-001 環境） | 本機無 make，以 docker compose run 等價；compose v5 專案名須小寫；同一任務不可同時兩個寫入者；DB 測試用不同專案名 | B-001 impl-notes | 沿用 |
| 27 | 資訊（B-001 未執行項） | `make test-integration`（需授權）、CI 雲端實跑、scheduler 實際 up、JOURNEY-03 C／D 跨容器（以單元測試替代） | B-001 impl-notes、qa-1 | 需要時授權補跑 |

## 風險與待決事項

- **資安高風險**：H-1 預設設定不安全已由 B-001 修復並通過資安審查（已合併進 master）；H-2 假金流可免費付款（B-002）已修，資安／QA 第 1 輪通過，待使用者合併。
- **合併 B-002 的連動風險（2026-11-18）**：合併後，凡仍以 provider=fake 建專案、但未開 `fake_gateway_enabled` 的測試都會轉紅。B-002 已補 5 個既有測試檔；其他分支（例如 B-007、B-031、B-032、B-034）合併後須全套重跑確認，不要把轉紅誤判為各分支自身缺陷。資安另要求合併前在可用環境完整重跑測試套件（security-1 條件）。
- **M-4 金流失敗通知鎖終態（涉及金額，待確認）**：需先確認 Q8（綠界／藍新同單號失敗後可否重試）。
- **合併三個分支時 `docs/code_map/` 會衝突**（三條分支各自 `make codemap`，同動 `INDEX.md`、`manifest.json`、`modules/tests.db.md`、`templates.md` 等）。處理方式：合併完成後重跑 `make codemap`，**不要手解衝突**，再以 `make codemap-check` 確認無 STALE。
- **合併前提醒**：`make test` 在沒有 `JOTFORM_API_KEY` 的環境會有 P-1 的 2 個失敗，驗證合併結果時需提供假金鑰（見上表第 1 項）。合併後預期全套測試數：903＋3＋0＋18＝924（推算值，未實測；B-005 為調整既有測試、數量不變）。
- **預覽站（已停止，2026-11-18）**：B-001（8100）、B-006（8101）預覽站已由使用者要求停止，`bin/console site list` 為「目前沒有預覽站」；資料與映像檔保留（未加 `--drop-db`）。批次 1 的舊預覽站屬舊機器、本機不存在。驗收需重開站（`bin/console site add`）或直接檢視分支。
- **14 項已合併並 push（2026-11-18，已解除）**：B-001、004、005、006、008、009、025、027、028、029、033、036、042、058；本機與 origin/master 一致。合併後驗證（調度者回報）：lint、manage check、無待產生 migration、1234 測試通過、覆蓋率 98.17%（假 JOTFORM_API_KEY；P-1 既有 2 失敗不變）、code_map 已重產。B-002 等 B-001 合併的前置已滿足。臨時驗證 worktree `worktrees/V-1` 因 docker root 檔案刪不掉，待使用者自行清除。尚有 6 項（B-002、007、031、032、034、037）依 merge-plan 為 worktree 未 commit，是否已處理未確認。
- **B-001 完成（已合併）**：分支 `t-B-001`。升級（同 worktree 並行寫入者）已 resolved（使用者選 B 停掉對方後接續）。**合併提醒**：`docs/code_map` 衝突由合併者重跑 `make codemap`（不手解）；`.env` 現為 compose 必要檔（`env_file`）；worktree 的 `.env` 金鑰在 DEBUG=0 被判佔位值，合併後須換自產金鑰。
- **B-001 未執行項**：`make test-integration`（需授權）、CI 雲端實跑、scheduler 實際 up、JOURNEY-03 C／D 跨容器（以單元測試替代）。
- **專案環境檔**：`config/env/teacher-crm/` 內容未經任何角色讀取。驗證仍以命令列環境變數提供假值（shell `export` 後以 `-e NAME` 傳入，不寫檔）；注意 compose 會用 worktree `.env` 做變數代換，故每次須在同一指令內先 export 假值。角色不建立、不讀取 `.env`。
- （已解決 2026-11-17）`.claude/settings.json` 舊路徑：使用者已修正，調度者已核對三處新路徑。
- **B-002**（使用者裁示：B-001 合併後才開，不疊分支）：B-001 已合併；B-002 已完成，資安／QA 第 1 輪通過，escalation `resolved: true`（協議第 8 節「測試前置例外」，QA 已認可四項），待使用者合併。
- **批次 2 範圍**（使用者裁示）：B-001 納入 `compose.yaml` scheduler 指令修正為 `python src/manage.py run_scheduler`，使 005 US3 驗收情境 2 可驗證。B-007 與 B-039／B-041 起的樣板鏈仍要等 B-004、B-005 合併。
- **部署現況（使用者 2026-11-13 回覆，對應 backlog Q7）**：尚無正式環境；曾以預設設定運作，並曾透過 ngrok 對外開放；目前環境沒有真實金流／LINE 憑證與真實學員資料（「是否曾經有過」未確認）。影響：H-1、H-2 視為「上線前必修」，不需緊急輪替；但**舊環境的資料庫與 SECRET_KEY 不得沿用到正式環境**（正式環境用全新資料庫與新產生的金鑰）。若 Jotform API 金鑰、webhook 密鑰在 ngrok 開放期間使用過，建議上線前一併更換（成本低）。
- **待使用者決定（2026-11-18 第二次更新）**：backlog Q1–Q20 中已答 19 題（新答 Q1、Q2、Q3、Q10；答覆原文記在 `backlog.md`「答覆」表），**仍待決 1 題：Q8（綠界／藍新同單號失敗後重試行為）**。受阻項目：B-003（Q8）、B-013（Q8 經 B-003／長時間 CREATED 異常判斷）、B-030（Q8）；B-049、B-053、B-056 間接依賴 B-013；B-048 依賴 B-013、B-040。Q1、Q2、Q3、Q10 的 Q 阻擋已解除（B-010、B-011、B-012、B-013（僅 Q10 部分）、B-040、B-055、B-056），但答覆帶來新範圍與待 pm 釐清事項（見 `backlog.md`「Q 答覆後的範圍變動與待釐清」）：B-010 改軟刪除（封存）＋稽核紀錄且動 model、B-011／B-055 後台設定發送時間且不補發（可能新增設定 model／排程機制）、B-012／B-030 已付款計名額且現場報名例外（是否入憲法待 pm）、B-013／B-040／B-048 行政專員權限放寬與待辦區顯示、B-024 稽核範圍是否與 B-010 合併（待 pm）。這些項目目前主要被「待合併 B-002（views.py／forms.py）」與「pm 釐清」擋住，而非未答 Q。
- **批次 23（2026-11-18，Q1／Q2／Q3／Q10 答覆後自動挑選）**：0 項，原因見 `work-plan.md` 批次 23。統計不變：待辦 41、完成 19、共 60。
- **待測試帳號**：B-035、B-038（Q6：時區確定 `America/New_York`，上線前要實測，測試帳號尚未提供；不得自動派工）。
- **答覆後待 pm 於規格階段釐清**：B-020（「用姓名電話」與一次性綁定碼是否並存）、B-019（修改密碼語意、刪除成員處理）、B-039（「前端課／後端課」標示對象）、B-049（「任何改變留紀錄」對象）、B-015（建議 3 是否保留）、B-044／B-045（客服資訊後台設定，路線與 model 判斷）；B-018（誰執行 pip-audit、結果回補）、B-057（待人工原因分佈蒐集方式）。B-023 因 Q4 答「可以」前提不成立，待使用者確認是否關閉（擱置）。細節見 `backlog.md`「Q 答覆後的範圍變動與待釐清」。
- 依賴欄已解除 Q 待決（狀態欄本來就是「待辦」，未變動）：B-016、B-018、B-019、B-020、B-021、B-023、B-037、B-039、B-057（僅剩本身待釐清或檔案衝突）；B-015、B-046、B-049、B-055、B-056 解除 Q 但仍依賴其他項目。B-006 預設勾選已由使用者裁示選 A（已解決）。
- **批次 20（2026-11-18，自動挑選）**：挑 B-037（文件，Q5 已答；僅動 specs／SITEMAP，與待合併分支無檔案重疊）；詳見 `work-plan.md` 批次 20。統計不變：待辦 41（B-037 尚未開工），完成 19，共 60。
- **本輪需要使用者決定**：(1) B-009「非 LINE 模式一律 400」是否補範圍／另立項；(2) 事後可瀏覽第 1 項 P-1（含 B-042／B-033 的 2 個既有失敗）是否另立項目；(3) 自動派工是否繼續開著；(4) 待合併分支（B-002、B-007、B-014、B-026、B-031、B-032、B-034、B-037）的合併時機；(4b) B-014 部署方式（是否在反向代理後、B-016 是否先上線，見批次 25 B-014 事後可瀏覽第 65 項）（14 條已合併；B-002 合併後其他分支須全套重跑）；(4a) 是否立項 B-002 的 L-1、觀察 2（見事後可瀏覽第 51–54 項）；(5) 確認 B-006／B-001 worktree 內來源不明 `.env` 的來源（角色未讀取）。
- **B-001 套件現況**：`specs/005-secure-config-defaults/` 的 testplan、tasks（T001～T093）、analyze-report 已產出（依 `tasks/B-001/{testplan-notes,tasks-notes}.md`），實作完成、資安／QA 通過（997 通過、覆蓋率 97%，未 commit）。
- **報告間口徑不一**：12 處，已列於 `SUMMARY.md` §4.2。architecture 與 ux 讀的是提交前的工作樹，動工前需對照 HEAD 重驗行號（評估基線 `eb0a518`；B-005 QA 報告記錄的 origin/master 為 `4675d95`，兩者差異未查）。
- 評估限制：architect、uiux 無 Bash 只做靜態閱讀；`pip-audit`、`make test-integration` 未執行。

## 下一步

0. 驗收並合併 `t-B-002`（資安／QA 通過，升級已 resolved）；合併前在可用環境完整重跑測試；合併後其他待合併分支全套重跑。
1. `t-B-001` 已合併；請重跑 `make codemap`、換自產金鑰。
1a. B-006 已合併；驗收時目視現場報名頁預設不勾選（預覽站已停止，需重開）。worktree 已清理，原「worktree 內 `.env` 來源」疑慮（事後可瀏覽第 21 項）隨 worktree 移除，是否仍需確認：未確認。
1b. 14 項（含 B-008、B-009、B-025、B-028、B-029、B-033、B-036、B-042、B-058）已合併並 push，合併後全套驗證與 code_map 重產已完成（2026-11-18）。
2. 決定是否授權 `make test-integration`（B-001 未執行項）。
3. 使用者驗收並合併 `t-B-007`、`t-B-031`、`t-B-032`、`t-B-034`（另 `t-B-002` 見第 0 項；B-007 預覽站 8100 仍開著；停用用 `bin/console site rm`）；`t-B-004`、`t-B-005`、`t-B-027` 已合併；另請授權清理測試資料庫容器、自行 `chmod 600` 專案 `.env`；合併後重跑 `make codemap`、`make codemap-check`，以假金鑰跑全套測試。
4. 決定是否把「事後可瀏覽」第 1、2 項（P-1 測試金鑰隔離、藍新 `Amt` 異常值）立為 backlog 項目；第 2 項涉及金額，建議優先。
5. 回答仍待決的 Q8（Q1、Q2、Q3、Q10 已於 2026-11-18 答覆）；合併 t-B-002、t-B-007 以解鎖 views.py／forms.py／base.html 鏈；提供 Q6 測試帳號以解除 B-035／B-038；確認是否關閉 B-023。
