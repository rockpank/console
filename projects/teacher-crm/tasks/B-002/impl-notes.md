---
status: done
tests: 通過
---

# B-002 impl-notes：假金流旗標關閉時不可用，且 HashKey 至少 32 字元

worktree：`/home/user/web/console/worktrees/B-002/teacher-crm/`（分支 t-B-002，未 commit）。spec package：`specs/009-fix-fake-gateway-when-disabled`，T001–T010 皆已回寫 `[X]`。

## 實作
- `src/crm/checkout.py`：新增 `fake_gateway_blocked(config)`（單一判斷函式）；`gateway_for` 在 fake 且旗標關閉時拋 `GatewayNotConfigured("付款設定需重新設定")`。`get_gateway` 未動。notify 既有的 `except GatewayNotConfigured` 回 400；`card_available` 因呼叫 `gateway_for` 自動為 False。
- `src/crm/forms.py`：`GatewaySettingsForm` 旗標關閉時過濾 `provider` choices 並在 `clean` 拒絕 fake；旗標開啟且勾選啟用時，fake 的 HashKey 新填需 >= 32 位元組（常數 `FAKE_HASH_KEY_MIN_BYTES`），無已存金鑰且未填則拒絕，已有已存金鑰留空則沿用。
- `src/crm/views.py`：`pay_page` 僅在「config.enabled 且 provider=fake 且旗標關閉」時顯示「付款設定需重新設定，請聯絡行政人員」；其他 card_available 為 False 情境維持「這個專案目前沒有開放信用卡付款」（`test_pay_page.py` 該案例未改、通過）。未牽動其他情境，無需停下回報。

## 測試
- 新增 `tests/db/test_fake_gateway_disabled.py`（11 案例，含專案 B 不受影響、旗標開啟仍可用、HashKey 空／31／32／沿用／未啟用不檢查）。RED 階段 5 個失敗，原因符合預期（選項仍列假金流、POST 成功儲存、gateway_for 仍回 FakeGateway／notify 入帳、短 HashKey 可儲存）。
- 全套：`pytest tests/unit tests/db --cov=src` 1245 passed（基線 1234，新增 11），覆蓋率 TOTAL 98%（checkout 100%、forms 99%、views 99%）。
- `ruff check src tests`：All checks passed；`ruff format --check src tests`：217 files already formatted。
- `manage.py check`：no issues；`makemigrations --check --dry-run`：No changes detected。
- `code_map.py update` 後 `check`：OK（tree 7d7254f520e2）。`validate_artifacts.py quickfix|tasks|all`：OK。

## 超出 work-plan 範圍的檔案（以全套紅燈為準，共 23 個既有測試轉紅）
只補前置設定，沒有刪改、skip 任何測試，斷言語意未變；`tests/db/conftest.py` 未動。
| 檔案 | 紅燈數 | 處理 | 為何 |
|---|---|---|---|
| `tests/db/test_checkout.py` | 12 | 加 `pytestmark usefixtures("fake_gateway_enabled")` | 以 provider=fake 呼叫 `handle_gateway_callback`／`gateway_for` |
| `tests/db/test_pay_page.py` | 3 | 同上 | 付款頁刷卡流程使用 fake |
| `tests/db/test_payments_search.py` | 1 | 同上 | 建 fake 設定並進付款流程 |
| `tests/db/test_jotform_gateway_numbers.py` | 2 | 同上 | 同上 |
| `tests/db/test_gateway_settings.py` | 5 | 加 pytestmark；`KEY-SECRET-123` 改為具名常數 `HASH_KEY`（32 字元） | 表單儲存 fake 需 HashKey >= 32；斷言中的比對值隨常數改變（不可避免，斷言結構不變） |
`test_gateway_notify_invalid_payload.py` 與 `course_helpers.py` 使用者在全套測試中未轉紅，故未動。其餘檔案（`test_checkout.py` 內 `KEY` 等）因不經表單，短 HashKey 不需改。
另有 `docs/code_map/*` 由 `scripts/code_map.py update` 重新產生（未手改）。

## tasks.md 依賴段假設（揭露）
1. HashKey 空白且已有已存金鑰時視為沿用。
2. 只在勾選啟用時檢查 HashKey 長度與必填（未啟用可存空）。
3. 長度以 UTF-8 位元組數計，與藍新分支一致。
4. 已存的舊短 HashKey 不回溯檢查；旗標開啟時照常使用。
補充假設：友善文案條件含 `config.enabled`，使「fake 但未啟用」維持原文案（`test_pay_page.py:231`）。

## 殘餘風險／備註
- 正式庫若已有 provider=fake 的專案，旗標關閉後這些專案刷卡會顯示需重新設定（預期行為，運維端盤點由使用者另做）。
- 設定頁在旗標關閉且 DB 內已是 fake 時，下拉無選中項，需改選綠界／藍新。
- 全套測試以假 `JOTFORM_API_KEY` 在命令列提供，未讀 `.env`。
