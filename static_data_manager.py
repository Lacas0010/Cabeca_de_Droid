import os
import re
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import requests


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DATA_DIR = os.path.join(BASE_DIR, "static_data")

def fetch_json_with_retry(urls: List[str], headers: Optional[Dict[str, str]] = None, max_retries: int = 2, backoff_factor: float = 0.4) -> Tuple[Optional[Any], Optional[str]]:
    """
    Realiza requisição HTTP resiliente com retry, exponential backoff e fallback entre múltiplos mirrors.
    Trata 403, 429, 503 e timeouts de rede sem quebrar a execução.
    """
    req_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
    }
    if headers:
        req_headers.update(headers)

    for url in urls:
        for attempt in range(max_retries + 1):
            try:
                resp = requests.get(url, headers=req_headers, timeout=8)

                if resp.status_code == 200:
                    return resp.json(), url
                elif resp.status_code in [403, 429, 503]:
                    time.sleep(backoff_factor * (2 ** attempt))
                    continue
            except Exception:
                time.sleep(backoff_factor * (2 ** attempt))
                continue
    return None, None


# ==========================================================
# DIAS DA SEMANA PADRONIZADOS
# 0 = Segunda, 1 = Terça, 2 = Quarta, 3 = Quinta, 4 = Sexta, 5 = Sábado, 6 = Domingo
# ==========================================================
WEEKDAY_NAMES_PT = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo"
]

# ==========================================================
# CATÁLOGO DE LIVROS DE TALENTO E MATERIAIS DE GENSHIN IMPACT
# ==========================================================
GENSHIN_TALENT_BOOKS = {
    "liberdade": {
        "base": "Liberdade",
        "t2": "Ensinamentos da Liberdade (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104301.png",
        "t3": "Guia da Liberdade (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104302.png",
        "t4": "Filosofias da Liberdade (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104303.png",
        "days": [0, 3, 6]
    },
    "resistencia": {
        "base": "Resistência",
        "t2": "Ensinamentos da Resistência (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104304.png",
        "t3": "Guia da Resistência (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104305.png",
        "t4": "Filosofias da Resistência (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104306.png",
        "days": [1, 4, 6]
    },
    "poemas": {
        "base": "Poemas",
        "t2": "Ensinamentos de Poemas (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104307.png",
        "t3": "Guia de Poemas (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104308.png",
        "t4": "Filosofias de Poemas (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104309.png",
        "days": [2, 5, 6]
    },
    "prosperidade": {
        "base": "Prosperidade",
        "t2": "Ensinamentos da Prosperidade (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104310.png",
        "t3": "Guia da Prosperidade (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104311.png",
        "t4": "Filosofias da Prosperidade (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104312.png",
        "days": [0, 3, 6]
    },
    "diligencia": {
        "base": "Diligência",
        "t2": "Ensinamentos da Diligência (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104313.png",
        "t3": "Guia da Diligência (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104314.png",
        "t4": "Filosofias da Diligência (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104315.png",
        "days": [1, 4, 6]
    },
    "ouro": {
        "base": "Ouro",
        "t2": "Ensinamentos de Ouro (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104316.png",
        "t3": "Guia de Ouro (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104317.png",
        "t4": "Filosofias de Ouro (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104318.png",
        "days": [2, 5, 6]
    },
    "transitoriedade": {
        "base": "Transitoriedade",
        "t2": "Ensinamentos da Transitoriedade (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104320.png",
        "t3": "Guia da Transitoriedade (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104321.png",
        "t4": "Filosofias da Transitoriedade (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104322.png",
        "days": [0, 3, 6]
    },
    "elegancia": {
        "base": "Elegância",
        "t2": "Ensinamentos da Elegância (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104323.png",
        "t3": "Guia da Elegância (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104324.png",
        "t4": "Filosofias da Elegância (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104325.png",
        "days": [1, 4, 6]
    },
    "luz": {
        "base": "Luz Celeste",
        "t2": "Ensinamentos da Luz Celeste (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104326.png",
        "t3": "Guia da Luz Celeste (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104327.png",
        "t4": "Filosofias da Luz Celeste (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104328.png",
        "days": [2, 5, 6]
    },
    "admoestacao": {
        "base": "Admoestação",
        "t2": "Ensinamentos de Admoestação (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104329.png",
        "t3": "Guia de Admoestação (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104330.png",
        "t4": "Filosofias de Admoestação (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104331.png",
        "days": [0, 3, 6]
    },
    "engenhosidade": {
        "base": "Engenhosidade",
        "t2": "Ensinamentos da Engenhosidade (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104332.png",
        "t3": "Guia da Engenhosidade (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104333.png",
        "t4": "Filosofias da Engenhosidade (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104334.png",
        "days": [1, 4, 6]
    },
    "praxis": {
        "base": "Práxis",
        "t2": "Ensinamentos da Práxis (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104335.png",
        "t3": "Guia da Práxis (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104336.png",
        "t4": "Filosofias da Práxis (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104337.png",
        "days": [2, 5, 6]
    },
    "equidade": {
        "base": "Equidade",
        "t2": "Ensinamentos da Equidade (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104338.png",
        "t3": "Guia da Equidade (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104339.png",
        "t4": "Filosofias da Equidade (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104340.png",
        "days": [0, 3, 6]
    },
    "justica": {
        "base": "Justiça",
        "t2": "Ensinamentos da Justiça (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104341.png",
        "t3": "Guia da Justiça (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104342.png",
        "t4": "Filosofias da Justiça (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104343.png",
        "days": [1, 4, 6]
    },
    "ordem": {
        "base": "Ordem",
        "t2": "Ensinamentos da Ordem (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104344.png",
        "t3": "Guia da Ordem (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104345.png",
        "t4": "Filosofias da Ordem (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104346.png",
        "days": [2, 5, 6]
    },
    "disputa": {
        "base": "Disputa",
        "t2": "Ensinamentos da Disputa (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104347.png",
        "t3": "Guia da Disputa (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104348.png",
        "t4": "Filosofias da Disputa (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104349.png",
        "days": [0, 3, 6]
    },
    "ignicao": {
        "base": "Ignição",
        "t2": "Ensinamentos da Ignição (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104350.png",
        "t3": "Guia da Ignição (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104351.png",
        "t4": "Filosofias da Ignição (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104352.png",
        "days": [1, 4, 6]
    },
    "conflito": {
        "base": "Conflito",
        "t2": "Ensinamentos do Conflito (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_104353.png",
        "t3": "Guia do Conflito (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_104354.png",
        "t4": "Filosofias do Conflito (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_104355.png",
        "days": [2, 5, 6]
    }
}

GENSHIN_MOB_DROPS = {
    "red_silk": {
        "t1": "Seda Vermelha Desbotada (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112065.png",
        "t2": "Seda Vermelha Bordada (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112066.png",
        "t3": "Seda Vermelha com Brocado (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112067.png"
    },
    "nectar": {
        "t1": "Néctar da Flor Gigante (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112038.png",
        "t2": "Néctar Brilhante (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112039.png",
        "t3": "Néctar Elemental (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112040.png"
    },
    "gear": {
        "t1": "Engrenagem de Malha (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112080.png",
        "t2": "Engrenagem Mecânica (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112081.png",
        "t3": "Engrenagem Articulada (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112082.png"
    },
    "handguard": {
        "t1": "Protetor de Mão Antigo (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112044.png",
        "t2": "Protetor de Mão Kageuchi (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112045.png",
        "t3": "Protetor de Mão Famoso (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112046.png"
    },
    "slime": {
        "t1": "Condensado de Slime (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112002.png",
        "t2": "Secreção de Slime (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112003.png",
        "t3": "Concentrado de Slime (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112004.png"
    },
    "mask": {
        "t1": "Máscara Danificada (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112005.png",
        "t2": "Máscara Manchada (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112006.png",
        "t3": "Máscara Ominosa (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112007.png"
    },
    "scroll": {
        "t1": "Guia de Pergaminho (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112008.png",
        "t2": "Pergaminho Lacrado (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112009.png",
        "t3": "Pergaminho da Maldição (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112010.png"
    },
    "arrowhead": {
        "t1": "Ponta de Flecha Firme (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112011.png",
        "t2": "Ponta de Flecha Afiada (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112012.png",
        "t3": "Ponta de Flecha Usada (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112013.png"
    },
    "chaos": {
        "t1": "Dispositivo do Caos (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112014.png",
        "t2": "Circuito do Caos (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112015.png",
        "t3": "Núcleo do Caos (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112016.png"
    },
    "treasure_hoarder": {
        "t1": "Insígnia dos Ladrões de Tesouro (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112035.png",
        "t2": "Insígnia do Corvo Prateado (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112036.png",
        "t3": "Insígnia do Corvo Dourado (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112037.png"
    },
    "fatui_insignia": {
        "t1": "Insígnia de Recruta (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112032.png",
        "t2": "Insígnia de Sargento (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112033.png",
        "t3": "Insígnia de Oficial (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112034.png"
    },
    "specter": {
        "t1": "Casca de Espectro (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112053.png",
        "t2": "Coração de Espectro (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112054.png",
        "t3": "Núcleo de Espectro (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112055.png"
    },
    "fungal_spores": {
        "t1": "Esporos de Cogumelo (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112059.png",
        "t2": "Pólen Luminescente (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112060.png",
        "t3": "Cisto Cristalino (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112061.png"
    },
    "transoceanic": {
        "t1": "Pérola Transoceânica (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112077.png",
        "t2": "Pedaço Transoceânico (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112078.png",
        "t3": "Cristal Xenocromático (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112079.png"
    },
    "saurian_fang": {
        "t1": "Presa de Sauriano Jovem (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112098.png",
        "t2": "Presa de Sauriano Guerreiro (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112099.png",
        "t3": "Presa de Sauriano Tirano (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112100.png"
    },
    "whistle": {
        "t1": "Apito de Madeira Sentinela (1★)", "t1_icon": "https://enka.network/ui/UI_ItemIcon_112101.png",
        "t2": "Apito de Ferro Guerreiro (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_112102.png",
        "t3": "Apito Dourado Coroado (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_112103.png"
    }
}

GENSHIN_WEAPON_MATERIALS = {
    "decarabian": {
        "base": "Decarabian",
        "t2": "Telha da Torre de Decarabian (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114001.png",
        "t3": "Escombro da Cidade de Decarabian (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114002.png",
        "t4": "Fragmento Épico de Decarabian (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114003.png",
        "t5": "Pedaço Fraturado de Decarabian (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114004.png",
        "days": [0, 3, 6]
    },
    "boreal_wolf": {
        "base": "Lobo Boreal",
        "t2": "Leite de Dente de Lobo Boreal (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114005.png",
        "t3": "Dente Quebrado de Lobo Boreal (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114006.png",
        "t4": "Presa Quebrada de Lobo Boreal (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114007.png",
        "t5": "Nostalgia do Lobo Boreal (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114008.png",
        "days": [1, 4, 6]
    },
    "dandelion_gladiator": {
        "base": "Gladiador de Dente-de-Leão",
        "t2": "Manilha do Gladiador de Dente-de-Leão (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114009.png",
        "t3": "Corrente do Gladiador de Dente-de-Leão (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114010.png",
        "t4": "Grilhões do Gladiador de Dente-de-Leão (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114011.png",
        "t5": "Sonho do Gladiador de Dente-de-Leão (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114012.png",
        "days": [2, 5, 6]
    },
    "guyun": {
        "base": "Guyun",
        "t2": "Areia Brilhante de Guyun (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114013.png",
        "t3": "Pedra Brilhante de Guyun (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114014.png",
        "t4": "Relíquia de Guyun (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114015.png",
        "t5": "Corpo Divino de Guyun (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114016.png",
        "days": [0, 3, 6]
    },
    "mist_veiled": {
        "base": "Névoa Velada",
        "t2": "Chumbo de Névoa Velada (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114017.png",
        "t3": "Mercúrio de Névoa Velada (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114018.png",
        "t4": "Ouro de Névoa Velada (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114019.png",
        "t5": "Elixir de Névoa Velada (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114020.png",
        "days": [1, 4, 6]
    },
    "aerosiderite": {
        "base": "Aerosiderite",
        "t2": "Grão de Aerosiderite Negra (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114021.png",
        "t3": "Pedaço de Aerosiderite Negra (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114022.png",
        "t4": "Fragmento de Aerosiderite Negra (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114023.png",
        "t5": "Pedaço Maciço de Aerosiderite Negra (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114024.png",
        "days": [2, 5, 6]
    },
    "distant_sea": {
        "base": "Mar Distante",
        "t2": "Galho de Coral do Mar Distante (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114025.png",
        "t3": "Galho de Jade do Mar Distante (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114026.png",
        "t4": "Galho de Ouro do Mar Distante (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114027.png",
        "t5": "Ramo Dourado do Mar Distante (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114028.png",
        "days": [0, 3, 6]
    },
    "narukami": {
        "base": "Narukami",
        "t2": "Sabedoria de Narukami (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114029.png",
        "t3": "Alegria de Narukami (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114030.png",
        "t4": "Afeição de Narukami (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114031.png",
        "t5": "Valentia de Narukami (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114032.png",
        "days": [1, 4, 6]
    },
    "mask": {
        "base": "Máscara da Mordida de Tigre",
        "t2": "Máscara do Tenente Maligno (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114033.png",
        "t3": "Máscara da Mordida de Tigre (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114034.png",
        "t4": "Máscara do Chifre Único (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114035.png",
        "t5": "Máscara Kijin (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114036.png",
        "days": [2, 5, 6]
    },
    "iron_talisman": {
        "base": "Talismã de Ferro",
        "t2": "Eco do Poder Escorregadio (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114037.png",
        "t3": "Eco do Poder Remanescente (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114038.png",
        "t4": "Eco do Sonho Brilhante (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114039.png",
        "t5": "Eco do Passado Glorioso (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114040.png",
        "days": [0, 3, 6]
    },
    "oasis_garden": {
        "base": "Jardim do Oásis",
        "t2": "Graça do Jardim do Oásis (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114041.png",
        "t3": "Vislumbre do Jardim do Oásis (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114042.png",
        "t4": "Flor do Jardim do Oásis (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114043.png",
        "t5": "Verdade do Jardim do Oásis (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114044.png",
        "days": [1, 4, 6]
    },
    "scorching_sun": {
        "base": "Sol Escaldante",
        "t2": "Poder do Sol Escaldante (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114045.png",
        "t3": "Esplendor do Sol Escaldante (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114046.png",
        "t4": "Glória do Sol Escaldante (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114047.png",
        "t5": "Luz do Sol Escaldante (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114048.png",
        "days": [2, 5, 6]
    },
    "chord": {
        "base": "Acorde Antigo",
        "t2": "Fragmento de Acorde Antigo (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114049.png",
        "t3": "Movimento de Acorde Antigo (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114050.png",
        "t4": "Eco de Acorde Antigo (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114051.png",
        "t5": "Sinfonia de Acorde Antigo (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114052.png",
        "days": [0, 3, 6]
    },
    "dewdrop": {
        "base": "Gota d'Água Sagrada",
        "t2": "Gota de Orvalho Puro (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114053.png",
        "t3": "Condensado de Orvalho Puro (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114054.png",
        "t4": "Essência de Orvalho Puro (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114055.png",
        "t5": "Manancial de Orvalho Puro (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114056.png",
        "days": [1, 4, 6]
    },
    "sacred_sea": {
        "base": "Mar Primordial Sagrado",
        "t2": "Cálice Quebrado do Mar Primordial (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114057.png",
        "t3": "Cálice de Prata do Mar Primordial (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114058.png",
        "t4": "Cálice de Ouro do Mar Primordial (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114059.png",
        "t5": "Cálice Primordial Imaculado (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114060.png",
        "days": [2, 5, 6]
    },
    "night_wind": {
        "base": "Vento Noturno",
        "t2": "Consideração do Vento Noturno (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114061.png",
        "t3": "Premonição do Vento Noturno (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114062.png",
        "t4": "Visão do Vento Noturno (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114063.png",
        "t5": "Bênção do Vento Noturno (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114064.png",
        "days": [0, 3, 6]
    },
    "blazing_hearth": {
        "base": "Fogueira Ardente",
        "t2": "Coração de Fogueira Ardente (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114065.png",
        "t3": "Labareda de Fogueira Ardente (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114066.png",
        "t4": "Cinzas de Fogueira Ardente (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114067.png",
        "t5": "Glória de Fogueira Ardente (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114068.png",
        "days": [1, 4, 6]
    },
    "sacred_lord": {
        "base": "Senhor Sagrado",
        "t2": "Terror do Senhor Sagrado (2★)", "t2_icon": "https://enka.network/ui/UI_ItemIcon_114069.png",
        "t3": "Fúria do Senhor Sagrado (3★)", "t3_icon": "https://enka.network/ui/UI_ItemIcon_114070.png",
        "t4": "Majestade do Senhor Sagrado (4★)", "t4_icon": "https://enka.network/ui/UI_ItemIcon_114071.png",
        "t5": "Imortalidade do Senhor Sagrado (5★)", "t5_icon": "https://enka.network/ui/UI_ItemIcon_114072.png",
        "days": [2, 5, 6]
    }
}

