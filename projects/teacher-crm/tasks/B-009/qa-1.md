verdict: 通過

# B-009 QA 交付驗證 (round 1)
範圍：僅「secret 為空」。環境：docker compose，COMPOSE_PROJECT_NAME=b-009，假 JOTFORM_API_KEY（命令列提供）；未讀 .env、未 down、未 commit。

| 項目 | 結果 |
|---|---|
| pytest tests/unit tests/db --cov | 905 passed，0 failed，覆蓋率 97.44%（門檻 95 達成） |
| ruff check / format --check | 通過 / 189 files already formatted |
| manage check | 無問題 |
| makemigrations --check --dry-run | No changes detected |
| code_map check | OK 最新（264 檔） |
| 變異：移除 `not channel_secret or` 守衛 | 2 個測試轉紅（單元 test_line_signature_rejects_empty_channel_secret、db test_webhook_with_empty_channel_secret_rejects_event_signed_with_empty_key）；還原後 git diff 與變異前逐字相同 |

觀察：實際只改 src/crm/domain/line.py（views.py 未改）；line_webhook 把 verify_signature 的 False 轉 400，故 BE-API-02 以 db 測試驗證通過。

已知落差（不算失敗）：「非 LINE 模式一律 400」未做，待使用者決定。
缺陷：無。
