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
from services.media_service import get_raw_url, get_endgame_icon_url
from services.team_matcher_service import ENDGAME_MODE_EN_MAP

_ENDGAME_CACHE: Dict[Tuple[str, str, str], Tuple[float, Dict[str, Any]]] = {}
_RESET_SCHEDULE_CACHE: Dict[Tuple[str, str], Tuple[float, Dict[str, Dict[str, Any]]]] = {}
_TACTICAL_ENRICH_CACHE: Dict[Tuple[str, str], float] = {}
CACHE_TTL = 60.0
RESET_SCHEDULE_TTL = 6 * 3600.0
RESET_SCHEDULE_RETRY_TTL = 600.0
_TACTICAL_SUPPORTED_MODES = frozenset({"pure_fiction", "apocalyptic_shadow", "imaginarium_theater", "deadly_assault"})

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
    global _ENDGAME_CACHE, _RESET_SCHEDULE_CACHE, _TACTICAL_ENRICH_CACHE
    if game_id:
        clean_g = game_id.lower().strip()
        for k in [k for k in _ENDGAME_CACHE if k[0] == clean_g]:
            _ENDGAME_CACHE.pop(k, None)
        for k in [k for k in _RESET_SCHEDULE_CACHE if k[0] == clean_g]:
            _RESET_SCHEDULE_CACHE.pop(k, None)
        for k in [k for k in _TACTICAL_ENRICH_CACHE if k[0] == clean_g]:
            _TACTICAL_ENRICH_CACHE.pop(k, None)
    else:
        _ENDGAME_CACHE.clear()
        _RESET_SCHEDULE_CACHE.clear()
        _TACTICAL_ENRICH_CACHE.clear()


def _proxy_tactical_icon(icon_url: Optional[str], width: int = 64) -> str:
    """Formata URLs externas de ícones de chefes/buffs via proxy anti-CORS de forma idempotente."""
    if not icon_url or not isinstance(icon_url, str):
        return ""
    raw_url = get_raw_url(icon_url).strip()
    if raw_url.startswith("http://") or raw_url.startswith("https://"):
        return f"/api/proxy_image?url={urllib.parse.quote(raw_url, safe='')}&w={width}&format=webp"
    return icon_url.strip()


def _needs_tactical_enrichment(modes: List[Dict[str, Any]]) -> bool:
    """Detecta se algum modo com suporte a chefes/buffs foi salvo antes da extração tática."""
    for mode in modes:
        mid = mode.get("id")
        if mid not in _TACTICAL_SUPPORTED_MODES:
            continue
        teams = mode.get("teams") or []
        if not teams:
            continue
        has_any_tactical = any(bool(t.get("boss")) or bool(t.get("buffs")) for t in teams)
        if not has_any_tactical:
            return True
    return False


def _extract_act_number(team_name: str) -> Optional[int]:
    m = re.search(r"(?:Ato|Act)\s*(\d+)", str(team_name or ""), re.IGNORECASE)
    return int(m.group(1)) if m else None


def _merge_tactical_meta(modes: List[Dict[str, Any]], tactical_meta: Dict[str, List[Dict[str, Any]]]) -> bool:
    """Mescla chefes/buffs/ícones de inimigos nos modos já salvos sem sobrescrever equipes ou pontuações."""
    changed = False
    for mode in modes:
        mid = mode.get("id")
        if not mid or mid not in tactical_meta:
            continue
        src_teams = tactical_meta[mid]
        dst_teams = mode.get("teams") or []
        if not src_teams or not dst_teams:
            continue

        if mid == "imaginarium_theater":
            by_round = {int(st["round_id"]): st for st in src_teams if st.get("round_id") is not None}
            for idx, dt in enumerate(dst_teams):
                rid = _extract_act_number(dt.get("name", ""))
                st = by_round.get(rid) if rid is not None else (src_teams[idx] if idx < len(src_teams) else None)
                if not st:
                    continue
                if st.get("boss") and not dt.get("boss"):
                    dt["boss"] = st["boss"]
                    changed = True
                if st.get("buffs") and not dt.get("buffs"):
                    dt["buffs"] = st["buffs"]
                    changed = True
                if st.get("monsters") and not dt.get("monsters"):
                    dt["monsters"] = st["monsters"]
                    changed = True
        else:
            for idx, dt in enumerate(dst_teams):
                if idx >= len(src_teams):
                    break
                st = src_teams[idx]
                if st.get("boss") and not dt.get("boss"):
                    dt["boss"] = st["boss"]
                    changed = True
                if st.get("buffs") and not dt.get("buffs"):
                    dt["buffs"] = st["buffs"]
                    changed = True
    return changed


