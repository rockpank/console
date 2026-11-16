# teacher-crm 工程師規則

> 來源：`/Users/Park/Site/teacher-crm` 的 `specs/constitution.md` 與 `.agents/skills/`（規格驅動開發 + TDD）。
> 本檔是摘要與在中控台內的執行方式；**與原文有出入時以原文為準**（憲法 > skill 預設 > 本檔）。

## 0. 開工前（每次任務）

1. `cd /Users/Park/Site/teacher-crm && git status --short`：記下與本任務無關的未提交變更，**不得碰**（見 profile「已知狀況」）。
2. `make codemap-check`。出現 `STALE` → `make codemap` 後再開始（`docs/code_map/` 是產生物，更新由指令負責，不手改）。
3. 讀 `specs/constitution.md` **整份**，萃取與本任務相關的 MUST。
4. 找程式碼：`docs/code_map/INDEX.md` → 對應目錄的 `modules/*.md`（行號範圍）→ 用 Read 的 offset/limit 只讀需要的區段。網址看 `routes.md`、資料表看 `models.md`、樣板看 `templates.md`。
5. 建基線：跑與本任務相關的測試與 `make lint`，記錄原本就紅的項目。

## 1. 開發模式：規格驅動 + TDD（唯一允許的做法）

- 工程師負責 **`/implement`**（它自動載入 `/tdd`）。做法：讀 `/Users/Park/Site/teacher-crm/.agents/skills/implement/SKILL.md` 與 `RULES.md`，在本次任務內依 SOP 執行；遇到 `[TDD-*]` 任務再讀 `tdd/SKILL.md` 與 `RULES.md` 依 SOP 執行。
- **前置產物缺失就停**：`specs/<pkg>/tasks.md`（快速路線為 `quickfix.md` + `tasks.md`）必須存在，且 `analyze-report.md`（完整路線）無未處理的可修項。缺了就回報調度者派 `pm`／`architect`／`qa-engineer` 補，**工程師不自行補規格**。
- 以 `tasks.md` 為唯一執行控制平面：一次一個非切片 task 或一個切片鏈；不得跳步、跨切片、預做後續；驗證後立刻回寫 `[X]`；`[P]` 才可平行，且仍一次一個 `CASE_ID`。
- 每個切片：**RED/ALIGN → GREEN → REFACTOR**。先有失敗的測試（失敗原因要對），才寫最小的 production code；GREEN 不偷塞下一案例或額外抽象；REFACTOR 只做 behavior-preserving 整理並維持綠燈。不得改產品碼來製造紅燈。
- Setup／Foundational 任務直接實作；**model 變更**依序：改 `models.py` → `make manage cmd="makemigrations <app>"` → 檢視產生的 migration → `make migrate` → `make manage cmd="makemigrations --check --dry-run"` 必須乾淨。
- `[ACCEPTANCE-GATE]` 不走 `/tdd`，依 `implement/RULES.md` 跑 Journey 驗收（無 E2E 的純後端故事以串接的 API 測試組合驗收）。
- 「在本次任務內執行」代表**你自己做**，不要另開子代理跑切片；對使用者的「下一步」不寫，回報給調度者。
- 遇到可自行決策的缺口：依 task、規格與最小可逆原則決定，並在回報中揭露假設與風險。命中客觀停點（規格矛盾、需要使用者拍板、憲法衝突）才停下回報。

## 2. 憲法 MUST 摘要（逐條都要遵守）

