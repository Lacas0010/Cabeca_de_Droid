import os
import json
import asyncio
import datetime
import threading
import time
import traceback
from typing import Dict, Any, Optional

import database
from core.config import get_cookies, get_config
from log_sanitizer import sanitize_log
from extractor import MultiGameExtractor
from scraper_prydwen import PrydwenScraper
from scraper_zzz import PrydwenZZZScraper
from scraper_genshin import PrydwenGenshinScraper
from scraper_meta import PrydwenMetaScraper

# Estado global para progresso da sincronização
sync_status: Dict[str, Dict[str, Any]] = {
    "zzz": {"running": False, "progress": 0.0, "message": "Aguardando...", "logs": []},
    "genshin": {"running": False, "progress": 0.0, "message": "Aguardando...", "logs": []},
    "hsr": {"running": False, "progress": 0.0, "message": "Aguardando...", "logs": []},
}

def log_game(game_id: str, msg: str, level: str = "INFO", progresso: Optional[float] = None) -> None:
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    clean_msg = sanitize_log(msg)
    formatted_msg = f"[{timestamp}] [{level}] {clean_msg}"
    print(formatted_msg)
    
    status = sync_status[game_id]
    status["logs"].append(formatted_msg)
    status["message"] = f"{level == 'ERROR' and ' ' or ''}{clean_msg}"
    if progresso is not None:
        status["progress"] = progresso

def bundle_guides(guides_dir: str, output_file: str, game_name: str) -> None:
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

def _bg_sync_thread(game_id: str, run_roster: bool, run_guides: bool, run_meta: bool) -> None:
    game_id = game_id.lower()
    log_game(game_id, f"Iniciando sincronização de {game_id.upper()}...", "INFO", progresso=0.01)
    sync_status[game_id]["running"] = True
    
    try:
        # 0. ATUALIZAÇÃO AUTOMÁTICA UPSTREAM (Datamines & Manifestos Públicos)
        try:
            from static_data_manager import static_data_manager
            log_game(game_id, f"Verificando atualizações de manifestos upstream ({game_id.upper()})...", "INFO", progresso=0.03)
            up_res = static_data_manager.sync_upstream_data(game_id)
            g_info = up_res.get(game_id, {})
            log_game(game_id, f"Catálogo atualizado: {g_info.get('character_count', 0)} entidades ({g_info.get('source', 'Local')})", "INFO", progresso=0.05)
        except Exception as up_err:
            log_game(game_id, f"Aviso na sincronização upstream: {up_err}", "WARN")

        # 1. EXTRAÇÃO DE ROSTER
        if run_roster:
            cookies = get_cookies()
            if not cookies:
                log_game(game_id, "Cookies da HoYoLAB ausentes em cookies.json. Configure-os na aba Configurações.", "ERROR", progresso=0.0)
                sync_status[game_id]["running"] = False
                return
                
            log_game(game_id, "Conectando à API HoYoLAB para extrair Roster...", "INFO", progresso=0.08)
            try:
                extractor = MultiGameExtractor(cookies)
                # Como rodamos em thread síncrona do FastAPI background, criamos um event loop próprio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                filename = loop.run_until_complete(extractor.extrair_jogo(game_id))
                loop.close()
                log_game(game_id, f"Roster extraído e salvo com sucesso em {filename}!", "SUCCESS", progresso=0.25)
                
                roster_data = database.get_roster_data(game_id)
                if roster_data:
                    first_uid = roster_data[0].get("uid", "000000000") if isinstance(roster_data, list) and roster_data else "000000000"
                    database.save_account_snapshot(uid=first_uid, game_id=game_id, roster_data=roster_data)
                    log_game(game_id, "Snapshot de evolução da conta registrado no histórico!", "INFO", progresso=0.26)
            except Exception as roster_err:
                traceback.print_exc()
                log_game(game_id, f"Falha ao extrair Roster: {roster_err}", "ERROR")

        # 2. EXTRAÇÃO DE GUIAS
        if run_guides:
            log_game(game_id, "Iniciando busca de guias no meta-hub...", "INFO", progresso=0.28)
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
                    log_game(game_id, "Buscando personagens Genshin Impact no Prydwen...", "INFO", progresso=0.30)
                    scraper = PrydwenGenshinScraper()
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
                    log_game(game_id, "Guias de Genshin baixados com sucesso!", "SUCCESS", progresso=0.82)
                    log_game(game_id, "Consolidando biblioteca de guias de Genshin...", "INFO", progresso=0.84)
                    bundle_guides("genshin/guias", "genshin/todos_os_guias_genshin.md", "Genshin Impact")
                except Exception as scraper_err:
                    traceback.print_exc()
                    log_game(game_id, f"Erro ao obter guias Genshin: {scraper_err}", "ERROR")

        # 2.5 VERIFICAÇÃO AUTOMÁTICA DE GUIAS DAY-1 PARA PERSONAGENS DO ROSTER
        try:
            roster_data = database.get_roster_data(game_id)
            if roster_data:
                from services.ai_build_generator import AIBuildGenerator
                for r_char in roster_data:
                    c_name = r_char.get("name", "")
                    c_elem = r_char.get("element", "")
                    if c_name:
                        AIBuildGenerator.get_or_generate_guide(game_id, c_name, c_elem)
        except Exception as auto_guide_err:
            print(f"[AUTO-GUIDE] Aviso na verificação de guias Day-1: {auto_guide_err}")


        # 3. EXTRAÇÃO DE META E ENDGAME
        if run_meta:
            log_game(game_id, "Iniciando sincronização do meta...", "INFO", progresso=0.86)
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
                    log_game(game_id, "Coletando meta e Tier List de Genshin do Prydwen...", "INFO", progresso=0.90)
                    scraper = PrydwenGenshinScraper()
                    filepath = scraper.save_meta_to_markdown()
                    log_game(game_id, "Meta de Genshin do Prydwen salvo com sucesso!", "SUCCESS", progresso=0.98)
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

