status: done
tests: 通過

# B-039 用語統一（規格 046，快速路線）impl-notes

範圍外（使用者裁示）：「前端課／後端課」標示不做。tasks.md T001–T012 已全部回寫 [X]。

## 變更檔案（worktree `teacher-crm/`）
產品碼：
- `src/crm/domain/project_nav.py`：側欄「課程費用與贈品」→「進階課程費用」
- `src/crm/templates/crm/project_products.html`：互指改「前端課費用」；按鈕「建立進階課程」→「新增進階課程」；「更新」→「儲存」
- `src/crm/templates/crm/project_front_course.html`：互指改「進階課程費用」；「建立」→「新增」（提示、按鈕）；「更新」→「儲存」
- `src/crm/templates/crm/project_notifications.html`：「課程與費用」→「前端課費用」；「請 admin」→「請系統管理員」
- `src/crm/templates/crm/project_jotform_settings.html`：去除 `JOTFORM_API_KEY`（改「請系統管理員在系統設定加入 Jotform 金鑰」）、`admin`、`scheduler 服務`（改「排程服務」）；僅改可見文字
- `src/crm/views.py`：`pay_return` 部分付款訊息 `NT$ {order.paid_amount:,}`；兩處 docstring「銷講」→「前端課」
- `src/crm/orders.py`、`src/crm/reports.py`、`src/crm/line/notifications.py`：docstring／註解舊稱改「前端課」（`retagging.py`、migrations 未動）
- `docs/wording.md`（新增）：用語表
測試：
- `tests/db/test_wording_labels.py`（新增，4 個測試，涵蓋 BE-API-01／02／03）
- ALIGN（舊稱／格式斷言）：`tests/unit/test_project_nav.py`（5 處「課程費用與贈品」→「進階課程費用」）；`tests/db/test_pay_page.py` 1 處 `"5000"` → `"5,000"`（`test_return_page_shows_collected_amount_after_deposit`，訊息改千分位後的連動）
- `tests/unit/test_wording.py` 未動。
- `specs/046-.../tasks.md`：勾選 [X]。

## 紅燈證據
`pytest tests/db/test_wording_labels.py`：4 failed（側欄無「進階課程費用」；兩頁含 admin／JOTFORM_API_KEY／scheduler；訊息為 `NT$ 1200`），原因與規格相符。綠燈：4 passed。

## 品質關卡（實際輸出）
- `pytest tests/unit tests/db --cov=src --cov-fail-under=95`：1441 passed、0 failed、1 warning；覆蓋率 98.19%（門檻 95%）。
- `ruff check src tests`：All checks passed；`ruff format --check src tests`：244 files already formatted（`make lint` 範圍）。
- `manage.py check`：no issues；`makemigrations --check --dry-run`：No changes detected。
- `validate_artifacts.py all --package 046-fix-wording-unification`：quickfix、tasks 皆 OK。
- `code_map.py check`：STALE（預期；不手改 docs/code_map/，請合併者重跑 `python3 scripts/code_map.py update`）。
- 未跑 tests/integration。
- 備註：中途曾兩批 pytest 並行共用同一 compose DB，造成假失敗與 setup error；已單獨重跑為全綠。

## 假設與回報
- 收款訊息實際在學員端 `pay_return`（約 962 行），非後台登記 view；規格「已收到款項」即此處。
- 動詞：僅改 products／front_course 頁；`project_payments.html` 的「建立訂單」、`project_attendance.html` 的「會建立學員」依「歧義保守不改」未動（用語表未明列為按鈕以外；建議 pm 確認是否改「新增訂單」）——此二處另有測試註解引用「建立訂單」。
- 未超出 work-plan 批次 28 檔案範圍以外的產品碼；新增檔為 `docs/wording.md`、測試檔。注意：樣板與 B-040、B-041 合併時可能衝突。
