---
task: B-004
role: engineer
status: done
tests: 通過
date: 2026-11-17
---

# B-004 實作紀錄（快速路線，specs/006-fix-student-edit-tags-in-title）

完成 T001–T006 並回寫 `[X]`；T007（Gate）以下列品質關卡執行，全綠（唯一例外為與本變更無關的 2 個既有失敗，見殘餘風險）。`tests:` 標「通過」的意義：本任務新增／修改的測試與回歸測試全綠，全套件僅剩基線即存在的 2 項失敗。

## 變更檔案（worktree `worktrees/B-004/teacher-crm/`）

- `src/crm/templates/crm/project_student_edit.html`：`{% block title %}` 補閉合、只剩「編輯學員｜專案名」單行；標籤區（標籤 h2、標籤卡片、標籤紀錄）搬進 `{% block content %}`，位於編輯表單之後、「改期紀錄」之前；`messages` 迴圈搬到 `<h1>` 之後、表單之前（只渲染一次，`base.html` 無 messages）；移除多餘的 `{% endblock %}`。文字與樣式原樣。
- `tests/db/test_manual_tags.py`：新增 `split_title_and_body` helper；改寫 `test_student_edit_page_shows_tags_and_tag_history`（title／本體分段斷言，標籤改用 `add_manual_tag`／`remove_manual_tag`）；新增 `test_student_edit_page_tag_form_in_body_puts_student_on_reschedule_page`（本體取得表單 action → POST 302 → 改期頁見學員）；新增參數化 `test_tag_message_after_redirect_shows_once_in_body_and_not_in_title`（success／error 兩組）。
- `specs/006-fix-student-edit-tags-in-title/tasks.md`：僅勾選 T001–T006（T007 見下，亦已勾）。
- `docs/code_map/*`（INDEX、manifest、modules/src.crm.md、modules/tests.db.md、templates.md）：由 `make codemap` 產生，未手改。
- 未動 views／urls／models／migration／base.html／quickfix.md。

## 紅燈與綠燈證據

- T001 ALIGN／新增（修改前樣板）：`pytest tests/db/test_manual_tags.py` → 2 failed、7 passed。失敗原因正確：`title` 內含 `<h2>…標籤…` 全文（`assert '編輯學員｜秋季前端課\n…' == '編輯學員｜秋季前端課'`）；本體 `<form action>` 只有 `/accounts/logout/`、找不到 `tags/add/`。
- T002 GREEN：樣板最小修正後，`test_manual_tags`／`test_student_edit`／`test_reschedule_pages`／`test_wording` → 36 passed。
- T003 REFACTOR：helper 已於 T001 抽出供共用，樣板無需整理（本則無重構，仍 36 passed）。
- T004 RED：兩組參數皆失敗，`body.count(message) == 0`（`assert 0 == 1`），即 messages 仍在 title 區塊；2 failed、9 deselected。
- T005 GREEN：messages 迴圈搬到 `<h1>` 後 → 同上四檔 38 passed。
- T006 REFACTOR：title 區塊收成單行 `{% block title %}編輯學員｜{{ project.name }}{% endblock %}`，38 passed。

## 品質關卡實際輸出（均以 `COMPOSE_PROJECT_NAME=teacher-crm-b-004`）

- `make lint`：`All checks passed!`、`188 files already formatted`
- `make test`：`2 failed, 904 passed`（基線為 `2 failed, 901 passed`；差額 +3 = 新增 3 項：串接測 1 ＋ 參數化 2）。失敗的 2 項與基線相同（見下）。
- `make manage cmd="check"`：`System check identified no issues (0 silenced).`
- `makemigrations --check --dry-run`：`No changes detected`
- `make coverage`：TOTAL 4178 stmts、119 miss、**97%**（≥95%）；同樣 `2 failed, 904 passed`
- `make codemap`：已更新（修改：project_student_edit.html、test_manual_tags.py）；`make codemap-check`：`OK code map 是最新的（tree 4f006ecd4316，263 檔）`
- `validate_artifacts.py all --package 006-fix-student-edit-tags-in-title`：tasks.md、quickfix.md 皆 OK
- 開工 `make codemap-check`：OK（無 STALE）

## 假設與殘餘風險

- **既有失敗（非本變更造成）**：`tests/db/test_jotform_sync_command.py::test_a_renamed_question_is_found_again_and_the_write_is_retried_once`、`::test_when_the_session_question_cannot_be_found_again_the_form_waits_for_the_admin`，在改碼前的基線即失敗（`status 'active'` 而非 `needs_question`）。推測與測試內寫死的日期（`2026-09-0x`）對照今日 2026-11-17 有關（時間相依），未確認；先前評估記錄為 903 通過，建議由調度者另開項目處理（不在 B-004 範圍，未動）。
- 標籤卡片中既有的 `<p>` 內含 `<form>`（原樣保留）。此前因在 `<title>` 內從未被渲染；現在渲染時瀏覽器會自動在 `<form>` 前結束 `<p>`，版面應仍可用（form 為 inline），但未做瀏覽器目視確認，建議 QA 看一眼；若要改為 `<div>` 屬樣式／結構調整，未納入本任務。
- messages 不加 `aria`／顏色處理（屬 B-007）。
- 未 commit；`specs/006-…/` 為未追蹤新目錄（前置產物）。
