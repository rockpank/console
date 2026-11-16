---
task: B-004
role: qa-engineer
verdict: 通過
round: 1
date: 2026-11-17
---

# B-004 QA 報告（第 1 輪）：學員編輯頁標籤區落在 `<title>` 內

結論：**通過**。驗收標準 1–5 全部達成；`make test` 的 2 個失敗已獨立驗證為「與本任務無關、改碼前就存在」，另列為既有問題。缺陷：本任務 0 項阻擋／高／中，1 項低（空 `<p>`，見缺陷清單）。

## 環境與方式

- 工作目錄：`worktrees/B-004/teacher-crm/`（分支 `t-B-004`，未 commit；變更為 `project_student_edit.html`、`tests/db/test_manual_tags.py`、`docs/code_map/*`（產生物）、未追蹤的 `specs/006-…/`）。我沒有修改產品碼與測試。
- 所有 docker 指令皆用 `COMPOSE_PROJECT_NAME=teacher-crm-b-004`（基線比對用 `teacher-crm-b-004-baseline`）。未執行 down／up／test-integration，未讀 `.env`。
- 預覽站 `http://localhost:8100/`（容器 `teacher-crm-b-004-web`，掛載本 worktree）。

## 1. 品質關卡（我自己跑的輸出）

| 關卡 | 結果 |
|---|---|
| `make lint` | 通過：`All checks passed!`、`188 files already formatted` |
| `make manage cmd="check"` | 通過：`System check identified no issues (0 silenced).` |
| `makemigrations --check --dry-run` | 通過：`No changes detected` |
| `make codemap-check` | 通過：`OK code map 是最新的（tree 4f006ecd4316，263 檔）` |
| `make test`（照預設環境） | **2 failed, 904 passed**；失敗的就是下方「既有問題」2 項 |
| `make test`（供應 `JOTFORM_API_KEY` 假值，見下） | **906 passed, 0 failed**（`docker compose run` 以環境變數傳入，未改任何檔案） |
| `make coverage` | TOTAL 4178 stmts／119 miss／**97%**（≥95% 達標）；同樣 2 failed, 904 passed |

測試數量：906 項（基線 903 ＋ 本任務新增 3 項：串接測 1、參數化 2），沒有變少。`git diff -- tests` 被刪除的行只屬於被改寫的 `test_student_edit_page_shows_tags_and_tag_history`，沒有新增 skip／xfail。

測試是否真的能抓到缺陷（驗證測試有效性）：把本 worktree 的新 `test_manual_tags.py` 複製到「origin/master 乾淨快照」（舊樣板，暫存目錄）執行 → **4 failed, 7 passed**（改寫的 1 項、串接 1 項、參數化 2 項皆失敗），既有 7 項維持通過。代表新測試在舊缺陷上會紅、在修正後會綠，不再是「偶然通過」。

## 2. 既有問題（另立項目，不影響本任務 verdict）

**P-1：`tests/db/test_jotform_sync_command.py` 兩個測試依賴環境變數 `JOTFORM_API_KEY`，未提供時必失敗（測試隔離缺陷）**

- 受影響：`test_a_renamed_question_is_found_again_and_the_write_is_retried_once`、`test_when_the_session_question_cannot_be_found_again_the_form_waits_for_the_admin`。
- 獨立驗證與本任務無關：
  1. 在 `git archive origin/master` 匯出的乾淨快照（`/private/tmp/claude-502/-Users-Park-Site-console/30f819db-ce92-4e93-9eaa-8247f858c0fe/scratchpad/baseline-snap/`，沒有 B-004 任何變更）跑 `pytest tests/db/test_jotform_sync_command.py` → **2 failed, 9 passed**，同樣兩項、同樣訊息（`'active'` 而非 `needs_question`）。
  2. 失敗時的輸出含「平台尚未設定 Jotform 金鑰，略過同步。」：指令因為沒有金鑰直接略過同步，所以狀態沒變。
  3. 同一個快照、同樣今天日期（2026-11-17），只在環境傳入 `JOTFORM_API_KEY=<假值>` → **11 passed**；本 worktree 同樣方式跑全套 → 906 passed。
