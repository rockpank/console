---
name: dispatch
description: 多角色總機。`/dispatch <工單號碼> [專案別名]` 依序調度 專案管理員 → 分析師審議團 → 工程師 → Code Review → 個資守門員；低／中嚴重度自動往下，只有高嚴重度才停下來通知你。`/dispatch status` 看全部工單進度；`/dispatch resume <工單號碼> [裁示]` 從停下的階段繼續；`/dispatch reopen <工單號碼> [專案別名]` 驗收後要調整，開新一輪。
argument-hint: "<工單號碼> [專案別名] | status | resume <工單號碼> [裁示] | reopen <工單號碼> [專案別名]"
allowed-tools: Read Write Edit Glob Agent ToolSearch Bash(bin/console:*) Bash(/opt/femashr/console/bin/console:*)
---

# /dispatch：工單多角色調度

繁體中文回覆。**絕不 `git push`、不開 PR、不部署、不 commit。** 對話、檔案、通知都不得出現客戶個資。先讀 `/opt/femashr/console/docs/agent-protocol.md`（鐵則、交接檔、嚴重度、升級規則），你自己也要遵守。

## 你的角色

你是**總機**，不是分析師或工程師：不自己查碼、不自己下技術結論，只調度角色、讀檔頭、判斷閘門、更新狀態。Subagent 不能再派 subagent，所以**辯論的調度只能由你做**。每個角色的回覆都 ≤ 10 行，細節在 `_ticket/` 的檔案裡，你只讀檔頭。

## 參數

- 工單號碼只來自參數；不是純數字（允許 `r-4059`／`#4059`）就停下問，不要猜。專案別名沒給就用預設（`bin/console projects`）。一次只處理一張工單。
- `status`：直接執行 `bin/console status`，回報（已升級的排最前），結束。
- `resume <工單號碼> [裁示]`：見最後一節。
- `reopen <工單號碼> [專案別名]`：驗收後要調整，見「reopen」一節。**只有使用者明說 reopen 才做。**
- 其他：新工單，從「階段 1」開始；若 `bin/console status <工單>` 已有紀錄，先告知目前階段並依 resume 的規則接續，不要重頭來過。已完成（`待人工交付`／`已釋放`）的工單只告知「已完成；驗收後要調整請用 `/dispatch reopen <工單>`」，不自行重跑。

## 額度保護（高耗 token 的階段開始前先問一次）

定義在協議「額度保護」，這裡只寫你怎麼做。**進入下列階段前**各執行一次 `bin/console usage --guard`：2a、2c、2d、階段 3、階段 4 的每一輪（審查與修正）、階段 5 的個資修正。階段 1 與個資掃描本身不用。

- 結束碼 0 → 照常往下。
- 結束碼 3 → **不要進入這個階段**，改走暫停：寫 `_ticket/escalation.md`（檔頭 `kind: 額度保護`、`resume_at: <要進入的階段：進 2a→已讀取；進 2c／2d→分析中；進階段 3→已裁決；進階段 4→實作中；進階段 5 的修正→個資掃描>`，內文只寫那一行輸出裡的原因與預計重置時間）→ `bin/console status <n> --set 已升級 --note "額度保護：<原因一句>"`（不帶 `--severity`，嚴重度維持原樣）→ **不推播**→ 回報後停止：

```
⏸ 工單 <n> 因額度保護暫停在 <階段> 之前：<原因>，預計 <時間> 重置
繼續：額度重置後 /dispatch resume <n>；或使用者在介面按「暫時解除暫停」後再 resume
```

**絕不自行解除**：不要重試、不要略過檢查、不要換別的方式派 subagent，也不要自己判斷「額度應該還夠」。已派出的 subagent 會做完，你只在下一個高耗階段開始前停。檢查指令本身失敗（不是 0 也不是 3）→ 當作可以繼續，並在最後回報註明「額度檢查失敗」。

## 階段 1：讀取工單（專案管理員）

