import os
import re
import json
from typing import Dict, List, Tuple, Optional

# ==========================================
# CACHE DO BANCO DE METADADOS JSON
# ==========================================
META_DATA_CACHE = {}

def get_meta_data(game_id: str) -> dict:
    """Carrega o banco de metadados JSON do cache em memória."""
    game_id = game_id.lower().strip()
    if game_id in META_DATA_CACHE:
        return META_DATA_CACHE[game_id]
        
    path = f"{game_id}/meta_data.json"
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
# DICIONÁRIO DE VALORES MÁXIMOS DE UM ÚNICO ROLL (5★ / S-Rank)
# ==========================================
MAX_ROLL_VALUES = {
    "genshin": {
        "crit_rate": 3.89,
        "crit_dmg": 7.77,
        "atk_pct": 5.83,
        "hp_pct": 5.83,
        "def_pct": 7.29,
        "em": 23.31,
        "er": 6.48,
        "atk_flat": 19.45,
        "hp_flat": 298.75,
        "def_flat": 23.15
    },
    "hsr": {
        "crit_rate": 3.24,
        "crit_dmg": 6.48,
        "atk_pct": 4.32,
        "hp_pct": 4.32,
        "def_pct": 5.40,
        "break_effect": 6.48,
        "spd": 2.60,
        "atk_flat": 21.30,
        "hp_flat": 42.30,
        "def_flat": 21.30,
        "ehr": 4.32,  # Effect Hit Rate
        "res": 4.32   # Effect RES
    },
    "zzz": {
        "crit_rate": 3.00,
        "crit_dmg": 6.00,
        "atk_pct": 3.00,
        "hp_pct": 3.00,
        "def_pct": 4.80,
        "anomaly_prof": 9.00,
        "pen_flat": 9.00,
        "atk_flat": 15.00,
        "hp_flat": 112.00,
        "def_flat": 15.00
    }
}

# ==========================================
# MAPEAMENTO PARA NORMALIZAÇÃO DE NOMES DE ATRIBUTOS
# ==========================================
STAT_NAME_MAP = {
    # Taxa Crítica
    "taxa crítica": "crit_rate", "taxa crit": "crit_rate", "crit rate": "crit_rate", "crit_rate": "crit_rate", "rate": "crit_rate", "taxa": "crit_rate",
    # Dano Crítico
    "dano crítico": "crit_dmg", "dano crit": "crit_dmg", "crit dmg": "crit_dmg", "crit_dmg": "crit_dmg", "dmg": "crit_dmg", "dano": "crit_dmg", "damage": "crit_dmg",
    # Velocidade
    "velocidade": "spd", "vel": "spd", "spd": "spd", "speed": "spd",
    # Efeito de Quebra
    "efeito de quebra": "break_effect", "quebra": "break_effect", "break effect": "break_effect", "break_effect": "break_effect", "be": "break_effect",
    # Proficiência Elemental / Anomalia
    "proficiência elemental": "em", "proficiência": "em", "elemental mastery": "em", "em": "em", "prof": "em", "prof. elemental": "em", "mastery": "em",
    "anomaly proficiency": "anomaly_prof", "proficiência em anomalia": "anomaly_prof", "proficiência de anomalia": "anomaly_prof", "anomaly_prof": "anomaly_prof",
    # Recarga de Energia
    "recarga de energia": "er", "recarga": "er", "energy recharge": "er", "er": "er", "recharge": "er", "recarga de energia%": "er",
    # Atributos Percentuais
    "atq %": "atk_pct", "atq%": "atk_pct", "atk%": "atk_pct", "atk %": "atk_pct", "ataque%": "atk_pct", "attack%": "atk_pct", "atk_pct": "atk_pct",
    "vida %": "hp_pct", "vida%": "hp_pct", "hp%": "hp_pct", "hp %": "hp_pct", "hp_pct": "hp_pct", "vida_pct": "hp_pct",
    "defesa %": "def_pct", "defesa%": "def_pct", "def%": "def_pct", "def %": "def_pct", "defesa_pct": "def_pct", "def_pct": "def_pct",
    # Atributos Planos (Flats)
    "atq": "atk_flat", "atk": "atk_flat", "ataque": "atk_flat", "attack": "atk_flat", "atk_flat": "atk_flat",
    "vida": "hp_flat", "hp": "hp_flat", "hp_flat": "hp_flat",
    "defesa": "def_flat", "def": "def_flat", "defesa_flat": "def_flat", "def_flat": "def_flat",
    # HSR Específicos
    "effect hit rate": "ehr", "ehr": "ehr", "taxa de acerto de efeito": "ehr",
    "effect res": "res", "res": "res", "resistência a efeito": "res", "res_efeito": "res",
    # ZZZ Específicos
    "pen flat": "pen_flat", "pen": "pen_flat", "pen flat bonus": "pen_flat"
}

