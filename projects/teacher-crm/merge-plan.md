# teacher-crm 合併計畫（2026-11-18）

前提：目標 repo `/home/user/web/teacher-crm`，base = `master`（本機 03d1f37，工作樹乾淨）；`origin/master` = 4675d95。六條分支（t-B-002、007、031、032、034、037）**全部沒有任何提交**（`rev-list --count master..分支` 皆 0，分支尖端都是 base 的祖先），所有成果都是 worktree 內**未 commit** 的變更。因此 `merge-tree` 不能用，下列衝突預判是以「檔案重疊」加 `git apply --check`（對目前 master 試套 worktree 差異，唯讀）推測。

## 可合併分支（建議順序）

| 順序 | 分支 | 需先 commit | 與誰重疊（檔案） | 遷移 | 備註 |
|---|---|---|---|---|---|
| 1 | t-B-037（純 specs 文件） | 是，23 檔（皆 specs/ 下，無非 specs 檔） | 與已合併的 B-006 同動 `specs/TEST_LIST.md`，但 B-037 起點 03d1f37 已含 B-006，且 apply --check 對 master 通過 → 無衝突；與其他待合併分支無重疊（它們不動 specs/001、003、004、SITEMAP、TDD_PROGRESS、TEST_LIST） | 無 | 順序任意，建議最先（零風險） |
| 2 | t-B-002（規格 009，改 checkout.py／forms.py／views.py＋db 測試） | 是，16 檔（含 code_map 產生物 6 檔；另有未追蹤的 `specs/009-*`、`tests/db/test_fake_gateway_disabled.py` 需 `git add`） | 與 B-007 無原始碼重疊；與其他分支僅 code_map 產生物重疊 | 無 | 起點 = master 尖端；apply --check 通過。合併後其他分支的 fake 測試可能轉紅（見 status.md 風險段），故建議先合、再跑全套測試 |
| 3 | t-B-031（規格 030，只新增測試＋spec） | 是，7 檔（含未追蹤 `specs/030-*`、`tests/db/test_webhook_to_line_payment_reminder.py`） | 僅 code_map 產生物 | 無 | 無原始碼變更 |
| 4 | t-B-032（規格 031，只新增測試＋spec） | 是，9 檔（含未追蹤 `specs/031-*`、兩個 `tests/db/test_line_*.py`） | 與 B-031 僅 code_map 產生物（`src.crm.line.md`、`tests.db.md`）重疊 | 無 | 無原始碼變更；與 B-031 順序任意 |
| 5 | t-B-034（規格 021，改 Makefile／pyproject.toml＋unit 測試） | 是，7 檔 | 與其他分支無原始碼重疊；apply --check 通過（master 這 29 個提交沒動 Makefile／pyproject） | 無 | 起點是 origin/master 4675d95，落後本機 master 29 個提交。覆蓋率門檻改變，合併後 `make coverage` 要重跑確認 |
| 6 | t-B-007（規格 012，改約 24 個 template） | 是，27 檔（含未追蹤 `specs/012-*`、`tests/db/test_messages_component.py`） | **會衝突**：起點 4675d95 落後 29 個提交；master 在這段期間改了 `base.html`、`project_attendance.html`、`project_follow_ups.html`、`project_student_edit.html`，B-007 也改這四檔。`git apply --check` 對 master 失敗於 `project_student_edit.html` | 無 | 見下方「不能合併／等待」 |

## 不能合併／等待

| 分支 | 原因 |
|---|---|
| t-B-007（目前狀態） | 起點過舊（落後 29），與 master 已合併內容（B-006 改 `project_attendance.html` 等）在 template 上重疊，直接 commit 後合併大概率衝突。建議方向：先在 worktree 內 commit，再由使用者決定是把分支 rebase／merge 到最新 master（本工具不替你做），衝突時以 master 現有的版本為底、再套上 B-007 的「訊息元件統一」改動（訊息區塊用 B-007 的元件，其他行為邏輯如 B-006 的預設未勾選保留 master 的）。解完後要重跑全套測試與 `make codemap`。 |
| 全部六條 | 都未 commit。使用者要先 commit（可請我進「執行模式」代為提交）才能合併；未追蹤檔（`specs/…`、新測試檔）要記得 add。 |

## 合併後收尾

