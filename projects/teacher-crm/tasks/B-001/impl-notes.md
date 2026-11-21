---
status: done
tests: 通過（997 passed、0 failed；覆蓋率 97%）
---

# B-001 impl-notes（specs/005-secure-config-defaults，T001～T093 全勾）

Worktree：`/home/user/web/console/worktrees/B-001/teacher-crm/`（分支 t-B-001，未 commit）。

## 對先前未提交變更的核對（沿用自先前寫入者，經核對）
- 來源：實為本任務前一輪工程師（T001～T068）的產物，impl-notes 舊版已記錄；本輪以 git diff 逐檔核對：僅在 work-plan 範圍內（外加 tests/unit/conftest.py，已由 PM 補列）、無真實值或金鑰（測試金鑰皆為可辨識假值）、`test_fake_checkout.py` 無刪除的 assert、無 skip／xfail。
- 重新驗證：接手時全套 `pytest tests/unit tests/db` = 989 passed、1 failed（唯一紅燈是 T068 刻意留下的 BE-SVC-20 RED），與舊版紀錄一致；無被打斷的半成品。
- 偏離（沿用舊紀錄）：T001～T068 的 RED／GREEN／REFACTOR 以「相鄰切片批次」執行，未逐切片各跑一次；BE-SVC-02～07、09 首次即綠，以變異自證補強（表見下）。本輪 T069～T092 已逐切片先紅後綠（回歸鎖定者見變異表）。

## 本輪完成（T069～T093）
- US3：`compose.yaml` app 加 `env_file: &app-env-file [.env]`、scheduler 以 `*app-env-file` 共用；scheduler command 改 `python src/manage.py run_scheduler`（BE-SVC-20／21／22）。
- US4：`ci.yml` test job 與 `external.yml` integration job 加 job 層級假值 env（`ci-fake-` 前綴、DEBUG／假金流 0；無 `secrets.`）（BE-SVC-23／24）；`.env.example` 全部變數加說明、新增 `DJANGO_CSRF_TRUSTED_ORIGINS`（空）、保留既有 11 變數與本機值（BE-SVC-25／26／27）。
- 測試：`test_compose_scheduler.py`（+3）、`test_ci_workflows.py`（+2）、`test_env_example.py`（+3）。
- 4 個 Gate：T042、T067、T077、T093 皆已執行（見下）。

## RED 證據（本輪）
- BE-SVC-20：`env_file` 缺（AssertionError）→ T069 後綠。
- BE-SVC-21：`['python','manage.py',…] != ['python','src/manage.py',…]` → T075 後綠。
- BE-SVC-23／24：2 failed（env 無假值）→ 改 workflow 後 12 passed。
- BE-SVC-25：1 failed（無 `DJANGO_CSRF_TRUSTED_ORIGINS`／無註解；中途一次因註解寫「相同」而非「不同」失敗，已改範例檔註解，未改測試）→ 3 passed。

## 回歸鎖定變異自證（皆已還原，已 diff 確認）
| 案例 | 暫時變異 | 結果 |
|---|---|---|
| BE-SVC-22（本輪） | compose app environment 加 `DJANGO_DEBUG: "0"` | 1 failed |
| BE-SVC-26（本輪） | 公開值標記移除 `changeme` | 1 failed |
| BE-SVC-27（本輪） | 移除除錯豁免 | 1 failed |
| BE-SVC-06／07／09／11／13／17／18／19／08（前一輪，沿用紀錄） | 移除豁免／只回第一則／加標記／strip／推導式改 upper／移除 `[::1]`／只傳兩把金鑰／加入假金流阻擋／訊息附值 | 各 1～2 failed |

## Gate 結果（實際執行；只記結束碼與變數名稱）
- JOURNEY-01：A（兩把金鑰清空 `manage.py check`）rc=1，一次列出兩變數並提示 `.env.example`；B（清空簽章金鑰跑 pytest tests/unit）rc=1，指名 `DJANGO_SECRET_KEY`，未執行任何測試；C（不覆寫，用 worktree 的 `.env`，內容未讀）rc=0。
- JOURNEY-02：A（debug=1＋對外網域）、B（`*`）rc=1，指名 `DJANGO_DEBUG` 與 `DJANGO_ALLOWED_HOSTS`、不含主機名稱；C（debug=1＋localhost,127.0.0.1）rc=0。
- JOURNEY-03：A `run_scheduler --help` rc=0 且為說明；B scheduler `check` rc=0；C app 產生付款權杖、scheduler 解回 `42`；D app 加密、scheduler 解回假明文；E 兩種缺金鑰 rc=1，指名被清空的變數、無排程輸出。未 `up`／`config`／`down`。
- JOURNEY-04：見下。`git diff -- tests` 被刪除的 `assert` 行 0、新增 skip／xfail 0。

## 品質關卡（實際輸出）
- 基線 T001（4675d95）：903 passed；ruff 通過；code map OK。
- `pytest tests/unit tests/db --cov=src`（`JOTFORM_API_KEY` 假值，其餘走 `.env`）：**997 passed**，覆蓋率 **97%**（TOTAL 4181 stmts／107 miss）。測試數 ≥ 903 基線＋新增。
- `ruff check src tests`：All checks passed；`ruff format --check`：192 files already formatted。tests/unit/conftest.py 無 >100 字元行、ruff 未報 E501（任務所述 E501 未出現）；本輪僅修了新增檔兩處 import 排序（`ruff --fix`）。
- `manage.py check`：no issues；`makemigrations --check --dry-run`：No changes detected。
- `python3 scripts/code_map.py update` → `check`：OK（267 檔，tree 706d99dbf5d7）；`docs/code_map/` 7 檔由指令更新。
- `validate_artifacts.py all --package 005-secure-config-defaults`：7 份全 OK。
- 以 `make` 等價指令執行（主機無 make）；compose 專案名 `b-001`（小寫）。`make test-integration` 未執行（需授權）。

## 變更檔案（未 commit）
- 修改：`.env.example`、`.github/workflows/ci.yml`、`.github/workflows/external.yml`、`compose.yaml`、`src/config/settings.py`、`src/crm/crypto.py`、`tests/conftest.py`、`tests/db/conftest.py`、`tests/db/test_fake_checkout.py`、`tests/unit/conftest.py`、`tests/unit/test_ci_workflows.py`、`tests/unit/test_compose_scheduler.py`、`tests/unit/test_crypto.py`、`docs/code_map/{INDEX.md,manifest.json,modules/src.config.md,src.crm.md,tests.db.md,tests.md,tests.unit.md}`、`specs/005-secure-config-defaults/spec.md`（PM 回寫，非本角色）
- 新增：`src/config/startup_checks.py`、`tests/unit/{test_startup_checks,test_settings_loading,test_env_example}.py`、`specs/005-secure-config-defaults/{tasks,testplan,analyze-report}.md`（規劃產物；tasks.md 勾選由本角色回寫）

## 假設與風險
- 公開值標記：`changeme`、`devinsecure`、`djangoinsecure`（黑名單，不證明強度）。
- `DJANGO_DEBUG` 預設改為 0；只靠預設、沒有 `.env` 的既有流程現在會因缺金鑰在載入設定時失敗（本項目要的行為）。`.env` 現在是 compose 必要檔（沒有就連 lint 都跑不起來）；使用者需知會團隊。
- worktree `.env` 未讀取；JOURNEY C 類操作 rc=0 間接顯示其內容合規。
- 預覽站、CI 雲端實際執行未驗證（不 push）。
- 需調度者轉交：合併時 `docs/code_map/` 衝突由合併者重跑 `make codemap`。