- 結論：**根因是這兩個測試沒有使用 `tests/db/conftest.py` 的 `platform_key`／`fake_jotform` fixture，也沒設 `settings.JOTFORM_API_KEY`，而是依賴容器環境變數**（`compose.yaml` 以 `${JOTFORM_API_KEY:-}` 傳入）。原 repo（有 `.env`）跑得過，沒有 `.env` 的新 worktree／乾淨環境就失敗。**工程師 impl-notes 推測的「寫死日期（時間相依）」不成立**，同日期下提供金鑰即通過；請別照那個方向修。
- 建議（另立項目，B-004 不處理）：兩測試加上 `platform_key` fixture（或 `settings.JOTFORM_API_KEY = "test-…"`），讓測試不依賴環境；順帶讓 `profile.md`「903 通過」的基線註明需有金鑰變數。價值中（任何無 `.env` 的 worktree／CI 都會踩到）、成本 S。
- 附帶影響：profile 的品質關卡「`make test`」在新 worktree 預設會有這 2 個失敗，調度者合併前不要把它誤當成 B-004 造成。

## 3. 驗收標準逐條驗證

| # | 標準 | 方式 | 結果 |
|---|---|---|---|
| 1 | GET 編輯頁：`<title>` 只含「編輯學員｜專案名」；本體含「標籤」「新增標籤」「標籤紀錄」；分段斷言 | 自動化：`test_student_edit_page_shows_tags_and_tag_history`（以 regex 分出 `<title>…</title>` 與其後本體，title 恰等於 `編輯學員｜<專案名>`，title 不含三詞，本體含三詞＋移除網址）通過。實站：curl 取得 HTML，`<title>` = `編輯學員｜QA測試專案A`、整頁 `<title>` 只有 1 個、title 不含三詞、本體含三詞 | 通過 |
| 2 | 該頁 POST 新增「改期」標籤 → 導回編輯頁 → 本體出現標籤；改期頁可見學員 | 自動化：`…tag_form_in_body_puts_student_on_reschedule_page`（表單 action 取自本體 → 302 → `response.url == edit_url` → 改期頁含學員）通過。實站：POST 新增標籤 → 302 至 `/projects/1/students/1/edit/`，GET 後標籤與紀錄在本體；`/projects/1/reschedule/` 含「測試學員」 | 通過 |
| 3 | 渲染測斷言「新增標籤」在本體；講師 GET／POST 403 | 本體斷言見 #1；`test_instructor_cannot_edit_student`、`test_instructor_cannot_change_tags` 通過。實站：講師帳號 GET 編輯頁 **403**、POST 新增標籤 **403** | 通過 |
| 4 | 標籤新增／移除後導回編輯頁，訊息恰好一次 | 自動化：參數化 success／error 兩組（本體 `count == 1`、title 不含、再次 GET 不再出現）通過。實站：新增標籤後第一次 GET 訊息在本體 1 次、title 0 次、頁面 alert 共 1 個；第二次 GET 訊息 0 次（一次性）；以保留名稱「未付款」觸發錯誤訊息，本體 1 次、title 0 次。（本任務未專測「移除」訊息，與新增共用同一迴圈，規格已註明） | 通過 |
| 5 | 共通回歸 | 見第 1 節；`make test` 在提供金鑰時 906 全過，覆蓋率 97%，codemap 無 STALE，無遷移 | 通過（`make test` 預設環境的 2 項失敗屬 P-1） |

## 4. 預覽站實測（資料庫為此任務專屬、可丟棄）

- 已在預覽資料庫建立假資料：專案「QA測試專案A」「QA測試專案B」、學員「測試學員」（0900-000-000）與「測試學員乙」、行政專員測試帳號與講師測試帳號（僅授權專案 A）。密碼為臨時隨機值，不記錄於本報告。
- 流程：curl 保存 cookie 登入（302 成功）→ 抓編輯頁 → 新增標籤 → 重抓兩次 → 新增保留名稱標籤 → 重抓。
- 權限與隔離（實站）：行政專員 GET 專案 B 學員編輯頁 **404**；以專案 A 路徑抓專案 B 學員 **404**；講師 GET／POST **403**。
- 版面結構（以 headless Chrome `--dump-dom` 取得瀏覽器重組後的 DOM，並截圖目視）：
  - 頁面順序：`h1 編輯學員`（訊息列在其下）→ 編輯表單 → `標籤` → `標籤紀錄` → `改期紀錄`；與設計一致；付款標籤說明文字保留。
  - 標籤卡片內既有的 `<p>` 內含 `<form>`：瀏覽器會在 `<form>` 前自動結束 `<p>`，DOM 中出現 **空的 `<p></p>`**（卡片頂端一個、新增表單前一個），**沒有巢狀 form**（DOM 內無 `<form>` 內含 `<form>`）。每個標籤的移除 form 依舊為 inline 並排。
  - 目視截圖：標籤、新增標籤輸入框、「加上標籤」按鈕、標籤紀錄皆正常顯示；唯一差異是標籤列上方多一小段空白（空 `<p>` 的邊距）。功能與排版可用。
