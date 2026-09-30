import os
import json
from fastapi import APIRouter, HTTPException

import database
from core.config import get_config
from build_calculator import normalize_char_name
from groq_rag import GroqRAG
from services.roster_service import (
    get_roster,
    get_overview,
    parse_character_build_data,
    parse_meta_target,
)

router = APIRouter(tags=["Roster & Characters"])

@router.get("/api/roster/{game_id}")
async def get_roster_endpoint(game_id: str):
    """Retorna os dados dos personagens salvos no roster local."""
    try:
        return await get_roster(game_id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/overview")
async def get_overview_endpoint():
    """Gera dados resumidos consolidados dos 3 jogos mesclando SQLite e arquivos locais."""
    return get_overview()

@router.get("/api/build/{game_id}/{char_name}")
async def get_build_detail_endpoint(game_id: str, char_name: str):
    """Retorna os dados detalhados da build de um personagem, parseando o MD consolidado ou SQLite."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
    return parse_character_build_data(game_id, char_name)

@router.get("/api/compare/{game_id}/{char_name}")
async def compare_build_endpoint(game_id: str, char_name: str):
    """Retorna os dados da build do jogador comparados aos dados ideais do metagame."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
        
    element = ""
    try:
        roster = database.get_roster_data(game_id)
        c_norm = normalize_char_name(char_name)
        for char in roster:
            if normalize_char_name(char.get("name", "")) == c_norm or char.get("name", "").lower() == char_name.lower():
                element = char.get("element", "").lower()
                break
    except Exception as e:
        print(f"Erro ao buscar elemento do personagem no SQLite: {e}")
        
    build_data = parse_character_build_data(game_id, char_name)
    meta_target = parse_meta_target(game_id, char_name, element)
    
    return {
        "character": char_name,
        "game_id": game_id,
        "player_build": {
            "weapon": build_data.get("weapon", "Não informado"),
            "weapon_clean": build_data.get("weapon_clean", ""),
            "sets": build_data.get("sets", []),
            "stats": build_data.get("stats", {}),
            "pieces": build_data.get("pieces", [])
        },
        "meta_target": meta_target
    }

@router.get("/api/optimize/{game_id}/{char_name}")
async def optimize_character_build(game_id: str, char_name: str):
    """Gera sugestões de otimização de build com base nos dados do roster e no guia de meta."""
    game_id = game_id.lower().strip()
    if game_id not in ["hsr", "genshin", "zzz"]:
        raise HTTPException(status_code=400, detail="Jogo inválido.")
        
    config = get_config()
    api_key = config.get("groq_api_key") or config.get("gemini_api_key") or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="Chave API do Groq não configurada nas Configurações.")
        
    # Carrega dados do personagem e o contexto de guias
    build_data = parse_character_build_data(game_id, char_name)
    if not build_data.get("raw") and not build_data.get("sets") and not build_data.get("pieces"):
        return {"suggestions": ["Nenhum dado de Roster/Build encontrado para este personagem. Faça a sincronização primeiro na aba do jogo."]}
        
    guide_context = ""
    guides_dir = f"{game_id}/guias"
    if os.path.exists(guides_dir):
        safe_fn = char_name.lower().replace(" ", "_") + ".md"
        guide_path = os.path.join(guides_dir, safe_fn)
        if os.path.exists(guide_path):
            try:
                with open(guide_path, "r", encoding="utf-8") as f:
                    guide_context = f.read()[:3000]
            except Exception:
                pass
                
    rag = GroqRAG(api_key=api_key)
    prompt = (
        f"Você é um coach especializado de {game_id.upper()}. Dê exatamente 3 sugestões de melhorias curtas, diretas e acionáveis "
        f"para a build de {char_name} com base na build atual e nas recomendações de metagame.\n\n"
        f"Build atual do jogador:\n{json.dumps(build_data, ensure_ascii=False)}\n\n"
        f"Guia de Metagame de referência:\n{guide_context if guide_context else 'Não disponível. Sugira com base nas melhores práticas do jogo.'}\n\n"
        f"Responda apenas em formato JSON com uma lista de strings sob a chave 'suggestions'. Exemplo:\n"
        f"{{\"suggestions\": [\"1. Trocar a bota por velocidade\", \"2. Focar em taxa crítica nos substatus\", \"3. Usar o conjunto de 4 peças de quebra\"]}}"
    )
    
    try:
        completion = rag.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "Você responde estritamente em formato JSON válido, contendo apenas a chave 'suggestions'."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=250
        )
        if completion and completion.choices:
            resp = completion.choices[0].message.content
            return json.loads(resp)
    except Exception as e:
        print(f"Erro ao gerar otimização IA com GPT-OSS 120B: {e}")
        try:
            completion = rag.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Você responde estritamente em formato JSON válido, contendo apenas a chave 'suggestions'."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=250
            )
            if completion and completion.choices:
                return json.loads(completion.choices[0].message.content)
        except Exception:
            pass
            
    return {"suggestions": [
        "1. Priorizar os atributos principais recomendados nas peças de Relíquias/Artefatos.",
        "2. Tentar alcançar os bônus máximos de conjunto equipando 4 peças ideais.",
        "3. Fortalecer o nível das relíquias equipadas para maximizar os atributos base."
    ]}
