import os
import re
import json
import urllib.parse
from typing import Dict, Any, List, Set, Optional, Tuple

import database
from core.config import get_resource_path
from services.roster_service import get_roster

def _load_known_4star_names() -> Set[str]:
    filepath = get_resource_path(os.path.join("static_data", "known_4star_characters.json"))
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_4s = set()
                for lst in data.values():
                    all_4s.update([x.lower().strip() for x in lst])
                return all_4s
        except Exception as e:
            print(f"[WARN] Erro ao ler known_4star_characters.json: {e}")
    return set()

KNOWN_4STAR_NAMES: Set[str] = _load_known_4star_names()

def _load_slug_mappings() -> Dict[str, str]:
    filepath = get_resource_path(os.path.join("static_data", "prydwen_slug_mappings.json"))
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Erro ao ler prydwen_slug_mappings.json: {e}")
    return {}

PRYDWEN_SLUG_MAP: Dict[str, str] = _load_slug_mappings()

def is_4star_char(name_str: str, rarity_val: Optional[Any] = None, db_rarities: Optional[Dict[str, int]] = None) -> bool:
    """Verifica se um personagem é 4★ / Rank A para exclusão do simulador de gacha."""
    name_clean = name_str.lower().strip()
    if name_clean in KNOWN_4STAR_NAMES:
        return True
    if db_rarities and name_clean in db_rarities and db_rarities[name_clean] < 5:
        return True
    if rarity_val is not None:
        try:
            if int(rarity_val) < 5:
                return True
        except Exception:
            pass
        if str(rarity_val).strip().upper() in ["4", "A", "4-STAR", "A-RANK", "4.0"]:
            return True
    return False

def make_prydwen_slug(game_id: str, name_str: str) -> str:
    """Gera o slug URL correspondente no Prydwen para o personagem."""
    if game_id == "zzz":
        from extractor import get_zzz_prydwen_slug
        slug = get_zzz_prydwen_slug(name_str)
        if slug:
            return slug
    
    name_clean = name_str.lower().strip()
    if name_clean in PRYDWEN_SLUG_MAP:
        return PRYDWEN_SLUG_MAP[name_clean]
        
    clean = re.sub(r'[\.\'\`•]', '', name_clean)
    clean = re.sub(r'\s+', '-', clean)
    return clean

def make_fallback_urls(game_id: str, name_str: str) -> Tuple[str, str]:
    """Gera URLs de fallback de ícone e imagem vertical para o personagem."""
    slug = make_prydwen_slug(game_id, name_str)
    if game_id == "genshin":
        icon = f"/api/proxy_image?url={urllib.parse.quote('https://cdn.prydwen.gg/images/genshin-impact/characters/' + slug + '_icon.webp', safe='')}"
        gacha = f"/api/proxy_image?url={urllib.parse.quote('https://cdn.prydwen.gg/images/genshin-impact/characters/' + slug + '_card.webp', safe='')}"
    elif game_id == "hsr":
        icon = f"/api/proxy_image?url={urllib.parse.quote('https://cdn.prydwen.gg/images/star-rail/characters/' + slug + '_icon.webp', safe='')}"
        gacha = f"/api/proxy_image?url={urllib.parse.quote('https://cdn.prydwen.gg/images/star-rail/characters/' + slug + '_card.webp', safe='')}"
    else:  # zzz
        icon = f"/api/proxy_image?url={urllib.parse.quote('https://cdn.prydwen.gg/images/zenless-zone-zero/characters/' + slug + '_icon.webp', safe='')}"
        gacha = f"/api/proxy_image?url={urllib.parse.quote('https://cdn.prydwen.gg/images/zenless-zone-zero/characters/' + slug + '_full.webp', safe='')}"
    return icon, gacha

