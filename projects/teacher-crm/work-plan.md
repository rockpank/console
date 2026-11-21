# 工作計畫：teacher-crm

> **2026-11-18 最新（事實，調度者核對）：B-001、004、005、006、008、009、025、027、028、029、033、036、042、058 共 14 項已 commit、合併進 master 並 push（本機＝origin）；批次 1（B-004、B-005、B-027）、批次 2（B-001、B-009、B-028、B-029、B-033、B-006）、批次 4（B-008、B-036）、批次 5（B-058）、批次 6（B-025）、批次 7（B-042）皆標「已合併」。合併後驗證：1234 測試通過、覆蓋率 98.17%。B-002 前置（B-001 合併）已滿足，但 B-002 本身已完成待合併，不再派工。新增批次 25（見檔尾）。**
>
> **2026-11-18 更新（事實）：t-B-001、006、008、009、025、028、029、033、036、042、058 共 11 條分支已合併進 teacher-crm master，其 worktree 已清理（分支保留）；下文各批次／任務段中「未 commit／待使用者合併」為當時紀錄，現況為「已合併」。B-002 的依賴（B-001 合併）已解除，可開工，尚未派工。B-009 仍僅 secret 為空範圍，「非 LINE 模式一律 400」未做。**
>
> **B-002 更新（2026-11-18，依檔頭）：完成，待使用者合併。`tasks/B-002/security-1.md`、`qa-1.md` 皆 `verdict: 通過`（round 1）；`escalation.md` 為 `resolved: true`（協議第 8 節「測試前置例外」，QA 已認可四項）。下文批次中「已升級／等裁示 A／B／開發中」為當時紀錄，已失效。**
>
> 維護者：`project-manager`（切分模式）。最後更新：2026-11-18（依 status.md／backlog.md／tasks 交接檔同步事實：B-001、B-006（規格 042）、B-008、B-009、B-025、B-028、B-029、B-033、B-036、B-042、B-058 皆已完成、資安／QA 通過、未 commit，待使用者 commit／合併；B-001／B-006／B-008 的 escalation.md 檔頭皆 resolved: true；B-002 仍等 B-001 合併。批次完成紀錄與各批「自動挑選紀錄」保留為當時內容）。不開 worktree、不寫程式。
> 依據：`backlog.md`（B-001、B-002 列與項目說明、檔案衝突表）、`profile.md` 路線判準、`docs/agent-protocol.md` 第 3 節閘門，以及對目標 repo `/home/user/web/teacher-crm`（master＝origin/master＝`4675d95`，工作樹乾淨，調度者提供）的唯讀確認：`specs/005-secure-config-defaults/` 下 `spec.md`、`plan.md`、`spec-mapping-checklist.md`、`system-analyze/technical-research.md`。未讀 `.env`。
> 環境：中控台已搬到新機器（`/home/user/web/`）；批次 1 的 worktree 與預覽站在本機不存在，三分支在 origin 上、尚未合併。B-001 worktree 已由調度者建立（見下）。**本機 Docker 已可用**（先前「無 Docker」升級已解除，依 status.md 環境段；本機無 `make`，改用 `docker compose run --rm [--no-deps] app <指令>` 等效指令，compose 專案名須小寫）。使用者已建立 `config/env/teacher-crm/` 目錄（內容未經任何角色讀取，是否含兩把互異金鑰未確認；是否已 `env sync` 進 worktree 未確認）；在另行裁示前沿用「使用者裁示」3。

> 已合併／已結束的批次與任務細節（批次 1–24、26、27，及已被取代的「執行佇列」）已封存到 `archive/work-plan-20261119.md`；
> 需要查歷史（舊檔案範圍、舊規格編號、自動挑選紀錄）才讀它，平常不必讀。封存日期 2026-11-19，內容原樣保留、未改寫。

## 批次

