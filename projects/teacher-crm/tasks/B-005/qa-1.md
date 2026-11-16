---
task: B-005
role: qa-engineer
verdict: 通過
date: 2026-11-17
---

# B-005 QA 報告（第 1 輪）：追售名單「待邀請出席」重複區塊去重

結論：**通過**。驗收標準 1–4 全部達成，沒有本任務造成的失敗。`make test` 與 `make coverage` 在沒帶環境變數時各有 2 個失敗，這 2 個是**既有問題（另立項目）**，已獨立驗證與本任務無關（見下），不影響 verdict。

## 範圍與環境

- worktree：`worktrees/B-005/teacher-crm/`，分支 `t-B-005`，HEAD 與 `origin/master` 同為 `4675d95`，變更全為未提交。
- 變更檔案：`src/crm/templates/crm/project_follow_ups.html`（刪 10 行）、`tests/db/test_follow_ups_page.py`（調整 1 個測試）、`specs/007-…/`（quickfix.md、tasks.md）、`docs/code_map/*`（4 檔，由 `make codemap` 產生）。views、urls、models、migrations、base.html 皆未動（`git diff` 確認）。
- 所有指令加 `COMPOSE_PROJECT_NAME=teacher-crm-b-005`；未執行 down／up／test-integration。
- B-004 的 `qa-1.md` 目前不存在，所以基線由我自己用乾淨快照驗證（見「既有問題」）。

## 1. 品質關卡（我自己的實際輸出）

| 關卡 | 指令 | 結果 |
|---|---|---|
| Lint | `make lint` | ruff check All checks passed；ruff format 188 files already formatted。通過 |
| 測試（原樣） | `make test` | **2 failed、901 passed**（85s）；失敗為既有那 2 個，與工程師回報一致 |
| 測試（帶假 Jotform 金鑰） | `JOTFORM_API_KEY=fake-test-key make test` | **903 passed、0 failed**（88s） |
| 框架檢查 | `make manage cmd="check"` | no issues (0 silenced)。通過 |
| 遷移檢查 | `make manage cmd="makemigrations --check --dry-run"` | No changes detected。通過 |
| 覆蓋率（原樣） | `make coverage` | TOTAL 4178 行、119 未涵蓋、**97%**（≥95%）；同樣 2 failed、901 passed，結束碼非 0 因為那 2 個既有失敗 |
| 覆蓋率（帶假金鑰） | `JOTFORM_API_KEY=fake-test-key make coverage` | TOTAL 4178 行、107 未涵蓋、**97%**；903 passed、0 failed、結束碼 0 |
| 程式碼地圖 | `make codemap-check` | OK 地圖是最新的（tree 2ddc4fb853e0，263 檔），無 STALE |

測試總數 903 不變（只調整既有函式，沒有刪除或新增測試函式）。

## 2. 驗收標準逐條驗證

| # | 驗收標準 | 驗證方式 | 結果 |
|---|---|---|---|
| 1 | 行政角色 GET 追售頁，「待邀請出席」標題整頁只一次，名單（或空狀態）一份 | 自動化：`content.count("待邀請出席") == 1`（測試通過）。實機：預覽站抓 HTML，`待邀請出席` 出現 1 次，`<h2>` 共 4 個（追售中／待邀請出席／進階未完款／已停止）。空狀態：另一個無缺席者的專案，標題 1 次、「沒有待邀請的學員。」1 次 | 通過 |
| 2 | 待邀請區塊內缺席者在、到場者不在（取到「進階未完款」之前） | 自動化：新斷言 `"缺席者" in invite`、`invite.count("缺席者") == 1`、`"到場者" not in invite`。實機：標題 `待邀請出席（1）`，該區段內缺席假學員 1 次、到場與訂金假學員 0 次 | 通過 |
| 3 | 追售中／進階未完款／已停止的標題、名單、按鈕維持原樣 | 自動化：test_follow_ups_page.py 其餘 8 個測試全過、未被改動（`git diff` 只動目標那 1 個測試）。實機：四個標題都在，順序為追售中→待邀請出席→進階未完款→已停止；行政角色可見「停止追售」「提醒完款」各 1 個；樣板 diff 只刪 10 行重複區塊，沒有新增任何文字 | 通過 |
| 4 | 講師可看且唯讀；A 專案成員讀不到 B 專案（404） | 自動化：`test_instructors_can_view_follow_ups_page_but_not_change`、`test_follow_ups_page_is_project_scoped` 通過。實機：講師 GET 200，無「停止追售」「提醒完款」按鈕；行政專員（只授權專案一）GET 專案二追售頁為 404 | 通過 |

測試確實能抓到重複：把改後的測試檔放進乾淨 `origin/master` 快照（未去重的樣板）跑，結果 `1 failed, 8 passed`，失敗為 `assert 2 == 1`（`content.count("待邀請出席")`），原因是重複，不是語法或資料錯誤。

## 3. 實機驗證（預覽站 http://localhost:8101/）

