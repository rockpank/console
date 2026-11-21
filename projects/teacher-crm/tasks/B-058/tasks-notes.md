---
verdict: 待釐清
---

# B-058 tasks 階段：停在 SOP 前置缺口

## 查清的事實（已實查，src／tests grep）

- `TIMEOUT_SECONDS` 只在 `src/crm/line/client.py` 定義（第 9 行）並只被同檔 `urllib_transport`（第 49 行）使用；tests 內沒有任何對 `TIMEOUT_SECONDS` 的引用或 monkeypatch。搬走不影響測試。
- Jotform（`src/crm/jotform/client.py`）沒有自己的 timeout 值，只在第 137 行函式內匯入 `crm.line.client.urllib_transport`、第 139 行當預設 transport；搬移後 Jotform 沿用共用的 15 秒，行為不變。
- 測試只有 `tests/unit/test_line_transport.py:9` 從 `crm.line.client` 匯入 `urllib_transport`（另有 `HttpLineClient`、`LineApiError`）；該檔的 `monkeypatch.setattr("crm.line.client.API_BASE", …)` 與搬移無關。若 line/client.py 改為 `from crm.http import urllib_transport`，名稱仍可從 `crm.line.client` 取得，舊測不改也綠；要做到「僅改匯入路徑」則把第 9 行拆成 `crm.http` 與 `crm.line.client` 兩行。兩種做法由 pm／調度者擇一。

## 阻塞（SOP 硬性要求，無法滿足）

- `tasks/SKILL.md` Phase 1 第 3 點：「無 `testplan.md` 停止，請先 `/testplan`」。
- `validate_artifacts.py`：tasks／analyze 以 `quickfix.md` 或 `testplan.md` 為案例來源；`all` 需 `spec.md`＋`testplan.md`（testplan 需「## 共用前置資料」「## 建議 TDD 實作順序」）。純搬移沒有行為案例，要寫 testplan 就得杜撰 RED 或把「匯入路徑」當案例，這正是不想做的事。
- 因此未產出 `specs/023-shared-http-transport/` 任何檔案，未跑 validator，未改 src。

## 待釐清（請調度者／使用者決定其一）

1. 授權 qa-engineer 寫一份精簡 testplan（案例＝既有 `test_line_transport.py` 的 Keep／Modify，無 Add／RED；Modify 僅匯入路徑走 ALIGN→GREEN），之後我再產 spec.md（精簡）、tasks.md、analyze-report.md。
2. 或承認此項為「不走切片」的純 refactor，允許以 Setup／Foundational 類 task 直接實作並跳過 testplan／analyze（需使用者同意偏離 skill SOP）。
3. 補充 (1) 的小問題：line client 是否保留對 `urllib_transport` 的 re-export（上述兩種匯入做法）。
