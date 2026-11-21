verdict: 通過

# B-014 資安審查 第 1 輪（規格 044）
範圍：throttle.py、login.py、views.py（jotform_return／jotform_webhook／pay_page）、urls.py（兩處）、settings.py CACHES、Makefile 的 diff 與原始碼。測試未重跑（環境找不到 python，標「未執行」）。

## 發現（皆非阻擋）
1. 中｜來源位址只取 REMOTE_ADDR（throttle.py client_ip）。不信任 X-Forwarded-For 是對的，無法偽造繞過。但若部署在反向代理後且 B-016 未上線，所有訪客共用代理 IP：REDIRECT（60/10 分）、登入鎖定（帳號＋IP）會變成全體共用，單一攻擊者可讓正常學員被 429 或鎖定特定帳號。repo 內未見代理設定（待確認部署）。建議：B-016 上線前不要部署到代理後；或在 B-016 一併處理。
2. 低｜登入鎖定期間連正確密碼也被擋（login.py 先查鎖），屬刻意取捨；鎖定鍵含 IP，故 DoS 限同 IP。鎖定訊息對存在／不存在帳號一致，無帳號列舉。帳號已 strip＋lower，大小寫無法繞過。
3. 低｜hit／record_login_failure 讀改寫非原子，併發可少計（文件已註明）；登入暴力破解可借併發略超 5 次，影響有限。轉帳回報與付款嘗試的上限改用 Order 列鎖（select_for_update，交易內僅 DB 操作），競態處理正確。
4. 低｜fail-open：快取後端失效即放行並只記警告。對付款與登入可用性的合理取捨；建議對 backend_unavailable 日誌設告警，避免防護長期靜默失效。
5. 資訊｜計數鍵為 sha256 雜湊，無鍵注入；日誌只記事件、IP、專案編號、帳號雜湊前 8 碼，無密碼／token；429 僅顯示「約 N 分鐘」，不洩漏門檻（登入訊息的 15 分鐘為鎖定時長，可接受）。
6. 資訊｜/admin/ 路由已移除，src 內無 admin: 反向解析或連結殘留。django.contrib.admin 仍在 INSTALLED_APPS（settings.py:43），無入口故無暴露；可於後續清理。
7. 資訊｜webhook 密鑰錯誤只對「專案存在」的請求計次、仍回 404（專案編號是否存在仍可由 404／429 差異推知，編號本就可猜，影響低）。

## 未涵蓋
測試未執行；依賴掃描未做（非本任務變更）；DatabaseCache 表由 createcachetable 建立，部署流程需確實執行（缺表時 fail-open 放行）。
