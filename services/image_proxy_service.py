"""Serviço de utilidades de sistema: proxy de imagens anti-SSRF, otimização WebP, ZIP de guias e reset local."""

import hashlib
import io
import ipaddress
import os
import shutil
import socket
import tempfile
import threading
import time
import zipfile
from typing import Callable, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from fastapi import HTTPException

import database
from core.config import get_data_path

_PROXY_THREAD_LOCAL = threading.local()
MAX_PROXY_IMAGE_BYTES = 15 * 1024 * 1024  # 15 MB


def get_proxy_session():
    session = getattr(_PROXY_THREAD_LOCAL, "session", None)
    if session is None:
        try:
            from curl_cffi import requests

            session = requests.Session(impersonate="chrome")
            _PROXY_THREAD_LOCAL.session = session
        except Exception:
            session = None
    return session


def is_blocked_ip(ip_obj: ipaddress._BaseAddress) -> bool:
    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_multicast
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
    )


def validate_public_image_url(url: str, socket_mod=socket) -> str:
    """Valida URL http/https e bloqueia endereços loopback, privados, link-local ou reservados (anti-SSRF)."""
    if not url or not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL de imagem inválida.")

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").strip().lower()
    if parsed.scheme not in ("http", "https") or not hostname:
        raise HTTPException(status_code=400, detail="URL de imagem inválida.")

    if hostname in ("localhost", "localhost.localdomain") or hostname.endswith((".local", ".internal")):
        raise HTTPException(status_code=400, detail="Acesso a endereços locais/privados não é permitido.")

    try:
        ip_obj = ipaddress.ip_address(hostname.strip("[]"))
        if is_blocked_ip(ip_obj):
            raise HTTPException(status_code=400, detail="Acesso a IPs privados ou de loopback não é permitido.")
        return url
    except ValueError:
        pass

    try:
        addr_infos = socket_mod.getaddrinfo(hostname, None)
    except socket.gaierror:
        addr_infos = []

    for info in addr_infos:
        raw_ip = info[4][0].split("%", 1)[0]
        try:
            resolved_ip = ipaddress.ip_address(raw_ip)
        except ValueError:
            continue
        if is_blocked_ip(resolved_ip):
            raise HTTPException(status_code=400, detail="Acesso a IPs privados ou de loopback não é permitido.")

    return url


def atomic_write_cache_file(target_path: str, content: bytes, fallback_dir: Optional[str] = None) -> None:
    """Grava arquivo de cache usando arquivo temporário único no mesmo diretório + os.replace."""
    target_dir = os.path.dirname(target_path) or fallback_dir or get_data_path(os.path.join("assets", "cache", "images"))
    os.makedirs(target_dir, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=target_dir, prefix=".img_", suffix=".tmp", delete=False) as tf:
            tmp_path = tf.name
            tf.write(content)
        os.replace(tmp_path, target_path)
    except Exception:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def detect_image_mime(data: bytes, default: str = "image/png") -> str:
    if not data or len(data) < 4:
        return default
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    if data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WEBP":
        return "image/webp"
    if b"ftypavif" in data[:24]:
        return "image/avif"
    if data.lstrip().startswith(b"<svg") or (data.lstrip().startswith(b"<?xml") and b"<svg" in data[:250]):
        return "image/svg+xml"
    return default


def optimize_image(content_bytes: bytes, w: Optional[int] = None, fmt: Optional[str] = "webp") -> Tuple[bytes, str]:
    """Redimensiona proporcionalmente e converte imagens para WebP via Pillow."""
    if (
        not content_bytes
        or content_bytes.startswith(b"<svg")
        or b"<svg" in content_bytes[:250]
        or content_bytes.startswith((b"GIF87a", b"GIF89a"))
    ):
        return content_bytes, detect_image_mime(content_bytes)

    clean_fmt = (fmt or "webp").lower().strip()
    if clean_fmt not in ("webp", "png", "jpeg", "jpg"):
        clean_fmt = "webp"

    try:
        from PIL import Image

        with Image.open(io.BytesIO(content_bytes)) as img:
            orig_w, orig_h = img.size
            if w and w > 0 and w < orig_w:
                ratio = w / float(orig_w)
                target_h = max(1, int(orig_h * ratio))
                img = img.resize((w, target_h), Image.Resampling.LANCZOS)

            out = io.BytesIO()
            if clean_fmt == "webp":
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA" if "transparency" in img.info else "RGB")
                img.save(out, format="WEBP", quality=82, method=4)
                return out.getvalue(), "image/webp"
            elif clean_fmt in ("jpeg", "jpg"):
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(out, format="JPEG", quality=85, optimize=True)
                return out.getvalue(), "image/jpeg"
            else:
                img.save(out, format="PNG", optimize=True)
                return out.getvalue(), "image/png"
    except Exception:
        return content_bytes, detect_image_mime(content_bytes)


