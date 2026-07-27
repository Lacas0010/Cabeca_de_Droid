import re

# Dicionário de Arquetipos de Personagens para priorização de substatus
# Isso garante que suportes, healers e DPS de reação/break sejam pontuados corretamente.
CHARACTER_ARCHETYPES = {
    # HSR Break scaling
    "Firefly": "BREAK", "Boothill": "BREAK", "Gallagher": "BREAK", "Ruan Mei": "BREAK",
    # Genshin HP scaling / Non-Crit
    "Sangonomiya Kokomi": "HEALER_HP", "Barbara": "HEALER_HP", "Zhongli": "SUPPORT_HP",
    # Genshin EM scaling
    "Kaedehara Kazuha": "SUPPORT_EM", "Sucrose": "SUPPORT_EM",
    # ZZZ Anomaly (EM/Anomaly Proficiency)
    "Nicole": "ANOMALY", "Grace": "ANOMALY", "Piper": "ANOMALY", "Yanagi": "ANOMALY"
}

def clean_value(val_str):
    """Extrai o valor numérico de uma string de status (removendo %, +, etc.)."""
    match = re.search(r'([\d\.]+)', val_str)
    return float(match.group(1)) if match else 0.0

def score_relic(game_id, character_name, slot, main_stat, substats_str):
    """
    Calcula a pontuação de uma relíquia/artefato/disco e retorna a nota (D a SSS) e o score.
    """
    if not substats_str or substats_str.strip() in ["Sem substatus", "Status não disponíveis", ""]:
        return "D", 0.0

    # Determina o arquetipo do personagem
    archetype = CHARACTER_ARCHETYPES.get(character_name, "CRIT_DPS")
    
    # Faz o parse dos substatus
    # Exemplo: "Taxa Crítica: 3.5%, ATQ: 39, Recarga de Energia: 16.2%"
    subs = {}
    parts = substats_str.split(",")
    for p in parts:
        if ":" in p:
            name, val = p.split(":", 1)
            name_clean = name.strip().lower()
            val_num = clean_value(val)
            subs[name_clean] = val_num

    score = 0.0
    
    # 1. Algoritmo CRIT DPS (Padrão para a maioria dos personagens)
    if archetype == "CRIT_DPS":
        # Crit Value (CV) = Dano Crítico + 2 * Taxa Crítica
        crit_rate = subs.get("taxa crítica", subs.get("crit rate", subs.get("taxa crit", 0.0)))
        crit_dmg = subs.get("dano crítico", subs.get("crit dmg", subs.get("dano crit", 0.0)))
        
        # HSR/Genshin/ZZZ podem ter nomes em inglês nos guias
        if not crit_rate:
            crit_rate = next((v for k, v in subs.items() if "rate" in k or "taxa" in k), 0.0)
        if not crit_dmg:
            crit_dmg = next((v for k, v in subs.items() if "dmg" in k or "dano" in k), 0.0)
            
        cv = crit_dmg + (2.0 * crit_rate)
        
        # Adiciona bônus menor para status úteis adicionais (ATQ%, ER, EM/Proficiência, SPD)
        atk_pct = next((v for k, v in subs.items() if "atq" in k or "atk" in k or "attack" in k), 0.0)
        er = next((v for k, v in subs.items() if "recarga" in k or "energy" in k or "er" in k), 0.0)
        spd = next((v for k, v in subs.items() if "vel" in k or "speed" in k or "spd" in k), 0.0)
        
        score = cv + (atk_pct * 0.5) + (spd * 1.5) + (er * 0.2)
        
        # Classificação baseada no score final (CV ponderado)
        if score >= 45: return "SSS", round(score, 1)
        if score >= 35: return "SS", round(score, 1)
        if score >= 28: return "S", round(score, 1)
        if score >= 20: return "A", round(score, 1)
        if score >= 12: return "B", round(score, 1)
        if score >= 5: return "C", round(score, 1)
        return "D", round(score, 1)
        
    # 2. Algoritmo BREAK (HSR)
    elif archetype == "BREAK":
        be = next((v for k, v in subs.items() if "efeito de quebra" in k or "break" in k), 0.0)
        spd = next((v for k, v in subs.items() if "vel" in k or "speed" in k or "spd" in k), 0.0)
        hp_pct = next((v for k, v in subs.items() if "vida" in k or "hp" in k), 0.0)
        
        score = be + (spd * 2.5) + (hp_pct * 0.3)
        
        if score >= 40: return "SSS", round(score, 1)
        if score >= 32: return "SS", round(score, 1)
        if score >= 25: return "S", round(score, 1)
        if score >= 18: return "A", round(score, 1)
        if score >= 10: return "B", round(score, 1)
        return "C", round(score, 1)

    # 3. Algoritmo SUPPORT EM / ANOMALY
    elif archetype in ["SUPPORT_EM", "ANOMALY"]:
        em = next((v for k, v in subs.items() if "proficiência" in k or "mastery" in k or "anomaly" in k or "prof" in k), 0.0)
        er = next((v for k, v in subs.items() if "recarga" in k or "energy" in k), 0.0)
        spd = next((v for k, v in subs.items() if "vel" in k or "speed" in k), 0.0)
        
        score = (em * 0.2) + (er * 0.5) + (spd * 1.5)
        
        if score >= 35: return "SSS", round(score, 1)
        if score >= 28: return "SS", round(score, 1)
        if score >= 22: return "S", round(score, 1)
        if score >= 15: return "A", round(score, 1)
        if score >= 8: return "B", round(score, 1)
        return "C", round(score, 1)

    # 4. Algoritmo HEALER/SUPPORT HP
    else:
        hp_pct = next((v for k, v in subs.items() if "vida" in k or "hp" in k), 0.0)
        er = next((v for k, v in subs.items() if "recarga" in k or "energy" in k), 0.0)
        spd = next((v for k, v in subs.items() if "vel" in k or "speed" in k), 0.0)
        def_pct = next((v for k, v in subs.items() if "def" in k), 0.0)
        
        score = hp_pct + (def_pct * 0.8) + (er * 0.5) + (spd * 2.0)
        
        if score >= 35: return "SSS", round(score, 1)
        if score >= 28: return "SS", round(score, 1)
        if score >= 22: return "S", round(score, 1)
        if score >= 15: return "A", round(score, 1)
        if score >= 8: return "B", round(score, 1)
        return "C", round(score, 1)


