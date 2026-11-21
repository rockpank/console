---
verdict: 通過
round: 1
task: B-011
spec: 043-builtin-daily-scheduler
date: 2026-11-19
---

# B-011 QA 第 1 輪（整體，累積 6 輪實作）

工作目錄 `/home/user/web/console/worktrees/B-011/teacher-crm/`（分支 `t-B-011`，未提交變更）。結果全部自己重跑；impl-notes 只當範圍線索。指令照 engineer-rules 第 4 節，`COMPOSE_PROJECT_NAME=b-011-qa`，`-e JOTFORM_API_KEY=fake -e COVERAGE_FILE=/tmp/.coverage -e RUFF_CACHE_DIR=/tmp/.ruff_cache -e PYTHONDONTWRITEBYTECODE=1`、pytest `-p no:cacheprovider`。worktree 沒被我修改（破壞實測在暫存副本），無 root 擁有的檔案。

## 1. 品質關卡（實際輸出）

| 關卡 | 結果 |
|---|---|
| ruff check src tests | All checks passed! |
| ruff format --check src tests | 242 files already formatted |
| manage.py check | System check identified no issues (0 silenced) |
| makemigrations --check --dry-run | No changes detected |
| pytest tests/unit tests/db --cov=src --cov-fail-under=95，第 1 次 | **1423 passed, 1 warning in 450.50s**；Total coverage **98.18%**（Required 95% reached） |
| 同上，第 2 次 | **1423 passed, 1 warning in 432.40s**；Total coverage **98.18%** |

- 兩次全套皆 0 失敗；`test_jotform_sync_command::test_an_invalid_key_stops_automatic_retries_for_that_form_only` 兩次都過，順序相依偶發未再出現（兩次都帶 JOTFORM_API_KEY=fake，P-1 的 2 個失敗在本輪不適用、未另測無 key 情境）。
- 新檔覆蓋率：`daily_jobs.py` 99%（104 行 0 未覆蓋，10 分支 1 部分）、`domain/daily_schedule.py` 100%、`run_scheduler.py` 100%、`scheduler.py` 98%、`forms.py` 98%、`jotform/sync.py` 94%（4 行未覆蓋，屬既有程式，非本任務新增行）。
- 兩次 run 與部分破壞實測同時在跑（耗時較長），不影響結果。

## 2. Migration

0032 只含兩個 CreateModel、依賴 0031、無 RunPython。`tests/db/test_daily_job_migration.py`（2 案）在兩次全套中皆通過（套用／回退到 0031／再套用）；`makemigrations --check` 乾淨。通過。

## 3. 需求覆蓋（抽查）

- testplan「需求覆蓋對照」FR-001～025、NFR-001/002、SC-001～005、API-SCHED-01～14、INT-JOB-NOTIFY-01～11 皆有對應案例；實作的 `tests/db/test_daily_*.py`、`tests/unit/test_daily_*.py` 共 83 個測試，對照案例語意抽查：
  - 23:00 邊界：`test_at_2300_40_it_still_runs_but_the_2301_first_look_skips`、`test_first_look_at_2301_00_skips...`、`test_decide_2300_boundary_is_judged_by_the_minute`（破壞後會紅，見 4）。
  - 同日已執行優先（decide 與 run/catchup 整合）、啟動日為準、權限 admin/manager/staff/instructor（`test_staff_and_instructor_get_403...`、`test_daily_job_permissions`）、整批全有或全無（`test_a_valid_time_with_one_invalid_field_changes_neither_job`）、失敗／逾時隔離（`test_daily_scheduler_failures.py` 11 案＋JOURNEY-US5）皆有有效測試。
- 無 `skip`／`xfail` 加在新測試上（grep 只命中函式名中的 skipped）。
- 可追溯性缺口（低）：testplan 的 `BE-*` 案例 ID 大多沒有出現在測試檔內（測試碼中只有約 49 個不同 ID 字串、約 20 個 ID 如 BE-TASK-01～10、BE-API-13～23 找不到），只能靠測試名稱語意比對；tasks.md 有對照，但日後維護者要從 ID 找測試不易。建議在測試函式 docstring／註解標 `BE-xxx-nn`。不影響結論。

## 4. 破壞實測（暫存副本，worktree 未動；每項還原後以副本與 worktree 逐檔 cmp 確認一致）

先確認副本基準：目標測試 45 passed。每個破壞後只跑對應測試：

