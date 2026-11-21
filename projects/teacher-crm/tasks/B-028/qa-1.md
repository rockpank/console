---
verdict: 通過
task: B-028
round: 1
---
# QA 報告 B-028（補測：金額與設定驗證）第 1 輪

## 實跑結果（COMPOSE_PROJECT_NAME=b-028-qa，JOTFORM_API_KEY 以 -e 假值傳入）
| 項目 | 結果 |
|---|---|
| ruff check + format --check | 通過（190 files formatted） |
| pytest tests/unit tests/db | 942 passed、0 failed（基線 903，+39） |
| 覆蓋率 | TOTAL 98%（4178 stmts / 102 miss）；forms.py 99% 僅剩 251；registration.py 99% 剩 165,178 |
| manage check | no issues |
| makemigrations --check --dry-run | No changes detected |
| codemap-check | OK（265 檔） |
| src／conftest／既有測試變更 | 零（git diff -- src tests 為空；新增僅 2 個測試檔＋specs/018＋code_map 重產） |

與 engineer 回報（942、98%）一致。

## 新測試有效性（複本突變，已刪除複本）
在複本上改預期：前端課訂金訊息、價格整數訊息、無前端課費用訊息、HashIV 訊息（db 與 unit）、_deposit_error(價格缺漏,0)。結果 11 failed / 28 passed，被改的案例全數轉紅，其餘不受影響。原目錄未動。

## 對 backlog B-028 驗收的判斷
驗收：各驗證各有一個測試、錯誤時不寫入資料、訊息明確、金額一律整數。
| 項目 | 覆蓋 | 判定 |
|---|---|---|
| 訂金 <=0 且價格缺漏（:222） | unit 參數化 + db 頁（price 缺漏+deposit 0，無寫入） | 滿足 |
| 前端課帶訂金（:243） | db 走 project_front_course，Product 數為 0 | 滿足（改走實際使用 ProductForm 的頁面，合理） |
| 訂金 >= 價格、ProductForm | 直接建 ProductForm 驗證 | 滿足（表單層；頁面層既有 advanced 案例在 test_gateway_settings） |
| 第二個前端課（:246） | 直接建 ProductForm，錯誤訊息精確比對，count 不變 | 滿足但僅表單層，無頁面層（該頁 ProductForm 的唯一入口即 front_course，且該頁是否另有「已存在」處理未以頁面驗證） |
| 價格整數 | 1500.5 -> 「價格必須是 1 以上的整數」，不寫入 | 滿足 |
| 藍新 HashKey／HashIV | unit+db：IV 15/17/多位元組、Key 31/33、先後順序、未啟用、ECPay、合法對照；db 確認不寫 GatewayConfig、不回顯金鑰 | 滿足 |
| 人工建單無前端課費用 | resolve 直呼與頁面；無 Registration／Order、狀態仍 REVIEW；有前端課後成功對照 | 滿足 |
| 錯誤時不寫入資料 | 各 db 案例均驗證 | 滿足 |

調整評估：project_products 用 AdvancedProductForm、ProductForm 僅用於 front_course 頁的調整不影響驗收；forms.py:251 的 validate_constraints 空覆寫為無行為程式碼，無法也不需要覆蓋（測試以「只回報一次錯誤」間接保護，但 :251 仍列未覆蓋，屬可接受）。

## 缺口與低風險備註
- :251 未覆蓋（空覆寫，無行為）；registration.py:165,178 非本任務範圍。
- 第二個前端課無頁面層（HTTP）案例；建議（低優先）補一個 POST project_front_course 在已有前端課時的行為，以確認該頁對重複建立的實際處理（該頁可能是編輯既有而非新增，屬行為確認，非缺陷）。
- 無缺陷、無規格疑義、無資安問題發現。

## 結論：通過
