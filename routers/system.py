import os
import io
import shutil
import zipfile
import asyncio
import traceback
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import JSONResponse

import database
from core.config import get_resource_path

router = APIRouter(tags=["System & Utilities"])

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

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://act.hoyoverse.com/"
    }
    
    try:
        from curl_cffi import requests
        def fetch():
            return requests.get(url, headers=headers, impersonate="chrome", timeout=30)
            
        resp = await asyncio.to_thread(fetch)
        
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=f"Falha ao obter imagem da origem: {resp.status_code}")
            
        content_type = resp.headers.get("content-type", "image/png")
        return Response(
            content=resp.content,
            media_type=content_type,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Cache-Control": "public, max-age=86400"
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
