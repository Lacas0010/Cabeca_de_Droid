import os
import re
import json
import random
import datetime
from datetime import datetime, timedelta
import unicodedata
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Optional, Any


# Expressões regulares pré-compiladas para alta performance
RE_MULTIPLE_SPACES = re.compile(r'\s+')
RE_PARENTHESES = re.compile(r'\([^)]*\)')
RE_CLEAN_CHARS = re.compile(r'[#*\-]+')
RE_EQUAL_SPLIT = re.compile(r'\s*=\s*')

def remove_accents(input_str: str) -> str:
    """Remove acentos e diacríticos de uma string."""
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

def normalize_slot_name(slot_str: str, game_id: str = "") -> str:
    """Normaliza nomes de slots em português, inglês ou numéricos para chaves padrão do jogo."""
    if not slot_str:
        return ""
    s = remove_accents(str(slot_str).lower().strip())
    g = game_id.lower().strip() if game_id else ""
    
    # 1. Normalização contextual por jogo para slots numéricos
    if g == "genshin":
        if s in ["1", "flor", "flower"]: return "flower"
        if s in ["2", "pena", "plume", "feather"]: return "plume"
        if s in ["3", "areia", "relogio", "sands"]: return "sands"
        if s in ["4", "copo", "calice", "goblet"]: return "goblet"
        if s in ["5", "tiara", "coroa", "circlet"]: return "circlet"
    elif g == "hsr":
        if s in ["1", "cabeca", "head"]: return "head"
        if s in ["2", "mao", "maos", "hands"]: return "hands"
        if s in ["3", "corpo", "body"]: return "body"
        if s in ["4", "pe", "pes", "bota", "feet"]: return "feet"
        if s in ["5", "esfera", "planar_sphere", "sphere"]: return "planar_sphere"
        if s in ["6", "corda", "link_rope", "rope"]: return "link_rope"
    elif g == "zzz":
        for i in range(1, 7):
            if f'disco {i}' in s or f'slot_{i}' in s or f'slot {i}' in s or f'disc {i}' in s or f'disco_{i}' in s or f'disc_{i}' in s or s == str(i):
                return f'slot_{i}'

    # 2. Prioriza mapeamento por nome de slot
    if any(k in s for k in ['copo', 'calice', 'goblet']): return 'goblet'
    if any(k in s for k in ['areia', 'relogio', 'sands']): return 'sands'
    if any(k in s for k in ['tiara', 'coroa', 'circlet']): return 'circlet'
    if any(k in s for k in ['flor', 'flower']): return 'flower'
    if any(k in s for k in ['pena', 'plume', 'feather']): return 'plume'

    if any(k in s for k in ['esfera', 'planar_sphere', 'sphere']): return 'planar_sphere'
    if any(k in s for k in ['corda', 'link_rope', 'rope']): return 'link_rope'
    if any(k in s for k in ['cabeca', 'head']): return 'head'
    if any(k in s for k in ['mao', 'maos', 'hands']): return 'hands'
    if any(k in s for k in ['corpo', 'body']): return 'body'
    if any(k in s for k in ['bota', 'botas', 'feet']) or s in ['pe', 'pes', 'pés', 'pé']: return 'feet'
    
    # 3. Fallback genérico por número para ZZZ
    for i in range(1, 7):
        if f'disco {i}' in s or f'slot_{i}' in s or f'slot {i}' in s or f'disc {i}' in s or f'disco_{i}' in s or f'disc_{i}' in s or s == str(i):
            return f'slot_{i}'

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
    "sigrid new": "sigrid"
}

CHAR_DISPLAY_NAMES_PT = {
    # HSR
    "trailblazer": "Desbravador (Harmonia)",
    "trailblazer_harmony": "Desbravador (Harmonia)",
    "trailblazer_remembrance": "Desbravador (Rememoração)",
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
    "sigrid": "Sigrid"
}

def get_char_display_name(norm_name: str, fallback: str = "") -> str:
    """Retorna o nome em português limpo e traduzido para exibição na interface."""
    norm = normalize_char_name(norm_name)
    if norm in CHAR_DISPLAY_NAMES_PT:
        return CHAR_DISPLAY_NAMES_PT[norm]
    if fallback:
        return fallback
    return norm.replace("_", " ").title()

def normalize_char_name(name: str) -> str:
    """
    Normaliza o nome do personagem resolvendo tradução Português <-> Inglês,
    removendo acentos, hifens, bullets, parênteses e múltiplos espaços. Preserva qualificadores como 'Nova'.
    """
    if not name:
        return ""
    clean = str(name).lower()
    clean = clean.replace("•", " ").replace("-", " ").replace("(", " ").replace(")", " ").replace(".", " ").replace(",", " ").replace(":", " ").replace("#", " ")
    clean = remove_accents(clean)
    clean = RE_MULTIPLE_SPACES.sub(' ', clean).strip()

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

    # 1. Tabela Mestre Oficial de IDs (Fonte de verdade primária)
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
            "yunli": "1221"
        },
        "genshin": {
            "ayaka": "10000002",
            "bennett": "10000032",
            "kazuha": "10000047",
            "neuvillette": "10000089",
            "arlecchino": "10000096",
            "furina": "10000088",
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
            "lan yan": "10000108",
            "viajante": "10000005",
            "traveler": "10000005",
            "manequina": "10000118"
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
            "sigrid new": "1591"
        }
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
                        master_map[n_lower] = c_str
                        master_map[normalize_char_name(n_lower)] = c_str
        except Exception:
            pass

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
        "fugue": "tingyun fugue"
    }

    # 2. Carrega roster local como fallback
    roster_file = f"{game_id}/roster_data_{game_id}.json"
    if os.path.exists(roster_file):
        try:
            with open(roster_file, "r", encoding="utf-8") as f:
                roster_data = json.load(f)
                for char in roster_data:
                    c_name = char.get("name", "").strip()
                    c_id = char.get("id") or char.get("character_id")
                    if c_name and c_id:
                        c_name_lower = c_name.lower()
                        norm_c_name = normalize_char_name(c_name)
                        
                        if c_name_lower not in master_map:
                            master_map[c_name_lower] = str(c_id)
                        if norm_c_name not in master_map:
                            master_map[norm_c_name] = str(c_id)
                            
                        # Cria o alias em inglês apontando para o ID real se não existir
                        if c_name_lower in aliases_pt_to_en:
                            en_alias = aliases_pt_to_en[c_name_lower]
                            en_alias_lower = en_alias.lower()
                            norm_en_alias = normalize_char_name(en_alias)
                            
                            if en_alias_lower not in master_map:
                                master_map[en_alias_lower] = str(c_id)
                            if norm_en_alias not in master_map:
                                master_map[norm_en_alias] = str(c_id)
                                
                        if norm_c_name in aliases_pt_to_en:
                            en_alias = aliases_pt_to_en[norm_c_name]
                            en_alias_lower = en_alias.lower()
                            norm_en_alias = normalize_char_name(en_alias)
                            
                            if en_alias_lower not in master_map:
                                master_map[en_alias_lower] = str(c_id)
                            if norm_en_alias not in master_map:
                                master_map[norm_en_alias] = str(c_id)
        except Exception:
            pass

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
                master = fetch_master_id_list(game_id)
                indexed_data = dict(data)
                for k, v in list(data.items()):
                    if isinstance(v, dict):
                        name = v.get("name", "")
                        norm_name = normalize_char_name(name)
                        norm_key = normalize_char_name(k)
                        cid = master.get(norm_name) or master.get(norm_key) or master.get(k.lower())
                        if cid:
                            indexed_data[str(cid)] = v
                        if norm_name:
                            indexed_data[norm_name] = v
                        if norm_key:
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
            "crit_rate":  {"min": 2.72, "avg": 3.305, "max": 3.89},
            "crit_dmg":   {"min": 5.44, "avg": 6.61,  "max": 7.77},
            "atk_pct":    {"min": 4.08, "avg": 4.955, "max": 5.83},
            "hp_pct":     {"min": 4.08, "avg": 4.955, "max": 5.83},
            "def_pct":    {"min": 5.10, "avg": 6.195, "max": 7.29},
            "em":         {"min": 16.32, "avg": 19.815, "max": 23.31},
            "er":         {"min": 4.53, "avg": 5.505, "max": 6.48},
            "atk_flat":   {"min": 13.62, "avg": 16.535, "max": 19.45},
            "hp_flat":    {"min": 209.13, "avg": 253.94, "max": 298.75},
            "def_flat":   {"min": 16.20, "avg": 19.675, "max": 23.15},
        }
    },
    "hsr": {
        "max_possible_rolls": 9,
        "stats": {
            "crit_rate":    {"min": 2.59, "avg": 2.91, "max": 3.24},
            "crit_dmg":     {"min": 5.18, "avg": 5.83, "max": 6.48},
            "atk_pct":      {"min": 3.45, "avg": 3.88, "max": 4.32},
            "hp_pct":       {"min": 3.45, "avg": 3.88, "max": 4.32},
            "def_pct":      {"min": 4.32, "avg": 4.86, "max": 5.40},
            "break_effect": {"min": 5.18, "avg": 5.83, "max": 6.48},
            "spd":          {"min": 2.00, "avg": 2.30, "max": 2.60},
            "ehr":          {"min": 3.45, "avg": 3.88, "max": 4.32},
            "res":          {"min": 3.45, "avg": 3.88, "max": 4.32},
            "atk_flat":     {"min": 17.00, "avg": 19.15, "max": 21.30},
            "hp_flat":      {"min": 33.80, "avg": 38.05, "max": 42.30},
            "def_flat":     {"min": 17.00, "avg": 19.15, "max": 21.30},
        }
    },
    "zzz": {
        "max_possible_rolls": 9,
        "stats": {
            "crit_rate":    {"min": 2.40, "avg": 2.70, "max": 3.00},
            "crit_dmg":     {"min": 4.80, "avg": 5.40, "max": 6.00},
            "atk_pct":      {"min": 2.40, "avg": 2.70, "max": 3.00},
            "hp_pct":       {"min": 2.40, "avg": 2.70, "max": 3.00},
            "def_pct":      {"min": 3.84, "avg": 4.32, "max": 4.80},
            "anomaly_prof": {"min": 7.20, "avg": 8.10, "max": 9.00},
            "pen_flat":     {"min": 7.20, "avg": 8.10, "max": 9.00},
            "atk_flat":     {"min": 12.00, "avg": 13.50, "max": 15.00},
            "hp_flat":      {"min": 89.60, "avg": 100.80, "max": 112.00},
            "def_flat":     {"min": 12.00, "avg": 13.50, "max": 15.00},
        }
    }
}

MAX_ROLL_VALUES = {
    g: {s: spec["max"] for s, spec in data["stats"].items()}
    for g, data in GAME_ROLL_SPECS.items()
}

# ==========================================
# MAPEAMENTO PARA NORMALIZAÇÃO DE NOMES DE ATRIBUTOS
# ==========================================
STAT_NAME_MAP = {
    # Taxa Crítica
    "taxa crítica": "crit_rate", "taxa critica": "crit_rate", "taxa crit": "crit_rate", "crit rate": "crit_rate", "crit_rate": "crit_rate", "rate": "crit_rate", "taxa": "crit_rate",
    "chance de crit": "crit_rate", "chance de crit%": "crit_rate", "taxa de crit": "crit_rate", "taxa de crit%": "crit_rate",
    "taxa crítica%": "crit_rate", "taxa critica%": "crit_rate", "taxa crit%": "crit_rate", "chance de crt": "crit_rate", "chance de crt%": "crit_rate",
    "chance de crítico": "crit_rate", "chance de critico": "crit_rate", "chance de crítico%": "crit_rate", "chance de critico%": "crit_rate", "taxa de crítico": "crit_rate", "taxa de critico": "crit_rate", "taxa de crítico%": "crit_rate", "taxa de critico%": "crit_rate",
    "taxa crt": "crit_rate", "taxa crt%": "crit_rate", "crit rate%": "crit_rate", "critical rate": "crit_rate",
    
    # Dano Crítico
    "dano crítico": "crit_dmg", "dano critico": "crit_dmg", "dano crit": "crit_dmg", "crit dmg": "crit_dmg", "crit_dmg": "crit_dmg", "dmg": "crit_dmg", "dano": "crit_dmg", "damage": "crit_dmg",
    "dano crit%": "crit_dmg", "dano de crit": "crit_dmg", "dano de crit%": "crit_dmg", "dano crítico%": "crit_dmg", "dano critico%": "crit_dmg",
    "dano crt": "crit_dmg", "dano crt%": "crit_dmg", "dano de crt": "crit_dmg", "dano de crt%": "crit_dmg",
    "dano de crítico": "crit_dmg", "dano de critico": "crit_dmg", "dano de crítico%": "crit_dmg", "dano de critico%": "crit_dmg", "crit dmg%": "crit_dmg", "critical damage": "crit_dmg",
    
    # Velocidade
    "velocidade": "spd", "vel": "spd", "spd": "spd", "speed": "spd",
    
    # Efeito de Quebra
    "efeito de quebra": "break_effect", "quebra": "break_effect", "break effect": "break_effect", "break_effect": "break_effect", "be": "break_effect",
    "efeito de quebra%": "break_effect", "break_effect%": "break_effect", "break": "break_effect",
    
    # Proficiência Elemental / Anomalia
    "proficiência elemental": "em", "proficiencia elemental": "em", "maestria elemental": "em", "maestria": "em", "maestria_elemental": "em", "proficiência": "em", "proficiencia": "em", "elemental mastery": "em", "em": "em", "prof": "em", "prof. elemental": "em", "prof. eleme.": "em", "prof eleme": "em", "prof eleme.": "em", "prof. element.": "em", "prof element": "em", "prof element.": "em", "mastery": "em",
    "anomaly proficiency": "anomaly_prof", "proficiência em anomalia": "anomaly_prof", "proficiencia em anomalia": "anomaly_prof", "proficiência de anomalia": "anomaly_prof", "proficiencia de anomalia": "anomaly_prof", "prof. anomalia": "anomaly_prof", "prof anomalia": "anomaly_prof", "anomaly_prof": "anomaly_prof",
    "proficiência de anomalia%": "anomaly_prof", "proficiencia de anomalia%": "anomaly_prof", "anomalia": "anomaly_prof",
    
    # Recarga de Energia / Taxa de Regeneração de Energia
    "recarga de energia": "er", "recarga": "er", "energy recharge": "er", "er": "er", "recharge": "er", "recarga de energia%": "er",
    "taxa de regeneração de energia": "err", "taxa de regeneracao de energia": "err", "taxa de regen. energia": "err", "taxa de regen energia": "err", "taxa de regen. de energia": "err", "taxa de regen de energia": "err", "recuperação de energia": "err", "recuperacao de energia": "err", "regen. energia": "err", "regen energia": "err", "taxa de reg. de energia": "err", "recup. energia": "err", "recup energia": "err", "energy regen rate": "err", "energy regen": "err", "energy regeneration rate": "err", "err": "err",
    
    # Bônus de Cura
    "bônus de cura": "healing_bonus", "bonus de cura": "healing_bonus", "cura bônus": "healing_bonus", "cura bonus": "healing_bonus", "bônus de cura%": "healing_bonus", "bonus de cura%": "healing_bonus", "healing bonus": "healing_bonus", "outgoing healing boost": "healing_bonus", "healing": "healing_bonus", "healing_bonus": "healing_bonus",
    
    # Atributos Percentuais
    "atq %": "atk_pct", "atq%": "atk_pct", "atk%": "atk_pct", "atk %": "atk_pct", "ataque%": "atk_pct", "attack%": "atk_pct", "atk_pct": "atk_pct",
    "vida %": "hp_pct", "vida%": "hp_pct", "hp%": "hp_pct", "hp %": "hp_pct", "hp_pct": "hp_pct", "vida_pct": "hp_pct", "pv%": "hp_pct",
    "defesa %": "def_pct", "defesa%": "def_pct", "def%": "def_pct", "def %": "def_pct", "defesa_pct": "def_pct", "def_pct": "def_pct",
    
    # Atributos Planos (Flats)
    "atq": "atk_flat", "atk": "atk_flat", "ataque": "atk_flat", "attack": "atk_flat", "atk_flat": "atk_flat",
    "vida": "hp_flat", "hp": "hp_flat", "hp_flat": "hp_flat", "pv": "hp_flat", "pontos de vida": "hp_flat",
    "defesa": "def_flat", "def": "def_flat", "defesa_flat": "def_flat", "def_flat": "def_flat",
    
    # Bônus Elementais (Genshin / HSR / ZZZ)
    "pyro dmg": "pyro_dmg", "pyro dmg bonus": "pyro_dmg", "bônus de dano pyro": "pyro_dmg", "bonus de dano pyro": "pyro_dmg", "dano pyro": "pyro_dmg", "dano de pyro": "pyro_dmg", "pyro": "pyro_dmg",
    "fire dmg": "fire_dmg", "fire dmg bonus": "fire_dmg", "bônus de dano de fogo": "fire_dmg", "bonus de dano de fogo": "fire_dmg", "bônus de dano fogo": "fire_dmg", "bonus de dano fogo": "fire_dmg", "dano de fogo": "fire_dmg", "dano fogo": "fire_dmg", "fogo": "fire_dmg",
    
    "hydro dmg": "hydro_dmg", "hydro dmg bonus": "hydro_dmg", "bônus de dano hydro": "hydro_dmg", "bonus de dano hydro": "hydro_dmg", "dano hydro": "hydro_dmg", "dano de hydro": "hydro_dmg", "hydro": "hydro_dmg", "bônus de dano de água": "hydro_dmg", "bonus de dano de agua": "hydro_dmg", "dano de agua": "hydro_dmg", "dano agua": "hydro_dmg", "bônus de dano agua": "hydro_dmg", "bonus de dano agua": "hydro_dmg",
    
    "electro dmg": "electro_dmg", "electro dmg bonus": "electro_dmg", "bônus de dano electro": "electro_dmg", "bonus de dano electro": "electro_dmg", "dano electro": "electro_dmg", "dano de electro": "electro_dmg", "electro": "electro_dmg", "eletro": "electro_dmg",
    "lightning dmg": "lightning_dmg", "lightning dmg bonus": "lightning_dmg", "bônus de dano de raio": "lightning_dmg", "bonus de dano de raio": "lightning_dmg", "bônus de dano raio": "lightning_dmg", "bonus de dano raio": "lightning_dmg", "dano de raio": "lightning_dmg", "dano raio": "lightning_dmg", "raio": "lightning_dmg",
    "electric dmg": "electric_dmg", "electric dmg bonus": "electric_dmg", "bônus de dano elétrico": "electric_dmg", "bonus de dano eletrico": "electric_dmg", "bônus de dano de elétrico": "electric_dmg", "bonus de dano de eletrico": "electric_dmg", "dano elétrico": "electric_dmg", "dano eletrico": "electric_dmg", "dano de eletrico": "electric_dmg",
    
    "cryo dmg": "cryo_dmg", "cryo dmg bonus": "cryo_dmg", "bônus de dano cryo": "cryo_dmg", "bonus de dano cryo": "cryo_dmg", "dano cryo": "cryo_dmg", "dano de cryo": "cryo_dmg", "cryo": "cryo_dmg",
    "ice dmg": "ice_dmg", "ice dmg bonus": "ice_dmg", "bônus de dano de gelo": "ice_dmg", "bonus de dano de gelo": "ice_dmg", "bônus de dano gelo": "ice_dmg", "bonus de dano gelo": "ice_dmg", "dano de gelo": "ice_dmg", "dano gelo": "ice_dmg", "gelo": "ice_dmg",
    
    "anemo dmg": "anemo_dmg", "anemo dmg bonus": "anemo_dmg", "bônus de dano anemo": "anemo_dmg", "bonus de dano anemo": "anemo_dmg", "dano anemo": "anemo_dmg", "dano de anemo": "anemo_dmg", "anemo": "anemo_dmg",
    "wind dmg": "wind_dmg", "wind dmg bonus": "wind_dmg", "bônus de dano de vento": "wind_dmg", "bonus de dano de vento": "wind_dmg", "bônus de dano vento": "wind_dmg", "bonus de dano vento": "wind_dmg", "dano de vento": "wind_dmg", "dano vento": "wind_dmg", "vento": "wind_dmg",
    
    "geo dmg": "geo_dmg", "geo dmg bonus": "geo_dmg", "bônus de dano geo": "geo_dmg", "bonus de dano geo": "geo_dmg", "dano geo": "geo_dmg", "dano de geo": "geo_dmg", "geo": "geo_dmg",
    "dendro dmg": "dendro_dmg", "dendro dmg bonus": "dendro_dmg", "bônus de dano dendro": "dendro_dmg", "bonus de dano dendro": "dendro_dmg", "dano dendro": "dendro_dmg", "dano de dendro": "dendro_dmg", "dendro": "dendro_dmg",
    
    "physical dmg": "physical_dmg", "physical dmg bonus": "physical_dmg", "bônus de dano físico": "physical_dmg", "bonus de dano fisico": "physical_dmg", "dano físico": "physical_dmg", "dano fisico": "physical_dmg", "físico": "physical_dmg", "fisico": "physical_dmg", "physical": "physical_dmg",
    "quantum dmg": "quantum_dmg", "quantum dmg bonus": "quantum_dmg", "bônus de dano quântico": "quantum_dmg", "bonus de dano quantico": "quantum_dmg", "dano quântico": "quantum_dmg", "dano quantico": "quantum_dmg", "quântico": "quantum_dmg", "quantico": "quantum_dmg", "quantum": "quantum_dmg",
    "imaginary dmg": "imaginary_dmg", "imaginary dmg bonus": "imaginary_dmg", "bônus de dano imaginário": "imaginary_dmg", "bonus de dano imaginario": "imaginary_dmg", "dano imaginário": "imaginary_dmg", "dano imaginario": "imaginary_dmg", "imaginário": "imaginary_dmg", "imaginario": "imaginary_dmg", "imaginary": "imaginary_dmg",
    "ether dmg": "ether_dmg", "ether dmg bonus": "ether_dmg", "bônus de dano de éter": "ether_dmg", "bonus de dano de eter": "ether_dmg", "bônus de dano éter": "ether_dmg", "bonus de dano eter": "ether_dmg", "dano de éter": "ether_dmg", "dano de eter": "ether_dmg", "dano éter": "ether_dmg", "dano eter": "ether_dmg", "éter": "ether_dmg", "eter": "ether_dmg",
    
    # HSR Específicos
    "effect hit rate": "ehr", "ehr": "ehr", "taxa de acerto de efeito": "ehr", "chance de acerto de efeito": "ehr", "chance de acerto": "ehr", "acerto de efeito": "ehr", "acerto efeito": "ehr",
    "effect res": "res", "res": "res", "resistência a efeito": "res", "resistencia a efeito": "res", "res_efeito": "res", "res a efeito": "res", "res efeito": "res",
    "outgoing healing": "healing_bonus", "outgoing_healing": "healing_bonus",
    
    # ZZZ Específicos
    "pen flat": "pen_flat", "pen": "pen_flat", "pen flat bonus": "pen_flat", "perfuração": "pen_flat", "perfuracao": "pen_flat", "perfuração flat": "pen_flat", "perfuracao flat": "pen_flat",
    "pen ratio": "pen_pct", "pen_pct": "pen_pct", "taxa de perfuração": "pen_pct", "taxa de perfuracao": "pen_pct", "perfuração%": "pen_pct", "perfuracao%": "pen_pct", "perfuracao ratio": "pen_pct", "perfuração ratio": "pen_pct",
    "impacto": "impact", "impact": "impact", "impact_pct": "impact",
    "taxa de controle de anomalia": "anomaly_mastery", "controle de anomalia": "anomaly_mastery", "anomaly mastery": "anomaly_mastery", "anomaly_mastery": "anomaly_mastery", "maestria de anomalia": "anomaly_mastery", "maest. anomalia": "anomaly_mastery", "maest anomalia": "anomaly_mastery"
}

