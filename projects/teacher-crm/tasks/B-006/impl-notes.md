---
status: done
tests: 通過
---
# B-006 impl-notes（042-fix-onsite-paid-default-unchecked）
- T001～T004 完成並回寫 [X]。紅燈：測試改成斷言不含 `name="paid" checked`，1 failed（原因正確）；樣板拿掉 `checked` 後轉綠。
- 變更：`src/crm/templates/crm/project_attendance.html`（第 91 行）、`specs/TEST_LIST.md`（901、909）、`tests/db/test_attendance_pages.py`、`docs/code_map/`（codemap update 產生）、`specs/042-.../tasks.md`。
- 結果（用 docker compose run 等效 make，project=b-006，假值金鑰）：pytest unit+db 903 passed；覆蓋率 97%；ruff check 通過、format 188 files formatted；manage check 無問題；makemigrations --check 無變更；codemap 更新後 check OK；validate_artifacts all 通過。
- 注意：worktree 內本來就有 .env（未讀取），compose 以假值環境變數傳入。
