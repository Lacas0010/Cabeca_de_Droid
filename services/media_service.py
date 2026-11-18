import io
import os
import json
import urllib.parse
from typing import Dict, Any
from core.config import get_resource_path, get_data_path

ELEMENT_FILENAME_ALIASES = {
    "fogo": "fire",
    "gelo": "ice",
    "fisico": "physical",
    "físico": "physical",
    "vento": "wind",
    "raio": "lightning",
    "eletrico": "electric",
    "elétrico": "electric",
    "quantico": "quantum",
    "quântico": "quantum",
    "imaginario": "imaginary",
    "imaginário": "imaginary",
    "eter": "ether",
    "éter": "ether",
    "element_100": "physical",
    "element 100": "physical",
    "element_200": "fire",
    "element 200": "fire",
    "element_300": "lumiflux",
    "element 300": "lumiflux",
    "auric ink": "lumiflux",
    "auric_ink": "lumiflux",
    "element_400": "electric",
    "element 400": "electric",
    "element_500": "ether",
    "element 500": "ether",
}


def _detect_valid_image_mime(data: bytes) -> str:
    """Retorna o MIME type se os bytes formarem uma imagem válida (rejeita HTML 403/404)."""
    if not data or len(data) < 16:
        return ""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    head = data[:256].lstrip().lower()
    if head.startswith(b"<svg"):
        return "image/svg+xml"
    return ""


def _save_element_png(raw_bytes: bytes, dest_path: str) -> bool:
    """Valida bytes de imagem e grava atomicamente em formato PNG real."""
    mime = _detect_valid_image_mime(raw_bytes)
    if not mime:
        return False

    out_bytes = raw_bytes
    if mime != "image/png" and mime != "image/svg+xml":
        try:
            from PIL import Image

            with Image.open(io.BytesIO(raw_bytes)) as img:
                buf = io.BytesIO()
                img.convert("RGBA").save(buf, format="PNG")
                out_bytes = buf.getvalue()
        except Exception:
            pass

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    tmp_path = f"{dest_path}.tmp"
    with open(tmp_path, "wb") as f:
        f.write(out_bytes)
    os.replace(tmp_path, dest_path)
    return True


def _normalize_element_filename(safe_name: str) -> str:
    """Normaliza prefixos/aliases PT-BR ou enums HoYoLAB para o nome canônico '<game>_<elem>.png'."""
    if "_" not in safe_name or "." not in safe_name:
        return safe_name
    stem, ext = safe_name.rsplit(".", 1)
    game_part, elem_part = stem.split("_", 1)
    elem_low = elem_part.lower().strip()
    canonical_elem = ELEMENT_FILENAME_ALIASES.get(elem_low, elem_low)
    return f"{game_part.lower()}_{canonical_elem}.{ext.lower()}"


def _is_valid_cached_image_file(path: str) -> bool:
    if not os.path.isfile(path):
        return False
    try:
        with open(path, "rb") as f:
            head = f.read(256)
        return bool(_detect_valid_image_mime(head))
    except OSError:
        return False


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


def download_element_icons(force_invalid: bool = True) -> None:
    """Garante que todos os ícones oficiais de elementos dos 3 jogos estejam em cache local PNG."""
    try:
        from curl_cffi import requests
    except ImportError:
        return

    icons_map = ELEMENT_ICONS_MAP or load_element_icons_map()
    if not icons_map:
        return

    target_dir = get_data_path(os.path.join("assets", "elements"))
    os.makedirs(target_dir, exist_ok=True)
    session = requests.Session(impersonate="chrome")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    for game, elements in icons_map.items():
        for elem_name, url in elements.items():
            path = os.path.join(target_dir, f"{game}_{elem_name}.png")
            already_ok = _is_valid_cached_image_file(path) if force_invalid else os.path.exists(path)
            if not already_ok:
                try:
                    res = session.get(url, headers=headers, timeout=20)
                    if res.status_code == 200 and _save_element_png(res.content, path):
                        print(f"[INFO] Elemento em cache local: {game}_{elem_name}.png")
                    else:
                        print(
                            f"[WARN] Resposta inválida ao baixar ícone de elemento {game}_{elem_name}: HTTP {res.status_code}"
                        )
                except Exception as e:
                    print(f"[WARN] Falha ao baixar ícone de elemento {game}_{elem_name}: {e}")


def get_element_icon_asset(filename: str) -> tuple[bytes, str]:
    """Retorna ícone elemental oficial em cache local (com fallback on-demand e SVG offline)."""
    safe_name = os.path.basename(str(filename or "")).strip()
    if not safe_name or not safe_name.lower().endswith((".png", ".webp", ".svg")):
        raise ValueError("Invalid element icon filename")

    canonical_name = _normalize_element_filename(safe_name)
    candidates = [canonical_name] if canonical_name == safe_name else [canonical_name, safe_name]

    for cand in candidates:
        for local_path in (
            get_data_path(os.path.join("assets", "elements", cand)),
            get_resource_path(os.path.join("assets", "elements", cand)),
        ):
            if os.path.isfile(local_path):
                with open(local_path, "rb") as f:
                    data = f.read()
                detected_mime = _detect_valid_image_mime(data)
                if detected_mime:
                    return data, detected_mime

    # Tenta baixar sob demanda caso ainda não exista em cache local
    if "_" in canonical_name and "." in canonical_name:
        game_id, rest = canonical_name.rsplit(".", 1)[0].split("_", 1)
        icons_map = ELEMENT_ICONS_MAP or load_element_icons_map()
        url = icons_map.get(game_id, {}).get(rest)
        if url:
            try:
                from curl_cffi import requests

                res = requests.get(url, impersonate="chrome", timeout=8)
                dest_path = get_data_path(os.path.join("assets", "elements", canonical_name))
                if res.status_code == 200 and _save_element_png(res.content, dest_path):
                    with open(dest_path, "rb") as f:
                        saved = f.read()
                    return saved, (_detect_valid_image_mime(saved) or "image/png")
            except Exception:
                pass

    palette = ("#38bdf8", "#a855f7", "#10b981", "#f59e0b", "#ec4899", "#ef4444")
    accent = palette[sum(ord(ch) for ch in canonical_name) % len(palette)]
    tail = canonical_name.rsplit(".", 1)[0].split("_")[-1]
    letter = next((ch.upper() for ch in tail if ch.isalnum()), "E")
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
        f'<circle cx="12" cy="12" r="10.5" fill="#0f172a" stroke="{accent}" stroke-width="2"/>'
        f'<path d="M12 4.5L18.5 12 12 19.5 5.5 12Z" fill="{accent}" fill-opacity="0.28" stroke="{accent}" stroke-width="1.3"/>'
        f'<text x="12" y="15.2" text-anchor="middle" font-family="sans-serif" font-size="9" font-weight="700" fill="#f8fafc">{letter}</text>'
        "</svg>"
    )
    return svg.encode("utf-8"), "image/svg+xml"


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

    target_dir = get_data_path(os.path.join("assets", "shards", "hsr"))
    os.makedirs(target_dir, exist_ok=True)

    session: Any = requests.Session(impersonate="chrome")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://honkai-star-rail.fandom.com/",
    }

    keys_to_process = []
    if char_names:
        for cname in char_names:
            c_clean = re.sub(r"[^a-z0-9_]", "", cname.lower().strip().replace(" ", "_"))
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
        clean_name = re.sub(r"[^a-z0-9_]", "", str(k).lower().replace(" ", "_"))
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
