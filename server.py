import os
import re
import json
import asyncio
import threading
import traceback
import datetime
import time
import genshin
import urllib.parse

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# Importações dos módulos do projeto
from auth import capturar_cookies_hoyolab
from extractor import MultiGameExtractor, clean_relic_name, sanitize_stat_name
from scraper_prydwen import PrydwenScraper
from scraper_zzz import PrydwenZZZScraper
from scraper_meta import PrydwenMetaScraper
from scraper_kqm import KQMScraper
from groq_rag import GroqRAG
import database
from build_calculator import score_relic, calculate_ascension, get_meta_data, extract_weights_from_guide, normalize_char_name

app = FastAPI(title="Cabeça de Droid API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_header(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


def get_raw_url(url_str: str) -> str:
    """Extrai a URL original subjacente caso a string já esteja envelopada pelo proxy interno."""
    if not url_str:
        return ""
    url_s = str(url_str)
    while "/api/proxy_image?url=" in url_s:
        raw = url_s.split("/api/proxy_image?url=")[-1]
        url_s = urllib.parse.unquote(raw)
    return url_s

# Estado global para progresso da sincronização
sync_status = {
    "zzz": {"running": False, "progress": 0.0, "message": "Aguardando...", "logs": []},
    "genshin": {"running": False, "progress": 0.0, "message": "Aguardando...", "logs": []},
    "hsr": {"running": False, "progress": 0.0, "message": "Aguardando...", "logs": []},
}

def log_game(game_id: str, msg: str, level: str = "INFO", progresso: float = None):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] [{level}] {msg}"
    print(formatted_msg)
    
    status = sync_status[game_id]
    status["logs"].append(formatted_msg)
    status["message"] = f"{level == 'ERROR' and '❌ ' or ''}{msg}"
    if progresso is not None:
        status["progress"] = progresso

def bundle_guides(guides_dir: str, output_file: str, game_name: str):
    """Consolida arquivos Markdown individuais em um único arquivo consolidado."""
    if not os.path.exists(guides_dir):
        return
    
    files = [f for f in os.listdir(guides_dir) if f.endswith(".md")]
    files.sort()
    
    lines = [f"# Biblioteca Consolidada de Guias - {game_name}\n"]
    for file in files:
        filepath = os.path.join(guides_dir, file)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                lines.append(f"## Personagem: {file[:-3]}")
                lines.append(content)
                lines.append("\n---\n")
        except Exception as e:
            print(f"Erro ao ler {file} para consolidação: {e}")
            
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as out_f:
        out_f.write("\n".join(lines))

