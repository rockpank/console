# 多角色協議（所有角色與調度者先讀）

## 1. 鐵則

- 繁體中文。**絕不 `git push`、不開 PR、不部署、不 commit**（除非使用者明確要求）。
- 角色只靠**文件**交接，不靠口頭記憶；Subagent 不能再派 subagent，**調度只能由主對話做**。
- 結果必須來自實際執行；沒跑的標「未執行」，不可標為通過。
- 規格不清楚就回報「待釐清」，不要自行假設後直接實作。
- 不得越權：不改別人負責的文件；需要變更就在回覆中提出，由調度者轉交。
- `.env` 等專案「禁區」（見 `projects/<專案>/profile.md`）與 `config/env/**` 不讀、不印、不改、不貼進任何檔案。

## 2. 單位與位置

| 名詞 | 說明 |
|---|---|
| 專案 | 登錄在 `config/console.toml` 的 `[projects.<別名>]`，工作區在 `projects/<別名>/` |
| 任務 | 一個可獨立開發的工作包，代號全中控台唯一（預設 backlog ID，如 `B-017`；非 backlog 用 `N-<序號>`；第二個專案登錄後加專案前綴） |
| worktree | `worktrees/<任務>/<專案別名>/`，分支 `t-<任務>`（`bin/console wt add <任務> -p <專案>` 建立；不手動 `git worktree add`） |
| 工作區文件 | `projects/<專案>/`：`profile.md`、`engineer-rules.md`、`backlog.md`、`status.md`、`work-plan.md`、`assessment/`、`tasks/<任務>/` |

**文件放哪裡**

- 專案流程規定要進 repo 的產物（如 `specs/<NNN-*>/`、程式、測試）→ **在該任務的 worktree 內**，跟著 `t-<任務>` 分支走。
- 角色的報告與交接檔 → `projects/<專案>/tasks/<任務>/`（`impl-notes.md`、`review-<k>.md`、`security-<k>.md`、`qa-<k>.md`）。這些**不進專案 repo**。
- 進度只記在 `projects/<專案>/status.md` 與 `backlog.md`（單一事實來源），由 `project-manager` 維護。

每份交接檔以 YAML 檔頭開始，調度者與看板（`bin/console ui`）**只讀檔頭**判斷閘門，細節留在檔內。角色回覆 ≤ 10 行。看板認得的檔名與欄位：

| 檔案 | 檔頭欄位 | 值 |
|---|---|---|
| `impl-notes.md`（engineer） | `status`、`tests` | `status: done｜blocked`；`tests: 通過｜失敗｜未執行` |
| `security-<k>.md`（security-reviewer） | `verdict` | `通過｜需修正｜阻擋` |
| `qa-<k>.md`（qa-engineer） | `verdict` | `通過｜失敗` |
| `escalation.md`（調度者） | `kind`、`resume_at`、`resolved` | `kind: 額度保護` 或省略；`resume_at: 規劃中｜開發中｜資安｜QA`；`resolved: true` 表示已處理，看板不再要求裁示 |

看板的階段（規劃中→開發中→資安→QA→完成）取 `backlog.md` 的「狀態」欄與上述交接檔中較後面的一個；`完成` 只認 backlog。

## 3. 階段與閘門（`/dispatch` 的骨架）

```
規劃（pm/architect/uiux/qa 依 profile 角色對應）→ 實作＋單元測試（engineer）→ QA 驗證＋整合測試＋安全檢查（qa-engineer；任務標「資安加派」才另有 security-reviewer 平行深審）→ 收尾（project-manager）
```

- **規劃完成閘門**：profile 規定的前置產物齊全（例如 skills 專案的 `tasks.md`，完整路線另需 `analyze-report.md` 無可修項），工程師才能開工；缺了不由工程師自補。
- **審查迴圈最多 2 輪**：QA（或加派的資安）退回 → `engineer` 修 → 複審；第 2 輪只重審被退回的一方，另一方僅在修正動到其範圍時才重審。
- **資安加派**由 `project-manager` 在 `work-plan.md` 標記（判準見其角色檔）；調度者不自行增減，要改請回頭請專案管理員改計畫。
- **同批平行**：只有「檔案範圍不重疊、無依賴」的任務放在同一批；批內上限 3；同一時間只允許一個任務動 model／migration；共用檔（settings、urls…）衝突者序列化；規格編號由 `project-manager` 在 `work-plan.md` 一次分配。
- 平行任務各自一個 worktree、各自 `COMPOSE_PROJECT_NAME=<任務>`；不得兩個任務共用一個 worktree。

## 4. 升級條件（才會停下來問使用者）

以下任一成立，調度者暫停該任務並回報（其餘不受影響的任務照常往下）：

1. 需求或規格矛盾、缺關鍵決定、需使用者拍板（含 profile 規定的「等使用者回答」硬停點）。
2. 與專案憲法／規範衝突。
3. QA 失敗（含安全檢查的嚴重／高風險）或加派資安「嚴重／高風險」，經 2 輪修正仍未解。
4. 需要使用者授權的指令（profile 標「需授權」者、連真實外部服務、`git push`、`docker compose down`…）。
5. 任務範圍與工作樹中「與本任務無關的未提交變更」重疊，或 model／migration 衝突無法靠排序解決。
6. 變更範圍明顯超出 `work-plan.md` 的檔案範圍（**例外**：既有測試檔若只補 fixture／前置設定〔如 `pytestmark = pytest.mark.usefixtures(...)`、測資常數〕、不新增或刪改任何斷言的結構，且是為了讓**本任務的 src 變更**下原本會紅的測試恢復，不算超出，免升級；條件見第 8 節「測試前置例外」）。
7. 額度保護（見下）。

