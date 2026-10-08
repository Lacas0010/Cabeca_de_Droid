import os
import re
import json
import urllib.parse
from typing import List, Dict, Any, Optional

import database
from core.config import get_resource_path
from services.media_service import get_raw_url
from services.translation_service import traduzir_item
from extractor import clean_relic_name, sanitize_stat_name, clean_hoyoverse_desc
from build_calculator import (
    score_relic,
    get_meta_data,
    extract_weights_from_guide,
    normalize_char_name,
)
import meta_comparator

# Carrega elementos conhecidos de static_data
def _load_character_elements() -> Dict[str, Dict[str, str]]:
    elements_file = get_resource_path(os.path.join("static_data", "character_elements.json"))
    if os.path.exists(elements_file):
        try:
            with open(elements_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Erro ao ler character_elements.json: {e}")
    return {"genshin": {}, "zzz": {}}

CHARACTER_ELEMENTS = _load_character_elements()

_GENSHIN_CONST_CACHE = None
_HSR_EIDOLON_CACHE = None
_ALIASES_CACHE = None
_MANIFESTS_CACHE = {}
_HSR_SKILLS_CACHE = None
_GENSHIN_SKILLS_CACHE = None
_ZZZ_SKILLS_CACHE = None

def _get_skills_cache(game_id: str) -> Dict[str, Any]:
    global _HSR_SKILLS_CACHE, _GENSHIN_SKILLS_CACHE, _ZZZ_SKILLS_CACHE
    if game_id == "hsr":
        if _HSR_SKILLS_CACHE is None:
            p = get_resource_path(os.path.join("static_data", "hsr_skills.json"))
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        _HSR_SKILLS_CACHE = json.load(f)
                except Exception:
                    _HSR_SKILLS_CACHE = {}
            else:
                _HSR_SKILLS_CACHE = {}
        return _HSR_SKILLS_CACHE
    elif game_id == "genshin":
        if _GENSHIN_SKILLS_CACHE is None:
            p = get_resource_path(os.path.join("static_data", "genshin_skills.json"))
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        _GENSHIN_SKILLS_CACHE = json.load(f)
                except Exception:
                    _GENSHIN_SKILLS_CACHE = {}
            else:
                _GENSHIN_SKILLS_CACHE = {}
        return _GENSHIN_SKILLS_CACHE
    elif game_id == "zzz":
        if _ZZZ_SKILLS_CACHE is None:
            p = get_resource_path(os.path.join("static_data", "zzz_skills.json"))
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        _ZZZ_SKILLS_CACHE = json.load(f)
                except Exception:
                    _ZZZ_SKILLS_CACHE = {}
            else:
                _ZZZ_SKILLS_CACHE = {}
        return _ZZZ_SKILLS_CACHE
    return {}

def enrich_character_skills(game_id: str, char_name: str, skills: list) -> list:
    """Enriquece as habilidades com ícones oficiais e descrições completas detalhadas."""
    if not skills:
        return []
    enriched = []
    cache = _get_skills_cache(game_id)
    c_norm = normalize_char_name(char_name) if char_name else ""
    c_clean = re.sub(r'[^a-z0-9_]', '', (char_name or "").lower().replace(' ', '_'))
    
    for idx, s in enumerate(skills):
        sk = dict(s)
        s_name = (sk.get("name") or "").strip()
        s_lower = s_name.lower()
        
        # 1. Ícones oficiais para ZZZ
        if game_id == "zzz":
            if not sk.get("icon") or "sparkles" in sk.get("icon", "") or "magic" in sk.get("icon", "") or sk.get("icon") == "":
                if "básico" in s_lower or "basico" in s_lower or idx == 0:
                    sk["icon"] = "/assets/skills/zzz/basic_attack.png"
                elif "esquiva" in s_lower:
                    sk["icon"] = "/assets/skills/zzz/dodge.png"
                elif "suporte" in s_lower or "assist" in s_lower:
                    sk["icon"] = "/assets/skills/zzz/assist.png"
                elif "especial" in s_lower:
                    sk["icon"] = "/assets/skills/zzz/special.png"
                elif "cadeia" in s_lower or "suprema" in s_lower:
                    sk["icon"] = "/assets/skills/zzz/ultimate.png"
                elif "passiva" in s_lower or "núcleo" in s_lower or "principal" in s_lower:
                    sk["icon"] = "/assets/skills/zzz/core.png"
                else:
                    sk["icon"] = "/assets/skills/zzz/basic_attack.png"
                    
        # 2. Descrições completas
        if not sk.get("desc") or sk.get("desc") == "":
            if game_id == "hsr":
                entry = cache.get(s_lower)
                if not entry:
                    for k, v in cache.items():
                        if k in s_lower or s_lower in k:
                            entry = v
                            break
                if entry:
                    sk["desc"] = entry.get("desc", "")
                    if (not sk.get("icon") or "magic" in sk.get("icon", "")) and entry.get("icon"):
                        sk["icon"] = entry.get("icon")
            elif game_id == "genshin":
                by_name = cache.get("by_name", {})
                by_char = cache.get("by_char", {})
                entry = by_name.get(s_lower)
                if not entry:
                    char_talents = by_char.get(c_clean) or by_char.get(c_norm) or []
                    if char_talents and idx < len(char_talents):
                        entry = char_talents[idx]
                if entry:
                    sk["desc"] = entry.get("desc", "")
            elif game_id == "zzz":
                by_name = cache.get("by_name", {})
                by_char = cache.get("by_char", {})
                entry = by_name.get(s_lower)
                if not entry:
                    clean_name = re.sub(r'^(Ataque Básico|Ataque Especial|Ataque Especial Reforçado|Esquiva|Ataque em Cadeia|Passiva Principal|Passiva de Núcleo|Assistência Reativa|Ataque de Suporte|Suporte):\s*', '', s_name, flags=re.IGNORECASE).strip().lower()
                    entry = by_name.get(clean_name)
                if not entry:
                    char_skills_guide = by_char.get(c_clean) or by_char.get(c_norm) or []
                    if char_skills_guide:
                        for c_sk in char_skills_guide:
                            c_sk_lower = c_sk["name"].lower()
                            if s_lower in c_sk_lower or c_sk_lower in s_lower:
                                entry = c_sk
                                break
                            cats = [("básico", "básico"), ("especial", "especial"), ("esquiva", "esquiva"), ("cadeia", "cadeia"), ("passiva", "passiva"), ("suporte", "suporte"), ("assist", "assist")]
                            for cat_a, cat_b in cats:
                                if cat_a in s_lower and cat_b in c_sk_lower:
                                    entry = c_sk
                                    break
                            if entry:
                                break
                if entry:
                    sk["desc"] = entry.get("desc", "")
                    
        if sk.get("desc"):
            sk["desc"] = clean_hoyoverse_desc(sk["desc"])
        enriched.append(sk)
    return enriched

def _get_character_aliases() -> Dict[str, Dict[str, str]]:
    global _ALIASES_CACHE
    if _ALIASES_CACHE is None:
        p = get_resource_path(os.path.join("static_data", "character_aliases.json"))
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    _ALIASES_CACHE = json.load(f)
            except Exception:
                _ALIASES_CACHE = {}
        else:
            _ALIASES_CACHE = {}
    return _ALIASES_CACHE

def _get_manifest(game_id: str) -> Dict[str, Any]:
    global _MANIFESTS_CACHE
    if game_id not in _MANIFESTS_CACHE:
        p = get_resource_path(os.path.join("static_data", f"{game_id}_manifest.json"))
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    _MANIFESTS_CACHE[game_id] = json.load(f).get("characters", {})
            except Exception:
                _MANIFESTS_CACHE[game_id] = {}
        else:
            _MANIFESTS_CACHE[game_id] = {}
    return _MANIFESTS_CACHE[game_id]

# Mapa de sinônimos universais comuns (PT/EN) para ID base
_COMMON_SYNONYMS = {
    "genshin": {
        "childe": "10000033",
        "tartaglia": "10000033",
        "shogun raiden": "10000052",
        "raiden shogun": "10000052",
        "raiden": "10000052",
        "wanderer": "10000075",
        "andarilho": "10000075",
        "scaramouche": "10000075",
        "baizhu": "10000082",
        "furina": "10000089",
        "neuvillette": "10000087",
        "xianyun": "10000093",
        "arlecchino": "10000096",
        "mavuika": "10000106",
        "citlali": "10000107",
        "xilonen": "10000103",
        "chasca": "10000104"
    },
    "hsr": {
        "firefly": "1310",
        "vaga-lume": "1310",
        "vagalume": "1310",
        "luciernaga": "1310",
        "march 7th": "1001",
        "7 de março": "1001",
        "7demarco": "1001",
        "acheron": "1308",
        "aqueronte": "1308",
        "robin": "1309",
        "robin - summeretto": "1512",
        "robin summeretto": "1512",
        "feixiao": "1220",
        "aventurine": "1304",
        "aventurina": "1304",
        "sparkle": "1306",
        "dan heng il": "1213",
        "imbibitor lunae": "1213",
        "black swan": "1307",
        "cisne negro": "1307",
        "the herta": "1401",
        "a herta": "1401",
        "tingyun • fugue": "1225",
        "fuga": "1225"
    }
}

def fetch_fandom_shards_for_character(char_name: str, char_id: str = None) -> List[Dict[str, Any]]:
    """Busca dinamicamente fragmentos de eidolons na API da Fandom para novos personagens não catalogados."""
    if not char_name:
        return []
    clean_name = re.sub(r'[\(\)]', '', char_name).strip()
    candidates = [
        clean_name,
        clean_name.replace(" ", "_"),
        clean_name.title(),
        clean_name.title().replace(" ", "_")
    ]
    for c_try in candidates:
        try:
            titles = [f"File:Character {c_try} Eidolon {i}.png" for i in range(1, 7)]
            titles_str = urllib.parse.quote("|".join(titles), safe="|:")
            url = f"https://honkai-star-rail.fandom.com/api.php?action=query&titles={titles_str}&prop=imageinfo&iiprop=url&format=json"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})
                shards = {}
                for pid, p in pages.items():
                    if "imageinfo" in p and p["imageinfo"]:
                        t = p.get("title", "")
                        m = re.search(r'Eidolon\s*(\d+)', t, re.IGNORECASE)
                        if m:
                            shards[int(m.group(1))] = p["imageinfo"][0]["url"]
                if len(shards) >= 1:
                    ranks = []
                    for pos in range(1, 7):
                        s_url = shards.get(pos, "")
                        ranks.append({
                            "pos": pos,
                            "name": f"Eidolon {pos}",
                            "desc": "",
                            "shard_icon": s_url,
                            "icon": s_url
                        })
                    return ranks
        except Exception:
            continue
    return []