def normalize_stat_name(raw_name: str, has_percent: bool = False) -> str:
    """Normaliza o nome do atributo para chaves padrão do motor de cálculo."""
    name_clean = raw_name.strip().lower()
    
    if "%" in name_clean:
        has_percent = True
        name_clean = name_clean.replace("%", "").strip()
        
    mapped = STAT_NAME_MAP.get(name_clean, name_clean)
    
    if has_percent:
        if mapped == "atk_flat": return "atk_pct"
        if mapped == "hp_flat": return "hp_pct"
        if mapped == "def_flat": return "def_pct"
        
    return mapped

# ==========================================
# EXTRATOR DE PESOS DINÂMICOS BASEADO NO GUIA
# ==========================================
def extract_weights_from_guide(game_id: str, character_name: str) -> Dict[str, float]:
    """
    Busca no arquivo meta_data.json a prioridade de substatus e converte em pesos (0.0 a 1.0).
    Faz fallback para o parsing clássico do markdown caso não encontre no JSON.
    """
    game_id = game_id.lower().strip()
    meta_db = get_meta_data(game_id)
    
    # 1. Tenta buscar no JSON compilado primeiro
    char_meta = None
    for name, m in meta_db.items():
        if name.lower().strip() == character_name.lower().strip():
            char_meta = m
            break
            
    if char_meta:
        subs = char_meta.get("substats_priority", [])
        if subs:
            weights = {}
            scale = [1.0, 0.85, 0.70, 0.55, 0.40]
            for i, s in enumerate(subs):
                norm_name = normalize_stat_name(s)
                weight_val = scale[i] if i < len(scale) else 0.30
                weights[norm_name] = weight_val
                
            if "crit_rate" in weights and "crit_dmg" not in weights:
                weights["crit_dmg"] = weights["crit_rate"] * 0.85
            elif "crit_dmg" in weights and "crit_rate" not in weights:
                weights["crit_rate"] = weights["crit_dmg"] * 0.85
                
            return weights

    # 2. Fallback caso não esteja no JSON: Parseia Markdown direto
    char_clean = character_name.lower().replace(" ", "_")
    guias_dir = f"{game_id}/guias"
    filepath = None
    
    if os.path.exists(guias_dir):
        try:
            files = os.listdir(guias_dir)
            for f in files:
                if f.endswith(".md"):
                    f_name = f[:-3].lower()
                    if (f_name == char_clean or 
                        f_name.replace("_", "") == char_clean.replace("_", "") or 
                        char_clean in f_name or 
                        f_name in char_clean):
                        filepath = os.path.join(guias_dir, f)
                        break
        except Exception:
            pass

    default_weights = {
        "crit_rate": 1.0,
        "crit_dmg": 1.0,
        "atk_pct": 0.6,
        "spd": 0.6,
        "break_effect": 0.5,
        "em": 0.5,
        "er": 0.5
    }
    
    if not filepath or not os.path.exists(filepath):
        return default_weights
        
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        pattern = r"(?:subatributos prioritários|sub-stats|prioridade de substatus).*?\n(.*)"
        match = re.search(pattern, content, re.IGNORECASE)
        
        if match:
            sub_line = match.group(1).strip()
            if not sub_line:
                lines = content[match.start(1):].split("\n")
                for l in lines:
                    if l.strip():
                        sub_line = l.strip()
                        break
            
            tokens = []
            for tok in re.split(r'[>,;]', sub_line):
                tok_clean = tok.strip()
                tok_clean = re.sub(r'\(.*?\)', '', tok_clean).strip()
                if tok_clean:
                    tokens.append(tok_clean)
                    
            if tokens:
                weights = {}
                scale = [1.0, 0.85, 0.70, 0.55, 0.40]
                for i, token in enumerate(tokens):
                    norm_name = normalize_stat_name(token)
                    weight_val = scale[i] if i < len(scale) else 0.30
                    weights[norm_name] = weight_val
                
                if "crit_rate" in weights and "crit_dmg" not in weights:
                    weights["crit_dmg"] = weights["crit_rate"] * 0.85
                elif "crit_dmg" in weights and "crit_rate" not in weights:
                    weights["crit_rate"] = weights["crit_dmg"] * 0.85
                    
                return weights
                
    except Exception:
        pass
        
    return default_weights

