import os
import json
import asyncio
import time
import re
import requests
from bs4 import BeautifulSoup

# Importa as ferramentas do motor principal
from build_calculator import fetch_master_id_list, sanitize_substats, normalize_stat_name

# URL Mestra de todos os personagens de Genshin no Game8 (Tier List / Roster Completo)
GAME8_INDEX_URL = "https://game8.co/games/Genshin-Impact/archives/297465"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

def clean_character_name(raw_name: str) -> str:
    """Limpa o nome do Game8 para cruzar com o nosso banco de IDs"""
    name = raw_name.lower().strip()
    
    # Remove sufixos como " Build", " Guide", " Best Weapons", etc.
    name = re.sub(r'\s+(build|guide|best|weapons?|artifacts?|teams?|materials?|rarity|tier\s+list|banner|lore|profile).*$', '', name)
    
    # Tratamentos específicos para aliases populares do Game8
    if "raiden" in name: return "raiden"
    if "tartaglia" in name or "childe" in name: return "tartaglia"
    if "ayato" in name: return "kamisato ayato"
    if "itto" in name: return "arataki itto"
    if "yae" in name: return "yae miko"
    if "hu tao" in name: return "hu tao"
    if "kokomi" in name: return "sangonomiya kokomi"
    if "shinobu" in name: return "kuki shinobu"
    if "heizou" in name: return "shikanoin heizou"
    if "sara" in name and "kujou" in name: return "kujou sara"
    if "yunjin" in name or "yun jin" in name: return "yun jin"
    if "mizuki" in name: return "yumemizuki mizuki"
    if ("wanderer" in name or "scaramouche" in name) and "troupe" not in name: return "wanderer"
    if "traveler" in name or "viajante" in name: return "traveler"
    
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

