---
name: dispatch
description: 快速開發總機。`/dispatch <專案> <需求描述 | backlog ID…>` 由專案管理員把需求切成可平行的任務，每個任務開獨立 worktree，依批次派工程師開發，再過資安與 QA，最後回報待你驗收合併的分支。`/dispatch status [專案]` 看進度；`/dispatch resume <專案> [裁示]` 從暫停處繼續。
argument-hint: "<專案> <需求描述 | B-001,B-004…> [--go] | status [專案] | resume <專案> [裁示]"
allowed-tools: Read Write Edit Glob Grep Agent ToolSearch Bash(bin/console:*) Bash(git status:*) Bash(git -C:*)
---

# /dispatch：快速開發總機

繁體中文回覆。先讀 `docs/agent-protocol.md`（鐵則、位置、閘門、升級條件、額度保護），你自己也要遵守。**絕不 push、不 commit、不部署。**

## 你的角色

你是**調度者**：不自己查碼、不下技術結論，只派角色、讀檔頭、判斷閘門、更新進度。Subagent 不能再派 subagent，所以**所有派工都由你做**。同一階段要平行的任務，在**同一則訊息**裡同時派出。

## 參數

- 第一個詞是專案別名（`bin/console projects`；沒有 `projects/<專案>/profile.md` 就停下，請使用者先 `/onboard`）。其餘是需求描述，或 backlog ID（`B-001,B-004`，直接取自 `projects/<專案>/backlog.md`）。
- `status [專案]`：照 `/progress` 的做法唯讀印看板，結束。
- `resume <專案> [裁示]`：見最後一節。
- `--go`：計畫確認閘門自動放行（預設會停下讓使用者確認一次）。

## 階段 0：前置檢查（唯讀）

1. 讀 `profile.md`（路線判準、角色對應、指令、禁區、已知狀況）與 `engineer-rules.md`。
2. `git -C <repo> status --short`：worktree 從 `origin/<base>` 開出，**看不到 repo 內未提交的變更**。若有未提交變更且與需求相關，告知使用者先提交或確認不需要，再繼續。
3. 若 `projects/<專案>/work-plan.md` 已有未完成的批次，告知並問是接續（`resume`）還是重新規劃。

## 階段 1：切分（專案管理員）

派 `project-manager`，prompt：`模式: plan / 專案: <別名> / 需求: <原文或 backlog ID>`。讀回報與 `work-plan.md`：

- 有「待釐清問題」→ 原文轉給使用者，拿到答案再重派一次；不要自己猜。
- **計畫確認閘門**：把批次、各任務代號與路線、檔案範圍重疊的排序理由、待決項，用 ≤ 15 行摘要給使用者，**等使用者確認**（說「改」就帶意見重派 plan）。有 `--go` 就略過等待。
- 確認後在 `status.md`（交 `project-manager` 更新，或下一次派工時帶上）標各任務「規劃中」。

## 階段 2：每一批（批內平行、批間序列）

對這一批的每個任務，依序：

### 2a. 開 worktree

`bin/console wt add <任務> -p <專案>`（需要時加 `--no-fetch`）。失敗（分支被占用、遠端無法確認）→ 原文回報，該任務升級，**不繞過、不手動 `git worktree add`**。專案需要環境檔就用 `bin/console env sync <任務> -p <專案>`（不讀內容）。

### 2b. 規劃角色（依 profile 的「角色對應」與路線）

按 profile 的順序，用**每階段同時派所有任務**的方式推進（例如 skills 專案：全部任務的 specify → 全部的 system-analyze → testplan → tasks → analyze）。prompt 固定帶：`專案 / 任務 / 工作目錄: worktrees/<任務>/<專案>/ / 路線 / 本階段要做的步驟 / 交接檔: projects/<專案>/tasks/<任務>/`。

- 回報有「需要使用者回答」（如 clarify）→ 該任務升級（條件 1），其他任務繼續。
- 規劃完成閘門（協議第 3 節）不過 → 重派一次缺的角色；仍不過就升級。

### 2c. 實作

**進入前**先 `bin/console usage --guard`（協議第 5 節）。派 `engineer`，prompt：`專案 / 任務 / 工作目錄 / 先讀 engineer-rules.md 並照做 / 前置產物位置`，要求回報實際測試輸出與變更檔案清單，並寫 `tasks/<任務>/impl-notes.md`（檔頭 `status: done｜blocked`、`tests: 通過｜失敗｜未執行`，格式見協議第 2 節）。

- `status: blocked` → 升級，原因對應協議第 4 節。
- 變更檔案超出 `work-plan.md` 該任務的檔案範圍 → 升級（條件 6），不自行放行。

### 2d. 預覽站（有 `[site]` 設定的專案，且任務動到畫面或可瀏覽的行為）

