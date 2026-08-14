import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from extractor import clean_relic_name

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_NAME = os.path.join(BASE_DIR, "hoyo_app.db")

def get_connection() -> sqlite3.Connection:
    """Retorna uma conexão configurada com o banco de dados SQLite."""
    conn = sqlite3.connect(DATABASE_NAME, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    except Exception:
        pass
    return conn

def parse_stats_from_raw_md(raw_md: str) -> Dict[str, str]:
    """Extrai o dicionário de status finais a partir do texto markdown do personagem."""
    if not raw_md:
        return {}
    import re
    match = re.search(r'\*\*(?:Status Finais|Status|Atributos Finais):\*\*\s*(.*?)(?=\n\n|\n  |\Z)', raw_md, re.DOTALL | re.I)
    if not match:
        return {}
    res = {}
    for part in match.group(1).replace('\n', ' ').split(','):
        if ':' in part:
            k, v = part.split(':', 1)
            k_clean, v_clean = k.strip(), v.strip()
            if k_clean and v_clean:
                res[k_clean] = v_clean
    return res

def backfill_snapshot_stats() -> None:
    """Preenche retroativamente os status dos personagens em snapshots históricos existentes."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT uid, name, raw_md, stats_json FROM characters")
            char_map = {}
            for r in cur.fetchall():
                r_keys = r.keys()
                st = {}
                if "stats_json" in r_keys and r["stats_json"]:
                    try:
                        st = json.loads(r["stats_json"])
                    except Exception:
                        st = {}
                if not st and r["raw_md"]:
                    st = parse_stats_from_raw_md(r["raw_md"])
                if st:
                    c_name = r["name"].lower().strip()
                    c_uid = r["uid"]
                    char_map[(c_uid, c_name)] = st
                    char_map[c_name] = st

            cur.execute("SELECT id, snapshot_json FROM account_snapshots")
            snaps = cur.fetchall()
            for s in snaps:
                snap_id = s["id"]
                s_json_str = s["snapshot_json"]
                if not s_json_str:
                    continue
                try:
                    s_json = json.loads(s_json_str)
                except Exception:
                    continue
                
                all_c = s_json.get("all_characters") or []
                top_c = s_json.get("top_built_characters") or []
                changed = False

                for c_list in [all_c, top_c]:
                    for c in c_list:
                        if not c.get("stats"):
                            c_name = (c.get("name") or "").lower().strip()
                            c_uid = c.get("uid")
                            st = char_map.get((c_uid, c_name)) or char_map.get(c_name)
                            if st:
                                c["stats"] = st
                                changed = True
                
                if changed:
                    cur.execute("UPDATE account_snapshots SET snapshot_json = ? WHERE id = ?", (json.dumps(s_json, ensure_ascii=False), snap_id))
    except Exception as err:
        print(f"[AVISO] Falha na migração automática de stats em snapshots: {err}")


def init_db() -> None:
    """Inicializa as tabelas e índices do banco de dados SQLite se não existirem."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Tabela de Contas
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_accounts (
            uid TEXT PRIMARY KEY,
            game_id TEXT NOT NULL,
            nickname TEXT,
            level INTEGER,
            active_days INTEGER,
            updated_at TEXT
        )
        """)
        
        # 2. Tabela de Personagens
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS characters (
            uid TEXT,
            game_id TEXT NOT NULL,
            name TEXT NOT NULL,
            level INTEGER,
            rarity INTEGER,
            rank_str TEXT,
            element TEXT,
            icon TEXT,
            gacha_art TEXT,
            weapon_name TEXT,
            weapon_level INTEGER,
            weapon_rank INTEGER,
            weapon_icon TEXT,
            raw_md TEXT,
            char_id TEXT,
            PRIMARY KEY (uid, name)
        )
        """)
        
        # Migrações seguras de colunas caso venham de versões antigas
        try:
            cursor.execute("ALTER TABLE characters ADD COLUMN gacha_art TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE characters ADD COLUMN char_id TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE characters ADD COLUMN skills_json TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE characters ADD COLUMN stats_json TEXT")
        except sqlite3.OperationalError:
            pass
        
        # 3. Tabela de Relíquias / Artefatos / Discos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_relics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT,
            character_name TEXT,
            name TEXT,
            slot TEXT,
            main_stat TEXT,
            sub_stats TEXT,
            icon TEXT,
            FOREIGN KEY(uid, character_name) REFERENCES characters(uid, name) ON DELETE CASCADE
        )
        """)
        
        # 4. Tabela de Cache de Notas Diárias (Resina / Energia)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_notes_cache (
            uid TEXT,
            game_id TEXT NOT NULL,
            nickname TEXT,
            current_energy INTEGER,
            max_energy INTEGER,
            recovery_time TEXT,
            extra_info TEXT,
            updated_at TEXT,
            PRIMARY KEY (uid, game_id)
        )
        """)
        
        # 5. Tabela de Logs do Auto-Check-in Diário
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_checkin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            game_id TEXT NOT NULL,
            uid TEXT,
            status TEXT,
            message TEXT,
            timestamp TEXT
        )
        """)
        
        # 6. Tabela de Snapshots da Conta para Timeline de Evolução
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid TEXT NOT NULL,
            game_id TEXT NOT NULL,
            character_count INTEGER,
            five_star_count INTEGER,
            average_build_score REAL,
            snapshot_json TEXT,
            created_at TEXT NOT NULL
        )
        """)
        
        # Criação de índices para acelerar consultas frequentes do Roster e de Relíquias
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_characters_game_uid ON characters(game_id, uid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relics_uid_char ON character_relics(uid, character_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkin_date ON daily_checkin_logs(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_uid ON account_snapshots(game_id, uid)")
        
    print("[INFO] Banco de dados SQLite inicializado com sucesso.")
    fix_skills_json_max_levels()
    backfill_snapshot_stats()

def fix_skills_json_max_levels():
    """Garante que os níveis máximos das habilidades/rastros estejam corretos no banco de dados."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT uid, name, game_id, skills_json FROM characters WHERE skills_json IS NOT NULL AND skills_json != ''")
            rows = cursor.fetchall()
            for r in rows:
                s_json = r["skills_json"]
                if not s_json:
                    continue
                skills = json.loads(s_json)
                changed = False
                g_clean = (r["game_id"] or "hsr").lower().strip()
                for idx, sk in enumerate(skills):
                    if g_clean == "hsr":
                        target_max = 6 if idx == 0 else (10 if idx < 4 else 1)
                    elif g_clean == "genshin":
                        target_max = 10 if idx < 3 else 1
                    else:
                        target_max = 12 if idx < 5 else 1
                    
                    if sk.get("max_level") != target_max:
                        sk["max_level"] = target_max
                        changed = True
                
                if changed:
                    cursor.execute(
                        "UPDATE characters SET skills_json = ? WHERE uid = ? AND name = ? AND game_id = ?",
                        (json.dumps(skills, ensure_ascii=False), r["uid"], r["name"], r["game_id"])
                    )
    except Exception as e:
        print(f"[Aviso] Erro ao atualizar max_level das habilidades: {e}")

# Inicializa o banco ao carregar o módulo
init_db()

def save_account_snapshot(uid: str, game_id: str, roster_data: List[Dict[str, Any]]) -> None:
    """Calcula métricas agregadas ricas da conta e salva um snapshot completo com todos os personagens."""
    if not roster_data:
        return
    
    from build_calculator import score_relic, normalize_char_name

    game_id_clean = (game_id or "hsr").lower().strip()
    max_lvl = 90 if game_id_clean == "genshin" else (80 if game_id_clean == "hsr" else 60)

    char_count = len(roster_data)
    five_star_count = sum(1 for c in roster_data if str(c.get("rarity", "")).startswith("5") or c.get("rarity") in [5, "5"])
    four_star_count = char_count - five_star_count
    max_lvl_count = sum(1 for c in roster_data if c.get("level", 0) >= max_lvl)

    scores = []
    all_chars_data = []
    endgame_ready_count = 0
    total_relics = 0

    for c in roster_data:
        char_name = c.get("name", "")
        norm = normalize_char_name(char_name)
        lvl = c.get("level", 1)
        rarity = c.get("rarity", 4)
        rank_str = c.get("rank_str", "") or (f"C{c.get('constellation', 0)}" if "constellation" in c else f"E{c.get('rank', 0)}")
        relics = c.get("relics", [])
        total_relics += len(relics)

        relic_scores = []
        for r in relics:
            slot = r.get("slot", "")
            main_stat = r.get("main") or r.get("main_stat") or ""
            sub_stats = r.get("sub") or r.get("sub_stats") or ""
            if isinstance(sub_stats, list):
                sub_stats_str = ", ".join([f"{s.get('name','')}: {s.get('val','')}" if isinstance(s, dict) else str(s) for s in sub_stats])
            else:
                sub_stats_str = str(sub_stats)
            g, sc = score_relic(game_id_clean, char_name, slot, main_stat, sub_stats_str)
            if sc > 0:
                relic_scores.append(sc)

        char_score = round(sum(relic_scores) / len(relic_scores), 1) if relic_scores else 0.0
        if char_score > 0:
            scores.append(char_score)

        grade = "SS" if char_score >= 85 else ("S+" if char_score >= 75 else ("S" if char_score >= 60 else ("A" if char_score >= 45 else ("B" if char_score >= 30 else "C"))))
        
        if lvl >= max_lvl - 10 and char_score >= 50.0:
            endgame_ready_count += 1

        weapon_data = c.get("weapon") or {}
        if not weapon_data and c.get("weapon_name"):
            weapon_data = {
                "name": c.get("weapon_name", ""),
                "level": c.get("weapon_level", 1),
                "rank": c.get("weapon_rank", 1),
                "icon": c.get("weapon_icon", "")
            }

        all_chars_data.append({
            "id": str(c.get("id", "")),
            "name": char_name,
            "norm": norm,
            "level": lvl,
            "rarity": rarity,
            "rank_str": rank_str,
            "element": c.get("element", ""),
            "icon": c.get("icon", ""),
            "gacha_art": c.get("gacha_art", ""),
            "weapon": weapon_data,
            "weapon_name": weapon_data.get("name", ""),
            "weapon_level": weapon_data.get("level", 1),
            "relics": relics,
            "skills": c.get("skills", []),
            "stats": c.get("stats", {}),
            "score": char_score,
            "grade": grade,
            "relics_count": len(relics)
        })

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    endgame_readiness_pct = min(100.0, round((endgame_ready_count / 8.0) * 100, 1))
    top_built = sorted(all_chars_data, key=lambda x: x["score"], reverse=True)[:5]

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    summary_json = json.dumps({
        "total_chars": char_count,
        "five_stars": five_star_count,
        "four_stars": four_star_count,
        "max_level_count": max_lvl_count,
        "avg_score": avg_score,
        "endgame_readiness_pct": endgame_readiness_pct,
        "endgame_ready_count": endgame_ready_count,
        "total_relics_analyzed": total_relics,
        "top_built_characters": top_built,
        "all_characters": all_chars_data
    })

    with get_connection() as conn:
        cursor = conn.cursor()

        # Verifica se já existe um snapshot gravado para este UID e jogo
        cursor.execute("""
            SELECT id, snapshot_json, character_count, five_star_count, average_build_score 
            FROM account_snapshots 
            WHERE game_id = ? AND uid = ? 
            ORDER BY id DESC LIMIT 1
        """, (game_id_clean, uid))
        latest_row = cursor.fetchone()

        if latest_row:
            latest_json_str = latest_row["snapshot_json"]
            try:
                latest_data = json.loads(latest_json_str or "{}")
                latest_chars = latest_data.get("all_characters") or []
                
                same_counts = (latest_row["character_count"] == char_count and 
                               latest_row["five_star_count"] == five_star_count and 
                               abs(latest_row["average_build_score"] - avg_score) < 0.01)

                if same_counts and len(latest_chars) == len(all_chars_data):
                    latest_map = { (c.get("norm") or c.get("name", "").lower().strip()): c for c in latest_chars }
                    has_changes = False

                    for cur_c in all_chars_data:
                        norm = cur_c.get("norm") or cur_c.get("name", "").lower().strip()
                        prev_c = latest_map.get(norm)
                        if not prev_c:
                            has_changes = True
                            break
                        
                        if (cur_c.get("level") != prev_c.get("level") or
                            cur_c.get("rank_str") != prev_c.get("rank_str") or
                            cur_c.get("score") != prev_c.get("score") or
                            json.dumps(cur_c.get("weapon"), sort_keys=True) != json.dumps(prev_c.get("weapon"), sort_keys=True) or
                            json.dumps(cur_c.get("relics"), sort_keys=True) != json.dumps(prev_c.get("relics"), sort_keys=True) or
                            json.dumps(cur_c.get("skills"), sort_keys=True) != json.dumps(prev_c.get("skills"), sort_keys=True)):
                            has_changes = True
                            break
                    
                    if not has_changes:
                        print(f"[INFO] Roster de {game_id_clean.upper()} (UID {uid}) não sofreu nenhuma alteração. Nulo o salvamento de snapshot duplicado.")
                        return
            except Exception as check_err:
                print(f"[AVISO] Falha ao comparar com o último snapshot: {check_err}")

        cursor.execute("""
        INSERT INTO account_snapshots (uid, game_id, character_count, five_star_count, average_build_score, snapshot_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (uid, game_id_clean, char_count, five_star_count, avg_score, summary_json, now_str))

def compare_two_snapshots(game_id: str, snap_id_a: int, snap_id_b: int) -> Dict[str, Any]:
    """Compara minuciosamente dois snapshots quaisquer pelo ID para exibir diffs de personagens, atributos, armas e relíquias."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM account_snapshots WHERE id IN (?, ?)", (snap_id_a, snap_id_b))
        rows = {r["id"]: dict(r) for r in cursor.fetchall()}
        
        if snap_id_a not in rows or snap_id_b not in rows:
            return {}

        snap_a = rows[snap_id_a]
        snap_b = rows[snap_id_b]

        # Garantir que A é o snapshot mais antigo e B é o mais recente
        if snap_a["created_at"] > snap_b["created_at"] or (snap_a["created_at"] == snap_b["created_at"] and snap_a["id"] > snap_b["id"]):
            snap_a, snap_b = snap_b, snap_a

        details_a = json.loads(snap_a.get("snapshot_json") or "{}") if snap_a.get("snapshot_json") else {}
        details_b = json.loads(snap_b.get("snapshot_json") or "{}") if snap_b.get("snapshot_json") else {}

        chars_a = details_a.get("all_characters") or details_a.get("top_built_characters") or []
        chars_b = details_b.get("all_characters") or details_b.get("top_built_characters") or []

        map_a = { (c.get("norm") or c.get("name", "").lower().strip()): c for c in chars_a }
        map_b = { (c.get("norm") or c.get("name", "").lower().strip()): c for c in chars_b }

        delta_chars = snap_b.get("character_count", 0) - snap_a.get("character_count", 0)
        delta_5star = snap_b.get("five_star_count", 0) - snap_a.get("five_star_count", 0)
        delta_avg_score = round(snap_b.get("average_build_score", 0.0) - snap_a.get("average_build_score", 0.0), 1)

        readiness_a = details_a.get("endgame_readiness_pct", 0.0)
        readiness_b = details_b.get("endgame_readiness_pct", 0.0)
        delta_readiness = round(readiness_b - readiness_a, 1)

        cursor.execute("SELECT name, raw_md, stats_json FROM characters")
        char_db_map = {}
        for r in cursor.fetchall():
            r_keys = r.keys()
            st = {}
            if "stats_json" in r_keys and r["stats_json"]:
                try:
                    st = json.loads(r["stats_json"])
                except Exception:
                    st = {}
            if not st and r["raw_md"]:
                st = parse_stats_from_raw_md(r["raw_md"])
            if st:
                char_db_map[r["name"].lower().strip()] = st

        all_norms = list(dict.fromkeys(list(map_b.keys()) + list(map_a.keys())))
        char_diffs = []

        for norm in all_norms:
            ca = map_a.get(norm)
            cb = map_b.get(norm)

            if not ca and cb:
                if not cb.get("stats"):
                    cb["stats"] = char_db_map.get((cb.get("name") or "").lower().strip(), {})
                char_diffs.append({
                    "name": cb.get("name"),
                    "norm": norm,
                    "icon": cb.get("icon"),
                    "rarity": cb.get("rarity", 4),
                    "element": cb.get("element", ""),
                    "is_new": True,
                    "is_modified": True,
                    "base": None,
                    "target": cb,
                    "diffs": {
                        "level_diff": cb.get("level", 1),
                        "score_diff": cb.get("score", 0.0),
                        "rank_changed": False,
                        "weapon_changed": False
                    }
                })
            elif ca and not cb:
                if not ca.get("stats"):
                    ca["stats"] = char_db_map.get((ca.get("name") or "").lower().strip(), {})
                char_diffs.append({
                    "name": ca.get("name"),
                    "norm": norm,
                    "icon": ca.get("icon"),
                    "rarity": ca.get("rarity", 4),
                    "element": ca.get("element", ""),
                    "is_new": False,
                    "is_removed": True,
                    "base": ca,
                    "target": None,
                    "diffs": {}
                })
            else:
                lvl_diff = cb.get("level", 0) - ca.get("level", 0)
                score_diff = round(cb.get("score", 0.0) - ca.get("score", 0.0), 1)
                rank_changed = ca.get("rank_str") != cb.get("rank_str")

                w_a = ca.get("weapon") or {"name": ca.get("weapon_name", ""), "level": ca.get("weapon_level", 1)}
                w_b = cb.get("weapon") or {"name": cb.get("weapon_name", ""), "level": cb.get("weapon_level", 1)}
                weapon_changed = w_a.get("name") != w_b.get("name")
                weapon_upgraded = w_a.get("level") != w_b.get("level") or w_a.get("rank") != w_b.get("rank")

                relics_a = ca.get("relics", [])
                relics_b = cb.get("relics", [])
                relics_changed = json.dumps(relics_a, sort_keys=True) != json.dumps(relics_b, sort_keys=True)

                skills_a = ca.get("skills", [])
                skills_b = cb.get("skills", [])
                skills_changed = json.dumps(skills_a, sort_keys=True) != json.dumps(skills_b, sort_keys=True)

                stats_a = ca.get("stats") or parse_stats_from_raw_md(ca.get("raw_md", "")) or char_db_map.get((ca.get("name") or "").lower().strip(), {})
                stats_b = cb.get("stats") or parse_stats_from_raw_md(cb.get("raw_md", "")) or char_db_map.get((cb.get("name") or "").lower().strip(), {})
                ca["stats"] = stats_a
                cb["stats"] = stats_b
                stats_changed = json.dumps(stats_a, sort_keys=True) != json.dumps(stats_b, sort_keys=True)

                is_modified = (lvl_diff != 0 or score_diff != 0.0 or rank_changed or weapon_changed or weapon_upgraded or relics_changed or skills_changed or stats_changed)

                char_diffs.append({
                    "name": cb.get("name") or ca.get("name"),
                    "norm": norm,
                    "icon": cb.get("icon") or ca.get("icon"),
                    "rarity": cb.get("rarity") or ca.get("rarity", 4),
                    "element": cb.get("element") or ca.get("element", ""),
                    "is_new": False,
                    "is_modified": is_modified,
                    "base": ca,
                    "target": cb,
                    "diffs": {
                        "level_diff": lvl_diff,
                        "score_diff": score_diff,
                        "rank_changed": rank_changed,
                        "weapon_changed": weapon_changed,
                        "weapon_upgraded": weapon_upgraded,
                        "relics_changed": relics_changed,
                        "skills_changed": skills_changed,
                        "stats_changed": stats_changed
                    }
                })

        return {
            "game_id": game_id,
            "snap_a": {
                "id": snap_a["id"],
                "created_at": snap_a["created_at"],
                "character_count": snap_a["character_count"],
                "five_star_count": snap_a["five_star_count"],
                "average_build_score": snap_a["average_build_score"],
                "endgame_readiness_pct": readiness_a
            },
            "snap_b": {
                "id": snap_b["id"],
                "created_at": snap_b["created_at"],
                "character_count": snap_b["character_count"],
                "five_star_count": snap_b["five_star_count"],
                "average_build_score": snap_b["average_build_score"],
                "endgame_readiness_pct": readiness_b
            },
            "summary_diff": {
                "delta_chars": delta_chars,
                "delta_5star": delta_5star,
                "delta_avg_score": delta_avg_score,
                "delta_readiness": delta_readiness
            },
            "char_diffs": char_diffs
        }

def get_account_history(game_id: str, uid: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retorna o histórico de snapshots comparando o snapshot atual com o anterior para gerar o diff de cada personagem."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if uid:
            cursor.execute("""
            SELECT id, uid, game_id, character_count, five_star_count, average_build_score, snapshot_json, created_at
            FROM account_snapshots WHERE game_id = ? AND uid = ? ORDER BY created_at ASC
            """, (game_id, uid))
        else:
            cursor.execute("""
            SELECT id, uid, game_id, character_count, five_star_count, average_build_score, snapshot_json, created_at
            FROM account_snapshots WHERE game_id = ? ORDER BY created_at ASC
            """, (game_id,))
        rows = cursor.fetchall()
        
        result = []
        prev_chars_map = {}
        prev_total_chars = 0
        prev_five_stars = 0
        prev_avg_score = 0.0

        for idx, r in enumerate(rows):
            snap = dict(r)
            details = {}
            if snap.get("snapshot_json"):
                try:
                    details = json.loads(snap["snapshot_json"])
                except Exception:
                    details = {}
            
            snap["details"] = details
            current_chars = details.get("all_characters") or details.get("top_built_characters") or []
            
            char_diffs = []
            if idx > 0:
                snap["delta_chars"] = snap["character_count"] - prev_total_chars
                snap["delta_5star"] = snap["five_star_count"] - prev_five_stars
                snap["delta_avg_score"] = round(snap["average_build_score"] - prev_avg_score, 1)

                for c in current_chars:
                    norm = c.get("norm") or c.get("name", "").lower()
                    prev_c = prev_chars_map.get(norm)

                    if not prev_c:
                        char_diffs.append({
                            "name": c.get("name"),
                            "icon": c.get("icon"),
                            "is_new": True,
                            "level_curr": c.get("level"),
                            "rank_curr": c.get("rank_str"),
                            "score_curr": c.get("score"),
                            "grade_curr": c.get("grade"),
                            "weapon_curr": c.get("weapon_name")
                        })
                    else:
                        lvl_diff = c.get("level", 0) - prev_c.get("level", 0)
                        score_diff = round(c.get("score", 0.0) - prev_c.get("score", 0.0), 1)
                        rank_changed = c.get("rank_str") != prev_c.get("rank_str")
                        weapon_changed = c.get("weapon_name") != prev_c.get("weapon_name")

                        if lvl_diff != 0 or score_diff != 0.0 or rank_changed or weapon_changed:
                            char_diffs.append({
                                "name": c.get("name"),
                                "icon": c.get("icon"),
                                "is_new": False,
                                "level_prev": prev_c.get("level"),
                                "level_curr": c.get("level"),
                                "level_diff": lvl_diff,
                                "rank_prev": prev_c.get("rank_str"),
                                "rank_curr": c.get("rank_str"),
                                "score_prev": prev_c.get("score"),
                                "score_curr": c.get("score"),
                                "score_diff": score_diff,
                                "grade_curr": c.get("grade"),
                                "weapon_curr": c.get("weapon_name")
                            })
            else:
                snap["delta_chars"] = 0
                snap["delta_5star"] = 0
                snap["delta_avg_score"] = 0.0

            snap["char_diffs"] = char_diffs

            prev_chars_map = { (c.get("norm") or c.get("name", "").lower()): c for c in current_chars }
            prev_total_chars = snap["character_count"]
            prev_five_stars = snap["five_star_count"]
            prev_avg_score = snap["average_build_score"]

            result.append(snap)

        return result

# ==========================================================================
# FUNÇÕES DE PERSISTÊNCIA E LEITURA DE DADOS
# ==========================================================================

def save_game_account(uid: str, game_id: str, nickname: str, level: int, active_days: Optional[int] = None) -> None:
    """Salva ou atualiza os dados do perfil de uma conta de jogo."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Se active_days for 0 ou None, preserva o valor atual salvo se houver
        if not active_days:
            cursor.execute("SELECT active_days FROM game_accounts WHERE uid = ?", (uid,))
            row = cursor.fetchone()
            if row and row["active_days"]:
                active_days = row["active_days"]
                
        cursor.execute("""
        INSERT OR REPLACE INTO game_accounts (uid, game_id, nickname, level, active_days, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (uid, game_id, nickname, level, active_days or 0, datetime.now().isoformat()))

def save_character(
    uid: str, game_id: str, name: str, level: int, rarity: int, rank_str: str, 
    element: str, icon: str, weapon_name: str, weapon_level: int, 
    weapon_rank: int, weapon_icon: str, raw_md: str, char_id: Optional[str] = None, 
    gacha_art: Optional[str] = None, skills_json: Optional[str] = None,
    stats_json: Optional[str] = None
) -> None:
    """Salva ou atualiza as informações de um personagem no SQLite."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO characters (
            uid, game_id, name, level, rarity, rank_str, element, icon, gacha_art,
            weapon_name, weapon_level, weapon_rank, weapon_icon, raw_md, char_id, skills_json, stats_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (uid, game_id, name, level, rarity, rank_str, element, icon, gacha_art,
              weapon_name, weapon_level, weapon_rank, weapon_icon, raw_md, char_id, skills_json, stats_json))

def clear_character_relics(uid: str, character_name: str) -> None:
    """Remove todas as relíquias/artefatos cadastrados de um personagem para atualização."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        DELETE FROM character_relics WHERE uid = ? AND character_name = ?
        """, (uid, character_name))

def save_relic(uid: str, character_name: str, name: str, slot: str, main_stat: str, sub_stats: str, icon: str) -> None:
    """Salva uma nova relíquia/artefato/disco vinculado a um personagem."""
    with get_connection() as conn:
        cursor = conn.cursor()
        clean_name = clean_relic_name(name) if name else name
        cursor.execute("""
        INSERT INTO character_relics (uid, character_name, name, slot, main_stat, sub_stats, icon)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (uid, character_name, clean_name, slot, main_stat, sub_stats, icon))

def get_roster_data(game_id: str) -> List[Dict[str, Any]]:
    """Obtém o roster completo de personagens e suas relíquias vinculadas para um jogo."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM characters WHERE game_id = ? ORDER BY rarity DESC, level DESC
        """, (game_id,))
        rows = cursor.fetchall()
        
        roster = []
        for r in rows:
            r_keys = r.keys()
            cursor.execute("""
            SELECT name, slot, main_stat as main, sub_stats as sub, icon FROM character_relics 
            WHERE uid = ? AND character_name = ?
            """, (r["uid"], r["name"]))
            relics_rows = cursor.fetchall()
            relics_list = []
            for rel in relics_rows:
                r_dict = dict(rel)
                if r_dict.get("name"):
                    r_dict["name"] = clean_relic_name(r_dict["name"])
                relics_list.append(r_dict)
            
            skills_list = []
            if "skills_json" in r_keys and r["skills_json"]:
                try:
                    skills_list = json.loads(r["skills_json"])
                except Exception:
                    skills_list = []
            
            stats_dict = {}
            if "stats_json" in r_keys and r["stats_json"]:
                try:
                    stats_dict = json.loads(r["stats_json"])
                except Exception:
                    stats_dict = {}
            if not stats_dict and r["raw_md"]:
                stats_dict = parse_stats_from_raw_md(r["raw_md"])
            
            char_dict = {
                "id": r["char_id"] if "char_id" in r_keys and r["char_id"] else "",
                "uid": r["uid"],
                "name": r["name"],
                "level": r["level"],
                "rarity": r["rarity"],
                "rank_str": r["rank_str"],
                "element": r["element"],
                "icon": r["icon"],
                "gacha_art": r["gacha_art"] if "gacha_art" in r_keys else None,
                "weapon": {
                    "name": r["weapon_name"],
                    "level": r["weapon_level"],
                    "rank": r["weapon_rank"],
                    "icon": r["weapon_icon"]
                } if r["weapon_name"] else None,
                "relics": relics_list,
                "skills": skills_list,
                "stats": stats_dict
            }
            roster.append(char_dict)
            
        return roster

def get_character_build_md(game_id: str, char_name: str) -> str:
    """Busca o detalhe bruto em markdown de um personagem no banco de dados."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT raw_md FROM characters WHERE game_id = ? AND name = ? COLLATE NOCASE
        """, (game_id, char_name))
        row = cursor.fetchone()
        return row["raw_md"] if row else ""

def save_daily_notes(uid: str, game_id: str, nickname: str, current_energy: int, max_energy: int, recovery_time: str, extra_info: dict) -> None:
    """Salva no cache local o status de energia/resina/bateria do jogador."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO daily_notes_cache (uid, game_id, nickname, current_energy, max_energy, recovery_time, extra_info, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (uid, game_id, nickname, current_energy, max_energy, recovery_time, json.dumps(extra_info, ensure_ascii=False), datetime.now().isoformat()))

def get_cached_daily_notes() -> Dict[str, Dict[str, Any]]:
    """Retorna as notas diárias mais recentes para cada jogo registrado."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, COALESCE(a.level, 0) as account_level
            FROM daily_notes_cache d
            LEFT JOIN game_accounts a ON d.uid = a.uid AND d.game_id = a.game_id
        """)
        rows = cursor.fetchall()
        
        notes = {}
        for r in rows:
            game_id = r["game_id"]
            level = r["account_level"]
            
            # Caso haja múltiplas contas registradas para o mesmo jogo, seleciona a de maior nível
            if game_id not in notes or level > notes[game_id].get("account_level", 0):
                notes[game_id] = {
                    "uid": r["uid"],
                    "nickname": r["nickname"],
                    "current_energy": r["current_energy"],
                    "max_energy": r["max_energy"],
                    "recovery_time": r["recovery_time"],
                    "extra_info": json.loads(r["extra_info"]) if r["extra_info"] else {},
                    "updated_at": r["updated_at"],
                    "account_level": level
                }
        return notes

def save_checkin_log(game_id: str, uid: str, status: str, message: str) -> None:
    """Registra uma execução de check-in diário no histórico do SQLite."""
    with get_connection() as conn:
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO daily_checkin_logs (date, game_id, uid, status, message, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (today, game_id, uid, status, message, timestamp))

def get_today_checkin_logs() -> List[Dict[str, Any]]:
    """Retorna os logs de check-in diário efetuados na data atual."""
    with get_connection() as conn:
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
        SELECT game_id, uid, status, message, timestamp FROM daily_checkin_logs 
        WHERE date = ? ORDER BY timestamp DESC
        """, (today,))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def get_overview_data() -> Dict[str, Dict[str, Any]]:
    """Retorna estatísticas resumidas das contas ativas por jogo."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM game_accounts")
        accounts_rows = cursor.fetchall()
        
        overview = {}
        for r in accounts_rows:
            game_id = r["game_id"]
            cursor.execute("""
            SELECT COUNT(*), SUM(CASE WHEN rarity = 5 THEN 1 ELSE 0 END) 
            FROM characters WHERE game_id = ? AND uid = ?
            """, (game_id, r["uid"]))
            stats_row = cursor.fetchone()
            count_all = stats_row[0] if stats_row else 0
            count_five = stats_row[1] if stats_row else 0
            
            current_lvl = int(r["level"]) if r["level"] is not None else 0
            if game_id not in overview or current_lvl > int(overview[game_id]["level"]):
                overview[game_id] = {
                    "active": True,
                    "uid": r["uid"],
                    "level": str(r["level"]),
                    "char_count": count_all,
                    "five_stars": count_five or 0
                }
                
        return overview

def get_all_saved_accounts() -> List[Dict[str, Any]]:
    """Retorna uma lista de todas as contas salvas no banco de dados."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT uid, game_id, nickname, level, active_days, updated_at FROM game_accounts ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]

def reset_database() -> None:
    """Remove todas as tabelas e recria a estrutura limpa do banco de dados SQLite."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS character_relics")
        cursor.execute("DROP TABLE IF EXISTS characters")
        cursor.execute("DROP TABLE IF EXISTS game_accounts")
        cursor.execute("DROP TABLE IF EXISTS daily_notes_cache")
        cursor.execute("DROP TABLE IF EXISTS daily_checkin_logs")
    init_db()