`bin/console status <n> --set 待讀取 -p <專案>`，派 `ticket-manager`，prompt：`模式: intake / 工單: <n> / 專案: <別名>`。回報有「需要人處理」項目（缺金鑰、憑證、分支衝突、站點失敗）→ 照實回報使用者後**停止**，不繞過。「未讀二進位附件」與「提醒（不停止）」只是資訊，**不停止、不問使用者**，記進 `--note` 後直接往下（協議「不因客戶資料而中斷」）。成功 → `--set 已讀取 --note "<一句話摘要>"`。

## 階段 2：分析師審議團（取代人工審方案）

`--set 分析中`。

**增量模式**：若 `worktrees/<n>/_ticket/landed-<專案>.json` 存在（用 Glob 檢查），這是重派、成果可能已在 base 上的工單，規則見協議「已併入的工單」。2a **只派一位** `ticket-analyst`（`視角: rootcause`），prompt 加 `增量: 是`；不派 risk、不辯論（跳過 2b／2c，風險由 2d 逐條判定）。讀 `rootcause.md` 檔頭的 `delta`：`full` → 偵測誤判，回到一般流程補派 risk（`bin/console` 不用動，把 landed 檔當線索即可）；其餘進 2d（prompt 一樣加 `增量: 是`）。

**2a. 獨立分析**：先 `bin/console wt fingerprint <n> -p <專案>` 記下指紋。**在同一則訊息裡同時派兩個** `ticket-analyst`，prompt：`模式: lens / 視角: rootcause|risk / 工單: <n> / 專案: <別名>`。兩位互相看不到對方（最小變更的做法由 rootcause 的方案提出、decide 取捨，不另派 minimal）。結束後再取一次指紋；**不一致**＝有人改了工作樹 → 升級（可能是分析師違規，也可能是你同時在編輯），不要自行還原。缺任何一份 `analysis/*.md` → 重派缺的一次，仍失敗就升級。

**2b. 是否需要辯論**：只讀兩份檔頭。**三項全成立就跳過辯論，直接進 2d**：兩位的 `severity` 都不是高、`hit_rules` 皆空、沒有人 `needs_clarification: true`。**不要求兩位結論一致**：`root_cause` 或 `recommended` 有分歧但都沒到高嚴重度時，交給 2d 的裁決逐一化解或標為未化解（同模型分析師的共識不是獨立證據，辯論也不改變嚴重度，高嚴重度看的是協議的客觀條件，所以分歧不值得多花一輪辯論）。只要有人 `severity` 為高、`hit_rules` 非空，或 `needs_clarification: true`，進 2c。

**2c. 辯論（預設 1 輪）**：同一則訊息同時派兩個 `ticket-analyst`，prompt：`模式: rebut / 視角: rootcause|risk / ...`。每位讀另一位的分析、用程式碼證據回應並更新立場。同樣前後比對指紋。

**2d. 裁決**：派一個全新的 `ticket-analyst`，prompt：`模式: decide / 工單 / 專案`，產出 `decision.md`（跳過辯論而兩份結論不一致時，裁決者會自己查驗分歧點，無法化解就判低信心並升級；完成回報的「事後可瀏覽」要列出未化解的分歧）。讀它的檔頭：

- `escalate: true` → 去「升級」。
- 否則 `bin/console status <n> --set 已裁決 --severity <低|中> --note "<一句話>"`，往下。

**2d 之後的 `delta: none`**：`decision.md` 檔頭 `delta: none` 且 `escalate: false` → 不進 spec 閘門、階段 3～5，直接 `--set 待人工交付 --severity 低 --note "已併入，無需改動"`，完成回報的「變更」寫「無（已併入 <base>）」，「事後可瀏覽」附對照表位置（`analysis/rootcause.md`）。`escalate: true` 仍走升級。

**不要自己改寫 decision.md 的結論。** 你若不同意，把理由當成升級原因交給使用者。

## 閘門：spec

用 Glob 檢查 `worktrees/<n>/<專案>/specs/<n>-*/spec.md`，並用 Bash 比較時間：`test "worktrees/<n>/_ticket/decision.md" -nt "<spec 資料夾>/consistency.md"`（`consistency.md` 不存在也算「較舊」）。