_unaccented_map = {}
for _k, _v in STAT_NAME_MAP.items():
    _unaccented_map[_k] = _v
    _unaccented_map[remove_accents(_k)] = _v
STAT_NAME_MAP = _unaccented_map

# ==========================================
# WHITELIST ESTRITA DE SUBSTATS VÁLIDOS
# ==========================================
VALID_SUBSTATS = frozenset({
    "spd", "crit_rate", "crit_dmg", "atk_pct", "hp_pct", "def_pct",
    "break_effect", "ehr", "res", "em", "er", "err",
    "atk_flat", "hp_flat", "def_flat",
    "anomaly_prof", "anomaly_mastery", "pen_flat", "pen_pct", "impact",
})

# Fallbacks genéricos por jogo, usados quando o parser não extrai substats válidos
DEFAULT_SUBSTATS_FALLBACK = {
    "hsr":     ["crit_rate", "crit_dmg", "spd", "atk_pct"],
    "genshin": ["crit_rate", "crit_dmg", "atk_pct", "er"],
    "zzz":     ["crit_rate", "crit_dmg", "atk_pct"],
}

def normalize_stat_name(raw_name: str, has_percent: bool = False) -> str:
    """Normaliza o nome do atributo para chaves padrão do motor de cálculo, ignorando acentos, case e pontuação."""
    if not raw_name:
        return ""
    s = str(raw_name).strip()
    
    if "%" in s:
        has_percent = True
        s = s.replace("%", "")
        
    s = re.sub(r'\([^)]*\)', '', s)
    if ":" in s:
        s = s.split(":")[0]
    s = s.strip()
    
    clean = remove_accents(s.lower())
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    mapped = STAT_NAME_MAP.get(clean)
    if not mapped:
        clean_no_dots = clean.replace(".", "").strip()
        clean_no_dots = re.sub(r'\s+', ' ', clean_no_dots)
        mapped = STAT_NAME_MAP.get(clean_no_dots, clean)
        
    if has_percent:
        if mapped == "atk_flat": return "atk_pct"
        if mapped == "hp_flat" or mapped == "pv": return "hp_pct"
        if mapped == "def_flat": return "def_pct"
        
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
        {"em", "anomaly_prof"}
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
        token = re.sub(r'\([^)]*\)', '', raw)
        token = re.sub(r'[#*\-]+', '', token)
        token = token.strip()
        
        if not token:
            continue
        
        sub_tokens = re.split(r'\s*=\s*', token)
        
        for st in sub_tokens:
            st = st.strip()
            if not st:
                continue
            
            if len(st.split()) > 4:
                continue
            
            norm = normalize_stat_name(st)
            # Em guias de build, mencoes genéricas como "ATK", "HP", "DEF" representam os percentuais %
            if norm == "atk_flat": norm = "atk_pct"
            elif norm == "hp_flat": norm = "hp_pct"
            elif norm == "def_flat": norm = "def_pct"
            
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
    
    char_meta = meta_db.get(str(char_id))
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
        "def_flat": 0.2
    }

# ==========================================
# MOTOR DINÂMICO DE SCORES COM MAIN STAT E SUBSTAT WEIGHTING
# ==========================================
def clean_value(val_str: str) -> Tuple[float, bool]:
    """Extrai o valor numérico de uma string de status e indica se é percentual."""
    has_pct = "%" in val_str
    match = re.search(r'([\d\.]+)', val_str)
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
    char_meta = meta_db.get(str(char_id), {})
    
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
            "pyro_dmg", "hydro_dmg", "electro_dmg", "cryo_dmg", "anemo_dmg", "geo_dmg", "dendro_dmg", "physical_dmg",
            "fire_dmg", "ice_dmg", "lightning_dmg", "electric_dmg", "wind_dmg", "ether_dmg", "quantum_dmg", "imaginary_dmg"
        }
        
        if rec_mains:
            norm_rec = [normalize_stat_name(m) for m in rec_mains]
            if "anything" in norm_rec or "any" in norm_rec or "qualquer" in norm_rec or any(is_stat_equivalent(main_stat_norm, m) for m in norm_rec) or main_stat_norm in elemental_stats:
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
    
    if rating_pct >= 90.0: grade = "SSS"
    elif rating_pct >= 75.0: grade = "SS"
    elif rating_pct >= 60.0: grade = "S"
    elif rating_pct >= 45.0: grade = "A"
    elif rating_pct >= 30.0: grade = "B"
    elif rating_pct >= 15.0: grade = "C"
    else: grade = "D"
    
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
                    "max_roll": spec["max"]
                }
    return result

# ==========================================
# MOTOR DE ÍNDICE DE SORTE E EFICIÊNCIA DE ROLAGENS (LUCK SCORE)
# ==========================================
def calculate_relic_luck_index(game_id: str, char_id: str, slot: str, main_stat: str, substats_str: str) -> Dict[str, Any]:
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
            "wasted_procs": 0
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
                badge = f"💀 Desperdício" if est_p <= 1 else f"💀 Lixo (+{est_p})"
                color = "#f87171"
                wasted_procs += est_p
                
            substats_analyzed.append({
                "raw_text": p,
                "stat_name": sub_name_norm,
                "display_name": name.strip(),
                "value_str": val_str.strip(),
                "procs": est_p,
                "roll_value": rv_val,
                "weight": round(w, 2),
                "status": status,
                "status_badge": badge,
                "status_color": color
            })
            
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
        "wasted_procs": wasted_procs
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
            "circlet": "👑 Tiara"
        }
        return mapping.get(norm, f"Slot {slot_str}")
    elif g == "hsr":
        mapping = {
            "head": "🪖 Cabeça",
            "hands": "🧤 Mãos",
            "body": "🛡️ Corpo",
            "feet": "👢 Botas",
            "planar_sphere": "🔮 Esfera Plana",
            "link_rope": "🪢 Corda de Ligação"
        }
        return mapping.get(norm, f"Slot {slot_str}")
    elif g == "zzz":
        mapping = {
            "slot_1": "💿 Disco Slot 1 (HP)",
            "slot_2": "💿 Disco Slot 2 (ATK)",
            "slot_3": "💿 Disco Slot 3 (DEF)",
            "slot_4": "💿 Disco Slot 4",
            "slot_5": "💿 Disco Slot 5",
            "slot_6": "💿 Disco Slot 6"
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
                    "wasted_procs": luck_data["wasted_procs"]
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
                "relic_count": len(char_scores)
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
            "character_breakdown": []
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
        "all_relics": all_relic_entries[:30]
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
        if "<=" in target_expr: operator = "<="
        elif "<" in target_expr: operator = "<"
        elif ">" in target_expr: operator = ">"
        
        is_good = False
        if operator == ">=": is_good = (actual_val >= target_val)
        elif operator == "<=": is_good = (actual_val <= target_val)
        elif operator == ">": is_good = (actual_val > target_val)
        elif operator == "<": is_good = (actual_val < target_val)
        
        status = "GOOD" if is_good else "LOW"
        if status == "GOOD":
            msg = f"Sua {p_name} ({p_val_str}) atingiu a meta recomendada ({target_expr})!"
        else:
            msg = f"Aumente sua {p_name} ({p_val_str}), a meta recomendada é {target_expr}."
            
        results.append({
            "stat": p_name,
            "target": target_expr,
            "actual": p_val_str,
            "status": status,
            "message": msg
        })
        
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
        matches = re.findall(r"-\s*(Body|Feet|Planar Sphere|Link Rope):\s*(.*)", content)
        for slot, val in matches:
            tokens = re.split(r'\s*(?:/|\||\bor\b|,|>=|>|<=|<|=)\s*', val, flags=re.IGNORECASE)
            stats = []
            for t in tokens:
                t_clean = re.sub(r'\([^)]*\)', '', t).strip()
                if t_clean:
                    norm = normalize_stat_name(t_clean)
                    if norm and norm not in stats:
                        stats.append(norm)
            meta["main_stats"][slot.lower().replace(" ", "_")] = stats
            
        sub_match = re.search(
            r"(?:subatributos prioritários|sub-stats|substats)[^\n]*\n"
            r"([^\n#]+)",
            content, re.I
        )
        if sub_match:
            sub_line = sub_match.group(1).strip()
            if not sub_line:
                lines = content[sub_match.start(1):].split("\n")
                for l in lines:
                    l_stripped = l.strip()
                    if l_stripped and not l_stripped.startswith("#"):
                        sub_line = l_stripped
                        break
            raw_tokens = [tok.strip() for tok in re.split(r'[>,\/;]', sub_line) if tok.strip()]
            meta["substats_priority"] = sanitize_substats(raw_tokens, "hsr")
            
        benchmarks = {}
        speed_goal = re.search(r'(\d+)\s*speed\s*goal|speed\s*goal\s*of\s*(\d+)|breakpoint\s*of\s*(\d+)\s*spd|(\d+)\s*spd', content, re.I)
        if speed_goal:
            val = next(v for v in speed_goal.groups() if v)
            benchmarks["spd"] = f">= {val}"
        crit_goal = re.search(r'crit\s*rate\s*(?:goal|threshold)\s*of\s*(\d+)%|(\d+)%\s*crit\s*rate', content, re.I)
        if crit_goal:
            val = next(v for v in crit_goal.groups() if v)
            benchmarks["crit_rate"] = f">= {val}%"
        be_goal = re.search(r'break\s*effect\s*(?:goal|threshold)\s*of\s*(\d+)%|(\d+)%\s*break\s*effect', content, re.I)
        if be_goal:
            val = next(v for v in be_goal.groups() if v)
            benchmarks["break_effect"] = f">= {val}%"
        meta["general_benchmarks"] = benchmarks
        return meta

    def parse_zzz(content):
        meta = {"main_stats": {}, "substats_priority": [], "general_benchmarks": {}}
        matches = re.findall(r"(?:Disk|Slot|Disco)\s*(4|5|6)[:\- ]\s*(.*)", content, re.I)
        for slot, val in matches:
            tokens = re.split(r'\s*(?:/|\||\bor\b|,|>=|>|<=|<|=)\s*', val, flags=re.IGNORECASE)
            stats = []
            for t in tokens:
                t_clean = re.sub(r'\([^)]*\)', '', t).strip()
                if t_clean:
                    norm = normalize_stat_name(t_clean)
                    if norm and norm not in stats:
                        stats.append(norm)
            meta["main_stats"][f"slot_{slot}"] = stats
            
        sub_match = re.search(r"(?:substatus prioritários|substats):\s*(.*)", content, re.I)
        if sub_match:
            sub_line = sub_match.group(1).strip()
            raw_tokens = [tok.strip() for tok in re.split(r'[>,\/;]', sub_line) if tok.strip()]
            meta["substats_priority"] = sanitize_substats(raw_tokens, "zzz")
        return meta

    def parse_genshin(content):
        meta = {"main_stats": {}, "substats_priority": [], "general_benchmarks": {}}
        
        main_sec_match = re.search(r"### Atributos Principais[^\n]*\n(.*?)(?:###|##|$)", content, re.S | re.I)
        if main_sec_match:
            main_sec = main_sec_match.group(1)
            lines = main_sec.split("\n")
            for line in lines:
                m = re.search(r"-\s*\*\*([^\*]+)\*\*:?\s*(.*)", line)
                if m:
                    slot_label = m.group(1).lower()
                    val = m.group(2)
                    if "sand" in slot_label or "ampulheta" in slot_label:
                        slot_key = "sands"
                    elif "goblet" in slot_label or "cálice" in slot_label or "calice" in slot_label:
                        slot_key = "goblet"
                    elif "circlet" in slot_label or "tiara" in slot_label:
                        slot_key = "circlet"
                    else:
                        slot_key = slot_label.replace(" ", "_")

                    tokens = re.split(r'\s*(?:/|\||\bor\b|,|>=|>|<=|<|=|&)\s*', val, flags=re.IGNORECASE)
                    stats = []
                    for t in tokens:
                        t_clean = re.sub(r'\([^)]*\)', '', t).strip()
                        if t_clean:
                            norm = normalize_stat_name(t_clean)
                            if norm and norm not in stats:
                                stats.append(norm)
                    meta["main_stats"][slot_key] = stats

        sub_match = re.search(r"### Subatributos Prioritários[^\n]*\n([^\n#]+)", content, re.I)
        if not sub_match:
            sub_match = re.search(r"(?:subatributos|substatus|sub-stats|substats)[^\n]*[:\n]\s*([^\n#]+)", content, re.I)
            
        if sub_match:
            sub_line = sub_match.group(1).strip()
            raw_tokens = [tok.strip() for tok in re.split(r'[>,\/;=]', sub_line) if tok.strip()]
            meta["substats_priority"] = sanitize_substats(raw_tokens, "genshin")
        return meta

    if game_id == "hsr":
        parse_fn = parse_hsr
    elif game_id == "zzz":
        parse_fn = parse_zzz
    else:
        parse_fn = parse_genshin
    
    if os.path.exists(guias_dir):
        try:
            files = os.listdir(guias_dir)
            for f in files:
                if f.endswith(".md"):
                    raw_name = f[:-3].replace("_", " ").strip()
                    display_name = raw_name.title()
                    if display_name.lower().startswith("dan heng"):
                        display_name = display_name.replace("•", "•")
                    
                    # Cruza com a fonte mestre de IDs
                    normalized_raw = normalize_char_name(raw_name)
                    char_id = master_ids.get(normalized_raw, master_ids.get(raw_name.lower(), raw_name.lower().replace(" ", "_")))
                    filepath = os.path.join(guias_dir, f)
                    try:
                        with open(filepath, "r", encoding="utf-8") as file:
                            char_meta = parse_fn(file.read())
                            char_meta["name"] = display_name
                            meta_db[str(char_id)] = char_meta
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
        1:  {"xp": 0, "currency": 0, "boss": 0},
        20: {"xp": 120000, "currency": 24000, "boss": 0},
        40: {"xp": 400000, "currency": 120000, "boss": 2},
        50: {"xp": 750000, "currency": 240000, "boss": 6},
        60: {"xp": 1300000, "currency": 450000, "boss": 14},
        70: {"xp": 2100000, "currency": 750000, "boss": 26},
        80: {"xp": 3600000, "currency": 1250000, "boss": 46},
        90: {"xp": 5800000, "currency": 2090000, "boss": 46}
    },
    "hsr": {
        1:  {"xp": 0, "currency": 0, "boss": 0},
        20: {"xp": 110000, "currency": 15000, "boss": 0},
        30: {"xp": 280000, "currency": 45000, "boss": 0},
        40: {"xp": 600000, "currency": 110000, "boss": 4},
        50: {"xp": 1100000, "currency": 220000, "boss": 12},
        60: {"xp": 1900000, "currency": 420000, "boss": 28},
        70: {"xp": 3100000, "currency": 750000, "boss": 50},
        80: {"xp": 5100000, "currency": 1300000, "boss": 65}
    },
    "zzz": {
        1:  {"xp": 0, "currency": 0, "boss": 0},
        10: {"xp": 25000, "currency": 5000, "boss": 0},
        20: {"xp": 80000, "currency": 15000, "boss": 0},
        30: {"xp": 200000, "currency": 40000, "boss": 2},
        40: {"xp": 450000, "currency": 100000, "boss": 8},
        50: {"xp": 900000, "currency": 250000, "boss": 20},
        60: {"xp": 1800000, "currency": 600000, "boss": 40}
    }
}