def get_cookies() -> dict:
    cookie_file = "cookies.json"
    if os.path.exists(cookie_file):
        try:
            with open(cookie_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_config() -> dict:
    config_file = "config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def parse_cookie_string(raw_cookie: str) -> dict:
    cookies = {}
    if not raw_cookie:
        return cookies
    raw_cookie = raw_cookie.strip()
    parts = raw_cookie.split(";")
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies

# Pydantic models para validação das APIs
class SyncRequest(BaseModel):
    run_roster: bool = True
    run_guides: bool = True
    run_meta: bool = True

class ConfigSaveRequest(BaseModel):
    groq_api_key: Optional[str] = None
    cookies_raw: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    text: str

class ChatRequest(BaseModel):
    message: str
    game_id: str
    history: List[ChatMessage] = []

class TeamAnalyzeRequest(BaseModel):
    game_id: str
    characters: List[str]

class MaterialsCalculateRequest(BaseModel):
    game_id: str
    char_name: str
    current_level: int
    target_level: int

# ==========================================
# LÓGICA DA THREAD DE SINCRONIZAÇÃO
# ==========================================
def _bg_sync_thread(game_id: str, run_roster: bool, run_guides: bool, run_meta: bool):
    game_id = game_id.lower()
    log_game(game_id, f"Iniciando sincronização de {game_id.upper()}...", "INFO", progresso=0.01)
    sync_status[game_id]["running"] = True
    
    try:
        # 1. EXTRAÇÃO DE ROSTER
        if run_roster:
            cookies = get_cookies()
            if not cookies:
                log_game(game_id, "Cookies da HoYoLAB ausentes em cookies.json. Configure-os na aba Configurações.", "ERROR", progresso=0.0)
                sync_status[game_id]["running"] = False
                return
                
            log_game(game_id, f"Conectando à API HoYoLAB para extrair Roster...", "INFO", progresso=0.05)
            try:
                extractor = MultiGameExtractor(cookies)
                # Como rodamos em thread síncrona do FastAPI background, criamos um event loop próprio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                filename = loop.run_until_complete(extractor.extrair_jogo(game_id))
                loop.close()
                log_game(game_id, f"Roster extraído e salvo com sucesso em {filename}!", "SUCCESS", progresso=0.25)
            except Exception as roster_err:
                traceback.print_exc()
                log_game(game_id, f"Falha ao extrair Roster: {roster_err}", "ERROR")

        # 2. EXTRAÇÃO DE GUIAS
        if run_guides:
            log_game(game_id, f"Iniciando busca de guias no meta-hub...", "INFO", progresso=0.28)
            if game_id == "hsr":
                try:
                    log_game(game_id, "Buscando personagens HSR...", "INFO", progresso=0.30)
                    scraper = PrydwenScraper()
                    chars = scraper.get_character_list()
                    log_game(game_id, f"Encontrados {len(chars)} personagens. Baixando guias...", "INFO", progresso=0.32)
                    total_chars = len(chars)
                    for idx, c in enumerate(chars, 1):
                        p_val = 0.32 + 0.50 * (idx / total_chars if total_chars > 0 else 1.0)
                        log_game(game_id, f"({idx}/{total_chars}) Coletando guia de {c['name']}...", "INFO", progresso=p_val)
                        try:
                            data = scraper.scrape_character_guide(c["name"], c["url"])
                            scraper.save_to_markdown(c["name"], data)
                        except Exception as child_err:
                            log_game(game_id, f"Aviso no guia de {c['name']}: {child_err}", "WARN", progresso=p_val)
                    log_game(game_id, "Guias de HSR baixados com sucesso!", "SUCCESS", progresso=0.82)
                    log_game(game_id, "Consolidando biblioteca de guias de HSR...", "INFO", progresso=0.84)
                    bundle_guides("hsr/guias", "hsr/todos_os_guias_hsr.md", "Honkai: Star Rail")
                except Exception as scraper_err:
                    traceback.print_exc()
                    log_game(game_id, f"Erro ao obter guias HSR: {scraper_err}", "ERROR")
                    
            elif game_id == "zzz":
                try:
                    log_game(game_id, "Buscando agentes ZZZ...", "INFO", progresso=0.30)
                    scraper = PrydwenZZZScraper()
                    agents = scraper.get_agent_list()
                    log_game(game_id, f"Encontrados {len(agents)} agentes. Baixando guias...", "INFO", progresso=0.32)
                    total_agents = len(agents)
                    for idx, a in enumerate(agents, 1):
                        p_val = 0.32 + 0.50 * (idx / total_agents if total_agents > 0 else 1.0)
                        log_game(game_id, f"({idx}/{total_agents}) Coletando guia de {a['name']}...", "INFO", progresso=p_val)
                        try:
                            data = scraper.scrape_agent_guide(a["name"], a["url"])
                            scraper.save_to_markdown(a["name"], data)
                        except Exception as child_err:
                            log_game(game_id, f"Aviso no guia de {a['name']}: {child_err}", "WARN", progresso=p_val)
                    log_game(game_id, "Guias de ZZZ baixados com sucesso!", "SUCCESS", progresso=0.82)
                    log_game(game_id, "Consolidando biblioteca de guias de ZZZ...", "INFO", progresso=0.84)
                    bundle_guides("zzz/guias", "zzz/todos_os_guias_zzz.md", "Zenless Zone Zero")
                except Exception as scraper_err:
                    traceback.print_exc()
                    log_game(game_id, f"Erro ao obter guias ZZZ: {scraper_err}", "ERROR")
                    
            elif game_id == "genshin":
                try:
                    extracted_characters = []
                    roster_path = "genshin/roster_genshin.md"
                    if os.path.exists(roster_path):
                        try:
                            with open(roster_path, "r", encoding="utf-8") as f:
                                for line in f:
                                    if line.startswith("|") and not line.startswith("| Personagem") and not line.startswith("| :---"):
                                        parts = [p.strip() for p in line.split("|")]
                                        if len(parts) > 2:
                                            cname = parts[1].replace("**", "").strip()
                                            if cname and cname not in extracted_characters:
                                                extracted_characters.append(cname)
                        except Exception as e:
                            log_game(game_id, f"Erro ao carregar roster de Genshin: {e}", "WARN")
                    
                    if not extracted_characters:
                        log_game(game_id, "Roster de Genshin não encontrado. Usando lista padrão de personagens populares.", "INFO", progresso=0.30)
                        extracted_characters = ["Keqing", "Hu Tao", "Raiden Shogun", "Furina", "Nahida", "Bennett", "Zhongli", "Kaedehara Kazuha", "Yelan", "Xingqiu"]
                        
                    log_game(game_id, f"Buscando guias KQM para {len(extracted_characters)} personagens de Genshin...", "INFO", progresso=0.32)
                    from scraper_kqm import KQMScraper
                    kqm = KQMScraper(output_dir="genshin/guias")
                    
                    # Como scrape_all_guides utiliza callbacks de log, criamos um callback local adequado
                    def kqm_callback(msg, level="INFO", progresso=None):
                        p_val = 0.32 + 0.50 * (progresso if progresso is not None else 0.5)
                        log_game(game_id, msg, level, progresso=p_val)
                        
                    kqm.scrape_all_guides(character_list=extracted_characters, logger_cb=kqm_callback)
                    log_game(game_id, "Guias do KQM baixados com sucesso!", "SUCCESS", progresso=0.82)
                    log_game(game_id, "Consolidando biblioteca de guias de Genshin...", "INFO", progresso=0.84)
                    bundle_guides("genshin/guias", "genshin/todos_os_guias_genshin.md", "Genshin Impact")
                except Exception as scraper_err:
                    traceback.print_exc()
                    log_game(game_id, f"Erro ao obter guias Genshin: {scraper_err}", "ERROR")

        # 3. EXTRAÇÃO DE META E ENDGAME
        if run_meta:
            log_game(game_id, f"Iniciando sincronização do meta...", "INFO", progresso=0.86)
            if game_id == "hsr":
                try:
                    log_game(game_id, "Coletando Tier Lists HSR do Prydwen...", "INFO", progresso=0.88)
                    scraper_m = PrydwenMetaScraper()
                    data = scraper_m.scrape_tier_list()
                    filepath_tier = scraper_m.save_meta_markdown(data, "hsr/meta_e_tierlists_atual.md")
                    
                    log_game(game_id, "Coletando estatísticas de endgame HSR...", "INFO", progresso=0.92)
                    reports = scraper_m.scrape_endgame_reports()
                    filepath_endgame = scraper_m.save_endgame_markdown(reports, "hsr/meta_endgame_report.md")
                    
                    # Consolidado
                    consolidated_path = "hsr/meta_endgame_hsr.md"
                    with open(consolidated_path, "w", encoding="utf-8") as out_f:
                        if os.path.exists(filepath_tier):
                            with open(filepath_tier, "r", encoding="utf-8") as f1:
                                out_f.write(f1.read())
                                out_f.write("\n\n---\n\n")
                        if os.path.exists(filepath_endgame):
                            with open(filepath_endgame, "r", encoding="utf-8") as f2:
                                out_f.write(f2.read())
                    log_game(game_id, "Meta de HSR consolidado com sucesso!", "SUCCESS", progresso=0.98)
                except Exception as meta_err:
                    traceback.print_exc()
                    log_game(game_id, f"Falha ao obter meta HSR: {meta_err}", "ERROR")
            elif game_id == "zzz":
                try:
                    log_game(game_id, "Coletando meta, tier list e relatórios de endgame do ZZZ...", "INFO", progresso=0.90)
                    scraper = PrydwenZZZScraper()
                    filepath = scraper.save_meta_to_markdown()
                    log_game(game_id, "Meta de ZZZ salvo com sucesso!", "SUCCESS", progresso=0.98)
                except Exception as meta_err:
                    traceback.print_exc()
                    log_game(game_id, f"Falha ao obter meta ZZZ: {meta_err}", "ERROR")
            elif game_id == "genshin":
                try:
                    log_game(game_id, "Coletando meta e builds de Genshin do Game8...", "INFO", progresso=0.90)
                    from scraper_game8 import run_genshin_game8_builds
                    
                    def genshin_meta_callback(msg, level="INFO", prog=None):
                        p_val = 0.90 + 0.08 * (prog if prog is not None else 0.5)
                        log_game(game_id, msg, level, progresso=p_val)
                        
                    run_genshin_game8_builds(logger_cb=genshin_meta_callback)
                    log_game(game_id, "Meta e builds de Genshin do Game8 salvos com sucesso!", "SUCCESS", progresso=0.98)
                except Exception as meta_err:
                    traceback.print_exc()
                    log_game(game_id, f"Falha ao obter meta Genshin: {meta_err}", "ERROR")

        # Regenera a base estruturada meta_data_{game_id}.json com os guias recém-baixados
        try:
            from build_calculator import generate_meta_json_from_markdown
            generate_meta_json_from_markdown(game_id)
            log_game(game_id, f"Banco de metadados meta_data_{game_id}.json de {game_id.upper()} reconstruído com sucesso!", "INFO", progresso=0.99)
        except Exception as json_err:
            log_game(game_id, f"Aviso ao atualizar cache JSON de metadados: {json_err}", "WARN")
            
        log_game(game_id, "Sincronização concluída com sucesso!", "SUCCESS", progresso=1.0)
    except Exception as general_err:
        log_game(game_id, f"Erro crítico na sincronização: {general_err}", "ERROR", progresso=0.0)
    finally:
        sync_status[game_id]["running"] = False

# ==========================================
# ROTINAS DE CHECK-IN AUTOMÁTICO
# ==========================================
async def perform_auto_checkin():
    cookies = get_cookies()
    if not cookies:
        print("[CHECKIN] Nenhum cookie configurado para o check-in automático.")
        return []
        
    client = genshin.Client(cookies=cookies, lang="pt-pt")
    
    try:
        accounts = await client.get_game_accounts()
    except Exception as e:
        print(f"[CHECKIN] Erro ao obter contas para check-in: {e}")
        return []
        
    logs = []
    processed = set()
    
    for acc in accounts:
        game_biz = acc.game_biz
        uid = str(acc.uid)
        
        game_type = None
        game_key = None
        if game_biz.startswith("hk4e"):
            game_type = genshin.Game.GENSHIN
            game_key = "genshin"
        elif game_biz.startswith("hkrpg"):
            game_type = genshin.Game.STARRAIL
            game_key = "hsr"
        elif game_biz.startswith("nap"):
            game_type = genshin.Game.ZZZ
            game_key = "zzz"
            
        if not game_type or (game_key, uid) in processed:
            continue
            
        processed.add((game_key, uid))
        client.game = game_type
        
        try:
            reward = await client.claim_daily_reward()
            msg = f"Check-in realizado com sucesso! Recompensa: {reward.name} (x{reward.amount})"
            database.save_checkin_log(game_key, uid, "SUCCESS", msg)
            logs.append({"game_id": game_key, "uid": uid, "status": "SUCCESS", "message": msg})
            print(f"[CHECKIN] {game_key.upper()} ({uid}): {msg}")
        except genshin.AlreadyClaimed:
            msg = "Recompensa diária já foi resgatada hoje."
            database.save_checkin_log(game_key, uid, "ALREADY_CLAIMED", msg)
            logs.append({"game_id": game_key, "uid": uid, "status": "ALREADY_CLAIMED", "message": msg})
            print(f"[CHECKIN] {game_key.upper()} ({uid}): {msg}")
        except Exception as err:
            err_msg = str(err)
            if "1008" in err_msg or "already claimed" in err_msg.lower():
                msg = "Recompensa diária já foi resgatada hoje."
                database.save_checkin_log(game_key, uid, "ALREADY_CLAIMED", msg)
                logs.append({"game_id": game_key, "uid": uid, "status": "ALREADY_CLAIMED", "message": msg})
            else:
                msg = f"Erro no check-in: {err_msg}"
                database.save_checkin_log(game_key, uid, "ERROR", msg)
                logs.append({"game_id": game_key, "uid": uid, "status": "ERROR", "message": msg})
            print(f"[CHECKIN] {game_key.upper()} ({uid}): Erro: {err_msg}")
            
    return logs

@app.on_event("startup")
def startup_checkin_scheduler():
    def checkin_loop():
        # Espera 10 segundos antes da primeira execução
        time.sleep(10)
        while True:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(perform_auto_checkin())
                loop.close()
            except Exception as loop_err:
                print(f"[CHECKIN] Erro no loop de check-in automático: {loop_err}")
            # Aguarda 6 horas
            time.sleep(21600)
            
    threading.Thread(target=checkin_loop, daemon=True).start()

# ==========================================
# ROTAS DA API REST
# ==========================================

@app.get("/api/proxy_image")
async def proxy_image(url: str):
    """Proxy para carregar imagens externas no HTML5 Canvas sem sofrer bloqueio de CORS ou Tainted Canvas."""
    if not url or not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL de imagem inválida.")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://act.hoyoverse.com/"
    }
    
    try:
        import requests
        def fetch():
            return requests.get(url, headers=headers, timeout=12)
            
        resp = await asyncio.to_thread(fetch)
        
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Falha ao obter imagem da origem: {resp.status_code}")
            
        content_type = resp.headers.get("content-type", "image/png")
        return Response(
            content=resp.content,
            media_type=content_type,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Cache-Control": "public, max-age=86400"
            }
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar proxy de imagem: {e}")

