---
verdict: 通過
---

# B-001 QA 第 1 輪（交付驗證）

環境：worktree `worktrees/B-001/teacher-crm/`（t-B-001，未 commit）；`docker compose run --rm`（make 等價），`COMPOSE_PROJECT_NAME=b-001-qa`；跑前確認無其他 pytest／compose run；假值以 `-e` 提供，未讀 `.env`、`config/env/**`；未 down。

## 獨立執行結果
| 項目 | 結果 |
|---|---|
| `pytest tests/unit tests/db --cov=src --cov-fail-under=95`（`-e JOTFORM_API_KEY=fake-qa-key`） | **997 passed**、0 failed、4181 stmts／107 miss，覆蓋率 **97.44%**（>= 95%；測試數 >= 基線 903） |
| `ruff check src tests` | All checks passed |
| `ruff format --check src tests` | 192 files already formatted |
| `manage.py check` | no issues |
| `makemigrations --check --dry-run` | No changes detected（無遷移） |
| `scripts/code_map.py check` | OK（267 檔，tree 706d99dbf5d7） |
| `validate_artifacts.py all --package 005-secure-config-defaults` | 7 份全 OK |

## 行為驗證
- 兩金鑰皆清空 `manage.py check`：rc=1，一次列出 `DJANGO_SECRET_KEY`、`FIELD_ENCRYPTION_KEY`，提示 `.env.example`，不含值。
- 清空 `DJANGO_SECRET_KEY` 跑 `pytest tests/unit`：以指名 `DJANGO_SECRET_KEY` 的 ImportError 失敗，未執行任何測試（尾端另有 pytest-django「could not find a Django project」附帶訊息，屬同一失敗的連帶輸出，不影響指名）。
- DEBUG=1＋`DJANGO_ALLOWED_HOSTS=example.test`：失敗，指名 `DJANGO_DEBUG`／`DJANGO_ALLOWED_HOSTS`；DEBUG=1＋`*`：同樣失敗。
- DEBUG=0＋`*`＋有效假金鑰：check 通過（符合規格：只限制 DEBUG 開啟時；非 DEBUG 下 `*` 的放行是既有行為，不屬本任務）。
- scheduler（US3 情境 2／SC-004）：compose 指令為 `python src/manage.py run_scheduler`，`run_scheduler --help` 在 app 容器 rc=0 顯示說明；app 與 scheduler 共用 `env_file: .env`；`environment` 不含受保護變數（BE-SVC-20／21／22 全綠）。未 `up` scheduler（避免發訊息）。
- 既有行為：`crypto.py` 金鑰推導（sha256→urlsafe_b64）不變，既有密文向量測試 BE-SVC-13 綠；付款 token `PAY_LINK_MAX_AGE = 30*24*60*60`，現有付款測試全綠；ALLOWED_HOSTS 預設為 `['localhost','127.0.0.1']`；CSRF 來源由 `SITE_BASE_URL` 推導為 `['https://qa.example.test']`（BE-SVC-11 亦綠）。
- 驗收 1-8 以對應測試（BE-SVC 系列）全綠＋上述實測判定；未逐條重寫對照表。

## 回歸鎖定變異（暫時破壞 → 還原，`git diff`／`status` 前後比對一致）
| 案例 | 破壞 | 結果 |
|---|---|---|
| BE-SVC-11 | settings 的 SECRET_KEY 加 `.strip()` | 1 failed |
| BE-SVC-13 | crypto 推導改 strip＋upper | 1 failed |
| BE-SVC-19 | 檢查函式加入「假金流開且非除錯」阻擋 | 1 failed |
| BE-SVC-22 | compose environment 加 `DJANGO_DEBUG` | 1 failed |

## 測試完整性
- `git diff -- tests`：7 檔 +199／−0，無被刪除的 assert；新增與修改的測試檔 grep 無 skip／xfail。`test_fake_checkout.py` 僅加 `pytestmark = usefixtures("fake_gateway_enabled")`（因假金流預設改為關閉，合理，非弱化）。

## 缺陷
無阻擋／高／中缺陷。

## 低風險備註
- worktree `.env` 的金鑰在 DEBUG=0 時被判為公開佔位值（check 失敗，僅見於清楚的變數名稱訊息）：符合設計，但使用者合併後需自行換成自產金鑰；`.env` 現為 compose 必要檔（impl-notes 已列）。
- `DJANGO_ALLOWED_HOSTS` 設為空字串時結果為 `['']`（既有行為，未變）。

## 未執行
- `make test-integration`（需授權）、CI 雲端實跑、預覽站（無畫面變更）、scheduler 實際 `up`（會發訊息）。
- JOURNEY-03 C／D（app 產生權杖由 scheduler 解回、跨容器加解密）未自行重做；以單元測試（BE-SVC-13／token 測試）與指令一致性替代。

## 結論
通過。