# Tabelas de Custo Acumulado de Ascensão de Personagens
# Contém o total aproximado acumulado de XP, Mora/Créditos e Itens de Ascensão de Chefe por nível.
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
    
    # Encontra o marco mais próximo nas tabelas
    def get_closest_values(lvl):
        sorted_keys = sorted(table.keys())
        # Acha o maior marco menor ou igual ao nível
        xp, curr, boss = 0, 0, 0
        for k in sorted_keys:
            if k <= lvl:
                xp = table[k]["xp"]
                curr = table[k]["currency"]
                boss = table[k]["boss"]
            else:
                # Interpolação linear simples para níveis intermediários
                prev_key = next((x for x in reversed(sorted_keys) if x < k), 1)
                factor = (lvl - prev_key) / (k - prev_key)
                xp = table[prev_key]["xp"] + int((table[k]["xp"] - table[prev_key]["xp"]) * factor)
                curr = table[prev_key]["currency"] + int((table[k]["currency"] - table[prev_key]["currency"]) * factor)
                # Itens de chefe geralmente só sobem nas quebras exatas de ascensão
                boss = table[prev_key]["boss"]
                break
        return {"xp": xp, "currency": curr, "boss": boss}
        
    current_res = get_closest_values(current_lvl)
    target_res = get_closest_values(target_lvl)
    
    # Diferença necessária
    xp_diff = max(0, target_res["xp"] - current_res["xp"])
    currency_diff = max(0, target_res["currency"] - current_res["currency"])
    boss_diff = max(0, target_res["boss"] - current_res["boss"])
    
    # Estima quantidade de livros de XP (assumindo livros roxos que valem 20.000 XP)
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
