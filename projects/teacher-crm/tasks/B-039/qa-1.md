---
verdict: 通過
round: 1
task: B-039（規格 046 用語統一，快速路線）
---

# QA 第 1 輪：B-039

環境：worktree `worktrees/B-039/teacher-crm`（分支 t-B-039），Docker，`COMPOSE_PROJECT_NAME=b-039-qa`。主機沒有 `make`，改直接執行 Makefile 內的 docker compose 指令（內容相同）。

## 基線與關卡（自己重跑）

| 項目 | 結果 |
|---|---|
| ruff check / format --check | 通過（244 檔已格式化） |
| manage.py check | 無問題 |
| makemigrations --check --dry-run | No changes detected |
| pytest tests/unit tests/db + coverage | 1439 passed、2 failed（共 1441），覆蓋率 97.92%（門檻 95%） |
| codemap-check | STALE（已知；新增 test_wording_labels.py 與多個修改檔）。依規定不手改，由合併者 `make codemap` 重產 |

2 項失敗（`tests/db/test_jotform_sync_command.py::test_a_renamed_question_is_found_again_and_the_write_is_retried_once`、`::test_when_the_session_question_cannot_be_found_again_the_form_waits_for_the_admin`）：
- 這兩個測試依賴容器環境的 `JOTFORM_API_KEY`（輸出為「平台尚未設定 Jotform 金鑰，略過同步」），只有部分測試把 settings 清空。
- 我的 QA 容器沒有該金鑰，故失敗；加 `-e JOTFORM_API_KEY=dummy-key` 單檔重跑 11 passed。補上金鑰後即為 1441 passed，與工程師結果一致。
- 本任務沒有改任何 jotform 邏輯，只動了一個樣板的文字。判定為**既有的測試與環境耦合**（不是本任務造成），不阻擋。建議另開 backlog：測試自己設定 `settings.JOTFORM_API_KEY`。

## 既有測試修改查核（git diff）

- `tests/unit/test_project_nav.py`：共 5 處，全是字串常數 `"課程費用與贈品"` → `"進階課程費用"`（3 處 labels 斷言、2 處 active 對照表值）。斷言結構、比較運算與元素數量完全不變，沒有新增 skip／xfail。**認可。**
- `tests/db/test_pay_page.py`：1 處 `assert "5000" in content` → `assert "5,000" in content`。僅常數變更，且與規格預期行為 3（千分位）一致。**認可。**
- `git diff tests` 中 skip／xfail 出現 0 次。
- `tests/unit/test_wording.py` 未被修改。確認。
- 「前端課／後端課」標示：src 內沒有「後端課」，確實未做，符合使用者裁示（範圍外）。

## 驗收對照

| 編號 | 案例 | 預期 | 實際 | 結果 |
|---|---|---|---|---|
| BE-API-01 | 側欄／標題／提示一致 | 側欄含「進階課程費用」「前端課費用」；通知頁指向「前端課費用」且不含「課程與費用」；products 頁不含「課程費用與贈品」「建立進階課程」；兩頁互指 | `test_wording_labels.py::test_sidebar_titles_and_hints_use_the_same_names` 通過；diff 確認路由、分組、權限未動 | 通過 |
| BE-API-02 | 無英文外洩 | Jotform 設定頁（無金鑰、排程停擺）與通知頁（無 LINE）的可見文字不含 admin／jotform_api_key／scheduler；含「系統管理員」「排程服務」 | 兩個測試通過（以去標籤文字判斷，屬性與欄位 name 未動） | 通過 |
| BE-API-03 | 千分位 | 部分收款訊息 `NT$ 1,200` | 測試通過；`views.py` 改為 `{order.paid_amount:,}`，仍是整數，無 float | 通過 |
| 非行為 | docstring 舊稱、`docs/wording.md` | 改為「前端課」；有用語表 | diff 確認 `views.py`、`orders.py`、`reports.py`、`line/notifications.py` 只動 docstring／註解；`docs/wording.md` 與 quickfix 用語表一致 | 通過 |

附註（低、不阻擋）：`orders.py` docstring「專案設定了前端課課程時」有「課」字重複，建議合併時順手修成「前端課」。預覽站 http://localhost:8101/ 回 302（需登入），本輪未登入逐頁目視，標「未測試」；頁面文字改動已由整合測試的實際渲染 HTML 驗證。

## 缺陷

無阻擋或高、中缺陷。低：上述 docstring 贅字；既有的 jotform 測試環境耦合（另列 backlog）。

## 安全檢查

- 授權與驗證：不適用。未新增或變更入口；`can_edit_data`、路由、權限條件未動（diff 確認）；新測試以 STAFF 身分實際開啟三頁。
- 輸入與注入：通過。千分位用 f-string `:,` 格式化整數 `paid_amount`，沒有使用者輸入進入格式字串；訊息經模板輸出仍受自動跳脫保護。無新查詢、上傳、SSRF、CSRF 變動（表單 `{% csrf_token %}` 未動）。
- 機敏資料：通過。可見文字已移除 admin、JOTFORM_API_KEY、scheduler（測試覆蓋）；測試資料為假值（`dummy-key`、「進階一階」）；未讀取 `.env`。
- 外部整合：不適用（未動驗簽、冪等、逾時邏輯）。
- 依賴與設定：不適用（無新增依賴，無 migration，無設定變更）。

## 結論

通過。依據：三個切片的測試與 diff 對得上驗收標準，既有測試修改只是常數取代、未弱化；lint、check、migrations 通過，覆蓋率 97.92%；唯一失敗為環境金鑰造成的既有耦合，補金鑰後 1441 全綠。codemap STALE 為已知，交合併者重產。
