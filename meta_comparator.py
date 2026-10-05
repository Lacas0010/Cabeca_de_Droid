import os
import re
import json
import unicodedata
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DATA_DIR = os.path.join(BASE_DIR, "static_data")

# Cache em memória para acesso ultrarrápido aos dados estáticos
_CACHE: Dict[str, Any] = {}

def _load_json_file(filename: str, default: Any) -> Any:
    """Carrega um arquivo JSON da pasta static_data com cache em memória."""
    if filename in _CACHE:
        return _CACHE[filename]
        
    filepath = os.path.join(STATIC_DATA_DIR, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                _CACHE[filename] = data
                return data
        except Exception as e:
            print(f"[META_COMPARATOR] Erro ao carregar {filename}: {e}")
            
    return default

def get_hoyolab_mappings() -> Dict[str, Dict[str, str]]:
    return _load_json_file("hoyolab_mappings.json", {"hsr": {}, "genshin": {}, "zzz": {}})

def get_character_aliases() -> Dict[str, Dict[str, str]]:
    return _load_json_file("character_aliases.json", {"hsr": {}, "genshin": {}, "zzz": {}})

def get_character_benchmarks() -> Dict[str, Dict[str, Dict[str, str]]]:
    return _load_json_file("character_benchmarks.json", {"hsr": {}, "genshin": {}, "zzz": {}})

def get_stat_mappings() -> Dict[str, str]:
    return _load_json_file("stat_mappings.json", {})

def normalize_slug_text(text: str) -> str:
    """Normaliza texto para chave de busca sem acentos ou caracteres especiais."""
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8')
    text = text.lower().strip()
    text = re.sub(r'[\'\"’`\(\)•·・:!?,]', '', text)
    text = re.sub(r'[\s\-_/\.]+', ' ', text)
    return text.strip()


def resolve_character_canonical_slug(game_id: str, char_name: str, element: str = "", roster_data: Optional[List[Dict[str, Any]]] = None) -> str:
    """Resolve o slug canônico de um personagem em qualquer idioma (PT-BR, EN, ES, ID HoYoLAB) com suporte a Fuzzy Matching."""
    if not char_name:
        return ""
    g = game_id.lower().strip()
    char_str = str(char_name).strip()
    
    hoyolab_map = get_hoyolab_mappings().get(g, {})
    
    # 1. Se for ID numérico direto do HoYoLAB
    if char_str.isdigit():
        if char_str in hoyolab_map:
            return hoyolab_map[char_str]
        try:
            from static_data_manager import static_data_manager
            char_info = static_data_manager.get_character_by_hoyolab_id(g, char_str)
            if char_info and "id" in char_info:
                return char_info["id"]
        except Exception:
            pass
            
    # 2. Consultar o Roster (se fornecido) para obter char_id ou matching exato
    if roster_data:
        for c in roster_data:
            c_name = str(c.get("name", "")).strip()
            c_id = str(c.get("char_id", "")).strip()
            if (c_name.lower() == char_str.lower() or c_id == char_str) and c_id in hoyolab_map:
                return hoyolab_map[c_id]
        
    # 3. Tratamento especial para Viajante / Desbravador com elemento
    norm = normalize_slug_text(char_str)
    if ("viajante" in norm or "traveler" in norm) and element:
        el_norm = normalize_slug_text(element)
        return f"traveler_{el_norm}"
    if ("desbravador" in norm or "trailblazer" in norm) and element:
        el_norm = normalize_slug_text(element)
        return f"trailblazer_•_{el_norm}"

    # 4. Consultar dicionário de Aliases multilíngues (PT-BR, ES, EN)
    aliases = get_character_aliases().get(g, {})
    
    if norm in aliases:
        return aliases[norm]
    if char_str.lower() in aliases:
        return aliases[char_str.lower()]
        
    for alias_k, canonical in aliases.items():
        if normalize_slug_text(alias_k) == norm:
            return canonical

    # 5. Busca Inteligente Dinâmica no Catálogo do static_data_manager (Zero-Maintenance)
    try:
        from static_data_manager import static_data_manager
        catalog = static_data_manager._cache.get(g, {}).get("characters", {})
        if catalog:
            # 5a. Match exato por chave / slug
            clean_q = norm.replace(" ", "_")
            if clean_q in catalog:
                return clean_q
                
            # 5b. Match exato por nome cadastrado
            for cid, cinfo in catalog.items():
                if normalize_slug_text(cinfo.get("name", "")) == norm:
                    return cid

            # 5c. Guarda rígida para Nomes Curtos (len <= 4) para evitar colisões
            # Ex: "Seth" deve casar com "Seth Lowell", mas NUNCA com "Sethos" ou "Sayu"
            if len(norm) <= 4:
                for cid, cinfo in catalog.items():
                    c_name_norm = normalize_slug_text(cinfo.get("name", ""))
                    tokens = c_name_norm.split()
                    if norm in tokens or cid == norm:
                        return cid
                return norm.replace(" ", "_")

            # 5d. Fuzzy Matching Estrito (Threshold >= 88) para nomes longos
            choices = {cid: normalize_slug_text(cinfo.get("name", cid)) for cid, cinfo in catalog.items()}
            try:
                from rapidfuzz import process, fuzz
                best_match = process.extractOne(norm, choices, scorer=fuzz.token_sort_ratio)
                if best_match and best_match[1] >= 88:
                    return best_match[2] # Retorna o ID canônico correspondente
            except ImportError:
                import difflib
                names = list(choices.values())
                matches = difflib.get_close_matches(norm, names, n=1, cutoff=0.88)
                if matches:
                    matched_name = matches[0]
                    for cid, cname in choices.items():
                        if cname == matched_name:
                            return cid
    except Exception:
        pass

    # 6. Normalização direta em slug (substituindo espaços por _)
    slug = norm.replace(" ", "_")
    return slug


def find_best_guide_file(game_id: str, char_name: str, element: str = "", roster_data: Optional[List[Dict[str, Any]]] = None) -> str:
    """Encontra o arquivo Markdown do guia oficial correspondente ao personagem com busca tolerante a variações."""
    g = game_id.lower().strip()
    guides_dir = os.path.join(BASE_DIR, g, "guias")
    
    if not os.path.exists(guides_dir):
        return ""
        
    canonical = resolve_character_canonical_slug(g, char_name, element, roster_data)
    
    # 1. Tentar arquivos candidatos exatos
    candidate_names = [
        f"{canonical}.md",
        f"{canonical.replace('_', ' ')}.md",
        f"{canonical.replace('_•_', '_')}.md",
        f"{canonical.replace('•', '')}.md",
        f"{char_name.lower().replace(' ', '_')}.md",
        f"{normalize_slug_text(char_name).replace(' ', '_')}.md",
        f"{char_name}.md"
    ]
    
    for cname in candidate_names:
        full_p = os.path.join(guides_dir, cname)
        if os.path.isfile(full_p):
            return full_p
            
    # 2. Varrer diretório de guias buscando correspondência aproximada/normalizada
    try:
        norm_target = normalize_slug_text(canonical)
        norm_char = normalize_slug_text(char_name)
        
        all_files = [f for f in os.listdir(guides_dir) if f.endswith(".md")]
        for fname in all_files:
            f_stem = fname[:-3]
            f_norm = normalize_slug_text(f_stem)
            
            if f_norm == norm_target or f_norm == norm_char:
                return os.path.join(guides_dir, fname)
                
        # 3. Substring match segura
        if len(norm_target) >= 4:
            for fname in all_files:
                f_norm = normalize_slug_text(fname[:-3])
                if norm_target in f_norm or f_norm in norm_target:
                    return os.path.join(guides_dir, fname)

        # 4. Fuzzy match com arquivos existentes
        try:
            from rapidfuzz import process, fuzz
            choices = {fname: fname[:-3] for fname in all_files}
            best = process.extractOne(canonical, choices, scorer=fuzz.token_set_ratio)
            if best and best[1] >= 80:
                return os.path.join(guides_dir, best[2])
        except Exception:
            pass
    except Exception:
        pass
        
    return ""


def clean_meta_item_name(s: str) -> str:
    """Limpa tags markdown e sufixos numéricos de nomes de armas/conjuntos."""
    if not s:
        return ""
    s = s.replace("**", "").replace("`", "").strip()
    s = re.sub(r'\s*\(\s*\d+(?:\.\d+)?%[^)]*\)', '', s)
    s = re.sub(r'\s*\(\s*[SR]\d+\s*\)', '', s)
    s = re.sub(r'\s*\(\s*\d+-[Pp][Cc]\s*\)', '', s)
    s = re.sub(r'\s*\(\s*\d+\s*peças\s*\)', '', s, flags=re.I)
    s = re.sub(r'\s*\(\s*\d+\s*de eficácia\s*\)', '', s, flags=re.I)
    s = re.sub(r'\s*-\s*—\s*$', '', s)
    s = re.sub(r'\s*-\s*$', '', s)
    return s.strip()

def get_section_lines_from_md(content: str, header_keywords: List[str]) -> List[str]:
    """Extrai as linhas pertencentes a uma seção Markdown identificada por palavras-chave."""
    lines = content.splitlines()
    in_section = False
    section_level = 0
    section_lines = []
    
    for line in lines:
        line_strip = line.strip()
        if line_strip.startswith('#'):
            level = len(line_strip) - len(line_strip.lstrip('#'))
            title = line_strip.lstrip('# \t').lower()
            if any(kw.lower() in title for kw in header_keywords):
                in_section = True
                section_level = level
                continue
            elif in_section and level <= section_level:
                in_section = False
        elif in_section:
            section_lines.append(line)
            
    return section_lines

def derive_dynamic_benchmarks(game_id: str, char_name: str, stats_found: Dict[str, str], substats_list: List[str]) -> Dict[str, str]:
    """Derivação de fallback inteligente baseada em arquétipo real do kit."""
    sub_lower = [str(x).lower() for x in substats_list]
    main_lower = [str(v).lower() for v in stats_found.values()]
    all_context = " ".join(sub_lower + main_lower)
    
    if game_id == "genshin":
        if any(k in all_context for k in ["def", "defesa"]):
            if any(k in all_context for k in ["recarga", "energy", "er"]):
                return {"DEF": "2.400+", "Recarga de Energia": "170%+", "Taxa Crítica": "50%+"}
            return {"DEF": "2.400+", "Taxa Crítica": "65%+", "Dano Crítico": "140%+"}
        elif any(k in all_context for k in ["cura", "healing"]):
            return {"Vida": "38.000+", "Bônus de Cura": "35%+", "Recarga de Energia": "160%+"}
        elif any(k in all_context for k in ["vida", "pv", "hp"]):
            return {"Vida": "34.000+", "Taxa Crítica": "65%+", "Dano Crítico": "150%+"}
        elif any(k in all_context for k in ["proficiência", "proficiencia", "mastery", "em"]):
            if any(k in all_context for k in ["crit", "crítica", "critica"]):
                return {"Proficiência Elemental": "350+", "Taxa Crítica": "70%+", "Dano Crítico": "150%+"}
            return {"Proficiência Elemental": "800+", "Recarga de Energia": "160%+"}
        elif any(k in all_context for k in ["recarga", "energy", "er"]):
            return {"Recarga de Energia": "200%+", "Taxa Crítica": "55%+", "ATQ": "1.700+"}
        else:
            return {"ATQ": "2.100+", "Taxa Crítica": "70%+", "Dano Crítico": "150%+"}
            
    elif game_id == "hsr":
        if any(k in all_context for k in ["quebra", "break", "be"]):
            return {"Efeito de Quebra": "220%+", "VEL": "145+", "ATQ": "2.400+"}
        elif any(k in all_context for k in ["acerto de efeito", "ehr", "effect hit"]):
            return {"ATQ": "3.000+", "Acerto de Efeito": "67%+", "VEL": "136+"}
        elif any(k in all_context for k in ["def", "defesa"]):
            return {"DEF": "3.800+", "VEL": "134+", "Resistência a Efeito": "30%+"}
        elif any(k in all_context for k in ["cura", "healing", "regen"]):
            return {"Vida": "6.000+", "VEL": "134+", "Bônus de Cura": "34.5%+", "Taxa de Regen. Energia": "19.4%+"}
        elif any(k in all_context for k in ["vida", "hp", "pv"]):
            return {"Vida": "7.000+", "Taxa Crítica": "65%+", "Dano Crítico": "140%+", "VEL": "134+"}
        elif any(k in all_context for k in ["regen. energia", "err"]):
            return {"VEL": "145+", "Taxa de Regen. Energia": "19.4%+", "Vida": "4.000+", "DEF": "1.200+"}
        else:
            return {"ATQ": "3.000+", "Taxa Crítica": "70%+", "Dano Crítico": "140%+", "VEL": "134+"}
            
    elif game_id == "zzz":
        if any(k in all_context for k in ["anomalia", "anomaly"]):
            return {"Proficiência de Anomalia": "380+", "ATQ": "2.600+", "Maestria de Anomalia": "110+"}
        elif any(k in all_context for k in ["impacto", "impact", "atordoamento", "stun"]):
            return {"Impacto": "170+", "ATQ": "2.200+", "Taxa CRIT": "50%+"}
        elif any(k in all_context for k in ["def", "defesa"]):
            return {"DEF": "2.500+", "Vida": "14.000+"}
        elif any(k in all_context for k in ["perfuração", "perfuracao", "pen"]):
            return {"Taxa de Perfuração": "50%+", "Taxa de Regen. Energia": "20%+", "ATQ": "2.400+"}
        else:
            return {"ATQ": "2.600+", "Taxa CRIT": "65%+", "Dano CRIT": "140%+"}
            
    return {"ATQ": "2.500+", "Taxa Crítica": "60%+", "Dano Crítico": "120%+"}

def parse_meta_target(
    game_id: str, 
    char_name: str, 
    element: str = "", 
    meta_json: Optional[Dict[str, Any]] = None, 
    roster_data: Optional[List[Dict[str, Any]]] = None,
    translate_fn=None
) -> Dict[str, Any]:
    """Extrai e compõe o alvo ideal do metagame a partir dos guias locais e base de dados calibrada."""
    target = {
        "weapon": "Não informado",
        "weapons": [],
        "sets": ["Não informado"],
        "all_sets": [],
        "stats": {},
        "endgame_stats": {}
    }
    
    translate = translate_fn if translate_fn else (lambda x: str(x))
    stat_en_to_pt = get_stat_mappings()
    benchmarks_db = get_character_benchmarks().get(game_id, {})
    
    guide_path = find_best_guide_file(game_id, char_name, element, roster_data)
    if not guide_path or not os.path.exists(guide_path):
        try:
            from services.ai_build_generator import AIBuildGenerator
            generated = AIBuildGenerator.get_or_generate_guide(game_id, char_name, element)
            if generated and os.path.exists(generated):
                guide_path = generated
        except Exception:
            pass

    guide_content = ""
    if guide_path and os.path.exists(guide_path):
        try:
            with open(guide_path, "r", encoding="utf-8", errors="ignore") as f:
                guide_content = f.read()
        except Exception:
            pass

            
    weapons_list: List[str] = []
    sets_list: List[str] = []
    stats_found: Dict[str, str] = {}
    endgame_stats: Dict[str, str] = {}
    
    if guide_content:
        # 1. Armas / W-Engines / Cones
        w_lines = get_section_lines_from_md(guide_content, ["melhores cones", "armas recomendadas", "melhores armas", "melhores w-engines", "best light cone", "best weapon", "best w-engine", "weapons"])
        for l in w_lines:
            m = re.search(r'-\s*\*\*([^*]+)\*\*', l)
            if m:
                w_name = clean_meta_item_name(m.group(1))
                if w_name and w_name not in weapons_list and len(w_name) > 2 and not w_name.lower().startswith(("justificativa", "review", "rationale", "nota")):
                    weapons_list.append(w_name)
                    
        # 2. Sets de Relíquias / Artefatos / Discos
        s_lines = get_section_lines_from_md(guide_content, ["melhores conjuntos", "conjuntos de artefatos", "melhores relíquias", "melhores discos", "melhores ornamentos", "best relics", "best artifacts", "best discs", "best planar"])
        for l in s_lines:
            m = re.search(r'-\s*\*\*([^*]+)\*\*', l)
            if m:
                s_name = clean_meta_item_name(m.group(1))
                if s_name and s_name not in sets_list and len(s_name) > 2 and not s_name.lower().startswith(("justificativa", "review", "rationale", "nota", "disk", "disco")):
                    sets_list.append(s_name)
                    
        # 3. Atributos Recomendados por Slot
        stat_lines = get_section_lines_from_md(guide_content, ["atributos principais", "atributos recomendados", "main stats"])
        for l in stat_lines:
            l_str = l.strip()
            if not (l_str.startswith("-") or l_str.startswith("*")):
                continue
            if ":" in l_str:
                parts = l_str.lstrip("-* \t").split(":", 1)
                raw_slot = parts[0].replace("**", "").strip()
                raw_val = parts[1].replace("**", "").replace("`", "").strip()
                
                slot_label = ""
                if game_id == "genshin":
                    if any(k in raw_slot.lower() for k in ["areia", "sands", "ampulheta"]): slot_label = "Areia"
                    elif any(k in raw_slot.lower() for k in ["cálice", "copo", "goblet"]): slot_label = "Copo"
                    elif any(k in raw_slot.lower() for k in ["tiara", "coroa", "circlet"]): slot_label = "Tiara"
                elif game_id == "hsr":
                    if any(k in raw_slot.lower() for k in ["corpo", "body"]): slot_label = "Corpo"
                    elif any(k in raw_slot.lower() for k in ["bota", "pés", "feet"]): slot_label = "Bota"
                    elif any(k in raw_slot.lower() for k in ["esfera", "planar sphere", "sphere"]): slot_label = "Esfera"
                    elif any(k in raw_slot.lower() for k in ["corda", "link rope", "rope"]): slot_label = "Corda"
                elif game_id == "zzz":
                    for d_i in range(1, 7):
                        if f"disk {d_i}" in raw_slot.lower() or f"disco {d_i}" in raw_slot.lower() or raw_slot == str(d_i):
                            slot_label = f"Disco {d_i}"
                            break
                if slot_label and raw_val:
                    stats_found[slot_label] = raw_val
            elif "disk" in l_str.lower() or "disco" in l_str.lower():
                for d_i in range(4, 7):
                    if f"disk {d_i}" in l_str.lower() or f"disco {d_i}" in l_str.lower():
                        raw_val = re.sub(rf'-\s*(?:disk|disco)\s*{d_i}\s*', '', l_str, flags=re.I).strip()
                        if raw_val:
                            stats_found[f"Disco {d_i}"] = raw_val
                            
        # 4. Atributos Finais / Endgame Stats
        endgame_lines = get_section_lines_from_md(guide_content, ["atributos finais", "endgame stats"])
        for l in endgame_lines:
            l_str = l.strip()
            if (l_str.startswith("-") or l_str.startswith("*")) and ":" in l_str:
                parts = l_str.lstrip("-* \t").split(":", 1)
                s_name = parts[0].replace("**", "").replace("`", "").strip()
                s_val = parts[1].replace("**", "").replace("`", "").strip()
                if s_name and s_val and len(s_name) < 40 and not s_name.lower().startswith(("justificativa", "nota")):
                    endgame_stats[s_name] = s_val

    # Fallback / Complemento com meta_data JSON estruturado
    char_entry = None
    c_norm = normalize_slug_text(char_name)
    if meta_json:
        char_entry = meta_json.get(c_norm) or meta_json.get(char_name.lower()) or meta_json.get(char_name)
        if not char_entry:
            for k_m, v_m in meta_json.items():
                if isinstance(v_m, dict) and normalize_slug_text(v_m.get("name", "")) == c_norm:
                    char_entry = v_m
                    break
                    
    if char_entry and "main_stats" in char_entry:
        slot_map_gen = {"sands": "Areia", "goblet": "Copo", "circlet": "Tiara"}
        slot_map_hsr = {"body": "Corpo", "feet": "Bota", "planar_sphere": "Esfera", "link_rope": "Corda"}
        slot_map_zzz = {"slot_4": "Disco 4", "slot_5": "Disco 5", "slot_6": "Disco 6"}
        active_map = slot_map_gen if game_id == "genshin" else (slot_map_hsr if game_id == "hsr" else slot_map_zzz)
        
        for k_s, label in active_map.items():
            if label not in stats_found and k_s in char_entry["main_stats"]:
                val_list = char_entry["main_stats"][k_s]
                if isinstance(val_list, list):
                    stats_found[label] = " / ".join([stat_en_to_pt.get(str(x).lower().strip(), str(x)) for x in val_list])
                else:
                    stats_found[label] = stat_en_to_pt.get(str(val_list).lower().strip(), str(val_list))
                    
    # 5. Resolução Inteligente de Benchmarks Específicos do Personagem
    guide_slug = os.path.basename(guide_path).replace('.md', '').lower() if guide_path else ""
    canonical_slug = resolve_character_canonical_slug(game_id, char_name, element, roster_data)
    
    char_bench = benchmarks_db.get(canonical_slug)
    if not char_bench and guide_slug:
        char_bench = benchmarks_db.get(guide_slug)
    if not char_bench:
        char_bench = benchmarks_db.get(c_norm)
    if not char_bench:
        char_bench = benchmarks_db.get(char_name.lower().strip())
        
    if char_bench:
        endgame_stats = dict(char_bench)
    elif not endgame_stats and char_entry and "general_benchmarks" in char_entry and char_entry["general_benchmarks"]:
        endgame_stats = dict(char_entry["general_benchmarks"])
        
    # 6. Fallback Dinâmico por Arquétipo e Kit
    if not endgame_stats:
        substats_list = char_entry.get("substats_priority", []) if char_entry else []
        endgame_stats = derive_dynamic_benchmarks(game_id, char_name, stats_found, substats_list)

    if weapons_list:
        target["weapon"] = translate(weapons_list[0])
        target["weapons"] = [translate(w) for w in weapons_list]
    if sets_list:
        target["sets"] = [translate(sets_list[0])]
        target["all_sets"] = [translate(s) for s in sets_list]
        
    target["stats"] = {translate(k): translate(v) for k, v in stats_found.items()}
    target["endgame_stats"] = {translate(k): translate(v) for k, v in endgame_stats.items()}
    
    return target
