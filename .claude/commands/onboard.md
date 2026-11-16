---
description: 登錄並接手既有專案：建立 profile、工程師規則、狀態總表
argument-hint: <repo 路徑或專案名稱>
---

你是中控台調度者，要接手既有專案：**$ARGUMENTS**

名稱可只給資料夾名，預設在 `/Users/Park/Site/` 下找。**這一步只登錄、不評估、不改專案任何檔案。**

1. **盤點（唯讀）**：確認路徑存在；讀專案自己的 `CLAUDE.md`／`README`、規範文件（憲法、規格）、目錄結構、`Makefile`／`package.json`／`pyproject.toml` 等指令入口、CI 設定、`git status` 與 `git log`（近 10 筆）、有無專案自有 skills（`.claude/skills`、`.agents/skills`）與其 README。**不得讀取 `.env` 等機密檔**（僅看 `.env.example`）；`.gitignore` 內的快取與產生物也不必讀。
2. **建立工作區**：複製 `projects/_template/` 到 `projects/<project>/`，填寫 `profile.md`（含指令、品質關卡、禁區、已知狀況：特別記下未提交變更）。
3. **工程師規則** `projects/<project>/engineer-rules.md`：
   - 專案有自己的開發模式（skills、憲法、TDD 規範等）→ 把它整理成工程師規則，寫明讀取順序、路線判準、必過關卡、禁止事項、平行與衝突規則；並在 profile 的「角色對應」寫出每個步驟由中控台哪個角色負責。摘要要忠於原文並標明「與原文有出入時以原文為準」。
   - 專案沒有自己的規範 → 刪除該檔並在 profile 標 `dev_mode: default`，同時在回報中建議先補專案規範（可列入 backlog）。
4. **權限**：把 repo 絕對路徑加進 `.claude/settings.json` 的 `permissions.additionalDirectories`（保留既有內容）。
5. **註冊**：在 `CLAUDE.md` 的「已註冊專案」表新增一列；並在 `config/console.toml` 加 `[projects.<別名>]`（`repo`、`remote`、`base_branch` 以專案實際主分支為準、`branch_prefix = "t-"`），讓 `bin/console wt add` 能建任務 worktree。
6. **回報**：專案概況（技術棧、規模、規範）、profile 中需要使用者確認的假設、工作樹狀況，以及下一步建議（`/assess <project>`）。若有未提交變更，提醒使用者先處理或確認。
