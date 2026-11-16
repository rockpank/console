---
task: B-005
role: security-reviewer
verdict: 通過
date: 2026-11-17
round: 1
---

# B-005 資安審查（輪 1）：追售名單「待邀請出席」去重

審查對象：worktree `worktrees/B-005/teacher-crm/`（分支 t-B-005，未 commit）相對 origin/master 的差異。
範圍：`src/crm/templates/crm/project_follow_ups.html`、`tests/db/test_follow_ups_page.py`；入口 `views.py:1427-1440`（`project_follow_ups`）、`urls.py:205-206`（只讀）。
方法：`git diff origin/master`、逐行比對樣板、讀 view／`followups.py` 查詢、讀測試。唯讀；未讀 `.env`、未動其他 worktree 或原 repo。

## 逐項結論

1. 輸出編碼與 CSRF：維持。
   - 樣板全檔無 `|safe`、`autoescape`、`mark_safe`（grep 為空）；剩下那份 `project_follow_ups.html:35-44` 一樣只用 `{{ student.name }}`、`{{ student.phone }}`、`{% include "crm/_line_state.html" %}`，沿用預設自動跳脫。`_line_state.html` 也無 `|safe`。
   - 被刪除的是 diff 中第 35-44 行（原第一份，10 行）。兩份內容逐行相同（diff 的刪除行與留下的 context 完全一致）。
   - 本次刪除的區塊不含任何 `<form>`／`csrf_token`。全檔 `<form>`＋`csrf_token` 比對 origin/master 與工作樹皆為 4 處（2 個 form：`project_follow_up_stop` 於 `:25-27`、`project_follow_up_remind` 於 `:50-52`，皆 `method="post"` 並帶 `{% csrf_token %}`），數量不變。
2. 權限與專案隔離：維持，既有測試仍涵蓋。
   - view 未改：`project_follow_ups` 有 `@login_required`（`views.py:1426`），`_project_or_404` 以 `Project.objects.visible_to(request.user)` 過濾（`views.py:258-259`，MUST 4）；`can_edit` 由 `can_perform_on(..., Action.EDIT_DATA)` 伺服端算出（`views.py:1438`，MUST 5）。`students_to_invite` 用 `Student.objects.for_project(project)`（`followups.py:78-85`），仍限本專案。
   - 樣板的 `can_edit` 控制只影響按鈕顯示；停止／提醒端點自身仍由 `_require`／`get_object_or_404(FollowUp.objects.filter(project=project))` 擋（`views.py:1445-1448`，未改）。
   - 測試仍在：`test_instructors_can_view_follow_ups_page_but_not_change`（講師可看、無「停止追售」、POST 403）、`test_follow_ups_page_is_project_scoped`（他專案頁 404、跨專案停止 404）、`test_staff_can_stop_follow_up_from_page`（含 GET 405）。此三者皆未被改動。
3. 有無誤刪：無。工作樹相對 origin/master 的原始碼變更僅此樣板刪除 10 行、無新增行。「追售中」（`:15-33`）、「進階未完款」（`:46-`）、「已停止」區塊與兩個表單都完整保留。另有 `docs/code_map/*` 變動（行數／產生物）與未追蹤的 `specs/007-…`（quickfix.md、tasks.md），皆非執行碼；程式碼地圖是否由 `make codemap` 產生而非手改，屬流程問題，本審查不展開（見「未能驗證」）。
4. 測試強度：未弱化，反而加強。
   - 新增 `content.count("待邀請出席") == 1`（真正偵測重複標題）、區段以 `.split("進階未完款")[0]` 截斷避免誤吃後面區塊、`invite.count("缺席者") == 1`（偵測重複名單項）。原有「缺席者在、到場者不在」斷言保留。
   - 無 skip／xfail、未調降門檻。相對舊版 `split("待邀請出席")[1]`（在重複時取到第一份、無法偵測重複），新版在還原重複時會失敗，確實在測行為。

## 發現清單

| 編號 | 嚴重度 | 位置 | 說明 |
|---|---|---|---|
| — | — | — | 本次變更無資安發現（無嚴重／高／中／低）。 |
| I-1 | 資訊（範圍外，另立項目建議） | `project_follow_ups.html:15-33`、`:55-` | 追售中名單 `{{ row.student.phone }}` 等個資在頁面上直接顯示給講師角色（唯讀可見）。是既有行為且為需求（講師可看），非本次引入；若要最小揭露可另立項目評估講師是否需看電話。 |
| I-2 | 資訊 | `test_follow_ups_page.py` | 跨專案隔離測試只驗證「頁面 404」與「停止 404」，未直接斷言本專案頁面不含他專案學員姓名（待邀請名單的隔離僅由 `for_project` 保證）。可另立補測項目（B-027 類）。不阻擋。 |

## 未能驗證之處

- 未實際執行測試（`make test` 需 Docker，且本任務限唯讀）。「新斷言在還原重複時會失敗、在現狀下通過」為靜態推論；交付驗證交由 qa-engineer 實跑。
- 未渲染實際頁面確認 `to_invite` 於 include `_line_state.html` 時的 `student` 變數解析；但該 include 與 origin/master 保留那份完全相同（迴圈變數 `student`），行為未變。
- `docs/code_map/*` 是否為 `make codemap` 產物（而非手改）無法由 diff 判定；profile 禁止手改，請調度者／qa 以 `make codemap-check` 確認無 STALE。

## 結論

verdict：通過。純樣板刪除重複的 10 行，輸出編碼、CSRF、POST、權限、專案隔離皆不變，既有測試仍涵蓋，新測試強化了去重斷言。可進入 qa-engineer 交付驗證。
