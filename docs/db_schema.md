# Esquema Oficial do Banco de Dados SQLite (`hoyo_app.db`)

Este documento serve como a fonte de verdade para a estrutura de tabelas e índices do banco local do **Cabeça de Droid**. Ao criar novas queries ou modificar `database.py`, utilize estritamente os nomes de colunas e tipos definidos abaixo.

---

## Tabelas Principais

### 1. `game_accounts`
Contas de jogadores vinculadas por jogo.
```sql
CREATE TABLE IF NOT EXISTS game_accounts (
    uid TEXT PRIMARY KEY,
    game_id TEXT NOT NULL,
    nickname TEXT,
    level INTEGER,
    active_days INTEGER,
    updated_at TEXT
);
```

### 2. `active_accounts`
Mapeamento de qual UID está atualmente selecionado/ativo por jogo (Multi-UID Switcher).
```sql
CREATE TABLE IF NOT EXISTS active_accounts (
    game_id TEXT PRIMARY KEY,
    active_uid TEXT NOT NULL,
    updated_at TEXT
);
```

### 3. `characters`
Personagens do jogador por conta e jogo, incluindo status, habilidades, armas e artefatos em JSON.
```sql
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
    skills_json TEXT,
    stats_json TEXT,
    ranks_json TEXT,
    PRIMARY KEY (uid, name)
);
```

### 4. `character_relics`
Relíquias, discos e artefatos equipados nos personagens.
```sql
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
);
```

### 5. `daily_notes_cache`
Cache de resina, energia e baterias em tempo real coletadas do HoYoLAB.
```sql
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
);
```

### 6. `daily_checkin_logs`
Histórico de execuções do check-in automático diário.
```sql
CREATE TABLE IF NOT EXISTS daily_checkin_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    game_id TEXT NOT NULL,
    uid TEXT,
    status TEXT,
    message TEXT,
    timestamp TEXT
);
```

### 7. `account_snapshots`
Snapshots periódicos do estado da conta para a timeline de evolução e gráficos de progresso.
```sql
CREATE TABLE IF NOT EXISTS account_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL,
    game_id TEXT NOT NULL,
    character_count INTEGER,
    five_star_count INTEGER,
    average_build_score REAL,
    snapshot_json TEXT,
    created_at TEXT NOT NULL
);
```

### 8. `endgame_records`
Relatórios e registros das modalidades de endgame (MoC, Pure Fiction, Apocalyptic Shadow, Abismo Espiral, Teatro Imaginário, Shiyu Defense).
```sql
CREATE TABLE IF NOT EXISTS endgame_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL,
    game_id TEXT NOT NULL,
    modes_json TEXT,
    raw_md TEXT,
    updated_at TEXT NOT NULL,
    UNIQUE(uid, game_id)
);
```

### 9. `security_settings`
Configurações de proteção por PIN local e liberação de acesso em rede local (LAN).
```sql
CREATE TABLE IF NOT EXISTS security_settings (
    id INTEGER PRIMARY KEY,
    pin_enabled INTEGER DEFAULT 0,
    pin_hash TEXT,
    pin_salt TEXT,
    allow_lan_access INTEGER DEFAULT 0,
    updated_at TEXT
);
```

### 10. `promo_code_history`
Registro de códigos promocionais já resgatados por jogo e conta para evitar requisições repetidas.
```sql
CREATE TABLE IF NOT EXISTS promo_code_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    uid TEXT NOT NULL,
    code TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT,
    redeemed_at TEXT NOT NULL,
    UNIQUE(game_id, uid, code)
);
```

### 11. `static_data_manifests`
Metadados sobre os arquivos JSON de dados estáticos e fontes de sincronização.
```sql
CREATE TABLE IF NOT EXISTS static_data_manifests (
    game_id TEXT PRIMARY KEY,
    version TEXT,
    item_count INTEGER,
    last_synced TEXT NOT NULL,
    status TEXT NOT NULL,
    source TEXT
);
```

### 12. `daily_farm_tasks_completed`
Controle diário de tarefas concluídas na ordem de serviço de farm diário.
```sql
CREATE TABLE IF NOT EXISTS daily_farm_tasks_completed (
    date TEXT NOT NULL,
    game_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    PRIMARY KEY (date, game_id, task_id)
);
```

### 13. `gacha_forecast_goals`
Metas de tiros, pity e taxa de sucesso planejados no simulador de forecast.
```sql
CREATE TABLE IF NOT EXISTS gacha_forecast_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    character_name TEXT NOT NULL,
    target_rank_str TEXT NOT NULL,
    current_pulls INTEGER NOT NULL,
    current_pity INTEGER NOT NULL,
    is_guaranteed INTEGER NOT NULL,
    target_days INTEGER NOT NULL,
    has_daily_pass INTEGER NOT NULL,
    success_rate REAL NOT NULL,
    projected_pulls INTEGER NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL
);
```

### 14. `chat_history`
Histórico de mensagens trocadas com o assistente de IA RAG local.
```sql
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
```

### 15. `gacha_pulls_history`
Histórico oficial importado de tiros / saltos (Warp, Wish, Signal) de banners da HoYoverse.
```sql
CREATE TABLE IF NOT EXISTS gacha_pulls_history (
    id TEXT PRIMARY KEY,
    uid TEXT NOT NULL,
    game_id TEXT NOT NULL,
    gacha_type TEXT NOT NULL,
    banner_category TEXT NOT NULL,
    item_id TEXT,
    item_name TEXT NOT NULL,
    item_type TEXT,
    rarity INTEGER NOT NULL,
    time TEXT NOT NULL,
    pity_count INTEGER,
    created_at TEXT NOT NULL
);
```

---

## Índices de Performance

```sql
CREATE INDEX IF NOT EXISTS idx_characters_game_uid ON characters(game_id, uid);
CREATE INDEX IF NOT EXISTS idx_relics_uid_char ON character_relics(uid, character_name);
CREATE INDEX IF NOT EXISTS idx_checkin_date ON daily_checkin_logs(date);
CREATE INDEX IF NOT EXISTS idx_snapshots_uid ON account_snapshots(game_id, uid);
CREATE INDEX IF NOT EXISTS idx_endgame_game_uid ON endgame_records(game_id, uid);
CREATE INDEX IF NOT EXISTS idx_promo_history_lookup ON promo_code_history(game_id, uid, code);
CREATE INDEX IF NOT EXISTS idx_static_data_game ON static_data_manifests(game_id);
CREATE INDEX IF NOT EXISTS idx_farm_tasks_lookup ON daily_farm_tasks_completed(date, game_id);
CREATE INDEX IF NOT EXISTS idx_gacha_goals_game ON gacha_forecast_goals(game_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_game ON chat_history(game_id);
CREATE INDEX IF NOT EXISTS idx_gacha_pulls_lookup ON gacha_pulls_history(uid, game_id, banner_category, time);
```
