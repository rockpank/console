route: 快速路線（資格 5 條全符合）
validate: 未執行（本角色無 Bash 工具，無法跑 validate_artifacts.py；請調度者或 engineer 開工前執行
  `python .agents/skills/_shared/validate_artifacts.py quickfix --package 016-import-size-limits` 與 `... tasks --package 016-import-size-limits`）

# B-025 PM notes

- 產物：worktrees/B-025/teacher-crm/specs/016-import-size-limits/{quickfix.md,tasks.md}；3 切片（BE-API-01 大小 2MB、02 列數 5000、03 name 100／address 255 逐列錯誤）。
- 套件名依調度者指定 `016-import-size-limits`；quickfix RULES 的命名是 `<NNN>-fix-<slug>`，validator 若檢查命名需改名。
- 範圍超出 work-plan：需動 `src/crm/domain/roster.py`（純邏輯放此處；importer.py 幾乎不動）。views.py 只改 `project_session_import` 內 file.size 檢查。
- 不改 model／migration／URL／權限。測試新增 `tests/db/test_import_limits.py`。
- 待確認：2MB／5000 沿用 sec 建議值；超長欄位採整批不匯入（沿用既有規則）。
