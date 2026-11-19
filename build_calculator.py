import os
import re
import json
import logging
import random
import sqlite3
from datetime import datetime, timedelta
import unicodedata
import time
from curl_cffi import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Optional, Any

from core.config import get_data_path, get_resource_path

logger = logging.getLogger(__name__)


# Expressões regulares pré-compiladas para alta performance
RE_MULTIPLE_SPACES = re.compile(r"\s+")
RE_PARENTHESES = re.compile(r"\([^)]*\)")
RE_CLEAN_CHARS = re.compile(r"[#*\-\[\]]+")
RE_SUB_SPLIT = re.compile(r"\s*=\s*|\s+\bor\b\s+", re.IGNORECASE)
RE_SUB_TRAILING_NOTE = re.compile(
    r"\s*\b(?:until|untill|to|up to|or more|or higher|in combat|pre[- ]combat|desired goal)\b.*$",
    re.IGNORECASE,
)
RE_NUM_FLOAT = re.compile(r"([\d\.]+)")
RE_SUB_NUM = re.compile(r"([0-9]+(?:\.[0-9]+)?)")
RE_HSR_MAIN_SLOTS = re.compile(
    r"-\s*(?:\*\*)?(Body|Corpo|Feet|Pés|Pes|Bota|Planar Sphere|Esfera Planar|Esfera|Link Rope|Corda de Ligação|Corda)(?:\*\*)?[:\- ]\s*(.*)",
    re.IGNORECASE,
)
RE_SLOT_SPLIT = re.compile(r"\s*(?:/|\||\bor\b|,|>=|>|<=|<|=)\s*", re.IGNORECASE)
RE_GENSHIN_SLOT_SPLIT = re.compile(r"\s*(?:/|\||\bor\b|,|>=|>|<=|<|=|&)\s*", re.IGNORECASE)
RE_SUB_HEADER = re.compile(
    r"#{2,4}\s*(?:subatributos prioritários|substatus prioritários|sub-stats|substats)[^\n]*\n\s*([^\n#]+)",
    re.IGNORECASE,
)
RE_SUB_INLINE = re.compile(
    r"(?:subatributos prioritários|substatus prioritários|sub-stats|substats)[:\n]\s*([^\n#]+)",
    re.IGNORECASE,
)
RE_SUB_TOKEN_SPLIT = re.compile(r"[>,\/;]")
RE_GENSHIN_SUB_TOKEN_SPLIT = re.compile(r"[>,\/;=]")
RE_ENDGAME_SEC = re.compile(
    r"#{2,4}\s*(?:Atributos Finais[^\n]*|Recommended Endgame Stats[^\n]*)\n(.*?)(?=\n#{1,4}\s|\Z)",
    re.DOTALL | re.IGNORECASE,
)
RE_STATS_REC_SEC = re.compile(
    r"#{2,4}\s*Atributos Recomendados[^\n]*\n(.*?)(?=\n##\s|\Z)",
    re.DOTALL | re.IGNORECASE,
)
RE_SPEED_GOAL = re.compile(
    r"(\d+)\s*speed\s*goal|speed\s*goal\s*of\s*(\d+)|breakpoint\s*of\s*(\d+)\s*spd|(\d+)\s*spd",
    re.IGNORECASE,
)
RE_CRIT_GOAL = re.compile(r"crit\s*rate\s*(?:goal|threshold)\s*of\s*(\d+)%|(\d+)%\s*crit\s*rate", re.IGNORECASE)
RE_BE_GOAL = re.compile(r"break\s*effect\s*(?:goal|threshold)\s*of\s*(\d+)%|(\d+)%\s*break\s*effect", re.IGNORECASE)
RE_HAS_DIGIT = re.compile(r"\d")
RE_BENCH_PLUS = re.compile(r"(\d+(?:\.\d+)?)\s*(%?)\s*\+")
RE_BENCH_PAREN = re.compile(r"(\d+(?:\.\d+)?)\s*(%?)\s*(\([^)]{1,35}\))")
RE_ZZZ_MAIN_SLOTS = re.compile(r"(?:Disk|Slot|Disco)\s*(4|5|6)[:\- ]\s*(.*)", re.IGNORECASE)
RE_GENSHIN_MAIN_SEC = re.compile(r"#{2,4}\s*Atributos Principais[^\n]*\n(.*?)(?:#{2,4}|##|$)", re.DOTALL | re.IGNORECASE)
RE_GENSHIN_MAIN_LINE_BOLD = re.compile(r"-\s*\*\*([^\*]+)\*\*:?\s*(.*)")
RE_GENSHIN_MAIN_LINE_PLAIN = re.compile(r"-\s*([^\*:]+):\s*(.*)")
RE_GENSHIN_SUB_HEADER = re.compile(r"#{2,4}\s*Subatributos Prioritários[^\n]*\n\s*([^\n#]+)", re.IGNORECASE)
RE_GENSHIN_SUB_INLINE = re.compile(r"(?:subatributos|substatus|sub-stats|substats)[^\n]*[:\n]\s*([^\n#]+)", re.IGNORECASE)
RE_PROMO_CODE_CLEAN = re.compile(r"(Quick|Redeem|\[\d+\])", re.IGNORECASE)
RE_PROMO_CODE_TOKEN = re.compile(r"[A-Za-z0-9]{5,30}")
RE_WIKI_REF = re.compile(r"\[\d+\]")
RE_PROMO_VALID_UNTIL = re.compile(r"valid until:\s*([^V\n\r]+)", re.IGNORECASE)
RE_PROMO_DATE = re.compile(r"([A-Za-z]+\s+\d+,\s+\d{4}).*")


def _resolve_static_file(filename: str) -> str:
    """Resolve arquivo em static_data priorizando get_data_path antes de get_resource_path."""
    rel = os.path.join("static_data", filename)
    data_p = get_data_path(rel)
    if os.path.exists(data_p):
        return data_p
    return get_resource_path(rel)


def remove_accents(input_str: str) -> str:
    """Remove acentos e diacríticos de uma string."""
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def normalize_slot_name(slot_str: str, game_id: str = "") -> str:
    """Normaliza nomes de slots em português, inglês ou numéricos para chaves padrão do jogo."""
    if not slot_str:
        return ""
    s = remove_accents(str(slot_str).lower().strip())
    g = game_id.lower().strip() if game_id else ""

    # 1. Normalização contextual por jogo para slots numéricos
    if g == "genshin":
        if s in ["1", "flor", "flower"]:
            return "flower"
        if s in ["2", "pena", "plume", "feather"]:
            return "plume"
        if s in ["3", "areia", "relogio", "sands"]:
            return "sands"
        if s in ["4", "copo", "calice", "goblet"]:
            return "goblet"
        if s in ["5", "tiara", "coroa", "circlet"]:
            return "circlet"
    elif g == "hsr":
        if s in ["1", "cabeca", "head"]:
            return "head"
        if s in ["2", "mao", "maos", "hands"]:
            return "hands"
        if s in ["3", "corpo", "body"]:
            return "body"
        if s in ["4", "pe", "pes", "bota", "feet"]:
            return "feet"
        if s in ["5", "esfera", "planar_sphere", "sphere"]:
            return "planar_sphere"
        if s in ["6", "corda", "link_rope", "rope"]:
            return "link_rope"
    elif g == "zzz":
        for i in range(1, 7):
            if (
                f"disco {i}" in s
                or f"slot_{i}" in s
                or f"slot {i}" in s
                or f"disc {i}" in s
                or f"disco_{i}" in s
                or f"disc_{i}" in s
                or s == str(i)
            ):
                return f"slot_{i}"

    # 2. Prioriza mapeamento por nome de slot
    if any(k in s for k in ["copo", "calice", "goblet"]):
        return "goblet"
    if any(k in s for k in ["areia", "relogio", "sands"]):
        return "sands"
    if any(k in s for k in ["tiara", "coroa", "circlet"]):
        return "circlet"
    if any(k in s for k in ["flor", "flower"]):
        return "flower"
    if any(k in s for k in ["pena", "plume", "feather"]):
        return "plume"

    if any(k in s for k in ["esfera", "planar_sphere", "sphere"]):
        return "planar_sphere"
    if any(k in s for k in ["corda", "link_rope", "rope"]):
        return "link_rope"
    if any(k in s for k in ["cabeca", "head"]):
        return "head"
    if any(k in s for k in ["mao", "maos", "hands"]):
        return "hands"
    if any(k in s for k in ["corpo", "body"]):
        return "body"
    if any(k in s for k in ["bota", "botas", "feet"]) or s in ["pe", "pes", "pés", "pé"]:
        return "feet"

    # 3. Fallback genérico por número para ZZZ
    for i in range(1, 7):
        if (
            f"disco {i}" in s
            or f"slot_{i}" in s
            or f"slot {i}" in s
            or f"disc {i}" in s
            or f"disco_{i}" in s
            or f"disc_{i}" in s
            or s == str(i)
        ):
            return f"slot_{i}"

    return s


# ==========================================
# FONTE MESTRE DE IDS DE PERSONAGENS
# ==========================================
CHAR_ALIASES = {
    # Trailblazer / Desbravador
    "desbravador": "trailblazer_harmony",
    "desbravadora": "trailblazer_harmony",
    "trailblazer": "trailblazer_harmony",
    "desbravador harmonia": "trailblazer_harmony",
    "desbravador a harmonia": "trailblazer_harmony",
    "desbravadora harmonia": "trailblazer_harmony",
    "desbravadora a harmonia": "trailblazer_harmony",
    "trailblazer harmony": "trailblazer_harmony",
    "desbravador recordacao": "trailblazer_remembrance",
    "desbravador a recordacao": "trailblazer_remembrance",
    "desbravadora recordacao": "trailblazer_remembrance",
    "desbravador remembranca": "trailblazer_remembrance",
    "desbravador a remembranca": "trailblazer_remembrance",
    "desbravador rememoracao": "trailblazer_remembrance",
    "desbravador a rememoracao": "trailblazer_remembrance",
    "desbravadora remembranca": "trailblazer_remembrance",
    "trailblazer remembrance": "trailblazer_remembrance",
    "desbravador preservacao": "trailblazer_preservation",
    "desbravador a preservacao": "trailblazer_preservation",
    "desbravadora preservacao": "trailblazer_preservation",
    "trailblazer preservation": "trailblazer_preservation",
    "desbravador destruicao": "trailblazer_destruction",
    "desbravador a destruicao": "trailblazer_destruction",
    "desbravadora destruicao": "trailblazer_destruction",
    "trailblazer destruction": "trailblazer_destruction",
    "desbravador jubilo": "trailblazer_elation",
    "desbravador o jubilo": "trailblazer_elation",
    "trailblazer elation": "trailblazer_elation",
    # March 7th / 7 de Março
    "7 de marco": "march_7th",
    "7 de marco preservacao": "march_7th",
    "march 7th": "march_7th",
    "march 7th preservation": "march_7th",
    "7 de marco a caca": "march_7th_hunt",
    "7 de marco caca": "march_7th_hunt",
    "march 7th the hunt": "march_7th_hunt",
    "march 7th hunt": "march_7th_hunt",
    "march 7th caca": "march_7th_hunt",
    "7 de marco noite eterna": "march_7th_evernight",
    "7 de marco a noite eterna": "march_7th_evernight",
    "march 7th evernight": "march_7th_evernight",
    "noite eterna": "march_7th_evernight",
    # Black Swan / Cisne Negro
    "cisne negro": "black_swan",
    "black swan": "black_swan",
    # Firefly / Vagalume
    "vagalume": "firefly",
    "vaga lume": "firefly",
    "firefly": "firefly",
    # Silver Wolf / Loba Prateada
    "loba prateada": "silver_wolf",
    "silver wolf": "silver_wolf",
    "loba prateada nv 999": "silver_wolf_999",
    "loba prateada 999": "silver_wolf_999",
    "silver wolf lv 999": "silver_wolf_999",
    "silver wolf 999": "silver_wolf_999",
    # Tingyun / Fugue
    "tingyun": "tingyun",
    "tingyun fuga": "tingyun_fugue",
    "tingyun a fuga": "tingyun_fugue",
    "tingyun fugue": "tingyun_fugue",
    "fuga": "tingyun_fugue",
    "fugue": "tingyun_fugue",
    # Dan Heng
    "dan heng": "dan_heng",
    "dan heng imbibitor lunae": "dan_heng_imbibitor_lunae",
    "dan heng embibitor lunae": "dan_heng_imbibitor_lunae",
    "imbibitor lunae": "dan_heng_imbibitor_lunae",
    "dhil": "dan_heng_imbibitor_lunae",
    "dan heng permansor terrae": "dan_heng_permansor_terrae",
    "permansor terrae": "dan_heng_permansor_terrae",
    # Himeko
    "himeko": "himeko",
    "himeko nova": "himeko_nova",
    # Hertas
    "herta": "herta",
    "a herta": "the_herta",
    "the herta": "the_herta",
    # Dahlia
    "a dalia": "the_dahlia",
    "the dahlia": "the_dahlia",
    "dalia": "the_dahlia",
    "dahlia": "the_dahlia",
    # Topaz
    "topaz": "topaz",
    "topaz e dinheirinho": "topaz",
    "topaz numby": "topaz",
    "topaz & numby": "topaz",
    # Dr. Ratio
    "dr ratio": "dr_ratio",
    "dr. ratio": "dr_ratio",
    "doctor ratio": "dr_ratio",
    "doutor ratio": "dr_ratio",
    # Genshin Aliases
    "raiden": "raiden_shogun",
    "raiden shogun": "raiden_shogun",
    "shogun raiden": "raiden_shogun",
    "kaedehara kazuha": "kazuha",
    "kazuha": "kazuha",
    "sangonomiya kokomi": "kokomi",
    "kokomi": "kokomi",
    "kamisato ayaka": "ayaka",
    "ayaka": "ayaka",
    "kamisato ayato": "ayato",
    "ayato": "ayato",
    "arataki itto": "itto",
    "itto": "itto",
    "tartaglia": "childe",
    "childe": "childe",
    "kuki shinobu": "kuki_shinobu",
    "shinobu": "kuki_shinobu",
    "yae miko": "yae_miko",
    "miko": "yae_miko",
    "hu tao": "hu_tao",
    "hutao": "hu_tao",
    "mochileiro": "wanderer",
    "wanderer": "wanderer",
    # ZZZ Aliases
    "von lycaon": "lycaon",
    "lycaon": "lycaon",
    "soldado 11": "soldier_11",
    "soldier 11": "soldier_11",
    "anby": "anby",
    "soldier 0 anby": "soldier_0_anby",
    "anby soldado 0": "soldier_0_anby",
    "astra": "astra",
    "astra yao": "astra",
    "ellen": "ellen",
    "ellen joe": "ellen",
    "jane": "jane",
    "jane doe": "jane",
    "zhu yuan": "zhu_yuan",
    "hoshimi miyabi": "miyabi",
    "miyabi": "miyabi",
    "asaba harumasa": "harumasa",
    "harumasa": "harumasa",
    "corin": "corin",
    "corin wickes": "corin",
    "anton": "anton",
    "anton ivanov": "anton",
    "billy": "billy",
    "billy kid": "billy",
    "koleda": "koleda",
    "koleda belobog": "koleda",
    "ben": "ben",
    "ben bigger": "ben",
    "alexandrina": "rina",
    "rina": "rina",
    "caesar": "caesar",
    "caesar king": "caesar",
    "piper": "piper",
    "piper wheel": "piper",
    "burnice": "burnice",
    "burnice white": "burnice",
    "nicole": "nicole",
    "nicole demara": "nicole",
    "seth": "seth",
    "seth lowell": "seth",
    "grace": "grace",
    "grace howard": "grace",
    "sigrid": "sigrid",
    "sigridnew": "sigrid",
    "sigrid new": "sigrid",
}

CHAR_DISPLAY_NAMES_PT = {
    # HSR
    "trailblazer": "Desbravador (Harmonia)",
    "trailblazer_harmony": "Desbravador (Harmonia)",
    "trailblazer_remembrance": "Desbravador (Recordação)",
    "trailblazer_preservation": "Desbravador (Preservação)",
    "trailblazer_destruction": "Desbravador (Destruição)",
    "trailblazer_elation": "Desbravador (Júbilo)",
    "march_7th": "7 de Março",
    "march_7th_hunt": "7 de Março (A Caça)",
    "march_7th_evernight": "7 de Março (Noite Eterna)",
    "dan_heng": "Dan Heng",
    "dan_heng_imbibitor_lunae": "Dan Heng • Imbibitor Lunae",
    "dan_heng_permansor_terrae": "Dan Heng • Permansor Terrae",
    "himeko": "Himeko",
    "himeko_nova": "Himeko Nova",
    "the_herta": "A Herta",
    "herta": "Herta",
    "the_dahlia": "A Dália",
    "silver_wolf": "Loba Prateada",
    "silver_wolf_999": "Loba Prateada (Nv. 999)",
    "black_swan": "Cisne Negro",
    "firefly": "Vagalume",
    "tingyun": "Tingyun",
    "tingyun_fugue": "Tingyun • Fuga",
    "topaz": "Topaz & Dinheirinho",
    "topaz_numby": "Topaz & Dinheirinho",
    "dr_ratio": "Dr. Ratio",
    "ruan_mei": "Ruan Mei",
    "kafka": "Kafka",
    "acheron": "Acheron",
    "feixiao": "Feixiao",
    "castorice": "Castorice",
    "cyrene": "Cyrene",
    "hyacine": "Hyacine",
    "aventurine": "Aventurine",
    "sparkle": "Sparkle",
    "robin": "Robin",
    "huohuo": "Huohuo",
    "lingsha": "Lingsha",
    "jiaoqiu": "Jiaoqiu",
    "gallagher": "Gallagher",
    "pela": "Pela",
    "bronya": "Bronya",
    "jingliu": "Jingliu",
    "jing_yuan": "Jing Yuan",
    "blade": "Blade",
    "seele": "Seele",
    "boothill": "Boothill",
    "yunli": "Yunli",
    "clara": "Clara",
    "argenti": "Argenti",
    "gepard": "Gepard",
    "fu_xuan": "Fu Xuan",
    "bailu": "Bailu",
    "lynx": "Lynx",
    "natasha": "Natasha",
    "luocha": "Luocha",
    "sampo": "Sampo",
    "guinaifen": "Guinaifen",
    "luka": "Luka",
    "xueyi": "Xueyi",
    "qingque": "Qingque",
    "asta": "Asta",
    "hanya": "Hanya",
    "yukong": "Yukong",
    "moze": "Moze",
    "jade": "Jade",
    "misha": "Misha",
    "sushang": "Sushang",
    "hook": "Hook",
    "arlan": "Arlan",
    "yanqing": "Yanqing",
    "sunday": "Sunday",
    "tribbie": "Tribbie",
    "sparxie": "Sparxie",
    "yao_guang": "Yao Guang",
    "rin_tohsaka": "Rin Tohsaka",
    "archer": "Archer",
    "aglaea": "Aglaea",
    "anaxa": "Anaxa",
    "cerydra": "Cerydra",
    "evanescia": "Evanescia",
    "hysilens": "Hysilens",
    "mydei": "Mydei",
    "phainon": "Phainon",
    # Genshin Impact
    "neuvillette": "Neuvillette",
    "arlecchino": "Arlecchino",
    "furina": "Furina",
    "kazuha": "Kaedehara Kazuha",
    "raiden_shogun": "Raiden Shogun",
    "bennett": "Bennett",
    "xiangling": "Xiangling",
    "xingqiu": "Xingqiu",
    "yelan": "Yelan",
    "nahida": "Nahida",
    "kuki_shinobu": "Kuki Shinobu",
    "zhongli": "Zhongli",
    "baizhu": "Baizhu",
    "alhaitham": "Alhaitham",
    "ayaka": "Kamisato Ayaka",
    "shenhe": "Shenhe",
    "kokomi": "Sangonomiya Kokomi",
    "fischl": "Fischl",
    "hu_tao": "Hu Tao",
    "childe": "Tartaglia",
    "yoimiya": "Yoimiya",
    "clorinde": "Clorinde",
    "tighnari": "Tighnari",
    "xiao": "Xiao",
    "wanderer": "Mochileiro (Wanderer)",
    "itto": "Arataki Itto",
    "navia": "Navia",
    "cyno": "Cyno",
    "eula": "Eula",
    "diluc": "Diluc",
    "mualani": "Mualani",
    "kinich": "Kinich",
    "wriothesley": "Wriothesley",
    "lyney": "Lyney",
    "gaming": "Gaming",
    "razor": "Razor",
    "chasca": "Chasca",
    "yae_miko": "Yae Miko",
    "rosaria": "Rosaria",
    "chiori": "Chiori",
    "emilie": "Emilie",
    "albedo": "Albedo",
    "ororon": "Ororon",
    "sucrose": "Sucrose",
    "faruzan": "Faruzan",
    "mona": "Mona",
    "gorou": "Gorou",
    "kujou_sara": "Kujou Sara",
    "chevreuse": "Chevreuse",
    "xianyun": "Xianyun",
    "xilonen": "Xilonen",
    "citlali": "Citlali",
    "iansan": "Iansan",
    "lan_yan": "Lan Yan",
    "venti": "Venti",
    "diona": "Diona",
    "charlotte": "Charlotte",
    "layla": "Layla",
    "kirara": "Kirara",
    "barbara": "Bárbara",
    "noelle": "Noelle",
    "sigewinne": "Sigewinne",
    "mika": "Mika",
    "jean": "Jean",
    "dehya": "Dehya",
    # ZZZ
    "ellen": "Ellen Joe",
    "lycaon": "Von Lycaon",
    "soukaku": "Soukaku",
    "jane": "Jane Doe",
    "seth": "Seth Lowell",
    "grace": "Grace Howard",
    "zhu_yuan": "Zhu Yuan",
    "qingyi": "Qingyi",
    "nicole": "Nicole Demara",
    "burnice": "Burnice White",
    "piper": "Piper Wheel",
    "lucy": "Lucy",
    "anby": "Anby Demara",
    "soldier_0_anby": "Anby (Soldado 0)",
    "soldier_11": "Soldado 11",
    "corin": "Corin Wickes",
    "anton": "Anton Ivanov",
    "billy": "Billy Kid",
    "nekomata": "Nekomata",
    "miyabi": "Hoshimi Miyabi",
    "harumasa": "Asaba Harumasa",
    "koleda": "Koleda Belobog",
    "ben": "Ben Bigger",
    "rina": "Alexandrina (Rina)",
    "caesar": "Caesar King",
    "lighter": "Lighter",
    "astra": "Astra Yao",
    "yuzuha": "Yuzuha",
    "lucia": "Lucia",
    "sunna": "Sunna",
    "velina": "Velina",
    "remielle": "Remielle",
    "promeia": "Promeia",
    "aria": "Aria",
    "alice": "Alice",
    "vivian": "Vivian",
    "dialyn": "Dialyn",
    "sigrid": "Sigrid",
}


