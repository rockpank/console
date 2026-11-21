---
status: done
tests: 通過
---

# B-028 補測實作紀錄

套件 `specs/018-fix-test-amount-and-gateway-settings-validation`，T001–T010 全部勾選 [X]。只新增測試檔，src／conftest／test_gateway_settings.py 未動。

## 變更檔案（worktree 內，未 commit）
- 新增 `tests/unit/test_form_amount_validation.py`（`_deposit_error` 參數化 13 例、GatewaySettingsForm 藍新長度，免 DB）
- 新增 `tests/db/test_amount_validation_pages.py`（前端課／商品表單、藍新設定頁、人工建單無前端課）
- `specs/018-.../tasks.md` 勾選；`docs/code_map/*` 由 `python3 scripts/code_map.py update` 更新（6 檔）；specs/018 為前置產物（未追蹤）

## 與規劃的差異
- `project_products` 頁用的是 `AdvancedProductForm`，不是 `ProductForm`；`ProductForm` 只在 `project_front_course` 頁使用，且該頁已有前端課時 POST 直接 403，無法由頁面走到 forms.py:246。故前端課案例改走 `project_front_course` 頁（訂金、非整數價格、缺價格＋訂金 0、不同專案各一個），「第二個前端課」改直接建 `ProductForm`（需 DB）驗證訊息。
- forms.py:251（`validate_constraints` 的 `pass`）覆蓋率仍為未覆蓋：Django 在 clean 失敗時不會呼叫它，無獨立可測行為（與規劃備註一致）；我另寫一例確認第二個前端課只回報一則錯誤，但此例無法證明移除該覆寫會變紅（不可動 src 驗證）。

## 驗證有效性（暫改預期，確認會紅後已還原）
逐一把斷言字串／數值暫改錯，皆有對應測試轉紅：前端課不能設定訂金（4 失敗）、訂金範圍訊息（5）、已有前端課訊息（1）、HashIV 訊息（5）、HashKey 訊息（4）、專案尚未設定前端課費用（2）、「無法建立：」（1）、價格必須是 1 以上的整數（1）、請輸入價格（1）、報名／訂單筆數 (0,0)→(1,1)（2）、302→200（4）、金額 1500→1501（1）、商品筆數（3＋1）、`is_valid` 反向（1）。過程中第一次用 "X" 替換因 HTML 內必含 X 而誤判全綠，已改用唯一字串重做。檔案已確認還原。

## 實際輸出
- 新增測試：39 passed
- `ruff check src tests`：All checks passed；`ruff format --check`：190 files already formatted
- `pytest tests/unit tests/db --cov=src`：942 passed（基線 942-39=903，未減少）；TOTAL 98%（>=95）；forms.py 99%（僅 251）、registration.py 99%（165、178 非本任務）；142 與 222、243、246、356 已覆蓋
- `manage.py check`：no issues；`makemigrations --check --dry-run`：No changes detected
- `code_map.py update` 後 `check`：OK（tree 59d365c689fa）
- `validate_artifacts.py all --package 018-...`：兩份皆 OK
- 未跑 make test-integration；COMPOSE_PROJECT_NAME=b-028；JOTFORM_API_KEY 以命令列假值提供

## 缺陷／建議新項目
- 未測出實際缺陷。
- 建議（低）：`ProductForm.validate_constraints` 的空覆寫（forms.py:250-252）實際上不會被執行到，可評估移除或以 `# pragma` 處理；非本任務範圍。
