---
task: B-005
role: pm
status: done
date: 2026-11-17
---

# B-005 規劃交接（快速路線 /quickfix）

## 產物（worktree 內，分支 t-B-005）

- `/Users/Park/Site/console/worktrees/B-005/teacher-crm/specs/007-fix-follow-ups-duplicate-invite-section/quickfix.md`
- `/Users/Park/Site/console/worktrees/B-005/teacher-crm/specs/007-fix-follow-ups-duplicate-invite-section/tasks.md`

套件名符合 quickfix 命名判準 `<NNN>-fix-<slug>`，與 work-plan 建議相同。

## 資格判定

五項全部符合，維持快速路線：1 個預期行為、不改 model、不新增 URL、不改權限、不推翻 FR（TEST_LIST 第 982 行規定各類名單各一份）。

## 切片

1 個切片 BE-API-01（Modify），任務 T001 ALIGN、T002 GREEN、T003 REFACTOR、T004 ACCEPTANCE-GATE。
- 把「標題整頁只出現一次」併入既有測試 `test_follow_ups_page_lists_absent_students_to_invite`，同一函式內改成取到「進階未完款」之前的區段，另斷言缺席者在區段內只出現一次。這樣 ALIGN 才有合法紅燈（重複造成次數為 2）；若拆成兩個切片，第二個在第一個 GREEN 後無法先紅。
- 只動 `project_follow_ups.html` 與 `tests/db/test_follow_ups_page.py`；不動 views、urls、models、followups、base.html；不加說明文字（Q11 待決，不阻擋）。

## 假設

- 規格 005 目錄（B-001 產物）已存在於 worktree，007 不衝突。
- 對應需求寫「現行行為：TEST_LIST 第 979／982 行」，因該功能無 spec.md。
- 驗證指令的單檔執行方式依 Makefile，未查。

## 未驗證

我沒有 Bash，未執行 `validate_artifacts.py`（quickfix、tasks 兩種），標記為「未驗證」，由調度者另外跑。已人工避開雙大括號字樣與 BE-REPO、mock ORM 等禁止詞，並對照驗證器規則（章節、欄位、SLICE 對應、ACCEPTANCE-GATE）自行核對。

## 待釐清

無需使用者回答。
