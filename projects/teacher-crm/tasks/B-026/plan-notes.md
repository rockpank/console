---
status: done
resume_at: 開發中
stage: 規劃（quickfix）
package: specs/045-fix-concurrent-duplicate-friendly-error
validated: 未執行（待調度者代跑）
---

# B-026 規劃交接

- 資格判定：符合快速路線（3 個切片、不改 model、不新增 URL、不改權限）。
- 產物（在 worktree 內）：`specs/045-fix-concurrent-duplicate-friendly-error/quickfix.md`、`tasks.md`。
- 做法：在領域函式（`attendance.py`、`orders.py`）的交易區塊外捕捉資料庫完整性例外，轉成既有 `AttendanceError`／`OrderError`；`views.py` 已會呈現這兩種錯誤，預期不需改。
- 範圍提醒：`work-plan.md` 把 `views.py` 列入檔案範圍，但實際預期不動，利於避開與其他任務的 `views.py` 衝突。
- 注意：`register_walk_in` 內部經 `ensure_intro_order` 會拋 `OrderError`，views 不接，需在領域層轉成 `AttendanceError`。
- 併發測試需 `transaction=True` 與多執行緒，並注意各執行緒資料庫連線要關閉；有不穩定風險，工程師可改用等效的確定性做法，但不可弱化斷言。
- 待跑驗證指令（在 worktree 根目錄）：
  - `python .agents/skills/_shared/validate_artifacts.py quickfix --package 045-fix-concurrent-duplicate-friendly-error`
  - `python .agents/skills/_shared/validate_artifacts.py tasks --package 045-fix-concurrent-duplicate-friendly-error`
  - `python .agents/skills/_shared/validate_artifacts.py all --package 045-fix-concurrent-duplicate-friendly-error`
