import os
import re
import json
import unicodedata
from typing import Dict, List, Any, Optional, Tuple
from core.paths import get_data_dir, get_data_path, get_resource_path

BASE_DIR = get_data_dir()
STATIC_DATA_DIR = os.path.join(BASE_DIR, "static_data")

# Cache em memória para acesso ultrarrápido aos dados estáticos e índice de guias
_CACHE: Dict[str, Any] = {}
_GUIDE_DIR_INDEX_CACHE: Dict[str, Tuple[float, List[str]]] = {}
_GUIDE_PRELIM_CACHE: Dict[str, Tuple[float, bool]] = {}

_RE_SLUG_PUNCT = re.compile(r"[\'\"’`\(\)•·・:!?,]")
_RE_SLUG_SEP = re.compile(r"[\s\-_/\.]+")
_RE_META_PCT = re.compile(r"\s*\(\s*\d+(?:\.\d+)?%[^)]*\)")
_RE_META_RANK = re.compile(r"\s*\(\s*[SR]\d+\s*\)")
_RE_META_PC = re.compile(r"\s*\(\s*\d+-[Pp][Cc]\s*\)")
_RE_META_PECAS = re.compile(r"\s*\(\s*\d+\s*peças\s*\)", re.IGNORECASE)
_RE_META_EFIC = re.compile(r"\s*\(\s*\d+\s*de eficácia\s*\)", re.IGNORECASE)
_RE_META_EMDASH = re.compile(r"\s*-\s*—\s*$")
_RE_META_DASH = re.compile(r"\s*-\s*$")
_RE_META_STARS = re.compile(r"\s*[1-5]\s*[\*★]\s*$")
_RE_BOLD_ITEM = re.compile(r"-\s*\*\*([^*]+)\*\*")


def _load_json_file(filename: str, default: Any) -> Any:
    """Carrega um arquivo JSON da pasta static_data com cache em memória (priorizando get_data_path)."""
    if filename in _CACHE:
        return _CACHE[filename]

    rel = os.path.join("static_data", filename)
    data_p = get_data_path(rel)
    filepath = data_p if os.path.exists(data_p) else get_resource_path(rel)
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
    text = unicodedata.normalize("NFKD", str(text)).encode("ASCII", "ignore").decode("utf-8")
    text = text.lower().strip()
    text = _RE_SLUG_PUNCT.sub("", text)
    text = _RE_SLUG_SEP.sub(" ", text)
    return text.strip()


