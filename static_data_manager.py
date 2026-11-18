import os
import re
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from curl_cffi import requests
from core.paths import get_data_dir, get_resource_path


BASE_DIR = get_data_dir()
STATIC_DATA_DIR = os.path.join(BASE_DIR, "static_data")


def fetch_json_with_retry(
    urls: List[str], headers: Optional[Dict[str, str]] = None, max_retries: int = 2, backoff_factor: float = 0.4
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Realiza requisição HTTP resiliente com retry, exponential backoff e fallback entre múltiplos mirrors.
    Trata 403, 429, 503 e timeouts de rede sem quebrar a execução.
    """
    req_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
    }
    if headers:
        req_headers.update(headers)

    for url in urls:
        for attempt in range(max_retries + 1):
            try:
                resp = requests.get(url, headers=req_headers, impersonate="chrome", timeout=8)

                if resp.status_code == 200:
                    return resp.json(), url
                elif resp.status_code in [403, 429, 503]:
                    time.sleep(backoff_factor * (2**attempt))
                    continue
            except Exception:
                time.sleep(backoff_factor * (2**attempt))
                continue
    return None, None


# ==========================================================
# DIAS DA SEMANA PADRONIZADOS
# 0 = Segunda, 1 = Terça, 2 = Quarta, 3 = Quinta, 4 = Sexta, 5 = Sábado, 6 = Domingo
# ==========================================================
WEEKDAY_NAMES_PT = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

# ==========================================================
# CATÁLOGO DE LIVROS DE TALENTO E MATERIAIS DE GENSHIN IMPACT
# ==========================================================

def _load_static_catalog_json(filename: str) -> Dict[str, Any]:
    path = get_resource_path(os.path.join("static_data", filename))
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


_MATERIAL_CATALOGS = _load_static_catalog_json("material_catalogs.json")
_CHARACTER_SEEDS = _load_static_catalog_json("character_seeds.json")

GENSHIN_TALENT_BOOKS = _MATERIAL_CATALOGS.get("GENSHIN_TALENT_BOOKS", {})
GENSHIN_MOB_DROPS = _MATERIAL_CATALOGS.get("GENSHIN_MOB_DROPS", {})
GENSHIN_WEAPON_MATERIALS = _MATERIAL_CATALOGS.get("GENSHIN_WEAPON_MATERIALS", {})
GENSHIN_DOMAINS_SCHEDULE = _MATERIAL_CATALOGS.get("GENSHIN_DOMAINS_SCHEDULE", {})

HSR_CALYX_MATERIALS = _MATERIAL_CATALOGS.get("HSR_CALYX_MATERIALS", {})
HSR_MOB_DROPS = _MATERIAL_CATALOGS.get("HSR_MOB_DROPS", {})
HSR_STAGNANT_SHADOW = _MATERIAL_CATALOGS.get("HSR_STAGNANT_SHADOW", {})
HSR_ECHO_OF_WAR = _MATERIAL_CATALOGS.get("HSR_ECHO_OF_WAR", {})

ZZZ_SKILL_CHIPS = _MATERIAL_CATALOGS.get("ZZZ_SKILL_CHIPS", {})
ZZZ_PROMOTION_SEALS = _MATERIAL_CATALOGS.get("ZZZ_PROMOTION_SEALS", {})
ZZZ_MOB_DROPS = _MATERIAL_CATALOGS.get("ZZZ_MOB_DROPS", {})
ZZZ_EXPERT_CHALLENGE = _MATERIAL_CATALOGS.get("ZZZ_EXPERT_CHALLENGE", {})
ZZZ_NOTORIOUS_HUNT = _MATERIAL_CATALOGS.get("ZZZ_NOTORIOUS_HUNT", {})

GENSHIN_CHARACTERS_SEED = _CHARACTER_SEEDS.get("GENSHIN_CHARACTERS_SEED", {})
HSR_CHARACTERS_SEED = _CHARACTER_SEEDS.get("HSR_CHARACTERS_SEED", {})
ZZZ_CHARACTERS_SEED = _CHARACTER_SEEDS.get("ZZZ_CHARACTERS_SEED", {})

class StaticDataManager:
    def __init__(self):
        self.data_dir = STATIC_DATA_DIR
        self._ensure_cache_dir()
        self._cache = {"genshin": {}, "hsr": {}, "zzz": {}, "schedules": {}}
        self.load_all()

    def _ensure_cache_dir(self):
        os.makedirs(self.data_dir, exist_ok=True)

    def _get_file_path(self, key: str) -> str:
        return os.path.join(self.data_dir, f"{key}_manifest.json")

    def init_seed_files_if_missing(self):
        """Garante que os arquivos JSON de seed existam no disco."""
        files_to_seed = {
            "genshin": {"characters": GENSHIN_CHARACTERS_SEED, "domains": GENSHIN_DOMAINS_SCHEDULE},
            "hsr": {"characters": HSR_CHARACTERS_SEED},
            "zzz": {"characters": ZZZ_CHARACTERS_SEED},
        }
        for game_id, payload in files_to_seed.items():
            path = self._get_file_path(game_id)
            if not os.path.exists(path) or os.path.getsize(path) < 10:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False, indent=2)

    def load_all(self):
        """Carrega todos os dados do disco ou inicializa seeds em memória."""
        self.init_seed_files_if_missing()
        for game_id in ["genshin", "hsr", "zzz"]:
            path = self._get_file_path(game_id)
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self._cache[game_id] = json.load(f)
                except Exception:
                    self._cache[game_id] = self._get_fallback_seed(game_id)
            else:
                self._cache[game_id] = self._get_fallback_seed(game_id)

    def _get_fallback_seed(self, game_id: str) -> Dict[str, Any]:
        if game_id == "genshin":
            return {"characters": GENSHIN_CHARACTERS_SEED, "domains": GENSHIN_DOMAINS_SCHEDULE}
        elif game_id == "hsr":
            return {"characters": HSR_CHARACTERS_SEED}
        elif game_id == "zzz":
            return {"characters": ZZZ_CHARACTERS_SEED}
        return {}

    def get_character_profile(self, game_id: str, char_name_or_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca o perfil completo de materiais e rotinas de farm de um personagem.
        Retorna nomes específicos dos 3 tiers de livros/rastros/chips, drop de chefe com ícone,
        especialidade local com ícone, chefe semanal com ícone e drops de monstros (1★, 2★, 3★).
        """
        g = game_id.lower().strip()
        if g not in self._cache:
            return None

        chars_dict = self._cache[g].get("characters", {})
        query = char_name_or_id.lower().strip().replace(" ", "_").replace("•", "").replace("'", "")
        q_clean = re.sub(r"[^a-z0-9]", "", char_name_or_id.lower())

        found_item = None
        # 1. Busca direta por chave
        if query in chars_dict:
            found_item = dict(chars_dict[query])
        else:
            # 2. Busca por matching flexível de nome
            for k, v in chars_dict.items():
                name_clean = v.get("name", "").lower().replace(" ", "_").replace("•", "").replace("'", "")
                k_clean = re.sub(r"[^a-z0-9]", "", k.lower())
                vn_clean = re.sub(r"[^a-z0-9]", "", v.get("name", "").lower())
                if (
                    query == name_clean
                    or k_clean == q_clean
                    or vn_clean == q_clean
                    or (len(q_clean) >= 3 and (q_clean in k_clean or k_clean in q_clean or q_clean in vn_clean or vn_clean in q_clean))
                    or query in name_clean
                    or name_clean in query
                    or k == query
                ):
                    found_item = dict(v)
                    break

        # Fallback nos seeds mestres se não encontrado no cache sincronizado
        if not found_item:
            seed_dict = self._get_fallback_seed(g).get("characters", {})
            if query in seed_dict:
                found_item = dict(seed_dict[query])
            else:
                for k, v in seed_dict.items():
                    name_clean = v.get("name", "").lower().replace(" ", "_").replace("•", "").replace("'", "")
                    k_clean = re.sub(r"[^a-z0-9]", "", k.lower())
                    vn_clean = re.sub(r"[^a-z0-9]", "", v.get("name", "").lower())
                    if (
                        query == name_clean
                        or k_clean == q_clean
                        or vn_clean == q_clean
                        or (len(q_clean) >= 3 and (q_clean in k_clean or k_clean in q_clean or q_clean in vn_clean or vn_clean in q_clean))
                        or query in name_clean
                        or name_clean in query
                        or k == query
                    ):
                        found_item = dict(v)
                        break

        if not found_item:
            return None

        found_item["open_today"] = self._is_character_farm_open_today(g, found_item)
        return self._enrich_character_profile(g, found_item)

    def _enrich_character_profile(self, game_id: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """Injeta metadados ricos de itens com ícones CDN oficiais e nomes dos tiers."""
        enriched = dict(item)

        # Mescla chaves do seed mestre se ausentes no item em cache
        char_id = str(item.get("id", "")).lower()
        char_name = str(item.get("name", "")).lower()
        seed_dict = self._get_fallback_seed(game_id).get("characters", {})
        seed_char = seed_dict.get(char_id)
        if not seed_char:
            for sk, sv in seed_dict.items():
                if sv.get("name", "").lower() == char_name or sk == char_id:
                    seed_char = sv
                    break
        if seed_char:
            for k, v in seed_char.items():
                if k not in item or not item[k]:
                    item[k] = v
                    enriched[k] = v

        if game_id == "genshin":
            # 1. Livros de Talento
            t_key = item.get("talent_key")
            if not t_key:
                raw_book = str(item.get("talent_book", ""))
                for k in GENSHIN_TALENT_BOOKS.keys():
                    if k in raw_book.lower() or GENSHIN_TALENT_BOOKS[k]["base"].lower() in raw_book.lower():
                        t_key = k
                        break

            # Se ainda não encontrou t_key, busca nos domínios oficiais pelo nome do personagem
            if not t_key:
                c_name = str(item.get("name", "")).lower()
                c_id = str(item.get("id", "")).lower()
                domains_data = self._cache.get("genshin", {}).get("domains", GENSHIN_DOMAINS_SCHEDULE)
                for nat, data in domains_data.get("talent_books", {}).items():
                    for sch_key, sch in data.get("schedules", {}).items():
                        sch_chars = [x.lower() for x in sch.get("characters", [])]
                        if any(c_name == sc or c_name in sc or sc in c_name or c_id in sc for sc in sch_chars):
                            sch_name = sch.get("name", "").lower()
                            for k, v in GENSHIN_TALENT_BOOKS.items():
                                if k in sch_name or v["base"].lower() in sch_name:
                                    t_key = k
                                    break
                            if t_key:
                                break
                    if t_key:
                        break

            if not t_key:
                # Default inteligente por elemento
                el = str(item.get("element", "")).lower()
                if "anemo" in el:
                    t_key = "poemas"
                elif "geo" in el:
                    t_key = "ouro"
                elif "electro" in el:
                    t_key = "luz"
                elif "dendro" in el:
                    t_key = "engenhosidade"
                elif "hydro" in el:
                    t_key = "justica"
                elif "pyro" in el:
                    t_key = "disputa"
                else:
                    t_key = "resistencia"

            if t_key and t_key in GENSHIN_TALENT_BOOKS:
                tb_data = GENSHIN_TALENT_BOOKS[t_key]
                enriched["talent_tier2_name"] = tb_data["t2"]
                enriched["talent_tier2_icon"] = tb_data["t2_icon"]
                enriched["talent_tier3_name"] = tb_data["t3"]
                enriched["talent_tier3_icon"] = tb_data["t3_icon"]
                enriched["talent_tier4_name"] = tb_data["t4"]
                enriched["talent_tier4_icon"] = tb_data["t4_icon"]
                enriched["domain_days"] = tb_data["days"]
                enriched["talent_book"] = f"{tb_data['base']} ({tb_data['t4']})"

            # 2. Chefe de Campo (Boss Mat & Icon)
            boss_name = item.get("boss_mat")
            boss_icon = item.get("boss_icon")
            if not boss_name or boss_name in ["Material de Chefe", ""]:
                el = str(item.get("element", "")).lower()
                if "pyro" in el:
                    boss_name, boss_icon = "Semente de Fogo Eterno", "https://enka.network/ui/UI_ItemIcon_113009.png"
                elif "hydro" in el:
                    boss_name, boss_icon = (
                        "Gota d'Água Não Envelhecida",
                        "https://enka.network/ui/UI_ItemIcon_113051.png",
                    )
                elif "anemo" in el:
                    boss_name, boss_icon = "Semente de Furacão", "https://enka.network/ui/UI_ItemIcon_113006.png"
                elif "electro" in el:
                    boss_name, boss_icon = "Pérola da Tempestade", "https://enka.network/ui/UI_ItemIcon_113028.png"
                elif "dendro" in el:
                    boss_name, boss_icon = "Videira Suprimida", "https://enka.network/ui/UI_ItemIcon_113040.png"
                elif "cryo" in el:
                    boss_name, boss_icon = "Núcleo de Gelo", "https://enka.network/ui/UI_ItemIcon_113005.png"
                elif "geo" in el:
                    boss_name, boss_icon = "Pilar de Basalto", "https://enka.network/ui/UI_ItemIcon_113010.png"
                else:
                    boss_name, boss_icon = (
                        "Gota d'Água Não Envelhecida",
                        "https://enka.network/ui/UI_ItemIcon_113051.png",
                    )
            enriched["boss_mat_name"] = boss_name
            enriched["boss_mat_icon"] = boss_icon

            # 3. Especialidade Local
            spec_name = item.get("local_specialty")
            spec_icon = item.get("specialty_icon")
            if not spec_name or spec_name in ["Especialidade Local", ""]:
                el = str(item.get("element", "")).lower()
                if "hydro" in el:
                    spec_name, spec_icon = "Lírio de Lakelight", "https://enka.network/ui/UI_ItemIcon_101235.png"
                elif "anemo" in el:
                    spec_name, spec_icon = "Dente-de-Leão", "https://enka.network/ui/UI_ItemIcon_100021.png"
                elif "geo" in el:
                    spec_name, spec_icon = "Cor Lapis", "https://enka.network/ui/UI_ItemIcon_100026.png"
                elif "electro" in el:
                    spec_name, spec_icon = "Fruto Amakumo", "https://enka.network/ui/UI_ItemIcon_101207.png"
                elif "dendro" in el:
                    spec_name, spec_icon = "Lótus Kalpalata", "https://enka.network/ui/UI_ItemIcon_101217.png"
                elif "pyro" in el:
                    spec_name, spec_icon = "Rosa Arco-íris", "https://enka.network/ui/UI_ItemIcon_101231.png"
                else:
                    spec_name, spec_icon = "Flor Qingxin", "https://enka.network/ui/UI_ItemIcon_100030.png"
            enriched["local_specialty_name"] = spec_name
            enriched["local_specialty_icon"] = spec_icon

            # 4. Chefe Semanal
            wk_name = item.get("weekly_boss_mat")
            wk_icon = item.get("weekly_icon")
            if not wk_name or wk_name in ["Material de Chefe Semanal", ""]:
                wk_name, wk_icon = "Massa Sem Luz", "https://enka.network/ui/UI_ItemIcon_113054.png"
            enriched["weekly_boss_mat_name"] = wk_name
            enriched["weekly_boss_mat_icon"] = wk_icon

            # 5. Drops de Inimigos Comuns
            e_key = item.get("enemy_key")
            if not e_key or e_key not in GENSHIN_MOB_DROPS:
                el = str(item.get("element", "")).lower()
                if "anemo" in el or "hydro" in el:
                    e_key = "nectar"
                elif "geo" in el or "cryo" in el:
                    e_key = "slime"
                elif "electro" in el:
                    e_key = "handguard"
                elif "dendro" in el:
                    e_key = "fungal_spores"
                elif "pyro" in el:
                    e_key = "treasure_hoarder"
                else:
                    e_key = "slime"

            mob = GENSHIN_MOB_DROPS.get(e_key, GENSHIN_MOB_DROPS["slime"])
            enriched["enemy_tier1_name"] = mob["t1"]
            enriched["enemy_tier1_icon"] = mob["t1_icon"]
            enriched["enemy_tier2_name"] = mob["t2"]
            enriched["enemy_tier2_icon"] = mob["t2_icon"]
            enriched["enemy_tier3_name"] = mob["t3"]
            enriched["enemy_tier3_icon"] = mob["t3_icon"]

            # Coroa Genshin
            enriched["crown_mat_name"] = "Coroa da Sabedoria"
            enriched["crown_icon"] = "https://enka.network/ui/UI_ItemIcon_104319.png"

        elif game_id == "hsr":
            # 1. Cálice de Rastros por Caminho
            c_key = item.get("calyx_key")
            if not c_key:
                p_lower = str(item.get("path", "")).lower()
                for k, v in HSR_CALYX_MATERIALS.items():
                    if v["path"].lower() == p_lower:
                        c_key = k
                        break
            if not c_key:
                c_key = "destruction_nanook"

            calyx = HSR_CALYX_MATERIALS.get(c_key, HSR_CALYX_MATERIALS["destruction_nanook"])
            enriched["talent_tier2_name"] = calyx["t2"]
            enriched["talent_tier2_icon"] = calyx["t2_icon"]
            enriched["talent_tier3_name"] = calyx["t3"]
            enriched["talent_tier3_icon"] = calyx["t3_icon"]
            enriched["talent_tier4_name"] = calyx["t4"]
            enriched["talent_tier4_icon"] = calyx["t4_icon"]

            # 2. Sombra Estagnada (Chefe de Ascensão)
            stagnant_key = item.get("stagnant_key")
            if not stagnant_key:
                stagnant_key = "primitive_lightning"
            stag = HSR_STAGNANT_SHADOW.get(
                stagnant_key,
                {
                    "name": item.get("stagnant_shadow_mat", "Material de Sombra Estagnada"),
                    "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110401.png",
                },
            )
            enriched["boss_mat_name"] = stag["name"]
            enriched["boss_mat_icon"] = stag["icon"]

            # 3. Eco da Guerra (Chefe Semanal)
            echo_key = item.get("echo_key")
            if not echo_key:
                echo_key = "dream_monster"
            echo = HSR_ECHO_OF_WAR.get(
                echo_key,
                {
                    "name": item.get("echo_of_war_mat", "Material de Eco da Guerra"),
                    "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110505.png",
                },
            )
            enriched["weekly_boss_mat_name"] = echo["name"]
            enriched["weekly_boss_mat_icon"] = echo["icon"]

            # 4. Inimigos Comuns
            e_key = item.get("enemy_key") or "dreamjolt"
            mob = HSR_MOB_DROPS.get(e_key, HSR_MOB_DROPS["silvermane"])
            enriched["enemy_tier1_name"] = mob["t1"]
            enriched["enemy_tier1_icon"] = mob["t1_icon"]
            enriched["enemy_tier2_name"] = mob["t2"]
            enriched["enemy_tier2_icon"] = mob["t2_icon"]
            enriched["enemy_tier3_name"] = mob["t3"]
            enriched["enemy_tier3_icon"] = mob["t3_icon"]

            # Coroa HSR
            enriched["crown_mat_name"] = "Pegadas do Destino"
            enriched["crown_icon"] = "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/11.png"

        elif game_id == "zzz":
            # 1. Chips de Habilidade por Elemento
            el = str(item.get("element", "physical")).lower()
            chip_key = "physical"
            for k in ZZZ_SKILL_CHIPS.keys():
                if k in el:
                    chip_key = k
                    break
            chip = ZZZ_SKILL_CHIPS.get(chip_key, ZZZ_SKILL_CHIPS["physical"])
            enriched["talent_tier2_name"] = chip["t2"]
            enriched["talent_tier2_icon"] = chip["t2_icon"]
            enriched["talent_tier3_name"] = chip["t3"]
            enriched["talent_tier3_icon"] = chip["t3_icon"]
            enriched["talent_tier4_name"] = chip["t4"]
            enriched["talent_tier4_icon"] = chip["t4_icon"]

            # 2. Desafio de Especialista (Habilidade Essencial / Boss)
            exp_key = item.get("expert_key") or "section6"
            exp_data = ZZZ_EXPERT_CHALLENGE.get(
                exp_key,
                {
                    "name": item.get("core_skill_mat", "Emblema de Especialista"),
                    "icon": "https://act-webstatic.hoyoverse.com/game_record/genshin/equip/UI_ItemIcon_113009.png",
                },
            )
            enriched["boss_mat_name"] = exp_data["name"]
            enriched["boss_mat_icon"] = exp_data["icon"]

            # 3. Selos de Especialidade
            spec = str(item.get("specialty", "attack")).lower()
            seal_key = "attack"
            for k in ZZZ_PROMOTION_SEALS.keys():
                if k in spec:
                    seal_key = k
                    break
            seal = ZZZ_PROMOTION_SEALS.get(seal_key, ZZZ_PROMOTION_SEALS["attack"])
            enriched["local_specialty_name"] = seal["t4"]
            enriched["local_specialty_icon"] = seal["t4_icon"]

            # 4. Caça Notória (Chefe Semanal)
            wk_key = item.get("weekly_key") or "silent_death"
            wk_data = ZZZ_NOTORIOUS_HUNT.get(
                wk_key,
                {
                    "name": item.get("weekly_boss_mat", "Material de Caça Notória"),
                    "icon": "https://act-webstatic.hoyoverse.com/game_record/genshin/equip/UI_ItemIcon_113028.png",
                },
            )
            enriched["weekly_boss_mat_name"] = wk_data["name"]
            enriched["weekly_boss_mat_icon"] = wk_data["icon"]

            # 5. Inimigos Comuns
            e_key = item.get("enemy_key") or "ethereal"
            mob = ZZZ_MOB_DROPS.get(e_key, ZZZ_MOB_DROPS["ethereal"])
            enriched["enemy_tier1_name"] = mob["t1"]
            enriched["enemy_tier1_icon"] = mob["t1_icon"]
            enriched["enemy_tier2_name"] = mob["t2"]
            enriched["enemy_tier2_icon"] = mob["t2_icon"]
            enriched["enemy_tier3_name"] = mob["t3"]
            enriched["enemy_tier3_icon"] = mob["t3_icon"]

            # Coroa ZZZ
            enriched["crown_mat_name"] = "Passaporte da Gaiola de Hamster"
            enriched["crown_icon"] = (
                "https://act-webstatic.hoyoverse.com/game_record/genshin/equip/UI_ItemIcon_104319.png"
            )

        return enriched

    def get_weapon_profile(self, game_id: str, weapon_name: str) -> Dict[str, Any]:
        """
        Retorna o perfil completo de ascensão da arma com os 4 tiers de materiais de domínio
        e drops de monstros com ícones CDN oficiais.
        """
        g = game_id.lower().strip()
        w_clean = weapon_name.lower().strip()

        if g == "genshin":
            w_mat_key = "dandelion_gladiator"  # Padrão Favonius
            mob_key = "chaos"

            # Identificação inteligente por série ou nome de arma
            if any(k in w_clean for k in ["favonius", "favônio", "favonio", "dente-de-leão", "dandelion"]):
                w_mat_key = "dandelion_gladiator"
                mob_key = "chaos"
            elif any(k in w_clean for k in ["sacrifício", "sacrificial", "boreal", "lobo"]):
                w_mat_key = "boreal_wolf"
                mob_key = "arrowhead"
            elif any(k in w_clean for k in ["decarabian", "cinegética", "windblume", "ferro negro"]):
                w_mat_key = "decarabian"
                mob_key = "horn"
            elif any(k in w_clean for k in ["guyun", "duelo", "solar", "espinha dorsal"]):
                w_mat_key = "guyun"
                mob_key = "mask"
            elif any(k in w_clean for k in ["névoa velada", "mist", "reforjadora", "protótipo rancor"]):
                w_mat_key = "mist_veiled"
                mob_key = "treasure_hoarder"
            elif any(k in w_clean for k in ["aerosiderite", "penhasco", "protótipo arcaico"]):
                w_mat_key = "aerosiderite"
                mob_key = "fatui_insignia"
            elif any(k in w_clean for k in ["mar distante", "distant sea", "akuoumaru", "mistsplitter"]):
                w_mat_key = "distant_sea"
                mob_key = "specter"
            elif any(k in w_clean for k in ["narukami", "kagura", "harakiri", "amenoma"]):
                w_mat_key = "narukami"
                mob_key = "handguard"
            elif any(k in w_clean for k in ["máscara", "mask", "katsuragikiri"]):
                w_mat_key = "mask"
                mob_key = "handguard"
            elif any(
                k in w_clean
                for k in ["talismã de ferro", "iron talisman", "luz lunar de xiphos", "madeira da floresta"]
            ):
                w_mat_key = "iron_talisman"
                mob_key = "fungal_spores"
            elif any(
                k in w_clean
                for k in ["jardim do oásis", "oasis garden", "luz das folhas cortadas", "espada de madeira"]
            ):
                w_mat_key = "oasis_garden"
                mob_key = "red_silk"
            elif any(
                k in w_clean
                for k in ["sol escaldante", "scorching sun", "báculo das areias escarlates", "agulha de ferro"]
            ):
                w_mat_key = "scorching_sun"
                mob_key = "fungal_spores"
            elif any(k in w_clean for k in ["acorde antigo", "chord", "tomo do fluxo eterno", "fluxo eterno"]):
                w_mat_key = "chord"
                mob_key = "gear"
            elif any(
                k in w_clean for k in ["gota d'água", "dewdrop", "esplendor das águas silenciosas", "águas silenciosas"]
            ):
                w_mat_key = "dewdrop"
                mob_key = "transoceanic"
            elif any(k in w_clean for k in ["mar primordial", "sacred sea", "semblante da lua carmesim"]):
                w_mat_key = "sacred_sea"
                mob_key = "gear"
            elif any(k in w_clean for k in ["vento noturno", "night-wind", "surfar na crista", "onda"]):
                w_mat_key = "night_wind"
                mob_key = "whistle"
            elif any(k in w_clean for k in ["fogueira ardente", "blazing hearth", "caçador de montanhas"]):
                w_mat_key = "blazing_hearth"
                mob_key = "saurian_fang"
            elif any(k in w_clean for k in ["senhor sagrado", "sacred lord", "hino da cimeira"]):
                w_mat_key = "sacred_lord"
                mob_key = "saurian_fang"

            w_data = GENSHIN_WEAPON_MATERIALS.get(w_mat_key, GENSHIN_WEAPON_MATERIALS["dandelion_gladiator"])
            mob_data = GENSHIN_MOB_DROPS.get(mob_key, GENSHIN_MOB_DROPS["chaos"])

            return {
                "weapon_name": weapon_name,
                "w_mat_tier2_name": w_data["t2"],
                "w_mat_tier2_icon": w_data["t2_icon"],
                "w_mat_tier3_name": w_data["t3"],
                "w_mat_tier3_icon": w_data["t3_icon"],
                "w_mat_tier4_name": w_data["t4"],
                "w_mat_tier4_icon": w_data["t4_icon"],
                "w_mat_tier5_name": w_data["t5"],
                "w_mat_tier5_icon": w_data["t5_icon"],
                "enemy_tier1_name": mob_data["t1"],
                "enemy_tier1_icon": mob_data["t1_icon"],
                "enemy_tier2_name": mob_data["t2"],
                "enemy_tier2_icon": mob_data["t2_icon"],
                "enemy_tier3_name": mob_data["t3"],
                "enemy_tier3_icon": mob_data["t3_icon"],
            }

        elif g == "hsr":
            # Identificação inteligente do Caminho do Cone de Luz
            calyx_key = "destruction_nanook"
            mob_key = "silvermane"

            if any(
                k in w_clean
                for k in [
                    "passing shore",
                    "along the passing shore",
                    "fogo",
                    "olhos da presa",
                    "paciência",
                    "solidão",
                    "chuva",
                    "tutorial",
                    "destino",
                ]
            ):
                calyx_key = "nihility_fiery_spirit"
                mob_key = "dreamjolt"
            elif any(
                k in w_clean
                for k in [
                    "flaming",
                    "whereabouts",
                    "queda de um aeon",
                    "sob o céu azul",
                    "coração secreto",
                    "mutação",
                    "topo do mundo",
                ]
            ):
                calyx_key = "destruction_borisin"
                mob_key = "memoryzone"
            elif any(
                k in w_clean
                for k in ["perseguição", "cruzeiro", "espada estelar", "sono", "jogo de espadas", "silêncio"]
            ):
                calyx_key = "hunt_meteor"
                mob_key = "borisin"
            elif any(k in w_clean for k in ["vocal", "passado e futuro", "dança", "engrenagens", "reunião", "lua"]):
                calyx_key = "harmony_firm_note"
                mob_key = "dreamjolt"
            elif any(k in w_clean for k in ["vitória", "momento de vitória", "tendência", "primeiro dia", "terra"]):
                calyx_key = "preservation_amber"
                mob_key = "memoryzone"
            elif any(k in w_clean for k in ["tempo não espera", "troca equivalente", "sentimento", "festa"]):
                calyx_key = "abundance_alien"
                mob_key = "borisin"
            elif any(k in w_clean for k in ["antes do amanhecer", "viajante", "paz", "nascimento"]):
                calyx_key = "erudition_sketch"
                mob_key = "dreamjolt"

            calyx = HSR_CALYX_MATERIALS.get(calyx_key, HSR_CALYX_MATERIALS["destruction_nanook"])
            mob = HSR_MOB_DROPS.get(mob_key, HSR_MOB_DROPS["silvermane"])

            return {
                "weapon_name": weapon_name,
                "w_mat_tier2_name": calyx["t2"],
                "w_mat_tier2_icon": calyx["t2_icon"],
                "w_mat_tier3_name": calyx["t3"],
                "w_mat_tier3_icon": calyx["t3_icon"],
                "w_mat_tier4_name": calyx["t4"],
                "w_mat_tier4_icon": calyx["t4_icon"],
                "w_mat_tier5_name": calyx["t5"],
                "w_mat_tier5_icon": calyx["t5_icon"],
                "enemy_tier1_name": mob["t1"],
                "enemy_tier1_icon": mob["t1_icon"],
                "enemy_tier2_name": mob["t2"],
                "enemy_tier2_icon": mob["t2_icon"],
                "enemy_tier3_name": mob["t3"],
                "enemy_tier3_icon": mob["t3_icon"],
                "ore_name": "Éter Refinado",
                "ore_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/102.png",
                "currency_name": "Créditos",
                "currency_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/2.png",
            }

        elif g == "zzz":
            # Identificação inteligente do W-Engine por Especialidade
            spec_key = "attack"
            mob_key = "ethereal"

            if any(
                k in w_clean
                for k in ["deep sea", "visitor", "visita", "enxofre", "canhão", "estrela", "lâmina", "fúria"]
            ):
                spec_key = "attack"
                mob_key = "ethereal"
            elif any(k in w_clean for k in ["fusão", "restrição", "vaporizador", "motor", "fita"]):
                spec_key = "stun"
                mob_key = "rebel"
            elif any(k in w_clean for k in ["eletro", "labareda", "bisturi", "lágrima", "calydon", "caos"]):
                spec_key = "anomaly"
                mob_key = "rebel"
            elif any(k in w_clean for k in ["cofre", "timbre", "berço", "ressonância", "eco"]):
                spec_key = "support"
                mob_key = "ethereal"
            elif any(k in w_clean for k in ["escudo", "presa", "fornalha", "defesa"]):
                spec_key = "defense"
                mob_key = "rebel"

            seal = ZZZ_PROMOTION_SEALS.get(spec_key, ZZZ_PROMOTION_SEALS["attack"])
            mob = ZZZ_MOB_DROPS.get(mob_key, ZZZ_MOB_DROPS["ethereal"])

            return {
                "weapon_name": weapon_name,
                "w_mat_tier2_name": seal["t2"].replace("Selo de", "Componente de W-Engine"),
                "w_mat_tier2_icon": seal["t2_icon"],
                "w_mat_tier3_name": seal["t3"].replace("Selo de", "Componente de W-Engine"),
                "w_mat_tier3_icon": seal["t3_icon"],
                "w_mat_tier4_name": seal["t4"].replace("Selo de", "Componente de W-Engine"),
                "w_mat_tier4_icon": seal["t4_icon"],
                "w_mat_tier5_name": "Componente Mestre de W-Engine (5★)",
                "w_mat_tier5_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
                "enemy_tier1_name": mob["t1"],
                "enemy_tier1_icon": mob["t1_icon"],
                "enemy_tier2_name": mob["t2"],
                "enemy_tier2_icon": mob["t2_icon"],
                "enemy_tier3_name": mob["t3"],
                "enemy_tier3_icon": mob["t3_icon"],
                "ore_name": "Fonte de Alimentação de W-Engine",
                "ore_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4f1444b51f52e8e0ad4a8dc13432b04f.png",
                "currency_name": "Dennys",
                "currency_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4fde02b5f3a4c790dcbef6c74cb4fabf.png",
            }

        return {}

    def _is_character_farm_open_today(
        self, game_id: str, char_data: Dict[str, Any], weekday: Optional[int] = None
    ) -> bool:
        """Verifica se o material de talento/ascensão do personagem está disponível hoje."""
        if weekday is None:
            weekday = datetime.now().weekday()

        if game_id in ["hsr", "zzz"]:
            return True

        if game_id == "genshin":
            if weekday == 6:
                return True
            domain_days = char_data.get("domain_days", [])
            return weekday in domain_days

        return True

    def get_daily_farm_schedule(self, game_id: str, weekday: Optional[int] = None) -> Dict[str, Any]:
        """Gera a agenda consolidada de domínios e materiais abertos para o dia."""
        g = game_id.lower().strip()
        if weekday is None:
            weekday = datetime.now().weekday()

        weekday_name = WEEKDAY_NAMES_PT[weekday]
        is_sunday = weekday == 6

        if g == "genshin":
            open_talents = []
            open_weapons = []
            open_chars = []

            domains_data = self._cache["genshin"].get("domains", GENSHIN_DOMAINS_SCHEDULE)

            for nation, data in domains_data.get("talent_books", {}).items():
                dom_name = data.get("domain", nation.title())
                for sch_key, sch in data.get("schedules", {}).items():
                    if is_sunday or weekday in sch.get("days", []):
                        open_talents.append(
                            {
                                "nation": nation.title(),
                                "domain": dom_name,
                                "material": sch["name"],
                                "characters": sch.get("characters", []),
                            }
                        )
                        open_chars.extend(sch.get("characters", []))

            for nation, data in domains_data.get("weapon_materials", {}).items():
                dom_name = data.get("domain", nation.title())
                for sch_key, sch in data.get("schedules", {}).items():
                    if is_sunday or weekday in sch.get("days", []):
                        open_weapons.append({"nation": nation.title(), "domain": dom_name, "material": sch["name"]})

            # Incorpora todos os personagens do cache que atendem aos dias de farm
            all_genshin_chars = self._cache.get("genshin", {}).get("characters", {})
            for cid, cdata in all_genshin_chars.items():
                if self._is_character_farm_open_today("genshin", cdata, weekday):
                    cname = cdata.get("name")
                    if cname:
                        open_chars.append(cname)

            return {
                "game_id": "genshin",
                "weekday": weekday,
                "weekday_name": weekday_name,
                "is_all_open_sunday": is_sunday,
                "open_talents": open_talents,
                "open_weapons": open_weapons,
                "farmable_characters": sorted(list(set(open_chars))),
            }
        elif g in ["hsr", "zzz"]:
            chars = list(self._cache.get(g, {}).get("characters", {}).values())
            char_names = [c.get("name") for c in chars if c.get("name")]
            return {
                "game_id": g,
                "weekday": weekday,
                "weekday_name": weekday_name,
                "is_all_open_sunday": True,
                "open_talents": [],
                "open_weapons": [],
                "farmable_characters": sorted(list(set(char_names))),
            }

        return {
            "game_id": g,
            "weekday": weekday,
            "weekday_name": weekday_name,
            "is_all_open_sunday": True,
            "open_talents": [],
            "open_weapons": [],
            "farmable_characters": [],
        }

    def get_all_characters(self, game_id: str) -> List[Dict[str, Any]]:
        """Retorna a lista completa de personagens conhecidos com seus materiais."""
        g = game_id.lower().strip()
        if g not in self._cache:
            return []
        chars_dict = self._cache[g].get("characters", {})
        result = []
        for _, c in chars_dict.items():
            item = self._enrich_character_profile(g, dict(c))
            item["open_today"] = self._is_character_farm_open_today(g, item)
            result.append(item)
        return sorted(result, key=lambda x: x.get("name", ""))

    def sync_upstream_data(self, game_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Sincroniza os manifestos estáticos com repositórios GitHub Datamines / CDNs / HoYoWiki.
        Possui fallback automático para a base local ou seed em caso de timeout ou indisponibilidade.
        """
        target_games = [game_id.lower().strip()] if game_id else ["hsr", "genshin", "zzz"]
        sync_results = {}

        for g in target_games:
            if g == "hsr":
                res = self._sync_hsr()
            elif g == "genshin":
                res = self._sync_genshin()
            elif g == "zzz":
                res = self._sync_zzz()
            else:
                continue

            sync_results[g] = res

        return sync_results

    def _sync_hsr(self) -> Dict[str, Any]:
        """Sincroniza dados de HSR a partir do Mar-7th/StarRailRes com múltiplos mirrors e retries."""
        endpoints = [
            "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/index_min/pt/characters.json",
            "https://cdn.jsdelivr.net/gh/Mar-7th/StarRailRes@master/index_min/pt/characters.json",
            "https://fastly.jsdelivr.net/gh/Mar-7th/StarRailRes@master/index_min/pt/characters.json",
        ]
        fetched_data, source_url = fetch_json_with_retry(endpoints)
        source_used = "StarRailRes (GitHub/CDN)" if fetched_data else None

        current_chars = dict(self._cache["hsr"].get("characters", HSR_CHARACTERS_SEED))

        if fetched_data and isinstance(fetched_data, dict):
            path_map = {
                "Warlock": "Nihility",
                "Warrior": "Destruction",
                "Rogue": "Hunt",
                "Mage": "Erudition",
                "Shaman": "Harmony",
                "Knight": "Preservation",
                "Priest": "Abundance",
                "Memory": "Remembrance",
            }
            elem_map = {"Thunder": "Lightning"}
            for cid, cinfo in fetched_data.items():
                name = cinfo.get("name", "")
                if not name:
                    continue
                safe_id = name.lower().replace(" ", "_").replace("•", "").replace("'", "")
                rarity = cinfo.get("rarity", 5)
                if isinstance(rarity, str) and rarity.isdigit():
                    rarity = int(rarity)

                existing = current_chars.get(safe_id, {})
                raw_path = cinfo.get("path", existing.get("path", ""))
                norm_path = path_map.get(raw_path, raw_path)
                raw_elem = cinfo.get("element", existing.get("element", ""))
                norm_elem = elem_map.get(raw_elem, raw_elem)

                current_chars[safe_id] = {
                    "id": safe_id,
                    "name": name,
                    "rarity": rarity,
                    "element": norm_elem,
                    "path": norm_path,
                    "calyx_mat": existing.get("calyx_mat", "Cálice de Rastros da Via"),
                    "calyx_tier2_name": existing.get("calyx_tier2_name", "Esboço de Rastro (2★)"),
                    "calyx_tier2_icon": existing.get(
                        "calyx_tier2_icon",
                        "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110.png",
                    ),
                    "calyx_tier3_name": existing.get("calyx_tier3_name", "Dinâmica de Rastro (3★)"),
                    "calyx_tier3_icon": existing.get(
                        "calyx_tier3_icon",
                        "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110.png",
                    ),
                    "calyx_tier4_name": existing.get("calyx_tier4_name", "Conhecimento de Rastro (4★)"),
                    "calyx_tier4_icon": existing.get(
                        "calyx_tier4_icon",
                        "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110.png",
                    ),
                    "stagnant_shadow_mat": existing.get("stagnant_shadow_mat", "Sombra Estagnada"),
                    "boss_icon": existing.get(
                        "boss_icon", "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/201.png"
                    ),
                    "echo_of_war_mat": existing.get("echo_of_war_mat", "Eco da Guerra"),
                    "weekly_icon": existing.get(
                        "weekly_icon", "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/3.png"
                    ),
                    "schedule_type": "Daily",
                    "hoyolab_id": str(cid),
                    "icon": cinfo.get("icon", ""),
                }

        # Retroalimenta entidades locais de HSR (SQLite Roster e guias de meta) no manifesto
        try:
            import database
            roster_chars = database.get_roster_data("hsr")
            meta_path_map = {}
            meta_md_path = os.path.join(database.BASE_DIR, "hsr", "meta_endgame_hsr.md")
            if os.path.exists(meta_md_path):
                with open(meta_md_path, "r", encoding="utf-8") as mf:
                    for mline in mf:
                        mm = re.search(r"-\s*([^(\n]+?)\s*\(\d+★\s*([^-]+?)\s*-\s*([^\)]+?)\)", mline)
                        if mm:
                            c_key = re.sub(r"[^a-z0-9]", "", mm.group(1).lower())
                            raw_p = mm.group(3).strip()
                            clean_p = re.split(r"[\s\(]", raw_p)[0].strip()
                            if clean_p:
                                meta_path_map[c_key] = clean_p.capitalize()

            for rc in roster_chars:
                r_name = rc.get("name", "").strip()
                r_id = str(rc.get("id") or rc.get("character_id") or "")
                if not r_name or not r_id:
                    continue
                safe_id = re.sub(r"[^a-z0-9_]", "", r_name.lower().replace(" ", "_")).strip("_")
                c_clean = re.sub(r"[^a-z0-9]", "", r_name.lower())

                already_exists = False
                for existing_k, existing_v in current_chars.items():
                    if existing_v.get("hoyolab_id") == r_id or existing_k == safe_id:
                        already_exists = True
                        break

                if not already_exists:
                    r_elem = str(rc.get("element") or "Quantum").capitalize()
                    r_path = rc.get("path") or meta_path_map.get(c_clean)
                    if not r_path:
                        for mpk, mpv in meta_path_map.items():
                            if mpk in c_clean or c_clean in mpk:
                                r_path = mpv
                                break
                    r_path = r_path or "Elation"

                    current_chars[safe_id] = {
                        "id": safe_id,
                        "name": r_name,
                        "rarity": int(rc.get("rarity") or 5),
                        "element": r_elem,
                        "path": r_path,
                        "calyx_mat": "Cálice de Rastros da Via",
                        "calyx_tier2_name": "Esboço de Rastro (2★)",
                        "calyx_tier2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110.png",
                        "calyx_tier3_name": "Dinâmica de Rastro (3★)",
                        "calyx_tier3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110.png",
                        "calyx_tier4_name": "Conhecimento de Rastro (4★)",
                        "calyx_tier4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110.png",
                        "stagnant_shadow_mat": "Sombra Estagnada",
                        "boss_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/201.png",
                        "echo_of_war_mat": "Eco da Guerra",
                        "weekly_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/3.png",
                        "schedule_type": "Daily",
                        "hoyolab_id": r_id,
                        "icon": rc.get("icon", ""),
                    }
        except Exception as retro_err:
            print(f"[WARN] Falha ao retroalimentar manifesto HSR com dados locais: {retro_err}")

        payload = {"characters": current_chars}
        self._cache["hsr"] = payload

        try:
            with open(self._get_file_path("hsr"), "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return {
            "status": "success" if source_used else "offline_ready",
            "source": source_used or "Local Seed/Cache",
            "character_count": len(current_chars),
            "updated_at": datetime.now().isoformat(),
        }

    def _sync_genshin(self) -> Dict[str, Any]:
        """Sincroniza manifestos de Genshin Impact consumindo EnkaNetwork Datamines, theBowja/genshin-db e integrando ao catálogo com fallback resiliente."""
        chars_endpoints = [
            "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/characters.json",
            "https://cdn.jsdelivr.net/gh/EnkaNetwork/API-docs@master/store/characters.json",
        ]
        loc_endpoints = [
            "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/loc.json",
            "https://cdn.jsdelivr.net/gh/EnkaNetwork/API-docs@master/store/loc.json",
        ]

        fetched_chars, _ = fetch_json_with_retry(chars_endpoints)
        fetched_loc, _ = fetch_json_with_retry(loc_endpoints)
        source_used = "EnkaNetwork & Open Datamines (GitHub/CDN)" if (fetched_chars and fetched_loc) else None

        current_chars = dict(GENSHIN_CHARACTERS_SEED)
        if "characters" in self._cache.get("genshin", {}):
            current_chars.update(self._cache["genshin"]["characters"])
        current_domains = self._cache.get("genshin", {}).get("domains", GENSHIN_DOMAINS_SCHEDULE)

        if fetched_chars and fetched_loc:
            elem_map = {
                "Ice": "Cryo",
                "Fire": "Pyro",
                "Electric": "Electro",
                "Water": "Hydro",
                "Wind": "Anemo",
                "Rock": "Geo",
                "Grass": "Dendro",
            }
            weap_map = {
                "WEAPON_SWORD_ONE_HAND": "Sword",
                "WEAPON_CLAYMORE": "Claymore",
                "WEAPON_POLE": "Polearm",
                "WEAPON_BOW": "Bow",
                "WEAPON_CATALYST": "Catalyst",
            }
            loc_pt = fetched_loc.get("pt", {})
            loc_en = fetched_loc.get("en", {})

            for cid, cinfo in fetched_chars.items():
                name_hash = str(cinfo.get("NameTextMapHash", ""))
                name = loc_pt.get(name_hash) or loc_en.get(name_hash, "")
                if not name or "{" in name:
                    continue

                safe_id = name.lower().replace(" ", "_").replace("•", "").replace("'", "")
                rarity = 5 if cinfo.get("QualityType") == "QUALITY_ORANGE" else 4
                elem = elem_map.get(cinfo.get("Element"), cinfo.get("Element", ""))
                weap = weap_map.get(cinfo.get("WeaponType"), cinfo.get("WeaponType", ""))

                existing = current_chars.get(safe_id, GENSHIN_CHARACTERS_SEED.get(safe_id, {}))

                char_entry = {
                    "id": safe_id,
                    "name": name,
                    "rarity": rarity,
                    "element": elem or existing.get("element", "Anemo"),
                    "weapon": weap or existing.get("weapon", "Sword"),
                    "talent_book": existing.get("talent_book", "Livro de Talento"),
                    "talent_key": existing.get("talent_key", ""),
                    "domain_days": existing.get("domain_days", [0, 3, 6]),
                    "boss_mat": existing.get("boss_mat", "Material de Chefe"),
                    "boss_icon": existing.get("boss_icon", "https://enka.network/ui/UI_ItemIcon_113001.png"),
                    "local_specialty": existing.get("local_specialty", "Especialidade Local"),
                    "specialty_icon": existing.get("specialty_icon", "https://enka.network/ui/UI_ItemIcon_100021.png"),
                    "weekly_boss_mat": existing.get("weekly_boss_mat", "Material de Chefe Semanal"),
                    "weekly_icon": existing.get("weekly_icon", "https://enka.network/ui/UI_ItemIcon_113021.png"),
                    "enemy_key": existing.get("enemy_key", "slime"),
                    "hoyolab_id": str(cid),
                    "enka_id": str(cid),
                    "side_icon": cinfo.get("SideIconName", ""),
                }

                # Auto-enriquecimento dinâmico caso seja um personagem novo descoberto via Upstream
                char_entry = self._enrich_character_profile("genshin", char_entry)
                current_chars[safe_id] = char_entry

        payload = {"characters": current_chars, "domains": current_domains}
        self._cache["genshin"] = payload

        try:
            with open(self._get_file_path("genshin"), "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return {
            "status": "success" if source_used else "offline_ready",
            "source": source_used or "Local Structured Seed/Datamine",
            "character_count": len(current_chars),
            "updated_at": datetime.now().isoformat(),
        }

    def _sync_zzz(self) -> Dict[str, Any]:
        """Sincroniza manifestos de Zenless Zone Zero consumindo Prydwen e datamines abertos."""
        current_chars = dict(self._cache["zzz"].get("characters", ZZZ_CHARACTERS_SEED))
        source_used = None

        try:
            from scrapers import PrydwenZZZScraper

            scraper = PrydwenZZZScraper()
            agent_list = scraper.get_agent_list()
            if agent_list and len(agent_list) > 0:
                source_used = "Prydwen ZZZ Live Catalog"
                for ag in agent_list:
                    ag_name = ag.get("name", "").strip()
                    if not ag_name:
                        continue
                    safe_id = ag_name.lower().replace(" ", "_").replace("•", "").replace("'", "").replace(":", "")
                    if safe_id not in current_chars:
                        current_chars[safe_id] = {
                            "id": safe_id,
                            "name": ag_name,
                            "rarity": 5,
                            "element": "Physical",
                            "specialty": "Attack",
                            "chip_type": "Chip de Combate Especializado",
                            "core_skill_mat": "Emblema de Especialista",
                            "weekly_boss_mat": "Material de Notorious Hunt",
                            "schedule_type": "Daily",
                            "url": ag.get("url", ""),
                        }
        except Exception:
            pass

        payload = {"characters": current_chars}
        self._cache["zzz"] = payload

        try:
            with open(self._get_file_path("zzz"), "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return {
            "status": "success" if source_used else "offline_ready",
            "source": source_used or "Local Structured Seed/Datamine",
            "character_count": len(current_chars),
            "updated_at": datetime.now().isoformat(),
        }

    def get_character_by_hoyolab_id(self, game_id: str, hoyolab_id: str) -> Optional[Dict[str, Any]]:
        """Localiza personagem diretamente pelo ID numérico oficial da HoYoverse/HoYoLAB."""
        g = game_id.lower().strip()
        if g not in self._cache:
            return None
        hid_str = str(hoyolab_id).strip()
        chars = self._cache[g].get("characters", {})
        for _, cdata in chars.items():
            if str(cdata.get("hoyolab_id", "")) == hid_str or str(cdata.get("enka_id", "")) == hid_str:
                return self._enrich_character_profile(g, dict(cdata))
        return None

    def get_sync_status(self) -> Dict[str, Any]:
        """Retorna o sumário de integridade e contagem de itens dos dados estáticos."""
        return {
            "genshin": {
                "characters": len(self._cache["genshin"].get("characters", {})),
                "domains_active": True,
                "offline_ready": True,
            },
            "hsr": {"characters": len(self._cache["hsr"].get("characters", {})), "offline_ready": True},
            "zzz": {"characters": len(self._cache["zzz"].get("characters", {})), "offline_ready": True},
            "last_check": datetime.now().isoformat(),
        }


# Instância Singleton global
static_data_manager = StaticDataManager()
