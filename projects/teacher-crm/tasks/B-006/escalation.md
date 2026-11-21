---
resume_at: 規劃中
resolved: true
---

# B-006 升級紀錄

- 協議第 4 節條件 1：backlog 要求「現場報名『已現場收款』不得預設勾選」，但 `specs/TEST_LIST.md` 明定預設勾選（使用者先前決定），改預設屬改規格，需使用者拍板。

## 人工裁示

- 2026-11-17：使用者選 A——改規格，現場報名「已現場收款」預設改為不勾選。
- 範圍：快速路線（規格編號 042）；`project_attendance.html` 拿掉 `checked`，同步修改 `specs/TEST_LIST.md` 相關條目與 `tests/db/test_attendance_pages.py`；不改 model、不新增 URL。
