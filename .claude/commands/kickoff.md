---
description: 啟動新專案／新需求：需求釐清 → 架構 → 模組切分
argument-hint: <project> <需求描述>
---

你現在是中控台調度者。參數（第一個詞是專案名稱，其餘是需求描述）：

$ARGUMENTS

專案若為**既有專案的新功能**，不要走本流程：改用專案自己的完整路線（見 `projects/<project>/profile.md`），並以 `/improve` 或直接指派對應角色。本指令用於**新建專案**。

請依 `CLAUDE.md` 流程 A 的階段 1–3 執行：

0. 專案若尚未登錄：複製 `projects/_template/` 到 `projects/<project>/`，profile 填寫類型＝新專案、repo 預設 `/Users/Park/Site/<project>/`（先向使用者確認路徑），登錄到 `CLAUDE.md` 的已註冊專案表，並把 repo 路徑加入 `.claude/settings.json` 的 `additionalDirectories`。
1. **需求釐清**：需求有重大不明確處，先向使用者提問（一次問完、最多 5 題），把整理結果寫入 `projects/<project>/requirements.md`；需求已清楚就直接整理。
2. **架構**：派 `architect`（寫明 `<project>`）產出 `projects/<project>/architecture/overview.md`。完成後把關鍵決策與需要拍板的事摘要給使用者，**等使用者確認架構**再往下。技術棧確定後寫回 profile，並建立該專案的 `engineer-rules.md`。
3. **切分**：確認後，為每個模組各派一位 `pm`（可平行），產出各自的 `spec.md`。
4. 派 `project-manager` 更新 `projects/<project>/status.md`。
5. 回報：模組清單、各模組待釐清事項、建議開發順序，以及下一步（`/module <project> <模組名>`）。
