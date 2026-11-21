---
verdict: 失敗
task: B-026
reviewer: qa-engineer
round: 2
---

# QA 報告 B-026 第 2 輪（資安 M-1／M-2 修正後重驗）

範圍：`worktrees/B-026/teacher-crm` 相對 origin/master 的 `src/crm/attendance.py`、`src/crm/orders.py`、`tests/db/test_concurrent_duplicate_friendly_error.py`、`specs/045-*`。未修改 worktree 內任何檔案。破壞性實測在 scratchpad 的複本（`.env` 以 `.env.example` 代替，未讀 .env）。

## 結論
產品行為（M-1／M-2 修正與原 3 個預期行為）全部驗證通過，品質關卡全綠；但新增測試中有一條修正路徑（現場報名捕捉 `ConcurrentOrderError`）**沒有任何測試能偵測退化**，覆蓋率也顯示該行未執行。依任務規則列缺陷（中），verdict 判「失敗」，請工程師補一個測試（見 D-1）後再驗。

## (1) 品質關卡（COMPOSE_PROJECT_NAME=b-026-qa，JOTFORM_API_KEY=fake）

| 關卡 | 結果 |
|---|---|
| ruff check src tests | All checks passed |
| ruff format --check src tests | 223 files already formatted |
| manage.py check | no issues |
| makemigrations --check --dry-run | No changes detected |
| pytest tests/unit tests/db --cov=src --cov-branch --cov-fail-under=95 | **1307 passed**，1 warning，342 秒；**總覆蓋率 98.17%**（門檻 95% 達標） |
| 個別檔案 | orders.py 100%（含分支）；**attendance.py 99%，缺第 167 行** |
| 併發測試檔重跑 3 次 | 13 passed x 3，無不穩定 |

attendance.py:167 即 `except ConcurrentOrderError` 區塊內的 `raise AttendanceError(CONCURRENT_DUPLICATE_MESSAGE) from exc`（第 1 輪是 100%，此輪因 M-1 修正新增而未被執行）。P-1 因給了假值未出現。codemap-check 未執行（任務範圍外）。

## (3) M-1／M-2 行為確認

| 項目 | 對應測試 | 結果 |
|---|---|---|
| 非併發 OrderError（專案不一致）在現場報名維持原訊息、型別仍為 OrderError、不是 AttendanceError、無日誌、無殘留學員 | test_walk_in_keeps_non_concurrent_order_error | 通過 |
| 已取消訂單 OrderError 維持原訊息 | test_walk_in_keeps_existing_active_order_error_for_cancelled_or_duplicate（後半） | 通過 |
| order_no 撞號（crm_order_order_no_key）重新拋出 IntegrityError、無日誌、無殘留訂單 | test_unrelated_integrity_error_is_reraised_in_create_order | 通過 |
| 不在白名單的 IntegrityError 在 register_walk_in／check_in_early 重新拋出 | ..._in_attendance[walk_in／early] | 通過 |
| 已知唯一約束衝突仍回友善訊息（建單 OrderError、現場報名／提前報到 AttendanceError，含「重新整理」） | 3 個併發測試（真實雙執行緒、真實 PostgreSQL） | 通過 |
| 日誌：恰 1 筆、含 operation／constraint／project id、不含姓名、電話、金額 | test_concurrent_loss_logs_constraint_without_personal_data | 通過（但見 D-2 的限度） |

## (4) 原 3 個預期行為
建單、現場報名（參數化 2 種起點）、提前報到的併發測試與 3 個序列測試（原訊息不變）皆綠；全套 1307 測試通過，成功路徑未變。**通過**。

## (2) 6 個後補測試的退化偵測（在 scratchpad 複本上破壞後執行該測試檔，13 個測試）

