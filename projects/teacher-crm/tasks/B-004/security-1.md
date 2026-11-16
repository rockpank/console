---
task: B-004
role: security-reviewer
verdict: 通過
date: 2026-11-17
round: 1
---

# B-004 資安輕量審查（第 1 輪）

範圍：worktree `worktrees/B-004/teacher-crm`（分支 t-B-004）相對 origin/master 的差異：
`src/crm/templates/crm/project_student_edit.html`、`tests/db/test_manual_tags.py`；入口 `views.py`（`project_student_edit` L430-448、`project_student_tag_add` L1015-1027、`project_student_tag_remove` L1030-1043）與 `urls.py`（L49、L163、L168）只讀確認，未改（`git diff` 的 `src/` 只有該樣板一個檔案）。`docs/code_map/*` 為產生物，未審。

## 逐項結論

1. 輸出編碼／XSS：無問題。
   - 樣板全文無 `|safe`、`mark_safe`、`{% autoescape off %}`（`project_student_edit.html` 全檔；`base.html` 亦無）。
   - `{{ project.name }}`（title L2、crumbs L5）、`{{ message }}`（L9）、`{{ tag.name }}`（L32、aria-label L32）、`{{ event.name }}`（L52）、表單欄位與錯誤皆維持預設自動跳脫。
   - 搬動後 `{{ tag.name }}` 位於 `aria-label="…"` 屬性內，Django 會跳脫引號，不能跳出屬性。
   - title 只剩 `{{ project.name }}` 且已閉合（L2），消除了原本「title 未閉合、其後整段被當 RCDATA／文字」的畸形結構。
   - messages 內容是伺服端組字串（含 `student.name`、`tag.name`），輸出仍跳脫。

2. 標籤新增／移除表單：維持 POST 並帶 csrf。
   - 移除表單：`method="post"` L30、`{% csrf_token %}` L31（每個標籤各一份）。
   - 新增表單：`method="post"` L37、`{% csrf_token %}` L38。
   - 編輯主表單 L11-12 同樣維持。
   - 端點端另有 `@require_POST`（views.py L1016、L1031）。
   - 設定中 CsrfViewMiddleware 的啟用未在本次範圍重新確認（無變更；既有設定）。

3. 權限與跨專案隔離：維持，既有測試仍涵蓋。
   - 三個 view 皆 `_project_or_404` → `_require(EDIT_DATA)` → `_student_or_404`（`Student.objects.for_project`）。標籤移除另以 `StudentTag.objects.filter(student=student)` 限定（views.py L1036），無新增資料存取。
   - view／urls／models 未動。
   - 既有測試未被改動且仍在：`test_instructor_cannot_change_tags`（講師 add／remove 皆 403）、`test_tag_changes_of_other_project_return_404`（跨專案 add 404、跨學員標籤編號 remove 404）；`tests/db/test_student_edit.py` L84-85（講師 GET／POST 403）、L91-100（他專案 404）。`git diff` 顯示 `test_manual_tags.py` 只新增 import 與新測試、改寫 `test_student_edit_page_shows_tags_and_tag_history`，其他測試原樣。

4. `<p>` 內含 `<form>` 的結構（L28-36）：不構成安全問題。
   - 依 HTML 解析規則，`<form>` 起始標籤會先關閉開啟中的 `<p>`，再插入 form；form 本身保留 action、method 與其內的 csrf hidden input，不會被重組失效。
   - 殘留的 `</p>` 只會多產生一個空 `<p>`，屬排版／驗證層級（W3C 不合法），非安全問題。
   - 各 form 為兄弟節點、無巢狀 form（主表單 L11-22 已先閉合），無「巢狀 form 被忽略」的風險。
   - 此結構是原有寫法，搬動未改變語意；建議另立項目清理（見下）。

5. 測試有效性：真的在測，且未弱化。
   - 新增 `split_title_and_body` 以正則擷取 `<title>…</title>` 與之後本體分段（test L131-136），斷言 title 全等於 `編輯學員｜{project.name}`、title 不含標籤相關字、本體含標籤區文字與 `remove_url`；此即修掉舊測試「整頁子字串偶然通過」。
   - 訊息測試以 `follow=True` 驗證成功與錯誤訊息在本體恰好一次、不在 title、第二次 GET 不再出現（一次性消耗）。`base.html` 全檔無 `messages` 渲染（grep 確認），所以編輯頁樣板的迴圈是唯一渲染點，不會重複。
   - 新增 POST 後改期頁可見學員的測試（驗收 2）。
   - 無 skip／xfail、無門檻調降；測試數量淨增（8→10 個，code map 顯示）。
   - 變更後不需要 `test_wording` 例外；用語維持原樣。

## 發現清單

| 編號 | 嚴重度 | 位置 | 說明 |
|---|---|---|---|
| S-1 | 資訊（正向） | 原 `project_student_edit.html` L2-30（變更前） | 修正前 `{% csrf_token %}` 與標籤表單被渲染在 `<title>` 內，標籤功能實際不可用，且 CSRF token 會以文字出現在分頁標題。搬動後移除此狀況。 |
| S-2 | 低 | `tests/db/test_manual_tags.py`（新測試） | 沒有測試斷言標籤表單 HTML 內含 `csrfmiddlewaretoken`，Django test client 預設也不強制 CSRF，所以日後若有人拿掉 `{% csrf_token %}`，測試不會失敗。不阻擋，可選擇在 `split_title_and_body` 之後加一行斷言，或使用 `Client(enforce_csrf_checks=True)`。 |
| S-3 | 資訊 | 同上 | 部分本體斷言是寬鬆子字串（如 "改期"、"加上" 也會出現在其他標題文字中）；但 `remove_url`、add form `action` 斷言足以證明標籤區位在本體，不影響結論。 |

無嚴重或高風險發現。

## 另立項目建議（範圍外，不阻擋）

- 把標籤卡片的 `<p>` 外殼改成 `<div>`（`project_student_edit.html` L28-36），消除 `<p>` 內含 `<form>` 的不合法結構（解析時產生空 `<p>`）。屬排版整潔，B-007 或後續樣板整理時一併處理。
- 補一條「標籤新增／移除表單含 csrf token」的渲染測試或以 `enforce_csrf_checks=True` 的 POST 測試（S-2）。

## 未能驗證之處

- 未執行 `make test`／`make lint`（需 Docker／PostgreSQL，且審查為唯讀）；測試是否實際通過、903 項不減、覆蓋率、`make codemap-check` 無 STALE 由 qa-engineer 驗證。
- 未實際以瀏覽器解析渲染結果；第 4 項依 HTML 解析規格推論（無巢狀 form、form 前先關閉 `<p>`）。
- 未重新審查 CSRF middleware 設定與 `_require`／`for_project` 實作（本次未改動，沿用既有評估）。
- 未涵蓋 `specs/006-…` 文件內容的資安面（非執行程式）。

## 結論

verdict：通過。樣板修正沒有引入輸出編碼、CSRF、權限或跨專案隔離的退化，憲法 MUST 4／5 所依賴的伺服端檢查原封不動且既有測試仍涵蓋；S-2 建議但不阻擋。
