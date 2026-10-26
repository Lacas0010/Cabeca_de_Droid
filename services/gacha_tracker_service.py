import os
import json
import urllib.parse
import unicodedata
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union

import database
from schemas.gacha_tracker import (
    GachaPullItem,
    FiveStarRecord,
    BannerTrackerStats,
    GachaTrackerOverviewResponse,
    GachaHistoryListResponse,
    ImportGachaResponse,
)

# Mapeamento oficial de chaves de jogos no formato universal UIGF v4.x
UIGF_GAME_KEY_MAP = {
    "hk4e": "genshin",
    "hkrpg": "hsr",
    "nap": "zzz",
}

# Mapeamento oficial de gacha_type das APIs da HoYoverse para categorias canônicas
GACHA_TYPE_MAPPING = {
    # Genshin Impact
    "100": "beginner",
    "200": "standard",
    "301": "character",
    "400": "character",  # Banner duplo
    "302": "weapon",
    "500": "chronicled",
    # Honkai: Star Rail
    "1": "standard",
    "2": "beginner",
    "11": "character",
    "12": "weapon",
    "21": "collab",  # Banner collab personagem (Saber, Rin Tohsaka)
    "22": "collab",  # Banner collab cone (A Thankless Coronation)
    # Zenless Zone Zero
    "1001": "standard",
    "2001": "character",
    "3001": "weapon",
    "5001": "bangboo",
}

# Personagens 5★ Permanentes do Mochileiro Padrão
STANDARD_5_STARS = {
    "genshin": ["diluc", "jean", "keqing", "mona", "qiqi", "tighnari", "dehya"],
    "hsr": ["bailu", "bronya", "clara", "gepard", "himeko", "welt", "yanqing"],
    "zzz": ["koleda", "nekomata", "grace", "rina", "lycaon", "soldier 11", "soldado 11"],
}

# Cache em memória para os manifestos de ícones estáticos
_STATIC_ICONS_CACHE: Dict[str, Dict[str, str]] = {}


