---
task: B-027
role: pm
status: done
date: 2026-11-17
---

# B-027 規劃交接（pm）

- 產物（worktree 內）：`specs/008-fix-gateway-callback-parse-tests/quickfix.md`、`tasks.md`。**未驗證**：pm 無 Bash，沒跑 `validate_artifacts.py`，由調度者執行（已自查：無雙大括號、無禁用詞、3 切片、T001–T010 連號、有 ACCEPTANCE-GATE）。
- 路線判定：快速路線。Rule 1 五條皆符合（3 個預期行為、不改 model、不新增 URL、不改權限、不推翻 FR）。quickfix 沒有「須為缺陷修正」的限制；純補測由 `tdd/RULES.md` §RED已綠覆蓋率判準 Rule 2 處理（RED＝已綠覆蓋率補強、GREEN＝本則無實作）。套件名依命名判準用 `008-fix-` 前綴（MUST），與 work-plan 建議的 `008-test-...` 不同。
- 切片：BE-SVC-01 藍新解析異常、BE-SVC-02 綠界解析異常（同放新檔 `tests/unit/test_gateway_callback_parse_errors.py`）、BE-API-01 端點 400 且狀態不變＋A／B 專案隔離（新檔 `tests/db/test_gateway_notify_invalid_payload.py`）。不改既有測試與任何產品碼。
- 憲法 MUST 2/4/7/8/9 對照寫在 quickfix.md 末段。

## 假設與發現（需調度者知悉）

1. **backlog／work-plan 驗收 1 的文字不精確**：藍新 `Result` 為「合法 JSON 字串」時，程式（L99–100）會正常解析，不拋 `InvalidCallback`。本規格改為：L100 由「字串但非 JSON／缺 MerchantOrderNo」案例覆蓋，不另測正向案例。若要加正向對照（合法字串 Result 成功解析），需決定是否放同一檔（會使 BE-SVC-01 對應兩個函式，與 tdd 一案例一函式略有出入）。
2. **疑似缺陷（未納入測試，不順手修）**：藍新 `Amt` 若為 JSON 浮點數（如 1500.5），`int()` 會無聲截斷成 1500、不拋錯（憲法 MUST 8 精神：金額禁 float）。建議調度者視需要另開缺陷項；本任務不釘住此行為。
3. 行號（L99–103、L109–112、L95–99）為 worktree 現況。
4. 測試命令只用 Makefile 目標（無單檔參數），工程師需要時自行在容器內執行單檔 pytest，不能改 Makefile。