# ==========================================
# MOTOR DINÂMICO DE SCORES COM MAIN STAT FORGIVENESS
# ==========================================
def clean_value(val_str: str) -> Tuple[float, bool]:
    """Extrai o valor numérico de uma string de status e indica se é percentual."""
    has_pct = "%" in val_str
    match = re.search(r'([\d\.]+)', val_str)
    val = float(match.group(1)) if match else 0.0
    return val, has_pct

def score_relic(game_id: str, character_name: str, slot: str, main_stat: str, substats_str: str) -> Tuple[str, float]:
    """
    Calcula a nota de uma relíquia usando Roll Value (RV) e Main Stat Forgiveness (Compensação).
    """
    game_id = game_id.lower().strip()
    if game_id not in MAX_ROLL_VALUES:
        return "D", 0.0
        
    if not substats_str or substats_str.strip() in ["Sem substatus", "Status não disponíveis", ""]:
        return "D", 0.0
        
    weights = extract_weights_from_guide(game_id, character_name)
    
    main_clean = main_stat.lower()
    slot_clean = slot.lower()
    is_fixed_main = False
    if game_id == "genshin" and ("flower" in slot_clean or "plume" in slot_clean or "flor" in slot_clean or "pena" in slot_clean):
        is_fixed_main = True
    elif game_id == "hsr" and ("head" in slot_clean or "hands" in slot_clean or "cabeça" in slot_clean or "mão" in slot_clean):
        is_fixed_main = True
        
    main_stat_norm = normalize_stat_name(main_stat, has_percent=("%" in main_clean))
    
    sorted_priorities = [k for k, v in sorted(weights.items(), key=lambda item: item[1], reverse=True) if v > 0.0]
    
    if not is_fixed_main and main_stat_norm in sorted_priorities:
        available_substats = [s for s in sorted_priorities if s != main_stat_norm]
    else:
        available_substats = sorted_priorities
        
    ideal_substats = available_substats[:4]
    while len(ideal_substats) < 4:
        ideal_substats.append("none")
        
    roll_distribution = [5, 2, 1, 1]
    max_possible_score = 0.0
    for i, sub in enumerate(ideal_substats):
        w = weights.get(sub, 0.0)
        max_possible_score += w * roll_distribution[i]
        
    if max_possible_score <= 0:
        max_possible_score = 5.0
        
    game_max_rolls = MAX_ROLL_VALUES[game_id]
    actual_score = 0.0
    
    parts = substats_str.split(",")
    for p in parts:
        if ":" in p:
            name, val_str = p.split(":", 1)
            val, has_pct = clean_value(val_str)
            sub_name_norm = normalize_stat_name(name, has_percent=has_pct)
            
            max_roll = game_max_rolls.get(sub_name_norm, 0.0)
            
            if max_roll > 0.0:
                rv = val / max_roll
                actual_score += rv * weights.get(sub_name_norm, 0.0)
                
    rating_pct = (actual_score / max_possible_score) * 100.0
    
    if rating_pct >= 90.0: grade = "SSS"
    elif rating_pct >= 75.0: grade = "SS"
    elif rating_pct >= 60.0: grade = "S"
    elif rating_pct >= 45.0: grade = "A"
    elif rating_pct >= 30.0: grade = "B"
    elif rating_pct >= 15.0: grade = "C"
    else: grade = "D"
    
    return grade, round(rating_pct, 1)

