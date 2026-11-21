verdict: 通過

# B-033 QA 第 1 輪

環境：worktree，無 make，以 `docker compose run`（COMPOSE_PROJECT_NAME=b-033-qa）；JOTFORM_API_KEY 以 `-e` 假值傳入，未寫檔。

| 項目 | 結果 |
|---|---|
| ruff check / format --check | 通過（191 檔已格式化） |
| tests/unit + tests/db（含假金鑰） | 916 passed，0 failed |
| 覆蓋率 | 98%（門檻 95%）；attendance.py 99%、domain/attendance.py 100%、registration.py 99%、process_finished_sessions 95%、process_jotform_submissions 100% |
| manage.py check | 無問題 |
| makemigrations --check --dry-run | No changes detected |
| codemap-check | OK（最新） |
| src／model／conftest 變更 | 零（src 與 origin/master 無差異；未追蹤檔僅 3 個新測試檔，已追蹤檔僅 docs/code_map 更新） |

## P-1 印證（2 個失敗測試）
- worktree 無金鑰：`tests/db/test_jotform_sync_command.py` 2 failed, 9 passed（即 engineer 回報的兩個）。
- worktree 提供假值：全過（全套 916 passed）。
- origin/master 基線（git archive 匯出到暫存目錄，掛載進容器；未 stash／reset／checkout）：無金鑰同樣 2 failed 9 passed；有假值 11 passed。
- 結論：已驗證為既有問題 P-1（缺金鑰才失敗），非 B-033 造成。

## 測試有效性（複本改預期值，已刪除複本）
改了 6 處預期，9 個案例轉紅：--date 訊息（3 個參數化）、--now 缺時區訊息、同日 later/earlier 斷言、已處理提交略過/人工處理（2 個參數化）、略過頁面訊息、立即同步無金鑰提示。未轉紅的 4 個為未改動的案例。

## 缺陷
無。

## 備註
正式環境若未提供 JOTFORM_API_KEY，全套會有 P-1 的 2 個失敗（既有，建議另立 backlog 讓這兩測試自備金鑰）。
