status: done
tests: 通過

# B-058 實作紀錄（023-shared-http-transport）
- T001～T024 全部完成並勾選。新增 src/crm/http.py（Transport、TIMEOUT_SECONDS=15、urllib_transport 逐字搬入）；line/client.py 改由 crm.http 匯入（保留 urllib_transport re-export，API_BASE 留原處）；jotform/client.py 改頂層 from crm.http import。
- 測試：tests/unit/test_line_transport.py 新增 2 案例（BE-SVC-06/07，先 RED：ModuleNotFoundError）、匯入拆成 crm.http / crm.line.client。
- 基線 32 passed -> 34 passed（三個相關檔）。全量 pytest tests/unit tests/db：905 通過（需 JOTFORM_API_KEY 假值；未帶時 tests/db/test_jotform_sync_command.py 有 2 案例因環境缺 key 失敗，帶假值後 11 passed）。覆蓋率 97%。
- ruff check／format 通過；manage check 無問題；makemigrations --check --dry-run 無變更；codemap check OK；validate_artifacts OK；grep 互不匯入通過。
