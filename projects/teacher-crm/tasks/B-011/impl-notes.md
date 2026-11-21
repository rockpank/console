---
status: done
tests: 通過（第 5 輪全套 見下方「第 5 輪」實際輸出）
progress: T001–T205 完成（US5 止於 T205）
round: 5/6
date: 2026-11-18
---

# B-011 impl-notes（規格 043，第 1 輪）

工作目錄：`/home/user/web/console/worktrees/B-011/teacher-crm/`（分支 `t-B-011`），未 commit、未 push。

## 完成範圍

- Phase 1：T001、T002。Phase 2：T003～T056。Phase 3 US1：T057～T093（含 JOURNEY-01 組合驗收）。
- `specs/043-builtin-daily-scheduler/tasks.md` 已勾選 T001～T093，T094 起維持未勾。

## 變更檔案

產品碼：
- `src/crm/domain/daily_schedule.py`（新）：`Decision`、`decide`、`is_overdue`、`DailyStatus`、`status_of`，只匯入標準函式庫。
- `src/crm/domain/permissions.py`：檔尾追加 `can_view_platform_job_status`。
- `src/crm/daily_jobs.py`（新）：`Outcome`、`ClaimResult`、`get_run_time`、`claim_and_run`、`run_due_daily_jobs`、`recover_orphans`（骨架，未接進迴圈）、兩項工作本體 `run_line_notifications`、`run_finished_sessions`。
- `src/crm/scheduler.py`：追加 `DailyJob`、`registered_daily_jobs()`；`run_scheduler(..., daily_jobs=None)` 每 30 秒呼叫 `run_due_daily_jobs`。`Job`、`registered_jobs()`、`JobRun` 沒動。
- `src/crm/management/commands/run_scheduler.py`：傳入 `registered_daily_jobs()`；新增 `--skip-daily-jobs`（預設關，僅供診斷與測試）。
- `src/crm/models.py`：檔尾追加 `DailyJobSetting`、`DailyJobRun`。
- `src/crm/migrations/0032_daily_job_scheduler.py`（新）：只兩個 CreateModel，依賴 `0031_jotform_submissions`，無 RunPython，可回退。檔案是 docker 容器以 root 產生，已 chown 回主機使用者。

測試：
- 新檔：`tests/unit/test_daily_schedule.py`、`test_daily_job_permissions.py`、`test_daily_schedule_isolation.py`；`tests/db/daily_helpers.py`、`test_daily_job_models.py`、`test_daily_job_migration.py`、`test_daily_job_commands.py`、`test_daily_scheduler_run.py`。
- `tests/db/conftest.py`：只新增 `no_network` fixture（不 autouse）。
- T056：`tests/db/test_scheduler.py` 第 130 行、`tests/db/test_jotform_intake_command.py` 第 188 行，各只在 `call_command("run_scheduler", once=True, ...)` 加 `skip_daily_jobs=True`，斷言一字未改（`git diff` 只有這兩行）。

沒有動：`docs/code_map/`、`JobRun`、兩個既有管理指令檔、`.env`、`views.py`、`urls.py`、`forms.py`、樣板。

## 實際測試輸出

- 基線（改碼前，`pytest tests/unit tests/db`）：`1294 passed, 1 warning`（任務敘述的 1301 與實測差 7，以實測為準；基線跑到一半我才加入新檔，集合在啟動時已定）。
- 本輪結束：`pytest tests/unit tests/db --cov=src --cov-fail-under=95` → `1358 passed, 1 warning`；`Total coverage: 98.13%`（`Required test coverage of 95% reached`）。新增 64 個測試。
- `ruff check src tests` → All checks passed；`ruff format --check src tests` → 232 files already formatted。
- `manage.py check` → no issues；`makemigrations --check --dry-run` → No changes detected。
- 另一次不含覆蓋率的全套曾有 1 個失敗：`tests/db/test_jotform_return.py::test_entering_again_goes_to_the_same_order_without_asking_jotform_and_paid_is_final`，原因是付款連結簽章帶秒級時間戳，兩次產生剛好跨過 1 秒（`...:1xTgac:` 對 `...:1xTgab:`）；與本任務無關，單獨重跑 14 個全過，帶覆蓋率的全套也全過。屬既有的時間不穩定，建議另開 backlog。
- `make codemap-check` / `make codemap`：未執行（本機無 make，且 `docs/code_map/` 不在授權清單）。新增 `daily_jobs.py`、`daily_schedule.py`、兩個 model，地圖會是 STALE，請調度者在收尾時處理。`validate_artifacts.py`：未執行。

## 特徵案例（首跑即綠）的「暫時破壞再還原」證據

| 案例 | 暫時破壞 | 結果 |
|---|---|---|
| BE-SVC-09 | 在 `daily_schedule.py` 加 `import django` | 測試紅，還原後綠 |
| BE-SVC-12／07 | 把 `overdue=` 改成 `False and is_overdue(...)` | 兩個 status_of 測試紅，還原後綠 |
| BE-SVC-10 | 從 0032 拿掉 `chk_dailyjobrun_finished_when_done` | `DID NOT RAISE IntegrityError`，還原後綠 |
| BE-CMD-01／02 | 0032 加不可逆的 `RunPython` | CMD-02 紅（operations 不只 CreateModel），CMD-01 同時受影響；還原後綠（CMD-01 的紅燈輸出只看了第一行，沒逐行確認是 IrreversibleError） |
| BE-CMD-03 | `send_line_notifications.py` 暫時寫入 DailyJobRun（事後用 `git checkout --` 還原，該檔乾淨） | `DailyJobRun.count == 0` 失敗，還原後綠 |
| BE-TASK-06／02 | 移除同日判定並讓佔位改為 update_or_create | `started_at` 被覆寫，測試紅，還原後綠 |
| BE-TASK-19 | 課前通知預設時間改成 08:59 | 測試紅，還原後綠 |
| BE-TASK-10 | 工作內連 203.0.113.9 | 網路閘 AssertionError，測試紅，還原後綠 |

