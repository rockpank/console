# 從 tests/test_mask_secrets.py 移出（依賴已搬走的 scan 模組）

    def test_scan_excerpt_is_masked(self):
        hits = scan.scan_lines("emma/app/Config/x.php", [(7, f"'password' => '{FAKE_PW}',")])
        self.assertEqual(len(hits), 1)
        source, no, cats, excerpt = hits[0]
        self.assertEqual((source, no, cats), ("emma/app/Config/x.php", 7, [SECRET]))
        self.assertNotIn(FAKE_PW, excerpt)

