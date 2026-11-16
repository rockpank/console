---
task: B-004
role: pm
status: done
date: 2026-11-17
---

# B-004 規劃交接（快速路線 /quickfix）

## 產物（worktree `worktrees/B-004/teacher-crm/`）

- `specs/006-fix-student-edit-tags-in-title/quickfix.md`
- `specs/006-fix-student-edit-tags-in-title/tasks.md`（T001–T007：2 個切片＋ACCEPTANCE-GATE）

## 資格判定

符合快速路線：5 條全數成立（3 個預期行為、不改 model、不新增 URL、不改權限、不推翻 FR）。套件名 `006-fix-student-edit-tags-in-title` 合乎命名判準 `<NNN>-fix-<slug>`。

## 切片

- BE-API-01（Modify＋Add）：`<title>`／本體分段斷言（取代偶然通過的整頁比對）＋從本體表單新增「改期」標籤後改期頁可見學員。
- BE-API-02（Add）：標籤操作訊息在本體恰好一次、title 內無、重新載入後消失。

## 關鍵發現與假設

- 已查 `base.html`：不渲染 `messages`，所以搬出 `<title>` 後此樣板的迴圈是唯一渲染處，不會重複。
- 為使 BE-API-02 有真實紅燈，BE-API-01 的 GREEN 暫不搬 `messages` 迴圈；BE-API-01 測試的標籤改用 `add_manual_tag`／`remove_manual_tag` 建立（不經 client.post，避免訊息排隊進 title）。工程師依 tasks.md 順序執行即可。
- 假設：標籤區放在編輯表單之後、改期紀錄之前；訊息迴圈放在 `<h1>` 之後。皆為 pm 決定，可由工程師回報異議。
- 預期測試數 903 → 約 906（BE-API-01 新增 1、BE-API-02 參數化 2），以實際輸出為準。
- 005 資料夾（B-001）在 worktree 內已存在但為未完整套件；本任務配 006，無撞號。

## 驗證狀態

未驗證：沒有 Bash，未執行 `validate_artifacts.py`，須由調度者執行
`python .agents/skills/_shared/validate_artifacts.py quickfix --package 006-fix-student-edit-tags-in-title` 與 `... tasks --package ...`。

## 待釐清

無。
