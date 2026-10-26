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


def is_4star_char(
    name_str: str, rarity_val: Optional[Any] = None, db_rarities: Optional[Dict[str, int]] = None
) -> bool:
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

    clean = re.sub(r"[\.\'\`•]", "", name_clean)
    clean = re.sub(r"\s+", "-", clean)
    return clean


def make_fallback_urls(game_id: str, name_str: str) -> Tuple[str, str]:
    """Gera URLs de fallback de ícone e imagem vertical para o personagem."""
    slug = make_prydwen_slug(game_id, name_str)
    if game_id == "genshin":
        icon = f"/api/proxy_image?url={urllib.parse.quote('https://cdn.prydwen.gg/images/genshin-impact/characters/' + slug + '_icon.webp', safe='')}"
        gacha = f"/api/proxy_image?url={urllib.parse.quote('https://cdn.prydwen.gg/images/genshin-impact/characters/' + slug + '_card.webp', safe='')}"
    elif game_id == "hsr":
        icon = f"/api/proxy_image?url={urllib.parse.quote('https://cdn.prydwen.gg/images/honkai-star-rail/characters/' + slug + '_icon.webp', safe='')}"
        gacha = f"/api/proxy_image?url={urllib.parse.quote('https://cdn.prydwen.gg/images/honkai-star-rail/characters/' + slug + '_card.webp', safe='')}"
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
            "level": c.get("level", 1),
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
                if (
                    m_name
                    and not is_4star_char(m_name, r_dict.get("rarity"), db_rarities)
                    and m_name not in all_chars_map
                ):
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
                        "level": 0,
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
                        m_name = str(item.get("name") or "")
                        if (
                            m_name
                            and not is_4star_char(m_name, item.get("rarity"), db_rarities)
                            and m_name not in all_chars_map
                        ):
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
                                "level": 0,
                            }
        except Exception:
            pass

    chars_list = list(all_chars_map.values())
    chars_list.sort(key=lambda x: (not x["owned"], x["name"]))
    return {"game_id": game_id, "characters": chars_list}