async def _enrich_endgame_tactical_meta(game_id: str, uid: str, modes: List[Dict[str, Any]]) -> None:
    """Preenche chefes e buffs sob demanda para bancos legados e persiste o resultado no SQLite."""
    if not modes or not uid or not uid.isdigit() or not _needs_tactical_enrichment(modes):
        return
    cache_key = (game_id, uid)
    now_ts = time.time()
    if now_ts < _TACTICAL_ENRICH_CACHE.get(cache_key, 0.0):
        return

    cookies = get_cookies()
    if not cookies:
        return

    try:
        import genshin

        client = genshin.Client(cookies, lang="pt-pt")
        live_meta = await asyncio.wait_for(
            endgame_extractor.extract_endgame_tactical_meta(client, game_id, int(uid)),
            timeout=6.0,
        )
        if live_meta and _merge_tactical_meta(modes, live_meta):
            _TACTICAL_ENRICH_CACHE[cache_key] = now_ts + RESET_SCHEDULE_TTL
            try:
                database.save_endgame_data(game_id, uid, modes)
            except Exception:
                pass
            return
    except Exception:
        pass

    _TACTICAL_ENRICH_CACHE[cache_key] = now_ts + RESET_SCHEDULE_RETRY_TTL


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
                "icon": get_endgame_icon_url(game_id, mid) or None,
                "begin_at": begin_at,
                "reset_at": reset_at,
                "source": source,
            }
        )

    # 4. Aplica reset_at/begin_at e ícone oficial nos modos retornados para exibição nos cards individuais
    sched_lookup = {item["id"]: item for item in reset_schedules}
    for m in modes:
        mid = m.get("id")
        if mid and mid in sched_lookup:
            m["reset_at"] = sched_lookup[mid]["reset_at"]
            if sched_lookup[mid].get("begin_at") and not m.get("begin_at"):
                m["begin_at"] = sched_lookup[mid]["begin_at"]
            m["reset_source"] = sched_lookup[mid]["source"]
            if sched_lookup[mid].get("icon"):
                m["icon"] = sched_lookup[mid]["icon"]

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

    effective_uid = str(uid or active_uid or "").strip()

    # 3.5. Backfill tático (chefes/buffs) para dados legados já salvos no SQLite antes da v1.4
    if modes and effective_uid:
        await _enrich_endgame_tactical_meta(game_id, effective_uid, modes)

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
                # Proxy seguro para ícone de chefe, buffs/bênçãos e monstros
                boss = team.get("boss")
                if isinstance(boss, dict) and boss.get("icon"):
                    boss["icon"] = _proxy_tactical_icon(boss["icon"], width=64)
                for buff in team.get("buffs") or []:
                    if isinstance(buff, dict) and buff.get("icon"):
                        buff["icon"] = _proxy_tactical_icon(buff["icon"], width=64)
                for mon in team.get("monsters") or []:
                    if isinstance(mon, dict) and mon.get("icon"):
                        mon["icon"] = _proxy_tactical_icon(mon["icon"], width=48)

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


_GAME_SHORT_LABELS: Dict[str, str] = {
    "hsr": "HSR",
    "genshin": "Genshin",
    "zzz": "ZZZ",
}
URGENT_PENDING_THRESHOLD_SECONDS = 72 * 3600
BANNER_ENDING_SOON_THRESHOLD_SECONDS = 48 * 3600