低、中風險的發現不停下，記進報告與 `status.md`「事後可瀏覽」。

## 5. 額度保護

進入高耗階段（實作、每一輪審查與修正）前，執行一次 `bin/console usage --guard`：結束碼 0 照常；**3 → 不進入該階段**，把任務標為「暫停（額度保護）」寫進 `status.md`，回報預計重置時間後停止。**絕不自行解除**（不重試、不換方式派 subagent）；解除只有 `bin/console ui` 的按鈕。檢查指令本身失敗（非 0 非 3）→ 當作可以繼續，並在回報註明「額度檢查失敗」。

## 6. 專案端技能

專案自己的 skills（如 teacher-crm 的 `.agents/skills/`）都是 `disable-model-invocation`，在中控台**不會自動載入**：角色是 Read 它們的 `SKILL.md`／`RULES.md`，在本次任務內依 SOP 自己執行（不另開子代理）。對應關係在各專案 `profile.md` 的「角色對應」。

## 7. 個資與祕密

不處理客戶資料：測試與範例一律用假資料。報告、備註、commit 訊息不得出現真實姓名、帳號、金額、金鑰。發現疑似真實資料 → 不引用原文，只寫位置與類型並升級。

## 8. 成本與獨立性（2026-11-17 由實戰覆盤導入；數字是初始值，用過幾輪再依實測調整）

- **成本在回合數，不在輸出長度**：子代理每個回合都會把累積內容與 `CLAUDE.md` 重讀一次。所以限制「查幾次」比限制「寫多長」有效，`CLAUDE.md` 只放每回合都用得到的規則，細節放 `docs/maintenance.md`（按需讀）。
- **工具呼叫預算**：調度者在 prompt 寫預算；沒寫就用預設——規劃類（pm／architect／uiux）25、資安審查（僅加派時）20、QA（含安全檢查）40、工程師 80（補測或小改 40）。**回覆最後一行固定寫 `工具呼叫：<實際>／<預算>`**。超出預算要在回覆說明原因（多半代表範圍太大，應拆任務），不是默默超支。調度者把各角色的實際／預算彙整進批次覆盤。
- **作者不審自己**：QA（及加派的資安）以「變更本身」為準（`git diff`、重跑測試）。工程師 `impl-notes.md` 只當範圍線索，**不採信其中的「測試通過」「無缺陷」**；要引用結果就自己重跑。
- **唯讀角色真的唯讀**：資安審查前後各取一次 `bin/console wt fingerprint`，不一致就升級（條件 5），不自行判斷誰動的。
- **範圍授權清單**：工程師只能改 `work-plan.md` 該任務「檔案範圍」內的檔案；交付時調度者用 `git -C <worktree> status --short` 對照，超出且不是 `docs/code_map/` 這類產生檔就升級（條件 6）。需要超出範圍時，工程師停下回報（`status: blocked`），不得自行擴大。
- **測試前置例外**（2026-11-18，使用者授權；條件 6 的免升級類別）：同時滿足才免升級——(1) 該測試檔在本任務變更 src 後原本會紅（工程師用基線與紅燈實測證明，不是預先猜測）；(2) 只改 fixture／前置設定與必要的測資常數，不新增、刪除、弱化任何斷言，不 skip／xfail，不在 `conftest` 加會讓新案例失去意義的 autouse；(3) 工程師在 `impl-notes.md` 逐檔列出「檔案／原本紅的測試數／改了什麼」；(4) QA 以 `git diff` 驗證「斷言未被弱化」，並在 `qa-<輪>.md` 明寫結論。任何一項不成立就照條件 6 升級。測資常數若連帶改了斷言的比對值，只限常數取代，QA 要特別指出。
- **被擋就停，不要繞**：工具或權限拒絕時，停下回報原因與需要什麼，不換寫法、不改用別的工具繞過；這同樣適用於祕密檔與 `docker compose down`。
- **覆盤**：每批收尾由 `project-manager` 在 `status.md` 寫三行：上一批的調整有沒有效（附證據，沒遇到就寫「未驗證」）、這批新發現的缺點、這批要改的一兩件事。改流程檔前先備份成 `<檔名>.bak-<yyyymmddHHMM>`；調整必須在下一批實際用上，只停在報告裡不算。
- **流程檢視（每輪覆盤，閉環）**：每輪結束調度者先記用量帳本（`bin/console ledger`）並做輕量覆盤（≤ 3 行）；`ledger due` 觸發（失敗／卡住、超預算、等使用者 ≥ 2 次、累積 ≥ 300k token）才派 `process-optimizer`。它依帳本數字評估上輪實驗、提出新實驗，低風險改進（Tier A）直接套用並在後續輪次驗證，其餘（Tier B）交使用者決定，直到指標收斂。它不得削弱本節與第 4、5、7 節的任何規則或降低品質關卡；套用前先備份到 `runtime/flow-backup-<時間>/`；效果以帳本數字為準，不由它自己宣稱。細節見 `.claude/agents/process-optimizer.md`、`docs/process-review/experiments.md`。
- **回報精簡**（2026-11-19，流程檢視採用）：子代理給調度者的回覆**限 15 行**，只放——結論、status／verdict、關鍵數字（測試通過數、覆蓋率）、需要使用者或調度者決定的事、交接檔路徑、最後一行的工具呼叫。實測輸出、變更檔案清單、紅燈證據、假設與偏差全部寫進交接檔，調度者要看再讀。原因：每則回報都會留在調度者的 context 裡，之後每個回合都重讀一次。
