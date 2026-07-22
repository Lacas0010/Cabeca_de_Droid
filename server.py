import os
import re
import json
import asyncio
import threading
import traceback
import datetime
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

# Importações dos módulos do projeto
from auth import capturar_cookies_hoyolab
from extractor import MultiGameExtractor
from scraper_prydwen import PrydwenScraper
from scraper_zzz import PrydwenZZZScraper
from scraper_meta import PrydwenMetaScraper
from scraper_kqm import KQMScraper
from scraper_genshin_meta import GenshinMetaScraper
from groq_rag import GroqRAG

app = FastAPI(title="Cabeça de Droid API", version="3.0")

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
                    log_game(game_id, "Coletando meta de Genshin do Game8...", "INFO", progresso=0.90)
                    from scraper_genshin_meta import GenshinMetaScraper
                    meta_scraper = GenshinMetaScraper(output_path="genshin/meta_kqm_genshin.md")
                    
                    def genshin_meta_callback(msg, level="INFO"):
                        log_game(game_id, msg, level, progresso=0.95)
                        
                    meta_scraper.run_full_scrape(logger_cb=genshin_meta_callback)
                    log_game(game_id, "Meta de Genshin salvo com sucesso!", "SUCCESS", progresso=0.98)
                except Exception as meta_err:
                    traceback.print_exc()
                    log_game(game_id, f"Falha ao obter meta Genshin: {meta_err}", "ERROR")

        log_game(game_id, "Sincronização concluída com sucesso!", "SUCCESS", progresso=1.0)
    except Exception as general_err:
        log_game(game_id, f"Erro crítico na sincronização: {general_err}", "ERROR", progresso=0.0)
    finally:
        sync_status[game_id]["running"] = False

# ==========================================
# ROTAS DA API REST
# ==========================================