沒做破壞驗證（BE-TASK-03、08、09、26 未做 03/08/09）：BE-TASK-03、08、09 的行為在既有發送層，要證明會紅得暫時改 `line/notifications.py` 規則，預算內沒做；BE-TASK-26 屬後續輪次。

## T056 前置例外如實記錄（agent-protocol 第 8 節）

- 兩個入口測試在基線下不會紅：T051 接上每日工作後、尚未加旗標時，對這兩個檔跑 `pytest`，結果 `11 passed`（測試時刻為台北晚上 22 點多，兩項工作都判定可跑，但這兩個測試的斷言只看 Jotform 結果，所以沒受影響）。仍依調度者認可加旗標，原因是結果會隨執行時段而變。
- 逐檔：`test_scheduler.py`：原本紅 0 個，改第 130 行，加 `skip_daily_jobs=True`；`test_jotform_intake_command.py`：原本紅 0 個，改第 188 行，加 `skip_daily_jobs=True`；`test_compose_scheduler.py` 不變。

## 與規格／測試計畫的差異與假設

1. 批次做法：預算有限，TDD 以「一組 RED（全部測試先寫，確認 ImportError 紅）→ 一組 GREEN → REFACTOR」進行，不是 65 個切片逐一走；每組仍是先紅後綠，沒有為過測試改測試。REFACTOR 只做了 `daily_schedule.py` 去除多餘的 `_minute_of` 別名。
2. T3 通知測試學員必須是已付款（`paid=True`）：既有 `select_recipients` 規定課前 1 天只發給已付款者，testplan 的 FX-notify-world 沒寫這點。
3. BE-TASK-18：testplan 寫「23:00:50 啟動、工作推進 20 分鐘跨午夜」，但 23:00 啟動加 20 分鐘只到 23:20，且逾 23:00 當天不會啟動，無法在 30 分鐘逾時內真的跨午夜。我照 testplan 寫（推進 20 分鐘，之後繼續跑到 11-07 00:10），斷言（run_date、T-1 規則、隔天 23:00 新增列）都成立，但沒有真正跨午夜。要真正證明得讓工作耗時超過 60 分鐘，會與 US5 的 30 分鐘逾時規則衝突，建議 pm／qa 重新評估這案。
4. BE-TASK-07：`tick_seconds=120`（testplan 寫 30）以縮短測試時間；判定只到分鐘，結論不受影響。BE-TASK-19 用 30 秒。
5. `claim_and_run` 本輪只實作成功路徑（含同日唯一約束的 ALREADY_CLAIMED）；工作例外記 failed、30 分鐘逾時、`recover_orphans` 接進迴圈、`run_due_daily_jobs` 的逐項 try/except 都屬 US5，尚未實作（`recover_orphans` 只有骨架且未被呼叫，覆蓋率缺口在這裡）。目前工作丟例外會讓該列留在 running 並向上拋，US5 會補。
6. `get_run_time` 的設定讀取已完成（BE-TASK-19 用到），設定頁、表單、權限檢視（US2、US4）未動。
7. 無 `make` 的情況下，測試用 `docker compose run`；基線用 `COMPOSE_PROJECT_NAME=b-011`，我的 DB 測試用 `b-011-dev` 避免與基線搶測試資料庫。`b-011-dev` 的容器仍在（未 down）。

## 給調度者／後續輪次的事項

- 下一輪 US2：從 T094 起；需動 `forms.py`、`views.py`、`urls.py`、樣板（B-014 衝突點見 plan.md）。
- `docs/code_map/` 需由有權限者執行 `make codemap`。
- 上線前須先停掉部署端舊 cron（見 tasks-notes）。


---

# 第 2 輪（US2 後台設定每日發送時間，T094–T136）

`tasks.md` 已勾選 T094～T136，T137 起未勾。未 commit、未 push。未做 US3。

## 變更檔案

產品碼：
- `src/crm/forms.py`：檔尾追加 `DailyJobTimesForm`（`TimeField`、`HH:MM`、不得晚於 23:00，兩項整批全有或全無，`save(user)` 在 transaction 內只寫與目前有效值不同的項目並記操作人）；檔頭新增 `import datetime` 與兩行 import（`crm.daily_jobs.FORM_FIELDS/get_run_time`、`crm.scheduler.registered_daily_jobs`）。
- `src/crm/views.py`：`project_jotform_settings` 只加一個 context 鍵 `daily_jobs`；檔尾新增 `_daily_jobs_card`、`daily_job_settings_update`（`@platform_admin_required` + `@require_POST`，`project_id` 不可見／非數字回 404，成功與失敗皆 302 回專案設定頁）；import 區新增 `DailyJobTimesForm`、`to_domain_user`、`can_view_platform_job_status`、`daily_jobs.status_rows`。
- `src/crm/urls.py`：一條路由 `scheduler/daily-jobs/`（name `daily_job_settings_update`），插在 jotform connect 之前。
- `src/crm/daily_jobs.py`：新增 `FORM_FIELDS`、`DailyJobStatusRow`（含 `label`、`field_name` 屬性）、`now_utc()`、`status_rows(daily_jobs=None, now=None)`。
- `src/crm/templates/crm/project_jotform_settings.html`：檔尾 `{% endblock %}` 前新增「每日排程」卡片（既有行未動）；admin 有兩個 `<input type="time">` 與儲存鈕，manager 只有唯讀文字，staff 不顯示。
- 沒有動 `domain/permissions.py`、`domain/daily_schedule.py`、`tests/db/conftest.py`。

