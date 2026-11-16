"""去識別化：工單文字進入對話之前先遮蔽。

兩類東西：
- 祕密（金鑰、密碼、token、私鑰、連線字串帳密）→ `[SECRET]`，最先處理。
- 「格式固定」的個資（身分證、電話、email、金額、長數字）。
姓名、公司名這類自由文字無法用規則可靠遮蔽——因此 Redmine 專案名稱、
使用者名稱、自訂欄位（客戶、聯絡人…）一律在 redmine.py 直接捨棄或改用 id。
"""
from __future__ import annotations

import re

SECRET = "[SECRET]"

# 有固定格式的祕密：整段換掉
_SECRET_TOKENS = re.compile(
    r"(?<![A-Za-z0-9])(?:"
    r"A(?:KIA|SIA|GPA|IDA|ROA|NPA|NVA|IPA)[A-Z0-9]{16}"                  # AWS access key id
    r"|gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,}"           # GitHub
    r"|xox[abposr]-[A-Za-z0-9-]{10,}"                                     # Slack
    r"|[sr]k_(?:live|test)_[A-Za-z0-9]{16,}"                              # Stripe
    r"|AIza[0-9A-Za-z_-]{35}"                                             # Google API key
    r"|sk-(?:ant-)?[A-Za-z0-9_-]{20,}"                                    # Anthropic／OpenAI 風格
    r"|eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"        # JWT
    r")(?![A-Za-z0-9])")

# 私鑰區塊（可跨行；被截斷時遮到結尾）。逐行掃描時，BEGIN 那一行就會命中。
_PRIVATE_KEY = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----[\s\S]*?(?:-----END [A-Z0-9 ]*PRIVATE KEY(?: BLOCK)?-----|\Z)")

# Authorization 標頭：Bearer 要 16 字以上且含數字；Basic 是 base64，要含數字或有 = 補位。避免誤傷一般英文
_BEARER = re.compile(r"(?i)\b(bearer)\s+(?=\S*\d)[A-Za-z0-9._~+/=-]{16,}")
_BASIC = re.compile(r"(?i)\b(basic)\s+(?:(?=\S*\d)[A-Za-z0-9+/]{16,}={0,2}|[A-Za-z0-9+/]{14,}={1,2})")

# 連線字串／網址裡的 帳號:密碼@
_URL_CREDENTIALS = re.compile(r"(?P<scheme>[A-Za-z][A-Za-z0-9+.-]*://)[^\s/:@]+:[^\s/@]+@")

# 「名稱 = 值」形式：只在名稱以這些字結尾、且值不像程式表達式／佔位符時才遮值（保留名稱，方便看欄位）
_SECRET_NAME = (r"(?:password|passwd|passphrase|pwd|(?<=[_.-])pass|secret(?:[_-]?access)?(?:[_-]?key)?"
                r"|token|api[_-]?key|access[_-]?key|private[_-]?key|auth[_-]?key)")
_SECRET_KV = re.compile(
    r"(?P<head>(?i:" + _SECRET_NAME + r")[\"']?\s*(?:=>|:=|[:=])(?![=~>:])\s*)"  # `::` 是類別常數，不是賦值
    r"(?P<val>\"[^\"\n]+\"|'[^'\n]+'|[^\s\"',;&)\]}<>]+)")
# 中文：密碼：xxx、金鑰為 xxx（值只取 ASCII，避免把後面的中文句子吃掉）
_SECRET_ZH = re.compile(r"(?P<head>(?:密碼|密鑰|金鑰|口令|權杖)\s*(?:[:：=]|是|為)\s*)(?P<val>[\x21-\x7e]{4,})")

# 明顯是假值／佔位符的不算祕密。測試資料想避開偵測，值用 dummy-／fake-／example- 開頭即可。
_FAKE_PREFIX = re.compile(
    r"(?i)^(?:dummy|fake|example|sample|demo|test|placeholder|changeme|redacted|your|todo|tbd|none|null|nil"
    r"|true|false|string|required|empty|\*{3,}|\.{3,}|x{3,}|-{3,})")
_FAKE_WORD = re.compile(r"(?i)^(?:password|passwd|secret|token|key)$")


_CODE_REF = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+")   # this.token、config.apiKey
_BARE_WORD = re.compile(r"[A-Za-z_]+")                         # 未加引號的純字母：變數或常數名


