---
description: 新建專案的模組：設計 → 開發 → 資安 → QA
argument-hint: <project> <模組名>
---

你是中控台調度者，要推進：**$ARGUMENTS**（第一個詞是專案名稱，第二個是模組名）。

前置：`projects/<project>/modules/<模組>/spec.md` 必須存在且沒有未解的「待釐清事項」；否則停下來回報使用者。
（既有專案的改善項目請用 `/improve`，它會依專案自己的開發模式走。）

依序執行（每步完成後檢查產出文件存在且合理，再進下一步；每個任務都寫明 `<project>`）：

1. **設計**：若 `projects/<project>/design/DESIGN_SYSTEM.md` 不存在，先派 `uiux-designer` 建立；再派它產出該模組 `design.md`。純後端模組可略過畫面。
2. **開發**：派 `engineer`，要求先讀 `projects/<project>/engineer-rules.md`（若有）。模組大時依 spec 的工作包切成多位工程師平行進行（各自負責不同檔案範圍）。要求回報實際測試結果。
3. **資安審查**：派 `security-reviewer`。有嚴重／高風險 → `engineer` 修復 → 複審，直到通過。
4. **QA**：派 `qa-engineer`。有缺陷 → `engineer` 修復 → QA 回歸，直到通過（有改動程式者需再過資安複審）。
5. **收尾**：派 `project-manager` 更新狀態，向使用者回報該模組結果（通過項目、遺留風險、遺留缺陷）。

遇到規格疑義或需要使用者決定的事，立即停下詢問，不要自行拍板。

## 工作目錄（worktree）

每個項目／模組在**自己的 worktree** 內開發，不直接改專案原 repo：先 `bin/console wt add <任務代號> -p <project>`（任務代號預設用 backlog ID 或模組代號；分支 `t-<代號>`；已存在就沿用），之後派角色時都帶「工作目錄: worktrees/<代號>/<project>/」與「`COMPOSE_PROJECT_NAME=<代號>`」。角色報告放 `projects/<project>/tasks/<代號>/`（見 `docs/agent-protocol.md` 第 2 節）。需要一次推進多項、平行開發時，改用 `/dispatch <project> <backlog ID,…>`（先由 `project-manager` 切批次）。
