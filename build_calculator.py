import os
import re
from typing import Dict, List, Tuple, Optional

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
    
    # Se o nome já tem "%" ou has_percent é verdadeiro, força mapear para percentual
    if "%" in name_clean:
        has_percent = True
        name_clean = name_clean.replace("%", "").strip()
        
    mapped = STAT_NAME_MAP.get(name_clean, name_clean)
    
    # Faz o ajuste se for percentual e caiu num mapeamento plano
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
    Varre o arquivo markdown de guias local do personagem e extrai a prioridade de substatus,
    atribuindo pesos dinâmicos em uma escala de 0.0 a 1.0.
    """
    game_id = game_id.lower().strip()
    char_clean = character_name.lower().replace(" ", "_")
    
    guias_dir = f"{game_id}/guias"
    filepath = None
    
    # Busca inteligente/difusa no diretório de guias
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
        except Exception as e:
            print(f"[WARN] Erro ao listar diretório {guias_dir}: {e}")

    # Fallbacks padrão caso não encontre o guia do personagem
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
            
        # Regex para buscar a seção de substatus prioritários
        # Suporta formatos como: "#### Subatributos Prioritários (Sub-stats)", "Sub-stats", etc.
        pattern = r"(?:subatributos prioritários|sub-stats|prioridade de substatus).*?\n(.*)"
        match = re.search(pattern, content, re.IGNORECASE)
        
        if match:
            sub_line = match.group(1).strip()
            # Se a linha seguinte estiver vazia, tenta ler a próxima
            if not sub_line:
                lines = content[match.start(1):].split("\n")
                for l in lines:
                    if l.strip():
                        sub_line = l.strip()
                        break
            
            # Limpa e divide a linha de prioridades (ex: "SPD > Break Effect% > ATK%")
            tokens = []
            # Divide por >, vírgula ou ponto-e-vírgula
            for tok in re.split(r'[>,;]', sub_line):
                tok_clean = tok.strip()
                # Remove anotações entre parênteses como "(Until Breakpoint)"
                tok_clean = re.sub(r'\(.*?\)', '', tok_clean).strip()
                if tok_clean:
                    tokens.append(tok_clean)
                    
            if tokens:
                weights = {}
                # Atribui pesos decrescentes baseados na ordem de prioridade
                scale = [1.0, 0.85, 0.70, 0.55, 0.40]
                for i, token in enumerate(tokens):
                    norm_name = normalize_stat_name(token)
                    weight_val = scale[i] if i < len(scale) else 0.30
                    weights[norm_name] = weight_val
                
                # Garante que taxa e dano crítico andem juntos se um deles for mencionado
                if "crit_rate" in weights and "crit_dmg" not in weights:
                    weights["crit_dmg"] = weights["crit_rate"] * 0.85
                elif "crit_dmg" in weights and "crit_rate" not in weights:
                    weights["crit_rate"] = weights["crit_dmg"] * 0.85
                    
                return weights
                
    except Exception as ex:
        print(f"[WARN] Erro ao ler ou extrair pesos dinâmicos do arquivo {filepath}: {ex}")
        
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
    
    Fórmula de RV: Valor real / Valor Máximo do Roll.
    Nota Final: Porcentagem do score real comparado ao máximo ideal da peça.
    """
    game_id = game_id.lower().strip()
    if game_id not in MAX_ROLL_VALUES:
        return "D", 0.0
        
    if not substats_str or substats_str.strip() in ["Sem substatus", "Status não disponíveis", ""]:
        return "D", 0.0
        
    # 1. Extração dinâmica de pesos baseados no RAG do personagem
    weights = extract_weights_from_guide(game_id, character_name)
    
    # 2. Identificação e Normalização do Main Stat para aplicação do Forgiveness
    main_clean = main_stat.lower()
    # Se o nome da peça/slot indica que o Main Stat é fixo (ex: Flor/Pena no Genshin, Cabeça/Mãos no HSR)
    # nós não compensamos porque o Main Stat não é opcional/competidor de substatus.
    slot_clean = slot.lower()
    is_fixed_main = False
    if game_id == "genshin" and ("flower" in slot_clean or "plume" in slot_clean or "flor" in slot_clean or "pena" in slot_clean):
        is_fixed_main = True
    elif game_id == "hsr" and ("head" in slot_clean or "hands" in slot_clean or "cabeça" in slot_clean or "mão" in slot_clean):
        is_fixed_main = True
        
    main_stat_norm = normalize_stat_name(main_stat, has_percent=("%" in main_clean))
    
    # 3. Main Stat Forgiveness: Remove o Main Stat da lista de possíveis substatus
    # Ordena as prioridades de substatus do personagem por peso decrescente
    sorted_priorities = [k for k, v in sorted(weights.items(), key=lambda item: item[1], reverse=True) if v > 0.0]
    
    # Se o Main Stat for útil e não for um slot fixo, nós removemos do pool de substatus disponíveis
    if not is_fixed_main and main_stat_norm in sorted_priorities:
        available_substats = [s for s in sorted_priorities if s != main_stat_norm]
    else:
        available_substats = sorted_priorities
        
    # Obtém as top 4 substatus ideais que a peça poderia ter
    ideal_substats = available_substats[:4]
    while len(ideal_substats) < 4:
        ideal_substats.append("none")
        
    # 4. Calcula o Teto Máximo Teórico de Pontuação (Max Possible Score)
    # Ponderação típica de distribuição de rolagens perfeitas (+15 possui 9 rolagens totais em média):
    # - 5 rolls no melhor substatus
    # - 2 rolls no segundo melhor
    # - 1 roll no terceiro
    # - 1 roll no quarto
    roll_distribution = [5, 2, 1, 1]
    max_possible_score = 0.0
    for i, sub in enumerate(ideal_substats):
        w = weights.get(sub, 0.0)
        max_possible_score += w * roll_distribution[i]
        
    # Proteção de divisão por zero caso o personagem não tenha pesos válidos
    if max_possible_score <= 0:
        max_possible_score = 5.0
        
    # 5. Calcula o Score Real baseado em Roll Value (RV)
    game_max_rolls = MAX_ROLL_VALUES[game_id]
    actual_score = 0.0
    
    parts = substats_str.split(",")
    for p in parts:
        if ":" in p:
            name, val_str = p.split(":", 1)
            val, has_pct = clean_value(val_str)
            sub_name_norm = normalize_stat_name(name, has_percent=has_pct)
            
            # Obtém o valor máximo de roll para esse status
            max_roll = game_max_rolls.get(sub_name_norm, 0.0)
            
            if max_roll > 0.0:
                # Calcula o Roll Value (quantos rolls perfeitos esse substatus equivale)
                rv = val / max_roll
                # Soma ponderada
                actual_score += rv * weights.get(sub_name_norm, 0.0)
                
    # 6. Calcula a nota percentual final
    rating_pct = (actual_score / max_possible_score) * 100.0
    
    # 7. Classificação por letras
    if rating_pct >= 90.0: grade = "SSS"
    elif rating_pct >= 75.0: grade = "SS"
    elif rating_pct >= 60.0: grade = "S"
    elif rating_pct >= 45.0: grade = "A"
    elif rating_pct >= 30.0: grade = "B"
    elif rating_pct >= 15.0: grade = "C"
    else: grade = "D"
    
    return grade, round(rating_pct, 1)


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
