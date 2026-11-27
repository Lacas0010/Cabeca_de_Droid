"""Rotas de sistema: proxy de imagens, download ZIP, reset local, ciclo de vida desktop e assets offline."""

import asyncio
import os
import socket
import traceback
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse

import database
from core.config import get_data_path
from core.security import is_loopback_request
from schemas.system import BrowserClientSignal
from services.browser_lifecycle_service import browser_lifecycle_manager
from services.image_proxy_service import (
    MAX_PROXY_IMAGE_BYTES,
    build_guides_zip_bytes,
    get_proxy_session,
    optimize_image,
    process_proxy_image,
    reset_all_local_data,
    validate_public_image_url,
)
from services.media_service import (
    get_element_icon_asset,
    get_endgame_icon_asset,
    get_resource_icon_asset,
    get_role_icon_asset,
)

router = APIRouter(tags=["System & Utilities"])

_IMAGE_CACHE_DIR = get_data_path(os.path.join("assets", "cache", "images"))
_get_proxy_session = get_proxy_session


@router.get("/api/proxy_image")
async def proxy_image(url: str, w: Optional[int] = None, format: Optional[str] = "webp"):
    """Proxy para carregar imagens externas, com redimensionamento e transcodificação WebP automática."""
    if not url or not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL de imagem inválida.")

    try:
        from extractor import sanitize_genshin_url

        url = sanitize_genshin_url(url)
    except Exception:
        pass

    await asyncio.to_thread(validate_public_image_url, url, socket)

    target_fmt = (format or "webp").lower().strip() if format else "raw"
    try:
        content_bytes, content_type, cache_status = await asyncio.to_thread(
            process_proxy_image,
            url,
            w,
            target_fmt,
            _IMAGE_CACHE_DIR,
            socket,
            _get_proxy_session,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar proxy de imagem: {e}")

    return Response(
        content=content_bytes,
        media_type=content_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Cache-Control": "public, max-age=604800",
            "X-Cache-Status": cache_status,
        },
    )


@router.get("/api/download/guides-zip")
async def download_guides_zip(game_id: Optional[str] = None):
    """Empacota as pastas de guias (genshin, hsr, zzz) em um arquivo .zip para download."""
    try:
        valid_games = ["genshin", "hsr", "zzz"]
        if game_id and game_id.lower() in valid_games:
            target_folders = [game_id.lower()]
            zip_filename = f"guias_{game_id.lower()}.zip"
        else:
            target_folders = valid_games
            zip_filename = "guias_hoyoverse_todos.zip"

        zip_bytes = await asyncio.to_thread(build_guides_zip_bytes, target_folders, get_data_path)
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'},
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar arquivo zip de guias: {e}")


@router.api_route("/api/reset-data", methods=["POST", "DELETE"])
async def reset_all_data():
    """Apaga as 3 pastas (zzz, hsr, genshin) e limpa o banco de dados SQLite."""
    try:
        await asyncio.to_thread(reset_all_local_data, get_data_path, database)
        return JSONResponse({"status": "success", "message": "Pastas zzz, hsr, genshin e banco de dados apagados."})
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao apagar dados: {str(e)}")


@router.post("/api/system/heartbeat")
async def browser_heartbeat(payload: BrowserClientSignal, request: Request):
    """Registra atividade contínua de uma aba local aberta no navegador."""
    return browser_lifecycle_manager.register_heartbeat(payload.client_id, is_loopback=is_loopback_request(request))


@router.post("/api/system/disconnect")
async def browser_disconnect(payload: BrowserClientSignal, request: Request):
    """Sinaliza fechamento de uma aba local; encerra o servidor após janela de tolerância se nenhuma restar."""
    return browser_lifecycle_manager.register_disconnect(payload.client_id, is_loopback=is_loopback_request(request))


@router.get("/api/i18n/glossary")
async def get_i18n_glossary():
    """Retorna glossário centralizado de caminhos, elementos e personagens do backend."""
    from services.translation_service import get_frontend_glossary

    return get_frontend_glossary()


@router.get("/assets/elements/{filename}")
async def serve_element_icon_with_offline_fallback(filename: str):
    """Serve ícone elemental em cache local ou fallback vetorial offline sem erros 404."""
    try:
        content, media_type = await asyncio.to_thread(get_element_icon_asset, filename)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")
    headers = {"Cache-Control": "no-store"} if media_type == "image/svg+xml" else {}
    return Response(content=content, media_type=media_type, headers=headers)


@router.get("/assets/endgame/{filename}")
async def serve_endgame_mode_icon(filename: str):
    """Serve o ícone oficial do modo endgame em cache local (com download sob demanda)."""
    try:
        content, media_type = await asyncio.to_thread(get_endgame_icon_asset, filename)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Endgame icon not available")
    return Response(
        content=content,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/assets/icons/{filename}")
async def serve_role_icon_with_offline_fallback(filename: str):
    """Serve ícone oficial de Caminho (HSR), Arma (Genshin) ou Especialidade (ZZZ) com fallback SVG offline."""
    try:
        content, media_type = await asyncio.to_thread(get_role_icon_asset, filename)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")
    headers = {"Cache-Control": "no-store"} if media_type == "image/svg+xml" else {"Cache-Control": "public, max-age=86400"}
    return Response(content=content, media_type=media_type, headers=headers)


@router.get("/assets/resources/{filename}")
async def serve_resource_icon_with_offline_fallback(filename: str):
    """Serve ícone oficial de Energia (Resina/Poder/Bateria), Moeda ou Passe com fallback SVG offline."""
    try:
        content, media_type = await asyncio.to_thread(get_resource_icon_asset, filename)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")
    headers = {"Cache-Control": "no-store"} if media_type == "image/svg+xml" else {"Cache-Control": "public, max-age=86400"}
    return Response(content=content, media_type=media_type, headers=headers)
