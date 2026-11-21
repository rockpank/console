---
status: done
tests: 通過
---

# B-036 impl-notes

- 變更：`tests/db/test_jotform_session_hooks.py`（移除 monkeypatch／boom，改 `fake_jotform.failures = [RuntimeError("意外")]`，加斷言 `calls_named("replace_options")` 長度 1）；`specs/022-*/tasks.md` T001-T004 回寫 `[X]`。未動 `src/`。
- 測試：`pytest tests/unit tests/db` 903 passed；目標檔 4 passed。
- Lint：目標檔 ruff check／format 通過；全專案 `ruff check .` 有 22 個既有錯誤（非本檔，未處理）。
- 環境：本機無 `make`，改用 `COMPOSE_PROJECT_NAME=b-036 docker compose run --rm app …`，JOTFORM_API_KEY 用假值。
- `make codemap` 未執行（只改測試，無 src 變動；make 不可用）。
- 未做：暫時移除 `except Exception` 的反向驗證（RED 非必要）。
