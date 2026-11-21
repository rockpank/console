verdict: 通過
round: 1

# B-031 QA 第 1 輪

環境：worktree B-031/teacher-crm，COMPOSE_PROJECT_NAME=b-031-qa，假 JOTFORM_API_KEY（只在命令列）。

| 項目 | 結果 |
|---|---|
| 新測試檔 tests/db/test_webhook_to_line_payment_reminder.py | 2 passed |
| 全套 pytest tests/unit tests/db | 1236 passed, 1 warning（既有 naive datetime 警告，與本任務無關） |
| ruff check／format --check（僅新檔） | All checks passed／already formatted |
| ruff 全專案 | check 22 errors、format 6 檔待格式化；新檔乾淨，變更檔只有新檔與 code_map（見下），判定為既有問題，非本任務造成（未逐檔列出） |
| codemap-check | OK 最新 |
| 未動 src/、conftest、line_helpers.py | git status 僅 docs/code_map、specs/030-*、新測試檔 |
| skip／xfail | 無 |

## 斷言有意義性（暫時破壞）
將預期改錯（`== order.id` 改 `!=`、kind 改 "payment_reminderX"）後，兩個測試皆轉紅（2 failed）；還原後 2 passed，git status 與破壞前一致。

## 檢視
- 案例 1 涵蓋 webhook 建單（學員/訂單 PENDING/報名各 1）、LineAccount 啟用、fake 推播對象、付款連結 token 對應訂單、OutboundMessage payment_reminder/SENT。
- 案例 2 涵蓋他專案同名同電話學員無 LineAccount／OutboundMessage，token 不等於他專案訂單。
- 規格第二點「只對專案 A 跑 sync_notifications」已由 run_flow 達成。

缺陷：無。規格疑義：無。