測試（新）：`tests/db/test_daily_job_settings_update.py`（21 個，BE-API-01～06、14～17）、`test_daily_scheduler_settings.py`（2，BE-TASK-11、12）、`test_daily_job_status_page.py`（2，BE-API-07、08）、`test_daily_job_journey_us2.py`（1，JOURNEY-02）。共 26 個。

## 紅燈證據（每個切片先紅後綠，沒有事後補測試）

| 切片 | 紅燈輸出 | 綠燈做法 |
|---|---|---|
| API-01 | `NoReverseMatch: 'daily_job_settings_update'`（第一次因 `Role` 匯入錯誤 ImportError，是測試自己的錯，修正後才是正確的紅） | 表單、檔尾 view（僅 login_required）、路由、卡片 |
| API-02、03 | 6 failed（空白／abc／25:00／9:7x、23:01、23:30：沒有錯誤訊息） | view 逐條 `messages.error`；表單 23:00 上限驗證 |
| API-04、05 | 3 failed：`302 == 403`（manager、staff、instructor） | `login_required` 換成 `platform_admin_required` |
| API-06 | 首跑即綠（`platform_admin_required` 內含 login_required） | 無 |
| API-15、16 | 4 failed：`MultiValueDictKeyError: 'project_id'`、405 未回 | 加 `require_POST`、project_id 解析與 404 |
| API-14、17 | 首跑即綠（01 的最小實作已含只寫變更項目） | 暫時把變更判斷改成 `if True or ...`：01、14、17 共 3 failed；還原後 21 passed |
| TASK-11、12 | 首跑即綠（第 1 輪的 `run_due_daily_jobs` 已每次重讀 `get_run_time`） | 暫時改成 `run_time = job.default_time`：2 failed（隔日起跑時間變 09:00）；還原後綠 |
| API-07 | `AttributeError: crm.daily_jobs has no attribute 'now_utc'` | `now_utc`、完整 `status_rows`、卡片列出最後執行與成功／失敗 |
| API-08 | `'每日排程' in html` 失敗（manager 沒有卡片） | `_daily_jobs_card` 改用 `can_view_platform_job_status` 控顯示、`can_manage_platform` 控可編輯 |
| JOURNEY-02（T136） | 組合驗收，首跑即綠 | 無（Gate 不改測） |

API-05 的 T107 預期「T104 後已綠」，實際是 04 與 05 同一輪才轉綠（兩者的 RED 在同一次執行），結果等價。

## 實際測試輸出

- 第一次全套（含覆蓋率）：`1 failed, 1383 passed, 1 warning in 399.66s`；`Total coverage: 98.18%`（`Required test coverage of 95% reached`）。失敗的是 `tests/db/test_jotform_sync_command.py::test_an_invalid_key_stops_automatic_retries_for_that_form_only`（與本任務無關，我沒動該檔也沒動 Jotform 程式）；單獨重跑該檔 `11 passed`。判定為既有的偶發（疑似時間戳／執行順序），補充：連續兩次全套都在同一處失敗、單獨重跑都過，加上第 2 輪（尚無本輪測試檔）也失敗過，所以它在全套中幾乎必紅，不像隨機偶發，比較像與前序測試的順序／狀態相依，與本輪新增檔案無關（第 2 輪沒有 catchup 檔也失敗）。沒有自行修，建議另開 backlog 與第 1 輪記的 test_jotform_return 一併處理。扣掉它與重跑後，通過數 1384（第 1 輪 1358，新增 26）。
- `ruff check src tests` → All checks passed（中途 3 個 import 排序問題已用 `ruff check --fix` 修正，只動到我的檔案）；`ruff format --check src tests` → 236 files already formatted。
- `manage.py check` → no issues；`makemigrations --check --dry-run` → No changes detected。
- 新增／變更模組覆蓋：`views.py` 99%；全專案 98.18%。
- `make codemap` / `validate_artifacts.py`：未執行（本機無 make，`docs/code_map/` 不在授權清單；新增路由、view、form、樣板卡片，地圖會 STALE，請合併者重跑）。
- 容器 `b-011-dev` 仍在（未 down）；worktree 內沒有 root 擁有的檔案（`ls -la` 檢查 0 個）。

## 與規格／測試計畫的差異與假設

