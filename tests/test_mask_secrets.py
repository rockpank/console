"""祕密（金鑰、密碼、token、私鑰、連線字串帳密）偵測。以下全是假值。"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from console_cli import mask  # noqa: E402
from console_cli.mask import SECRET, detect, mask_text  # noqa: E402

# 假值：長度與格式像，但不是任何真實憑證
FAKE_AWS = "AKIA" + "ABCDEFGHIJKLMNOP"
FAKE_GH = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
FAKE_JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJmYWtlIn0.c2lnbmF0dXJl"
FAKE_PW = "Zx9-fake-Pw1"
FAKE_KEY = "-----BEGIN RSA PRIVATE KEY-----\nMIIBOgIBAAJBAKfakefakefake\nAAECQBfakefakefake\n-----END RSA PRIVATE KEY-----"


class SecretMaskedTests(unittest.TestCase):
    def assertMasked(self, text: str, secret: str):
        out = mask_text(text)
        self.assertNotIn(secret, out, text)
        self.assertIn(SECRET, out, text)
        self.assertEqual(detect(text), [SECRET] + [c for c in detect(text) if c != SECRET])  # [SECRET] 一定列出
        self.assertIn(SECRET, detect(text))

    def test_fixed_format_tokens(self):
        for secret in (FAKE_AWS, FAKE_GH, FAKE_JWT, "sk_live_" + "abcdef0123456789ABCD", "xoxb-" + "1234567890-abcdefghij"):
            self.assertMasked(f"找到 {secret} 這個值", secret)

    def test_private_key_block_multiline_and_truncated(self):
        out = mask_text(f"前\n{FAKE_KEY}\n後")
        self.assertEqual(out, f"前\n{SECRET}\n後")
        truncated = "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEfake"
        self.assertEqual(mask_text(truncated), SECRET)
        # 逐行掃描時 BEGIN 那一行就要命中
        self.assertIn(SECRET, detect("-----BEGIN RSA PRIVATE KEY-----"))

    def test_url_credentials_do_not_leave_email_fragment(self):
        out = mask_text(f"mysql://root:{FAKE_PW}@db.example.com/app")
        self.assertEqual(out, f"mysql://{SECRET}@db.example.com/app")
        self.assertNotIn("[EMAIL]", out)

    def test_authorization_header(self):
        self.assertMasked("Authorization: Bearer abc123def456ghi789jkl", "abc123def456ghi789jkl")
        self.assertMasked("Authorization: Basic dXNlcjpmYWtlcGFzczEyMw==", "dXNlcjpmYWtlcGFzczEyMw")

    def test_name_value_forms(self):
        forms = [
            f"DB_PASSWORD={FAKE_PW}",
            f'"password": "{FAKE_PW}"',
            f"'password' => '{FAKE_PW}',",
            f"password: {FAKE_PW}",
            f"REDMINE_API_KEY={'0123456789abcdef' * 2}",
            f"--password={FAKE_PW}",
            f"https://x.example.com/api?api_key={FAKE_PW}&a=1",
            f"aws_secret_access_key = {FAKE_PW}",
            f"X-Redmine-API-Key: {FAKE_PW}",
            f"export MYSQL_ROOT_PASSWORD='{FAKE_PW}'",
            f"db_pass={FAKE_PW}",
        ]
        for text in forms:
            with self.subTest(text=text):
                out = mask_text(text)
                self.assertNotIn(FAKE_PW, out)
                self.assertNotIn("0123456789abcdef", out)
                self.assertIn(SECRET, out)

    def test_name_is_kept_value_is_masked(self):
        self.assertEqual(mask_text(f"password={FAKE_PW}"), f"password={SECRET}")
        self.assertEqual(mask_text(f"'token' => '{FAKE_PW}'"), f"'token' => {SECRET}")

    def test_chinese_forms(self):
        self.assertMasked(f"測試帳號密碼：{FAKE_PW}，請登入", FAKE_PW)
        self.assertMasked(f"金鑰為 {FAKE_PW}", FAKE_PW)
        self.assertMasked(f"密碼={FAKE_PW}", FAKE_PW)

    def test_secrets_masked_before_pii_rules(self):
        # 值裡剛好像電話／長數字，也要整個被當祕密處理
        self.assertEqual(mask_text("password=0912345678"), f"password={SECRET}")

    def test_idempotent(self):
        once = mask_text(f"password={FAKE_PW} 與 {FAKE_AWS}")
        self.assertEqual(mask_text(once), once)


class NotSecretTests(unittest.TestCase):
    """常見的程式碼與句子不能誤判，否則掃描會一直把流程卡在「有疑似」。"""

    CASES = [
        "$password = $this->request->data['password'];",
        "'password' => $password,",
        "$token = $this->Auth->user('token');",
        "password: string",
        "password: required",
        "password: ****",
        "'password' => 'dummy-abc123',",
        "password=example-password",
        "'token' => null,",
        "auth_token_ttl: 3600",
        "PWD=/opt/femashr/console",
        "compass: 123456",
        "$h = password_hash($plain, PASSWORD_DEFAULT);",
        "if ($password == 'abc12345') {",
        "if ($password != $confirm) {",
        "'type' => 'password',",
        "<input type=\"password\" name=\"password\" value=\"\">",
        "Basic functionality overview",
        "使用者回報密碼錯誤",
        "忘記密碼 reset 流程",
        "password: ${DB_PASSWORD}",
        "password: {{ secret }}",
        "https://example.com:8080/path",
        "員工編號 E0123 請假 3 天",
        "",
    ]

    def test_not_flagged(self):
        for text in self.CASES:
            with self.subTest(text=text):
                self.assertNotIn(SECRET, detect(text))
                self.assertNotIn(SECRET, mask_text(text))


class SecretReportingTests(unittest.TestCase):
    def test_detect_never_returns_original(self):
        self.assertEqual(detect(f"password={FAKE_PW}"), [SECRET])

    def test_sensitive_custom_field_names_dropped(self):
        for name in ("密碼", "API Key", "api_key", "Token", "金鑰", "客戶名稱"):
            self.assertTrue(mask.SENSITIVE_FIELD_NAMES.search(name), name)
        for name in ("優先順序", "環境", "版本"):
            self.assertFalse(mask.SENSITIVE_FIELD_NAMES.search(name), name)


if __name__ == "__main__":
    unittest.main()
