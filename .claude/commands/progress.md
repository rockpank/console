---
description: 以固定格式的文字看板顯示專案進度概況（唯讀、即時、不派 agent）
argument-hint: [project]
---

指定專案：**$ARGUMENTS**（未指定 = `CLAUDE.md` 已註冊專案表中的所有專案）。

這是**唯讀快速檢視**：只讀檔案、直接印出看板，不派任何 agent、不寫任何檔案、不執行測試。需要重新彙整進度請用 `/status`。

## 讀取來源（缺哪個就在看板標「無」，不要猜）

- `projects/<project>/status.md`（階段、風險、下一步、最後更新）
- `projects/<project>/backlog.md`（項目與狀態；計數以表格欄位為準，不要自己估）
- `projects/<project>/assessment/`（用檔案是否存在判斷各面向評估是否完成：architecture／quality／security／ux／SUMMARY）
- 新建專案另看 `requirements.md`、`architecture/overview.md`、`modules/*/` 下 spec／design／impl-notes／security-report／qa-report 是否存在

## 輸出格式（純文字，等寬排版，單專案不超過 25 行；不要用表格與標題語法，也不要加看板以外的說明）

```
══ 中控台進度 ｜ <今天日期> ══
【<project>】 健康度：<正常|有風險|受阻|未定>　｜　階段：<目前階段>
  評估　架構<✔|…|✘> 品質<✔|…|✘> 資安<✔|…|✘> UX<✔|…|✘> 摘要<✔|…|✘>
  基線　<實測數據一行，如：測試 903 過／0 敗｜覆蓋率 97%｜資安：不通過（高風險 2）>
  Backlog　共 <N> 項：待辦 <n>｜規劃中 <n>｜開發中 <n>｜資安 <n>｜QA <n>｜完成 <n>｜擱置 <n>
  進行中　<項目 ID 標題 → 目前階段>（無則寫「無」）
  待你決定　<編號與一句話，最多 5 項>（無則寫「無」）
  阻塞／風險　<最多 3 項>（無則寫「無」）
  下一步　<最多 3 項，依優先順序>
  更新　<status.md 最後更新日期>　<若 assessment 或 backlog 比 status.md 新，加「⚠ 進度表可能落後，建議 /status」>
```

符號：✔ 完成、… 進行中或檔案尚未產生但已派工、✘ 未開始。
多個專案時，先印一行跨專案總覽（`專案 健康度 進行中項目數`），再逐專案印上述區塊。
所有數字、狀態必須來自檔案內容；讀不到就寫「未確認」。