def _build_active_banner_resets(now_utc: datetime) -> List[Dict[str, Any]]:
    """Agrupa e ordena os banners ativos de personagem dos 3 jogos pela data/hora real de virada."""
    try:
        from services import gacha_service
    except Exception:
        return []

    grouped: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    for gid in ("genshin", "hsr", "zzz"):
        try:
            defaults = gacha_service.get_gacha_simulator_defaults(gid, banner_type="character")
        except Exception:
            continue

        for banner in defaults.get("available_banners") or []:
            if not isinstance(banner, dict):
                continue
            end_at = banner.get("end_at")
            duration_type = str(banner.get("duration_type") or "phase_1").lower()
            if not end_at or duration_type == "collab":
                continue

            dt_end = _parse_utc_iso(end_at)
            if dt_end is None:
                continue
            secs_rem = max(0, int((dt_end - now_utc).total_seconds()))

            char_name = str(banner.get("character_name") or "").strip()
            if not char_name:
                continue
            c_info = banner.get("character_info") if isinstance(banner.get("character_info"), dict) else {}
            c_icon = str(c_info.get("icon") or banner.get("banner_image") or "").strip()

            g_key = (gid, end_at, duration_type)
            if g_key not in grouped:
                grouped[g_key] = {
                    "game_id": gid,
                    "game_label": _GAME_SHORT_LABELS.get(gid, gid.upper()),
                    "primary_character": char_name,
                    "characters": [],
                    "patch_label": str(banner.get("patch_label") or defaults.get("patch_info") or "").strip(),
                    "duration_type": duration_type,
                    "phase": banner.get("phase"),
                    "banner_time": str(banner.get("banner_time") or defaults.get("banner_time") or "23:30"),
                    "end_date": banner.get("end_date"),
                    "end_at": end_at,
                    "seconds_remaining": secs_rem,
                    "is_ending_soon": secs_rem <= BANNER_ENDING_SOON_THRESHOLD_SECONDS,
                }

            bucket = grouped[g_key]
            existing_names = {c["name"].lower() for c in bucket["characters"]}
            if char_name.lower() not in existing_names:
                bucket["characters"].append({"name": char_name, "icon": c_icon})
                if banner.get("is_primary"):
                    bucket["primary_character"] = char_name

    banner_items: List[Dict[str, Any]] = []
    for bucket in grouped.values():
        chars = bucket["characters"]
        # Mantém o personagem principal em 1º lugar na lista visual
        prim_lower = bucket["primary_character"].lower()
        chars.sort(key=lambda c: 0 if c["name"].lower() == prim_lower else 1)
        bucket["title"] = " · ".join(c["name"] for c in chars[:3]) + (
            f" +{len(chars) - 3}" if len(chars) > 3 else ""
        )
        banner_items.append(bucket)

    banner_items.sort(
        key=lambda b: (
            b["seconds_remaining"] if b["seconds_remaining"] is not None else 10**12,
            b["game_id"],
            b["title"],
        )
    )
    return banner_items


