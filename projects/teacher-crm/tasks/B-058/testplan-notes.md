---
verdict: 完成
---

# B-058 testplan

- 產出：`worktrees/B-058/teacher-crm/specs/023-shared-http-transport/testplan.md`；validator 結果見回覆（通過）。
- 案例 7 個，全 BE-SVC，無 JOURNEY：01-03 Modify（`test_line_transport.py` 前三測，僅匯入 urllib_transport 改自 `crm.http`）、04-05 Keep（HttpLineClient、Jotform 既有測試）、06-07 Add（TIMEOUT_SECONDS==15；re-export 身分相同，因 `crm.http` 不存在而自然 RED）。
- 互不匯入以 grep 指令檢查（FR-003／SC-002），列於「全域 NFR 測試規劃」，非 pytest 案例。
- 基線：line transport／line client／jotform client 三檔 32 passed（docker compose，COMPOSE_PROJECT_NAME=b-058，--no-deps app，--no-cov）。全套與覆蓋率未執行。
- 解答前次待釐清 3：採 re-export（FR-002）；測試拆成兩行匯入（Modify）。
- 觀察：Jotform 既有測試皆注入假 transport，預設 transport 路徑（client.py:137-139）無測試涵蓋，本重構不補。