def resolve_character_canonical_slug(
    game_id: str, char_name: str, element: str = "", roster_data: Optional[List[Dict[str, Any]]] = None
) -> str:
    """Resolve o slug canônico de um personagem em qualquer idioma (PT-BR, EN, ES, ID HoYoLAB) com suporte a Fuzzy Matching."""
    if not char_name:
        return ""
    g = game_id.lower().strip()
    char_str = str(char_name).strip()

    hoyolab_map = get_hoyolab_mappings().get(g, {})

    # 1. Se for ID numérico direto do HoYoLAB
    aliases = get_character_aliases().get(g, {})

    def _resolve_alias_slug(raw_slug: str) -> str:
        if not raw_slug:
            return ""
        s_low = raw_slug.lower().strip()
        s_norm = normalize_slug_text(raw_slug)
        if s_low in aliases:
            return aliases[s_low]
        if s_norm in aliases:
            return aliases[s_norm]
        return raw_slug

    if char_str.isdigit():
        if char_str in hoyolab_map:
            return _resolve_alias_slug(hoyolab_map[char_str])
        try:
            from static_data_manager import static_data_manager

            char_info = static_data_manager.get_character_by_hoyolab_id(g, char_str)
            if char_info and "id" in char_info:
                return _resolve_alias_slug(char_info["id"])
        except Exception:
            pass

    # 2. Consultar o Roster (se fornecido) para obter id/char_id oficial (resolve PT-BR automaticamente!)
    matched_roster_char = None
    if roster_data:
        char_str_low = char_str.lower()
        char_str_norm = normalize_slug_text(char_str)
        for c in roster_data:
            c_name = str(c.get("name", "")).strip()
            c_id = str(c.get("id") or c.get("char_id") or "").strip()
            if (
                c_name.lower() == char_str_low
                or normalize_slug_text(c_name) == char_str_norm
                or (c_id and c_id == char_str)
            ):
                matched_roster_char = c
                if c_id and c_id in hoyolab_map:
                    mapped_from_id = _resolve_alias_slug(hoyolab_map[c_id])
                    # Se o mapeamento salvo ainda for genérico ('desbravadora'/'viajante'), delega para o Passo 3 (elemento->caminho)
                    m_norm = normalize_slug_text(mapped_from_id)
                    if m_norm not in ("desbravador", "desbravadora", "viajante", "trailblazer", "traveler", "nickname"):
                        return mapped_from_id
                break

    # 3. Tratamento especial para Viajante (Genshin) / Desbravador (HSR — elemento -> caminho!)
    norm = normalize_slug_text(char_str)
    if ("viajante" in norm or "traveler" in norm) and element:
        el_norm = normalize_slug_text(element)
        return f"traveler_{el_norm}"
    if "desbravador" in norm or "trailblazer" in norm:
        tb_elem_to_path = {
            "physical": "destruction",
            "fisico": "destruction",
            "destruction": "destruction",
            "destruicao": "destruction",
            "fire": "preservation",
            "fogo": "preservation",
            "preservation": "preservation",
            "preservacao": "preservation",
            "imaginary": "harmony",
            "imaginario": "harmony",
            "harmony": "harmony",
            "harmonia": "harmony",
            "ice": "remembrance",
            "gelo": "remembrance",
            "remembrance": "remembrance",
            "recordacao": "remembrance",
            "lightning": "elation",
            "raio": "elation",
            "elation": "elation",
            "euforia": "elation",
            "jubilo": "elation",
        }
        raw_hint = ""
        if matched_roster_char:
            raw_hint = str(matched_roster_char.get("path") or matched_roster_char.get("element") or "")
        if not raw_hint:
            raw_hint = element or ""
        hint_norm = normalize_slug_text(raw_hint)
        if hint_norm in tb_elem_to_path:
            return f"trailblazer_•_{tb_elem_to_path[hint_norm]}"
        for tok in norm.split():
            if tok in tb_elem_to_path:
                return f"trailblazer_•_{tb_elem_to_path[tok]}"

    # 4. Consultar dicionário de Aliases multilíngues (PT-BR, ES, EN)
    if norm in aliases:
        return aliases[norm]
    if char_str.lower() in aliases:
        return aliases[char_str.lower()]

    for alias_k, canonical in aliases.items():
        if normalize_slug_text(alias_k) == norm:
            return canonical

    # 4b. Fallback dinâmico via tabela oficial de traduções de personagens (REVERSE_TRANSLATIONS)
    try:
        from services.translation_service import REVERSE_TRANSLATIONS

        rev_en = REVERSE_TRANSLATIONS.get(char_str.lower()) or REVERSE_TRANSLATIONS.get(norm)
        if rev_en:
            rev_norm = normalize_slug_text(rev_en)
            if rev_norm in aliases:
                return aliases[rev_norm]
            if rev_en.lower() in aliases:
                return aliases[rev_en.lower()]
    except Exception:
        pass

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
                    return best_match[2]  # Retorna o ID canônico correspondente
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


