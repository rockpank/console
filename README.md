# 快速開發中控台

以中控台為主體的「快速開發網站代理」：專案管理員把需求切成可平行的任務，每個任務一個 worktree，工程師、資安、QA 依專案自己的開發模式推進，最後交回待驗收的分支。

```
/dispatch teacher-crm B-001,B-004     ← 在 console 開 Claude Code 執行
        │  project-manager 切分（工作包／檔案範圍／依賴／批次）→ 你確認
        ▼
bin/console wt add B-001 -p teacher-crm   → worktrees/B-001/teacher-crm/（分支 t-B-001）
        │  規劃角色 → engineer（批內平行）→ security-reviewer + qa-engineer
        ▼
待驗收：進各 worktree 檢視、commit、合併（console 不 commit、不 push）
```

規則、角色、流程見 [CLAUDE.md](CLAUDE.md)；位置、閘門、升級條件見 [docs/agent-protocol.md](docs/agent-protocol.md)。

## 入口

| 指令 | 用途 |
|---|---|
| `/onboard <路徑>` | 登錄並接手既有專案（profile、工程師規則、`config/console.toml`） |
| `/assess <專案>` | 現況評估（架構／品質／資安／UX）→ backlog，停下由你挑項目 |
| `/improve <專案> <ID>` | 單一項目走專案自己的流程 |
| `/dispatch <專案> <需求｜ID,ID…>` | 切分 → 平行 worktree → 資安／QA → 回報分支 |
| `/kickoff`、`/module` | 新建專案：需求 → 架構 → 模組開發 |
| `/progress`、`/status` | 看板（唯讀）／請專案管理員更新進度 |

## 預覽站

`bin/console site add <任務> -p <專案>` 為任務 worktree 開預覽站（埠由 console 配、網址顯示在看板卡片上），`site test` 測試、`site rm [--drop-db]` 停止。指令寫在 `config/console.toml` 的 `[projects.<別名>.site]`，細節見 CLAUDE.md「預覽站」。

## 環境檔

`config/env/<專案>/*.env` 由建 worktree 時複製進去（對應關係寫在 `config/console.toml` 的 `[[projects.<別名>.env_files]]`，目標必須是專案 git 忽略的路徑）。祕密不進版控、`chmod 600`、不貼進對話。teacher-crm 的 `.env` 屬於禁區，只看 `.env.example`。

## 舊版

Redmine 工單流程（角色、技能、協議，以及 `redmine.py`、`scan.py`、`status.py`、`reopen.py`、`landed.py`、`login.py`、cake73 站點 driver 與其測試）已移到 [legacy/redmine/](legacy/redmine/README.md)，不再載入。測試：`python3 -m unittest discover -s tests`。
