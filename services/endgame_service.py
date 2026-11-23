import asyncio
import re
import os
import json
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple

import database
import endgame_extractor
from core.config import get_cookies, get_data_path
from services.roster_service import get_roster
from services.media_service import get_raw_url
from services.team_matcher_service import ENDGAME_MODE_EN_MAP

_ENDGAME_CACHE: Dict[Tuple[str, str, str], Tuple[float, Dict[str, Any]]] = {}
_RESET_SCHEDULE_CACHE: Dict[Tuple[str, str], Tuple[float, Dict[str, Dict[str, Any]]]] = {}
CACHE_TTL = 60.0
RESET_SCHEDULE_TTL = 6 * 3600.0
RESET_SCHEDULE_RETRY_TTL = 600.0

_ENDGAME_MODE_CATALOG: Dict[str, List[Dict[str, Any]]] = {
    "hsr": [
        {"id": "moc", "name_pt": "Caos da Memória (MoC)", "name_en": "Memory of Chaos (MoC)", "badge": "MoC", "cycle_days": 42},
        {"id": "pure_fiction", "name_pt": "Ficção Pura", "name_en": "Pure Fiction", "badge": "PF", "cycle_days": 42},
        {"id": "apocalyptic_shadow", "name_pt": "Sombra Apocalíptica", "name_en": "Apocalyptic Shadow", "badge": "AS", "cycle_days": 42},
    ],
    "genshin": [
        {"id": "spiral_abyss", "name_pt": "Abismo Espiral", "name_en": "Spiral Abyss", "badge": "Abyss", "reset_day": 16},
        {"id": "imaginarium_theater", "name_pt": "Teatro Imaginário", "name_en": "Imaginarium Theater", "badge": "Teatro", "reset_day": 1},
    ],
    "zzz": [
        {"id": "shiyu_defense", "name_pt": "Defesa Shiyu", "name_en": "Shiyu Defense", "badge": "Shiyu", "cycle_days": 14},
        {"id": "deadly_assault", "name_pt": "Assalto Mortal", "name_en": "Deadly Assault", "badge": "DA", "cycle_days": 14},
    ],
}

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
    global _ENDGAME_CACHE, _RESET_SCHEDULE_CACHE
    if game_id:
        clean_g = game_id.lower().strip()
        for k in [k for k in _ENDGAME_CACHE if k[0] == clean_g]:
            _ENDGAME_CACHE.pop(k, None)
        for k in [k for k in _RESET_SCHEDULE_CACHE if k[0] == clean_g]:
            _RESET_SCHEDULE_CACHE.pop(k, None)
    else:
        _ENDGAME_CACHE.clear()
        _RESET_SCHEDULE_CACHE.clear()