def find_best_guide_file(
    game_id: str,
    char_name: str,
    element: str = "",
    roster_data: Optional[List[Dict[str, Any]]] = None,
    canonical_slug: Optional[str] = None,
) -> str:
    """Encontra o arquivo Markdown do guia oficial correspondente ao personagem com busca tolerante a variações."""
    g = game_id.lower().strip()
    guides_dir = os.path.join(BASE_DIR, g, "guias")

    if not os.path.exists(guides_dir):
        return ""

    canonical = canonical_slug or resolve_character_canonical_slug(g, char_name, element, roster_data)

    # 1. Tentar arquivos candidatos exatos
    candidate_names = [
        f"{canonical}.md",
        f"{canonical.replace('_', ' ')}.md",
        f"{canonical.replace('_•_', '_')}.md",
        f"{canonical.replace('•', '')}.md",
        f"{char_name.lower().replace(' ', '_')}.md",
        f"{normalize_slug_text(char_name).replace(' ', '_')}.md",
        f"{char_name}.md",
    ]

    def _is_preliminary_file(fpath: str) -> bool:
        try:
            mtime = os.path.getmtime(fpath)
            cached_p = _GUIDE_PRELIM_CACHE.get(fpath)
            if cached_p and cached_p[0] == mtime:
                return cached_p[1]
            with open(fpath, "r", encoding="utf-8", errors="ignore") as gf:
                head = gf.read(400)
                is_prelim = "ai_preliminary" in head or "Guia Preliminar" in head
            _GUIDE_PRELIM_CACHE[fpath] = (mtime, is_prelim)
            return is_prelim
        except Exception:
            return False

    prelim_fallback = ""

    for cname in candidate_names:
        full_p = os.path.join(guides_dir, cname)
        if os.path.isfile(full_p):
            if not _is_preliminary_file(full_p):
                return full_p
            if not prelim_fallback:
                prelim_fallback = full_p

    # 2. Varrer diretório de guias com índice cacheado por mtime do diretório
    try:
        norm_target = normalize_slug_text(canonical)
        norm_char = normalize_slug_text(char_name)

        dir_mtime = os.path.getmtime(guides_dir)
        cached_dir = _GUIDE_DIR_INDEX_CACHE.get(guides_dir)
        if cached_dir and cached_dir[0] == dir_mtime:
            all_files = cached_dir[1]
        else:
            all_files = [f for f in os.listdir(guides_dir) if f.endswith(".md")]
            _GUIDE_DIR_INDEX_CACHE[guides_dir] = (dir_mtime, all_files)
        for fname in all_files:
            f_stem = fname[:-3]
            f_norm = normalize_slug_text(f_stem)

            if f_norm == norm_target or f_norm == norm_char:
                cand_p = os.path.join(guides_dir, fname)
                if not _is_preliminary_file(cand_p):
                    return cand_p
                if not prelim_fallback:
                    prelim_fallback = cand_p

        # 3. Substring match segura
        if len(norm_target) >= 4:
            for fname in all_files:
                f_norm = normalize_slug_text(fname[:-3])
                if norm_target in f_norm or f_norm in norm_target:
                    cand_p = os.path.join(guides_dir, fname)
                    if not _is_preliminary_file(cand_p):
                        return cand_p
                    if not prelim_fallback:
                        prelim_fallback = cand_p

        # 4. Fuzzy match com arquivos existentes
        try:
            from rapidfuzz import process, fuzz

            choices = {fname: fname[:-3] for fname in all_files}
            best = process.extractOne(canonical, choices, scorer=fuzz.token_set_ratio)
            if best and best[1] >= 80:
                cand_p = os.path.join(guides_dir, best[2])
                if not _is_preliminary_file(cand_p):
                    return cand_p
                if not prelim_fallback:
                    prelim_fallback = cand_p
        except Exception:
            pass
    except Exception:
        pass

    return prelim_fallback


def clean_meta_item_name(s: str) -> str:
    """Limpa tags markdown e sufixos numéricos de nomes de armas/conjuntos."""
    if not s:
        return ""
    s = s.replace("**", "").replace("`", "").strip()
    s = _RE_META_PCT.sub("", s)
    s = _RE_META_RANK.sub("", s)
    s = _RE_META_PC.sub("", s)
    s = _RE_META_PECAS.sub("", s)
    s = _RE_META_EFIC.sub("", s)
    s = _RE_META_EMDASH.sub("", s)
    s = _RE_META_DASH.sub("", s)
    s = _RE_META_STARS.sub("", s)
    return s.strip()


