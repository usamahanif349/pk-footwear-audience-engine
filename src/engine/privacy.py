"""Remove personal details from comment text before it is saved or published:
phone numbers and other long digit runs (order numbers), e-mail addresses and @handles."""
import re

PATTERNS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[email]"),
    (re.compile(r"(?<![\w@])@[\w.\-]{2,}"), "@[user]"),
    # Pakistani mobile numbers (0300 1234567, +92 300-1234567, 923001234567)
    (re.compile(r"(?<!\d)(?:\+?92|0)?[\s-]?3\d{2}[\s-]?\d{7}(?!\d)"), "[number]"),
    # any other run of 7+ digits, e.g. order numbers (prices and years are shorter)
    (re.compile(r"(?<!\d)\d{7,}(?!\d)"), "[number]"),
]


def redact(text):
    t = str(text)
    for pat, rep in PATTERNS:
        t = pat.sub(rep, t)
    return t
