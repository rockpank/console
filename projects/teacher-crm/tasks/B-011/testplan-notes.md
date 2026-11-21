---
status: done
resume_at: /tasks
validated: 已執行 `python3 .agents/skills/_shared/validate_artifacts.py all --package 043-builtin-daily-scheduler`，9 個產物全部 OK（含 testplan.md，第一次即通過、無警告）
---

# B-011 testplan 筆記

- 產物：worktree 內 `specs/043-builtin-daily-scheduler/testplan.md`。68 個案例：BE-SVC 11、BE-CMD 4、BE-TASK 26、BE-API 22（編號 18 空缺）、JOURNEY 5；無 FE-E2E（專案無 tests/e2e）。
- 「需求覆蓋對照」表涵蓋 FR-001～025、NFR-001～002、SC-001～005、API-SCHED-01～14、INT-JOB-* 共 19 個；產生時腳本自檢每個 ID 都有對應案例。FR-020（raw SQL 註解）無自動化案例，以 code review 處理（已寫入「不納入」）。
- 判斷 (a)：計數用假 run 不採用。理由：替換了 Jotform 工作本體（自家業務行為），且「呼叫次數」不是允許的觀測通道。改為真實 `registered_jobs()` + `fake_jotform`，以 JobRun／DailyJobRun 資料列判定（BE-TASK-20、25）。保留三案「測試自帶 DailyJob」（BE-TASK-18、23、24），其 run 呼叫真實 run_all 或只寫標記列，不替換自家函式。
- 判斷 (b)：已讀程式碼確認，`LineConfig.mode=fake` 時 `build_client` 回 `FakeLineClient`，`run_all`／`finish_due_sessions` 路徑無任何 HTTP 匯入；唯一外連路徑為 mode=line 的 `HttpLineClient`。BE-TASK-10 以網路閘動態證明。
- 發現：`FakeLineClient.failures` 放 `LineApiError` 會被既有流程記成失敗訊息、工作仍 ok；要讓 `run_all` 丟例外必須放非 LineApiError（如 RuntimeError）。INT-JOB-NOTIFY-08 的「丟錯 fake」須據此實作。
- 發現：`FakeClock()` 預設為 UTC 09:00 = 台北 17:00，本任務每個案例都必須明確傳台北時區起點。

## 待調度者／上游處理

1. architect：`integration-plan.md` INT-JOB-SCHED-01、05 的 `boundary_double` 與假設段落應改為「真實工作 + fake_jotform」（testplan 不改上游文件）。
2. architect／pm（tasks 前）：INT-JOB-SCHED-03 要「繞過諮詢鎖」需公開的「佔位並執行」服務函式，函式名稱與簽章未定（BE-TASK-23 的受測部位）；請在 tasks 指定。同理 `is_overdue`／`status_of` 簽章、設定頁取得「現在」的時鐘注入點。
3. pm 澄清（不阻擋）：恰 10:00:00 是否過期；設定 22:30、現在 23:45 時「已跳過」與「已過期」是否並存；失敗當天同時顯示過期（待決 6，已依字面固定在 BE-API-20）。
4. 風險：加入每日工作後，不凍結時鐘就跑 `run_scheduler --once` 的既有測試會隨實際時間新增 DailyJobRun；BE-TASK-26 要求其斷言不得依賴實際時間。

工具呼叫：18／30

## 同步修訂（2026-11-18，依 architect 補的上游設計）

---
status: done
resume_at: /tasks
validated: 已重跑 `python3 .agents/skills/_shared/validate_artifacts.py all --package 043-builtin-daily-scheduler`（結果見本任務回報；以最後一次實際輸出為準）
---

- 案例總數 68 → 70：新增 BE-SVC-12（status_of 跳過與過期並存、23:00 寬限跨午夜只跳過）、BE-CMD-05（--skip-daily-jobs 旗標與函式層 daily_jobs 預設為空）。BE-SVC 12、BE-CMD 5、BE-TASK 26、BE-API 22、JOURNEY 5；「建議 TDD 實作順序」已重編為 1～70，標題數與清單一致。
- BE-SVC-06：加 10:00:00／10:00:59 否、10:01:00 是。BE-API-21 擴為甲（23:00@23:30 只跳過）、乙（22:30@23:45 並存，跳過在前、過期在後）。
- BE-TASK-23：受測部位改 `claim_and_run`，連續呼叫（RAN_OK 後 ALREADY_CLAIMED）加雙執行緒 Barrier 20 回合。
- BE-CMD-04／BE-TASK-26：「不改動」改為「指令入口測試只加 --skip-daily-jobs、斷言不改；函式層測試完全不變」。
- 覆蓋對照：FR-015、FR-016、SC-005、NFR-002、API-SCHED-10 補新案例；INT-JOB-SCHED-03 仍對 BE-TASK-23。「仍待澄清」已移除三項已定案、改列 /tasks 盤點待辦（test_scheduler.py 8 處、test_jotform_intake_command.py 1 處）。
- 仍待：pm 可於 FR-015 補「嚴格晚於、分鐘精度」（非阻擋）。
