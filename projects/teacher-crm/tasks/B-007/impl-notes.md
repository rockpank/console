status: done
tests: 通過

# B-007 impl-notes（統一訊息元件，specs/012-unify-message-component）

完成：T001–T010（BE-API-01/02/03 + Gate），tasks.md 已勾 [X]。
紅燈：新測試檔先跑 10 failed（class/role 錯、樣板仍有迴圈、CSS 無 warning/info），綠燈後 12 passed。
做法：base.html `<main>` 內 content 前統一渲染訊息（error→alert error/role=alert，warning→alert warning/role=alert，success→alert ok/status，info→alert info/status）；18 個樣板移除 messages 迴圈；補亮暗 --warn/--info 變數與 .alert.warning/.info；LINE、藍新提醒改 warning（role=note 保留），模擬金流改 info（role=note 保留）。
品質關卡：ruff check 通過、format --check 189 files 已格式化；pytest unit+db 915 passed，覆蓋率 97%；manage.py check 無問題；makemigrations --check --dry-run 無變更；codemap 已更新、check OK。未跑 test-integration（依規則）。
與規格差異：project_jotform_settings 的 localhost 提醒原為 role="alert"，規格寫 role="note" 保留，故維持原 role="alert"（改為 alert warning），測試接受 note 或 alert。其餘三處 role="note" 不變。
變更：base.html、manage_base.html 與 17 個樣板（fake_checkout、project_access/attendance/follow_ups/front_course/jotform_settings/jotform_submissions/line_settings/message_templates/notifications/payment_settings/payments/products/reschedule/session_detail/sessions/student_edit/students）、tests/db/test_messages_component.py（新）、specs/012-.../tasks.md、docs/code_map/*（指令產生）。未動 views/forms/checkout/model/urls/conftest。