- `spec.md` **存在**，且 `consistency.md` 存在、不比 `decision.md` 舊 → 閘門通過，進階段 3。
- `spec.md` **不存在**，或 `decision.md` 比 `consistency.md` 新（spec 還沒對照過這版裁決，例如人工裁示改了方向）→ 先**核對檔頭**：`decision.md` 必須 `escalate: false`（或有 `resolved_by:`），否則去「升級」。通過後 `--set 待spec --note "專案管理員產出／修訂 spec"`，進入額度檢查（算高耗階段），派 `ticket-manager`，prompt：`模式: spec / 工單: <n> / 專案: <別名>`。

讀它的回報：

- 回報說「寫檔：被拒」並附內容 → 你**原文**寫入 `spec.md`／`consistency.md`（只搬運，不改內容、不下結論）；寫入後的位置只限這兩個檔。
- `放行: 是` → `--set 已裁決 --note "spec 已對照裁決"`（維持嚴重度），進階段 3。
- `放行: 否`（有阻擋項、或 spec 與 decision 有它無法消除的實質衝突）→ 去「升級」，原因寫阻擋項編號與一句話；選項通常是「A. 改 decision（回 2d 或人工改範圍） B. 人工在 worktree 開專案端 `/redmine-ticket <n>` 處理 spec」。**不自己改 spec 或 decision。**
- 回報缺漏、工具失敗 → 照實回報使用者後停止，不繞過。

工程師仍不得改 `specs/**`；只有專案管理員的 `spec` 模式（或使用者在專案端視窗）能動它。專案端流程照舊可用：使用者想親自處理 spec 時，在 `worktrees/<n>/<專案>/` 開 Claude Code 執行 `/redmine-ticket <n>`，完成後 `/dispatch resume <n>` 會重新檢查這個閘門。

## 階段 3：實作（工程師）

`--set 實作中`。派 `ticket-engineer`，prompt：`模式: implement / 工單 / 專案`。讀 `implementation.md` 檔頭：`status: blocked` → 升級（原因對應協議第 7 條或資訊不足）；`tests: 失敗` → 把失敗摘要放進給審查前的備註並繼續審查（審查員會自己驗證）。

## 階段 4：審查迴圈（最多 2 輪）

`--set 審查中`。第 `k` 輪（k=1,2）：

1. 取指紋 → 派**全新的** `code-reviewer`，prompt：`工單 / 專案 / 輪次: k` → 再取指紋，不一致就升級。
2. 讀 `review-k.md` 檔頭。`verdict: 通過` → 進階段 5。`需修正` 或 `阻擋` → 派 `ticket-engineer`，prompt：`模式: fix review-k.md`，然後進下一輪。
3. 第 2 輪仍不是「通過」→ 升級（原因：審查 2 輪仍有未解的 blocker／major）。審查員指出「範圍外改動」且實質成立 → 直接升級，不走修正。

## 階段 5：個資掃描（出口）

`--set 個資掃描`。取指紋 → 派 `pii-guard`，prompt：`工單 / 專案 / 輪次: j`（j 從 1 起）→ 再取指紋。讀 `pii-j.md` 檔頭：

- `乾淨` 且 `secret_paths: 0` → 完成。
- `有個資已commit` → 立即升級（要改歷史，不能自動處理）。
- `有疑似`，或 `secret_paths` > 0 → 只允許一次修正：派 `ticket-engineer` `模式: fix pii-j.md`，再派 `pii-guard` 第 j+1 輪。仍非乾淨 → 升級。
- 個資修正只是換成假資料，**不重跑審查**；最後回報要註明這點。

## 完成

`bin/console status <n> --set 待人工交付 --severity <最終> --note "<一句話>"`。回報：

```
工單 <n>（<專案>）：待人工交付  嚴重度 <低|中>
決策：<approach 一句>（信心 <x>）
變更：<N> 個檔案；審查 <k> 輪（最終 <verdict>）；個資掃描 <verdict>
事後可瀏覽：<中嚴重度的原因、minor 發現、分析師未化解的分歧；沒有就寫無>
下一步：你確認後要 commit，依專案端技能第 7 節；我不會自己 commit 或 push。
```

## 升級（唯一會主動打擾使用者的地方）