def _parse_utc_iso(iso_str: Optional[str]) -> Optional[datetime]:
    if not iso_str or not isinstance(iso_str, str):
        return None
    try:
        dt = datetime.fromisoformat(iso_str.strip().replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _is_future_iso(iso_str: Optional[str], now_utc: datetime) -> bool:
    dt = _parse_utc_iso(iso_str)
    return bool(dt and dt > now_utc)


def _compute_next_monthly_reset(reset_day: int, game_id: str, uid: str, now_utc: datetime) -> str:
    """Calcula o próximo reset mensal (dia 1 ou 16 às 04:00 do servidor) em ISO-8601 UTC."""
    srv_tz = endgame_extractor.get_server_timezone(game_id, uid)
    now_srv = now_utc.astimezone(srv_tz)
    candidate = now_srv.replace(day=reset_day, hour=4, minute=0, second=0, microsecond=0)
    if candidate <= now_srv:
        year = now_srv.year + (1 if now_srv.month == 12 else 0)
        month = 1 if now_srv.month == 12 else now_srv.month + 1
        candidate = candidate.replace(year=year, month=month, day=reset_day)
    return candidate.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _project_expired_reset(
    mode_meta: Dict[str, Any], stale_iso: Optional[str], game_id: str, uid: str, now_utc: datetime
) -> Optional[str]:
    """Projeta o próximo reset caso o timestamp salvo já tenha expirado (ou via calendário mensal no Genshin)."""
    if mode_meta.get("reset_day"):
        return _compute_next_monthly_reset(int(mode_meta["reset_day"]), game_id, uid, now_utc)
    cycle_days = mode_meta.get("cycle_days")
    dt = _parse_utc_iso(stale_iso)
    if dt and cycle_days:
        step = timedelta(days=int(cycle_days))
        while dt <= now_utc:
            dt += step
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return None


def _schedules_disk_path() -> str:
    return get_data_path(os.path.join("static_data", "endgame_schedules.json"))


def _server_region_key(game_id: str, uid: str) -> str:
    srv_tz = endgame_extractor.get_server_timezone(game_id, uid)
    offset = srv_tz.utcoffset(None)
    hours = int(offset.total_seconds() // 3600) if offset is not None else -5
    return f"utc{hours:+d}"


def _load_disk_schedules(game_id: str, uid: str) -> Dict[str, Dict[str, Any]]:
    path = _schedules_disk_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, dict):
            game_bucket = payload.get(game_id, {})
            if isinstance(game_bucket, dict):
                region_key = _server_region_key(game_id, uid)
                bucket = game_bucket.get(region_key) or game_bucket.get("_default") or {}
                if isinstance(bucket, dict):
                    return bucket
    except Exception:
        pass
    return {}


def _save_disk_schedules(game_id: str, uid: str, schedules: Dict[str, Dict[str, Any]]) -> None:
    if not schedules:
        return
    path = _schedules_disk_path()
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        payload: Dict[str, Any] = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as rf:
                    loaded = json.load(rf)
                    if isinstance(loaded, dict):
                        payload = loaded
            except Exception:
                payload = {}
        payload.setdefault(game_id, {})
        payload[game_id][_server_region_key(game_id, uid)] = schedules
        with open(path, "w", encoding="utf-8") as wf:
            json.dump(payload, wf, ensure_ascii=False, indent=2)
    except Exception:
        pass


async def _fetch_live_reset_schedules(game_id: str, uid: str) -> Dict[str, Dict[str, Any]]:
    """Busca horários oficiais de reset na HoYoLAB sob demanda com cache em memória e disco."""
    cache_key = (game_id, uid)
    now_ts = time.time()
    cached = _RESET_SCHEDULE_CACHE.get(cache_key)
    if cached and now_ts < cached[0]:
        return cached[1]

    if not uid or not uid.isdigit():
        return {}

    cookies = get_cookies()
    if not cookies:
        return {}

    try:
        import genshin

        client = genshin.Client(cookies, lang="pt-pt")
        live = await asyncio.wait_for(
            endgame_extractor.extract_endgame_schedules(client, game_id, int(uid)),
            timeout=6.0,
        )
        if live:
            _RESET_SCHEDULE_CACHE[cache_key] = (now_ts + RESET_SCHEDULE_TTL, live)
            _save_disk_schedules(game_id, uid, live)
            return live
    except Exception:
        pass

    _RESET_SCHEDULE_CACHE[cache_key] = (now_ts + RESET_SCHEDULE_RETRY_TTL, {})
    return {}


async def _resolve_reset_schedules(
    game_id: str, uid: str, modes: List[Dict[str, Any]], lang: str
) -> List[Dict[str, Any]]:
    """Enriquece cada modo com reset_at e retorna o cronograma completo de todos os modos do jogo."""
    catalog = _ENDGAME_MODE_CATALOG.get(game_id, [])
    now_utc = datetime.now(timezone.utc)

    # 1. Coleta timestamps já presentes nos modos salvos e no cache em disco
    by_mode: Dict[str, Dict[str, Any]] = {}
    disk_scheds = _load_disk_schedules(game_id, uid)
    for mid, info in disk_scheds.items():
        if isinstance(info, dict) and info.get("reset_at"):
            by_mode[mid] = {
                "begin_at": info.get("begin_at"),
                "reset_at": info.get("reset_at"),
                "source": "hoyolab",
            }

    for m in modes:
        mid = m.get("id")
        if mid and m.get("reset_at"):
            if _is_future_iso(m.get("reset_at"), now_utc) or mid not in by_mode:
                by_mode[mid] = {
                    "begin_at": m.get("begin_at"),
                    "reset_at": m.get("reset_at"),
                    "source": "hoyolab",
                }

    # 2. Se algum modo do catálogo estiver sem reset_at futuro, consulta HoYoLAB (com cache 6h)
    missing_or_expired = any(not _is_future_iso(by_mode.get(c["id"], {}).get("reset_at"), now_utc) for c in catalog)
    if missing_or_expired and uid and uid.isdigit():
        live_scheds = await _fetch_live_reset_schedules(game_id, uid)
        for mid, info in live_scheds.items():
            if info.get("reset_at"):
                by_mode[mid] = {
                    "begin_at": info.get("begin_at"),
                    "reset_at": info.get("reset_at"),
                    "source": "hoyolab",
                }

    # 3. Constrói lista final de cronogramas (com fallback determinístico offline se expirado/sem cookies)
    reset_schedules: List[Dict[str, Any]] = []
    for c_meta in catalog:
        mid = c_meta["id"]
        entry = by_mode.get(mid, {})
        reset_at = entry.get("reset_at")
        begin_at = entry.get("begin_at")
        source = entry.get("source", "hoyolab")

        if not _is_future_iso(reset_at, now_utc):
            projected = _project_expired_reset(c_meta, reset_at, game_id, uid, now_utc)
            if projected:
                reset_at = projected
                source = "estimated"

        reset_schedules.append(
            {
                "id": mid,
                "name": c_meta["name_en"] if lang == "en" else c_meta["name_pt"],
                "badge": c_meta["badge"],
                "begin_at": begin_at,
                "reset_at": reset_at,
                "source": source,
            }
        )

    # 4. Aplica reset_at/begin_at nos modos retornados para exibição nos cards individuais
    sched_lookup = {item["id"]: item for item in reset_schedules}
    for m in modes:
        mid = m.get("id")
        if mid and mid in sched_lookup:
            m["reset_at"] = sched_lookup[mid]["reset_at"]
            if sched_lookup[mid].get("begin_at") and not m.get("begin_at"):
                m["begin_at"] = sched_lookup[mid]["begin_at"]
            m["reset_source"] = sched_lookup[mid]["source"]

    return reset_schedules


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
            if m_name == "Assalto Mortal":
                mode["name"] = "Deadly Assault"
            elif m_name in ENDGAME_MODE_EN_MAP:
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

    effective_uid = str(uid or active_uid or "").strip()
    reset_schedules = await _resolve_reset_schedules(game_id, effective_uid, modes or [], lang)

    res = {
        "status": "success",
        "game_id": game_id,
        "has_data": bool(modes and len(modes) > 0),
        "updated_at": updated_at,
        "uid": uid,
        "modes": modes or [],
        "reset_schedules": reset_schedules,
    }
    _ENDGAME_CACHE[cache_key] = (now, res)
    return res
