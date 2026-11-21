---
status: planned
task: B-037
route: 快速路線（文件）— /quickfix 資格不符，改為直接列修訂清單
author: pm
date: 2026-11-18
---

# B-037 規劃：規格狀態欄與 SITEMAP 校正

## 1. 路線判定

- /quickfix 的資格與產物（quickfix.md 的 RED/GREEN 切片、行為測試）針對「行為 bug 修正」。本項是純文件校正，沒有行為切片可寫，**判不符資格**，不建立 `specs/<pkg>/quickfix.md`。
- 改以本清單作為 engineer 的執行依據。不新增 specs 套件（避免佔用 005 編號）；工程師逐項勾選並在回報中貼證據。
- 範圍僅：`specs/SITEMAP.md`、`specs/001-*/spec.md`、`specs/003-*/spec.md`（及其 system-analyze）、`specs/004-*/spec.md`（及其 system-analyze）、`specs/TDD_PROGRESS.md`、`specs/TEST_LIST.md`。不動 src、tests、model、憲法；不改 spec 的 FR 內容（僅狀態與說明）。
- 不做：004 的 `JOTFORM_TIMEZONE` 與 `tasks.md` T002／`integration-plan.md` 的 Asia/Taipei 回寫、`origins.py` 規格段落、監控項（屬 B-038）。

## 2. 現況盤點（我在 worktree 讀到的，engineer 開工先重新確認）

worktree 已有一些 B-037 字樣的修改（可能是先前一輪留下），視為已完成待驗證，**不要重做、不要重複加註**：

| 項目 | 現況 |
|---|---|
| 001 spec.md 狀態欄 | 已改為「已實作…」（第 7 行）；但 `plan.md:7`、`system-analyze/technical-research.md:7` 仍為「草稿」 |
| 003 spec.md 狀態欄、CASCADE 說明 | 已改（第 7、280 行）；`003 plan.md`、`data-plan.md`、`integration-plan.md`、`models.md` 的狀態仍為「草稿」；`data-plan.md:95-97` 已有 CASCADE 理由 |
| 004 spec.md 狀態欄、CASCADE 說明 | 已改（第 7、304、305 行） |
| TDD_PROGRESS.md、TEST_LIST.md 頂部歷史標示 | 已加（第 3 行）；TEST_LIST 自述第 15 節重複標題已改 15A，需驗證 |
| SITEMAP.md | **看起來完全未動**：仍有「銷講」「JOSTFOTM」、Google 未標撤回、無公開端點清單、無做／未做標示 |

## 3. 修訂清單（engineer 逐項做，勾選）

### 3.1 SITEMAP.md（主要工作）

- [ ] S1 檔頭加「校正說明（B-037，2026-11-18）」：本檔為原始規劃，下列標示為現況；圖例：已做／部分／未做（排入）／已撤回。
- [ ] S2 第 1 節站點圖逐項標示狀態，依據 arch §4.2：
  - 團隊管理、專案管理、專案授權、成員與角色（`/manage/teams|projects|members/`、`/projects/<id>/access/`）：已做。
  - 儀表板（今日待辦／場次總覽／異常提醒，`project_detail`）：已做。
  - 場次列表／詳情／編輯：已做；註明「新增場次」在列表頁以 POST 處理，無獨立 /new/。
  - 通知（範本、發送排程、LINE 額度、發送紀錄與重送）、回報（每週、前一天、一鍵複製）：已做。
  - 學員詳情彙整頁：**部分**（資料分散在學員編輯、付款頁、通知頁），**未做（排入，B-056）**。
  - 跨專案總覽（獨立權限）：**未做（排入，B-056）**；註明目前由 `/projects/` 專案列表部分涵蓋，`permissions.py` 無對應 Action。
  - 付款中的「金流回報 webhook 紀錄」頁（含 UNAPPLIED 待處理）：**未做（排入，B-056，邊界與 B-013 待處理清單另議）**。
  - 排程時間規則設定：**未做（排入，B-056）**。
  - 依據 Q5 答案：四頁皆標「做」，**不得寫成不做**。
- [ ] S3 第 1 節（約 L75）「Google 表單 / Sheets 同步」與第 3 節 P8（約 L169）「Google Sheets 同步」、第 2 節、第 4 節里程碑（L189「Google 表單手動維護」）、第 5 節（L220「保留 Google Sheets 同步」）、第 3 節 L110「Google」：標「已撤回（2026-11-04，見第 7 節；規格 002 已撤回）」。用刪除線或括號註記，不刪原文。檔頭原則句（L4）「Google 表單…三者一致」加註同上。
- [ ] S4 新增「公開端點清單（不需登入）」小節，建議放第 1 節後：欄位＝路徑、用途、驗證方式。端點：`/pay/<token>/`（付款頁，簽章 token）、`/fake-gateway/*`（開發用假金流，僅非正式環境）、`/jotform/return`（報名後導向）、`/jotform/webhook`（Jotform 回呼）、`/projects/<id>/jotform/*`（**注意：engineer 須對照 `docs/code_map/routes.md` 與 `src/config/urls.py`／`crm/urls.py` 確認此組是否需登入；若需登入則列於「Jotform 管理端點」而非公開**）、`front-course`、`products`（同樣以 routes.md 確認路徑全名與是否公開；無法確認者標「待確認」並在回報列出，不臆測）。另列金流與 LINE 的 webhook（如 routes.md 有）。驗證方式只寫 routes.md／spec 可證實者。
- [ ] S5 用語：通篇「銷講」改為「前端課」（憲法 §3：統一用語）；全檔 `JOSTFOTM`（L3 附近、L40、L91、L129、L180、L195、L217、L236-256 等，用 Grep 全找）改為 `Jotform`。保留「來源：利聖亞「銷講課程 行政執行 SOP」（2026.08 版）」這類原文件名稱的引用（書名不改），並在改動處註明；標題「銷講課程行政系統」可改為「前端課程行政系統」，由 engineer 判斷，於回報揭露。第 2 節 SOP 對照中的「銷講已付款」等標籤名若為實際標籤常數，對照 `crm` 內標籤常數後以現行名稱為準。
- [ ] S6 第 6 節待確認事項：「付款銜接」案已定案且 spec 004 已實作，加註「已實作，見 004」；第 7 節上線前實測五項加註「未完成，見 004 狀態欄；待使用者提供測試帳號」（不得標為已結案，因 Q6 答覆為尚未實測）。
- [ ] S7 第 3 節各 P0–P10 階段旁標狀態（依 TEST_LIST／TDD_PROGRESS 顯示 P0–P9 已完成、P10 即 001）；有疑問者標「依 TDD_PROGRESS 快照」。

