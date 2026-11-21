---
status: done
validate: 未執行（本角色無 Bash，需調度者或工程師執行 python3 .agents/skills/_shared/validate_artifacts.py all --package 018-fix-test-amount-and-gateway-settings-validation）
---

# B-028 規劃備註

- 套件：`specs/018-fix-test-amount-and-gateway-settings-validation/`（`quickfix.md`、`tasks.md`；命名依 quickfix RULES 的 `<NNN>-fix-<slug>`，與 work-plan 建議名不同）。
- 3 個切片，案例 ID 受 validator 限制用 BE-API/BE-SVC：BE-API-01 商品訂金／前端課唯一（forms 222、243、246、251）、BE-API-02 藍新 HashKey／IV（356）、BE-SVC-01 人工建單無前端課（registration 142）。
- 建議新檔：`tests/unit/test_form_amount_validation.py`（`_deposit_error`、GatewaySettingsForm，免 DB）、`tests/db/test_amount_validation_pages.py`。ProductForm 第 246 行需 DB，故放 db 檔。
- 補測型：測試寫成即綠，非真 RED；已在切片註明以暫改預期驗證測試有效。
- 發現：`forms.py:251` 的 `validate_constraints` 只是 `pass`，由 clean 以第 246 行覆蓋，無獨立可測行為。未發現實際缺陷。
- 現有 `test_provider_flows.py:179` 已測 HashKey 過短，HashIV 過短無測試。
- 不動 src、conftest、`tests/db/test_gateway_settings.py`。
