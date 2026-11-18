"""High-recall regular expressions for emergency detection across English, Hindi, and Hinglish."""

import re

# English emergency regex patterns
EN_PATTERNS = [
    r"\b(?:chest\s+(?:pain|pressure|tightness)|heart\s+attack|cardiac\s+arrest)\b",
    r"\b(?:can'?t\s+breathe|cannot\s+breathe|difficulty\s+breathing|shortness\s+of\s+breath|gasping|suffocat(?:ing|ed)|choking)\b",
    r"\b(?:collapsed|unresponsive|unconscious|passed\s+out|fainted|loss\s+of\s+consciousness)\b",
    r"\b(?:severe\s+bleeding|bleeding\s+(?:profusely|heavily|unstoppably)|blood\s+gushing)\b",
    r"\b(?:stroke|slurred\s+speech|facial\s+droop|face\s+drooping|arm\s+weakness|paralysis)\b",
    r"\b(?:seizure|convulsion|having\s+a\s+fit)\b",
    r"\b(?:suicide|kill\s+myself|end\s+(?:my\s+life|it\s+all)|want\s+to\s+die)\b",
]

# Hindi (Devanagari) emergency regex patterns
HI_PATTERNS = [
    r"(?:सीने\s*में\s*दर्द|छाती\s*में\s*दर्द|दिल\s*का\s*दौरा)",
    r"(?:सांस\s*नहीं\s*आ\s*रही|सांस\s*लेने\s*में\s*(?:दिक्कत|तकलीफ)|दम\s*घुट)",
    r"(?:बेहोश|अचेत|गिर\s*(?:गया|पड़ा)|होश\s*नहीं)",
    r"(?:बहुत\s*खून|खून\s*बह\s*रहा|रक्तस्राव)",
    r"(?:दौरा\s*पड़|मिर्गी)",
    r"(?:आत्महत्या|जान\s*(?:देना|लेना)|मरना\s*चाहता)",
]

# Hinglish (Romanised Hindi/English mix) emergency regex patterns
HINGLISH_PATTERNS = [
    r"\b(?:seene\s*m(?:ein|e)\s*dard|chaati\s*m(?:ein|e)\s*dard|dil\s*ka\s*daura)\b",
    r"\b(?:saans\s*nah?i\s*aa\s*rah?i|saans\s*lene\s*m(?:ein|e)\s*(?:dikkat|takleef)|dam\s*ghut)\b",
    r"\b(?:behosh|gir\s*gaya|hosh\s*nah?i|koi\s*response\s*nah?i)\b",
    r"\b(?:khoon\s*bah\s*raha|bahut\s*zyada\s*khoon|heavy\s*bleeding)\b",
    r"\b(?:daura\s*pad\s*gaya|seizure\s*aa\s*raha)\b",
    r"\b(?:aatmhatya|jaan\s*dena|marna\s*chahta|suicide\s*karna)\b",
]

ALL_PATTERNS = EN_PATTERNS + HI_PATTERNS + HINGLISH_PATTERNS
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in ALL_PATTERNS]


def is_regex_emergency(text: str) -> bool:
    """Return True if text matches any high-recall emergency regex pattern."""
    if not text:
        return False
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            return True
    return False
