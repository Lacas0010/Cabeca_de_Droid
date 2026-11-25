"""
Motor padronizado de normalização de benchmarks e geração de payload para o
Gráfico Radar ("Minha Build vs. Benchmark Meta") em Genshin Impact, HSR e ZZZ.

Módulo puro e determinístico (sem I/O ou rede) para uso compartilhado entre
`meta_comparator.py`, `build_calculator.py` e `services/roster_service.py`.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple


# Whitelist estrita de atributos válidos para benchmarks finais (evita vazamento de nomes
# de personagens/notas como 'phainon', 'sunday', 'bronya' vindos de guias de speed tuning)
VALID_BENCHMARK_STATS = frozenset(
    {
        "hp_flat",
        "atk_flat",
        "def_flat",
        "spd",
        "crit_rate",
        "crit_dmg",
        "break_effect",
        "ehr",
        "res",
        "em",
        "er",
        "err",
        "healing_bonus",
        "anomaly_prof",
        "anomaly_mastery",
        "pen_pct",
        "pen_flat",
        "impact",
    }
)

# Mapa canônico para normalização de rótulos de atributos (PT-BR, EN-US, HoYoLAB e snake_case)
_BENCHMARK_KEY_ALIASES: Dict[str, str] = {
    # Vida / HP
    "hp": "hp_flat",
    "hp_flat": "hp_flat",
    "hp_pct": "hp_flat",
    "pv": "hp_flat",
    "pv_pct": "hp_flat",
    "vida": "hp_flat",
    "vida maxima": "hp_flat",
    "vida max": "hp_flat",
    "max hp": "hp_flat",
    # Ataque / ATK
    "atk": "atk_flat",
    "atk_flat": "atk_flat",
    "atk_pct": "atk_flat",
    "atq": "atk_flat",
    "ataque": "atk_flat",
    "attack": "atk_flat",
    # Defesa / DEF
    "def": "def_flat",
    "def_flat": "def_flat",
    "def_pct": "def_flat",
    "defesa": "def_flat",
    "defense": "def_flat",
    # Velocidade / SPD
    "spd": "spd",
    "speed": "spd",
    "vel": "spd",
    "velocidade": "spd",
    # Taxa Crítica
    "crit_rate": "crit_rate",
    "crit rate": "crit_rate",
    "cr": "crit_rate",
    "taxa critica": "crit_rate",
    "taxa crit": "crit_rate",
    "taxa crt": "crit_rate",
    "chance de crit": "crit_rate",
    "chance de critico": "crit_rate",
    "chance critica": "crit_rate",
    # Dano Crítico
    "crit_dmg": "crit_dmg",
    "crit dmg": "crit_dmg",
    "crit damage": "crit_dmg",
    "cd": "crit_dmg",
    "cdmg": "crit_dmg",
    "dano critico": "crit_dmg",
    "dano crit": "crit_dmg",
    "dano crt": "crit_dmg",
    # Efeito de Quebra (HSR)
    "break_effect": "break_effect",
    "break effect": "break_effect",
    "be": "break_effect",
    "efeito de quebra": "break_effect",
    "quebra": "break_effect",
    # Acerto de Efeito (HSR)
    "ehr": "ehr",
    "effect hit rate": "ehr",
    "effect hit rating": "ehr",
    "taxa de acerto de efeito": "ehr",
    "chance de acerto de efeito": "ehr",
    "chance de acerto": "ehr",
    "acerto de efeito": "ehr",
    "acerto efeito": "ehr",
    # Resistência a Efeito (HSR)
    "res": "res",
    "effect res": "res",
    "effect resistance": "res",
    "resistencia a efeito": "res",
    "res efeito": "res",
    "res a efeito": "res",
    "res_efeito": "res",
    # Proficiência Elemental (Genshin)
    "em": "em",
    "elemental mastery": "em",
    "elemental_mastery": "em",
    "proficiencia elemental": "em",
    "proficiencia": "em",
    "maestria elemental": "em",
    # Recarga de Energia (Genshin)
    "er": "er",
    "energy recharge": "er",
    "energy_recharge": "er",
    "recarga de energia": "er",
    "recarga": "er",
    # Regeneração / Recuperação de Energia (HSR / ZZZ)
    "err": "err",
    "energy regen": "err",
    "energy_regen": "err",
    "energy regeneration": "err",
    "energy regeneration rate": "err",
    "taxa de regeneracao de energia": "err",
    "taxa de regen energia": "err",
    "regen energia": "err",
    "regeneracao de energia": "err",
    "recuperacao de energia": "err",
    "recup energia": "err",
    "rec de energia": "err",
    # Bônus de Cura
    "healing": "healing_bonus",
    "healing_bonus": "healing_bonus",
    "healing bonus": "healing_bonus",
    "outgoing healing": "healing_bonus",
    "outgoing_healing": "healing_bonus",
    "bonus de cura": "healing_bonus",
    "bonus de cura realizada": "healing_bonus",
    "cura realizada": "healing_bonus",
    "cura": "healing_bonus",
    # ZZZ Específicos
    "anomaly_prof": "anomaly_prof",
    "anomaly proficiency": "anomaly_prof",
    "ap": "anomaly_prof",
    "proficiencia de anomalia": "anomaly_prof",
    "prof anomalia": "anomaly_prof",
    "anomaly_mastery": "anomaly_mastery",
    "anomaly mastery": "anomaly_mastery",
    "am": "anomaly_mastery",
    "maestria de anomalia": "anomaly_mastery",
    "maest anomalia": "anomaly_mastery",
    "controle de anomalia": "anomaly_mastery",
    "taxa de controle de anomalia": "anomaly_mastery",
    "pen_pct": "pen_pct",
    "pen ratio": "pen_pct",
    "taxa de perfuracao": "pen_pct",
    "taxa de pen": "pen_pct",
    "taxa pen": "pen_pct",
    "pen_flat": "pen_flat",
    "pen": "pen_flat",
    "perfuracao": "pen_flat",
    "impact": "impact",
    "impacto": "impact",
    "impactoo": "impact",
}

# Metadados de exibição (PT-BR / EN-US + rótulo curto para vértices do Radar SVG)
_STAT_DISPLAY_META: Dict[str, Dict[str, Any]] = {
    "hp_flat": {"pt": "Vida", "en": "HP", "short_pt": "Vida", "short_en": "HP", "pct": False},
    "atk_flat": {"pt": "ATQ", "en": "ATK", "short_pt": "ATQ", "short_en": "ATK", "pct": False},
    "def_flat": {"pt": "DEF", "en": "DEF", "short_pt": "DEF", "short_en": "DEF", "pct": False},
    "spd": {"pt": "VEL", "en": "SPD", "short_pt": "VEL", "short_en": "SPD", "pct": False},
    "crit_rate": {"pt": "Taxa Crítica", "en": "CRIT Rate", "short_pt": "Taxa CRIT", "short_en": "CRIT Rate", "pct": True},
    "crit_dmg": {"pt": "Dano Crítico", "en": "CRIT DMG", "short_pt": "Dano CRIT", "short_en": "CRIT DMG", "pct": True},
    "break_effect": {"pt": "Efeito de Quebra", "en": "Break Effect", "short_pt": "Quebra", "short_en": "Break", "pct": True},
    "ehr": {"pt": "Acerto de Efeito", "en": "Effect Hit Rate", "short_pt": "Acerto Ef.", "short_en": "EHR", "pct": True},
    "res": {"pt": "Resistência a Efeito", "en": "Effect RES", "short_pt": "RES Ef.", "short_en": "Eff. RES", "pct": True},
    "em": {"pt": "Proficiência Elemental", "en": "Elemental Mastery", "short_pt": "Prof. Elem.", "short_en": "EM", "pct": False},
    "er": {"pt": "Recarga de Energia", "en": "Energy Recharge", "short_pt": "Recarga", "short_en": "ER", "pct": True},
    "err": {"pt": "Taxa de Regen. Energia", "en": "Energy Regen", "short_pt": "Regen. En.", "short_en": "ERR", "pct": True},
    "healing_bonus": {"pt": "Bônus de Cura", "en": "Healing Bonus", "short_pt": "Cura", "short_en": "Healing", "pct": True},
    "anomaly_prof": {"pt": "Proficiência de Anomalia", "en": "Anomaly Proficiency", "short_pt": "Prof. Anom.", "short_en": "AP", "pct": False},
    "anomaly_mastery": {"pt": "Maestria de Anomalia", "en": "Anomaly Mastery", "short_pt": "Maest. Anom.", "short_en": "AM", "pct": False},
    "pen_pct": {"pt": "Taxa de Perfuração", "en": "PEN Ratio", "short_pt": "Perf. %", "short_en": "PEN%", "pct": True},
    "pen_flat": {"pt": "Perfuração", "en": "PEN", "short_pt": "Perfuração", "short_en": "PEN", "pct": False},
    "impact": {"pt": "Impacto", "en": "Impact", "short_pt": "Impacto", "short_en": "Impact", "pct": False},
}

# Placeholders genéricos legados de character_benchmarks.json que devem ceder lugar
# a benchmarks reais raspados do guia oficial (HSR e ZZZ: Evanescia, Sigrid, Claret, Trigger, etc.)
GENERIC_BENCHMARK_PLACEHOLDERS: Dict[str, List[Dict[str, str]]] = {
    "hsr": [
        {"ATQ": "3.000+", "Taxa Crítica": "70%+", "Dano Crítico": "150%+"},
        {"ATQ": "3.000+", "Taxa Crítica": "75%+", "Dano Crítico": "150%+"},
    ],
    "zzz": [
        {"Taxa CRIT": "65%+", "Dano CRIT": "140%+", "ATQ": "2.600+"},
        {"Taxa CRIT": "70%+", "Dano CRIT": "150%+", "ATQ": "2.700+"},
        {"Taxa CRIT": "70%+", "Dano CRIT": "140%+", "ATQ": "2.700+"},
        {"Taxa CRIT": "70%+", "Dano CRIT": "150%+", "ATQ": "2.800+"},
        {"Taxa CRIT": "65%+", "Dano CRIT": "150%+", "ATQ": "2.600+"},
        {"Impacto": "170+", "ATQ": "2.200+"},
        {"Proficiência de Anomalia": "380+", "ATQ": "2.600+"},
        {"Proficiência de Anomalia": "380+", "ATQ": "2.700+"},
    ],
}

# Prioridade dos eixos para manter o polígono SVG entre 3 e 6 vértices mais relevantes
MAX_RADAR_POLYGON_AXES = 6
_AXIS_PLOT_PRIORITY: Dict[str, int] = {
    "crit_rate": 100,
    "crit_dmg": 99,
    "spd": 98,
    "break_effect": 96,
    "anomaly_prof": 95,
    "anomaly_mastery": 94,
    "em": 93,
    "impact": 92,
    "ehr": 91,
    "er": 90,
    "err": 89,
    "pen_pct": 88,
    "healing_bonus": 87,
    "atk_flat": 82,
    "hp_flat": 70,
    "def_flat": 65,
    "res": 60,
    "pen_flat": 58,
}

_RE_PARENS = re.compile(r"\([^)]*\)")
_RE_THOUSANDS_DOT = re.compile(r"\b(\d{1,3}(?:\.\d{3})+)(?!\d)")
_RE_THOUSANDS_COMMA = re.compile(r"\b(\d{1,3}(?:,\d{3})+)(?!\d)")
_RE_DECIMAL_COMMA = re.compile(r"(\d),(\d{1,2})(?!\d)")
_RE_NUMBER = re.compile(r"\d+(?:\.\d+)?")
_RE_RANGE = re.compile(r"(\d+(?:\.\d+)?)\s*%?\s*[-–—~]\s*(\d+(?:\.\d+)?)\s*%?")
_RE_RECOMMENDED_TIER = re.compile(
    r"(\d+(?:\.\d+)?)\s*%?\+?\s*\(\s*(?:recommended|recomendado|best|ideal)\s*\)",
    re.IGNORECASE,
)
_RE_RELATIVE_SPD = re.compile(
    r"\b\d+(?:\s*[-–—]\s*\d+)?\s*(?:spd|speed|vel(?:ocidade)?)\s*(?:slower|faster|mais\s+lent[oa]|mais\s+r[aá]pid[oa])[^/,;]*",
    re.IGNORECASE,
)
_RE_OUT_OF_COMBAT_SEG = re.compile(
    r"(\d+(?:\.\d+)?)\s*%?\+?\s*(?:\(\s*(?:outside\s+of\s+combat|out\s+of\s+combat|pre[- ]?combat|before\s+combat|fora\s+de\s+combate)\s*\)|before\s+[^(/,;]+)",
    re.IGNORECASE,
)
_RE_PRE_COMBAT_PREFIX = re.compile(
    r"(?:outside\s+of\s+combat|out\s+of\s+combat|pre[- ]?combat|before\s+combat|fora\s+de\s+combate)\s*[:\-]?\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_RE_AT_LEAST_OOC = re.compile(r"(?:need\s+)?at\s+least\s+(\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
_RE_IN_COMBAT_ONLY = re.compile(
    r"\bin[- ]?(?:combat|battle)\b|\bem\s+(?:combate|batalha)\b|\bincluding\s+(?:the\s+)?(?:passiva|passive|trace|disc\s+drive|add\s+ability|bonus)\b",
    re.IGNORECASE,
)
_RE_PRE_COMBAT_TAG = re.compile(
    r"\b(?:pre[- ]?combat|outside\s+of\s+combat|out\s+of\s+combat|before\s+combat|before\s+trace|before\s+[a-z])\b",
    re.IGNORECASE,
)
_RE_OVERCAP_CAP = re.compile(
    r"\bovercap\w*\b|\bnot\s+more\b|\bdo\s+not\s+exceed\b|\bno\s+more\s+than\b|\bany\s+more\b|\bcaps?\s+out\b",
    re.IGNORECASE,
)
_RE_BASE_OPTION = re.compile(r"\bbase(?:\s*(?:spd|speed|vel(?:ocidade)?))?\b", re.IGNORECASE)
_RE_OPTIONAL = re.compile(r"\b(?:optional|opcional)\b|^\s*0%?\s*(?:or|ou|/|-)\s*", re.IGNORECASE)
_RE_FLEX_WORD = re.compile(
    r"\b(?:anything|any|qualquer(?:\s+um|\s+atributo)?|flex(?:ible|ível)?|varies|depends|n/?a|none|as\s+much\s+as\s+is\s+needed|whatever)\b",
    re.IGNORECASE,
)
_RE_MAIN_ANY_PARENS = re.compile(r"\(\s*(?:anything|any|qualquer|flex(?:ible)?)\s*\)", re.IGNORECASE)
_RE_MAIN_ANY_TOKEN = re.compile(r"\b(?:anything|any)\b", re.IGNORECASE)
_RE_SNAKE_RAW = re.compile(r"^[a-z]+_[a-z]+$")
_RE_LEAD_VALUE_CHUNK = re.compile(
    r"^([<>=\s]*\d[\d\.,]*%?\+?(?:\s*(?:[-–—~/]|or|ou)\s*\d[\d\.,]*%?\+?)*)(?:\s*(\([^)]{1,45}\)))?",
    re.IGNORECASE,
)


def _strip_accents(text: str) -> str:
    if not text:
        return ""
    return "".join(c for c in unicodedata.normalize("NFKD", str(text)) if not unicodedata.combining(c))


def normalize_numeric_string(raw: str) -> str:
    """Padroniza separadores de milhar (3.000 -> 3000, 1,600 -> 1600) preservando decimais (2.88, 19.4)."""
    if not raw:
        return ""
    s = str(raw)
    s = _RE_THOUSANDS_DOT.sub(lambda m: m.group(1).replace(".", ""), s)
    s = _RE_THOUSANDS_COMMA.sub(lambda m: m.group(1).replace(",", ""), s)
    s = _RE_DECIMAL_COMMA.sub(r"\1.\2", s)
    return s


def parse_stat_number(raw: Any) -> Optional[float]:
    """Extrai o primeiro número real de uma string de atributo tratando separador de milhar PT-BR."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = normalize_numeric_string(str(raw).strip())
    m = _RE_NUMBER.search(s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def canonicalize_benchmark_key(raw_key: str, game_id: str = "") -> str:
    """Converte qualquer nome de status (PT/EN/HoYoLAB/snake_case) na chave canônica ou '' se inválido."""
    if not raw_key:
        return ""
    s = str(raw_key).replace("**", "").replace("`", "").replace("%", "")
    s = _RE_PARENS.sub("", s)
    if ":" in s:
        s = s.split(":", 1)[0]
    clean = _strip_accents(s).lower().strip()
    clean = re.sub(r"[\.\-]+", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    key = _BENCHMARK_KEY_ALIASES.get(clean)
    if not key:
        clean_underscored = clean.replace(" ", "_")
        key = _BENCHMARK_KEY_ALIASES.get(clean_underscored, "")

    if not key:
        return ""

    # Em HSR e ZZZ, "ER" no texto do guia refere-se a Energy Regen (err)
    g = (game_id or "").lower().strip()
    if key == "er" and g in ("hsr", "zzz"):
        key = "err"
    elif key == "err" and g == "genshin":
        key = "er"

    return key if key in VALID_BENCHMARK_STATS else ""


def format_benchmark_label(stat_key: str, game_id: str = "", lang: str = "pt", short: bool = False) -> str:
    """Retorna rótulo limpo e padronizado de um stat canônico."""
    meta = _STAT_DISPLAY_META.get(stat_key)
    if not meta:
        return stat_key
    is_en = str(lang or "pt").lower().startswith("en")
    if short:
        return meta["short_en"] if is_en else meta["short_pt"]
    if not is_en:
        g = (game_id or "").lower().strip()
        if g == "zzz":
            if stat_key == "crit_rate":
                return "Taxa CRIT"
            if stat_key == "crit_dmg":
                return "Dano CRIT"
            if stat_key == "err":
                return "Recuperação de Energia"
    return meta["en"] if is_en else meta["pt"]


def deduplicate_endgame_stats(endgame_stats: Dict[str, Any], game_id: str = "") -> Dict[str, str]:
    """
    Remove chaves duplicadas (ex.: 'Taxa CRIT' + 'Taxa Crítica'), filtra chaves inválidas
    (ex.: nomes de personagens como 'phainon'/'sunday') e substitui chaves snake_case cruas
    por rótulos legíveis.
    """
    if not endgame_stats or not isinstance(endgame_stats, dict):
        return {}

    cleaned: Dict[str, str] = {}
    seen_canonical: set = set()

    for raw_k, raw_v in endgame_stats.items():
        if raw_v is None:
            continue
        val_str = str(raw_v).strip()
        if not val_str:
            continue

        canon = canonicalize_benchmark_key(str(raw_k), game_id=game_id)
        if not canon or canon in seen_canonical:
            continue
        seen_canonical.add(canon)

        raw_k_str = str(raw_k).strip()
        # Substitui chaves cruas em snake_case/inglês técnico (hp_flat, ehr, break_effect, effect hit rating)
        raw_k_low = raw_k_str.lower()
        needs_pretty_label = (
            bool(_RE_SNAKE_RAW.match(raw_k_str))
            or raw_k_low in ("ehr", "err", "er", "em", "be", "res", "hp", "atk", "spd", "speed", "crit rate", "crit dmg", "effect hit rate", "effect hit rating", "energy regen", "energy regeneration", "break effect")
        )
        display_key = format_benchmark_label(canon, game_id=game_id, lang="pt") if needs_pretty_label else raw_k_str
        cleaned[display_key] = val_str

    return cleaned


def standardize_main_stat_display(raw_val: str, lang: str = "pt") -> str:
    """
    Padroniza expressões curinga nos Main Stats (ex.: 'Anything', 'PV% / Anything',
    'DEF% (Anything)') de forma idempotente para exibição consistente na UI.
    """
    if not raw_val:
        return ""
    s = str(raw_val).strip()
    is_en = str(lang).lower().startswith("en")
    flex_label = "Any (Flex)" if is_en else "Qualquer (Flex)"

    # Idempotência: se já estiver padronizado em PT ou EN, apenas ajusta o idioma
    if re.search(r"\b(?:Qualquer|Any)\s*\(Flex\)", s, flags=re.IGNORECASE):
        s = re.sub(r"\b(?:Qualquer|Any)\s*\(Flex\)", flex_label, s, flags=re.IGNORECASE)
        return re.sub(r"\s{2,}", " ", s).strip()

    # Caso especial Xilonen: "DEF% (Anything)" -> "DEF% / Qualquer (Flex)"
    if _RE_MAIN_ANY_PARENS.search(s):
        base = _RE_MAIN_ANY_PARENS.sub("", s).strip(" /,-")
        return f"{base} / {flex_label}" if base else flex_label

    if _RE_MAIN_ANY_TOKEN.search(s):
        s = _RE_MAIN_ANY_TOKEN.sub(flex_label, s)

    return re.sub(r"\s{2,}", " ", s).strip()


def is_generic_placeholder_benchmark(bench: Optional[Dict[str, Any]], game_id: str = "hsr") -> bool:
    """Detecta se o registro de character_benchmarks.json é apenas um placeholder genérico de HSR/ZZZ."""
    if not bench or not isinstance(bench, dict):
        return False
    g = (game_id or "hsr").lower().strip()
    return any(bench == tpl for tpl in GENERIC_BENCHMARK_PLACEHOLDERS.get(g, []))


def is_generic_hsr_placeholder(bench: Optional[Dict[str, Any]]) -> bool:
    """Alias retrocompatível para detecção de placeholder genérico de HSR."""
    return is_generic_placeholder_benchmark(bench, game_id="hsr")


def parse_benchmark_spec(stat_key: str, raw_expr: str, game_id: str = "") -> Dict[str, Any]:
    """
    Converte expressões reais de guias Prydwen/KQM/Game8 em uma especificação numérica/semântica
    padronizada (suportando ranges, milhar PT-BR, in-combat/in-battle, overcap/cap de passiva,
    Base SPD, relative SPD, 'Anything'/'Base', 'As high as possible (160-200)', e opcionais).
    """
    raw_str = str(raw_expr or "").strip()
    norm_str = normalize_numeric_string(raw_str)
    meta = _STAT_DISPLAY_META.get(stat_key, {})
    is_percent = ("%" in raw_str) or bool(meta.get("pct", False))

    # Em ZZZ, Recuperação de Energia do jogo é flat (ex.: 2.88+), exceto quando explicitamente em %
    if (game_id or "").lower() == "zzz" and stat_key in ("er", "err") and "%" not in raw_str:
        is_percent = False

    operator = ">="
    if "<=" in raw_str:
        operator = "<="
    elif "<" in raw_str:
        operator = "<"
    elif ">" in raw_str and ">=" not in raw_str:
        operator = ">"

    tags: List[str] = []
    has_base_option = bool(_RE_BASE_OPTION.search(norm_str))
    is_optional = bool(_RE_OPTIONAL.search(norm_str))
    is_cap = bool(_RE_OVERCAP_CAP.search(norm_str))
    is_relative = bool(_RE_RELATIVE_SPD.search(norm_str)) or bool(
        re.search(r"\b(?:slower|faster)\s+than\b", norm_str, re.IGNORECASE)
    )

    if is_optional:
        tags.append("optional")
    if is_relative:
        tags.append("relative")
    if is_cap:
        tags.append("cap")

    # 1. Remove cláusulas relativas tipo "1-2 Speed slower than carry" antes de buscar números
    working = _RE_RELATIVE_SPD.sub(" ", norm_str).strip()

    # Caso puramente "Base" / "Anything" / "Any" / texto descritivo sem números
    has_any_digit = bool(_RE_NUMBER.search(working))
    if not has_any_digit:
        mode = "relative" if is_relative else "flexible"
        if mode == "flexible" and "flex" not in tags:
            tags.append("flex")
        return {
            "stat_key": stat_key,
            "raw_target": raw_str,
            "mode": mode,
            "target_min": None,
            "target_ideal": None,
            "is_percent": is_percent,
            "is_flexible": True,
            "has_base_option": has_base_option,
            "is_in_combat": False,
            "is_cap": is_cap,
            "is_optional": is_optional,
            "operator": operator,
            "tags": tags,
        }

    target_min: Optional[float] = None
    target_ideal: Optional[float] = None
    is_in_combat = False

    # 2. Caso explícito "at least X%" fora de combate junto a passiva (ex.: Evelyn: "80-100% (including Passiva...) she'll need at least 55%")
    m_at_least = _RE_AT_LEAST_OOC.search(working)
    if m_at_least and _RE_IN_COMBAT_ONLY.search(working):
        target_min = float(m_at_least.group(1))
        tags.append("pre_combat")
    else:
        # 2b. Caso explícito Out-of-Combat / Pre-Combat / Before Combat / Before Passive
        m_ooc = _RE_OUT_OF_COMBAT_SEG.search(working) or _RE_PRE_COMBAT_PREFIX.search(working)
        if m_ooc:
            target_min = float(m_ooc.group(1))
            tags.append("pre_combat")
        elif _RE_IN_COMBAT_ONLY.search(working) and not _RE_PRE_COMBAT_TAG.search(working):
            # Ex.: "79.4% (with Signature W-Engine), 100% in Combat" -> prioriza o valor fora de combate antes da vírgula
            parts_comma = [p.strip() for p in re.split(r"[,/]", working) if p.strip()]
            non_combat_part = next(
                (p for p in parts_comma if _RE_NUMBER.search(p) and not _RE_IN_COMBAT_ONLY.search(p)),
                None,
            )
            if non_combat_part:
                clean_nc = _RE_PARENS.sub(" ", non_combat_part)
                nums_nc = [float(x) for x in _RE_NUMBER.findall(clean_nc)]
                if nums_nc:
                    target_min = nums_nc[0]
                    if len(nums_nc) >= 2 and nums_nc[1] > nums_nc[0]:
                        target_ideal = nums_nc[1]
                    tags.append("pre_combat")
            if target_min is None:
                is_in_combat = True
                tags.append("in_combat")

    # 3. Tier marcado explicitamente como (Recommended) / (Best)
    if target_min is None:
        m_rec = _RE_RECOMMENDED_TIER.search(working)
        if m_rec:
            target_min = float(m_rec.group(1))
            outer_nums = [float(x) for x in _RE_NUMBER.findall(_RE_PARENS.sub(" ", working))]
            higher = [x for x in outer_nums if x > target_min]
            if higher:
                target_ideal = max(higher)

    # 4. Expressões com parênteses (ex.: "33.8% (any more and she'll overcap...)", "As high as possible ( 160-200 )")
    if target_min is None:
        outer_clean = _RE_PARENS.sub(" ", working).strip()
        # Se houver prosa explicativa longa após o valor inicial (ex.: Astra Yao "3430+ Astra requires..."), foca no cabeçalho numérico
        m_lead = _RE_LEAD_VALUE_CHUNK.match(outer_clean)
        if m_lead and len(outer_clean) > 45:
            outer_clean = m_lead.group(1).strip()

        outer_clean = re.sub(r"^\s*0%?\s*(?:or|ou|/)\s*", "", outer_clean, flags=re.IGNORECASE).strip()

        m_range = _RE_RANGE.search(outer_clean)
        if m_range:
            lo, hi = float(m_range.group(1)), float(m_range.group(2))
            if lo == 0.0 and hi > 0.0:
                target_min = hi
                is_optional = True
                if "optional" not in tags:
                    tags.append("optional")
            else:
                target_min = min(lo, hi)
                target_ideal = max(lo, hi)
        else:
            outer_nums = [float(x) for x in _RE_NUMBER.findall(outer_clean)]
            if outer_nums:
                if has_base_option and len(outer_nums) >= 2 and outer_nums[0] < 115 and outer_nums[-1] >= 120:
                    target_min = outer_nums[1]
                    if len(outer_nums) > 2:
                        target_ideal = max(outer_nums)
                else:
                    target_min = outer_nums[0]
                    if len(outer_nums) >= 2 and max(outer_nums) > target_min:
                        target_ideal = max(outer_nums)
            else:
                m_paren_range = _RE_RANGE.search(working)
                if m_paren_range:
                    lo, hi = float(m_paren_range.group(1)), float(m_paren_range.group(2))
                    target_min, target_ideal = min(lo, hi), max(lo, hi)
                else:
                    all_nums = [float(x) for x in _RE_NUMBER.findall(working)]
                    if all_nums:
                        target_min = all_nums[0]
                        if len(all_nums) >= 2 and max(all_nums) > target_min:
                            target_ideal = max(all_nums)

    if has_base_option and stat_key == "spd":
        tags.append("base_ok")

    if target_min is None or target_min <= 0:
        is_flex = bool(_RE_FLEX_WORD.search(working)) or is_optional or has_base_option or is_relative
        if is_flex and "flex" not in tags:
            tags.append("flex")
        return {
            "stat_key": stat_key,
            "raw_target": raw_str,
            "mode": "flexible",
            "target_min": None,
            "target_ideal": None,
            "is_percent": is_percent,
            "is_flexible": True,
            "has_base_option": has_base_option,
            "is_in_combat": is_in_combat,
            "is_cap": is_cap,
            "is_optional": is_optional,
            "operator": operator,
            "tags": tags,
        }

    mode = (
        "cap"
        if is_cap
        else ("base_or_target" if (has_base_option and stat_key == "spd") else ("range" if target_ideal and target_ideal > target_min else "numeric"))
    )
    if mode == "range" and "range" not in tags:
        tags.append("range")

    return {
        "stat_key": stat_key,
        "raw_target": raw_str,
        "mode": mode,
        "target_min": round(target_min, 2),
        "target_ideal": round(target_ideal, 2) if target_ideal else None,
        "is_percent": is_percent,
        "is_flexible": False,
        "has_base_option": has_base_option,
        "is_in_combat": is_in_combat,
        "is_cap": is_cap,
        "is_optional": is_optional,
        "operator": operator,
        "tags": tags,
    }


def _align_target_scale(
    game_id: str,
    stat_key: str,
    target_min: Optional[float],
    target_ideal: Optional[float],
    actual_val: Optional[float],
    raw_target: str,
    actual_str: str,
) -> Tuple[Optional[float], Optional[float], bool]:
    """
    Alinha divergências de escala entre guias e a API do HoYoLAB:
    - HSR ERR: HoYoLAB reporta base 100% (ex.: 119.4%), enquanto alguns guias listam bônus (+19.4%).
    - ZZZ ER: HoYoLAB reporta regen flat/s (ex.: 1.20–3.12), enquanto legados listam bônus % (25%+).
    """
    if target_min is None:
        return target_min, target_ideal, "%" in raw_target

    g = (game_id or "").lower().strip()
    is_pct = ("%" in raw_target) or ("%" in str(actual_str or ""))

    if g == "hsr" and stat_key == "err" and actual_val is not None:
        if 0 < target_min < 60.0 and actual_val >= 95.0:
            adj_min = round(100.0 + target_min, 2)
            adj_ideal = round(100.0 + target_ideal, 2) if (target_ideal is not None and target_ideal < 60.0) else target_ideal
            return adj_min, adj_ideal, True

    if g == "zzz" and stat_key in ("er", "err") and actual_val is not None:
        if "%" in raw_target and "%" not in str(actual_str or "") and actual_val < 15.0 and target_min >= 10.0:
            adj_min = round(1.20 * (1.0 + target_min / 100.0), 2)
            adj_ideal = round(1.20 * (1.0 + target_ideal / 100.0), 2) if target_ideal is not None else None
            return adj_min, adj_ideal, False

    return target_min, target_ideal, is_pct


def _localize_target_display(raw_target: str, lang: str = "pt", spec: Optional[Dict[str, Any]] = None) -> str:
    """Padroniza, compacta prosa longa e traduz expressões comuns de benchmarks de guias (PT-BR / EN-US)."""
    s = str(raw_target or "").strip()
    if not s:
        return s

    # Compacta explicações longas vindas de guias Prydwen (ex.: Sigrid, Astra Yao, Vivian, Trigger, Evelyn)
    if len(s) > 48:
        m_lead = _RE_LEAD_VALUE_CHUNK.match(s)
        if m_lead:
            core = m_lead.group(1).strip()
            short_paren = (m_lead.group(2) or "").strip()
            if spec and spec.get("is_cap"):
                s = f"{core} (Cap)"
            elif spec and "pre_combat" in (spec.get("tags") or []) and spec.get("target_min"):
                is_pct = bool(spec.get("is_percent"))
                t_str = _format_num_display(float(spec["target_min"]), is_pct)
                s = f"{t_str} (fora de combate)" if not str(lang).lower().startswith("en") else f"{t_str} (out of combat)"
            elif short_paren and len(short_paren) <= 28:
                s = f"{core} {short_paren}"
            else:
                s = core

    is_en = str(lang or "pt").lower().startswith("en")
    if is_en:
        s = re.sub(r"\bBase\s+VEL\b", "Base SPD", s, flags=re.IGNORECASE)
        s = re.sub(r"\bQualquer\s*\(Flex\)", "Any (Flex)", s, flags=re.IGNORECASE)
        s = re.sub(r"\(\s*(\d+)\s*-\s*(\d+)\s*\)", r"(\1–\2)", s)
        return re.sub(r"\s{2,}", " ", s).strip()

    # PT-BR
    if re.fullmatch(r"base", s, flags=re.IGNORECASE):
        return "Base (Flexível)"
    if re.fullmatch(r"anything|any|flex(?:ible)?", s, flags=re.IGNORECASE):
        return "Qualquer (Flex)"
    s = re.sub(r"\bBase\s+(?:SPD|Speed|VEL)\b", "VEL Base", s, flags=re.IGNORECASE)
    s = re.sub(r"\bBase\s+or\b", "Base ou", s, flags=re.IGNORECASE)
    s = re.sub(r"\bor\b", "ou", s, flags=re.IGNORECASE)
    s = re.sub(r"\(\s*in[- ]?(?:combat|battle)\s*\)", "(em combate)", s, flags=re.IGNORECASE)
    s = re.sub(r"\bin[- ]?(?:combat|battle)\b", "em combate", s, flags=re.IGNORECASE)
    s = re.sub(r"\(\s*(?:pre[- ]?combat|before\s+combat)\s*\)", "(pré-combate)", s, flags=re.IGNORECASE)
    s = re.sub(r"\(\s*outside\s+of\s+combat\s*\)", "(fora de combate)", s, flags=re.IGNORECASE)
    s = re.sub(r"\(\s*not\s+more\s*\)", "(Cap máx.)", s, flags=re.IGNORECASE)
    s = re.sub(r"\(\s*recommended\s*\)", "(Recomendado)", s, flags=re.IGNORECASE)
    s = re.sub(r"\(\s*optional\s*\)", "(Opcional)", s, flags=re.IGNORECASE)
    s = re.sub(r"\(\s*best\s*\)", "(Melhor)", s, flags=re.IGNORECASE)
    s = re.sub(r"as\s+high\s+as\s+possible", "Máximo possível", s, flags=re.IGNORECASE)
    s = re.sub(r"before\s+trace(?:\s+buff)?", "antes do Rastro", s, flags=re.IGNORECASE)
    s = re.sub(r"after\s+buffs", "após buffs", s, flags=re.IGNORECASE)
    s = re.sub(r"slower\s+than\s+carry", "mais lento que o DPS", s, flags=re.IGNORECASE)
    s = re.sub(r"slower\s+than\s+sustain", "mais lento que o sustain", s, flags=re.IGNORECASE)
    s = re.sub(r"faster\s+than\s+your\s+booster", "mais rápido que o suporte", s, flags=re.IGNORECASE)
    s = re.sub(r"\(\s*(\d+)\s*-\s*(\d+)\s*\)", r"(\1–\2)", s)
    return re.sub(r"\s{2,}", " ", s).strip()


def _format_num_display(val: float, is_percent: bool) -> str:
    if is_percent:
        return f"{val:.1f}%"
    if val >= 100:
        return f"{int(round(val))}"
    if float(val).is_integer():
        return f"{int(val)}"
    return f"{val:.2f}"


def _format_diff_display(diff: float, is_percent: bool, target_min: float) -> str:
    sign = "+" if diff >= 0 else ""
    if is_percent:
        return f"{sign}{diff:.1f}%"
    if target_min < 20:
        return f"{sign}{diff:.2f}"
    return f"{sign}{int(round(diff))}"


def match_player_stat(
    player_stats: Dict[str, Any], stat_key: str, game_id: str = ""
) -> Tuple[Optional[str], Optional[str], Optional[float]]:
    """Localiza um stat canônico dentro do dicionário player_stats vindo do HoYoLAB/SQLite."""
    if not player_stats or not isinstance(player_stats, dict):
        return None, None, None

    for p_key, p_val in player_stats.items():
        if canonicalize_benchmark_key(str(p_key), game_id=game_id) == stat_key:
            val_str = str(p_val).strip()
            return str(p_key), val_str, parse_stat_number(val_str)

    # Fallback para ER <-> ERR caso a chave venha trocada entre jogos
    if stat_key in ("er", "err"):
        alt = "err" if stat_key == "er" else "er"
        for p_key, p_val in player_stats.items():
            if canonicalize_benchmark_key(str(p_key), game_id=game_id) == alt:
                val_str = str(p_val).strip()
                return str(p_key), val_str, parse_stat_number(val_str)

    return None, None, None


def build_radar_benchmark_payload(
    game_id: str,
    char_name: str,
    player_stats: Optional[Dict[str, Any]],
    endgame_stats: Optional[Dict[str, Any]],
    main_stats: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Constrói o payload estruturado completo para o Gráfico Radar 'Minha Build vs. Benchmark Meta'
    no #build-inspector, incluindo eixos normalizados, casos especiais (Anything/Flex nos main stats
    ou benchmarks, Base SPD, In-Combat, Cap/Overcap, Opcional, Ranges) e pontuação unificada de 20 pontos.
    """
    g = (game_id or "").lower().strip()
    p_stats = player_stats or {}
    clean_endgame = deduplicate_endgame_stats(endgame_stats or {}, game_id=g)

    axes: List[Dict[str, Any]] = []
    flex_notes: List[Dict[str, Any]] = []

    met_count = 0
    close_count = 0
    low_count = 0
    flex_count = 0
    scored_ratios: List[float] = []
    radar_ratio_sum = 0.0
    radar_ratio_count = 0

    for display_k, raw_target in clean_endgame.items():
        stat_key = canonicalize_benchmark_key(display_k, game_id=g)
        if not stat_key:
            continue

        spec = parse_benchmark_spec(stat_key, raw_target, game_id=g)
        matched_key, actual_str, actual_num = match_player_stat(p_stats, stat_key, game_id=g)

        label_pt = format_benchmark_label(stat_key, game_id=g, lang="pt")
        label_en = format_benchmark_label(stat_key, game_id=g, lang="en")
        short_pt = format_benchmark_label(stat_key, game_id=g, lang="pt", short=True)
        short_en = format_benchmark_label(stat_key, game_id=g, lang="en", short=True)

        # Caso puramente flexível / relativo sem meta numérica absoluta (ex.: Anything, Base, 1-2 SPD slower)
        if spec["is_flexible"] or spec["target_min"] is None:
            flex_count += 1
            scored_ratios.append(1.0)
            flex_notes.append(
                {
                    "stat_key": stat_key,
                    "label_pt": label_pt,
                    "label_en": label_en,
                    "short_pt": short_pt,
                    "short_en": short_en,
                    "actual_display": actual_str or "—",
                    "actual_num": actual_num,
                    "target_display": _localize_target_display(raw_target, "pt"),
                    "target_display_pt": _localize_target_display(raw_target, "pt"),
                    "target_display_en": _localize_target_display(raw_target, "en"),
                    "mode": spec["mode"],
                    "status": "flex",
                    "tags": spec["tags"],
                }
            )
            continue

        eff_min, eff_ideal, is_pct = _align_target_scale(
            g, stat_key, spec["target_min"], spec["target_ideal"], actual_num, raw_target, actual_str or ""
        )

        # Monta exibição limpa da meta alinhada (ex.: 19.4%+ -> 119.4%+ em HSR quando alinhado)
        target_display_pt = _localize_target_display(raw_target, "pt", spec=spec)
        target_display_en = _localize_target_display(raw_target, "en", spec=spec)
        if g == "hsr" and stat_key == "err" and eff_min is not None and spec["target_min"] is not None and eff_min != spec["target_min"]:
            target_display_pt = f"{_format_num_display(eff_min, True)}+ (Base 100% + {raw_target})"
            target_display_en = f"{_format_num_display(eff_min, True)}+ (Base 100% + {raw_target})"
        elif g == "zzz" and stat_key in ("er", "err") and eff_min is not None and spec["target_min"] is not None and eff_min != spec["target_min"]:
            target_display_pt = f"{_format_num_display(eff_min, False)}+ ({raw_target})"
            target_display_en = f"{_format_num_display(eff_min, False)}+ ({raw_target})"
        target_clean_display = target_display_pt
        tooltip_note = raw_target if len(raw_target) > len(target_display_pt) + 6 else ""

        if actual_num is None or eff_min is None or eff_min <= 0:
            low_count += 1
            scored_ratios.append(0.0)
            axes.append(
                {
                    "stat_key": stat_key,
                    "label_pt": label_pt,
                    "label_en": label_en,
                    "short_pt": short_pt,
                    "short_en": short_en,
                    "actual_display": actual_str or "—",
                    "actual_num": None,
                    "target_display": target_clean_display,
                    "raw_target": raw_target,
                    "target_min": eff_min,
                    "target_ideal": eff_ideal,
                    "is_percent": is_pct,
                    "ratio_pct": 0.0,
                    "radar_ratio": 0.0,
                    "diff_num": None,
                    "diff_display": "",
                    "status": "missing",
                    "score_weight_ratio": 0.0,
                    "tags": spec["tags"],
                    "plot_on_radar": False,
                }
            )
            continue

        # Calcula aderência em % (100% = meta exata atingida; teto visual no radar = 120%)
        raw_ratio_pct = (actual_num / eff_min) * 100.0 if eff_min > 0 else 100.0
        # Trata operador '<=' / '<' (raro, ex.: builds de baixa velocidade proposital)
        if spec["operator"] in ("<=", "<"):
            reached = actual_num <= eff_min if spec["operator"] == "<=" else actual_num < eff_min
            ratio_pct = 100.0 if reached else max(0.0, (eff_min / actual_num) * 100.0)
        else:
            reached = actual_num >= eff_min
            ratio_pct = raw_ratio_pct

        diff_num = actual_num - eff_min
        diff_display = _format_diff_display(diff_num, is_pct, eff_min)

        # Regras inteligentes para casos especiais (Cap/Overcap, Base SPD, In-Combat, Optional)
        axis_tags = list(spec["tags"])
        base_spd_satisfied = False
        if spec.get("is_cap"):
            # Ex.: Sigrid Taxa CRIT 33.8% (overcap acima disso devido +66% da Passiva de Núcleo)
            if actual_num >= eff_min * 0.98:
                status = "ok"
                weight_ratio = 1.0
                met_count += 1
                if actual_num > eff_min + 5.0 and "overcap" not in axis_tags:
                    axis_tags.append("overcap")
            elif ratio_pct >= 85.0:
                status = "close"
                weight_ratio = 0.5
                close_count += 1
            else:
                status = "low"
                weight_ratio = 0.0
                low_count += 1
        elif reached:
            status = "ok"
            weight_ratio = 1.0
            met_count += 1
        elif spec["has_base_option"] and stat_key == "spd" and actual_num >= 90.0:
            # Ex.: Evanescia ("Base SPD or 134") com 115 SPD satisfaz 100% do ramo VEL Base!
            status = "ok"
            weight_ratio = 1.0
            met_count += 1
            base_spd_satisfied = True
        elif spec["is_optional"]:
            status = "flex"
            weight_ratio = 1.0
            flex_count += 1
        elif spec["is_in_combat"] and ratio_pct >= 65.0:
            # Ex.: Evanescia 100% (in-combat) com 65.4% fora de combate (A2 dá +30% em combate!)
            status = "close"
            weight_ratio = 0.85
            close_count += 1
        elif ratio_pct >= 85.0:
            status = "close"
            weight_ratio = 0.5
            close_count += 1
        else:
            status = "low"
            weight_ratio = 0.0
            low_count += 1

        scored_ratios.append(weight_ratio)
        # Quando o ramo VEL Base já cumpre 100% da meta (ex.: Evanescia 115 SPD em "VEL Base ou 134"),
        # plota o vértice exatamente no anel de 100% para não parecer um "afundamento" de stat faltando.
        effective_ratio_pct = 100.0 if base_spd_satisfied else ratio_pct
        radar_ratio = round(min(1.20, max(0.08, effective_ratio_pct / 100.0)), 3)
        radar_ratio_sum += min(120.0, effective_ratio_pct)
        radar_ratio_count += 1

        axes.append(
            {
                "stat_key": stat_key,
                "label_pt": label_pt,
                "label_en": label_en,
                "short_pt": short_pt,
                "short_en": short_en,
                "actual_display": actual_str or _format_num_display(actual_num, is_pct),
                "actual_num": round(actual_num, 2),
                "target_display": target_clean_display,
                "target_display_pt": target_display_pt,
                "target_display_en": target_display_en,
                "raw_target": raw_target,
                "tooltip_note": tooltip_note,
                "target_min": eff_min,
                "target_ideal": eff_ideal,
                "is_percent": is_pct,
                "ratio_pct": round(effective_ratio_pct, 1),
                "radar_ratio": radar_ratio,
                "diff_num": round(diff_num, 2),
                "diff_display": diff_display,
                "status": status,
                "score_weight_ratio": weight_ratio,
                "tags": axis_tags,
                "plot_on_radar": True,
            }
        )

    # Inclui slots de Main Stats marcados como "Qualquer (Flex)" / "Anything" como tags Flex abaixo do Radar
    if main_stats and isinstance(main_stats, dict):
        slot_en_map = {
            "Corpo": "Body",
            "Bota": "Feet",
            "Esfera": "Planar Sphere",
            "Corda": "Link Rope",
            "Areia": "Sands",
            "Copo": "Goblet",
            "Tiara": "Circlet",
            "Disco 4": "Disc 4",
            "Disco 5": "Disc 5",
            "Disco 6": "Disc 6",
        }
        for slot_lbl, slot_target in main_stats.items():
            s_val = str(slot_target or "").strip()
            if s_val and _RE_FLEX_WORD.search(_strip_accents(s_val)):
                flex_notes.append(
                    {
                        "stat_key": f"slot_{_strip_accents(str(slot_lbl)).lower().replace(' ', '_')}",
                        "label_pt": str(slot_lbl),
                        "label_en": slot_en_map.get(str(slot_lbl), str(slot_lbl)),
                        "short_pt": str(slot_lbl),
                        "short_en": slot_en_map.get(str(slot_lbl), str(slot_lbl)),
                        "actual_display": "",
                        "actual_num": None,
                        "target_display": standardize_main_stat_display(s_val, "pt"),
                        "target_display_pt": standardize_main_stat_display(s_val, "pt"),
                        "target_display_en": standardize_main_stat_display(s_val, "en"),
                        "mode": "slot_flex",
                        "status": "flex",
                        "tags": ["flex"],
                    }
                )

    # Garante no máximo MAX_RADAR_POLYGON_AXES (6) vértices no polígono SVG, priorizando atributos
    # definidores da build (mantendo todos visíveis na lista de breakdown!)
    plotted_indices = [idx for idx, ax in enumerate(axes) if ax.get("plot_on_radar")]
    if len(plotted_indices) > MAX_RADAR_POLYGON_AXES:
        ranked = sorted(
            plotted_indices,
            key=lambda idx: (-_AXIS_PLOT_PRIORITY.get(axes[idx]["stat_key"], 50), idx),
        )
        keep_set = set(ranked[:MAX_RADAR_POLYGON_AXES])
        for idx in plotted_indices:
            if idx not in keep_set:
                axes[idx]["plot_on_radar"] = False

    plotted_count = sum(1 for a in axes if a.get("plot_on_radar"))
    total_scored = len(scored_ratios)
    benchmark_score_20 = round((sum(scored_ratios) / total_scored) * 20.0, 2) if total_scored > 0 else 0.0
    avg_ratio_pct = round(radar_ratio_sum / radar_ratio_count, 1) if radar_ratio_count > 0 else 0.0

    if plotted_count >= 3:
        radar_mode = "polygon"
    elif plotted_count >= 1:
        radar_mode = "gauges"
    else:
        radar_mode = "empty"

    return {
        "character": char_name,
        "game_id": g,
        "axes": axes,
        "flex_notes": flex_notes,
        "summary": {
            "met_count": met_count,
            "close_count": close_count,
            "low_count": low_count,
            "flex_count": flex_count,
            "plotted_count": plotted_count,
            "total_scored": total_scored,
            "avg_ratio_pct": avg_ratio_pct,
            "benchmark_score_20": benchmark_score_20,
            "radar_mode": radar_mode,
        },
    }
