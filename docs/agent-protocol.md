# 多角色協議（所有角色與調度者先讀）

## 1. 鐵則

- 繁體中文。**絕不 `git push`、不開 PR、不部署、不 commit**（除非使用者明確要求）。
- 角色只靠**文件**交接，不靠口頭記憶；Subagent 不能再派 subagent，**調度只能由主對話做**。
- 結果必須來自實際執行；沒跑的標「未執行」，不可標為通過。
- 規格不清楚就回報「待釐清」，不要自行假設後直接實作。
- 不得越權：不改別人負責的文件；需要變更就在回覆中提出，由調度者轉交。
- `.env` 等專案「禁區」（見 `projects/<專案>/profile.md`）與 `config/env/**` 不讀、不印、不改、不貼進任何檔案。

## 2. 單位與位置

| 名詞 | 說明 |
|---|---|
| 專案 | 登錄在 `config/console.toml` 的 `[projects.<別名>]`，工作區在 `projects/<別名>/` |
| 任務 | 一個可獨立開發的工作包，代號全中控台唯一（預設 backlog ID，如 `B-017`；非 backlog 用 `N-<序號>`；第二個專案登錄後加專案前綴） |
| worktree | `worktrees/<任務>/<專案別名>/`，分支 `t-<任務>`（`bin/console wt add <任務> -p <專案>` 建立；不手動 `git worktree add`） |
| 工作區文件 | `projects/<專案>/`：`profile.md`、`engineer-rules.md`、`backlog.md`、`status.md`、`work-plan.md`、`assessment/`、`tasks/<任務>/` |

**文件放哪裡**

- 專案流程規定要進 repo 的產物（如 `specs/<NNN-*>/`、程式、測試）→ **在該任務的 worktree 內**，跟著 `t-<任務>` 分支走。
- 角色的報告與交接檔 → `projects/<專案>/tasks/<任務>/`（`impl-notes.md`、`review-<k>.md`、`security-<k>.md`、`qa-<k>.md`）。這些**不進專案 repo**。
- 進度只記在 `projects/<專案>/status.md` 與 `backlog.md`（單一事實來源），由 `project-manager` 維護。

每份交接檔以 YAML 檔頭開始，調度者與看板（`bin/console ui`）**只讀檔頭**判斷閘門，細節留在檔內。角色回覆 ≤ 10 行。看板認得的檔名與欄位：

| 檔案 | 檔頭欄位 | 值 |
|---|---|---|
| `impl-notes.md`（engineer） | `status`、`tests` | `status: done｜blocked`；`tests: 通過｜失敗｜未執行` |
| `security-<k>.md`（security-reviewer） | `verdict` | `通過｜需修正｜阻擋` |
| `qa-<k>.md`（qa-engineer） | `verdict` | `通過｜失敗` |
| `escalation.md`（調度者） | `kind`、`resume_at`、`resolved` | `kind: 額度保護` 或省略；`resume_at: 規劃中｜開發中｜資安｜QA`；`resolved: true` 表示已處理，看板不再要求裁示 |

看板的階段（規劃中→開發中→資安→QA→完成）取 `backlog.md` 的「狀態」欄與上述交接檔中較後面的一個；`完成` 只認 backlog。

## 3. 階段與閘門（`/dispatch` 的骨架）

```
規劃（pm/architect/uiux/qa 依 profile 角色對應）→ 實作（engineer）→ 資安審查（security-reviewer）→ QA 驗證（qa-engineer）→ 收尾（project-manager）
```

- **規劃完成閘門**：profile 規定的前置產物齊全（例如 skills 專案的 `tasks.md`，完整路線另需 `analyze-report.md` 無可修項），工程師才能開工；缺了不由工程師自補。
- **審查迴圈最多 2 輪**：資安或 QA 退回 → `engineer` 修 → 複審；有改程式者資安要複審。
- **同批平行**：只有「檔案範圍不重疊、無依賴」的任務放在同一批；批內上限 3；同一時間只允許一個任務動 model／migration；共用檔（settings、urls…）衝突者序列化；規格編號由 `project-manager` 在 `work-plan.md` 一次分配。
- 平行任務各自一個 worktree、各自 `COMPOSE_PROJECT_NAME=<任務>`；不得兩個任務共用一個 worktree。

## 4. 升級條件（才會停下來問使用者）

以下任一成立，調度者暫停該任務並回報（其餘不受影響的任務照常往下）：

1. 需求或規格矛盾、缺關鍵決定、需使用者拍板（含 profile 規定的「等使用者回答」硬停點）。
2. 與專案憲法／規範衝突。
3. 資安「嚴重／高風險」或 QA 失敗，經 2 輪修正仍未解。
4. 需要使用者授權的指令（profile 標「需授權」者、連真實外部服務、`git push`、`docker compose down`…）。
5. 任務範圍與工作樹中「與本任務無關的未提交變更」重疊，或 model／migration 衝突無法靠排序解決。
6. 變更範圍明顯超出 `work-plan.md` 的檔案範圍。
7. 額度保護（見下）。

低、中風險的發現不停下，記進報告與 `status.md`「事後可瀏覽」。

## 5. 額度保護

進入高耗階段（實作、每一輪審查與修正）前，執行一次 `bin/console usage --guard`：結束碼 0 照常；**3 → 不進入該階段**，把任務標為「暫停（額度保護）」寫進 `status.md`，回報預計重置時間後停止。**絕不自行解除**（不重試、不換方式派 subagent）；解除只有 `bin/console ui` 的按鈕。檢查指令本身失敗（非 0 非 3）→ 當作可以繼續，並在回報註明「額度檢查失敗」。

## 6. 專案端技能

專案自己的 skills（如 teacher-crm 的 `.agents/skills/`）都是 `disable-model-invocation`，在中控台**不會自動載入**：角色是 Read 它們的 `SKILL.md`／`RULES.md`，在本次任務內依 SOP 自己執行（不另開子代理）。對應關係在各專案 `profile.md` 的「角色對應」。

## 7. 個資與祕密

不處理客戶資料：測試與範例一律用假資料。報告、備註、commit 訊息不得出現真實姓名、帳號、金額、金鑰。發現疑似真實資料 → 不引用原文，只寫位置與類型並升級。
