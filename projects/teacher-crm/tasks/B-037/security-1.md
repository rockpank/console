verdict: 通過

# B-037 資安審查（第 1 輪）
範圍：worktrees/B-037/teacher-crm 相對 origin/master 的 diff（133 檔；specs/ 文件為主，另有 code_map、.env.example、ci 等隨附）。方法：git diff 靜態 grep（金鑰／token／email／電話／身分證／URL），並與 src/crm/urls.py、views.py 對照公開端點清單。

## 發現
- 無嚴重／高／中。
- 資訊 1：`.github/workflows/ci.yml`、`external.yml` 含 `DJANGO_SECRET_KEY`／`FIELD_ENCRYPTION_KEY` 值，經確認為 `ci-fake-...-tests-only` 明顯假值，非真實機密，可接受。
- 資訊 2：`.env.example` 僅說明與產生方式，未見真實值（只看範例檔，未讀 .env）。
- 資訊 3：未發現真實個資（email、手機、身分證）、真實 token 或金鑰；文件中的 `<token>` 皆為佔位。

## 公開端點清單（specs/SITEMAP.md 1.1）
逐項對照 urls.py／views.py：
- /pay/<token>/、/return/（無 login_required，簽章 token）：正確。
- /fake-gateway/*：正確標註僅開發測試；程式有 FAKE_GATEWAY_ENABLED 旗標把關。
- /gateway/notify/、/line/webhook/（csrf_exempt、驗簽）、/jotform/return/、/jotform/webhook/<token>/：正確。
- Jotform 設定、報名紀錄、前端課、課程費用皆明確寫為登入後頁面，未誤列為公開。
- 未把任何 @login_required 端點寫成公開。
- 待確認（低）：spec 002 FR-014 的「姓名加電話查詢頁」為舊規格描述，現行 urls 未見對應公開端點，SITEMAP 未列，不構成誤導。

## 未涵蓋
未逐一核對全部 133 檔的每一行；未跑依賴掃描（文件任務）。
結論：通過。
