import os
import re
import json
import unicodedata
from typing import Dict, List, Tuple, Optional

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
def normalize_char_name(name: str) -> str:
    """
    Normaliza o nome do personagem para facilitar o cruzamento de IDs,
    removendo hifens, bullets, parênteses e múltiplos espaços.
    """
    name = name.lower()
    name = name.replace("•", " ").replace("-", " ").replace("(", " ").replace(")", " ").replace(".", " ")
    return re.sub(r'\s+', ' ', name).strip()

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
            "velina": "1561"
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
                META_DATA_CACHE[game_id] = data
                return data
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
    "proficiência elemental": "em", "proficiencia elemental": "em", "proficiência": "em", "proficiencia": "em", "elemental mastery": "em", "em": "em", "prof": "em", "prof. elemental": "em", "mastery": "em",
    "anomaly proficiency": "anomaly_prof", "proficiência em anomalia": "anomaly_prof", "proficiencia em anomalia": "anomaly_prof", "proficiência de anomalia": "anomaly_prof", "proficiencia de anomalia": "anomaly_prof", "anomaly_prof": "anomaly_prof",
    "proficiência de anomalia%": "anomaly_prof", "proficiencia de anomalia%": "anomaly_prof", "anomalia": "anomaly_prof",
    
    # Recarga de Energia / Taxa de Regeneração de Energia
    "recarga de energia": "er", "recarga": "er", "energy recharge": "er", "er": "er", "recharge": "er", "recarga de energia%": "er",
    "taxa de regeneração de energia": "err", "taxa de regeneracao de energia": "err", "recuperação de energia": "err", "recuperacao de energia": "err", "energy regen rate": "err", "energy regen": "err", "err": "err",
    
    # Bônus de Cura
    "bônus de cura": "healing_bonus", "bonus de cura": "healing_bonus", "bônus de cura%": "healing_bonus", "bonus de cura%": "healing_bonus", "healing bonus": "healing_bonus", "healing": "healing_bonus", "healing_bonus": "healing_bonus",
    
    # Atributos Percentuais
    "atq %": "atk_pct", "atq%": "atk_pct", "atk%": "atk_pct", "atk %": "atk_pct", "ataque%": "atk_pct", "attack%": "atk_pct", "atk_pct": "atk_pct",
    "vida %": "hp_pct", "vida%": "hp_pct", "hp%": "hp_pct", "hp %": "hp_pct", "hp_pct": "hp_pct", "vida_pct": "hp_pct",
    "defesa %": "def_pct", "defesa%": "def_pct", "def%": "def_pct", "def %": "def_pct", "defesa_pct": "def_pct", "def_pct": "def_pct",
    
    # Atributos Planos (Flats)
    "atq": "atk_flat", "atk": "atk_flat", "ataque": "atk_flat", "attack": "atk_flat", "atk_flat": "atk_flat",
    "vida": "hp_flat", "hp": "hp_flat", "hp_flat": "hp_flat",
    "defesa": "def_flat", "def": "def_flat", "defesa_flat": "def_flat", "def_flat": "def_flat",
    "pv": "hp_flat", "pv%": "hp_pct", "pontos de vida": "hp_flat",
    
    # Bônus Elementais (Genshin / HSR / ZZZ)
    "pyro dmg": "pyro_dmg", "pyro dmg bonus": "pyro_dmg", "bônus de dano pyro": "pyro_dmg", "bonus de dano pyro": "pyro_dmg", "bônus de dano de fogo": "fire_dmg", "bonus de dano de fogo": "fire_dmg", "fire dmg": "fire_dmg", "fire dmg bonus": "fire_dmg", "fogo": "fire_dmg", "pyro": "pyro_dmg", "dano de fogo": "fire_dmg", "dano fogo": "fire_dmg", "bônus de dano fogo": "fire_dmg", "bonus de dano fogo": "fire_dmg",
    "hydro dmg": "hydro_dmg", "hydro dmg bonus": "hydro_dmg", "bônus de dano hydro": "hydro_dmg", "bonus de dano hydro": "hydro_dmg", "bônus de dano de água": "hydro_dmg", "bonus de dano de agua": "hydro_dmg", "hydro": "hydro_dmg", "dano de agua": "hydro_dmg", "dano hydro": "hydro_dmg", "bônus de dano agua": "hydro_dmg", "bonus de dano agua": "hydro_dmg",
    "electro dmg": "electro_dmg", "electro dmg bonus": "electro_dmg", "bônus de dano electro": "electro_dmg", "bonus de dano electro": "electro_dmg", "bônus de dano de raio": "lightning_dmg", "bonus de dano de raio": "lightning_dmg", "bônus de dano elétrico": "electric_dmg", "bonus de dano eletrico": "electric_dmg", "lightning dmg": "lightning_dmg", "lightning dmg bonus": "lightning_dmg", "electric dmg": "electric_dmg", "electric dmg bonus": "electric_dmg", "raio": "lightning_dmg", "eletro": "electro_dmg", "dano eletrico": "electric_dmg", "dano de raio": "lightning_dmg", "bônus de dano eletrico": "electric_dmg", "bonus de dano eletrico": "electric_dmg",
    "cryo dmg": "cryo_dmg", "cryo dmg bonus": "cryo_dmg", "bônus de dano cryo": "cryo_dmg", "bonus de dano cryo": "cryo_dmg", "bônus de dano de gelo": "ice_dmg", "bonus de dano de gelo": "ice_dmg", "ice dmg": "ice_dmg", "ice dmg bonus": "ice_dmg", "gelo": "ice_dmg", "cryo": "cryo_dmg", "dano de gelo": "ice_dmg", "dano gelo": "ice_dmg", "bônus de dano gelo": "ice_dmg", "bonus de dano gelo": "ice_dmg",
    "anemo dmg": "anemo_dmg", "anemo dmg bonus": "anemo_dmg", "bônus de dano anemo": "anemo_dmg", "bonus de dano anemo": "anemo_dmg", "bônus de dano de vento": "wind_dmg", "bonus de dano de vento": "wind_dmg", "wind dmg": "wind_dmg", "wind dmg bonus": "wind_dmg", "vento": "wind_dmg", "anemo": "anemo_dmg", "dano de vento": "wind_dmg", "dano vento": "wind_dmg", "bônus de dano vento": "wind_dmg", "bonus de dano vento": "wind_dmg",
    "geo dmg": "geo_dmg", "geo dmg bonus": "geo_dmg", "bônus de dano geo": "geo_dmg", "bonus de dano geo": "geo_dmg", "geo": "geo_dmg", "dano geo": "geo_dmg",
    "dendro dmg": "dendro_dmg", "dendro dmg bonus": "dendro_dmg", "bônus de dano dendro": "dendro_dmg", "bonus de dano dendro": "dendro_dmg", "dendro": "dendro_dmg", "dano dendro": "dendro_dmg",
    "physical dmg": "physical_dmg", "physical dmg bonus": "physical_dmg", "bônus de dano físico": "physical_dmg", "bonus de dano fisico": "physical_dmg", "físico": "physical_dmg", "fisico": "physical_dmg", "physical": "physical_dmg", "dano físico": "physical_dmg", "dano fisico": "physical_dmg", "bônus de dano fisico": "physical_dmg", "bonus de dano fisico": "physical_dmg",
    "quantum dmg": "quantum_dmg", "quantum dmg bonus": "quantum_dmg", "bônus de dano quântico": "quantum_dmg", "bonus de dano quantico": "quantum_dmg", "quântico": "quantum_dmg", "quantico": "quantum_dmg", "quantum": "quantum_dmg", "dano quântico": "quantum_dmg", "dano quantico": "quantum_dmg",
    "imaginary dmg": "imaginary_dmg", "imaginary dmg bonus": "imaginary_dmg", "bônus de dano imaginário": "imaginary_dmg", "bonus de dano imaginario": "imaginary_dmg", "imaginário": "imaginary_dmg", "imaginario": "imaginary_dmg", "imaginary": "imaginary_dmg", "dano imaginário": "imaginary_dmg", "dano imaginario": "imaginary_dmg",
    "ether dmg": "ether_dmg", "ether dmg bonus": "ether_dmg", "bônus de dano de éter": "ether_dmg", "bonus de dano de eter": "ether_dmg", "éter": "ether_dmg", "eter": "ether_dmg", "dano de éter": "ether_dmg", "dano de eter": "ether_dmg", "dano éter": "ether_dmg", "dano eter": "ether_dmg", "bônus de dano eter": "ether_dmg", "bonus de dano eter": "ether_dmg",
    
    # HSR Específicos
    "effect hit rate": "ehr", "ehr": "ehr", "taxa de acerto de efeito": "ehr",
    "chance de acerto de efeito": "ehr", "chance de acerto de efeito%": "ehr", "chance de acerto": "ehr", "acerto de efeito": "ehr",
    "effect res": "res", "res": "res", "resistência a efeito": "res", "resistencia a efeito": "res", "res_efeito": "res",
    "res a efeito": "res", "res a efeito%": "res", "resistência a efeito%": "res", "resistencia a efeito%": "res",
    "outgoing healing": "healing_bonus", "outgoing_healing": "healing_bonus",
    
    # ZZZ Específicos
    "pen flat": "pen_flat", "pen": "pen_flat", "pen flat bonus": "pen_flat", "perfuração": "pen_flat", "perfuracao": "pen_flat",
    "pen ratio": "pen_pct", "pen_pct": "pen_pct", "taxa de perfuração": "pen_pct", "taxa de perfuracao": "pen_pct", "perfuração%": "pen_pct", "perfuracao%": "pen_pct", "perfuracao ratio": "pen_pct", "perfuração ratio": "pen_pct",
    "impacto": "impact", "impact": "impact", "impact_pct": "impact",
    "taxa de controle de anomalia": "anomaly_mastery", "controle de anomalia": "anomaly_mastery", "anomaly mastery": "anomaly_mastery", "anomaly_mastery": "anomaly_mastery", "maestria de anomalia": "anomaly_mastery"
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
    "break_effect", "ehr", "res", "em", "er",
    "atk_flat", "hp_flat", "def_flat",
    "anomaly_prof", "pen_flat",
})

