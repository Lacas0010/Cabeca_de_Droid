import sqlite3
import os
import json
from datetime import datetime
from extractor import clean_relic_name

DATABASE_NAME = "hoyo_app.db"

def get_connection():
    """Retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa as tabelas do banco de dados se não existirem."""
    conn = get_connection()
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
        weapon_name TEXT,
        weapon_level INTEGER,
        weapon_rank INTEGER,
        weapon_icon TEXT,
        raw_md TEXT,
        PRIMARY KEY (uid, name)
    )
    """)
    
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
        extra_info TEXT, -- JSON com dados extras como expedições, diárias
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
        status TEXT, -- SUCCESS, ALREADY_CLAIMED, ERROR
        message TEXT,
        timestamp TEXT
    )
    """)
    
    conn.commit()
    conn.close()
    print("[INFO] Banco de dados SQLite inicializado com sucesso.")

# Inicializa o banco ao carregar o módulo
init_db()

# ==========================================================================
# FUNÇÕES DE PERSISTÊNCIA E LEITURA
# ==========================================================================

def save_game_account(uid: str, game_id: str, nickname: str, level: int, active_days: int = None):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Se active_days for 0 ou None, preserva o valor atual do banco se houver
    if active_days is None or active_days == 0:
        cursor.execute("SELECT active_days FROM game_accounts WHERE uid = ?", (uid,))
        row = cursor.fetchone()
        if row:
            active_days = row["active_days"]
            
    cursor.execute("""
    INSERT OR REPLACE INTO game_accounts (uid, game_id, nickname, level, active_days, updated_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (uid, game_id, nickname, level, active_days or 0, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def save_character(uid: str, game_id: str, name: str, level: int, rarity: int, rank_str: str, 
                   element: str, icon: str, weapon_name: str, weapon_level: int, 
                   weapon_rank: int, weapon_icon: str, raw_md: str, char_id: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO characters (
        uid, game_id, name, level, rarity, rank_str, element, icon, 
        weapon_name, weapon_level, weapon_rank, weapon_icon, raw_md
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (uid, game_id, name, level, rarity, rank_str, element, icon,
          weapon_name, weapon_level, weapon_rank, weapon_icon, raw_md))
    conn.commit()
    conn.close()

def clear_character_relics(uid: str, character_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    DELETE FROM character_relics WHERE uid = ? AND character_name = ?
    """, (uid, character_name))
    conn.commit()
    conn.close()

def save_relic(uid: str, character_name: str, name: str, slot: str, main_stat: str, sub_stats: str, icon: str):
    conn = get_connection()
    cursor = conn.cursor()
    clean_name = clean_relic_name(name) if name else name
    cursor.execute("""
    INSERT INTO character_relics (uid, character_name, name, slot, main_stat, sub_stats, icon)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (uid, character_name, clean_name, slot, main_stat, sub_stats, icon))
    conn.commit()
    conn.close()

def get_roster_data(game_id: str) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM characters WHERE game_id = ? ORDER BY rarity DESC, level DESC
    """, (game_id,))
    rows = cursor.fetchall()
    
    roster = []
    for r in rows:
        # Busca as relíquias vinculadas a este personagem
        cursor.execute("""
        SELECT name, slot, main_stat as main, sub_stats as sub, icon FROM character_relics 
        WHERE uid = ? AND character_name = ?
        """, (r["uid"], r["name"]))
        relics_rows = cursor.fetchall()
        relics_list = []
        for rel in relics_rows:
            r_dict = dict(rel)
            if "name" in r_dict:
                r_dict["name"] = clean_relic_name(r_dict["name"])
            relics_list.append(r_dict)
        
        char_dict = {
            "uid": r["uid"],
            "name": r["name"],
            "level": r["level"],
            "rarity": r["rarity"],
            "rank_str": r["rank_str"],
            "element": r["element"],
            "icon": r["icon"],
            "weapon": {
                "name": r["weapon_name"],
                "level": r["weapon_level"],
                "rank": r["weapon_rank"],
                "icon": r["weapon_icon"]
            } if r["weapon_name"] else None,
            "relics": relics_list
        }
        roster.append(char_dict)
        
    conn.close()
    return roster

def get_character_build_md(game_id: str, char_name: str) -> str:
    """Busca o detalhe bruto em markdown de um personagem no banco."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT raw_md FROM characters WHERE game_id = ? AND name = ? COLLATE NOCASE
    """, (game_id, char_name))
    row = cursor.fetchone()
    conn.close()
    return row["raw_md"] if row else ""

def save_daily_notes(uid: str, game_id: str, nickname: str, current_energy: int, max_energy: int, recovery_time: str, extra_info: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO daily_notes_cache (uid, game_id, nickname, current_energy, max_energy, recovery_time, extra_info, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (uid, game_id, nickname, current_energy, max_energy, recovery_time, json.dumps(extra_info, ensure_ascii=False), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_cached_daily_notes() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    # Junta com game_accounts para obter o level de cada conta para resolver multi-contas
    cursor.execute("""
        SELECT d.*, COALESCE(a.level, 0) as account_level
        FROM daily_notes_cache d
        LEFT JOIN game_accounts a ON d.uid = a.uid AND d.game_id = a.game_id
    """)
    rows = cursor.fetchall()
    conn.close()
    
    notes = {}
    for r in rows:
        game_id = r["game_id"]
        level = r["account_level"]
        
        # Se houver mais de uma conta para o mesmo jogo, mantém a de maior nível
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

def save_checkin_log(game_id: str, uid: str, status: str, message: str):
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO daily_checkin_logs (date, game_id, uid, status, message, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (today, game_id, uid, status, message, timestamp))
    conn.commit()
    conn.close()

def get_today_checkin_logs() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
    SELECT game_id, uid, status, message, timestamp FROM daily_checkin_logs 
    WHERE date = ? ORDER BY timestamp DESC
    """, (today,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_overview_data() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM game_accounts")
    accounts_rows = cursor.fetchall()
    
    overview = {}
    for r in accounts_rows:
        game_id = r["game_id"]
        # Conta personagens e de 5 estrelas filtrando pelo UID específico da conta
        cursor.execute("SELECT COUNT(*), SUM(CASE WHEN rarity = 5 THEN 1 ELSE 0 END) FROM characters WHERE game_id = ? AND uid = ?", (game_id, r["uid"]))
        stats_row = cursor.fetchone()
        count_all = stats_row[0] if stats_row else 0
        count_five = stats_row[1] if stats_row else 0
        
        # Só insere ou substitui se for a primeira conta deste jogo ou se possuir nível maior
        current_lvl = int(r["level"]) if r["level"] is not None else 0
        if game_id not in overview or current_lvl > int(overview[game_id]["level"]):
            overview[game_id] = {
                "active": True,
                "uid": r["uid"],
                "level": str(r["level"]),
                "char_count": count_all,
                "five_stars": count_five or 0
            }
            
    conn.close()
    return overview