def get_all_character_urls_sync(session, master_ids, logger_cb=None):
    """Raspa o index do Game8 e retorna um dicionário {char_id: url_do_guia}"""
    msg = "[INFO] Acessando a lista mestre de personagens do Game8..."
    if logger_cb: logger_cb(msg)
    else: print(msg)
    
    r = session.get(GAME8_INDEX_URL, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Falha ao acessar index do Game8 (Status HTTP {r.status_code})")
        
    soup = BeautifulSoup(r.text, 'html.parser')
    char_urls = {}
    
    # Busca todos os links na página
    for a in soup.find_all('a', href=True):
        href = a['href']
        name_raw = a.get_text(strip=True)
        
        # Filtra apenas links que vão para guias (archives) e têm nome
        if '/games/Genshin-Impact/archives/' in href and name_raw:
            if any(x in name_raw.lower() for x in ["tier list", "build", "guide", "update", "materials", "weapon", "artifact", "map", "codes", "quest", "boss", "story", "comment", "livestream", "version", "banner", "lore", "profile", "quiz", "survey", "tier maker", "troupe", "set"]):
                continue
                
            name_clean = clean_character_name(name_raw)
            
            if name_clean in master_ids:
                char_id = master_ids[name_clean]
                if href.startswith('/'):
                    href = f"https://game8.co{href}"
                char_urls[char_id] = {"name": name_raw.title(), "url": href}
                
    msg = f"[INFO] Foram encontrados {len(char_urls)} guias de personagens válidos para raspar."
    if logger_cb: logger_cb(msg)
    else: print(msg)
    return char_urls

def parse_stat_priority_table(table):
    """Extrai Main Stats e Substats de uma tabela de Stat Priority do Game8."""
    main_stats = {"sands": [], "goblet": [], "circlet": []}
    substats = []
    
    rows = table.find_all("tr")
    expecting_main_stats = False
    
    for row in rows:
        cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"]) if c.get_text(" ", strip=True)]
        if not cells:
            continue
        
        row_str = " ".join(cells)
        row_lower = row_str.lower()
        
        if row_lower.startswith("summary"):
            continue
            
        if expecting_main_stats:
            if len(cells) >= 3:
                main_stats["sands"] = clean_and_normalize_genshin_stat(cells[0])
                main_stats["goblet"] = clean_and_normalize_genshin_stat(cells[1])
                main_stats["circlet"] = clean_and_normalize_genshin_stat(cells[2])
            expecting_main_stats = False
            continue
            
        if "stat priority" in row_lower and len(cells) == 1:
            expecting_main_stats = True
            continue
        elif "stat priority" in row_lower and len(cells) >= 4:
            main_stats["sands"] = clean_and_normalize_genshin_stat(cells[1])
            main_stats["goblet"] = clean_and_normalize_genshin_stat(cells[2])
            main_stats["circlet"] = clean_and_normalize_genshin_stat(cells[3])
            
        # Suporte a Main Stats em layout vertical
        for i, c in enumerate(cells):
            cl = c.lower()
            if "sands" in cl and not main_stats["sands"]:
                val = cells[i+1] if i+1 < len(cells) else c
                main_stats["sands"] = clean_and_normalize_genshin_stat(val)
            elif "goblet" in cl and not main_stats["goblet"]:
                val = cells[i+1] if i+1 < len(cells) else c
                main_stats["goblet"] = clean_and_normalize_genshin_stat(val)
            elif "circlet" in cl and not main_stats["circlet"]:
                val = cells[i+1] if i+1 < len(cells) else c
                main_stats["circlet"] = clean_and_normalize_genshin_stat(val)
                
        # Substats
        if not substats and ("substat" in row_lower or "sub-stat" in row_lower or "sub stat" in row_lower):
            val_text = row_str.split(":", 1)[1] if ":" in row_str else row_str
            val_text_clean = re.sub(r'\b(artifact|substats?|sub-stats?|sub|stats?|priority)\b', '', val_text, flags=re.IGNORECASE)
            raw_tokens = re.split(r'[>/|,\n]|\bor\b', val_text_clean)
            cleaned = []
            for tok in raw_tokens:
                norm = normalize_stat_name(tok.strip())
                if norm and norm not in cleaned:
                    cleaned.append(norm)
            substats = sanitize_substats(cleaned, "genshin")
            
    return main_stats, substats

def scrape_game8_character_sync(session, char_name, url, logger_cb=None):
    """Raspa as tabelas de Builds, Artefatos, Armas e Substats de um personagem específico via requests"""
    try:
        r = session.get(url, timeout=20)
        if r.status_code != 200:
            if logger_cb: logger_cb(f"[AVISO] HTTP {r.status_code} para {url}", "WARN")
            return None
            
        soup = BeautifulSoup(r.text, 'html.parser')

        build_data = {
            "main_stats": {"sands": [], "goblet": [], "circlet": []},
            "substats_priority": [],
            "best_weapons": [],
            "best_artifacts": []
        }

        tables = soup.find_all("table")
        for table in tables:
            t_text = table.get_text(" ", strip=True)
            t_lower = t_text.lower()
            rows = table.find_all("tr")
            if not rows:
                continue
            
            first_row_text = rows[0].get_text(" ", strip=True).lower()

            # 1. Tabela de Stat Priority / Artifact Main Stats
            if "stat priority" in t_lower or "artifact main stats" in t_lower or "substats" in t_lower:
                m_stats, s_priority = parse_stat_priority_table(table)
                if m_stats["sands"] and not build_data["main_stats"]["sands"]:
                    build_data["main_stats"]["sands"] = m_stats["sands"]
                if m_stats["goblet"] and not build_data["main_stats"]["goblet"]:
                    build_data["main_stats"]["goblet"] = m_stats["goblet"]
                if m_stats["circlet"] and not build_data["main_stats"]["circlet"]:
                    build_data["main_stats"]["circlet"] = m_stats["circlet"]
                if s_priority and not build_data["substats_priority"]:
                    build_data["substats_priority"] = s_priority

            # 2. Tabela de Armas Recomendadas
            if "recommended weapons" in first_row_text or "weapon information" in first_row_text:
                for row in rows[1:]:
                    cells = row.find_all(["td", "th"])
                    if not cells:
                        continue
                    c0 = cells[0].get_text(" ", strip=True)
                    c0_clean = re.sub(r'^\d+\.\s*', '', c0).strip()
                    if c0_clean and len(c0_clean) > 2 and not any(x in c0_clean.lower() for x in ['recommended weapons', 'how to get', 'weapon', 'gacha', 'crafted', 'event', 'battle pass', '1st', '2nd', '3rd', 'replacement']):
                        if c0_clean not in build_data["best_weapons"]:
                            build_data["best_weapons"].append(c0_clean)

            # 3. Tabela de Artefatos Recomendados
            if "artifact bonuses" in first_row_text or "best artifact sets" in first_row_text or "alternate artifacts" in first_row_text:
                for row in rows[1:]:
                    cells = row.find_all(["td", "th"])
                    if not cells:
                        continue
                    for c in cells:
                        for b in c.find_all(["b", "strong", "a"]):
                            b_text = b.get_text(strip=True)
                            b_clean = re.sub(r'\s*x[24]', '', b_text, flags=re.IGNORECASE).strip()
                            if len(b_clean) > 3 and not any(x in b_clean.lower() for x in ['best-in-slot', 'substitute', 'artifact', 'bonus', '2-pc', '4-pc', 'set', 'main', 'sub', 'stat', 'how to', 'guide', 'view', '1st', '2nd', '3rd', 'summary']):
                                if b_clean not in build_data["best_artifacts"]:
                                    build_data["best_artifacts"].append(b_clean)

        # Fallback de células individuais caso os parsers de tabela não preencham tudo
        if not build_data["main_stats"]["sands"] or not build_data["substats_priority"]:
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all(["th", "td"])
                    if not cells:
                        continue
                    for idx, cell in enumerate(cells):
                        cell_text = cell.get_text(" ", strip=True)
                        cell_text_lower = cell_text.lower()
                        
                        if any(x in cell_text_lower for x in ["sands of eon", "sands:"]):
                            if not build_data["main_stats"]["sands"]:
                                val_part = cell_text.split(":", 1)[1] if ":" in cell_text else (cells[idx+1].get_text(" ", strip=True) if idx+1 < len(cells) else "")
                                stats = clean_and_normalize_genshin_stat(val_part)
                                if stats: build_data["main_stats"]["sands"] = stats

                        if any(x in cell_text_lower for x in ["goblet of eonothem", "goblet:"]):
                            if not build_data["main_stats"]["goblet"]:
                                val_part = cell_text.split(":", 1)[1] if ":" in cell_text else (cells[idx+1].get_text(" ", strip=True) if idx+1 < len(cells) else "")
                                stats = clean_and_normalize_genshin_stat(val_part)
                                if stats: build_data["main_stats"]["goblet"] = stats

                        if any(x in cell_text_lower for x in ["circlet of logos", "circlet:"]):
                            if not build_data["main_stats"]["circlet"]:
                                val_part = cell_text.split(":", 1)[1] if ":" in cell_text else (cells[idx+1].get_text(" ", strip=True) if idx+1 < len(cells) else "")
                                stats = clean_and_normalize_genshin_stat(val_part)
                                if stats: build_data["main_stats"]["circlet"] = stats

                        if any(x in cell_text_lower for x in ["sub-stat", "substat"]):
                            if not build_data["substats_priority"]:
                                val_part = cell_text.split(":", 1)[1] if ":" in cell_text else (cells[idx+1].get_text(" ", strip=True) if idx+1 < len(cells) else "")
                                subs = normalize_extracted_text(val_part)
                                if subs: build_data["substats_priority"] = sanitize_substats(subs, "genshin")

        return build_data
    except Exception as e:
        msg = f"[ERRO] Falha ao raspar {char_name}: {e}"
        if logger_cb: logger_cb(msg, "WARN")
        else: print(msg)
        return None

async def scrape_game8_character(page_or_dummy, char_name, url, logger_cb=None):
    """Wrapper assíncrono para compatibilidade com assinaturas existentes"""
    session = requests.Session()
    session.headers.update(HEADERS)
    return await asyncio.to_thread(scrape_game8_character_sync, session, char_name, url, logger_cb)

async def scrape_genshin_game8_builds(logger_cb=None):
    """Executa a raspagem automatizada dos guias do Game8 e atualiza genshin/meta_data_genshin.json"""
    master_ids = fetch_master_id_list("genshin")
    
    session = requests.Session()
    session.headers.update(HEADERS)

    characters_to_scrape = await asyncio.to_thread(get_all_character_urls_sync, session, master_ids, logger_cb)
    
    meta_db = {}
    total = len(characters_to_scrape)
    count = 0

    for char_id, info in characters_to_scrape.items():
        count += 1
        msg = f"[Scraping] Processando {info['name']} (ID: {char_id}) ({count}/{total})..."
        prog_val = count / max(total, 1)
        if logger_cb: logger_cb(msg, "INFO", prog_val)
        else: print(msg)
        
        data = await asyncio.to_thread(scrape_game8_character_sync, session, info['name'], info['url'], logger_cb)
        
        if data:
            clean_subs = sanitize_substats(data["substats_priority"], "genshin")
            
            meta_db[str(char_id)] = {
                "main_stats": data["main_stats"],
                "substats_priority": clean_subs,
                "best_weapons": data.get("best_weapons", []),
                "best_artifacts": data.get("best_artifacts", []),
                "general_benchmarks": {},
                "name": info['name']
            }
        
        # Pausa leve para respeitar o servidor do Game8
        await asyncio.sleep(0.5)

    output_path = "genshin/meta_data_genshin.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(meta_db, f, indent=4, ensure_ascii=False)
        
    final_msg = f"[SUCESSO] Construção automatizada concluída! {len(meta_db)} personagens salvos em {output_path}!"
    if logger_cb: logger_cb(final_msg, "SUCCESS", 1.0)
    else: print(final_msg)
    return meta_db

def run_genshin_game8_builds(logger_cb=None):
    """Invoca o scraper em contexto assíncrono ou síncrono"""
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return loop.create_task(scrape_genshin_game8_builds(logger_cb=logger_cb))
        else:
            return asyncio.run(scrape_genshin_game8_builds(logger_cb=logger_cb))
    except Exception as e:
        print(f"[ERRO] Executando scraper do Game8: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(scrape_genshin_game8_builds())
