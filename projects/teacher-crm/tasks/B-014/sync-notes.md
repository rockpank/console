---
status: done
---

# B-014 文件同步筆記（裁示：進行中付款嘗試只計最近 30 分鐘內建立的）

目錄：worktrees/B-014/teacher-crm/specs/044-public-endpoint-rate-limit/

- spec.md：FR-007 文字、US2 情境 3 改為只計 30 分鐘內建立的進行中嘗試（無 HTTP 碼、無新 FR）。spec 假設區原無時間窗敘述，未改。
- plan.md：LIMITS 表 ATTEMPT_OPEN_WINDOW_MINUTES 預設 30；§7-1 改為已裁示並註明 PaymentAttempt.created_at。
- testplan.md：BE-API-29 改寫（窗內 3 筆擋下）、BE-API-30 升正式案例（移除條件字樣）、覆蓋對照表 FR-007 去「（條件）」、待釐清段落改為已裁示。案例 ID 與數量不變。
- tasks.md：T082～T084 說明對齊；T085～T087 移除 [條件任務] 與引言；總覽、T103、依賴、備註、Add 段落同步。T001～T054 未動。
- analyze-report.md：K-2 已裁示；F-6 已解決；摘要表、覆蓋表、結論處「條件」字樣同步。

殘留矛盾：tasks.md T003（屬 T001～T054，禁改）仍寫 `ATTEMPT_OPEN_WINDOW_MINUTES=None`；工程師實作時以 plan.md（預設 30）為準，T003 骨架可寫 30。另 system-analyze/ 下 api-plan、data-plan、technical-research 仍有「預設 None／待裁示」字樣，未在本次範圍。