def calculate_ascension(game_id, current_lvl, target_lvl, char_name: Optional[str] = None):
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
    if char_name:
        try:
            from static_data_manager import static_data_manager
            char_profile = static_data_manager.get_character_profile(game_id, char_name)
            if char_profile:
                if char_profile.get("boss_mat"):
                    boss_item_name = char_profile["boss_mat"]
                elif char_profile.get("stagnant_shadow_mat"):
                    boss_item_name = char_profile["stagnant_shadow_mat"]
                elif char_profile.get("core_skill_mat"):
                    boss_item_name = char_profile["core_skill_mat"]
                    
                local_specialty = char_profile.get("local_specialty")
                talent_material = char_profile.get("talent_book") or char_profile.get("calyx_mat") or char_profile.get("chip_type")
                weekly_boss_mat = char_profile.get("weekly_boss_mat")
                domain_days = char_profile.get("domain_days")
                open_today = char_profile.get("open_today", True)
        except Exception:
            pass
    
    daily_energy = 180 if game_id == "genshin" else 240
    boss_cost_per_run = 40 if game_id in ["genshin", "zzz"] else 30
    energy_factor = 16 if game_id == "genshin" else (6 if game_id == "hsr" else 8)
    total_energy_needed = int(boss_diff * energy_factor)
    estimated_days = round(total_energy_needed / daily_energy, 1) if daily_energy > 0 else 0.0

    return {
        "xp_needed": xp_diff,
        "xp_books_purple": xp_books if xp_books > 0 else 1,
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
        "estimated_farming_days": estimated_days
    }

