---
status: done
resume_at: /tasks
validated: python3 .agents/skills/_shared/validate_artifacts.py all --package 044-public-endpoint-rate-limit 全部 OK（僅 models.md 缺少警告，本任務無新 model）
---

# B-014 /testplan 階段筆記（qa-engineer）

產出：worktree `specs/044-public-endpoint-rate-limit/testplan.md`（4 旅程、51 切片，皆為正式案例）。

- 測試位置：沿用專案 `tests/db/`（非 skill 預設 tests/api/）；autouse LocMem 與固定時鐘 fixture 放 `tests/db/conftest.py`。
- 真 DatabaseCache：BE-API-15、BE-CMD-01。併發（兩執行緒、transaction=True）：BE-API-33、BE-API-34。
- 正常使用不受影響：BE-API-04（50 人同 IP）、BE-API-22、BE-API-43（成功歸零）、BE-API-12／13（fail-open）。
- /admin/：BE-API-50／51／52／53、BE-CMD-02（admin 仍安裝、check 乾淨）、BE-CMD-01（makemigrations --check）。
- 時間窗（使用者已裁示 ATTEMPT_OPEN_WINDOW_MINUTES=30）：BE-API-29／30 為正式案例；BE-API-27／28／34 的 created 嘗試皆明載建立時間（窗內計入、超過不計）；以可控時鐘＋queryset update 改 PaymentAttempt.created_at，不 sleep。切片 ID／數量不變。
- 待澄清：登入「連續失敗」窗口語意（BE-API-47 依 plan 15 分鐘窗）；run_scheduler 是否結案逾時 created。
- 本階段未執行任何測試（只寫計畫）。