async def get_gacha_characters(game_id: str) -> Dict[str, Any]:
    """
    Retorna a lista de personagens 5★ (Lendários / Rank S) para o simulador de gacha.
    Garante rigorosamente que:
    1. Personagens 4★ / Rank A sejam EXCLUÍDOS tanto dos possuídos quanto dos não possuídos.
    2. Imagens (icon e gacha_art) sejam resolvidas via Roster, SQLite ou Prydwen/Enka proxy fallback.
    """
    game_id = game_id.lower().strip()
    if game_id not in ["genshin", "hsr", "zzz"]:
        raise ValueError("Jogo inválido. Use 'genshin', 'hsr' ou 'zzz'.")

    # 0. Mapa de raridades do banco SQLite para conferência exata
    db_rarities = {}
    try:
        with database.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name, rarity FROM characters WHERE game_id = ?", (game_id,))
            for r in cur.fetchall():
                db_rarities[r["name"].lower().strip()] = int(r["rarity"])
    except Exception as e:
        print(f"Aviso ao buscar db_rarities: {e}")

    # 1. Roster do Usuário (Apenas personagens 5★ possuídos)
    roster_map = {}
    try:
        roster_data = await get_roster(game_id)
        if isinstance(roster_data, list):
            for c in roster_data:
                c_name = c.get("name")
                if c_name and not is_4star_char(c_name, c.get("rarity"), db_rarities):
                    roster_map[c_name] = c
    except Exception as e:
        print(f"Aviso ao buscar roster no gacha chars: {e}")

    all_chars_map = {}

    # Adicionar personagens 5★ do roster
    for name, c in roster_map.items():
        rank_str = c.get("rank_str") or "C0"
        rank_num = 0
        if rank_str and len(rank_str) > 1 and rank_str[1:].isdigit():
            rank_num = int(rank_str[1:])
            
        icon = c.get("icon")
        gacha_art = c.get("gacha_art")
        if not icon or not gacha_art:
            fb_icon, fb_gacha = make_fallback_urls(game_id, name)
            icon = icon or fb_icon
            gacha_art = gacha_art or fb_gacha

        all_chars_map[name] = {
            "name": name,
            "rarity": 5,
            "element": c.get("element", ""),
            "icon": icon,
            "gacha_art": gacha_art,
            "owned": True,
            "current_rank": rank_num,
            "rank_str": rank_str,
            "level": c.get("level", 1)
        }

    # 2. Adicionar outros personagens 5★ salvos no banco SQLite (não possuídos)
    try:
        with database.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name, rarity, element, icon, gacha_art FROM characters WHERE game_id = ?", (game_id,))
            db_rows = cur.fetchall()
            for r in db_rows:
                r_dict = dict(r)
                m_name = r_dict.get("name")
                if m_name and not is_4star_char(m_name, r_dict.get("rarity"), db_rarities) and m_name not in all_chars_map:
                    fb_icon, fb_gacha = make_fallback_urls(game_id, m_name)
                    icon = r_dict.get("icon") or fb_icon
                    gacha_art = r_dict.get("gacha_art") or fb_gacha
                    
                    if icon and not icon.startswith("/api/proxy_image") and icon.startswith("http"):
                        icon = f"/api/proxy_image?url={urllib.parse.quote(icon, safe='')}"
                    if gacha_art and not gacha_art.startswith("/api/proxy_image") and gacha_art.startswith("http"):
                        gacha_art = f"/api/proxy_image?url={urllib.parse.quote(gacha_art, safe='')}"

                    all_chars_map[m_name] = {
                        "name": m_name,
                        "rarity": 5,
                        "element": r_dict.get("element", ""),
                        "icon": icon,
                        "gacha_art": gacha_art,
                        "owned": False,
                        "current_rank": -1,
                        "rank_str": None,
                        "level": 0
                    }
    except Exception as e:
        print(f"Aviso ao consultar SQLite no gacha chars: {e}")

    # 3. Adicionar da meta_data JSON apenas se for 5★
    meta_json_path = f"{game_id}/meta_data_{game_id}.json"
    if os.path.exists(meta_json_path):
        try:
            with open(meta_json_path, "r", encoding="utf-8") as jf:
                mdata = json.load(jf)
                for item in mdata.values():
                    if isinstance(item, dict) and item.get("name"):
                        m_name = item.get("name")
                        if not is_4star_char(m_name, item.get("rarity"), db_rarities) and m_name not in all_chars_map:
                            fb_icon, fb_gacha = make_fallback_urls(game_id, m_name)
                            all_chars_map[m_name] = {
                                "name": m_name,
                                "rarity": 5,
                                "element": item.get("element", ""),
                                "icon": item.get("icon") or fb_icon,
                                "gacha_art": item.get("gacha_art") or fb_gacha,
                                "owned": False,
                                "current_rank": -1,
                                "rank_str": None,
                                "level": 0
                            }
        except Exception:
            pass

    chars_list = list(all_chars_map.values())
    chars_list.sort(key=lambda x: (not x["owned"], x["name"]))
    return {"game_id": game_id, "characters": chars_list}