# Fallbacks genéricos por jogo, usados quando o parser não extrai substats válidos
DEFAULT_SUBSTATS_FALLBACK = {
    "hsr":     ["crit_rate", "crit_dmg", "spd", "atk_pct"],
    "genshin": ["crit_rate", "crit_dmg", "atk_pct", "er"],
    "zzz":     ["crit_rate", "crit_dmg", "atk_pct"],
}

def normalize_stat_name(raw_name: str, has_percent: bool = False) -> str:
    """Normaliza o nome do atributo para chaves padrão do motor de cálculo, ignorando acentos e case."""
    name_clean = remove_accents(raw_name.strip().lower())
    
    if "%" in name_clean:
        has_percent = True
        name_clean = name_clean.replace("%", "").strip()
        
    mapped = STAT_NAME_MAP.get(name_clean, name_clean)
    
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
        if rec_mains:
            norm_rec = [normalize_stat_name(m) for m in rec_mains]
            if "anything" in norm_rec or "any" in norm_rec or "qualquer" in norm_rec or any(is_stat_equivalent(main_stat_norm, m) for m in norm_rec):
                main_stat_tier = 1.0
            elif weights.get(main_stat_norm, 0.0) > 0.3:
                main_stat_tier = 0.6
            else:
                main_stat_tier = 0.0
        else:
            if weights.get(main_stat_norm, 0.0) > 0.35:
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
        
    ideal_substats = available_substats[:4]
    
    # Distribuição calibrada para o limite teórico de 9 rolls úteis (4 base + 5 procs)
    # Até 6 rolls no 1º atributo prioritário, 1 roll nos demais
    roll_distribution = [6.0, 1.0, 1.0, 1.0]
    if len(ideal_substats) < 4:
        if len(ideal_substats) == 1:
            roll_distribution = [9.0]
        elif len(ideal_substats) == 2:
            roll_distribution = [6.0, 3.0]
        elif len(ideal_substats) == 3:
            roll_distribution = [6.0, 2.0, 1.0]
        elif len(ideal_substats) == 0:
            roll_distribution = []

    max_possible_sub_score = 0.0
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
    Para Genshin Impact, os metadados são gerados via game8_scraper.py.
    """
    game_id = game_id.lower().strip()

    if game_id == "genshin":
        print("[INFO] Metadados de Genshin são gerados via game8_scraper.py. Ignorando parse de Markdown.")
        return

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

    parse_fn = parse_hsr if game_id == "hsr" else parse_zzz
    
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

def calculate_ascension(game_id, current_lvl, target_lvl):
    """
    Calcula a diferença de recursos necessários entre o nível atual e o nível alvo.
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
    
    return {
        "xp_needed": xp_diff,
        "xp_books_purple": xp_books if xp_books > 0 else 1,
        "currency_needed": currency_diff,
        "currency_name": currency_name,
        "boss_items_needed": boss_diff,
        "boss_item_name": boss_item_name
    }
