# B-037 pm 交接

資格判定：`/quickfix` 不適用（無程式行為、無 RED/GREEN 切片），依 work-plan 批次 20 改走 pm 直接修訂文件，不開 043 套件。

變更檔（worktree `worktrees/B-037/teacher-crm/`，僅 specs/）：
- `specs/SITEMAP.md`：頂部校正說明與 Q5；四缺頁標「要做（尚未實作）」；Google 整合標已撤回；新增 1.1 對外端點清單；JOSTFOTM→Jotform、銷講→前端課（保留原 SOP 文件名稱與說明中的舊稱）
- `specs/001-*/spec.md`、`003-*/spec.md`、`004-*/spec.md`：狀態欄；003／004 補 CASCADE 理由；004 補 Q6（時區 America/New_York）與上線前實測待辦
- `specs/TDD_PROGRESS.md`、`specs/TEST_LIST.md`：頂部標歷史紀錄；TEST_LIST 重複的第 15 節標題改 15A

驗證（調度者代跑，於 worktree）：
python3 .agents/skills/_shared/validate_artifacts.py all --package 001-ci-quality-automation（003-jotform-session-sync、004-jotform-registration-payment 同）

待 B-038：004 的 tasks.md T002 與 system-analyze/integration-plan.md 仍寫 Asia/Taipei。

D-1 已修、D-2 使用者接受
