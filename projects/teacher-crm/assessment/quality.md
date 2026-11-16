# teacher-crm 品質健檢（實測基線）

- 日期：2026-11-13
- 角色：qa-engineer（品質健檢模式，唯讀；未改任何產品碼或測試碼）
- Repo：`/Users/Park/Site/teacher-crm`，分支 `master`，HEAD `eb0a518`
- 環境：Docker 可用（`docker info` 正常），PostgreSQL 16 容器 `teacher-crm-db-1` 執行中；所有指令經 `make`
- 工作樹狀態：**執行當下為乾淨**（`git status` 無變更）。profile 登錄時記載的 12 項未提交變更已在 `eb0a518`、`606e744`、`25cb607` 提交，因此本次所有結果都對應已提交的程式碼，沒有「疑似由未提交變更造成」的失敗。
- 未執行：`make test-integration`（依規定需使用者授權、會連真實外部服務）、未讀 `.env`。

## 1. 基線數據

| 指令 | 結果 | 備註 |
|---|---|---|
| `make test-fast` | **通過**：311 passed，2.9 秒 | 不啟動資料庫（`--no-deps`），證實 tests/unit 不需 DB |
| `make test` | **通過**：903 passed、0 failed、0 skipped、0 xfail，76 秒 | 單元 311 + 資料庫 592 |
| `make lint` | **通過** | ruff check 全過；188 個檔案格式正確 |
| `make manage cmd="check"` | **通過** | 0 issues |
| `make manage cmd="makemigrations --check --dry-run"` | **通過** | No changes detected |
| `make coverage` | **通過**：總覆蓋率 **97%**（4178 敘述、107 未覆蓋），903 passed | 門檻 95%（CI `--cov-fail-under=95`）；`make coverage` 本身不帶門檻，只有 CI 會擋 |
| `make codemap-check` | **通過** | code map 最新（tree 049b71d2dd3a，263 檔） |
| `validate_artifacts.py all`（001、003、004） | 通過，附警示 | 003、004 的 models 用 CASCADE 需確認有說明理由；004 integration-plan 有 3 個 `[NEEDS CLARIFICATION]` 未關閉（即三個「上線前以真實 Jotform 實測」項目） |
| `make test-integration` | **未執行** | 需使用者授權 |

**既有失敗：無。** 品質關卡（lint、test、check、makemigrations、覆蓋率 ≥95%、codemap）本機實測全數通過。

測試規模：定義 792 個測試函式，pytest 展開後 903 項（含 parametrize）；另有 tests/integration 2 項（僅綠燈 ECPay 測試站，未執行）。

### 覆蓋率未達 100% 的檔案（全部列出）

| 檔案 | 覆蓋 | 未覆蓋行 | 高風險區？ |
|---|---|---|---|
| gateways/newebpay.py | 92% | 100, 102-103, 111-112 | **是：金流 webhook 驗簽後的回報解析（金額、冪等的上游）** |
| gateways/ecpay.py | 96% | 98-99 | **是：同上，缺欄位／金額格式錯誤** |
| gateways/base.py、gateways/__init__.py | 90%、89% | base 36,39；init 26-27 | 低（抽象方法、不支援的供應商例外） |
| forms.py | 98% | 222,243,246,251,356 | **是：訂金／價格驗證（金額）、前端課唯一性、藍新 HashKey/IV 長度** |
| jotform/registration.py | 98% | 142, 165, 178 | **是：人工建單時專案沒有前端課費用、略過的並行防護（鎖後狀態已變）** |
| line/service.py | 94% | 30, 38, 94-95, 114 | 是：LINE 真實模式 client、webhook 事件、重新綁定停用中的帳號、手動綁定衝突 |
| line/notifications.py | 97% | 180, 236, 248, 278-281 | 是：對外發送（重試上限、無設定時重送、付款提醒的略過／失敗計數） |
| views.py | 98% | 243, 580, 582, 966, 1007-8, 1170-71, 1192-93, 1278, 1356-57, 1419, 1526, 1575 | 部分：LINE webhook 非法 body（1170-71）、假金流回報失敗（1007-8）、同步在無金鑰／無表單時（580-582）、略過已處理提交（1575） |
| jotform/client.py | 94% | 77,80,83,86（抽象方法）, 112, 224, 229-230 | 低～中：偽造提交時間解析（224, 229-230） |
| jotform/sync.py | 96% | 103-104, 116, 130 | 中：排程 job 的金鑰設定檢查與例外保護 |
| jotform/service.py | 96% | 23-25, 67 | 低（真實 client 建構）、中（選題 ChoiceError） |
| management/commands/process_finished_sessions、process_jotform_submissions、sync_jotform_forms、send_line_notifications | 84–95% | 皆為 `--date`／`--now` 格式錯誤的 CommandError 分支 | 中：排程指令的非法參數（排程類） |
| attendance.py | 97% | 21, 61, 72 | **是：21 為服務層「學員不屬於這個專案」防護（專案隔離）；61、72 為同日有開始時間的前後場次判斷** |
| access.py | 96% | 35, 81 | **是：權限橋接中 `to_domain_user` 為 None 時一律拒絕** |
| models.py | 95% | 多為 `__str__`、`is_active` 等屬性 | 低 |
| dashboard.py、context_processors.py、domain/line.py | 97–98% | 各 1 行 | 低 |

