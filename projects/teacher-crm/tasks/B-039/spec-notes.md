# B-039 規格交接（快速路線，規格 046）

- 產物（worktree 內）：`specs/046-fix-wording-unification/quickfix.md`、`tasks.md`（3 切片＋2 非行為任務＋Gate，共 T001–T012）。
- 資格：符合（不改 model、不新增頁面／URL、不改權限）。
- 範圍：側欄「課程費用與贈品」→「進階課程費用」；通知頁「課程與費用」→「前端課費用」；去除可見的 `admin`／`JOTFORM_API_KEY`／`scheduler`；動詞依用語表；`views.py` 收款訊息千分位；docstring 舊稱（`views.py`、`orders.py`、`reports.py`、`line/notifications.py:74`）；新增 `docs/wording.md`。
- **範圍外（Q13 裁示）**：「前端課／後端課」標示（標籤／場次／產品）另列新 backlog 項目，需 pm 另行釐清對象與「後端課」與「進階課程」的關係。資料庫舊標籤修正不做。
- 假設：行號以 grep 現況為準（`views.py` 收款訊息約 962 行，backlog 寫 947）；動詞表為 pm 草擬，工程師遇歧義保守不改並回報；`project_products`／`project_front_course` 的現有測試若斷言舊稱，以 ALIGN 處理；`test_wording.py` 不動。
- 風險：樣板與 B-040、B-041 衝突，序列合併。取代英文詞時勿改 HTML 屬性或表單 `name`。
- 實測：本角色無 Bash，`validate_artifacts.py quickfix/tasks --package 046-fix-wording-unification` **未執行**，須由工程師或調度者開工前先跑。
