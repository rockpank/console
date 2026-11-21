verdict: 通過
round: 1

# B-037 QA 報告（第 1 輪）

工作目錄 `worktrees/B-037/teacher-crm/`，base = master 03d1f37（HEAD 相同）。純文件，未跑 docker、未讀 .env、未 commit。

## 結果

| # | 項目 | 結果 | 證據 |
|---|---|---|---|
| 1 | 只動 specs/ | 通過 | `git diff HEAD --name-only` 共 23 檔，全在 specs/（001:4、003:8、004:8、SITEMAP、TDD_PROGRESS、TEST_LIST）；src/、tests/、憲法 0 個。（調度者說 6 個文件，實際是 23 個檔案，涵蓋 6 類文件，皆在範圍內。）|
| 2 | validate 重跑 | 通過 | 001 全 OK 無警告。003：1 個 CASCADE 警示（models.md）。004：1 個 CASCADE 警示（models.md）＋integration-plan 3 個 [NEEDS CLARIFICATION]。|
| 2a | 警示是否本來就有 | 既有，非本任務造成 | `git show HEAD:` 對照：003 models.md 有 2 處 CASCADE、004 models.md 1 處、004 integration-plan 3 個 NEEDS CLARIFICATION，與現況相同；本任務 diff 未改這些檔的內文（models.md／integration-plan 只改狀態行）。CASCADE 理由其實已在兩份 data-plan（003 L95–97、004 L87、L91）；B-037 另在 003、004 spec 補了「資料關聯的刪除行為」說明，但 validator 只掃 models.md，故警示仍在，屬驗證器限制、非缺陷。3 個 NEEDS CLARIFICATION 屬 B-038。|
| 3 | SITEMAP 1.1 對外端點 vs urls.py | 通過 | 逐條對照：`pay/<token>/`、`pay/<token>/return/`（L157-158）、`fake-gateway/checkout/`、`complete/`（L159-160）、`gateway/notify/<project_id>/`（L153）、`line/webhook/<project_id>/`（L186）、`jotform/return/<project_id>/`（L187）、`jotform/webhook/<project_id>/<token>/`（L189）全部存在，無遺漏、無多列。登入後列表所列 jotform connect／question／sync／remove／fields、submissions（含 resolve／dismiss）、front-course、products 亦都存在。|
| 4 | 狀態欄「已實作」抽查 | 通過（有一項限定） | 001：`.github/workflows/ci.yml`、`external.yml` 存在。003：`run_scheduler` 管理指令與 `src/crm/scheduler.py`、compose `scheduler` 服務、jotform connect／sync 路由存在。004：`JotformSubmission` model、`jotform_return`／`jotform_webhook` 路由、`JOTFORM_TIMEZONE` 設定存在。無矛盾。限定：未逐條驗證各 FR 的實作完整度（超出本任務，且各 spec 已註明「FR 內容未改」）；004 的「上線前實測尚未完成」本就無法以程式證實，已標為未完成，處理正確。|
| 5 | Q5、Q6 與答覆一致 | 通過 | Q5：SITEMAP 頂部與四處標記皆為「[要做（尚未實作）]」，明寫「不是列為不做」，四頁名稱與使用者答覆完全相同；無一處寫成不做。Q6：004 spec L305 寫「目前確定 America/New_York（程式現行預設，settings.py L34 相符）」，並寫上線前仍須實測、測試帳號尚未提供、不得標為已驗證。|
| 6 | T002／integration-plan 的 Asia/Taipei | 通過 | tasks.md L47、integration-plan L11、L114 仍寫 Asia/Taipei（兩者本任務未動，diff 僅 integration-plan 狀態行）；004 spec L305 明確點名這兩處並歸 B-038。|
| 7 | 有無過度改動 | 有輕微超範圍（不阻擋） | 見缺陷 D-1、D-2。|

## 缺陷

- D-1（低，文字錯誤）：SITEMAP 第 7 節「後續改以 Jotform（上文原誤植的「Jotform」即此服務 Jotform）」——全域取代造成語意不通的句子（原文是「上文的「JOSTFOTM」應即此服務」）。建議改為「上文原誤植的「JOSTFOTM」即此服務」。
- D-2（低，範圍）：SITEMAP 把「銷講」全面改為「前端課」（標籤名、步驟名、章節名多處）。backlog B-037 列的項目沒有這項；頂部校正說明有交代，且使用者答覆 Q13 的背景支持「前端課」用語，但屬用語統一，較接近 B-039 範圍。另 `src/crm/retagging.py`、`orders.py`、`reports.py` 與 migration 0005 仍含「銷講」字樣，故 SITEMAP 標籤名與程式內標籤字串未必一致（SITEMAP 自述 0017 已改名舊標籤，未逐一核對）。建議調度者確認是否接受；若不接受，還原該批取代。
- D-3（資訊）：SITEMAP 殘留 3 處「銷講」皆屬刻意保留的原文件名稱與說明，符合頂部說明。

## 結論

通過。範圍僅限 specs/、Q5／Q6 與答覆一致、對外端點清單與 urls.py 完全吻合、validate 警示皆為 base 既有。D-1、D-2 為低嚴重度，建議在收尾前修 D-1，D-2 由調度者決定。
