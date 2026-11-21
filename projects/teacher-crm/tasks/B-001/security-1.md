---
verdict: 通過
round: 1
---

# B-001 資安審查（第 1 輪，sec H-1 完整複審）

範圍：worktree 相對 base 的變更與新增檔（settings、startup_checks、crypto、.env.example、compose.yaml、ci.yml、external.yml、tests）。方法：靜態閱讀、git grep、以獨立 python 驗證 crypto 固定向量。未讀 .env 與 config/env/**。未執行：完整 pytest、docker compose run（無需）。

## 結論檢核
- 無真實值：.env.example 只有 change-me 佔位；CI 為 `ci-fake-` 假值；測試金鑰為 qa- 假值；git grep 未見金鑰特徵；版控只追蹤 .env.example，未追蹤 .env。通過。
- 錯誤訊息：startup_checks 與 settings 的 ImproperlyConfigured、crypto 的訊息只含變數名稱與原因，不含值、長度或片段。通過。
- crypto：已移除退回 SECRET_KEY；金鑰推導（sha256 後 urlsafe_b64encode）不變，固定向量密文以相同金鑰實測可解密。通過。
- 預設失敗即拒絕：兩把金鑰缺／空白／相同即失敗；DEBUG 預設 0；FAKE_GATEWAY 預設 0；DEBUG=1 搭配非本機 ALLOWED_HOSTS 拒絕（含 `*`）；非除錯下公開值（changeme、devinsecure、djangoinsecure，已正規化）拒絕。DEBUG 只認 "1"，其他值皆視為關閉，偏安全。通過。
- compose：app／scheduler 以 YAML anchor 共用 env_file `.env`；environment 區塊未定義任何金鑰或開關變數，不會覆蓋；scheduler 指令改為 `python src/manage.py run_scheduler`，無新增權限、埠或掛載。通過。
- CI：假值只在 job env，無 `secrets.`；外部整合工作流程同樣為假值；DEBUG=0 與假金流關閉，與正式形態一致，且有測試鎖定（含 check_environment 驗證）。假值帶 ci-fake- 前綴，且在非除錯下不命中公開值黑名單，若誤用到正式環境不會被擋下，見 L-2。

## 發現
- L-1（低）src/config/settings.py:35（ALLOWED_HOSTS）：`.split(",")` 未去空白，而檢查端有 strip，兩者行為不一致。僅造成帶空白的主機名稱不匹配，不是漏洞。建議 settings 端同樣 strip／略過空項。
- L-2（低）src/config/startup_checks.py:12-13：公開值判定為黑名單，不檢查長度或熵；`ci-fake-` 假值與 `x` 這類短金鑰在非除錯下仍通過。規格已明示黑名單不證明強度。建議（可延後）非除錯下加最小長度，並把 `ci-fake-` 納入公開值標記（需同步調整 CI 測試，因 CI 以 DEBUG=0 運行，納入後要改走其他做法），或維持現況並在維運文件註明。
- L-3（資訊）DEBUG=0 時 DJANGO_ALLOWED_HOSTS 允許 `*`：規格範圍外，建議留給後續項目（B-002 或另立）。
- 資訊：.env.example 預設 DEBUG=1、FAKE_GATEWAY=1，僅限本機且被主機檢查約束，符合規格。

無嚴重／高風險發現。低風險項不阻擋，記入 status「事後可瀏覽」。
