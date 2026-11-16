"""站點登入驗證：照 e2e 的 auth.setup.js 與登入頁的 JS 流程，用測試帳號做一次登入。

流程：GET 登入頁（取 session cookie）→ POST checkMfa（若要 MFA 就判失敗，測試帳號必須能直接帳密登入）
      → POST 登入 → 手動跟隨轉址 → 最後不在登入頁、頁面沒有登入表單即成功。

安全：帳密只存在記憶體，只放進 POST 本文；回傳的說明文字絕不含帳號、密碼或頁面內容。
連線直接打 127.0.0.1，但 SNI／Host 用站點網域，所以不需要 hosts 設定。
"""
from __future__ import annotations

import http.client
import json
import re
import socket
import ssl
import urllib.parse

TIMEOUT = 40
MAX_REDIRECTS = 5
_LOGIN_PATH_RE = re.compile(r"/accounts/login", re.I)
_BAD_CREDENTIALS_TEXT = "帳號/密碼錯誤"


class _Conn(http.client.HTTPConnection):
    """固定連到 connect_ip，Host 標頭與（TLS 時的）SNI 用站點網域。"""

    def __init__(self, host, port, connect_ip, tls):
        super().__init__(host, port, timeout=TIMEOUT)
        self._connect_ip, self._tls = connect_ip, tls

    def connect(self):
        sock = socket.create_connection((self._connect_ip, self.port), self.timeout)
        if self._tls:
            ctx = ssl._create_unverified_context()  # 本機自簽萬用字元憑證
            sock = ctx.wrap_socket(sock, server_hostname=self.host)
        self.sock = sock


class _Session:
    def __init__(self, host, port, connect_ip, tls):
        self.host, self.port, self.connect_ip, self.tls = host, port, connect_ip, tls
        self.cookies: dict[str, str] = {}

    def request(self, method, path, body=None, headers=None):
        conn = _Conn(self.host, self.port, self.connect_ip, self.tls)
        hdrs = {"User-Agent": "femashr-console-site-test", **(headers or {})}
        if self.cookies:
            hdrs["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        data = None
        if body is not None:
            data = urllib.parse.urlencode(body).encode()
            hdrs["Content-Type"] = "application/x-www-form-urlencoded"
        try:
            conn.request(method, path, body=data, headers=hdrs)
            resp = conn.getresponse()
            text = resp.read(500_000).decode("utf-8", errors="replace")
        finally:
            conn.close()
        for raw in resp.headers.get_all("Set-Cookie") or []:
            name, _, rest = raw.split(";", 1)[0].partition("=")
            if rest in ("deleted", ""):
                self.cookies.pop(name.strip(), None)
            else:
                self.cookies[name.strip()] = rest
        return resp.status, resp.headers, text


def check_login(host: str, port: int, base_path: str, username: str, password: str, *,
                tls: bool = True, connect_ip: str = "127.0.0.1",
                login_path: str = "Accounts/login", mfa_path: str = "Accounts/checkMfa") -> tuple[bool, str]:
    """回傳 (是否成功, 說明)。說明不含任何帳密或頁面內容。"""
    base = base_path if base_path.endswith("/") else base_path + "/"
    session = _Session(host, port, connect_ip, tls)
    form = {"data[Account][username]": username, "data[Account][passwd]": password, "data[remember]": "0"}
    try:
        status, _, _ = session.request("GET", base + login_path)
        if status != 200:
            return False, f"登入頁回 HTTP {status}"

        status, _, text = session.request("POST", base + mfa_path, form, {"X-Requested-With": "XMLHttpRequest"})
        try:
            if status == 200 and json.loads(text).get("isMfa") == 1:
                return False, "此帳號會觸發 MFA；測試帳號必須能直接帳密登入"
        except (ValueError, AttributeError):
            pass  # 不是 JSON（例如沒開 MFA 檢查）就直接登入

        status, headers, text = session.request("POST", base + login_path, form)
        path = base + login_path
        for _ in range(MAX_REDIRECTS):
            if status not in (301, 302, 303, 307, 308) or not headers.get("Location"):
                break
            target = urllib.parse.urlsplit(urllib.parse.urljoin(f"https://{host}{path}", headers["Location"]))
            if target.hostname != host:
                return False, "登入後轉址到不同網域，已停止"
            path = target.path + (f"?{target.query}" if target.query else "")
            status, headers, text = session.request("GET", path)
        else:
            return False, f"轉址超過 {MAX_REDIRECTS} 次"

        if status != 200:
            return False, f"登入後頁面回 HTTP {status}"
        if _LOGIN_PATH_RE.search(path) or 'id="loginForm"' in text:
            if _BAD_CREDENTIALS_TEXT in text:  # 應用程式自己的失敗訊息（登入頁本身不含這句）
                return False, "應用程式回報帳號／密碼錯誤（確認測試帳號存在於這個站點的資料庫、密碼正確）"
            return False, "登入後仍在登入頁（帳號被鎖定，或授權／資料庫問題）"
        return True, f"登入成功，落在 {urllib.parse.urlsplit(path).path}"
    except (OSError, http.client.HTTPException) as exc:
        return False, f"連線錯誤：{type(exc).__name__}"
