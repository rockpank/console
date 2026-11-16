# 專案狀態總表：teacher-crm

> 維護者：`project-manager`（部分由調度者代寫）。最後更新：2026-11-17（批次 1 收尾）

## 整體健康度

**有風險**（非受阻）。批次 1 三項（B-004、B-005、B-027）資安與 QA 皆通過，且沒有新增缺陷；但整體風險來源未變：資安「不通過（修復後複審）」的高風險 2（H-1、H-2，對應 B-001、B-002，尚未開工）與 4 項架構高嚴重度落差。品質基線：提供 `JOTFORM_API_KEY` 假值時全套測試通過（三分支各為 906／903／921，覆蓋率 97–98%）；未提供時有 2 個既有失敗（P-1，與批次 1 無關）。依據：`assessment/SUMMARY.md`、`tasks/B-004|B-005|B-027/{impl-notes,security-1,qa-1}.md`。

## 階段總覽

| 階段 | 狀態 | 產出 |
|---|---|---|
| 接手登錄 | 完成 | `profile.md`、`engineer-rules.md` |
| 現況評估 | 完成 | `assessment/{architecture,quality,security,ux}.md`、`SUMMARY.md` |
| backlog | 完成（待使用者排序與挑選） | `backlog.md`（60 項） |
| 改善執行 | 批次 1 完成（3 項，待使用者合併）；批次 2 暫停 | `work-plan.md`；三分支 `t-B-004`（80cf8a4）、`t-B-005`（a8738aa）、`t-B-027`（6dcb9a6），未 push、未合併 |

批次 1 任務明細：

| 任務 | 內容 | 規格 | 資安／QA | 分支狀態 |
|---|---|---|---|---|
| B-004 | 學員編輯頁標籤區移出 `<title>`、搬到內容區 | `specs/006-fix-student-edit-tags-in-title/` | 通過／通過 | 已 commit，待合併；預覽站 http://localhost:8100/ 執行中 |
| B-005 | 追售名單「待邀請出席」去重 | `specs/007-fix-follow-ups-duplicate-invite-section/` | 通過／通過 | 已 commit，待合併；預覽站 http://localhost:8101/ 執行中 |
| B-027 | 補測：藍新／綠界回報解析異常（新增 18 個測試，`newebpay.py`、`ecpay.py` 覆蓋率 100%，產品碼零變更） | `specs/008-fix-gateway-callback-parse-tests/` | 通過／通過 | 已 commit，待合併 |

commit 編號取自調度者回報，未另行查證。

## Backlog 進度

共 60 項：完成 3、待辦 57。完成的 3 項在 `backlog.md` 狀態欄註明「已 commit 於分支 t-<任務>，待使用者合併」（狀態詞彙沒有「待合併」，使用者合併前相關後續項目仍受衝突鏈限制）。

| 階段 | 數量 |
|---|---|
| 待辦 | 57 |
| 規劃中／開發中／資安／QA | 0 |
| 完成（3 項皆待使用者合併） | 3（B-004、B-005、B-027） |
| 擱置 | 0 |

依類型（剩餘待辦 57）：資安 13、缺陷 4（B-003、006、007、026）、補完 16（含補測 7）、優化 18、重構 4、文件 2。已完成：缺陷 2（B-004、B-005）、補完 1（B-027）。

建議先做（來自 backlog，尚未經使用者確認）：B-001 設定預設改失敗即拒絕、B-002 假金流管制、B-003 金流失敗鎖終態（先確認 Q8）、B-008 發送前條件重驗。（B-004 已完成。）

## 事後可瀏覽（批次 1 的低／中風險與另立項目建議）

以下皆不阻擋批次 1 的合併。**目前都未進 backlog**（我不改 backlog 項目內容）；建議使用者挑選後由 `pm` 立項，並由 `pm` 配規格編號（009 起已預留給佇列，新項目請另配）。