| # | 破壞 | 結果 |
|---|---|---|
| M1 | decide 的 `> LAST_RUN_TIME` 跳過分支改 `if False` | 紅：8 failed（含 2301 跳過、2300 邊界） |
| M2 | claim_and_run 的 IntegrityError 回 ALREADY_CLAIMED 改 `raise` | 紅：2 failed（循序佔位、兩執行緒同時佔位） |
| M3 | JOB_TIMEOUT 30 → 300 分鐘 | 紅：2 failed（逾時 31 分、US5 旅程）。註：30 分整的邊界未見獨立案例，僅 31 分 |
| M4 | recover_orphans 篩選改空集合 | 紅：3 failed |
| M5 | 設定更新 view 的 platform_admin_required 改 login_required | 紅：4 failed（instructor 403 等） |
| M6 | 表單 23:00 上限驗證改 no-op | 紅：2 failed（23:01、23:30） |
| M7 | view 在驗證失敗時仍進入儲存（破壞整批全有或全無） | 紅：1 failed（`...one_invalid_field_changes_neither_job`）；紅因是 view 層 KeyError 而非表單層部分寫入，但行為保護有效 |
| M8 | status_of 讓「已跳過」時不顯示過期（破壞並存） | 紅：3 failed |
| M9 | sync_all 移除 `.order_by("id")` | 紅：1 failed（`test_jotform_sync_all_order`，回歸測試確實鑑別） |
| M10 | decide 的 ran_today 優先判定改 `if False` | 紅：8 failed |
| M11 | run_date 改取 `timezone.localdate()`（非啟動時刻） | 紅：13 failed |
| M12 | 工作例外不再被捕捉 | 紅：3 failed |

12／12 皆會紅。M7 與 M3 的細項為觀察，非缺陷。

## 5. BE-TASK-18「跨午夜」評估

- testplan 原案（22:59 起、工作內推進 20 分鐘）實際只到 23:19，沒有跨午夜；工程師已誠實標注。`test_run_date_is_the_claim_day_even_when_the_job_runs_past_midnight` 因此只證明「run_date 是啟動日、隔日 23:00 仍新增一列」，**不足以證明跨午夜**。
- 補強案 `test_a_claim_made_before_midnight_keeps_the_start_day_when_the_job_ends_after_midnight` 直接以注入時鐘（23:59:30 → 隔日 00:05:00）呼叫 `claim_and_run`，斷言 `run_date == row.run_date == 啟動日`、傳給工作的 today 為啟動日、`finished_at` 當地日期為隔日、未逾時（歷時 5.5 分）。我認為這**足夠證明 FR-013 的核心**（以啟動當日為準），且 M11 破壞會讓 13 個測試紅，證明有鑑別力。
- 殘餘缺口（低）：真實排程迴圈下「23:00 啟動、工作跑過午夜」在 30 分鐘逾時規則下本來不可能發生（23:00 起算 30 分鐘到 23:30），所以只有 claim_and_run 層級的案例才有意義；非缺陷。
- 建議 testplan 改寫：BE-TASK-18 拆成 (a) 「claim_and_run 層」以注入時鐘模擬 23:59:30 佔位、00:05 結束，斷言 run_date／today／finished_at 日期（即現行補強案，升為正式案）；(b) 「迴圈層」改為 22:59 起、工作耗時 20 分鐘，只斷言無跨午夜情境下 run_date 與隔日新增列，並明寫「本案不驗證跨午夜」；刪除原敘述中「跨午夜」字樣以免誤導。同時註明 23:00 起算有 30 分鐘逾時上限，真正跨午夜只在 claim_and_run 單元層可驗證。

## 6. src/ 變更範圍

`git diff origin/master --stat`（src）：permissions.py、forms.py、jotform/sync.py、run_scheduler.py、models.py、scheduler.py、project_jotform_settings.html、urls.py、views.py；新檔 daily_jobs.py、domain/daily_schedule.py、migrations/0032。皆在 work-plan 範圍內；`jotform/sync.py` 僅 `sync_all` 加 `.order_by("id")`（使用者 2026-11-19 核准，見 escalation.md）。tests 另改 conftest（新增非 autouse fixture）、test_scheduler／test_jotform_intake_command 各一行 `skip_daily_jobs=True`（斷言未改）。無範圍外變更。

**合併提醒**：`views.py`、`urls.py` 與 B-014 同動，合併時需手動解衝突（B-011 在 views.py 檔尾新增 `_daily_jobs_card`、`daily_job_settings_update`，並在 `project_jotform_settings` 加 `daily_jobs` context 鍵；urls.py 一條 `scheduler/daily-jobs/`）。`docs/code_map/` 需合併者重跑 `python3 scripts/code_map.py update`；上線前須先停部署端舊 cron。

## 缺陷清單

無阻擋／高／中缺陷。

| ID | 嚴重度 | 說明 |
|---|---|---|
| D-1 | 低 | 測試與 testplan `BE-*` 案例 ID 缺乏可追溯標記（見 3）。 |
| D-2 | 低 | 逾時 30 分整的邊界沒有獨立案例（僅 31 分），規格若為「超過 30 分鐘」則 `>` 與 `>=` 差異未被鎖住。建議補一案：歷時恰 30:00 為 ok、30:01 為 failed。 |

## 未測試／限制

- 無 JOTFORM_API_KEY 時 test_jotform_sync_command 的 2 個既有失敗（P-1）本輪未重驗。
- 端對端啟動真實 `run_scheduler` 常駐程序、`docs/code_map` 檢查、integration 測試（需授權）：未執行。

## 結論

**通過**：全套 1423 passed 連跑兩次皆綠、覆蓋率 98.18%、lint／format／check／migration 皆乾淨；12 個關鍵行為破壞全部讓對應測試變紅；跨午夜補強案足以證明啟動日語意；變更範圍合規。僅 2 項低風險建議。