def parse_roster_md_fallback(game_id: str) -> List[Dict[str, Any]]:
    md_path = f"{game_id}/roster_{game_id}.md"
    chars = []
    if not os.path.exists(md_path):
        return chars
        
    genshin_elements = {
        "mavuika": "Pyro", "bennett": "Pyro", "xiangling": "Pyro", "hu tao": "Pyro", "gaming": "Pyro",
        "arlecchino": "Pyro", "yoimiya": "Pyro", "diluc": "Pyro", "dehya": "Pyro", "klee": "Pyro",
        "thoma": "Pyro", "yanfei": "Pyro", "xinyan": "Pyro", "chevreuse": "Pyro", "amber": "Pyro",
        "furina": "Hydro", "yelan": "Hydro", "nefer": "Hydro", "sangonomiya kokomi": "Hydro",
        "nilou": "Hydro", "tartaglia": "Hydro", "mona": "Hydro", "xingqiu": "Hydro", "barbara": "Hydro",
        "candace": "Hydro", "aino": "Hydro", "dahlia": "Hydro",
        "skirk": "Cryo", "citlali": "Cryo", "shenhe": "Cryo", "ganyu": "Cryo", "kamisato ayaka": "Cryo",
        "eula": "Cryo", "rosaria": "Cryo", "charlotte": "Cryo", "layla": "Cryo", "diona": "Cryo",
        "chongyun": "Cryo", "mika": "Cryo", "freminet": "Cryo", "aloy": "Cryo", "qiqi": "Cryo",
        "yae miko": "Electro", "shogun raiden": "Electro", "keqing": "Electro", "kuki shinobu": "Electro",
        "clorinde": "Electro", "sethos": "Electro", "ororon": "Electro", "iansan": "Electro", "fischl": "Electro",
        "beidou": "Electro", "razor": "Electro", "kujou sara": "Electro", "dori": "Electro", "lisa": "Electro",
        "zibai": "Geo", "xilonen": "Geo", "navia": "Geo", "zhongli": "Geo", "albedo": "Geo", "chiori": "Geo",
        "arataki itto": "Geo", "ningguang": "Geo", "gorou": "Geo", "yunjin": "Geo", "noelle": "Geo", "kachina": "Geo",
        "lauma": "Dendro", "nahida": "Dendro", "tighnari": "Dendro", "alhaitham": "Dendro", "baizhu": "Dendro",
        "emilie": "Dendro", "kinich": "Dendro", "yaoyao": "Dendro", "kirara": "Dendro", "collei": "Dendro", "kaveh": "Dendro"
    }

    zzz_elements = {
        "ellen": "ICE", "lycaon": "ICE", "soukaku": "ICE", "miyabi": "ICE",
        "soldier 11": "FIRE", "koleda": "FIRE", "ben": "FIRE", "lucy": "FIRE", "burnice": "FIRE", "lighter": "FIRE",
        "anby": "ELECTRIC", "anton": "ELECTRIC", "rina": "ELECTRIC", "grace": "ELECTRIC", "seth": "ELECTRIC", "yanagi": "ELECTRIC", "harumasa": "ELECTRIC", "qingyi": "ELECTRIC",
        "billy": "PHYSICAL", "corin": "PHYSICAL", "nekomata": "PHYSICAL", "piper": "PHYSICAL", "caesar": "PHYSICAL",
        "nicole": "ETHER", "zhu yuan": "ETHER", "astra yao": "ETHER", "jane": "PHYSICAL"
    }

    try:
        with open(md_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("|") and not line.startswith("| Personagem") and not line.startswith("| :---"):
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 7:
                        cname = parts[1].replace("**", "").strip()
                        lvl_str = parts[2].replace("Nv.", "").strip()
                        try:
                            lvl = int(lvl_str)
                        except Exception:
                            lvl = 1
                        stars = parts[3].count("⭐")
                        if stars == 0:
                            stars = 5 if "5" in parts[3] else 4
                        c_str = parts[4].strip()
                        w_str = parts[5].strip()
                        w_name, w_lvl, w_rank = w_str, 90, 1
                        w_m = re.search(r'^(.*?)\s*\(Nv\.\s*(\d+),\s*R(\d+)\)$', w_str)
                        if w_m:
                            w_name = w_m.group(1).strip()
                            w_lvl = int(w_m.group(2))
                            w_rank = int(w_m.group(3))

                        elem = "Anemo"
                        if game_id == "genshin":
                            elem = genshin_elements.get(cname.lower(), "Anemo")
                        elif game_id == "zzz":
                            elem = zzz_elements.get(cname.lower(), "PHYSICAL")

                        chars.append({
                            "id": "",
                            "uid": "",
                            "name": cname,
                            "level": lvl,
                            "rarity": stars,
                            "rank_str": c_str,
                            "element": elem,
                            "icon": f"/api/proxy_image?url=https%3A%2F%2Fenka.network%2Fui%2FUI_AvatarIcon_{cname}.png",
                            "gacha_art": None,
                            "weapon": {
                                "name": w_name,
                                "level": w_lvl,
                                "rank": w_rank,
                                "icon": ""
                            } if w_name and w_name != "Nenhuma" else None,
                            "relics": []
                        })
    except Exception as e:
        print(f"Aviso ao realizar parse de fallback do MD para {game_id}: {e}")
    return chars

@app.get("/api/roster/{game_id}")
async def get_roster(game_id: str):
    """Retorna os dados dos personagens salvos no roster local."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido. Escolha 'hsr', 'genshin' ou 'zzz'.")
        
    data = None
    # Tenta carregar do SQLite primeiro
    try:
        data = database.get_roster_data(game_id)
    except Exception as e:
        print(f"Aviso ao carregar roster do SQLite para {game_id}: {e}")
        
    # Se não carregou do SQLite, tenta do JSON
    if not data:
        json_path = f"{game_id}/roster_data_{game_id}.json"
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao carregar banco de dados local: {e}")

    # Fallback de emergência APENAS se SQLite e JSON estiverem totalmente vazios
    if not data:
        data = parse_roster_md_fallback(game_id)
                
    if data:
        # Enriquece gacha_art do JSON se faltar no banco
        json_path = f"{game_id}/roster_data_{game_id}.json"
        json_map = {}
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    jdata = json.load(jf)
                    for jc in jdata:
                        if jc.get("name") and jc.get("gacha_art"):
                            json_map[jc["name"]] = jc["gacha_art"]
            except Exception:
                pass

        # Pondera e calcula as notas de cada relíquia do roster e a nota geral da build
        max_slots = 5 if game_id == "genshin" else 6
        for char in data:
            if char.get("name") in json_map and json_map[char["name"]]:
                char["gacha_art"] = json_map[char["name"]]

            # Garante fallback de gacha_art em HD para ZZZ e skins do Genshin
            if game_id == "zzz":
                from extractor import get_zzz_prydwen_slug
                icon_str = get_raw_url(char.get("icon") or "")
                g_art_str = get_raw_url(char.get("gacha_art") or "")
                check_str = icon_str + " " + g_art_str
                match = re.search(r'(?:role_square_avatar|role_vertical_painting)_(\d+)_(\d{7,})\.png', check_str)
                if match:
                    base_id, skin_id = match.group(1), match.group(2)
                    char["gacha_art"] = f"https://act-webstatic.hoyoverse.com/game_record/zzzv2/role_vertical_painting/role_vertical_painting_{base_id}_{skin_id}.png"
                else:
                    slug = get_zzz_prydwen_slug(char.get("name", ""))
                    if slug:
                        char["gacha_art"] = f"https://cdn.prydwen.gg/images/zenless-zone-zero/characters/{slug}_full.webp"
            elif game_id == "genshin":
                from extractor import sanitize_genshin_url
                if char.get("icon"):
                    char["icon"] = sanitize_genshin_url(char["icon"])
                if char.get("gacha_art"):
                    char["gacha_art"] = sanitize_genshin_url(char["gacha_art"])

                raw_g_art = get_raw_url(char.get("gacha_art") or "")
                raw_c_icon = get_raw_url(char.get("icon") or "")
                combined_check = raw_c_icon + " " + raw_g_art
                
                skin_match = re.search(r'(UI_AvatarIcon_[A-Za-z0-9_]+Costume[A-Za-z0-9_]*)', combined_check)
                if skin_match:
                    skin_fn = skin_match.group(1)
                    char["gacha_art"] = f"https://enka.network/ui/{skin_fn.replace('UI_AvatarIcon_', 'UI_Costume_')}.png"
                    if not raw_c_icon or "UI_AvatarIcon_" not in raw_c_icon:
                        char["icon"] = f"https://enka.network/ui/{skin_fn}.png"

            # Garante proxy interno para URLs de imagem externas evitando 403 Forbidden e duplicação
            if char.get("icon"):
                raw_icon = get_raw_url(char["icon"])
                if raw_icon.startswith("http"):
                    char["icon"] = f"/api/proxy_image?url={urllib.parse.quote(raw_icon, safe='')}"
            if char.get("gacha_art"):
                raw_gacha = get_raw_url(char["gacha_art"])
                if raw_gacha.startswith("http"):
                    char["gacha_art"] = f"/api/proxy_image?url={urllib.parse.quote(raw_gacha, safe='')}"
            if isinstance(char.get("weapon"), dict) and char["weapon"].get("icon"):
                raw_w_icon = get_raw_url(char["weapon"]["icon"])
                if raw_w_icon.startswith("http"):
                    char["weapon"]["icon"] = f"/api/proxy_image?url={urllib.parse.quote(raw_w_icon, safe='')}"

            char_id_val = str(char.get("id") or char.get("character_id") or "")
            meta_db = get_meta_data(game_id)
            c_name = char.get("name") or ""
            char_meta = meta_db.get(char_id_val) or meta_db.get(c_name.lower()) or meta_db.get(normalize_char_name(c_name)) or {}
            if char_meta:
                char["substats_priority"] = char_meta.get("substats_priority", [])
                char["recommended_weights"] = extract_weights_from_guide(game_id, char_id_val)

            relic_scores = []
            relics = char.get("relics") or char.get("artifacts") or char.get("discs") or []
            for relic in relics:
                if "name" in relic:
                    relic["name"] = clean_relic_name(relic["name"])
                if "main" in relic:
                    relic["main"] = sanitize_stat_name(relic["main"])
                if "sub" in relic and relic["sub"]:
                    subs_list = [sanitize_stat_name(s.strip()) for s in str(relic["sub"]).split(",") if s.strip()]
                    relic["sub"] = ", ".join(subs_list)
                if relic.get("icon"):
                    raw_r_icon = get_raw_url(relic["icon"])
                    if raw_r_icon.startswith("http"):
                        relic["icon"] = f"/api/proxy_image?url={urllib.parse.quote(raw_r_icon, safe='')}"

                grade, score = score_relic(
                    game_id=game_id,
                    char_id=char_id_val,
                    slot=str(relic.get("slot", "")),
                    main_stat=relic.get("main") or relic.get("main_stat") or "",
                    substats_str=relic.get("sub", "")
                )
                relic["grade"] = grade
                relic["score"] = score
                relic_scores.append(score)
            
            # A nota geral da build é calculada dividindo a soma pelo total de slots do jogo (6 para HSR/ZZZ, 5 para Genshin).
            # Peças não equipadas contam como 0 pontos, penalizando builds incompletas.
            equipped_count = len(relic_scores)
            if relic_scores and max_slots > 0:
                avg_score = round(sum(relic_scores) / max_slots, 1)
            else:
                avg_score = 0.0

            if avg_score >= 90.0: overall_grade = "SSS"
            elif avg_score >= 75.0: overall_grade = "SS"
            elif avg_score >= 60.0: overall_grade = "S"
            elif avg_score >= 45.0: overall_grade = "A"
            elif avg_score >= 30.0: overall_grade = "B"
            elif avg_score >= 15.0: overall_grade = "C"
            else: overall_grade = "D"

            char["overall_score"] = avg_score
            char["overall_grade"] = overall_grade
            char["equipped_pieces"] = equipped_count
            char["max_pieces"] = max_slots
        return data
        
    return []

@app.post("/api/sync/{game_id}")
async def start_sync(game_id: str, request: SyncRequest, background_tasks: BackgroundTasks):
    """Trigga a sincronização do roster, guias e metagame de um jogo específico."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
        
    if sync_status[game_id]["running"]:
        return JSONResponse(status_code=409, content={"status": "error", "message": "A sincronização para este jogo já está em execução."})
        
    # Limpa logs anteriores
    sync_status[game_id] = {
        "running": True,
        "progress": 0.0,
        "message": "Inicializando...",
        "logs": []
    }
    
    # Executa a thread de background
    background_tasks.add_task(
        _bg_sync_thread,
        game_id,
        request.run_roster,
        request.run_guides,
        request.run_meta
    )
    
    return {"status": "started", "message": "Sincronização iniciada com sucesso."}

@app.get("/api/status/{game_id}")
async def get_sync_status(game_id: str):
    """Retorna o progresso atual e os logs da sincronização."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
    return sync_status[game_id]

@app.get("/api/config")
async def get_configuration():
    """Retorna as chaves de API e cookies ativos atualmente."""
    cookies_dict = get_cookies()
    config_dict = get_config()
    
    cookies_str_list = []
    for k, v in cookies_dict.items():
        cookies_str_list.append(f"{k}={v}")
    cookies_raw = "; ".join(cookies_str_list)
    
    return {
        "groq_api_key": config_dict.get("groq_api_key") or config_dict.get("gemini_api_key") or "",
        "cookies_raw": cookies_raw,
        "has_cookies": len(cookies_dict) > 0,
        "has_api_key": bool(config_dict.get("groq_api_key") or config_dict.get("gemini_api_key"))
    }

@app.post("/api/config")
async def save_configuration(req: ConfigSaveRequest):
    """Salva a chave API do Groq e/ou os cookies HoYoLAB no formato JSON."""
    config_file = "config.json"
    cookie_file = "cookies.json"
    
    if req.groq_api_key is not None:
        config = get_config()
        config["groq_api_key"] = req.groq_api_key.strip()
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao salvar config.json: {e}")
            
    if req.cookies_raw is not None:
        cookies = parse_cookie_string(req.cookies_raw)
        if cookies:
            try:
                with open(cookie_file, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, indent=4)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Erro ao salvar cookies.json: {e}")
        else:
            if os.path.exists(cookie_file):
                os.remove(cookie_file)
                
    return {"status": "success", "message": "Configurações salvas localmente."}

@app.post("/api/login/auto")
async def auto_login_hoyolab(background_tasks: BackgroundTasks):
    """Dispara a janela do navegador via Playwright para capturar os cookies automaticamente."""
    def _run_login():
        print("[INFO] Abrindo navegador Playwright para capturar cookies...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            cookies_captured = loop.run_until_complete(capturar_cookies_hoyolab())
            loop.close()
            
            if cookies_captured:
                cookie_file = "cookies.json"
                with open(cookie_file, "w", encoding="utf-8") as f:
                    json.dump(cookies_captured, f, indent=4)
                print("[SUCCESS] Cookies capturados e salvos automaticamente!")
        except Exception as e:
            print(f"[ERROR] Falha na captura automática de cookies: {e}")
            
    background_tasks.add_task(_run_login)
    return {"status": "started", "message": "Navegador de Login Automático iniciado em segundo plano."}

@app.get("/api/notes")
async def get_notes():
    """Busca as notas diárias (resina, energia, diárias) em tempo real via API do HoYoLAB."""
    cookies = get_cookies()
    if not cookies:
        try:
            return database.get_cached_daily_notes()
        except Exception:
            return {}
            
    client = genshin.Client(cookies=cookies, lang="pt-pt")
    
    try:
        accounts = await client.get_game_accounts()
    except Exception as e:
        print(f"Erro ao obter contas vinculadas no HoYoLAB para notas: {e}")
        try:
            return database.get_cached_daily_notes()
        except Exception:
            return {}
            
    for acc in accounts:
        # 1. Genshin Impact
        if acc.game_biz.startswith("hk4e"):
            try:
                client.game = genshin.Game.GENSHIN
                notes = await client.get_genshin_notes(acc.uid)
                
                # Salva os detalhes básicos da conta no banco de dados para sincronizar nível
                database.save_game_account(
                    uid=str(acc.uid),
                    game_id="genshin",
                    nickname=acc.nickname,
                    level=acc.level
                )
                
                expeditions = []
                for exp in notes.expeditions:
                    rem_time = getattr(exp, "remaining_time", getattr(exp, "remained_time", None))
                    expeditions.append({
                        "character_icon": getattr(exp, "character_icon", getattr(getattr(exp, "character", None), "icon", "")),
                        "status": str(exp.status),
                        "remaining_time": str(rem_time) if rem_time is not None else "0"
                    })
                    
                extra_info = {
                    "completed_commissions": notes.completed_commissions,
                    "max_commissions": notes.max_commissions,
                    "claimed_commission_reward": notes.claimed_commission_reward,
                    "expeditions": expeditions,
                    "current_realm_currency": notes.current_realm_currency,
                    "max_realm_currency": notes.max_realm_currency
                }
                
                database.save_daily_notes(
                    uid=str(acc.uid),
                    game_id="genshin",
                    nickname=acc.nickname,
                    current_energy=notes.current_resin,
                    max_energy=notes.max_resin,
                    recovery_time=str(notes.remaining_resin_recovery_time),
                    extra_info=extra_info
                )
            except Exception as ge:
                print(f"Erro ao obter notas do Genshin: {ge}")
                
        # 2. Honkai: Star Rail
        elif acc.game_biz.startswith("hkrpg"):
            try:
                client.game = genshin.Game.STARRAIL
                notes = await client.get_starrail_notes(acc.uid)
                
                # Salva os detalhes básicos da conta no banco de dados para sincronizar nível
                database.save_game_account(
                    uid=str(acc.uid),
                    game_id="hsr",
                    nickname=acc.nickname,
                    level=acc.level
                )
                
                expeditions = []
                for exp in notes.expeditions:
                    rem_time = getattr(exp, "remaining_time", getattr(exp, "remained_time", None))
                    expeditions.append({
                        "name": getattr(exp, "name", "Expedição"),
                        "remaining_time": str(rem_time) if rem_time is not None else "0"
                    })
                    
                extra_info = {
                    "expeditions": expeditions,
                    "current_train_score": notes.current_train_score,
                    "max_train_score": notes.max_train_score,
                    "current_rogue_score": getattr(notes, "current_rogue_score", 0),
                    "max_rogue_score": getattr(notes, "max_rogue_score", 0)
                }
                
                # Stamina recovery time é timedelta, convertemos para segundos (string int) para o front decodificar
                recovery_sec = "0"
                if hasattr(notes, "stamina_recover_time") and notes.stamina_recover_time:
                    recovery_sec = str(int(notes.stamina_recover_time.total_seconds()))
                
                database.save_daily_notes(
                    uid=str(acc.uid),
                    game_id="hsr",
                    nickname=acc.nickname,
                    current_energy=notes.current_stamina,
                    max_energy=notes.max_stamina,
                    recovery_time=recovery_sec,
                    extra_info=extra_info
                )
            except Exception as he:
                print(f"Erro ao obter notas do HSR: {he}")
                
        # 3. Zenless Zone Zero
        elif acc.game_biz.startswith("nap"):
            try:
                client.game = genshin.Game.ZZZ
                notes = await client.get_zzz_notes(acc.uid)
                
                # Salva os detalhes básicos da conta no banco de dados para sincronizar nível
                database.save_game_account(
                    uid=str(acc.uid),
                    game_id="zzz",
                    nickname=acc.nickname,
                    level=acc.level
                )
                
                extra_info = {
                    "engagement": getattr(notes.engagement, "current", 0) if hasattr(notes, "engagement") and hasattr(notes.engagement, "current") else getattr(notes, "engagement", 0),
                    "video_store_state": str(getattr(notes, "video_store_state", "Desconhecido")),
                    "scratch_card_completed": bool(getattr(notes, "scratch_card_completed", False))
                }
                
                # No pydantic model do genshin.py, recovery_time está em battery_charge.seconds_till_full
                recovery_sec = "0"
                if hasattr(notes, "battery_charge"):
                    recovery_sec = str(getattr(notes.battery_charge, "seconds_till_full", 0))
                
                database.save_daily_notes(
                    uid=str(acc.uid),
                    game_id="zzz",
                    nickname=acc.nickname,
                    current_energy=notes.battery_charge.current if hasattr(notes.battery_charge, "current") else getattr(notes, "battery_charge", 0),
                    max_energy=notes.battery_charge.max if hasattr(notes.battery_charge, "max") else 240,
                    recovery_time=recovery_sec,
                    extra_info=extra_info
                )
            except Exception as ze:
                print(f"Erro ao obter notas do ZZZ: {ze}")
                
    try:
        return database.get_cached_daily_notes()
    except Exception as e:
        return {}

@app.post("/api/checkin/run")
async def run_manual_checkin():
    """Roda o check-in manual na HoYoLAB e retorna o resultado."""
    logs = await perform_auto_checkin()
    return {"status": "completed", "logs": logs}

@app.get("/api/checkin/today")
async def get_checkin_today():
    """Retorna os logs de check-in efetuados hoje."""
    try:
        return database.get_today_checkin_logs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# TRADUTOR DE ITENS E STATUS (INGLÊS -> PT-BR)
# ==========================================

TRANSLATIONS = {}
try:
    with open("traducoes.json", "r", encoding="utf-8") as f:
        TRANSLATIONS = json.load(f)
except Exception as te:
    print(f"[WARN] Não foi possível carregar traducoes.json: {te}")

def traduzir_item(nome_ingles: str) -> str:
    if not nome_ingles:
        return nome_ingles
        
    nome_clean = nome_ingles.strip()
    
    # Extrai sufixos comuns como (4-PC), (2-PC), (S1), (R5)
    suffix = ""
    match_suffix = re.search(r'\s*(\((?:\d-PC|\d-pc|S\d|R\d)\))\s*$', nome_clean, re.I)
    if match_suffix:
        suffix = " " + match_suffix.group(1)
        nome_clean = nome_clean[:match_suffix.start()].strip()
        
    # Tenta correspondência exata no dicionário
    if nome_clean in TRANSLATIONS:
        return TRANSLATIONS[nome_clean] + suffix
        
    # Tenta correspondência case-insensitive
    nome_lower = nome_clean.lower()
    for eng_key, pt_val in TRANSLATIONS.items():
        if eng_key.lower() == nome_lower:
            return pt_val + suffix
            
    # Tenta substituir termos dentro de expressões maiores (como em status principais)
    traduzido = nome_clean
    for eng_key, pt_val in TRANSLATIONS.items():
        if len(eng_key) < 30:
            pattern = re.compile(rf'\b{re.escape(eng_key)}\b', re.IGNORECASE)
            traduzido = pattern.sub(pt_val, traduzido)
            
    return traduzido + suffix

def find_best_guide_file(game_id: str, char_name: str, element: str = "") -> str:
    char_name_lower = char_name.lower()
    
    # Mapeamento do Trailblazer e Traveler baseado no elemento
    if game_id == "hsr" and ("desbravador" in char_name_lower or "trailblazer" in char_name_lower):
        elem_map = {
            "ice": "remembrance",
            "fire": "preservation",
            "physical": "destruction",
            "imaginary": "harmony"
        }
        path_name = elem_map.get(element.lower(), "harmony")
        char_name = f"trailblazer • {path_name}"
    elif game_id == "genshin" and ("viajante" in char_name_lower or "traveler" in char_name_lower):
        elem_map = {
            "anemo": "anemo",
            "geo": "geo",
            "electro": "electro",
            "dendro": "dendro",
            "hydro": "hydro",
            "pyro": "pyro",
            "cryo": "cryo"
        }
        path_name = elem_map.get(element.lower(), "dendro")
        char_name = f"{path_name} traveler"
        
    char_name_clean = char_name.lower().replace(' ', '').replace('-', '').replace('•', '').replace('_', '').replace('(a)', '')
    
    # 1. Correspondência exata/preferencial de caminhos
    paths_to_check = [
        f"{game_id}/guias/{char_name.lower().replace(' ', '_').replace('•_', '')}.md",
        f"{game_id}/guias/{char_name.lower().replace(' ', '_')}.md",
        f"{game_id}/guias/{char_name.lower()}.md",
        f"{game_id}/guias_prydwen/{char_name.lower().replace(' ', '_')}.md",
        f"{game_id}/guias_kqm/{char_name.lower().replace(' ', '_')}.md"
    ]
    for p in paths_to_check:
        if os.path.exists(p):
            return p
            
    # 2. Varredura e correspondência por substring inteligente nos arquivos
    guias_dir = f"{game_id}/guias"
    if os.path.exists(guias_dir):
        files = os.listdir(guias_dir)
        best_match = None
        best_len = 0
        for f in files:
            if not f.endswith(".md"):
                continue
            f_clean = f.lower().replace('.md', '').replace(' ', '').replace('-', '').replace('•', '').replace('_', '')
            
            # Checa se o nome limpo do arquivo está contido no personagem ou vice-versa
            if f_clean in char_name_clean or char_name_clean in f_clean:
                if len(f_clean) > best_len:
                    best_match = f
                    best_len = len(f_clean)
        if best_match:
            return os.path.join(guias_dir, best_match)
            
    return paths_to_check[0]

def parse_meta_target(game_id: str, char_name: str, element: str = "") -> dict:
    target = {
        "weapon": "Não informado",
        "weapons": [],
        "sets": ["Não informado"],
        "all_sets": [],
        "stats": {},
        "endgame_stats": {}
    }
    
    guide_path = find_best_guide_file(game_id, char_name, element)
    
    guide_content = ""
    if os.path.exists(guide_path):
        try:
            with open(guide_path, "r", encoding="utf-8") as f:
                guide_content = f.read()
        except Exception:
            pass
                
    if not guide_content:
        return target

    lines = guide_content.splitlines()
    
    # 1. Busca W-Engine / Arma / Cone baseada em seção (listas ou tabelas)
    found_weapon_section = False
    weapons_list = []
    for i, line in enumerate(lines):
        if any(term in line.lower() for term in ["melhores w-engines", "melhor w-engine", "best w-engine", "melhores cones", "melhor cone", "best light cone", "melhores armas", "melhor arma", "best weapon", "weapons"]):
            for next_line in lines[i+1:i+16]:
                next_line_strip = next_line.strip()
                if next_line_strip.startswith("-") or next_line_strip.startswith("*") or (next_line_strip and next_line_strip[0].isdigit() and "." in next_line_strip):
                    val = next_line_strip.lstrip("-*0123456789. \t").strip()
                    if "(" in val:
                        val = val.split("(")[0].strip()
                    val = val.replace("**", "").replace("`", "").strip()
                    if val and val not in weapons_list:
                        weapons_list.append(val)
                elif "|" in next_line_strip:
                    parts = [p.strip() for p in next_line_strip.split("|") if p.strip()]
                    if parts:
                        val = parts[0].replace("**", "").replace("`", "").strip()
                        if val and val.lower() not in ["weapon", "arma", "cone", "w-engine", "cone de luz", "eficácia"]:
                            if "(" in val:
                                val = val.split("(")[0].strip()
                            if val and val not in weapons_list:
                                weapons_list.append(val)
            if weapons_list:
                target["weapon"] = weapons_list[0]
                target["weapons"] = weapons_list
                found_weapon_section = True
                break

    # Fallback clássico se não achou por seção
    if target["weapon"] == "Não informado":
        m_w = re.search(r'(?:Melhor Cone de Luz|Melhor Arma|Melhor W-Engine|Cone de Luz Recomendado|Arma Recomendada|W-Engine Recomendado|Best Light Cone|Best Weapon|Best W-Engine)[:\*\-\s]+([^\n]+)', guide_content, re.IGNORECASE)
        if m_w:
            target["weapon"] = m_w.group(1).replace("**", "").strip()
            target["weapons"] = [target["weapon"]]

    # 2. Busca Sets / Relíquias / Discos baseada em seção (listas ou tabelas)
    found_sets_section = False
    sets_list = []
    for i, line in enumerate(lines):
        if any(term in line.lower() for term in ["melhores conjuntos", "melhores artefatos", "relíquias recomendadas", "best relics", "best artifacts", "best discs", "melhores discos", "artifact sets", "artifacts", "relics", "discs"]):
            for next_line in lines[i+1:i+16]:
                next_line_strip = next_line.strip()
                if next_line_strip.startswith("-") or next_line_strip.startswith("*") or (next_line_strip and next_line_strip[0].isdigit() and "." in next_line_strip):
                    val = next_line_strip.lstrip("-*0123456789. \t").strip()
                    if "(" in val:
                        val = val.split("(")[0].strip()
                    val = val.replace("**", "").replace("`", "").strip()
                    if val and val not in sets_list:
                        sets_list.append(val)
                elif "|" in next_line_strip:
                    parts = [p.strip() for p in next_line_strip.split("|") if p.strip()]
                    if parts:
                        val = parts[0].replace("**", "").replace("`", "").strip()
                        if val and val.lower() not in ["artifact", "set", "conjunto", "artefato", "relíquia", "relic", "disco", "eficácia"]:
                            if "(" in val:
                                val = val.split("(")[0].strip()
                            if val and val not in sets_list:
                                sets_list.append(val)
            if sets_list:
                target["sets"] = [sets_list[0]]
                target["all_sets"] = sets_list
                found_sets_section = True
                break

    if target["sets"] == ["Não informado"]:
        m_s = re.search(r'(?:Melhores Conjuntos|Melhores Artefatos|Relíquias Recomendadas|Best Relics|Best Artifacts|Best Discs)[:\*\-\s]+([^\n]+)', guide_content, re.IGNORECASE)
        if m_s:
            target["sets"] = [s.strip().replace("**", "") for s in m_s.group(1).split(',')]
            target["all_sets"] = target["sets"]

    # 3. Busca Peças e Status (Corpo, Bota, Esfera, Corda / Tiara, Copo, Areia, Pena, Flor / Discos)
    stats_found = {}
    
    # 3a. Tenta buscar em tabelas de status de Genshin (Sands | Goblet | Circlet)
    if game_id == "genshin":
        for i, line in enumerate(lines):
            line_strip = line.strip().lower()
            if "sands" in line_strip and "goblet" in line_strip and "circlet" in line_strip:
                if i + 2 < len(lines):
                    val_line = lines[i+2].strip()
                    if val_line.startswith("|") and val_line.endswith("|"):
                        parts = [p.strip().replace("**", "").replace("`", "") for p in val_line.split("|") if p.strip()]
                        if len(parts) >= 3:
                            stats_found["Areia"] = parts[0]
                            stats_found["Copo"] = parts[1]
                            stats_found["Tiara"] = parts[2]
                break
                
    # 3b. Tenta buscar em formato de lista baseado no jogo
    if not stats_found:
        if game_id == "genshin":
            piece_patterns = [
                (re.compile(r'\b(?:Tiara|Circlet)\b', re.IGNORECASE), "Tiara"),
                (re.compile(r'\b(?:Cálice|Copo|Goblet)\b', re.IGNORECASE), "Copo"),
                (re.compile(r'\b(?:Areia|Sands)\b', re.IGNORECASE), "Areia"),
                (re.compile(r'\b(?:Pena|Plume)\b', re.IGNORECASE), "Pena"),
                (re.compile(r'\b(?:Flor|Flower)\b', re.IGNORECASE), "Flor"),
            ]
        elif game_id == "hsr":
            piece_patterns = [
                (re.compile(r'\b(?:Corpo|Body)\b', re.IGNORECASE), "Corpo"),
                (re.compile(r'\b(?:Bota|Pés|Feet)\b', re.IGNORECASE), "Bota"),
                (re.compile(r'\b(?:Esfera|Planar Sphere)\b', re.IGNORECASE), "Esfera"),
                (re.compile(r'\b(?:Corda|Link Rope)\b', re.IGNORECASE), "Corda"),
                (re.compile(r'\b(?:Cabeça|Head)\b', re.IGNORECASE), "Cabeça"),
                (re.compile(r'\b(?:Mãos|Hands)\b', re.IGNORECASE), "Mãos"),
            ]
        else: # zzz
            piece_patterns = [
                (re.compile(r'\b(?:Disco 4|Disk 4)\b', re.IGNORECASE), "Disco 4"),
                (re.compile(r'\b(?:Disco 5|Disk 5)\b', re.IGNORECASE), "Disco 5"),
                (re.compile(r'\b(?:Disco 6|Disk 6)\b', re.IGNORECASE), "Disco 6"),
                (re.compile(r'\b(?:Disco 1|Disk 1)\b', re.IGNORECASE), "Disco 1"),
                (re.compile(r'\b(?:Disco 2|Disk 2)\b', re.IGNORECASE), "Disco 2"),
                (re.compile(r'\b(?:Disco 3|Disk 3)\b', re.IGNORECASE), "Disco 3"),
            ]
            
        for line in lines:
            line_strip = line.strip()
            if not line_strip.startswith("-") and not line_strip.startswith("*"):
                continue
                
            for pattern, label in piece_patterns:
                if pattern.search(line_strip):
                    clean_val = line_strip.lstrip("-* \t")
                    clean_val = pattern.sub("", clean_val).strip()
                    clean_val = clean_val.lstrip(":-*` \t").replace("**", "").replace("`", "").strip()
                    if clean_val:
                        stats_found[label] = clean_val
                        break
                        
    if stats_found:
        target["stats"] = stats_found
    else:
        stats_matches = re.findall(r'(?:Corpo|Bota|Pés|Corda|Esfera|Areia|Cálice|Copo|Tiara|Flor|Pluma|Pena|Body|Feet|Sands|Goblet|Circlet|Link Rope|Planar Sphere|Disco \d)[:\*\-\s]+([^\n\r]+)', guide_content, re.IGNORECASE)
        if stats_matches:
            if game_id == "genshin":
                parts = ["Tiara", "Copo", "Areia", "Pena", "Flor"]
            elif game_id == "hsr":
                parts = ["Corpo", "Bota", "Esfera", "Corda", "Cabeça", "Mãos"]
            else:
                parts = ["Disco 4", "Disco 5", "Disco 6"]
            for idx, match in enumerate(stats_matches[:len(parts)]):
                label = parts[idx]
                target["stats"][label] = match.replace("**", "").strip()
                
    # 4. Busca Atributos Finais Recomendados (Endgame Stats)
    endgame_stats = {}
    for i, line in enumerate(lines):
        if any(term in line.lower() for term in ["atributos finais", "endgame stats"]):
            for next_line in lines[i+1:i+12]:
                next_line_strip = next_line.strip()
                if next_line_strip.startswith("-") or next_line_strip.startswith("*"):
                    clean_line = next_line_strip.lstrip("-* \t")
                    if ":" in clean_line:
                        parts = clean_line.split(":")
                        stat_name = parts[0].replace("**", "").replace("`", "").strip()
                        stat_val = parts[1].replace("**", "").replace("`", "").strip()
                        endgame_stats[stat_name] = stat_val
                elif next_line_strip and next_line_strip.startswith("#"):
                    break
            break
            
    # Se não houver atributos finais no guia (caso do HSR e Genshin), geramos valores de benchmark recomendados
    if not endgame_stats:
        if game_id == "hsr":
            guide_lower = guide_content.lower()
            is_break = "break effect" in guide_lower or "efeito de quebra" in guide_lower or "super break" in guide_lower
            is_def = "def%" in guide_lower or "defesa" in guide_lower
            is_hp = "hp%" in guide_lower or "pv%" in guide_lower
            
            endgame_stats["VEL"] = "134+"
            if is_break:
                endgame_stats["Efeito de Quebra"] = "150%+"
            else:
                endgame_stats["Chance de CRIT"] = "70%+"
                endgame_stats["Dano CRIT"] = "140%+"
                
            if is_def:
                endgame_stats["DEF"] = "3000+"
            elif is_hp:
                endgame_stats["PV"] = "5000+"
            else:
                endgame_stats["ATQ"] = "3000+"
                
        elif game_id == "genshin":
            guide_lower = guide_content.lower()
            is_em = "elemental mastery" in guide_lower or "proficiência elemental" in guide_lower or "mastery" in guide_lower
            is_hp = "hp%" in guide_lower or "vida%" in guide_lower
            is_def = "def%" in guide_lower or "defesa%" in guide_lower
            
            endgame_stats["Recarga de Energia"] = "150%+"
            if is_em:
                endgame_stats["Proficiência Elemental"] = "600+"
            else:
                endgame_stats["Taxa Crítica"] = "60%+"
                endgame_stats["Dano Crítico"] = "120%+"
                
            if is_hp:
                endgame_stats["Vida Máxima"] = "30000+"
            elif is_def:
                endgame_stats["DEF"] = "2000+"
            else:
                endgame_stats["ATQ"] = "1800+"
                
    target["endgame_stats"] = endgame_stats
    
    # 5. Traduz todos os campos extraídos para PT-BR usando o dicionário local
    if target["weapon"] != "Não informado":
        target["weapon"] = traduzir_item(target["weapon"])
    if target["weapons"]:
        target["weapons"] = [traduzir_item(w) for w in target["weapons"]]
    if target["sets"] and target["sets"] != ["Não informado"]:
        target["sets"] = [traduzir_item(s) for s in target["sets"]]
    if target["all_sets"]:
        target["all_sets"] = [traduzir_item(s) for s in target["all_sets"]]
        
    translated_stats = {}
    for k, v in target["stats"].items():
        translated_stats[traduzir_item(k)] = traduzir_item(v)
    target["stats"] = translated_stats
    
    translated_endgame = {}
    for k, v in target["endgame_stats"].items():
        translated_endgame[traduzir_item(k)] = traduzir_item(v)
    target["endgame_stats"] = translated_endgame
    
    return target

@app.get("/api/compare/{game_id}/{char_name}")
async def compare_build(game_id: str, char_name: str):
    """Retorna os dados da build do jogador comparados aos dados ideais do metagame."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
        
    element = ""
    try:
        roster_json_path = f"{game_id}/roster_data_{game_id}.json"
        if os.path.exists(roster_json_path):
            with open(roster_json_path, "r", encoding="utf-8") as rf:
                roster_data = json.load(rf)
                for char in roster_data:
                    if char.get("name") == char_name:
                        element = char.get("element", "").lower()
                        break
    except Exception as e:
        print(f"Erro ao buscar elemento do personagem: {e}")
        
    build_data = parse_character_build_data(game_id, char_name)
    meta_target = parse_meta_target(game_id, char_name, element)
    
    return {
        "character": char_name,
        "game_id": game_id,
        "player_build": {
            "weapon": build_data.get("weapon", "Não informado"),
            "sets": build_data.get("sets", []),
            "stats": build_data.get("stats", {}),
            "pieces": build_data.get("pieces", [])
        },
        "meta_target": meta_target
    }

@app.post("/api/chat")
async def chat_interaction(req: ChatRequest):
    """Endpoint do Chat RAG Local (Groq) com streaming SSE de tokens."""
    config = get_config()
    api_key = config.get("groq_api_key") or config.get("gemini_api_key") or os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        async def err_generator():
            yield "data: " + json.dumps({"error": "Erro: Chave API do Groq não configurada. Salve-a na aba Configurações."}) + "\n\n"
        return StreamingResponse(err_generator(), media_type="text/event-stream")
        
    try:
        rag = GroqRAG(api_key=api_key)
        context = rag.load_game_context(req.game_id, req.message)
        
        history_list = []
        for h in req.history:
            history_list.append({
                "role": h.role,
                "text": h.text
            })
            
        async def event_generator():
            try:
                for chunk in rag.ask_assistant_stream(
                    prompt_usuario=req.message,
                    contexto_rag=context,
                    historico_chat=history_list
                ):
                    yield "data: " + json.dumps({"token": chunk}) + "\n\n"
            except Exception as stream_err:
                yield "data: " + json.dumps({"error": str(stream_err)}) + "\n\n"
                
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as chat_err:
        traceback.print_exc()
        async def err_gen():
            yield "data: " + json.dumps({"error": f"Ocorreu um erro no processador do chat: {chat_err}"}) + "\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")