1. 寫 `_ticket/escalation.md`：檔頭 `resume_at: <繼續的階段，例如 已裁決／實作中／審查中>`；內文：觸發的協議條件編號與一句話原因、目前狀況、**兩個選項與你的建議**。內容去識別化。
2. `bin/console status <n> --set 已升級 --severity <x> --note "<條件編號：一句話>"`。
3. 通知：先 `ToolSearch` 載入 `PushNotification`，可用就推播**一次**，內容只寫「工單 <n> 需要你裁示：<條件一句話>」；載入或呼叫失敗就略過，不要因此卡住。
4. 在對話中回報（格式如下），然後停止這張工單：

```
⚠ 工單 <n> 需要你裁示
原因：<協議第 x 條>：<一句話>
選項：A. …  B. …
建議：<A|B>，因為 …
詳情：worktrees/<n>/_ticket/escalation.md
回覆：/dispatch resume <n> <你的裁示，例如「採 A」>
```

## resume

先 `bin/console status <n>` 看階段。

- `已升級`：讀 `escalation.md`。若檔頭 `kind: 額度保護`：不需要裁示、不改 `decision.md`，直接從 `resume_at` 繼續（進入高耗階段前照樣先檢查額度，仍暫停就再停一次並告知）。否則讀 `resume_at`。把使用者的裁示以去識別化的文字附在 `escalation.md` 的「## 人工裁示」段（若裁示含個資，改寫成去識別化描述，不要原樣寫入）。若升級來自 `decision.md`，用 Edit 在其檔頭把 `escalate: true` 改成 `false` 並加一行 `resolved_by: 人工裁示`；使用者裁示若擴大允許範圍，同時更新檔頭 `files`。從 `resume_at` 繼續；後續階段的嚴重度與閘門照常。
- `待spec`：重新檢查 spec 閘門，通過就從階段 3 繼續。
- `待讀取`：重跑階段 1（`reopen` 之後也是停在這裡）。
- 其他中間階段（工作階段中斷）：已有且完整的產出檔直接重用，缺的才重跑；審查／個資的輪次看 `review-*.md`、`pii-*.md` 已有幾份。
- `待人工交付`／`已釋放`：已完成，告知即可；驗收後要調整請使用者用 `/dispatch reopen <工單>`，不要自己判斷重跑。

## reopen（驗收後要調整：開新一輪）

使用者明說 `reopen` 才做；一次一張工單。

1. `bin/console status <n>`：階段必須是 `待人工交付` 或 `已釋放`，否則拒絕並指向 `resume`（進行中的工單不開新一輪）。
2. `bin/console reopen <n> [-p <專案>]`。console 會：把前一輪的交接檔封存到 `_ticket/round-<N>/`（只搬不刪；遮蔽版工單複製留底）、為既有分支寫新的 `prior-<專案>.json`（本輪起點＝分支目前的提交，worktree 還在也一樣）、把階段退回 `待讀取` 並清掉嚴重度。**失敗就原文回報後停止，不繞過**：worktree 有未提交變更、查不到遠端分支狀態、`round-<N>` 已存在、專案未登錄。
3. 從「階段 1」重新開始：重新抓 Redmine 才讀得到驗收後的新留言。分析與裁決照協議「回頭調整的工單」：前一輪的 `round-*/` 只當背景，現況一律以程式碼與本輪的 `masked.md` 為準；本輪起點用 `prior-<專案>.json` 的 `head`。
4. 完成回報多一行：`輪次：第 <N> 輪；本輪起點 <head 前 9 碼>；前一輪封存於 round-<N-1>`。

## 速查

```bash
bin/console ticket list             # Redmine 上分派給我、未結案的工單
bin/console status                  # 全部工單進度
bin/console status <n>              # 單張歷程
bin/console wt fingerprint <n>      # 工作樹指紋（唯讀角色前後比對）
bin/console scan <n> -p <專案>       # 個資掃描
```

各角色用的 model 在 `.claude/agents/*.md` 的 frontmatter 調整（目前專案管理員與個資守門員用 sonnet，其餘繼承目前工作階段）。
