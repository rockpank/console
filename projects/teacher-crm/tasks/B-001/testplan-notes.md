---
role: qa-engineer
step: testplan
status: done
artifact: worktrees/B-001/teacher-crm/specs/005-secure-config-defaults/testplan.md
validate: OK（all --package 005-secure-config-defaults，rc=0）
baseline: 未執行（本機無 docker）
---

# B-001 /testplan 摘要（2026-11-17）

- 產物：`specs/005-secure-config-defaults/testplan.md`（worktree 內，未 commit）。
- 案例 32：JOURNEY 4（每故事 1）、BE-SVC 27、BE-API 1（既有假金流流程回歸）。無 api/integration 契約（plan 四項介面皆「否」）。
- seam：`startup_checks` 純函式、`runpy` 載入 `settings.py`、`crm.crypto`、compose／ci／external／.env.example 檔案契約；全部新增測試放 `tests/unit`（憲法三層優先於 RULES 預設的 tests/api、tests/e2e）。
- 使用者裁示已涵蓋：BE-SVC-21（scheduler command = `python src/manage.py run_scheduler` 且路徑存在）、JOURNEY-03（容器內 `run_scheduler --help`、check、app 簽出的付款權杖與密文由 scheduler 解回；缺金鑰失敗）。
- 旅程禁用 `docker compose config`（會展開 .env 值）、不 `up scheduler`、不 `down`；只看結束碼與變數名稱。
- 回歸鎖定（首次可能即綠，tasks 需揭露並以暫時破壞自證）：BE-SVC-11、13、19、22。

## 待處理

1. 基線未實測：本機 `docker: command not found`。實作 RED 前須在有 Docker 環境以 `COMPOSE_PROJECT_NAME=B-001 JOTFORM_API_KEY=<假值> make test` 實測（起點 4675d95，非 plan 的 eb0a518／903）。
2. 旅程 JOURNEY-01～04 都需 Docker＋使用者 `.env`；無 Docker 則只能標「未執行」。
3. `[::1]` 視為本機是 D-04 對 spec 假設 9 的補充，PM 可在 /tasks 或 /analyze 決定是否回寫 spec。
