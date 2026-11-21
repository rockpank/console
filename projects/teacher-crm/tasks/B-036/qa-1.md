---
verdict: 通過
---

# B-036 QA 第 1 輪

範圍：worktree 相對 origin/master 的變更（tests/db/test_jotform_session_hooks.py、specs/022-*）。環境：`COMPOSE_PROJECT_NAME=b-036 docker compose run --rm`，JOTFORM_API_KEY 為命令列假值。

| 項目 | 結果 |
|---|---|
| 目標檔 test_jotform_session_hooks.py | 4 passed |
| tests/unit + tests/db 全套 | 903 passed（208s） |
| ruff check／format --check（目標檔） | 通過 |
| 反向驗證：sync.py 第 134 行 `except Exception` 暫改為 `except KeyboardInterrupt` | 新測試 `test_an_unexpected_error_inside_the_sync_is_swallowed_...` 失敗（RuntimeError: 意外 冒出），其餘 3 個通過 |
| 還原 | 已還原；`git diff -- src` 為空，狀態僅剩 tests 檔修改與 specs 新增 |

測試現在經 fake_jotform.failures 注入，真實走過 client 與 sync 路徑，並斷言 replace_options 呼叫 1 次；確實能偵測 except 被移除。

缺陷：無。備註：impl-notes 稱全專案 `ruff check .` 有 22 個既有錯誤，本輪未重跑（範圍外）。