1. BE-TASK-11：`tick_seconds=10`（testplan 寫 1），避免 6600 個迴圈輪；判定每 30 秒一次，「10:30:00–10:30:30 內開始」的斷言照 testplan 保留。BE-TASK-12 用 `tick_seconds=60`。兩案都只傳課前通知一項工作（`registered_daily_jobs()` 過濾），避免結束場次工作（預設 00:30，晚啟動補跑當天）在起跑時多出列。
2. 測試的 `<input type="time">` 用正規式 `<input[^>]*type="time"` 計數：`base.html` 的 CSS 含 `input[type="time"]` 字樣，直接數 `type="time"` 會多 1。
3. `forms.py` 在模組層匯入 `crm.scheduler`（為取預設時間）與 `crm.daily_jobs`；無循環匯入。`status_rows` 內延後匯入 `crm.scheduler`（因 scheduler 匯入 daily_jobs）。
4. 卡片目前只顯示：每項工作的設定時間、最後執行時間與成功／失敗／執行中；錯誤摘要、已過期、尚未到時間、今日已跳過標示屬 US4 的後續切片，`status_rows` 已算好 `status`（`DailyStatus`），樣板尚未使用。staff 因 `_daily_jobs_card` 回 None 已不顯示卡片（BE-API-09 之後應首跑即綠）。
5. 儲存失敗與成功皆 302 回設定頁（Post/Redirect/Get），錯誤訊息逐條以 `messages.error` 顯示並去重。


---

# 第 3 輪（US3 漏跑不補發，T137–T151 完成；T152–T155 blocked）

`tasks.md` 已勾選 T137～T151；T152 起未勾。未 commit、未 push。未做 US4。

## 為何停在 T151（blocked）

BE-API-12（T152～T154）要讓設定頁顯示「今日已跳過（逾 23:00）」，`status_rows` 已算好 `status.skipped`，但樣板 `project_jotform_settings.html` 目前沒有使用它，GREEN 必須改樣板（T153 原文也寫「樣板顯示…」）。任務授權清單寫「樣板本輪不需要動；若發現必須動就停下回報」，所以我只做了 RED 確認就停下，沒有改樣板。T155（JOURNEY-03）需要 BE-API-12 全綠，一併待辦。

RED 證據（T152）：新增測試後 `pytest tests/db/test_daily_job_status_page.py` → `1 failed, 2 passed`，失敗訊息 `assert 0 == 2 where 0 = ....count('今日已跳過（逾 23:00）')`（頁面確實渲染、原因正確）。測試已從檔案移除，讓本輪維持全綠；還原用的測試內容如下（附在 `test_daily_job_status_page.py` 檔尾，並把檔頭 `from crm.models import JobRun` 改成 `DailyJobRun, JobRun`）：

```python
@pytest.mark.django_db
def test_after_2300_without_a_row_the_page_says_skipped_not_failed_and_writes_nothing(monkeypatch):
    monkeypatch.setattr("crm.daily_jobs.now_utc", lambda: taipei(2026, 11, 6, 23, 30))
    project, _ = two_projects()
    client = Client()
    login_as(client, Role.ADMIN, project, "a1")
    response = client.get(reverse("project_jotform_settings", args=[project.id]))
    html = response.content.decode()
    card = html[html.index("每日排程") :]
    assert response.status_code == 200
    assert card.count("今日已跳過（逾 23:00）") == 2
    assert "失敗" not in card
    assert DailyJobRun.objects.count() == 0
```

最小 GREEN（需授權）：樣板每列在 `last_started_at` 區塊後加 `{% if row.status.skipped %}<span class="badge">今日已跳過（逾 23:00）</span>{% endif %}`（非失敗樣式，只加一行、不動既有行）。

## 變更檔案

- 新增 `tests/db/test_daily_scheduler_catchup.py`（8 個測試：BE-TASK-13、14、15×2 參數、16、17 三個情境）。
- `specs/043-builtin-daily-scheduler/tasks.md`：勾 T137～T151。
- 產品碼、`tests/db/conftest.py`、views／urls／forms／樣板：本輪**零變更**。

## 紅燈證據：本輪全是特徵案例（首跑即綠），以「暫時破壞再還原」證明會紅

首跑 `8 passed`（符合 tasks.md T138 的「預期由 decide RUN 分支已綠」）。逐項暫時改產品碼，跑 `test_daily_scheduler_catchup.py`，之後以備份還原並 `diff` 確認零差異：

| 案例 | 暫時破壞 | 結果 |
|---|---|---|
| BE-TASK-13 | `decide` 的 WAIT 條件改成「非恰好等於設定時間才 WAIT」 | `test_starting_after_the_set_time_still_runs_today_once` 紅 |
| BE-TASK-14、17 乙 | 移除 SKIP 分支（`if False`） | 14 與 17 乙共 2 個紅 |
| BE-TASK-15 | `decide` 忽略 ran_today，且 `claim_and_run` 改 `update_or_create`（只改其一仍綠：決策層與唯一約束雙重保護） | 兩個重啟參數案例（22:59、23:00:30）紅 |
| BE-TASK-16 | `job.run` 改傳 `run_date - 1 天`（模擬回溯補發） | 16 紅（另連帶 13、17 兩案紅） |
| BE-TASK-17 | `LAST_RUN_TIME` 改 23:01 | 17 乙紅 |
| BE-TASK-17 甲 | 提早一分鐘就判定 RUN | 17 甲（22:59 tick 不得執行）紅 |

## BE-TASK-18「跨午夜」（第 1 輪遺留）怎麼處理

沒有補做、沒有假裝：本輪範圍（US3）不含 BE-TASK-18，它的測試仍是第 1 輪的版本（推進 20 分鐘，其實沒跨午夜，只證明 run_date 取開始時刻、T-1 規則與隔天新增列），維持原註記。真要跨午夜得讓工作耗時超過 60 分鐘，與 US5 的 30 分鐘逾時規則衝突；留給 US5（T 逾時切片）一起處理，建議 pm／qa 改寫該案（例如 23:00 啟動並以逾時／孤兒回復情境驗收），或改用單元層證明 run_date 取開始時刻。本輪 BE-TASK-14 測試有真正跨午夜（23:30 起空轉到隔日 09:30），但那是「跳過後的迴圈跨日」，不是「工作執行中跨午夜」。