| # | 嚴重度 | 內容 | 來源 | 建議 |
|---|---|---|---|---|
| 1 | 中（測試隔離，影響所有無 `.env` 的 worktree／CI） | **P-1**：`tests/db/test_jotform_sync_command.py` 的 `test_a_renamed_question_is_found_again_and_the_write_is_retried_once`、`test_when_the_session_question_cannot_be_found_again_the_form_waits_for_the_admin` 缺 `JOTFORM_API_KEY` 環境變數必失敗（輸出含「平台尚未設定 Jotform 金鑰，略過同步」）。**非日期問題**：同日期下提供假金鑰即全過；B-004 與 B-005 impl-notes 推測的「寫死日期」不成立，請勿往那個方向修。根因是兩測試沒用 `tests/db/conftest.py` 的 `platform_key`／`fake_jotform` fixture、也沒設 `settings.JOTFORM_API_KEY` | B-004 qa-1、B-005 qa-1、B-027 qa-1 | 另立項目（成本 S）：讓測試自行設定金鑰；修正前，profile 的「903 通過」基線需註明要有金鑰變數，且合併前不要把這 2 個失敗誤判為批次 1 造成 |
| 2 | 低（資安評為資訊偏低；金額相關，建議另立缺陷項） | **藍新 `Amt` 異常值**：`newebpay.py` 對 JSON 浮點數 `int()` 無聲截斷（`1500.5` 變 1500，字串 `"1500.5"` 卻會被拒，兩者不一致，與憲法 MUST 8 精神不符）；`Amt` 為 `1e999`（解析成 inf）時 `int()` 拋 `OverflowError`，而程式只捕捉 `ValueError`、`TypeError`，使端點回 **500 而非 400**；資安另列 `int(True)`＝1、`"1_500"` 被接受（綠界 `TradeAmt` 的 `"1_500"` 同理）。不構成可被利用的繞過：需先通過驗簽，入帳金額取自伺服器端 `attempt.amount`，`Amt` 只用於相等核對 | B-027 impl-notes 發現 1、security-1「另立項目建議」 | 另立缺陷項：金額解析前拒絕非整數型別、改用 `fullmatch(r"\d+")`、捕捉 `OverflowError`；先補「先紅」測試（`1500.9`、`true`、`1e999`）再修產品碼。B-027 的測試未固化這些現象，修正不會與之衝突 |
| 3 | 低 | **B-004 S-2**：沒有測試斷言標籤新增／移除表單含 `csrfmiddlewaretoken`（Django test client 預設不強制 CSRF，日後有人拿掉 `{% csrf_token %}` 測試不會失敗） | B-004 security-1 | 補一行斷言或用 `Client(enforce_csrf_checks=True)` 的 POST 測試 |
| 4 | 低（外觀） | **B-004 D-1**：標籤卡片的 `<p>` 內含 `<form>`，瀏覽器重組出兩個空 `<p></p>`，標籤列上方多一小段空白；無功能影響、無巢狀 form。僅在桌面寬度（1000px）以 headless Chrome 目視，未測手機寬度與 Safari／Firefox | B-004 qa-1、security-1、impl-notes | 把外殼改成 `<div>`；可併入 B-007 或後續樣板整理（B-007 本來就要動這個樣板） |
| 5 | 資訊 | **B-005**：跨專案隔離測試只驗證頁面 404 與停止 404，沒有直接斷言本專案頁面不含他專案學員姓名（待邀請名單隔離僅由 `for_project` 保證） | B-005 security-1 I-2 | 可併入 B-029（隔離守門補測）；不另立 |
| 6 | 資訊 | **B-005**：追售名單頁對講師角色顯示學員電話（既有行為、屬需求，非本次引入） | B-005 security-1 I-1 | 若要最小揭露，與 B-023（講師可見範圍）一併評估 |
| 7 | 低 | **B-027 F-1**：端點測試（`tests/db/test_gateway_notify_invalid_payload.py`）只斷言狀態碼 400、不看原因，其他原因的 400 也會綠；解析原因由單元測試以訊息關鍵字鎖定，QA 的變異驗證（m8、m9）已證明異常內容確為 400 的原因 | B-027 security-1 F-1、qa-1 | 補斷言回應文字含「無法解析」「欄位」「金額」（價值低、成本 S），可併入下一次動該檔時 |
| 8 | 低／資訊 | **B-027 F-2、F-3**：綠界官方公開沙箱值在 `tests/db` 新檔未註明（`tests/unit` 新檔已註明），日後若導入 secret scanner 需加白名單；隔離測試中 A、B 專案共用同一組假金鑰，偵測不到「B 專案設定被誤用於 A」 | B-027 security-1 | 加一行註解；B 專案改用不同假金鑰（可選） |
| 9 | 資訊（文件落差） | B-027 的 `specs/008-…/quickfix.md` 驗收寫「沒有 `docs/code_map/` 變更、通常不需 `make codemap`」，實況新增測試檔後地圖需更新（6 個產生檔，由 `make codemap` 產生，非手改）；backlog 驗收文字「`Result` 字串形式 JSON 一律 `InvalidCallback`」與實際程式不同（合法 JSON 字串會正常解析），實作已改以「字串但非 JSON」「字串 JSON 缺 `MerchantOrderNo`」案例覆蓋，與 pm 的解讀一致 | B-027 qa-1、impl-notes | 僅知悉；日後 quickfix 範本可提醒「新增測試檔也會動 code map」 |
| 10 | 資訊 | 藍新成功通知缺 `Amt` 時預設為 0，之後由 `handle_gateway_callback` 的金額核對擋下（400）；縱深防禦成立，不列缺陷 | B-027 impl-notes 發現 2 | 無 |

