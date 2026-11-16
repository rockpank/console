---
task: B-005
role: engineer
status: done
tests: 通過
date: 2026-11-17
---

# B-005 實作筆記（快速路線，spec 007）

注意：`tests: 通過` 的意思是本任務相關測試全綠，且全套件的失敗與基線相同。`make test` 與 `make coverage` 結束碼仍為非 0，因為有 2 個與本任務無關的既有失敗（見下）。

## 變更檔案（worktree `worktrees/B-005/teacher-crm/`）

- `src/crm/templates/crm/project_follow_ups.html`：刪除第 45–54 行逐字重複的「待邀請出席」區塊（共 10 行），保留第一份。沒有新增任何文字。
- `tests/db/test_follow_ups_page.py`：調整 `test_follow_ups_page_lists_absent_students_to_invite`（同一函式內，沒有新增或刪除測試函式）。
  - 新增 `content.count("待邀請出席") == 1`。
  - invite 區段改成取到「進階未完款」之前。
  - 新增 `invite.count("缺席者") == 1`。
  - 保留 `"到場者" not in invite`。
- `specs/007-fix-follow-ups-duplicate-invite-section/tasks.md`：只把 T001–T004 勾成 `[X]`。
- `docs/code_map/{INDEX.md,manifest.json,modules/tests.db.md,templates.md}`：由 `make codemap` 產生，沒有手改。
- 未動 views、urls、models、migration、base.html、其他樣板，也沒有動 specs 下的其他檔案。

## 紅燈與綠燈證據

- 基線（改碼前）：`make codemap-check` 為 OK；`make lint` 通過；`make test` 為 2 failed、901 passed。
- RED（T001，只改測試）：`pytest tests/db/test_follow_ups_page.py` 為 1 failed、8 passed。失敗是 `assert 2 == 1`（`content.count("待邀請出席")`），原因是重複，不是語法或資料錯誤。
- GREEN（T002）：刪除重複區塊後，同一檔案為 9 passed。
- REFACTOR（T003）：無需整理。刪除後區塊間空行一致，樣板結尾沒有殘留。

## 品質關卡實際輸出

- `make lint`：ruff check 為 All checks passed；ruff format 為 188 files already formatted。
- `make test`：2 failed、901 passed。
  - 2 個失敗是既有問題，改碼前的基線就有：`tests/db/test_jotform_sync_command.py::test_a_renamed_question_is_found_again_and_the_write_is_retried_once` 和 `::test_when_the_session_question_cannot_be_found_again_the_form_waits_for_the_admin`。
  - 失敗訊息範例：`assert ('11', '請選擇場次') == ('21', '可報名的場次')`。
  - 與追售頁無關，我沒有動它們。評估基線記的是 903 通過，所以這 2 個是新近才變紅的既有問題，原因未查，建議另立 backlog 項目。
- `make manage cmd="check"`：System check identified no issues。
- `make manage cmd="makemigrations --check --dry-run"`：No changes detected。
- `make coverage`：TOTAL 4178 行、119 行未涵蓋，97%（≥95%）。同樣是這 2 個既有失敗，所以結束碼非 0。
- `make codemap` 後 `make codemap-check`：OK，tree 2ddc4fb853e0。
- `validate_artifacts.py all --package 007-fix-follow-ups-duplicate-invite-section`：tasks.md 與 quickfix.md 都是 OK。

## 假設與殘餘風險

- 假設：T004 Gate 的範圍是受影響測試（`tests/db/test_follow_ups_page.py` 9/9 綠）加上品質關卡。全套件的 2 個既有失敗不在本任務範圍，我據此勾了 `[X]`；若調度者認為 Gate 要求全套件全綠，請重新裁示。
- 整頁「待邀請出席」文字（`content.count`）現在只出現一次，沒有導覽列等其他位置帶這幾個字。
- 與 B-007 共用 `project_follow_ups.html`，B-007 排在本項之後；`docs/code_map` 產生物在合併時需要重跑一次 `make codemap`。
- 有一個容器 `teacher-crm-b-005-db-1` 還在跑，沒有執行 down，留給調度者收尾。
