---
status: done
resume_at: 開發中
validated: 未執行（本角色無 Bash）。待執行：cd /home/user/web/console/worktrees/B-014/teacher-crm && python3 .agents/skills/_shared/validate_artifacts.py all --package 044-public-endpoint-rate-limit
---

# B-014 /tasks 與 /analyze 階段筆記（pm）

產出（worktree `specs/044-public-endpoint-rate-limit/`）：`tasks.md`（T001～T165）、`analyze-report.md`；spec.md 假設補一句登入失敗窗口。

- 結構：Setup 2（T001～T002）、Foundational 6（T003～T008）、US1 T009～T054、US2 T055～T103、US3 T104～T131、US4 T132～T150、Phase 7 跨故事 T151～T165（BE-API-12／13／14／60／61，依賴 US1～US3 GREEN，故後移）。51 切片全為 Add 鏈，4 個 ACCEPTANCE-GATE（T054、T103、T131、T150）。既有測試全 Keep。
- BE-API-30 = T085～T087 為必做（使用者 2026-11-18 已裁示 N=30，`ATTEMPT_OPEN_WINDOW_MINUTES=30`）；BE-API-29 亦以 30 分鐘為準。
- 無 models.md、無 migration 工單；T008 以 makemigrations --check 確認無異動。
- 檔案範圍護欄寫在 tasks.md 任務契約：不得動 models／migrations／forms.py／pay.html。
- analyze：無 CRITICAL／HIGH；中 2（啟動指令位置待工程師定位 F-4；N 值 F-6 已裁示 30）；FR 21/21、NFR 2/2、SC 6/6、Journey 4/4。已知假設 K-1：登入連續失敗採 15 分鐘窗（plan D-07），已補進 spec 假設。
- 下一步：實作 /implement（engineer）。BE-API-30 已確定啟用。