def get_gacha_item_icon(game_id: str, item_name: str, item_type: str = "character") -> str:
    """
    Resolve o ícone oficial ou arte do item (personagem, cone, arma, motor-w ou bangboo)
    utilizando cache local de manifestos, banco SQLite e fallbacks com proxy.
    """
    clean_game = (game_id or "hsr").lower().strip()
    name_clean = (item_name or "").strip()
    name_lower = name_clean.lower()
    if not name_clean:
        return ""

    # 1. Carrega manifest de ícones estáticos do jogo se não estiver em cache
    if clean_game not in _STATIC_ICONS_CACHE or not _STATIC_ICONS_CACHE[clean_game]:
        _STATIC_ICONS_CACHE[clean_game] = {}
        manifest_path = os.path.join(database.BASE_DIR, "static_data", f"{clean_game}_gacha_icons.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    _STATIC_ICONS_CACHE[clean_game] = json.load(f)
            except Exception:
                pass

    cached_icon = _STATIC_ICONS_CACHE.get(clean_game, {}).get(name_lower)
    if not cached_icon:
        name_no_accents = "".join(
            c for c in unicodedata.normalize("NFD", name_lower) if unicodedata.category(c) != "Mn"
        )
        cached_icon = _STATIC_ICONS_CACHE.get(clean_game, {}).get(name_no_accents)

    if not cached_icon:
        # Variações comuns de pontuação e apóstrofos (ex: Sharpshooter's Oath vs Sharpshooter s Oath vs Sharpshooters)
        clean_punct = " ".join(name_lower.replace("'", " ").replace("-", " ").split())
        clean_hyphen = "-".join(clean_punct.split())
        clean_no_quote = name_lower.replace("'", "")
        game_icons = _STATIC_ICONS_CACHE.get(clean_game, {})
        cached_icon = (
            game_icons.get(clean_punct)
            or game_icons.get(clean_hyphen)
            or game_icons.get(clean_no_quote)
            or game_icons.get(clean_no_quote.replace(" ", "-"))
        )

    if not cached_icon and clean_game == "zzz":
        zzz_aliases = {
            "soldier 11": "n.º 11",
            "soldado 11": "n.º 11",
            "n.º 11": "soldier 11",
            "orphie & magus": "orfeu & magus",
            "orfeu & magus": "orphie & magus",
            "cissia": "císsia",
            "císsia": "cissia",
        }
        alias = zzz_aliases.get(name_lower)
        if alias:
            cached_icon = _STATIC_ICONS_CACHE.get(clean_game, {}).get(alias)

    if cached_icon:
        if cached_icon.startswith("http"):
            return f"/api/proxy_image?url={urllib.parse.quote(cached_icon, safe='')}"
        return cached_icon

    # 2. Consulta tabela characters no banco SQLite
    try:
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT icon FROM characters WHERE game_id = ? AND LOWER(name) = ? LIMIT 1",
                (clean_game, name_lower),
            )
            row = cursor.fetchone()
            if row and row["icon"]:
                raw_url = str(row["icon"])
                if raw_url.startswith("http"):
                    return f"/api/proxy_image?url={urllib.parse.quote(raw_url, safe='')}"
                return raw_url

            cursor.execute(
                "SELECT weapon_icon FROM characters WHERE game_id = ? AND LOWER(weapon_name) = ? LIMIT 1",
                (clean_game, name_lower),
            )
            row_w = cursor.fetchone()
            if row_w and row_w["weapon_icon"]:
                raw_w = str(row_w["weapon_icon"])
                if raw_w.startswith("http"):
                    return f"/api/proxy_image?url={urllib.parse.quote(raw_w, safe='')}"
                return raw_w
    except Exception:
        pass

    # 3. Fallbacks inteligentes por jogo
    slug = name_lower.replace(" ", "-").replace("'", "").replace("[", "").replace("]", "").replace(":", "")
    clean_pascal = "".join(part.capitalize() for part in name_clean.split())

    if clean_game == "genshin":
        if item_type == "weapon" or any(
            w in name_lower for w in ["bow", "sword", "spear", "claymore", "catalyst", "queller", "tassel", "slingshot"]
        ):
            raw = f"https://genshin.jmp.blue/weapons/{slug}/icon"
        else:
            raw = f"https://enka.network/ui/UI_AvatarIcon_{clean_pascal}.png"
        return f"/api/proxy_image?url={urllib.parse.quote(raw, safe='')}"

    elif clean_game == "hsr":
        if item_type == "weapon":
            raw = f"https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/light_cone/{slug}.png"
        else:
            raw = f"https://cdn.prydwen.gg/images/star-rail/characters/{slug}_icon.webp"
        return f"/api/proxy_image?url={urllib.parse.quote(raw, safe='')}"

    elif clean_game == "zzz":
        if (
            item_type == "bangboo"
            or name_lower.endswith("boo")
            or name_lower.startswith("boo")
            or slug
            in [
                "ariel",
                "safety",
                "bangvolver",
                "sharkboo",
                "amillion",
                "butler",
                "robin",
                "belion",
                "snap",
                "sprout",
                "ultra-jake",
                "miss-esme",
                "red-moccus",
            ]
        ):
            raw = f"https://cdn.prydwen.gg/images/zenless-zone-zero/bangboos/{slug}.webp"
        elif item_type == "weapon":
            raw = ""
        else:
            raw = f"https://cdn.prydwen.gg/images/zenless-zone-zero/characters/{slug}_icon.webp"
        if raw:
            return f"/api/proxy_image?url={urllib.parse.quote(raw, safe='')}"
        return ""

    return ""


def reload_icons_cache(game_id: Optional[str] = None) -> None:
    """Invalida e recarrega o cache de manifestos de ícones estáticos em memória."""
    global _STATIC_ICONS_CACHE
    if game_id:
        clean = game_id.lower().strip()
        _STATIC_ICONS_CACHE.pop(clean, None)
    else:
        _STATIC_ICONS_CACHE.clear()


