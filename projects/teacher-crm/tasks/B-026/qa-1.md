---
verdict: 通過
task: B-026
round: 1
---

# QA 報告 B-026（併發重複操作回友善訊息）

範圍：worktree `worktrees/B-026/teacher-crm`，相對 origin/master 的變更：`src/crm/attendance.py`、`src/crm/orders.py`、新增 `tests/db/test_concurrent_duplicate_friendly_error.py` 與 `specs/045-*/`。未修改 worktree 內任何檔案。

## 品質關卡（自己重跑，COMPOSE_PROJECT_NAME=b-026-qa，JOTFORM_API_KEY=fake）

| 關卡 | 結果 |
|---|---|
| ruff check src tests | All checks passed |
| ruff format --check src tests | 223 files already formatted |
| manage.py check（src/manage.py） | no issues |
| makemigrations --check --dry-run | No changes detected |
| pytest tests/unit tests/db --cov=src --cov-fail-under=95 | 1301 passed，覆蓋率 98.17%（達標）；attendance.py 100%、orders.py 100%（含分支）|
| 併發測試檔重複 3 次 | 7 passed x 3，無不穩定 |

P-1（無 JOTFORM_API_KEY 的 2 個失敗）：因給了假值，未出現。
未執行：codemap-check（任務指定範圍外，工程師需於收尾確認 `make codemap-check` 無 STALE）。

## 預期行為對照

| quickfix 預期 | 測試 | 判定 |
|---|---|---|
| 1 建單併發：一成功、一 OrderError（含「重新整理」）、僅 1 張有效單；序列訊息不變 | test_concurrent_create_order_loses_with_friendly_order_error、test_serial_duplicate_create_order_keeps_original_message | 通過 |
| 2 現場報名併發：一成功、一 AttendanceError；學員/報名/到場/訂單各 1 且訂單已付款；涵蓋學員不存在與已存在兩起點；序列訊息不變 | test_concurrent_walk_in...（參數化 2 種）、test_serial_duplicate_walk_in_keeps_original_message | 通過 |
| 3 提前報到併發：一成功、一 AttendanceError；本場報名 1、較晚場次 0、到場 1、改期歷程 1；序列訊息不變 | test_concurrent_check_in_early...、test_serial_duplicate_check_in_early_keeps_original_message | 通過 |

併發測試使用 transaction=True、雙執行緒各自連線，並在「先查」檢查後以 Barrier 對齊，使競態每次必然發生（非靠時序碰運氣），三次重跑皆穩定。失敗方無部分寫入由各表計數斷言證明（交易整體回滾）。

## 修正前後行為與退化偵測（推理，未改檔）

- 序列重複：先查邏輯在 try 之前/之內以原訊息拋出，`OrderError` 於 create_order 內被拋出後不屬 IntegrityError，不被捕捉改寫；現場報名的 `_registered_here` 檢查在 try 之外。序列測試以 match 驗證原訊息，維持不變。
- 成功路徑：僅外包 try/except，邏輯與縮排內容一致；全套 1301 測試（含既有出席／訂單測試）通過。
- 註：register_walk_in 的 `except (IntegrityError, OrderError)` 會把「序列」情境下 ensure_intro_order 的 OrderError 也轉成 AttendanceError 友善訊息；序列路徑由 _registered_here 先攔，已有訂單時 ensure_intro_order 不會拋，既有測試全綠，視為無影響。
- 退化偵測：拿掉任一 `except`，併發後完成者會拋 IntegrityError（或 walk-in 的 OrderError 未轉型），`isinstance(errors[0], AttendanceError/OrderError)` 斷言轉紅；覆蓋率 100% 亦代表各 except 分支皆被執行。

## 缺陷清單

無阻擋／高／中缺陷。

低（觀察，不影響結論）：
- L-1：quickfix 的「觀測通道」列有「端點回應為重新導向／非 500、帶錯誤訊息」，新測試只驗領域函式，未做 view 層（project_order_create、project_attendance_walk_in、project_attendance_early）訊息呈現測試。views 已接 AttendanceError/OrderError 並以 messages.error 呈現（依 quickfix 預期不需改），風險低；建議可補一個 client 層案例，非必要。
- L-2：未驗證 make codemap-check（見上）。

## 結論

通過。品質關卡全綠、覆蓋率 98.17%、併發測試穩定 3/3，三個預期行為皆有對應且能抓到退化。
