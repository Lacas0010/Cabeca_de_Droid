import re
import os
import json
import time
import urllib.parse
from typing import Dict, Any, Optional, Tuple

import database
import endgame_extractor
from core.config import get_data_path
from services.roster_service import get_roster
from services.media_service import get_raw_url
from services.team_matcher_service import ENDGAME_MODE_EN_MAP

_ENDGAME_CACHE: Dict[Tuple[str, str, str], Tuple[float, Dict[str, Any]]] = {}
CACHE_TTL = 60.0

_STAGE_TRANSLATION_RULES = [
    (re.compile(r"Piso\s*(\d+)", re.IGNORECASE), r"Floor \1"),
    (re.compile(r"Câmara\s*(\d+)", re.IGNORECASE), r"Chamber \1"),
    (re.compile(r"Desafio Arcano\s*(\d+)", re.IGNORECASE), r"Arcane Challenge \1"),
    (re.compile(r"Temporada Atual", re.IGNORECASE), "Current Season"),
    (re.compile(r"Temporada\s*(\d+)", re.IGNORECASE), r"Season \1"),
    (re.compile(r"Cruzando o Além", re.IGNORECASE), "Crossing the Beyond"),
    (re.compile(r"Modo Estelar", re.IGNORECASE), "Star Mode"),
    (re.compile(r"Palavras Imaginadas", re.IGNORECASE), "Imagined Words"),
    (re.compile(r"Dominação do Esquecimento", re.IGNORECASE), "Dominance of Oblivion"),
    (re.compile(r"Fronteira Crítica", re.IGNORECASE), "Critical Node"),
    (re.compile(r"Fronteira Estável", re.IGNORECASE), "Stable Node"),
    (re.compile(r"Nó Crítico", re.IGNORECASE), "Critical Node"),
    (re.compile(r"Zona Disputada", re.IGNORECASE), "Disputed Node"),
    (re.compile(r"Ato\s*(\d+)", re.IGNORECASE), r"Act \1"),
]

_TEAM_TRANSLATION_RULES = [
    (re.compile(r"Lado\s*(\d+)", re.IGNORECASE), r"Side \1"),
    (re.compile(r"Primeira Metade", re.IGNORECASE), "First Half"),
    (re.compile(r"Segunda Metade", re.IGNORECASE), "Second Half"),
    (re.compile(r"Ato\s*(\d+)", re.IGNORECASE), r"Act \1"),
    (re.compile(r"Elenco Principal\s*/\s*Destaques", re.IGNORECASE), "Main Cast / Highlights"),
    (re.compile(r"Agentes da Rotação", re.IGNORECASE), "Rotation Agents"),
]


def invalidate_endgame_cache(game_id: Optional[str] = None) -> None:
    """Invalida o cache em memória do endgame para forçar atualização imediata."""
    global _ENDGAME_CACHE
    if game_id:
        clean_g = game_id.lower().strip()
        keys_to_del = [k for k in _ENDGAME_CACHE if k[0] == clean_g]
        for k in keys_to_del:
            _ENDGAME_CACHE.pop(k, None)
    else:
        _ENDGAME_CACHE.clear()


