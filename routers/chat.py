import os
import json
import traceback
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from core.config import get_config
from groq_rag import GroqRAG
from schemas.chat import ChatRequest, TeamAnalyzeRequest

router = APIRouter(tags=["AI Chat & Combat Team Synergy"])

@router.post("/api/chat")
async def chat_interaction(req: ChatRequest):
    """Endpoint do Chat RAG Local (Groq) com streaming SSE de tokens."""
    config = get_config()
    api_key = config.get("groq_api_key") or config.get("gemini_api_key") or os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        async def err_generator():
            yield "data: " + json.dumps({"error": "Erro: Chave API do Groq não configurada. Salve-a na aba Configurações."}) + "\n\n"
        return StreamingResponse(err_generator(), media_type="text/event-stream")
        
    try:
        rag = GroqRAG(api_key=api_key)
        context = rag.load_game_context(req.game_id, req.message)
        
        history_list = []
        for h in req.history:
            history_list.append({
                "role": h.role,
                "text": h.text
            })
            
        async def event_generator():
            try:
                for chunk in rag.ask_assistant_stream(
                    prompt_usuario=req.message,
                    contexto_rag=context,
                    historico_chat=history_list
                ):
                    yield "data: " + json.dumps({"token": chunk}) + "\n\n"
            except Exception as stream_err:
                yield "data: " + json.dumps({"error": str(stream_err)}) + "\n\n"
                
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as chat_err:
        traceback.print_exc()
        async def err_gen():
            yield "data: " + json.dumps({"error": f"Ocorreu um erro no processador do chat: {chat_err}"}) + "\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")

@router.post("/api/team/analyze")
async def analyze_team(req: TeamAnalyzeRequest):
    """Endpoint que analisa a sinergia de um time de personagens do roster via IA (SSE Stream)."""
    config = get_config()
    api_key = config.get("groq_api_key") or config.get("gemini_api_key") or os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        async def err_generator():
            yield "data: " + json.dumps({"error": "Erro: Chave API do Groq/Gemini não configurada. Configure na aba Configurações."}) + "\n\n"
        return StreamingResponse(err_generator(), media_type="text/event-stream")
        
    try:
        rag = GroqRAG(api_key=api_key)
        query_str = ", ".join(req.characters)
        context = rag.load_game_context(req.game_id, query_str)
        
        prompt_analysis = (
            f"Faça uma análise de sinergia de combate extremamente profissional e aprofundada para a seguinte equipe selecionada do jogo {req.game_id.upper()}: {', '.join(req.characters)}.\n"
            "Com base no contexto fornecido (suas builds reais de personagem + guias de metagame ideais):\n"
            "1. Descreva a sinergia geral do time e como as habilidades se complementam.\n"
            "2. Avalie as armas e relíquias/discos equipados em relação ao ideal do metagame, apontando acertos e desvios críticos.\n"
            "3. Detalhe a rotação de combate ideal passo a passo (quem inicia, quem buffa, quem aplica elemento, quem é o DPS principal).\n"
            "4. Forneça sugestões de melhorias diretas (substitutos ideais de personagens ou trocas recomendadas de armas/artefatos).\n"
            "Formate a resposta em Markdown limpo e amigável com emojis."
        )
        
        async def event_generator():
            try:
                for chunk in rag.ask_assistant_stream(
                    prompt_usuario=prompt_analysis,
                    contexto_rag=context,
                    historico_chat=[]
                ):
                    yield "data: " + json.dumps({"token": chunk}) + "\n\n"
            except Exception as stream_err:
                yield "data: " + json.dumps({"error": str(stream_err)}) + "\n\n"
                
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as chat_err:
        traceback.print_exc()
        async def err_gen():
            yield "data: " + json.dumps({"error": f"Erro no processamento do time: {chat_err}"}) + "\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")
