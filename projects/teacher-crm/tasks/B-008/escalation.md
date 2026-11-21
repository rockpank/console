---
resume_at: 規劃中
resolved: true
---

> 調度者註記（2026-11-17）：此升級是另一個派工流程在本次 `/dispatch teacher-crm --auto 2 --go` 進行中，看到本次自己開的 `t-B-008` worktree 與進行中的變更而誤判為「來源不明」。變更來源即本次派工（規格 010 → engineer → 資安通過／QA 通過，見同目錄 impl-notes／security-1／qa-1）。已視為選項 A 處理並標 resolved；使用者如有異議請於驗收時告知。

# B-008 升級（協議第 4 節條件 5）

- 原因：自動派工挑中 B-008，但 `worktrees/B-008/teacher-crm/`（分支 `t-B-008`）已存在，且有來源不明、未提交的變更（11 個已修改檔＋`specs/010-send-revalidation/`、`src/crm/domain/send_check.py`、多個 `tests/db/test_send_*`、`tests/unit/test_send_check.py` 等），但 `projects/teacher-crm/tasks/B-008/` 沒有任何交接檔（無 impl-notes、security、qa），backlog 狀態仍為「待辦」。
- 目前狀況：未派任何角色，未動 worktree。
- 選項：
  - A. 把這些變更視為先前未記錄的 B-008 進行中成果：從現況接續，由 engineer 對照 `specs/010-send-revalidation/` 驗證後走資安／QA（建議）。
  - B. 視為無效：由使用者自行清理 worktree 後重開（本中控台不 reset／clean）。
- 建議：A，需使用者先確認這批變更的來源。
