"""Hide secrets in text the agent reads (owner, 2026-11-04).

Every tool whose output reaches the agent (tools/vmssh.py run and logs,
tools/appapi.py call) passes it through here. It hides:

- the rest of a line after a secret word and a separator ("Client secret: x",
  "password=x", "token": "x", "admin password is x", "Bearer x"), and the
  next non-empty line after a label that ends its line ("Your password:");
  colour codes are removed first;
- random-looking strings anywhere (mixed-case with digits, long hex, UUIDs),
  which catches a value printed on its own line;
- private-key blocks, whole.

It errs toward hiding: a hidden value shows as [hidden], so the agent knows
something was there. It can't recognize every secret (a short, plain-word
password on a line of its own passes), so the rules about what the agent may
read still apply.
"""
import re

HIDDEN = "[hidden]"

SECRET_WORD = (r"secret|passw(?:or)?d|passphrase|(?:\b|_)pass\b|(?:\b|_)pwd\b|token|bearer|authorization|cookie|credential|salt"
               r"|(?:api|app|access|private|auth|encryption|signing|license|client)[_ -]?key")
# A secret word, maybe more word characters ("password_hash"), a closing quote, then a separator.
AFTER_WORD = re.compile(rf"(?i)((?:{SECRET_WORD})[\w-]*[\"']?\s*(?:[:=]|\s(?:is|was)\s)\s*)\S.*")
# A label ending its line ("Your admin password:"): the next non-empty line is the value.
LABEL_END = re.compile(rf"(?i)(?:{SECRET_WORD})[\w-]*[\"']?\s*[:=]\s*$")
COLOUR = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
AUTH_SCHEME = re.compile(r"(?i)(\bbearer\s+)\S+")
CANDIDATE = re.compile(r"[A-Za-z0-9+/=_-]{20,}")
HEXISH = re.compile(r"[0-9a-fA-F-]{32,}")
PEM_BEGIN = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
PEM_END = re.compile(r"-----END [A-Z0-9 ]*PRIVATE KEY-----")
KEY_NAME = re.compile(rf"(?i)({SECRET_WORD}|(?:^|_)key$)")


def _random_looking(part: str) -> bool:
    if len(part) < 20:
        return False
    if HEXISH.fullmatch(part) and sum(c.isdigit() for c in part) >= 4:
        return True
    upper, lower, digit = (any(c.isupper() for c in part), any(c.islower() for c in part),
                           any(c.isdigit() for c in part))
    if upper and lower and digit:
        return True
    return len(part) >= 32 and (upper or lower) and digit and len(set(part)) >= 16


def _hide_random(match: re.Match) -> str:
    text = match.group(0)
    # A path or URL is judged segment by segment, so its folder names stay readable.
    if text.startswith(("/", ".")) or "://" in text:
        return "/".join(HIDDEN if _random_looking(p) else p for p in text.split("/"))
    return HIDDEN if _random_looking(text) else text


def redact_line(line: str) -> str:
    line = AFTER_WORD.sub(lambda m: m.group(1) + HIDDEN, line)
    line = AUTH_SCHEME.sub(lambda m: m.group(1) + HIDDEN, line)
    return CANDIDATE.sub(_hide_random, line)


def redact_text(text: str) -> str:
    out, in_key, after_label = [], False, False
    for line in COLOUR.sub("", text).split("\n"):
        if after_label and line.strip():
            out.append(HIDDEN)
            after_label = False
            continue
        if LABEL_END.search(line):
            after_label = True
        if PEM_BEGIN.search(line):
            in_key = True
        if in_key:
            if PEM_END.search(line):
                in_key = False
            out.append(HIDDEN)
            continue
        out.append(redact_line(line))
    return "\n".join(out)


def redact_json(value, key: str = ""):
    """The same rules for parsed JSON: a value under a secret-like key is hidden whole."""
    if key and KEY_NAME.search(key):
        return HIDDEN
    if isinstance(value, dict):
        return {k: redact_json(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_json(v) for v in value]
    if isinstance(value, str):
        return redact_text(value)
    return value
