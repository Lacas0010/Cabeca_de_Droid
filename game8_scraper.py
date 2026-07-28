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
                header = row.find(["th", "td"])
                if not header:
                    continue
                
                header_text = header.get_text(strip=True).lower()
                value_cell = header.find_next_sibling("td")
                
                if not value_cell:
                    continue
                
                # Extraindo Main Stats
                if "sands of eon" in header_text or "sands" in header_text:
                    if not build_data["main_stats"]["sands"]:
                        build_data["main_stats"]["sands"] = normalize_extracted_text(value_cell.text)
                
                elif "goblet of eonothem" in header_text or "goblet" in header_text:
                    if not build_data["main_stats"]["goblet"]:
                        build_data["main_stats"]["goblet"] = normalize_extracted_text(value_cell.text)
                
                elif "circlet of logos" in header_text or "circlet" in header_text:
                    if not build_data["main_stats"]["circlet"]:
                        build_data["main_stats"]["circlet"] = normalize_extracted_text(value_cell.text)
                
                # Extraindo Substats
                elif "sub-stats" in header_text or "substats" in header_text or "sub stat" in header_text:
                    if not build_data["substats_priority"]:
                        build_data["substats_priority"] = normalize_extracted_text(value_cell.text)

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