| 批次 | 任務 | 狀態 | 說明 |
|---|---|---|---|
| 1 | B-004、B-005、B-027 | **完成（2026-11-17），待使用者合併** | 紀錄見下方「批次 1 完成紀錄」 |
| 2 | **B-001**、**B-009**（批內 2，可平行；B-006 待決，不在本批） | **B-009：完成並已合併（分支 `t-B-009`，worktree 已清理）；資安通過／QA 通過（905 通過、覆蓋率 97.44%）；僅 secret 為空範圍。B-001：完成並已合併（分支 `t-B-001`，worktree 已清理）；資安通過／QA 通過，997 通過、覆蓋率 97%；escalation 已 resolved。** B-001：（已完成；原「從 `tasks.md`／`analyze-report.md` 接續」已走完，升級已 resolved）；B-009：新任務，快速路線 | 設定鏈 C 首位；範圍含 scheduler 指令路徑修正（裁示 2）。B-001 與 B-009 檔案不重疊（見「B-009」「重疊檢查」）；與批次 1 檔案不重疊 |
| 2（併入） | **B-028**、**B-029**、**B-033**（補測，快速路線） | **B-028（規格 018）、B-029（規格 019）、B-033（規格 020）：完成並已合併（分支 `t-B-028`／`t-B-029`／`t-B-033`，worktree 已清理）；資安通過／QA 通過**（942／961／916 通過，覆蓋率 98／97／98%）。同時開發上限放寬為 5（裁示 4，僅本次），本批實際 5 條（B-001、B-009、B-028、B-029、B-033） | 只動新增測試檔，與 B-001／B-009 無檔案重疊；語意耦合見各任務與「重疊檢查」 |
| 2（含 B-006） | **B-006** | **完成並已合併（分支 `t-B-006`，worktree 已清理）；資安通過／QA 通過**（規格 042，903 通過，覆蓋率 97% 為 engineer 自報、QA 未複驗；預覽站僅確認 302、未實際操作；worktree 內有來源不明 `.env`，未讀取，待使用者確認）。使用者 2026-11-17 裁示選 A：改規格，預設不勾選 | 見「任務 B-006」 |
| 3 | **B-002** | **完成（分支 `t-B-002`，資安／QA 第 1 輪通過），待使用者合併**（原「可開工、尚未派工」已失效；原裁示 1：等 B-001 合併後才開，不疊分支） | 與 B-001 同動 `settings.py`、`tests/db/conftest.py`、`tests/db/test_fake_checkout.py`，且依賴 B-001 新增的「假金流旗標預設關＋具名 fixture」；`bin/console wt add` 只能從 `origin/<base_branch>` 開分支（無起點參數），所以預設必須等 B-001 合併並進到 origin/master 後再開 |

model 通道：B-001、B-002 皆**不動** `models.py`／migration（005 plan 已判定；B-002 由 `/quickfix` 再確認），本計畫期間 model 通道空閒。

## 批次 25（`--auto 3 --go`，2026-11-18，追加；B-001 等 14 項已合併並 push 後重新挑選；既有批次、任務、規格編號、檔案範圍皆未改）

批內 3 條可平行；model 通道只有 B-011 可能動，另兩項不動 model。規格編號取 043、044、045：核對目標 repo `specs/`（現有 001–005、010、023 套件目錄可見）與本檔（佇列預留 009–041 為 a 類、042 已由 B-006 使用），043 起無人使用；佇列原預留的 014（B-014）、017（B-026）不沿用，避免與日後預留表混淆（由調度者／pm 最終確認）。

| 任務 | 標題／路線 | 規格 | 檔案範圍（粗估） | model | 依賴 |
|---|---|---|---|---|---|
| B-011 | 每日 job 納入內建排程，後台設定發送時間、不補發（Q2 已答）／**完整路線**（含 `/clarify`：時區、設定放平台或專案層級、設定頁狀態） | 043（`specs/043-builtin-daily-scheduler/`，名稱由 pm 定） | `scheduler.py`、`line/notifications.py`、`views.py`（排程設定頁區段）、`forms.py`（設定表單）、新增測試檔；可能 `models.py`＋migration（設定儲存）、`urls.py`（若新增路由） | **可能（model 通道唯一一位）**；若判定不需則不動 | B-008 已完成；無待決 Q |
| B-014 | 公開端點與登入入口濫用防護：節流、嘗試上限、登入失敗鎖定、`/admin/` 不公開／**完整路線** | 044（`specs/044-public-endpoint-rate-limit/`，名稱由 pm 定） | `settings.py`（cache 設定）、`views.py`（`jotform_return`／`jotform_webhook`／`pay_page` POST、登入，與 B-011 不同區段）、`urls.py`（`/admin/`）、新增測試檔 | **否**（採 DB cache＋`createcachetable`；若 architect 判需計數表 → 停下回報，因 model 通道已給 B-011） | B-001 已合併；無待決 Q。**完成（2026-11-21）**：資安／QA 第 1 輪通過，impl-notes done，escalation resolved；分支 t-B-014 待使用者合併 |
| B-026 | 現場報名、提前報到、建立訂單的併發重複操作回友善訊息而非 500／**快速路線（候選）**，`/quickfix` 若判不符轉完整，編號不變 | 045（`specs/045-fix-concurrent-duplicate-friendly-error/`，名稱由 pm 定） | `attendance.py`、`orders.py`、`views.py`（報名／報到／建單的錯誤處理區段）、新增測試檔 | 否 | 無；名額口徑（Q1）只影響與 B-012 的後續整合，不阻擋重複操作的友善訊息。**【完成，2026-11-18】** 資安／QA 第 1 輪通過；實動 `attendance.py`、`orders.py`＋新測試，`views.py` 未動；待使用者合併（t-B-026，規格 045） |

