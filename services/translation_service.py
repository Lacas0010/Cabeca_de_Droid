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

CHARACTER_TRANSLATIONS: Dict[str, str] = {
    # HSR
    "Silver Wolf": "Loba Prateada",
    "Silver Wolf Lv. 999": "Loba Prateada Nv. 999",
    "Silver Wolf • Lv. 999": "Loba Prateada • Nv. 999",
    "Trailblazer": "Desbravador",
    "Trailblazer (Destruction)": "Desbravador (Destruição)",
    "Trailblazer (Preservation)": "Desbravador (Preservação)",
    "Trailblazer (Harmony)": "Desbravador (Harmonia)",
    "Trailblazer (Remembrance)": "Desbravador (Recordação)",
    "Trailblazer (Elation)": "Desbravador (Euforia)",
    "Trailblazer • Destruction": "Desbravador • Destruição",
    "Trailblazer • Preservation": "Desbravador • Preservação",
    "Trailblazer • Harmony": "Desbravador • Harmonia",
    "Trailblazer • Remembrance": "Desbravador • Recordação",
    "Trailblazer • Elation": "Desbravador • Euforia",
    "March 7th": "7 de Março",
    "March 7th (The Hunt)": "7 de Março (Caça)",
    "March 7th • The Hunt": "7 de Março • A Caça",
    "March 7th (Preservation)": "7 de Março (Preservação)",
    "March 7th • Preservation": "7 de Março • Preservação",
    "March 7th (Evernight)": "7 de Março (Noite Eterna)",
    "Evernight": "Noite Eterna",
    "Black Swan": "Cisne Negro",
    "Firefly": "Vaga-lume",
    "Sparkle": "Faísca",
    "Aventurine": "Aventurina",
    "The Herta": "A Herta",
    "The Dahlia": "A Dália",
    "Topaz & Numby": "Topaz e Dinheirinho",
    "Dan Heng • Imbibitor Lunae": "Dan Heng • Embebedor de Luna",
    "Tingyun • Fugue": "Tingyun • Fuga",
    "Dr. Ratio": "Doutor Ratio",
    "Sunday": "Domingo",
    "Acheron": "Aqueronte",
    # Genshin
    "Traveler": "Viajante",
    "Traveler (Anemo)": "Viajante (Anemo)",
    "Traveler (Geo)": "Viajante (Geo)",
    "Traveler (Electro)": "Viajante (Electro)",
    "Traveler (Dendro)": "Viajante (Dendro)",
    "Traveler (Hydro)": "Viajante (Hydro)",
    "Traveler (Pyro)": "Viajante (Pyro)",
    "Traveler (Cryo)": "Viajante (Cryo)",
    "Wanderer": "Andarilho",
    "Raiden Shogun": "Shogun Raiden",
    "Arlecchino": "Arlequino",
    "Mannequin": "Manequina",
    # ZZZ
    "Soldier 11": "Soldado 11",
    "Anby: Soldier 0": "Anby (Soldado 0)",
    "Cissia": "Císsia",
    "Orphie & Magus": "Orfeu & Magus",
}

PATH_TRANSLATIONS: Dict[str, str] = {
    # HSR Paths
    "Destruction": "Destruição",
    "The Hunt": "A Caça",
    "Erudition": "Erudição",
    "Harmony": "Harmonia",
    "Nihility": "Inexistência",
    "Preservation": "Preservação",
    "Abundance": "Abundância",
    "Remembrance": "Reminiscência",
    "Elation": "Euforia",
    # ZZZ Specialties
    "Attack": "Ataque",
    "Stun": "Atordoamento",
    "Anomaly": "Anomalia",
    "Support": "Suporte",
    "Defense": "Defesa",
    # Genshin Weapon Types
    "Sword": "Espada",
    "Claymore": "Espadão",
    "Polearm": "Lança",
    "Bow": "Arco",
    "Catalyst": "Catalisador",
}

