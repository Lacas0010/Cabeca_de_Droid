import os
import threading
import time
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Core modules
from core.config import get_resource_path, get_cookies, get_config, parse_cookie_string
from core.security import (
    create_session,
    is_valid_session,
    active_sessions,
    security_guard_middleware,
    add_no_cache_header,
)

# Services and logic
import database
import security_vault
from notifications import notifier
from groq_rag import GroqRAG
from static_data_manager import static_data_manager
from services.media_service import get_raw_url, download_element_icons, download_hsr_eidolon_shards, ELEMENT_ICONS_MAP
from services.translation_service import traduzir_item
from services.sync_service import (
    sync_status,
    log_game,
    bundle_guides,
    _bg_sync_thread,
    start_auto_sync_scheduler,
)
from services.checkin_service import (
    perform_auto_checkin,
    fetch_realtime_notes,
    start_checkin_scheduler,
    start_energy_watchdog_scheduler,
)
from services.promo_codes_service import (
    perform_auto_promo_code_redeem,
    redeem_promo_codes_for_game,
    start_auto_code_redeemer,
)
from services.roster_service import (
    parse_roster_md_fallback,
    get_roster,
    get_character_build_detail,
    parse_character_build_data,
    parse_meta_target,
    get_overview,
    get_account_audit,
)
from services.endgame_service import get_endgame
from services.gacha_service import (
    KNOWN_4STAR_NAMES,
    is_4star_char,
    make_prydwen_slug,
    make_fallback_urls,
    get_gacha_characters,
)
from services.roast_service import generate_account_roast_stream

# Schemas for backward compatibility
from schemas import (
    SyncRequest,
    ConfigSaveRequest,
    NotificationTestRequest,
    ChatMessage,
    ChatRequest,
    TeamAnalyzeRequest,
    MaterialsCalculateRequest,
    StaticDataSyncRequest,
    FarmOrderToggleRequest,
    FarmOrderSendNotificationRequest,
    GachaRequest,
    GachaForecastRequest,
    GachaGoalSaveRequest,
    StrategyAskAIRequest,
    RedeemCodeRequest,
    BreakpointRequest,
    ManualCookieRequest,
    PinSetRequest,
    PinVerifyRequest,
    PinDisableRequest,
    LanToggleRequest,
)

# Routers
from routers import all_routers
import meta_comparator

# Proxies retrocompatíveis para funções e dicionários legados
HOYOLAB_ID_TO_CANONICAL = meta_comparator.get_hoyolab_mappings()
CHAR_GUIDE_ALIASES = meta_comparator.get_character_aliases()
CHARACTER_SPECIFIC_BENCHMARKS = meta_comparator.get_character_benchmarks()
STAT_EN_TO_PT = meta_comparator.get_stat_mappings()

normalize_slug_text = meta_comparator.normalize_slug_text
resolve_character_canonical_slug = meta_comparator.resolve_character_canonical_slug
find_best_guide_file = meta_comparator.find_best_guide_file
clean_meta_item_name = meta_comparator.clean_meta_item_name
get_section_lines_from_md = meta_comparator.get_section_lines_from_md
derive_dynamic_benchmarks = meta_comparator.derive_dynamic_benchmarks

# ==============================================================================
# FASTAPI APPLICATION ORCHESTRATION & LIFECYCLE
# ==============================================================================

app = FastAPI(
    title="Cabeça de Droid API",
    version="4.0",
    description="Assistente local completo para jogos da HoYoverse (Genshin Impact, Honkai: Star Rail e Zenless Zone Zero)"
)

# Inicialização de banco de dados e migração transparente de cofre seguro
@app.on_event("startup")
def startup_event():
    database.init_db()
    security_vault.load_secure_cookies()

# Agendadores em segundo plano
@app.on_event("startup")
def startup_schedulers():
    start_checkin_scheduler()
    start_auto_sync_scheduler()
    start_energy_watchdog_scheduler()
    start_auto_code_redeemer()

@app.on_event("startup")
def startup_static_data_sync_scheduler():
    def static_sync_loop():
        time.sleep(5)
        try:
            results = static_data_manager.sync_upstream_data()
            for gid, info in results.items():
                database.save_static_data_manifest(
                    game_id=gid,
                    version="1.0",
                    item_count=info.get("character_count", 0),
                    status=info.get("status", "success"),
                    source=info.get("source", "seed")
                )
            print("[STATIC-DATA] Manifestos de dados estáticos e datamines inicializados com sucesso.")
        except Exception as s_err:
            print(f"[STATIC-DATA] Erro na inicialização dos dados estáticos: {s_err}")

        while True:
            time.sleep(86400)
            try:
                results = static_data_manager.sync_upstream_data()
                for gid, info in results.items():
                    database.save_static_data_manifest(
                        game_id=gid,
                        version="1.0",
                        item_count=info.get("character_count", 0),
                        status=info.get("status", "success"),
                        source=info.get("source", "seed")
                    )
            except Exception as loop_err:
                print(f"[STATIC-DATA] Erro no loop diário de sincronização estática: {loop_err}")

    threading.Thread(target=static_sync_loop, daemon=True).start()

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(add_no_cache_header)
app.middleware("http")(security_guard_middleware)

# Montagem de todos os módulos de rotas (APIRouters)
for router in all_routers:
    app.include_router(router)

# Download proativo de ícones dos elementos e fragmentos de Eidolon
download_element_icons()
threading.Thread(target=download_hsr_eidolon_shards, daemon=True).start()

# Montagem de arquivos estáticos da interface Web Glassmorphism
static_dir = get_resource_path("static")
assets_dir = get_resource_path("assets")

os.makedirs(static_dir, exist_ok=True)
os.makedirs(assets_dir, exist_ok=True)

app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    import webbrowser

    def open_browser():
        time.sleep(3.5)
        print("[INFO] Abrindo Cabeça de Droid no navegador...")
        webbrowser.open("http://127.0.0.1:8000")
        
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
