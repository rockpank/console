---
status: done
tests: 通過
---

# B-029 實作紀錄（補測：專案隔離守門）

T001-T011 全數完成並於 `specs/019-fix-project-isolation-guard/tasks.md` 勾選。只新增 5 個測試檔；src、model、migration、conftest 無變更。fixture 全寫在各檔內。未發現產品缺陷（新測試一開始即綠）。

## 新增測試檔（共 58 個測試）
- `tests/db/test_project_isolation_routes.py`（37）：session_import／session_delete／attendance_walk_in／attendance_close／front_course／message_templates／line_settings。A 成員（MANAGER、STAFF）打 B 網址，以及 A 網址配 B 場次，皆 404，且 B 與 A 全部帶 project 的資料列（含 LineConfig 密文）前後相同；對照組以各路由最低可執行角色打 A 自己的資源，狀態為 200/302，且 A 資料確實改變；快照自證測試。
- `tests/db/test_line_webhook_cross_project.py`（7）：A 的 secret 簽章（follow、text、混合）打 B 回 400，B 資料與 fake LINE 無任何動作；對照組 B 自己的 secret 回 200 且有回覆；雙向 secret 互通矩陣。不測空 secret（B-009）。
- `tests/db/test_attendance_cross_project.py`（4）與 `tests/unit/test_attendance_check_project.py`（4）：`_check_project`、`mark_attendance`、`check_in_early` 跨專案丟 `AttendanceError("學員不屬於這個專案")`，Attendance／Registration／Reschedule 數量不變；對照組同專案通過。
- `tests/db/test_project_consistency.py`（6）：`apps.get_models()` 動態掃描，涵蓋集合斷言含 Registration／Order／Payment／Attendance；負向自證（故意不一致的 Registration、Attendance、Order、Payment 皆被抓到）；經 `register_walk_in`、`check_in_early`、`mark_attendance`、`ensure_intro_order`、`mark_order_paid` 兩專案產生的資料違規為空。

## 與規格的微調
- line_settings 需 `CONFIGURE_INTEGRATIONS`（僅 admin），manager 打自己專案會 403；對照組因此用 ADMIN 打 A（admin 本來就看得到所有專案，無法扮演「A 成員」，攻擊側仍以 A 的 MANAGER／STAFF）。
- 「A 網址配 B 場次」：STAFF 缺少該動作權限時會先 403（權限測試範圍，非隔離缺陷），故該目標只對有權限的角色（MANAGER，或動作只需 STAFF 的路由）斷言 404。
- 巡檢器用 `field.name__project_id` 對 `F("project_id")` 的 exclude 做查詢式比對；Payment 經 `order` 外鍵比對 `order.project_id`。

## 暫改預期值驗證（補測不會先紅）
各檔暫改預期（404→200、400→200、200/302→404、訊息改字、`== []`→`!= []`、`in`→`not in`、對照組 effect 反向、快照比對反向、單元 `is None` 反向、`count()==1`→2）後執行，共 58 個測試皆至少在一種暫改下轉紅（第一輪 52 紅，第二輪補測漏網的 6 個全紅），之後已從備份還原，檔案與最終綠燈版本一致。

## 驗證輸出（COMPOSE_PROJECT_NAME=b-029，JOTFORM_API_KEY 以命令列假值，未寫檔、未跑 integration）
- `ruff check src tests`：All checks passed；`ruff format --check`：193 files already formatted
- `pytest tests/unit tests/db --cov=src`：961 passed（基線 903，新增 58）；覆蓋率 TOTAL 97%
- `manage.py check`：no issues；`makemigrations --check --dry-run`：No changes detected
- `scripts/code_map.py update`：已更新（268 檔）；`check`：OK 最新
- 未做 `validate_artifacts`（前置已通過，本任務只勾選 tasks.md）

## 變更檔案
新增：上列 5 個測試檔。修改：`specs/019-fix-project-isolation-guard/tasks.md`（勾選）、`docs/code_map/{INDEX.md,manifest.json,modules/src.crm.md,modules/tests.db.md,modules/tests.unit.md}`（由 `code_map.py update` 產生；src.crm.md 的變動為既有地圖與現況的行號／索引差異，非本任務改 src）。
`specs/019-fix-project-isolation-guard/` 本身為前置產物（未追蹤）。

## 建議新項目
無（未發現缺陷）。可選：S1 資料健檢 command（quickfix 已列為另案）。
