---
status: done
---

# B-006 規劃交接（快速路線）

- 套件名：`specs/042-fix-onsite-paid-default-unchecked/`（`quickfix.md`＋`tasks.md`，在 worktree 內）
- 資格：符合快速路線（1 個行為、不改 model／URL／權限）。附註：無 spec package FR，被改的是 TEST_LIST 敘述，已有使用者 2026-11-17 裁示。
- 行為：臨時報名「已現場收款」核取方塊預設不勾選；POST `paid=on` 記已付款、未帶維持未付款（後端不變）。
- 驗收：點名頁含「已現場收款」「1,500」「name="paid"」且不含 `name="paid" checked`；既有 walk-in POST 兩測試維持綠；TEST_LIST 第 901、909 行已改。
- 檔案範圍：`src/crm/templates/crm/project_attendance.html`（約第 91 行）、`specs/TEST_LIST.md`（901、909）、`tests/db/test_attendance_pages.py`（約第 313–314 行的 `'name="paid" checked' in content`）。
- 假設：樣板變更若使 codemap STALE，由 engineer 跑 `make codemap`。
- 未執行：本階段無 Bash，`validate_artifacts.py quickfix/tasks --package 042-fix-onsite-paid-default-unchecked` 未跑，請 engineer／調度者補跑。