# ==========================================
# PARSER DE DETALHES DE BUILD DE PERSONAGEM
# ==========================================

def get_character_build_detail(game_id: str, char_name: str) -> str:
    # Tenta obter do SQLite primeiro
    try:
        db_md = database.get_character_build_md(game_id, char_name)
        if db_md:
            return db_md
    except Exception as e:
        print(f"Erro ao buscar build no SQLite para {char_name}: {e}")

    filepath = f"{game_id}/roster_{game_id}.md"
    if not os.path.exists(filepath):
        return ""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        # Busca o bloco sob o nome do personagem correspondente
        pattern = rf'(\*\*(?:Personagem|Agente):\*\*\s*{re.escape(char_name)}.*?)(?=\n\*\*(?:Personagem|Agente):\*\*|\n## |\Z)'
        match = re.search(pattern, content, re.DOTALL | re.I)
        if match:
            return match.group(1).strip()
    except Exception as e:
        print(f"Erro ao buscar detalhes da build de {char_name}: {e}")
    return ""

def parse_character_build_data(game_id: str, char_name: str) -> dict:
    raw_text = get_character_build_detail(game_id, char_name)
    data = {
        "name": char_name,
        "raw": raw_text,
        "weapon": "Não informado",
        "sets": [],
        "stats": {},
        "pieces": []
    }
    if not raw_text:
        # Mesmo sem texto, tenta carregar stats do JSON
        pass
        
    if raw_text:
        m_w = re.search(r'-\s*\*\*(?:Cone de Luz|Arma|W-Engine):\*\*\s*(.*)', raw_text)
        if m_w:
            data["weapon"] = m_w.group(1).strip()
            
        m_s = re.search(r'-\s*\*\*(?:Relíquias|Artefatos|Discos):\*\*\s*(.*)', raw_text)
        if m_s:
            sets_raw = m_s.group(1).strip()
            data["sets"] = [s.strip() for s in sets_raw.split('+')]
            
        m_st = re.search(r'-\s*\*\*Status Finais:\*\*\s*(.*)', raw_text)
        if m_st:
            stats_raw = m_st.group(1).strip()
            for pair in stats_raw.split(','):
                if ':' in pair:
                    k, v = pair.split(':', 1)
                    data["stats"][k.strip()] = v.strip()
                    
        m_pieces = re.findall(r'•\s*\[(.*?)\]\s*(.*?)\n\s*-\s*Principal:\s*(.*?)\n\s*-\s*Substatus:\s*(.*?)(?=\n\s*•|\Z|\n\n|\n---)', raw_text, re.DOTALL)
        for slot, p_name, main_s, sub_s in m_pieces:
            slot_clean = slot.strip()
            if game_id == "genshin":
                if any(term in slot_clean.lower() for term in ["circlet", "tiara", "tiara de logos"]) or slot_clean == "5":
                    slot_clean = "Tiara"
                elif any(term in slot_clean.lower() for term in ["goblet", "cálice", "copo", "cálice de eonothem"]) or slot_clean == "4":
                    slot_clean = "Copo"
                elif any(term in slot_clean.lower() for term in ["sands", "areia", "ampulheta", "areias do tempo"]) or slot_clean == "3":
                    slot_clean = "Areia"
                elif any(term in slot_clean.lower() for term in ["plume", "pena", "pluma da morte"]) or slot_clean == "2":
                    slot_clean = "Pena"
                elif any(term in slot_clean.lower() for term in ["flower", "flor", "flor da vida"]) or slot_clean == "1":
                    slot_clean = "Flor"
            elif game_id == "hsr":
                if any(term in slot_clean.lower() for term in ["body", "corpo"]):
                    slot_clean = "Corpo"
                elif any(term in slot_clean.lower() for term in ["feet", "bota", "pés"]):
                    slot_clean = "Bota"
                elif any(term in slot_clean.lower() for term in ["sphere", "esfera", "esfera plana"]):
                    slot_clean = "Esfera"
                elif any(term in slot_clean.lower() for term in ["rope", "corda", "corda de ligação"]):
                    slot_clean = "Corda"
                elif any(term in slot_clean.lower() for term in ["head", "cabeça"]):
                    slot_clean = "Cabeça"
                elif any(term in slot_clean.lower() for term in ["hands", "mãos"]):
                    slot_clean = "Mãos"
            elif game_id == "zzz":
                slot_clean = slot_clean.replace("Disk", "Disco").replace("disk", "Disco")
                
            data["pieces"].append({
                "slot": slot_clean,
                "name": p_name.strip(),
                "main": main_s.strip(),
                "sub": sub_s.strip()
            })

    # Enriquece stats com os Status Finais do roster JSON (prioridade sobre MD parsed)
    try:
        json_path = f"{game_id}/roster_data_{game_id}.json"
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as jf:
                roster_data = json.load(jf)
            char_lower = char_name.lower().strip()
            for c in roster_data:
                if c.get("name", "").lower().strip() == char_lower:
                    json_stats = c.get("stats") or {}
                    if json_stats:
                        data["stats"] = json_stats  # Substitui pelo dado da API, que é mais preciso
                    break
    except Exception:
        pass

    return data