注意：**未啟用分支覆蓋率**（`pyproject.toml` 的 `[tool.coverage.run]` 沒有 `branch = true`）。97% 是行覆蓋；實際分支覆蓋未知，高風險區（權限、金額）的條件組合可能比數字顯示的更薄。

## 2. 憲法測試紀律檢查

| 項目 | 結果 | 證據 |
|---|---|---|
| 憲法 2：禁止 mock ORM／model／自家業務函式 | **大致符合，1 處例外** | 全 tests 無 `unittest.mock`／`MagicMock`／`mocker`；只用 `monkeypatch`。替身都在外部邊界（`crm.line.service.build_client`、`crm.jotform.service.build_client` 換成 fake 或注入傳輸層）、`getpass`、`_sleep`。**例外**：`tests/db/test_jotform_session_hooks.py:98` 以 `monkeypatch.setattr("crm.jotform.sync.sync_form", boom)` 取代自家業務函式 `sync_form` 來注入例外。這是故障注入而非替身行為，嚴格讀憲法屬灰色地帶，列為低嚴重度 |
| skip／xfail | **符合** | `tests/unit`、`tests/db` 沒有 skip/xfail/importorskip。唯一 `pytest.skip` 在 `tests/integration/test_ecpay_stage.py:32`（無法連線測試站時略過，屬合理）。`make test` 0 skipped |
| 每個功能有「A 專案讀不到 B 專案」測試（憲法 4） | **大部分有，列出缺口** | 見下表。tests/db 60+ 個檔案中，學員、場次、訂單、退款、標籤、改期、商品、金流設定、報表、LINE 通知、追售、Jotform 全套（設定、同步、提交、補處理、webhook）都有跨專案測試 |
| tests/unit 真的不需 DB | **符合** | `make test-fast` 用 `--no-deps` 在沒有資料庫容器下 311 項全過。`crm/domain/` 內沒有匯入 django 或 models（grep 無結果） |
| 憲法 3：domain 不匯入 Django | 符合 | 同上 grep |
| 憲法 8：金額整數、機密不回顯 | 符合（靜態檢查） | src 無 float／DecimalField／FloatField；有對應「不回顯憑證」測試（LINE、Jotform 金鑰、金流設定） |
| 憲法 7：外部服務先 fake、真實連線放 integration | 符合 | `FakeLineClient`、`FakeJotformClient`、`FakeGateway`；integration 只有 ECPay 測試站 2 項 |
| 憲法：資料庫鎖保護有限資源 | **有實作、測試偏弱** | `select_for_update` 用在改期目標場次、訂單、付款嘗試、Jotform 提交；但**並行測試只有 2 處**（Jotform 導向 vs 通知、排程諮詢鎖）。改期超收、付款通知同時重複送達都只以序列方式測 |
| 憲法 10：發送當下重新檢查 | 符合 | `test_follow_up_message_skips_and_stops_students_who_enrolled_meanwhile` 等 |
| 測試品質（無斷言測試） | 符合 | 792 個測試函式全部含 assert 或 raises；採 Arrange/Act/Assert 註解風格 |

### 跨專案隔離測試缺口（路由層級）