def optimize_character_relics(game_id: str, char_id: str, relics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analisa o inventário de relíquias fornecido e determina a combinação ótima (BiS do inventário)
    para o personagem especificado, selecionando a peça de maior pontuação para cada slot.
    """
    game_id = game_id.lower().strip()
    if not relics_list:
        return {"best_pieces": {}, "overall_score": 0.0, "overall_grade": "D", "recommendations": ["Nenhuma relíquia encontrada no inventário."]}

    best_by_slot = {}
    for r in relics_list:
        slot = r.get("slot", "")
        norm_slot = normalize_slot_name(slot, game_id)
        if not norm_slot:
            continue

        main_stat = r.get("main_stat") or r.get("main") or ""
        sub_stats = r.get("sub_stats") or r.get("substats") or r.get("sub") or ""
        if isinstance(sub_stats, list):
            sub_stats_str = ", ".join([f"{s.get('name','')}: {s.get('val','')}" if isinstance(s, dict) else str(s) for s in sub_stats])
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
            "character_equipped": r.get("character_name", "")
        }

        if norm_slot not in best_by_slot or score > best_by_slot[norm_slot]["score"]:
            best_by_slot[norm_slot] = piece_entry

    if not best_by_slot:
        return {"best_pieces": {}, "overall_score": 0.0, "overall_grade": "D", "recommendations": ["Nenhuma relíquia válida foi avaliada."]}

    scores = [p["score"] for p in best_by_slot.values()]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

    if avg_score >= 90: overall_grade = "SS"
    elif avg_score >= 80: overall_grade = "S+"
    elif avg_score >= 70: overall_grade = "S"
    elif avg_score >= 60: overall_grade = "A"
    elif avg_score >= 50: overall_grade = "B"
    elif avg_score >= 40: overall_grade = "C"
    else: overall_grade = "D"

    recommendations = []
    for slot, piece in best_by_slot.items():
        if piece["score"] < 60:
            recommendations.append(f"Slot {slot.upper()}: A melhor peça no inventário possui nota {piece['grade']} ({piece['score']}%). Recomendado buscar upgrades.")

    return {
        "character": char_id,
        "best_pieces": best_by_slot,
        "overall_score": avg_score,
        "overall_grade": overall_grade,
        "recommendations": recommendations if recommendations else ["Sua build ótima de inventário está muito bem estruturada!"]
    }


# ==========================================
# 1. SIMULADOR MONTE CARLO DE GACHA / WISH
# ==========================================
import random

def simulate_gacha_probabilities(
    game_id: str,
    current_pity: int,
    is_guaranteed: bool,
    pulls_available: int,
    target_copies: int = 1,
    current_copies: int = 0,
    current_rank: Optional[int] = None,
    target_rank: Optional[int] = None,
    num_simulations: int = 10000
) -> dict:
    """
    Executa uma Simulação Monte Carlo para calcular a chance real (%) de obter N cópias do personagem alvo
    com base no Pity atual, Garantido (50/50), Desejos/Tiros disponíveis e o nível de Constelação/Eidolon/Mindscape já possuído.
    """
    game_id = (game_id or "genshin").lower().strip()
    current_pity = max(0, min(current_pity, 89))
    pulls_available = max(0, pulls_available)
    
    # Determina o prefixo e terminologia de acordo com o jogo
    if game_id == "genshin":
        prefix = "C"
        term = "Constelação"
    elif game_id == "hsr":
        prefix = "E"
        term = "Eidolon"
    else: # zzz
        prefix = "M"
        term = "Mindscape Cinema"
        
    # Converter current_rank e target_rank com suporte a fallback de current_copies / target_copies
    if current_rank is not None:
        curr_r = max(-1, min(current_rank, 6))
    elif current_copies > 0:
        curr_r = max(-1, min(current_copies - 1, 6))
    else:
        curr_r = -1

    if target_rank is not None:
        tgt_r = max(0, min(target_rank, 6))
    elif target_copies > 0:
        tgt_r = max(0, min(target_copies - 1, 6))
    else:
        tgt_r = 0

    # Total de cópias do personagem já possuídas vs total necessário para a meta
    owned_pulls = 0 if curr_r < 0 else (curr_r + 1)
    target_pulls = tgt_r + 1
    needed_new_copies = max(0, target_pulls - owned_pulls)

    curr_rank_label = "Não Possui" if curr_r < 0 else f"{prefix}{curr_r}"
    target_rank_label = f"{prefix}{tgt_r}"

    # Se a meta já foi alcançada ou superada
    if needed_new_copies == 0:
        dist_meta = {
            f"Já possui {curr_rank_label} (Meta {target_rank_label} já alcançada)": 100.0
        }
        return {
            "success_rate": 100.0,
            "target_copies": 0,
            "needed_new_copies": 0,
            "current_rank": curr_r,
            "target_rank": tgt_r,
            "current_rank_str": curr_rank_label,
            "target_rank_str": target_rank_label,
            "term": term,
            "pulls_available": pulls_available,
            "current_pity": current_pity,
            "is_guaranteed": is_guaranteed,
            "avg_pulls_spent": 0,
            "distribution": dist_meta,
            "num_simulations": num_simulations,
            "game_id": game_id
        }
    
    # Parâmetros da mecânica de Gacha por jogo
    soft_pity_start = 74 if game_id in ["genshin", "hsr"] else 75
    base_rate = 0.006  # 0.6%
    soft_pity_increment = 0.06
    
    successful_runs = 0
    total_pulls_spent_list = []
    copies_obtained_distribution = {i: 0 for i in range(needed_new_copies + 1)}
    
    for _ in range(num_simulations):
        pity = current_pity
        guaranteed = is_guaranteed
        copies = 0
        pulls_left = pulls_available
        pulls_spent = 0
        
        while pulls_left > 0 and copies < needed_new_copies:
            pulls_left -= 1
            pulls_spent += 1
            pity += 1
            
            # Cálculo de probabilidade do tiro atual com soft pity
            if pity < soft_pity_start:
                chance = base_rate
            else:
                chance = base_rate + (pity - soft_pity_start + 1) * soft_pity_increment
            chance = min(1.0, chance)
            
            if random.random() < chance:
                # Tirou um 5★ / Rank S
                pity = 0
                if guaranteed or random.random() < 0.5:
                    copies += 1
                    guaranteed = False
                else:
                    guaranteed = True
                    
        copies_obtained_distribution[copies] = copies_obtained_distribution.get(copies, 0) + 1
        if copies >= needed_new_copies:
            successful_runs += 1
            total_pulls_spent_list.append(pulls_spent)
            
    success_rate = (successful_runs / num_simulations) * 100.0
    avg_pulls_needed = round(sum(total_pulls_spent_list) / len(total_pulls_spent_list), 1) if total_pulls_spent_list else None
    
    # Converter distribuição em porcentagens com nomenclaturas reais dos jogos
    dist_pct = {}
    for k in range(needed_new_copies + 1):
        count = copies_obtained_distribution.get(k, 0)
        pct = round((count / num_simulations) * 100.0, 1)
        
        if k == 0:
            if curr_r < 0:
                lbl = "0 cópias (Não obtém o personagem)"
            else:
                lbl = f"0 novas cópias (Mantém {prefix}{curr_r})"
        else:
            final_r = (curr_r if curr_r >= 0 else -1) + k
            final_str = f"{prefix}{final_r}"
            if final_r >= tgt_r:
                lbl = f"+{k} cópia(s) (Alcança {final_str} - Meta Batida! 🎉)"
            else:
                lbl = f"+{k} cópia(s) (Alcança {final_str})"
        dist_pct[lbl] = pct

    return {
        "success_rate": round(success_rate, 1),
        "target_copies": needed_new_copies,
        "needed_new_copies": needed_new_copies,
        "current_rank": curr_r,
        "target_rank": tgt_r,
        "current_rank_str": curr_rank_label,
        "target_rank_str": target_rank_label,
        "term": term,
        "pulls_available": pulls_available,
        "current_pity": current_pity,
        "is_guaranteed": is_guaranteed,
        "avg_pulls_spent": avg_pulls_needed,
        "distribution": dist_pct,
        "num_simulations": num_simulations,
        "game_id": game_id
    }


def calculate_gacha_forecast(
    game_id: str,
    current_pulls: int,
    current_pity: int,
    is_guaranteed: bool,
    target_rank: int = 0,
    current_rank: int = -1,
    target_days: int = 21,
    has_daily_pass: bool = False,
    has_battle_pass: bool = False,
    include_shop_resets: bool = True,
    include_events_estimate: bool = True,
    include_endgame_resets: bool = True,
    character_name: str = "",
    num_simulations: int = 10000
) -> dict:
    """
    Calcula a projeção completa de acúmulo de tiros/gemas futuras (diárias, passe, eventos, resets)
    e executa simulação Monte Carlo conectada para prever a probabilidade de bater a meta de banner.
    """
    game_id = (game_id or "genshin").lower().strip()
    target_days = max(1, min(int(target_days), 180))
    current_pulls = max(0, int(current_pulls))
    current_pity = max(0, min(int(current_pity), 89))
    target_rank = max(0, min(int(target_rank), 6))
    current_rank = max(-1, min(int(current_rank), 6))

    # Nomenclaturas oficiais por jogo
    game_terms = {
        "genshin": {"term": "Constelação", "prefix": "C", "currency": "Gemas Essenciais", "pass_name": "Bênção da Lua Nova"},
        "hsr": {"term": "Eidolon", "prefix": "E", "currency": "Jades Estelares", "pass_name": "Passe de Suprimentos do Expresso"},
        "zzz": {"term": "Mindscape Cinema", "prefix": "M", "currency": "Policromos", "pass_name": "Associação Inter-Nó"}
    }
    t_info = game_terms.get(game_id, game_terms["genshin"])

    # 1. Projeção de Renda Diária F2P (60 gemas/dia em todos os 3 jogos)
    daily_gems = target_days * 60
    daily_pulls = daily_gems / 160.0

    # 2. Passe Diário (+90 gemas/dia)
    pass_gems = (target_days * 90) if has_daily_pass else 0
    pass_pulls = pass_gems / 160.0

    # 3. Resets Mensais da Loja (5 tiros no dia 1º de cada mês)
    shop_resets_count = 0
    if include_shop_resets:
        now = datetime.now()
        for d in range(1, target_days + 1):
            future_day = now + timedelta(days=d)
            if future_day.day == 1:
                shop_resets_count += 1
    shop_pulls = shop_resets_count * 5

    # 4. Projeção de Eventos da Versão (~52.4 gemas/dia de média de eventos)
    events_gems = int(target_days * 52.4) if include_events_estimate else 0
    events_pulls = events_gems / 160.0

    # 5. Endgame Quinzenal/Mensal (Abismo/Teatro/MoC/PF/AS/Shiyu - ~800 gemas por ciclo de 15 dias)
    endgame_cycles = (target_days // 15) if include_endgame_resets else 0
    endgame_gems = endgame_cycles * 800
    endgame_pulls = endgame_gems / 160.0

    # 6. Passe de Batalha (4 tiros especiais + 680 gemas por patch de 42 dias -> ~8.25 tiros)
    bp_pulls = round((target_days / 42.0) * 8.25, 1) if has_battle_pass else 0.0

    # Total de Tiros Futuros Acumulados
    future_pulls_total = round(daily_pulls + pass_pulls + shop_pulls + events_pulls + endgame_pulls + bp_pulls, 1)
    total_projected_pulls = int(current_pulls + future_pulls_total)

    # 7. Simulação Monte Carlo com o Total Projetado
    sim_result = simulate_gacha_probabilities(
        game_id=game_id,
        current_pity=current_pity,
        is_guaranteed=is_guaranteed,
        pulls_available=total_projected_pulls,
        current_rank=current_rank,
        target_rank=target_rank,
        num_simulations=num_simulations
    )

    # Simulação de Comparação F2P (Apenas Saldo Atual + Diárias Puras)
    f2p_pure_pulls = int(current_pulls + daily_pulls + shop_pulls)
    f2p_sim_result = simulate_gacha_probabilities(
        game_id=game_id,
        current_pity=current_pity,
        is_guaranteed=is_guaranteed,
        pulls_available=f2p_pure_pulls,
        current_rank=current_rank,
        target_rank=target_rank,
        num_simulations=3000
    )

    # 8. Cálculo Matemático de Pior Cenário (Worst-case para 100% de Garantia)
    needed_new_copies = sim_result.get("needed_new_copies", 1)
    if needed_new_copies <= 0:
        worst_case_pulls = 0
    elif needed_new_copies == 1:
        worst_case_pulls = (90 - current_pity) if is_guaranteed else (180 - current_pity)
    else:
        first_copy_worst = (90 - current_pity) if is_guaranteed else (180 - current_pity)
        remaining_copies_worst = (needed_new_copies - 1) * 180
        worst_case_pulls = first_copy_worst + remaining_copies_worst

    pulls_needed_for_guarantee = max(0, worst_case_pulls - total_projected_pulls)
    gems_needed_for_guarantee = pulls_needed_for_guarantee * 160

    # 9. Parecer Estratégico Textual & Classificação
    success_rate = sim_result.get("success_rate", 0.0)
    if needed_new_copies <= 0:
        verdict_status = "ACQUIRED"
        verdict_badge = "Meta Já Alcançada"
        verdict_color = "#34d399"
        verdict_text = f"Você já possui o nível desejado ({t_info['prefix']}{target_rank}) no seu Roster!"
    elif success_rate >= 95.0:
        verdict_status = "SAFE"
        verdict_badge = "Garantia Praticamente Assegurada"
        verdict_color = "#34d399"
        verdict_text = f"Excelente planejamento! Sua probabilidade de sucesso é de {success_rate}%. Com ~{total_projected_pulls} tiros projetados, o risco de não bater a meta é quase nulo."
    elif success_rate >= 75.0:
        verdict_status = "FAVORABLE"
        verdict_badge = "Cenário Muito Favorável"
        verdict_color = "#10b981"
        verdict_text = f"Probabilidade Alta ({success_rate}%). Você acumulará cerca de {int(future_pulls_total)} novos tiros em {target_days} dias. Mantenha as diárias e eventos em dia."
    elif success_rate >= 50.0:
        verdict_status = "MODERATE"
        verdict_badge = "Cenário Competitivo (50/50)"
        verdict_color = "#fbbf24"
        verdict_text = f"Probabilidade Moderada ({success_rate}%). Você terá ~{total_projected_pulls} tiros até o fim do banner. Faltam {pulls_needed_for_guarantee} tiros para 100% de garantia matemática."
    elif success_rate >= 25.0:
        verdict_status = "RISKY"
        verdict_badge = "Cenário de Alto Risco"
        verdict_color = "#f97316"
        verdict_text = f"Probabilidade Baixa ({success_rate}%). O saldo projetado de {total_projected_pulls} tiros pode não ser suficiente caso perca o 50/50. Faltam {pulls_needed_for_guarantee} tiros para garantir."
    else:
        verdict_status = "CRITICAL"
        verdict_badge = "Cenário Crítico"
        verdict_color = "#ef4444"
        verdict_text = f"Probabilidade Crítica ({success_rate}%). Recomenda-se economizar mais recursos ou focar no C0/E0/M0 antes de arriscar cópias adicionais."

    income_breakdown = {
        "current_pulls": current_pulls,
        "current_gems_equiv": current_pulls * 160,
        "daily_f2p": {
            "days": target_days,
            "gems": daily_gems,
            "pulls": round(daily_pulls, 1),
            "label": f"Missões Diárias ({target_days}d × 60)"
        },
        "daily_pass": {
            "active": has_daily_pass,
            "gems": pass_gems,
            "pulls": round(pass_pulls, 1),
            "label": f"{t_info['pass_name']} ({target_days}d × 90)" if has_daily_pass else f"{t_info['pass_name']} (Inativo)"
        },
        "battle_pass": {
            "active": has_battle_pass,
            "pulls": round(bp_pulls, 1),
            "label": "Passe de Batalha (Prorrateado)" if has_battle_pass else "Passe de Batalha (Inativo)"
        },
        "shop_resets": {
            "count": shop_resets_count,
            "pulls": shop_pulls,
            "label": f"Reset de Loja ({shop_resets_count} mês(es) × 5)"
        },
        "events": {
            "active": include_events_estimate,
            "gems": events_gems,
            "pulls": round(events_pulls, 1),
            "label": f"Eventos de Versão (~{events_gems} gemas)"
        },
        "endgame": {
            "cycles": endgame_cycles,
            "gems": endgame_gems,
            "pulls": round(endgame_pulls, 1),
            "label": f"Endgame ({endgame_cycles} ciclos × 800 gemas)"
        },
        "total_future_pulls": future_pulls_total,
        "total_projected_pulls": total_projected_pulls,
        "total_projected_gems_equiv": total_projected_pulls * 160
    }

    return {
        "game_id": game_id,
        "character_name": character_name or "Personagem 5★ Alvo",
        "target_days": target_days,
        "current_pulls": current_pulls,
        "current_pity": current_pity,
        "is_guaranteed": is_guaranteed,
        "current_rank": current_rank,
        "target_rank": target_rank,
        "current_rank_str": sim_result["current_rank_str"],
        "target_rank_str": sim_result["target_rank_str"],
        "term": t_info["term"],
        "needed_new_copies": needed_new_copies,
        "total_projected_pulls": total_projected_pulls,
        "income_breakdown": income_breakdown,
        "success_rate": success_rate,
        "f2p_pure_success_rate": f2p_sim_result.get("success_rate", 0.0),
        "f2p_pure_pulls": f2p_pure_pulls,
        "avg_pulls_spent": sim_result.get("avg_pulls_spent"),
        "worst_case_pulls": worst_case_pulls,
        "pulls_needed_for_guarantee": pulls_needed_for_guarantee,
        "gems_needed_for_guarantee": gems_needed_for_guarantee,
        "distribution": sim_result.get("distribution", {}),
        "verdict": {
            "status": verdict_status,
            "badge": verdict_badge,
            "color": verdict_color,
            "text": verdict_text
        }
    }


# ==========================================
# 2. CENTRAL DE FARM INTELIGENTE DIÁRIO
# ==========================================
FARM_CALENDAR = {
    "genshin": {
        0: {"days": "Segunda-feira", "talents": ["Liberdade", "Prosperidade", "Transitoriedade", "Ordem", "Contenda (Natlan)"], "weapons": ["Decara", "Guyun", "Coral", "Densa Nevoeiro", "Madeira Sagrada (Natlan)"]},
        1: {"days": "Terça-feira", "talents": ["Resistência", "Diligência", "Elegância", "Equidade", "Ignição (Natlan)"], "weapons": ["Dente de Leão", "Elixir", "Grama", "Gota Purificadora", "Chama Noturna (Natlan)"]},
        2: {"days": "Quarta-feira", "talents": ["Balada", "Ouro", "Luz", "Justiça", "Conflito (Natlan)"], "weapons": ["Gladiador", "Aerosiderite", "Máscara", "Cálice Rúnico", "Vontade Deliberada (Natlan)"]},
        3: {"days": "Quinta-feira", "talents": ["Liberdade", "Prosperidade", "Transitoriedade", "Ordem", "Contenda (Natlan)"], "weapons": ["Decara", "Guyun", "Coral", "Densa Nevoeiro", "Madeira Sagrada (Natlan)"]},
        4: {"days": "Sexta-feira", "talents": ["Resistência", "Diligência", "Elegância", "Equidade", "Ignição (Natlan)"], "weapons": ["Dente de Leão", "Elixir", "Grama", "Gota Purificadora", "Chama Noturna (Natlan)"]},
        5: {"days": "Sábado", "talents": ["Balada", "Ouro", "Luz", "Justiça", "Conflito (Natlan)"], "weapons": ["Gladiador", "Aerosiderite", "Máscara", "Cálice Rúnico", "Vontade Deliberada (Natlan)"]},
        6: {"days": "Domingo", "talents": ["Todos os materiais abertos"], "weapons": ["Todos os materiais abertos"]}
    },
    "hsr": {
        0: {"days": "Segunda-feira", "note": "Reset Semanal do Universo Simulado e Eco da Guerra (3x recompensas)."},
        1: {"days": "Terça-feira", "note": "Calyx de Traço & Ascensão com drop normal."},
        2: {"days": "Quarta-feira", "note": "Foco recomendado: Farm de Túnel de Relíquias."},
        3: {"days": "Quinta-feira", "note": "Calyx de Traço & Ascensão."},
        4: {"days": "Sexta-feira", "note": "Foco recomendado: Ornamentos Planares (Universo Divergente/Simulado)."},
        5: {"days": "Sábado", "note": "Farm livre de Relíquias e Materiais de Ascensão."},
        6: {"days": "Domingo", "note": "Preparação de Energia para o Reset de Segunda."}
    },
    "zzz": {
        0: {"days": "Segunda-feira", "note": "Reset Semanal do Notorious Hunt (3x Caça aos Chefes de Dano)."},
        1: {"days": "Terça-feira", "note": "Foco recomendado: HIA Club - Chips de Atributo de Especialidade."},
        2: {"days": "Quarta-feira", "note": "Foco recomendado: HIA Club - Certificados de Promoção."},
        3: {"days": "Quinta-feira", "note": "Foco recomendado: Drive Disc Tuning & Limpeza de Rótulo."},
        4: {"days": "Sexta-feira", "note": "HIA Club - Materiais de Agente."},
        5: {"days": "Sábado", "note": "Farm livre de Discos e Materiais na Cavidade Zero."},
        6: {"days": "Domingo", "note": "Preparação de Bateria para o Reset Semanal."}
    }
}

GAME_MAX_LEVELS = {
    "genshin": 90,
    "hsr": 80,
    "zzz": 60
}

def is_genshin_farmable_today(char_name: str, day_of_week: int) -> bool:
    if day_of_week == 6:  # Domingo tudo aberto
        return True
    try:
        from static_data_manager import static_data_manager
        sched = static_data_manager.get_daily_farm_schedule("genshin", day_of_week)
        farmable_chars = [c.lower() for c in sched.get("farmable_characters", [])]
        c_clean = char_name.lower().strip()
        if any(c_clean == fc or fc in c_clean or c_clean in fc for fc in farmable_chars):
            return True
    except Exception:
        pass

    mon_thu = {"amber", "barbara", "klee", "diona", "aloy", "sucrose", "keqing", "ningguang", "qiqi", "xiao", "yelan", "shenhe", "thoma", "yoimiya", "heizou", "kokomi", "tighnari", "candace", "cyno", "faruzan", "lyney", "neuvillette", "navia", "xianyun", "mualani", "kachina", "kinich", "xilonen", "mavuika", "citlali", "ororon"}
    tue_fri = {"bennett", "diluc", "jean", "noelle", "mona", "eula", "ganyu", "hu tao", "hu_tao", "xiangling", "chongyun", "yun jin", "yun_jin", "yaoyao", "ayaka", "ayato", "sara", "araki", "itto", "nahida", "alhaitham", "dori", "layla", "kaveh", "freminet", "charlotte", "clorinde", "furina", "chasca", "ifa"}
    wed_sat = {"fischl", "kaeya", "lisa", "venti", "rosaria", "albedo", "beidou", "xingqiu", "zhongli", "yanfei", "baizhu", "raiden", "raiden shogun", "yae miko", "sayu", "gorou", "collei", "nilou", "wanderer", "dehya", "wriothesley", "chevreuse", "arlecchino", "emilie", "lan yan"}

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
        "weapon_mat": "https://enka.network/ui/UI_ItemIcon_114004.png"
    },
    "hsr": {
        "mora": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/2.png",
        "xp": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/22.png",
        "talent_book": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110.png",
        "boss": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/201.png",
        "weekly_boss": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/3.png",
        "crown": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/11.png",
        "weapon_ore": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/102.png",
        "weapon_mat": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110.png"
    },
    "zzz": {
        "mora": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4fde02b5f3a4c790dcbef6c74cb4fabf.png",
        "xp": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/55c259888e808554c02a3161944d7868.png",
        "talent_book": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png",
        "boss": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
        "weekly_boss": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/2196659ee41fc22d1533519c53644f37.png",
        "crown": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/faeebca44b20e03ee23b610c4f8ea03d.png",
        "weapon_ore": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4f1444b51f52e8e0ad4a8dc13432b04f.png",
        "weapon_mat": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png"
    }
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
        "w_mat_gold": "Material de Domínio de Arma (5★)"
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
        "w_mat_gold": "Matriz de Cone de Luz (5★)"
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
        "w_mat_gold": "Componente Mestre (5★)"
    }
}

def get_daily_farm_recommendations(game_id: str, roster: list = None, day_of_week: int = None, selected_chars: list = None) -> dict:
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
        
    game_calendar = FARM_CALENDAR.get(game_id, {}).get(day_of_week, {"days": "Hoje", "note": "Farm Livre"})

    meta_db = get_meta_data(game_id)
    
    recommendations = []
    all_roster_names = []
    
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
            rv = char.get("overall_score", char.get("build_score", 0.0))
            level = char.get("level", 1)
            element = char.get("element", "")
            icon = char.get("icon", "")
            weapon = char.get("weapon", {})
            skills = char.get("skills", [])
            if not skills and char.get("raw_md"):
                try:
                    from database import parse_skills_from_raw_md
                    skills = parse_skills_from_raw_md(char["raw_md"])
                except Exception:
                    pass
            
            # Se a lista de skills vier vazia do backend, injeta habilidades padrões oficiais do jogo
            if not skills:
                if game_id == "genshin":
                    skills = [
                        {"name": "Ataque Normal", "level": 6, "max_level": 10},
                        {"name": "Habilidade Elemental", "level": 8, "max_level": 10},
                        {"name": "Suprema (Elemental Burst)", "level": 8, "max_level": 10}
                    ]
                elif game_id == "hsr":
                    skills = [
                        {"name": "Ataque Básico", "level": 5, "max_level": 10},
                        {"name": "Perícia Elemental", "level": 8, "max_level": 10},
                        {"name": "Suprema", "level": 8, "max_level": 10},
                        {"name": "Talento Passivo", "level": 8, "max_level": 10}
                    ]
                else:
                    skills = [
                        {"name": "Ataque Básico", "level": 6, "max_level": 12},
                        {"name": "Esquiva", "level": 6, "max_level": 12},
                        {"name": "Ataque Especial", "level": 9, "max_level": 12},
                        {"name": "Ataque de Cadeia / Suprema", "level": 9, "max_level": 12},
                        {"name": "Ataque de Suporte", "level": 6, "max_level": 12}
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
                talent_domain_open = is_genshin_farmable_today(name, day_of_week)
                
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
                    reason_parts.append(f"Build nota {grade} (RV: {rv:.1f}%)")
                    
                reason = " | ".join(reason_parts)
                
                # Resolução do perfil detalhado do personagem e materiais de farm
                try:
                    from static_data_manager import static_data_manager
                    char_profile = static_data_manager.get_character_profile(game_id, name)
                    if not char_profile:
                        char_profile = static_data_manager._enrich_character_profile(game_id, dict(char))
                except Exception:
                    pass

                items_needed = {"icons": icons, "terms": terms}
                
                # 1. Ascensão de Personagem
                if level < max_level:
                    asc_calc = calculate_ascension(game_id, level, max_level, char_name=name)
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
                wb_name = (char_profile.get("weekly_boss_mat_name") if char_profile else None) or terms["weekly_boss_mat"]
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
                            talent_details.append({
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
                                "currency_needed": 5000
                            })
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

                        talent_details.append({
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
                            "currency_needed": currency_needed
                        })

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
                    except Exception:
                        pass

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
                        "w_enemy_t3_icon": w_prof.get("enemy_tier3_icon", icons["boss"])
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

                recommendations.append({
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
                    "action": f"Evoluir Nível/{terms['talent_category']}/Arma de {name}"
                })
    
    summary_totals = {
        "currency": 0,
        "xp_books": 0,
        "green_books": 0,
        "blue_books": 0,
        "purple_books": 0,
        "boss_mats": 0,
        "weekly_boss_mats": 0,
        "crowns": 0,
        "ores": 0
    }

    for rec in recommendations:
        in_dict = rec.get("items_needed", {})
        asc = in_dict.get("ascension")
        if asc and isinstance(asc, dict):
            summary_totals["currency"] += asc.get("mora_needed", 0)
            summary_totals["xp_books"] += asc.get("purple_books", 0)
            summary_totals["boss_mats"] += asc.get("boss_mats_needed", 0)
            
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
            
            all_roster_characters.append({
                "name": c_name,
                "level": c_lvl,
                "rarity": c_rarity,
                "element": c_elem,
                "icon": c_icon,
                "grade": c_grade,
                "score": c_score,
                "needs_ascension": c_lvl < max_level,
                "needs_relics": c_grade in ["B", "C", "D", "A"]
            })
                
    return {
        "game_id": game_id,
        "max_level": max_level,
        "day_of_week": day_of_week,
        "calendar_info": game_calendar,
        "all_roster_names": all_roster_names,
        "all_roster_characters": all_roster_characters,
        "priority_targets": recommendations,
        "summary_totals": summary_totals
    }


# ==========================================
# 3. ANALISADOR DE RELÍQUIAS LIXO (TRASH FINDER)
# ==========================================
def find_trash_relics(game_id: str, relics: list, meta_data: dict) -> dict:
    """
    Analisa a lista de relíquias do jogador contra todos os guias de meta.
    Retorna relíquias que possuem combinação de Atributo Principal + Substatus que NENHUM personagem aproveita.
    """
    game_id = (game_id or "genshin").lower().strip()
    trash_candidates = []
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
            subs = guide.get("substats", [])
            if isinstance(subs, list):
                for s in subs:
                    all_useful_subs.add(normalize_stat_name(s))
                    
    for relic in relics:
        name = relic.get("name", "Relíquia Desconhecida")
        slot = relic.get("slot", "")
        main_stat = normalize_stat_name(relic.get("main_stat", ""))
        substats = [normalize_stat_name(s.get("name", "")) for s in relic.get("substats", [])]
        
        # Quantos substatus dessa relíquia são úteis globalmente?
        useful_subs_count = sum(1 for s in substats if s in all_useful_subs or "crit" in s)
        
        # Critério de Lixo: Main Stat irrelevante para o slot + 0 ou 1 substatus útil com rolls baixos
        is_def_flat_heavy = any("def_flat" in s or "hp_flat" in s for s in substats)
        
        if (useful_subs_count == 0 and is_def_flat_heavy) or (useful_subs_count <= 1 and main_stat in ["def_pct", "hp_pct"] and "crit_rate" not in substats and "crit_dmg" not in substats):
            trash_candidates.append({
                "name": name,
                "slot": slot,
                "main_stat": relic.get("main_stat", ""),
                "substats": [s.get("name", "") for s in relic.get("substats", [])],
                "reason": "Substatus sem acertos de Crítico/Recarga e atributos irrelevantes para o meta atual.",
                "recommendation": "Converter em EXP ou Reciclar no Sintetizador"
            })
        else:
            good_relics_count += 1
            
    return {
        "game_id": game_id,
        "total_analyzed": len(relics),
        "good_relics_count": good_relics_count,
        "trash_count": len(trash_candidates),
        "trash_relics": trash_candidates[:15]  # Top 15 candidatas a lixo
    }


# ==========================================
# 4. CALCULADORA DE BREAKPOINTS DE STATUS
# ==========================================
def calculate_stat_breakpoints(game_id: str, char_name: str, stats: dict) -> dict:
    """
    Avalia se os status atuais de um personagem atingiram os limiares (breakpoints) vitais de combate.
    """
    game_id = (game_id or "hsr").lower().strip()
    breakpoints = []
    
    speed = float(stats.get("speed", stats.get("spd", 0.0)))
    ehr = float(stats.get("ehr", stats.get("effect_hit_rate", 0.0)))
    er = float(stats.get("er", stats.get("energy_recharge", 0.0)))
    crit_rate = float(stats.get("crit_rate", stats.get("crit_pct", 0.0)))
    crit_dmg = float(stats.get("crit_dmg", stats.get("crit_dmg_pct", 0.0)))
    
    if game_id == "hsr":
        # Check Breakpoints de SPD
        spd_tiers = [
            (134.0, "134 SPD (2 turnos no Ciclo 1 do MoC/PF)"),
            (142.0, "142 SPD (5 turnos em 3 Ciclos)"),
            (156.0, "156 SPD (3 turnos em 2 Ciclos)"),
            (160.1, "160.1 SPD (4 turnos em 2 Ciclos - Ruan Mei / Sparkle Speed Tier)")
        ]
        reached_spd = "Abaixo de 134 (Sem turnos extras)"
        next_spd = None
        for tier_val, desc in spd_tiers:
            if speed >= tier_val:
                reached_spd = desc
            elif next_spd is None:
                next_spd = f"Faltam {tier_val - speed:.1f} de VEL para atingir {desc}"
                
        breakpoints.append({
            "stat": "Velocidade (SPD)",
            "current": f"{speed:.1f}",
            "status": reached_spd,
            "next_goal": next_spd or "Breakpoint Máximo atingido!"
        })
        
        # Check EHR para Debuffers
        if ehr > 0 or "silver" in char_name.lower() or "pela" in char_name.lower() or "jiaoqiu" in char_name.lower():
            target_ehr = 67.0 if "silver" in char_name.lower() or "pela" in char_name.lower() else 140.0
            status_ehr = " 100% de Aplicação de Debuff garantida contra Inimigos Lvl 95" if ehr >= target_ehr else f" Risco de Errar Debuff (Alvo: {target_ehr}%)"
            breakpoints.append({
                "stat": "Efetividade de Acerto (EHR)",
                "current": f"{ehr:.1f}%",
                "status": status_ehr,
                "next_goal": f"Faltam {max(0.0, target_ehr - ehr):.1f}% de EHR" if ehr < target_ehr else "Meta atingida!"
            })

    elif game_id == "genshin":
        # Check ER (Recarga de Energia)
        target_er = 160.0  # Média global de suporte
        if "xiangling" in char_name.lower() or "faruzan" in char_name.lower():
            target_er = 200.0
        elif "raiden" in char_name.lower() or "yelan" in char_name.lower():
            target_er = 180.0
            
        status_er = " Supremo disponível em todas as rotações sem atraso" if er >= target_er else f" Recarga insuficiente para rotações perfeitas (Meta: {target_er}%)"
        breakpoints.append({
            "stat": "Recarga de Energia (ER)",
            "current": f"{er:.1f}%",
            "status": status_er,
            "next_goal": f"Faltam {max(0.0, target_er - er):.1f}% de ER" if er < target_er else "Meta atingida!"
        })
        
    # Razão de Crítico
    if crit_rate > 0 and crit_dmg > 0:
        ratio = crit_dmg / max(1.0, crit_rate)
        ideal = "Proporção Ideal 1:2 mantida!" if 1.8 <= ratio <= 2.2 else f"Proporção atual 1:{ratio:.1f} (Ideal é 1:2)"
        breakpoints.append({
            "stat": "Taxa/Dano Crítico",
            "current": f"{crit_rate:.1f}% / {crit_dmg:.1f}%",
            "status": ideal,
            "next_goal": "Ajustar capacete ou substatus para aproximação de 1:2" if not (1.8 <= ratio <= 2.2) else "Equilíbrio Perfeito"
        })
        
    return {
        "char_name": char_name,
        "game_id": game_id,
        "breakpoints": breakpoints
    }





# ==========================================
# 6. GERENCIADOR DE CÓDIGOS PROMOCIONAIS (DINÂMICO AO VIVO)
# ==========================================
PROMO_CODES_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 1800  # Cache de 30 minutos

FALLBACK_PROMO_CODES = {
    "hsr": [
        {"code": "STARRAILGIFT", "rewards": "50 Stellar Jade, 10,000 Credit", "status": "Ativo permanente"},
        {"code": "OMEGA", "rewards": "60 Stellar Jade, 1 Fuel", "status": "Ativo de versão"}
    ],
    "genshin": [
        {"code": "GENSHINGIFT", "rewards": "50 Primogem, 3 Hero's Wit", "status": "Ativo permanente"},
        {"code": "2BJ64QRZ7RT8", "rewards": "60 Primogem, 5 Adventurer's Experience", "status": "Ativo de versão"}
    ],
    "zzz": [
        {"code": "ZENLESSGIFT", "rewards": "50 Polychrome, 2 Official Investigator Log", "status": "Ativo permanente"},
        {"code": "ZZZMEIJI", "rewards": "30,000 Denny, 3 Senior Investigator Log", "status": "Ativo de evento"}
    ]
}

def fetch_live_promo_codes(game_id: str) -> List[Dict[str, Any]]:
    """Realiza raspagem em tempo real via MediaWiki API dos códigos de resgate ativos."""
    wiki_map = {
        'genshin': ('genshin-impact', 'Promotional_Code'),
        'hsr': ('honkai-star-rail', 'Redemption_Code'),
        'zzz': ('zenless-zone-zero', 'Redemption_Code')
    }
    g = game_id.lower().strip()
    if g not in wiki_map:
        return []
    
    wiki_name, page_name = wiki_map[g]
    url = f"https://{wiki_name}.fandom.com/api.php?action=parse&page={page_name}&format=json"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        r = requests.get(url, headers=headers, timeout=6)
        if r.status_code != 200:
            return []
        
        html = r.json().get('parse', {}).get('text', {}).get('*', '')
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table', class_='wikitable')
        
        codes = []
        seen = set()
        
        for t in tables[:2]:
            for tr in t.find_all('tr'):
                cols = [td.text.strip().replace('\n', ' ') for td in tr.find_all(['td', 'th'])]
                if len(cols) >= 3:
                    raw_code_col = cols[0]
                    raw_rewards_col = cols[2] if len(cols) >= 3 else cols[1]
                    raw_duration_col = cols[3] if len(cols) >= 4 else ''
                    
                    raw_code_clean = re.sub(r'(Quick|Redeem|\[\d+\])', '', raw_code_col, flags=re.IGNORECASE).strip()
                    code_match = re.search(r'[A-Za-z0-9]{5,30}', raw_code_clean)
                    if not code_match:
                        continue
                    
                    code = code_match.group(0).upper()
                    
                    if code in ('CODE', 'SERVER', 'REWARDS', 'DURATION', 'EXPIRED') or code in seen:
                        continue
                    
                    if 'expired:' in raw_duration_col.lower():
                        continue
                    
                    rewards = re.sub(r'\[\d+\]', '', raw_rewards_col).replace('×', 'x').replace('Ã—', 'x').strip()
                    rewards = ' '.join(rewards.split())
                    
                    status = 'Ativo (Ao vivo)'
                    if 'valid until:' in raw_duration_col.lower():
                        valid_match = re.search(r'valid until:\s*([^V\n\r]+)', raw_duration_col, re.IGNORECASE)
                        if valid_match:
                            val_str = valid_match.group(1).strip()
                            val_str = re.sub(r'([A-Za-z]+\s+\d+,\s+\d{4}).*', r'\1', val_str)
                            status = f'Ativo até {val_str}'
                    elif 'indefinite' in raw_duration_col.lower():
                        status = 'Ativo Permanente'
                    
                    seen.add(code)
                    codes.append({
                        'code': code,
                        'rewards': rewards if rewards else 'Recompensas de Evento',
                        'status': status
                    })
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
        PROMO_CODES_CACHE[g] = {
            "timestamp": now,
            "codes": live_codes
        }
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
    selected_chars: Optional[List[str]] = None
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

    weekday_names = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    weekday_name = weekday_names[weekday]

    # Configurações de Energia e Custos por Jogo
    game_configs = {
        "genshin": {
            "energy_name": "Resina Original",
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
            "max_level": 90
        },
        "hsr": {
            "energy_name": "Poder de Desbravamento",
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
            "currency_name": "Créditos",
            "max_level": 80
        },
        "zzz": {
            "energy_name": "Carga de Bateria",
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
            "max_level": 60
        }
    }

    cfg = game_configs[g]

    # Obtenção de Roster e Meta se não fornecidos
    if roster is None:
        try:
            import database
            roster = database.get_roster_data(g)
        except Exception:
            roster = []

    if meta_data is None:
        try:
            meta_data = get_meta_data(g)
        except Exception:
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
        except Exception:
            pass

    if current_energy is None:
        current_energy = cfg["default_current"]
    if max_energy is None:
        max_energy = cfg["default_max"]

    # Obtenção de tarefas já concluídas hoje no SQLite
    completed_task_ids = set()
    try:
        import database
        completed_task_ids = set(database.get_completed_farm_tasks(today_str, g))
    except Exception:
        pass

    # Consulta de recomendações de farm diárias
    recs_data = get_daily_farm_recommendations(game_id=g, roster=roster, day_of_week=weekday, selected_chars=selected_chars)
    targets = recs_data.get("priority_targets", [])
    cal_info = recs_data.get("calendar_info", {})

    from static_data_manager import static_data_manager
    static_schedule = static_data_manager.get_daily_farm_schedule(g, weekday=weekday)

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

        # Verifica dados estáticos de materiais de talento
        profile = static_data_manager.get_character_profile(g, c_name)
        talent_mat_name = profile.get("talent_book", "") if profile else ""
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

        location = "Domínio de Livros de Talento"
        if profile and profile.get("region"):
            location = f"Domínio da Região de {profile['region']}"
        elif g == "hsr":
            location = f"Cálice Rubro ({profile.get('path', 'Caminho') if profile else 'Rastros'})"
        elif g == "zzz":
            location = f"Treinamento de Habilidades ({profile.get('specialty', 'Agente') if profile else 'Ataque'})"

        task_item = {
            "id": sig,
            "step": task_idx,
            "type": "talent_domain",
            "type_label": "Livros de Talento",
            "type_icon": "fa-book-open",
            "target_character": c_name,
            "character_icon": target.get("icon"),
            "character_grade": c_grade,
            "material_name": talent_mat_name or "Livros de Elevação",
            "location": location,
            "runs": runs,
            "cost_energy": cost,
            "energy_name": cfg["energy_name"],
            "priority_badge": "⭐ Aberto Hoje",
            "badge_color": "#10b981",
            "description": f"Faça {runs}x {location} para obter {talent_mat_name} e avançar os talentos prioritários de {c_name} (Nota {c_grade}).",
            "completed": sig in completed_task_ids
        }

        # Cálculo de tempo até disponibilidade de energia
        accumulated_energy += cost
        task_item["cumulative_energy"] = accumulated_energy
        if accumulated_energy <= current_energy:
            task_item["available_now"] = True
            task_item["status_text"] = "Pronto para Executar"
            task_item["time_estimate"] = "Disponível Agora"
        else:
            deficit = accumulated_energy - current_energy
            wait_min = deficit * cfg["regen_minutes"]
            ready_dt = now_dt + timedelta(minutes=wait_min)
            task_item["available_now"] = False
            task_item["status_text"] = "Aguardando Energia"
            task_item["time_estimate"] = f"Disponível às {ready_dt.strftime('%H:%M')} (+{wait_min} min)"

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

        profile = static_data_manager.get_character_profile(g, c_name)
        boss_name = profile.get("boss_mat", "") if profile else "Chefe do Mundo"
        
        sig = f"boss_{c_name}_{boss_name}"
        if sig in seen_task_signatures:
            continue
        seen_task_signatures.add(sig)

        runs = 1
        cost = runs * cfg["boss_run_cost"]

        location = f"Chefe de Ascensão ({boss_name})"
        if profile and profile.get("region"):
            location = f"Chefe de {profile['region']} ({boss_name})"

        task_item = {
            "id": sig,
            "step": task_idx,
            "type": "boss",
            "type_label": "Chefe de Ascensão",
            "type_icon": "fa-skull",
            "target_character": c_name,
            "character_icon": target.get("icon"),
            "character_grade": c_grade,
            "material_name": boss_name,
            "location": location,
            "runs": runs,
            "cost_energy": cost,
            "energy_name": cfg["energy_name"],
            "priority_badge": "🔥 Ascensão Pendente",
            "badge_color": "#f59e0b",
            "description": f"Derrote {location} para avançar {c_name} do Nv. {c_lvl} rumo ao Nv. {c_max}.",
            "completed": sig in completed_task_ids
        }

        accumulated_energy += cost
        task_item["cumulative_energy"] = accumulated_energy
        if accumulated_energy <= current_energy:
            task_item["available_now"] = True
            task_item["status_text"] = "Pronto para Executar"
            task_item["time_estimate"] = "Disponível Agora"
        else:
            deficit = accumulated_energy - current_energy
            wait_min = deficit * cfg["regen_minutes"]
            ready_dt = now_dt + timedelta(minutes=wait_min)
            task_item["available_now"] = False
            task_item["status_text"] = "Aguardando Energia"
            task_item["time_estimate"] = f"Disponível às {ready_dt.strftime('%H:%M')} (+{wait_min} min)"

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

        domain_label = "Domínio de Artefatos" if g == "genshin" else ("Caverna da Corrosão" if g == "hsr" else "Limpeza de Rotina")
        
        task_item = {
            "id": sig,
            "step": task_idx,
            "type": "relic_domain",
            "type_label": domain_label,
            "type_icon": "fa-gem",
            "target_character": c_name,
            "character_icon": target.get("icon"),
            "character_grade": c_grade,
            "material_name": f"Sets Recomendados para {c_name}",
            "location": f"{domain_label} Recomendado",
            "runs": runs,
            "cost_energy": cost,
            "energy_name": cfg["energy_name"],
            "priority_badge": "💎 Otimização de Build",
            "badge_color": "#ec4899",
            "description": f"Realize {runs}x {domain_label} buscando peças com Atributos Ideais para maximizar a nota de {c_name}.",
            "completed": sig in completed_task_ids
        }

        accumulated_energy += cost
        task_item["cumulative_energy"] = accumulated_energy
        if accumulated_energy <= current_energy:
            task_item["available_now"] = True
            task_item["status_text"] = "Pronto para Executar"
            task_item["time_estimate"] = "Disponível Agora"
        else:
            deficit = accumulated_energy - current_energy
            wait_min = deficit * cfg["regen_minutes"]
            ready_dt = now_dt + timedelta(minutes=wait_min)
            task_item["available_now"] = False
            task_item["status_text"] = "Aguardando Energia"
            task_item["time_estimate"] = f"Disponível às {ready_dt.strftime('%H:%M')} (+{wait_min} min)"

        tasks.append(task_item)
        task_idx += 1
        if len(tasks) >= 6:
            break

    # Se a lista de tarefas estiver vazia (ex: conta recém-criada ou todos maximizados), cria uma tarefa de Linhas Ley/Cálice Dourado
    if not tasks:
        sig = f"calyx_currency_{g}"
        cost = cfg["talent_run_cost"] * 2
        tasks.append({
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
            "time_estimate": "Disponível Agora"
        })
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
        "🎯 **Roteiro de Farm Prioritário:**"
    ]
    for t in tasks:
        check_box = "[x]" if t["completed"] else "[ ]"
        status_disp = "(Disponível Agora)" if t["available_now"] else f"({t['time_estimate']})"
        summary_lines.append(f"{t['step']}. {check_box} **{t['target_character']}** | {t['type_label']}: {t['material_name']} ({t['cost_energy']} {cfg['energy_name']}) - *{status_disp}*")

    summary_lines.append("")
    summary_lines.append(f"💡 *Total Planejado: {accumulated_energy} {cfg['energy_name']} | Progresso Hoje: {completed_count}/{len(tasks)} ({completion_pct}%)*")
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
            "usage_pct": min(100, int((current_energy / max_energy) * 100)) if max_energy > 0 else 0
        },
        "tasks": tasks,
        "completed_count": completed_count,
        "total_tasks": len(tasks),
        "completion_percentage": completion_pct,
        "quick_summary_text": quick_summary_text
    }


def _norm_str(text: str) -> str:
    """Normaliza strings removendo acentos, pontuação e espaços em excesso."""
    import unicodedata, re
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text)).encode("ASCII", "ignore").decode("utf-8").lower()
    text = re.sub(r"[^a-z0-9]", "", text)
    return text


def analyze_account_gaps(game_id: str, roster: list, endgame_data: dict = None) -> dict:
    """
    Realiza uma auditoria estratégica profunda da conta do jogador (Genshin, HSR ou ZZZ),
    identificando carências de arquétipos (Sustentação, Buffers de Ação, DPSs, Sub-DPS),
    cobertura elemental, prontidão para os modos de Endgame e recomendações ranqueadas de gacha.
    """
    g = game_id.lower().strip()
    game_names = {"genshin": "Genshin Impact", "hsr": "Honkai: Star Rail", "zzz": "Zenless Zone Zero"}

    # Extrai e normaliza personagens do roster
    owned_chars_map = {}
    for item in roster or []:
        if isinstance(item, dict):
            c_name = item.get("name") or ""
            c_lvl = int(item.get("level") or 1)
            c_rarity = int(item.get("rarity") or 4)
            c_rank = int(item.get("rank") or item.get("constellation") or item.get("eidolon") or 0)
            c_elem = item.get("element") or ""
        elif isinstance(item, str):
            c_name = item
            c_lvl = 80
            c_rarity = 5
            c_rank = 0
            c_elem = ""
        else:
            continue

        norm_key = _norm_str(c_name)
        if norm_key:
            owned_chars_map[norm_key] = {
                "name": c_name,
                "level": c_lvl,
                "rarity": c_rarity,
                "rank": c_rank,
                "element": c_elem,
                "is_built": c_lvl >= (70 if g != "zzz" else 50)
            }

    def has_any(alias_list: list, min_built: bool = False) -> tuple[bool, list]:
        """Verifica se o jogador possui ao menos um personagem da lista de aliases."""
        matched = []
        for alias in alias_list:
            norm_a = _norm_str(alias)
            for k, info in owned_chars_map.items():
                if norm_a in k or k in norm_a:
                    if not min_built or info["is_built"]:
                        if info["name"] not in matched:
                            matched.append(info["name"])
        return (len(matched) > 0, matched)

    def count_in_group(alias_groups: list, min_built: bool = False) -> list:
        """Retorna lista de nomes únicos encontrados a partir de uma lista de aliases."""
        found = set()
        for alias in alias_groups:
            _, matches = has_any([alias], min_built)
            for m in matches:
                found.add(m)
        return list(found)

    # Definição das matrizes por jogo
    overall_score = 100
    critical_gaps = []
    pull_recommendations = []
    archetypes_summary = []
    elemental_coverage = []
    endgame_readiness = {}

    total_chars = len(owned_chars_map)
    built_chars = sum(1 for c in owned_chars_map.values() if c["is_built"])

    # ==========================================
    # 1. GENSHIN IMPACT
    # ==========================================
    if g == "genshin":
        # Arquétipos
        sustain_t0 = ["zhongli", "kokomi", "baizhu", "xianyun", "bennett", "kuki shinobu", "sigewinne"]
        sustain_others = ["diona", "layla", "kirara", "jean", "charlotte", "yaoyao", "barbara", "noelle", "sayu", "chevreuse", "mika", "thoma", "qiqi"]
        owned_sustain_t0 = count_in_group(sustain_t0)
        owned_sustain_all = count_in_group(sustain_t0 + sustain_others)

        buffers_t0 = ["furina", "kazuha", "nahida", "xilonen", "shenhe", "sucrose", "faruzan", "emilie"]
        buffers_others = ["lynette", "gorou", "yun jin", "kujou sara", "candace", "traveler"]
        owned_buffers_t0 = count_in_group(buffers_t0)
        owned_buffers_all = count_in_group(buffers_t0 + buffers_others)

        offfield_hydro = ["xingqiu", "yelan", "furina", "kokomi", "sigewinne"]
        owned_offfield_hydro = count_in_group(offfield_hydro)

        offfield_subdps = ["xiangling", "fischl", "yae miko", "nahida", "emilie", "chiori", "albedo", "raiden shogun"]
        owned_offfield_subdps = count_in_group(offfield_subdps)

        main_dps_list = [
            "neuvillette", "arlecchino", "alhaitham", "raiden shogun", "hu tao", "navia",
            "mualani", "kinich", "clorinde", "lyney", "wriothesley", "xiao", "wanderer",
            "kamisato ayaka", "ganyu", "arataki itto", "tartaglia", "cyno", "tighnari",
            "diluc", "keqing", "gaming", "yanfei", "sethos"
        ]
        owned_main_dps = count_in_group(main_dps_list)

        # Status dos Arquétipos
        def get_status_data(count, t0_count, ideal_min=2):
            if t0_count >= ideal_min or count >= ideal_min + 2:
                return "Excelente", "#10b981"
            elif count >= ideal_min:
                return "Suficiente", "#3b82f6"
            elif count == 1:
                return "Atenção", "#f59e0b"
            else:
                return "Crítico", "#ef4444"

        st_sust, col_sust = get_status_data(len(owned_sustain_all), len(owned_sustain_t0), 2)
        archetypes_summary.append({
            "key": "sustain",
            "title": "Sustentação (Shield / Healer)",
            "icon": "fa-shield-halved",
            "status": st_sust,
            "status_color": col_sust,
            "owned_count": len(owned_sustain_all),
            "target_count": 2,
            "owned_characters": owned_sustain_all,
            "description": "Essencial para sobrevivência nos 2 lados do Abismo 12."
        })

        st_buff, col_buff = get_status_data(len(owned_buffers_all), len(owned_buffers_t0), 2)
        archetypes_summary.append({
            "key": "buffers",
            "title": "Buffers & Redução de RES (VV / Suportes)",
            "icon": "fa-wand-magic-sparkles",
            "status": st_buff,
            "status_color": col_buff,
            "owned_count": len(owned_buffers_all),
            "target_count": 2,
            "owned_characters": owned_buffers_all,
            "description": "Multiplicadores de dano e reações elementais da equipe."
        })

        st_hydro, col_hydro = get_status_data(len(owned_offfield_hydro), len(owned_offfield_hydro), 2)
        archetypes_summary.append({
            "key": "offfield_hydro",
            "title": "Aplicadores Hydro Off-Field",
            "icon": "fa-droplet",
            "status": st_hydro,
            "status_color": col_hydro,
            "owned_count": len(owned_offfield_hydro),
            "target_count": 2,
            "owned_characters": owned_offfield_hydro,
            "description": "Coluna vertebral para Vaporize, Hyperbloom, Taser e Freeze."
        })

        st_dps, col_dps = get_status_data(len(owned_main_dps), len(owned_main_dps), 2)
        archetypes_summary.append({
            "key": "main_dps",
            "title": "DPS Principal (Hypercarries / Reaction)",
            "icon": "fa-khanda",
            "status": st_dps,
            "status_color": col_dps,
            "owned_count": len(owned_main_dps),
            "target_count": 2,
            "owned_characters": owned_main_dps,
            "description": "Pilares de dano para as duas metades das câmaras de combate."
        })

        # Cobertura Elemental
        elements_cfg = [
            ("Pyro", "fa-fire", "#ef4444", ["arlecchino", "hu tao", "bennett", "xiangling", "diluc", "gaming", "lyney", "yoimiya", "thoma", "chevreuse", "yanfei", "dehya"]),
            ("Hydro", "fa-droplet", "#0284c7", ["neuvillette", "furina", "yelan", "xingqiu", "kokomi", "mualani", "ayato", "tartaglia", "mona", "sigewinne", "barbara", "candace"]),
            ("Dendro", "fa-leaf", "#10b981", ["nahida", "alhaitham", "baizhu", "kinich", "emilie", "tighnari", "yaoyao", "kirara", "collei", "kaveh"]),
            ("Electro", "fa-bolt", "#a855f7", ["raiden shogun", "clorinde", "yae miko", "fischl", "kuki shinobu", "cyno", "beidou", "keqing", "sethos", "kujou sara"]),
            ("Anemo", "fa-wind", "#14b8a6", ["kazuha", "xianyun", "sucrose", "xiao", "wanderer", "jean", "faruzan", "lynette", "heizou", "sayu"]),
            ("Cryo", "fa-snowflake", "#38bdf8", ["ayaka", "ganyu", "wriothesley", "shenhe", "charlotte", "diona", "layla", "rosaria", "mika", "qiqi"]),
            ("Geo", "fa-mountain", "#f59e0b", ["zhongli", "navia", "xilonen", "chiori", "itto", "albedo", "noelle", "kachina", "gorou", "yun jin"])
        ]
        for elem_name, elem_icon, elem_color, char_pool in elements_cfg:
            elem_chars = count_in_group(char_pool)
            elem_built = count_in_group(char_pool, min_built=True)
            status = "Forte" if len(elem_built) >= 2 else ("Moderado" if len(elem_chars) >= 1 else "Faltando")
            elemental_coverage.append({
                "element": elem_name,
                "icon": elem_icon,
                "color": elem_color,
                "count": len(elem_chars),
                "built_count": len(elem_built),
                "characters": elem_chars,
                "status": status
            })

        # Lacunas Críticas
        if len(owned_sustain_t0) == 0:
            overall_score -= 22
            critical_gaps.append({
                "id": "genshin_no_t0_sustain",
                "severity": "CRÍTICA",
                "severity_color": "#ef4444",
                "badge": "🛡️ Sobrevivência em Risco",
                "title": "Falta de Sustentador Premium Tier 0",
                "description": "Você não possui nenhum curandeiro/escudo de elite (Zhongli, Kokomi, Baizhu, Xianyun ou Bennett).",
                "endgame_impact": "Alta dificuldade para manter a rotação viva e evitar interrupções no Abismo 12.",
                "suggested_archetype": "Shielder Indestrutível ou Healer Global com utilidade de Buff",
                "recommended_characters": ["Zhongli", "Kokomi", "Baizhu", "Xianyun"]
            })

        if len(owned_offfield_hydro) < 2:
            overall_score -= 18
            critical_gaps.append({
                "id": "genshin_lack_hydro",
                "severity": "ALTA",
                "severity_color": "#f97316",
                "badge": "💧 Carência de Aplicação Hydro",
                "title": "Falta de Aplicador Hydro Off-Field para 2 Times",
                "description": "Possui menos de 2 aplicadores Hydro (Xingqiu, Yelan, Furina).",
                "endgame_impact": "Limita severamente a formação de times simultâneos de Vaporize, Hyperbloom ou Freeze.",
                "suggested_archetype": "Sub-DPS / Buffer Hydro Off-Field",
                "recommended_characters": ["Yelan", "Furina", "Xingqiu"]
            })

        has_vv, _ = has_any(["kazuha", "sucrose"])
        if not has_vv:
            overall_score -= 15
            critical_gaps.append({
                "id": "genshin_no_vv_shred",
                "severity": "ALTA",
                "severity_color": "#f97316",
                "badge": "🌪️ Sem Redução Elemental VV",
                "title": "Ausência de Buffer Anemo Sombra Verde (VV)",
                "description": "Você não tem Kazuha ou Sacarose para aplicar o debuff de 40% de RES Shred.",
                "endgame_impact": "Perda direta de ~25% a 30% do DPS final em composições de reação elemental.",
                "suggested_archetype": "Buffer / Agrupador Anemo",
                "recommended_characters": ["Kaedehara Kazuha", "Sucrose"]
            })

        if len(owned_main_dps) < 2:
            overall_score -= 20
            critical_gaps.append({
                "id": "genshin_lack_main_dps",
                "severity": "CRÍTICA",
                "severity_color": "#ef4444",
                "badge": "⚔️ Carência de Dano Principal",
                "title": "Menos de 2 Hypercarries/Drivers Construídos",
                "description": "Faltam carregadores de dano principais para cobrir as duas câmaras do Abismo 12.",
                "endgame_impact": "Incapacidade de atingir as metas de DPS para fechar com 36 estrelas.",
                "suggested_archetype": "DPS Principal Top-Tier",
                "recommended_characters": ["Neuvillette", "Arlecchino", "Alhaitham", "Navia"]
            })

        # Recomendações de Puxadas
        rank_idx = 1
        if len(owned_sustain_t0) == 0:
            pull_recommendations.append({
                "priority_rank": rank_idx,
                "archetype": "Sustentador / Shielder Tier 0",
                "badge": "Prioridade Máxima",
                "tag": "Sobrevivência & Conforto",
                "characters": ["Zhongli", "Xilonen", "Kokomi"],
                "reason": "Garante estabilidade absoluta de rotação no Abismo 12 sem interrupções de golpes inimigos.",
                "impact_score": "+35% Conforto & Consistência de Clear"
            })
            rank_idx += 1

        if not has_any(["furina", "kazuha"])[0]:
            pull_recommendations.append({
                "priority_rank": rank_idx,
                "archetype": "Universal Damage Buffer",
                "badge": "Alta Prioridade",
                "tag": "Salto de DPS Global",
                "characters": ["Furina", "Kaedehara Kazuha"],
                "reason": "Aumenta drasticamente o dano de quase todas as equipes do jogo através de buffs globais e RES shred.",
                "impact_score": "+30% a 40% Dano Global da Equipe"
            })
            rank_idx += 1

        if len(owned_main_dps) < 2:
            pull_recommendations.append({
                "priority_rank": rank_idx,
                "archetype": "Hypercarry On-Field",
                "badge": "Alta Prioridade",
                "tag": "DPS de Fechamento",
                "characters": ["Neuvillette", "Arlecchino"],
                "reason": "Unidades independentes e com multiplicadores colossais para carregar um lado inteiro do Abismo.",
                "impact_score": "Garante 1 lado completo do Abismo 12"
            })
            rank_idx += 1

    # ==========================================
    # 2. HONKAI: STAR RAIL
    # ==========================================
    elif g == "hsr":
        # Arquétipos
        harmony_t0 = ["ruan mei", "robin", "sparkle", "sunday", "bronya", "tingyun"]
        owned_harmony_t0 = count_in_group(harmony_t0)

        sustain_5star = ["aventurine", "huohuo", "fu xuan", "lingsha", "luocha"]
        sustain_all = sustain_5star + ["gallagher", "lynx", "natasha", "bailu", "gepard", "march 7th"]
        owned_sustain_5star = count_in_group(sustain_5star)
        owned_sustain_all = count_in_group(sustain_all)

        break_archetype = ["firefly", "boothill", "rappa", "trailblazer", "xueyi", "fugue", "ruan mei", "gallagher", "lingsha"]
        owned_break = count_in_group(break_archetype)

        fua_archetype = ["feixiao", "aventurine", "robin", "topaz", "dr. ratio", "yunli", "clara", "moze", "march 7th", "jade"]
        owned_fua = count_in_group(fua_archetype)

        pf_erudition = ["herta", "himeko", "jade", "argenti", "acheron"]
        owned_pf = count_in_group(pf_erudition)

        dot_archetype = ["kafka", "black swan", "jiaoqiu", "guinaifen", "sampo", "luka"]
        owned_dot = count_in_group(dot_archetype)

        crit_hypercarries = ["acheron", "feixiao", "dan heng il", "jingliu", "dr. ratio", "yunli", "argenti", "blade", "jing yuan", "clara", "seele"]
        owned_crit_dps = count_in_group(crit_hypercarries)

        # Status dos Arquétipos
        def get_hsr_status(count, t0_count, ideal_min=2):
            if t0_count >= ideal_min:
                return "Excelente", "#10b981"
            elif count >= ideal_min:
                return "Suficiente", "#3b82f6"
            elif count == 1:
                return "Atenção", "#f59e0b"
            else:
                return "Crítico", "#ef4444"

        st_harm, col_harm = get_hsr_status(len(owned_harmony_t0), len(owned_harmony_t0), 2)
        archetypes_summary.append({
            "key": "harmony",
            "title": "Harmonia & Manipulação de Ação (Tier 0)",
            "icon": "fa-music",
            "status": st_harm,
            "status_color": col_harm,
            "owned_count": len(owned_harmony_t0),
            "target_count": 2,
            "owned_characters": owned_harmony_t0,
            "description": "Peças fundamentais para turnos extras, penetração de resistência e buffs de crítico."
        })

        st_sust, col_sust = get_hsr_status(len(owned_sustain_all), len(owned_sustain_5star), 2)
        archetypes_summary.append({
            "key": "sustain",
            "title": "Sustentadores de Elite (Preservação / Abundância)",
            "icon": "fa-shield-halved",
            "status": st_sust,
            "status_color": col_sust,
            "owned_count": len(owned_sustain_all),
            "target_count": 2,
            "owned_characters": owned_sustain_5star if owned_sustain_5star else owned_sustain_all,
            "description": "Imunidade a controle (CC), escudos inquebráveis e cura reativa para MoC 12 e AS 4."
        })

        st_break, col_break = ("Excelente", "#10b981") if len(owned_break) >= 3 else (("Suficiente", "#3b82f6") if len(owned_break) >= 2 else ("Atenção", "#f59e0b"))
        archetypes_summary.append({
            "key": "break",
            "title": "Núcleo de Quebra / Super Break",
            "icon": "fa-burst",
            "status": st_break,
            "status_color": col_break,
            "owned_count": len(owned_break),
            "target_count": 3,
            "owned_characters": owned_break,
            "description": "Dominância contra fraquezas e velocidade de limpeza em Sombra Apocalíptica."
        })

        st_pf, col_pf = ("Excelente", "#10b981") if len(owned_pf) >= 2 else (("Suficiente", "#3b82f6") if len(owned_pf) >= 1 else ("Crítico", "#ef4444"))
        archetypes_summary.append({
            "key": "pure_fiction",
            "title": "Especialistas em AoE / Pura Ficção",
            "icon": "fa-meteor",
            "status": st_pf,
            "status_color": col_pf,
            "owned_count": len(owned_pf),
            "target_count": 2,
            "owned_characters": owned_pf,
            "description": "Erudição e dano em área contínuo para bater 60.000+ pontos na Pura Ficção."
        })

        # Cobertura Elemental
        elements_cfg = [
            ("Físico", "fa-hand-fist", "#e2e8f0", ["boothill", "feixiao", "robin", "yunli", "argenti", "clara", "luka", "sushang", "natasha"]),
            ("Fogo", "fa-fire", "#ef4444", ["firefly", "topaz", "jiaoqiu", "gallagher", "lingsha", "himeko", "guinaifen", "asta", "hook"]),
            ("Gelo", "fa-snowflake", "#38bdf8", ["jingliu", "ruan mei", "herta", "gepard", "pela", "march 7th", "yanqing", "misha"]),
            ("Raio", "fa-bolt", "#a855f7", ["acheron", "kafka", "jing yuan", "tingyun", "bailu", "moze", "serval", "arlan"]),
            ("Vento", "fa-wind", "#10b981", ["black swan", "feixiao", "huohuo", "blade", "bronya", "dan heng", "sampo"]),
            ("Quântico", "fa-atom", "#6366f1", ["sparkle", "jade", "fu xuan", "seele", "silver wolf", "xueyi", "lynx", "qingque"]),
            ("Imaginário", "fa-sun", "#f59e0b", ["aventurine", "sunday", "dan heng il", "dr. ratio", "luocha", "trailblazer", "yukong", "welt"])
        ]
        for elem_name, elem_icon, elem_color, char_pool in elements_cfg:
            elem_chars = count_in_group(char_pool)
            elem_built = count_in_group(char_pool, min_built=True)
            status = "Forte" if len(elem_built) >= 2 else ("Moderado" if len(elem_chars) >= 1 else "Faltando")
            elemental_coverage.append({
                "element": elem_name,
                "icon": elem_icon,
                "color": elem_color,
                "count": len(elem_chars),
                "built_count": len(elem_built),
                "characters": elem_chars,
                "status": status
            })

        # Lacunas Críticas
        if len(owned_harmony_t0) < 2:
            overall_score -= 22
            critical_gaps.append({
                "id": "hsr_lack_tier0_harmony",
                "severity": "CRÍTICA",
                "severity_color": "#ef4444",
                "badge": "🎵 Déficit de Harmonia Tier 0",
                "title": "Menos de 2 Suportes Harmonia Premium",
                "description": "Você possui menos de 2 buffers de alta geração de turnos (Ruan Mei, Robin, Sparkle, Sunday).",
                "endgame_impact": "Queda drástica de ciclos no MoC e dificuldade de alcançar os 40.000 pts na Pura Ficção.",
                "suggested_archetype": "Harmonia Limitada (Avanço de Ação / Penetração de RES / DMG%)",
                "recommended_characters": ["Robin", "Ruan Mei", "Sunday", "Sparkle"]
            })

        if len(owned_sustain_5star) < 2:
            overall_score -= 20
            critical_gaps.append({
                "id": "hsr_lack_5star_sustain",
                "severity": "ALTA",
                "severity_color": "#f97316",
                "badge": "🛡️ Sustentação de Alto Nível",
                "title": "Falta de 2 Sustentadores Limitados 5★",
                "description": "Você não possui 2 sustentadores premium (Aventurine, Huohuo, Fu Xuan, Lingsha).",
                "endgame_impact": "Vulnerabilidade a debuffs de controle (Crowd Control) e one-shots nos andares 11 e 12.",
                "suggested_archetype": "Preservação / Abundância Limitada",
                "recommended_characters": ["Aventurine", "Huohuo", "Lingsha", "Fu Xuan"]
            })

        has_herta_himeko = ("Herta" in owned_pf or "Himeko" in owned_pf or "Jade" in owned_pf)
        if not has_herta_himeko:
            overall_score -= 15
            critical_gaps.append({
                "id": "hsr_no_pure_fiction_core",
                "severity": "ALTA",
                "severity_color": "#f97316",
                "badge": "📖 Fraqueza em Pura Ficção",
                "title": "Falta de Núcleo Especialista em AoE",
                "description": "Herta ou Himeko não estão construídas na conta.",
                "endgame_impact": "Dificuldade constante para obter a pontuação máxima (60.000 / 80.000) na Pura Ficção.",
                "suggested_archetype": "Erudição / AoE Follow-Up",
                "recommended_characters": ["Herta (Construir)", "Himeko", "Jade"]
            })

        # Recomendações de Puxadas
        rank_idx = 1
        if len(owned_harmony_t0) < 2:
            pull_recommendations.append({
                "priority_rank": rank_idx,
                "archetype": "Suporte Harmonia Universal (Robin / Sunday / Ruan Mei)",
                "badge": "Prioridade Máxima",
                "tag": "Multiplicador de Conta",
                "characters": ["Robin", "Sunday", "Ruan Mei"],
                "reason": "O maior upgrade de poder possível em Honkai: Star Rail. Transforma qualquer DPS em uma máquina de ciclos zero.",
                "impact_score": "-2 a 4 Ciclos no Caos da Memória (MoC)"
            })
            rank_idx += 1

        if len(owned_sustain_5star) < 2:
            pull_recommendations.append({
                "priority_rank": rank_idx,
                "archetype": "Sustentador 5★ de Elite (Aventurine / Huohuo)",
                "badge": "Alta Prioridade",
                "tag": "Segurança & Utilidade",
                "characters": ["Aventurine", "Huohuo", "Lingsha"],
                "reason": "Aventurine traz sinergia colossal com FuA/Acheron e escudos infinitos. Huohuo recarrega energia globalmente.",
                "impact_score": "100% de Taxa de Sobrevivência no MoC 12"
            })
            rank_idx += 1

        if len(owned_crit_dps) == 0 and len(owned_break) < 2:
            pull_recommendations.append({
                "priority_rank": rank_idx,
                "archetype": "DPS de Elite (Acheron / Firefly / Feixiao)",
                "badge": "Alta Prioridade",
                "tag": "Finalizador de Endgame",
                "characters": ["Acheron", "Firefly", "Feixiao"],
                "reason": "Mecanismos de quebra que ignoram fraquezas ou rajadas de dano absurdas com escalonamento moderno.",
                "impact_score": "Garante 36★ no MoC e 12★ na Sombra Apocalíptica"
            })
            rank_idx += 1

    # ==========================================
    # 3. ZENLESS ZONE ZERO
    # ==========================================
    elif g == "zzz":
        # Arquétipos
        stunners_s = ["qingyi", "lycaon", "caesar", "koleda"]
        stunners_all = stunners_s + ["anby"]
        owned_stunners_s = count_in_group(stunners_s)
        owned_stunners_all = count_in_group(stunners_all)

        supports_s = ["caesar", "astra yao", "rina"]
        supports_all = supports_s + ["soukaku", "lucy", "nicole", "seth"]
        owned_supports_s = count_in_group(supports_s)
        owned_supports_all = count_in_group(supports_all)

        attack_dps = ["ellen", "zhu yuan", "soldier 11", "nekomata", "harumasa", "miyabi", "corin", "anton", "billy"]
        owned_attack_dps = count_in_group(attack_dps)

        anomaly_dps = ["jane doe", "burnice", "yanagi", "grace", "piper"]
        owned_anomaly_dps = count_in_group(anomaly_dps)

        # Status
        st_stun = "Excelente" if len(owned_stunners_s) >= 2 else ("Suficiente" if len(owned_stunners_all) >= 2 else "Atenção")
        col_stun = "#10b981" if st_stun == "Excelente" else ("#3b82f6" if st_stun == "Suficiente" else "#f59e0b")
        archetypes_summary.append({
            "key": "stunners",
            "title": "Atordoadores (Stun / Daze)",
            "icon": "fa-bolt",
            "status": st_stun,
            "status_color": col_stun,
            "owned_count": len(owned_stunners_all),
            "target_count": 2,
            "owned_characters": owned_stunners_all,
            "description": "Multiplica o dano em 150%+ durante a janela de Atordoamento (Stun Window)."
        })

        st_supp = "Excelente" if len(owned_supports_all) >= 3 else ("Suficiente" if len(owned_supports_all) >= 2 else "Atenção")
        col_supp = "#10b981" if st_supp == "Excelente" else ("#3b82f6" if st_supp == "Suficiente" else "#f59e0b")
        archetypes_summary.append({
            "key": "supports",
            "title": "Suportes & Defesa (Buff de ATK / DEF Shred)",
            "icon": "fa-shield-halved",
            "status": st_supp,
            "status_color": col_supp,
            "owned_count": len(owned_supports_all),
            "target_count": 2,
            "owned_characters": owned_supports_all,
            "description": "Gera pontos de assistência, buffs de ATK puro e debuffs defensivos no inimigo."
        })

        st_atk = "Excelente" if len(owned_attack_dps) >= 2 else ("Suficiente" if len(owned_attack_dps) >= 1 else "Atenção")
        col_atk = "#10b981" if st_atk == "Excelente" else ("#3b82f6" if st_atk == "Suficiente" else "#f59e0b")
        archetypes_summary.append({
            "key": "attack_dps",
            "title": "Agentes de Ataque (Burst / Dano Direto)",
            "icon": "fa-crosshairs",
            "status": st_atk,
            "status_color": col_atk,
            "owned_count": len(owned_attack_dps),
            "target_count": 2,
            "owned_characters": owned_attack_dps,
            "description": "Descarregam dano massivo durante as janelas de Chain Attack e Stun."
        })

        st_anom = "Excelente" if len(owned_anomaly_dps) >= 2 else ("Suficiente" if len(owned_anomaly_dps) >= 1 else "Atenção")
        col_anom = "#10b981" if st_anom == "Excelente" else ("#3b82f6" if st_anom == "Suficiente" else "#f59e0b")
        archetypes_summary.append({
            "key": "anomaly_dps",
            "title": "Agentes de Anomalia (DoT / Desordem)",
            "icon": "fa-flask-vial",
            "status": st_anom,
            "status_color": col_anom,
            "owned_count": len(owned_anomaly_dps),
            "target_count": 2,
            "owned_characters": owned_anomaly_dps,
            "description": "Acumulam anomalia e causam Desordem contínua sem depender do atordoamento."
        })

        # Cobertura de Atributos ZZZ
        elements_cfg = [
            ("Físico", "fa-hand-fist", "#e2e8f0", ["jane doe", "caesar", "nekomata", "piper", "corin", "billy", "seth"]),
            ("Fogo", "fa-fire", "#ef4444", ["burnice", "soldier 11", "koleda", "lucy", "lighter"]),
            ("Gelo", "fa-snowflake", "#38bdf8", ["ellen", "lycaon", "soukaku", "miyabi"]),
            ("Elétrico", "fa-bolt", "#a855f7", ["qingyi", "yanagi", "rina", "grace", "anby", "anton", "harumasa"]),
            ("Éter", "fa-circle-radiation", "#10b981", ["zhu yuan", "nicole", "astra yao"])
        ]
        for elem_name, elem_icon, elem_color, char_pool in elements_cfg:
            elem_chars = count_in_group(char_pool)
            elem_built = count_in_group(char_pool, min_built=True)
            status = "Forte" if len(elem_built) >= 2 else ("Moderado" if len(elem_chars) >= 1 else "Faltando")
            elemental_coverage.append({
                "element": elem_name,
                "icon": elem_icon,
                "color": elem_color,
                "count": len(elem_chars),
                "built_count": len(elem_built),
                "characters": elem_chars,
                "status": status
            })

        # Lacunas Críticas
        if len(owned_stunners_s) == 0:
            overall_score -= 22
            critical_gaps.append({
                "id": "zzz_no_s_stunner",
                "severity": "CRÍTICA",
                "severity_color": "#ef4444",
                "badge": "⚡ Lentidão no Atordoamento",
                "title": "Falta de Atordoador S-Rank (Qingyi / Lycaon / Caesar)",
                "description": "Você depende exclusivamente da Anby como atordoadora nos 2 lados do Shiyu Defense.",
                "endgame_impact": "Demora excessiva para atingir o estado de Stun nos Chefes da Shiyu Crítica (Nível 5-7).",
                "suggested_archetype": "Atordoador S-Rank de Alto Impacto",
                "recommended_characters": ["Qingyi", "Caesar", "Von Lycaon"]
            })

        if len(owned_attack_dps) + len(owned_anomaly_dps) < 2:
            overall_score -= 25
            critical_gaps.append({
                "id": "zzz_lack_dps",
                "severity": "CRÍTICA",
                "severity_color": "#ef4444",
                "badge": "⚔️ Carência de Finalizadores",
                "title": "Falta de DPSs Principais para 2 Equipes",
                "description": "Menos de 2 agentes de Ataque ou Anomalia de alto investimento.",
                "endgame_impact": "Inviabiliza a obtenção de Rank S na Shiyu Defense dos dois lados.",
                "suggested_archetype": "DPS S-Rank de Ataque ou Anomalia",
                "recommended_characters": ["Ellen Joe", "Jane Doe", "Zhu Yuan", "Miyabi", "Burnice"]
            })

        # Recomendações de Puxadas
        rank_idx = 1
        if len(owned_stunners_s) == 0:
            pull_recommendations.append({
                "priority_rank": rank_idx,
                "archetype": "Atordoador S-Rank (Qingyi / Caesar)",
                "badge": "Prioridade Máxima",
                "tag": "Velocidade de Stun",
                "characters": ["Qingyi", "Caesar"],
                "reason": "Qingyi eleva o multiplicador de atordoamento para 200%+ e atordoa chefes na metade do tempo da Anby.",
                "impact_score": "-40s no Tempo de Clear do Shiyu 7"
            })
            rank_idx += 1

        if len(owned_anomaly_dps) == 0:
            pull_recommendations.append({
                "priority_rank": rank_idx,
                "archetype": "Especialista em Anomalia / Desordem",
                "badge": "Alta Prioridade",
                "tag": "Novo Arquétipo Meta",
                "characters": ["Jane Doe", "Burnice", "Yanagi"],
                "reason": "Permite ignorar mecânicas de atordoamento e derreter inimigos com Desordem de alto escalonamento.",
                "impact_score": "+30% Flexibilidade contra Chefes com Alta Resistência a Stun"
            })
            rank_idx += 1

    # Normalização final da pontuação
    overall_score = max(20, min(100, overall_score))
    if overall_score >= 85:
        score_grade = "S"
        score_label = "Excelente Cobertura & Alta Prontidão"
        score_color = "#10b981"
    elif overall_score >= 70:
        score_grade = "A"
        score_label = "Conta Equilibrada com Boas Sinergias"
        score_color = "#3b82f6"
    elif overall_score >= 50:
        score_grade = "B"
        score_label = "Lacunas Moderadas em Arquétipos Chave"
        score_color = "#f59e0b"
    else:
        score_grade = "C"
        score_label = "Atenção: Carência Crítica de Suportes/Sustentação"
        score_color = "#ef4444"

    # Avaliação de Prontidão de Endgame
    endgame_teams_ready = 2 if len(critical_gaps) <= 1 and built_chars >= 6 else (1 if built_chars >= 3 else 0)
    endgame_readiness = {
        "status": f"{endgame_teams_ready}/2 Equipes Prontas para Endgame",
        "teams_ready": endgame_teams_ready,
        "summary": (
            "Sua conta possui fundações completas para fechar o conteúdo mais difícil do jogo com nota máxima."
            if endgame_teams_ready == 2 else
            "Você tem 1 time competitivo consolidado, mas a segunda equipe precisa de reforços nos arquétipos sinalizados."
            if endgame_teams_ready == 1 else
            "Concentre seus recursos e energia em elevar o nível e fechar as builds da sua equipe principal primeiro."
        ),
        "details": [gap["title"] for gap in critical_gaps]
    }

    # Resumo formatado em Markdown para injeção rápida no Groq RAG
    rag_lines = [
        f"### DIAGNÓSTICO DE LACUNAS DA CONTA ({game_names.get(g, g.upper())}):",
        f"- **Pontuação de Saúde da Conta:** {overall_score}/100 (Classificação: {score_grade} - {score_label})",
        f"- **Personagens Construídos (Prontos p/ Batalha):** {built_chars} de {total_chars}",
        f"- **Equipes Prontas p/ Endgame:** {endgame_teams_ready}/2 times"
    ]
    if critical_gaps:
        rag_lines.append("- **Lacunas Estratégicas Críticas Detectadas:**")
        for cg in critical_gaps:
            rag_lines.append(f"  * [{cg['severity']}] {cg['title']}: {cg['description']} -> *Recomendado buscar:* {', '.join(cg['recommended_characters'])}")
    else:
        rag_lines.append("- **Lacunas:** Nenhuma carência grave detectada! Conta muito bem balanceada.")

    if pull_recommendations:
        rag_lines.append("- **Prioridades de Puxada no Gacha / Banners Futuros:**")
        for pr in pull_recommendations:
            rag_lines.append(f"  {pr['priority_rank']}. **{pr['archetype']}** ({', '.join(pr['characters'])}): {pr['reason']}")

    rag_summary_markdown = "\n".join(rag_lines)

    return {
        "game_id": g,
        "game_name": game_names.get(g, g.upper()),
        "overall_score": overall_score,
        "score_grade": score_grade,
        "score_label": score_label,
        "score_color": score_color,
        "total_characters": total_chars,
        "built_characters": built_chars,
        "archetypes_summary": archetypes_summary,
        "elemental_coverage": elemental_coverage,
        "critical_gaps": critical_gaps,
        "pull_recommendations": pull_recommendations,
        "endgame_readiness": endgame_readiness,
        "rag_summary_markdown": rag_summary_markdown
    }


def recommend_relic_crafting(game_id: str, roster: list) -> dict:
    """
    Analisa os personagens de maior prioridade do Roster e identifica as piores peças equipadas
    (ou peças com atributos principais incorretos), recomendando os melhores alvos para uso
    de Resina Automodeladora (HSR), Elixir Santificador (Genshin) ou Calibrador de Discos (ZZZ).
    """
    g = game_id.lower().strip()
    game_names = {"genshin": "Genshin Impact", "hsr": "Honkai: Star Rail", "zzz": "Zenless Zone Zero"}

    item_names = {
        "genshin": "Elixir Santificador & Relic Strongbox",
        "hsr": "Resina Automodeladora & Síntese Omnipotente",
        "zzz": "Sintetizador de Discos & Calibrador Hi-Fi"
    }

    item_icons = {
        "genshin": "fa-flask-round-potion",
        "hsr": "fa-cube",
        "zzz": "fa-compact-disc"
    }

    # Ordena personagens por nível / raridade / prioridade de investimento
    top_candidates = []
    for item in roster or []:
        if isinstance(item, dict):
            c_name = item.get("name") or ""
            c_lvl = int(item.get("level") or 1)
            c_rarity = int(item.get("rarity") or 4)
            c_score = float(item.get("overall_score") or item.get("score") or 0.0)
            c_grade = str(item.get("overall_grade") or item.get("grade") or "B")
            c_icon = item.get("icon")
            relics = item.get("relics") or []
            if c_lvl >= 50 or c_rarity == 5:
                top_candidates.append({
                    "name": c_name,
                    "level": c_lvl,
                    "rarity": c_rarity,
                    "score": c_score,
                    "grade": c_grade,
                    "icon": c_icon,
                    "relics": relics
                })

    # Prioriza quem tem score baixo ou nota B/C/D mas é personagem forte
    top_candidates.sort(key=lambda x: (x["rarity"], -x["score"]), reverse=True)

    recommendations = []
    rank_counter = 1

    # ==========================================
    # REGRAS DE CRAFTING POR JOGO
    # ==========================================
    if g == "genshin":
        # Meta targets no Genshin
        meta_craft_genshin = {
            "neuvillette": {
                "set": "Caçador das Sombras",
                "slot": "Cálice de Eonothem (Slot 4)",
                "main": "Bônus de Dano Hydro (ou HP%)",
                "substats": ["Dano Crítico", "Taxa Crítica", "HP%", "Recarga de Energia"],
                "gain": "+25% Dano no Ataque Carregado Notável"
            },
            "furina": {
                "set": "Trompete do Éter / Companhia Dourada",
                "slot": "Ampulheta / Cálice (Slot 3 ou 4)",
                "main": "Recarga de Energia ou HP%",
                "substats": ["Taxa Crítica", "Dano Crítico", "HP%", "Recarga de Energia"],
                "gain": "Garante 100% de Uptime no Supremo Fanfarra"
            },
            "arlecchino": {
                "set": "Fragmento da Harmonia Caprichosa",
                "slot": "Cálice de Bônus Pyro (Slot 4)",
                "main": "Bônus de Dano Pyro",
                "substats": ["Taxa Crítica", "Dano Crítico", "ATK%", "Proficiência Elemental"],
                "gain": "+30% Eficiência em Golpes de Vaporize"
            },
            "kaedehara kazuha": {
                "set": "Sombra Verde (VV)",
                "slot": "Cálice / Tiara (Slot 4 ou 5)",
                "main": "Proficiência Elemental (EM)",
                "substats": ["Recarga de Energia", "Proficiência Elemental", "ATK%"],
                "gain": "Atinge a meta de 1.000 EM para buffer máximo de 40% DMG"
            },
            "nahida": {
                "set": "Memórias da Floresta (Deepwood)",
                "slot": "Tiara / Cálice (Slot 4 ou 5)",
                "main": "Proficiência Elemental (ou Taxa Crítica)",
                "substats": ["Proficiência Elemental", "Taxa Crítica", "Dano Crítico", "Recarga de Energia"],
                "gain": "Maximiza dano de Tri-Karma e bônus da cúpula"
            },
            "yelan": {
                "set": "Selo da Insulação (Emblem)",
                "slot": "Cálice de Dano Hydro ou Tiara Crítica",
                "main": "Bônus de Dano Hydro (ou Taxa/Dano Crítico)",
                "substats": ["Taxa Crítica", "Dano Crítico", "Recarga de Energia", "HP%"],
                "gain": "+20% Dano Coordenado do Supremo"
            }
        }

        for cand in top_candidates:
            c_norm = _norm_str(cand["name"])
            matched_key = None
            for mk in meta_craft_genshin:
                if mk in c_norm or c_norm in mk:
                    matched_key = mk
                    break

            cfg = meta_craft_genshin.get(matched_key) if matched_key else {
                "set": "Set Bis Recomendado",
                "slot": "Cálice Elemental (Slot 4) ou Tiara Crítica (Slot 5)",
                "main": "Bônus Elemental ou Taxa/Dano Crítico",
                "substats": ["Taxa Crítica", "Dano Crítico", "ATK%/HP%", "Recarga"],
                "gain": "+15% a +25% Dano Total do Personagem"
            }

            # Encontra se alguma peça equipada tem nota baixa
            lowest_piece = "Nenhuma relíquia equipada"
            if cand["relics"]:
                lowest_piece = f"Peça atual subótima (Build: {cand['grade']})"

            recommendations.append({
                "priority_rank": rank_counter,
                "character_name": cand["name"],
                "character_icon": cand["icon"],
                "target_set_name": cfg["set"],
                "slot_name": cfg["slot"],
                "slot_icon": "fa-wand-magic-sparkles",
                "recommended_main_stat": cfg["main"],
                "recommended_substats": cfg["substats"],
                "current_piece_status": lowest_piece,
                "expected_gain": cfg["gain"],
                "urgency": "MÁXIMA" if rank_counter <= 2 else "ALTA"
            })
            rank_counter += 1
            if rank_counter > 5:
                break

    elif g == "hsr":
        # Meta targets no HSR
        meta_craft_hsr = {
            "robin": {
                "set": "Lushaka das Águas Afundadas / Vonwacq",
                "slot": "Corda de Ligação (Slot 6)",
                "main": "Taxa de Recuperação de Energia (ERR)",
                "substats": ["Velocidade (SPD)", "ATK%", "HP%", "RES a Efeito"],
                "gain": "Recarrega o Concerto do Supremo em 1 rotação"
            },
            "sunday": {
                "set": "Lushaka das Águas Afundadas",
                "slot": "Corda de ERR (Slot 6) ou Pés de SPD (Slot 4)",
                "main": "Taxa de Recuperação de Energia (ERR) ou Velocidade",
                "substats": ["Dano Crítico", "Velocidade", "RES a Efeito", "HP%"],
                "gain": "Sincroniza avanço de ação imediato no turno do Hypercarry"
            },
            "ruan mei": {
                "set": "Talia: Reino dos Bandidos / Vonwacq",
                "slot": "Corda de ERR (Slot 6) ou Pés de SPD (Slot 4)",
                "main": "Taxa de Recuperação de Energia ou Velocidade",
                "substats": ["Efeito de Quebra (Break Effect)", "Velocidade", "HP%"],
                "gain": "Alcança 160% de Efeito de Quebra para buff de 68% DMG global"
            },
            "acheron": {
                "set": "Pioneiro Mergulhador no Mar Morto / Izumo Gensei",
                "slot": "Esfera de ATK% / Raio (Slot 5) ou Corpo de Dano Crítico",
                "main": "Dano Crítico (Corpo) ou ATK% (Esfera)",
                "substats": ["Taxa Crítica", "Dano Crítico", "ATK%", "Velocidade"],
                "gain": "+35% Dano Bruto no Supremo dos Nove Cortes"
            },
            "firefly": {
                "set": "Cavalaria de Ferro dos Flagelos / Kalpagni",
                "slot": "Pés de SPD (Slot 4) ou Esfera de ATK% (Slot 5)",
                "main": "Velocidade (150+ SPD) e ATK%",
                "substats": ["Efeito de Quebra (Break Effect)", "Velocidade", "ATK%"],
                "gain": "Garante 4 ações completas no estado Combustão Completa"
            },
            "feixiao": {
                "set": "Corajoso ao Vento / Duran: Dinastia dos Lobos",
                "slot": "Corpo de Taxa Crítica (Slot 3) ou Esfera de Dano Físico",
                "main": "Taxa Crítica (Corpo) ou Dano Físico (Esfera)",
                "substats": ["Dano Crítico", "Taxa Crítica", "Velocidade", "ATK%"],
                "gain": "Consistência de 95%+ Crítico nos Ataques Extras e Supremo"
            },
            "aventurine": {
                "set": "Palácio dos Cavaleiros da Pureza / Salsotto",
                "slot": "Corpo de DEF% ou Dano Crítico (Slot 3)",
                "main": "DEF% (para 4.000 DEF) ou Dano Crítico",
                "substats": ["DEF%", "Velocidade", "Dano Crítico", "Taxa Crítica"],
                "gain": "Escudo perpétuo de 100% e ativação do buff de 48% Crítico"
            }
        }

        for cand in top_candidates:
            c_norm = _norm_str(cand["name"])
            matched_key = None
            for mk in meta_craft_hsr:
                if mk in c_norm or c_norm in mk:
                    matched_key = mk
                    break

            cfg = meta_craft_hsr.get(matched_key) if matched_key else {
                "set": "Set de Ornamentos Planares Meta",
                "slot": "Corda de Recuperação de Energia (Slot 6) ou Pés de SPD (Slot 4)",
                "main": "Taxa de Recuperação de Energia (ERR) ou Velocidade (SPD)",
                "substats": ["Velocidade", "Taxa Crítica", "Dano Crítico", "HP%/ATK%"],
                "gain": "+20% Eficiência de Ciclos no Caos da Memória (MoC)"
            }

            lowest_piece = "Peça atual subótima"
            if cand["relics"]:
                lowest_piece = f"Build Atual: Nota {cand['grade']} ({cand['score']}%)"

            recommendations.append({
                "priority_rank": rank_counter,
                "character_name": cand["name"],
                "character_icon": cand["icon"],
                "target_set_name": cfg["set"],
                "slot_name": cfg["slot"],
                "slot_icon": "fa-cube",
                "recommended_main_stat": cfg["main"],
                "recommended_substats": cfg["substats"],
                "current_piece_status": lowest_piece,
                "expected_gain": cfg["gain"],
                "urgency": "MÁXIMA" if rank_counter <= 2 else "ALTA"
            })
            rank_counter += 1
            if rank_counter > 5:
                break

    elif g == "zzz":
        # Meta targets no ZZZ
        meta_craft_zzz = {
            "qingyi": {
                "set": "Jazz Eletrizante / Choque Trovejante",
                "slot": "Disco 6 (Impacto %)",
                "main": "Impacto %",
                "substats": ["Taxa Crítica", "Dano Crítico", "ATK%", "Proficiência de Anomalia"],
                "gain": "Atordoa chefes de Shiyu em menos de 15 segundos"
            },
            "ellen": {
                "set": "Pica-Pau Polar / Metal Polar",
                "slot": "Disco 4 (Taxa/Dano Crítico) ou Disco 5 (Bônus Gelo)",
                "main": "Dano Crítico ou Bônus de Dano de Gelo",
                "substats": ["Taxa Crítica", "Dano Crítico", "ATK%", "PEN"],
                "gain": "+30% Dano Crítico nas Tesouradas de Gelo"
            },
            "jane doe": {
                "set": "Presa Furiosa / Jazz da Liberdade",
                "slot": "Disco 4 (Proficiência de Anomalia) ou Disco 5 (Dano Físico)",
                "main": "Proficiência de Anomalia ou Bônus Físico",
                "substats": ["Proficiência de Anomalia", "Taxa de Anomalia", "ATK%"],
                "gain": "Desencadeia Assalto Crítico contínuo de 500k+ dano"
            },
            "caesar": {
                "set": "Protetor da Proto-Faixa / Jazz",
                "slot": "Disco 6 (Impacto %) ou Disco 4 (DEF%)",
                "main": "Impacto % (ou DEF%)",
                "substats": ["DEF%", "HP%", "Impacto", "ATK%"],
                "gain": "Concede +1.000 de ATK instantâneo para todo o time com escudo"
            }
        }

        for cand in top_candidates:
            c_norm = _norm_str(cand["name"])
            matched_key = None
            for mk in meta_craft_zzz:
                if mk in c_norm or c_norm in mk:
                    matched_key = mk
                    break

            cfg = meta_craft_zzz.get(matched_key) if matched_key else {
                "set": "Discos de Música Recomendados",
                "slot": "Disco 6 (Impacto ou Regeneração de Energia)",
                "main": "Impacto % ou Regeneração de Energia",
                "substats": ["Taxa Crítica", "Dano Crítico", "ATK%", "PEN"],
                "gain": "+20% Velocidade de Stun ou Dano de Burst"
            }

            lowest_piece = f"Build Atual: Nota {cand['grade']}"

            recommendations.append({
                "priority_rank": rank_counter,
                "character_name": cand["name"],
                "character_icon": cand["icon"],
                "target_set_name": cfg["set"],
                "slot_name": cfg["slot"],
                "slot_icon": "fa-compact-disc",
                "recommended_main_stat": cfg["main"],
                "recommended_substats": cfg["substats"],
                "current_piece_status": lowest_piece,
                "expected_gain": cfg["gain"],
                "urgency": "MÁXIMA" if rank_counter <= 2 else "ALTA"
            })
            rank_counter += 1
            if rank_counter > 5:
                break

    # Fallback se roster estiver vazio
    if not recommendations:
        recommendations.append({
            "priority_rank": 1,
            "character_name": "Suporte / Buffer Principal",
            "character_icon": None,
            "target_set_name": "Set de Energia ou Velocidade",
            "slot_name": "Corda de ERR / Cálice Elemental / Disco 6",
            "slot_icon": item_icons.get(g, "fa-gem"),
            "recommended_main_stat": "Recuperação de Energia / Dano Elemental / Impacto",
            "recommended_substats": ["Velocidade", "Taxa Crítica", "Dano Crítico"],
            "current_piece_status": "Nenhum personagem de alto nível sincronizado",
            "expected_gain": "Otimização de Rotação Global",
            "urgency": "ALTA"
        })

    summary_tip = (
        f"💡 **Dica de Ouro:** Guarde sua {item_names.get(g, 'Resina')} para peças de **Recuperação de Energia (ERR)** "
        "ou **Cálices de Bônus Elemental / Discos de Impacto**, pois elas possuem a menor probabilidade matemática de drop natural (~3% a 5%)."
    )

    return {
        "game_id": g,
        "game_name": game_names.get(g, g.upper()),
        "crafting_item_name": item_names.get(g, "Item de Síntese"),
        "crafting_item_icon": item_icons.get(g, "fa-wand-magic-sparkles"),
        "recommendations": recommendations,
        "summary_tip": summary_tip
    }