- code_map：各分支在 `docs/code_map/*` 都有產生物變更，**彼此必然衝突／重複**（INDEX.md、manifest.json、modules/src.crm.md、tests.db.md 幾乎每條都動）。建議 commit 時各分支不帶 code_map 變更（或合併後直接丟棄再重產），全部合完後執行 `make codemap` → `make codemap-check`（需無 STALE）。code_map 不得手改。
- 全套品質關卡：`make lint`、`make test`、`make manage cmd="check"`、`make manage cmd="makemigrations --check --dry-run"`、`make coverage`（≥ 95%；B-034 會改門檻／分支覆蓋）。status.md 註記需提供假 `JOTFORM_API_KEY`，否則有 2 個既有失敗（P-1）。
- 特別留意 B-002 合併後其他 fake 測試是否轉紅。
- `status.md`／`backlog.md` 把 B-002、007、031、032、034、037 改「已合併」，交 `project-manager`。
- worktree 清除：`bin/console wt rm <任務> -p teacher-crm`（有未提交變更會拒絕，所以要先 commit）；B-007 預覽站先 `bin/console site rm B-007 -p teacher-crm`。分支保留。
- 本機 master 比 `origin/master` 多 29 個提交（尚未 push；本角色不 push，由使用者決定）。

## 風險旗標

- 全部分支零提交，成果僅存在 worktree；誤清 worktree 會遺失。
- 起點不一：B-002／031／032／037 = 本機 master 尖端 03d1f37；B-007／034 = origin/master 4675d95（落後 29）。本機 master 與 origin 沒有分岔（只是領先 29、落後 0）。
- worktree 內有 root 擁有的檔案：各 worktree 的 `.ruff_cache`、`.pytest_cache`、B-002 另有 `.coverage`（docker 產生）。`wt rm` 可能 Permission denied，需使用者同意後處理；本次未做任何刪除。
- B-037 的 worktree 與 B-006 同動 `TEST_LIST.md`，已確認無衝突；但 B-037 的 specs 修改量大（23 檔），commit 前建議只確認沒有夾帶非 specs 檔（已查：非 specs 檔 0 個）。
- 以上衝突預判屬推測（未 commit，無 merge-tree）；commit 後應重跑一次 `git merge-tree --write-tree master <分支>`。

## 執行結果（2026-11-18，execute 模式）
- 停在第 1 步：`git commit` 失敗，錯誤為 `Author identity unknown`（git 未設定 user.name／user.email）。未自行捏造身分。
- t-B-002 worktree 已 `git add src tests specs`（已暫存 11 檔，code_map 未納入），尚未 commit；其餘五條分支未動；master 未變動（HEAD 03d1f37）。
- 需使用者設定 git 身分（或指定要用的身分）後再執行。

## 更新（2026-11-21，分析模式，base 核對）
- base：master = 173ca7b，工作樹乾淨；origin/master = 8e4f73f，是 master 的祖先，master 領先 5 個提交、落後 0（未分岔，未 push）。
- 已進 master（`merge-base --is-ancestor`）：全部 20 條 t-B-* 分支（001、002、006、007、008、009、011、014、025、026、028、029、031、032、033、034、036、037、042、058），各分支 `rev-list --count master..分支` 皆 0。B-007 的 e5dfbd4 為 master 祖先（合併提交 b9e0e27 存在）。
- 仍待合併：0 條（無任何分支領先 master）。
- 注意：分支尖端是 master 祖先 = 無獨有提交。t-B-014 worktree 尚有 17 個未提交變更（無提交），這些不在 master，清除前需使用者確認。
- B-007：worktree 乾淨（0 變更）、分支已合併，可清理。預覽站 localhost:8100 目前回應 HTTP 302（仍在跑）。順序：`bin/console site rm B-007 -p teacher-crm`（資料庫 volume 保留，要清加 --drop-db）→ `bin/console wt rm B-007 -p teacher-crm`（分支保留；若有 root 擁有的 .ruff_cache／.pytest_cache 可能 Permission denied，需使用者同意）。本次未執行任何清除。
- 新任務起點：`wt add` 起點是 origin/master（8e4f73f）。核對：e5dfbd4（B-007 分支尖端）已是 origin/master 祖先，且 origin/master 的 `src/crm/templates/crm/base.html` 已含訊息元件（`role="status/alert"` 的 alert 區塊）及 `tests/db/test_messages_component.py`。結論：新任務起點已含 B-007 程式。master 另多 5 個未 push 提交（含合併提交 b9e0e27）不在起點內，若要含它們需使用者先 push 或另行處理（本角色不 push）。