def get_static_ranks_for_character(game_id: str, char_id: str = None, char_name: str = None, element: str = None) -> List[Dict[str, Any]]:
    """Carrega dados e ícones estáticos de Constelações (Genshin) e Eidolons (HSR) em alta definição."""
    global _GENSHIN_CONST_CACHE, _HSR_EIDOLON_CACHE
    aliases = _get_character_aliases().get(game_id, {})
    manifest = _get_manifest(game_id)
    synonyms = _COMMON_SYNONYMS.get(game_id, {})
    
    if game_id == "genshin":
        if _GENSHIN_CONST_CACHE is None:
            p = get_resource_path(os.path.join("static_data", "genshin_constellations.json"))
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        _GENSHIN_CONST_CACHE = json.load(f)
                except Exception:
                    _GENSHIN_CONST_CACHE = {}
            else:
                _GENSHIN_CONST_CACHE = {}
        
        db = _GENSHIN_CONST_CACHE
        res = None
        if char_id and str(char_id) in db:
            res = db[str(char_id)]
        elif char_name:
            c_norm = normalize_char_name(char_name)
            c_lower = char_name.lower().strip()
            
            # 1. Checa sinônimos diretos
            syn_id = synonyms.get(c_lower) or synonyms.get(c_norm)
            if syn_id and str(syn_id) in db:
                return [dict(item) for item in db[str(syn_id)]]
                
            # 2. Checa manifest
            man_entry = manifest.get(c_lower) or manifest.get(c_norm) or manifest.get(c_lower.replace(" ", "_"))
            if man_entry:
                hid = man_entry.get("hoyolab_id") or man_entry.get("id")
                if hid and str(hid) in db:
                    return [dict(item) for item in db[str(hid)]]
            
            alias_val = aliases.get(c_lower) or aliases.get(c_norm) or ""
            candidates = [c_norm, c_lower]
            if alias_val:
                candidates.extend([alias_val, normalize_char_name(alias_val), alias_val.replace("_", " ")])
            
            for cand in candidates:
                if cand in db:
                    res = db[cand]
                    break
            
            if not res:
                # Substring e palavra chave
                for k, v in db.items():
                    if len(k) >= 3 and (k in c_norm or c_norm in k or (alias_val and (k in alias_val or alias_val in k))):
                        res = v
                        break
        if res:
            return [dict(item) for item in res]
            
    elif game_id == "hsr":
        if _HSR_EIDOLON_CACHE is None:
            p = get_resource_path(os.path.join("static_data", "hsr_eidolons.json"))
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        _HSR_EIDOLON_CACHE = json.load(f)
                except Exception:
                    _HSR_EIDOLON_CACHE = {}
            else:
                _HSR_EIDOLON_CACHE = {}
                
        db = _HSR_EIDOLON_CACHE
        res = None
        if char_id and str(char_id) in db:
            res = db[str(char_id)]
        elif char_name:
            c_norm = normalize_char_name(char_name)
            c_lower = char_name.lower().strip()
            
            # 1. Checa sinônimos diretos
            syn_id = synonyms.get(c_lower) or synonyms.get(c_norm)
            if syn_id and str(syn_id) in db:
                return [dict(item) for item in db[str(syn_id)]]
                
            # 2. Checa manifest
            man_entry = manifest.get(c_lower) or manifest.get(c_norm) or manifest.get(c_lower.replace(" ", "_"))
            if man_entry:
                hid = man_entry.get("hoyolab_id") or man_entry.get("id")
                if hid and str(hid) in db:
                    return [dict(item) for item in db[str(hid)]]
            
            alias_val = aliases.get(c_lower) or aliases.get(c_norm) or ""
            candidates = [c_norm, c_lower]
            if alias_val:
                candidates.extend([alias_val, normalize_char_name(alias_val), alias_val.replace("_", " ")])
            
            for cand in candidates:
                if cand in db:
                    res = db[cand]
                    break
            
            if not res:
                for k, v in db.items():
                    if len(k) >= 3 and (k in c_norm or c_norm in k or (alias_val and (k in alias_val or alias_val in k))):
                        res = v
                        break

        # Se não encontrou no cache local, tenta buscar automaticamente na API para personagens recém-lançados
        if not res and char_name:
            auto_ranks = fetch_fandom_shards_for_character(char_name, char_id)
            if auto_ranks:
                res = auto_ranks
                try:
                    if char_id:
                        _HSR_EIDOLON_CACHE[str(char_id)] = auto_ranks
                    _HSR_EIDOLON_CACHE[char_name.lower().strip()] = auto_ranks
                    p = get_resource_path(os.path.join("static_data", "hsr_eidolons.json"))
                    with open(p, "w", encoding="utf-8") as f:
                        json.dump(_HSR_EIDOLON_CACHE, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass

        if res:
            ranks_list = [dict(item) for item in res]
            shards_dir = get_resource_path(os.path.join("assets", "shards", "hsr"))
            c_norm = normalize_char_name(char_name) if char_name else ""
            c_clean = re.sub(r'[^a-z0-9_]', '', (char_name or "").lower().replace(' ', '_'))
            for rk in ranks_list:
                pos = rk.get("pos", 1)
                candidates = [
                    f"{c_clean}_{pos}.png",
                    f"{c_norm}_{pos}.png",
                    f"{char_id}_{pos}.png" if char_id else ""
                ]
                for cand in candidates:
                    if cand and os.path.exists(os.path.join(shards_dir, cand)):
                        rk["icon"] = f"/assets/shards/hsr/{cand}"
                        rk["shard_icon"] = f"/assets/shards/hsr/{cand}"
                        break
            return ranks_list
            
    elif game_id == "zzz":
        ranks_list = []
        c_clean = re.sub(r'[^a-z0-9_]', '', (char_name or "").lower().replace(' ', '_'))
        focus_path = f"assets/mindscapes/zzz/focus/{c_clean}.png"
        has_focus = os.path.exists(get_resource_path(focus_path))
        for p in range(1, 7):
            icon_url = f"/assets/mindscapes/zzz/focus/{c_clean}.png" if has_focus else f"/assets/mindscapes/zzz/m{p}.png"
            ranks_list.append({
                "pos": p,
                "name": f"Cinema Mental {p}",
                "icon": icon_url,
                "desc": ""
            })
        return ranks_list

    return []

def parse_roster_md_fallback(game_id: str) -> List[Dict[str, Any]]:
    """Fallback de parsing a partir do arquivo Markdown se o banco SQLite estiver vazio."""
    md_path = f"{game_id}/roster_{game_id}.md"
    chars = []
    if not os.path.exists(md_path):
        return chars

    genshin_elements = CHARACTER_ELEMENTS.get("genshin", {})
    zzz_elements = CHARACTER_ELEMENTS.get("zzz", {})

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

def get_hsr_effective_id(char: Any) -> str:
    """Detecta com precisão o ID efetivo (incluindo skins 1501..1515, 1414) para Honkai: Star Rail."""
    if isinstance(char, dict):
        c_name = str(char.get("name") or "")
        c_id = str(char.get("id") or char.get("character_id") or "")
        c_icon = str(char.get("icon") or "")
        c_gacha = str(char.get("gacha_art") or "")
        costumes = char.get("costumes") or char.get("skins") or char.get("outfits") or []
        costume_id = char.get("costume_id") or char.get("skin_id") or char.get("outfit_id")
    else:
        c_name = str(getattr(char, "name", ""))
        c_id = str(getattr(char, "id", ""))
        c_icon = str(getattr(char, "icon", getattr(char, "image", "")))
        c_gacha = str(getattr(char, "gacha_art", ""))
        costumes = getattr(char, "costumes", getattr(char, "skins", getattr(char, "outfits", []))) or []
        costume_id = getattr(char, "costume_id", getattr(char, "skin_id", getattr(char, "outfit_id", None)))

    # 1. Se costume_id direto estiver presente
    if costume_id and str(costume_id).isdigit():
        return str(costume_id)

    # 2. Se costumes list estiver presente na estrutura, pega o ID do primeiro costume
    if costumes and isinstance(costumes, list) and len(costumes) > 0:
        first_costume = costumes[0]
        if isinstance(first_costume, (int, str)) and str(first_costume).isdigit():
            return str(first_costume)
        c_c_id = getattr(first_costume, "id", None) if not isinstance(first_costume, dict) else first_costume.get("id")
        if c_c_id and str(c_c_id).isdigit():
            return str(c_c_id)

    check_str = f"{c_name} {c_id} {c_icon} {c_gacha}".lower()
    
    # 3. Busca por ID de skin explícito nas strings (ex: 1512, 1510, 1506, 1414, etc.)
    skin_match = re.search(r'\b(150[1-9]|151[0-5]|1414)\b', check_str)
    if skin_match:
        return skin_match.group(1)
        
    # 4. Busca por sufixos ou nomes de skins
    if "summeretto" in check_str or "robin summer" in check_str or "robin verão" in check_str:
        return "1512"
    if "himeko - nova" in check_str or "himeko nova" in check_str:
        return "1510"
    if "999" in check_str or "loba prateada nv." in check_str:
        return "1506"
    if "permansor" in check_str:
        return "1414" if "terrae" in check_str else "1505"
    if "veraneio" in check_str:
        return "1513"
    if "noite de inverno" in check_str or "winter" in check_str or "sparxie" in check_str:
        return "1501"
    if "evanescia" in check_str:
        return "1505"
    if "mortenax" in check_str:
        return "1507"
    if "tohsaka" in check_str:
        return "1508"
    if "gilgamesh" in check_str:
        return "1509"
        
    return c_id

async def get_roster(game_id: str) -> List[Dict[str, Any]]:
    """Retorna e enriquece os dados dos personagens salvos no roster local."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise ValueError("Jogo inválido. Escolha 'hsr', 'genshin' ou 'zzz'.")
        
    data = None
    # 1. Tenta carregar do SQLite primeiro
    try:
        data = database.get_roster_data(game_id)
    except Exception as e:
        print(f"Aviso ao carregar roster do SQLite para {game_id}: {e}")
        
    # 2. Se não carregou do SQLite, tenta do JSON
    if not data:
        json_path = f"{game_id}/roster_data_{game_id}.json"
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
            except Exception as e:
                raise RuntimeError(f"Erro ao carregar banco de dados local: {e}")

    # 3. Fallback de emergência APENAS se SQLite e JSON estiverem totalmente vazios
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

            # Garante fallback de gacha_art em HD para HSR (Skins e Eidolons screen art), ZZZ e skins do Genshin
            if game_id == "hsr":
                orig_gacha = char.get("gacha_art") or ""
                raw_gacha = get_raw_url(orig_gacha)
                char_id_val = get_hsr_effective_id(char) or str(char.get("id") or char.get("character_id") or "")
                if char_id_val:
                    char["id"] = char_id_val
                    char["character_id"] = char_id_val
                    eidolon_url = f"https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/character_preview/{char_id_val}.png"
                    portrait_url = f"https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/character_portrait/{char_id_val}.png"
                    char["eidolon_art"] = eidolon_url
                    
                    if "avatar_skin_image" in raw_gacha:
                        char["portrait"] = raw_gacha
                        char["splash_art"] = raw_gacha
                        char["gacha_art"] = raw_gacha
                    elif char_id_val in ["1505", "1501"] or "evanescia" in str(char.get("name", "")).lower() or "sparxie" in str(char.get("name", "")).lower():
                        skin_id = "1505" if (char_id_val == "1505" or "evanescia" in str(char.get("name", "")).lower()) else "1501"
                        hoyolab_skin = f"https://act-webstatic.hoyoverse.com/game_record/hkrpg/custom/avatar_skin_image/{skin_id}@2x.png"
                        char["portrait"] = hoyolab_skin
                        char["splash_art"] = hoyolab_skin
                        char["gacha_art"] = hoyolab_skin
                    else:
                        char["portrait"] = portrait_url
                        char["splash_art"] = portrait_url
                        char["gacha_art"] = orig_gacha if orig_gacha and "avatar_image" in orig_gacha else portrait_url
            elif game_id == "zzz":
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
            if char.get("eidolon_art"):
                raw_eid = get_raw_url(char["eidolon_art"])
                if raw_eid.startswith("http"):
                    char["eidolon_art"] = f"/api/proxy_image?url={urllib.parse.quote(raw_eid, safe='')}"
            if char.get("portrait"):
                raw_port = get_raw_url(char["portrait"])
                if raw_port.startswith("http"):
                    char["portrait"] = f"/api/proxy_image?url={urllib.parse.quote(raw_port, safe='')}"
            if char.get("splash_art"):
                raw_spl = get_raw_url(char["splash_art"])
                if raw_spl.startswith("http"):
                    char["splash_art"] = f"/api/proxy_image?url={urllib.parse.quote(raw_spl, safe='')}"
            if isinstance(char.get("weapon"), dict) and char["weapon"].get("icon"):
                raw_w_icon = get_raw_url(char["weapon"]["icon"])
                if raw_w_icon.startswith("http"):
                    char["weapon"]["icon"] = f"/api/proxy_image?url={urllib.parse.quote(raw_w_icon, safe='')}"

            # Enriquece e aplica proxy aos ícones das habilidades (skills)
            skills = char.get("skills") or []
            for sk in skills:
                if sk.get("icon"):
                    raw_s_icon = get_raw_url(sk["icon"])
                    if raw_s_icon.startswith("http"):
                        sk["icon"] = f"/api/proxy_image?url={urllib.parse.quote(raw_s_icon, safe='')}"
            char["skills"] = skills

            # Enriquece e aplica proxy aos ícones de constelações / eidolons / mindscapes (ranks)
            ranks = char.get("ranks") or char.get("constellations") or char.get("mindscapes") or []
            c_name = char.get("name") or ""
            char_id_val = str(char.get("id") or char.get("character_id") or "")
            char_elem = str(char.get("element") or "").lower()
            rank_str_val = char.get("rank_str", "C0")
            m_rank = re.search(r'\d+', str(rank_str_val))
            char_rank_num = int(m_rank.group(0)) if m_rank else 0
            
            static_ranks = get_static_ranks_for_character(game_id, char_id_val, c_name, char_elem)
            
            if not ranks:
                name_prefix = "Constelação" if game_id == "genshin" else ("Cinema Mental" if game_id == "zzz" else "Eidolon")
                ranks = []
                for p in range(1, 7):
                    s_rk = static_ranks[p - 1] if len(static_ranks) >= p else {}
                    rk_icon = s_rk.get("icon", "")
                    rk_name = s_rk.get("name", f"{name_prefix} {p}")
                    if not rk_icon and char_elem:
                        rk_icon = f"/assets/elements/{game_id}_{char_elem}.png"
                    ranks.append({
                        "pos": p,
                        "name": rk_name,
                        "icon": rk_icon,
                        "desc": s_rk.get("desc", ""),
                        "is_unlocked": p <= char_rank_num
                    })
            else:
                for idx, rk in enumerate(ranks):
                    if len(static_ranks) > idx:
                        if not rk.get("icon") or rk.get("icon") == "" or (game_id == "hsr" and static_ranks[idx].get("icon")):
                            rk["icon"] = static_ranks[idx]["icon"]
                        if not rk.get("name") or "Constelação" in rk.get("name", "") or re.match(r'^(Eidolon|Mindscape|Constelação)\s*\d+$', rk.get("name", ""), re.IGNORECASE):
                            if static_ranks[idx].get("name"):
                                rk["name"] = static_ranks[idx]["name"]
                        if not rk.get("desc") and static_ranks[idx].get("desc"):
                            rk["desc"] = static_ranks[idx]["desc"]
                    if not rk.get("icon") and char_elem:
                        rk["icon"] = f"/assets/elements/{game_id}_{char_elem}.png"

            for rk in ranks:
                if rk.get("icon"):
                    raw_rk_icon = get_raw_url(rk["icon"])
                    if raw_rk_icon.startswith("http"):
                        rk["icon"] = f"/api/proxy_image?url={urllib.parse.quote(raw_rk_icon, safe='')}"
            char["ranks"] = ranks
            char["constellations"] = ranks
            char["mindscapes"] = ranks

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

def get_character_build_detail(game_id: str, char_name: str) -> str:
    """Busca o detalhe textual da build do personagem a partir do SQLite ou do arquivo Markdown."""
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
        pattern = rf'(\*\*(?:Personagem|Agente):\*\*\s*{re.escape(char_name)}.*?)(?=\n\*\*(?:Personagem|Agente):\*\*|\n## |\Z)'
        match = re.search(pattern, content, re.DOTALL | re.I)
        if match:
            return match.group(1).strip()
    except Exception as e:
        print(f"Erro ao buscar detalhes da build de {char_name}: {e}")
    return ""

def parse_character_build_data(game_id: str, char_name: str) -> Dict[str, Any]:
    """Extrai com precisão máxima os dados da build atual do jogador consultando primariamente o SQLite."""
    data = {
        "name": char_name,
        "weapon": "Não informado",
        "weapon_clean": "",
        "sets": [],
        "stats": {},
        "pieces": []
    }
    
    # 1. Tenta buscar no banco SQLite (fonte mais rica e estruturada)
    char_db = None
    try:
        roster = database.get_roster_data(game_id)
        c_norm = normalize_char_name(char_name)
        c_lower = char_name.lower().strip()
        syn_id = _COMMON_SYNONYMS.get(game_id, {}).get(c_lower) or _COMMON_SYNONYMS.get(game_id, {}).get(c_norm)
        
        for c in roster:
            cand_name = c.get("name", "")
            cand_norm = normalize_char_name(cand_name)
            cand_lower = cand_name.lower().strip()
            cand_id = str(c.get("id") or c.get("character_id") or "")
            
            if cand_norm == c_norm or cand_lower == c_lower:
                char_db = c
                break
            if syn_id and (cand_id == str(syn_id) or cand_norm == str(syn_id)):
                char_db = c
                break
            if len(c_norm) >= 3 and (c_norm in cand_norm or cand_norm in c_norm or c_lower in cand_lower or cand_lower in c_lower):
                char_db = c
                break
    except Exception as e:
        print(f"[WARN] Erro ao consultar SQLite para {char_name}: {e}")

    if char_db:
        # Arma
        w = char_db.get("weapon")
        if isinstance(w, dict) and w.get("name"):
            lvl = w.get("level", 1)
            rnk = w.get("rank", 1)
            data["weapon"] = f"{w['name']} (Nv. {lvl}, R{rnk})"
            data["weapon_clean"] = w["name"]
        elif isinstance(w, str) and w:
            data["weapon"] = w
            data["weapon_clean"] = re.sub(r'\s*\([^)]*\)', '', w).strip()
            
        # Combat Stats
        if char_db.get("stats"):
            data["stats"] = dict(char_db["stats"])
            
        # Peças de Relíquias / Artefatos / Discos
        for r in char_db.get("relics", []):
            slot = r.get("slot", "")
            slot_clean = slot
            if game_id == "genshin":
                if slot in ["1", "flor", "flower"]: slot_clean = "Flor"
                elif slot in ["2", "pena", "plume"]: slot_clean = "Pena"
                elif slot in ["3", "areia", "sands"]: slot_clean = "Areia"
                elif slot in ["4", "copo", "calice", "goblet"]: slot_clean = "Copo"
                elif slot in ["5", "tiara", "coroa", "circlet"]: slot_clean = "Tiara"
            elif game_id == "hsr":
                if "cabeça" in slot.lower() or slot == "1": slot_clean = "Cabeça"
                elif "mãos" in slot.lower() or slot == "2": slot_clean = "Mãos"
                elif "corpo" in slot.lower() or slot == "3": slot_clean = "Corpo"
                elif "pés" in slot.lower() or "bota" in slot.lower() or slot == "4": slot_clean = "Bota"
                elif "esfera" in slot.lower() or slot == "5": slot_clean = "Esfera"
                elif "corda" in slot.lower() or slot == "6": slot_clean = "Corda"
            elif game_id == "zzz":
                slot_clean = slot.replace("Disk", "Disco").replace("disk", "Disco").replace("slot_", "Disco ")
                
            data["pieces"].append({
                "slot": slot_clean,
                "name": r.get("name", ""),
                "main": r.get("main", ""),
                "sub": r.get("sub", ""),
                "icon": r.get("icon", "")
            })

        # Skills & Ranks (Constelações / Eidolons / Mindscapes)
        data["skills"] = char_db.get("skills", [])
        char_ranks = char_db.get("ranks", char_db.get("constellations", []))
        c_id = str(char_db.get("id") or char_db.get("character_id") or "")
        c_elem = str(char_db.get("element") or "").lower()
        c_rank_str = char_db.get("rank_str", "C0")
        m_r = re.search(r'\d+', str(c_rank_str))
        c_rank_n = int(m_r.group(0)) if m_r else 0
        
        static_ranks = get_static_ranks_for_character(game_id, c_id, char_name, c_elem)
        if not char_ranks:
            name_prefix = "Constelação" if game_id == "genshin" else ("Cinema Mental" if game_id == "zzz" else "Eidolon")
            char_ranks = []
            for p in range(1, 7):
                s_rk = static_ranks[p - 1] if len(static_ranks) >= p else {}
                rk_icon = s_rk.get("icon", "")
                rk_name = s_rk.get("name", f"{name_prefix} {p}")
                if not rk_icon and c_elem:
                    rk_icon = f"/assets/elements/{game_id}_{c_elem}.png"
                char_ranks.append({
                    "pos": p,
                    "name": rk_name,
                    "icon": rk_icon,
                    "desc": s_rk.get("desc", ""),
                    "is_unlocked": p <= c_rank_n
                })
        else:
            for idx, rk in enumerate(char_ranks):
                if len(static_ranks) > idx:
                    if not rk.get("icon") or rk.get("icon") == "" or (game_id == "hsr" and static_ranks[idx].get("icon")):
                        rk["icon"] = static_ranks[idx]["icon"]
                    if not rk.get("name") or "Constelação" in rk.get("name", "") or re.match(r'^(Eidolon|Mindscape|Constelação)\s*\d+$', rk.get("name", ""), re.IGNORECASE):
                        if static_ranks[idx].get("name"):
                            rk["name"] = static_ranks[idx]["name"]
                    if not rk.get("desc") and static_ranks[idx].get("desc"):
                        rk["desc"] = static_ranks[idx]["desc"]
                if not rk.get("icon") and c_elem:
                    rk["icon"] = f"/assets/elements/{game_id}_{c_elem}.png"

        if game_id == "zzz":
            c_clean = re.sub(r'[^a-z0-9_]', '', (char_name or "").lower().replace(' ', '_'))
            focus_path = f"assets/mindscapes/zzz/focus/{c_clean}.png"
            has_focus = os.path.exists(get_resource_path(focus_path))
            for idx, rk in enumerate(char_ranks):
                pos = rk.get("pos", idx + 1)
                if not rk.get("icon") or rk.get("icon") == "" or "/assets/elements/" in rk.get("icon", ""):
                    rk["icon"] = f"/assets/mindscapes/zzz/focus/{c_clean}.png" if has_focus else f"/assets/mindscapes/zzz/m{pos}.png"

        for rk in char_ranks:
            if rk.get("desc"):
                rk["desc"] = clean_hoyoverse_desc(rk["desc"])
            if rk.get("icon"):
                raw_rk_icon = get_raw_url(rk["icon"])
                if raw_rk_icon.startswith("http"):
                    rk["icon"] = f"/api/proxy_image?url={urllib.parse.quote(raw_rk_icon, safe='')}"

        data["skills"] = enrich_character_skills(game_id, char_name, data.get("skills", []))
        for sk in data.get("skills", []):
            if sk.get("desc"):
                sk["desc"] = clean_hoyoverse_desc(sk["desc"])

        data["ranks"] = char_ranks
        data["constellations"] = char_ranks
        data["mindscapes"] = char_ranks
        data["id"] = c_id
        data["character_id"] = c_id
        if game_id == "hsr":
            target_id = get_hsr_effective_id(char_db or {"name": char_name, "id": c_id})
            orig_gacha = (char_db.get("gacha_art") if char_db else "") or ""
            raw_gacha = get_raw_url(orig_gacha)
            if not target_id:
                c_norm = normalize_char_name(char_name)
                c_lower = char_name.lower().strip()
                target_id = _COMMON_SYNONYMS.get("hsr", {}).get(c_lower) or _COMMON_SYNONYMS.get("hsr", {}).get(c_norm) or ""
                if not target_id:
                    man_e = _get_manifest("hsr").get(c_lower) or _get_manifest("hsr").get(c_norm) or {}
                    target_id = str(man_e.get("hoyolab_id") or man_e.get("id") or "")
            if target_id:
                data["id"] = target_id
                data["character_id"] = target_id
                data["eidolon_art"] = f"/api/proxy_image?url={urllib.parse.quote(f'https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/character_preview/{target_id}.png', safe='')}"
                
                if "avatar_skin_image" in raw_gacha:
                    data["portrait"] = f"/api/proxy_image?url={urllib.parse.quote(raw_gacha, safe='')}"
                    data["splash_art"] = data["portrait"]
                    data["gacha_art"] = data["portrait"]
                elif target_id in ["1505", "1501"] or "evanescia" in char_name.lower() or "sparxie" in char_name.lower():
                    skin_id = "1505" if (target_id == "1505" or "evanescia" in char_name.lower()) else "1501"
                    hoyolab_skin = f"https://act-webstatic.hoyoverse.com/game_record/hkrpg/custom/avatar_skin_image/{skin_id}@2x.png"
                    data["portrait"] = f"/api/proxy_image?url={urllib.parse.quote(hoyolab_skin, safe='')}"
                    data["splash_art"] = data["portrait"]
                    data["gacha_art"] = data["portrait"]
                else:
                    data["portrait"] = f"/api/proxy_image?url={urllib.parse.quote(f'https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/character_portrait/{target_id}.png', safe='')}"
                    data["splash_art"] = data["portrait"]
                    data["gacha_art"] = data["portrait"]
        else:
            if char_db.get("eidolon_art"):
                data["eidolon_art"] = char_db["eidolon_art"]
            if char_db.get("gacha_art"):
                data["gacha_art"] = char_db["gacha_art"]

    # 2. Busca conjuntos (sets) ativos no roster_{game_id}.md ou roster_data_{game_id}.json
    try:
        raw_text = get_character_build_detail(game_id, char_name)
        if raw_text:
            m_s = re.search(r'-\s*\*\*(?:Relíquias|Artefatos|Discos):\*\*\s*(.*)', raw_text)
            if m_s:
                sets_raw = m_s.group(1).strip()
                data["sets"] = [s.strip() for s in sets_raw.split('+') if s.strip()]
            if not data["weapon"] or data["weapon"] == "Não informado":
                m_w = re.search(r'-\s*\*\*(?:Cone de Luz|Arma|W-Engine):\*\*\s*(.*)', raw_text)
                if m_w:
                    data["weapon"] = m_w.group(1).strip()
                    data["weapon_clean"] = re.sub(r'\s*\([^)]*\)', '', data["weapon"]).strip()
    except Exception as e:
        print(f"[WARN] Erro ao extrair conjuntos do markdown para {char_name}: {e}")

    # 3. Fallback de stats, skills e ranks do roster_data_{game_id}.json se ainda estiver vazio
    if not data["stats"] or not data.get("skills") or not data.get("ranks"):
        try:
            json_path = f"{game_id}/roster_data_{game_id}.json"
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8", errors="ignore") as jf:
                    roster_data = json.load(jf)
                char_lower = char_name.lower().strip()
                for c in roster_data:
                    if c.get("name", "").lower().strip() == char_lower:
                        if not data["stats"] and c.get("stats"):
                            data["stats"] = c["stats"]
                        if not data.get("skills") and c.get("skills"):
                            data["skills"] = c["skills"]
                        if not data.get("ranks") and (c.get("ranks") or c.get("constellations")):
                            data["ranks"] = c.get("ranks") or c.get("constellations")
                        break
        except Exception:
            pass

    if not data.get("ranks"):
        static_ranks = get_static_ranks_for_character(game_id, None, char_name, None)
        name_prefix = "Constelação" if game_id == "genshin" else ("Cinema Mental" if game_id == "zzz" else "Eidolon")
        ranks = []
        for p in range(1, 7):
            s_rk = static_ranks[p - 1] if len(static_ranks) >= p else {}
            rk_icon = s_rk.get("icon", "")
            if rk_icon.startswith("http"):
                rk_icon = f"/api/proxy_image?url={urllib.parse.quote(rk_icon, safe='')}"
            ranks.append({
                "pos": p,
                "name": s_rk.get("name", f"{name_prefix} {p}"),
                "icon": rk_icon,
                "desc": clean_hoyoverse_desc(s_rk.get("desc", "")),
                "is_unlocked": False
            })
        data["ranks"] = ranks
        data["constellations"] = ranks
        data["mindscapes"] = ranks

    return data

def parse_meta_target(game_id: str, char_name: str, element: str = "") -> Dict[str, Any]:
    """Calcula e retorna as referências do meta ideais para um personagem."""
    meta_json = get_meta_data(game_id)
    try:
        roster = database.get_roster_data(game_id)
    except Exception:
        roster = None
    return meta_comparator.parse_meta_target(
        game_id=game_id,
        char_name=char_name,
        element=element,
        meta_json=meta_json,
        roster_data=roster,
        translate_fn=traduzir_item
    )

def get_overview() -> Dict[str, Any]:
    """Gera dados resumidos consolidados dos 3 jogos mesclando SQLite e arquivos locais."""
    db_overview = {}
    try:
        db_overview = database.get_overview_data()
    except Exception as e:
        print(f"Erro ao buscar visão geral no SQLite: {e}")

    overview = {}
    for game in ["hsr", "genshin", "zzz"]:
        fallback_info = {"active": False, "uid": "Não sincronizado", "level": "N/A", "char_count": 0, "five_stars": 0}
        
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
                
                m_uid = re.search(r'UID[:\*]*\s*(\d+)', content)
                if m_uid:
                    fallback_info["uid"] = m_uid.group(1)
                    
                if game == "hsr":
                    m_lvl = re.search(r'Nível de Desbravamento[:\*]*\s*(\d+)', content)
                elif game == "genshin":
                    m_lvl = re.search(r'Rank de Aventura[:\*]*\s*(\d+)', content)
                else:  # zzz
                    m_lvl = re.search(r'Nível de Intermediário[:\*]*\s*(\d+)', content)
                    
                if m_lvl:
                    fallback_info["level"] = m_lvl.group(1)
            except Exception:
                pass

        db_game = db_overview.get(game, {})
        if db_game and db_game.get("active") and db_game.get("char_count", 0) > 0:
            overview[game] = db_game
        elif fallback_info["active"] and fallback_info.get("char_count", 0) > 0:
            overview[game] = fallback_info
        else:
            overview[game] = db_game if db_game else fallback_info
            
    return overview

async def get_account_audit(game_id: str) -> Dict[str, Any]:
    """Retorna relatório de auditoria de saúde da conta + Tier List dos seus personagens."""
    roster = await get_roster(game_id)
    if not roster:
        return {
            "game_id": game_id,
            "total_characters": 0,
            "avg_rv": 0.0,
            "tier_list": {"S+": [], "S": [], "A": [], "B": [], "C/D": []},
            "sss_count": 0,
            "s_count": 0
        }
        
    tier_list: Dict[str, List[Dict[str, Any]]] = {"S+": [], "S": [], "A": [], "B": [], "C/D": []}
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