async def get_endgame(game_id: str, lang: str = "pt") -> Dict[str, Any]:
    """Retorna os dados estruturados de Endgame (MoC, Ficção Pura, Sombra, Abismo, Teatro, Shiyu) de um jogo."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise ValueError("Jogo inválido. Escolha 'hsr', 'genshin' ou 'zzz'.")

    # Verifica cache em memória (incluindo active_uid para evitar dados obsoletos ao trocar de conta)
    active_uid = str(database.get_active_uid(game_id) or "")
    cache_key = (game_id, lang, active_uid)
    now = time.time()
    if cache_key in _ENDGAME_CACHE:
        cached_time, cached_val = _ENDGAME_CACHE[cache_key]
        if now - cached_time < CACHE_TTL:
            return cached_val

    modes = []
    updated_at = ""
    uid = ""

    # 1. Tenta carregar do SQLite
    try:
        db_endgame = database.get_endgame_data(game_id)
        if db_endgame and db_endgame.get("modes"):
            modes = db_endgame["modes"]
            updated_at = db_endgame.get("updated_at", "")
            uid = db_endgame.get("uid", "")
    except Exception as e:
        print(f"[Aviso] Erro ao ler endgame do SQLite para {game_id}: {e}")

    # 2. Se não encontrou no SQLite, tenta carregar do JSON salvo
    if not modes:
        rel_json = f"{game_id}/endgame_data_{game_id}.json"
        json_path = rel_json if os.path.exists(rel_json) else get_data_path(rel_json)
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as ejf:
                    modes = json.load(ejf)
            except Exception as je:
                print(f"[Aviso] Erro ao ler {json_path}: {je}")

    # 3. Fallback retrocompatível: lê do Markdown de roster
    if not modes:
        rel_md = f"{game_id}/roster_{game_id}.md"
        md_path = rel_md if os.path.exists(rel_md) else get_data_path(rel_md)
        if os.path.exists(md_path):
            try:
                with open(md_path, "r", encoding="utf-8") as mf:
                    md_text = mf.read()
                roster_data = None
                try:
                    roster_data = await get_roster(game_id)
                except Exception:
                    pass
                modes = endgame_extractor.parse_endgame_from_markdown(game_id, md_text, roster_data or [])
            except Exception as me:
                print(f"[Aviso] Erro ao fazer parse de endgame do MD para {game_id}: {me}")

    # 4. Enriquece todos os personagens dos times com ícones seguros (via proxy), raridade, elemento e rank
    if modes:
        roster_data = None
        try:
            roster_data = await get_roster(game_id)
        except Exception:
            pass

        roster_map = {}
        if roster_data and isinstance(roster_data, list):
            for c in roster_data:
                cname = c.get("name", "")
                if cname:
                    roster_map[cname.lower().strip()] = c

        for mode in modes:
            for team in mode.get("teams", []):
                for char in team.get("characters", []):
                    cname = char.get("name", "").strip()
                    cid = str(char.get("id", "")).strip()

                    # Normalização proativa de IDs do Trailblazer e Traveler
                    if not cname or "desconhecido" in cname.lower() or "avatar" in cname.lower():
                        if cid.startswith("800") or cid.startswith("801") or "8009" in cname or "800" in cname:
                            cname = "Desbravador(a)"
                            char["name"] = cname
                            if not char.get("element"):
                                char["element"] = "ice"
                            char["rarity"] = 5
                        elif cid in ["10000005", "10000007"] or "1000000" in cname:
                            cname = "Viajante"
                            char["name"] = cname
                            char["rarity"] = 5

                    c_lower = cname.lower()

                    if c_lower in roster_map:
                        rm = roster_map[c_lower]
                        if rm.get("icon"):
                            char["icon"] = rm["icon"]
                        if not char.get("element") and rm.get("element"):
                            char["element"] = rm["element"]
                        if rm.get("rarity"):
                            char["rarity"] = rm["rarity"]
                        if not char.get("rank_str") and rm.get("rank_str"):
                            char["rank_str"] = rm["rank_str"]
                        if rm.get("id"):
                            char["id"] = rm["id"]

                    # Sanitiza URLs de Genshin (eliminando .png.png e ide_)
                    if game_id == "genshin" and char.get("icon"):
                        try:
                            from extractor import sanitize_genshin_url

                            raw_c_icon = get_raw_url(char["icon"])
                            char["icon"] = sanitize_genshin_url(raw_c_icon)
                        except Exception:
                            pass

                    # Fallbacks especiais para personagens sem ícone (ex: Traveler / Desbravador)
                    if not char.get("icon") or char.get("icon").strip() == "":
                        if "desbravador" in c_lower or "trailblazer" in c_lower:
                            char["icon"] = "/assets/hsr_icon.png"
                        elif "traveler" in c_lower or "viajante" in c_lower:
                            char["icon"] = "/assets/genshin_icon.png"
                        elif "bangboo" in c_lower:
                            char["icon"] = "/assets/zzz_icon.png"

                    # Formata URL do ícone com proxy anti-CORS
                    if char.get("icon"):
                        raw_c_icon = get_raw_url(char["icon"])
                        if raw_c_icon.startswith("http"):
                            char["icon"] = f"/api/proxy_image?url={urllib.parse.quote(raw_c_icon, safe='')}"

    if lang == "en" and modes:
        for mode in modes:
            m_name = mode.get("name", "")
            if m_name in ENDGAME_MODE_EN_MAP:
                mode["name"] = ENDGAME_MODE_EN_MAP[m_name]
            stg = mode.get("stage", "")
            if stg:
                for pat, repl in _STAGE_TRANSLATION_RULES:
                    stg = pat.sub(repl, stg)
                mode["stage"] = stg
            ml = mode.get("metric_label", "")
            if ml:
                ml = ml.replace("Rodadas Utilizadas", "Cycles Used")
                ml = ml.replace("Pontuação", "Score")
                ml = ml.replace("Estrelas do Piso", "Floor Stars")
                ml = ml.replace("Atos Concluídos", "Acts Completed")
                mode["metric_label"] = ml
            for team in mode.get("teams", []):
                t_name = team.get("name", "")
                if t_name:
                    for pat, repl in _TEAM_TRANSLATION_RULES:
                        t_name = pat.sub(repl, t_name)
                    team["name"] = t_name
                for m in team.get("monsters", []):
                    if m.get("name") == "Inimigo":
                        m["name"] = "Enemy"

    res = {
        "status": "success",
        "game_id": game_id,
        "has_data": bool(modes and len(modes) > 0),
        "updated_at": updated_at,
        "uid": uid,
        "modes": modes or [],
    }
    _ENDGAME_CACHE[cache_key] = (now, res)
    return res