1. **測試先行**：行為變更先有失敗的 pytest 測試。
2. **真實資料庫**：DB 測試用真實 PostgreSQL；**禁止 mock ORM、model、自家業務函式**。
3. **純邏輯隔離**：`crm/domain/` 不得匯入 Django、不得存取 DB；對應測試放 `tests/unit`，不需 DB 即可跑。
4. **專案完全隔離**：所有業務資料帶專案歸屬、查詢經專案範圍過濾、預設拒絕跨專案；**新功能必附「A 專案成員讀不到 B 專案資料」的測試**。
5. **權限在伺服器端判定**（admin、行政管理者、行政專員、講師）；不能只隱藏按鈕。
6. **系統為單一事實來源**：付款狀態、標籤、場次報名以本系統為準；外部服務只是輸入／輸出。
7. **外部服務先 fake**：先定義介面與 fake 實作，日常測試只用 fake；真實連線測試只放 `tests/integration`。
8. **金額用整數（新台幣元），禁止 float**；金流金鑰與 LINE 憑證加密儲存、畫面不回顯、不進版控、不寫日誌。
9. **外部通知可重送**：金流回報與 LINE webhook 必須驗簽，且重複收到同一則通知不得重複扣款、重複改狀態、重複發訊。
10. **對外發送前再檢查**：自動訊息在發送當下重新確認條件（例：已報名進階即停止追售）。

## 3. 技術基線與流程關卡

- Python 3.12、Django 5.2 LTS、PostgreSQL 16、純 Django template（**不使用 DRF 或前端框架**）、pytest 三層：`tests/unit`、`tests/db`、`tests/integration`。
- `USE_TZ = True`、時區 `Asia/Taipei`、語系 `zh-hant`。
- 排程與非同步：無佇列；以 management command 實作，由外部排程器呼叫，**必須可安全重跑**。
- **交易內不得同步呼叫外部服務**：需外部呼叫時在交易提交後執行，並記錄結果以便失敗重送。
- 有限資源（如場次人數上限）**必須用資料庫鎖**保護，避免超收。
- 資料庫存取走 ORM；用 raw SQL 必須在程式註解說明原因。
- 使用者可見文字沿用統一用語（例如「前端課」），不混用舊稱（如「銷講」）。
- 套件版本用相容範圍 `~=`；依賴變更需有理由。
- 風格：ruff，行寬 100（以 `pyproject.toml` 為準）。

## 4. 交付前驗證（全部通過才可回報完成）

```
cd /Users/Park/Site/teacher-crm
make lint
make test
make manage cmd="check"
make manage cmd="makemigrations --check --dry-run"
make coverage            # 覆蓋率 >= 95%
make codemap             # 改完程式後更新地圖；之後 make codemap-check 應無 STALE
python3 .agents/skills/_shared/validate_artifacts.py all --package <pkg>   # 有動 spec 產物時
```

回報必須貼**實際輸出摘要**（通過數、失敗數、覆蓋率），不得只寫「已通過」。

## 5. 平行與衝突規則

- 同一個 spec package 內**序列執行**。
- 不同 package 可平行，**前提是檔案範圍不重疊**。
- **同一時間只允許一位工程師改 `models.py`／migrations**（migration 編號會衝突）；有 model 變更的 package 排在前面，其餘等它完成再開工。
- 共用檔案（`settings.py`、`urls.py`、`views.py`、`models.py` 等）有衝突風險，調度者派工時要先排程。

## 6. 禁止事項

- 不讀、不印、不改 `.env`；不把任何金鑰、token、憑證寫入程式、測試、日誌或報告。
- 不手改 `docs/code_map/`。
- 不 `git push`、不 `docker compose down`、不 commit（除非調度者明確要求）；不跑 `make test-integration`。
- 不為了過測試而改測試或降低門檻、不加 `skip`／`xfail`；不 mock ORM／model／自家業務函式。
- 不改 `specs/constitution.md`（憲法修訂只能經 `/constitution` 並更新版本，由使用者決定）。
- 不碰工作樹中與本任務無關的未提交變更。

## 7. 回報格式

完成的 task ID／`CASE_ID`、變更檔案清單、紅燈與綠燈證據（測試指令與結果）、品質關卡實際輸出、假設與殘餘風險、需調度者轉交的事項（規格疑義、他人範圍的修改）。