@app.get("/api/overview")
async def get_overview():
    """Gera dados resumidos consolidados dos 3 jogos mesclando SQLite e arquivos locais."""
    db_overview = {}
    try:
        db_overview = database.get_overview_data()
    except Exception as e:
        print(f"Erro ao buscar visão geral no SQLite: {e}")

    overview = {}
    for game in ["hsr", "genshin", "zzz"]:
        # Inicializa a estrutura de fallback
        fallback_info = {"active": False, "uid": "Não sincronizado", "level": "N/A", "char_count": 0, "five_stars": 0}
        
        # Carrega dados do arquivo local
        json_path = f"{game}/roster_data_{game}.json"
        md_path = f"{game}/roster_{game}.md"
        
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    fallback_info["char_count"] = len(data)
                    if game == "zzz":
                        fallback_info["five_stars"] = sum(1 for c in data if str(c.get("rarity")) in ["5", "S"])
                    else:
                        fallback_info["five_stars"] = sum(1 for c in data if c.get("rarity") == 5)
                    fallback_info["active"] = True
            except Exception:
                pass
                
        if os.path.exists(md_path):
            try:
                with open(md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Regex flexível para capturar UID independente de formatação do Markdown
                m_uid = re.search(r'UID[:\*]*\s*(\d+)', content)
                if m_uid:
                    fallback_info["uid"] = m_uid.group(1)
                    
                # Regex flexível para capturar o Nível/Rank independente de formatação
                if game == "hsr":
                    m_lvl = re.search(r'Nível de Desbravamento[:\*]*\s*(\d+)', content)
                elif game == "genshin":
                    m_lvl = re.search(r'Rank de Aventura[:\*]*\s*(\d+)', content)
                else: # zzz
                    m_lvl = re.search(r'Nível de Intermediário[:\*]*\s*(\d+)', content)
                    
                if m_lvl:
                    fallback_info["level"] = m_lvl.group(1)
            except Exception:
                pass

        # Decisão de qual info usar
        db_game = db_overview.get(game, {})
        
        # Se temos dados válidos no DB e ele possui personagens cadastrados, prioriza o DB
        if db_game and db_game.get("active") and db_game.get("char_count", 0) > 0:
            overview[game] = db_game
        # Caso contrário, se o fallback do arquivo local tiver personagens sincronizados, usa o local
        elif fallback_info["active"] and fallback_info.get("char_count", 0) > 0:
            overview[game] = fallback_info
        else:
            # Fallback final, priorizando o DB se existir
            overview[game] = db_game if db_game else fallback_info
            
    return overview

@app.get("/api/build/{game_id}/{char_name}")
async def get_build_detail(game_id: str, char_name: str):
    """Retorna os dados detalhados da build de um personagem, parseando o MD consolidado."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
    return parse_character_build_data(game_id, char_name)

@app.post("/api/team/analyze")
async def analyze_team(req: TeamAnalyzeRequest):
    """Endpoint que analisa a sinergia de um time de personagens do roster via IA (SSE Stream)."""
    config = get_config()
    api_key = config.get("groq_api_key") or config.get("gemini_api_key") or os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        async def err_generator():
            yield "data: " + json.dumps({"error": "Erro: Chave API do Groq/Gemini não configurada. Configure na aba Configurações."}) + "\n\n"
        return StreamingResponse(err_generator(), media_type="text/event-stream")
        
    try:
        rag = GroqRAG(api_key=api_key)
        # Carrega o contexto filtrando pelos personagens selecionados
        query_str = ", ".join(req.characters)
        context = rag.load_game_context(req.game_id, query_str)
        
        prompt_analysis = (
            f"Faça uma análise de sinergia de combate extremamente profissional e aprofundada para a seguinte equipe selecionada do jogo {req.game_id.upper()}: {', '.join(req.characters)}.\n"
            "Com base no contexto fornecido (suas builds reais de personagem + guias de metagame ideais):\n"
            "1. Descreva a sinergia geral do time e como as habilidades se complementam.\n"
            "2. Avalie as armas e relíquias/discos equipados em relação ao ideal do metagame, apontando acertos e desvios críticos.\n"
            "3. Detalhe a rotação de combate ideal passo a passo (quem inicia, quem buffa, quem aplica elemento, quem é o DPS principal).\n"
            "4. Forneça sugestões de melhorias diretas (substitutos ideais de personagens ou trocas recomendadas de armas/artefatos).\n"
            "Formate a resposta em Markdown limpo e amigável com emojis."
        )
        
        async def event_generator():
            try:
                for chunk in rag.ask_assistant_stream(
                    prompt_usuario=prompt_analysis,
                    contexto_rag=context,
                    historico_chat=[]
                ):
                    yield "data: " + json.dumps({"token": chunk}) + "\n\n"
            except Exception as stream_err:
                yield "data: " + json.dumps({"error": str(stream_err)}) + "\n\n"
                
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as chat_err:
        traceback.print_exc()
        async def err_gen():
            yield "data: " + json.dumps({"error": f"Erro no processamento do time: {chat_err}"}) + "\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")

@app.post("/api/materials/calculate")
async def calculate_materials(req: MaterialsCalculateRequest):
    """Calcula o total estimado de materiais necessários para elevar um personagem."""
    res = calculate_ascension(req.game_id, req.current_level, req.target_level)
    if not res:
        raise HTTPException(status_code=400, detail="Erro ao realizar o cálculo de ascensão.")
    return res

@app.post("/api/evaluate-stats/{game_id}/{char_id}")
async def evaluate_character_stats(game_id: str, char_id: str, final_stats: Dict[str, str]):
    """Compara os status consolidados reais do personagem contra os benchmarks do metagame."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
    from build_calculator import evaluate_general_stats
    results = evaluate_general_stats(game_id, str(char_id), final_stats)
    return results

# ==========================================
# ENDPOINT OTIMIZADOR DE BUILDS VIA IA
# ==========================================

@app.get("/api/optimize/{game_id}/{char_name}")
async def optimize_character_build(game_id: str, char_name: str):
    """Gera sugestões de otimização de build com base nos dados do roster e no guia de meta."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
        
    config = get_config()
    api_key = config.get("groq_api_key") or config.get("gemini_api_key") or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="Chave API do Groq não configurada nas Configurações.")
        
    # Carrega dados do personagem e o contexto de guias
    build_data = parse_character_build_data(game_id, char_name)
    if not build_data.get("raw"):
        return {"suggestions": ["Nenhum dado de Roster/Build encontrado para este personagem. Faça a sincronização primeiro na aba do jogo."]}
        
    # Carrega o guia de metagame
    guide_context = ""
    guides_dir = f"{game_id}/guias_prydwen" if game_id in ["hsr", "zzz"] else f"{game_id}/guias_kqm"
    if os.path.exists(guides_dir):
        safe_fn = char_name.lower().replace(" ", "_") + ".md"
        guide_path = os.path.join(guides_dir, safe_fn)
        if os.path.exists(guide_path):
            try:
                with open(guide_path, "r", encoding="utf-8") as f:
                    guide_context = f.read()[:3000] # Limita tamanho do guia
            except Exception:
                pass
                
    rag = GroqRAG(api_key=api_key)
    prompt = (
        f"Você é um coach especializado de {game_id.upper()}. Dê exatamente 3 sugestões de melhorias curtas, diretas e acionáveis "
        f"para a build de {char_name} com base na build atual e nas recomendações de metagame.\n\n"
        f"Build atual do jogador:\n{build_data['raw']}\n\n"
        f"Guia de Metagame de referência:\n{guide_context if guide_context else 'Não disponível. Sugira com base nas melhores práticas do jogo.'}\n\n"
        f"Responda apenas em formato JSON com uma lista de strings sob a chave 'suggestions'. Exemplo:\n"
        f"{{\"suggestions\": [\"1. Trocar a bota por velocidade\", \"2. Focar em taxa crítica nos substatus\", \"3. Usar o conjunto de 4 peças de quebra\"]}}"
    )
    
    try:
        completion = rag.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "Você responde estritamente em formato JSON válido, contendo apenas a chave 'suggestions'."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=250
        )
        if completion and completion.choices:
            resp = completion.choices[0].message.content
            return json.loads(resp)
    except Exception as e:
        print(f"Erro ao gerar otimização IA com GPT-OSS 120B: {e}")
        # Fallback para Llama
        try:
            completion = rag.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Você responde estritamente em formato JSON válido, contendo apenas a chave 'suggestions'."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=250
            )
            if completion and completion.choices:
                return json.loads(completion.choices[0].message.content)
        except Exception:
            pass
            
    return {"suggestions": [
        "1. Priorizar os atributos principais recomendados nas peças de Relíquias/Artefatos.",
        "2. Tentar alcançar os bônus máximos de conjunto equipando 4 peças ideais.",
        "3. Fortalecer o nível das relíquias equipadas para maximizar os atributos base."
    ]}

# ==========================================
# DOWNLOAD AUTOMÁTICO DE ÍCONES DE ELEMENTOS
# ==========================================

ELEMENT_ICONS_MAP = {
    "hsr": {
        "fire": "https://static.wikia.nocookie.net/houkai-star-rail/images/c/ca/Element_Fire.png",
        "ice": "https://static.wikia.nocookie.net/houkai-star-rail/images/1/15/Element_Ice.png",
        "physical": "https://static.wikia.nocookie.net/houkai-star-rail/images/2/29/Element_Physical.png",
        "wind": "https://static.wikia.nocookie.net/houkai-star-rail/images/7/77/Element_Wind.png",
        "lightning": "https://static.wikia.nocookie.net/houkai-star-rail/images/e/e0/Element_Lightning.png",
        "quantum": "https://static.wikia.nocookie.net/houkai-star-rail/images/d/df/Element_Quantum.png",
        "imaginary": "https://static.wikia.nocookie.net/houkai-star-rail/images/a/ab/Element_Imaginary.png",
    },
    "genshin": {
        "pyro": "https://static.wikia.nocookie.net/genshin-impact/images/a/ad/Element_Pyro.png",
        "hydro": "https://static.wikia.nocookie.net/genshin-impact/images/3/35/Element_Hydro.png",
        "anemo": "https://static.wikia.nocookie.net/genshin-impact/images/a/a4/Element_Anemo.png",
        "electro": "https://static.wikia.nocookie.net/genshin-impact/images/7/73/Element_Electro.png",
        "dendro": "https://static.wikia.nocookie.net/genshin-impact/images/f/f4/Element_Dendro.png",
        "cryo": "https://static.wikia.nocookie.net/genshin-impact/images/8/88/Element_Cryo.png",
        "geo": "https://static.wikia.nocookie.net/genshin-impact/images/4/4a/Element_Geo.png",
    },
    "zzz": {
        "fire": "https://static.wikia.nocookie.net/zenless-zone-zero/images/d/df/Attribute_Fire.png",
        "electric": "https://static.wikia.nocookie.net/zenless-zone-zero/images/5/52/Attribute_Electric.png",
        "ice": "https://static.wikia.nocookie.net/zenless-zone-zero/images/c/c3/Attribute_Ice.png",
        "physical": "https://static.wikia.nocookie.net/zenless-zone-zero/images/1/15/Attribute_Physical.png",
        "ether": "https://static.wikia.nocookie.net/zenless-zone-zero/images/e/ea/Attribute_Ether.png",
    }
}

def get_resource_path(relative_path):
    """Obtém o caminho absoluto para o recurso, compatível com desenvolvimento e executável do PyInstaller."""
    import sys
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

def download_element_icons():
    """Garante que todos os ícones oficiais de elementos dos 3 jogos estejam em cache local."""
    import requests
    target_dir = get_resource_path(os.path.join("assets", "elements"))
    os.makedirs(target_dir, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0"}
    for game, elements in ELEMENT_ICONS_MAP.items():
        for elem_name, url in elements.items():
            path = os.path.join(target_dir, f"{game}_{elem_name}.png")
            if not os.path.exists(path):
                try:
                    res = requests.get(url, headers=headers, timeout=10)
                    if res.status_code == 200:
                        with open(path, "wb") as f:
                            f.write(res.content)
                        print(f"[INFO] Elemento em cache local: {game}_{elem_name}.png")
                except Exception as e:
                    print(f"[WARN] Falha ao baixar ícone de elemento {game}_{elem_name}: {e}")

# Executa download de elementos no carregamento do módulo
download_element_icons()

# ==========================================
# NOVOS ENDPOINTS: GACHA, FARM, TRASH, BREAKPOINTS & AUDIT
# ==========================================

class GachaRequest(BaseModel):
    game_id: Optional[str] = "genshin"
    current_pity: Optional[int] = 0
    is_guaranteed: Optional[bool] = False
    pulls_available: Optional[int] = 0
    target_copies: Optional[int] = 1

@app.post("/api/gacha/calculate")
async def calculate_gacha_sim(req: GachaRequest):
    """Executa simulação Monte Carlo para probabilidade de obtenção em banners gacha."""
    from build_calculator import simulate_gacha_probabilities
    try:
        res = simulate_gacha_probabilities(
            game_id=req.game_id,
            current_pity=req.current_pity,
            is_guaranteed=req.is_guaranteed,
            pulls_available=req.pulls_available,
            target_copies=req.target_copies
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/farming/today/{game_id}")
async def get_farming_today(game_id: str, selected_chars: Optional[str] = None):
    """Retorna o calendário de farm do dia atual + sugestões com base nos seus personagens."""
    from build_calculator import get_daily_farm_recommendations
    try:
        roster_data = await get_roster(game_id)
        selected_list = [s.strip() for s in selected_chars.split(",") if s.strip()] if selected_chars else None
        res = get_daily_farm_recommendations(game_id=game_id, roster=roster_data, selected_chars=selected_list)
        return res
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/relics/trash/{game_id}")
async def get_trash_relics(game_id: str):
    """Analisa o inventário de relíquias salvas contra o metagame e identifica peças lixo."""
    from build_calculator import find_trash_relics, get_meta_data
    try:
        roster = database.get_roster_data(game_id=game_id)
        all_relics = []
        for char in roster:
            for r in char.get("relics", []):
                all_relics.append({
                    "name": r.get("name", ""),
                    "slot": r.get("slot", ""),
                    "main_stat": r.get("main", r.get("main_stat", "")),
                    "substats": [{"name": s.strip()} for s in str(r.get("sub", "")).split(",") if s.strip()]
                })
        meta = get_meta_data(game_id)
        res = find_trash_relics(game_id=game_id, relics=all_relics, meta_data=meta)
        return res
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


class BreakpointRequest(BaseModel):
    game_id: Optional[str] = "hsr"
    char_name: str
    stats: Dict[str, Any]

@app.post("/api/stats/breakpoints")
async def check_breakpoints(req: BreakpointRequest):
    """Verifica limiares de velocidade, EHR, Recarga e Crítico do personagem."""
    from build_calculator import calculate_stat_breakpoints
    try:
        res = calculate_stat_breakpoints(game_id=req.game_id, char_name=req.char_name, stats=req.stats)
        return res
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit/{game_id}")
async def get_account_audit(game_id: str):
    """Retorna relatório de auditoria de saúde da conta + Tier List dos seus personagens."""
    try:
        roster = await get_roster(game_id)
        if not roster:
            return {"total_characters": 0, "avg_rv": 0.0, "tier_list": {"S+": [], "S": [], "A": [], "B": [], "C/D": []}, "sss_count": 0, "s_count": 0}
            
        tier_list = {"S+": [], "S": [], "A": [], "B": [], "C/D": []}
        scores = []
        
        for char in roster:
            name = char.get("name")
            icon = char.get("icon")
            rarity = char.get("rarity", 4)
            level = char.get("level", 1)
            score = char.get("overall_score", 0.0)
            grade = char.get("overall_grade", "D")
            scores.append(score)
            
            char_entry = {
                "name": name,
                "icon": icon,
                "rarity": rarity,
                "level": level,
                "score": score,
                "grade": grade
            }
            
            if score >= 85.0 or grade in ["SSS", "SS"]:
                tier_list["S+"].append(char_entry)
            elif score >= 65.0 or grade == "S":
                tier_list["S"].append(char_entry)
            elif score >= 45.0 or grade == "A":
                tier_list["A"].append(char_entry)
            elif score >= 30.0 or grade == "B":
                tier_list["B"].append(char_entry)
            else:
                tier_list["C/D"].append(char_entry)
                
        avg_rv = round(sum(scores) / len(scores), 1) if scores else 0.0
        
        return {
            "game_id": game_id,
            "total_characters": len(roster),
            "avg_rv": avg_rv,
            "tier_list": tier_list,
            "sss_count": sum(1 for s in scores if s >= 90.0),
            "s_count": sum(1 for s in scores if s >= 60.0)
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/accounts")
async def get_saved_accounts():
    """Retorna todas as contas salvas para alternância multi-conta."""
    try:
        return database.get_all_saved_accounts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================


static_dir = get_resource_path("static")
assets_dir = get_resource_path("assets")

os.makedirs(static_dir, exist_ok=True)
os.makedirs(assets_dir, exist_ok=True)

app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import time
    
    def open_browser():
        time.sleep(3.5)
        print("[INFO] Abrindo Cabeça de Droid no navegador...")
        webbrowser.open("http://127.0.0.1:8000")
        
    # Inicia a thread para abrir o navegador em background
    threading.Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
