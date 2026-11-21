---
route: 快速
status: done
needs_views_py: false
validate_artifacts: 未執行（本角色無 Bash）
---

# B-007 規劃交接

- 資格：符合快速路線（3 切片、不改 model／URL／權限）。約 18 個樣板為機械式替換，不在資格判準內；風險由 BE-API-01 把關。
- 產物（worktree）：`specs/012-unify-message-component/quickfix.md`、`tasks.md`（T001–T010，3 切片＋Gate）。
- 不需動 views.py：BE-API-02（views.py:243）只驗呈現；若實作發現需改 views.py，工程師 `status: blocked`。
- 套件名依調度者指定 `012-unify-message-component`，不是 skill 命名規則的 `012-fix-<slug>`；validate_artifacts 若對命名有檢查，需調度者確認。
- 假設：訊息統一渲染於 base.html `<main>` 內、content 之前；訊息位置會略上移（原在 h1／tabs 之後）。
- 注意：T004 RED 序列——BE-API-02 預期被 T002 一併滿足，工程師應先寫 BE-API-02 測試確認紅燈再做 T002（tasks 已註記）。
- 18 個含 messages 的樣板：manage_base、project_access、attendance、follow_ups、front_course、jotform_settings、jotform_submissions、line_settings、message_templates、notifications、payment_settings、payments、products、reschedule、session_detail、sessions、student_edit、students。
- 提醒：`pay.html`、`login.html` 等用 context `error`，不屬 messages，不改。