def normalize_banner_category(game_id: str, gacha_type: str, fallback_cat: str = "") -> str:
    """Normaliza o tipo de banner a partir do gacha_type numérico ou textual preservando categorias específicas."""
    clean_game = (game_id or "").lower().strip()
    gt_clean = str(gacha_type or "").strip()
    fb = (fallback_cat or "").lower().strip()

    # Preserva categorias canônicas explícitas já persistidas
    if fb in ["collab", "beginner", "bangboo", "chronicled"]:
        return fb

    # Tratamento específico para ZZZ onde os códigos de banner no formato UIGF/StarDB são 1, 2, 3, 5
    if clean_game == "zzz":
        if gt_clean in ["1", "1001"]:
            return "standard"
        if gt_clean in ["2", "2001"]:
            return "character"
        if gt_clean in ["3", "3001"]:
            return "weapon"
        if gt_clean in ["5", "5001"]:
            return "bangboo"

    # Tratamento específico para HSR onde 21 e 22 são os banners da colaboração Fate
    if clean_game == "hsr":
        if gt_clean in ["21", "22"]:
            return "collab"
        if gt_clean == "2":
            return "beginner"

    # Tratamento específico para Genshin onde 100 é novatos e 500 é crônica
    if clean_game == "genshin":
        if gt_clean == "100":
            return "beginner"
        if gt_clean == "500":
            return "chronicled"

    if gt_clean in GACHA_TYPE_MAPPING:
        return GACHA_TYPE_MAPPING[gt_clean]

    if any(k in fb for k in ["collab", "colabora"]):
        return "collab"
    if any(k in fb for k in ["beginner", "iniciante", "novato", "partida"]):
        return "beginner"
    if any(k in fb for k in ["bangboo"]):
        return "bangboo"
    if any(k in fb for k in ["chronicled", "crônica", "cronica"]):
        return "chronicled"
    if any(k in fb for k in ["char", "personagem", "limitado"]):
        return "character"
    if any(k in fb for k in ["weapon", "cone", "arma", "engine", "motor"]):
        return "weapon"
    if any(k in fb for k in ["standard", "mochileiro", "padrao", "padrão", "regular"]):
        return "standard"

    return "character"


def is_standard_5_star(game_id: str, item_name: str) -> bool:
    """Verifica se o item/personagem 5★ pertence ao mochileiro permanente (derrota no 50/50)."""
    game_clean = (game_id or "hsr").lower().strip()
    name_clean = (item_name or "").lower().strip()
    std_list = STANDARD_5_STARS.get(game_clean, [])
    return any(s in name_clean or name_clean in s for s in std_list)


