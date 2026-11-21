---
verdict: 通過
---
# B-025 資安審查 第 1 輪（sec L-4）

範圍：worktree 相對 origin/master 的 roster.py、views.py 匯入區段（diff 為準）。

## 結論
無嚴重/高/中風險。權限（`login_required`、`_project_or_404`→`visible_to`、`Action.EDIT_DATA`、`Session.for_project`）未動，跨專案隔離不變。

## 已驗證
- 檔案上限 2 MB 於 view 以 `upload.size` 判斷，超限不讀入、不解析。
- 列數上限 5000（空列不計），超限即回單一錯誤並停止，不入庫（我實際跑 5001 列：1 筆錯誤）。
- 姓名 100／住址 255 與 model max_length 一致，超長改為列錯誤而非 DB 例外。
- 超大欄位（20 萬字元）觸發 `csv.Error`，被攔截回通用訊息，不洩漏堆疊/內容（實跑確認）。
- 有錯誤列時整批不匯入（rows 僅含無錯誤列，view 於 errors 非空時不顯示成功）。

## 發現
- L-1（低）roster.py 電話格式錯誤訊息回顯原值 `電話格式不正確：{值}`。受 2 MB 總量限制，且 Django 模板預設跳脫，僅回應放大，無 XSS 風險。建議：回顯截斷到約 30 字（可選）。
- L-2（低／資訊）2 MB 檢查在 Django 已接收上傳之後；真正的請求體上限應由反向代理（如 nginx client_max_body_size）設定，Django 未設 FILE_UPLOAD_MAX_MEMORY_SIZE 以外的拒收機制。屬部署層建議，非本變更缺陷。

## 未涵蓋／未執行
- tests/db/test_import_limits.py：環境無 pytest／DB，**未執行**；僅以 python 直接呼叫 parse_roster_csv 驗證解析器行為。
- 模板跳脫為依 Django 預設推定，未逐檔檢視。
- 依賴掃描未執行（本變更未動依賴）。
