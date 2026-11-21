---
status: done
resume_at: /testplan
validated: 未執行（architect 無 shell；請調度者代跑 `cd worktrees/B-011/teacher-crm && python3 .agents/skills/_shared/validate_artifacts.py all --package 043-builtin-daily-scheduler`，已依驗證器原始碼逐條自查格式）
---

# B-011 system-analyze 筆記

## 產物（worktree 內 `specs/043-builtin-daily-scheduler/`）

- `plan.md`（含與 B-014 的衝突點表；ui-plan 標「否」並寫明沿用 `project_jotform_settings.html`）
- `system-analyze/technical-research.md`（D-01～D-08）
- `system-analyze/data-plan.md`、`system-analyze/models.md`
- `system-analyze/api-plan.md`（API-SCHED-01～14，HTML 端點契約）
- `system-analyze/integration-plan.md`（INT-JOB-NOTIFY-01～11、FINISH-01～03、SCHED-01～05）
- 未產：ui-plan（依指示跳過）

## 關鍵決策

1. 新增 `DailyJobSetting`（設定，無列＝預設 09:00／00:30）與 `DailyJobRun`（`job_name+run_date` 唯一）；`JobRun` 完全不動。
2. migration `0032_daily_job_scheduler`：只 CreateModel x2，無資料遷移，可回退（刪表）。
3. 判定為 domain 純函式 `decide`；先佔位（唯一約束）再執行；諮詢鎖＋唯一約束兩層擋重複；孤兒 running 改 failed；失敗當天不重試；跳過不留列。
4. 每日工作直接呼叫 `run_all(today)`／`finish_due_sessions(today)`，不經 `call_command`。
5. 權限：儲存＝`platform_admin_required`；檢視卡片＝admin、manager（新 domain 純函式）；落點＝既有 Jotform 設定頁。

## 待決（需使用者或 pm 決定，規劃階段已用預設值繼續）

1. 設定卡片放在「Jotform 報名表」專案頁（預設，沿用既有排程狀態區塊）是否可接受？此頁是專案層級、設定卻是全平台；staff 進得了頁面但不顯示卡片（US4 情境 4 的解讀）。
2. 23:00 截止以「分鐘精度」解讀（設定 23:00 時 23:00:59 前仍會執行），否則 23:00 設定不可用。
3. FR-018 逾時為「事後判定」不強制終止（同步呼叫無法安全中止）；要硬中止需改子程序，成本較高。
4. FR-011 只保留最後一次修改的操作人與時間；要完整變更歷史需多一張追加表。
5. 設定頁預設只顯示彙總與狀態，不列「尚未點名的場次」（細節存於 `DailyJobRun.details` 只含 id，避免跨專案揭露）；要在頁面列出需另做依專案可見性的過濾。
6. 失敗當天依 FR-015 字面同時顯示「失敗」與「過期」；若只想顯示失敗需調整規格。

## 風險／須知

- 每日工作與 Jotform 工作同一迴圈，長時間執行會延後 Jotform 同步（不開執行緒）。
- 與 B-014 的衝突點：`views.py`（import 區與 521–526 行附近）、`urls.py` 相鄰一行、`project_jotform_settings.html`（B-014 範圍待確認）。
- 待確認：compose 的 scheduler 服務（未讀）；fake 模式下 `run_all` 不連外網（testplan 確認）；`urls.py` 設定頁實際路徑。
## testplan 回饋修訂（2026-11-18）

做了哪些改動（皆在 worktree `specs/043-builtin-daily-scheduler/`，契約 ID 未變、已定案決策 D-01～D-08 未動）：

1. `integration-plan.md`：INT-JOB-SCHED-01、05 改為真實 `registered_jobs()` + `fake_jotform`，只看 `JobRun`／`DailyJobRun` 列；更新 boundary_double 與「假設」段落。INT-JOB-SCHED-03 改指向公開入口 `claim_and_run`。
2. `plan.md` 新增「公開介面定案」：`daily_jobs.claim_and_run(job, now_fn) -> ClaimResult(outcome, run_date, row_id)`（唯一衝突回 `ALREADY_CLAIMED`、job 例外記 failed 不外洩）、`run_due_daily_jobs`、`recover_orphans`、`get_run_time`、`status_rows`；`domain.is_overdue(now_local, run_time, succeeded_today)`、`status_of(now_local, run_time, today_status) -> DailyStatus`；設定頁時鐘注入點 `crm.daily_jobs.now_utc()`（測試 monkeypatch）。
3. `plan.md` 新增「邊界語意定案」：(a) 恰 +60 分鐘整點不過期（嚴格晚於、分鐘精度，10:01:00 起過期）；(b) 跳過與過期並存（主要狀態在前、過期警示在後）；(c) 失敗同帶過期，維持 FR-015 字面。
4. `plan.md` 風險段：既有測試不依賴實際時間——函式層 `daily_jobs` 預設為空；指令入口新增 `--skip-daily-jobs`，經指令且不需每日工作的既有測試只加此參數。
5. `api-plan.md` API-SCHED-10：補 10:00:00 不過期、並存案例與時鐘注入點。

需要 pm 補 spec：無強制。建議性：FR-015 加註「嚴格晚於、分鐘精度」；邊界情況加一句「已跳過與已過期可並存」。

需要 qa 同步 testplan（architect 不改 testplan）：BE-SVC-06 加 10:00:00／10:00:59 否、10:01:00 是；BE-TASK-23 受測部位改為 `claim_and_run`；BE-CMD-04 與 BE-TASK-26 註記「既有指令入口測試只加 `--skip-daily-jobs`，斷言不改」（原文寫「不改動」）。

待確認：`tests/db/test_scheduler.py`（8 處）、`test_jotform_intake_command.py`（1 處）哪些走指令入口，tasks 階段盤點；驗證器「未執行」（architect 無 shell），請調度者代跑 `cd worktrees/B-011/teacher-crm && python3 .agents/skills/_shared/validate_artifacts.py all --package 043-builtin-daily-scheduler`。

- 憲法專案隔離（MUST 4）：新表為平台全域、不含專案資料，已在 data-plan 說明；測試需含 A 專案 manager 看不到 B 專案頁（API-SCHED-13）。
