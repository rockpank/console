---
verdict: 快速資格 不符
route: 轉精簡完整路線（單一 package、tasks 清單；規格編號 023 不變）
---

# B-058 /quickfix 資格判定

依 quickfix/RULES.md「資格判準 Rule 1」逐條：

| 條件 | 結果 | 說明 |
|---|---|---|
| 1-3 個預期行為 | 不符 | 本項是純搬移重構，沒有「行為」可寫成預期行為，也不是 bug／單一行為調整（skill 定位）。 |
| 不改 models.py | 符合 | 不動 model／migration。 |
| 不新增 URL／頁面／整合／排程 | 符合 | 無。 |
| 不改權限 | 符合 | 無。 |
| 不推翻既有 FR | 符合 | 行為不變。 |

關鍵原因：quickfix 的每個切片須是 RED/ALIGN→GREEN，且要有「預期 RED 原因」。純搬移不會產生行為上的紅燈，唯一可 RED 的是「匯入路徑」，屬人為湊切片，不符 skill 精神。work-plan 已預先規定此情況轉精簡完整路線。

依 RULES「不符即不寫任何檔案」：**未產出** `specs/023-…/quickfix.md`、`tasks.md`；未跑 validate_artifacts.py；未改 src、未碰 .env。worktree 內 `specs/` 目前無 023 套件。

## 現況事實（供後續 pm／tasks 使用）

- `src/crm/line/client.py`：`TIMEOUT_SECONDS = 15`（第 9 行）、`Transport` 型別（第 43 行）、`urllib_transport`（第 46-49 行，用 `TIMEOUT_SECONDS`）、`HttpLineClient` 預設 `urllib_transport`（第 65 行）。
- `src/crm/jotform/client.py:137` 在函式內 `from crm.line.client import urllib_transport`，第 139 行使用。
- 測試匯入 `urllib_transport`／`HttpLineClient`：`tests/unit/test_line_transport.py`（另有 `monkeypatch.setattr("crm.line.client.API_BASE", …)`）。其他測試匯入 `crm.line.client` 的 `FakeLineClient`、`LineApiError`、`QuotaInfo`、`PushResult`，不受影響。
- 注意：`TIMEOUT_SECONDS` 在 line client 內另被別處引用的話，搬移後須維持 15 且 line 端可被 `crm.line.client.TIMEOUT_SECONDS` 存取與否需確認（避免測試 monkeypatch 失效）；Jotform 是否另有自己的 timeout 值，tasks 階段要先查。

## 建議精簡完整路線 tasks 骨架（套件名建議 `specs/023-shared-http-transport/`）

1. 新增 `src/crm/http.py`：搬入 `Transport`、`TIMEOUT_SECONDS`（值 15）、`urllib_transport`（程式碼逐字搬移）。
2. `line/client.py`、`jotform/client.py` 改從 `crm.http` 匯入；Jotform 改為頂層匯入，兩者互不匯入。
3. `tests/unit/test_line_transport.py` 僅改匯入路徑（或維持 line 端 re-export 以免改測，由 pm 決定；工作計畫要求「僅匯入路徑」）。
4. `make codemap` → `make codemap-check` 無 STALE；lint、test（`JOTFORM_API_KEY` 假值）、check、makemigrations --check、覆蓋率 ≥ 95%。

待調度者決定：是否改派 pm 以「精簡完整路線」產出 `tasks.md`（含 testplan 精簡版）。