def start_auto_sync_scheduler() -> None:
    """Inicia thread do agendador automático de sincronização diária."""
    def auto_sync_loop():
        # Aguarda 15 segundos antes da primeira verificação
        time.sleep(15)
        while True:
            try:
                config = get_config()
                if config.get("auto_sync_enabled", True):
                    scheduled_time = config.get("auto_sync_time", "04:00").strip()
                    now = datetime.datetime.now()
                    current_time_str = now.strftime("%H:%M")
                    current_date_str = now.strftime("%Y-%m-%d")
                    last_run_date = config.get("last_auto_sync_date", "")

                    if current_time_str == scheduled_time and last_run_date != current_date_str:
                        print(f"[AUTO-SYNC] Horário programado ({scheduled_time}) atingido! Iniciando atualização automática diária de Rosters e Guias...")
                        
                        run_roster = config.get("auto_sync_roster", True)
                        run_guides = config.get("auto_sync_guides", True)
                        cookies = get_cookies()

                        if cookies:
                            for game_id in ["hsr", "genshin", "zzz"]:
                                try:
                                    print(f"[AUTO-SYNC] Sincronizando {game_id.upper()} em segundo plano...")
                                    _bg_sync_thread(game_id, run_roster=run_roster, run_guides=run_guides, run_meta=False)
                                except Exception as game_err:
                                    print(f"[AUTO-SYNC] Erro ao sincronizar {game_id}: {game_err}")

                            config["last_auto_sync_date"] = current_date_str
                            try:
                                with open("config.json", "w", encoding="utf-8") as f:
                                    json.dump(config, f, indent=4)
                            except Exception:
                                pass
                            
                            print(f"[AUTO-SYNC] Sincronização automática diária concluída para a data {current_date_str}!")
                        else:
                            print("[AUTO-SYNC] Cookies HoYoLAB não configurados. Sincronização automática em espera.")

            except Exception as sched_err:
                print(f"[AUTO-SYNC] Erro no loop do agendador: {sched_err}")

            time.sleep(30)

    threading.Thread(target=auto_sync_loop, daemon=True).start()
