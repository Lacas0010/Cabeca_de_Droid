import os
import re
import json
from typing import Dict
from core.config import get_resource_path

TRANSLATIONS: Dict[str, str] = {}
try:
    trans_path = get_resource_path("traducoes.json")
    if os.path.exists(trans_path):
        with open(trans_path, "r", encoding="utf-8") as f:
            TRANSLATIONS = json.load(f)
except Exception as te:
    print(f"[WARN] Não foi possível carregar traducoes.json: {te}")

def traduzir_item(nome_ingles: str) -> str:
    """Traduz nomes de armas, relíquias e atributos do inglês para PT-BR."""
    if not nome_ingles:
        return nome_ingles
        
    nome_clean = nome_ingles.strip()
    
    # Extrai sufixos comuns como (4-PC), (2-PC), (S1), (R5)
    suffix = ""
    match_suffix = re.search(r'\s*(\((?:\d-PC|\d-pc|S\d|R\d)\))\s*$', nome_clean, re.I)
    if match_suffix:
        suffix = " " + match_suffix.group(1)
        nome_clean = nome_clean[:match_suffix.start()].strip()
        
    # Tenta correspondência exata no dicionário
    if nome_clean in TRANSLATIONS:
        return TRANSLATIONS[nome_clean] + suffix
        
    # Tenta correspondência case-insensitive
    nome_lower = nome_clean.lower()
    for eng_key, pt_val in TRANSLATIONS.items():
        if eng_key.lower() == nome_lower:
            return pt_val + suffix
            
    # Tenta substituir termos dentro de expressões maiores (como em status principais)
    traduzido = nome_clean
    for eng_key, pt_val in TRANSLATIONS.items():
        if len(eng_key) < 30:
            pattern = re.compile(rf'\b{re.escape(eng_key)}\b', re.IGNORECASE)
            traduzido = pattern.sub(pt_val, traduzido)
            
    return traduzido + suffix
