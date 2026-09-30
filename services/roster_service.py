import os
import re
import json
import urllib.parse
from typing import List, Dict, Any, Optional

import database
from core.config import get_resource_path
from services.media_service import get_raw_url
from services.translation_service import traduzir_item
from extractor import clean_relic_name, sanitize_stat_name
from build_calculator import (
    score_relic,
    get_meta_data,
    extract_weights_from_guide,
    normalize_char_name,
)
import meta_comparator

# Carrega elementos conhecidos de static_data
def _load_character_elements() -> Dict[str, Dict[str, str]]:
    elements_file = get_resource_path(os.path.join("static_data", "character_elements.json"))
    if os.path.exists(elements_file):
        try:
            with open(elements_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Erro ao ler character_elements.json: {e}")
    return {"genshin": {}, "zzz": {}}

CHARACTER_ELEMENTS = _load_character_elements()

def parse_roster_md_fallback(game_id: str) -> List[Dict[str, Any]]:
    """Fallback de parsing a partir do arquivo Markdown se o banco SQLite estiver vazio."""
    md_path = f"{game_id}/roster_{game_id}.md"
    chars = []
    if not os.path.exists(md_path):
        return chars

    genshin_elements = CHARACTER_ELEMENTS.get("genshin", {})
    zzz_elements = CHARACTER_ELEMENTS.get("zzz", {})

    try:
        with open(md_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("|") and not line.startswith("| Personagem") and not line.startswith("| :---"):
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 7:
                        cname = parts[1].replace("**", "").strip()
                        lvl_str = parts[2].replace("Nv.", "").strip()
                        try:
                            lvl = int(lvl_str)
                        except Exception:
                            lvl = 1
                        stars = parts[3].count("⭐")
                        if stars == 0:
                            stars = 5 if "5" in parts[3] else 4
                        c_str = parts[4].strip()
                        w_str = parts[5].strip()
                        w_name, w_lvl, w_rank = w_str, 90, 1
                        w_m = re.search(r'^(.*?)\s*\(Nv\.\s*(\d+),\s*R(\d+)\)$', w_str)
                        if w_m:
                            w_name = w_m.group(1).strip()
                            w_lvl = int(w_m.group(2))
                            w_rank = int(w_m.group(3))

                        elem = "Anemo"
                        if game_id == "genshin":
                            elem = genshin_elements.get(cname.lower(), "Anemo")
                        elif game_id == "zzz":
                            elem = zzz_elements.get(cname.lower(), "PHYSICAL")

                        chars.append({
                            "id": "",
                            "uid": "",
                            "name": cname,
                            "level": lvl,
                            "rarity": stars,
                            "rank_str": c_str,
                            "element": elem,
                            "icon": f"/api/proxy_image?url=https%3A%2F%2Fenka.network%2Fui%2FUI_AvatarIcon_{cname}.png",
                            "gacha_art": None,
                            "weapon": {
                                "name": w_name,
                                "level": w_lvl,
                                "rank": w_rank,
                                "icon": ""
                            } if w_name and w_name != "Nenhuma" else None,
                            "relics": []
                        })
    except Exception as e:
        print(f"Aviso ao realizar parse de fallback do MD para {game_id}: {e}")
    return chars

async def get_roster(game_id: str) -> List[Dict[str, Any]]:
    """Retorna e enriquece os dados dos personagens salvos no roster local."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise ValueError("Jogo inválido. Escolha 'hsr', 'genshin' ou 'zzz'.")
        
    data = None
    # 1. Tenta carregar do SQLite primeiro
    try:
        data = database.get_roster_data(game_id)
    except Exception as e:
        print(f"Aviso ao carregar roster do SQLite para {game_id}: {e}")
        
    # 2. Se não carregou do SQLite, tenta do JSON
    if not data:
        json_path = f"{game_id}/roster_data_{game_id}.json"
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
            except Exception as e:
                raise RuntimeError(f"Erro ao carregar banco de dados local: {e}")

    # 3. Fallback de emergência APENAS se SQLite e JSON estiverem totalmente vazios
    if not data:
        data = parse_roster_md_fallback(game_id)
                
    if data:
        # Enriquece gacha_art do JSON se faltar no banco
        json_path = f"{game_id}/roster_data_{game_id}.json"
        json_map = {}
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    jdata = json.load(jf)
                    for jc in jdata:
                        if jc.get("name") and jc.get("gacha_art"):
                            json_map[jc["name"]] = jc["gacha_art"]
            except Exception:
                pass

        # Pondera e calcula as notas de cada relíquia do roster e a nota geral da build
        max_slots = 5 if game_id == "genshin" else 6
        for char in data:
            if char.get("name") in json_map and json_map[char["name"]]:
                char["gacha_art"] = json_map[char["name"]]

            # Garante fallback de gacha_art em HD para ZZZ e skins do Genshin
            if game_id == "zzz":
                from extractor import get_zzz_prydwen_slug
                icon_str = get_raw_url(char.get("icon") or "")
                g_art_str = get_raw_url(char.get("gacha_art") or "")
                check_str = icon_str + " " + g_art_str
                match = re.search(r'(?:role_square_avatar|role_vertical_painting)_(\d+)_(\d{7,})\.png', check_str)
                if match:
                    base_id, skin_id = match.group(1), match.group(2)
                    char["gacha_art"] = f"https://act-webstatic.hoyoverse.com/game_record/zzzv2/role_vertical_painting/role_vertical_painting_{base_id}_{skin_id}.png"
                else:
                    slug = get_zzz_prydwen_slug(char.get("name", ""))
                    if slug:
                        char["gacha_art"] = f"https://cdn.prydwen.gg/images/zenless-zone-zero/characters/{slug}_full.webp"
            elif game_id == "genshin":
                from extractor import sanitize_genshin_url
                if char.get("icon"):
                    char["icon"] = sanitize_genshin_url(char["icon"])
                if char.get("gacha_art"):
                    char["gacha_art"] = sanitize_genshin_url(char["gacha_art"])

                raw_g_art = get_raw_url(char.get("gacha_art") or "")
                raw_c_icon = get_raw_url(char.get("icon") or "")
                combined_check = raw_c_icon + " " + raw_g_art
                
                skin_match = re.search(r'(UI_AvatarIcon_[A-Za-z0-9_]+Costume[A-Za-z0-9_]*)', combined_check)
                if skin_match:
                    skin_fn = skin_match.group(1)
                    char["gacha_art"] = f"https://enka.network/ui/{skin_fn.replace('UI_AvatarIcon_', 'UI_Costume_')}.png"
                    if not raw_c_icon or "UI_AvatarIcon_" not in raw_c_icon:
                        char["icon"] = f"https://enka.network/ui/{skin_fn}.png"

            # Garante proxy interno para URLs de imagem externas evitando 403 Forbidden e duplicação
            if char.get("icon"):
                raw_icon = get_raw_url(char["icon"])
                if raw_icon.startswith("http"):
                    char["icon"] = f"/api/proxy_image?url={urllib.parse.quote(raw_icon, safe='')}"
            if char.get("gacha_art"):
                raw_gacha = get_raw_url(char["gacha_art"])
                if raw_gacha.startswith("http"):
                    char["gacha_art"] = f"/api/proxy_image?url={urllib.parse.quote(raw_gacha, safe='')}"
            if isinstance(char.get("weapon"), dict) and char["weapon"].get("icon"):
                raw_w_icon = get_raw_url(char["weapon"]["icon"])
                if raw_w_icon.startswith("http"):
                    char["weapon"]["icon"] = f"/api/proxy_image?url={urllib.parse.quote(raw_w_icon, safe='')}"

            char_id_val = str(char.get("id") or char.get("character_id") or "")
            meta_db = get_meta_data(game_id)
            c_name = char.get("name") or ""
            char_meta = meta_db.get(char_id_val) or meta_db.get(c_name.lower()) or meta_db.get(normalize_char_name(c_name)) or {}
            if char_meta:
                char["substats_priority"] = char_meta.get("substats_priority", [])
                char["recommended_weights"] = extract_weights_from_guide(game_id, char_id_val)

            relic_scores = []
            relics = char.get("relics") or char.get("artifacts") or char.get("discs") or []
            for relic in relics:
                if "name" in relic:
                    relic["name"] = clean_relic_name(relic["name"])
                if "main" in relic:
                    relic["main"] = sanitize_stat_name(relic["main"])
                if "sub" in relic and relic["sub"]:
                    subs_list = [sanitize_stat_name(s.strip()) for s in str(relic["sub"]).split(",") if s.strip()]
                    relic["sub"] = ", ".join(subs_list)
                if relic.get("icon"):
                    raw_r_icon = get_raw_url(relic["icon"])
                    if raw_r_icon.startswith("http"):
                        relic["icon"] = f"/api/proxy_image?url={urllib.parse.quote(raw_r_icon, safe='')}"

                grade, score = score_relic(
                    game_id=game_id,
                    char_id=char_id_val,
                    slot=str(relic.get("slot", "")),
                    main_stat=relic.get("main") or relic.get("main_stat") or "",
                    substats_str=relic.get("sub", "")
                )
                relic["grade"] = grade
                relic["score"] = score
                relic_scores.append(score)
            
            equipped_count = len(relic_scores)
            if relic_scores and max_slots > 0:
                avg_score = round(sum(relic_scores) / max_slots, 1)
            else:
                avg_score = 0.0

            if avg_score >= 90.0: overall_grade = "SSS"
            elif avg_score >= 75.0: overall_grade = "SS"
            elif avg_score >= 60.0: overall_grade = "S"
            elif avg_score >= 45.0: overall_grade = "A"
            elif avg_score >= 30.0: overall_grade = "B"
            elif avg_score >= 15.0: overall_grade = "C"
            else: overall_grade = "D"

            char["overall_score"] = avg_score
            char["overall_grade"] = overall_grade
            char["equipped_pieces"] = equipped_count
            char["max_pieces"] = max_slots
        return data
        
    return []

def get_character_build_detail(game_id: str, char_name: str) -> str:
    """Busca o detalhe textual da build do personagem a partir do SQLite ou do arquivo Markdown."""
    try:
        db_md = database.get_character_build_md(game_id, char_name)
        if db_md:
            return db_md
    except Exception as e:
        print(f"Erro ao buscar build no SQLite para {char_name}: {e}")

    filepath = f"{game_id}/roster_{game_id}.md"
    if not os.path.exists(filepath):
        return ""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        pattern = rf'(\*\*(?:Personagem|Agente):\*\*\s*{re.escape(char_name)}.*?)(?=\n\*\*(?:Personagem|Agente):\*\*|\n## |\Z)'
        match = re.search(pattern, content, re.DOTALL | re.I)
        if match:
            return match.group(1).strip()
    except Exception as e:
        print(f"Erro ao buscar detalhes da build de {char_name}: {e}")
    return ""

def parse_character_build_data(game_id: str, char_name: str) -> Dict[str, Any]:
    """Extrai com precisão máxima os dados da build atual do jogador consultando primariamente o SQLite."""
    data = {
        "name": char_name,
        "weapon": "Não informado",
        "weapon_clean": "",
        "sets": [],
        "stats": {},
        "pieces": []
    }
    
    # 1. Tenta buscar no banco SQLite (fonte mais rica e estruturada)
    char_db = None
    try:
        roster = database.get_roster_data(game_id)
        c_norm = normalize_char_name(char_name)
        for c in roster:
            if normalize_char_name(c.get("name", "")) == c_norm or c.get("name", "").lower() == char_name.lower():
                char_db = c
                break
    except Exception as e:
        print(f"[WARN] Erro ao consultar SQLite para {char_name}: {e}")

    if char_db:
        # Arma
        w = char_db.get("weapon")
        if isinstance(w, dict) and w.get("name"):
            lvl = w.get("level", 1)
            rnk = w.get("rank", 1)
            data["weapon"] = f"{w['name']} (Nv. {lvl}, R{rnk})"
            data["weapon_clean"] = w["name"]
        elif isinstance(w, str) and w:
            data["weapon"] = w
            data["weapon_clean"] = re.sub(r'\s*\([^)]*\)', '', w).strip()
            
        # Combat Stats
        if char_db.get("stats"):
            data["stats"] = dict(char_db["stats"])
            
        # Peças de Relíquias / Artefatos / Discos
        for r in char_db.get("relics", []):
            slot = r.get("slot", "")
            slot_clean = slot
            if game_id == "genshin":
                if slot in ["1", "flor", "flower"]: slot_clean = "Flor"
                elif slot in ["2", "pena", "plume"]: slot_clean = "Pena"
                elif slot in ["3", "areia", "sands"]: slot_clean = "Areia"
                elif slot in ["4", "copo", "calice", "goblet"]: slot_clean = "Copo"
                elif slot in ["5", "tiara", "coroa", "circlet"]: slot_clean = "Tiara"
            elif game_id == "hsr":
                if "cabeça" in slot.lower() or slot == "1": slot_clean = "Cabeça"
                elif "mãos" in slot.lower() or slot == "2": slot_clean = "Mãos"
                elif "corpo" in slot.lower() or slot == "3": slot_clean = "Corpo"
                elif "pés" in slot.lower() or "bota" in slot.lower() or slot == "4": slot_clean = "Bota"
                elif "esfera" in slot.lower() or slot == "5": slot_clean = "Esfera"
                elif "corda" in slot.lower() or slot == "6": slot_clean = "Corda"
            elif game_id == "zzz":
                slot_clean = slot.replace("Disk", "Disco").replace("disk", "Disco").replace("slot_", "Disco ")
                
            data["pieces"].append({
                "slot": slot_clean,
                "name": r.get("name", ""),
                "main": r.get("main", ""),
                "sub": r.get("sub", ""),
                "icon": r.get("icon", "")
            })

    # 2. Busca conjuntos (sets) ativos no roster_{game_id}.md ou roster_data_{game_id}.json
    try:
        raw_text = get_character_build_detail(game_id, char_name)
        if raw_text:
            m_s = re.search(r'-\s*\*\*(?:Relíquias|Artefatos|Discos):\*\*\s*(.*)', raw_text)
            if m_s:
                sets_raw = m_s.group(1).strip()
                data["sets"] = [s.strip() for s in sets_raw.split('+') if s.strip()]
            if not data["weapon"] or data["weapon"] == "Não informado":
                m_w = re.search(r'-\s*\*\*(?:Cone de Luz|Arma|W-Engine):\*\*\s*(.*)', raw_text)
                if m_w:
                    data["weapon"] = m_w.group(1).strip()
                    data["weapon_clean"] = re.sub(r'\s*\([^)]*\)', '', data["weapon"]).strip()
    except Exception as e:
        print(f"[WARN] Erro ao extrair conjuntos do markdown para {char_name}: {e}")

    # 3. Fallback de stats do roster_data_{game_id}.json se ainda estiver vazio
    if not data["stats"]:
        try:
            json_path = f"{game_id}/roster_data_{game_id}.json"
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8", errors="ignore") as jf:
                    roster_data = json.load(jf)
                char_lower = char_name.lower().strip()
                for c in roster_data:
                    if c.get("name", "").lower().strip() == char_lower:
                        if c.get("stats"):
                            data["stats"] = c["stats"]
                        break
        except Exception:
            pass

    return data

def parse_meta_target(game_id: str, char_name: str, element: str = "") -> Dict[str, Any]:
    """Calcula e retorna as referências do meta ideais para um personagem."""
    meta_json = get_meta_data(game_id)
    try:
        roster = database.get_roster_data(game_id)
    except Exception:
        roster = None
    return meta_comparator.parse_meta_target(
        game_id=game_id,
        char_name=char_name,
        element=element,
        meta_json=meta_json,
        roster_data=roster,
        translate_fn=traduzir_item
    )

def get_overview() -> Dict[str, Any]:
    """Gera dados resumidos consolidados dos 3 jogos mesclando SQLite e arquivos locais."""
    db_overview = {}
    try:
        db_overview = database.get_overview_data()
    except Exception as e:
        print(f"Erro ao buscar visão geral no SQLite: {e}")

    overview = {}
    for game in ["hsr", "genshin", "zzz"]:
        fallback_info = {"active": False, "uid": "Não sincronizado", "level": "N/A", "char_count": 0, "five_stars": 0}
        
        json_path = f"{game}/roster_data_{game}.json"
        md_path = f"{game}/roster_{game}.md"
        
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    fallback_info["char_count"] = len(data)
                    if game == "zzz":
                        fallback_info["five_stars"] = sum(1 for c in data if str(c.get("rarity")) in ["5", "S"])
                    else:
                        fallback_info["five_stars"] = sum(1 for c in data if c.get("rarity") == 5)
                    fallback_info["active"] = True
            except Exception:
                pass
                
        if os.path.exists(md_path):
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                m_uid = re.search(r'UID[:\*]*\s*(\d+)', content)
                if m_uid:
                    fallback_info["uid"] = m_uid.group(1)
                    
                if game == "hsr":
                    m_lvl = re.search(r'Nível de Desbravamento[:\*]*\s*(\d+)', content)
                elif game == "genshin":
                    m_lvl = re.search(r'Rank de Aventura[:\*]*\s*(\d+)', content)
                else:  # zzz
                    m_lvl = re.search(r'Nível de Intermediário[:\*]*\s*(\d+)', content)
                    
                if m_lvl:
                    fallback_info["level"] = m_lvl.group(1)
            except Exception:
                pass

        db_game = db_overview.get(game, {})
        if db_game and db_game.get("active") and db_game.get("char_count", 0) > 0:
            overview[game] = db_game
        elif fallback_info["active"] and fallback_info.get("char_count", 0) > 0:
            overview[game] = fallback_info
        else:
            overview[game] = db_game if db_game else fallback_info
            
    return overview

async def get_account_audit(game_id: str) -> Dict[str, Any]:
    """Retorna relatório de auditoria de saúde da conta + Tier List dos seus personagens."""
    roster = await get_roster(game_id)
    if not roster:
        return {
            "game_id": game_id,
            "total_characters": 0,
            "avg_rv": 0.0,
            "tier_list": {"S+": [], "S": [], "A": [], "B": [], "C/D": []},
            "sss_count": 0,
            "s_count": 0
        }
        
    tier_list: Dict[str, List[Dict[str, Any]]] = {"S+": [], "S": [], "A": [], "B": [], "C/D": []}
    scores = []
    
    for char in roster:
        name = char.get("name")
        icon = char.get("icon")
        rarity = char.get("rarity", 4)
        level = char.get("level", 1)
        score = char.get("overall_score", 0.0)
        grade = char.get("overall_grade", "D")
        scores.append(score)
        
        char_entry = {
            "name": name,
            "icon": icon,
            "rarity": rarity,
            "level": level,
            "score": score,
            "grade": grade
        }
        
        if score >= 85.0 or grade in ["SSS", "SS"]:
            tier_list["S+"].append(char_entry)
        elif score >= 65.0 or grade == "S":
            tier_list["S"].append(char_entry)
        elif score >= 45.0 or grade == "A":
            tier_list["A"].append(char_entry)
        elif score >= 30.0 or grade == "B":
            tier_list["B"].append(char_entry)
        else:
            tier_list["C/D"].append(char_entry)
            
    avg_rv = round(sum(scores) / len(scores), 1) if scores else 0.0
    
    return {
        "game_id": game_id,
        "total_characters": len(roster),
        "avg_rv": avg_rv,
        "tier_list": tier_list,
        "sss_count": sum(1 for s in scores if s >= 90.0),
        "s_count": sum(1 for s in scores if s >= 60.0)
    }
