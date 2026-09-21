import re
from typing import Any

# Padrões de expressões regulares para higienização (Redaction)
REDACTION_PATTERNS = [
    # Tokens de sessão HoYoLAB
    (re.compile(r'(ltoken(?:_v2)?\s*=\s*)([^;,\s&\'"]+)', re.IGNORECASE), r'\1***[LTOKEN_REDACTED]***'),
    (re.compile(r'(cookie_token(?:_v2)?\s*=\s*)([^;,\s&\'"]+)', re.IGNORECASE), r'\1***[COOKIE_TOKEN_REDACTED]***'),
    (re.compile(r'(account_id(?:_v2)?\s*=\s*)([^;,\s&\'"]+)', re.IGNORECASE), r'\1***[ACCOUNT_ID_REDACTED]***'),
    (re.compile(r'(ltuid(?:_v2)?\s*=\s*)([^;,\s&\'"]+)', re.IGNORECASE), r'\1***[LTUID_REDACTED]***'),
    
    # Chaves de API Groq (gsk_...)
    (re.compile(r'gsk_[a-zA-Z0-9_-]{10,}', re.IGNORECASE), 'gsk_***[API_KEY_REDACTED]***'),
    
    # Chaves de API Google Gemini (AIzaSy...)
    (re.compile(r'AIzaSy[a-zA-Z0-9_-]{10,}', re.IGNORECASE), 'AIzaSy***[API_KEY_REDACTED]***'),
    
    # Cabeçalhos Authorization Bearer
    (re.compile(r'(Bearer\s+)[a-zA-Z0-9_\-\.]{15,}', re.IGNORECASE), r'\1***[BEARER_REDACTED]***')
]

def sanitize_log(msg: Any) -> str:
    """
    Higieniza qualquer mensagem de log ou texto de traceback,
    removendo tokens de autenticação, cookies e chaves de API sensíveis.
    """
    if msg is None:
        return ""
    text = str(msg)
    
    for pattern, replacement in REDACTION_PATTERNS:
        text = pattern.sub(replacement, text)
        
    return text

def safe_log_print(msg: Any, *args, **kwargs) -> None:
    """Wrapper para print() tradicional que aplica sanitização automática."""
    clean_msg = sanitize_log(msg)
    clean_args = [sanitize_log(a) for a in args]
    print(clean_msg, *clean_args, **kwargs)
