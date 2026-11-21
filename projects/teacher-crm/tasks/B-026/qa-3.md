---
verdict: 通過
task: B-026
reviewer: qa-engineer
round: 3
---

# QA 報告 B-026 第 3 輪（D-1 補測試後窄範圍驗證）

未修改 worktree 任何檔案。破壞性實測在 scratchpad 複本（`.env` 以 `.env.example` 代替，未讀 .env；COMPOSE_PROJECT_NAME=b-026-qamut）。

## (1) 補的測試存在且在做事
- (a) `test_walk_in_converts_concurrent_order_error_to_attendance_error`：monkeypatch `attendance_module.ensure_intro_order` 拋 `ConcurrentOrderError("請重新整理")`，斷言 `register_walk_in` 拋 `AttendanceError` 且 match「重新整理」，並斷言未殘留學員。存在、有實質斷言。
- (b) `test_concurrent_create_order_loses_with_friendly_order_error` 有 `assert isinstance(errors[0], ConcurrentOrderError)`。存在。

## (2) 破壞實測（複本；複本的三個檔案先與 worktree `cmp` 一致）

| 破壞 | 結果 | 失敗的測試 |
|---|---|---|
| E：orders.py:131 改拋一般 `OrderError` | 紅（實測）：1 failed, 13 passed | test_concurrent_create_order_loses_with_friendly_order_error |
| I：拿掉 register_walk_in 的 `except ConcurrentOrderError` 區塊 | 紅（實測）：1 failed, 13 passed（ConcurrentOrderError 直接外洩） | test_walk_in_converts_concurrent_order_error_to_attendance_error |
| 還原後 | 綠（實測）：14 passed | — |

D-1 已關閉。

## (3) 品質關卡（COMPOSE_PROJECT_NAME=b-026-qa，JOTFORM_API_KEY=fake）

| 關卡 | 結果 |
|---|---|
| ruff check src tests | All checks passed |
| ruff format --check src tests | 223 files already formatted |
| manage.py check | no issues |
| makemigrations --check --dry-run | No changes detected |
| pytest tests/unit tests/db --cov=src --cov-branch --cov-fail-under=95 | **1308 passed**，1 warning，350 秒；**總覆蓋率 98.18%**（門檻 95% 達標） |
| attendance.py／orders.py | **皆 100%**（含分支，Miss 0）；attendance.py 已回到 100% |
| 併發測試檔重跑 3 次 | 14 passed x 3，無不穩定 |

P-1 因給假值未出現。codemap-check 不在範圍。

## (4) src 差異
`git diff origin/master --stat -- src`：僅 `src/crm/attendance.py`、`src/crm/orders.py`（121 增 53 刪），與第 1、2 輪一致，第 3 輪無新增產品碼變更；其餘未追蹤項目僅 specs/045-* 與測試檔。

## 缺陷
無新增。D-2（低，記錄）維持不變。流程事項（測試後補、無紅燈紀錄）無法補救，維持記錄。

## 結論
通過。