| 破壞（模擬拿掉修正） | 結果 | 抓到的測試 |
|---|---|---|
| A：register_walk_in 改回 `except OrderError`（捕捉所有 OrderError） | 紅 | test_walk_in_keeps_non_concurrent_order_error（實測，OrderError 被轉成 AttendanceError） |
| B：is_concurrent_duplicate 拿掉白名單（任何 IntegrityError 都轉友善） | 紅 | test_unrelated_integrity_error_is_reraised_in_create_order（實測，且在 attendance 兩個參數化也紅，見 F、G） |
| F：只拿掉 register_walk_in 的白名單判斷 | 紅 | ..._in_attendance[walk_in]（實測） |
| G：只拿掉 check_in_early 的白名單判斷 | 紅 | ..._in_attendance[early]（實測） |
| C：日誌加上 str(exc)（psycopg 訊息含電話、值） | 紅 | test_concurrent_loss_logs_...（實測，電話／姓名出現在日誌） |
| H：日誌加入金額 1500 | 紅 | 同上（實測） |
| D：拿掉日誌 | 紅 | 同上，`len(records)==1` 失敗（實測） |
| J：白名單漏掉 unique_active_order_per_student_product | 紅 | test_concurrent_create_order_loses...（實測） |
| E：create_order 落敗改拋一般 OrderError（不是 ConcurrentOrderError） | **仍綠（13 passed）** | 無 |
| I：拿掉 register_walk_in 的 `except ConcurrentOrderError` 區塊 | **仍綠（13 passed）** | 無 |

六個後補測試各自都能抓到它對應的退化（A、B、F、G、C/H/D 皆實測轉紅）。第 6 個「test_walk_in_keeps_existing_active_order_error_for_cancelled_or_duplicate」後半與 test_walk_in_keeps_non_concurrent_order_error 效果重疊、前半與序列建單測試重複，價值低但不是缺陷。

## 缺陷清單

### D-1（中）ConcurrentOrderError → AttendanceError 的轉換路徑無測試
位置：src/crm/attendance.py:166-168（`except ConcurrentOrderError`）與 orders.py 的 `ConcurrentOrderError` 子類。
證據：破壞 E、I 皆不會讓任何測試轉紅，覆蓋率顯示 attendance.py:167 未執行。現場報名併發測試中，落敗方是在 Student／Registration 的唯一約束就被擋（IntegrityError 路徑），從未走到 create_order 的併發落敗；而建單併發測試只斷言 `isinstance(..., OrderError)`，無法分辨一般 OrderError 與 ConcurrentOrderError。因此若有人把該 except 拿掉或讓 create_order 改拋一般 OrderError，「現場報名時建單輸給併發方，回友善 AttendanceError」這條行為會無聲退化（變回原始 OrderError，訊息雖友善但型別不符，views 以 AttendanceError 捕捉時會變 500）。
重現：見上表 E、I。
建議補測（成本低）：用 monkeypatch 讓 `attendance_module.ensure_intro_order` 拋 `ConcurrentOrderError("x")`，斷言 register_walk_in 拋 AttendanceError 且含「重新整理」、學員未殘留；另在建單併發測試加 `assert isinstance(errors[0], ConcurrentOrderError)`。補完後覆蓋率 attendance.py 應回到 100%。

### D-2（低，記錄）日誌個資測試只涵蓋 register_walk_in 的一種競態
該測試觸發的是 unique_student_per_project（學員建立）路徑；建單／提前報到的日誌格式共用同一個 is_concurrent_duplicate，退化偵測已由破壞 C/H/D 證明有效，故僅記錄。

### 流程事項（低）
工程師自承測試後補、無紅燈紀錄，屬 TDD 流程違規，已無法補救；以上實測確認 6 個後補測試中，5 個類別的退化能被抓到（見表），僅 D-1 的路徑沒有測試。

## 規格疑義／資安
無新增。M-3（Jotform order_no 衝突）此輪行為：order_no 撞號現在重新拋出原 IntegrityError（與修正前一致），已由測試確認，M-3 的行為改變疑慮已消除。

## 修復後回歸
工程師補 D-1 測試後，需重跑：concurrent 測試檔（確認 E、I 破壞會轉紅）、ruff、全套覆蓋率（attendance.py 應 100%）。