def normalize_char_name(name: str) -> str:
    """
    Normaliza o nome do personagem resolvendo tradução Português <-> Inglês,
    removendo acentos, hifens, bullets, parênteses e múltiplos espaços. Preserva qualificadores como 'Nova'.
    """
    if not name:
        return ""
    clean = str(name).lower()
    clean = (
        clean.replace("•", " ")
        .replace("-", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace(".", " ")
        .replace(",", " ")
        .replace(":", " ")
        .replace("#", " ")
    )
    clean = remove_accents(clean)
    clean = RE_MULTIPLE_SPACES.sub(" ", clean).strip()

    if clean in CHAR_ALIASES:
        return CHAR_ALIASES[clean]

    clean_underscore = clean.replace(" ", "_")
    if clean_underscore in CHAR_ALIASES:
        return CHAR_ALIASES[clean_underscore]

    return clean_underscore


def fetch_master_id_list(game_id: str) -> Dict[str, str]:
    """
    Simula/obtém a fonte mestre de IDs de personagens vinculando nomes em inglês aos IDs oficiais (chaves primárias).
    Retorna um dicionário no formato {nome_em_ingles_lowercase: id_oficial}.
    """
    game_id = game_id.lower().strip()
    master_map = {}

    # 1. Fonte de verdade primária dinâmica: static_data/hoyolab_mappings.json
    hoyolab_file = _resolve_static_file("hoyolab_mappings.json")
    slug_to_hid = {}
    if os.path.exists(hoyolab_file):
        try:
            with open(hoyolab_file, "r", encoding="utf-8") as f:
                hmap = json.load(f).get(game_id, {})
                for hid, slug in hmap.items():
                    cid_str = str(hid).strip()
                    slug_str = str(slug).strip()
                    if not cid_str or not slug_str:
                        continue
                    slug_lower = slug_str.lower()
                    slug_space = slug_lower.replace("_", " ")
                    norm_slug = normalize_char_name(slug_str)
                    slug_to_hid[slug_lower] = cid_str
                    slug_to_hid[norm_slug] = cid_str
                    master_map.setdefault(slug_lower, cid_str)
                    master_map.setdefault(slug_space, cid_str)
                    master_map.setdefault(norm_slug, cid_str)
        except (OSError, json.JSONDecodeError, TypeError, AttributeError) as exc:
            logger.warning("[CALC] Falha ao ler hoyolab_mappings.json (%s): %s", game_id, exc)

    # 2. Fallback de IDs e aliases conhecidos (não sobrescreve hoyolab_mappings.json)
    known_master = {
        "hsr": {
            "acheron": "1308",
            "firefly": "1310",
            "sparkle": "1306",
            "black swan": "1307",
            "blade": "1205",
            "jingliu": "1212",
            "jing yuan": "1204",
            "march 7th": "1001",
            "march 7th the hunt": "1224",
            "march 7th • the hunt": "1224",
            "march 7th evernight": "1225",
            "march 7th • evernight": "1225",
            "aglaea": "1402",
            "anaxa": "1403",
            "archer": "1015",
            "argenti": "1302",
            "arlan": "1008",
            "asta": "1009",
            "aventurine": "1304",
            "bailu": "1211",
            "bronya": "1101",
            "boothill": "1316",
            "clara": "1107",
            "dan heng": "1002",
            "dr. ratio": "1305",
            "feixiao": "1220",
            "fu xuan": "1208",
            "gallagher": "1301",
            "gepard": "1104",
            "gilgamesh": "1509",
            "guinaifen": "1210",
            "hanya": "1215",
            "herta": "1013",
            "himeko": "1003",
            "himeko - nova": "1510",
            "himeko_nova": "1510",
            "himeko nova": "1510",
            "hook": "1109",
            "huohuo": "1217",
            "jade": "1314",
            "jiaoqiu": "1218",
            "kafka": "1005",
            "lingsha": "1222",
            "luka": "1111",
            "luocha": "1203",
            "lynx": "1110",
            "misha": "1312",
            "moze": "1223",
            "natasha": "1105",
            "pela": "1106",
            "qingque": "1201",
            "rappa": "1317",
            "robin": "1309",
            "ruan mei": "1303",
            "sampo": "1108",
            "seele": "1102",
            "serval": "1103",
            "silver wolf": "1006",
            "sunday": "1313",
            "sushang": "1206",
            "the dahlia": "1321",
            "a dahlia": "1321",
            "a dália": "1321",
            "tingyun": "1202",
            "topaz & numby": "1112",
            "trailblazer": "8009",
            "desbravador": "8009",
            "desbravador(a)": "8009",
            "welt": "1004",
            "xueyi": "1214",
            "yanqing": "1209",
            "yukong": "1207",
            "yunli": "1221",
        },
        "genshin": {
            "ayaka": "10000002",
            "bennett": "10000032",
            "kazuha": "10000047",
            "neuvillette": "10000087",
            "charlotte": "10000088",
            "furina": "10000089",
            "arlecchino": "10000095",
            "raiden": "10000052",
            "zhongli": "10000030",
            "nahida": "10000073",
            "kokomi": "10000054",
            "sangonomiya kokomi": "10000054",
            "yae": "10000058",
            "yae miko": "10000058",
            "shinobu": "10000065",
            "kuki shinobu": "10000065",
            "sara": "10000056",
            "kujou sara": "10000056",
            "heizou": "10000059",
            "shikanoin heizou": "10000059",
            "yunjin": "10000064",
            "yun jin": "10000064",
            "mizuki": "10000109",
            "yumemizuki mizuki": "10000109",
            "lan yan": "10000107",
            "viajante": "10000005",
            "traveler": "10000005",
            "manequina": "10000118",
        },
        "zzz": {
            "anby": "1011",
            "nekomata": "1021",
            "nicole": "1031",
            "soldier 11": "1041",
            "soldier_11": "1041",
            "corin": "1061",
            "caesar": "1071",
            "billy": "1081",
            "miyabi": "1091",
            "koleda": "1101",
            "anton": "1111",
            "ben": "1121",
            "soukaku": "1131",
            "lycaon": "1141",
            "lucy": "1151",
            "burnice": "1171",
            "grace": "1181",
            "ellen": "1191",
            "harumasa": "1201",
            "rina": "1211",
            "zhu yuan": "1241",
            "jane": "1261",
            "jane doe": "1261",
            "seth": "1271",
            "piper": "1281",
            "orphie & magus": "1301",
            "orphie and magus": "1301",
            "orphie_&_magus": "1301",
            "astra yao": "1311",
            "astra_yao": "1311",
            "evelyn": "1321",
            "zhao": "1341",
            "pulchra": "1351",
            "yixuan": "1371",
            "pan yinhu": "1421",
            "pan_yinhu": "1421",
            "ye shunguang": "1431",
            "ye_shunguang": "1431",
            "manato": "1441",
            "dialyn": "1481",
            "cissia": "1521",
            "pyrois": "1551",
            "remielle": "1581",
            "remielle new": "1581",
            "sigrid": "1591",
            "sigridnew": "1591",
            "sigrid_new": "1591",
            "sigrid new": "1591",
        },
    }

    # Preenche primeiro com a tabela oficial de conhecidos (para evitar colisões/sobrescritas incorretas)
    if game_id in known_master:
        for name, cid in known_master[game_id].items():
            name_lower = name.lower()
            if name_lower not in master_map:
                master_map[name_lower] = cid
            norm_name = normalize_char_name(name)
            if norm_name not in master_map:
                master_map[norm_name] = cid

    if game_id == "genshin":
        try:
            from genshin.models.genshin.constants import CHARACTER_NAMES

            for lang in ["en-us", "pt-pt"]:
                if lang in CHARACTER_NAMES:
                    for cid, db_char in CHARACTER_NAMES[lang].items():
                        c_str = str(cid)
                        n_lower = db_char.name.lower().strip()
                        master_map.setdefault(n_lower, c_str)
                        master_map.setdefault(normalize_char_name(n_lower), c_str)
        except (ImportError, KeyError, TypeError, AttributeError) as exc:
            logger.debug("[CALC] Falha ao ler mapa genshin.py para %s: %s", game_id, exc)

    aliases_pt_to_en = {
        "cisne negro": "black swan",
        "vaga-lume": "firefly",
        "faísca": "sparkle",
        "loba prateada": "silver wolf",
        "7 de março": "march 7th",
        "topaz e numby": "topaz & numby",
        "topaz e dinheirinho": "topaz & numby",
        "dr. ratio": "dr. ratio",
        "loba prateada nv. 999": "silver wolf lv. 999",
        "noite eterna": "march 7th evernight",
        "desbravador(a)": "trailblazer",
        "a herta": "the herta",
        "fugue": "tingyun fugue",
    }

    # 2. Carrega roster local (JSON + SQLite) e manifestos estáticos dinamicamente (Zero Hardcoding)
    def _register_dynamic_char(raw_char_name: str, raw_cid: str):
        c_n = str(raw_char_name or "").strip()
        c_i = str(raw_cid or "").strip()
        if not c_n or not c_i or "nickname" in c_n.lower():
            return
        c_n_lower = c_n.lower()
        norm_c = normalize_char_name(c_n)
        if c_n_lower not in master_map:
            master_map[c_n_lower] = c_i
        if norm_c not in master_map:
            master_map[norm_c] = c_i

        if c_n_lower in aliases_pt_to_en:
            en_alias = aliases_pt_to_en[c_n_lower]
            en_lower = en_alias.lower()
            norm_en = normalize_char_name(en_alias)
            master_map.setdefault(en_lower, c_i)
            master_map.setdefault(norm_en, c_i)

        if norm_c in aliases_pt_to_en:
            en_alias = aliases_pt_to_en[norm_c]
            en_lower = en_alias.lower()
            norm_en = normalize_char_name(en_alias)
            master_map.setdefault(en_lower, c_i)
            master_map.setdefault(norm_en, c_i)

    roster_file = f"{game_id}/roster_data_{game_id}.json"
    if os.path.exists(roster_file):
        try:
            with open(roster_file, "r", encoding="utf-8") as f:
                for char in json.load(f):
                    _register_dynamic_char(char.get("name", ""), char.get("id") or char.get("character_id"))
        except (OSError, json.JSONDecodeError, TypeError, AttributeError) as exc:
            logger.warning("[CALC] Falha ao carregar %s: %s", roster_file, exc)

    try:
        import database

        for char in database.get_roster_data(game_id) or []:
            _register_dynamic_char(char.get("name", ""), char.get("id") or char.get("character_id"))
    except (ImportError, sqlite3.Error, TypeError, AttributeError) as exc:
        logger.debug("[CALC] Roster SQLite indisponível em get_master_ids(%s): %s", game_id, exc)

    manifest_file = _resolve_static_file(f"{game_id}_manifest.json")
    if os.path.exists(manifest_file):
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                m_data = json.load(f)
                m_chars = m_data.get("characters", m_data) if isinstance(m_data, dict) else {}
                if isinstance(m_chars, dict):
                    for m_key, m_entry in m_chars.items():
                        if not isinstance(m_entry, dict):
                            continue
                        hid = str(m_entry.get("hoyolab_id") or "").strip()
                        if not hid or hid == "9999":
                            continue
                        _register_dynamic_char(m_entry.get("name", ""), hid)
                        _register_dynamic_char(str(m_key).replace("_", " "), hid)
        except (OSError, json.JSONDecodeError, TypeError, AttributeError) as exc:
            logger.warning("[CALC] Falha ao ler manifesto %s: %s", manifest_file, exc)

    # 3. Vincula aliases multilíngues e mapeamentos HoYoLAB estáticos se o destino já tiver ID
    try:
        aliases_file = _resolve_static_file("character_aliases.json")
        for sl, hid in slug_to_hid.items():
            master_map.setdefault(sl, hid)
        if os.path.exists(aliases_file):
            with open(aliases_file, "r", encoding="utf-8") as f:
                amap = json.load(f).get(game_id, {})
                for a_k, a_v in amap.items():
                    target_id = (
                        master_map.get(normalize_char_name(a_v))
                        or master_map.get(str(a_v).lower().strip())
                        or slug_to_hid.get(normalize_char_name(a_v))
                    )
                    if target_id:
                        master_map.setdefault(str(a_k).lower().strip(), target_id)
                        master_map.setdefault(normalize_char_name(a_k), target_id)
    except (OSError, json.JSONDecodeError, TypeError, AttributeError) as exc:
        logger.warning("[CALC] Falha ao vincular aliases para %s: %s", game_id, exc)

    return master_map


# ==========================================
# CACHE DO BANCO DE METADADOS JSON
# ==========================================
META_DATA_CACHE = {}


def get_meta_data(game_id: str) -> dict:
    """Carrega o banco de metadados JSON do cache em memória."""
    game_id = game_id.lower().strip()
    if game_id in META_DATA_CACHE:
        return META_DATA_CACHE[game_id]

    path = f"{game_id}/meta_data_{game_id}.json"
    if not os.path.exists(path):
        old_path = f"{game_id}/meta_data.json"
        if os.path.exists(old_path):
            path = old_path

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Auto-repara se o arquivo JSON contiver artefatos de markdown ('**') ou entradas órfãs de benchmark
            needs_regen = any(
                isinstance(v, dict)
                and (
                    any("**" in str(s) for ms in v.get("main_stats", {}).values() for s in ms)
                    or (not v.get("main_stats") and bool(v.get("substats_priority")))
                )
                for v in data.values()
            )
            if needs_regen and os.path.exists(f"{game_id}/guias"):
                generate_meta_json_from_markdown(game_id)
                with open(path, "r", encoding="utf-8") as f2:
                    data = json.load(f2)

            master = fetch_master_id_list(game_id)
            indexed_data = dict(data)
            for k, v in list(data.items()):
                if isinstance(v, dict):
                    name = v.get("name", "")
                    norm_name = normalize_char_name(name)
                    norm_key = normalize_char_name(k)
                    cid = master.get(norm_name) or master.get(norm_key) or master.get(k.lower())
                    has_mains = bool(v.get("main_stats"))
                    if cid and (
                        str(cid) not in indexed_data or has_mains or not indexed_data[str(cid)].get("main_stats")
                    ):
                        indexed_data[str(cid)] = v
                    if norm_name and (
                        norm_name not in indexed_data or has_mains or not indexed_data[norm_name].get("main_stats")
                    ):
                        indexed_data[norm_name] = v
                    if norm_key and (
                        norm_key not in indexed_data or has_mains or not indexed_data[norm_key].get("main_stats")
                    ):
                        indexed_data[norm_key] = v
            META_DATA_CACHE[game_id] = indexed_data
            return indexed_data
        except Exception as e:
            print(f"[WARN] Erro ao ler {path}: {e}")
    return {}


# ==========================================
# ESPECIFICAÇÃO DE ROLLS / PROCS DE SUBSTATUS POR JOGO
# ==========================================
GAME_ROLL_SPECS = {
    "genshin": {
        "max_possible_rolls": 9,
        "stats": {
            "crit_rate": {"min": 2.72, "avg": 3.305, "max": 3.89},
            "crit_dmg": {"min": 5.44, "avg": 6.61, "max": 7.77},
            "atk_pct": {"min": 4.08, "avg": 4.955, "max": 5.83},
            "hp_pct": {"min": 4.08, "avg": 4.955, "max": 5.83},
            "def_pct": {"min": 5.10, "avg": 6.195, "max": 7.29},
            "em": {"min": 16.32, "avg": 19.815, "max": 23.31},
            "er": {"min": 4.53, "avg": 5.505, "max": 6.48},
            "atk_flat": {"min": 13.62, "avg": 16.535, "max": 19.45},
            "hp_flat": {"min": 209.13, "avg": 253.94, "max": 298.75},
            "def_flat": {"min": 16.20, "avg": 19.675, "max": 23.15},
        },
    },
    "hsr": {
        "max_possible_rolls": 9,
        "stats": {
            "crit_rate": {"min": 2.59, "avg": 2.91, "max": 3.24},
            "crit_dmg": {"min": 5.18, "avg": 5.83, "max": 6.48},
            "atk_pct": {"min": 3.45, "avg": 3.88, "max": 4.32},
            "hp_pct": {"min": 3.45, "avg": 3.88, "max": 4.32},
            "def_pct": {"min": 4.32, "avg": 4.86, "max": 5.40},
            "break_effect": {"min": 5.18, "avg": 5.83, "max": 6.48},
            "spd": {"min": 2.00, "avg": 2.30, "max": 2.60},
            "ehr": {"min": 3.45, "avg": 3.88, "max": 4.32},
            "res": {"min": 3.45, "avg": 3.88, "max": 4.32},
            "atk_flat": {"min": 17.00, "avg": 19.15, "max": 21.30},
            "hp_flat": {"min": 33.80, "avg": 38.05, "max": 42.30},
            "def_flat": {"min": 17.00, "avg": 19.15, "max": 21.30},
        },
    },
    "zzz": {
        "max_possible_rolls": 9,
        "stats": {
            "crit_rate": {"min": 2.40, "avg": 2.70, "max": 3.00},
            "crit_dmg": {"min": 4.80, "avg": 5.40, "max": 6.00},
            "atk_pct": {"min": 2.40, "avg": 2.70, "max": 3.00},
            "hp_pct": {"min": 2.40, "avg": 2.70, "max": 3.00},
            "def_pct": {"min": 3.84, "avg": 4.32, "max": 4.80},
            "anomaly_prof": {"min": 7.20, "avg": 8.10, "max": 9.00},
            "pen_flat": {"min": 7.20, "avg": 8.10, "max": 9.00},
            "atk_flat": {"min": 12.00, "avg": 13.50, "max": 15.00},
            "hp_flat": {"min": 89.60, "avg": 100.80, "max": 112.00},
            "def_flat": {"min": 12.00, "avg": 13.50, "max": 15.00},
        },
    },
}

MAX_ROLL_VALUES = {g: {s: spec["max"] for s, spec in data["stats"].items()} for g, data in GAME_ROLL_SPECS.items()}

# ==========================================
# MAPEAMENTO PARA NORMALIZAÇÃO DE NOMES DE ATRIBUTOS
# ==========================================
STAT_NAME_MAP = {
    # Taxa Crítica
    "taxa crítica": "crit_rate",
    "taxa critica": "crit_rate",
    "taxa crit": "crit_rate",
    "crit rate": "crit_rate",
    "crit_rate": "crit_rate",
    "rate": "crit_rate",
    "taxa": "crit_rate",
    "chance de crit": "crit_rate",
    "chance de crit%": "crit_rate",
    "taxa de crit": "crit_rate",
    "taxa de crit%": "crit_rate",
    "taxa crítica%": "crit_rate",
    "taxa critica%": "crit_rate",
    "taxa crit%": "crit_rate",
    "chance de crt": "crit_rate",
    "chance de crt%": "crit_rate",
    "chance de crítico": "crit_rate",
    "chance de critico": "crit_rate",
    "chance de crítico%": "crit_rate",
    "chance de critico%": "crit_rate",
    "taxa de crítico": "crit_rate",
    "taxa de critico": "crit_rate",
    "taxa de crítico%": "crit_rate",
    "taxa de critico%": "crit_rate",
    "taxa crt": "crit_rate",
    "taxa crt%": "crit_rate",
    "crit rate%": "crit_rate",
    "critical rate": "crit_rate",
    # Dano Crítico
    "dano crítico": "crit_dmg",
    "dano critico": "crit_dmg",
    "dano crit": "crit_dmg",
    "crit dmg": "crit_dmg",
    "crit_dmg": "crit_dmg",
    "dmg": "crit_dmg",
    "dano": "crit_dmg",
    "damage": "crit_dmg",
    "dano crit%": "crit_dmg",
    "dano de crit": "crit_dmg",
    "dano de crit%": "crit_dmg",
    "dano crítico%": "crit_dmg",
    "dano critico%": "crit_dmg",
    "dano crt": "crit_dmg",
    "dano crt%": "crit_dmg",
    "dano de crt": "crit_dmg",
    "dano de crt%": "crit_dmg",
    "dano de crítico": "crit_dmg",
    "dano de critico": "crit_dmg",
    "dano de crítico%": "crit_dmg",
    "dano de critico%": "crit_dmg",
    "crit dmg%": "crit_dmg",
    "critical damage": "crit_dmg",
    # Velocidade
    "velocidade": "spd",
    "vel": "spd",
    "spd": "spd",
    "speed": "spd",
    # Efeito de Quebra
    "efeito de quebra": "break_effect",
    "quebra": "break_effect",
    "break effect": "break_effect",
    "break_effect": "break_effect",
    "be": "break_effect",
    "efeito de quebra%": "break_effect",
    "break_effect%": "break_effect",
    "break": "break_effect",
    # Proficiência Elemental / Anomalia
    "proficiência elemental": "em",
    "proficiencia elemental": "em",
    "maestria elemental": "em",
    "maestria": "em",
    "maestria_elemental": "em",
    "proficiência": "em",
    "proficiencia": "em",
    "elemental mastery": "em",
    "em": "em",
    "prof": "em",
    "prof. elemental": "em",
    "prof. eleme.": "em",
    "prof eleme": "em",
    "prof eleme.": "em",
    "prof. element.": "em",
    "prof element": "em",
    "prof element.": "em",
    "mastery": "em",
    "anomaly proficiency": "anomaly_prof",
    "proficiência em anomalia": "anomaly_prof",
    "proficiencia em anomalia": "anomaly_prof",
    "proficiência de anomalia": "anomaly_prof",
    "proficiencia de anomalia": "anomaly_prof",
    "prof. anomalia": "anomaly_prof",
    "prof anomalia": "anomaly_prof",
    "anomaly_prof": "anomaly_prof",
    "proficiência de anomalia%": "anomaly_prof",
    "proficiencia de anomalia%": "anomaly_prof",
    "anomalia": "anomaly_prof",
    # Recarga de Energia / Taxa de Regeneração de Energia
    "recarga de energia": "er",
    "recarga": "er",
    "energy recharge": "er",
    "er": "er",
    "recharge": "er",
    "recarga de energia%": "er",
    "taxa de regeneração de energia": "err",
    "taxa de regeneracao de energia": "err",
    "taxa de regen. energia": "err",
    "taxa de regen energia": "err",
    "taxa de regen. de energia": "err",
    "taxa de regen de energia": "err",
    "recuperação de energia": "err",
    "recuperacao de energia": "err",
    "regen. energia": "err",
    "regen energia": "err",
    "taxa de reg. de energia": "err",
    "recup. energia": "err",
    "recup energia": "err",
    "energy regen rate": "err",
    "energy regen": "err",
    "energy regeneration rate": "err",
    "err": "err",
    # Bônus de Cura
    "bônus de cura": "healing_bonus",
    "bonus de cura": "healing_bonus",
    "cura bônus": "healing_bonus",
    "cura bonus": "healing_bonus",
    "bônus de cura%": "healing_bonus",
    "bonus de cura%": "healing_bonus",
    "healing bonus": "healing_bonus",
    "outgoing healing boost": "healing_bonus",
    "healing": "healing_bonus",
    "healing_bonus": "healing_bonus",
    # Atributos Percentuais
    "atq %": "atk_pct",
    "atq%": "atk_pct",
    "atk%": "atk_pct",
    "atk %": "atk_pct",
    "ataque%": "atk_pct",
    "attack%": "atk_pct",
    "atk_pct": "atk_pct",
    "vida %": "hp_pct",
    "vida%": "hp_pct",
    "hp%": "hp_pct",
    "hp %": "hp_pct",
    "hp_pct": "hp_pct",
    "vida_pct": "hp_pct",
    "pv%": "hp_pct",
    "defesa %": "def_pct",
    "defesa%": "def_pct",
    "def%": "def_pct",
    "def %": "def_pct",
    "defesa_pct": "def_pct",
    "def_pct": "def_pct",
    # Atributos Planos (Flats)
    "atq": "atk_flat",
    "atk": "atk_flat",
    "ataque": "atk_flat",
    "attack": "atk_flat",
    "atk_flat": "atk_flat",
    "vida": "hp_flat",
    "hp": "hp_flat",
    "hp_flat": "hp_flat",
    "pv": "hp_flat",
    "pontos de vida": "hp_flat",
    "defesa": "def_flat",
    "def": "def_flat",
    "defesa_flat": "def_flat",
    "def_flat": "def_flat",
    # Bônus Elementais (Genshin / HSR / ZZZ)
    "pyro dmg": "pyro_dmg",
    "pyro dmg bonus": "pyro_dmg",
    "bônus de dano pyro": "pyro_dmg",
    "bonus de dano pyro": "pyro_dmg",
    "dano pyro": "pyro_dmg",
    "dano de pyro": "pyro_dmg",
    "pyro": "pyro_dmg",
    "fire dmg": "fire_dmg",
    "fire dmg bonus": "fire_dmg",
    "bônus de dano de fogo": "fire_dmg",
    "bonus de dano de fogo": "fire_dmg",
    "bônus de dano fogo": "fire_dmg",
    "bonus de dano fogo": "fire_dmg",
    "dano de fogo": "fire_dmg",
    "dano fogo": "fire_dmg",
    "fogo": "fire_dmg",
    "hydro dmg": "hydro_dmg",
    "hydro dmg bonus": "hydro_dmg",
    "bônus de dano hydro": "hydro_dmg",
    "bonus de dano hydro": "hydro_dmg",
    "dano hydro": "hydro_dmg",
    "dano de hydro": "hydro_dmg",
    "hydro": "hydro_dmg",
    "bônus de dano de água": "hydro_dmg",
    "bonus de dano de agua": "hydro_dmg",
    "dano de agua": "hydro_dmg",
    "dano agua": "hydro_dmg",
    "bônus de dano agua": "hydro_dmg",
    "bonus de dano agua": "hydro_dmg",
    "electro dmg": "electro_dmg",
    "electro dmg bonus": "electro_dmg",
    "bônus de dano electro": "electro_dmg",
    "bonus de dano electro": "electro_dmg",
    "dano electro": "electro_dmg",
    "dano de electro": "electro_dmg",
    "electro": "electro_dmg",
    "eletro": "electro_dmg",
    "lightning dmg": "lightning_dmg",
    "lightning dmg bonus": "lightning_dmg",
    "bônus de dano de raio": "lightning_dmg",
    "bonus de dano de raio": "lightning_dmg",
    "bônus de dano raio": "lightning_dmg",
    "bonus de dano raio": "lightning_dmg",
    "dano de raio": "lightning_dmg",
    "dano raio": "lightning_dmg",
    "raio": "lightning_dmg",
    "electric dmg": "electric_dmg",
    "electric dmg bonus": "electric_dmg",
    "bônus de dano elétrico": "electric_dmg",
    "bonus de dano eletrico": "electric_dmg",
    "bônus de dano de elétrico": "electric_dmg",
    "bonus de dano de eletrico": "electric_dmg",
    "dano elétrico": "electric_dmg",
    "dano eletrico": "electric_dmg",
    "dano de eletrico": "electric_dmg",
    "cryo dmg": "cryo_dmg",
    "cryo dmg bonus": "cryo_dmg",
    "bônus de dano cryo": "cryo_dmg",
    "bonus de dano cryo": "cryo_dmg",
    "dano cryo": "cryo_dmg",
    "dano de cryo": "cryo_dmg",
    "cryo": "cryo_dmg",
    "ice dmg": "ice_dmg",
    "ice dmg bonus": "ice_dmg",
    "bônus de dano de gelo": "ice_dmg",
    "bonus de dano de gelo": "ice_dmg",
    "bônus de dano gelo": "ice_dmg",
    "bonus de dano gelo": "ice_dmg",
    "dano de gelo": "ice_dmg",
    "dano gelo": "ice_dmg",
    "gelo": "ice_dmg",
    "anemo dmg": "anemo_dmg",
    "anemo dmg bonus": "anemo_dmg",
    "bônus de dano anemo": "anemo_dmg",
    "bonus de dano anemo": "anemo_dmg",
    "dano anemo": "anemo_dmg",
    "dano de anemo": "anemo_dmg",
    "anemo": "anemo_dmg",
    "wind dmg": "wind_dmg",
    "wind dmg bonus": "wind_dmg",
    "bônus de dano de vento": "wind_dmg",
    "bonus de dano de vento": "wind_dmg",
    "bônus de dano vento": "wind_dmg",
    "bonus de dano vento": "wind_dmg",
    "dano de vento": "wind_dmg",
    "dano vento": "wind_dmg",
    "vento": "wind_dmg",
    "geo dmg": "geo_dmg",
    "geo dmg bonus": "geo_dmg",
    "bônus de dano geo": "geo_dmg",
    "bonus de dano geo": "geo_dmg",
    "dano geo": "geo_dmg",
    "dano de geo": "geo_dmg",
    "geo": "geo_dmg",
    "dendro dmg": "dendro_dmg",
    "dendro dmg bonus": "dendro_dmg",
    "bônus de dano dendro": "dendro_dmg",
    "bonus de dano dendro": "dendro_dmg",
    "dano dendro": "dendro_dmg",
    "dano de dendro": "dendro_dmg",
    "dendro": "dendro_dmg",
    "physical dmg": "physical_dmg",
    "physical dmg bonus": "physical_dmg",
    "bônus de dano físico": "physical_dmg",
    "bonus de dano fisico": "physical_dmg",
    "dano físico": "physical_dmg",
    "dano fisico": "physical_dmg",
    "físico": "physical_dmg",
    "fisico": "physical_dmg",
    "physical": "physical_dmg",
    "quantum dmg": "quantum_dmg",
    "quantum dmg bonus": "quantum_dmg",
    "bônus de dano quantum": "quantum_dmg",
    "bonus de dano quantum": "quantum_dmg",
    "bônus de dano quântico": "quantum_dmg",
    "bonus de dano quantico": "quantum_dmg",
    "dano quântico": "quantum_dmg",
    "dano quantico": "quantum_dmg",
    "quântico": "quantum_dmg",
    "quantico": "quantum_dmg",
    "quantum": "quantum_dmg",
    "imaginary dmg": "imaginary_dmg",
    "imaginary dmg bonus": "imaginary_dmg",
    "bônus de dano imaginário": "imaginary_dmg",
    "bonus de dano imaginario": "imaginary_dmg",
    "dano imaginário": "imaginary_dmg",
    "dano imaginario": "imaginary_dmg",
    "imaginário": "imaginary_dmg",
    "imaginario": "imaginary_dmg",
    "imaginary": "imaginary_dmg",
    "ether dmg": "ether_dmg",
    "ether dmg bonus": "ether_dmg",
    "bônus de dano de éter": "ether_dmg",
    "bonus de dano de eter": "ether_dmg",
    "bônus de dano éter": "ether_dmg",
    "bonus de dano eter": "ether_dmg",
    "dano de éter": "ether_dmg",
    "dano de eter": "ether_dmg",
    "dano éter": "ether_dmg",
    "dano eter": "ether_dmg",
    "éter": "ether_dmg",
    "eter": "ether_dmg",
    # HSR Específicos
    "effect hit rate": "ehr",
    "ehr": "ehr",
    "taxa de acerto de efeito": "ehr",
    "chance de acerto de efeito": "ehr",
    "chance de acerto": "ehr",
    "acerto de efeito": "ehr",
    "acerto efeito": "ehr",
    "effect res": "res",
    "res": "res",
    "resistência a efeito": "res",
    "resistencia a efeito": "res",
    "res_efeito": "res",
    "res a efeito": "res",
    "res efeito": "res",
    "outgoing healing": "healing_bonus",
    "outgoing_healing": "healing_bonus",
    # ZZZ Específicos
    "pen flat": "pen_flat",
    "pen": "pen_flat",
    "pen flat bonus": "pen_flat",
    "perfuração": "pen_flat",
    "perfuracao": "pen_flat",
    "perfuração flat": "pen_flat",
    "perfuracao flat": "pen_flat",
    "pen ratio": "pen_pct",
    "pen_pct": "pen_pct",
    "taxa de perfuração": "pen_pct",
    "taxa de perfuracao": "pen_pct",
    "perfuração%": "pen_pct",
    "perfuracao%": "pen_pct",
    "perfuracao ratio": "pen_pct",
    "perfuração ratio": "pen_pct",
    "impacto": "impact",
    "impact": "impact",
    "impact_pct": "impact",
    "taxa de controle de anomalia": "anomaly_mastery",
    "controle de anomalia": "anomaly_mastery",
    "anomaly mastery": "anomaly_mastery",
    "anomaly_mastery": "anomaly_mastery",
    "taxa de pen": "pen_pct",
    "taxa pen": "pen_pct",
    "pen%": "pen_pct",
    "bonus de cura realizada": "healing_bonus",
    "bônus de cura realizada": "healing_bonus",
    "cura realizada": "healing_bonus",
    "cura": "healing_bonus",
    "impactoo": "impact",
    "maestria de anomalia": "anomaly_mastery",
    "maest. anomalia": "anomaly_mastery",
    "maest anomalia": "anomaly_mastery",
}

_unaccented_map = {}
for _k, _v in STAT_NAME_MAP.items():
    _unaccented_map[_k] = _v
    _unaccented_map[remove_accents(_k)] = _v
STAT_NAME_MAP = _unaccented_map

# ==========================================
# WHITELIST ESTRITA DE SUBSTATS VÁLIDOS
# ==========================================
VALID_SUBSTATS = frozenset(
    {
        "spd",
        "crit_rate",
        "crit_dmg",
        "atk_pct",
        "hp_pct",
        "def_pct",
        "break_effect",
        "ehr",
        "res",
        "em",
        "er",
        "err",
        "atk_flat",
        "hp_flat",
        "def_flat",
        "anomaly_prof",
        "anomaly_mastery",
        "pen_flat",
        "pen_pct",
        "impact",
    }
)

# Fallbacks genéricos por jogo, usados quando o parser não extrai substats válidos
DEFAULT_SUBSTATS_FALLBACK = {
    "hsr": ["crit_rate", "crit_dmg", "spd", "atk_pct"],
    "genshin": ["crit_rate", "crit_dmg", "atk_pct", "er"],
    "zzz": ["crit_rate", "crit_dmg", "atk_pct"],
}


def normalize_stat_name(raw_name: str, has_percent: bool = False) -> str:
    """Normaliza o nome do atributo para chaves padrão do motor de cálculo, ignorando acentos, case e pontuação."""
    if not raw_name:
        return ""
    s = str(raw_name).strip()

    if "%" in s:
        has_percent = True
        s = s.replace("%", "")

    s = RE_PARENTHESES.sub("", s)
    if ":" in s:
        s = s.split(":")[0]
    s = s.strip()

    clean = remove_accents(s.lower())
    clean = RE_MULTIPLE_SPACES.sub(" ", clean).strip()

    mapped = STAT_NAME_MAP.get(clean)
    if not mapped:
        clean_no_dots = clean.replace(".", "").strip()
        clean_no_dots = RE_MULTIPLE_SPACES.sub(" ", clean_no_dots)
        mapped = STAT_NAME_MAP.get(clean_no_dots, clean)

    if has_percent:
        if mapped == "atk_flat":
            return "atk_pct"
        if mapped == "hp_flat" or mapped == "pv":
            return "hp_pct"
        if mapped == "def_flat":
            return "def_pct"

    return mapped


def is_stat_equivalent(stat1: str, stat2: str) -> bool:
    """Verifica equivalência entre variantes de nomes de atributos."""
    if stat1 == stat2:
        return True
    eq_groups = [
        {"cryo_dmg", "ice_dmg"},
        {"electro_dmg", "lightning_dmg", "electric_dmg"},
        {"anemo_dmg", "wind_dmg"},
        {"pyro_dmg", "fire_dmg"},
        {"er", "err"},
        {"pen_flat", "pen_pct"},
        {"em", "anomaly_prof"},
    ]
    for group in eq_groups:
        if stat1 in group and stat2 in group:
            return True
    return False


def sanitize_substats(raw_tokens: list, game_id: str) -> list:
    """
    Sanitiza uma lista de tokens brutos extraídos dos guias Markdown,
    filtrando por VALID_SUBSTATS para evitar poluição no meta_data.json.
    Mapeia nomes de atributos base (ATK, HP, DEF) para suas versões percentuais %.
    """
    cleaned = []
    seen = set()

    for raw in raw_tokens:
        token = RE_PARENTHESES.sub("", raw)
        token = RE_CLEAN_CHARS.sub("", token)
        token = token.strip()

        if not token:
            continue

        sub_tokens = RE_SUB_SPLIT.split(token)

        for st in sub_tokens:
            st = RE_SUB_TRAILING_NOTE.sub("", st.strip()).strip()
            if not st:
                continue

            if len(st.split()) > 4:
                continue

            norm = normalize_stat_name(st)
            # Em guias de build, mencoes genéricas como "ATK", "HP", "DEF" representam os percentuais %
            if norm == "atk_flat":
                norm = "atk_pct"
            elif norm == "hp_flat":
                norm = "hp_pct"
            elif norm == "def_flat":
                norm = "def_pct"

            if norm in VALID_SUBSTATS and norm not in seen:
                seen.add(norm)
                cleaned.append(norm)

    return cleaned[:5]


# ==========================================
# EXTRATOR DE PESOS DINÂMICOS BASEADO NO GUIA
# ==========================================
def extract_weights_from_guide(game_id: str, char_id: str) -> Dict[str, float]:
    """
    Busca no arquivo meta_data.json a prioridade de substatus diretamente pelo char_id (chave primária)
    e converte em pesos (0.0 a 1.0).
    Aplica Survival/Support Fallback para personagens com poucos atributos recomendados (< 4)
    e Forgiveness inteligente de atributos Flat (50% do peso da versão % correspondente).
    """
    game_id = game_id.lower().strip()
    meta_db = get_meta_data(game_id)

    char_key = str(char_id)
    char_meta = (
        meta_db.get(char_key) or meta_db.get(char_key.lower().strip()) or meta_db.get(normalize_char_name(char_key))
    )
    if char_meta:
        subs = char_meta.get("substats_priority", [])
        if subs:
            weights = {}
            scale = [1.0, 0.85, 0.70, 0.55, 0.40]
            for i, s in enumerate(subs):
                norm_name = normalize_stat_name(s)
                weight_val = scale[i] if i < len(scale) else 0.30
                weights[norm_name] = weight_val

            if "crit_rate" in weights or "crit_dmg" in weights:
                top_crit = max(weights.get("crit_rate", 0.0), weights.get("crit_dmg", 0.0), 1.0)
                weights["crit_rate"] = top_crit
                weights["crit_dmg"] = top_crit

            if "hp_pct" in weights and "hp_flat" not in weights:
                weights["hp_flat"] = round(weights["hp_pct"] * 0.5, 3)
            if "atk_pct" in weights and "atk_flat" not in weights:
                weights["atk_flat"] = round(weights["atk_pct"] * 0.5, 3)
            if "def_pct" in weights and "def_flat" not in weights:
                weights["def_flat"] = round(weights["def_pct"] * 0.5, 3)

            return weights

    return {
        "crit_rate": 1.0,
        "crit_dmg": 1.0,
        "atk_pct": 0.6,
        "hp_pct": 0.6,
        "spd": 0.6,
        "break_effect": 0.5,
        "em": 0.5,
        "er": 0.5,
        "hp_flat": 0.3,
        "atk_flat": 0.3,
        "def_flat": 0.2,
    }


# ==========================================
# MOTOR DINÂMICO DE SCORES COM MAIN STAT E SUBSTAT WEIGHTING
# ==========================================
def clean_value(val_str: str) -> Tuple[float, bool]:
    """Extrai o valor numérico de uma string de status e indica se é percentual."""
    has_pct = "%" in val_str
    match = RE_NUM_FLOAT.search(val_str)
    val = float(match.group(1)) if match else 0.0
    return val, has_pct


def score_relic(game_id: str, char_id: str, slot: str, main_stat: str, substats_str: str) -> Tuple[str, float]:
    """
    Calcula a nota de uma relíquia considerando Main Stat (40%) e Substatus (60%).
    """
    game_id = game_id.lower().strip()
    if game_id not in MAX_ROLL_VALUES:
        return "D", 0.0

    if not substats_str or substats_str.strip() in ["Sem substatus", "Status não disponíveis", ""]:
        return "D", 0.0

    weights = extract_weights_from_guide(game_id, str(char_id))
    meta_db = get_meta_data(game_id)
    char_key = str(char_id)
    char_meta = (
        meta_db.get(char_key)
        or meta_db.get(char_key.lower().strip())
        or meta_db.get(normalize_char_name(char_key))
        or {}
    )

    main_clean = main_stat.lower()
    norm_slot = normalize_slot_name(slot, game_id)

    # 1. Identifica se o slot possui Main Stat Fixo
    is_fixed_main = False
    if norm_slot in ["flower", "plume", "head", "hands", "slot_1", "slot_2", "slot_3"]:
        is_fixed_main = True

    # Extrai main stat normalizado
    raw_main_name = main_clean.split("(")[0].strip()
    has_pct = "%" in main_clean or "%" in main_stat
    main_stat_norm = normalize_stat_name(raw_main_name, has_percent=has_pct)

    # 2. Avalia a validade do Main Stat (Sistema de 3 Níveis: 1.0 Ideal, 0.6 Útil/Alternativo, 0.0 Inútil)
    main_stat_tier = 0.0
    if is_fixed_main:
        main_stat_tier = 1.0
    else:
        guide_mains = char_meta.get("main_stats", {})
        slot_key = None
        for k in guide_mains:
            norm_k = normalize_slot_name(k, game_id)
            if norm_k == norm_slot or norm_k in norm_slot or norm_slot in norm_k:
                slot_key = k
                break

        rec_mains = guide_mains.get(slot_key, []) if slot_key else []
        elemental_stats = {
            "pyro_dmg",
            "hydro_dmg",
            "electro_dmg",
            "cryo_dmg",
            "anemo_dmg",
            "geo_dmg",
            "dendro_dmg",
            "physical_dmg",
            "fire_dmg",
            "ice_dmg",
            "lightning_dmg",
            "electric_dmg",
            "wind_dmg",
            "ether_dmg",
            "quantum_dmg",
            "imaginary_dmg",
        }

        if rec_mains:
            norm_rec = [normalize_stat_name(m) for m in rec_mains]
            flex_tokens = {"anything", "any", "qualquer", "qualquer um", "qualquer atributo", "flexible", "flex"}
            if (
                any(ft in norm_rec for ft in flex_tokens)
                or any(is_stat_equivalent(main_stat_norm, m) for m in norm_rec)
                or main_stat_norm in elemental_stats
            ):
                main_stat_tier = 1.0
            elif weights.get(main_stat_norm, 0.0) > 0.3:
                main_stat_tier = 0.6
            else:
                main_stat_tier = 0.0
        else:
            if weights.get(main_stat_norm, 0.0) > 0.35 or main_stat_norm in elemental_stats:
                main_stat_tier = 1.0
            elif weights.get(main_stat_norm, 0.0) > 0.0:
                main_stat_tier = 0.6
            else:
                main_stat_tier = 0.0

    # 3. Pontuação de Substatus (RV - Roll Value) com suporte a Procs
    sorted_priorities = [k for k, v in sorted(weights.items(), key=lambda item: item[1], reverse=True) if v > 0.0]

    if not is_fixed_main and main_stat_norm in sorted_priorities:
        available_substats = [s for s in sorted_priorities if s != main_stat_norm]
    else:
        available_substats = sorted_priorities

    # Substatus prioritários ativos (com peso > 0.30 pós-exclusão do Main Stat)
    priority_substats = [s for s in available_substats if weights.get(s, 0.0) > 0.30]
    num_priority = len(priority_substats)

    max_possible_sub_score = 0.0

    if num_priority == 1:
        # Caso 1: Apenas 1 substatus prioritário pós-exclusão (ex: apenas ER)
        # 4.0 rolagens nele + 5.0 rolagens no pool de "Outros Atributos" (peso base 0.30)
        w1 = weights.get(priority_substats[0], 1.0)
        max_possible_sub_score = (4.0 * w1) + (5.0 * 0.30)
    elif num_priority == 2:
        # Caso 2: Apenas 2 substatus prioritários pós-exclusão
        # 4.0 rolagens no 1º, 3.0 no 2º + 2.0 rolagens no pool de "Outros Atributos" (peso base 0.30)
        w1 = weights.get(priority_substats[0], 1.0)
        w2 = weights.get(priority_substats[1], 0.85)
        max_possible_sub_score = (4.0 * w1) + (3.0 * w2) + (2.0 * 0.30)
    elif num_priority == 3:
        # Caso 3: Apenas 3 substatus prioritários pós-exclusão
        # 5.0 rolagens no 1º, 2.0 no 2º, 1.0 no 3º + 1.0 rolagem no pool de "Outros Atributos" (peso base 0.30)
        w1 = weights.get(priority_substats[0], 1.0)
        w2 = weights.get(priority_substats[1], 0.85)
        w3 = weights.get(priority_substats[2], 0.70)
        max_possible_sub_score = (5.0 * w1) + (2.0 * w2) + (1.0 * w3) + (1.0 * 0.30)
    else:
        # Caso 4: 4 ou mais substatus prioritários (ou fallback se 0)
        # Distribuição padrão [6.0, 1.0, 1.0, 1.0] sem rolagens para "Outros Atributos"
        ideal_substats = available_substats[:4]
        roll_distribution = [6.0, 1.0, 1.0, 1.0]
        for i, sub in enumerate(ideal_substats):
            w = weights.get(sub, 0.0)
            dist = roll_distribution[i] if i < len(roll_distribution) else 1.0
            max_possible_sub_score += w * dist

    if max_possible_sub_score <= 0:
        max_possible_sub_score = 3.5

    game_specs = GAME_ROLL_SPECS[game_id]["stats"]
    actual_sub_score = 0.0

    parts = substats_str.split(",")
    for p in parts:
        if ":" in p:
            name, val_str = p.split(":", 1)
            val, has_p = clean_value(val_str)
            sub_name_norm = normalize_stat_name(name, has_percent=has_p)

            spec = game_specs.get(sub_name_norm)
            if spec:
                max_roll = spec["max"]
                if max_roll > 0.0:
                    rv = val / max_roll
                    actual_sub_score += rv * weights.get(sub_name_norm, 0.0)

    sub_ratio = min(1.0, actual_sub_score / max_possible_sub_score)

    # 4. Composição da Nota Final
    if is_fixed_main:
        rating_pct = (0.30 + 0.70 * sub_ratio) * 100.0
    else:
        main_stat_credit = 0.40 * main_stat_tier
        rating_pct = (main_stat_credit + 0.60 * sub_ratio) * 100.0

    rating_pct = round(rating_pct, 1)

    if rating_pct >= 90.0:
        grade = "SSS"
    elif rating_pct >= 75.0:
        grade = "SS"
    elif rating_pct >= 60.0:
        grade = "S"
    elif rating_pct >= 45.0:
        grade = "A"
    elif rating_pct >= 30.0:
        grade = "B"
    elif rating_pct >= 15.0:
        grade = "C"
    else:
        grade = "D"

    return grade, rating_pct


def estimate_relic_procs(game_id: str, substats_str: str) -> Dict[str, Dict[str, float]]:
    """
    Dada uma string de substatus (ex: "Taxa Crítica: 9.3%, Dano Crítico: 14.0%"),
    calcula os procs estimados (rolls), valor numérico real, RV e roll médio de cada substatus.
    """
    game_id = game_id.lower().strip()
    if game_id not in GAME_ROLL_SPECS:
        return {}

    specs = GAME_ROLL_SPECS[game_id]["stats"]
    result = {}

    parts = substats_str.split(",")
    for p in parts:
        if ":" in p:
            name, val_str = p.split(":", 1)
            val, has_p = clean_value(val_str)
            sub_name_norm = normalize_stat_name(name, has_percent=has_p)

            spec = specs.get(sub_name_norm)
            if spec and spec["max"] > 0:
                avg_roll = spec["avg"]
                max_roll = spec["max"]
                est_procs = round(val / avg_roll) if avg_roll > 0 else 0
                rv = round(val / max_roll, 2)
                result[sub_name_norm] = {
                    "stat_name": sub_name_norm,
                    "value": val,
                    "estimated_procs": est_procs,
                    "roll_value": rv,
                    "min_roll": spec["min"],
                    "avg_roll": spec["avg"],
                    "max_roll": spec["max"],
                }
    return result


# ==========================================
# MOTOR DE ÍNDICE DE SORTE E EFICIÊNCIA DE ROLAGENS (LUCK SCORE)
# ==========================================
def calculate_relic_luck_index(
    game_id: str, char_id: str, slot: str, main_stat: str, substats_str: str
) -> Dict[str, Any]:
    """
    Calcula a Eficiência de Rolagens e o Índice de Sorte (Luck Score) de uma relíquia individual.
    Retorna métricas detalhadas com análise visual de cada substatus (bom vs ruim).
    """
    game_id = game_id.lower().strip()
    if not substats_str or substats_str.strip() in ["Sem substatus", "Status não disponíveis", ""]:
        return {
            "luck_score": 0.0,
            "rv_pct": 0.0,
            "total_rv": 0.0,
            "luck_grade": "D",
            "luck_badge": "💀 Amaldiçoado",
            "luck_title": "Amaldiçoado pelo RNG",
            "procs": {},
            "substats_analyzed": [],
            "useful_procs": 0,
            "wasted_procs": 0,
        }

    procs = estimate_relic_procs(game_id, substats_str)
    weights = extract_weights_from_guide(game_id, str(char_id))

    total_rv = sum(p["roll_value"] for p in procs.values())

    useful_procs = 0
    wasted_procs = 0
    useful_weight_sum = 0.0
    substats_analyzed = []

    parts = [s.strip() for s in substats_str.split(",") if s.strip()]
    for p in parts:
        if ":" in p:
            name, val_str = p.split(":", 1)
            val, has_p = clean_value(val_str)
            sub_name_norm = normalize_stat_name(name, has_percent=has_p)

            pdata = procs.get(sub_name_norm, {})
            est_p = pdata.get("estimated_procs", 1)
            rv_val = pdata.get("roll_value", 0.0)
            w = weights.get(sub_name_norm, 0.0)

            if w >= 0.70:
                if est_p >= 3:
                    status = "god"
                    badge = f"🔥 Perfeito (+{est_p})"
                    color = "#34d399"
                else:
                    status = "good"
                    badge = f"✅ Ótimo (+{est_p})"
                    color = "#10b981"
                useful_procs += est_p
                useful_weight_sum += rv_val * w
            elif w >= 0.40:
                status = "useful"
                badge = f"👍 Útil (+{est_p})"
                color = "#fbbf24"
                useful_procs += est_p
                useful_weight_sum += rv_val * w
            else:
                status = "bad"
                badge = "💀 Desperdício" if est_p <= 1 else f"💀 Lixo (+{est_p})"
                color = "#f87171"
                wasted_procs += est_p

            substats_analyzed.append(
                {
                    "raw_text": p,
                    "stat_name": sub_name_norm,
                    "display_name": name.strip(),
                    "value_str": val_str.strip(),
                    "procs": est_p,
                    "roll_value": rv_val,
                    "weight": round(w, 2),
                    "status": status,
                    "status_badge": badge,
                    "status_color": color,
                }
            )

    # Max RV teórico para 5-6 rolagens de 5★ é cerca de 5.0 a 6.0 RV
    rv_pct = round(min(100.0, (total_rv / 5.0) * 100.0), 1) if total_rv > 0 else 0.0

    # Synergistic Roll Ratio: % do valor que caiu em status úteis
    useful_ratio = (useful_weight_sum / total_rv) if total_rv > 0 else 0.0
    useful_ratio = min(1.0, useful_ratio)

    # Pontuação de Sorte (0.0 a 100.0)
    luck_score = round((useful_ratio * 65.0) + (rv_pct * 0.35), 1)
    luck_score = min(100.0, max(0.0, luck_score))

    if luck_score >= 93.0:
        grade, badge, title = "SSS+", "🦄 Deus do RNG", "Top 0.1% God-tier"
    elif luck_score >= 85.0:
        grade, badge, title = "SS", "⚡ Abençoado", "Top 1% Excepcional"
    elif luck_score >= 74.0:
        grade, badge, title = "S", "🔥 Sortudo", "Top 5% Excelente"
    elif luck_score >= 60.0:
        grade, badge, title = "A", "👍 Boa Peça", "Sorte Acima da Média"
    elif luck_score >= 45.0:
        grade, badge, title = "B", "⚖️ Mediana", "Sorte Mediana"
    elif luck_score >= 30.0:
        grade, badge, title = "C", "🌧️ Azarado", "Rolagens Ruins"
    else:
        grade, badge, title = "D", "💀 Amaldiçoado", "Lixo de RNG"

    return {
        "luck_score": luck_score,
        "rv_pct": rv_pct,
        "total_rv": round(total_rv, 2),
        "luck_grade": grade,
        "luck_badge": badge,
        "luck_title": title,
        "procs": procs,
        "substats_analyzed": substats_analyzed,
        "useful_procs": useful_procs,
        "wasted_procs": wasted_procs,
    }


def format_slot_display_name(slot_str: str, game_id: str = "") -> str:
    """Formatador de nome de exibição de slot de relíquia/artefato por jogo."""
    norm = normalize_slot_name(slot_str, game_id)
    g = game_id.lower().strip()

    if g == "genshin":
        mapping = {
            "flower": "🌸 Flor da Vida",
            "plume": "🪶 Pluma da Morte",
            "sands": "⏳ Ampulheta",
            "goblet": "🍷 Cálice",
            "circlet": "👑 Tiara",
        }
        return mapping.get(norm, f"Slot {slot_str}")
    elif g == "hsr":
        mapping = {
            "head": "🪖 Cabeça",
            "hands": "🧤 Mãos",
            "body": "🛡️ Corpo",
            "feet": "👢 Botas",
            "planar_sphere": "🔮 Esfera Plana",
            "link_rope": "🪢 Corda de Ligação",
        }
        return mapping.get(norm, f"Slot {slot_str}")
    elif g == "zzz":
        mapping = {
            "slot_1": "💿 Disco Slot 1 (HP)",
            "slot_2": "💿 Disco Slot 2 (ATK)",
            "slot_3": "💿 Disco Slot 3 (DEF)",
            "slot_4": "💿 Disco Slot 4",
            "slot_5": "💿 Disco Slot 5",
            "slot_6": "💿 Disco Slot 6",
        }
        return mapping.get(norm, f"Disco Slot {slot_str}")

    return f"Slot {slot_str}"


def analyze_account_luck(game_id: str, roster_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analisa todas as relíquias equipadas no Roster do usuário e calcula o Índice de Sorte Global da Conta.
    Identifica: Peça God Roll, Peça Cursed Roll, Personagem mais sortudo e menos sortudo.
    """
    game_id = game_id.lower().strip()
    total_relics = 0
    all_relic_entries = []
    char_luck_map = {}

    for char in roster_data:
        char_name = char.get("name", "Desconhecido")
        char_id = str(char.get("id") or char.get("character_id") or char_name)
        relics = char.get("relics") or char.get("artifacts") or char.get("discs") or []

        char_scores = []
        for relic in relics:
            slot = str(relic.get("slot", ""))
            main_stat = relic.get("main") or relic.get("main_stat") or ""
            substats_str = relic.get("sub", "")
            if not substats_str:
                continue

            luck_data = calculate_relic_luck_index(game_id, char_id, slot, main_stat, substats_str)
            if luck_data["luck_score"] > 0 or luck_data["total_rv"] > 0:
                total_relics += 1
                slot_disp = format_slot_display_name(slot, game_id)
                entry = {
                    "character_name": char_name,
                    "character_icon": char.get("icon", ""),
                    "relic_name": relic.get("name", "Relíquia"),
                    "relic_icon": relic.get("icon", ""),
                    "slot": slot,
                    "slot_display": slot_disp,
                    "main_stat": main_stat,
                    "substats_str": substats_str,
                    "substats_analyzed": luck_data["substats_analyzed"],
                    "luck_score": luck_data["luck_score"],
                    "rv_pct": luck_data["rv_pct"],
                    "total_rv": luck_data["total_rv"],
                    "luck_grade": luck_data["luck_grade"],
                    "luck_badge": luck_data["luck_badge"],
                    "luck_title": luck_data["luck_title"],
                    "useful_procs": luck_data["useful_procs"],
                    "wasted_procs": luck_data["wasted_procs"],
                }
                all_relic_entries.append(entry)
                char_scores.append(luck_data["luck_score"])

        if char_scores:
            avg_char_luck = round(sum(char_scores) / len(char_scores), 1)
            char_luck_map[char_name] = {
                "character_name": char_name,
                "character_icon": char.get("icon", ""),
                "rank_str": char.get("rank_str", "C0"),
                "level": char.get("level", 1),
                "avg_luck": avg_char_luck,
                "relic_count": len(char_scores),
            }

    if not all_relic_entries:
        return {
            "game_id": game_id,
            "overall_account_luck": 0.0,
            "luck_title": "Sem Relíquias Equipadas",
            "luck_badge": "❓ Indefinido",
            "total_relics_analyzed": 0,
            "god_roll": None,
            "cursed_roll": None,
            "luckiest_character": None,
            "cursed_character": None,
            "character_breakdown": [],
        }

    all_relic_entries.sort(key=lambda x: x["luck_score"], reverse=True)
    god_roll = all_relic_entries[0]
    cursed_roll = all_relic_entries[-1]

    account_luck_avg = round(sum(r["luck_score"] for r in all_relic_entries) / len(all_relic_entries), 1)

    if account_luck_avg >= 85.0:
        account_title = "👑 Rei da Sorte do Servidor (Top 1%)"
        account_badge = "SSS Luck Account"
    elif account_luck_avg >= 75.0:
        account_title = "⚡ Abençoado pelo RNG"
        account_badge = "SS Luck Account"
    elif account_luck_avg >= 65.0:
        account_title = "✨ Conta Sortuda"
        account_badge = "S Luck Account"
    elif account_luck_avg >= 50.0:
        account_title = "⚖️ Equilibrado (Sorte Média)"
        account_badge = "A Luck Account"
    elif account_luck_avg >= 35.0:
        account_title = "🌧️ Conta Azarada"
        account_badge = "B Luck Account"
    else:
        account_title = "💀 Amaldiçoada pela HoYoverse"
        account_badge = "Cursed Account"

    char_list = list(char_luck_map.values())
    char_list.sort(key=lambda x: x["avg_luck"], reverse=True)

    luckiest_char = char_list[0] if char_list else None
    cursed_char = char_list[-1] if char_list else None

    return {
        "game_id": game_id,
        "overall_account_luck": account_luck_avg,
        "luck_title": account_title,
        "luck_badge": account_badge,
        "total_relics_analyzed": len(all_relic_entries),
        "god_roll": god_roll,
        "cursed_roll": cursed_roll,
        "luckiest_character": luckiest_char,
        "cursed_character": cursed_char,
        "character_breakdown": char_list,
        "all_relics": all_relic_entries[:30],
    }


# ==========================================
# AVALIADOR DE STATUS GERAIS DO PERSONAGEM
# ==========================================
def evaluate_general_stats(game_id: str, char_id: str, final_stats: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Compara os status consolidados reais do personagem contra os benchmarks ideais do metagame.
    Retorna uma lista estruturada de avaliações.
    """
    game_id = game_id.lower().strip()
    meta_db = get_meta_data(game_id)

    char_meta = meta_db.get(str(char_id))
    if not char_meta or "general_benchmarks" not in char_meta:
        return []

    benchmarks = char_meta.get("general_benchmarks", {})
    results = []

    normalized_player_stats = {}
    for p_name, p_val in final_stats.items():
        norm_key = normalize_stat_name(p_name)
        normalized_player_stats[norm_key] = (p_name, p_val)

    for bench_key, target_expr in benchmarks.items():
        player_stat_info = normalized_player_stats.get(bench_key)
        if not player_stat_info:
            continue

        p_name, p_val_str = player_stat_info

        target_val = clean_value(target_expr)[0]
        actual_val = clean_value(p_val_str)[0]

        operator = ">="
        if "<=" in target_expr:
            operator = "<="
        elif "<" in target_expr:
            operator = "<"
        elif ">" in target_expr:
            operator = ">"

        is_good = False
        if operator == ">=":
            is_good = actual_val >= target_val
        elif operator == "<=":
            is_good = actual_val <= target_val
        elif operator == ">":
            is_good = actual_val > target_val
        elif operator == "<":
            is_good = actual_val < target_val

        status = "GOOD" if is_good else "LOW"
        if status == "GOOD":
            msg = f"Sua {p_name} ({p_val_str}) atingiu a meta recomendada ({target_expr})!"
        else:
            msg = f"Aumente sua {p_name} ({p_val_str}), a meta recomendada é {target_expr}."

        results.append({"stat": p_name, "target": target_expr, "actual": p_val_str, "status": status, "message": msg})

    return results


# ==========================================
# GERADOR DE ARQUIVOS META_DATA.JSON (EXTRATOR DE IDS)
# ==========================================
def generate_meta_json_from_markdown(game_id: str):
    """
    Varre todos os guias markdown do jogo e regenera o arquivo meta_data.json
    tendo o ID do personagem como chave principal.
    """
    game_id = game_id.lower().strip()

    guias_dir = f"{game_id}/guias"
    meta_db = {}
    master_ids = fetch_master_id_list(game_id)

    def parse_hsr(content):
        meta = {"main_stats": {}, "substats_priority": [], "general_benchmarks": {}}
        matches = RE_HSR_MAIN_SLOTS.findall(content)
        for slot, val in matches:
            tokens = RE_SLOT_SPLIT.split(val)
            stats = []
            for t in tokens:
                t_clean = RE_PARENTHESES.sub("", t).strip()
                if t_clean:
                    norm = normalize_stat_name(t_clean)
                    if norm and norm not in stats:
                        stats.append(norm)
            norm_s = normalize_slot_name(slot, "hsr")
            meta["main_stats"][norm_s] = stats

        sub_match = RE_SUB_HEADER.search(content) or RE_SUB_INLINE.search(content)
        if sub_match:
            sub_line = sub_match.group(1).strip()
            if not sub_line:
                lines = content[sub_match.start(1) :].split("\n")
                for l in lines:
                    l_stripped = l.strip()
                    if l_stripped and not l_stripped.startswith("#"):
                        sub_line = l_stripped
                        break
            raw_tokens = [tok.strip() for tok in RE_SUB_TOKEN_SPLIT.split(sub_line) if tok.strip()]
            meta["substats_priority"] = sanitize_substats(raw_tokens, "hsr")

        benchmarks = {}
        endgame_sec = RE_ENDGAME_SEC.search(content)
        if endgame_sec:
            for line in endgame_sec.group(1).splitlines():
                l_str = line.strip()
                if not l_str or not (l_str.startswith("-") or l_str.startswith("*")) or ":" not in l_str:
                    continue
                s_label, s_raw = l_str.lstrip("-* \t").split(":", 1)
                s_label = s_label.replace("**", "").replace("`", "").strip()
                s_raw = s_raw.replace("**", "").replace("`", "").strip()
                if not s_label or not s_raw or s_label.lower().startswith(("note", "nota", "justificativa", "other ")):
                    continue
                if not RE_HAS_DIGIT.search(s_raw):
                    continue
                norm_k = normalize_stat_name(s_label)
                if not norm_k:
                    continue
                m_plus = RE_BENCH_PLUS.fullmatch(s_raw)
                m_paren = RE_BENCH_PAREN.fullmatch(s_raw)
                if m_plus:
                    formatted_val = f">= {m_plus.group(1)}{m_plus.group(2)}"
                elif m_paren:
                    formatted_val = f">= {m_paren.group(1)}{m_paren.group(2)} {m_paren.group(3)}"
                else:
                    formatted_val = s_raw
                benchmarks[norm_k] = formatted_val
        else:
            # Fallback legado apenas dentro da seção de Atributos Recomendados (nunca sobre texto corrido de review/kit)
            stats_sec_m = RE_STATS_REC_SEC.search(content)
            scoped_txt = stats_sec_m.group(1) if stats_sec_m else ""
            if scoped_txt:
                speed_goal = RE_SPEED_GOAL.search(scoped_txt)
                if speed_goal:
                    val = next(v for v in speed_goal.groups() if v)
                    benchmarks["spd"] = f">= {val}"
                crit_goal = RE_CRIT_GOAL.search(scoped_txt)
                if crit_goal:
                    val = next(v for v in crit_goal.groups() if v)
                    benchmarks["crit_rate"] = f">= {val}%"
                be_goal = RE_BE_GOAL.search(scoped_txt)
                if be_goal:
                    val = next(v for v in be_goal.groups() if v)
                    benchmarks["break_effect"] = f">= {val}%"
        meta["general_benchmarks"] = benchmarks
        return meta

    def parse_zzz(content):
        meta = {"main_stats": {}, "substats_priority": [], "general_benchmarks": {}}
        matches = RE_ZZZ_MAIN_SLOTS.findall(content)
        for slot, val in matches:
            tokens = RE_SLOT_SPLIT.split(val)
            stats = []
            for t in tokens:
                t_clean = RE_PARENTHESES.sub("", t).strip()
                if t_clean:
                    norm = normalize_stat_name(t_clean)
                    if norm and norm not in stats:
                        stats.append(norm)
            meta["main_stats"][f"slot_{slot}"] = stats

        sub_match = RE_SUB_HEADER.search(content) or RE_SUB_INLINE.search(content)
        if sub_match:
            sub_line = sub_match.group(1).strip()
            raw_tokens = [tok.strip() for tok in RE_SUB_TOKEN_SPLIT.split(sub_line) if tok.strip()]
            meta["substats_priority"] = sanitize_substats(raw_tokens, "zzz")
        return meta

    def parse_genshin(content):
        meta = {"main_stats": {}, "substats_priority": [], "general_benchmarks": {}}

        main_sec_match = RE_GENSHIN_MAIN_SEC.search(content)
        if main_sec_match:
            main_sec = main_sec_match.group(1)
            lines = main_sec.split("\n")
            for line in lines:
                m = RE_GENSHIN_MAIN_LINE_BOLD.search(line) or RE_GENSHIN_MAIN_LINE_PLAIN.search(line)
                if m:
                    slot_label = m.group(1).lower().strip()
                    val = m.group(2)
                    if "sand" in slot_label or "ampulheta" in slot_label or "areia" in slot_label:
                        slot_key = "sands"
                    elif (
                        "goblet" in slot_label
                        or "cálice" in slot_label
                        or "calice" in slot_label
                        or "copo" in slot_label
                    ):
                        slot_key = "goblet"
                    elif "circlet" in slot_label or "tiara" in slot_label or "coroa" in slot_label:
                        slot_key = "circlet"
                    else:
                        slot_key = slot_label.replace(" ", "_")

                    tokens = RE_GENSHIN_SLOT_SPLIT.split(val)
                    stats = []
                    for t in tokens:
                        t_clean = RE_PARENTHESES.sub("", t).replace("*", "").strip()
                        if t_clean:
                            norm = normalize_stat_name(t_clean)
                            if norm and norm not in stats:
                                stats.append(norm)
                    meta["main_stats"][slot_key] = stats

        sub_match = RE_GENSHIN_SUB_HEADER.search(content) or RE_GENSHIN_SUB_INLINE.search(content)

        if sub_match:
            sub_line = sub_match.group(1).strip()
            raw_tokens = [tok.strip() for tok in RE_GENSHIN_SUB_TOKEN_SPLIT.split(sub_line) if tok.strip()]
            meta["substats_priority"] = sanitize_substats(raw_tokens, "genshin")
        return meta

    if game_id == "hsr":
        parse_fn = parse_hsr
    elif game_id == "zzz":
        parse_fn = parse_zzz
    else:
        parse_fn = parse_genshin

    # Índice auxiliar dinâmico para resolução de títulos/variantes sem hardcoding (ex: 'Aha' <-> 'Aeon ★ Aha')
    id_to_canonical_name = {}
    id_to_tokens = {}
    for m_name, m_cid in master_ids.items():
        cid_s = str(m_cid)
        norm_m = normalize_char_name(m_name)
        if norm_m:
            id_to_tokens.setdefault(cid_s, set()).update(t for t in norm_m.split("_") if len(t) >= 3)

    # Prioriza nomes oficiais do roster/manifesto para exibição
    for src_path in [
        f"{game_id}/roster_data_{game_id}.json",
        get_resource_path(os.path.join("static_data", f"{game_id}_manifest.json")),
    ]:
        if os.path.exists(src_path):
            try:
                with open(src_path, "r", encoding="utf-8") as sf:
                    raw_s = json.load(sf)
                    items_s = (
                        raw_s
                        if isinstance(raw_s, list)
                        else list((raw_s.get("characters", raw_s) if isinstance(raw_s, dict) else {}).values())
                    )
                    for it in items_s:
                        if not isinstance(it, dict):
                            continue
                        it_id = str(it.get("id") if isinstance(raw_s, list) else it.get("hoyolab_id") or "").strip()
                        it_name = str(it.get("name") or "").strip()
                        if it_id and it_name and "nickname" not in it_name.lower() and it_id != "9999":
                            id_to_canonical_name.setdefault(it_id, it_name)
                            norm_it = normalize_char_name(it_name)
                            if norm_it:
                                id_to_tokens.setdefault(it_id, set()).update(
                                    t for t in norm_it.split("_") if len(t) >= 3
                                )
            except (OSError, json.JSONDecodeError, TypeError, AttributeError) as exc:
                logger.warning("[CALC] Falha ao indexar nomes canônicos de %s: %s", src_path, exc)

    def _resolve_guide_id(raw_n: str, norm_r: str, doc_content: str) -> str:
        direct = master_ids.get(norm_r) or master_ids.get(raw_n.lower())
        if direct:
            return str(direct)
        if len(norm_r) >= 3:
            # Busca dinâmica: token inteiro único no catálogo OU menção literal do nome canônico dentro do guia
            token_hits = [cid for cid, toks in id_to_tokens.items() if norm_r in toks]
            if len(token_hits) == 1:
                return token_hits[0]
            content_lower = doc_content.lower()
            content_hits = [
                cid
                for cid in (token_hits or list(id_to_canonical_name.keys()))
                if len(id_to_canonical_name.get(cid, "")) >= 5
                and id_to_canonical_name[cid].lower() in content_lower
                and norm_r in id_to_tokens.get(cid, set())
            ]
            if len(content_hits) == 1:
                return content_hits[0]
        return norm_r

    preliminary_ids = set()

    if os.path.exists(guias_dir):
        try:
            files = sorted(os.listdir(guias_dir))
            for f in files:
                if f.endswith(".md"):
                    raw_name = f[:-3].replace("_", " ").strip()
                    display_name = raw_name.title()
                    if display_name.lower().startswith("dan heng"):
                        display_name = display_name.replace("•", "•")

                    normalized_raw = normalize_char_name(raw_name)
                    filepath = os.path.join(guias_dir, f)
                    try:
                        with open(filepath, "r", encoding="utf-8") as file:
                            content = file.read()
                        is_prelim = "ai_preliminary" in content or "Guia Preliminar" in content
                        char_id = str(_resolve_guide_id(raw_name, normalized_raw, content))

                        # Guia oficial (Prydwen/atualizado) sempre tem precedência sobre guia preliminar Day-1
                        if char_id in meta_db and is_prelim and char_id not in preliminary_ids:
                            continue

                        char_meta = parse_fn(content)
                        canonical_disp = id_to_canonical_name.get(char_id)
                        char_meta["name"] = canonical_disp if canonical_disp else display_name
                        meta_db[char_id] = char_meta
                        if is_prelim:
                            preliminary_ids.add(char_id)
                        else:
                            preliminary_ids.discard(char_id)
                    except Exception as ex:
                        print(f"[WARN] Erro ao parsear {filepath}: {ex}")
        except Exception as e:
            print(f"[WARN] Erro ao listar diretório {guias_dir}: {e}")

    output_path = f"{game_id}/meta_data_{game_id}.json"
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(meta_db, out, indent=4, ensure_ascii=False)

    if game_id in META_DATA_CACHE:
        del META_DATA_CACHE[game_id]


# ==========================================================================
# CALCULADORA DE MATERIAIS DE ASCENSÃO (MANTIDA INTACTA)
# ==========================================================================
ASCENSION_TABLES = {
    "genshin": {
        1: {"xp": 0, "currency": 0, "boss": 0},
        20: {"xp": 120000, "currency": 24000, "boss": 0},
        40: {"xp": 400000, "currency": 120000, "boss": 2},
        50: {"xp": 750000, "currency": 240000, "boss": 6},
        60: {"xp": 1300000, "currency": 450000, "boss": 14},
        70: {"xp": 2100000, "currency": 750000, "boss": 26},
        80: {"xp": 3600000, "currency": 1250000, "boss": 46},
        90: {"xp": 5800000, "currency": 2090000, "boss": 46},
    },
    "hsr": {
        1: {"xp": 0, "currency": 0, "boss": 0},
        20: {"xp": 110000, "currency": 15000, "boss": 0},
        30: {"xp": 280000, "currency": 45000, "boss": 0},
        40: {"xp": 600000, "currency": 110000, "boss": 4},
        50: {"xp": 1100000, "currency": 220000, "boss": 12},
        60: {"xp": 1900000, "currency": 420000, "boss": 28},
        70: {"xp": 3100000, "currency": 750000, "boss": 50},
        80: {"xp": 5100000, "currency": 1300000, "boss": 65},
    },
    "zzz": {
        1: {"xp": 0, "currency": 0, "boss": 0},
        10: {"xp": 25000, "currency": 5000, "boss": 0},
        20: {"xp": 80000, "currency": 15000, "boss": 0},
        30: {"xp": 200000, "currency": 40000, "boss": 2},
        40: {"xp": 450000, "currency": 100000, "boss": 8},
        50: {"xp": 900000, "currency": 250000, "boss": 20},
        60: {"xp": 1800000, "currency": 600000, "boss": 40},
    },
}


def calculate_ascension(
    game_id,
    current_lvl,
    target_lvl,
    char_name: Optional[str] = None,
    char_profile: Optional[Dict[str, Any]] = None,
):
    """
    Calcula a diferença de recursos necessários entre o nível atual e o nível alvo,
    enriquecendo opcionalmente com materiais reais do personagem via static_data_manager.
    """
    game_id = game_id.lower().strip()
    if game_id not in ASCENSION_TABLES:
        return None

    table = ASCENSION_TABLES[game_id]

    def get_closest_values(lvl):
        sorted_keys = sorted(table.keys())
        xp, curr, boss = 0, 0, 0
        for k in sorted_keys:
            if k <= lvl:
                xp = table[k]["xp"]
                curr = table[k]["currency"]
                boss = table[k]["boss"]
            else:
                prev_key = next((x for x in reversed(sorted_keys) if x < k), 1)
                factor = (lvl - prev_key) / (k - prev_key)
                xp = table[prev_key]["xp"] + int((table[k]["xp"] - table[prev_key]["xp"]) * factor)
                curr = table[prev_key]["currency"] + int((table[k]["currency"] - table[prev_key]["currency"]) * factor)
                boss = table[prev_key]["boss"]
                break
        return {"xp": xp, "currency": curr, "boss": boss}

    current_res = get_closest_values(current_lvl)
    target_res = get_closest_values(target_lvl)

    xp_diff = max(0, target_res["xp"] - current_res["xp"])
    currency_diff = max(0, target_res["currency"] - current_res["currency"])
    boss_diff = max(0, target_res["boss"] - current_res["boss"])

    xp_books = int(xp_diff / 20000)

    currency_name = "Mora" if game_id == "genshin" else ("Créditos" if game_id == "hsr" else "Dennys")
    boss_item_name = "Materiais de Chefe"
    local_specialty = None
    talent_material = None
    weekly_boss_mat = None
    domain_days = None
    open_today = True

    # Enriquecimento via static_data_manager se nome do personagem for fornecido
    if char_profile is None and char_name:
        try:
            from static_data_manager import static_data_manager

            char_profile = static_data_manager.get_character_profile(game_id, char_name)
        except (ImportError, KeyError, TypeError, AttributeError) as exc:
            logger.debug("[CALC] Perfil estático indisponível para %s (%s): %s", char_name, game_id, exc)

    if char_profile:
        if char_profile.get("boss_mat"):
            boss_item_name = char_profile["boss_mat"]
        elif char_profile.get("stagnant_shadow_mat"):
            boss_item_name = char_profile["stagnant_shadow_mat"]
        elif char_profile.get("core_skill_mat"):
            boss_item_name = char_profile["core_skill_mat"]

        local_specialty = char_profile.get("local_specialty")
        talent_material = (
            char_profile.get("talent_book") or char_profile.get("calyx_mat") or char_profile.get("chip_type")
        )
        weekly_boss_mat = char_profile.get("weekly_boss_mat")
        domain_days = char_profile.get("domain_days")
        open_today = char_profile.get("open_today", True)

    daily_energy = 180 if game_id == "genshin" else 240
    energy_factor = 16 if game_id == "genshin" else (6 if game_id == "hsr" else 8)
    total_energy_needed = int(boss_diff * energy_factor)
    estimated_days = round(total_energy_needed / daily_energy, 1) if daily_energy > 0 else 0.0

    return {
        "xp_needed": xp_diff,
        "xp_books_purple": 0 if xp_diff <= 0 else (xp_books if xp_books > 0 else 1),
        "currency_needed": currency_diff,
        "currency_name": currency_name,
        "boss_items_needed": boss_diff,
        "boss_item_name": boss_item_name,
        "local_specialty": local_specialty,
        "talent_material": talent_material,
        "weekly_boss_material": weekly_boss_mat,
        "domain_days": domain_days,
        "open_today": open_today,
        "energy_needed": total_energy_needed,
        "daily_energy_limit": daily_energy,
        "estimated_farming_days": estimated_days,
    }


def optimize_character_relics(game_id: str, char_id: str, relics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analisa o inventário de relíquias fornecido e determina a combinação ótima (BiS do inventário)
    para o personagem especificado, selecionando a peça de maior pontuação para cada slot.
    """
    game_id = game_id.lower().strip()
    if not relics_list:
        return {
            "best_pieces": {},
            "overall_score": 0.0,
            "overall_grade": "D",
            "recommendations": ["Nenhuma relíquia encontrada no inventário."],
        }

    best_by_slot = {}
    for r in relics_list:
        slot = r.get("slot", "")
        norm_slot = normalize_slot_name(slot, game_id)
        if not norm_slot:
            continue

        main_stat = r.get("main_stat") or r.get("main") or ""
        sub_stats = r.get("sub_stats") or r.get("substats") or r.get("sub") or ""
        if isinstance(sub_stats, list):
            sub_stats_str = ", ".join(
                [f"{s.get('name', '')}: {s.get('val', '')}" if isinstance(s, dict) else str(s) for s in sub_stats]
            )
        else:
            sub_stats_str = str(sub_stats)

        grade, score = score_relic(game_id, char_id, norm_slot, main_stat, sub_stats_str)

        piece_entry = {
            "name": r.get("name", "Relíquia"),
            "slot": norm_slot,
            "raw_slot": slot,
            "main_stat": main_stat,
            "sub_stats": sub_stats_str,
            "grade": grade,
            "score": score,
            "icon": r.get("icon", ""),
            "character_equipped": r.get("character_name", ""),
        }

        if norm_slot not in best_by_slot or score > best_by_slot[norm_slot]["score"]:
            best_by_slot[norm_slot] = piece_entry

    if not best_by_slot:
        return {
            "best_pieces": {},
            "overall_score": 0.0,
            "overall_grade": "D",
            "recommendations": ["Nenhuma relíquia válida foi avaliada."],
        }

    max_slots = 5 if game_id == "genshin" else 6
    scores = [p["score"] for p in best_by_slot.values()]
    avg_score = round(sum(scores) / max_slots, 1) if scores else 0.0

    if avg_score >= 90:
        overall_grade = "SS"
    elif avg_score >= 80:
        overall_grade = "S+"
    elif avg_score >= 70:
        overall_grade = "S"
    elif avg_score >= 60:
        overall_grade = "A"
    elif avg_score >= 50:
        overall_grade = "B"
    elif avg_score >= 40:
        overall_grade = "C"
    else:
        overall_grade = "D"

    recommendations = []
    for slot, piece in best_by_slot.items():
        if piece["score"] < 60:
            recommendations.append(
                f"Slot {slot.upper()}: A melhor peça no inventário possui nota {piece['grade']} ({piece['score']}%). Recomendado buscar upgrades."
            )

    return {
        "character": char_id,
        "best_pieces": best_by_slot,
        "overall_score": avg_score,
        "overall_grade": overall_grade,
        "recommendations": recommendations
        if recommendations
        else ["Sua build ótima de inventário está muito bem estruturada!"],
    }


# ==========================================
# 1. SIMULADOR MONTE CARLO DE GACHA / WISH
# ==========================================




# ==========================================
# 2. CENTRAL DE FARM INTELIGENTE DIÁRIO
# ==========================================
FARM_CALENDAR = {
    "genshin": {
        0: {
            "days": "Segunda-feira",
            "talents": ["Liberdade", "Prosperidade", "Transitoriedade", "Ordem", "Contenda (Natlan)"],
            "weapons": ["Decara", "Guyun", "Coral", "Densa Nevoeiro", "Madeira Sagrada (Natlan)"],
        },
        1: {
            "days": "Terça-feira",
            "talents": ["Resistência", "Diligência", "Elegância", "Equidade", "Ignição (Natlan)"],
            "weapons": ["Dente de Leão", "Elixir", "Grama", "Gota Purificadora", "Chama Noturna (Natlan)"],
        },
        2: {
            "days": "Quarta-feira",
            "talents": ["Balada", "Ouro", "Luz", "Justiça", "Conflito (Natlan)"],
            "weapons": ["Gladiador", "Aerosiderite", "Máscara", "Cálice Rúnico", "Vontade Deliberada (Natlan)"],
        },
        3: {
            "days": "Quinta-feira",
            "talents": ["Liberdade", "Prosperidade", "Transitoriedade", "Ordem", "Contenda (Natlan)"],
            "weapons": ["Decara", "Guyun", "Coral", "Densa Nevoeiro", "Madeira Sagrada (Natlan)"],
        },
        4: {
            "days": "Sexta-feira",
            "talents": ["Resistência", "Diligência", "Elegância", "Equidade", "Ignição (Natlan)"],
            "weapons": ["Dente de Leão", "Elixir", "Grama", "Gota Purificadora", "Chama Noturna (Natlan)"],
        },
        5: {
            "days": "Sábado",
            "talents": ["Balada", "Ouro", "Luz", "Justiça", "Conflito (Natlan)"],
            "weapons": ["Gladiador", "Aerosiderite", "Máscara", "Cálice Rúnico", "Vontade Deliberada (Natlan)"],
        },
        6: {"days": "Domingo", "talents": ["Todos os materiais abertos"], "weapons": ["Todos os materiais abertos"]},
    },
    "hsr": {
        0: {"days": "Segunda-feira", "note": "Reset Semanal do Universo Simulado e Eco da Guerra (3x recompensas)."},
        1: {"days": "Terça-feira", "note": "Calyx de Traço & Ascensão com drop normal."},
        2: {"days": "Quarta-feira", "note": "Foco recomendado: Farm de Túnel de Relíquias."},
        3: {"days": "Quinta-feira", "note": "Calyx de Traço & Ascensão."},
        4: {"days": "Sexta-feira", "note": "Foco recomendado: Ornamentos Planares (Universo Divergente/Simulado)."},
        5: {"days": "Sábado", "note": "Farm livre de Relíquias e Materiais de Ascensão."},
        6: {"days": "Domingo", "note": "Preparação de Energia para o Reset de Segunda."},
    },
    "zzz": {
        0: {"days": "Segunda-feira", "note": "Reset Semanal do Notorious Hunt (3x Caça aos Chefes de Dano)."},
        1: {"days": "Terça-feira", "note": "Foco recomendado: HIA Club - Chips de Atributo de Especialidade."},
        2: {"days": "Quarta-feira", "note": "Foco recomendado: HIA Club - Certificados de Promoção."},
        3: {"days": "Quinta-feira", "note": "Foco recomendado: Drive Disc Tuning & Limpeza de Rótulo."},
        4: {"days": "Sexta-feira", "note": "HIA Club - Materiais de Agente."},
        5: {"days": "Sábado", "note": "Farm livre de Discos e Materiais na Cavidade Zero."},
        6: {"days": "Domingo", "note": "Preparação de Bateria para o Reset Semanal."},
    },
}

GAME_MAX_LEVELS = {"genshin": 90, "hsr": 80, "zzz": 60}


def is_genshin_farmable_today(
    char_name: str, day_of_week: int, farmable_chars: Optional[List[str]] = None
) -> bool:
    if day_of_week == 6:  # Domingo tudo aberto
        return True
    if farmable_chars is None:
        try:
            from static_data_manager import static_data_manager

            sched = static_data_manager.get_daily_farm_schedule("genshin", day_of_week)
            farmable_chars = [c.lower() for c in sched.get("farmable_characters", [])]
        except (ImportError, KeyError, TypeError, AttributeError) as exc:
            logger.debug("[CALC] Agenda diária dinâmica indisponível para %s: %s", char_name, exc)
            farmable_chars = []

    c_clean = char_name.lower().strip()
    if any(c_clean == fc or fc in c_clean or c_clean in fc for fc in farmable_chars):
        return True

    mon_thu = {
        "amber",
        "barbara",
        "klee",
        "diona",
        "aloy",
        "sucrose",
        "keqing",
        "ningguang",
        "qiqi",
        "xiao",
        "yelan",
        "shenhe",
        "thoma",
        "yoimiya",
        "heizou",
        "kokomi",
        "tighnari",
        "candace",
        "cyno",
        "faruzan",
        "lyney",
        "neuvillette",
        "navia",
        "xianyun",
        "mualani",
        "kachina",
        "kinich",
        "xilonen",
        "mavuika",
        "citlali",
        "ororon",
    }
    tue_fri = {
        "bennett",
        "diluc",
        "jean",
        "noelle",
        "mona",
        "eula",
        "ganyu",
        "hu tao",
        "hu_tao",
        "xiangling",
        "chongyun",
        "yun jin",
        "yun_jin",
        "yaoyao",
        "ayaka",
        "ayato",
        "sara",
        "araki",
        "itto",
        "nahida",
        "alhaitham",
        "dori",
        "layla",
        "kaveh",
        "freminet",
        "charlotte",
        "clorinde",
        "furina",
        "chasca",
        "ifa",
    }
    wed_sat = {
        "fischl",
        "kaeya",
        "lisa",
        "venti",
        "rosaria",
        "albedo",
        "beidou",
        "xingqiu",
        "zhongli",
        "yanfei",
        "baizhu",
        "raiden",
        "raiden shogun",
        "yae miko",
        "sayu",
        "gorou",
        "collei",
        "nilou",
        "wanderer",
        "dehya",
        "wriothesley",
        "chevreuse",
        "arlecchino",
        "emilie",
        "lan yan",
    }

    c_clean = char_name.lower().strip()
    if day_of_week in (0, 3):
        return any(k in c_clean for k in mon_thu)
    elif day_of_week in (1, 4):
        return any(k in c_clean for k in tue_fri)
    elif day_of_week in (2, 5):
        return any(k in c_clean for k in wed_sat)
    return True


ITEM_ICONS = {
    "genshin": {
        "mora": "https://enka.network/ui/UI_ItemIcon_202.png",
        "xp": "https://enka.network/ui/UI_ItemIcon_104003.png",
        "talent_book": "https://enka.network/ui/UI_ItemIcon_104303.png",
        "boss": "https://enka.network/ui/UI_ItemIcon_113001.png",
        "weekly_boss": "https://enka.network/ui/UI_ItemIcon_113021.png",
        "crown": "https://enka.network/ui/UI_ItemIcon_104319.png",
        "weapon_ore": "https://enka.network/ui/UI_ItemIcon_104013.png",
        "weapon_mat": "https://enka.network/ui/UI_ItemIcon_114004.png",
    },
    "hsr": {
        "mora": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/2.png",
        "xp": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/22.png",
        "talent_book": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110.png",
        "boss": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/201.png",
        "weekly_boss": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/3.png",
        "crown": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/11.png",
        "weapon_ore": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/102.png",
        "weapon_mat": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110.png",
    },
    "zzz": {
        "mora": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4fde02b5f3a4c790dcbef6c74cb4fabf.png",
        "xp": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/55c259888e808554c02a3161944d7868.png",
        "talent_book": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png",
        "boss": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
        "weekly_boss": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/2196659ee41fc22d1533519c53644f37.png",
        "crown": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/faeebca44b20e03ee23b610c4f8ea03d.png",
        "weapon_ore": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4f1444b51f52e8e0ad4a8dc13432b04f.png",
        "weapon_mat": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png",
    },
}

GAME_SPECIFIC_TERMS = {
    "genshin": {
        "currency_name": "Mora",
        "xp_book_name": "EXP do Herói",
        "talent_category": "Talentos",
        "green_book": "Ensinamentos (2★)",
        "blue_book": "Guia (3★)",
        "purple_book": "Filosofias (4★)",
        "enemy_t1": "Drop Inimigo Comum (1★)",
        "enemy_t2": "Drop Inimigo Incomum (2★)",
        "enemy_t3": "Drop Inimigo Raro (3★)",
        "boss_mat": "Material de Chefe de Campo",
        "weekly_boss_mat": "Material de Chefe Semanal",
        "crown_mat": "Coroa da Sabedoria",
        "ore_name": "Minério de Amplificação Místico",
        "w_mat_green": "Material de Domínio de Arma (2★)",
        "w_mat_blue": "Material de Domínio de Arma (3★)",
        "w_mat_purple": "Material de Domínio de Arma (4★)",
        "w_mat_gold": "Material de Domínio de Arma (5★)",
    },
    "hsr": {
        "currency_name": "Créditos",
        "xp_book_name": "Guia do Mochileiro",
        "talent_category": "Rastros",
        "green_book": "Esboço / Mat. de Traço (2★)",
        "blue_book": "Dinâmica / Mat. de Traço (3★)",
        "purple_book": "Conhecimento / Mat. de Traço (4★)",
        "enemy_t1": "Componente de Inimigo (1★)",
        "enemy_t2": "Núcleo de Inimigo (2★)",
        "enemy_t3": "Essência de Inimigo (3★)",
        "boss_mat": "Material de Sombra Estagnada",
        "weekly_boss_mat": "Material do Eco da Guerra",
        "crown_mat": "Rastro do Destino",
        "ore_name": "Éter Refinado",
        "w_mat_green": "Componente de Cone de Luz (2★)",
        "w_mat_blue": "Módulo de Cone de Luz (3★)",
        "w_mat_purple": "Núcleo de Cone de Luz (4★)",
        "w_mat_gold": "Matriz de Cone de Luz (5★)",
    },
    "zzz": {
        "currency_name": "Dennys",
        "xp_book_name": "Registro Oficial de Investigador",
        "talent_category": "Habilidades",
        "green_book": "Chip Básico de Habilidade (2★)",
        "blue_book": "Chip Avançado de Habilidade (3★)",
        "purple_book": "Chip Especializado de Habilidade (4★)",
        "enemy_t1": "Sinalizador Básico (1★)",
        "enemy_t2": "Sinalizador Avançado (2★)",
        "enemy_t3": "Sinalizador Especializado (3★)",
        "boss_mat": "Dado de Alta Dimensão",
        "weekly_boss_mat": "Material de Caça Notória",
        "crown_mat": "Passaporte da Gaiola de Hamster",
        "ore_name": "Fonte de Alimentação de W-Engine",
        "w_mat_green": "Componente Básico de W-Engine (2★)",
        "w_mat_blue": "Componente Avançado de W-Engine (3★)",
        "w_mat_purple": "Componente Especializado (4★)",
        "w_mat_gold": "Componente Mestre (5★)",
    },
}


def get_daily_farm_recommendations(
    game_id: str, roster: list = None, day_of_week: int = None, selected_chars: list = None, lang: str = "pt"
) -> dict:
    """
    Retorna o calendário de farm do dia atual e gera sugestões personalizadas de gasto de energia
    com base nos personagens selecionados da conta que possuem RV < S ou níveis pendentes.
    Inclui detalhamento completo de itens faltantes para Personagem, Talentos e Armas + Prioridades do Prydwen.
    """
    game_id = (game_id or "genshin").lower().strip()
    max_level = GAME_MAX_LEVELS.get(game_id, 90)
    max_talent_lvl = 10 if game_id in ["genshin", "hsr"] else 12
    max_weapon_lvl = 90 if game_id == "genshin" else (80 if game_id == "hsr" else 60)
    icons = ITEM_ICONS.get(game_id, ITEM_ICONS["genshin"])
    terms = GAME_SPECIFIC_TERMS.get(game_id, GAME_SPECIFIC_TERMS["genshin"])

    if day_of_week is None:
        day_of_week = datetime.now().weekday()  # 0=Segunda, 6=Domingo

    raw_cal = FARM_CALENDAR.get(game_id, {}).get(day_of_week, {"days": "Hoje", "note": "Farm Livre"})
    game_calendar = dict(raw_cal)
    if lang == "en":
        day_en_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
        game_calendar["days"] = day_en_map.get(day_of_week, "Today")
        if game_calendar.get("talents") and "Todos os materiais abertos" in game_calendar["talents"]:
            game_calendar["talents"] = ["All materials open"]
        if game_calendar.get("weapons") and "Todos os materiais abertos" in game_calendar["weapons"]:
            game_calendar["weapons"] = ["All materials open"]

    meta_db = get_meta_data(game_id)

    recommendations = []
    all_roster_names = []

    farmable_chars_today: Optional[List[str]] = None
    if game_id == "genshin" and day_of_week != 6:
        try:
            from static_data_manager import static_data_manager

            sched = static_data_manager.get_daily_farm_schedule("genshin", day_of_week)
            farmable_chars_today = [c.lower() for c in sched.get("farmable_characters", [])]
        except (ImportError, KeyError, TypeError, AttributeError) as exc:
            logger.debug("[CALC] Agenda diária dinâmica indisponível: %s", exc)
            farmable_chars_today = []

    if roster:
        all_roster_names = [char.get("name") for char in roster if char.get("name")]

        filtered_roster = roster
        if selected_chars and isinstance(selected_chars, list) and len(selected_chars) > 0:
            selected_set = set(selected_chars)
            filtered_roster = [c for c in roster if c.get("name") in selected_set]

        for char in filtered_roster:
            name = char.get("name", "Desconhecido")
            char_id = str(char.get("id", ""))
            grade = char.get("overall_grade", char.get("build_grade", "N/A"))
            raw_rv = char.get("overall_score", char.get("build_score", 0.0))
            try:
                rv = float(raw_rv) if raw_rv is not None else 0.0
            except (ValueError, TypeError):
                rv = 0.0
            level = char.get("level", 1)
            element = char.get("element", "")
            icon = char.get("icon", "")
            weapon = char.get("weapon", {})
            skills = char.get("skills", [])
            if not skills and char.get("raw_md"):
                try:
                    from database import parse_skills_from_raw_md

                    skills = parse_skills_from_raw_md(char["raw_md"])
                except (ImportError, ValueError, TypeError, AttributeError) as exc:
                    logger.debug("[CALC] Falha ao extrair skills do markdown de %s: %s", name, exc)

            # Se a lista de skills vier vazia do backend, injeta habilidades padrões oficiais do jogo
            if not skills:
                if game_id == "genshin":
                    skills = [
                        {"name": "Ataque Normal", "level": 6, "max_level": 10},
                        {"name": "Habilidade Elemental", "level": 8, "max_level": 10},
                        {"name": "Suprema (Elemental Burst)", "level": 8, "max_level": 10},
                    ]
                elif game_id == "hsr":
                    skills = [
                        {"name": "Ataque Básico", "level": 5, "max_level": 10},
                        {"name": "Perícia Elemental", "level": 8, "max_level": 10},
                        {"name": "Suprema", "level": 8, "max_level": 10},
                        {"name": "Talento Passivo", "level": 8, "max_level": 10},
                    ]
                else:
                    skills = [
                        {"name": "Ataque Básico", "level": 6, "max_level": 12},
                        {"name": "Esquiva", "level": 6, "max_level": 12},
                        {"name": "Ataque Especial", "level": 9, "max_level": 12},
                        {"name": "Ataque de Cadeia / Suprema", "level": 9, "max_level": 12},
                        {"name": "Ataque de Suporte", "level": 6, "max_level": 12},
                    ]

            # Busca prioridade Prydwen
            char_meta = meta_db.get(char_id, {})
            if not char_meta and isinstance(meta_db, dict):
                for k, v in meta_db.items():
                    if isinstance(v, dict) and v.get("name", "").lower() == name.lower():
                        char_meta = v
                        break
            talent_priority = char_meta.get("talent_priority", "") if isinstance(char_meta, dict) else ""

            talent_domain_open = True
            if game_id == "genshin":
                talent_domain_open = is_genshin_farmable_today(name, day_of_week, farmable_chars=farmable_chars_today)

            w_lvl = weapon.get("level", 1) if isinstance(weapon, dict) and weapon else max_weapon_lvl
            w_name = weapon.get("name", "Arma Equipada") if isinstance(weapon, dict) and weapon else "Arma Equipada"
            w_icon = weapon.get("icon", "") if isinstance(weapon, dict) and weapon else ""

            # Verifica se possui algum item/nível pendente
            has_pending_talents = False
            if skills:
                for sk_idx, sk in enumerate(skills):
                    s_l = sk.get("level", 1)
                    s_m = sk.get("max_level")
                    if not s_m:
                        if game_id == "hsr":
                            s_m = 1 if sk_idx >= 4 else (6 if sk_idx == 0 else 10)
                        elif game_id == "genshin":
                            s_m = 1 if sk_idx >= 3 else 10
                        else:
                            s_m = 6 if sk_idx == 5 else 12
                    if s_l < s_m:
                        has_pending_talents = True
                        break
            else:
                has_pending_talents = True

            has_pending_weapon = w_lvl < max_weapon_lvl

            if grade in ["B", "C", "D", "A"] or level < max_level or has_pending_talents or has_pending_weapon:
                reason_parts = []
                if level < max_level:
                    reason_parts.append(f"Personagem Nv. {level}/{max_level}")
                if has_pending_weapon:
                    reason_parts.append(f"Arma Nv. {w_lvl}/{max_weapon_lvl}")
                if has_pending_talents:
                    reason_parts.append(f"{terms['talent_category']} A Evoluir")
                if grade in ["B", "C", "D", "A"]:
                    reason_parts.append(f"Build nota {grade} (RV: {(rv or 0.0):.1f}%)")

                reason = " | ".join(reason_parts)

                # Resolução do perfil detalhado do personagem e materiais de farm
                char_profile = None
                try:
                    from static_data_manager import static_data_manager

                    char_profile = static_data_manager.get_character_profile(game_id, name)
                    if not char_profile:
                        char_profile = static_data_manager._enrich_character_profile(game_id, dict(char))
                except (ImportError, KeyError, TypeError, AttributeError) as exc:
                    logger.debug("[CALC] Perfil estático indisponível em farm (%s): %s", name, exc)

                items_needed = {"icons": icons, "terms": terms}

                # 1. Ascensão de Personagem
                if level < max_level:
                    asc_calc = calculate_ascension(
                        game_id,
                        level,
                        max_level,
                        char_name=name,
                        char_profile=char_profile if char_profile is not None else {},
                    )
                    if asc_calc:
                        asc_calc["currency_name"] = terms["currency_name"]
                        asc_calc["xp_book_name"] = terms["xp_book_name"]
                        if char_profile:
                            if char_profile.get("boss_mat_name"):
                                asc_calc["boss_item_name"] = char_profile["boss_mat_name"]
                            if char_profile.get("boss_mat_icon"):
                                asc_calc["boss_item_icon"] = char_profile["boss_mat_icon"]
                            if char_profile.get("local_specialty_name"):
                                asc_calc["local_specialty"] = char_profile["local_specialty_name"]
                            if char_profile.get("local_specialty_icon"):
                                asc_calc["specialty_icon"] = char_profile["local_specialty_icon"]
                    items_needed["ascension"] = asc_calc
                else:
                    items_needed["ascension"] = None

                # 2. Detalhamento por Talento / Habilidade
                talent_details = []

                # Nomes e ícones específicos para talentos
                t2_name = (char_profile.get("talent_tier2_name") if char_profile else None) or terms["green_book"]
                t2_icon = (char_profile.get("talent_tier2_icon") if char_profile else None) or icons["talent_book"]
                t3_name = (char_profile.get("talent_tier3_name") if char_profile else None) or terms["blue_book"]
                t3_icon = (char_profile.get("talent_tier3_icon") if char_profile else None) or icons["talent_book"]
                t4_name = (char_profile.get("talent_tier4_name") if char_profile else None) or terms["purple_book"]
                t4_icon = (char_profile.get("talent_tier4_icon") if char_profile else None) or icons["talent_book"]
                e1_name = (char_profile.get("enemy_tier1_name") if char_profile else None) or terms["enemy_t1"]
                e1_icon = (char_profile.get("enemy_tier1_icon") if char_profile else None) or icons["boss"]
                e2_name = (char_profile.get("enemy_tier2_name") if char_profile else None) or terms["enemy_t2"]
                e2_icon = (char_profile.get("enemy_tier2_icon") if char_profile else None) or icons["boss"]
                e3_name = (char_profile.get("enemy_tier3_name") if char_profile else None) or terms["enemy_t3"]
                e3_icon = (char_profile.get("enemy_tier3_icon") if char_profile else None) or icons["boss"]
                wb_name = (char_profile.get("weekly_boss_mat_name") if char_profile else None) or terms[
                    "weekly_boss_mat"
                ]
                wb_icon = (char_profile.get("weekly_boss_mat_icon") if char_profile else None) or icons["weekly_boss"]

                for sk_idx, sk in enumerate(skills):
                    s_n = sk.get("name", "Habilidade")
                    s_l = sk.get("level", 1)
                    if game_id == "hsr":
                        s_m = 1 if sk_idx >= 4 else (sk.get("max_level") or (6 if sk_idx == 0 else 10))
                    elif game_id == "genshin":
                        s_m = 1 if sk_idx >= 3 else (sk.get("max_level") or 10)
                    else:
                        s_m = 1 if sk_idx >= 5 else (sk.get("max_level") or 12)
                    s_icon = sk.get("icon", sk.get("image", sk.get("icon_url", "")))

                    if s_m == 1:
                        if s_l >= 1:
                            continue
                        else:
                            talent_details.append(
                                {
                                    "skill_name": s_n,
                                    "skill_icon": s_icon,
                                    "current_level": 0,
                                    "target_level": 1,
                                    "green_books": 1,
                                    "green_book_name": t2_name,
                                    "green_book_icon": t2_icon,
                                    "blue_books": 0,
                                    "blue_book_name": t3_name,
                                    "blue_book_icon": t3_icon,
                                    "purple_books": 0,
                                    "purple_book_name": t4_name,
                                    "purple_book_icon": t4_icon,
                                    "enemy_tier1": 2,
                                    "enemy_t1_name": e1_name,
                                    "enemy_t1_icon": e1_icon,
                                    "enemy_tier2": 0,
                                    "enemy_t2_name": e2_name,
                                    "enemy_t2_icon": e2_icon,
                                    "enemy_tier3": 0,
                                    "enemy_t3_name": e3_name,
                                    "enemy_t3_icon": e3_icon,
                                    "weekly_boss_mats": 0,
                                    "weekly_boss_mat_name": wb_name,
                                    "weekly_boss_mat_icon": wb_icon,
                                    "crowns_needed": 0,
                                    "crown_mat_name": terms["crown_mat"],
                                    "crown_icon": icons["crown"],
                                    "currency_needed": 5000,
                                }
                            )
                    elif s_l < s_m:
                        is_normal = (sk_idx == 0) or any(w in s_n.lower() for w in ["normal", "básico", "basico"])
                        if is_normal and s_l == 1 and talent_priority:
                            tp_low = talent_priority.lower()
                            if not any(w in tp_low for w in ["normal", "basic", "básico", "basico"]):
                                continue

                        lvl_diff = s_m - s_l
                        green_books = max(0, min(3, 6 - s_l)) if s_l < 3 else 0
                        blue_books = max(0, min(21, (6 - s_l) * 4)) if s_l < 6 else 0
                        purple_books = max(0, (s_m - max(6, s_l)) * 6)
                        enemy_tier1 = max(0, min(6, (6 - s_l) * 1)) if s_l < 3 else 0
                        enemy_tier2 = max(0, min(18, (6 - s_l) * 3)) if s_l < 6 else 0
                        enemy_tier3 = max(0, (s_m - max(6, s_l)) * 3)
                        weekly_boss_mats = max(0, (s_m - max(6, s_l)) * 2)
                        crowns_needed = 1 if s_m in [10, 12] and s_l < s_m else 0
                        currency_needed = lvl_diff * 150000

                        talent_details.append(
                            {
                                "skill_name": s_n,
                                "skill_icon": s_icon,
                                "current_level": s_l,
                                "target_level": s_m,
                                "green_books": green_books,
                                "green_book_name": t2_name,
                                "green_book_icon": t2_icon,
                                "blue_books": blue_books,
                                "blue_book_name": t3_name,
                                "blue_book_icon": t3_icon,
                                "purple_books": purple_books,
                                "purple_book_name": t4_name,
                                "purple_book_icon": t4_icon,
                                "enemy_tier1": enemy_tier1,
                                "enemy_t1_name": e1_name,
                                "enemy_t1_icon": e1_icon,
                                "enemy_tier2": enemy_tier2,
                                "enemy_t2_name": e2_name,
                                "enemy_t2_icon": e2_icon,
                                "enemy_tier3": enemy_tier3,
                                "enemy_t3_name": e3_name,
                                "enemy_t3_icon": e3_icon,
                                "weekly_boss_mats": weekly_boss_mats,
                                "weekly_boss_mat_name": wb_name,
                                "weekly_boss_mat_icon": wb_icon,
                                "crowns_needed": crowns_needed,
                                "crown_mat_name": terms["crown_mat"],
                                "crown_icon": icons["crown"],
                                "currency_needed": currency_needed,
                            }
                        )

                items_needed["talent_upgrade_details"] = talent_details

                # 3. Detalhamento de Arma / W-Engine Equipado
                weapon_details = None
                if has_pending_weapon or weapon:
                    w_lvl_diff = max(0, max_weapon_lvl - w_lvl)
                    ores_needed = int(w_lvl_diff * 3.5)
                    w_currency_needed = w_lvl_diff * 10000

                    w_mat_green = 3 if w_lvl < 40 else 0
                    w_mat_blue = 9 if w_lvl < 60 else 0
                    w_mat_purple = 9 if w_lvl < 80 else 0
                    w_mat_gold = 4 if w_lvl < 90 else 0

                    w_enemy_t1 = 15 if w_lvl < 40 else 0
                    w_enemy_t2 = 18 if w_lvl < 60 else 0
                    w_enemy_t3 = 27 if w_lvl < 90 else 0

                    w_prof = {}
                    try:
                        from static_data_manager import static_data_manager

                        w_prof = static_data_manager.get_weapon_profile(game_id, w_name)
                    except (ImportError, KeyError, TypeError, AttributeError) as exc:
                        logger.debug("[CALC] Perfil de arma indisponível (%s): %s", w_name, exc)

                    weapon_details = {
                        "weapon_name": w_name,
                        "weapon_icon": w_icon,
                        "current_level": w_lvl,
                        "target_level": max_weapon_lvl,
                        "ores_needed": ores_needed,
                        "ore_name": terms["ore_name"],
                        "ore_icon": icons["weapon_ore"],
                        "currency_needed": w_currency_needed,
                        "currency_name": terms["currency_name"],
                        "currency_icon": icons["mora"],
                        "w_mat_green": w_mat_green,
                        "w_mat_green_name": w_prof.get("w_mat_tier2_name", terms["w_mat_green"]),
                        "w_mat_green_icon": w_prof.get("w_mat_tier2_icon", icons["weapon_mat"]),
                        "w_mat_blue": w_mat_blue,
                        "w_mat_blue_name": w_prof.get("w_mat_tier3_name", terms["w_mat_blue"]),
                        "w_mat_blue_icon": w_prof.get("w_mat_tier3_icon", icons["weapon_mat"]),
                        "w_mat_purple": w_mat_purple,
                        "w_mat_purple_name": w_prof.get("w_mat_tier4_name", terms["w_mat_purple"]),
                        "w_mat_purple_icon": w_prof.get("w_mat_tier4_icon", icons["weapon_mat"]),
                        "w_mat_gold": w_mat_gold,
                        "w_mat_gold_name": w_prof.get("w_mat_tier5_name", terms["w_mat_gold"]),
                        "w_mat_gold_icon": w_prof.get("w_mat_tier5_icon", icons["weapon_mat"]),
                        "w_enemy_t1": w_enemy_t1,
                        "w_enemy_t1_name": w_prof.get("enemy_tier1_name", terms["enemy_t1"]),
                        "w_enemy_t1_icon": w_prof.get("enemy_tier1_icon", icons["boss"]),
                        "w_enemy_t2": w_enemy_t2,
                        "w_enemy_t2_name": w_prof.get("enemy_tier2_name", terms["enemy_t2"]),
                        "w_enemy_t2_icon": w_prof.get("enemy_tier2_icon", icons["boss"]),
                        "w_enemy_t3": w_enemy_t3,
                        "w_enemy_t3_name": w_prof.get("enemy_tier3_name", terms["enemy_t3"]),
                        "w_enemy_t3_icon": w_prof.get("enemy_tier3_icon", icons["boss"]),
                    }
                items_needed["weapon_upgrade_details"] = weapon_details

                # 4. Relíquias / Discos
                relic_info = f"Farm de Relíquias/Artefatos/Discos (Otimizar Nota {grade})"
                items_needed["relics"] = relic_info

                # Se o personagem precisa de ascensão de nível, materiais de chefe, especialidades ou drops de monstros,
                # todos esses itens de mundo aberto estão abertos 24/7 (hoje!).
                # Se faltam apenas talentos, o farm depende do domínio de talentos estar aberto hoje.
                if game_id == "genshin":
                    if level < max_level or has_pending_weapon:
                        farmable_today = True
                    else:
                        farmable_today = talent_domain_open
                else:
                    farmable_today = True

                recommendations.append(
                    {
                        "name": name,
                        "level": level,
                        "max_level": max_level,
                        "grade": grade,
                        "score": rv,
                        "element": element,
                        "icon": icon,
                        "weapon_info": weapon,
                        "skills_info": skills,
                        "talent_priority": talent_priority,
                        "talent_domain_open": talent_domain_open,
                        "farmable_today": farmable_today,
                        "reason": reason,
                        "items_needed": items_needed,
                        "action": f"Evoluir Nível/{terms['talent_category']}/Arma de {name}",
                    }
                )

    summary_totals = {
        "currency": 0,
        "xp_books": 0,
        "green_books": 0,
        "blue_books": 0,
        "purple_books": 0,
        "boss_mats": 0,
        "weekly_boss_mats": 0,
        "crowns": 0,
        "ores": 0,
    }

    for rec in recommendations:
        in_dict = rec.get("items_needed", {})
        asc = in_dict.get("ascension")
        if asc and isinstance(asc, dict):
            summary_totals["currency"] += asc.get("currency_needed", asc.get("mora_needed", 0)) or 0
            summary_totals["xp_books"] += asc.get("xp_books_purple", asc.get("purple_books", 0)) or 0
            summary_totals["boss_mats"] += asc.get("boss_items_needed", asc.get("boss_mats_needed", 0)) or 0

        for td in in_dict.get("talent_upgrade_details", []):
            summary_totals["currency"] += td.get("currency_needed", 0)
            summary_totals["green_books"] += td.get("green_books", 0)
            summary_totals["blue_books"] += td.get("blue_books", 0)
            summary_totals["purple_books"] += td.get("purple_books", 0)
            summary_totals["weekly_boss_mats"] += td.get("weekly_boss_mats", 0)
            summary_totals["crowns"] += td.get("crowns_needed", 0)

        wd = in_dict.get("weapon_upgrade_details")
        if wd and isinstance(wd, dict):
            summary_totals["currency"] += wd.get("currency_needed", 0)
            summary_totals["ores"] += wd.get("ores_needed", 0)

    all_roster_characters = []
    if roster:
        for char in roster:
            c_name = char.get("name")
            if not c_name:
                continue
            c_lvl = char.get("level", 1)
            c_rarity = char.get("rarity", 5 if "5" in str(char.get("rarity", "")) else 4)
            c_elem = char.get("element", "")
            c_icon = char.get("icon", "")
            c_grade = char.get("overall_grade", char.get("build_grade", "N/A"))
            c_score = char.get("overall_score", char.get("build_score", 0.0))

            all_roster_characters.append(
                {
                    "name": c_name,
                    "level": c_lvl,
                    "rarity": c_rarity,
                    "element": c_elem,
                    "icon": c_icon,
                    "grade": c_grade,
                    "score": c_score,
                    "needs_ascension": c_lvl < max_level,
                    "needs_relics": c_grade in ["B", "C", "D", "A"],
                }
            )

    return {
        "game_id": game_id,
        "max_level": max_level,
        "day_of_week": day_of_week,
        "calendar_info": game_calendar,
        "all_roster_names": all_roster_names,
        "all_roster_characters": all_roster_characters,
        "priority_targets": recommendations,
        "summary_totals": summary_totals,
    }


def extract_relic_substats_data(raw_substats: Any) -> dict:
    """
    Analisa os substatus de uma relíquia, normalizando nomes e extraindo valores numéricos de Crítico e Velocidade.
    Retorna dicionário contendo métricas calculadas de Crit Value (CV = 2*CR + CD).
    """
    formatted_subs = []
    normalized_subs = []
    crit_rate_val = None
    crit_dmg_val = None
    speed_val = None

    if isinstance(raw_substats, str):
        items = [part.strip() for part in raw_substats.split(",") if part.strip()]
    elif isinstance(raw_substats, list):
        items = raw_substats
    else:
        items = []

    for s in items:
        if isinstance(s, dict):
            s_name = str(s.get("name", "")).strip()
            s_val = s.get("val")
            sub_str = f"{s_name}: {s_val}" if (s_val is not None and ":" not in s_name) else s_name
        else:
            sub_str = str(s)
        sub_str = sub_str.strip()
        if not sub_str:
            continue
        formatted_subs.append(sub_str)
        norm_name = normalize_stat_name(sub_str)
        normalized_subs.append(norm_name)

        val_match = RE_SUB_NUM.search(sub_str)
        num_val = float(val_match.group(1)) if val_match else None

        if norm_name == "crit_rate" and num_val is not None:
            crit_rate_val = num_val
        elif norm_name == "crit_dmg" and num_val is not None:
            crit_dmg_val = num_val
        elif norm_name == "spd" and num_val is not None:
            speed_val = num_val

    has_double_crit = (crit_rate_val is not None and crit_dmg_val is not None) or (
        "crit_rate" in normalized_subs and "crit_dmg" in normalized_subs
    )

    cv = None
    if crit_rate_val is not None or crit_dmg_val is not None:
        cr = crit_rate_val or 0.0
        cd = crit_dmg_val or 0.0
        cv = round((cr * 2.0) + cd, 1)

    return {
        "formatted_subs": formatted_subs,
        "normalized_subs": normalized_subs,
        "crit_rate_val": crit_rate_val,
        "crit_dmg_val": crit_dmg_val,
        "speed_val": speed_val,
        "cv": cv,
        "has_double_crit": has_double_crit,
    }


# ==========================================
# 3. ANALISADOR DE RELÍQUIAS LIXO & PEÇAS CORINGA (OFF-PIECE FINDER)
# ==========================================
def find_trash_relics(game_id: str, relics: list, meta_data: dict) -> dict:
    """
    Analisa a lista de relíquias do jogador contra todos os guias de meta.
    Identifica com segurança peças lixo e PROTEGE peças 'Coringa / Off-Piece' com alto valor universal.
    """
    game_id = (game_id or "genshin").lower().strip()
    trash_candidates = []
    coringa_candidates = []
    good_relics_count = 0

    # Coletar todas as combinações de Main Stat + Substats prioritários de TODOS os guias
    all_useful_mains = set()
    all_useful_subs = set()

    for char_key, guide in meta_data.items():
        if isinstance(guide, dict):
            mains = guide.get("main_stats", {})
            for slot, m_list in mains.items():
                if isinstance(m_list, list):
                    for m in m_list:
                        all_useful_mains.add(normalize_stat_name(m))
            subs = guide.get("substats_priority") or guide.get("substats", [])
            if isinstance(subs, list):
                for s in subs:
                    all_useful_subs.add(normalize_stat_name(s))

    # Advice estratégico por jogo
    if game_id == "genshin":
        game_advice = "Perfeita como 5ª peça Off-Piece da equipe sem quebrar o bônus de 4 peças do set."
    elif game_id == "hsr":
        game_advice = "Excelente para combinações 2pc + 2pc de Caverna ou Ornamentos Planares híbridos."
    else:
        game_advice = "Ideal para composições híbridas 4pc + 2pc em Discos de Acionamento."

    noble_main_stats = {
        "pyro_dmg",
        "hydro_dmg",
        "cryo_dmg",
        "electro_dmg",
        "anemo_dmg",
        "geo_dmg",
        "dendro_dmg",
        "physical_dmg",
        "quantum_dmg",
        "imaginary_dmg",
        "ether_dmg",
        "lightning_dmg",
        "ice_dmg",
        "wind_dmg",
        "fire_dmg",
        "electric_dmg",
        "crit_rate",
        "crit_dmg",
        "spd",
        "er",
        "err",
    }

    for relic in relics:
        name = relic.get("name", "Relíquia Desconhecida")
        slot = relic.get("slot", "")
        main_stat_raw = relic.get("main_stat", relic.get("main", ""))
        main_stat = normalize_stat_name(main_stat_raw)
        character_name = relic.get("character_name")
        icon = relic.get("icon")

        raw_subs = relic.get("sub") or relic.get("substats") or relic.get("sub_stats", [])
        sub_info = extract_relic_substats_data(raw_subs)
        normalized_subs = sub_info["normalized_subs"]
        formatted_subs = sub_info["formatted_subs"]
        cv = sub_info["cv"]
        has_double_crit = sub_info["has_double_crit"]
        has_crit = "crit_rate" in normalized_subs or "crit_dmg" in normalized_subs or (cv is not None and cv > 0)
        has_spd = "spd" in normalized_subs or (sub_info["speed_val"] is not None and sub_info["speed_val"] > 0)

        # ----------------------------------------------------
        # 1. VERIFICAÇÃO DE PEÇA CORINGA / OFF-PIECE (PROTEÇÃO)
        # ----------------------------------------------------
        is_coringa = False
        coringa_tier = ""
        coringa_reason = ""

        # Caso 1: Duplo Crítico (Taxa CRIT + Dano CRIT)
        if has_double_crit:
            is_coringa = True
            if cv is not None and cv >= 30.0:
                coringa_tier = "God-Tier Coringa (CV 30+)"
                coringa_reason = f"Duplo Crítico supremo com {cv:.1f} Crit Value! Raridade máxima. {game_advice}"
            elif cv is not None and cv >= 20.0:
                coringa_tier = "Excelente Peça Coringa (CV 20+)"
                coringa_reason = f"Duplo Crítico de alto impacto ({cv:.1f} CV). {game_advice}"
            else:
                cv_str = f" ({cv:.1f} CV)" if cv is not None else ""
                coringa_tier = "Peça Coringa com Duplo Crítico"
                coringa_reason = f"Contém Taxa CRIT e Dano CRIT simultâneos{cv_str}. {game_advice}"

        # Caso 2: Crit Value Concentrado Alto (CV >= 18.0)
        elif cv is not None and cv >= 18.0:
            is_coringa = True
            coringa_tier = "Peça de Alto Crítico Acumulado"
            coringa_reason = f"Múltiplos rolls no atributo crítico resultando em {cv:.1f} CV. {game_advice}"

        # Caso 3: Main Stat Nobre + Crítico ou Velocidade
        elif (main_stat in noble_main_stats or any(n in main_stat for n in ["dmg", "crit", "spd", "er"])) and (
            has_crit or has_spd
        ):
            is_coringa = True
            coringa_tier = "Peça Híbrida Nobre"
            stat_label = relic.get("main_stat", main_stat)
            coringa_reason = f"Atributo Principal nobre ({stat_label}) com substatus crítico/velocidade. {game_advice}"

        if is_coringa:
            coringa_candidates.append(
                {
                    "name": name,
                    "slot": slot,
                    "main_stat": main_stat_raw,
                    "substats": formatted_subs,
                    "crit_value": cv,
                    "coringa_tier": coringa_tier,
                    "reason": coringa_reason,
                    "character_name": character_name,
                    "icon": icon,
                }
            )
            good_relics_count += 1
            continue  # NUNCA VAI PARA LIXO! PROTEÇÃO ABSOLUTA.

        # ----------------------------------------------------
        # 2. VERIFICAÇÃO DE RELÍQUIAS LIXO
        # ----------------------------------------------------
        useful_subs_count = sum(1 for s in normalized_subs if s in all_useful_subs or "crit" in s or "spd" in s)
        is_def_flat_heavy = any("def_flat" in s or "hp_flat" in s for s in normalized_subs)
        is_noble_main = main_stat in noble_main_stats or any(n in main_stat for n in ["dmg", "crit", "spd", "er"])

        if not is_noble_main and (
            (useful_subs_count == 0 and is_def_flat_heavy)
            or (useful_subs_count <= 1 and main_stat in ["def_pct", "hp_pct"] and not has_crit and not has_spd)
        ):
            trash_candidates.append(
                {
                    "name": name,
                    "slot": slot,
                    "main_stat": main_stat_raw,
                    "substats": formatted_subs,
                    "reason": "Substatus sem acertos de Crítico/Recarga/VEL e atributos irrelevantes para o meta atual.",
                    "recommendation": "Converter em EXP ou Reciclar no Sintetizador",
                    "character_name": character_name,
                    "icon": icon,
                }
            )
        else:
            good_relics_count += 1

    # Ordena coringas: God-Tier e maiores CVs primeiro
    coringa_candidates.sort(key=lambda x: x.get("crit_value") or 0.0, reverse=True)

    return {
        "game_id": game_id,
        "total_analyzed": len(relics),
        "good_relics_count": good_relics_count,
        "trash_count": len(trash_candidates),
        "trash_relics": trash_candidates[:15],
        "coringa_count": len(coringa_candidates),
        "coringa_relics": coringa_candidates[:15],
    }


# ==========================================
# 4. CALCULADORA DE BREAKPOINTS DE STATUS
# ==========================================


# ==========================================
# 6. GERENCIADOR DE CÓDIGOS PROMOCIONAIS (DINÂMICO AO VIVO)
# ==========================================
PROMO_CODES_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 1800  # Cache de 30 minutos

FALLBACK_PROMO_CODES = {
    "hsr": [
        {"code": "STARRAILGIFT", "rewards": "50 Stellar Jade, 10,000 Credit", "status": "Ativo permanente"},
        {"code": "OMEGA", "rewards": "60 Stellar Jade, 1 Fuel", "status": "Ativo de versão"},
    ],
    "genshin": [
        {"code": "GENSHINGIFT", "rewards": "50 Primogem, 3 Hero's Wit", "status": "Ativo permanente"},
        {"code": "2BJ64QRZ7RT8", "rewards": "60 Primogem, 5 Adventurer's Experience", "status": "Ativo de versão"},
    ],
    "zzz": [
        {"code": "ZENLESSGIFT", "rewards": "50 Polychrome, 2 Official Investigator Log", "status": "Ativo permanente"},
        {"code": "ZZZMEIJI", "rewards": "30,000 Denny, 3 Senior Investigator Log", "status": "Ativo de evento"},
    ],
}


def fetch_live_promo_codes(game_id: str) -> List[Dict[str, Any]]:
    """Realiza raspagem em tempo real via MediaWiki API dos códigos de resgate ativos."""
    wiki_map = {
        "genshin": ("genshin-impact", "Promotional_Code"),
        "hsr": ("honkai-star-rail", "Redemption_Code"),
        "zzz": ("zenless-zone-zero", "Redemption_Code"),
    }
    g = game_id.lower().strip()
    if g not in wiki_map:
        return []

    wiki_name, page_name = wiki_map[g]
    url = f"https://{wiki_name}.fandom.com/api.php?action=parse&page={page_name}&format=json"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    try:
        r = requests.get(url, headers=headers, impersonate="chrome", timeout=6)
        if r.status_code != 200:
            return []

        html = r.json().get("parse", {}).get("text", {}).get("*", "")
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table", class_="wikitable")

        codes = []
        seen = set()

        for t in tables[:2]:
            for tr in t.find_all("tr"):
                cols = [td.text.strip().replace("\n", " ") for td in tr.find_all(["td", "th"])]
                if len(cols) >= 3:
                    raw_code_col = cols[0]
                    raw_rewards_col = cols[2] if len(cols) >= 3 else cols[1]
                    raw_duration_col = cols[3] if len(cols) >= 4 else ""

                    raw_code_clean = RE_PROMO_CODE_CLEAN.sub("", raw_code_col).strip()
                    code_match = RE_PROMO_CODE_TOKEN.search(raw_code_clean)
                    if not code_match:
                        continue

                    code = code_match.group(0).upper()

                    if code in ("CODE", "SERVER", "REWARDS", "DURATION", "EXPIRED") or code in seen:
                        continue

                    if "expired:" in raw_duration_col.lower():
                        continue

                    rewards = RE_WIKI_REF.sub("", raw_rewards_col).replace("×", "x").replace("Ã—", "x").strip()
                    rewards = " ".join(rewards.split())

                    status = "Ativo (Ao vivo)"
                    if "valid until:" in raw_duration_col.lower():
                        valid_match = RE_PROMO_VALID_UNTIL.search(raw_duration_col)
                        if valid_match:
                            val_str = valid_match.group(1).strip()
                            val_str = RE_PROMO_DATE.sub(r"\1", val_str)
                            status = f"Ativo até {val_str}"
                    elif "indefinite" in raw_duration_col.lower():
                        status = "Ativo Permanente"

                    seen.add(code)
                    codes.append(
                        {"code": code, "rewards": rewards if rewards else "Recompensas de Evento", "status": status}
                    )
        return codes
    except Exception as e:
        print(f"Erro ao buscar códigos promocionais ao vivo para {game_id}: {e}")
        return []


def fetch_active_promo_codes(game_id: str) -> List[Dict[str, Any]]:
    """Busca dinamicamente os códigos promocionais ativos para o jogo solicitado, com suporte a cache e fallback."""
    g = game_id.lower().strip()
    now = time.time()

    # Verifica cache em memória
    if g in PROMO_CODES_CACHE:
        entry = PROMO_CODES_CACHE[g]
        if (now - entry["timestamp"]) < CACHE_TTL_SECONDS and entry["codes"]:
            return entry["codes"]

    # Busca ao vivo via MediaWiki API
    live_codes = fetch_live_promo_codes(g)
    if live_codes:
        PROMO_CODES_CACHE[g] = {"timestamp": now, "codes": live_codes}
        return live_codes

    # Fallback caso a busca ao vivo falhe ou dê timeout
    return FALLBACK_PROMO_CODES.get(g, [])


# ==========================================
# 6. GERADOR DE ORDEM DE SERVIÇO DIÁRIA
# ==========================================
def generate_daily_farm_order(
    game_id: str,
    roster: Optional[List[Dict[str, Any]]] = None,
    meta_data: Optional[Dict[str, Any]] = None,
    current_energy: Optional[int] = None,
    max_energy: Optional[int] = None,
    weekday: Optional[int] = None,
    selected_chars: Optional[List[str]] = None,
    lang: str = "pt",
) -> Dict[str, Any]:
    """
    Gera a 'Ordem de Serviço do Dia' inteligente e otimizada.
    Cruza o saldo de energia atual, os domínios abertos hoje, os personagens do Roster
    e os materiais prioritários para alocar os pontos de resina/energia com máxima eficiência.
    """
    g = (game_id or "genshin").lower().strip()
    if g not in ["genshin", "hsr", "zzz"]:
        g = "genshin"

    now_dt = datetime.now()
    if weekday is None:
        weekday = now_dt.weekday()
    today_str = now_dt.strftime("%Y-%m-%d")

    if lang == "en":
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    else:
        weekday_names = [
            "Segunda-feira",
            "Terça-feira",
            "Quarta-feira",
            "Quinta-feira",
            "Sexta-feira",
            "Sábado",
            "Domingo",
        ]
    weekday_name = weekday_names[weekday]

    # Configurações de Energia e Custos por Jogo
    game_configs = {
        "genshin": {
            "energy_name": "Original Resin" if lang == "en" else "Resina Original",
            "energy_icon": "fa-droplet",
            "default_max": 200,
            "default_current": 160,
            "regen_minutes": 8,
            "talent_run_cost": 20,
            "talent_runs_default": 2,
            "boss_run_cost": 40,
            "weekly_boss_run_cost": 30,
            "relic_run_cost": 20,
            "relic_runs_default": 2,
            "currency_name": "Mora",
            "max_level": 90,
        },
        "hsr": {
            "energy_name": "Trailblaze Power" if lang == "en" else "Poder de Desbravamento",
            "energy_icon": "fa-bolt",
            "default_max": 300,
            "default_current": 240,
            "regen_minutes": 6,
            "talent_run_cost": 30,
            "talent_runs_default": 2,
            "boss_run_cost": 30,
            "weekly_boss_run_cost": 30,
            "relic_run_cost": 40,
            "relic_runs_default": 1,
            "currency_name": "Credits" if lang == "en" else "Créditos",
            "max_level": 80,
        },
        "zzz": {
            "energy_name": "Battery Charge" if lang == "en" else "Carga de Bateria",
            "energy_icon": "fa-battery-full",
            "default_max": 240,
            "default_current": 240,
            "regen_minutes": 6,
            "talent_run_cost": 40,
            "talent_runs_default": 1,
            "boss_run_cost": 40,
            "weekly_boss_run_cost": 60,
            "relic_run_cost": 60,
            "relic_runs_default": 1,
            "currency_name": "Dennys",
            "max_level": 60,
        },
    }

    cfg = game_configs[g]

    # Obtenção de Roster e Meta se não fornecidos
    if roster is None:
        try:
            import database

            roster = database.get_roster_data(g)
        except (ImportError, sqlite3.Error, TypeError) as exc:
            logger.debug("[CALC] Falha ao carregar roster SQLite (%s): %s", g, exc)
            roster = []

    if meta_data is None:
        try:
            meta_data = get_meta_data(g)
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            logger.warning("[CALC] Falha ao carregar meta_data (%s): %s", g, exc)
            meta_data = {}

    # Obtenção de Energia via Cache se não fornecida
    if current_energy is None or max_energy is None:
        try:
            import database

            cached_notes = database.get_cached_daily_notes()
            if g in cached_notes and cached_notes[g].get("current_energy") is not None:
                if current_energy is None:
                    current_energy = int(cached_notes[g]["current_energy"])
                if max_energy is None:
                    max_energy = int(cached_notes[g].get("max_energy", cfg["default_max"]))
        except (ImportError, sqlite3.Error, ValueError, TypeError) as exc:
            logger.debug("[CALC] Falha ao consultar notas diárias (%s): %s", g, exc)

    if current_energy is None:
        current_energy = cfg["default_current"]
    if max_energy is None:
        max_energy = cfg["default_max"]

    # Obtenção de tarefas já concluídas hoje no SQLite
    completed_task_ids = set()
    try:
        import database

        completed_task_ids = set(database.get_completed_farm_tasks(today_str, g))
    except (ImportError, sqlite3.Error, TypeError) as exc:
        logger.debug("[CALC] Falha ao consultar tarefas de farm concluídas (%s): %s", g, exc)

    # Consulta de recomendações de farm diárias
    recs_data = get_daily_farm_recommendations(
        game_id=g, roster=roster, day_of_week=weekday, selected_chars=selected_chars
    )
    targets = recs_data.get("priority_targets", [])
    cal_info = recs_data.get("calendar_info", {})

    from static_data_manager import static_data_manager

    profile_cache: Dict[str, Optional[Dict[str, Any]]] = {}

    def _get_cached_profile(char_name_key: Optional[str]) -> Optional[Dict[str, Any]]:
        if not char_name_key:
            return None
        if char_name_key not in profile_cache:
            profile_cache[char_name_key] = static_data_manager.get_character_profile(g, char_name_key)
        return profile_cache[char_name_key]

    # Construção da lista de tarefas priorizadas
    tasks = []
    task_idx = 1
    accumulated_energy = 0
    seen_task_signatures = set()

    # PRIORIDADE 1: Livros de Talentos ABERTOS HOJE para personagens prioritários
    for target in targets:
        c_name = target.get("name")
        c_grade = target.get("grade", "A")
        items_needed = target.get("items_needed", {})
        talents_list = items_needed.get("talent_upgrade_details", [])

        # Verifica se tem talentos pendentes
        if not talents_list:
            continue

        # Verifica dados estáticos de materiais de talento (Genshin, HSR e ZZZ)
        profile = _get_cached_profile(c_name)
        talent_mat_name = (
            (profile.get("talent_book") or profile.get("calyx_mat") or profile.get("chip_type") or "")
            if profile
            else ""
        )
        if not talent_mat_name and cal_info.get("talents"):
            talent_mat_name = cal_info["talents"][0]

        is_farmable_today = target.get("farmable_today", True)
        if g == "genshin" and not is_farmable_today:
            # Em Genshin, pula se o domínio NÃO estiver aberto hoje (a não ser que seja domingo)
            continue

        sig = f"talent_{c_name}_{talent_mat_name}"
        if sig in seen_task_signatures:
            continue
        seen_task_signatures.add(sig)

        runs = cfg["talent_runs_default"]
        cost = runs * cfg["talent_run_cost"]

        if lang == "en":
            location = "Talent Book Domain"
            if profile and profile.get("region"):
                location = f"{profile['region']} Region Domain"
            elif g == "hsr":
                location = f"Crimson Calyx ({profile.get('path', 'Path') if profile else 'Traces'})"
            elif g == "zzz":
                location = f"Skill Training ({profile.get('specialty', 'Agent') if profile else 'Attack'})"
            t_label = "Talent Books"
            p_badge = "⭐ Open Today"
            desc_text = f"Run {runs}x {location} to obtain {talent_mat_name} and advance priority talents for {c_name} (Grade {c_grade})."
        else:
            location = "Domínio de Livros de Talento"
            if profile and profile.get("region"):
                location = f"Domínio da Região de {profile['region']}"
            elif g == "hsr":
                location = f"Cálice Rubro ({profile.get('path', 'Caminho') if profile else 'Rastros'})"
            elif g == "zzz":
                location = f"Treinamento de Habilidades ({profile.get('specialty', 'Agente') if profile else 'Ataque'})"
            t_label = "Livros de Talento"
            p_badge = "⭐ Aberto Hoje"
            desc_text = f"Faça {runs}x {location} para obter {talent_mat_name} e avançar os talentos prioritários de {c_name} (Nota {c_grade})."

        task_item = {
            "id": sig,
            "step": task_idx,
            "type": "talent_domain",
            "type_label": t_label,
            "type_icon": "fa-book-open",
            "target_character": c_name,
            "character_icon": target.get("icon"),
            "character_grade": c_grade,
            "material_name": talent_mat_name or ("Elevation Books" if lang == "en" else "Livros de Elevação"),
            "location": location,
            "runs": runs,
            "cost_energy": cost,
            "energy_name": cfg["energy_name"],
            "priority_badge": p_badge,
            "badge_color": "#10b981",
            "description": desc_text,
            "completed": sig in completed_task_ids,
        }

        # Cálculo de tempo até disponibilidade de energia
        accumulated_energy += cost
        task_item["cumulative_energy"] = accumulated_energy
        if accumulated_energy <= current_energy:
            task_item["available_now"] = True
            task_item["status_text"] = "Ready to Execute" if lang == "en" else "Pronto para Executar"
            task_item["time_estimate"] = "Available Now" if lang == "en" else "Disponível Agora"
        else:
            deficit = accumulated_energy - current_energy
            wait_min = deficit * cfg["regen_minutes"]
            ready_dt = now_dt + timedelta(minutes=wait_min)
            task_item["available_now"] = False
            task_item["status_text"] = "Waiting for Energy" if lang == "en" else "Aguardando Energia"
            time_prefix = "Available at" if lang == "en" else "Disponível às"
            task_item["time_estimate"] = f"{time_prefix} {ready_dt.strftime('%H:%M')} (+{wait_min} min)"

        tasks.append(task_item)
        task_idx += 1
        if len(tasks) >= 3:
            break

    # PRIORIDADE 2: Materiais de Chefe de Ascensão (se personagem estiver abaixo do nível máximo)
    for target in targets:
        c_name = target.get("name")
        c_lvl = target.get("level", 1)
        c_max = target.get("max_level", cfg["max_level"])
        c_grade = target.get("grade", "A")

        if c_lvl >= c_max:
            continue

        profile = _get_cached_profile(c_name)
        boss_name = (
            (profile.get("boss_mat") or profile.get("stagnant_shadow_mat") or profile.get("core_skill_mat") or "")
            if profile
            else ""
        ) or "Chefe do Mundo"

        sig = f"boss_{c_name}_{boss_name}"
        if sig in seen_task_signatures:
            continue
        seen_task_signatures.add(sig)

        runs = 1
        cost = runs * cfg["boss_run_cost"]

        if lang == "en":
            location = f"Ascension Boss ({boss_name})"
            if profile and profile.get("region"):
                location = f"{profile['region']} Boss ({boss_name})"
            t_label = "Ascension Boss"
            p_badge = "🔥 Pending Ascension"
            desc_text = f"Defeat {location} to advance {c_name} from Lv. {c_lvl} towards Lv. {c_max}."
        else:
            location = f"Chefe de Ascensão ({boss_name})"
            if profile and profile.get("region"):
                location = f"Chefe de {profile['region']} ({boss_name})"
            t_label = "Chefe de Ascensão"
            p_badge = "🔥 Ascensão Pendente"
            desc_text = f"Derrote {location} para avançar {c_name} do Nv. {c_lvl} rumo ao Nv. {c_max}."

        task_item = {
            "id": sig,
            "step": task_idx,
            "type": "boss",
            "type_label": t_label,
            "type_icon": "fa-skull",
            "target_character": c_name,
            "character_icon": target.get("icon"),
            "character_grade": c_grade,
            "material_name": boss_name,
            "location": location,
            "runs": runs,
            "cost_energy": cost,
            "energy_name": cfg["energy_name"],
            "priority_badge": p_badge,
            "badge_color": "#f59e0b",
            "description": desc_text,
            "completed": sig in completed_task_ids,
        }

        accumulated_energy += cost
        task_item["cumulative_energy"] = accumulated_energy
        if accumulated_energy <= current_energy:
            task_item["available_now"] = True
            task_item["status_text"] = "Ready to Execute" if lang == "en" else "Pronto para Executar"
            task_item["time_estimate"] = "Available Now" if lang == "en" else "Disponível Agora"
        else:
            deficit = accumulated_energy - current_energy
            wait_min = deficit * cfg["regen_minutes"]
            ready_dt = now_dt + timedelta(minutes=wait_min)
            task_item["available_now"] = False
            task_item["status_text"] = "Waiting for Energy" if lang == "en" else "Aguardando Energia"
            time_prefix = "Available at" if lang == "en" else "Disponível às"
            task_item["time_estimate"] = f"{time_prefix} {ready_dt.strftime('%H:%M')} (+{wait_min} min)"

        tasks.append(task_item)
        task_idx += 1
        if len(tasks) >= 5:
            break

    # PRIORIDADE 3: Otimização de Relíquias / Artefatos / Discos (Min-Maxing)
    for target in targets:
        c_name = target.get("name")
        c_grade = target.get("grade", "A")

        sig = f"relic_{c_name}_meta"
        if sig in seen_task_signatures:
            continue
        seen_task_signatures.add(sig)

        runs = cfg["relic_runs_default"]
        cost = runs * cfg["relic_run_cost"]

        if lang == "en":
            domain_label = (
                "Artifact Domain" if g == "genshin" else ("Cavern of Corrosion" if g == "hsr" else "Routine Cleanup")
            )
            p_badge = "💎 Build Optimization"
            mat_name = f"Recommended Sets for {c_name}"
            loc_name = f"Recommended {domain_label}"
            desc_text = f"Run {runs}x {domain_label} seeking optimal main and sub-stats to maximize {c_name}'s rating."
        else:
            domain_label = (
                "Domínio de Artefatos"
                if g == "genshin"
                else ("Caverna da Corrosão" if g == "hsr" else "Limpeza de Rotina")
            )
            p_badge = "💎 Otimização de Build"
            mat_name = f"Sets Recomendados para {c_name}"
            loc_name = f"{domain_label} Recomendado"
            desc_text = (
                f"Realize {runs}x {domain_label} buscando peças com Atributos Ideais para maximizar a nota de {c_name}."
            )

        task_item = {
            "id": sig,
            "step": task_idx,
            "type": "relic_domain",
            "type_label": domain_label,
            "type_icon": "fa-gem",
            "target_character": c_name,
            "character_icon": target.get("icon"),
            "character_grade": c_grade,
            "material_name": mat_name,
            "location": loc_name,
            "runs": runs,
            "cost_energy": cost,
            "energy_name": cfg["energy_name"],
            "priority_badge": p_badge,
            "badge_color": "#ec4899",
            "description": desc_text,
            "completed": sig in completed_task_ids,
        }

        accumulated_energy += cost
        task_item["cumulative_energy"] = accumulated_energy
        if accumulated_energy <= current_energy:
            task_item["available_now"] = True
            task_item["status_text"] = "Ready to Execute" if lang == "en" else "Pronto para Executar"
            task_item["time_estimate"] = "Available Now" if lang == "en" else "Disponível Agora"
        else:
            deficit = accumulated_energy - current_energy
            wait_min = deficit * cfg["regen_minutes"]
            ready_dt = now_dt + timedelta(minutes=wait_min)
            task_item["available_now"] = False
            task_item["status_text"] = "Waiting for Energy" if lang == "en" else "Aguardando Energia"
            time_prefix = "Available at" if lang == "en" else "Disponível às"
            task_item["time_estimate"] = f"{time_prefix} {ready_dt.strftime('%H:%M')} (+{wait_min} min)"

        tasks.append(task_item)
        task_idx += 1
        if len(tasks) >= 6:
            break

    # Se a lista de tarefas estiver vazia (ex: conta recém-criada ou todos maximizados), cria uma tarefa de Linhas Ley/Cálice Dourado
    if not tasks:
        sig = f"calyx_currency_{g}"
        cost = cfg["talent_run_cost"] * 2
        tasks.append(
            {
                "id": sig,
                "step": 1,
                "type": "currency",
                "type_label": f"Reserva de {cfg['currency_name']}",
                "type_icon": "fa-coins",
                "target_character": "Conta Geral",
                "character_icon": None,
                "character_grade": "S",
                "material_name": cfg["currency_name"],
                "location": "Linhas Ley / Cálice Dourado",
                "runs": 2,
                "cost_energy": cost,
                "energy_name": cfg["energy_name"],
                "priority_badge": "🪙 Reserva Econômica",
                "badge_color": "#eab308",
                "description": f"Todos os seus personagens principais estão no nível máximo! Farme {cfg['currency_name']} para futuras versões.",
                "completed": sig in completed_task_ids,
                "cumulative_energy": cost,
                "available_now": True,
                "status_text": "Pronto para Executar",
                "time_estimate": "Disponível Agora",
            }
        )
        accumulated_energy = cost

    completed_count = sum(1 for t in tasks if t["completed"])
    completion_pct = int((completed_count / len(tasks)) * 100) if tasks else 0

    # Geração do texto formatado para cópia / webhook
    game_names = {"genshin": "Genshin Impact", "hsr": "Honkai: Star Rail", "zzz": "Zenless Zone Zero"}
    summary_lines = [
        f"📋 **ORDEM DE SERVIÇO DO DIA - {game_names.get(g, g.upper())}**",
        f"⚡ **Energia Atual:** {current_energy} / {max_energy} {cfg['energy_name']}",
        f"📅 **Dia:** {weekday_name} ({today_str})",
        "",
        "🎯 **Roteiro de Farm Prioritário:**",
    ]
    for t in tasks:
        check_box = "[x]" if t["completed"] else "[ ]"
        status_disp = "(Disponível Agora)" if t["available_now"] else f"({t['time_estimate']})"
        summary_lines.append(
            f"{t['step']}. {check_box} **{t['target_character']}** | {t['type_label']}: {t['material_name']} ({t['cost_energy']} {cfg['energy_name']}) - *{status_disp}*"
        )

    summary_lines.append("")
    summary_lines.append(
        f"💡 *Total Planejado: {accumulated_energy} {cfg['energy_name']} | Progresso Hoje: {completed_count}/{len(tasks)} ({completion_pct}%)*"
    )
    quick_summary_text = "\n".join(summary_lines)

    return {
        "game_id": g,
        "game_name": game_names.get(g, g.upper()),
        "date": today_str,
        "weekday": weekday,
        "weekday_name": weekday_name,
        "energy": {
            "current": current_energy,
            "max": max_energy,
            "name": cfg["energy_name"],
            "icon": cfg["energy_icon"],
            "allocated_total": accumulated_energy,
            "usage_pct": min(100, int((current_energy / max_energy) * 100)) if max_energy > 0 else 0,
        },
        "tasks": tasks,
        "completed_count": completed_count,
        "total_tasks": len(tasks),
        "completion_percentage": completion_pct,
        "quick_summary_text": quick_summary_text,
    }

# Re-exports para compatibilidade total de API e mocks (calculators/*)
from calculators.gacha_math import simulate_gacha_probabilities, calculate_gacha_forecast  # noqa: E402,F401
from calculators.stat_breakpoints import calculate_stat_breakpoints  # noqa: E402,F401
from calculators.account_strategy import _norm_str, analyze_account_gaps, recommend_relic_crafting  # noqa: E402,F401
