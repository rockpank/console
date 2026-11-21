---
resume_at: 開發中
resolved: true
---

# 升級：B-026 —— QA 第 2 輪失敗（測試缺口 D-1），已達協議第 3 條的 2 輪上限

- 條件：協議第 4 節第 3 條（第 2 輪仍未過）。
- 原因：QA 第 2 輪 verdict 失敗。產品行為全數正確（1307 通過、覆蓋率 98.17%、併發測試穩定、M-1／M-2 行為皆如預期），**唯一缺陷是測試缺口 D-1（中）**：QA 在暫存複本上實測，兩種破壞仍全綠——(E) `create_order` 落敗改拋一般 `OrderError`；(I) 拿掉 `register_walk_in` 的 `except ConcurrentOrderError` 區塊。原因是 `attendance.py:166-168` 沒有任何測試走到：現場報名併發測試的落敗方在 Student／Registration 唯一約束就被擋，從沒走到 `create_order` 落敗；建單併發測試只斷言 `isinstance OrderError`，分不出一般 `OrderError` 與子類。
- 影響：這條路徑日後退化時，現場報名會拋出原始 `OrderError` 而非 `AttendanceError`，views 以 `AttendanceError` 捕捉時會變 500。
- 附帶（已無法補救、僅記錄）：第 2 輪的 6 個新測試是實作後才補寫，無紅燈紀錄，屬 TDD 違規；QA 以破壞實測證明其中 8 種破壞會轉紅，退化偵測有效。
- 目前狀況：資安第 2 輪通過；QA 報告 `qa-2.md`。

## 選項

- **A（建議）**：再做一次**窄範圍**修補：只補 QA 建議的兩個測試——(1) 用 monkeypatch 讓 `ensure_intro_order` 拋 `ConcurrentOrderError`，斷言 `register_walk_in` 拋 `AttendanceError` 且訊息含「重新整理」；(2) 建單併發測試加 `assert isinstance(errors[0], ConcurrentOrderError)`。只改測試檔，不動產品碼；補完 `attendance.py` 應回到 100%。之後 QA 只做窄範圍驗證（重跑該測試檔、並對 E、I 兩種破壞各實測一次，確認會轉紅），不重跑資安。
- **B**：照現在合併，把 D-1 記進 backlog 當後續項目。風險：`attendance.py:166-168` 目前無測試保護。

## 人工裁示

使用者裁示（2026-11-19）：選 A——做窄範圍修補，只補 QA 建議的兩個測試（不動產品碼）；QA 之後只做窄範圍驗證，不重跑資安。
