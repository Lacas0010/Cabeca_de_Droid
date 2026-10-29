import json
import traceback
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

import database
from schemas.chat import ChatRequest, TeamAnalyzeRequest

router = APIRouter(tags=["Chat & Combat Team Synergy"])


@router.get("/api/chat/history/{game_id}")
async def get_chat_history_endpoint(game_id: str, limit: int = 50):
    """Retorna o histórico persistido de mensagens de chat para o jogo selecionado ou global."""
    try:
        messages = database.get_chat_history(game_id, limit=limit)
        return {"game_id": game_id, "messages": messages}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/chat/history/{game_id}")
async def clear_chat_history_endpoint(game_id: str):
    """Limpa o histórico persistido de mensagens de chat para o jogo selecionado ou global."""
    try:
        deleted = database.clear_chat_history(game_id)
        return {"status": "success", "game_id": game_id, "deleted_count": deleted}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/chat")
async def chat_interaction(req: ChatRequest):
    """Endpoint do Chat com persistência no SQLite (Módulo de IA temporariamente desativado)."""
    try:
        database.save_chat_message(req.game_id, "user", req.message)
    except Exception:
        pass

    async def event_generator():
        msg = "O módulo de IA conversacional está temporariamente desativado nesta versão."
        yield "data: " + json.dumps({"token": msg}, ensure_ascii=False) + "\n\n"
        try:
            database.save_chat_message(req.game_id, "assistant", msg)
        except Exception:
            pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/api/team/analyze")
async def analyze_team(req: TeamAnalyzeRequest):
    """Endpoint de análise de sinergia de time (Módulo de IA temporariamente desativado)."""

    async def err_generator():
        yield (
            "data: "
            + json.dumps(
                {"error": "O módulo de análise por IA está temporariamente desativado nesta versão."},
                ensure_ascii=False,
            )
            + "\n\n"
        )

    return StreamingResponse(err_generator(), media_type="text/event-stream")
