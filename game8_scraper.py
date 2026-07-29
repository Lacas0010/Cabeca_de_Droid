import os
import json
import asyncio
import re
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Importa as ferramentas do motor principal da calculadora
from build_calculator import fetch_master_id_list, sanitize_substats

# URL Mestra de todos os personagens de Genshin no Game8
GAME8_INDEX_URL = "https://game8.co/games/Genshin-Impact/archives/297496"

def clean_character_name(raw_name: str) -> str:
    """Limpa o nome do Game8 para cruzar com o nosso banco de IDs"""
    name = raw_name.lower().strip()
    # Remove títulos e sobrenomes comuns que o Game8 usa
    prefixes_to_remove = ["kamisato ", "kaedehara ", "sangonomiya ", "shikanoin ", "kuki ", "arabalanq "]
    for prefix in prefixes_to_remove:
        name = name.replace(prefix, "")
    
    # Tratamentos específicos
    if "raiden" in name: return "raiden"
    if "tartaglia" in name or "childe" in name: return "tartaglia"
    if "yae" in name: return "yae"
    if "hu tao" in name: return "hutao"
    
    return name

def normalize_extracted_text(text: str) -> list:
    """Limpa o texto da tabela do Game8 e separa os atributos"""
    clean_text = re.sub(r'<[^>]+>', ' ', text)
    tokens = re.split(r'[/|,]| or ', clean_text)
    return [t.strip().lower() for t in tokens if t.strip()]

def clean_and_normalize_genshin_stat(raw_text: str) -> list:
    """
    Limpa o texto extraído da tabela do Game8 para Genshin Impact,
    removendo ruídos, números, parênteses e aplicando o mapeamento estrito.
    """
    # 1. Remove tags HTML residuais
    clean_text = re.sub(r'<[^>]+>', ' ', raw_text)
    
    # 2. Separa por delimitadores comuns (/ ou , ou : ou 'or')
    tokens = re.split(r'[/|:,]| or |\n', clean_text)
    
    normalized_stats = []
    seen = set()
    
    # Dicionário de mapeamento estrito de status válidos
    mapa_main_stats = {
        "atk": "atk_pct",
        "atk%": "atk_pct",
        "atk_pct": "atk_pct",
        "attack": "atk_pct",
        "attack%": "atk_pct",
        "atk percent": "atk_pct",
        "attack percent": "atk_pct",
        
        "hp": "hp_pct",
        "hp%": "hp_pct",
        "hp_pct": "hp_pct",
        "health": "hp_pct",
        "health%": "hp_pct",
        "hp percent": "hp_pct",
        "health percent": "hp_pct",
        
        "def": "def_pct",
        "def%": "def_pct",
        "def_pct": "def_pct",
        "defense": "def_pct",
        "defense%": "def_pct",
        "def percent": "def_pct",
        "defense percent": "def_pct",
        
        "em": "em",
        "elemental mastery": "em",
        "mastery": "em",
        
        "er": "er",
        "energy recharge": "er",
        "recharge": "er",
        "energy": "er",
        
        "crit rate": "crit_rate",
        "crit rate%": "crit_rate",
        "crit_rate": "crit_rate",
        "rate": "crit_rate",
        "crit dmg": "crit_dmg",
        "crit dmg%": "crit_dmg",
        "crit_dmg": "crit_dmg",
        
        "healing bonus": "healing_bonus",
        "healing": "healing_bonus",
        "healing%": "healing_bonus",
        "healing bonus%": "healing_bonus",
        
        "anemo dmg bonus": "anemo dmg",
        "anemo dmg": "anemo dmg",
        "anemo": "anemo dmg",
        "geo dmg bonus": "geo dmg",
        "geo dmg": "geo dmg",
        "geo": "geo dmg",
        "electro dmg bonus": "electro dmg",
        "electro dmg": "electro dmg",
        "electro": "electro dmg",
        "dendro dmg bonus": "dendro dmg",
        "dendro dmg": "dendro dmg",
        "dendro": "dendro dmg",
        "hydro dmg bonus": "hydro dmg",
        "hydro dmg": "hydro dmg",
        "hydro": "hydro dmg",
        "pyro dmg bonus": "pyro dmg",
        "pyro dmg": "pyro dmg",
        "pyro": "pyro dmg",
        "cryo dmg bonus": "cryo dmg",
        "cryo dmg": "cryo dmg",
        "cryo": "cryo dmg",
        "physical dmg bonus": "physical dmg",
        "physical dmg": "physical dmg",
        "physical": "physical dmg",
        "phys dmg": "physical dmg",
        "phys": "physical dmg",
    }
    
    # Lista de termos a serem sumariamente desconsiderados
    stop_words = {"gacha", "pull", "banner", "wish", "wish simulator", "recommended", "best", "placeholder", "sub", "main", "stat", "weapon", "artifact"}
    
    for t in tokens:
        # Remove parênteses e todo o conteúdo dentro deles (ex: "(187)", "(gacha)")
        t_clean = re.sub(r'\(.*?\)', '', t)
        
        # Remove números, pontos e símbolos de percentagem (ex: "46.6%")
        t_clean = re.sub(r'[\d%\.]+', '', t_clean)
        
        # Substitui múltiplos espaços por um único espaço
        t_clean = re.sub(r'\s+', ' ', t_clean).strip().lower()
        
        if not t_clean or t_clean in stop_words:
            continue
            
        # Tenta mapear o termo sanitizado para o nosso padrão de main stats
        mapped_stat = mapa_main_stats.get(t_clean)
        if mapped_stat and mapped_stat not in seen:
            seen.add(mapped_stat)
            normalized_stats.append(mapped_stat)
            
    return normalized_stats