已確認有跨專案測試：students edit/delete、sessions list/edit/detail、registration remove、payments confirm/refund/cancel、products、gateway settings、manual tags、reschedule、reports、attendance（頁面、標記、提早到）、notifications retry、line binding、follow-ups、Jotform 全部路由、gateway notify（A 的簽章打 B 的網址被拒）。

**未找到跨專案測試的路由（以測試檔內容與路由對照，建議補測）：**

| 路由 | 風險 |
|---|---|
| `project_session_import`（匯入名單，tests/db/test_import_page.py 無任何第二專案） | 以 A 專案網址匯入到 B 專案的場次 |
| `project_session_delete` | 以 A 專案網址刪除 B 專案場次（`test_session_delete.py` 只有一個專案） |
| `project_attendance_walk_in`、`project_attendance_close` | 同頁其他路由有測，這兩個漏了（`test_attendance_of_other_project_returns_404` 只涵蓋頁面、標記、提早到） |
| `project_front_course`、`project_message_templates`、`project_line_settings` | 設定頁讀寫別專案資料（前兩者測試檔只有單一專案；LINE 設定頁僅測 admin 權限） |
| `line_webhook` | 只測「未知專案 404」與「簽章錯誤」；缺「A 專案 channel secret 簽的內容打到 B 專案被拒」（付款 webhook 有這種測試，LINE 沒有） |
| 服務層 `attendance._check_project`（attendance.py:21） | 覆蓋率顯示整個防護分支從未被執行 |

## 3. 需求 → 測試對照

說明：testplan 的案例編號（BE-API-01 等）沒有寫進測試名稱或註解，**追溯只能靠語意比對，不是機器可驗證**。下表為人工比對 specs 與 tests 的結果。

### 001 CI 品質自動化（spec 161 行、testplan 10 個案例）

| 範圍 | 對應測試 | 判斷 |
|---|---|---|
| BE-SVC-01～10（觸發、lint 同本機、關卡、PG16 無機密、併發與權限、快取、覆蓋率門檻、覆蓋率排除、external 只手動／定期、integration 只在 external） | `tests/unit/test_ci_workflows.py` 10 項逐一對應 | **完整**，且是純檔案結構測試 |
| 限制 | 只驗 workflow 檔內容，無法驗證 GitHub 上實際會跑；`make coverage` 本機不擋 95%，只有 CI 擋 | 可接受，列為提醒 |

### 002 Google 表單報名

規格狀態「已撤回（2026-11-04）」，程式已移除（migration 0027），tests 中無 Google 相關測試，與撤回狀態一致。**不計入缺口。** 建議：之後可在 spec 目錄標示不納入測試追溯。

### 003 Jotform 場次同步（FR-001～026）

| 需求 | 對應測試 | 判斷 |
|---|---|---|
| FR-001～007 連結表單、辨識場次題、只動場次選項、僅 admin、金鑰、單一專案單一表單 | `test_jotform_settings_page.py`（15 項）、`test_jotform_rules.py`、`test_jotform_client.py` | 完整 |
| FR-008～015 同步規則、選項文字、失敗不影響異動、不重複呼叫、無場次提示、歷史對應、找回場次題 | `test_jotform_sync_command.py`（11）、`test_jotform_session_hooks.py`（4）、`test_jotform_options` 相關單元測試 | 完整 |
| FR-016～018 同步狀態顯示、立即同步 | `test_jotform_sync_page.py`（4） | 完整；`views.py:580-582`（無金鑰／無表單按立即同步）未覆蓋 |
| FR-019～023 內建排程、單一實例、例外隔離、最近執行警示 | `test_scheduler.py`（5，含真實 PostgreSQL 諮詢鎖，`transaction=True`）、`test_compose_scheduler.py` | 完整 |
| FR-024～026 隔離、金鑰不入日誌、外部失敗不影響既有 | 設定頁／同步指令的跨專案測試；`test_the_platform_key_never_appears_in_pages_error_messages_or_logs` | 完整 |

### 004 Jotform 報名建單與付款（FR-001～030，狀態「草稿」但程式已實作並已提交）

