verdict: 通過

# QA 報告 B-007（統一訊息元件）第 1 輪

範圍：worktree `worktrees/B-007/teacher-crm`，相對 origin/master。以 diff 與重跑為準，未採信 impl-notes。環境：`COMPOSE_PROJECT_NAME=qa-b-007`，假 `JOTFORM_API_KEY`，`docker compose run --rm`。

## 重跑結果
| 項目 | 結果 |
|---|---|
| ruff check / format --check | 通過（All checks passed；189 files formatted） |
| tests/unit + tests/db | 915 passed、0 failed、0 skipped |
| 覆蓋率 | 總計 97%（門檻 95%）；views.py 98% |
| manage.py check | 無問題 |
| makemigrations --check --dry-run | No changes detected |
| codemap-check | OK（tree d9eb2d50c64c，264 檔），無 STALE |
| 預覽站 8100 | 未做 UI 實測（302 導向登入，無帳號）；以測試與靜態 diff 為準 |
| test-integration | 未執行（需授權） |

工作樹的未提交變更即為本任務變更（含新增 specs/012 與 tests/db/test_messages_component.py），無既有失敗。

## 驗收對照
1. error 為 `.alert.error` + `role=alert`，success 為 `.alert.ok` + `role=status`：base.html 單一迴圈依 level_tag 對應；`test_every_level_renders_once...` 與 manage_project_edit 失敗／成功兩案通過。通過。
2. warning／info 亮暗對比（自行以 CSS 變數值算 WCAG）：warning 亮 6.24、暗 9.14；info 亮 7.11、暗 8.75，皆 >= 4.5。通過。（附註：既有 `.alert.ok` 亮色 #1a7f4b 對 #e8f5ee 為 4.48，略低於 4.5，非本任務範圍，建議列 backlog。）
3. 四處提醒改新樣式：LINE 未驗證、藍新未驗證、jotform localhost 為 `alert warning`；fake_checkout 為 `alert info`；role=note 保留。通過。
4. 訊息只在 base.html 渲染：`grep "in messages"` 顯示 templates 內僅 base.html 有迴圈；靜態測試與「每則恰出現一次」測試通過；無訊息時無空 `.alert` 容器（測試通過）。通過。

## jotform localhost 提醒維持 role=alert：合理
原樣板即為 `role="alert"`（LINE、藍新為 `role="note"`）。規格「role=note 保留」指原本是 note 者。localhost 會使 Jotform 完全連不到導向與 webhook，是需立即處理的功能性故障，保留 alert 對輔助科技較合適；diff 僅改 class（error 到 warning），role 未動，不構成退步。建議規格補註此例外（規格疑義，低）。

## 缺陷與觀察
- 無阻擋／高／中缺陷。
- 低：`project_access.html` 殘留空的 `{% if messages %}{% endif %}`（輸出無內容，不影響功能），建議清除。
- 低：warning 迴圈的 `role="alert"` 與 spec 一致；level_tag 為自訂 tag 時退回 ok／status，可接受。

## 結論
通過。