STAT_TRANSLATIONS: Dict[str, str] = {
    "Speed": "Velocidade",
    "SPD": "VEL",
    "HP": "Vida",
    "Max HP": "Vida Máx.",
    "ATK": "ATQ",
    "Attack": "Ataque",
    "DEF": "DEF",
    "Defense": "Defesa",
    "CRIT Rate": "Taxa CRIT",
    "CRIT DMG": "Dano CRIT",
    "Break Effect": "Efeito de Quebra",
    "Effect Hit Rate": "Taxa de Acerto de Efeito",
    "Effect RES": "Resistência a Efeito",
    "Energy Regen Rate": "Taxa de Regeneração de Energia",
    "Energy Regen": "Regen. Energia",
    "Energy Recharge": "Recarga de Energia",
    "Elemental Mastery": "Proficiência Elemental",
    "Healing Bonus": "Bônus de Cura",
    "Incoming Healing": "Cura Recebida",
    "Anomaly Proficiency": "Proficiência de Anomalia",
    "Anomaly Mastery": "Maestria de Anomalia",
    "PEN Ratio": "Taxa de Perfuração",
    "Impact": "Impacto",
    "Physical DMG Boost": "Bônus de Dano Físico",
    "Fire DMG Boost": "Bônus de Dano de Fogo",
    "Ice DMG Boost": "Bônus de Dano de Gelo",
    "Lightning DMG Boost": "Bônus de Dano de Raio",
    "Wind DMG Boost": "Bônus de Dano de Vento",
    "Quantum DMG Boost": "Bônus de Dano Quântico",
    "Imaginary DMG Boost": "Bônus de Dano Imaginário",
    "Anemo DMG Bonus": "Bônus de Dano Anemo",
    "Pyro DMG Bonus": "Bônus de Dano Pyro",
    "Hydro DMG Bonus": "Bônus de Dano Hydro",
    "Electro DMG Bonus": "Bônus de Dano Electro",
    "Cryo DMG Bonus": "Bônus de Dano Cryo",
    "Geo DMG Bonus": "Bônus de Dano Geo",
    "Dendro DMG Bonus": "Bônus de Dano Dendro",
    "Electric DMG Boost": "Bônus de Dano Elétrico",
    "Ether DMG Boost": "Bônus de Dano Éter",
}

ELEMENT_TRANSLATIONS: Dict[str, str] = {
    "Physical": "Físico",
    "Fire": "Fogo",
    "Ice": "Gelo",
    "Lightning": "Raio",
    "Electric": "Elétrico",
    "Wind": "Vento",
    "Quantum": "Quântico",
    "Imaginary": "Imaginário",
    "Ether": "Éter",
    "Anemo": "Anemo",
    "Geo": "Geo",
    "Electro": "Electro",
    "Dendro": "Dendro",
    "Hydro": "Hydro",
    "Pyro": "Pyro",
    "Cryo": "Cryo",
}

# Mescla os dicionários base
for _d in (CHARACTER_TRANSLATIONS, PATH_TRANSLATIONS, STAT_TRANSLATIONS, ELEMENT_TRANSLATIONS):
    for k, v in _d.items():
        if k not in TRANSLATIONS:
            TRANSLATIONS[k] = v
        v_low = v.lower().strip()
        if v_low not in REVERSE_TRANSLATIONS:
            REVERSE_TRANSLATIONS[v_low] = k

