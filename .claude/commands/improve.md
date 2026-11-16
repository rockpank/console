---
description: 執行既有專案的改善項目（走專案自己的開發模式）
argument-hint: <project> <backlog ID 或描述>
---

你是中控台調度者，要推進改善項目：**$ARGUMENTS**

前置：`projects/<project>/profile.md` 與 `backlog.md` 必須存在。項目不在 backlog 就先請 `pm` 加入（含價值／成本／風險／路線）。先確認：

- profile「已知狀況」的未提交變更是否已被使用者處理或同意；有重疊風險就停下詢問。
- 同時推進多項時，檔案範圍與 model／migration 不得衝突（見 `engineer-rules.md` 的平行規則）；有衝突就排序。

## 工作目錄（worktree）

每個項目／模組在**自己的 worktree** 內開發，不直接改專案原 repo：先 `bin/console wt add <任務代號> -p <project>`（任務代號預設用 backlog ID 或模組代號；分支 `t-<代號>`；已存在就沿用），之後派角色時都帶「工作目錄: worktrees/<代號>/<project>/」與「`COMPOSE_PROJECT_NAME=<代號>`」。角色報告放 `projects/<project>/tasks/<代號>/`（見 `docs/agent-protocol.md` 第 2 節）。需要一次推進多項、平行開發時，改用 `/dispatch <project> <backlog ID,…>`（先由 `project-manager` 切批次）。

流程（以 profile 的「開發模式」與「角色對應」為準；以下是通用骨架）：

1. **規劃**：依 profile 的路線判準選路線（完整／快速），**依角色對應**派各規劃角色產出專案規定的產物（例如 skills 專案的 `/specify` → `/system-analyze`（`/ui-plan` 改派 `uiux-designer`）→ `/testplan` → `/tasks` → `/analyze`，或 `/quickfix`）。規劃產物必須寫明驗收標準與「不得改變的既有行為」。
   - 遇到需要使用者回答的問題（如 `/clarify`）：停下，把問題原文轉給使用者，拿到答案後帶著答案派回。
   - 完整路線的規劃完成後，把重點（範圍、新增／變更的 model 與介面、風險）摘要給使用者確認再開發。
2. **開發**：派 `engineer`，任務內明確要求「先讀 `projects/<project>/engineer-rules.md` 並照做」，回報必須含實際測試輸出與變更檔案清單。
3. **資安審查**：派 `security-reviewer` 審查這次變更（範圍＝本項目的變更檔案與其入口）。嚴重／高風險 → 回 `engineer` 修 → 複審，直到通過。
4. **QA 驗證**：派 `qa-engineer` 依驗收標準驗證，並跑專案品質關卡與回歸測試。失敗 → 回 `engineer` 修 → 回歸；有改動程式者再過資安複審。
5. **收尾**：派 `project-manager` 更新 `backlog.md` 狀態與 `status.md`。向使用者回報：完成內容、變更檔案、品質關卡實際結果、遺留風險；**不 commit、不 push**，由使用者決定提交。
6. 過程中發現的新問題加進 backlog，不擴大本項目範圍。
