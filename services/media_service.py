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

def download_hsr_eidolon_shards(char_names=None) -> None:
    """Garante que os fragmentos de Eidolon do HSR estejam baixados localmente na pasta assets/shards/hsr/."""
    try:
        from curl_cffi import requests
        import re
    except ImportError:
        return

    json_path = get_resource_path(os.path.join("static_data", "hsr_eidolon_shards.json"))
    if not os.path.exists(json_path):
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            shards_db = json.load(f)
    except Exception:
        return

    target_dir = get_resource_path(os.path.join("assets", "shards", "hsr"))
    os.makedirs(target_dir, exist_ok=True)

    session = requests.Session(impersonate="chrome")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://honkai-star-rail.fandom.com/"
    }

    keys_to_process = []
    if char_names:
        for cname in char_names:
            c_clean = re.sub(r'[^a-z0-9_]', '', cname.lower().strip().replace(' ', '_'))
            if cname.lower().strip() in shards_db:
                keys_to_process.append(cname.lower().strip())
            elif c_clean in shards_db:
                keys_to_process.append(c_clean)
    else:
        keys_to_process = list(shards_db.keys())

    for k in keys_to_process:
        char_shards = shards_db.get(k)
        if not isinstance(char_shards, dict):
            continue
        clean_name = re.sub(r'[^a-z0-9_]', '', str(k).lower().replace(' ', '_'))
        for pos_str, url in char_shards.items():
            if not url:
                continue
            fname = f"{clean_name}_{pos_str}.png"
            dest = os.path.join(target_dir, fname)
            if not os.path.exists(dest) or os.path.getsize(dest) < 1000:
                try:
                    res = session.get(url, headers=headers, timeout=15)
                    if res.status_code == 200 and len(res.content) > 1000:
                        tmp = dest + ".tmp"
                        with open(tmp, "wb") as f:
                            f.write(res.content)
                        os.replace(tmp, dest)
                except Exception:
                    pass