# Sinônimos e variações comuns em português para busca reversa
_EXTRA_REVERSE = {
    "loba prateada": "Silver Wolf",
    "lobo prateado": "Silver Wolf",
    "loba prateada nv. 999": "Silver Wolf Lv. 999",
    "loba prateada nv 999": "Silver Wolf Lv. 999",
    "loba prateada (nv. 999)": "Silver Wolf (Lv. 999)",
    "loba prateada • nv. 999": "Silver Wolf • Lv. 999",
    "noite eterna": "Evernight",
    "7 de março (noite eterna)": "March 7th (Evernight)",
    "a dália": "The Dahlia",
    "a dalia": "The Dahlia",
    "manequina": "Mannequin",
    "anby (soldado 0)": "Anby: Soldier 0",
    "anby: soldado 0": "Anby: Soldier 0",
    "euforia": "Elation",
    "júbilo": "Elation",
    "jubilo": "Elation",
    "desbravador": "Trailblazer",
    "desbravadora": "Trailblazer",
    "desbravador(a)": "Trailblazer",
    "desbravador destruição": "Trailblazer (Destruction)",
    "desbravador preservação": "Trailblazer (Preservation)",
    "desbravador harmonia": "Trailblazer (Harmony)",
    "desbravador recordação": "Trailblazer (Remembrance)",
    "desbravador reminiscência": "Trailblazer (Remembrance)",
    "desbravadora destruição": "Trailblazer (Destruction)",
    "desbravadora preservação": "Trailblazer (Preservation)",
    "desbravadora harmonia": "Trailblazer (Harmony)",
    "desbravadora recordação": "Trailblazer (Remembrance)",
    "desbravadora reminiscência": "Trailblazer (Remembrance)",
    "viajante": "Traveler",
    "viajante anemo": "Traveler (Anemo)",
    "viajante geo": "Traveler (Geo)",
    "viajante electro": "Traveler (Electro)",
    "viajante dendro": "Traveler (Dendro)",
    "viajante hydro": "Traveler (Hydro)",
    "viajante pyro": "Traveler (Pyro)",
    "viajante cryo": "Traveler (Cryo)",
    "mochileiro": "Wanderer",
    "trotamundos": "Wanderer",
    "vagalume": "Firefly",
    "faisca": "Sparkle",
    "7 de marco": "March 7th",
    "topaz e dinhero": "Topaz & Numby",
    "topaz & dinhero": "Topaz & Numby",
    "topaz & dinheirinho": "Topaz & Numby",
    "dan heng embebedor de luna": "Dan Heng • Imbibitor Lunae",
    "embebedor de luna": "Dan Heng • Imbibitor Lunae",
    "tingyun fuga": "Tingyun • Fugue",
    "dr ratio": "Dr. Ratio",
    "soldado 11": "Soldier 11",
    "n.º 11": "Soldier 11",
    "nº 11": "Soldier 11",
    "n° 11": "Soldier 11",
    "número 11": "Soldier 11",
    "numero 11": "Soldier 11",
    "orfeu e magus": "Orphie & Magus",
    # Caminhos / Especialidades
    "caça": "The Hunt",
    "recordação": "Remembrance",
    "espada larga": "Claymore",
    # Stats
    "velocidade": "Speed",
    "vel": "SPD",
    "vida": "HP",
    "pv": "HP",
    "vida máx": "Max HP",
    "vida máx.": "Max HP",
    "pv máx.": "Max HP",
    "ataque": "ATK",
    "atq": "ATK",
    "defesa": "DEF",
    "taxa crit": "CRIT Rate",
    "taxa crítica": "CRIT Rate",
    "chance de crit": "CRIT Rate",
    "tx. cr": "CRIT Rate",
    "tx. crítica": "CRIT Rate",
    "tx. crit": "CRIT Rate",
    "dano crit": "CRIT DMG",
    "dano crítico": "CRIT DMG",
    "dano de crit": "CRIT DMG",
    "dano cr": "CRIT DMG",
    "efeito de quebra": "Break Effect",
    "quebra": "Break Effect",
    "taxa de acerto de efeito": "Effect Hit Rate",
    "acerto efeito": "Effect Hit Rate",
    "acerto de efeito": "Effect Hit Rate",
    "resistência a efeito": "Effect RES",
    "res a efeito": "Effect RES",
    "res efeito": "Effect RES",
    "taxa de regeneração de energia": "Energy Regen Rate",
    "taxa de reg. de energia": "Energy Regen Rate",
    "regeneração de energia": "Energy Regen Rate",
    "regen. energia": "Energy Regen",
    "recuperação de energia": "Energy Regen",
    "recup. energia": "Energy Regen",
    "recarga de energia": "Energy Recharge",
    "recarga": "Energy Recharge",
    "proficiência elemental": "Elemental Mastery",
    "proficiência elementar": "Elemental Mastery",
    "prof. elementar": "Elemental Mastery",
    "prof. element.": "Elemental Mastery",
    "bônus de cura": "Healing Bonus",
    "bônus cura": "Healing Bonus",
    "cura bônus": "Healing Bonus",
    "bônus de cura recebida": "Incoming Healing Bonus",
    "cura recebida": "Incoming Healing",
    "proficiência de anomalia": "Anomaly Proficiency",
    "prof. anomalia": "Anomaly Prof.",
    "prof. anom": "Anomaly Prof.",
    "taxa de acerto de anomalia": "Anomaly Mastery",
    "maestria de anomalia": "Anomaly Mastery",
    "maest. anomalia": "Anomaly Mastery",
    "taxa de perfuração": "PEN Ratio",
    "perfuração": "PEN Ratio",
    "impacto": "Impact",
}

