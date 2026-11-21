---
status: done
resume_at: 規劃中（下一步 system-analyze）
---

# B-014 /specify 階段筆記（pm）

## 已產出（worktree 內，分支 t-B-014）
- specs/044-public-endpoint-rate-limit/spec-mapping-checklist.md
- specs/044-public-endpoint-rate-limit/spec.md（4 故事、FR-001~021、SC-001~006）
- clarify-log.md 與 validate_artifacts 驗證：未執行（受工具預算限制）；續做時先跑
  `python3 .agents/skills/_shared/validate_artifacts.py spec --package 044-public-endpoint-rate-limit`，並依 Q1/Q2 答案建立 clarify-log.md。

## 查證依據
- CACHES 在 src/config 無設定，預設 LocMem，多 worker 不共享，須換 DB cache（createcachetable，不產生 migration）。
- pay_page POST：views.py 約 906-949；jotform_return 約 1504-1520；jotform_webhook 約 1592-1605；/admin/ 在 config/urls.py:5。
- 未查證：登入 view 實作位置（crm/urls.py）、/admin/ 是否被系統內連結引用、TransferClaim／付款嘗試的「未處理／進行中」狀態值。皆交 /system-analyze。

## 待釐清問題（硬停點，等使用者）
- Q1 /admin/：預設「移除路由」；替代「保留但限制來源」。
- Q2 門檻是否採建議預設：導向 60/10 分鐘（來源+專案）；通知 錯誤密鑰 20/10 分鐘、專案整體 300/10 分鐘；付款頁 POST 10/10 分鐘；未處理轉帳回報 3；進行中付款嘗試 3；登入 5 次失敗鎖 15 分鐘。