## 實際測試輸出

- 基線：第 2 輪結束 1384 通過（1383 + 重跑的 1 個）。
- 全套第 1 次（`pytest tests/unit tests/db --cov=src --cov-fail-under=95`）：`1 failed, 1391 passed, 1 warning in 400.60s`；`Total coverage: 98.18%`。失敗：`tests/db/test_jotform_sync_command.py::test_an_invalid_key_stops_automatic_retries_for_that_form_only`（`assert 'active' == NEEDS_ATTENTION`，行 131），與第 2 輪同一個測試。單獨重跑 `11 passed`。通過數 1391 + 該測試 = 1392 = 1384 + 8（新增 8 個）。
- 全套第 2 次：`1 failed, 1391 passed, 1 warning in 400.39s`；`Total coverage: 98.18%`；失敗的仍是同一個 `test_an_invalid_key_stops_automatic_retries_for_that_form_only`。
- 偶發失敗判斷：此測試第 2、3 輪各失敗一次、單獨重跑會過；斷言是 Jotform 表單狀態沒變成 needs_attention，與時鐘／每日排程無直接關聯，本輪新增的檔案不使用 monkeypatch 全域時鐘（`taipei_clock` 是傳入迴圈的物件）、不留狀態（每個測試皆 `django_db` 交易回滾）；但此測試在全套後段（約 85% 處）才跑，我無法排除與前面某個測試的狀態洩漏有關（例如 `crm.daily_jobs.now_utc` 的 monkeypatch 都用 pytest monkeypatch，會自動還原）。補充：連續兩次全套都在同一處失敗、單獨重跑都過，加上第 2 輪（尚無本輪測試檔）也失敗過，所以它在全套中幾乎必紅，不像隨機偶發，比較像與前序測試的順序／狀態相依，與本輪新增檔案無關（第 2 輪沒有 catchup 檔也失敗）。沒有自行修，建議另開 backlog 調查（先用 `pytest -p randomly` 或 bisect 前序測試）。
- `ruff check src tests` → All checks passed（中途 B007 未使用迴圈變數已修）；`ruff format --check src tests` → 237 files already formatted。
- `manage.py check` → no issues；`makemigrations --check --dry-run` → No changes detected。
- `make codemap`／`validate_artifacts.py`：未執行（同前兩輪理由）；本輪未改產品碼，地圖狀態與第 2 輪相同。
- 容器 `b-011-dev` 仍在（未 down）；執行時使用 `-e` 旗標，未產生 root 檔案。


## 續做（調度者裁示後）：T152～T155 完成

- 調度者放行改樣板：`project_jotform_settings.html` 的「每日排程」卡片每列 `last_started_at` 之後只加一個 `{% if row.status.skipped %}　<span class="badge">今日已跳過（逾 23:00）</span>{% endif %}`，既有行未動。
- T152 RED：測試補回 `tests/db/test_daily_job_status_page.py`，`1 failed, 2 passed`，`assert 0 == 2`。T153 GREEN：加上述一行後 `status_page` + `journey_us2` 共 `4 passed`。T154：無需整理。
- T155（JOURNEY-03）：新增 `tests/db/test_daily_job_journey_us3.py`（1 個）：停機 3 日 → 第 4 日 14:00 恢復 → 22:59、23:00:30 重啟（列的 started_at 不變）→ 第 5 日 23:30 啟動 → admin 看頁面；斷言第 4 日有列、第 5 日 0 列、通知只有 1 則 T-1、頁面「今日已跳過（逾 23:00）」兩項各一。首跑即綠（Gate 不改測）。
- tasks.md 已勾 T152～T155；US4 未開始。
- 品質關卡：ruff check All checks passed；format 238 files already formatted；check no issues；makemigrations No changes detected。
- 全套第 3 次（含覆蓋率）：`1 failed, 1393 passed, 1 warning in 403.16s`；`Total coverage` 見 98%（高於 95%）。失敗仍是 invalid key 那個測試。通過數 1393 比上一輪 1384 多 9（新增 catchup 8、status_page 1、journey_us3 1，扣除計入方式差異以 pytest 實際為準）。

## 偶發失敗（invalid key）二分結果與根因

目標：`tests/db/test_jotform_sync_command.py::test_an_invalid_key_stops_automatic_retries_for_that_form_only`，斷言 `form_a.status == NEEDS_ATTENTION` 得到 `active`。

二分（每次整個 `tests/db`（或加 unit）、無覆蓋率、固定在同一環境）：

| 排除 | 結果 |
|---|---|
| 無（全套，含覆蓋率）×3 | 3 次皆失敗（1 failed） |
| 所有 `test_daily_*`（db 與 unit） | 1294 passed，不失敗 |
| 只排除 scheduler_run／settings／catchup（重迴圈三檔） | 仍失敗 |
| 只排除 test_daily_job_migration（唯一用 transaction=True 的新檔） | 仍失敗 |
| 排除 settings_update／status_page／commands／models／journeys（保留 scheduler 三檔與 migration） | 全過 |
| 只排除 settings_update | 仍失敗 |
| 只排除 commands + models | 仍失敗 |
| 排除 status_page + journey_us2 + journey_us3 | 全過 |
| **只排除 `test_daily_job_status_page.py`** | **全過（859 passed）** |

