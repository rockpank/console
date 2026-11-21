---
verdict: 通過
round: 1
---

# B-032 QA 第 1 輪

worktree `worktrees/B-032/teacher-crm`（分支 t-B-032，基底 03d1f37）。docker compose run --rm，COMPOSE_PROJECT_NAME=b-032-qa，假 JOTFORM_API_KEY 只在命令列，序列執行。

## 結果
| 項目 | 指令／範圍 | 結果 |
|---|---|---|
| 新測試 | pytest tests/db/test_line_outbound_paths.py tests/db/test_line_binding_edge_cases.py | 33 passed（29 情境，含 parametrize 展開） |
| 全套 | pytest tests/unit tests/db | 1267 passed、0 failed，1 個既有 RuntimeWarning（naive datetime，非本任務） |
| ruff check | `src tests` | All checks passed |
| ruff format --check | `src tests` | 218 files already formatted |
| ruff（新檔） | 兩個新測試檔 | check 與 format 皆通過 |
| codemap-check | `python3 scripts/code_map.py check`（Makefile 的 CODEMAP；主機無 make） | OK，最新（293 檔） |

## 22 errors／6 檔的範圍差異
- `ruff check .` 為 22 errors，全部在 `.claude/skills/_shared/`（test_validate_artifacts.py 16、validate_artifacts.py 6）。
- `ruff format --check .` 為 6 檔：上述 2 檔、`.claude/skills/data-plan/templates/models.example.md`、`specs/002、003、004/system-analyze/models.md`。
- 這些檔案皆為版控中的檔案，本任務對 `.claude/` 無 diff，且 specs 下只新增 031 目錄。故在 03d1f37 上本來就存在，不是 B-032 造成。
- 範圍不同：工程師用的 `ruff check src tests` 不含 `.claude/`、`specs/`，所以乾淨；全專案 `.` 才有這 22／6。我沒有另外 checkout master 重跑，是依「基底相同且該些檔案無變更」推定。
- 建議另開 backlog 項處理：清掉這批，或在 ruff 設定排除 `.claude/`。

## 範圍確認
- 變更只有：兩個新測試檔、`specs/031-*/`、`docs/code_map/*`（六檔，為 codemap 更新）。`src/`、tests/conftest.py、tests/db/line_helpers.py 與既有輔助檔 git diff 皆為空。
- 兩個新檔無 skip／xfail（grep 僅命中函式名 `skipped`）。

## 29 情境對照
測試註解標有 BE-SVC-01 至 17、BE-API-01 至 12，去重共 29，與 spec 一一對應，無缺漏。BE-SVC-13（ineligible projects）、BE-API-04（缺簽章／錯簽章）、BE-API-11 為 parametrize，故 29 情境展開成 33 筆。

## 變異驗證（暫時破壞 src，驗完以 `git checkout -- <該檔>` 還原，git status 與原先相同）
1. `notifications.py` 的 MAX_ATTEMPTS 3 改 4，並停用 `if error.quota:` 分支：BE-SVC-01 與 BE-SVC-11 轉紅（2 failed、14 passed）。
2. `views.py:1177` 的 invalid body 狀態 400 改 200：BE-API-01 與 BE-API-02 轉紅（2 failed、15 passed）。
斷言對行為敏感，非空轉。

## 缺陷
無。

## 結論
通過。新測試 29 情境全覆蓋且通過、全套無回歸、src 未動、codemap 最新、新檔 lint 與格式乾淨。

## 備註
全專案 ruff 的既有 22 errors／6 檔屬 B-032 以外的既有問題。

工具呼叫：16／35
