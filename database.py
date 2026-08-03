import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from extractor import clean_relic_name

DATABASE_NAME = "hoyo_app.db"

def get_connection() -> sqlite3.Connection:
    """Retorna uma conexão configurada com o banco de dados SQLite."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

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
        
        # Criação de índices para acelerar consultas frequentes do Roster e de Relíquias
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_characters_game_uid ON characters(game_id, uid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relics_uid_char ON character_relics(uid, character_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_checkin_date ON daily_checkin_logs(date)")
        
    print("[INFO] Banco de dados SQLite inicializado com sucesso.")

# Inicializa o banco ao carregar o módulo
init_db()

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
    gacha_art: Optional[str] = None
) -> None:
    """Salva ou atualiza as informações de um personagem no SQLite."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO characters (
            uid, game_id, name, level, rarity, rank_str, element, icon, gacha_art,
            weapon_name, weapon_level, weapon_rank, weapon_icon, raw_md, char_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (uid, game_id, name, level, rarity, rank_str, element, icon, gacha_art,
              weapon_name, weapon_level, weapon_rank, weapon_icon, raw_md, char_id))

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
                "relics": relics_list
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