另：新增檔各自或全部與該測試放同一次 pytest（新檔在前）都過（110 passed），所以不是 fixture／全域狀態洩漏（`now_utc` 用 monkeypatch 自動還原；`no_network` 只在用到的測試內；沒有模組層級狀態被改）。

根因（部分證實、部分推論）：
1. 證實：觸發條件是 `test_daily_job_status_page.py` 在全套中存在。該檔的 `seed()` 會建立 `JotformForm`、`JobRun`（交易回滾）。
2. 失敗的直接機制（讀碼）：`crm/jotform/sync.py::sync_all` 的 `JotformForm.objects.filter(status=ACTIVE).select_related("project")` **沒有 ORDER BY**；測試假設先建的 form_a 先被處理，第一次 `replace_options` 才會吃到 `JotformKeyInvalid`。若 PostgreSQL 回傳順序對調（heap 空間重用或 autovacuum／autoanalyze 改變計畫），失敗會落在 form_b，form_a 保持 active，於是斷言失敗。多寫入／回滾一組 JotformForm 的測試足以改變實體順序，所以任何新增這類資料的測試檔都可能讓它變紅（B-026 與 master 沒有這個檔，所以沒遇到）。我沒有直接證明順序確實對調（沒有印出處理順序），這是依二分結果與碼的推論。
3. 根因在範圍外：既有產品碼 `sync.py`（查詢無排序）與既有測試 `test_jotform_sync_command.py`（隱含依賴順序）。我沒有改，也沒有改 status_page 的 seed 去繞過（那只是掩蓋）。
建議（需調度者決定）：在 `sync_all` 加 `.order_by("id")`（一行，產品碼，不改行為），或把該測試改成與處理順序無關；做完後全套應 0 failed。另可用 `docker compose run ... pytest tests/db/test_jotform_sync_command.py` 前先插入並回滾一些 JotformForm 來重現，我未做。

因此本輪「全套 0 failed」未達成，原因如上，非本任務碼的缺陷。


# 第 4 輪（US4 設定頁顯示排程狀態，T156–T183）

`tasks.md` 已勾 T156～T183，T184 起未勾。未 commit、未 push。未做 US5。

## 變更檔案

- `src/crm/templates/crm/project_jotform_settings.html`（僅「每日排程」卡片內）：失敗徽章後加錯誤摘要 `{% if row.error %}<span class="muted">{{ row.error }}</span>{% endif %}`（Django 自動跳脫，無 `|safe`）；每列尾端依序加 `尚未到時間`（not_yet）、`今日已跳過（逾 23:00）`（skipped，原有）、`已過期`（overdue，`badge bad`）。主要狀態在前、警示在後。
- 測試：`tests/db/test_daily_job_status_page.py` 追加 11 個（BE-API-09、10、11×2、13、19、20、21甲、21乙、22、23）；新增 `tests/db/test_daily_job_journey_us4.py`（1 個，JOURNEY-04）。
- 產品碼 `daily_jobs.py`、`domain/*`、`views.py`、`tests/db/conftest.py`：本輪零變更（`status_rows` 已算好 status 旗標與 error，`_daily_jobs_card` 已依權限控制顯示）。

## 紅燈證據

測試先於實作寫好，第一次執行 `test_daily_job_status_page.py`：`6 failed, 8 passed`。
- 紅（原因正確，樣板缺顯示）：API-10（無「已過期」）、API-11 兩案（錯誤摘要未顯示）、API-20（失敗＋已過期並存）、API-21 乙（只有跳過、缺已過期）、API-22（缺「尚未到時間」）。
- 首跑即綠（特徵案例）：API-09、13、19、21 甲、23。實作後 `14 passed`。

特徵案例「暫時破壞再還原」（每項各自只有該測試紅，還原後以 diff 確認三個檔案與備份相同，`14 passed`）：

| 案例 | 暫時破壞 | 結果 |
|---|---|---|
| API-09 | `_daily_jobs_card` 的權限判斷改成 `False`（任何人都顯示） | staff 測試紅 |
| API-13 | `_project_or_404` 改成不經 `visible_to` | 跨專案測試紅 |
| API-19 | `status_rows` 把 `last_started_at` 轉成 UTC naive | 台北時間測試紅 |
| API-21 甲 | 樣板讓 skipped 也顯示「已過期」 | 23:00／23:30 測試紅 |
| API-23 | `status_rows` 的 error 改成 `str(details)` | 兩個 failed 測試紅（含跳脫案的「details 不得出現」）；API-23 本案本身是 ok 列，不顯示 error，故該案由失敗列案間接證明，沒有單獨變紅 |

T183（JOURNEY-04）：同一資料庫 08:00（兩項尚未到時間）→ 09:30（課前通知成功、無已過期）→ 10:05（結束場次設 09:00，已過期）→ 23:30（結束場次已跳過），manager 唯讀、staff 無卡片，開頁不建列；首跑即綠（Gate 不改測）。

## 實際測試輸出

