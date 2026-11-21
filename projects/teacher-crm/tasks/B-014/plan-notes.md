---
status: done
resume_at: /testplan（qa-engineer）；ui-plan 已由調度者裁示跳過
validated: 未執行（architect 無 Bash）；已對照 validate_artifacts.py 逐項人工檢查章節、D-nn 欄位、約束「因為」句型、classDiagram、契約案例欄位與雙向覆蓋。請調度者代跑下方指令，結果回填此欄
---

# B-014 /system-analyze 階段筆記（architect）

## 產出（worktree specs/044-public-endpoint-rate-limit/）
plan.md、system-analyze/{technical-research,data-plan,api-plan,integration-plan}.md；spec.md 已把 HTTP 狀態碼改寫為業務語言。第二輪補齊驗證器要求的章節與 D-nn、契約案例（API 14 筆、INT 7 筆）。

## 關鍵決策（已定案）
- 無新 model／migration：DatabaseCache 別名 `throttle`（表 `crm_throttle`，createcachetable）。不產出 models.md（驗證器僅警告）。
- `crm/throttle.py`、`crm/login.py`（ThrottledLoginForm）；不改 forms.py；urls.py 只改一行；settings.py 只加 CACHES。
- 轉帳回報／付款嘗試上限用 Order 列鎖；/admin/ 移除路由、admin app 保留；通知入口超限 429＋Retry-After；門檻採 spec 預設。
- ui-plan 跳過：429 頁沿用 `crm/jotform_notice.html`（heading／text／note），不派 uiux-designer。

## 待使用者裁示
- 進行中付款嘗試若永不結案會永久擋信用卡付款：是否只計最近 N 分鐘內建立的嘗試（建議 N=30）？已預留 `LIMITS.ATTEMPT_OPEN_WINDOW_MINUTES`（預設 None＝照 spec）。記於 plan §4／§7-1、technical-research 假設 A-1、data-plan、api-plan、integration-plan。若裁示啟用，需確認 PaymentAttempt 的建立時間欄位名稱（我未查證，待確認）。

## 待確認
Dockerfile 啟動指令、README 位置、`src/crm/admin.py` 是否存在、CI 是否自行 migrate、B-002 動過 settings.py 的區段、Jotform 對 429 的重送、run_scheduler 是否結案逾時 created。clarify-log.md 仍含「404」字樣（非驗證對象）。

## 請代跑（worktree 內）
- `python3 .agents/skills/_shared/validate_artifacts.py all --package 044-public-endpoint-rate-limit`
- `make codemap-check`（本階段未動程式）
