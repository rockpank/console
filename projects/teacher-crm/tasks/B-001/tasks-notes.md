---
role: pm
step: tasks+analyze
status: done
artifact: worktrees/B-001/teacher-crm/specs/005-secure-config-defaults/tasks.md、analyze-report.md
analyze_fixable: 無（嚴重／高 0；中低項已處理或列排除列）
validate: 未執行（本角色無可執行指令的工具，validate_artifacts.py 需由調度者執行）
needs_user: 是（Docker；T069 起 worktree 需 .env）
---

# B-001 /tasks＋/analyze 摘要（2026-11-17）

- `tasks.md`：T001～T093。Setup 2（T001 改動前實測 `4675d95` 基線、T002 確認 `-e` 假值傳入方式）、Foundational 3（FX-1～FX-5；FX-6 屬 BE-API-01 的 ALIGN）、28 組切片鏈、4 個 Gate。無 migration 工單（不改 model）。
- 回歸鎖定（首次可能即綠，要求「暫時改壞 → 確認紅 → 還原 → 記 impl-notes」）：QA 指明的 BE-SVC-11、13、19、22，另加 BE-SVC-08、09、26、27。
- 排序調整：BE-API-01 移到 US2 最前（早於 BE-SVC-15 改預設）；BE-SVC-08 整鏈移到 US2 主機規則之後；JOURNEY-01／02 的 Gate 延到 T069（compose `env_file`）之後執行。
- spec 回寫（PM 決定）：假設 9 補入 `[::1]`（採 D-04）；假設 16 註明起點 `4675d95`、「903」解讀為實測基線；使用者澄清決策 4 記錄 scheduler 指令裁示。
- scheduler 指令修正：BE-SVC-21（T074～T076）＋JOURNEY-03（T077）。

## 需調度者處理

1. **Docker**：T001 起全部需要（已另案升級）。
2. **T069 起需要 worktree 有 `.env`**：compose 加 `env_file: .env` 後，沒有 `.env` 連 `make lint` 都無法執行；裁示 3 禁止角色建立。請使用者擇一：自行放環境檔到 `config/env/teacher-crm/` 後 `env sync`，或授權把 `.env.example` 原樣複製為 worktree 的 `.env`（只含佔位值），或其他方式。T001～T068 不受影響。
3. 低：work-plan 檔案範圍補列 `tests/unit/conftest.py`；plan.md 的 scheduler「待確認」與 `eb0a518` 基線過時（architect 視需要更新）。
4. `validate_artifacts.py all --package 005-secure-config-defaults` 未執行，請調度者代跑。
