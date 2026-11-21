---
status: done
resume_at: 開發中
stage: /tasks + /analyze（pm）
date: 2026-11-18
---

# B-011 tasks-notes（規格 043）

## 產出

- `specs/043-builtin-daily-scheduler/tasks.md`：T001～T205；65 切片鏈（RED／GREEN／REFACTOR）＋5 Gate；T003 為 makemigrations 工單（0032，只兩個 CreateModel，依賴 0031，可回退）；T056 為既有指令入口測試加 `skip_daily_jobs=True`。
- `specs/043-builtin-daily-scheduler/analyze-report.md`：CRITICAL 0、HIGH 0；FR 25/25、NFR 2/2、SC 5/5、API 14/14、INT 19/19、案例 70/70、Journey 5/5。
- spec.md 補註兩處（2026-11-18）：FR-015「嚴格晚於、分鐘精度」；邊界情況「已跳過與已過期可並存」。不改既有數字與裁示。

## 既有測試盤點（行號為 2026-11-18）

- `tests/db/test_scheduler.py`：直接呼叫函式第 44、61、81、84、105 行不變；指令入口只有第 130 行 → 加旗標。
- `tests/db/test_jotform_intake_command.py` 第 188 行 → 加旗標。
- `tests/unit/test_compose_scheduler.py` 不變。

## 給工程師的注意

- 檔案範圍護欄在 tasks.md「任務契約」；範圍外要改就停下回報。
- 預期首跑即綠的案例（BE-SVC-10、BE-CMD-01/02/03、BE-TASK-26 等）要以暫時破壞行為證明測試會紅。
- JOURNEY-02 的組成切片含 BE-API-07、08，已提前到 Phase 4（T130～T135）。
- FakeClock 起點一律台北 aware；LINE 只用 fake 模式。

## 待辦／交接

- `validate_artifacts.py all` 未執行（本角色無 Bash）：請調度者或工程師在 worktree 跑 `python .agents/skills/_shared/validate_artifacts.py all --package 043-builtin-daily-scheduler`，若有 FAIL 回報 pm 修。
- architect 擇機修 integration-plan.md 的 INT-JOB-SCHED-01、05（非阻擋）。
- B-014 衝突（views.py、urls.py）：合併順序交 merge-manager。
- 上線前須先停掉部署端舊 cron。