def calculate_gacha_tracker_stats(game_id: str, uid: Optional[str] = None) -> GachaTrackerOverviewResponse:
    """
    Calcula as estatísticas precisas de Pity Atual, 50/50 Garantido e histórico de 5★
    a partir das puxadas registradas no SQLite para o UID selecionado, separando banners específicos por jogo.
    """
    clean_game = (game_id or "hsr").lower().strip()
    target_uid = str(uid).strip() if uid else database.get_active_uid(clean_game)
    if not target_uid:
        # Retorna estrutura vazia graciosa
        empty_banner = lambda cat, name, hard=90, soft=74: BannerTrackerStats(
            banner_category=cat, display_name=name, hard_pity_cap=hard, soft_pity_start=soft
        )
        return GachaTrackerOverviewResponse(
            game_id=clean_game,
            uid="Não sincronizado",
            character_banner=empty_banner("character", "Banner de Personagem"),
            weapon_banner=empty_banner("weapon", "Banner de Arma/Cone", hard=80, soft=64),
            standard_banner=empty_banner("standard", "Banner Padrão"),
            overall_luck_rating="Sem dados",
            banners=[],
        )

    all_pulls = database.get_gacha_pulls(clean_game, uid=target_uid, limit=50000)

    # Separação por categorias completas
    pulls_by_cat: Dict[str, List[Dict[str, Any]]] = {
        "character": [],
        "weapon": [],
        "standard": [],
        "beginner": [],
        "collab": [],
        "bangboo": [],
        "chronicled": [],
    }

    for p in all_pulls:
        cat = normalize_banner_category(clean_game, p.get("gacha_type", ""), p.get("banner_category", ""))
        if cat in pulls_by_cat:
            pulls_by_cat[cat].append(p)
        else:
            pulls_by_cat["character"].append(p)

    def process_banner(
        cat: str, display_name: str, hard_pity_cap: int = 90, soft_pity_start: int = 74
    ) -> BannerTrackerStats:
        items = pulls_by_cat.get(cat, [])
        # Ordena estritamente por cronologia (time ASC, id ASC)
        items_sorted = sorted(items, key=lambda x: (str(x.get("time", "")), str(x.get("id", ""))))

        current_pity = 0
        is_guaranteed = False
        five_stars: List[FiveStarRecord] = []
        four_stars_count = 0
        three_stars_count = 0

        total_pulls = len(items_sorted)

        for p in items_sorted:
            current_pity += 1
            rarity = int(p.get("rarity") or 3)
            name = str(p.get("item_name") or "Item Desconhecido")
            time_val = str(p.get("time") or "")
            itype = str(p.get("item_type") or "character")

            if rarity == 5:
                # É 5 Estrelas
                is_std = is_standard_5_star(clean_game, name)

                if cat in ["character", "collab"]:
                    if is_guaranteed:
                        is_win = True
                        is_rate_up = True
                        is_guaranteed = False  # Consumiu o garantido
                    else:
                        if is_std:
                            is_win = False
                            is_rate_up = False
                            is_guaranteed = True  # Perdeu 50/50, o próximo é 100% garantido!
                        else:
                            is_win = True
                            is_rate_up = True
                            is_guaranteed = False
                elif cat == "bangboo":
                    # No banner de Bangboo do ZZZ a escolha do Bangboo S-Rank é 100% garantida
                    is_win = True
                    is_rate_up = True
                else:
                    # Em armas, iniciante e mochileiro
                    is_win = not is_std
                    is_rate_up = not is_std

                # Encontra o ícone oficial do item
                icon_url = get_gacha_item_icon(clean_game, name, itype)

                five_stars.append(
                    FiveStarRecord(
                        name=name,
                        rarity=5,
                        time=time_val,
                        pity=current_pity,
                        is_win_5050=is_win,
                        is_rate_up=is_rate_up,
                        banner_category=cat,
                        icon=icon_url,
                        item_type=itype,
                    )
                )
                current_pity = 0
            elif rarity == 4:
                four_stars_count += 1
            else:
                three_stars_count += 1

        five_stars_count = len(five_stars)
        avg_pity = round(sum(f.pity for f in five_stars) / five_stars_count, 1) if five_stars_count > 0 else 0.0

        # Taxa de vitórias de 50/50
        wins = sum(1 for f in five_stars if f.is_win_5050)
        win_rate = round((wins / five_stars_count) * 100, 1) if five_stars_count > 0 else 100.0

        next_soft = max(0, soft_pity_start - current_pity)
        to_hard = max(0, hard_pity_cap - current_pity)

        # Inverte a lista de 5★ para exibição cronológica reversa (os mais recentes primeiro)
        recent_five = list(reversed(five_stars))[:15]

        return BannerTrackerStats(
            banner_category=cat,
            display_name=display_name,
            current_pity=current_pity,
            is_guaranteed=is_guaranteed,
            total_pulls=total_pulls,
            five_stars_count=five_stars_count,
            four_stars_count=four_stars_count,
            three_stars_count=three_stars_count,
            avg_five_star_pity=avg_pity,
            win_5050_rate=win_rate,
            recent_five_stars=recent_five,
            next_soft_pity_in=next_soft,
            pulls_to_hard_pity=to_hard,
            hard_pity_cap=hard_pity_cap,
            soft_pity_start=soft_pity_start,
        )

    # Configuração dos banners específicos por jogo
    beginner_stats: Optional[BannerTrackerStats] = None
    collab_stats: Optional[BannerTrackerStats] = None
    bangboo_stats: Optional[BannerTrackerStats] = None
    chronicled_stats: Optional[BannerTrackerStats] = None

    if clean_game == "genshin":
        char_stats = process_banner("character", "Banner de Personagem Limitado", hard_pity_cap=90, soft_pity_start=74)
        weapon_stats = process_banner("weapon", "Banner de Armas de Evento", hard_pity_cap=80, soft_pity_start=64)
        standard_stats = process_banner("standard", "Banner Padrão / Mochileiro", hard_pity_cap=90, soft_pity_start=74)
        beginner_stats = process_banner(
            "beginner", "Desejo dos Novatos (Iniciante)", hard_pity_cap=20, soft_pity_start=20
        )
        chronicled_stats = process_banner(
            "chronicled", "Oração das Crônicas (Regional)", hard_pity_cap=90, soft_pity_start=74
        )
        ordered_banners = [char_stats, weapon_stats, standard_stats]
        if beginner_stats.total_pulls > 0 or True:
            ordered_banners.append(beginner_stats)
        if chronicled_stats.total_pulls > 0:
            ordered_banners.append(chronicled_stats)

    elif clean_game == "hsr":
        char_stats = process_banner(
            "character", "Salto Hiperespacial de Personagem", hard_pity_cap=90, soft_pity_start=74
        )
        weapon_stats = process_banner("weapon", "Salto de Cones de Luz", hard_pity_cap=80, soft_pity_start=64)
        collab_stats = process_banner(
            "collab", "Salto de Colaboração (Fate/stay night)", hard_pity_cap=90, soft_pity_start=74
        )
        standard_stats = process_banner("standard", "Salto Estelar Padrão", hard_pity_cap=90, soft_pity_start=74)
        beginner_stats = process_banner(
            "beginner", "Salto de Partida (Iniciante)", hard_pity_cap=50, soft_pity_start=50
        )
        ordered_banners = [char_stats, weapon_stats, collab_stats, standard_stats]
        if beginner_stats.total_pulls > 0 or True:
            ordered_banners.append(beginner_stats)

    elif clean_game == "zzz":
        char_stats = process_banner("character", "Canal Exclusivo de Agente", hard_pity_cap=90, soft_pity_start=74)
        weapon_stats = process_banner("weapon", "Canal de Motores-W", hard_pity_cap=80, soft_pity_start=64)
        bangboo_stats = process_banner("bangboo", "Canal de Bangboos de Destaque", hard_pity_cap=80, soft_pity_start=65)
        standard_stats = process_banner("standard", "Canal Estelar Padrão", hard_pity_cap=90, soft_pity_start=74)
        ordered_banners = [char_stats, weapon_stats, bangboo_stats, standard_stats]

    else:
        char_stats = process_banner("character", "Banner de Personagem", hard_pity_cap=90, soft_pity_start=74)
        weapon_stats = process_banner("weapon", "Banner de Armas", hard_pity_cap=80, soft_pity_start=64)
        standard_stats = process_banner("standard", "Banner Padrão", hard_pity_cap=90, soft_pity_start=74)
        ordered_banners = [char_stats, weapon_stats, standard_stats]

    total_pulls_all = len(all_pulls)
    total_five_all = sum(b.five_stars_count for b in ordered_banners)

    # Avaliação global de sorte
    if char_stats.five_stars_count >= 2:
        if char_stats.avg_five_star_pity <= 62:
            luck_rating = "Sortudo dos Aeons! 🍀"
        elif char_stats.avg_five_star_pity <= 72:
            luck_rating = "Acima da Média ✨"
        elif char_stats.avg_five_star_pity <= 77:
            luck_rating = "Dentro da Média ⚖️"
        else:
            luck_rating = "Hard Pity Warrior 💀"
    else:
        luck_rating = "Dados Iniciais"

    return GachaTrackerOverviewResponse(
        game_id=clean_game,
        uid=target_uid,
        character_banner=char_stats,
        weapon_banner=weapon_stats,
        standard_banner=standard_stats,
        beginner_banner=beginner_stats,
        collab_banner=collab_stats,
        bangboo_banner=bangboo_stats,
        chronicled_banner=chronicled_stats,
        banners=ordered_banners,
        total_pulls_all_banners=total_pulls_all,
        total_five_stars_all_banners=total_five_all,
        overall_luck_rating=luck_rating,
    )


