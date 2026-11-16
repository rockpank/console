---
description: 請專案管理員更新並回報專案進度
argument-hint: [project]
---

指定專案：**$ARGUMENTS**（未指定 = 逐一處理 `CLAUDE.md` 已註冊專案表中的所有專案）。

對每個專案，派 `project-manager`（寫明 `<project>`）依實際文件內容更新 `projects/<project>/status.md`（接手專案同時對照 `backlog.md` 與 `assessment/`），然後向使用者回報：

- 整體健康度（正常 / 有風險 / 受阻）
- 各模組或各 backlog 項目目前階段
- 卡住的事與需要使用者決定的事
- 建議的下一步

多個專案時，先給一張跨專案總表（專案、健康度、進行中項目數、最大風險），再逐專案細節。
