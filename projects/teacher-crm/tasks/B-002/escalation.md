---
resume_at: 資安
resolved: true
---

# B-002 升級紀錄

- 協議第 4 節條件 6：工程師變更的檔案超出 work-plan 批次 13 的 B-002 檔案範圍。

## 目前狀況

- `src/crm/checkout.py`、`forms.py`、`views.py` 與新增 `tests/db/test_fake_gateway_disabled.py`、`test_gateway_settings.py` 都在範圍內。
- 超出範圍的既有測試檔（各只加 2 行 `pytestmark = pytest.mark.usefixtures("fake_gateway_enabled")`，不改斷言）：`tests/db/test_checkout.py`、`test_pay_page.py`、`test_payments_search.py`、`test_jotform_gateway_numbers.py`。
- 原因：`gateway_for` 開始擋假金流後，這些以 `provider="fake"` 建專案的既有測試轉紅，必須補前置設定。`tests/db/conftest.py` 未加 autouse（否則關閉旗標的案例失去意義）。
- 工程師回報全套 1245 通過、覆蓋率 98%、ruff 通過（尚未經資安與 QA 重跑）。

## 選項

- A. 放行：把上述 4 個測試檔納入 B-002 範圍，繼續資安與 QA。
- B. 退回：改用其他做法（例如在 conftest 加 autouse，但會讓關閉旗標的案例失去意義）。

建議：A，因為只補前置設定、未改斷言，且 QA 會重跑確認。

## 處置（2026-11-18）

- 使用者授權新增協議第 8 節「測試前置例外」（條件 6 的免升級類別）。對照 `impl-notes.md`：(1) 5 個測試檔、23 個紅燈為實測；(2) 只加 `pytestmark` 與把 `KEY-SECRET-123` 換成 32 字元常數 `HASH_KEY`（斷言結構不變，比對值隨常數改變）；(3) 已逐檔列出。(4) 由 QA 以 `git diff` 驗證斷言未被弱化，不認可就重新升級。
- 因此本項不再需要使用者裁示 A／B，繼續資安與 QA。
