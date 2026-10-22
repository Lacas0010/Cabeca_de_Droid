import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union

import database
from schemas.gacha_tracker import (
    GachaPullItem,
    FiveStarRecord,
    BannerTrackerStats,
    GachaTrackerOverviewResponse,
    ImportGachaResponse,
)

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
    # Zenless Zone Zero
    "1001": "standard",
    "2001": "character",
    "3001": "weapon",
}

# Personagens 5★ Permanentes do Mochileiro Padrão
STANDARD_5_STARS = {
    "genshin": ["diluc", "jean", "keqing", "mona", "qiqi", "tighnari", "dehya"],
    "hsr": ["bailu", "bronya", "clara", "gepard", "himeko", "welt", "yanqing"],
    "zzz": ["koleda", "nekomata", "grace", "rina", "lycaon", "soldier 11", "soldado 11"],
}


def normalize_banner_category(game_id: str, gacha_type: str, fallback_cat: str = "") -> str:
    """Normaliza o tipo de banner a partir do gacha_type numérico ou textual."""
    gt_clean = str(gacha_type or "").strip()
    if gt_clean in GACHA_TYPE_MAPPING:
        return GACHA_TYPE_MAPPING[gt_clean]

    fb = (fallback_cat or "").lower().strip()
    if any(k in fb for k in ["char", "personagem", "limitado"]):
        return "character"
    if any(k in fb for k in ["weapon", "cone", "arma", "engine", "motor"]):
        return "weapon"
    if any(k in fb for k in ["standard", "mochileiro", "padrao", "padrão", "regular"]):
        return "standard"
    if any(k in fb for k in ["beginner", "iniciante"]):
        return "beginner"

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
    a partir das puxadas registradas no SQLite para o UID selecionado.
    """
    clean_game = (game_id or "hsr").lower().strip()
    target_uid = str(uid).strip() if uid else database.get_active_uid(clean_game)
    if not target_uid:
        # Retorna estrutura vazia graciosa
        empty_banner = lambda cat, name: BannerTrackerStats(banner_category=cat, display_name=name)
        return GachaTrackerOverviewResponse(
            game_id=clean_game,
            uid="Não sincronizado",
            character_banner=empty_banner("character", "Banner de Personagem"),
            weapon_banner=empty_banner("weapon", "Banner de Arma/Cone"),
            standard_banner=empty_banner("standard", "Banner Padrão"),
            overall_luck_rating="Sem dados",
        )

    all_pulls = database.get_gacha_pulls(clean_game, uid=target_uid, limit=10000)

    # Separação por categorias
    pulls_by_cat: Dict[str, List[Dict[str, Any]]] = {"character": [], "weapon": [], "standard": [], "beginner": []}

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

            if rarity == 5:
                # É 5 Estrelas
                is_std = is_standard_5_star(clean_game, name)

                if cat == "character":
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
                else:
                    # Em armas e mochileiro não há regra clássica de 50/50 de personagem
                    is_win = not is_std
                    is_rate_up = not is_std

                five_stars.append(
                    FiveStarRecord(
                        name=name,
                        rarity=5,
                        time=time_val,
                        pity=current_pity,
                        is_win_5050=is_win,
                        is_rate_up=is_rate_up,
                        banner_category=cat,
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
        )

    # Caps oficiais de cada banner
    # Genshin / HSR: Char 90 (Soft 74), Arma 80 (Soft 64), Padrão 90 (Soft 74)
    # ZZZ: Char 90 (Soft 74), W-Engine 80 (Soft 64)
    char_stats = process_banner("character", "Banner de Personagem Limitado", hard_pity_cap=90, soft_pity_start=74)
    weapon_stats = process_banner("weapon", "Banner de Armas / Cones de Luz", hard_pity_cap=80, soft_pity_start=64)
    standard_stats = process_banner("standard", "Banner Padrão / Mochileiro", hard_pity_cap=90, soft_pity_start=74)

    total_pulls_all = len(all_pulls)
    total_five_all = char_stats.five_stars_count + weapon_stats.five_stars_count + standard_stats.five_stars_count

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
        total_pulls_all_banners=total_pulls_all,
        total_five_stars_all_banners=total_five_all,
        overall_luck_rating=luck_rating,
    )


def import_gacha_log_data(game_id: str, raw_data: Any, uid: Optional[str] = None) -> ImportGachaResponse:
    """
    Importa registros de gacha nos formatos universais da comunidade (UIGF v2.4+, SRGF)
    ou listas brutas de logs da API oficial da HoYoverse.
    """
    clean_game = (game_id or "hsr").lower().strip()
    pulls_to_save: List[Dict[str, Any]] = []

    target_uid = uid
    raw_list = []

    # 1. Parsing de Formato UIGF / SRGF (Dicionário com 'info' e 'list')
    if isinstance(raw_data, dict):
        info_block = raw_data.get("info", {})
        if not target_uid and info_block.get("uid"):
            target_uid = str(info_block["uid"]).strip()

        if "list" in raw_data and isinstance(raw_data["list"], list):
            raw_list = raw_data["list"]
        elif "pulls" in raw_data and isinstance(raw_data["pulls"], list):
            raw_list = raw_data["pulls"]
        elif "data" in raw_data and isinstance(raw_data["data"], dict) and "list" in raw_data["data"]:
            raw_list = raw_data["data"]["list"]
    elif isinstance(raw_data, list):
        raw_list = raw_data

    if not target_uid:
        # Tenta pegar da primeira entrada da lista ou do UID ativo do banco
        for item in raw_list:
            if isinstance(item, dict) and item.get("uid"):
                target_uid = str(item["uid"]).strip()
                break

    if not target_uid:
        target_uid = database.get_active_uid(clean_game) or "default_uid"

    # 2. Converte itens para formato padronizado
    for p in raw_list:
        if not isinstance(p, dict):
            continue

        gacha_type = str(p.get("gacha_type") or p.get("gacha_id") or "301").strip()
        cat = normalize_banner_category(clean_game, gacha_type, str(p.get("banner_category") or ""))

        name = str(p.get("name") or p.get("item_name") or "Item").strip()
        rarity = int(p.get("rarity") or p.get("rank_type") or 3)
        time_val = str(p.get("time") or p.get("datetime") or datetime.now().isoformat()).strip()
        pull_id = str(p.get("id") or "").strip()
        item_type = str(
            p.get("item_type")
            or (
                "character"
                if rarity >= 4
                and not any(
                    k in name.lower() for k in ["espada", "lança", "cone", "arco", "motor", "amplificador", "w-engine"]
                )
                else "weapon"
            )
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

    pulls = database.get_gacha_pulls(clean_game, uid=target_uid, limit=10000)

    uigf_list = []
    for p in pulls:
        uigf_list.append(
            {
                "id": p.get("id", ""),
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