def get_section_lines_from_md(content: str, header_keywords: List[str]) -> List[str]:
    """Extrai as linhas pertencentes a uma seção Markdown identificada por palavras-chave."""
    lines = content.splitlines()
    in_section = False
    section_level = 0
    section_lines = []

    for line in lines:
        line_strip = line.strip()
        if line_strip.startswith("#"):
            level = len(line_strip) - len(line_strip.lstrip("#"))
            title = line_strip.lstrip("# \t").lower()
            if any(kw.lower() in title for kw in header_keywords):
                in_section = True
                section_level = level
                continue
            elif in_section and level <= section_level:
                in_section = False
        elif in_section:
            section_lines.append(line)

    return section_lines


def _is_benchmark_consistent_with_guide(
    game_id: str,
    bench: Dict[str, Any],
    stats_found: Dict[str, str],
    guide_substats: str = "",
) -> bool:
    """
    Valida se um preset estático de character_benchmarks.json é consistente com o escalonamento real
    do guia oficial (Main Stats + Substats). Evita que personagens DEF/ATK/EM (ex.: Linnea, Escoffier,
    Odette, Nefer, Nicole) peçam metas de 'Vida: 32.000+' ou 'EM: 750+' incompatíveis com o kit.
    """
    if not bench or not stats_found:
        return True

    from calculators.benchmark_radar import canonicalize_benchmark_key, parse_stat_number

    ctx = " ".join(str(v) for v in stats_found.values()).lower()
    if guide_substats:
        ctx = f"{ctx} {guide_substats.lower()}"

    has_hp = bool(re.search(r"\b(?:hp%?|vida|pv%?)\b", ctx))
    has_def = bool(re.search(r"\b(?:def%?|defesa)\b", ctx))
    has_atk = bool(re.search(r"\b(?:atk%?|atq%?|ataque)\b", ctx))
    has_em = bool(re.search(r"\b(?:em|maestria|profici[eê]ncia)\b", ctx))

    g = (game_id or "").lower().strip()
    for raw_k, raw_v in bench.items():
        ck = canonicalize_benchmark_key(str(raw_k), game_id=g)
        num = parse_stat_number(raw_v) or 0.0
        if g == "genshin":
            if ck == "hp_flat" and num >= 22000 and not has_hp:
                return False
            if ck == "def_flat" and num >= 1500 and not has_def:
                return False
            if ck == "em" and num >= 400 and not has_em:
                return False
            if ck == "atk_flat" and num >= 1800 and not has_atk and (has_hp or has_def or has_em):
                return False
        elif g == "hsr":
            if ck == "hp_flat" and num >= 5500 and not has_hp:
                return False
            if ck == "def_flat" and num >= 2500 and not has_def:
                return False
    return True