def _detect_primary_server_timezone(lang: str = "pt") -> Tuple[timezone, str]:
    """Infere o fuso do servidor HoYoverse a partir dos UIDs ativos (padrão América UTC-5)."""
    chosen_game = "genshin"
    chosen_uid = "600000000"
    for g in ("genshin", "hsr", "zzz"):
        uid_val = str(database.get_active_uid(g) or "").strip()
        if uid_val and uid_val.isdigit():
            chosen_game = g
            chosen_uid = uid_val
            break

    srv_tz = endgame_extractor.get_server_timezone(chosen_game, chosen_uid)
    offset = srv_tz.utcoffset(None)
    hours = int(offset.total_seconds() // 3600) if offset is not None else -5
    if hours == -5:
        region = "America" if lang == "en" else "América"
    elif hours == 1:
        region = "Europe" if lang == "en" else "Europa"
    else:
        region = "Asia" if lang == "en" else "Ásia"
    return srv_tz, f"UTC{hours:+d} ({region})"


def compute_server_cycle_resets(
    now_utc: Optional[datetime] = None,
    lang: str = "pt",
    server_tz: Optional[timezone] = None,
    tz_label: Optional[str] = None,
) -> Dict[str, str]:
    """Calcula os próximos resets Diário (04:00) e Semanal (Segunda 04:00) no horário do servidor."""
    ref_utc = now_utc.astimezone(timezone.utc) if now_utc else datetime.now(timezone.utc)
    if server_tz is None:
        srv_tz, auto_label = _detect_primary_server_timezone(lang=lang)
        label = tz_label or auto_label
    else:
        srv_tz = server_tz
        if tz_label:
            label = tz_label
        else:
            offset = srv_tz.utcoffset(None)
            hours = int(offset.total_seconds() // 3600) if offset is not None else -5
            label = f"UTC{hours:+d}"

    now_srv = ref_utc.astimezone(srv_tz)

    # Reset Diário: 04:00 do servidor
    daily_target = now_srv.replace(hour=4, minute=0, second=0, microsecond=0)
    if daily_target <= now_srv:
        daily_target += timedelta(days=1)

    # Reset Semanal: Segunda-feira (weekday == 0) às 04:00 do servidor
    days_until_monday = (7 - now_srv.weekday()) % 7
    weekly_target = (now_srv + timedelta(days=days_until_monday)).replace(hour=4, minute=0, second=0, microsecond=0)
    if weekly_target <= now_srv:
        weekly_target += timedelta(days=7)

    return {
        "daily_reset_at": daily_target.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "weekly_reset_at": weekly_target.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "server_tz_label": label,
    }


def _evaluate_mode_completion(
    mode_data: Optional[Dict[str, Any]],
) -> Tuple[str, Optional[int], Optional[int], Optional[str], bool]:
    """Avalia se um modo endgame está 'completed', 'in_progress' ou 'pending' com base nos registros salvos."""
    if not isinstance(mode_data, dict):
        return ("pending", None, None, None, False)

    teams = mode_data.get("teams") or []
    stars_raw = mode_data.get("stars")
    max_stars_raw = mode_data.get("max_stars")
    metric_val = str(mode_data.get("metric_value") or "").strip() or None

    stars: Optional[int] = None
    max_stars: Optional[int] = None
    try:
        if stars_raw is not None and str(stars_raw).strip() != "":
            stars = int(stars_raw)
    except (TypeError, ValueError):
        stars = None
    try:
        if max_stars_raw is not None and str(max_stars_raw).strip() != "":
            max_stars = int(max_stars_raw)
    except (TypeError, ValueError):
        max_stars = None

    has_record = bool(teams) or (stars is not None and stars > 0) or bool(metric_val and metric_val not in ("None", "?"))

    if stars is not None and max_stars is not None and max_stars > 0:
        if stars >= max_stars:
            return ("completed", stars, max_stars, metric_val, True)
        if stars > 0 or bool(teams):
            return ("in_progress", stars, max_stars, metric_val, True)
        return ("pending", stars, max_stars, metric_val, has_record)

    # Modos sem contagem numérica de estrelas (ex.: Defesa Shiyu com classificação S/A/B)
    if metric_val:
        mv_up = metric_val.upper().strip()
        if mv_up in ("S", "S+", "CONCLUÍDO", "CONCLUIDO", "COMPLETED") or mv_up.startswith("RANK S"):
            return ("completed", stars, max_stars, metric_val, True)
        if has_record:
            return ("in_progress", stars, max_stars, metric_val, True)

    if teams:
        return ("in_progress", stars, max_stars, metric_val, True)

    return ("pending", stars, max_stars, metric_val, False)


async def get_unified_reset_radar(lang: str = "pt") -> Dict[str, Any]:
    """Agrega os 7 modos de endgame dos 3 jogos ordenados por urgência + resets Diário e Semanal."""
    clean_lang = "en" if str(lang or "pt").lower().startswith("en") else "pt"
    now_utc = datetime.now(timezone.utc)
    server_resets = compute_server_cycle_resets(now_utc=now_utc, lang=clean_lang)

    game_ids = ("hsr", "genshin", "zzz")
    results = await asyncio.gather(
        *(get_endgame(gid, lang=clean_lang) for gid in game_ids),
        return_exceptions=True,
    )

    items: List[Dict[str, Any]] = []
    for gid, payload in zip(game_ids, results):
        catalog = _ENDGAME_MODE_CATALOG.get(gid, [])
        modes_by_id: Dict[str, Dict[str, Any]] = {}
        sched_by_id: Dict[str, Dict[str, Any]] = {}

        if isinstance(payload, dict):
            for m in payload.get("modes") or []:
                if isinstance(m, dict) and m.get("id"):
                    modes_by_id[m["id"]] = m
            for sc in payload.get("reset_schedules") or []:
                if isinstance(sc, dict) and sc.get("id"):
                    sched_by_id[sc["id"]] = sc

        for c_meta in catalog:
            mid = c_meta["id"]
            sched = sched_by_id.get(mid, {})
            mode_data = modes_by_id.get(mid)

            reset_at = sched.get("reset_at") or (mode_data.get("reset_at") if isinstance(mode_data, dict) else None)
            begin_at = sched.get("begin_at") or (mode_data.get("begin_at") if isinstance(mode_data, dict) else None)
            source = sched.get("source") or "estimated"
            icon_url = sched.get("icon") or get_endgame_icon_url(gid, mid) or None
            display_name = sched.get("name") or (c_meta["name_en"] if clean_lang == "en" else c_meta["name_pt"])

            status, stars, max_stars, metric_value, has_record = _evaluate_mode_completion(mode_data)

            dt_reset = _parse_utc_iso(reset_at)
            seconds_remaining: Optional[int] = None
            if dt_reset is not None:
                seconds_remaining = max(0, int((dt_reset - now_utc).total_seconds()))

            is_urgent_pending = (
                status != "completed"
                and seconds_remaining is not None
                and seconds_remaining <= URGENT_PENDING_THRESHOLD_SECONDS
            )

            items.append(
                {
                    "game_id": gid,
                    "game_label": _GAME_SHORT_LABELS.get(gid, gid.upper()),
                    "id": mid,
                    "name": display_name,
                    "badge": c_meta["badge"],
                    "icon": icon_url,
                    "begin_at": begin_at,
                    "reset_at": reset_at,
                    "source": source,
                    "status": status,
                    "stars": stars,
                    "max_stars": max_stars,
                    "metric_value": metric_value,
                    "has_record": has_record,
                    "seconds_remaining": seconds_remaining,
                    "is_urgent_pending": is_urgent_pending,
                }
            )

    # Ordenação por urgência:
    # 1º Pendências próximas do reset (<= 72h), 2º Menor tempo restante até o reset, 3º Pendente antes de concluído
    items.sort(
        key=lambda it: (
            0 if it["is_urgent_pending"] else 1,
            it["seconds_remaining"] if it["seconds_remaining"] is not None else 10**12,
            0 if it["status"] != "completed" else 1,
            it["game_id"],
            it["id"],
        )
    )

    completed_count = sum(1 for it in items if it["status"] == "completed")
    urgent_pending_count = sum(1 for it in items if it["is_urgent_pending"])
    pending_count = len(items) - completed_count
    banner_items = _build_active_banner_resets(now_utc)
    banners_ending_soon_count = sum(1 for b in banner_items if b.get("is_ending_soon"))

    return {
        "status": "success",
        "generated_at": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "server_resets": server_resets,
        "summary": {
            "total_modes": len(items),
            "completed_count": completed_count,
            "pending_count": pending_count,
            "urgent_pending_count": urgent_pending_count,
            "banners_count": len(banner_items),
            "banners_ending_soon_count": banners_ending_soon_count,
        },
        "items": items,
        "banners": banner_items,
    }