def get_current_banners(game_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retorna os banners atuais extraídos do manifesto static_data/current_banners.json.
    Se o arquivo não existir, executa o scraper para obter e consolidar os dados em tempo real.
    """
    filepath = get_resource_path(os.path.join("static_data", "current_banners.json"))
    data = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[WARN] Erro ao ler current_banners.json: {e}")

    if not data or (game_id and game_id.lower().strip() not in data):
        try:
            from scrapers.scraper_prydwen import PrydwenScraper

            data = PrydwenScraper().get_current_banners(game_id)
        except Exception as e:
            print(f"[WARN] Falha ao extrair banners em tempo real: {e}")

    if game_id:
        clean_g = game_id.lower().strip()
        return data.get(clean_g, {"game_id": clean_g, "patch_info": "", "banners": []})
    return data


def resolve_character_icon(game_id: str, char_name: str, item_type: str = "character") -> str:
    """Resolve a URL segura (proxied) do ícone/foto de qualquer personagem ou item (arma/cone/motor)."""
    clean_g = game_id.lower().strip()

    # 1. Tenta resolver via manifestos estáticos completos e banco de dados de gacha (personagens e armas)
    try:
        from services.gacha_tracker_service import get_gacha_item_icon

        tracker_icon = get_gacha_item_icon(clean_g, char_name, item_type=item_type)
        if tracker_icon:
            return tracker_icon
    except Exception as e:
        print(f"[WARN] Erro ao resolver ícone via tracker para {char_name}: {e}")

    try:
        from static_data_manager import StaticDataManager

        sdm = StaticDataManager()
        prof = sdm.get_character_profile(clean_g, char_name)
        if prof and prof.get("icon"):
            raw_icon = prof["icon"]
            if raw_icon.startswith("http"):
                return f"/api/proxy_image?url={urllib.parse.quote(raw_icon, safe='')}"
            elif clean_g == "hsr" and (raw_icon.startswith("icon/") or "character" in raw_icon):
                full_url = f"https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/{raw_icon}"
                return f"/api/proxy_image?url={urllib.parse.quote(full_url, safe='')}"
            elif raw_icon.startswith("/"):
                return raw_icon
            else:
                return f"/assets/{raw_icon}"
    except Exception as e:
        print(f"[WARN] Erro ao resolver ícone de {char_name}: {e}")

    fb_icon, _ = make_fallback_urls(clean_g, char_name)
    return fb_icon


def get_character_mini_info(
    game_id: str, char_name: str, default_rarity: int = 5, item_type: str = "character"
) -> Dict[str, Any]:
    """Retorna dados simplificados com foto, raridade e elemento do personagem ou arma."""
    clean_g = game_id.lower().strip()
    icon_url = resolve_character_icon(clean_g, char_name, item_type=item_type)
    rarity = default_rarity
    element = None

    try:
        from static_data_manager import StaticDataManager

        sdm = StaticDataManager()
        prof = sdm.get_character_profile(clean_g, char_name)
        if prof:
            if "rarity" in prof:
                try:
                    rarity = int(prof["rarity"])
                except Exception:
                    pass
            element = prof.get("element")
    except Exception:
        pass

    return {
        "name": char_name,
        "icon": icon_url,
        "rarity": rarity,
        "element": element,
    }


def get_gacha_simulator_defaults(
    game_id: str, uid: Optional[str] = None, banner_type: str = "character"
) -> Dict[str, Any]:
    """
    Retorna os valores padrão automáticos para o Simulador de Tiros:
    1. Pity atual e status de 50/50 ou 75/25 calculados a partir do histórico de puxadas do usuário.
    2. Personagem ou arma, título e imagem oficial in-game do banner atual do jogo em destaque como pré-seleção padrão.
    3. Fotos e dados completos dos personagens ou armas 5★ e 4★ ativos no banner.
    4. Suporte a banners de personagem ('character') e de armas/cones/motores ('weapon').
    """
    clean_game = game_id.lower().strip()
    clean_banner_type = (banner_type or "character").lower().strip()

    # 1. Pity Atual e Status 50/50 ou 75/25 (Personagem e Arma)
    char_pity = 0
    char_guaranteed = False
    weapon_pity = 0
    weapon_guaranteed = False

    try:
        from services.gacha_tracker_service import calculate_gacha_tracker_stats

        tracker_stats = calculate_gacha_tracker_stats(game_id=clean_game, uid=uid)
        if tracker_stats:
            if tracker_stats.character_banner:
                char_pity = int(tracker_stats.character_banner.current_pity)
                char_guaranteed = bool(tracker_stats.character_banner.is_guaranteed)
            if tracker_stats.weapon_banner:
                weapon_pity = int(tracker_stats.weapon_banner.current_pity)
                weapon_guaranteed = bool(tracker_stats.weapon_banner.is_guaranteed)
    except Exception as e:
        print(f"[WARN] Erro ao obter estatísticas de gacha tracker para defaults: {e}")

    current_pity = weapon_pity if clean_banner_type == "weapon" else char_pity
    is_guaranteed = weapon_guaranteed if clean_banner_type == "weapon" else char_guaranteed

    # 2. Banners Atuais
    banner_data = get_current_banners(clean_game)
    char_banners_list = banner_data.get("banners", [])
    weapon_banners_list = banner_data.get("weapon_banners", [])
    patch_info = banner_data.get("patch_info", "")

    def _format_banner_item(b: Dict[str, Any], is_weapon: bool = False) -> Dict[str, Any]:
        item_type = "weapon" if is_weapon else "character"
        raw_b_img = b.get("banner_image", "")
        alt_b_img = b.get("remote_banner_image", "")

        # Se for caminho local /assets/, verifica se o arquivo realmente existe fisicamente no disco
        if raw_b_img and raw_b_img.startswith("/assets/"):
            rel_path = raw_b_img.lstrip("/")
            local_exists = os.path.exists(get_resource_path(rel_path))
            if not local_exists and alt_b_img:
                raw_b_img = alt_b_img

        if raw_b_img and not raw_b_img.startswith("/api/proxy_image") and raw_b_img.startswith("http"):
            proxy_img = f"/api/proxy_image?url={urllib.parse.quote(raw_b_img, safe='')}"
        else:
            proxy_img = raw_b_img

        b_name = b.get("character_name", "")
        b_title = b.get("banner_title", "")
        b_info = get_character_mini_info(clean_game, b_name, default_rarity=5, item_type=item_type)
        b_4stars = b.get("featured_4stars", [])
        b_4stars_info = [
            get_character_mini_info(clean_game, f4, default_rarity=4, item_type=item_type)
            for f4 in b_4stars
        ]

        return {
            "character_name": b_name,
            "banner_title": b_title,
            "banner_image": proxy_img,
            "character_info": b_info,
            "featured_4stars": b_4stars,
            "featured_4stars_info": b_4stars_info,
            "is_primary": bool(b.get("is_primary", False)),
            "banner_type": item_type,
        }

    formatted_char_banners = [_format_banner_item(b, is_weapon=False) for b in char_banners_list]
    formatted_weapon_banners = [_format_banner_item(b, is_weapon=True) for b in weapon_banners_list]

    target_list = formatted_weapon_banners if clean_banner_type == "weapon" else formatted_char_banners
    if not target_list and formatted_char_banners:
        target_list = formatted_char_banners

    active_char = None
    active_banner_title = None
    active_banner_img = None
    active_char_info = None
    active_4stars: List[str] = []
    active_4stars_info: List[Dict[str, Any]] = []

    if target_list:
        primary_banner = next((b for b in target_list if b.get("is_primary")), target_list[0])
        active_char = primary_banner.get("character_name")
        active_banner_title = primary_banner.get("banner_title")
        active_banner_img = primary_banner.get("banner_image")
        active_char_info = primary_banner.get("character_info")
        active_4stars = primary_banner.get("featured_4stars", [])
        active_4stars_info = primary_banner.get("featured_4stars_info", [])

    return {
        "game_id": clean_game,
        "banner_type": clean_banner_type,
        "current_pity": current_pity,
        "is_guaranteed": is_guaranteed,
        "character_pity": char_pity,
        "character_guaranteed": char_guaranteed,
        "weapon_pity": weapon_pity,
        "weapon_guaranteed": weapon_guaranteed,
        "active_banner_character": active_char,
        "active_banner_title": active_banner_title,
        "active_banner_image": active_banner_img,
        "active_character_info": active_char_info,
        "featured_4stars": active_4stars,
        "featured_4stars_info": active_4stars_info,
        "patch_info": patch_info,
        "available_banners": formatted_char_banners,
        "available_weapon_banners": formatted_weapon_banners,
    }