# ==========================================
# AVALIADOR DE STATUS GERAIS DO PERSONAGEM
# ==========================================
def evaluate_general_stats(game_id: str, character_name: str, final_stats: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Compara os status consolidados reais do personagem contra os benchmarks ideais do metagame.
    Retorna uma lista estruturada de avaliações.
    """
    game_id = game_id.lower().strip()
    meta_db = get_meta_data(game_id)
    
    char_meta = None
    for name, m in meta_db.items():
        if name.lower().strip() == character_name.lower().strip():
            char_meta = m
            break
            
    if not char_meta or "general_benchmarks" not in char_meta:
        return []
        
    benchmarks = char_meta["general_benchmarks"]
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
# GERADOR DE ARQUIVOS META_DATA.JSON
# ==========================================
def generate_meta_json_from_markdown(game_id: str):
    """
    Varre todos os guias markdown do jogo e regenera o arquivo meta_data.json
    """
    game_id = game_id.lower().strip()
    guias_dir = f"{game_id}/guias"
    meta_db = {}
    
    def parse_hsr(content):
        meta = {"main_stats": {}, "substats_priority": [], "general_benchmarks": {}}
        matches = re.findall(r"-\s*(Body|Feet|Planar Sphere|Link Rope):\s*(.*)", content)
        for slot, val in matches:
            stats = [normalize_stat_name(s) for s in re.split(r'[/|or]', val)]
            meta["main_stats"][slot.lower().replace(" ", "_")] = [s for s in stats if s]
            
        sub_match = re.search(r"(?:subatributos prioritários|sub-stats|substats).*?\n(.*)", content, re.I)
        if sub_match:
            sub_line = sub_match.group(1).strip()
            if not sub_line:
                lines = content[sub_match.start(1):].split("\n")
                for l in lines:
                    if l.strip(): sub_line = l.strip(); break
            tokens = [normalize_stat_name(tok.strip()) for tok in re.split(r'[>,\/;]', sub_line) if tok.strip()]
            meta["substats_priority"] = [t for t in tokens if t]
            
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

    def parse_genshin(content):
        meta = {"main_stats": {}, "substats_priority": [], "general_benchmarks": {}}
        main_match = re.search(r"\|\s*\*?\*?Sands\*?\*?\s*\|\s*\*?\*?Goblet\*?\*?\s*\|\s*\*?\*?Circlet\*?\*?\s*\|.*?\n\|.*?\|.*?\|.*?\|\n\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|", content, re.I)
        if main_match:
            sands = [normalize_stat_name(s) for s in re.split(r'[/|or]', main_match.group(1))]
            goblet = [normalize_stat_name(s) for s in re.split(r'[/|or]', main_match.group(2))]
            circlet = [normalize_stat_name(s) for s in re.split(r'[/|or]', main_match.group(3))]
            meta["main_stats"] = {
                "sands": [s for s in sands if s],
                "goblet": [s for s in goblet if s],
                "circlet": [s for s in circlet if s]
            }
        else:
            matches = re.findall(r"-\s*(Sands|Goblet|Circlet):\s*(.*)", content, re.I)
            for slot, val in matches:
                stats = [normalize_stat_name(s) for s in re.split(r'[/|or]', val)]
                meta["main_stats"][slot.lower()] = [s for s in stats if s]
                
        sub_match = re.search(r"\*?\*?Stat Priority:\*?\*?\s*(.*)", content, re.I)
        if sub_match:
            sub_line = sub_match.group(1).strip()
            tokens = [normalize_stat_name(tok.strip()) for tok in re.split(r'[>=\/;\+]', sub_line) if tok.strip()]
            meta["substats_priority"] = [t for t in tokens if t]
        return meta

    def parse_zzz(content):
        meta = {"main_stats": {}, "substats_priority": [], "general_benchmarks": {}}
        matches = re.findall(r"Slot\s*(4|5|6):\s*(.*)", content, re.I)
        for slot, val in matches:
            stats = [normalize_stat_name(s) for s in re.split(r'[/|or]', val)]
            meta["main_stats"][f"slot_{slot}"] = [s for s in stats if s]
            
        sub_match = re.search(r"(?:substatus prioritários|substats):\s*(.*)", content, re.I)
        if sub_match:
            sub_line = sub_match.group(1).strip()
            tokens = [normalize_stat_name(tok.strip()) for tok in re.split(r'[>,\/;]', sub_line) if tok.strip()]
            meta["substats_priority"] = [t for t in tokens if t]
        return meta

    parse_fn = parse_hsr if game_id == "hsr" else (parse_genshin if game_id == "genshin" else parse_zzz)
    
    if os.path.exists(guias_dir):
        try:
            files = os.listdir(guias_dir)
            for f in files:
                if f.endswith(".md"):
                    char_name = f[:-3].replace("_", " ").title()
                    if char_name.lower().startswith("dan heng"):
                        char_name = char_name.replace("•", "•")
                    filepath = os.path.join(guias_dir, f)
                    try:
                        with open(filepath, "r", encoding="utf-8") as file:
                            char_meta = parse_fn(file.read())
                            meta_db[char_name] = char_meta
                    except Exception as ex:
                        print(f"[WARN] Erro ao parsear {filepath}: {ex}")
        except Exception as e:
            print(f"[WARN] Erro ao listar diretório {guias_dir}: {e}")
            
    output_path = f"{game_id}/meta_data.json"
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