def derive_dynamic_benchmarks(
    game_id: str, char_name: str, stats_found: Dict[str, str], substats_list: List[str]
) -> Dict[str, str]:
    """Derivação de fallback baseada no escalonamento real dos Main Stats e Substats do guia."""
    sub_lower = [str(x).lower() for x in substats_list]
    main_lower = [str(v).lower() for v in stats_found.values()]
    all_context = " ".join(sub_lower + main_lower)
    has_crit = bool(re.search(r"\b(?:crit|cr[ií]tic[oa])\b", all_context))
    has_er = bool(re.search(r"\b(?:recarga|energy|er)\b", all_context))

    if game_id == "genshin":
        if re.search(r"\b(?:def%?|defesa)\b", all_context):
            res: Dict[str, str] = {"DEF": "2.400+"}
            if has_crit:
                res["Taxa Crítica"] = "65%+"
                res["Dano Crítico"] = "140%+"
            if has_er:
                res["Recarga de Energia"] = "160%+"
            return res
        elif re.search(r"\b(?:hp%?|vida|pv%?)\b", all_context):
            if re.search(r"\b(?:cura|healing)\b", all_context) and not has_crit:
                return {"Vida": "38.000+", "Bônus de Cura": "35%+", "Recarga de Energia": "160%+"}
            res = {"Vida": "34.000+"}
            if has_crit:
                res["Taxa Crítica"] = "65%+"
                res["Dano Crítico"] = "150%+"
            if has_er:
                res["Recarga de Energia"] = "160%+"
            return res
        elif re.search(r"\b(?:profici[eê]ncia|maestria|mastery|em)\b", " ".join(main_lower)):
            if has_crit:
                return {"Proficiência Elemental": "650+", "Taxa Crítica": "70%+", "Dano Crítico": "150%+"}
            return {"Proficiência Elemental": "800+", "Recarga de Energia": "160%+"}
        elif re.search(r"\b(?:cura|healing)\b", all_context) and not has_crit:
            return {"ATQ": "2.200+", "Bônus de Cura": "35%+", "Recarga de Energia": "180%+"}
        elif has_er and not has_crit:
            return {"ATQ": "2.200+", "Recarga de Energia": "180%+"}
        else:
            res = {"ATQ": "2.100+", "Taxa Crítica": "70%+", "Dano Crítico": "150%+"}
            if has_er and re.search(r"\b(?:recarga|energy|er)\b", " ".join(main_lower)):
                res["Recarga de Energia"] = "160%+"
            return res

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
    translate_fn=None,
) -> Dict[str, Any]:
    """Extrai e compõe o alvo ideal do metagame a partir dos guias locais e base de dados calibrada."""
    target = {
        "weapon": "Não informado",
        "weapons": [],
        "sets": ["Não informado"],
        "all_sets": [],
        "stats": {},
        "endgame_stats": {},
    }

    translate = translate_fn if translate_fn else (lambda x: str(x))
    stat_en_to_pt = get_stat_mappings()
    benchmarks_db = get_character_benchmarks().get(game_id, {})

    canonical_slug = resolve_character_canonical_slug(game_id, char_name, element, roster_data)
    guide_path = find_best_guide_file(
        game_id, char_name, element, roster_data, canonical_slug=canonical_slug
    )
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
    relic_sets_list: List[str] = []
    planar_sets_list: List[str] = []
    stats_found: Dict[str, str] = {}
    endgame_stats: Dict[str, str] = {}
    is_ai_preliminary = bool(guide_content and ("ai_preliminary" in guide_content[:500] or "Guia Preliminar" in guide_content[:500]))

    from calculators.equipment_comparator import is_junk_set_name, localize_equipment_name

    if guide_content:
        # 1. Armas / W-Engines / Cones
        w_lines = get_section_lines_from_md(
            guide_content,
            [
                "melhores cones",
                "armas recomendadas",
                "melhores armas",
                "melhores w-engines",
                "melhores motores",
                "motores-w",
                "motores",
                "best light cone",
                "best weapon",
                "best w-engine",
                "weapons",
            ],
        )
        for l in w_lines:
            m = _RE_BOLD_ITEM.search(l)
            if m:
                w_name = clean_meta_item_name(m.group(1))
                if (
                    w_name
                    and w_name not in weapons_list
                    and len(w_name) > 2
                    and not w_name.lower().startswith(("justificativa", "review", "rationale", "nota"))
                ):
                    weapons_list.append(w_name)

        # 2. Sets de Relíquias / Artefatos / Discos (separando Caverna vs Planares no HSR!)
        relic_lines = get_section_lines_from_md(
            guide_content,
            [
                "melhores conjuntos",
                "conjuntos de artefatos",
                "melhores relíquias",
                "melhores discos",
                "best relics",
                "best artifacts",
                "best discs",
            ],
        )
        for l in relic_lines:
            m = _RE_BOLD_ITEM.search(l)
            if m:
                s_name = clean_meta_item_name(m.group(1))
                if (
                    s_name
                    and s_name not in relic_sets_list
                    and len(s_name) > 2
                    and not is_junk_set_name(s_name)
                    and not s_name.lower().startswith(("justificativa", "review", "rationale", "nota", "disk", "disco"))
                ):
                    relic_sets_list.append(s_name)
                    if s_name not in sets_list:
                        sets_list.append(s_name)

        planar_lines = get_section_lines_from_md(
            guide_content,
            [
                "melhores ornamentos",
                "ornamentos planares",
                "best planar",
                "planar ornaments",
            ],
        )
        for l in planar_lines:
            m = _RE_BOLD_ITEM.search(l)
            if m:
                p_name = clean_meta_item_name(m.group(1))
                if (
                    p_name
                    and p_name not in planar_sets_list
                    and len(p_name) > 2
                    and not is_junk_set_name(p_name)
                    and not p_name.lower().startswith(("justificativa", "review", "rationale", "nota"))
                ):
                    planar_sets_list.append(p_name)
                    if p_name not in sets_list:
                        sets_list.append(p_name)

        # 3. Atributos Recomendados por Slot (NUNCA sobrescreve a primeira build principal!)
        stat_lines = get_section_lines_from_md(
            guide_content, ["atributos principais", "atributos recomendados", "main stats"]
        )
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
                    if any(k in raw_slot.lower() for k in ["areia", "sands", "ampulheta"]):
                        slot_label = "Areia"
                    elif any(k in raw_slot.lower() for k in ["cálice", "copo", "goblet"]):
                        slot_label = "Copo"
                    elif any(k in raw_slot.lower() for k in ["tiara", "coroa", "circlet"]):
                        slot_label = "Tiara"
                elif game_id == "hsr":
                    if any(k in raw_slot.lower() for k in ["corpo", "body"]):
                        slot_label = "Corpo"
                    elif any(k in raw_slot.lower() for k in ["bota", "pés", "feet"]):
                        slot_label = "Bota"
                    elif any(k in raw_slot.lower() for k in ["esfera", "planar sphere", "sphere"]):
                        slot_label = "Esfera"
                    elif any(k in raw_slot.lower() for k in ["corda", "link rope", "rope"]):
                        slot_label = "Corda"
                elif game_id == "zzz":
                    for d_i in range(1, 7):
                        if (
                            f"disk {d_i}" in raw_slot.lower()
                            or f"disco {d_i}" in raw_slot.lower()
                            or raw_slot == str(d_i)
                        ):
                            slot_label = f"Disco {d_i}"
                            break
                if slot_label and raw_val and slot_label not in stats_found:
                    stats_found[slot_label] = raw_val
            elif "disk" in l_str.lower() or "disco" in l_str.lower():
                for d_i in range(4, 7):
                    if f"disk {d_i}" in l_str.lower() or f"disco {d_i}" in l_str.lower():
                        raw_val = re.sub(rf"-\s*(?:disk|disco)\s*{d_i}\s*", "", l_str, flags=re.I).strip()
                        if raw_val and f"Disco {d_i}" not in stats_found:
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
                    if s_name not in endgame_stats:
                        endgame_stats[s_name] = s_val

    # Fallback / Complemento com meta_data JSON estruturado (incluindo busca por canonical_slug / guide_slug)
    char_entry = None
    c_norm = normalize_slug_text(char_name)
    guide_slug = os.path.basename(guide_path).replace(".md", "").lower() if guide_path else ""
    if meta_json:
        for cand_k in (canonical_slug, guide_slug, c_norm, char_name.lower(), char_name):
            if cand_k and cand_k in meta_json:
                char_entry = meta_json[cand_k]
                break
        if not char_entry:
            canon_norm = normalize_slug_text(canonical_slug)
            for k_m, v_m in meta_json.items():
                if isinstance(v_m, dict):
                    vn = normalize_slug_text(v_m.get("name", ""))
                    if vn and (vn == c_norm or vn == canon_norm):
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
                    stats_found[label] = " / ".join(
                        [stat_en_to_pt.get(str(x).lower().strip(), str(x)) for x in val_list]
                    )
                else:
                    stats_found[label] = stat_en_to_pt.get(str(val_list).lower().strip(), str(val_list))

    # 5. Resolução Inteligente de Benchmarks Específicos do Personagem
    from calculators.benchmark_radar import (
        deduplicate_endgame_stats,
        is_generic_placeholder_benchmark,
        standardize_main_stat_display,
    )

    char_bench = benchmarks_db.get(canonical_slug)
    if not char_bench and guide_slug:
        char_bench = benchmarks_db.get(guide_slug)
    if not char_bench:
        char_bench = benchmarks_db.get(c_norm)
    if not char_bench:
        char_bench = benchmarks_db.get(char_name.lower().strip())

    cleaned_guide_endgame = deduplicate_endgame_stats(endgame_stats, game_id=game_id)
    guide_sub_lines = get_section_lines_from_md(guide_content, ["subatributos", "substatus", "sub-stats"]) if guide_content else []
    guide_sub_text = " ".join(l.strip() for l in guide_sub_lines if l.strip())[:200]

    # Valida se o preset estático contradiz o escalonamento real do guia (ex.: pedir Vida 32k em personagem DEF/ATQ)
    if char_bench and stats_found and not is_ai_preliminary:
        if not _is_benchmark_consistent_with_guide(game_id, char_bench, stats_found, guide_sub_text):
            char_bench = None

    # Prioriza benchmarks REAIS raspados do guia oficial (não preliminares de IA) sobre presets estáticos antigos!
    if cleaned_guide_endgame and not is_ai_preliminary and len(cleaned_guide_endgame) >= 2:
        endgame_stats = cleaned_guide_endgame
    elif char_bench and not (is_generic_placeholder_benchmark(char_bench, game_id) and cleaned_guide_endgame):
        endgame_stats = deduplicate_endgame_stats(dict(char_bench), game_id=game_id)
    elif cleaned_guide_endgame:
        endgame_stats = cleaned_guide_endgame
    elif char_entry and "general_benchmarks" in char_entry and char_entry["general_benchmarks"]:
        endgame_stats = deduplicate_endgame_stats(dict(char_entry["general_benchmarks"]), game_id=game_id)
    else:
        endgame_stats = {}

    # 6. Fallback Dinâmico por Arquétipo e Kit
    if not endgame_stats:
        substats_list = list(char_entry.get("substats_priority", [])) if char_entry else []
        if guide_sub_text:
            substats_list.append(guide_sub_text)
        endgame_stats = deduplicate_endgame_stats(
            derive_dynamic_benchmarks(game_id, char_name, stats_found, substats_list),
            game_id=game_id,
        )

    # Localiza nomes de armas/sets exclusivamente via catálogo oficial HoYoVerse (sem traduzir palavra por palavra!)
    if weapons_list:
        weapons_pt = [localize_equipment_name(game_id, "weapons", w, lang="pt") for w in weapons_list]
        target["weapon"] = weapons_pt[0]
        target["weapons"] = weapons_pt
        target["weapons_raw"] = list(weapons_list)
    if sets_list:
        relic_pt = [localize_equipment_name(game_id, "sets", s, lang="pt") for s in relic_sets_list]
        planar_pt = [localize_equipment_name(game_id, "sets", s, lang="pt") for s in planar_sets_list]
        all_sets_pt = [localize_equipment_name(game_id, "sets", s, lang="pt") for s in sets_list]
        target["sets"] = [relic_pt[0]] if relic_pt else [all_sets_pt[0]]
        target["all_sets"] = all_sets_pt
        target["all_sets_raw"] = list(sets_list)
        if relic_pt:
            target["relic_sets"] = relic_pt
            target["relic_sets_raw"] = list(relic_sets_list)
        if planar_pt:
            target["planar_sets"] = planar_pt
            target["planar_sets_raw"] = list(planar_sets_list)

    target["stats"] = {
        translate(k): standardize_main_stat_display(translate(v), lang="pt")
        for k, v in stats_found.items()
    }
    target["endgame_stats"] = deduplicate_endgame_stats(
        {translate(k): translate(v) for k, v in endgame_stats.items()},
        game_id=game_id,
    )

    return target
