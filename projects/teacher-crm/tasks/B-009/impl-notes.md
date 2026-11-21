---
status: done
tests: 通過
---
# B-009 impl-notes
- 範圍：僅 channel secret 為空（「非 LINE 模式一律 400」未做，待使用者決定）。
- 改動：`src/crm/domain/line.py` verify_signature 加 `not channel_secret` 守衛（views 不需改）；新增 unit 案例與 `tests/db/test_line_webhook_empty_secret.py`；tasks.md T001-T007 標 [X]；docs/code_map 由 codemap update 產生。
- RED：unit 回 True、webhook 回 200（修前實測）。GREEN：905 passed、覆蓋率 97%；ruff check/format、manage check、makemigrations --check 皆乾淨；code_map check OK；validate_artifacts OK。
- 環境：本機無 make，直接用 `docker compose run`（COMPOSE_PROJECT_NAME=b-009，compose 名稱不允許大寫）；JOTFORM_API_KEY 以命令列假值提供；make test 未跑 integration。