驗收標準：各項依 `backlog.md` 說明；共通回歸範圍（lint、test 不得變少、check、無待產生 migration、覆蓋率 ≥ 95%、codemap-check）；提供 `JOTFORM_API_KEY` 假值；A 專案讀不到 B 專案。不得改變：既有通知內容與冪等（MUST 9）、公開端點既有驗簽與冪等、既有報名／建單成功路徑。

互相重疊檢查：B-011 與 B-014 同動 `views.py`（不同區段）；若 B-011 新增路由則同動 `urls.py`，該處序列（B-011 先），其餘不重疊。B-014 與 B-026 `views.py` 不同區段。B-011 與 B-026 無重疊。`docs/code_map/` 由合併者重產，不手解衝突。

### 自動挑選紀錄

挑了 3 項：**B-011**、**B-014**、**B-026**（依 backlog ID 優先序；每項理由見上表：Q 已解除、無依賴、彼此不重疊）。沒挑的主要原因（一行一項）：
- B-002：已完成（資安／QA 第 1 輪通過，分支 t-B-002，規格 009），尚待合併，重派會與既有 worktree 衝突；請調度者確認其狀態。
- B-003、B-013、B-030：仍依賴 Q8（B-013 另依賴 B-003）。
- B-010、B-012、B-024、B-020：動 model，與 B-011 搶同一個 model 通道（建議序 B-024 → B-012 → B-010）；皆有待 pm 釐清事項。
- B-015、B-059、B-060：依賴 B-014／B-019／B-002；B-060 須排最後。B-055：依賴 B-011。
- B-016：與 B-014 同動 `settings.py`，排 B-014 之後。B-017：與 B-014 同動 `views.py` 的 `pay_page`。B-019：與 B-011 同動 `forms.py`。B-021：動 `scheduler.py`、`line/notifications.py`（與 B-011 重疊）。B-022：與 B-014 同動 `views.py`／`settings.py`。B-050：動 `views.py`，序列於後。
- B-018：pip-audit 誰執行待釐清，且與 t-B-034（`pyproject.toml`）可能重疊。B-023：Q4 使前提不成立，待使用者確認關閉。B-057：須先蒐集原因分佈。B-035、B-038：待測試帳號（Q6）。
- B-039、B-041、B-043、B-044～B-049、B-051～B-054、B-056：`base.html`／多樣板鏈須序於待合併 t-B-007，或依賴 B-013／B-040／B-051 等未完成項，或 Q15 範圍待釐清（B-044）。
- 已完成不再挑：B-001、B-002、B-004～B-009、B-025、B-027～B-029、B-031～B-034、B-036、B-037、B-042、B-058。

風險旗標：調度者稱「沒有未合併分支」，但 `merge-plan.md`（六條分支零提交、成果在 worktree 未 commit）與本檔記錄的 t-B-002、007、031、032、034、037 不在 14 項合併清單內；若它們仍未合併，B-011／B-014／B-026 的 `views.py`、`forms.py` 與 t-B-002 有合併期衝突可能（已依調度者指示不當作排除條件，僅標記）。

## 使用者裁示（2026-11-17）