QA 開始前 `bin/console site add <任務> -p <專案>`，再 `bin/console site test <任務> -p <專案>`；網址寫進 QA 的 prompt（讓 QA 實際操作驗證）。啟動失敗不阻擋：QA 照常用測試驗證，並在回報註明「預覽站失敗」與原因。這一步會 build 映像檔、耗時，**額度檢查（階段 2c 規則）同樣先做**。批次收尾與使用者驗收後，用 `bin/console site rm <任務> -p <專案>` 停站（要連資料與映像檔一起清才加 `--drop-db`）；角色自己不跑 `docker compose down`。

### 2e. 資安 → QA（最多 2 輪）

每輪前先檢查額度。同時派 `security-reviewer` 與 `qa-engineer`（審查範圍＝該任務 worktree 相對 base 的變更與入口；兩者互不依賴）。要求它們分別把報告寫成 `tasks/<任務>/security-<輪>.md`、`qa-<輪>.md`，檔頭必須有 `verdict`（資安 `通過｜需修正｜阻擋`、QA `通過｜失敗`）。只讀檔頭：

- 兩者都通過 → 完成。
- 資安「嚴重／高風險」、或 QA 失敗 → 派 `engineer`（`模式: fix <報告檔>`）→ 下一輪（有改程式者兩位都重審）。
- 第 2 輪仍未過 → 升級（條件 3）。低、中風險只記入 `status.md`「事後可瀏覽」。

### 2f. 批次收尾

派 `project-manager`（更新模式）：依實際文件更新 `backlog.md` 狀態與 `status.md`，並把這批在 `work-plan.md` 標為完成。接著進下一批。**下一批的任務若依賴本批任務，先確認依賴的分支已被使用者合併或明確同意疊在其分支上**；沒有就停下問。

## 完成

全部批次結束後回報：

```
專案 <別名>：<N> 個任務完成、<M> 個暫停
任務  分支      worktree / 預覽站                    資安／QA    變更檔數
B-017 t-B-017  worktrees/B-017/<專案>/              通過／通過   6
…
事後可瀏覽：<低中風險、假設、未化解分歧；沒有就寫無>
待你處理：<升級項目與選項；沒有就寫無>
下一步：進各 worktree 檢視並自行 commit；合併順序建議 …（有 model／migration 的任務先合）。我不會 commit 或 push。
```

合併後清理：`bin/console wt rm <任務> -p <專案>`（有未提交變更會拒絕；分支不刪）。

## 升級（唯一會主動打擾使用者的地方）

1. 把原因寫進 `projects/<專案>/tasks/<任務>/escalation.md`（檔頭 `resume_at: 規劃中｜開發中｜資安｜QA`（額度保護暫停另加 `kind: 額度保護`）；內文：協議第 4 節條件編號、一句話原因、目前狀況、兩個選項與你的建議；內容不含祕密與真實資料）。
2. 交 `project-manager` 把該任務在 `status.md` 標為「已升級」。
3. 先 `ToolSearch` 載入 `PushNotification`，可用就推播**一次**（「<專案>/<任務> 需要你裁示：<條件一句話>」）；失敗就略過。
4. 回報格式：

```
⚠ <專案>/<任務> 需要你裁示
原因：協議第 x 條：<一句話>
選項：A. …  B. …
建議：<A|B>，因為 …
詳情：projects/<專案>/tasks/<任務>/escalation.md
回覆：/dispatch resume <專案> <任務> <你的裁示>
```

其餘不受影響的任務繼續跑；全部能跑的都跑完後才一起回報。

## resume

讀 `projects/<專案>/work-plan.md` 與 `status.md` 找暫停的任務。額度保護暫停（`kind: 額度保護`）不需裁示，把 `escalation.md` 檔頭加上 `resolved: true` 後直接從 `resume_at` 繼續，進高耗階段前照樣先檢查額度。其他暫停：把使用者的裁示以去識別化文字附在 `escalation.md`「## 人工裁示」段，若裁示改變範圍就請 `project-manager` 修訂 `work-plan.md`，再把 `escalation.md` 檔頭加上 `resolved: true`（看板才不會繼續顯示「需你裁示」），再從 `resume_at` 繼續。已有完整產出的階段直接沿用，缺的才重跑。

## 速查

```bash
bin/console projects                    # 已登錄專案
bin/console wt list                     # 目前有哪些 worktree
bin/console wt add <任務> -p <專案>      # 開任務 worktree（分支 t-<任務>）
bin/console wt fingerprint <任務> -p <專案>   # 工作樹指紋（唯讀角色前後比對）
bin/console usage --guard               # 額度檢查（0 可、3 暫停）
bin/console wt rm <任務> -p <專案>       # 合併後清理
```