for k, v in _EXTRA_REVERSE.items():
    REVERSE_TRANSLATIONS[k] = v


def traduzir_personagem(nome: str, lang: str = "pt") -> str:
    """Traduz o nome do personagem entre PT-BR e EN."""
    if not nome:
        return ""
    n = nome.strip()
    if lang == "en":
        n_low = n.lower()
        if n_low in REVERSE_TRANSLATIONS:
            return REVERSE_TRANSLATIONS[n_low]
        for pt_key, en_val in sorted(REVERSE_TRANSLATIONS.items(), key=lambda x: len(x[0]), reverse=True):
            if pt_key in n_low and len(pt_key) > 3:
                replaced = n_low.replace(pt_key, en_val).title()
                replaced = re.sub(r"\bNv\.\s*", "Lv. ", replaced, flags=re.IGNORECASE)
                return replaced
        return n
    else:
        if n in CHARACTER_TRANSLATIONS:
            return CHARACTER_TRANSLATIONS[n]
        n_low = n.lower()
        for en_key, pt_val in CHARACTER_TRANSLATIONS.items():
            if en_key.lower() == n_low:
                return pt_val
        return n


def traduzir_caminho(caminho: str, lang: str = "pt") -> str:
    """Traduz o caminho/especialidade/arma entre PT-BR e EN."""
    if not caminho:
        return ""
    c = caminho.strip()
    if lang == "en":
        c_low = c.lower()
        if c_low in REVERSE_TRANSLATIONS:
            return REVERSE_TRANSLATIONS[c_low]
        return c
    else:
        if c in PATH_TRANSLATIONS:
            return PATH_TRANSLATIONS[c]
        c_low = c.lower()
        for en_k, pt_v in PATH_TRANSLATIONS.items():
            if en_k.lower() == c_low:
                return pt_v
        return c


def traduzir_status(status: str, lang: str = "pt") -> str:
    """Traduz o nome do atributo/substat entre PT-BR e EN."""
    if not status:
        return ""
    s = status.strip()
    if lang == "en":
        s_low = s.lower()
        if s_low in REVERSE_TRANSLATIONS:
            return REVERSE_TRANSLATIONS[s_low]
        return s
    else:
        if s in STAT_TRANSLATIONS:
            return STAT_TRANSLATIONS[s]
        s_low = s.lower()
        for en_k, pt_v in STAT_TRANSLATIONS.items():
            if en_k.lower() == s_low:
                return pt_v
        return s


def traduzir_elemento(elemento: str, lang: str = "pt") -> str:
    """Traduz o elemento entre PT-BR e EN."""
    if not elemento:
        return ""
    e = elemento.strip()
    if lang == "en":
        e_low = e.lower()
        if e_low in REVERSE_TRANSLATIONS:
            return REVERSE_TRANSLATIONS[e_low]
        return e
    else:
        if e in ELEMENT_TRANSLATIONS:
            return ELEMENT_TRANSLATIONS[e]
        e_low = e.lower()
        for en_k, pt_v in ELEMENT_TRANSLATIONS.items():
            if en_k.lower() == e_low:
                return pt_v
        return e


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
