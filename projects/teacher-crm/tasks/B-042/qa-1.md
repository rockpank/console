verdict: 通過

# B-042 QA 第 1 輪

環境：worktree worktrees/B-042/teacher-crm，COMPOSE_PROJECT_NAME=b-042-qa，JOTFORM_API_KEY=fake；未 down、未跑 integration、未讀 .env。

## 實測結果
| 項目 | 結果 |
|---|---|
| tests/db/test_double_submit_guard.py + test_jotform_sync_command.py | 16 passed |
| 全套 pytest tests/unit tests/db | 908 passed, 0 failed (201s) |
| ruff check / ruff format --check | 通過（189 檔已格式化） |
| scripts/code_map.py check | OK 最新 |

## 工程師回報的 2 個失敗
test_a_renamed_question_is_found_again_and_the_write_is_retried_once 與 test_when_the_session_question_cannot_be_found_again_the_form_waits_for_the_admin：本輪在含本變更的狀態下，單檔與全套各重跑皆通過，無法重現。本變更只動 base.html（加 script）與新增測試，未碰 jotform 同步程式碼，diff 與這 2 個測試無關。判定：非本變更造成；疑似間歇性（flaky）或工程師當次環境差異（如未提供 JOTFORM_API_KEY），根因未驗證。因無法重現，也未能在不含本變更的狀態下比對（未做，標「未驗證」）。建議列入 backlog 觀察 flaky。

## 驗收對應（quickfix.md）
| 預期行為 | 對應 | 狀態 |
|---|---|---|
| 1 送出後停用並顯示「處理中…」、事件委派、無 JS 照常送出 | 測試檢查頁面含 data-submit-guard、「處理中…」、addEventListener("submit")、button[type="submit"]（payments 頁、Jotform 設定頁）；diff 為 base.html 單一委派 script，未改樣板 | 靜態內容已測；實際瀏覽器停用／連按只送一次：未自動化 |
| 2 驗證失敗頁／上一頁恢復 | 驗證失敗頁無 disabled 按鈕且含 pageshow（已測）；pageshow persisted 還原邏輯存在於 diff（內容測試） | bfcache 還原實際行為：未自動化 |
| 3 重複 POST 冪等 | test_duplicate_confirm_payment_post_yields_single_result 等（含在 16 passed） | 通過 |
| backlog B-042：防連點與處理中狀態、後端冪等 | 同上 | 對應 |

## 缺陷
無。

## 觀察（低）
- script 以 setTimeout(0) 延後停用按鈕，以保留按鈕 name/value；form.dataset.submitting 同時阻擋第二次 submit 事件，邏輯合理。瀏覽器人工驗收需覆蓋：立即同步、確認入帳、退款、確認付款方式連點，及驗證失敗後上一頁。