- 限制：目視只做了一張桌面寬度（1000px）截圖，未測手機寬度或其他瀏覽器（Safari／Firefox）；在這些瀏覽器的重組行為依 HTML 規範應相同，但未實測。

## 5. 回歸對照（「不得改變的既有行為」）

| 既有行為 | 對應測試／實測 | 結果 |
|---|---|---|
| 標籤新增／移除端點、`EDIT_DATA` 權限、跨專案 404 | `test_staff_can_add_manual_tag_to_student`、`test_staff_can_remove_manual_tag`、`test_instructor_cannot_change_tags`、`test_tag_changes_of_other_project_return_404`（未改動，通過）；實站 404／403 | 通過 |
| 付款標籤不可手動新增／移除；說明文字保留 | `test_add_manual_tag_rejects_reserved_name`、`test_cannot_remove_automatic_payment_tag`（未改動，通過）；實站保留名稱被拒並顯示訊息；說明文字在本體 | 通過 |
| 編輯表單欄位／驗證／儲存／導向列表 | `tests/db/test_student_edit.py` 10 項全過（正規化電話、非法電話、同專案重複、儲存）；表單位置與內容 diff 僅搬動 | 通過 |
| 「改期紀錄」區塊 | `test_student_edit_page_shows_reschedule_history` 通過；實站「改期紀錄」在標籤紀錄之後 | 通過 |
| 講師看不到編輯連結、編輯頁 403 | `test_students_page_shows_edit_link_only_when_allowed[instructor-False]`、`test_instructor_cannot_edit_student` 通過；實站 403 | 通過 |
| 用語掃描 | `tests/unit/test_wording.py` 通過 | 通過 |
| 專案隔離與伺服器端權限（憲法 MUST 4／5） | 本修正只動樣板、無新增資料存取；views／urls／models／base.html 皆未變（`git status` 確認） | 通過 |

受影響的四個測試檔：`test_manual_tags.py`、`test_student_edit.py`、`test_reschedule_pages.py`、`test_wording.py` 共 38 項全過。

## 6. 無法驗證／未測之處

- 未在 Safari／Firefox／手機寬度目視（見第 4 節）。
- 標籤「移除」後的訊息，未做專項計數測試（與新增共用同一個 `messages` 迴圈，已由新增的兩組參數化測試覆蓋該迴圈行為）；實站也只測了新增與錯誤兩種。
- 未執行外部服務測試（無授權、與本任務無關）。

## 7. 缺陷清單（本任務）

| 編號 | 嚴重度 | 說明 | 相關 |
|---|---|---|---|
| D-1 | 低（外觀，建議併入後續樣式／結構項目如 B-007，不阻擋） | 標籤卡片內既有的 `<p>` 包 `<form>`，瀏覽器重組出兩個空 `<p></p>`，標籤列上方多一小段空白；無功能影響、無巢狀 form。若要修，把 `<p>` 改為 `<div>` 即可（屬結構調整，`impl-notes.md` 已提及並排除於本任務） | 驗收 1、2 |

另無規格疑義、無資安疑慮（權限與跨專案行為經實站確認未變；密碼未寫入任何檔案；假資料僅留在可丟棄的任務專屬資料庫）。

## 8. 給調度者的事項

1. 既有問題 P-1 請另立項目（backlog）：兩個 Jotform 同步測試未使用 `platform_key`，沒有 `JOTFORM_API_KEY` 環境變數時必失敗；impl-notes 的「日期寫死」推測不成立。
2. B-004 內容可進入後續流程（收尾）；合併前仍需 `make codemap`（與 B-005 等平行線合併時 `docs/code_map/` 可能衝突，依 work-plan 註記處理）。
3. QA 留在可丟棄資料庫的測試資料與暫存快照：`/private/tmp/claude-502/-Users-Park-Site-console/30f819db-ce92-4e93-9eaa-8247f858c0fe/scratchpad/`（baseline-snap、e2e、含臨時密碼的檔案），報告外不引用；`teacher-crm-b-004-baseline` 容器未清理（依指示）。
