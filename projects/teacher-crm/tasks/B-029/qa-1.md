verdict: 通過

# B-029 QA 第 1 輪（補測，獨立重跑）

環境：worktree `worktrees/B-029/teacher-crm`，`COMPOSE_PROJECT_NAME=b-029-qa`，本機無 make，改用 docker compose run。JOTFORM_API_KEY 以 `-e` 假值傳入，未寫入檔案。

## 實測結果
| 項目 | 結果 |
|---|---|
| ruff check src tests | All checks passed |
| ruff format --check | 193 files already formatted |
| manage.py check | no issues |
| makemigrations --check --dry-run | No changes detected |
| pytest tests/unit tests/db --cov=src | 961 passed（基線 903，增加 58），覆蓋率 97%（門檻 95%）。與 engineer 回報一致 |
| codemap-check | OK，無 STALE |

## 新測試有效性
- 零變更確認：`git status` 只有 docs/code_map 5 檔（自動產生）與新增的 5 個測試檔和 specs/019 目錄。src、models、migrations、所有 conftest 均無變更。
- 變異驗證（在複本檔上改預期，已刪除複本，工作樹已還原）：
  - 路由測試的 404 預期改成 200：全部轉紅。
  - webhook 的 400 預期改成 200：轉紅。
  - `_check_project` 單元測試的訊息比對改成錯誤字串：轉紅。
  - 合計 30 failed、18 passed。通過的是對照組與不依賴被改預期的案例，符合預期。
- 對照組：路由檔 11 個路由參數都有 `test_control_same_request_on_own_project_is_not_404`。該測試檢查回應為 200 或 302，並用 effect 斷言確認 A 的資料真的被改到。webhook 有 `test_control_own_secret...`，以及兩個專案各自 secret 的交叉測試。服務層有 `test_control_same_project_student_is_accepted`。
- 另有 `test_snapshot_detects_changes_to_project_b`，證明資料快照比對本身有鑑別力（含密文欄位）。
- 沒有 skip 或 xfail。

## code map 差異（只讀比對）
`src.crm.md` 的 diff 只有 3 處 `tests:` 反向連結行變動。`attendance.py` 新增 `test_attendance_cross_project`、`test_project_consistency`；`models.py` 與 `orders.py` 的測試數量增加。src 的 imports、函式、行數都沒變。結論：因新測試檔而更新，**不是**地圖原本與現況有落差，推測不成立。

## 缺陷與規格疑義
無。

## 備註
- 規模：約 58 個參數化後案例，超過協議建議的約 10 個，已由 quickfix 註明，屬調度者裁示範圍。
- 容器：b-029-qa-db-1 仍在執行。依規定不執行 `docker compose down`，請調度者決定收尾。