GENSHIN_DOMAINS_SCHEDULE = {
    "talent_books": {
        "mondstadt": {
            "domain": "Fenda do Esquecimento (Mondstadt)",
            "schedules": {
                "mon_thu": {"name": "Liberdade (Freedom)", "days": [0, 3, 6], "characters": ["Amber", "Barbara", "Diona", "Klee", "Sucrose", "Tartaglia", "Aloy"]},
                "tue_fri": {"name": "Resistência (Resistance)", "days": [1, 4, 6], "characters": ["Bennett", "Diluc", "Eula", "Jean", "Mona", "Noelle", "Razor"]},
                "wed_sat": {"name": "Poemas (Ballad)", "days": [2, 5, 6], "characters": ["Albedo", "Fischl", "Kaeya", "Lisa", "Rosaria", "Venti", "Mika"]}
            }
        },
        "liyue": {
            "domain": "Mansão Taishan (Liyue)",
            "schedules": {
                "mon_thu": {"name": "Prosperidade (Prosperity)", "days": [0, 3, 6], "characters": ["Keqing", "Ningguang", "Qiqi", "Shenhe", "Xiao", "Yelan", "Gaming"]},
                "tue_fri": {"name": "Diligência (Diligence)", "days": [1, 4, 6], "characters": ["Chongyun", "Ganyu", "Hu Tao", "Kazuha", "Xiangling", "Yun Jin", "Yaoyao"]},
                "wed_sat": {"name": "Ouro (Gold)", "days": [2, 5, 6], "characters": ["Beidou", "Xingqiu", "Xinyan", "Yanfei", "Zhongli", "Baizhu"]}
            }
        },
        "inazuma": {
            "domain": "Jardim Violeta (Inazuma)",
            "schedules": {
                "mon_thu": {"name": "Transitoriedade (Transience)", "days": [0, 3, 6], "characters": ["Yoimiya", "Kokomi", "Thoma", "Shikanoin Heizou", "Kirara"]},
                "tue_fri": {"name": "Elegância (Elegance)", "days": [1, 4, 6], "characters": ["Kamisato Ayaka", "Kamisato Ayato", "Kujou Sara", "Kuki Shinobu", "Itto"]},
                "wed_sat": {"name": "Luz Celeste (Light)", "days": [2, 5, 6], "characters": ["Raiden Shogun", "Yae Miko", "Sayu", "Gorou"]}
            }
        },
        "sumeru": {
            "domain": "Campanário da Ignorância (Sumeru)",
            "schedules": {
                "mon_thu": {"name": "Admoestação (Admonition)", "days": [0, 3, 6], "characters": ["Tighnari", "Cyno", "Candace", "Faruzan"]},
                "tue_fri": {"name": "Engenhosidade (Ingenuity)", "days": [1, 4, 6], "characters": ["Nahida", "Alhaitham", "Dori", "Layla", "Kaveh"]},
                "wed_sat": {"name": "Práxis (Praxis)", "days": [2, 5, 6], "characters": ["Nilou", "Wanderer", "Dehya", "Collei", "Sethos"]}
            }
        },
        "fontaine": {
            "domain": "Glória Pálida Esquecida (Fontaine)",
            "schedules": {
                "mon_thu": {"name": "Equidade (Equity)", "days": [0, 3, 6], "characters": ["Lyney", "Neuvillette", "Navia", "Sigewinne"]},
                "tue_fri": {"name": "Justiça (Justice)", "days": [1, 4, 6], "characters": ["Freminet", "Furina", "Charlotte", "Clorinde"]},
                "wed_sat": {"name": "Ordem (Order)", "days": [2, 5, 6], "characters": ["Lynette", "Wriothesley", "Chevreuse", "Arlecchino", "Emilie"]}
            }
        },
        "natlan": {
            "domain": "Ruínas Incandescentes (Natlan)",
            "schedules": {
                "mon_thu": {"name": "Disputa (Contention)", "days": [0, 3, 6], "characters": ["Mualani", "Xilonen", "Ororon", "Mavuika"]},
                "tue_fri": {"name": "Ignição (Kindling)", "days": [1, 4, 6], "characters": ["Kinich", "Chasca", "Iansan"]},
                "wed_sat": {"name": "Conflito (Conflict)", "days": [2, 5, 6], "characters": ["Kachina", "Citlali"]}
            }
        }
    },
    "weapon_materials": {
        "mondstadt": {
            "domain": "Jardim de Cecília (Mondstadt)",
            "schedules": {
                "mon_thu": {"name": "Decarabian", "days": [0, 3, 6]},
                "tue_fri": {"name": "Lobo Boreal (Boreal Wolf)", "days": [1, 4, 6]},
                "wed_sat": {"name": "Gladiador de Dente-de-Leão (Dandelion Gladiator)", "days": [2, 5, 6]}
            }
        },
        "liyue": {
            "domain": "Labirinto Liangshan (Liyue)",
            "schedules": {
                "mon_thu": {"name": "Guyun", "days": [0, 3, 6]},
                "tue_fri": {"name": "Névoa Velada (Mist Veiled)", "days": [1, 4, 6]},
                "wed_sat": {"name": "Aerosiderite", "days": [2, 5, 6]}
            }
        },
        "inazuma": {
            "domain": "Corte da Areia Fluente (Inazuma)",
            "schedules": {
                "mon_thu": {"name": "Mar Distante (Distant Sea)", "days": [0, 3, 6]},
                "tue_fri": {"name": "Narukami", "days": [1, 4, 6]},
                "wed_sat": {"name": "Máscara de Mordida de Tigre (Mask of the Tiger's Bite)", "days": [2, 5, 6]}
            }
        },
        "sumeru": {
            "domain": "Torre do Orgulho Desprezível (Sumeru)",
            "schedules": {
                "mon_thu": {"name": "Talismã de Ferro (Iron Talisman)", "days": [0, 3, 6]},
                "tue_fri": {"name": "Jardim do Oásis (Oasis Garden)", "days": [1, 4, 6]},
                "wed_sat": {"name": "Sol Escaldante (Scorching Sun)", "days": [2, 5, 6]}
            }
        },
        "fontaine": {
            "domain": "Ecos das Marés Profundas (Fontaine)",
            "schedules": {
                "mon_thu": {"name": "Acorde Antigo (Chord)", "days": [0, 3, 6]},
                "tue_fri": {"name": "Gota d'Água Sagrada (Dewdrop)", "days": [1, 4, 6]},
                "wed_sat": {"name": "Mar Primordial Sagrado (Sacred Primordial Sea)", "days": [2, 5, 6]}
            }
        },
        "natlan": {
            "domain": "Fornalha das Chamas Eternas (Natlan)",
            "schedules": {
                "mon_thu": {"name": "Vento Noturno (Night-Wind)", "days": [0, 3, 6]},
                "tue_fri": {"name": "Fogueira Ardente (Blazing Hearth)", "days": [1, 4, 6]},
                "wed_sat": {"name": "Senhor Sagrado (Sacred Lord)", "days": [2, 5, 6]}
            }
        }
    }
}