- `pytest tests/unit tests/db --cov=src --cov-fail-under=95`：`1406 passed, 1 warning in 411.35s`；`Total coverage: 98.15%`（`Required test coverage of 95% reached`）；`views.py` 99%。1406 = 1393 + 13（新增 12 個本輪測試 + 先前每輪算法的 1 個原本失敗的 invalid key 測試這次通過）。
- 失敗清單：**無**。上一輪固定失敗的 `test_an_invalid_key_stops_automatic_retries_for_that_form_only` 這次全套通過。這不代表根因消失：`sync_all` 查詢無 ORDER BY 的問題仍在（回傳順序依賴 PostgreSQL 實體順序），本輪新增的 DB 寫入量剛好讓順序又恢復，仍屬脆弱，建議照上一輪建議在 `sync_all` 加 `.order_by("id")`（範圍外）。
- `ruff check src tests` → All checks passed；`ruff format --check src tests` → 239 files already formatted；`manage.py check` → no issues；`makemigrations --check --dry-run` → No changes detected。
- worktree 內 root 擁有的檔案：0 個。容器 `b-011-dev` 未 down。
- `make codemap`、`validate_artifacts.py`：未執行（理由同前）；本輪只改樣板與測試，地圖影響僅樣板內容。

## 假設與差異

1. 批次紅燈：本輪 11 個切片的測試一次寫完、一次跑出紅燈，再一次 GREEN（樣板一處改動），不是逐切片分次；每個測試仍都在實作前存在並被觀察過結果。REFACTOR 無需整理（樣板單行已很長，但沿用既有每列一行的寫法，未拆）。
2. 錯誤摘要只在「最近一列為 failed」時顯示（含非今日的最近失敗列），與既有「最後執行」徽章同一邏輯；不輸出 details（`DailyJobStatusRow` 本來就沒有該欄位）。
3. 「尚未到時間」「已過期」「今日已跳過」皆為卡片每列行尾 badge；格式字串固定在樣板，測試以文字斷言。
4. API-10 恰 10:00 補了一個斷言（不顯示已過期），對應 api-plan 邊界語意；testplan 本案原只列 09:59 與 10:05。


## 第 5 輪（US5：單一工作失敗互不影響，T184～T205）

### 變更檔案
- `src/crm/daily_jobs.py`：`claim_and_run` 補完——`job.run` 例外記 `failed`（`error` 為訊息截 200 字，空訊息用例外類別名；不含堆疊，堆疊只進日誌）、回 `RAN_FAILED`；結束時刻減開始時刻 > `JOB_TIMEOUT`（30 分鐘，常數）記 `failed`／「執行逾時」（事後判定、不回滾、不強制中止；剛好 30 分鐘為 ok）；結束時刻只取一次。`run_due_daily_jobs` 每項各自 `try/except Exception`（佔位時的資料庫錯誤等也不影響其他工作）。
- `src/crm/scheduler.py`：新增 `_recover`；`run_scheduler` 在「剛取得鎖」且有 `daily_jobs` 時呼叫 `recover_orphans`（running 殘留列改 failed／執行中斷；未持鎖不動別人的列；復原本身出錯只記日誌）。
- 測試（新）：`tests/db/test_daily_scheduler_failures.py`（BE-TASK-20、21、22、23、24、25 與 BE-TASK-18 補強案，共 15 案）、`tests/db/test_daily_job_journey_us5.py`（JOURNEY-05）。
- `specs/043-builtin-daily-scheduler/tasks.md`：T184～T205 勾選（沿用既有 `[X]` 寫法）。
- 沒有動：views／urls／forms／樣板、`docs/code_map/`、`JobRun`、兩個既有管理指令、jotform 模組、`.env`、`line/notifications.py`（暫時破壞後已還原，`git diff` 為空）、`tests/db/conftest.py`（本輪未改）。

### 紅燈證據（先紅後綠）
先只寫測試檔、未改產品碼，跑出 `7 failed, 8 passed`：
- 紅：BE-TASK-20（工作例外使迴圈中止，RuntimeError 外洩）、20 補案（佔位時 DataError 外洩）、BE-TASK-21（外洩）、21 補案（類別名）、BE-TASK-22 兩案（running 列仍是 running）、BE-TASK-24 的 31 分鐘案（status 仍 ok）。
- 首跑即綠（特徵案例）：BE-TASK-23 兩案、24 的 29／30 分鐘案、25 兩案、22 未持鎖案、18 補強案，改以下表暫時破壞證明會紅。
- 實作後 `15 passed`。第一次實作時 18 補強案紅（`claim_and_run` 多呼叫一次時鐘），改成結束時刻只取一次後轉綠。

### 暫時破壞再還原（每項只跑該測試，還原後 `git diff` 確認；`line/notifications.py` 無差異）
| 案例 | 暫時破壞 | 結果 |
|---|---|---|
| BE-TASK-03（第 1 輪漏做） | `_send` 的 `elif message.status != PENDING: return` 改 `pass` | 紅（重複發送） |
| BE-TASK-08（第 1 輪漏做） | 刪除 `_deliver` 的 `if not account.active` 略過 | 紅 |
| BE-TASK-09（第 1 輪漏做） | `except LineApiError` 改 `except RuntimeError` | 紅（工作變 failed） |
| BE-TASK-18 補強 | `run_date` 改取結束時刻 | 紅 |
| BE-TASK-23 | 唯一衝突時不回 ALREADY_CLAIMED 而取既有列繼續執行（等同佔位無效；沒有真的移除資料庫約束，避免動 migration） | 2 案皆紅 |
| BE-TASK-24 邊界 | `>` 改 `>=` | 30 分鐘案紅（1 failed, 2 passed） |
| BE-TASK-21 | 拿掉 200 字截斷 | 紅 |
| BE-TASK-22 未持鎖 | `if holding and daily_jobs` 改 `if daily_jobs` | 紅 |
| BE-TASK-25 | 每日工作判定後 `sleep_fn(1000)`（模擬每日工作拖延 Jotform） | 有每日工作案紅、無每日工作案綠。先試 `sleep_fn(5)` 兩案皆綠，鑑別力不足，改用 1000 |
| JOURNEY-05 | 孤兒復原改 `if False` | 紅 |