## 更新（2026-11-21，分析模式，納入 t-B-014／規格 044）
- 狀態：t-B-014 零提交（`rev-list --count master..t-B-014` = 0；分支尖端 = 8e4f73f = origin/master），成果全在 worktree 未 commit：6 個修改檔（Makefile、src/config/settings.py、src/config/urls.py、src/crm/urls.py、src/crm/views.py、tests/db/conftest.py）＋未追蹤 `specs/044-public-endpoint-rate-limit/`、`src/crm/login.py`、`src/crm/throttle.py`、`tests/db/` 下 7 個新測試檔＋`throttle_helpers.py`。commit 時務必 `git add` 這些未追蹤檔。
- 起點落後：master = 173ca7b，領先 B-014 起點 5 個提交（落後 5，未分岔）。master 這 5 個提交動了 `src/crm/urls.py`、`src/crm/views.py`、`tests/db/conftest.py`（與 B-014 重疊），沒動 Makefile、src/config/。
- 衝突預判（未 commit，只能以重疊＋`git apply --check` 推測）：對 master 試套 B-014 差異，**`tests/db/conftest.py` 失敗**（hunk 約 31 行處），urls.py／views.py 無 apply 錯誤（同檔但不同區段，仍建議 commit 後跑 `git merge-tree --write-tree master t-B-014` 確認）。建議方向：conftest 以 master 現版為底，再加入 B-014 新增的 throttle 相關 fixture（清快取等），不丟掉 master 新增內容。
- 與其他分支：其餘 t-B-* 皆已在 master（領先 0）；t-B-039 worktree 乾淨、領先 master 0，無重疊。目前**唯一待合併 = t-B-014**，順序無需排。
- 遷移：B-014 無 model／migration（migrations 最新 0032_daily_job_scheduler，無撞號）。`CACHES` 用資料庫快取表，由 `createcachetable` 建立，不在 migration 內。
- 合併後收尾：(1) 每個環境（含測試／預覽站／正式）執行 `make manage cmd="createcachetable"`（Makefile 已加 `createcachetable` 目標，行 36），否則限流快取表不存在；(2) `make codemap` → `make codemap-check`（B-014 新增 login.py／throttle.py／路由，code_map 不得手改，commit 時不帶 code_map 變更）；(3) `make lint`、`make test`、`make manage cmd="check"`、`make manage cmd="makemigrations --check --dry-run"`、`make coverage` ≥ 95%（需假 JOTFORM_API_KEY）；(4) status.md／backlog.md 改「已合併」交 `project-manager`；(5) `bin/console wt rm B-014 -p teacher-crm`（先 commit；.ruff_cache／.pytest_cache 若 root 擁有會 Permission denied，需使用者同意）。
- **風險旗標：`specs/044-public-endpoint-rate-limit/_wip/`（內含 `draft/`：Makefile.patch、conftest.py.patch／.full、settings.py.patch、舊版 test_throttle_*.py 等）是舊草稿，不該進分支。使用者需在 commit 前手動移除該目錄（本角色不刪除）；否則 `git add specs/044-…` 會把它帶進去。**
- 其他風險：成果僅在 worktree，誤清會遺失；`settings.py` 新增 CACHES，部署前確認資料庫快取表已建立。

## push 紀錄（2026-11-21）
- 結果：**未推送**（前置檢查③失敗，停下）。
- 範圍：origin/master..master 共 5 個提交，涉及 B-011、B-026 合併與程式碼地圖（另含 specs/043、045 與對應 src／tests 檔案，共約 50 檔）。
- ①祕密掃描：檔名無命中；內容樣式掃描無命中。通過。
- ②fetch 後 origin/master 為 master 祖先（可快轉）。通過。
- ③base 工作樹乾淨、`codemap check` OK；但 `manage.py check` 未執行：docker compose 需要 repo 根目錄 `.env`（不存在，且不得建立／讀取），主機也沒有 django。快速檢查無法通過，故不推。
- 需調度者／使用者決定：提供可跑檢查的環境（如在有 `.env` 的環境由使用者跑 check），或明確同意以「code map OK＋先前各任務 QA 通過」替代。

## 執行紀錄（2026-11-21，B-039）
- t-B-039 已 commit 並 `merge --no-ff` 進本機 master；程式碼地圖已重產並另行 commit，`code_map.py check` OK。
- 快速檢查（B-039 worktree，COMPOSE_PROJECT_NAME=b-039）：`manage.py check` 無問題；`makemigrations --check --dry-run` 無變更。
- push 前檢查通過（origin/master..master 共 8 個提交、74 檔，可快轉，無祕密樣式命中，master 工作樹乾淨）。
- push：未執行，`git push origin master` 被權限系統拒絕，待使用者決定。
- 清理（僅列出，未執行）：t-B-039 worktree（wt rm；內有 root 擁有且被忽略的 .coverage、.pytest_cache、.ruff_cache，可能需使用者同意）、預覽站 8101（site rm）。