| 需求 | 對應測試 | 判斷 |
|---|---|---|
| FR-001～008 導向建單、不採信網址金額、同名同電話沿用、場次對應、訂單編號=提交編號、去重、已付款、沿用付款方式 | `test_jotform_return.py`（8）、`test_pay_page.py` | 完整 |
| FR-009～013 無法自動處理五種原因、待處理清單、行政人員指定場次、略過 | `test_jotform_return.py`（parametrize 各原因）、`test_jotform_submissions_page.py`（8）、`test_check_submission_names_the_first_reason...` | 完整；人工建單「無前端課費用」（registration.py:142）與「略過時狀態已被改變」（165, 178, views 1575）未覆蓋 |
| FR-014～018 webhook 回查不採信內容、共用建單規則、暫時失敗重試、偽造不建資料、LINE 付款連結 | `test_jotform_webhook.py`（3，含真實並行）、`test_jotform_intake_command.py`（6） | FR-014～017 完整；**FR-018 沒有 004 專屬測試**（testplan 明列「沿用既有 LINE 流程，既有測試已覆蓋」，但沒有一個測試把「由 webhook 建立的訂單」串到 LINE 付款提醒） |
| FR-019～021 設定頁網址、辨識姓名／電話題、只接受已連結表單 | `test_jotform_fields_settings.py`（3）、`test_jotform_settings_page.py` | 完整 |
| FR-022～024 交易編號（綠界 20 字元限制、36 次上限、可追溯）、提交編號搜尋 | `test_jotform_gateway_numbers.py`（3）、`test_payments_search.py`、單元測試 trade number | 完整 |
| FR-025～030 隔離、伺服器端權限、金鑰與個資不入日誌、不重複查詢、失敗不顯示錯誤頁 | `test_projects_cannot_see_or_touch_each_others_submissions`、`test_neither_the_key_nor_personal_data_shows_up_in_pages_or_logs` 等 | 完整 |
| NFR-001（5 秒內看到付款頁）、SC-001、SC-004 | 無 | testplan 明列不納入；未測 |
| 真實 Jotform 行為（導向／通知實際欄位、免費方案、姓名題型答案形狀、提交時間時區） | 無（integration 只有 ECPay） | **未驗證**，是 004 最大的外部假設風險；近期 commit 606e744 已出現「Jotform 時區」「未知提交」修正，顯示這類假設確實會出錯 |

### specs/TEST_LIST.md（P0–P9、第 1～16 節，640 項已勾選、0 項未勾）

清單與 tests/ 的實際內容無明顯脫節：所有章節對應的測試檔都存在，且 `make test` 全綠。TEST_LIST 第 15 節標題重複（「JOSTFOTM 送出後導向（之後展開）」與「P9」並存），屬文件整理問題。`specs/TDD_PROGRESS.md` 為舊流程、2026-10-30 後未更新（profile 已知）。

## 4. 補測建議（依價值排序）

價值：高=金額／權限／驗簽／冪等／隔離；成本：S=單一測試或單檔、M=需新 fixture 或多檔、L=需新測試基礎設施。