def get_gacha_pulls_history_detailed(
    game_id: str,
    uid: Optional[str] = None,
    banner_category: Optional[str] = None,
    rarity: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> GachaHistoryListResponse:
    """
    Retorna o histórico detalhado e paginado de puxadas com ícones oficiais de cada item.
    """
    clean_game = (game_id or "hsr").lower().strip()
    target_uid = str(uid).strip() if uid else database.get_active_uid(clean_game)
    if not target_uid:
        return GachaHistoryListResponse(game_id=clean_game, uid="", total_pulls=0, pulls=[])

    rows, total_count = database.get_gacha_pulls_filtered(
        game_id=clean_game,
        uid=target_uid,
        banner_category=banner_category,
        rarity=rarity,
        order_desc=True,
        limit=limit,
        offset=offset,
    )

    pull_items: List[GachaPullItem] = []
    for r in rows:
        name = str(r.get("item_name") or "Item Desconhecido")
        itype = str(r.get("item_type") or "character")
        icon_url = get_gacha_item_icon(clean_game, name, itype)

        pity_val = r.get("pity_count")
        pity_int = int(pity_val) if pity_val is not None else 1

        pull_items.append(
            GachaPullItem(
                id=str(r.get("id") or ""),
                time=str(r.get("time") or ""),
                name=name,
                item_type=itype,
                rarity=int(r.get("rarity") or 3),
                gacha_type=str(r.get("gacha_type") or ""),
                banner_category=str(r.get("banner_category") or "character"),
                pity=pity_int,
                icon=icon_url,
            )
        )

    return GachaHistoryListResponse(
        game_id=clean_game,
        uid=target_uid,
        total_pulls=total_count,
        pulls=pull_items,
    )


def import_gacha_log_data(game_id: str, raw_data: Any, uid: Optional[str] = None) -> ImportGachaResponse:
    """
    Importa registros de gacha nos formatos universais da comunidade:
    - UIGF v4.x Multi-Game (chaves 'hk4e', 'hkrpg', 'nap')
    - UIGF v2.4+ / v3.0 / SRGF Single-Game (dicionário com 'info' e 'list'/'pulls')
    - Listas brutas de logs de APIs ou dumps JSON.
    """
    clean_game = (game_id or "all").lower().strip()

    # 1. Detecção de Formato Multi-Jogo UIGF v4.x
    if isinstance(raw_data, dict) and any(k in raw_data for k in UIGF_GAME_KEY_MAP):
        total_inserted_all = 0
        total_ignored_all = 0
        game_summaries: List[str] = []
        last_uid = uid

        for uigf_key, target_game in UIGF_GAME_KEY_MAP.items():
            if uigf_key not in raw_data:
                continue

            game_data = raw_data[uigf_key]
            # Pode ser lista de contas ou um único dicionário de conta
            account_entries = game_data if isinstance(game_data, list) else [game_data]

            for acc in account_entries:
                if not isinstance(acc, dict):
                    continue

                acc_uid = str(acc.get("uid") or uid or "").strip()
                if not acc_uid:
                    acc_uid = database.get_active_uid(target_game) or "default_uid"
                last_uid = acc_uid

                pulls_list = acc.get("list") or acc.get("pulls") or []
                if not isinstance(pulls_list, list):
                    continue

                pulls_to_save: List[Dict[str, Any]] = []
                for p in pulls_list:
                    if not isinstance(p, dict):
                        continue

                    gacha_type = str(
                        p.get("gacha_type") or p.get("uigf_gacha_type") or p.get("gacha_id") or "default"
                    ).strip()
                    cat = normalize_banner_category(target_game, gacha_type, str(p.get("banner_category") or ""))

                    name = str(p.get("name") or p.get("item_name") or "Item").strip()

                    # Conversão de raridade inteligente (ZZZ: 4=S-rank/5*, 3=A-rank/4*, 2=B-rank/3*)
                    rank_raw = str(p.get("rarity") or p.get("rank_type") or "3").strip()
                    if target_game == "zzz":
                        if rank_raw == "4":
                            rarity = 5
                        elif rank_raw == "3":
                            rarity = 4
                        elif rank_raw == "2":
                            rarity = 3
                        else:
                            rarity = int(rank_raw) if rank_raw.isdigit() else 3
                    else:
                        rarity = int(rank_raw) if rank_raw.isdigit() else 3

                    time_val = str(p.get("time") or p.get("datetime") or datetime.now().isoformat()).strip()
                    raw_id = str(p.get("id") or "").strip()

                    # Gera chave determinística única para evitar colisões entre banners sequenciais
                    pull_id = f"{target_game}_{acc_uid}_{gacha_type}_{raw_id}" if raw_id else ""

                    raw_item_type = str(p.get("item_type") or "").lower()
                    if any(c in raw_item_type for c in ["char", "personagem", "agent", "agente"]):
                        item_type = "character"
                    elif "bangboo" in raw_item_type:
                        item_type = "bangboo"
                    elif any(w in raw_item_type for w in ["weapon", "arma", "cone", "w-engine", "engine", "motor"]):
                        item_type = "weapon"
                    else:
                        item_type = (
                            "character"
                            if rarity >= 4
                            and not any(
                                k in name.lower()
                                for k in ["espada", "lança", "cone", "arco", "motor", "amplificador", "w-engine"]
                            )
                            else "weapon"
                        )

                    pulls_to_save.append(
                        {
                            "id": pull_id,
                            "uid": acc_uid,
                            "game_id": target_game,
                            "gacha_type": gacha_type,
                            "banner_category": cat,
                            "item_name": name,
                            "item_type": item_type,
                            "rarity": rarity,
                            "time": time_val,
                        }
                    )

                inserted, ignored = database.save_gacha_pulls(target_game, acc_uid, pulls_to_save)
                total_inserted_all += inserted
                total_ignored_all += ignored
                game_summaries.append(f"{target_game.upper()} (UID {acc_uid}): {inserted} novos / {ignored} duplicados")

                # Garante que a conta cujos tiros foram importados fique registrada como ativa
                database.set_active_account(target_game, acc_uid)

        summary_msg = (
            f"Importação multi-jogo UIGF v4 concluída: {total_inserted_all} novos tiros importados "
            f"({total_ignored_all} duplicados). Detalhes: " + "; ".join(game_summaries)
        )
        return ImportGachaResponse(
            success=True,
            game_id=clean_game,
            uid=str(last_uid or "multi_uid"),
            total_imported=total_inserted_all,
            total_duplicates=total_ignored_all,
            message=summary_msg,
        )

    # 2. Parsing de Formato de Jogo Único (UIGF v2.x/v3.x, SRGF ou lista plana)
    target_uid = uid
    raw_list = []

    if isinstance(raw_data, dict):
        info_block = raw_data.get("info", {})
        if not target_uid and info_block.get("uid"):
            target_uid = str(info_block["uid"]).strip()
        if not clean_game or clean_game == "all":
            if info_block.get("game_id"):
                clean_game = str(info_block["game_id"]).strip().lower()

        if "list" in raw_data and isinstance(raw_data["list"], list):
            raw_list = raw_data["list"]
        elif "pulls" in raw_data and isinstance(raw_data["pulls"], list):
            raw_list = raw_data["pulls"]
        elif "data" in raw_data and isinstance(raw_data["data"], dict) and "list" in raw_data["data"]:
            raw_list = raw_data["data"]["list"]
    elif isinstance(raw_data, list):
        raw_list = raw_data

    if not clean_game or clean_game == "all":
        clean_game = "hsr"

    if not target_uid:
        for item in raw_list:
            if isinstance(item, dict) and item.get("uid"):
                target_uid = str(item["uid"]).strip()
                break

    if not target_uid:
        target_uid = database.get_active_uid(clean_game) or "default_uid"

    pulls_to_save = []
    for p in raw_list:
        if not isinstance(p, dict):
            continue

        gacha_type = str(p.get("gacha_type") or p.get("uigf_gacha_type") or p.get("gacha_id") or "301").strip()
        cat = normalize_banner_category(clean_game, gacha_type, str(p.get("banner_category") or ""))

        name = str(p.get("name") or p.get("item_name") or "Item").strip()

        rank_raw = str(p.get("rarity") or p.get("rank_type") or "3").strip()
        if clean_game == "zzz":
            if rank_raw == "4":
                rarity = 5
            elif rank_raw == "3":
                rarity = 4
            elif rank_raw == "2":
                rarity = 3
            else:
                rarity = int(rank_raw) if rank_raw.isdigit() else 3
        else:
            rarity = int(rank_raw) if rank_raw.isdigit() else 3

        time_val = str(p.get("time") or p.get("datetime") or datetime.now().isoformat()).strip()
        raw_id = str(p.get("id") or "").strip()
        pull_id = f"{clean_game}_{target_uid}_{gacha_type}_{raw_id}" if raw_id else ""

        raw_item_type = str(p.get("item_type") or "").lower()
        if any(c in raw_item_type for c in ["char", "personagem"]):
            item_type = "character"
        elif "bangboo" in raw_item_type:
            item_type = "bangboo"
        elif any(w in raw_item_type for w in ["weapon", "arma", "cone", "w-engine"]):
            item_type = "weapon"
        else:
            item_type = (
                "character"
                if rarity >= 4
                and not any(
                    k in name.lower() for k in ["espada", "lança", "cone", "arco", "motor", "amplificador", "w-engine"]
                )
                else "weapon"
            )

        pulls_to_save.append(
            {
                "id": pull_id,
                "uid": target_uid,
                "game_id": clean_game,
                "gacha_type": gacha_type,
                "banner_category": cat,
                "item_name": name,
                "item_type": item_type,
                "rarity": rarity,
                "time": time_val,
            }
        )

    # 3. Salva no SQLite
    inserted, ignored = database.save_gacha_pulls(clean_game, target_uid, pulls_to_save)

    return ImportGachaResponse(
        success=True,
        game_id=clean_game,
        uid=target_uid,
        total_imported=inserted,
        total_duplicates=ignored,
        message=f"{inserted} novos tiros importados com sucesso! ({ignored} duplicados ignorados).",
    )


def export_gacha_log_uigf(game_id: str, uid: Optional[str] = None) -> Dict[str, Any]:
    """
    Exporta o histórico de tiros do usuário no formato universal UIGF v2.4 (Unified Interchangeable Gacha-log Format).
    """
    clean_game = (game_id or "hsr").lower().strip()
    target_uid = str(uid).strip() if uid else database.get_active_uid(clean_game)
    if not target_uid:
        target_uid = "000000000"

    pulls = database.get_gacha_pulls(clean_game, uid=target_uid, limit=50000)

    uigf_list = []
    for p in pulls:
        pid = str(p.get("id", ""))
        prefix = f"{clean_game}_{target_uid}_{p.get('gacha_type', '')}_"
        clean_pid = pid[len(prefix) :] if pid.startswith(prefix) else pid

        uigf_list.append(
            {
                "id": clean_pid,
                "uid": p.get("uid", target_uid),
                "gacha_type": p.get("gacha_type", "301"),
                "item_id": p.get("item_id", ""),
                "name": p.get("item_name", ""),
                "item_type": "Personagem" if p.get("item_type") == "character" else "Arma",
                "rank_type": str(p.get("rarity", 3)),
                "time": p.get("time", ""),
            }
        )

    uigf_payload = {
        "info": {
            "uid": target_uid,
            "lang": "pt-br",
            "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "export_app": "Cabeca_de_Droid",
            "export_app_version": "v5.1",
            "uigf_version": "v2.4",
            "game_id": clean_game,
        },
        "list": uigf_list,
    }
    return uigf_payload


def import_uigf_file(file_path: str) -> ImportGachaResponse:
    """Carrega diretamente um arquivo JSON no padrão UIGF v4 ou legado do disco e processa."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return import_gacha_log_data(game_id="all", raw_data=data)
