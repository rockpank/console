---
description: 既有專案現況評估：架構、品質、資安、UX，並產出 backlog
argument-hint: <project> [architecture|quality|security|ux|all]
---

你是中控台調度者，要評估專案：**$ARGUMENTS**（未指定面向 = `all`）。

前置：`projects/<project>/profile.md` 必須存在，否則先執行 `/onboard`。**評估全程唯讀：不改專案任何檔案，只寫入 `projects/<project>/assessment/` 與 `backlog.md`。**

1. 讀 profile 的「已知狀況」。若工作樹有未提交變更，提醒使用者：品質健檢的測試結果會包含這些變更；仍可繼續，報告會註明。
2. **平行派工**（各面向互相獨立），任務內寫明 `<project>` 與「評估模式」：
   - `architect` → `assessment/architecture.md`
   - `qa-engineer` → `assessment/quality.md`（實際執行測試、lint、覆蓋率；profile 標為「需授權」的測試不跑）
   - `security-reviewer` → `assessment/security.md`
   - `uiux-designer` → `assessment/ux.md`（專案有使用者畫面才派）
3. 四份報告到齊後：
   - `project-manager` 彙整 `assessment/SUMMARY.md`（整體健康度、各面向重點、矛盾與重複、建議先做什麼）。
   - `pm` 建立 `backlog.md`（合併重複、標註類型／價值／成本／風險／依賴／建議路線、排序）。
   - `project-manager` 更新 `status.md`。
4. **停下來報告並讓使用者挑選**，回報內容：健康度結論、各面向最重要的發現（嚴重／高風險優先）、建議先做的前 5 個 backlog 項目與理由、需要使用者決定的事。不要自動開始改善。
