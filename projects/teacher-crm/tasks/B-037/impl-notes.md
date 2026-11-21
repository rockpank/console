---
status: done
tests: 未執行（純文件；make 在此環境不存在，lint 未執行；validate_artifacts 已跑）
task: B-037
---
# B-037 實作紀錄
- S1-S7（SITEMAP）：先前一輪已完成，本輪驗證：JOSTFOTM 0 處；「銷講」僅剩原文件名稱與校正說明；Google 各處皆有已撤回標示；第 1.1 節公開端點清單依 routes.md 逐項對照（/pay、/pay/return、/fake-gateway、/gateway/notify、/line/webhook、/jotform/return、/jotform/webhook）；四缺頁標[要做]；標題仍為「銷講課程行政系統」（第 1 行，未改，揭露）。
- R1/R2：001/003/004 所有套件檔第 7 行「草稿」改為「已實作（B-037 ... 內文未改）」，共 17 檔；validate 不限制狀態欄值。002 未動。
- R3：validate 的 CASCADE 警示只掃 models.md python block，003/004 data-plan 已有理由（003:95-97、004:87-91），警示無法消除，保留。
- H1/H2：標示存在；TEST_LIST 已有 15A / 15，無重複。
- validate：001 全 OK；003 僅 CASCADE 警示；004 CASCADE 警示＋3 個 NEEDS CLARIFICATION（B-038 範圍，保留）。
- 提醒：與 B-006 同動 TEST_LIST.md，合併時留意。