def read_cached_bytes(path: str) -> Optional[bytes]:
    if os.path.exists(path) and os.path.getsize(path) > 100:
        try:
            with open(path, "rb") as f:
                return f.read()
        except OSError:
            return None
    return None


def fetch_remote_image_bytes(
    url: str,
    socket_mod=socket,
    session_getter: Callable = get_proxy_session,
) -> bytes:
    referer = "https://act.hoyoverse.com/"
    if "prydwen.gg" in url:
        referer = "https://www.prydwen.gg/"
    elif "zenless" in url:
        referer = "https://zenless-zone-zero.fandom.com/"
    elif "genshin" in url or "gensin" in url:
        referer = "https://genshin-impact.fandom.com/"
    elif "wikia" in url or "fandom" in url:
        referer = "https://honkai-star-rail.fandom.com/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": referer,
    }

    from curl_cffi import requests

    session = session_getter() or requests
    last_resp = None

    for attempt in range(3):
        current_url = url
        for _redirect_hop in range(4):
            validate_public_image_url(current_url, socket_mod=socket_mod)
            try:
                resp = session.get(
                    current_url,
                    headers=headers,
                    impersonate="chrome",
                    timeout=20,
                    allow_redirects=False,
                )
            except TypeError:
                resp = session.get(current_url, headers=headers, impersonate="chrome", timeout=20)
            except Exception:
                resp = None
                break

            last_resp = resp
            status_code = getattr(resp, "status_code", 0)
            resp_headers = getattr(resp, "headers", {}) or {}
            if status_code in (301, 302, 303, 307, 308):
                loc = resp_headers.get("Location") or resp_headers.get("location")
                if not loc:
                    break
                current_url = urljoin(current_url, str(loc))
                continue

            final_url = getattr(resp, "url", None)
            if final_url and str(final_url) != current_url:
                validate_public_image_url(str(final_url), socket_mod=socket_mod)

            raw_len = resp_headers.get("Content-Length") or resp_headers.get("content-length")
            if raw_len:
                try:
                    if int(raw_len) > MAX_PROXY_IMAGE_BYTES:
                        raise HTTPException(status_code=413, detail="Imagem excede o tamanho máximo permitido.")
                except ValueError:
                    pass

            if status_code == 200:
                body = getattr(resp, "content", b"") or b""
                if len(body) > MAX_PROXY_IMAGE_BYTES:
                    raise HTTPException(status_code=413, detail="Imagem excede o tamanho máximo permitido.")
                if len(body) > 100:
                    return body
                break

            break

        if attempt < 2:
            time.sleep(0.35 * (attempt + 1))

    status_code = getattr(last_resp, "status_code", 502) if last_resp is not None else 502
    raise HTTPException(status_code=status_code, detail=f"Falha ao obter imagem da origem: {status_code}")


def process_proxy_image(
    url: str,
    w: Optional[int],
    target_fmt: str,
    cache_dir: str,
    socket_mod=socket,
    session_getter: Callable = get_proxy_session,
) -> Tuple[bytes, str, str]:
    """Executa leitura de cache, download, otimização Pillow e escrita atômica."""
    os.makedirs(cache_dir, exist_ok=True)
    cache_sig = f"{url}|w={w or 0}|fmt={target_fmt}"
    cache_key = hashlib.sha256(cache_sig.encode("utf-8")).hexdigest()
    cache_path = os.path.join(cache_dir, f"{cache_key}.bin")

    cached = read_cached_bytes(cache_path)
    if cached is not None:
        return cached, detect_image_mime(cached), "HIT"

    raw_key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    raw_path = os.path.join(cache_dir, f"{raw_key}.raw")
    content_bytes = read_cached_bytes(raw_path)

    if content_bytes is None:
        content_bytes = fetch_remote_image_bytes(url, socket_mod=socket_mod, session_getter=session_getter)
        atomic_write_cache_file(raw_path, content_bytes, fallback_dir=cache_dir)

    if target_fmt != "raw" or (w and w > 0):
        content_bytes, content_type = optimize_image(content_bytes, w=w, fmt=target_fmt)
    else:
        content_type = detect_image_mime(content_bytes)

    atomic_write_cache_file(cache_path, content_bytes, fallback_dir=cache_dir)
    return content_bytes, content_type, "MISS"


def build_guides_zip_bytes(target_folders: List[str], data_path_fn: Callable = get_data_path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for folder in target_folders:
            folder_path = data_path_fn(folder)
            if os.path.exists(folder_path):
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        if file.endswith((".pyc", ".tmp", ".log", ".DS_Store")):
                            continue
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, start=os.path.dirname(folder_path))
                        zf.write(full_path, arcname=rel_path)
    return buffer.getvalue()


def reset_all_local_data(data_path_fn: Callable = get_data_path, db_mod=database) -> None:
    for folder in ("zzz", "hsr", "genshin"):
        folder_path = data_path_fn(folder)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path, ignore_errors=True)
    db_mod.reset_database()