def _is_secret_value(val: str) -> bool:
    quoted = val[:1] in "\"'"
    v = val.strip("\"'")
    if len(v) < 4 or v[0] in "$<{%@[/~.":      # 變數、樣板、已遮蔽、路徑
        return False
    if re.search(r"\(|\[|->|::|\$\{|\{\{|%[sd]", v):  # 函式呼叫、陣列／物件存取、樣板
        return False
    if _CODE_REF.fullmatch(v) or (not quoted and _BARE_WORD.fullmatch(v)):
        return False
    return not (_FAKE_PREFIX.match(v) or _FAKE_WORD.match(v))


def _sub_kv(match: re.Match) -> str:
    return match.group("head") + SECRET if _is_secret_value(match.group("val")) else match.group(0)


# (規則, 取代內容)：取代內容可以是字串或函式。偵測與遮蔽用同一套，所以「命中」＝「真的會被換掉」。
_SECRET_RULES = [
    (_PRIVATE_KEY, SECRET),
    (_URL_CREDENTIALS, r"\g<scheme>" + SECRET + "@"),
    (_BEARER, r"\1 " + SECRET),
    (_BASIC, r"\1 " + SECRET),
    (_SECRET_TOKENS, SECRET),
    (_SECRET_KV, _sub_kv),
    (_SECRET_ZH, _sub_kv),
]

_RULES = [
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[EMAIL]"),
    (re.compile(r"(?<![A-Za-z0-9])[A-Za-z][12]\d{8}(?![A-Za-z0-9])"), "[ID]"),
    (re.compile(r"(?<!\d)(?:\+?886[-\s]?|0)9\d{2}[-\s]?\d{3}[-\s]?\d{3}(?!\d)"), "[PHONE]"),
    (re.compile(r"(?<!\d)0\d{1,2}[-\s]?\d{6,8}(?!\d)"), "[PHONE]"),
    (re.compile(r"(?:NT\$|NTD|\$)\s?\d[\d,]*(?:\.\d+)?"), "[AMOUNT]"),
    (re.compile(r"\d[\d,]*(?:\.\d+)?\s?元"), "[AMOUNT]"),
    (re.compile(r"(?<!\d)\d{10,}(?!\d)"), "[NUM]"),
]

# 啟發式：公司名、人名稱謂（寧可多遮，不漏）
_HEURISTICS = [
    (re.compile(r"[一-鿿]{2,12}(?:股份有限公司|有限公司|企業社|企業|工作室|商行|實業|集團)"), "[公司]"),
    (re.compile(r"[一-鿿]{2,3}(?:先生|小姐|女士|總經理|副總|協理|副理|經理|主任|老師|董事長)"), "[人名]"),
]

# 這些名稱的自訂欄位整個捨棄（值多半是客戶資料）
SENSITIVE_FIELD_NAMES = re.compile(
    r"客戶|公司|聯絡|電話|信箱|e-?mail|姓名|統編|地址|帳號|身分證|密碼|密鑰|金鑰|passw|secret|token|api.?key", re.I)

_terms: list[re.Pattern] = []


def load_terms(path) -> int:
    """載入使用者自填的遮蔽詞（一行一個，# 開頭為註解，不分大小寫）。檔案不存在視為沒有。"""
    _terms.clear()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (FileNotFoundError, OSError):
        return 0
    for line in lines:
        term = line.strip()
        if term and not term.startswith("#"):
            _terms.append(re.compile(re.escape(term), re.I))
    return len(_terms)


def detect(text: str | None) -> list[str]:
    """回傳命中的類別標籤（例如 [EMAIL]），絕不回傳原文。使用者遮蔽詞命中時標為 [已遮蔽]。"""
    if not text:
        return []
    found: list[str] = []
    if any(pattern.search(text) for pattern in _terms):
        found.append("[已遮蔽]")
    if any(pattern.sub(repl, text) != text for pattern, repl in _SECRET_RULES):
        found.append(SECRET)
    for pattern, label in _RULES + _HEURISTICS:
        if label not in found and pattern.search(text):
            found.append(label)
    return found


def mask_text(text: str | None) -> str:
    if not text:
        return ""
    for pattern in _terms:  # 使用者遮蔽詞最先處理
        text = pattern.sub("[已遮蔽]", text)
    for pattern, repl in _SECRET_RULES:  # 祕密先於個資：避免 user:pass@host 先被當成 email 而留下半截
        text = pattern.sub(repl, text)
    for pattern, repl in _RULES + _HEURISTICS:
        text = pattern.sub(repl, text)
    return text
