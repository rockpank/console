status: done-with-caveat（快速路線資格通過；validate_artifacts.py 未執行——本角色無 Bash 工具）

# B-042 pm-notes

- 資格：5 條全符合（3 個預期行為、不改 model、不新增 URL、不改權限、不推翻 FR）。
- 產物：worktree `specs/026-prevent-double-submit/quickfix.md`、`tasks.md`（3 切片：BE-VIEW-01 script、BE-VIEW-02 回頁還原、BE-VIEW-03 鎖定後端冪等）。
- 套件名沿用佇列預留的 `026-prevent-double-submit`（skill 命名規則是 `NNN-fix-slug`；validate 未見強制，若報錯請改名）。
- 待調度者執行：`python .agents/skills/_shared/validate_artifacts.py quickfix --package 026-prevent-double-submit` 與 `... tasks --package ...`。
- 發現：base.html 目前完全沒有 `<script>`；JS 行為無自動化測試工具，以渲染標記斷言＋人工驗收。BE-VIEW-03 若紅燈代表後端非冪等，停止回報、不改 views.py。
- 工程提醒：檔案範圍限 base.html（可能 project_jotform_settings.html）與新測試檔；`JOTFORM_API_KEY` 用假值。