GENSHIN_CHARACTERS_SEED = {
    # MONDSTADT
    "albedo": {"id": "albedo", "name": "Albedo", "rarity": 5, "element": "Geo", "weapon": "Sword", "talent_book": "Poemas (Ballad)", "talent_key": "poemas", "domain_days": [2, 5, 6], "boss_mat": "Pilar de Basalto", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113010.png", "local_specialty": "Cecília", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100022.png", "weekly_boss_mat": "Chifre de Monoceros Caeli", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113013.png", "enemy_key": "scroll"},
    "aloy": {"id": "aloy", "name": "Aloy", "rarity": 5, "element": "Cryo", "weapon": "Bow", "talent_book": "Liberdade (Freedom)", "talent_key": "liberdade", "domain_days": [0, 3, 6], "boss_mat": "Núcleo Cristalino Espectral", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113005.png", "local_specialty": "Medula de Cristal", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101205.png", "weekly_boss_mat": "Momento Derretido", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113026.png", "enemy_key": "specter"},
    "amber": {"id": "amber", "name": "Amber", "rarity": 4, "element": "Pyro", "weapon": "Bow", "talent_book": "Liberdade (Freedom)", "talent_key": "liberdade", "domain_days": [0, 3, 6], "boss_mat": "Semente de Fogo Eterno", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113009.png", "local_specialty": "Lâmpada de Grama", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100019.png", "weekly_boss_mat": "Pluma de Dvalin", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113002.png", "enemy_key": "arrowhead"},
    "barbara": {"id": "barbara", "name": "Barbara", "rarity": 4, "element": "Hydro", "weapon": "Catalyst", "talent_book": "Liberdade (Freedom)", "talent_key": "liberdade", "domain_days": [0, 3, 6], "boss_mat": "Coração da Água", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113007.png", "local_specialty": "Cogumelo Philanemo", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100023.png", "weekly_boss_mat": "Anel de Boreas", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113012.png", "enemy_key": "scroll"},
    "bennett": {"id": "bennett", "name": "Bennett", "rarity": 4, "element": "Pyro", "weapon": "Sword", "talent_book": "Resistência (Resistance)", "talent_key": "resistencia", "domain_days": [1, 4, 6], "boss_mat": "Semente de Fogo Eterno", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113009.png", "local_specialty": "Áster de Vento", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100024.png", "weekly_boss_mat": "Pluma de Dvalin", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113002.png", "enemy_key": "treasure_hoarder"},
    "diluc": {"id": "diluc", "name": "Diluc", "rarity": 5, "element": "Pyro", "weapon": "Claymore", "talent_book": "Resistência (Resistance)", "talent_key": "resistencia", "domain_days": [1, 4, 6], "boss_mat": "Semente de Fogo Eterno", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113009.png", "local_specialty": "Fruto Valberry", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100025.png", "weekly_boss_mat": "Pluma de Dvalin", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113002.png", "enemy_key": "fatui_insignia"},
    "diona": {"id": "diona", "name": "Diona", "rarity": 4, "element": "Cryo", "weapon": "Bow", "talent_book": "Liberdade (Freedom)", "talent_key": "liberdade", "domain_days": [0, 3, 6], "boss_mat": "Núcleo de Gelo", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113005.png", "local_specialty": "Lírio Calila", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100020.png", "weekly_boss_mat": "Fragmento do Rei do Mal", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113014.png", "enemy_key": "arrowhead"},
    "eula": {"id": "eula", "name": "Eula", "rarity": 5, "element": "Cryo", "weapon": "Claymore", "talent_book": "Resistência (Resistance)", "talent_key": "resistencia", "domain_days": [1, 4, 6], "boss_mat": "Flor Cristalina", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113021.png", "local_specialty": "Dente-de-Leão", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100021.png", "weekly_boss_mat": "Coroa do Senhor dos Dragões", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113018.png", "enemy_key": "mask"},
    "fischl": {"id": "fischl", "name": "Fischl", "rarity": 4, "element": "Electro", "weapon": "Bow", "talent_book": "Poemas (Ballad)", "talent_key": "poemas", "domain_days": [2, 5, 6], "boss_mat": "Prisma de Raio", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113008.png", "local_specialty": "Lâmpada de Grama", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100019.png", "weekly_boss_mat": "Espírito de Boreas", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113010.png", "enemy_key": "arrowhead"},
    "jean": {"id": "jean", "name": "Jean", "rarity": 5, "element": "Anemo", "weapon": "Sword", "talent_book": "Resistência (Resistance)", "talent_key": "resistencia", "domain_days": [1, 4, 6], "boss_mat": "Semente de Furacão", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113006.png", "local_specialty": "Dente-de-Leão", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100021.png", "weekly_boss_mat": "Pluma de Dvalin", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113002.png", "enemy_key": "mask"},
    "kaeya": {"id": "kaeya", "name": "Kaeya", "rarity": 4, "element": "Cryo", "weapon": "Sword", "talent_book": "Poemas (Ballad)", "talent_key": "poemas", "domain_days": [2, 5, 6], "boss_mat": "Núcleo de Gelo", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113005.png", "local_specialty": "Lírio Calila", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100020.png", "weekly_boss_mat": "Espírito de Boreas", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113010.png", "enemy_key": "treasure_hoarder"},
    "klee": {"id": "klee", "name": "Klee", "rarity": 5, "element": "Pyro", "weapon": "Catalyst", "talent_book": "Liberdade (Freedom)", "talent_key": "liberdade", "domain_days": [0, 3, 6], "boss_mat": "Semente de Fogo Eterno", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113009.png", "local_specialty": "Cogumelo Philanemo", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100023.png", "weekly_boss_mat": "Anel de Boreas", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113012.png", "enemy_key": "scroll"},
    "lisa": {"id": "lisa", "name": "Lisa", "rarity": 4, "element": "Electro", "weapon": "Catalyst", "talent_book": "Poemas (Ballad)", "talent_key": "poemas", "domain_days": [2, 5, 6], "boss_mat": "Prisma de Raio", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113008.png", "local_specialty": "Valberry", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100025.png", "weekly_boss_mat": "Garra de Dvalin", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113003.png", "enemy_key": "slime"},
    "mika": {"id": "mika", "name": "Mika", "rarity": 4, "element": "Cryo", "weapon": "Polearm", "talent_book": "Poemas (Ballad)", "talent_key": "poemas", "domain_days": [2, 5, 6], "boss_mat": "Crisálida da Areia", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113043.png", "local_specialty": "Gancho do Lobo", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100018.png", "weekly_boss_mat": "Espelho de Mushin", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113043.png", "enemy_key": "fatui_insignia"},
    "mona": {"id": "mona", "name": "Mona", "rarity": 5, "element": "Hydro", "weapon": "Catalyst", "talent_book": "Resistência (Resistance)", "talent_key": "resistencia", "domain_days": [1, 4, 6], "boss_mat": "Coração da Água", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113007.png", "local_specialty": "Cogumelo Philanemo", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100023.png", "weekly_boss_mat": "Anel de Boreas", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113012.png", "enemy_key": "nectar"},
    "noelle": {"id": "noelle", "name": "Noelle", "rarity": 4, "element": "Geo", "weapon": "Claymore", "talent_book": "Resistência (Resistance)", "talent_key": "resistencia", "domain_days": [1, 4, 6], "boss_mat": "Pilar de Basalto", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113010.png", "local_specialty": "Valberry", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100025.png", "weekly_boss_mat": "Garra de Dvalin", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113003.png", "enemy_key": "mask"},
    "razor": {"id": "razor", "name": "Razor", "rarity": 4, "element": "Electro", "weapon": "Claymore", "talent_book": "Resistência (Resistance)", "talent_key": "resistencia", "domain_days": [1, 4, 6], "boss_mat": "Prisma de Raio", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113008.png", "local_specialty": "Gancho do Lobo", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100018.png", "weekly_boss_mat": "Garra de Dvalin", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113003.png", "enemy_key": "mask"},
    "rosaria": {"id": "rosaria", "name": "Rosaria", "rarity": 4, "element": "Cryo", "weapon": "Polearm", "talent_book": "Poemas (Ballad)", "talent_key": "poemas", "domain_days": [2, 5, 6], "boss_mat": "Núcleo de Gelo", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113005.png", "local_specialty": "Valberry", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100025.png", "weekly_boss_mat": "Sombra do Guerreiro", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113015.png", "enemy_key": "fatui_insignia"},
    "sucrose": {"id": "sucrose", "name": "Sucrose", "rarity": 4, "element": "Anemo", "weapon": "Catalyst", "talent_book": "Liberdade (Freedom)", "talent_key": "liberdade", "domain_days": [0, 3, 6], "boss_mat": "Semente de Furacão", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113006.png", "local_specialty": "Áster de Vento", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100024.png", "weekly_boss_mat": "Espírito de Boreas", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113010.png", "enemy_key": "nectar"},
    "venti": {"id": "venti", "name": "Venti", "rarity": 5, "element": "Anemo", "weapon": "Bow", "talent_book": "Poemas (Ballad)", "talent_key": "poemas", "domain_days": [2, 5, 6], "boss_mat": "Semente de Furacão", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113006.png", "local_specialty": "Cecília", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100022.png", "weekly_boss_mat": "Cauda do Vento Oriental", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113004.png", "enemy_key": "slime"},

    # LIYUE
    "baizhu": {"id": "baizhu", "name": "Baizhu", "rarity": 5, "element": "Dendro", "weapon": "Catalyst", "talent_book": "Ouro (Gold)", "talent_key": "ouro", "domain_days": [2, 5, 6], "boss_mat": "Anel da Escuridão Sombria", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113045.png", "local_specialty": "Sino de Vidro", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100029.png", "weekly_boss_mat": "Samambaia Primordial", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113047.png", "enemy_key": "fungal_spores"},
    "beidou": {"id": "beidou", "name": "Beidou", "rarity": 4, "element": "Electro", "weapon": "Claymore", "talent_book": "Ouro (Gold)", "talent_key": "ouro", "domain_days": [2, 5, 6], "boss_mat": "Prisma de Raio", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113008.png", "local_specialty": "Jade Noctiluque", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100032.png", "weekly_boss_mat": "Suspiro de Dvalin", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113001.png", "enemy_key": "treasure_hoarder"},
    "chongyun": {"id": "chongyun", "name": "Chongyun", "rarity": 4, "element": "Cryo", "weapon": "Claymore", "talent_book": "Diligência (Diligence)", "talent_key": "diligencia", "domain_days": [1, 4, 6], "boss_mat": "Núcleo de Gelo", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113005.png", "local_specialty": "Cor Lapis", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100026.png", "weekly_boss_mat": "Suspiro de Dvalin", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113001.png", "enemy_key": "mask"},
    "gaming": {"id": "gaming", "name": "Gaming", "rarity": 4, "element": "Pyro", "weapon": "Claymore", "talent_book": "Prosperidade (Prosperity)", "talent_key": "prosperidade", "domain_days": [0, 3, 6], "boss_mat": "Nuvem do Imperador", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113055.png", "local_specialty": "Concha Estelar", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100031.png", "weekly_boss_mat": "Massa Sem Luz", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113054.png", "enemy_key": "slime"},
    "ganyu": {"id": "ganyu", "name": "Ganyu", "rarity": 5, "element": "Cryo", "weapon": "Bow", "talent_book": "Diligência (Diligence)", "talent_key": "diligencia", "domain_days": [1, 4, 6], "boss_mat": "Núcleo de Gelo", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113005.png", "local_specialty": "Flor Qingxin", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100030.png", "weekly_boss_mat": "Sombra do Guerreiro", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113015.png", "enemy_key": "nectar"},
    "hu_tao": {"id": "hu_tao", "name": "Hu Tao", "rarity": 5, "element": "Pyro", "weapon": "Polearm", "talent_book": "Diligência (Diligence)", "talent_key": "diligencia", "domain_days": [1, 4, 6], "boss_mat": "Jade Juvenil", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113017.png", "local_specialty": "Flor da Seda", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100028.png", "weekly_boss_mat": "Fragmento do Rei do Mal", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113014.png", "enemy_key": "nectar"},
    "kaedehara_kazuha": {"id": "kazuha", "name": "Kaedehara Kazuha", "rarity": 5, "element": "Anemo", "weapon": "Sword", "talent_book": "Diligência (Diligence)", "talent_key": "diligencia", "domain_days": [1, 4, 6], "boss_mat": "Núcleo de Marionete", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113023.png", "local_specialty": "Ganoderma Marinho", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101201.png", "weekly_boss_mat": "Escama Dourada", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113020.png", "enemy_key": "treasure_hoarder"},
    "kazuha": {"id": "kazuha", "name": "Kaedehara Kazuha", "rarity": 5, "element": "Anemo", "weapon": "Sword", "talent_book": "Diligência (Diligence)", "talent_key": "diligencia", "domain_days": [1, 4, 6], "boss_mat": "Núcleo de Marionete", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113023.png", "local_specialty": "Ganoderma Marinho", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101201.png", "weekly_boss_mat": "Escama Dourada", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113020.png", "enemy_key": "treasure_hoarder"},
    "keqing": {"id": "keqing", "name": "Keqing", "rarity": 5, "element": "Electro", "weapon": "Sword", "talent_book": "Prosperidade (Prosperity)", "talent_key": "prosperidade", "domain_days": [0, 3, 6], "boss_mat": "Prisma de Raio", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113008.png", "local_specialty": "Cor Lapis", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100026.png", "weekly_boss_mat": "Anel de Boreas", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113012.png", "enemy_key": "nectar"},
    "lan_yan": {"id": "lan_yan", "name": "Lan Yan", "rarity": 4, "element": "Anemo", "weapon": "Catalyst", "talent_book": "Conflito (Conflict)", "talent_key": "conflito", "domain_days": [2, 5, 6], "boss_mat": "Nuvem do Imperador", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113055.png", "local_specialty": "Flor Qingxin", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100030.png", "weekly_boss_mat": "Chama da Criação", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113061.png", "enemy_key": "whistle"},
    "ningguang": {"id": "ningguang", "name": "Ningguang", "rarity": 4, "element": "Geo", "weapon": "Catalyst", "talent_book": "Prosperidade (Prosperity)", "talent_key": "prosperidade", "domain_days": [0, 3, 6], "boss_mat": "Pilar de Basalto", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113010.png", "local_specialty": "Lírio Glaze", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100033.png", "weekly_boss_mat": "Espírito de Boreas", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113010.png", "enemy_key": "fatui_insignia"},
    "qiqi": {"id": "qiqi", "name": "Qiqi", "rarity": 5, "element": "Cryo", "weapon": "Sword", "talent_book": "Prosperidade (Prosperity)", "talent_key": "prosperidade", "domain_days": [0, 3, 6], "boss_mat": "Núcleo de Gelo", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113005.png", "local_specialty": "Sino de Vidro", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100029.png", "weekly_boss_mat": "Cauda de Boreas", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113011.png", "enemy_key": "scroll"},
    "shenhe": {"id": "shenhe", "name": "Shenhe", "rarity": 5, "element": "Cryo", "weapon": "Polearm", "talent_book": "Prosperidade (Prosperity)", "talent_key": "prosperidade", "domain_days": [0, 3, 6], "boss_mat": "Falsa Barbatana do Dragão", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113030.png", "local_specialty": "Flor Qingxin", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100030.png", "weekly_boss_mat": "Momento Derretido", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113026.png", "enemy_key": "nectar"},
    "xiangling": {"id": "xiangling", "name": "Xiangling", "rarity": 4, "element": "Pyro", "weapon": "Polearm", "talent_book": "Diligência (Diligence)", "talent_key": "diligencia", "domain_days": [1, 4, 6], "boss_mat": "Semente de Fogo Eterno", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113009.png", "local_specialty": "Pimenta de Jueyun", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100027.png", "weekly_boss_mat": "Garra de Dvalin", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113003.png", "enemy_key": "slime"},
    "xianyun": {"id": "xianyun", "name": "Xianyun", "rarity": 5, "element": "Anemo", "weapon": "Catalyst", "talent_book": "Ouro (Gold)", "talent_key": "ouro", "domain_days": [2, 5, 6], "boss_mat": "Nuvem do Imperador", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113055.png", "local_specialty": "Jade de Água Clara", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101237.png", "weekly_boss_mat": "Massa Sem Luz", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113054.png", "enemy_key": "scroll"},
    "xiao": {"id": "xiao", "name": "Xiao", "rarity": 5, "element": "Anemo", "weapon": "Polearm", "talent_book": "Prosperidade (Prosperity)", "talent_key": "prosperidade", "domain_days": [0, 3, 6], "boss_mat": "Jade Juvenil", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113017.png", "local_specialty": "Flor Qingxin", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100030.png", "weekly_boss_mat": "Sombra do Guerreiro", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113015.png", "enemy_key": "slime"},
    "xingqiu": {"id": "xingqiu", "name": "Xingqiu", "rarity": 4, "element": "Hydro", "weapon": "Sword", "talent_book": "Ouro (Gold)", "talent_key": "ouro", "domain_days": [2, 5, 6], "boss_mat": "Coração da Água", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113007.png", "local_specialty": "Flor da Seda", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100028.png", "weekly_boss_mat": "Cauda do Vento Oriental", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113004.png", "enemy_key": "mask"},
    "xinyan": {"id": "xinyan", "name": "Xinyan", "rarity": 4, "element": "Pyro", "weapon": "Claymore", "talent_book": "Ouro (Gold)", "talent_key": "ouro", "domain_days": [2, 5, 6], "boss_mat": "Semente de Fogo Eterno", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113009.png", "local_specialty": "Sino de Vidro", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100029.png", "weekly_boss_mat": "Chifre de Monoceros Caeli", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113013.png", "enemy_key": "treasure_hoarder"},
    "yanfei": {"id": "yanfei", "name": "Yanfei", "rarity": 4, "element": "Pyro", "weapon": "Catalyst", "talent_book": "Ouro (Gold)", "talent_key": "ouro", "domain_days": [2, 5, 6], "boss_mat": "Jade Juvenil", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113017.png", "local_specialty": "Jade Noctiluque", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100032.png", "weekly_boss_mat": "Ramo de Jade de Sangue", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113019.png", "enemy_key": "treasure_hoarder"},
    "yaoyao": {"id": "yaoyao", "name": "Yaoyao", "rarity": 4, "element": "Dendro", "weapon": "Polearm", "talent_book": "Diligência (Diligence)", "talent_key": "diligencia", "domain_days": [1, 4, 6], "boss_mat": "Videira Suprimida", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113040.png", "local_specialty": "Pimenta de Jueyun", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100027.png", "weekly_boss_mat": "Māgha", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113031.png", "enemy_key": "slime"},
    "yelan": {"id": "yelan", "name": "Yelan", "rarity": 5, "element": "Hydro", "weapon": "Bow", "talent_book": "Prosperidade (Prosperity)", "talent_key": "prosperidade", "domain_days": [0, 3, 6], "boss_mat": "Engrenagem Rúnica", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113034.png", "local_specialty": "Concha Estelar", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100031.png", "weekly_boss_mat": "Escala Dourada", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113020.png", "enemy_key": "fatui_insignia"},
    "yun_jin": {"id": "yun_jin", "name": "Yun Jin", "rarity": 4, "element": "Geo", "weapon": "Polearm", "talent_book": "Diligência (Diligence)", "talent_key": "diligencia", "domain_days": [1, 4, 6], "boss_mat": "Garra do Lobo Dourado", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113029.png", "local_specialty": "Lírio Glaze", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100033.png", "weekly_boss_mat": "Momento Derretido", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113026.png", "enemy_key": "mask"},
    "yunjin": {"id": "yun_jin", "name": "Yun Jin", "rarity": 4, "element": "Geo", "weapon": "Polearm", "talent_book": "Diligência (Diligence)", "talent_key": "diligencia", "domain_days": [1, 4, 6], "boss_mat": "Garra do Lobo Dourado", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113029.png", "local_specialty": "Lírio Glaze", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100033.png", "weekly_boss_mat": "Momento Derretido", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113026.png", "enemy_key": "mask"},
    "zhongli": {"id": "zhongli", "name": "Zhongli", "rarity": 5, "element": "Geo", "weapon": "Polearm", "talent_book": "Ouro (Gold)", "talent_key": "ouro", "domain_days": [2, 5, 6], "boss_mat": "Pilar de Basalto", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113010.png", "local_specialty": "Cor Lapis", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100026.png", "weekly_boss_mat": "Chifre de Monoceros Caeli", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113013.png", "enemy_key": "slime"},

    # INAZUMA
    "arataki_itto": {"id": "arataki_itto", "name": "Arataki Itto", "rarity": 5, "element": "Geo", "weapon": "Claymore", "talent_book": "Elegância (Elegance)", "talent_key": "elegancia", "domain_days": [1, 4, 6], "boss_mat": "Chifre do Rei Lobo", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113029.png", "local_specialty": "Escaravelho Onikabuto", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101202.png", "weekly_boss_mat": "Cinzas do Coração", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113024.png", "enemy_key": "slime"},
    "itto": {"id": "arataki_itto", "name": "Arataki Itto", "rarity": 5, "element": "Geo", "weapon": "Claymore", "talent_book": "Elegância (Elegance)", "talent_key": "elegancia", "domain_days": [1, 4, 6], "boss_mat": "Chifre do Rei Lobo", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113029.png", "local_specialty": "Escaravelho Onikabuto", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101202.png", "weekly_boss_mat": "Cinzas do Coração", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113024.png", "enemy_key": "slime"},
    "kamisato_ayaka": {"id": "kamisato_ayaka", "name": "Kamisato Ayaka", "rarity": 5, "element": "Cryo", "weapon": "Sword", "talent_book": "Elegância (Elegance)", "talent_key": "elegancia", "domain_days": [1, 4, 6], "boss_mat": "Coração Perpétuo", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113024.png", "local_specialty": "Flor de Cerejeira", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101203.png", "weekly_boss_mat": "Ramo de Jade de Sangue", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113019.png", "enemy_key": "handguard"},
    "ayaka": {"id": "kamisato_ayaka", "name": "Kamisato Ayaka", "rarity": 5, "element": "Cryo", "weapon": "Sword", "talent_book": "Elegância (Elegance)", "talent_key": "elegancia", "domain_days": [1, 4, 6], "boss_mat": "Coração Perpétuo", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113024.png", "local_specialty": "Flor de Cerejeira", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101203.png", "weekly_boss_mat": "Ramo de Jade de Sangue", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113019.png", "enemy_key": "handguard"},
    "kamisato_ayato": {"id": "kamisato_ayato", "name": "Kamisato Ayato", "rarity": 5, "element": "Hydro", "weapon": "Sword", "talent_book": "Elegância (Elegance)", "talent_key": "elegancia", "domain_days": [1, 4, 6], "boss_mat": "Orvalho da Repudiação", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113027.png", "local_specialty": "Flor de Cerejeira", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101203.png", "weekly_boss_mat": "Mudra do General Supremo", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113033.png", "enemy_key": "handguard"},
    "ayato": {"id": "kamisato_ayato", "name": "Kamisato Ayato", "rarity": 5, "element": "Hydro", "weapon": "Sword", "talent_book": "Elegância (Elegance)", "talent_key": "elegancia", "domain_days": [1, 4, 6], "boss_mat": "Orvalho da Repudiação", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113027.png", "local_specialty": "Flor de Cerejeira", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101203.png", "weekly_boss_mat": "Mudra do General Supremo", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113033.png", "enemy_key": "handguard"},
    "chiori": {"id": "chiori", "name": "Chiori", "rarity": 5, "element": "Geo", "weapon": "Sword", "talent_book": "Ordem (Order)", "talent_key": "ordem", "domain_days": [2, 5, 6], "boss_mat": "Mola Mecânica Sobressalente", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113049.png", "local_specialty": "Dendróbio", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101204.png", "weekly_boss_mat": "Fio de Seda Sem Luz", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113053.png", "enemy_key": "specter"},
    "gorou": {"id": "gorou", "name": "Gorou", "rarity": 4, "element": "Geo", "weapon": "Bow", "talent_book": "Luz Celeste (Light)", "talent_key": "luz", "domain_days": [2, 5, 6], "boss_mat": "Coração Perpétuo", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113024.png", "local_specialty": "Pérola de Sango", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101206.png", "weekly_boss_mat": "Momento Derretido", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113026.png", "enemy_key": "specter"},
    "kirara": {"id": "kirara", "name": "Kirara", "rarity": 4, "element": "Dendro", "weapon": "Sword", "talent_book": "Transitoriedade (Transience)", "talent_key": "transitoriedade", "domain_days": [0, 3, 6], "boss_mat": "Anel da Escuridão Sombria", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113045.png", "local_specialty": "Fruto Amakumo", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101207.png", "weekly_boss_mat": "Samambaia Primordial", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113047.png", "enemy_key": "specter"},
    "kujou_sara": {"id": "kujou_sara", "name": "Kujou Sara", "rarity": 4, "element": "Electro", "weapon": "Bow", "talent_book": "Elegância (Elegance)", "talent_key": "elegancia", "domain_days": [1, 4, 6], "boss_mat": "Pérola da Tempestade", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113028.png", "local_specialty": "Dendróbio", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101204.png", "weekly_boss_mat": "Cinzas do Coração", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113024.png", "enemy_key": "mask"},
    "sara": {"id": "kujou_sara", "name": "Kujou Sara", "rarity": 4, "element": "Electro", "weapon": "Bow", "talent_book": "Elegância (Elegance)", "talent_key": "elegancia", "domain_days": [1, 4, 6], "boss_mat": "Pérola da Tempestade", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113028.png", "local_specialty": "Dendróbio", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101204.png", "weekly_boss_mat": "Cinzas do Coração", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113024.png", "enemy_key": "mask"},
    "kuki_shinobu": {"id": "kuki_shinobu", "name": "Kuki Shinobu", "rarity": 4, "element": "Electro", "weapon": "Sword", "talent_book": "Elegância (Elegance)", "talent_key": "elegancia", "domain_days": [1, 4, 6], "boss_mat": "Presa Rúnica", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113036.png", "local_specialty": "Grama Naku", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101208.png", "weekly_boss_mat": "Lágrimas da Deusa Calamidosa", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113032.png", "enemy_key": "specter"},
    "shinobu": {"id": "kuki_shinobu", "name": "Kuki Shinobu", "rarity": 4, "element": "Electro", "weapon": "Sword", "talent_book": "Elegância (Elegance)", "talent_key": "elegancia", "domain_days": [1, 4, 6], "boss_mat": "Presa Rúnica", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113036.png", "local_specialty": "Grama Naku", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101208.png", "weekly_boss_mat": "Lágrimas da Deusa Calamidosa", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113032.png", "enemy_key": "specter"},
    "raiden_shogun": {"id": "raiden_shogun", "name": "Raiden Shogun", "rarity": 5, "element": "Electro", "weapon": "Polearm", "talent_book": "Luz Celeste (Light)", "talent_key": "luz", "domain_days": [2, 5, 6], "boss_mat": "Pérola da Tempestade", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113028.png", "local_specialty": "Fruto Amakumo", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101207.png", "weekly_boss_mat": "Momento Derretido", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113026.png", "enemy_key": "handguard"},
    "sangonomiya_kokomi": {"id": "sangonomiya_kokomi", "name": "Sangonomiya Kokomi", "rarity": 5, "element": "Hydro", "weapon": "Catalyst", "talent_book": "Transitoriedade (Transience)", "talent_key": "transitoriedade", "domain_days": [0, 3, 6], "boss_mat": "Orvalho da Repudiação", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113027.png", "local_specialty": "Pérola de Sango", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101206.png", "weekly_boss_mat": "Borboleta Infernal", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113025.png", "enemy_key": "specter"},
    "kokomi": {"id": "sangonomiya_kokomi", "name": "Sangonomiya Kokomi", "rarity": 5, "element": "Hydro", "weapon": "Catalyst", "talent_book": "Transitoriedade (Transience)", "talent_key": "transitoriedade", "domain_days": [0, 3, 6], "boss_mat": "Orvalho da Repudiação", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113027.png", "local_specialty": "Pérola de Sango", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101206.png", "weekly_boss_mat": "Borboleta Infernal", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113025.png", "enemy_key": "specter"},
    "sayu": {"id": "sayu", "name": "Sayu", "rarity": 4, "element": "Anemo", "weapon": "Claymore", "talent_book": "Luz Celeste (Light)", "talent_key": "luz", "domain_days": [2, 5, 6], "boss_mat": "Núcleo de Marionete", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113023.png", "local_specialty": "Medula de Cristal", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101205.png", "weekly_boss_mat": "Escala Dourada", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113020.png", "enemy_key": "nectar"},
    "shikanoin_heizou": {"id": "shikanoin_heizou", "name": "Shikanoin Heizou", "rarity": 4, "element": "Anemo", "weapon": "Catalyst", "talent_book": "Transitoriedade (Transience)", "talent_key": "transitoriedade", "domain_days": [0, 3, 6], "boss_mat": "Presa Rúnica", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113036.png", "local_specialty": "Escaravelho Onikabuto", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101202.png", "weekly_boss_mat": "Signo de Mudra", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113033.png", "enemy_key": "treasure_hoarder"},
    "heizou": {"id": "shikanoin_heizou", "name": "Shikanoin Heizou", "rarity": 4, "element": "Anemo", "weapon": "Catalyst", "talent_book": "Transitoriedade (Transience)", "talent_key": "transitoriedade", "domain_days": [0, 3, 6], "boss_mat": "Presa Rúnica", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113036.png", "local_specialty": "Escaravelho Onikabuto", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101202.png", "weekly_boss_mat": "Signo de Mudra", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113033.png", "enemy_key": "treasure_hoarder"},
    "thoma": {"id": "thoma", "name": "Thoma", "rarity": 4, "element": "Pyro", "weapon": "Polearm", "talent_book": "Transitoriedade (Transience)", "talent_key": "transitoriedade", "domain_days": [0, 3, 6], "boss_mat": "Pérola da Tempestade", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113028.png", "local_specialty": "Cogumelo Fluorescente", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101209.png", "weekly_boss_mat": "Borboleta Infernal", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113025.png", "enemy_key": "treasure_hoarder"},
    "yae_miko": {"id": "yae_miko", "name": "Yae Miko", "rarity": 5, "element": "Electro", "weapon": "Catalyst", "talent_book": "Luz Celeste (Light)", "talent_key": "luz", "domain_days": [2, 5, 6], "boss_mat": "Falsa Barbatana do Dragão", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113030.png", "local_specialty": "Ganoderma Marinho", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101201.png", "weekly_boss_mat": "Mudra do General Supremo", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113033.png", "enemy_key": "handguard"},
    "yoimiya": {"id": "yoimiya", "name": "Yoimiya", "rarity": 5, "element": "Pyro", "weapon": "Bow", "talent_book": "Transitoriedade (Transience)", "talent_key": "transitoriedade", "domain_days": [0, 3, 6], "boss_mat": "Pérola da Tempestade", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113028.png", "local_specialty": "Grama Naku", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101208.png", "weekly_boss_mat": "Coroa do Senhor dos Dragões", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113018.png", "enemy_key": "scroll"},

    # SUMERU
    "alhaitham": {"id": "alhaitham", "name": "Alhaitham", "rarity": 5, "element": "Dendro", "weapon": "Sword", "talent_book": "Engenhosidade (Ingenuity)", "talent_key": "engenhosidade", "domain_days": [1, 4, 6], "boss_mat": "Presa Rúnica", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113036.png", "local_specialty": "Crisântemo de Areia", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101221.png", "weekly_boss_mat": "Espelho de Mushin", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113043.png", "enemy_key": "red_silk"},
    "candace": {"id": "candace", "name": "Candace", "rarity": 4, "element": "Hydro", "weapon": "Polearm", "talent_book": "Admoestação (Admonition)", "talent_key": "admoestacao", "domain_days": [0, 3, 6], "boss_mat": "Tetraedro Guia de Luz", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113039.png", "local_specialty": "Fruto Henna", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101222.png", "weekly_boss_mat": "Lágrimas da Deusa Calamidosa", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113032.png", "enemy_key": "red_silk"},
    "collei": {"id": "collei", "name": "Collei", "rarity": 4, "element": "Dendro", "weapon": "Bow", "talent_book": "Práxis (Praxis)", "talent_key": "praxis", "domain_days": [2, 5, 6], "boss_mat": "Bico de Gancho Majestoso", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113037.png", "local_specialty": "Cogumelo Rukkha", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101214.png", "weekly_boss_mat": "Lágrimas da Deusa Calamidosa", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113032.png", "enemy_key": "arrowhead"},
    "cyno": {"id": "cyno", "name": "Cyno", "rarity": 5, "element": "Electro", "weapon": "Polearm", "talent_book": "Admoestação (Admonition)", "talent_key": "admoestacao", "domain_days": [0, 3, 6], "boss_mat": "Miragem Trovão", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113038.png", "local_specialty": "Escaravelho", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101221.png", "weekly_boss_mat": "Māgha", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113031.png", "enemy_key": "scroll"},
    "dehya": {"id": "dehya", "name": "Dehya", "rarity": 5, "element": "Pyro", "weapon": "Claymore", "talent_book": "Práxis (Praxis)", "talent_key": "praxis", "domain_days": [2, 5, 6], "boss_mat": "Tetraedro Guia de Luz", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113039.png", "local_specialty": "Crisântemo de Areia", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101221.png", "weekly_boss_mat": "Fios de Marionete", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113041.png", "enemy_key": "red_silk"},
    "dori": {"id": "dori", "name": "Dori", "rarity": 4, "element": "Electro", "weapon": "Claymore", "talent_book": "Engenhosidade (Ingenuity)", "talent_key": "engenhosidade", "domain_days": [1, 4, 6], "boss_mat": "Miragem Trovão", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113038.png", "local_specialty": "Lótus Kalpalata", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101217.png", "weekly_boss_mat": "Ramo de Jade de Sangue", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113019.png", "enemy_key": "red_silk"},
    "faruzan": {"id": "faruzan", "name": "Faruzan", "rarity": 4, "element": "Anemo", "weapon": "Bow", "talent_book": "Admoestação (Admonition)", "talent_key": "admoestacao", "domain_days": [0, 3, 6], "boss_mat": "Tetraedro Guia de Luz", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113039.png", "local_specialty": "Fruto Henna", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101222.png", "weekly_boss_mat": "Fios de Marionete", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113041.png", "enemy_key": "red_silk"},
    "kaveh": {"id": "kaveh", "name": "Kaveh", "rarity": 4, "element": "Dendro", "weapon": "Claymore", "talent_book": "Engenhosidade (Ingenuity)", "talent_key": "engenhosidade", "domain_days": [1, 4, 6], "boss_mat": "Anel da Escuridão Sombria", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113045.png", "local_specialty": "Flor de Mourning", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101224.png", "weekly_boss_mat": "Samambaia Primordial", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113047.png", "enemy_key": "fungal_spores"},
    "layla": {"id": "layla", "name": "Layla", "rarity": 4, "element": "Cryo", "weapon": "Sword", "talent_book": "Engenhosidade (Ingenuity)", "talent_key": "engenhosidade", "domain_days": [1, 4, 6], "boss_mat": "Bico de Gancho Majestoso", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113037.png", "local_specialty": "Flor Lunar Nilotpala", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101215.png", "weekly_boss_mat": "Espelho de Mushin", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113043.png", "enemy_key": "scroll"},
    "nahida": {"id": "nahida", "name": "Nahida", "rarity": 5, "element": "Dendro", "weapon": "Catalyst", "talent_book": "Engenhosidade (Ingenuity)", "talent_key": "engenhosidade", "domain_days": [1, 4, 6], "boss_mat": "Videira Suprimida", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113040.png", "local_specialty": "Lótus Kalpalata", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101217.png", "weekly_boss_mat": "Fios de Marionete", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113041.png", "enemy_key": "fungal_spores"},
    "nilou": {"id": "nilou", "name": "Nilou", "rarity": 5, "element": "Hydro", "weapon": "Sword", "talent_book": "Práxis (Praxis)", "talent_key": "praxis", "domain_days": [2, 5, 6], "boss_mat": "Falso Estame", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113035.png", "local_specialty": "Flor de Padisarah", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101218.png", "weekly_boss_mat": "Lágrimas da Deusa Calamidosa", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113032.png", "enemy_key": "fungal_spores"},
    "sethos": {"id": "sethos", "name": "Sethos", "rarity": 4, "element": "Electro", "weapon": "Bow", "talent_book": "Práxis (Praxis)", "talent_key": "praxis", "domain_days": [2, 5, 6], "boss_mat": "Nuvem do Imperador", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113055.png", "local_specialty": "Crisântemo de Areia", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101221.png", "weekly_boss_mat": "Vela Apagada", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113058.png", "enemy_key": "red_silk"},
    "tighnari": {"id": "tighnari", "name": "Tighnari", "rarity": 5, "element": "Dendro", "weapon": "Bow", "talent_book": "Admoestação (Admonition)", "talent_key": "admoestacao", "domain_days": [0, 3, 6], "boss_mat": "Bico de Gancho Majestoso", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113037.png", "local_specialty": "Flor Lunar Nilotpala", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101215.png", "weekly_boss_mat": "Signo de Mudra", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113033.png", "enemy_key": "fungal_spores"},
    "wanderer": {"id": "wanderer", "name": "Wanderer", "rarity": 5, "element": "Anemo", "weapon": "Catalyst", "talent_book": "Práxis (Praxis)", "talent_key": "praxis", "domain_days": [2, 5, 6], "boss_mat": "Tetraedro Guia de Luz", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113039.png", "local_specialty": "Cogumelo Rukkha", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101214.png", "weekly_boss_mat": "Fios de Marionete", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113041.png", "enemy_key": "handguard"},
    "andarilho": {"id": "wanderer", "name": "Wanderer", "rarity": 5, "element": "Anemo", "weapon": "Catalyst", "talent_book": "Práxis (Praxis)", "talent_key": "praxis", "domain_days": [2, 5, 6], "boss_mat": "Tetraedro Guia de Luz", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113039.png", "local_specialty": "Cogumelo Rukkha", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101214.png", "weekly_boss_mat": "Fios de Marionete", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113041.png", "enemy_key": "handguard"},

    # FONTAINE
    "arlecchino": {"id": "arlecchino", "name": "Arlecchino", "rarity": 5, "element": "Pyro", "weapon": "Polearm", "talent_book": "Ordem (Order)", "talent_key": "ordem", "domain_days": [2, 5, 6], "boss_mat": "Fragmento da Melodia Dourada", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113056.png", "local_specialty": "Rosa Arco-íris", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101231.png", "weekly_boss_mat": "Vela Apagada", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113058.png", "enemy_key": "fatui_insignia"},
    "charlotte": {"id": "charlotte", "name": "Charlotte", "rarity": 4, "element": "Cryo", "weapon": "Catalyst", "talent_book": "Justiça (Justice)", "talent_key": "justica", "domain_days": [1, 4, 6], "boss_mat": "Mola Mecânica Sobressalente", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113049.png", "local_specialty": "Beryl Conch", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101230.png", "weekly_boss_mat": "Massa Sem Luz", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113054.png", "enemy_key": "gear"},
    "chevreuse": {"id": "chevreuse", "name": "Chevreuse", "rarity": 4, "element": "Pyro", "weapon": "Polearm", "talent_book": "Ordem (Order)", "talent_key": "ordem", "domain_days": [2, 5, 6], "boss_mat": "Chifre de Fontemer", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113050.png", "local_specialty": "Lírio Lumidouce", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101232.png", "weekly_boss_mat": "Massa Sem Luz", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113054.png", "enemy_key": "gear"},
    "clorinde": {"id": "clorinde", "name": "Clorinde", "rarity": 5, "element": "Electro", "weapon": "Sword", "talent_book": "Justiça (Justice)", "talent_key": "justica", "domain_days": [1, 4, 6], "boss_mat": "Chifre de Fontemer", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113050.png", "local_specialty": "Lírio Lumidouce", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101232.png", "weekly_boss_mat": "Vela Apagada", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113058.png", "enemy_key": "gear"},
    "emilie": {"id": "emilie", "name": "Emilie", "rarity": 5, "element": "Dendro", "weapon": "Polearm", "talent_book": "Ordem (Order)", "talent_key": "ordem", "domain_days": [2, 5, 6], "boss_mat": "Fragmento da Melodia Dourada", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113056.png", "local_specialty": "Lírio de Lakelight", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101235.png", "weekly_boss_mat": "Vela Apagada", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113058.png", "enemy_key": "gear"},
    "freminet": {"id": "freminet", "name": "Freminet", "rarity": 4, "element": "Cryo", "weapon": "Claymore", "talent_book": "Justiça (Justice)", "talent_key": "justica", "domain_days": [1, 4, 6], "boss_mat": "Mola Mecânica Sobressalente", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113049.png", "local_specialty": "Flor Romaritime", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101234.png", "weekly_boss_mat": "Samambaia Primordial", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113047.png", "enemy_key": "transoceanic"},
    "furina": {"id": "furina", "name": "Furina", "rarity": 5, "element": "Hydro", "weapon": "Sword", "talent_book": "Justiça (Justice)", "talent_key": "justica", "domain_days": [1, 4, 6], "boss_mat": "Gota d'Água Não Envelhecida", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113051.png", "local_specialty": "Lírio de Lakelight", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101235.png", "weekly_boss_mat": "Massa Sem Luz", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113054.png", "enemy_key": "nectar"},
    "lynette": {"id": "lynette", "name": "Lynette", "rarity": 4, "element": "Anemo", "weapon": "Sword", "talent_book": "Ordem (Order)", "talent_key": "ordem", "domain_days": [2, 5, 6], "boss_mat": "Mola Mecânica Sobressalente", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113049.png", "local_specialty": "Flor Romaritime", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101234.png", "weekly_boss_mat": "Vela Apagada", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113058.png", "enemy_key": "gear"},
    "lyney": {"id": "lyney", "name": "Lyney", "rarity": 5, "element": "Pyro", "weapon": "Bow", "talent_book": "Equidade (Equity)", "talent_key": "equidade", "domain_days": [0, 3, 6], "boss_mat": "Chifre do Imperador do Fogo", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113048.png", "local_specialty": "Rosa Arco-íris", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101231.png", "weekly_boss_mat": "Samambaia Primordial", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113047.png", "enemy_key": "fatui_insignia"},
    "navia": {"id": "navia", "name": "Navia", "rarity": 5, "element": "Geo", "weapon": "Claymore", "talent_book": "Equidade (Equity)", "talent_key": "equidade", "domain_days": [0, 3, 6], "boss_mat": "Mola Mecânica Sobressalente", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113049.png", "local_specialty": "Gotas de Orvalho", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101233.png", "weekly_boss_mat": "Fio de Seda Sem Luz", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113053.png", "enemy_key": "transoceanic"},
    "neuvillette": {"id": "neuvillette", "name": "Neuvillette", "rarity": 5, "element": "Hydro", "weapon": "Catalyst", "talent_book": "Equidade (Equity)", "talent_key": "equidade", "domain_days": [0, 3, 6], "boss_mat": "Chifre de Fontemer", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113050.png", "local_specialty": "Estrela Lumitoile", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101236.png", "weekly_boss_mat": "Massa Sem Luz", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113054.png", "enemy_key": "gear"},
    "sigewinne": {"id": "sigewinne", "name": "Sigewinne", "rarity": 5, "element": "Hydro", "weapon": "Bow", "talent_book": "Equidade (Equity)", "talent_key": "equidade", "domain_days": [0, 3, 6], "boss_mat": "Gota d'Água Não Envelhecida", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113051.png", "local_specialty": "Flor Romaritime", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101234.png", "weekly_boss_mat": "Massa Sem Luz", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113054.png", "enemy_key": "transoceanic"},
    "wriothesley": {"id": "wriothesley", "name": "Wriothesley", "rarity": 5, "element": "Cryo", "weapon": "Catalyst", "talent_book": "Ordem (Order)", "talent_key": "ordem", "domain_days": [2, 5, 6], "boss_mat": "Dispositivo de Gravidade", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113052.png", "local_specialty": "Unidade de Subdetecção", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101238.png", "weekly_boss_mat": "Samambaia Primordial", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113047.png", "enemy_key": "gear"},

    # NATLAN
    "chasca": {"id": "chasca", "name": "Chasca", "rarity": 5, "element": "Anemo", "weapon": "Bow", "talent_book": "Ignição (Kindling)", "talent_key": "ignicao", "domain_days": [1, 4, 6], "boss_mat": "Pluma da Tempestade Natlan", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113063.png", "local_specialty": "Flor da Chama Voadora", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101244.png", "weekly_boss_mat": "Olho da Destruição", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113060.png", "enemy_key": "saurian_fang"},
    "citlali": {"id": "citlali", "name": "Citlali", "rarity": 5, "element": "Cryo", "weapon": "Catalyst", "talent_book": "Conflito (Conflict)", "talent_key": "conflito", "domain_days": [2, 5, 6], "boss_mat": "Gelo da Noite Estelar", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113065.png", "local_specialty": "Orquídea Celestial", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101246.png", "weekly_boss_mat": "Chama da Criação", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113061.png", "enemy_key": "saurian_fang"},
    "iansan": {"id": "iansan", "name": "Iansan", "rarity": 4, "element": "Electro", "weapon": "Polearm", "talent_book": "Ignição (Kindling)", "talent_key": "ignicao", "domain_days": [1, 4, 6], "boss_mat": "Coração do Vulcão Sagrado", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113064.png", "local_specialty": "Crisântemo Reluzente", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101243.png", "weekly_boss_mat": "Chama da Criação", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113061.png", "enemy_key": "whistle"},
    "kachina": {"id": "kachina", "name": "Kachina", "rarity": 4, "element": "Geo", "weapon": "Polearm", "talent_book": "Disputa (Contention)", "talent_key": "disputa", "domain_days": [0, 3, 6], "boss_mat": "Marca do Tirano de Lava", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113061.png", "local_specialty": "Quenepa Berry", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101240.png", "weekly_boss_mat": "Olho da Destruição", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113060.png", "enemy_key": "whistle"},
    "kinich": {"id": "kinich", "name": "Kinich", "rarity": 5, "element": "Dendro", "weapon": "Claymore", "talent_book": "Ignição (Kindling)", "talent_key": "ignicao", "domain_days": [1, 4, 6], "boss_mat": "Garras da Sombra Insaciável", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113059.png", "local_specialty": "Cogumelo Sauriano", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101242.png", "weekly_boss_mat": "Olho da Destruição", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113060.png", "enemy_key": "saurian_fang"},
    "mavuika": {"id": "mavuika", "name": "Mavuika", "rarity": 5, "element": "Pyro", "weapon": "Claymore", "talent_book": "Disputa (Contention)", "talent_key": "disputa", "domain_days": [0, 3, 6], "boss_mat": "Coração do Vulcão Sagrado", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113064.png", "local_specialty": "Chama Solar de Natlan", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101245.png", "weekly_boss_mat": "Chama da Criação", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113061.png", "enemy_key": "whistle"},
    "mualani": {"id": "mualani", "name": "Mualani", "rarity": 5, "element": "Hydro", "weapon": "Catalyst", "talent_book": "Disputa (Contention)", "talent_key": "disputa", "domain_days": [0, 3, 6], "boss_mat": "Marca do Tirano de Lava", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113061.png", "local_specialty": "Fruta de Espray", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101241.png", "weekly_boss_mat": "Massa Sem Luz", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113054.png", "enemy_key": "whistle"},
    "ororon": {"id": "ororon", "name": "Ororon", "rarity": 4, "element": "Electro", "weapon": "Bow", "talent_book": "Conflito (Conflict)", "talent_key": "conflito", "domain_days": [2, 5, 6], "boss_mat": "Garras da Sombra Insaciável", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113059.png", "local_specialty": "Flor da Chama Voadora", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101244.png", "weekly_boss_mat": "Chama da Criação", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113061.png", "enemy_key": "saurian_fang"},
    "xilonen": {"id": "xilonen", "name": "Xilonen", "rarity": 5, "element": "Geo", "weapon": "Sword", "talent_book": "Disputa (Contention)", "talent_key": "disputa", "domain_days": [0, 3, 6], "boss_mat": "Núcleo de Cristal Vulcânico", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113062.png", "local_specialty": "Crisântemo Reluzente", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_101243.png", "weekly_boss_mat": "Vela Apagada", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113058.png", "enemy_key": "whistle"},

    # SNEZHNAYA
    "tartaglia": {"id": "tartaglia", "name": "Tartaglia", "rarity": 5, "element": "Hydro", "weapon": "Bow", "talent_book": "Liberdade (Freedom)", "talent_key": "liberdade", "domain_days": [0, 3, 6], "boss_mat": "Coração da Água", "boss_icon": "https://enka.network/ui/UI_ItemIcon_113007.png", "local_specialty": "Concha Estelar", "specialty_icon": "https://enka.network/ui/UI_ItemIcon_100031.png", "weekly_boss_mat": "Fragmento do Rei do Mal", "weekly_icon": "https://enka.network/ui/UI_ItemIcon_113014.png", "enemy_key": "fatui_insignia"}
}

HSR_CALYX_MATERIALS = {
    "destruction_nanook": {
        "path": "Destruction",
        "t2": "Lâmina Despedaçada (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110111.png",
        "t3": "Lâmina Sem Vida (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110112.png",
        "t4": "Destruidora do Mundo (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110113.png",
        "t5": "Destruidora do Mundo (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110113.png"
    },
    "destruction_borisin": {
        "path": "Destruction",
        "t2": "Dente de Borisin (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110251.png",
        "t3": "Dente de Lupotoxina (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110252.png",
        "t4": "Mandíbula Voraz Lunífera (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110253.png",
        "t5": "Mandíbula Voraz Lunífera (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110253.png"
    },
    "hunt_arrow": {
        "path": "Hunt",
        "t2": "Flecha do Caçador (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110121.png",
        "t3": "Flecha do Matador de Demônios (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110122.png",
        "t4": "Flecha do Perseguidor de Estrelas (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110123.png",
        "t5": "Flecha do Perseguidor de Estrelas (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110123.png"
    },
    "hunt_meteor": {
        "path": "Hunt",
        "t2": "Ponta de Flecha Meteorítica (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110261.png",
        "t3": "Ponta de Flecha do Destino (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110262.png",
        "t4": "Flecha Estilhaçadora do Céu (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110263.png",
        "t5": "Flecha Estilhaçadora do Céu (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110263.png"
    },
    "erudition_key": {
        "path": "Erudition",
        "t2": "Chave da Inspiração (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110131.png",
        "t3": "Chave do Conhecimento (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110132.png",
        "t4": "Chave da Sabedoria (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110133.png",
        "t5": "Chave da Sabedoria (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110133.png"
    },
    "erudition_sketch": {
        "path": "Erudition",
        "t2": "Rascunho Áspero (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110271.png",
        "t3": "Linhas Dinâmicas (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110272.png",
        "t4": "Obra-prima Exquista (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110273.png",
        "t5": "Obra-prima Exquista (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110273.png"
    },
    "harmony_melody": {
        "path": "Harmony",
        "t2": "Melodia Harmoniosa (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110141.png",
        "t3": "Hino Ancestral (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110142.png",
        "t4": "Sinfonia Celestial (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110143.png",
        "t5": "Sinfonia Celestial (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110143.png"
    },
    "harmony_firm_note": {
        "path": "Harmony",
        "t2": "Nota Firme (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110281.png",
        "t3": "Seção Celestial (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110282.png",
        "t4": "Movimento Celestial (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110283.png",
        "t5": "Movimento Celestial (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110283.png"
    },
    "nihility_obsidian": {
        "path": "Nihility",
        "t2": "Obsidiana do Terror (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110151.png",
        "t3": "Obsidiana da Desolação (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110152.png",
        "t4": "Obsidiana da Obsessão (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110153.png",
        "t5": "Obsidiana da Obsessão (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110153.png"
    },
    "nihility_fiery_spirit": {
        "path": "Nihility",
        "t2": "Espírito Ardente (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110291.png",
        "t3": "Essência de Fogo Estelar (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110292.png",
        "t4": "Incinerador Celestial (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110293.png",
        "t5": "Incinerador Celestial (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110293.png"
    },
    "preservation_endurance": {
        "path": "Preservation",
        "t2": "Resistência de Bronze (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110161.png",
        "t3": "Juramento de Aço Congelado (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110162.png",
        "t4": "Salvaguarda de Âmbar (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110163.png",
        "t5": "Salvaguarda de Âmbar (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110163.png"
    },
    "preservation_amber": {
        "path": "Preservation",
        "t2": "Âmbar Cintilante (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110301.png",
        "t3": "Cristal da Proteção (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110302.png",
        "t4": "Escudo Sagrado Inquebrável (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110303.png",
        "t5": "Escudo Sagrado Inquebrável (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110303.png"
    },
    "abundance_seed": {
        "path": "Abundance",
        "t2": "Semente da Abundância (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110171.png",
        "t3": "Broto da Vida (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110172.png",
        "t4": "Flor da Eternidade (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110173.png",
        "t5": "Flor da Eternidade (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110173.png"
    },
    "abundance_alien": {
        "path": "Abundance",
        "t2": "Pedaço de Alienação (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110311.png",
        "t3": "Fruto da Transmutação (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110312.png",
        "t4": "Orbe Divino da Nutrição (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110313.png",
        "t5": "Orbe Divino da Nutrição (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110313.png"
    },
    "remembrance": {
        "path": "Remembrance",
        "t2": "Cristal da Memória (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110321.png",
        "t3": "Fragmento de Reminiscência (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110322.png",
        "t4": "Espelho da Eternidade (4★)", "t4_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110323.png",
        "t5": "Espelho da Eternidade (5★)", "t5_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110323.png"
    }
}

HSR_MOB_DROPS = {
    "antimatter": {
        "name": "Legião Antimatéria",
        "t1": "Núcleo Extinto (1★)", "t1_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/111001.png",
        "t2": "Núcleo Vaga-fogo (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/111002.png",
        "t3": "Núcleo Ondulante (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/111003.png"
    },
    "silvermane": {
        "name": "Guardas de Crina de Prata",
        "t1": "Insígnia dos Guardas de Crina de Prata (1★)", "t1_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/111011.png",
        "t2": "Insígnia dos Guardas de Crina de Prata (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/111012.png",
        "t3": "Medalha dos Guardas de Crina de Prata (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/111013.png"
    },
    "robot": {
        "name": "Autômatos de Belobog",
        "t1": "Pedaço de Ferro Antigo (1★)", "t1_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/112001.png",
        "t2": "Eixo do Motor Antigo (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/112002.png",
        "t3": "Motor Antigo (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/112003.png"
    },
    "fragmentum": {
        "name": "Monstros do Fragmentum",
        "t1": "Dente da Extinção (1★)", "t1_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/112011.png",
        "t2": "Mandíbula Dilaceradora (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/112012.png",
        "t3": "Presa da Morte (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/112013.png"
    },
    "mara": {
        "name": "Atingidos por Mara",
        "t1": "Broto Imortal (1★)", "t1_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/113001.png",
        "t2": "Flor Étera Imortal (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/113002.png",
        "t3": "Ramo Glorioso Imortal (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/113003.png"
    },
    "artificer": {
        "name": "Comissão de Artesanato",
        "t1": "Componente Mecânico Artificial (1★)", "t1_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/113011.png",
        "t2": "Roda Cilíndrica Mecânica (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/113012.png",
        "t3": "Coração Mecânico do Caos (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/113013.png"
    },
    "dreamjolt": {
        "name": "Trupe do Pesadelo",
        "t1": "Fragmento de Pensamento (1★)", "t1_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/114001.png",
        "t2": "Fragmento de Impressão (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/114002.png",
        "t3": "Fragmento de Desejo (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/114003.png"
    },
    "memoryzone": {
        "name": "Zona das Memórias",
        "t1": "Dente da Besta do Pesadelo (1★)", "t1_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/114011.png",
        "t2": "Mandíbula do Caçador das Sombras (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/114012.png",
        "t3": "Presa da Morte Noturna (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/114013.png"
    },
    "borisin": {
        "name": "Matilha Borisin",
        "t1": "Dente Espinhado Borisin (1★)", "t1_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/114021.png",
        "t2": "Garra do Predador Borisin (2★)", "t2_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/114022.png",
        "t3": "Presa do Alfa Borisin (3★)", "t3_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/114023.png"
    }
}

HSR_STAGNANT_SHADOW = {
    "primitive_lightning": {"name": "Relâmpago Primitivo", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110401.png"},
    "raging_fire": {"name": "Chama Estrondosa", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110402.png"},
    "iron_wolf_tooth": {"name": "Dente Quebrado do Lobisomem de Ferro", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110403.png"},
    "luminous_jelly": {"name": "Gelatina Luminescente", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110404.png"},
    "wind_storm_eye": {"name": "Olho de Tempestade de Vento", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110405.png"},
    "frozen_spine": {"name": "Espinho de Glória Gelada", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110406.png"},
    "dead_wood": {"name": "Madeira Morta de Fogo", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110415.png"},
    "monkey_coffin": {"name": "Prego do Caixão do Macaco", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110417.png"},
    "suppression_rod": {"name": "Vara de Supressão", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110418.png"},
    "fissure_ice": {"name": "Gelo Gelado da Fissura", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110419.png"},
    "space_ashes": {"name": "Ectoplasma de Cinzas Espaciais", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110420.png"},
    "cold_flame_spine": {"name": "Espinho de Fogo Frio", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110421.png"},
    "suppression_statute": {"name": "Estatuto Supressor da Lei", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110422.png"},
    "celestial_ectoplasm": {"name": "Ectoplasma Celestial", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110423.png"},
    "scorch_heart": {"name": "Coração Flamejante", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110424.png"},
    "puppet_piece": {"name": "Pedaço de Fantoche Quebrado", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110425.png"},
    "purifying_fire": {"name": "Bálsamo do Purgatório", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110426.png"},
    "lightning_crown": {"name": "Coroa de Chamas de Cinzas", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110427.png"},
    "night_wind_claw": {"name": "Garra de Fera do Vento Noturno", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110428.png"},
    "aevum_flux": {"name": "Fluxo do Destino Dimensional", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110429.png"}
}

HSR_ECHO_OF_WAR = {
    "queen_lament": {"name": "Lamento da Rainha da Destruição", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110501.png"},
    "end_road": {"name": "Caminho Final do Destruidor", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110502.png"},
    "infinite_body": {"name": "Arrependimento do Falso Corpo Infinito", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110503.png"},
    "stellar_fissure": {"name": "Fenda da Destruição Estelar", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110504.png"},
    "dream_monster": {"name": "Pecados Passados do Monstro dos Sonhos", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110505.png"},
    "destiny_serpent": {"name": "Lamento da Serpente do Destino", "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110506.png"}
}

ZZZ_SKILL_CHIPS = {
    "physical": {
        "element": "Físico",
        "t2": "Chip Básico de Físico (2★)", "t2_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png",
        "t3": "Chip Avançado de Físico (3★)", "t3_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png",
        "t4": "Chip Especializado de Físico (4★)", "t4_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png"
    },
    "fire": {
        "element": "Fogo",
        "t2": "Chip Básico de Fogo (2★)", "t2_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png",
        "t3": "Chip Avançado de Fogo (3★)", "t3_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png",
        "t4": "Chip Especializado de Fogo (4★)", "t4_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png"
    },
    "ice": {
        "element": "Gelo",
        "t2": "Chip Básico de Gelo (2★)", "t2_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png",
        "t3": "Chip Avançado de Gelo (3★)", "t3_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png",
        "t4": "Chip Especializado de Gelo (4★)", "t4_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png"
    },
    "electric": {
        "element": "Elétrico",
        "t2": "Chip Básico de Elétrico (2★)", "t2_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png",
        "t3": "Chip Avançado de Elétrico (3★)", "t3_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png",
        "t4": "Chip Especializado de Elétrico (4★)", "t4_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png"
    },
    "ether": {
        "element": "Éter",
        "t2": "Chip Básico de Éter (2★)", "t2_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png",
        "t3": "Chip Avançado de Éter (3★)", "t3_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png",
        "t4": "Chip Especializado de Éter (4★)", "t4_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png"
    }
}

ZZZ_PROMOTION_SEALS = {
    "attack": {
        "specialty": "Ataque",
        "t2": "Selo de Ataque Básico (2★)", "t2_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
        "t3": "Selo de Ataque Avançado (3★)", "t3_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
        "t4": "Selo de Ataque Pioneiro (4★)", "t4_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png"
    },
    "stun": {
        "specialty": "Atordoamento",
        "t2": "Selo de Atordoamento Básico (2★)", "t2_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
        "t3": "Selo de Atordoamento Avançado (3★)", "t3_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
        "t4": "Selo de Atordoamento Pioneiro (4★)", "t4_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png"
    },
    "anomaly": {
        "specialty": "Anomalia",
        "t2": "Selo de Anomalia Básico (2★)", "t2_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
        "t3": "Selo de Anomalia Avançado (3★)", "t3_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
        "t4": "Selo de Anomalia Pioneiro (4★)", "t4_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png"
    },
    "support": {
        "specialty": "Suporte",
        "t2": "Selo de Suporte Básico (2★)", "t2_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
        "t3": "Selo de Suporte Avançado (3★)", "t3_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
        "t4": "Selo de Suporte Pioneiro (4★)", "t4_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png"
    },
    "defense": {
        "specialty": "Defesa",
        "t2": "Selo de Defesa Básico (2★)", "t2_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
        "t3": "Selo de Defesa Avançado (3★)", "t3_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
        "t4": "Selo de Defesa Pioneiro (4★)", "t4_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png"
    }
}

ZZZ_MOB_DROPS = {
    "ethereal": {
        "name": "Etereais",
        "t1": "Sinalizador Básico (1★)", "t1_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4f1444b51f52e8e0ad4a8dc13432b04f.png",
        "t2": "Sinalizador Avançado (2★)", "t2_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4f1444b51f52e8e0ad4a8dc13432b04f.png",
        "t3": "Sinalizador Especializado (3★)", "t3_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4f1444b51f52e8e0ad4a8dc13432b04f.png"
    },
    "rebel": {
        "name": "Rebeldes e Facções",
        "t1": "Componente de Rebelde (1★)", "t1_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4f1444b51f52e8e0ad4a8dc13432b04f.png",
        "t2": "Engrenagem Reforçada (2★)", "t2_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4f1444b51f52e8e0ad4a8dc13432b04f.png",
        "t3": "Microcontrolador de Precisão (3★)", "t3_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4f1444b51f52e8e0ad4a8dc13432b04f.png"
    },
    "corrupted": {
        "name": "Corrompidos e Mutantes",
        "t1": "Fluido Etéreo Diluído (1★)", "t1_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4f1444b51f52e8e0ad4a8dc13432b04f.png",
        "t2": "Fluido Etéreo Concentrado (2★)", "t2_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4f1444b51f52e8e0ad4a8dc13432b04f.png",
        "t3": "Cristal Etéreo Puro (3★)", "t3_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4f1444b51f52e8e0ad4a8dc13432b04f.png"
    }
}

ZZZ_EXPERT_CHALLENGE = {
    "victoria": {"name": "Insígnia de Serviço Victoria", "icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4fde02b5f3a4c790dcbef6c74cb4fabf.png"},
    "public_security": {"name": "Emblema da Segurança Pública Criminal", "icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4fde02b5f3a4c790dcbef6c74cb4fabf.png"},
    "calydon": {"name": "Medalha dos Filhos de Calydon", "icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4fde02b5f3a4c790dcbef6c74cb4fabf.png"},
    "section6": {"name": "Emblema de Maestria da Seção 6", "icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4fde02b5f3a4c790dcbef6c74cb4fabf.png"},
    "belobog": {"name": "Insígnia Belobog de Construção Pesada", "icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4fde02b5f3a4c790dcbef6c74cb4fabf.png"},
    "cunning_hares": {"name": "Moeda Especial das Lebres Astutas", "icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4fde02b5f3a4c790dcbef6c74cb4fabf.png"},
    "defense_force": {"name": "Medalha do Batalhão de Defesa", "icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4fde02b5f3a4c790dcbef6c74cb4fabf.png"},
    "new_eridu": {"name": "Medalha de Honra de Nova Eridu", "icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4fde02b5f3a4c790dcbef6c74cb4fabf.png"},
    "obsidian": {"name": "Insígnia da Divisão Obsidian", "icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4fde02b5f3a4c790dcbef6c74cb4fabf.png"}
}

ZZZ_NOTORIOUS_HUNT = {
    "silent_death": {"name": "Testemunho da Morte Silenciosa", "icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/2196659ee41fc22d1533519c53644f37.png"},
    "corrupted_heart": {"name": "Coração do Tirano da Fissura", "icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/2196659ee41fc22d1533519c53644f37.png"},
    "butcher_ferocity": {"name": "Ferocidade Carniceira", "icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/2196659ee41fc22d1533519c53644f37.png"},
    "puppet_core": {"name": "Núcleo Corrompido da Marionete", "icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/2196659ee41fc22d1533519c53644f37.png"},
    "pompey_bite": {"name": "Mordida Feroz de Pompey", "icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/2196659ee41fc22d1533519c53644f37.png"}
}

HSR_CHARACTERS_SEED = {
    "acheron": {
        "id": "acheron",
        "name": "Acheron",
        "rarity": 5,
        "element": "Lightning",
        "path": "Nihility",
        "calyx_key": "nihility_fiery_spirit",
        "stagnant_key": "suppression_statute",
        "echo_key": "dream_monster",
        "enemy_key": "dreamjolt",
        "hoyolab_id": "1308",
        "icon": "icon/character/1308.png"
    },
    "firefly": {
        "id": "firefly",
        "name": "Firefly",
        "rarity": 5,
        "element": "Fire",
        "path": "Destruction",
        "calyx_key": "destruction_borisin",
        "stagnant_key": "raging_fire",
        "echo_key": "dream_monster",
        "enemy_key": "memoryzone",
        "hoyolab_id": "1310",
        "icon": "icon/character/1310.png"
    },
    "feixiao": {
        "id": "feixiao",
        "name": "Feixiao",
        "rarity": 5,
        "element": "Wind",
        "path": "Hunt",
        "calyx_key": "hunt_meteor",
        "stagnant_key": "night_wind_claw",
        "echo_key": "destiny_serpent",
        "enemy_key": "borisin",
        "hoyolab_id": "1220",
        "icon": "icon/character/1220.png"
    },
    "robin": {
        "id": "robin",
        "name": "Robin",
        "rarity": 5,
        "element": "Physical",
        "path": "Harmony",
        "calyx_key": "harmony_firm_note",
        "stagnant_key": "celestial_ectoplasm",
        "echo_key": "dream_monster",
        "enemy_key": "dreamjolt",
        "hoyolab_id": "1309",
        "icon": "icon/character/1309.png"
    },
    "ruan_mei": {
        "id": "ruan_mei",
        "name": "Ruan Mei",
        "rarity": 5,
        "element": "Ice",
        "path": "Harmony",
        "calyx_key": "harmony_melody",
        "stagnant_key": "fissure_ice",
        "echo_key": "stellar_fissure",
        "enemy_key": "artificer",
        "hoyolab_id": "1303",
        "icon": "icon/character/1303.png"
    },
    "aventurine": {
        "id": "aventurine",
        "name": "Aventurine",
        "rarity": 5,
        "element": "Imaginary",
        "path": "Preservation",
        "calyx_key": "preservation_amber",
        "stagnant_key": "suppression_statute",
        "echo_key": "dream_monster",
        "enemy_key": "memoryzone",
        "hoyolab_id": "1304",
        "icon": "icon/character/1304.png"
    },
    "black_swan": {
        "id": "black_swan",
        "name": "Black Swan",
        "rarity": 5,
        "element": "Wind",
        "path": "Nihility",
        "calyx_key": "nihility_fiery_spirit",
        "stagnant_key": "space_ashes",
        "echo_key": "stellar_fissure",
        "enemy_key": "dreamjolt",
        "hoyolab_id": "1307",
        "icon": "icon/character/1307.png"
    },
    "sparkle": {
        "id": "sparkle",
        "name": "Sparkle",
        "rarity": 5,
        "element": "Quantum",
        "path": "Harmony",
        "calyx_key": "harmony_melody",
        "stagnant_key": "cold_flame_spine",
        "echo_key": "stellar_fissure",
        "enemy_key": "dreamjolt",
        "hoyolab_id": "1306",
        "icon": "icon/character/1306.png"
    },
    "sunday": {
        "id": "sunday",
        "name": "Sunday",
        "rarity": 5,
        "element": "Imaginary",
        "path": "Harmony",
        "calyx_key": "harmony_firm_note",
        "stagnant_key": "puppet_piece",
        "echo_key": "destiny_serpent",
        "enemy_key": "dreamjolt",
        "hoyolab_id": "1313",
        "icon": "icon/character/1313.png"
    },
    "fugue": {
        "id": "fugue",
        "name": "Fugue",
        "rarity": 5,
        "element": "Fire",
        "path": "Nihility",
        "calyx_key": "nihility_fiery_spirit",
        "stagnant_key": "purifying_fire",
        "echo_key": "destiny_serpent",
        "enemy_key": "borisin",
        "hoyolab_id": "1225",
        "icon": "icon/character/1225.png"
    },
    "castorice": {
        "id": "castorice",
        "name": "Castorice",
        "rarity": 5,
        "element": "Quantum",
        "path": "Remembrance",
        "calyx_key": "remembrance",
        "stagnant_key": "aevum_flux",
        "echo_key": "destiny_serpent",
        "enemy_key": "memoryzone",
        "hoyolab_id": "1401",
        "icon": "icon/character/1401.png"
    },
    "boothill": {
        "id": "boothill",
        "name": "Boothill",
        "rarity": 5,
        "element": "Physical",
        "path": "Hunt",
        "calyx_key": "hunt_meteor",
        "stagnant_key": "suppression_statute",
        "echo_key": "dream_monster",
        "enemy_key": "fragmentum",
        "hoyolab_id": "1315",
        "icon": "icon/character/1315.png"
    },
    "dr_ratio": {
        "id": "dr_ratio",
        "name": "Dr. Ratio",
        "rarity": 5,
        "element": "Imaginary",
        "path": "Hunt",
        "calyx_key": "hunt_arrow",
        "stagnant_key": "suppression_rod",
        "echo_key": "stellar_fissure",
        "enemy_key": "artificer",
        "hoyolab_id": "1305",
        "icon": "icon/character/1305.png"
    },
    "topaz": {
        "id": "topaz",
        "name": "Topaz & Dinheirinho",
        "rarity": 5,
        "element": "Fire",
        "path": "Hunt",
        "calyx_key": "hunt_arrow",
        "stagnant_key": "dead_wood",
        "echo_key": "infinite_body",
        "enemy_key": "silvermane",
        "hoyolab_id": "1112",
        "icon": "icon/character/1112.png"
    },
    "jingliu": {
        "id": "jingliu",
        "name": "Jingliu",
        "rarity": 5,
        "element": "Ice",
        "path": "Destruction",
        "calyx_key": "destruction_nanook",
        "stagnant_key": "fissure_ice",
        "echo_key": "infinite_body",
        "enemy_key": "mara",
        "hoyolab_id": "1212",
        "icon": "icon/character/1212.png"
    },
    "dan_heng_il": {
        "id": "dan_heng_il",
        "name": "Dan Heng • Embebidor Lunae",
        "rarity": 5,
        "element": "Imaginary",
        "path": "Destruction",
        "calyx_key": "destruction_nanook",
        "stagnant_key": "suppression_rod",
        "echo_key": "infinite_body",
        "enemy_key": "artificer",
        "hoyolab_id": "1213",
        "icon": "icon/character/1213.png"
    },
    "blade": {
        "id": "blade",
        "name": "Blade",
        "rarity": 5,
        "element": "Wind",
        "path": "Destruction",
        "calyx_key": "destruction_nanook",
        "stagnant_key": "dead_wood",
        "echo_key": "infinite_body",
        "enemy_key": "mara",
        "hoyolab_id": "1205",
        "icon": "icon/character/1205.png"
    },
    "kafka": {
        "id": "kafka",
        "name": "Kafka",
        "rarity": 5,
        "element": "Lightning",
        "path": "Nihility",
        "calyx_key": "nihility_obsidian",
        "stagnant_key": "primitive_lightning",
        "echo_key": "infinite_body",
        "enemy_key": "silvermane",
        "hoyolab_id": "1005",
        "icon": "icon/character/1005.png"
    },
    "silver_wolf": {
        "id": "silver_wolf",
        "name": "Loba Prateada (Silver Wolf)",
        "rarity": 5,
        "element": "Quantum",
        "path": "Nihility",
        "calyx_key": "nihility_obsidian",
        "stagnant_key": "fissure_ice",
        "echo_key": "end_road",
        "enemy_key": "robot",
        "hoyolab_id": "1006",
        "icon": "icon/character/1006.png"
    },
    "seele": {
        "id": "seele",
        "name": "Seele",
        "rarity": 5,
        "element": "Quantum",
        "path": "Hunt",
        "calyx_key": "hunt_arrow",
        "stagnant_key": "fissure_ice",
        "echo_key": "end_road",
        "enemy_key": "fragmentum",
        "hoyolab_id": "1102",
        "icon": "icon/character/1102.png"
    },
    "jing_yuan": {
        "id": "jing_yuan",
        "name": "Jing Yuan",
        "rarity": 5,
        "element": "Lightning",
        "path": "Erudition",
        "calyx_key": "erudition_key",
        "stagnant_key": "primitive_lightning",
        "echo_key": "end_road",
        "enemy_key": "mara",
        "hoyolab_id": "1204",
        "icon": "icon/character/1204.png"
    },
    "luocha": {
        "id": "luocha",
        "name": "Luocha",
        "rarity": 5,
        "element": "Imaginary",
        "path": "Abundance",
        "calyx_key": "abundance_seed",
        "stagnant_key": "suppression_rod",
        "echo_key": "end_road",
        "enemy_key": "artificer",
        "hoyolab_id": "1203",
        "icon": "icon/character/1203.png"
    },
    "huohuo": {
        "id": "huohuo",
        "name": "Huohuo",
        "rarity": 5,
        "element": "Wind",
        "path": "Abundance",
        "calyx_key": "abundance_seed",
        "stagnant_key": "dead_wood",
        "echo_key": "infinite_body",
        "enemy_key": "mara",
        "hoyolab_id": "1217",
        "icon": "icon/character/1217.png"
    },
    "lingsha": {
        "id": "lingsha",
        "name": "Lingsha",
        "rarity": 5,
        "element": "Fire",
        "path": "Abundance",
        "calyx_key": "abundance_alien",
        "stagnant_key": "raging_fire",
        "echo_key": "destiny_serpent",
        "enemy_key": "borisin",
        "hoyolab_id": "1222",
        "icon": "icon/character/1222.png"
    },
    "jiaoqiu": {
        "id": "jiaoqiu",
        "name": "Jiaoqiu",
        "rarity": 5,
        "element": "Fire",
        "path": "Nihility",
        "calyx_key": "nihility_fiery_spirit",
        "stagnant_key": "raging_fire",
        "echo_key": "destiny_serpent",
        "enemy_key": "borisin",
        "hoyolab_id": "1218",
        "icon": "icon/character/1218.png"
    },
    "bronya": {
        "id": "bronya",
        "name": "Bronya",
        "rarity": 5,
        "element": "Wind",
        "path": "Harmony",
        "calyx_key": "harmony_melody",
        "stagnant_key": "wind_storm_eye",
        "echo_key": "end_road",
        "enemy_key": "silvermane",
        "hoyolab_id": "1101",
        "icon": "icon/character/1101.png"
    },
    "tingyun": {
        "id": "tingyun",
        "name": "Tingyun",
        "rarity": 4,
        "element": "Lightning",
        "path": "Harmony",
        "calyx_key": "harmony_melody",
        "stagnant_key": "primitive_lightning",
        "echo_key": "end_road",
        "enemy_key": "mara",
        "hoyolab_id": "1202",
        "icon": "icon/character/1202.png"
    },
    "clara": {
        "id": "clara",
        "name": "Clara",
        "rarity": 5,
        "element": "Physical",
        "path": "Destruction",
        "calyx_key": "destruction_nanook",
        "stagnant_key": "iron_wolf_tooth",
        "echo_key": "end_road",
        "enemy_key": "robot",
        "hoyolab_id": "1107",
        "icon": "icon/character/1107.png"
    },
    "gepard": {
        "id": "gepard",
        "name": "Gepard",
        "rarity": 5,
        "element": "Ice",
        "path": "Preservation",
        "calyx_key": "preservation_endurance",
        "stagnant_key": "frozen_spine",
        "echo_key": "end_road",
        "enemy_key": "silvermane",
        "hoyolab_id": "1104",
        "icon": "icon/character/1104.png"
    },
    "bailu": {
        "id": "bailu",
        "name": "Bailu",
        "rarity": 5,
        "element": "Lightning",
        "path": "Abundance",
        "calyx_key": "abundance_seed",
        "stagnant_key": "primitive_lightning",
        "echo_key": "end_road",
        "enemy_key": "mara",
        "hoyolab_id": "1211",
        "icon": "icon/character/1211.png"
    },
    "himeko": {
        "id": "himeko",
        "name": "Himeko",
        "rarity": 5,
        "element": "Fire",
        "path": "Erudition",
        "calyx_key": "erudition_key",
        "stagnant_key": "raging_fire",
        "echo_key": "end_road",
        "enemy_key": "antimatter",
        "hoyolab_id": "1003",
        "icon": "icon/character/1003.png"
    },
    "welt": {
        "id": "welt",
        "name": "Welt",
        "rarity": 5,
        "element": "Imaginary",
        "path": "Nihility",
        "calyx_key": "nihility_obsidian",
        "stagnant_key": "suppression_rod",
        "echo_key": "end_road",
        "enemy_key": "antimatter",
        "hoyolab_id": "1004",
        "icon": "icon/character/1004.png"
    }
}

ZZZ_CHARACTERS_SEED = {
    "miyabi": {
        "id": "miyabi",
        "name": "Hoshimi Miyabi",
        "rarity": 5,
        "element": "ice",
        "specialty": "anomaly",
        "expert_key": "section6",
        "weekly_key": "butcher_ferocity",
        "enemy_key": "ethereal"
    },
    "harumasa": {
        "id": "harumasa",
        "name": "Asaba Harumasa",
        "rarity": 5,
        "element": "electric",
        "specialty": "attack",
        "expert_key": "section6",
        "weekly_key": "butcher_ferocity",
        "enemy_key": "ethereal"
    },
    "astra": {
        "id": "astra",
        "name": "Astra Yao",
        "rarity": 5,
        "element": "ether",
        "specialty": "support",
        "expert_key": "new_eridu",
        "weekly_key": "puppet_core",
        "enemy_key": "ethereal"
    },
    "ellen": {
        "id": "ellen",
        "name": "Ellen Joe",
        "rarity": 5,
        "element": "ice",
        "specialty": "attack",
        "expert_key": "victoria",
        "weekly_key": "silent_death",
        "enemy_key": "ethereal"
    },
    "zhu_yuan": {
        "id": "zhu_yuan",
        "name": "Zhu Yuan",
        "rarity": 5,
        "element": "ether",
        "specialty": "attack",
        "expert_key": "public_security",
        "weekly_key": "silent_death",
        "enemy_key": "ethereal"
    },
    "jane": {
        "id": "jane",
        "name": "Jane Doe",
        "rarity": 5,
        "element": "physical",
        "specialty": "anomaly",
        "expert_key": "public_security",
        "weekly_key": "corrupted_heart",
        "enemy_key": "rebel"
    },
    "caesar": {
        "id": "caesar",
        "name": "Caesar King",
        "rarity": 5,
        "element": "physical",
        "specialty": "defense",
        "expert_key": "calydon",
        "weekly_key": "corrupted_heart",
        "enemy_key": "rebel"
    },
    "burnice": {
        "id": "burnice",
        "name": "Burnice White",
        "rarity": 5,
        "element": "fire",
        "specialty": "anomaly",
        "expert_key": "calydon",
        "weekly_key": "corrupted_heart",
        "enemy_key": "rebel"
    },
    "qingyi": {
        "id": "qingyi",
        "name": "Qingyi",
        "rarity": 5,
        "element": "electric",
        "specialty": "stun",
        "expert_key": "public_security",
        "weekly_key": "silent_death",
        "enemy_key": "ethereal"
    },
    "yanagi": {
        "id": "yanagi",
        "name": "Tsukishiro Yanagi",
        "rarity": 5,
        "element": "electric",
        "specialty": "anomaly",
        "expert_key": "section6",
        "weekly_key": "butcher_ferocity",
        "enemy_key": "ethereal"
    },
    "lighter": {
        "id": "lighter",
        "name": "Lighter",
        "rarity": 5,
        "element": "fire",
        "specialty": "stun",
        "expert_key": "calydon",
        "weekly_key": "pompey_bite",
        "enemy_key": "rebel"
    },
    "lycaon": {
        "id": "lycaon",
        "name": "Von Lycaon",
        "rarity": 5,
        "element": "ice",
        "specialty": "stun",
        "expert_key": "victoria",
        "weekly_key": "silent_death",
        "enemy_key": "ethereal"
    },
    "rina": {
        "id": "rina",
        "name": "Alexandrina",
        "rarity": 5,
        "element": "electric",
        "specialty": "support",
        "expert_key": "victoria",
        "weekly_key": "silent_death",
        "enemy_key": "ethereal"
    },
    "soldier_11": {
        "id": "soldier_11",
        "name": "Soldier 11",
        "rarity": 5,
        "element": "fire",
        "specialty": "attack",
        "expert_key": "defense_force",
        "weekly_key": "silent_death",
        "enemy_key": "rebel"
    },
    "koleda": {
        "id": "koleda",
        "name": "Koleda Belobog",
        "rarity": 5,
        "element": "fire",
        "specialty": "stun",
        "expert_key": "belobog",
        "weekly_key": "silent_death",
        "enemy_key": "rebel"
    },
    "grace": {
        "id": "grace",
        "name": "Grace Howard",
        "rarity": 5,
        "element": "electric",
        "specialty": "anomaly",
        "expert_key": "belobog",
        "weekly_key": "silent_death",
        "enemy_key": "rebel"
    },
    "nekomata": {
        "id": "nekomata",
        "name": "Nekomata",
        "rarity": 5,
        "element": "physical",
        "specialty": "attack",
        "expert_key": "cunning_hares",
        "weekly_key": "silent_death",
        "enemy_key": "ethereal"
    },
    "nicole": {
        "id": "nicole",
        "name": "Nicole Demara",
        "rarity": 4,
        "element": "ether",
        "specialty": "support",
        "expert_key": "cunning_hares",
        "weekly_key": "silent_death",
        "enemy_key": "ethereal"
    },
    "anby": {
        "id": "anby",
        "name": "Anby Demara",
        "rarity": 4,
        "element": "electric",
        "specialty": "stun",
        "expert_key": "cunning_hares",
        "weekly_key": "silent_death",
        "enemy_key": "ethereal"
    },
    "billy": {
        "id": "billy",
        "name": "Billy Kid",
        "rarity": 4,
        "element": "physical",
        "specialty": "attack",
        "expert_key": "cunning_hares",
        "weekly_key": "silent_death",
        "enemy_key": "ethereal"
    },
    "corin": {
        "id": "corin",
        "name": "Corin Wickes",
        "rarity": 4,
        "element": "physical",
        "specialty": "attack",
        "expert_key": "victoria",
        "weekly_key": "silent_death",
        "enemy_key": "ethereal"
    },
    "seth": {
        "id": "seth",
        "name": "Seth Lowell",
        "rarity": 4,
        "element": "electric",
        "specialty": "defense",
        "expert_key": "public_security",
        "weekly_key": "corrupted_heart",
        "enemy_key": "ethereal"
    },
    "piper": {
        "id": "piper",
        "name": "Piper Wheel",
        "rarity": 4,
        "element": "physical",
        "specialty": "anomaly",
        "expert_key": "calydon",
        "weekly_key": "corrupted_heart",
        "enemy_key": "rebel"
    },
    "lucy": {
        "id": "lucy",
        "name": "Lucy",
        "rarity": 4,
        "element": "fire",
        "specialty": "support",
        "expert_key": "calydon",
        "weekly_key": "corrupted_heart",
        "enemy_key": "rebel"
    },
    "soukaku": {
        "id": "soukaku",
        "name": "Soukaku",
        "rarity": 4,
        "element": "ice",
        "specialty": "support",
        "expert_key": "section6",
        "weekly_key": "silent_death",
        "enemy_key": "ethereal"
    }
}

class StaticDataManager:
    def __init__(self):
        self.data_dir = STATIC_DATA_DIR
        self._ensure_cache_dir()
        self._cache = {
            "genshin": {},
            "hsr": {},
            "zzz": {},
            "schedules": {}
        }
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
            "zzz": {"characters": ZZZ_CHARACTERS_SEED}
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
        
        found_item = None
        # 1. Busca direta por chave
        if query in chars_dict:
            found_item = dict(chars_dict[query])
        else:
            # 2. Busca por matching flexível de nome
            for k, v in chars_dict.items():
                name_clean = v.get("name", "").lower().replace(" ", "_").replace("•", "").replace("'", "")
                if query == name_clean or query in name_clean or name_clean in query or k == query:
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
                    if query == name_clean or query in name_clean or name_clean in query or k == query:
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
                if "anemo" in el: t_key = "poemas"
                elif "geo" in el: t_key = "ouro"
                elif "electro" in el: t_key = "luz"
                elif "dendro" in el: t_key = "engenhosidade"
                elif "hydro" in el: t_key = "justica"
                elif "pyro" in el: t_key = "disputa"
                else: t_key = "resistencia"

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
                if "pyro" in el: boss_name, boss_icon = "Semente de Fogo Eterno", "https://enka.network/ui/UI_ItemIcon_113009.png"
                elif "hydro" in el: boss_name, boss_icon = "Gota d'Água Não Envelhecida", "https://enka.network/ui/UI_ItemIcon_113051.png"
                elif "anemo" in el: boss_name, boss_icon = "Semente de Furacão", "https://enka.network/ui/UI_ItemIcon_113006.png"
                elif "electro" in el: boss_name, boss_icon = "Pérola da Tempestade", "https://enka.network/ui/UI_ItemIcon_113028.png"
                elif "dendro" in el: boss_name, boss_icon = "Videira Suprimida", "https://enka.network/ui/UI_ItemIcon_113040.png"
                elif "cryo" in el: boss_name, boss_icon = "Núcleo de Gelo", "https://enka.network/ui/UI_ItemIcon_113005.png"
                elif "geo" in el: boss_name, boss_icon = "Pilar de Basalto", "https://enka.network/ui/UI_ItemIcon_113010.png"
                else: boss_name, boss_icon = "Gota d'Água Não Envelhecida", "https://enka.network/ui/UI_ItemIcon_113051.png"
            enriched["boss_mat_name"] = boss_name
            enriched["boss_mat_icon"] = boss_icon

            # 3. Especialidade Local
            spec_name = item.get("local_specialty")
            spec_icon = item.get("specialty_icon")
            if not spec_name or spec_name in ["Especialidade Local", ""]:
                el = str(item.get("element", "")).lower()
                if "hydro" in el: spec_name, spec_icon = "Lírio de Lakelight", "https://enka.network/ui/UI_ItemIcon_101235.png"
                elif "anemo" in el: spec_name, spec_icon = "Dente-de-Leão", "https://enka.network/ui/UI_ItemIcon_100021.png"
                elif "geo" in el: spec_name, spec_icon = "Cor Lapis", "https://enka.network/ui/UI_ItemIcon_100026.png"
                elif "electro" in el: spec_name, spec_icon = "Fruto Amakumo", "https://enka.network/ui/UI_ItemIcon_101207.png"
                elif "dendro" in el: spec_name, spec_icon = "Lótus Kalpalata", "https://enka.network/ui/UI_ItemIcon_101217.png"
                elif "pyro" in el: spec_name, spec_icon = "Rosa Arco-íris", "https://enka.network/ui/UI_ItemIcon_101231.png"
                else: spec_name, spec_icon = "Flor Qingxin", "https://enka.network/ui/UI_ItemIcon_100030.png"
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
                if "anemo" in el or "hydro" in el: e_key = "nectar"
                elif "geo" in el or "cryo" in el: e_key = "slime"
                elif "electro" in el: e_key = "handguard"
                elif "dendro" in el: e_key = "fungal_spores"
                elif "pyro" in el: e_key = "treasure_hoarder"
                else: e_key = "slime"

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
            stag = HSR_STAGNANT_SHADOW.get(stagnant_key, {"name": item.get("stagnant_shadow_mat", "Material de Sombra Estagnada"), "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110401.png"})
            enriched["boss_mat_name"] = stag["name"]
            enriched["boss_mat_icon"] = stag["icon"]

            # 3. Eco da Guerra (Chefe Semanal)
            echo_key = item.get("echo_key")
            if not echo_key:
                echo_key = "dream_monster"
            echo = HSR_ECHO_OF_WAR.get(echo_key, {"name": item.get("echo_of_war_mat", "Material de Eco da Guerra"), "icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110505.png"})
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
            exp_data = ZZZ_EXPERT_CHALLENGE.get(exp_key, {"name": item.get("core_skill_mat", "Emblema de Especialista"), "icon": "https://act-webstatic.hoyoverse.com/game_record/genshin/equip/UI_ItemIcon_113009.png"})
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
            wk_data = ZZZ_NOTORIOUS_HUNT.get(wk_key, {"name": item.get("weekly_boss_mat", "Material de Caça Notória"), "icon": "https://act-webstatic.hoyoverse.com/game_record/genshin/equip/UI_ItemIcon_113028.png"})
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
            enriched["crown_icon"] = "https://act-webstatic.hoyoverse.com/game_record/genshin/equip/UI_ItemIcon_104319.png"

        return enriched

    def get_weapon_profile(self, game_id: str, weapon_name: str) -> Dict[str, Any]:
        """
        Retorna o perfil completo de ascensão da arma com os 4 tiers de materiais de domínio
        e drops de monstros com ícones CDN oficiais.
        """
        g = game_id.lower().strip()
        w_clean = weapon_name.lower().strip()

        if g == "genshin":
            w_mat_key = "dandelion_gladiator" # Padrão Favonius
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
            elif any(k in w_clean for k in ["talismã de ferro", "iron talisman", "luz lunar de xiphos", "madeira da floresta"]):
                w_mat_key = "iron_talisman"
                mob_key = "fungal_spores"
            elif any(k in w_clean for k in ["jardim do oásis", "oasis garden", "luz das folhas cortadas", "espada de madeira"]):
                w_mat_key = "oasis_garden"
                mob_key = "red_silk"
            elif any(k in w_clean for k in ["sol escaldante", "scorching sun", "báculo das areias escarlates", "agulha de ferro"]):
                w_mat_key = "scorching_sun"
                mob_key = "fungal_spores"
            elif any(k in w_clean for k in ["acorde antigo", "chord", "tomo do fluxo eterno", "fluxo eterno"]):
                w_mat_key = "chord"
                mob_key = "gear"
            elif any(k in w_clean for k in ["gota d'água", "dewdrop", "esplendor das águas silenciosas", "águas silenciosas"]):
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
                "w_mat_tier2_name": w_data["t2"], "w_mat_tier2_icon": w_data["t2_icon"],
                "w_mat_tier3_name": w_data["t3"], "w_mat_tier3_icon": w_data["t3_icon"],
                "w_mat_tier4_name": w_data["t4"], "w_mat_tier4_icon": w_data["t4_icon"],
                "w_mat_tier5_name": w_data["t5"], "w_mat_tier5_icon": w_data["t5_icon"],
                "enemy_tier1_name": mob_data["t1"], "enemy_tier1_icon": mob_data["t1_icon"],
                "enemy_tier2_name": mob_data["t2"], "enemy_tier2_icon": mob_data["t2_icon"],
                "enemy_tier3_name": mob_data["t3"], "enemy_tier3_icon": mob_data["t3_icon"]
            }

        elif g == "hsr":
            # Identificação inteligente do Caminho do Cone de Luz
            calyx_key = "destruction_nanook"
            mob_key = "silvermane"
            
            if any(k in w_clean for k in ["passing shore", "along the passing shore", "fogo", "olhos da presa", "paciência", "solidão", "chuva", "tutorial", "destino"]):
                calyx_key = "nihility_fiery_spirit"
                mob_key = "dreamjolt"
            elif any(k in w_clean for k in ["flaming", "whereabouts", "queda de um aeon", "sob o céu azul", "coração secreto", "mutação", "topo do mundo"]):
                calyx_key = "destruction_borisin"
                mob_key = "memoryzone"
            elif any(k in w_clean for k in ["perseguição", "cruzeiro", "espada estelar", "sono", "jogo de espadas", "silêncio"]):
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
                "w_mat_tier2_name": calyx["t2"], "w_mat_tier2_icon": calyx["t2_icon"],
                "w_mat_tier3_name": calyx["t3"], "w_mat_tier3_icon": calyx["t3_icon"],
                "w_mat_tier4_name": calyx["t4"], "w_mat_tier4_icon": calyx["t4_icon"],
                "w_mat_tier5_name": calyx["t5"], "w_mat_tier5_icon": calyx["t5_icon"],
                "enemy_tier1_name": mob["t1"], "enemy_tier1_icon": mob["t1_icon"],
                "enemy_tier2_name": mob["t2"], "enemy_tier2_icon": mob["t2_icon"],
                "enemy_tier3_name": mob["t3"], "enemy_tier3_icon": mob["t3_icon"],
                "ore_name": "Éter Refinado",
                "ore_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/102.png",
                "currency_name": "Créditos",
                "currency_icon": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/2.png"
            }

        elif g == "zzz":
            # Identificação inteligente do W-Engine por Especialidade
            spec_key = "attack"
            mob_key = "ethereal"

            if any(k in w_clean for k in ["deep sea", "visitor", "visita", "enxofre", "canhão", "estrela", "lâmina", "fúria"]):
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
                "w_mat_tier2_name": seal["t2"].replace("Selo de", "Componente de W-Engine"), "w_mat_tier2_icon": seal["t2_icon"],
                "w_mat_tier3_name": seal["t3"].replace("Selo de", "Componente de W-Engine"), "w_mat_tier3_icon": seal["t3_icon"],
                "w_mat_tier4_name": seal["t4"].replace("Selo de", "Componente de W-Engine"), "w_mat_tier4_icon": seal["t4_icon"],
                "w_mat_tier5_name": "Componente Mestre de W-Engine (5★)", "w_mat_tier5_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
                "enemy_tier1_name": mob["t1"], "enemy_tier1_icon": mob["t1_icon"],
                "enemy_tier2_name": mob["t2"], "enemy_tier2_icon": mob["t2_icon"],
                "enemy_tier3_name": mob["t3"], "enemy_tier3_icon": mob["t3_icon"],
                "ore_name": "Fonte de Alimentação de W-Engine",
                "ore_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4f1444b51f52e8e0ad4a8dc13432b04f.png",
                "currency_name": "Dennys",
                "currency_icon": "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4fde02b5f3a4c790dcbef6c74cb4fabf.png"
            }

        return {}

    def _is_character_farm_open_today(self, game_id: str, char_data: Dict[str, Any], weekday: Optional[int] = None) -> bool:
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
        is_sunday = (weekday == 6)

        if g == "genshin":
            open_talents = []
            open_weapons = []
            open_chars = []

            domains_data = self._cache["genshin"].get("domains", GENSHIN_DOMAINS_SCHEDULE)
            
            for nation, data in domains_data.get("talent_books", {}).items():
                dom_name = data.get("domain", nation.title())
                for sch_key, sch in data.get("schedules", {}).items():
                    if is_sunday or weekday in sch.get("days", []):
                        open_talents.append({
                            "nation": nation.title(),
                            "domain": dom_name,
                            "material": sch["name"],
                            "characters": sch.get("characters", [])
                        })
                        open_chars.extend(sch.get("characters", []))

            for nation, data in domains_data.get("weapon_materials", {}).items():
                dom_name = data.get("domain", nation.title())
                for sch_key, sch in data.get("schedules", {}).items():
                    if is_sunday or weekday in sch.get("days", []):
                        open_weapons.append({
                            "nation": nation.title(),
                            "domain": dom_name,
                            "material": sch["name"]
                        })

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
                "farmable_characters": sorted(list(set(open_chars)))
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
                "farmable_characters": sorted(list(set(char_names)))
            }

        return {
            "game_id": g,
            "weekday": weekday,
            "weekday_name": weekday_name,
            "is_all_open_sunday": True,
            "open_talents": [],
            "open_weapons": [],
            "farmable_characters": []
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
            "https://fastly.jsdelivr.net/gh/Mar-7th/StarRailRes@master/index_min/pt/characters.json"
        ]
        fetched_data, source_url = fetch_json_with_retry(endpoints)
        source_used = "StarRailRes (GitHub/CDN)" if fetched_data else None

        current_chars = dict(self._cache["hsr"].get("characters", HSR_CHARACTERS_SEED))
        
        if fetched_data and isinstance(fetched_data, dict):
            path_map = {
                'Warlock': 'Nihility', 'Warrior': 'Destruction', 'Rogue': 'Hunt',
                'Mage': 'Erudition', 'Shaman': 'Harmony', 'Knight': 'Preservation',
                'Priest': 'Abundance', 'Memory': 'Remembrance'
            }
            elem_map = {
                'Thunder': 'Lightning'
            }
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
                    "calyx_tier2_icon": existing.get("calyx_tier2_icon", "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110.png"),
                    "calyx_tier3_name": existing.get("calyx_tier3_name", "Dinâmica de Rastro (3★)"),
                    "calyx_tier3_icon": existing.get("calyx_tier3_icon", "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110.png"),
                    "calyx_tier4_name": existing.get("calyx_tier4_name", "Conhecimento de Rastro (4★)"),
                    "calyx_tier4_icon": existing.get("calyx_tier4_icon", "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110.png"),
                    "stagnant_shadow_mat": existing.get("stagnant_shadow_mat", "Sombra Estagnada"),
                    "boss_icon": existing.get("boss_icon", "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/201.png"),
                    "echo_of_war_mat": existing.get("echo_of_war_mat", "Eco da Guerra"),
                    "weekly_icon": existing.get("weekly_icon", "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/3.png"),
                    "schedule_type": "Daily",
                    "hoyolab_id": str(cid),
                    "icon": cinfo.get("icon", "")
                }

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
            "updated_at": datetime.now().isoformat()
        }

    def _sync_genshin(self) -> Dict[str, Any]:
        """Sincroniza manifestos de Genshin Impact consumindo EnkaNetwork Datamines, theBowja/genshin-db e integrando ao catálogo com fallback resiliente."""
        chars_endpoints = [
            "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/characters.json",
            "https://cdn.jsdelivr.net/gh/EnkaNetwork/API-docs@master/store/characters.json"
        ]
        loc_endpoints = [
            "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/loc.json",
            "https://cdn.jsdelivr.net/gh/EnkaNetwork/API-docs@master/store/loc.json"
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
                'Ice': 'Cryo', 'Fire': 'Pyro', 'Electric': 'Electro', 
                'Water': 'Hydro', 'Wind': 'Anemo', 'Rock': 'Geo', 'Grass': 'Dendro'
            }
            weap_map = {
                'WEAPON_SWORD_ONE_HAND': 'Sword', 'WEAPON_CLAYMORE': 'Claymore', 
                'WEAPON_POLE': 'Polearm', 'WEAPON_BOW': 'Bow', 'WEAPON_CATALYST': 'Catalyst'
            }
            loc_pt = fetched_loc.get('pt', {})
            loc_en = fetched_loc.get('en', {})

            for cid, cinfo in fetched_chars.items():
                name_hash = str(cinfo.get('NameTextMapHash', ''))
                name = loc_pt.get(name_hash) or loc_en.get(name_hash, '')
                if not name or "{" in name:
                    continue
                
                safe_id = name.lower().replace(" ", "_").replace("•", "").replace("'", "")
                rarity = 5 if cinfo.get('QualityType') == 'QUALITY_ORANGE' else 4
                elem = elem_map.get(cinfo.get('Element'), cinfo.get('Element', ''))
                weap = weap_map.get(cinfo.get('WeaponType'), cinfo.get('WeaponType', ''))
                
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
                    "side_icon": cinfo.get("SideIconName", "")
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
            "updated_at": datetime.now().isoformat()
        }

    def _sync_zzz(self) -> Dict[str, Any]:
        """Sincroniza manifestos de Zenless Zone Zero consumindo Prydwen e datamines abertos."""
        current_chars = dict(self._cache["zzz"].get("characters", ZZZ_CHARACTERS_SEED))
        source_used = None
        
        try:
            from scraper_zzz import PrydwenZZZScraper
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
                            "url": ag.get("url", "")
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
            "updated_at": datetime.now().isoformat()
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
                "offline_ready": True
            },
            "hsr": {
                "characters": len(self._cache["hsr"].get("characters", {})),
                "offline_ready": True
            },
            "zzz": {
                "characters": len(self._cache["zzz"].get("characters", {})),
                "offline_ready": True
            },
            "last_check": datetime.now().isoformat()
        }

# Instância Singleton global
static_data_manager = StaticDataManager()
