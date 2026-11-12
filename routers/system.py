import os
import io
import time
import shutil
import zipfile
import hashlib
import asyncio
import traceback
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse

import database
from core.config import get_resource_path

router = APIRouter(tags=["System & Utilities"])

_IMAGE_CACHE_DIR = get_resource_path(os.path.join("assets", "cache", "images"))
_PROXY_SESSION = None


def _get_proxy_session():
    global _PROXY_SESSION
    if _PROXY_SESSION is None:
        try:
            from curl_cffi import requests

            _PROXY_SESSION = requests.Session(impersonate="chrome")
        except Exception:
            _PROXY_SESSION = None
    return _PROXY_SESSION


def _detect_image_mime(data: bytes, default: str = "image/png") -> str:
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


def optimize_image(content_bytes: bytes, w: Optional[int] = None, fmt: Optional[str] = "webp") -> tuple[bytes, str]:
    """Redimensiona proporcionalmente e converte imagens para WebP via Pillow."""
    if (
        not content_bytes
        or content_bytes.startswith(b"<svg")
        or b"<svg" in content_bytes[:250]
        or content_bytes.startswith((b"GIF87a", b"GIF89a"))
    ):
        return content_bytes, _detect_image_mime(content_bytes)

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
            if clean_fmt in ("webp",):
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
        return content_bytes, _detect_image_mime(content_bytes)


@router.get("/api/proxy_image")
async def proxy_image(url: str, w: Optional[int] = None, format: Optional[str] = "webp"):
    """Proxy para carregar imagens externas, com redimensionamento e transcodificação WebP automática."""
    if not url or not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL de imagem inválida.")

    # Sanitização defensiva para URLs do Genshin com .png.png ou ide_
    try:
        from extractor import sanitize_genshin_url

        url = sanitize_genshin_url(url)
    except Exception:
        pass

    target_fmt = (format or "webp").lower().strip() if format else "raw"
    os.makedirs(_IMAGE_CACHE_DIR, exist_ok=True)
    cache_sig = f"{url}|w={w or 0}|fmt={target_fmt}"
    cache_key = hashlib.sha256(cache_sig.encode("utf-8")).hexdigest()
    cache_path = os.path.join(_IMAGE_CACHE_DIR, f"{cache_key}.bin")

    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 100:
        try:
            with open(cache_path, "rb") as cf:
                content = cf.read()
            media_type = _detect_image_mime(content)
            return Response(
                content=content,
                media_type=media_type,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Cache-Control": "public, max-age=604800",
                    "X-Cache-Status": "HIT",
                },
            )
        except Exception:
            pass

    # Verifica cache bruto de download para evitar requisições redundantes se apenas 'w' variou
    raw_key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    raw_path = os.path.join(_IMAGE_CACHE_DIR, f"{raw_key}.raw")
    content_bytes = None

    if os.path.exists(raw_path) and os.path.getsize(raw_path) > 100:
        try:
            with open(raw_path, "rb") as rf:
                content_bytes = rf.read()
        except Exception:
            content_bytes = None

    if content_bytes is None:
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

        try:
            from curl_cffi import requests

            session = _get_proxy_session() or requests

            def fetch_with_retry():
                last_resp = None
                for attempt in range(3):
                    try:
                        resp = session.get(url, headers=headers, impersonate="chrome", timeout=20)
                        if resp.status_code == 200 and len(resp.content) > 100:
                            return resp
                        last_resp = resp
                        if resp.status_code in (403, 429, 502, 503, 504):
                            time.sleep(0.35 * (attempt + 1))
                    except Exception:
                        time.sleep(0.35 * (attempt + 1))
                return last_resp

            resp = await asyncio.to_thread(fetch_with_retry)

            if not resp or resp.status_code != 200:
                status_code = resp.status_code if resp else 502
                raise HTTPException(status_code=status_code, detail=f"Falha ao obter imagem da origem: {status_code}")

            content_bytes = resp.content

            # Salva o arquivo original bruto
            try:
                tmp_raw = f"{raw_path}.tmp"
                with open(tmp_raw, "wb") as f:
                    f.write(content_bytes)
                os.replace(tmp_raw, raw_path)
            except Exception:
                pass
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro ao processar proxy de imagem: {e}")

    # Otimização / WebP / Redimensionamento
    if target_fmt != "raw" or (w and w > 0):
        content_bytes, content_type = optimize_image(content_bytes, w=w, fmt=target_fmt)
    else:
        content_type = _detect_image_mime(content_bytes)

    # Salva variante processada no cache
    try:
        tmp_path = f"{cache_path}.tmp"
        with open(tmp_path, "wb") as f:
            f.write(content_bytes)
        os.replace(tmp_path, cache_path)
    except Exception:
        pass

    return Response(
        content=content_bytes,
        media_type=content_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Cache-Control": "public, max-age=604800",
            "X-Cache-Status": "MISS",
        },
    )


@router.get("/api/download/guides-zip")
async def download_guides_zip(game_id: Optional[str] = None):
    """
    Empacota as pastas de guias (genshin, hsr, zzz) ou uma pasta específica em um arquivo .zip
    e retorna para download direto no navegador.
    """
    try:
        buffer = io.BytesIO()
        valid_games = ["genshin", "hsr", "zzz"]

        if game_id and game_id.lower() in valid_games:
            target_folders = [game_id.lower()]
        else:
            target_folders = valid_games

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for folder in target_folders:
                folder_path = get_resource_path(folder)
                if os.path.exists(folder_path):
                    for root, _, files in os.walk(folder_path):
                        for file in files:
                            if file.endswith((".pyc", ".tmp", ".log", ".DS_Store")):
                                continue
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, start=os.path.dirname(folder_path))
                            zf.write(full_path, arcname=rel_path)

        buffer.seek(0)
        zip_filename = (
            f"guias_{game_id.lower()}.zip"
            if game_id and game_id.lower() in valid_games
            else "guias_hoyoverse_todos.zip"
        )

        return Response(
            content=buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'},
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar arquivo zip de guias: {e}")


@router.api_route("/api/reset-data", methods=["GET", "POST"])
async def reset_all_data():
    """Apaga as 3 pastas (zzz, hsr, genshin) e limpa todo o banco de dados SQLite."""
    try:
        folders = ["zzz", "hsr", "genshin"]
        for folder in folders:
            folder_path = get_resource_path(folder)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path, ignore_errors=True)

        database.reset_database()

        return JSONResponse(
            {"status": "success", "message": "Pastas zzz, hsr, genshin e banco de dados foram apagados com sucesso!"}
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao apagar dados: {str(e)}")