1. **B-002 等 B-001 合併進 origin/master 後才開**，不疊分支；批次 3 本次不執行。
2. **B-001 範圍納入 scheduler 指令修正**：`compose.yaml` 的 scheduler 指令改為 `python src/manage.py run_scheduler`，讓 005 US3 驗收情境 2 可驗證。
3. **本機（新機器）當時尚無 `config/env/teacher-crm/` 目錄**（之後使用者已建立，內容未經角色讀取），worktree 沒有 `.env`。驗證時角色以命令列環境變數提供假值（假 `DJANGO_SECRET_KEY`、`FIELD_ENCRYPTION_KEY`、`JOTFORM_API_KEY` 等），不建立或讀取 `.env`。

4. **同時開發上限放寬為 5 條線（僅本次；協議第 3 節批內上限 3 的例外）**。目前有效進行 4 條：B-001（完整）、B-009、B-028、B-029（快速）；B-006 已裁示改規格，成為第 5 條有效進行線（B-001、B-009、B-028、B-029、B-033 中 B-009／B-028／B-029／B-033 已完成，進行中為 B-001 與 B-006，未超過批內上限 3）。

## 需要使用者決定

0. （已解決 2026-11-17）B-006：使用者裁示選 A，改規格、預設不勾選；B-006 以快速路線、規格 042 進批次 2。
0a. **B-009 範圍（仍待決；B-009 已合併，僅 secret 為空）**：「非 LINE 模式一律 400」未做（與「既有有效簽章綁定流程不得改變」矛盾，見 `tasks/B-009/impl-notes.md`）；是否另立項，由使用者決定、`pm` 立項。
0b. （已解決，`tasks/B-001/escalation.md` 檔頭 `resolved: true`，2026-11-18 核對）B-001 的 `.env` 升級；B-001 已完成。worktree `.env` 來源與金鑰（DEBUG=0 被判佔位值）仍須使用者確認，見 status.md 事後可瀏覽第 21、25 項。
0c. （已解決）B-008 升級：`tasks/B-008/escalation.md` 檔頭 `resolved: true`；B-006 升級亦 resolved。

1. （沿用）批次 1 合併時機：B-007 起的樣板鏈與 B-002 起的設定鏈都在等合併。
2. （沿用）Q7 運維動作：曾以預設值經 ngrok 對外，是否輪替 `SECRET_KEY`、重新輸入 Jotform 金鑰與 webhook 密鑰，由使用者另做。
3. （已解決）B-001 升級裁示（`tasks/B-001/escalation.md` 檔頭 `resolved: true`；Docker 已可用、B-001 已完成）。
4. （已解決 2026-11-17）`.claude/settings.json` 舊路徑：使用者已修正，調度者已核對三處新路徑。

> **範圍擴大（使用者核准 2026-11-19）**：B-011 可改 `src/crm/jotform/sync.py` 的 `sync_all`（加 `.order_by("id")`）與其回歸測試，僅此一處；見 `tasks/B-011/escalation.md`。

## 批次 28（**完成，已合併並已 push**，2026-11-21；B-039 QA 第 1 輪通過，無資安加派；分支 t-B-039 已 commit 並 `merge --no-ff` 進 master，master 8 個提交已 push（8e4f73f..418249d）；「前端課／後端課」範圍外，改列 backlog B-061）（追加；B-039 用語統一；既有批次、任務、規格編號、檔案範圍皆未改）

B-007 已合併進 master（使用者告知），base.html／樣板鏈前置已解除。注意：本次無法執行 git 指令（無 Bash），master 現況以 Grep 讀工作樹核對，未用 `git -C` 確認 master 提交；請調度者建 worktree 時以 origin/master 為準。

