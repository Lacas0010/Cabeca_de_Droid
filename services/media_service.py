import os
import json
import urllib.parse
from typing import Dict, Any
from core.config import get_resource_path

def get_raw_url(url_str: str) -> str:
    """Extrai a URL original subjacente caso a string já esteja envelopada pelo proxy interno."""
    if not url_str:
        return ""
    url_s = str(url_str)
    while "/api/proxy_image?url=" in url_s:
        raw = url_s.split("/api/proxy_image?url=")[-1]
        url_s = urllib.parse.unquote(raw)
    return url_s

def load_element_icons_map() -> Dict[str, Dict[str, str]]:
    """Carrega o mapeamento de URLs de ícones elementais do arquivo estático JSON."""
    json_path = get_resource_path(os.path.join("static_data", "element_icons.json"))
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Erro ao carregar static_data/element_icons.json: {e}")
    return {}

ELEMENT_ICONS_MAP: Dict[str, Dict[str, str]] = load_element_icons_map()

def download_element_icons() -> None:
    """Garante que todos os ícones oficiais de elementos dos 3 jogos estejam em cache local."""
    try:
        from curl_cffi import requests
    except ImportError:
        return

    target_dir = get_resource_path(os.path.join("assets", "elements"))
    os.makedirs(target_dir, exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    for game, elements in ELEMENT_ICONS_MAP.items():
        for elem_name, url in elements.items():
            path = os.path.join(target_dir, f"{game}_{elem_name}.png")
            if not os.path.exists(path):
                try:
                    res = requests.get(url, headers=headers, impersonate="chrome", timeout=30)
                    if res.status_code == 200:
                        with open(path, "wb") as f:
                            f.write(res.content)
                        print(f"[INFO] Elemento em cache local: {game}_{elem_name}.png")
                except Exception as e:
                    print(f"[WARN] Falha ao baixar ícone de elemento {game}_{elem_name}: {e}")