@app.get("/api/roster/{game_id}")
async def get_roster(game_id: str):
    """Retorna os dados dos personagens salvos no roster local."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido. Escolha 'hsr', 'genshin' ou 'zzz'.")
        
    json_path = f"{game_id}/roster_data_{game_id}.json"
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                return data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao carregar banco de dados local: {e}")
            
    # Caso não exista JSON, tenta buscar do Markdown (.md)
    md_path = f"{game_id}/roster_{game_id}.md"
    if os.path.exists(md_path):
        return []
        
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

@app.post("/api/chat")
async def chat_interaction(req: ChatRequest):
    """Endpoint do Chat RAG Local (Groq) que injeta dados de roster, guias e meta."""
    config = get_config()
    api_key = config.get("groq_api_key") or config.get("gemini_api_key") or os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        return {"response": "Erro: Chave API do Groq não configurada. Salve-a na aba Configurações."}
        
    try:
        rag = GroqRAG(api_key=api_key)
        context = rag.load_game_context(req.game_id, req.message)
        
        history_list = []
        for h in req.history:
            history_list.append({
                "role": h.role,
                "text": h.text
            })
            
        reply = rag.ask_assistant(
            prompt_usuario=req.message,
            contexto_rag=context,
            historico_chat=history_list
        )
        return {"response": reply}
    except Exception as chat_err:
        traceback.print_exc()
        return {"response": f"Ocorreu um erro no processador do chat: {chat_err}"}

# ==========================================
# PARSER DE DETALHES DE BUILD DE PERSONAGEM
# ==========================================

def get_character_build_detail(game_id: str, char_name: str) -> str:
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
        return data
        
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
        data["pieces"].append({
            "slot": slot.strip(),
            "name": p_name.strip(),
            "main": main_s.strip(),
            "sub": sub_s.strip()
        })
    return data

@app.get("/api/overview")
async def get_overview():
    """Gera dados resumidos consolidados dos 3 jogos."""
    overview = {}
    
    # 1. Honkai Star Rail
    hsr_info = {"active": False, "uid": "Não sincronizado", "level": "N/A", "char_count": 0, "five_stars": 0}
    hsr_json_path = "hsr/roster_data_hsr.json"
    hsr_md_path = "hsr/roster_hsr.md"
    if os.path.exists(hsr_json_path):
        try:
            with open(hsr_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                hsr_info["char_count"] = len(data)
                hsr_info["five_stars"] = sum(1 for c in data if c.get("rarity") == 5)
                hsr_info["active"] = True
        except Exception:
            pass
    if os.path.exists(hsr_md_path):
        try:
            with open(hsr_md_path, "r", encoding="utf-8") as f:
                content = f.read()
            m_uid = re.search(r'UID:\s*(\d+)', content)
            if m_uid: hsr_info["uid"] = m_uid.group(1)
            m_lvl = re.search(r'Nível de Desbravamento:\*\* (\d+)', content)
            if m_lvl: hsr_info["level"] = m_lvl.group(1)
        except Exception:
            pass
    overview["hsr"] = hsr_info

    # 2. Genshin Impact
    genshin_info = {"active": False, "uid": "Não sincronizado", "level": "N/A", "char_count": 0, "five_stars": 0}
    genshin_json_path = "genshin/roster_data_genshin.json"
    genshin_md_path = "genshin/roster_genshin.md"
    if os.path.exists(genshin_json_path):
        try:
            with open(genshin_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                genshin_info["char_count"] = len(data)
                genshin_info["five_stars"] = sum(1 for c in data if c.get("rarity") == 5)
                genshin_info["active"] = True
        except Exception:
            pass
    if os.path.exists(genshin_md_path):
        try:
            with open(genshin_md_path, "r", encoding="utf-8") as f:
                content = f.read()
            m_uid = re.search(r'UID:\*\*\s*(\d+)', content)
            if m_uid: genshin_info["uid"] = m_uid.group(1)
            m_lvl = re.search(r'Rank de Aventura:\*\*\s*(\d+)', content)
            if m_lvl: genshin_info["level"] = m_lvl.group(1)
        except Exception:
            pass
    overview["genshin"] = genshin_info

    # 3. Zenless Zone Zero
    zzz_info = {"active": False, "uid": "Não sincronizado", "level": "N/A", "char_count": 0, "five_stars": 0}
    zzz_json_path = "zzz/roster_data_zzz.json"
    zzz_md_path = "zzz/roster_zzz.md"
    if os.path.exists(zzz_json_path):
        try:
            with open(zzz_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                zzz_info["char_count"] = len(data)
                zzz_info["five_stars"] = sum(1 for c in data if str(c.get("rarity")) in ["5", "S"])
                zzz_info["active"] = True
        except Exception:
            pass
    if os.path.exists(zzz_md_path):
        try:
            with open(zzz_md_path, "r", encoding="utf-8") as f:
                content = f.read()
            m_uid = re.search(r'UID:\*\*\s*(\d+)', content)
            if m_uid: zzz_info["uid"] = m_uid.group(1)
            m_lvl = re.search(r'Nível de Intermediário:\*\*\s*(\d+)', content)
            if m_lvl: zzz_info["level"] = m_lvl.group(1)
        except Exception:
            pass
    overview["zzz"] = zzz_info

    return overview

@app.get("/api/build/{game_id}/{char_name}")
async def get_build_detail(game_id: str, char_name: str):
    """Retorna os dados detalhados da build de um personagem, parseando o MD consolidado."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
    return parse_character_build_data(game_id, char_name)

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
            temperature=0.4,
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
                temperature=0.4,
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

def download_element_icons():
    """Garante que todos os ícones oficiais de elementos dos 3 jogos estejam em cache local."""
    import requests
    os.makedirs("assets/elements", exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0"}
    for game, elements in ELEMENT_ICONS_MAP.items():
        for elem_name, url in elements.items():
            path = f"assets/elements/{game}_{elem_name}.png"
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

os.makedirs("static", exist_ok=True)
os.makedirs("assets", exist_ok=True)

app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/", StaticFiles(directory="static", html=True), name="static")

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
    
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