BE-TASK-03、08、09 的測試本體在 `test_daily_scheduler_run.py`（第 1 輪已寫），本輪只補破壞證明；這三項的破壞改的是 `line/notifications.py`，依授權只做暫時破壞、已還原。

### BE-TASK-18「跨午夜」的處理（如實）
- 原案（`test_run_date_is_the_claim_day_even_when_the_job_runs_past_midnight`）維持不動：23:00 啟動、`run` 推進 20 分鐘，實際只到 23:20，**沒有跨午夜**。它驗證：run_date 取啟動日、T-1 規則是 11-06、隔天 23:00 會新增 11-07 的列。沒驗證：工作執行中真的跨過 00:00。
- 真正跨午夜在經迴圈的路徑不可能：23:00 設定的最晚啟動是 23:00:59，30 分鐘內最多到 23:30，要跨午夜須耗時 > 60 分鐘，會被判逾時。
- 本輪補強案（`test_a_claim_made_before_midnight_keeps_the_start_day_when_the_job_ends_after_midnight`）：直接呼叫 `claim_and_run`（它不看 23:00 截止，那是 `decide` 的事），注入時鐘 23:59:30 啟動、00:05 結束（6.5 分鐘，不逾時）。斷言 run_date 與傳給工作的 today 為 11-06、finished_at 的台北日期是 11-07、狀態 ok。沒驗證：經迴圈與 `decide` 的整條路徑下的跨午夜（理論上不會發生）。
- 建議 QA 把 BE-TASK-18 改寫成上述注入時鐘版本，並把原案的「跨午夜」字樣改為「長耗時」。

### 假設與偏差
1. `recover_orphans` 只在「剛取得鎖」時執行一次，且 `daily_jobs` 為空時不執行（不動未啟用每日工作的既有行為）。同一程序自己建立的 running 列不會被誤改。
2. 例外與逾時同時發生時，以例外為準。
3. BE-TASK-23 的雙執行緒案每回合用不同日期（2026-12-01 起連續 20 日），免清資料；斷言「最多一次」且恰一個 RAN_OK。
4. BE-TASK-25 的 `is_stale` 用 `JobRun.last_finished_at` 與時鐘比較（兩情況皆 False）。
5. T202～T204（BE-TASK-26 回歸）：沒有新增測試檔；既有測試斷言一字未改，全套通過即為回歸結果。`make codemap`／`codemap-check` 依規定不手動執行，由合併者重跑（`docs/code_map/` 不在授權內）。
6. JOURNEY-05 有一個測試檔 `test_daily_job_journey_us5.py`（第 1 日例外、第 2 日殘留 running、第 3 日 31 分鐘逾時、第 4 日正常；結束場次每日 ok、Jotform last_ok=True），組合驗收首跑即綠。

### 實際測試輸出
- `ruff check src tests`：All checks passed；`ruff format --check src tests`：240 files already formatted（新增旅程檔後再 format 一次，無變更）。
- `manage.py check`：no issues；`makemigrations --check --dry-run`：No changes detected。
- `pytest tests/unit tests/db --cov=src --cov-fail-under=95`：**1422 passed**（上一輪 1406，+15 失敗隔離案 +1 旅程）、0 failed；總覆蓋率 98.18%；`daily_jobs.py` 99%（僅 56->60 分支）、`daily_schedule.py` 100%、`scheduler.py` 98%（未覆蓋 74-75 行，即 `_recover` 復原本身出錯的日誌分支，屬防禦性程式碼）。
- 既有偶發失敗（jotform 順序相依那一案）本輪全套未出現。
- 第一次全套（未加旅程）為 1421 passed。

## 第 6 輪（使用者核准的範圍擴大：sync_all 處理順序確定化）

- 產品碼：`src/crm/jotform/sync.py` 的 `sync_all` 查詢加 `.order_by("id")`（ruff format 風格拆成多行，行為不變，只讓順序確定）。
- 新回歸測試：`tests/db/test_jotform_sync_all_order.py`（未改 `test_jotform_sync_command.py`）。建立兩個啟用中、都需寫入的表單 A、B，對 A 做 UPDATE 使 PostgreSQL 實體順序變成 B、A，呼叫 `sync_all`，用既有 `fake_jotform`（真實 FakeJotformClient，不 mock 自家函式）記錄 `replace_options` 的 form_id，斷言 `[A, B]`。
- 紅燈（先紅後綠）：沒有 order_by 時第一次執行即失敗（處理順序 B、A）；暫時移除 order_by 連跑 50 次，**50/50 皆紅**，穩定；補回後 20/20 綠（`--count` 不可用，改以同一容器內迴圈）。已確認 order_by 已還原。
- 品質關卡：`ruff check src tests` 通過、`ruff format --check src tests` 242 檔已格式化；`ruff check .`／`format --check .` 另有 `.claude/skills/_shared/tests/` 等既有、與本任務無關的項目（6 檔待格式化、1 項 lint），未動。`manage.py check` 無問題；`makemigrations --check --dry-run` 無變更。
- 全套 `pytest tests/unit tests/db` 兩次：皆 **1423 passed, 0 failed**（1422 + 新增 1），兩次都沒有再出現順序相依的 invalid key 失敗。覆蓋率數字：未執行（-q 輸出未顯示 TOTAL 行，無法確認 ≥95%，請調度者以專案設定核對）。
