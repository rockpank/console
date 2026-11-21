---
resume_at: 開發中
resolved: true
---

# 升級：B-014 —— 同一 worktree 出現第二個寫入者

- 條件：協議第 4 節第 5 條（工作樹中出現與本次派工無關的變更，無法靠排序解決）。
- 原因：本次 resume 的工程師（開工後約 22:01–22:04）發現 `worktrees/B-014/teacher-crm/` 內出現不是它寫的變更：`src/crm/throttle.py`、`tests/db/test_throttle_cache.py`、`Makefile`（createcachetable）、`src/config/settings.py`（CACHES）、`src/crm/views.py`（jotform_return／jotform_webhook 已掛 throttle）。更早（21:57–21:58）`tasks.md`、`analyze-report.md`、`tasks-notes.md`、`spec.md` 也被改寫成另一版（重編為 T001～T165；驗證器五份皆 OK）。
- 推測（未證實）：另一個同時在跑的自動派工 session（`--auto … --go`，status.md 把 B-014 列為批次 25「規劃中」）也挑中 B-014，與本 resume 同時寫同一 worktree。
- 目前狀況：工程師 `impl-notes.md` 為 `status: blocked`，`tasks.md` 無任何 [X]，tests 未執行（它當時跑出 18 failed／23 passed，但與對方的 `throttle.py` API 假設可能不相容，不可採信）。我方的 `tests/db/throttle_helpers.py`、`test_throttle_{jotform,pay,login}.py`、`tests/db/conftest.py` 附加的 4 個 fixture 與對方的檔案混在同一工作樹。我沒有動任何檔案，也沒有再派工。
- 環境備忘：compose 專案名要小寫 `b-014`（大寫會被拒）。

## 選項

- A（建議）：你先確認並停掉其中一個寫入者（保留哪一個由你決定），我再核對工作樹現況（以 `git status`／`wt fingerprint`），從 `tasks.md` 實際勾選狀態接續實作。
- B：以目前工作樹為準，由我重派工程師，先盤點雙方變更再整合，風險是兩邊的 API 假設不一致（`hit(category, …)` 與字串類別 `hit("REDIRECT", …)`）。

建議 A：兩個寫入者同時存在時，任何測試結果與勾選狀態都不可信。

## 規劃階段已驗證完成，不需重跑

spec／plan／testplan／tasks／analyze 驗證器皆 OK；Q1、Q2 裁示已落入 `clarify-log.md`；`ATTEMPT_OPEN_WINDOW_MINUTES` 仍待使用者裁示（預設 None，不阻擋）。

## 人工裁示（追加，2026-11-18）

1. **調度者衝突**：使用者先選 A（`dev-B-014` 當唯一調度者），後於 2026-11-19 改選 B——**由 console-9e 接手**，`dev-B-014` 不再調度（以此為準；上一行 A 的描述已失效）。
2. **付款嘗試時間窗**：使用者選 A——進行中付款嘗試**只計最近 30 分鐘內建立的**（`ATTEMPT_OPEN_WINDOW_MINUTES = 30`），超過的不計入 3 筆上限。BE-API-30 由「條件案例」升為**正式案例**，tasks.md 的條件任務 T085～T087 改為必做；BE-API-29（預設不設時間窗、超過 2 天仍擋）不再是正式行為，需改成與 30 分鐘一致（由 pm／QA 在文件同步）。`PaymentAttempt.created_at`（auto_now_add，`models.py:342`）已由 QA 確認存在。

使用者於 `dev-B-014` 對話親自回覆「繼續」（2026-11-20），確認上述兩項裁示；已據此續做。