- 預覽站容器掛載的就是這個 worktree（`/app`），跑 `runserver`，所以看到的是改後樣板。
- 在任務專屬的可丟棄預覽資料庫用 `manage.py shell` 建立假資料：2 個假專案、3 位假學員（到場、缺席、到場且進階只付訂金）、1 個已結束場次、行政專員與講師各 1 個測試帳號（臨時隨機密碼，存在 scratchpad 暫存檔、未印出，用完已刪除；報告不含任何密碼）。
- 以 curl 保存 cookie 登入（`/accounts/login/`，302 轉到專案列表）後抓 `/projects/1/follow-ups/`（200）。未登入 GET 為 302。
- 實測數字：標題計數 待邀請出席=1、追售中=1、進階未完款=1、已停止=1；缺席假學員全頁 1 次且在待邀請區段內；到場假學員只在「追售中」出現（正確，他是追售對象），不在待邀請區段；訂金假學員在追售中與進階未完款各 1 次（正確）。
- 預覽資料庫留有這些假資料與兩個測試帳號（`qa_staff_b005`、`qa_instr_b005`），屬於可丟棄資料庫，建議收尾時隨 `site rm --drop-db` 一併清掉。

## 4. 回歸：「不得改變的既有行為」對照

| 不得改變 | 既有測試涵蓋 | 結果 |
|---|---|---|
| 追售中名單與第 N 天 | `test_follow_ups_page_lists_active_follow_ups_with_day_count` | 通過 |
| 進階未完款名單 | `test_follow_ups_page_lists_students_with_unsettled_advanced_payment` | 通過 |
| 已停止名單與原因 | `test_follow_ups_page_lists_stopped_follow_ups_with_reason` | 通過 |
| LINE 綁定狀態顯示 | `test_follow_ups_page_shows_line_binding_state` | 通過 |
| 沒點名警示 | `test_follow_ups_page_warns_about_sessions_without_roll_call` | 通過 |
| 講師唯讀（可看、無按鈕、停止 403） | `test_instructors_can_view_follow_ups_page_but_not_change` | 通過 |
| 跨專案 404 | `test_follow_ups_page_is_project_scoped` | 通過 |
| 行政專員可停止追售 | `test_staff_can_stop_follow_up_from_page` | 通過 |
| 名單內容與排序、view／followups.py | 未動（git diff）；`followups.py` 另有 test_finishing、test_follow_up_messages 等，全套 903 通過 | 通過 |
| messages 迴圈、說明文字、區塊順序 | 樣板 diff 只含刪除；實機確認順序 | 通過 |
| 用語掃描（test_wording） | 全套通過；刪除不引入新字串 | 通過 |

## 5. 既有問題（另立項目，不影響本任務 verdict）

**P-1：`tests/db/test_jotform_sync_command.py` 的 2 個測試在沒有 `JOTFORM_API_KEY` 環境變數時失敗**

- 受影響：`test_a_renamed_question_is_found_again_and_the_write_is_retried_once`、`test_when_the_session_question_cannot_be_found_again_the_form_waits_for_the_admin`。失敗訊息範例 `('11','請選擇場次') != ('21','可報名的場次')`，另一個為 `needs_question` 對 `active`；測試輸出夾有「平台尚未設定 Jotform 金鑰，略過同步。」
- 獨立驗證（B-004 qa-1.md 不存在，自行驗證）：把 `git archive origin/master`（`4675d95`，乾淨快照）匯出到 scratchpad，用 `COMPOSE_PROJECT_NAME=teacher-crm-b-005-baseline` 跑該檔：**2 failed、9 passed**，失敗相同，證明改碼前就存在，且乾淨快照不含 B-005 任何變更。
- 這兩個測試與 B-005 無關：變更檔案（樣板、test_follow_ups_page.py、code_map、specs）不含 jotform，測試檔與其 import 不涉及追售頁。
- 初步原因：`settings.JOTFORM_API_KEY` 在載入時從環境變數讀取（`src/config/settings.py:18`），compose 由主機環境傳入（`${JOTFORM_API_KEY:-}`）。這兩個測試依賴金鑰「已設定」，但測試本身沒有設定它。在乾淨快照帶任意假金鑰重跑：**11 passed**；在 worktree 帶假金鑰跑全套：**903 passed**。所以不是程式回歸，而是測試依賴執行環境（原本開發機大概有設金鑰，所以基線記錄為 903 通過）。
- 建議：另立 backlog 項目，讓這 2 個測試自己設定金鑰（例如用 `settings` fixture），不依賴外部環境。CI 若未設金鑰同樣會紅，值得確認。
- 我沒有讀取 `.env`，沒有改產品碼或測試。

## 6. 無法驗證之處

- 無。預覽站登入與頁面抓取都成功。「已停止」區塊在實機沒有資料（只驗證標題在），其內容由既有測試涵蓋。
- 沒有做瀏覽器視覺檢查（只用 curl 檢查 HTML 結構與計數）。

## 7. 缺陷清單

本任務造成的缺陷：**無**。

觀察（低、非缺陷）：工程師的 T004 將全套 2 個既有失敗視為不在 Gate 範圍；依本報告 P-1，該失敗與本任務無關，此處理合理。

## 8. 產物

- 本報告：`/Users/Park/Site/console/projects/teacher-crm/tasks/B-005/qa-1.md`
- 暫存（scratchpad，非專案內）：乾淨快照 `…/scratchpad/base-b005/`；基線用的 `teacher-crm-b-005-baseline` 專案的 db 容器已 `docker stop`（未 down），可由調度者清理。
