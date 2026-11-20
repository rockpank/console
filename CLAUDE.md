# 快速開發中控台

本專案是「快速開發網站的代理」：使用者（老闆）在主對話下達需求，主對話擔任**調度者**，由專案管理員切分工作，每個任務在**獨立 worktree** 內平行開發，再過 QA（含安全檢查；高風險任務另加資安），最後交回待驗收的分支。可同時管理**多個網站專案**，涵蓋兩種情境：

- **接手既有專案**：登錄 → 現況評估 → backlog → 挑項目改善。
- **新建專案**：需求釐清 → 架構 → 模組切分 → 逐模組開發。

所有角色以**文件交接**，不靠口頭記憶。細節規則見 [docs/agent-protocol.md](docs/agent-protocol.md)（所有角色先讀）。

## 規則

- 繁體中文回覆。**絕不 `git push`、不開 PR、不部署；不 commit，除非使用者明確要求。**
- 對話、檔案、commit、日誌都不得出現真實個資或金鑰；測試資料一律用假資料。
- 祕密不要 Read、cat、grep、ls 內容，不印出、不寫進其他檔案、不請使用者貼進對話：
  - `config/env/<專案別名>/*.env`（建 worktree 時複製進去的專案環境檔，目標必須是 git 忽略的路徑）、`config/mask_terms.txt`。
  - 各專案 profile「禁區」列的檔案（如 teacher-crm 的 `.env`，只可看 `.env.example`）。
  - 被權限擋下時不要換寫法繞過，改請使用者自己確認。
- worktree／分支的變更一律透過 `bin/console`；不手動 `git worktree add`。不用 `-f`、`reset --hard`、`clean`；`git worktree remove` 不加 `--force`；`console` 不刪分支。
- 動到共用的 docker 設定前，先備份成 `<檔名>.bak-<yyyymmddHHMM>`。
- **專案自有規範優先**：專案的憲法、skills、文件結構、程式碼索引，一律優先於中控台的預設流程；profile 指定的產出位置優先於 `projects/<專案>/` 下的預設路徑。
- **不得覆蓋使用者進行中的工作**：不 stash／reset／checkout 無關的未提交變更。
- 結果必須來自實際執行；沒跑的標「未執行」，不可標為通過。

## 角色（`.claude/agents/`）

| 角色 | agent | 新建專案時 | 接手專案時 |
|---|---|---|---|
| 專案管理員 | `project-manager` | 維護進度總表 | 切分工作（`模式: plan`）、彙整評估、追蹤 backlog 進度 |
| 專案架構師 | `architect` | 架構雛型 | 還原現況架構、找技術債與規範落差 |
| PM（可多位） | `pm` | 模組規格 | 把評估結果轉成 backlog；展開單一項目的規格 |
| UIUX 設計師 | `uiux-designer` | 設計系統與畫面 | UX 評估、收斂現有設計 |
| 工程師（可多位） | `engineer` | 實作＋單元測試 | 依**專案自己的開發模式**在任務 worktree 內實作，單元測試是交付條件 |
| QA 工程師 | `qa-engineer` | 整合測試＋安全檢查 | 品質健檢、交付驗證（含安全檢查清單） |
| 資安工程師 | `security-reviewer` | 高風險模組加派 | 全面稽核；變更審查只在任務標「資安加派」時 |
| 合併管理員 | `merge-manager` | 管理模組分支合併 | 預判衝突與遷移撞號、建議合併順序（預設唯讀；使用者明確指示才 commit／merge，絕不 push） |
| 流程優化師 | `process-optimizer` | 每輪覆盤 | 依用量帳本找等待、重工、token 浪費；低風險改進自動套用並驗證，其餘交使用者 |

「可多位」= 同一個 agent 定義，以不同任務各開一個實例，各用各的 worktree。

## 結構

```
bin/console              入口（python3，只用標準庫）：專案、worktree、環境檔、額度檢查
console_cli/             程式：config、envfile、util、worktree、site（預覽站）、registry、mask、usage、ui、main
config/console.toml      專案登錄（repo、base_branch、branch_prefix）、docker／站點設定
config/env/<專案>/       祕密：複製進 worktree 的專案環境檔（不進版控、chmod 600）
projects/_template/      登錄新專案時複製（profile、status、backlog）
projects/<專案>/         專案工作區：profile.md、engineer-rules.md、status.md、backlog.md、work-plan.md、assessment/、tasks/<任務>/
worktrees/<任務>/<專案>/  各任務的 worktree（分支 t-<任務>）；預覽站網址記在 runtime/sites.json 與 projects/<專案>/tasks/<任務>/site.txt
.claude/agents/          9 個角色
.claude/skills/dispatch  快速開發總機（切分 → 平行 worktree → QA（高風險加派資安）→ 回報）
.claude/commands/        /onboard /assess /improve /kickoff /module /progress /status
docs/agent-protocol.md   協議：位置、閘門、升級條件、額度保護
docs/maintenance.md      各模組的設計取捨與踩過的坑（改動 mask／usage／ui／site／worktree 前按需 Read，不會自動載入）
legacy/redmine/          Redmine 工單時代的角色、技能、協議、Python 模組與測試（已停用、不載入，說明與還原方法見其 README）
tests/                   python3 -m unittest discover -s tests
```

