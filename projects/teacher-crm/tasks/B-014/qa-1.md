verdict: 通過

# QA 第 1 輪：B-014（規格 044 公開端點與登入入口濫用防護）

環境：worktree `worktrees/B-014/teacher-crm`，COMPOSE_PROJECT_NAME=b-014，無 .env，命令列假值 JOTFORM_API_KEY=fake。未執行 docker compose down。

## 基線（自行重跑）
| 項目 | 結果 |
|---|---|
| `pytest tests/unit tests/db --cov=src --cov-fail-under=95 --create-db` | 1365 passed、1 warning、0 failed／skipped；總覆蓋率 98.23%（門檻 95）；throttle.py 99%、views.py 99%；耗時 6 分 51 秒 |
| ruff check／ruff format --check（src tests） | All checks passed／232 files already formatted |
| manage.py check | no issues |
| makemigrations --check --dry-run | No changes detected（FR-017／SC-006 成立） |
| 整合測試（連真實外部服務） | 未執行（需授權） |

## 規格對照
| 項目 | 驗證方式 | 結果 |
|---|---|---|
| FR-001／SC-002 導向 60／10 分、第 61 次拒、Jotform 零呼叫 | 讀 throttle.py 與 test_throttle_jotform；全套綠 | 通過 |
| FR-002 通知錯誤密鑰 20、專案 300；專案不存在仍 404 | views.py 先判密鑰再節流；form 為 None 不節流，符合邊界情況 | 通過 |
| FR-004 只取 REMOTE_ADDR | throttle.client_ip，無讀 XFF | 通過 |
| FR-005／006 回報上限 3、去重（鎖 Order 列、resolved 不計） | record_transfer_claim；pay_concurrency 測試 | 通過 |
| FR-007 進行中嘗試 3、30 分鐘窗（BE-API-29／30） | LIMITS.ATTEMPT_OPEN_WINDOW_MINUTES=30，test_throttle_pay_page.py:238-262：窗內 10 分鐘前 3 筆被拒且筆數不變；31／29 分鐘三種組合（3+0、2+1、0+3）各斷言導向與筆數 | 通過 |
| FR-008／009 付款頁 POST 10／10 分、連結驗證不計次 | pay_post_rejection 在 token 驗證之後、僅 POST | 通過 |
| FR-010～014、SC-004 登入 5 次鎖 15 分 | login.py＋throttle.py：帳號 strip／lower＋IP 成鍵，第 5 次顯示鎖定訊息，鎖定期間不延長（先查鎖再 authenticate），成功清零；BE-API-48 899／900 秒邊界；BE-API-47 過窗歸零；JOURNEY-03 | 通過 |
| FR-015／SC-005 /admin/ | urls.py 移除路由；test_admin_removed：匿名與平台管理者對 /admin/、/admin/login/、/admin/crm/order/ 等皆 404，且 content 與不存在網址相同、無 Location；admin 仍在 INSTALLED_APPS；src 內無 `/admin/` 引用（FR-016） | 通過 |
| fail-open（邊界情況） | `_fail_open` 裝飾所有快取操作，出錯放行並記警告；BrokenCache 與真實 DatabaseCache（缺表）測試在 test_throttle_cache 內，全套綠 | 通過 |
| FR-017 多 worker 共用 | DatabaseCache 別名 throttle，無 model、無 migration；Makefile migrate 加 createcachetable | 通過 |
| FR-018 門檻集中 | throttle.LIMITS | 通過 |
| FR-019 日誌 | 只記事件、IP、專案 id、帳號雜湊前 8 碼 | 通過 |
| FR-021 專案／訂單隔離 | 有測試（regression／jotform／pay_page） | 通過 |

## 抽驗：impl-notes 自承未做破壞驗證的案例
未對 src 做突變測試：自動模式判定修改 src 屬禁止，已改為靜態審視斷言，結論是「斷言有效，但弱度未經突變實證」。
- BE-API-45：以存在與不存在帳號各 5 次，逐次比對錯誤區塊文字，並斷言第 5 次含鎖定訊息。有效。若把錯誤文案改成因帳號而異，會被抓到。
- BE-API-46：站外 next 導向 /projects/、站內導向 /projects/new/，斷言 302 與 Location。有效。
- BE-API-48：899 秒仍鎖、900 秒恢復，同時斷言訊息與 302。有效。
- BE-API-52：只覆蓋 manage_teams、manage_projects、manage_members 三頁，不是「全部」平台管理頁。有效但範圍偏窄（見建議 1）。
- BE-API-53：同 52 的三頁加 /projects/，僅檢查回應不含字串 `/admin/`；另外 src 無 `/admin/` 引用，雙重保險。有效。
- BE-API-60：斷言含「請求過於頻繁，請稍後再試」，且不含「10 次／60 次／300 次／3 次」。有效。
- 特徵測試首跑即綠（既有行為鎖定）屬合理，但這些案例的 RED 無法證明；未發現測試只是恆真。

