import os
import sys
import json
import traceback
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

import database
import build_calculator
from groq_rag import GroqRAG
from services.roster_service import get_roster, get_account_audit
from services.roast_service import generate_account_roast_stream
from schemas.gacha import StrategyAskAIRequest

router = APIRouter(tags=["Strategy & Account Audit"])

@router.get("/api/strategy/account-gaps/{game_id}")
async def get_account_gaps_endpoint(game_id: str):
    """
    Retorna o diagnóstico de lacunas da conta (Account Gap Analysis):
    - Cobertura de arquétipos essenciais (Sustentação, Buffers de Ação, DPSs, Sub-DPS)
    - Matriz de cobertura elemental
    - Lacunas estratégicas com severidade (Crítica, Alta, Moderada)
    - Recomendações ranqueadas de gacha para próximos banners
    - Prontidão para o Endgame (Abismo / Caos da Memória / Shiyu Defense)
    """
    game_id = game_id.lower().strip()
    if game_id not in ["genshin", "hsr", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido. Use 'genshin', 'hsr' ou 'zzz'.")
    
    try:
        roster_data = database.get_roster_data(game_id)
        endgame_data = database.get_endgame_data(game_id)
        result = build_calculator.analyze_account_gaps(game_id, roster_data, endgame_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/strategy/ask-ai-gaps")
async def ask_ai_account_gaps(req: StrategyAskAIRequest):
    """Executa consulta com o Groq RAG alimentado diretamente com a auditoria de lacunas da conta."""
    game_id = req.game_id.lower().strip()
    if game_id not in ["genshin", "hsr", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")

    try:
        roster_data = database.get_roster_data(game_id)
        endgame_data = database.get_endgame_data(game_id)
        gap_analysis = build_calculator.analyze_account_gaps(game_id, roster_data, endgame_data)

        # Carrega configuração para obter chave
        api_key = None
        if os.path.exists("config.json"):
            try:
                with open("config.json", "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    api_key = cfg.get("groq_api_key") or cfg.get("gemini_api_key")
            except Exception:
                pass

        server_mod = sys.modules.get("server")
        groq_cls = getattr(server_mod, "GroqRAG", GroqRAG) if server_mod else GroqRAG
        rag = groq_cls(api_key=api_key)
        if not rag.client:
            return {
                "analysis": gap_analysis,
                "ai_response": "⚠️ **Chave da IA Groq não configurada.** Vá até a aba **Configurações** e insira sua chave gratuita da Groq para habilitar as recomendações estratégicas inteligentes da IA em tempo real.",
                "has_ai": False
            }

        user_query = req.custom_question.strip() if req.custom_question else (
            f"Faça um parecer estratégico profundo sobre as lacunas da minha conta em {game_id.upper()}. "
            "Destaque: 1) Quais arquétipos devo priorizar nos próximos banners do Gacha; "
            "2) Quais personagens do meu Roster devo investir hoje para acelerar meu fechamento de Endgame; "
            "3) Como estruturar 2 composições equilibradas com o que tenho disponível."
        )

        context = gap_analysis.get("rag_summary_markdown", "")
        ai_response = rag.ask_assistant(prompt_usuario=user_query, contexto_rag=context)

        return {
            "analysis": gap_analysis,
            "ai_response": ai_response,
            "has_ai": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/luck-index/{game_id}")
async def get_luck_index(game_id: str):
    """Retorna a análise consolidada do Índice de Sorte da Conta (Luck Score & Substat Efficiency)."""
    game_id = game_id.lower().strip()
    if game_id not in ["genshin", "hsr", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
        
    try:
        roster_data = await get_roster(game_id)
        if not isinstance(roster_data, list):
            roster_data = []
            
        res = build_calculator.analyze_account_luck(game_id, roster_data)
        return res
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/audit/{game_id}")
async def get_account_audit_endpoint(game_id: str):
    """Retorna relatório de auditoria de saúde da conta + Tier List dos seus personagens."""
    try:
        return await get_account_audit(game_id)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/roast/{game_id}")
async def get_account_roast_stream(game_id: str):
    """Endpoint de streaming SSE para o Roast sarcástico da conta de um jogo (Persona Herta/Nous)."""
    return StreamingResponse(
        generate_account_roast_stream(game_id),
        media_type="text/event-stream"
    )
