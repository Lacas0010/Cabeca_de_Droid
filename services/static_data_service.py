"""Serviço de orquestração dos manifestos estáticos, banners e avaliação de status."""

import os
from typing import Any, Callable, Dict, Optional

import database
from build_calculator import evaluate_general_stats, generate_meta_json_from_markdown
from services.roster_service import invalidate_roster_cache
from static_data_manager import static_data_manager


def get_static_data_status_summary(db_mod=database, manager=static_data_manager) -> Dict[str, Any]:
    manifests = db_mod.get_static_data_manifests()
    summary = manager.get_sync_status()
    return {"status": "success", "manifests": manifests, "summary": summary}


def sync_static_data_and_banners(
    target_game: Optional[str],
    manager=static_data_manager,
    db_mod=database,
    invalidate_fn: Callable = invalidate_roster_cache,
) -> Dict[str, Any]:
    results = manager.sync_upstream_data(target_game)
    db_mod.save_static_data_manifests(results)
    games_to_rebuild = [target_game.lower().strip()] if target_game else ["hsr", "genshin", "zzz"]
    for g in games_to_rebuild:
        if os.path.exists(f"{g}/guias"):
            try:
                generate_meta_json_from_markdown(g)
            except Exception as meta_err:
                print(f"[WARN] Erro ao regenerar meta_data_{g}.json após sync estático: {meta_err}")
    invalidate_fn(target_game)
    try:
        from scrapers.scraper_prydwen import PrydwenScraper

        PrydwenScraper().get_current_banners(target_game)
    except Exception as e:
        print(f"[WARN] Erro ao sincronizar banners em sync_static_data_and_banners: {e}")
    return results


def evaluate_stats_against_meta(game_id: str, char_id: str, final_stats: Dict[str, str]) -> Dict[str, Any]:
    return evaluate_general_stats(game_id, str(char_id), final_stats)
