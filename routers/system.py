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

@router.get("/api/proxy_image")
async def proxy_image(url: str):
    """Proxy para carregar imagens externas no HTML5 Canvas sem sofrer bloqueio de CORS ou Tainted Canvas."""
    if not url or not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL de imagem inválida.")
    
    # Sanitização defensiva para URLs do Genshin com .png.png ou ide_
    try:
        from extractor import sanitize_genshin_url
        url = sanitize_genshin_url(url)
    except Exception:
        pass

    # 1. Verifica cache local em disco
    os.makedirs(_IMAGE_CACHE_DIR, exist_ok=True)
    cache_key = hashlib.sha256(url.encode("utf-8")).hexdigest()
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
                    "X-Cache-Status": "HIT"
                }
            )
        except Exception:
            pass

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://honkai-star-rail.fandom.com/" if ("wikia" in url or "fandom" in url) else "https://act.hoyoverse.com/"
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
        content_type = _detect_image_mime(content_bytes, resp.headers.get("content-type", "image/png"))

        # Salva em cache local de forma atômica
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
                "X-Cache-Status": "MISS"
            }
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar proxy de imagem: {e}")

@router.get("/api/accounts")
async def get_saved_accounts():
    """Retorna todas as contas salvas para alternância multi-conta."""
    try:
        return database.get_all_saved_accounts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        zip_filename = f"guias_{game_id.lower()}.zip" if game_id and game_id.lower() in valid_games else "guias_hoyoverse_todos.zip"
        
        return Response(
            content=buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{zip_filename}"'
            }
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

        return JSONResponse({
            "status": "success",
            "message": "Pastas zzz, hsr, genshin e banco de dados foram apagados com sucesso!"
        })
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao apagar dados: {str(e)}")
