status: done（附帶 2 項疑似既有失敗，見下）
tests: 失敗（全套 906 通過／2 失敗；新增 5 測試全綠；2 失敗在 test_jotform_sync_command.py，與本變更無關）

# B-042 impl-notes

- 切片：BE-API-01、02、03 完成（tasks.md 的 [X] 未回寫勾選 — 勾選請由調度者決定）。
- 變更：`src/crm/templates/crm/base.html`（`</body>` 前加 `<script data-submit-guard>`：document 層 submit 事件委派；延後 setTimeout(0) 停用 `button[type="submit"]` 並顯示「處理中…」，避免按鈕 name/value 未帶出；防重送旗標；`pageshow` 且 `persisted` 時還原）。
- 新增：`tests/db/test_double_submit_guard.py`（5 測試）。`docs/code_map/*` 由 codemap 腳本重產。
- RED：4 個 script 相關測試先紅（找不到標記）；BE-API-03（重複確認入帳）一開始即綠＝後端既有冪等，未動 views.py。
- 關卡：ruff check 通過；ruff format 189 檔已格式化；manage.py check 無問題；makemigrations --check 無變更；coverage 97%；codemap check OK。
- 環境：host 無 `make`，改用 `COMPOSE_PROJECT_NAME=b-042 docker compose run --rm app ...` 等效指令。
- 失敗：`test_a_renamed_question_is_found_again_and_the_write_is_retried_once`、`test_when_the_session_question_cannot_be_found_again_the_form_waits_for_the_admin`（單獨跑亦失敗）。為指令層測試、不渲染 base.html，推測既有問題（可能與日期有關），但未在乾淨基線驗證。
- 未自動化：瀏覽器實際行為。人工驗收：(1) 專案付款頁對「確認入帳」連按兩次，只送一次且按鈕顯示「處理中…」；(2) Jotform 設定頁「立即同步」同上；(3) 驗證失敗頁按鈕可用；(4) 送出後按上一頁，按鈕還原。
- 限制：`<a>` 連結式送出、JS 發起的 form.submit()（不觸發 submit 事件）不受保護；未動 project_jotform_settings.html。
