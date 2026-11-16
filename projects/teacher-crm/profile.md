# 專案設定：teacher-crm

## 基本資料

- 名稱：teacher-crm（銷講課程行政系統）
- 類型：既有專案（接手）
- Repo 路徑：`/Users/Park/Site/teacher-crm`
- 版控：git，分支 `master`；2026-11-13 登錄時工作樹有 12 項未提交變更（見「已知狀況」）
- 登錄日期：2026-11-13

## 技術棧

Python 3.12、Django 5.2 LTS、PostgreSQL 16、純 Django template（不用 DRF 或前端框架）、pytest + pytest-django + pytest-cov、ruff、Docker Compose。排程用 management command（`run_scheduler`），無佇列系統。外部整合：金流（ECPay、NewebPay）、LINE、Jotform。原始碼 `src/`（`config`、`crm`），測試 `tests/{unit,db,integration}`。

## 專案自有文件與規範

- **憲法**：`specs/constitution.md`（v1.0.0，10 條 MUST + 技術基線 + 流程關卡）。**優先於中控台預設與各 skill 預設。**
- **規格套件**：`specs/NNN-*/`（目前 001–004），另有 `specs/SITEMAP.md`、`specs/TEST_LIST.md`、`specs/TDD_PROGRESS.md`
- **程式碼地圖**：`docs/code_map/`（`INDEX.md` → `modules/*.md`；`routes.md`、`models.md`、`templates.md`）。由 `scripts/code_map.py` 產生，**不得手改**，也不需讀 `manifest.json`。
- **專案 CLAUDE.md**：`/Users/Park/Site/teacher-crm/CLAUDE.md`
- CI：`.github/workflows/ci.yml`、`external.yml`

## 開發模式

- `dev_mode`：**skills**（規格驅動開發 + TDD）
- Skills 位置：`/Users/Park/Site/teacher-crm/.agents/skills/`（符號連結到 `.claude/skills/`），總覽見其 `README.md`；共用規則在 `_shared/`（`讀取憲法.md`、`委派約定.md`、`validate_artifacts.py`）
- 這些 skill 都是 `disable-model-invocation: true`，只在 teacher-crm 專案內可用斜線指令啟動。**在中控台內，角色以「讀取 `SKILL.md` 與 `RULES.md`，並在本次任務內依 SOP 執行」的方式使用**（對應 `委派約定.md` 的 DELEGATE 定義）。
- 路線判準：

| 路線 | 何時用 | 順序 |
|---|---|---|
| 完整路線 | 新功能；新增 model、API、頁面、外部整合、排程；跨多個故事 | specify → system-analyze → testplan → tasks →（analyze）→ implement |
| 快速路線 | 單一行為的 bug 修正或小改動，**且不改 model**（`/quickfix` 會判資格，不符即轉完整路線） | quickfix → implement |

- 產物位置：`specs/<NNN-名稱>/`（下一個編號從 `005` 起，依序遞增）
- 工程規則：`engineer-rules.md`（同目錄）

## 角色對應

| 步驟／skill | 中控台角色 | 產物 |
|---|---|---|
| `/specify`、`/clarify` | `pm` | `specs/<pkg>/spec.md`、`clarify-log.md` |
| `/quickfix` | `pm` | `specs/<pkg>/quickfix.md`、`tasks.md` |
| `/system-analyze`（含 technical-research、data-plan、api-plan、integration-plan） | `architect` | `specs/<pkg>/plan.md`、`system-analyze/` |
| `/ui-plan` | `uiux-designer` | `specs/<pkg>/system-analyze/ui/` |
| `/testplan` | `qa-engineer` | `specs/<pkg>/testplan.md` |
| `/tasks`、`/analyze` | `pm` | `specs/<pkg>/tasks.md`、`analyze-report.md` |
| `/implement`（自動載入 `/tdd`） | `engineer` | 程式、測試、勾選後的 `tasks.md` |
| 資安審查 | `security-reviewer` | `projects/teacher-crm/` 下報告 |
| 交付驗證 | `qa-engineer` | `projects/teacher-crm/` 下報告 |

`/system-analyze` 依 plan 自動委派 ui-plan；在中控台內，architect 做到 ui-plan 時**跳過並回報**，由調度者改派 `uiux-designer` 執行，完成後再繼續。`/clarify` 等「等使用者回答」的硬停點，由當前角色回報調度者，調度者問使用者後帶答案再派回。

## 指令（一律在 repo 根目錄執行：`cd /Users/Park/Site/teacher-crm && make …`）

| 用途 | 指令 | 備註 |
|---|---|---|
| 純邏輯單元測試 | `make test-fast` | 不啟動資料庫 |
| 單元 + 資料庫測試 | `make test` | 需 Docker（PostgreSQL） |
| 外部服務測試 | `make test-integration` | **需使用者授權**，會連真實外部服務 |
| Lint | `make lint` | ruff check + format --check |
| 格式化 | `make format` | |
| 覆蓋率 | `make coverage` | CI 門檻 `--cov-fail-under=95` |
| 框架指令 | `make manage cmd="check"`、`make manage cmd="makemigrations --check --dry-run"` | skill 內寫的 `python manage.py …` 一律改用這個 |
| 程式碼地圖檢查／更新 | `make codemap-check`／`make codemap` | |
| 驗證 spec 產物 | `python .agents/skills/_shared/validate_artifacts.py all --package <pkg>` | 只需標準函式庫，可在主機執行 |

## 品質關卡（合併／交付前全部要過）

`make lint`、`make test`、`make manage cmd="check"`、`make manage cmd="makemigrations --check --dry-run"`、覆蓋率 ≥ 95%、`make codemap-check` 無 STALE。

## 禁區

- **`.env`**：不得讀取、列印、複製或修改（含機密）。只可參考 `.env.example`。
- 不得自行執行：`git push`、`docker compose down`、`make test-integration`、任何會連真實金流／LINE／Jotform 的指令。
- 不得手改 `docs/code_map/` 內任何檔案。
- 不得讀取 `.pytest_cache/`、`.ruff_cache/`、`.coverage`、`docs/code_map/manifest.json`（雜訊，無資訊）。

## 已知狀況（2026-11-13 登錄時）

- **2026-11-13 更新**：登錄時記錄的 12 項未提交變更（004 Jotform 報名付款收尾）已由使用者提交（`25cb607`、`606e744`、`eb0a518`），評估期間工作樹乾淨。（原則不變：之後若再出現與任務無關的未提交變更，任何角色都不得動，也不得 stash／reset。）
- **部署現況（使用者 2026-11-13 回覆 U1）**：尚無正式環境；系統「曾用過」（以預設設定運作）。曾透過 **ngrok** 對外網開放；使用者表示**目前沒有**（真實金流／LINE 憑證與真實學員資料）——調度者解讀為「目前環境中沒有」，是否「從來沒有」未確認。Jotform 整合有實際連線過（commit `606e744` 時區修正），Jotform API 金鑰與 webhook 密鑰可能是真實的。
- 現況評估已於 2026-11-13 完成，報告在 `projects/teacher-crm/assessment/`；實測基線見 `quality.md`（903 測試通過、覆蓋率 97%）。
- `specs/TDD_PROGRESS.md` 為舊版 TDD 流程的進度檔（2026-10-30 後未再更新），與現行 skills 流程不同，評估時視為歷史紀錄。
- `.agents/skills` 是指向 `.claude/skills` 的符號連結。
