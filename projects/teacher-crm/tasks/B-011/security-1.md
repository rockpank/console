---
verdict: 通過
round: 1
task: B-011
---
# B-011 資安審查第 1 輪

範圍：git diff origin/master 與未追蹤檔（靜態審查，未執行測試、未動 worktree）。

## 結論：通過（嚴重 0／高 0／中 0／低 3／資訊 2）

## 逐項
1. 權限：`daily_job_settings_update` 為 `@platform_admin_required` + `@require_POST`（views.py 末段）。後者內含 `login_required` 與 `can_manage_platform_as`（只有 ADMIN），manager／staff 一律 403；project_id 只用於重導，經 `visible_to` 過濾，非數字（ValueError）與不可見都回 404，無法區分存在與否。樣板有 `{% csrf_token %}`，未見 csrf_exempt。設定頁卡片以 `can_view_platform_job_status`（admin、manager）顯示，編輯表單僅 admin。
2. 輸入驗證：伺服端 `DailyJobTimesForm`：TimeField 只收 `%H:%M`，required／invalid 皆統一訊息；`_not_after_2300` 擋 >23:00；兩欄任一不合法則整個 form invalid，save 不執行（全有或全無）；save 在 transaction.atomic 內。DB 另有 CheckConstraint（run_time ≤ 23:00）。前端 min／max 僅輔助。
3. 樣板：無 `|safe`／mark_safe；`row.error`、messages 皆自動跳脫。error 為 `str(exception)[:200]`，不含堆疊（堆疊只進 logger）。日誌只記工作名稱與筆數，details 只有彙總數字與場次 id。
4. 資料：兩張新表為平台全域，不含專案／學員資料，無跨專案外洩；migration 0032 只有兩個 CreateModel，依賴 0031，可回退，不動既有表；唯一約束與 CheckConstraint 已在 migration 內。
5. 並行：claim_and_run 先 create 佔位，IntegrityError 即 ALREADY_CLAIMED 不執行；recover_orphans 僅在 `holding` 剛取得鎖時呼叫；孤兒標 failed 後當天視為已執行，不會重跑，不會放大發送；發送層既有 (student, session, kind) 唯一約束仍為第二道防線。`--skip-daily-jobs` 為本機管理指令參數，沒有網路入口可遠端觸發。
6. 無 raw SQL（僅沿用既有諮詢鎖 SQL，固定常數）；無祕密或個資；本次變更未新增外網連線。
7. sync.py 僅加 `.order_by("id")`，只讓走訪順序確定，無副作用。

## 發現
- L1（低）`DailyJobRun.error` 可能含例外原文前 200 字（如外部 API 錯誤訊息），顯示給 admin／manager。建議日後可對已知例外改用固定訊息；目前僅內部人員可見。
- L2（低）儲存端點缺 project_id 時回 404（admin 手動 POST 時困惑），屬可用性，非安全問題。
- L3（低）每日工作失敗後當天不重試（設計取捨）；可靠性議題，非資安。
- I1（資訊）設定儲存未留稽核日誌，只有 `updated_by`／`updated_at`（最後一次）。
- I2（資訊）依賴漏洞掃描：未執行（本次未新增依賴）。

未涵蓋：實際執行測試、真實 LINE 發送路徑（沿用既有 run_all，未改動）。
