verdict: 通過

# B-042 第 1 輪資安審查（輕量）

範圍：base.html 新增 inline script、tests/db/test_double_submit_guard.py、specs/026-prevent-double-submit/。

- CSP：settings.py 與 src 內無 CSP 設定或 header（grep Content-Security/csp 無結果），inline script 不會被擋，也沒有新增衝突。若日後導入 CSP，此 script 需要 nonce 或外移（資訊）。
- XSS／注入：script 為靜態，沒有 Django 模板變數插值。文案 "處理中…" 與 `b.textContent` 都用 textContent，不用 innerHTML，沒有新增注入面。idleLabel 只存取自 DOM 的文字。
- CSRF：只在 submit 事件上 preventDefault 重複送出，不改表單、token 或 header。CsrfViewMiddleware 維持啟用。按鈕延後 setTimeout 0 才停用，因此 name/value 仍會被帶出。
- 後端冪等：後端沒有改動，仍需自行處理重複請求。前端防連點只是 UX，不是安全控制（資訊）。停用 JS 或直接發請求都能繞過，與原本相同，無退步。
- 測試：環境沒有 pytest，未執行。以靜態審查為準。
- 發現：嚴重／高／中／低皆無。