| 任務 | 標題／路線 | 規格 | 檔案範圍（粗估，Grep 核對） | model | 依賴 | 資安加派 |
|---|---|---|---|---|---|---|
| B-039 | 用語統一／**快速路線**：純使用者可見文字、docstring、一處千分位，不動權限／路由／model；Q13 已答（資料庫無舊稱，資料修正不納入）。唯一需 pm 在 `/quickfix` 前確認：「前端課／後端課」標示對象與 `test_wording.py` 相容（見 backlog Q13 範圍變動），若變成新增 UI 元素則轉完整，編號不變 | 046（`specs/046-wording-unification/`，名稱由 pm 定；核對 specs 與本檔 046 起無人使用） | `domain/project_nav.py`；樣板 `project_notifications.html`、`project_jotform_settings.html`、`project_products.html`、`project_front_course.html`、可能 `project_payments.html`／`project_attendance.html`／`project_session_detail.html`（`NT$` 千分位核對）；`views.py`（僅 docstring 與 962 行一字串）、`orders.py`、`reports.py`（docstring）；新增用語表文件；`tests/unit/test_wording.py` 不改 | 否 | **B-014**（同動 `views.py`，且 B-011／B-026 也動 `views.py`）：不與批次 25 同批，排在 B-014 合併後；若調度者堅持提早，僅可在 B-014 不碰 docstring 區段時由合併者處理衝突 | 否：純文字與 docstring，不碰登入／權限／金額計算／個資／外部串接（`NT$` 千分位僅顯示格式） |

驗收標準：依 backlog B-039；`test_wording.py` 通過；共通回歸（lint、測試不減少、check、無待產生 migration、覆蓋率 ≥ 95%、codemap-check）。不得改變：權限、路由名稱、側欄分組結構、既有資料、`retagging.py` 與 migrations 的舊稱。

排程：批次 28 單任務，待 B-014 合併後開（或 B-011、B-014、B-026 全合併後最安全）；不動 model／migration，不占 model 通道。
需要使用者決定：無新增（Q13 已答；標示對象由 pm 規格階段確認）。

## 批次 29（自動挑選最多 1 項，2026-11-21，追加；既有批次、任務、規格編號、檔案範圍皆未改）

### 自動挑選紀錄

結果：**沒有可挑的項目**，不建立任務、不配規格編號（下一個可用編號為 047）。判斷依據：backlog 狀態欄、本檔、status.md；進行中／待合併的檔案範圍——B-011（規劃中：`scheduler.py`、`line/notifications.py`、`views.py`、`forms.py`、可能 model）、B-014（待合併：`settings.py`、`views.py`、`urls.py`）、B-026（待合併：`attendance.py`、`orders.py`）、B-039（待合併，依 `tasks/B-039/impl-notes.md`：`project_nav.py`、`project_products／front_course／notifications／jotform_settings.html`、`views.py` docstring、`orders.py`／`reports.py`／`line/notifications.py` docstring）、B-002（待合併：`settings.py`、`forms.py`）、B-034（待合併：`pyproject.toml`、`Makefile`）。沒挑的原因（一行一項）：
- B-003、B-013、B-030：待決 Q8（B-013 另依賴 B-003）。B-035、B-038：待測試帳號（Q6）。B-057：須先蒐集原因分佈。B-023：Q4 使前提不成立，待使用者確認關閉。
- B-010、B-012、B-024、B-020：動 model，與 B-011（可能動 model）搶同一個 model 通道；另有 pm 待釐清事項。
- B-016、B-017、B-022、B-044：與待合併的 B-014 重疊（`settings.py`／`views.py` 的 `pay_page`／`urls.py`）；B-044 另有 Q15 範圍待釐清。B-015：依賴 B-014（尚未合併）。
- B-019、B-021、B-050：與進行中的 B-011 重疊（`forms.py`、`scheduler.py`、`line/notifications.py`、`views.py`）；B-055 依賴 B-011。
- B-018：與待合併的 B-034 重疊（`pyproject.toml`），且 pip-audit 由誰執行待釐清。
- B-040、B-041、B-043、B-054：樣板或 `views.py` 與待合併的 B-039／B-014 重疊（如 `project_products.html`），且屬 base.html 鏈；B-040 另涉 Q10 權限放寬。
- B-045、B-046、B-047、B-048、B-049、B-051、B-052、B-053、B-056：依賴 B-013、B-041、B-044、B-051 等未完成項。
- B-059：依賴 B-019、B-002 合併；B-060：須排在所有碰 `views.py` 的項目之後。B-061：須待 B-039 合併。
- 已完成（含待合併）不再挑：B-001、B-002、B-004～B-009、B-014、B-025～B-029、B-031～B-034、B-036、B-037、B-039、B-042、B-058。

解除方式（供使用者參考，不代為決定）：合併 B-014、B-039、B-026、B-002、B-034 後，B-015、B-016、B-017、B-022、B-041 等可重新挑選；回答 Q8 可解開 B-003。