async def get_all_character_urls(page, master_ids, logger_cb=None):
    """Raspa o index do Game8 e retorna um dicionário {char_id: url_do_guia}"""
    msg = "[INFO] Acessando a lista mestre de personagens do Game8..."
    if logger_cb: logger_cb(msg)
    else: print(msg)
    
    await page.goto(GAME8_INDEX_URL, wait_until="domcontentloaded", timeout=60000)
    soup = BeautifulSoup(await page.content(), 'html.parser')
    
    char_urls = {}
    
    # Busca todos os links na página
    for a in soup.find_all('a', href=True):
        href = a['href']
        name_raw = a.get_text(strip=True)
        
        # Filtra apenas links que vão para guias (archives) e têm nome
        if '/games/Genshin-Impact/archives/' in href and name_raw:
            # Ignora links genéricos que não são de personagens
            if any(x in name_raw.lower() for x in ["tier list", "build", "guide", "update", "materials", "weapon", "artifact"]):
                continue
                
            name_clean = clean_character_name(name_raw)
            
            # Se o nome raspado existir no nosso banco de IDs (master_ids)
            if name_clean in master_ids:
                char_id = master_ids[name_clean]
                if href.startswith('/'):
                    href = f"https://game8.co{href}"
                char_urls[char_id] = {"name": name_raw.title(), "url": href}
                
    msg = f"[INFO] Foram encontrados {len(char_urls)} guias de personagens válidos para raspar."
    if logger_cb: logger_cb(msg)
    else: print(msg)
    return char_urls