## BE-API-60 的 429 頁樣板落差
實作沿用 `crm/jotform_notice.html`（標題、說明、「大約 N 分鐘後可再試」），testplan 寫「用 pay.html 既有錯誤區塊」。判斷：**非實質缺口，低嚴重度**。理由：spec US2 情境 4 與 FR-003 只要求「看到『請求過於頻繁，請稍後再試』」「不洩漏門檻」，兩者皆滿足，且 429 狀態碼正確；spec 假設也禁止在本任務動 pay.html 的互動。代價是被擋的學員看到獨立頁而非付款頁內錯誤，需自行返回。此為 testplan 與實作的文字不一致，建議 PM／工程師擇一更新 testplan（改為「沿用提示頁樣板」）。該測試也未驗證 testplan 所寫「頁面其他區塊與正常 POST 失敗頁相同」，因為實作並非如此。

## 既有測試是否被弱化
`git diff HEAD --stat -- tests` 只有 tests/db/conftest.py（+63、0 刪除）；其餘為新增檔案。無既有斷言被刪或放寬。
conftest 新增 autouse fixture `throttle_cache`，把 throttle 別名換成 LocMem 並於每測試前清空，這讓既有測試不被節流污染，屬 testplan 的 FX-2，合理。注意它也使所有 tests/db 預設不走真實 DatabaseCache；真實後端由 `database_throttle_cache` 專用 fixture 覆蓋。

## 範圍外變更
- Makefile：migrate 加 createcachetable（plan 要求，範圍內）。
- views.py：移除未用的 `TransferClaim` import（因改走 throttle.record_transfer_claim，連帶清理，範圍內）。
- settings.py：新增 CACHES，default 明確寫成 LocMem，與先前隱含預設相同，無行為變更。
- 無 model／migration 變更，無無關檔案。
未發現範圍外變更。

## 安全檢查
- 授權與驗證：通過。新增入口皆為既有公開端點的前置節流；付款頁先驗 token 再計次；ThrottledLoginForm 不改變認證；以平台管理者實打 /admin/ 為 404。跨專案計數以專案／訂單隔離，有測試。
- 輸入與注入：通過。鍵為 sha256 雜湊；ORM 查詢；CSRF 行為未改（webhook 既有 csrf_exempt 不變）。
- 機敏資料：通過。日誌只記事件、IP、專案 id、帳號雜湊前 8 碼；測資為假值（FAKE_PASSWORD、203.0.113.x 保留網段）。
- 外部整合：通過。webhook 超限回 429 且帶 Retry-After，Jotform 可重送；驗簽（hmac.compare_digest）不變；本任務不增加外部呼叫。
- 依賴與設定：通過。無新增依賴；未動除錯設定。
- 已知取捨（低、不阻擋）：(1) 計數讀改寫非原子，併發會少計，程式註解與規格皆承認為粗粒度防護；回報去重與嘗試上限另以列鎖保證精確。(2) 登入失敗與鎖定皆依 IP，經 ngrok／反向代理時全體共用同一位址，受信代理屬 B-016。(3) fail-open 時鎖定與節流同時失效，規格已列為取捨。

## 缺陷清單
無阻擋、高、中缺陷。
- D-1（低）：BE-API-60 文件落差，見上。
- 規格疑義：無。

## 建議（不阻擋）
1. BE-API-52 可改為涵蓋 `docs/code_map/routes.md` 的全部平台管理 URL，以符合 testplan 的「逐頁」。
2. 針對 impl-notes 自承未破壞驗證的案例，工程師補一次突變驗證並記錄（例如 LOGIN_FAIL 5→6、窗 30→1、note 加「10 次」，預期對應測試轉紅）。

## 結論：通過
依據：全套 1365 通過、覆蓋率 98.23%、lint／check／makemigrations 乾淨；spec 各 FR／SC 與 4 個故事在測試中皆有對應斷言（含 30 分鐘窗 BE-API-29／30、/admin/ 404、登入 5 次／15 分鐘、fail-open）；既有測試未被弱化；無範圍外變更。低風險項目見上。