## 風險與待決事項

- **資安高風險未修**：H-1 預設設定不安全（B-001）、H-2 假金流可免費付款（B-002）。批次 1 未處理；修復並複審前，相關項目不得標為完成。
- **M-4 金流失敗通知鎖終態（涉及金額，待確認）**：需先確認 Q8（綠界／藍新同單號失敗後可否重試）。
- **合併三個分支時 `docs/code_map/` 會衝突**（三條分支各自 `make codemap`，同動 `INDEX.md`、`manifest.json`、`modules/tests.db.md`、`templates.md` 等）。處理方式：合併完成後重跑 `make codemap`，**不要手解衝突**，再以 `make codemap-check` 確認無 STALE。
- **合併前提醒**：`make test` 在沒有 `JOTFORM_API_KEY` 的環境會有 P-1 的 2 個失敗，驗證合併結果時需提供假金鑰（見上表第 1 項）。合併後預期全套測試數：903＋3＋0＋18＝924（推算值，未實測；B-005 為調整既有測試、數量不變）。
- **兩個預覽站仍在執行**：http://localhost:8100/（B-004）、http://localhost:8101/（B-005）。待使用者驗收後以 `bin/console site rm <任務> -p teacher-crm` 停。預覽資料庫留有 QA 建立的假資料與測試帳號（B-005 QA 建議收尾時隨 `--drop-db` 一併清；該旗標以 `bin/console site rm --help` 為準，未確認）。另有 QA 暫存容器未清理：`teacher-crm-b-004-baseline`、`teacher-crm-b-005-baseline`（已 stop，未 down）、`teacher-crm-b-005-db-1`（執行中）；scratchpad 內有快照與變異驗證副本。
- **批次 2 暫停**（使用者指示）：批次 1 完成後不開新 worktree，待使用者合併並決定後再補位。合併越晚，可自動做完的項目上限越低（約 13 項，見 `work-plan.md`）；B-007 與 B-039／B-041 起的樣板鏈要等 B-004、B-005 合併。
- **部署現況（使用者 2026-11-13 回覆，對應 backlog Q7）**：尚無正式環境；曾以預設設定運作，並曾透過 ngrok 對外開放；目前環境沒有真實金流／LINE 憑證與真實學員資料（「是否曾經有過」未確認）。影響：H-1、H-2 視為「上線前必修」，不需緊急輪替；但**舊環境的資料庫與 SECRET_KEY 不得沿用到正式環境**（正式環境用全新資料庫與新產生的金鑰）。若 Jotform API 金鑰、webhook 密鑰在 ngrok 開放期間使用過，建議上線前一併更換（成本低）。
- **待使用者決定**：backlog 共 Q1–Q20（`SUMMARY.md` 另有整併版 U1–U15，兩者編號不同但內容重疊）。阻擋最多項目的：Q1 名額語意、Q2 每日排程由誰跑、Q3 有收款學員可否刪、Q7 部署現況（已部分回覆）、Q8 金流失敗重試行為。另有 B-006 預設勾選屬規格而非缺陷（`work-plan.md` 需要使用者決定第 3 項）、是否允許「疊分支」（第 5 項）。
- **B-001 現況未確認**：目標 repo 已有 `specs/005-secure-config-defaults/`，是否已提交未確認（影響設定鏈第一位）。
- **報告間口徑不一**：12 處，已列於 `SUMMARY.md` §4.2。architecture 與 ux 讀的是提交前的工作樹，動工前需對照 HEAD 重驗行號（評估基線 `eb0a518`；B-005 QA 報告記錄的 origin/master 為 `4675d95`，兩者差異未查）。
- 評估限制：architect、uiux 無 Bash 只做靜態閱讀；`pip-audit`、`make test-integration` 未執行。

## 下一步

1. 使用者驗收兩個預覽站（B-004、B-005），然後合併 `t-B-004`、`t-B-005`、`t-B-027`；合併後重跑 `make codemap` 與 `make codemap-check`，並以假金鑰跑全套測試確認。
2. 使用者決定批次 2 要補位的項目，並回答能解鎖最多項目的 Q：Q10、Q1、Q8、Q3、Q2。建議的補位順序見 `work-plan.md` 執行佇列：B-001 → B-008 → B-024（並可同期補測 B-028、B-029、B-033、B-036）；B-007 在 B-004、B-005 合併後即可開。
3. 決定是否把「事後可瀏覽」第 1、2 項（P-1 測試金鑰隔離、藍新 `Amt` 異常值）立為 backlog 項目；第 2 項涉及金額，建議優先於其他低風險項。
4. 驗收後停預覽站（`bin/console site rm <任務> -p teacher-crm`）並清 QA 暫存容器。
5. B-018（pip-audit）、B-035／B-038（真實連線測試）需使用者授權才能動。