async def scrape_game8_character(page, char_name, url, logger_cb=None):
    """Raspa a tabela de Melhor Artefato e Substats de um personagem específico"""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        soup = BeautifulSoup(await page.content(), 'html.parser')

        build_data = {
            "main_stats": {"sands": [], "goblet": [], "circlet": []},
            "substats_priority": []
        }

        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["th", "td"])
                if not cells:
                    continue
                
                for idx, cell in enumerate(cells):
                    cell_text = cell.get_text(" ", strip=True)
                    cell_text_lower = cell_text.lower()
                    
                    # Ignorar linhas de tabelas de armas ou outras seções indesejadas
                    if "weapon" in cell_text_lower or "talents" in cell_text_lower:
                        continue
                    
                    # 1. Areias (Sands)
                    if "sands of eon" in cell_text_lower or "sands:" in cell_text_lower or (cell_text_lower == "sands" and len(cells) > 1):
                        if not build_data["main_stats"]["sands"]:
                            val_part = ""
                            if ":" in cell_text:
                                val_part = cell_text.split(":", 1)[1]
                            elif idx + 1 < len(cells):
                                val_part = cells[idx + 1].get_text(" ", strip=True)
                            if val_part:
                                build_data["main_stats"]["sands"] = clean_and_normalize_genshin_stat(val_part)
                                
                    # 2. Cálice (Goblet)
                    elif "goblet of eonothem" in cell_text_lower or "goblet:" in cell_text_lower or (cell_text_lower == "goblet" and len(cells) > 1):
                        if not build_data["main_stats"]["goblet"]:
                            val_part = ""
                            if ":" in cell_text:
                                val_part = cell_text.split(":", 1)[1]
                            elif idx + 1 < len(cells):
                                val_part = cells[idx + 1].get_text(" ", strip=True)
                            if val_part:
                                build_data["main_stats"]["goblet"] = clean_and_normalize_genshin_stat(val_part)
                                
                    # 3. Tiara (Circlet)
                    elif "circlet of logos" in cell_text_lower or "circlet:" in cell_text_lower or (cell_text_lower == "circlet" and len(cells) > 1):
                        if not build_data["main_stats"]["circlet"]:
                            val_part = ""
                            if ":" in cell_text:
                                val_part = cell_text.split(":", 1)[1]
                            elif idx + 1 < len(cells):
                                val_part = cells[idx + 1].get_text(" ", strip=True)
                            if val_part:
                                build_data["main_stats"]["circlet"] = clean_and_normalize_genshin_stat(val_part)
                                
                    # 4. Substats
                    elif "sub-stats" in cell_text_lower or "substats" in cell_text_lower or "sub stat" in cell_text_lower:
                        if not build_data["substats_priority"]:
                            val_part = ""
                            if ":" in cell_text:
                                val_part = cell_text.split(":", 1)[1]
                            elif idx + 1 < len(cells):
                                val_part = cells[idx + 1].get_text(" ", strip=True)
                            if val_part:
                                build_data["substats_priority"] = normalize_extracted_text(val_part)

        return build_data
    except Exception as e:
        msg = f"[ERRO] Falha ao raspar {char_name}: {e}"
        if logger_cb: logger_cb(msg, "WARN")
        else: print(msg)
        return None

async def scrape_genshin_game8_builds(logger_cb=None):
    """Executa a raspagem automatizada dos guias do Game8 e atualiza genshin/meta_data_genshin.json"""
    master_ids = fetch_master_id_list("genshin")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        characters_to_scrape = await get_all_character_urls(page, master_ids, logger_cb=logger_cb)
        
        meta_db = {}
        total = len(characters_to_scrape)
        count = 0

        for char_id, info in characters_to_scrape.items():
            count += 1
            msg = f"[Scraping] Processando {info['name']} (ID: {char_id}) ({count}/{total})..."
            prog_val = count / max(total, 1)
            if logger_cb: logger_cb(msg, "INFO", prog_val)
            else: print(msg)
            
            data = await scrape_game8_character(page, info['name'], info['url'], logger_cb=logger_cb)
            
            if data:
                clean_subs = sanitize_substats(data["substats_priority"], "genshin")
                
                meta_db[str(char_id)] = {
                    "main_stats": data["main_stats"],
                    "substats_priority": clean_subs,
                    "general_benchmarks": {},
                    "name": info['name']
                }
            
            await asyncio.sleep(1)

        await browser.close()

        output_path = "genshin/meta_data_genshin.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(meta_db, f, indent=4, ensure_ascii=False)
            
        final_msg = f"[SUCESSO] Construção automatizada concluída! {len(meta_db)} personagens salvos em {output_path}!"
        if logger_cb: logger_cb(final_msg, "SUCCESS", 1.0)
        else: print(final_msg)
        return meta_db

def run_genshin_game8_builds(logger_cb=None):
    """Invoca o scraper assíncrono em contexto síncrono para integração simples"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.ensure_future(scrape_genshin_game8_builds(logger_cb=logger_cb))
        else:
            return loop.run_until_complete(scrape_genshin_game8_builds(logger_cb=logger_cb))
    except Exception:
        return asyncio.run(scrape_genshin_game8_builds(logger_cb=logger_cb))

async def main():
    await scrape_genshin_game8_builds()

if __name__ == "__main__":
    asyncio.run(main())
