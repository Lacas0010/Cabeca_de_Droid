import os
import re
import json
from typing import Dict
from core.config import get_resource_path

TRANSLATIONS: Dict[str, str] = {}
REVERSE_TRANSLATIONS: Dict[str, str] = {}
try:
    trans_path = get_resource_path("traducoes.json")
    if os.path.exists(trans_path):
        with open(trans_path, "r", encoding="utf-8") as f:
            TRANSLATIONS = json.load(f)
            REVERSE_TRANSLATIONS = {v.lower().strip(): k for k, v in TRANSLATIONS.items()}
except Exception as te:
    print(f"[WARN] Não foi possível carregar traducoes.json: {te}")


def traduzir_item(nome_item: str, lang: str = "pt") -> str:
    """Traduz nomes de armas, relíquias e atributos do inglês para PT-BR (ou vice-versa se lang='en')."""
    if not nome_item:
        return nome_item

    nome_clean = nome_item.strip()

    # Extrai sufixos comuns como (4-PC), (2-PC), (S1), (R5)
    suffix = ""
    match_suffix = re.search(r"\s*(\((?:\d-PC|\d-pc|S\d|R\d)\))\s*$", nome_clean, re.I)
    if match_suffix:
        suffix = " " + match_suffix.group(1)
        nome_clean = nome_clean[: match_suffix.start()].strip()

    if lang == "en":
        # Se solicitado em inglês e o termo estiver em português, reverte
        nome_lower = nome_clean.lower()
        if nome_lower in REVERSE_TRANSLATIONS:
            return REVERSE_TRANSLATIONS[nome_lower] + suffix
        return nome_clean + suffix

    # Tenta correspondência exata no dicionário (EN -> PT)
    if nome_clean in TRANSLATIONS:
        return TRANSLATIONS[nome_clean] + suffix

    # Tenta correspondência case-insensitive (EN -> PT)
    nome_lower = nome_clean.lower()
    for eng_key, pt_val in TRANSLATIONS.items():
        if eng_key.lower() == nome_lower:
            return pt_val + suffix

    # Tenta substituir termos dentro de expressões maiores (como em status principais)
    traduzido = nome_clean
    for eng_key, pt_val in TRANSLATIONS.items():
        if len(eng_key) < 30:
            pattern = re.compile(rf"\b{re.escape(eng_key)}\b", re.IGNORECASE)
            traduzido = pattern.sub(pt_val, traduzido)

    return traduzido + suffix