### 3.2 規格狀態欄

- [ ] R1 驗證 001／003／004 的 spec.md 狀態欄已反映現況（見 §2）；002 保持「已撤回」不動。
- [ ] R2 套件內其他檔（001 `plan.md`、`system-analyze/technical-research.md`；003 `plan.md`、`system-analyze/{data-plan,integration-plan,models}.md`；004 對應檔）的「**狀態**: 草稿」：改為與該套件 spec 一致（已實作），只改狀態欄，不動內文。**先 Grep 確認 validate_artifacts 是否限制狀態欄允許值**，若不允許「已實作」則維持原格式並在 spec 內說明，回報揭露。
- [ ] R3 004 的 `system-analyze/data-plan.md`（及 `models.md`）補 CASCADE 理由（對應 004 spec L304 的說明：專案刪除連帶刪提交；提交對訂單／學員的關聯不使用 CASCADE），格式比照 003 `data-plan.md:95-97`。003 的 `models.md:19、52` 有 CASCADE：確認其「異動說明」段落或 data-plan 已有理由，缺則補一句。validate 警示要消失，需在 validate 認得的位置（用 Grep 找 validate_artifacts.py 檢查 CASCADE 的規則）。

### 3.3 TDD_PROGRESS.md、TEST_LIST.md

- [ ] H1 確認兩檔頂部歷史標示存在且措辭正確（已有）；不重複添加。
- [ ] H2 TEST_LIST：確認原兩個第 15 節標題已無重複（Grep `^## 15`）；若仍重複，把「JOSTFOTM 送出後導向（之後展開）」改為 15A（內文 JOSTFOTM 為歷史用字，可在標題註明「即 Jotform」）。
- [ ] H3 TEST_LIST 檔頭「640 項已勾選」「第 1～16 節」、TDD_PROGRESS「660 項」「683 項」：不改數字本身（歷史快照），僅確認標示已說明不代表現況。注意：quality 基線為 903 項測試，可在標示中引用「撰寫時基線 903 項（assessment/quality.md）」，非必要。
- [ ] H4 與 B-006 同動 `TEST_LIST.md` 的風險：B-006 分支尚未合併，B-037 只動檔頭與 15 節標題，衝突面小；回報中提醒調度者合併順序。

## 4. 驗收（QA 可直接驗證）

1. `python .agents/skills/_shared/validate_artifacts.py all --package 001-ci-quality-automation`、`003-jotform-session-sync`、`004-jotform-registration-payment` 各自通過；CASCADE 警示消失；004 integration-plan 的 3 個 `[NEEDS CLARIFICATION]` 警示可保留（B-038 範圍，不得為了消警示而刪除）。
2. SITEMAP：Grep `JOSTFOTM` 無結果（引用原文處除外並有註記）；Grep `銷講` 僅剩原始文件名稱引用；每個 Google 提及處皆有「已撤回」標示；存在公開端點清單；四缺頁標「未做（排入 B-056）」；每個站點項目有狀態。
3. 001／003／004 spec 狀態欄 ≠「草稿」；002 為已撤回；FR 內容的 git diff 為零（`git diff` 僅見狀態欄與已標示 B-037 的補充句）。
4. `git diff --stat` 僅含 `specs/` 下文件，無 src／tests／migrations／憲法／docs/code_map。
5. 不改變的既有行為（回歸範圍）：程式與測試完全不動；`make test`、`make lint` 結果不應受影響（文件任務可不跑完整測試，但需跑 `make lint` 確認未誤碰 py；結果須實際貼出或標「未執行」）。

## 5. 待調度者／使用者注意

- 公開端點清單的路徑全名、是否需登入需對照路由；engineer 不確定者標「待確認」，不可臆測。
- 「銷講」→「前端課」的標題層級改名是小判斷，engineer 揭露即可。
- 本任務未發現架構問題；SITEMAP 與 B-056（四缺頁）、B-013（金流回報待處理清單）的邊界只以「排入」標示，不定義細節。
- 未解決：Q6 相關（時區、實測）依 B-038，不在此項。

工具呼叫：16／25