## 工作流程

### A. 新建專案（`/kickoff`、`/module`）

1. 需求釐清 → `requirements.md`
2. 架構（`architect`）→ `architecture/overview.md`，**使用者確認後**再往下
3. 模組切分（`pm`，每模組一位）→ 各模組 `spec.md`
4. 設計（`uiux-designer`）→ 5. 開發（`engineer`，任務 worktree）→ 6. QA（含安全檢查；高風險模組加派資安）→ 7. 驗收（`project-manager`）

### B. 接手既有專案（`/onboard`、`/assess`、`/improve`）

1. **`/onboard`**：讀專案現況，建立 `profile.md`、`engineer-rules.md`（含專案自有開發模式）、`status.md`，並在 `config/console.toml` 登錄專案、加入權限目錄。
2. **`/assess`**（四個面向可平行，唯讀）：architect／qa／security／uiux 各出報告，`project-manager` 彙整 `SUMMARY.md`、`pm` 轉成 `backlog.md`。**到這裡停下，由使用者挑要做哪些項目**（唯一例外：看板的「自動派工」，使用者已授權由專案管理員從 backlog 待辦直接挑，見 `docs/maintenance.md`）。
3. **改善**：單項用 `/improve <專案> <ID>`；多項、要平行開發用 `/dispatch <專案> <ID,ID,…>`。
4. 發現新問題 → 加進 backlog，不在改善過程中順手擴大範圍。

### C. 快速開發（`/dispatch`）

```
/dispatch <專案> <需求 | backlog ID…>
  → project-manager 切分（工作包、檔案範圍、依賴、規格編號、批次）→ 使用者確認計畫
  → 每批：bin/console wt add（每任務一個 worktree）→ 規劃角色 → engineer（批內平行）
        → qa-engineer（含安全檢查，最多 2 輪；標「資安加派」才加 security-reviewer）→ project-manager 更新進度
  → 回報待驗收的分支（t-<任務>），由使用者 commit、合併
```

低、中風險的發現不停下來；只有協議第 4 節的升級條件才主動打擾使用者。

## 共通規則

- **單一事實來源**：進度只記在 `projects/<專案>/status.md`＋`backlog.md`；規格只記在規格文件。不要在多處重複。
- 角色之間只透過文件交接：開工前先讀上游文件，交付時把結果寫回文件並在回覆中摘要。
- 規格不清楚就回報「待釐清事項」；專案 skills 若有「等使用者回答」的硬停點，角色回報問題原文給調度者，問完使用者再帶答案派回。
- 專案端技能在中控台不會自動載入，角色是 Read 它們的 `SKILL.md` 當程序依據（見協議第 6 節）。
- **平行規則**：只有檔案範圍不重疊、無依賴的任務同批；批內上限 3；同一時間只允許一個任務動 model／migration；docker compose 一律加 `COMPOSE_PROJECT_NAME=<任務>` 隔離。
- **額度保護**（協議第 5 節）：高耗階段前跑 `bin/console usage --guard`，回 3 就暫停（看板的派工與接續處理同樣被擋）；解除只有 `bin/console ui` 的按鈕，不要新增讓角色能解除的指令。

## 已註冊專案

| 專案 | Repo | 類型 | 開發模式 | 工作區 |
|---|---|---|---|---|
| teacher-crm | `/home/user/web/teacher-crm` | 既有（Django） | skills：規格驅動 + TDD | [projects/teacher-crm/](projects/teacher-crm/profile.md) |

登錄新專案：`/onboard <路徑>`（會同時在 `config/console.toml` 加 `[projects.<別名>]`，`branch_prefix = "t-"`）。

## 常用指令

```bash
bin/console projects                          # 已登錄專案
bin/console wt add <任務> -p <專案>             # 任務 worktree（分支 t-<任務>，起點 origin/<base_branch>；已有分支就沿用）
bin/console wt list | wt fingerprint <任務> -p <專案>
bin/console env sync <任務> -p <專案>           # 複製專案環境檔進 worktree（不覆蓋已存在的）
bin/console wt rm <任務> -p <專案>              # 有未提交變更時拒絕；分支保留
bin/console site add|test|rm <任務> -p <專案>   # 預覽站（command driver）：開／測／停（rm --drop-db 連資料與映像檔一起清）
bin/console site list
bin/console usage --guard                     # 額度檢查（0 可、3 暫停）
python3 -m unittest discover -s tests
```

## 預覽站與維護注意

- 預覽站（`site.py`，driver = "command"）：用 `bin/console site add|test|rm`；指令寫在 `config/console.toml` 的 `[projects.<別名>.site]`，不需要改程式；角色不得自己跑 `docker compose down`，要停站走 `bin/console site rm`。細節見 `docs/maintenance.md`「預覽站」。
- 改動用量監控、看板、預覽站、建 worktree、遮蔽前，**先 Read `docs/maintenance.md` 對應條目**。硬規則：遮蔽（`mask.py`）不得放寬；用量監控不讀不存對話內容；看板只綁 127.0.0.1、不自動開瀏覽器；worktree 已有 `<branch_prefix><任務>` 分支就沿用，不用 `git log` 抓提交主旨；路徑變數別在 zsh 取名 `path`。