| # | 項目 | 價值 | 成本 | 說明 |
|---|---|---|---|---|
| 1 | NewebPay／ECPay 回報解析的異常路徑：`Result` 為字串 JSON、內容無法解析、金額非數字（藍新）；缺欄位、金額非數字（綠界） | 高 | S | gateways/newebpay.py:100,102-103,111-112、ecpay.py:98-99。金流 webhook 的輸入驗證，應確認一律 `InvalidCallback` → 400，且不改訂單狀態。純邏輯，放 tests/unit |
| 2 | 補齊跨專案隔離測試：session_import、session_delete、attendance walk-in／close、front_course、message_templates、line_settings、LINE webhook（A 的 secret 打 B）、`attendance._check_project` | 高 | S～M | 憲法 4 的 MUST；每個約 1 個測試，依既有 `test_attendance_of_other_project_returns_404` 樣式 |
| 3 | 並行測試：改期同時搶最後一個名額（`rescheduling.py` 的 `select_for_update`）、同一筆付款通知同時送兩次（冪等）、同時按兩次「確認收款」 | 高 | M | 現只有 Jotform 導向／通知與排程鎖有真實並行測試；憲法「有限資源以資料庫鎖保護」與「通知可重送」都以序列方式驗。可沿用 `test_jotform_webhook.py` 的 `transaction=True` + Barrier 樣式 |
| 4 | 金額驗證：訂金 ≥ 價格／≤ 0、第二個前端課被拒、藍新 HashKey／IV 長度；人工建單時專案沒有前端課費用（registration.py:142） | 高 | S | forms.py:222,243,246,251,356；都是使用者可觸發的輸入驗證 |
| 5 | 串起「webhook 建單 → LINE 綁定 → 付款提醒」的流程測試（FR-018） | 中高 | M | 004 FR-018 目前僅靠「既有測試涵蓋」的文字宣稱，沒有一個測試證明由 webhook 建立的訂單進得了 LINE 提醒流程 |
| 6 | LINE 外送路徑：重試上限後標失敗（notifications.py:180）、無設定時重送（236）、付款提醒略過／失敗計數（278-281）、非法 webhook body 回 400（views 1170-71）、重新綁定停用帳號（service 94-95）、手動綁定衝突（114） | 中高 | S～M | 對外發送區；多為單一分支 |
| 7 | 啟用分支覆蓋率（`branch = true`）並看新基線，再決定是否在 CI 加分支門檻 | 中高 | S | 現在 97% 只是行覆蓋；權限與金額多為條件判斷，分支才是真實風險度量 |
| 8 | 管理指令非法參數：四個指令的 `--date`／`--now` 格式錯誤與缺時區 → `CommandError` | 中 | S | 排程類；process_finished_sessions 84%、process_jotform_submissions 88% 是全專案較低的檔案 |
| 9 | 同日有開始時間時的前後場次判斷（attendance.py:61,72） | 中 | S | 影響「提前到場、後面場次視為取消」的判定 |
| 10 | 略過已處理提交（views 1575、registration 165/178）與同步在無金鑰／無表單時的提示（views 580-582） | 中 | S | 並行下的狀態防護 |
| 11 | integration 層擴充：藍新測試站、Jotform（需使用者提供測試帳號與授權）、LINE 的 get_quota／push 驗證 | 中 | L | 現僅綠燈 ECPay 2 項；004 的三項「上線前實測」目前完全沒有自動化。需使用者授權才能執行 |
| 12 | 測試與需求的機器可追溯：測試名稱或標記帶 testplan 案例編號（如 `BE-API-07`） | 低～中 | M | 現在只能人工對照；可在日後新功能起步，不必回補舊的 |
| 13 | 將 `test_jotform_session_hooks.py:98` 的 `sync_form` monkeypatch 改為在 fake client 注入例外 | 低 | S | 消除對憲法 2 字面上的違反疑慮（fake client 已能 raise，應可替代） |

## 5. 規格與文件疑義（回報，不修改）

1. 004 spec 狀態仍為「草稿」，但功能已實作、提交並有測試；integration-plan 有 3 個 `[NEEDS CLARIFICATION]`（真實 Jotform 行為）未關閉。建議由 pm 確認狀態並決定是否補真實帳號實測。
2. 憲法流程關卡寫「覆蓋率 MUST 維持在專案約定門檻以上」，但 `make coverage` 不帶門檻，只有 CI 擋。本機 `make coverage` 通過不代表達標，需看總計或加 `--cov-fail-under`。
3. 002 規格已撤回但仍在 `specs/` 內，且 SITEMAP 仍提到 Google；易讓新進者誤以為是現行範圍。
4. NFR-001／SC-001／SC-004（Jotform 延遲、5 秒內看到付款頁）明列不測，規格卻沒有對應的上線後監控項目，建議補上。

## 6. 結論

**健檢結論：品質良好，可作為後續改善的穩固基線。** 依據：已提交的程式碼在本機實測下 lint、903 項測試、check、makemigrations、codemap 全部通過，行覆蓋率 97%（門檻 95%），無失敗、無跳過；測試風格守規（無 ORM mock、純邏輯與資料庫分層正確、tests/unit 不需 DB）；Jotform 各功能的需求與測試對應完整。

主要風險不在「現有測試壞了」，而在「測試證明不了的事」：金流回報解析的異常輸入、並行與鎖、部分路由缺跨專案測試、無分支覆蓋率、真實 Jotform 行為完全未自動化驗證。以上補測建議中 #1、#2、#4 成本低且價值高，建議優先納入 backlog。

## 7. 重現方式

```
cd /Users/Park/Site/teacher-crm
make test-fast
make test
make lint
make manage cmd="check"
make manage cmd="makemigrations --check --dry-run"
make coverage
make codemap-check
```
