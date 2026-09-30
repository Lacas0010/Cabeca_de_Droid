import os
import json
from typing import AsyncGenerator
from groq_rag import GroqRAG
from core.config import get_config
from services.roster_service import get_roster
from build_calculator import find_trash_relics, analyze_account_luck, get_meta_data
import database

async def generate_account_roast_stream(game_id: str) -> AsyncGenerator[str, None]:
    """Prepara o contexto rico da conta e transmite o Roast gerado pela IA via tokens SSE."""
    config = get_config()
    api_key = config.get("groq_api_key") or config.get("gemini_api_key") or os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        yield "data: " + json.dumps({"error": "Erro: Chave API do Groq não configurada. Por favor, adicione e salve sua chave na aba Configurações."}) + "\n\n"
        return
        
    try:
        rag = GroqRAG(api_key=api_key)
        
        # 1. Carrega Roster do banco/arquivos
        roster = await get_roster(game_id)
        
        # Consolida resumo legível dos personagens para o prompt
        roster_summary_lines = []
        if roster:
            for c in roster[:15]:  # Top 15 personagens
                name = c.get("name", "Desconhecido")
                level = c.get("level", 1)
                rarity = c.get("rarity", 4)
                score = c.get("overall_score", 0.0)
                grade = c.get("overall_grade", "D")
                weapon = c.get("weapon_name") or (c.get("weapon", {}).get("name") if isinstance(c.get("weapon"), dict) else "Nenhuma/Sem Dados")
                
                # Relíquias equipadas e status principais
                relics = c.get("relics", [])
                relic_details = []
                if isinstance(relics, list):
                    for r in relics:
                        if isinstance(r, dict):
                            slot = r.get("slot") or r.get("slot_name", "slot")
                            main_stat = r.get("main_stat") or r.get("main_stat_name", "")
                            rv = r.get("rv", 0)
                            relic_details.append(f"{slot}:{main_stat}(RV:{rv}%)")
                
                relics_str = ", ".join(relic_details[:6]) if relic_details else "Nenhuma relíquia equipada"
                roster_summary_lines.append(
                    f"- {name} (Nv {level}, {rarity}★) | Nota Build: {score}% ({grade}) | Arma: {weapon} | Relíquias: [{relics_str}]"
                )
        
        account_summary = "\n".join(roster_summary_lines) if roster_summary_lines else "Nenhum personagem sincronizado no roster."
        
        # 2. Busca Peças Lixo (Trash Relics)
        trash_info_str = ""
        try:
            roster_db = database.get_roster_data(game_id=game_id)
            all_relics = []
            for char in roster_db:
                for r in char.get("relics", []):
                    all_relics.append({
                        "name": r.get("name", ""),
                        "slot": r.get("slot", ""),
                        "main_stat": r.get("main", r.get("main_stat", "")),
                        "substats": [{"name": s.strip()} for s in str(r.get("sub", "")).split(",") if s.strip()]
                    })
            meta = get_meta_data(game_id)
            trash_data = find_trash_relics(game_id=game_id, relics=all_relics, meta_data=meta)
            if isinstance(trash_data, dict) and "trash_relics" in trash_data:
                trash_list = trash_data.get("trash_relics", [])
                trash_lines = []
                for t in trash_list[:8]:
                    char_n = t.get("character_name", "Inventário")
                    slot_n = t.get("slot", "")
                    main_s = t.get("main_stat", "")
                    reason = t.get("reason", "")
                    trash_lines.append(f"- {char_n} ({slot_n}): {main_s} | Motivo: {reason}")
                trash_info_str = "\n".join(trash_lines)
        except Exception as t_err:
            print(f"[WARN] Erro ao buscar trash relics para o roast: {t_err}")

        # 3. Busca Índice de Sorte (Luck Index)
        luck_info_str = ""
        try:
            roster_luck = roster if isinstance(roster, list) else []
            luck_data = analyze_account_luck(game_id, roster_luck)
            if isinstance(luck_data, dict):
                score_name = luck_data.get("luck_score_name", "Desconhecido")
                god_roll = luck_data.get("god_roll")
                cursed_roll = luck_data.get("cursed_roll")
                luck_info_str = f"Nota Geral de Sorte: {score_name}\n"
                if isinstance(god_roll, dict):
                    luck_info_str += f"God Roll: Peça de {god_roll.get('char_name')} ({god_roll.get('slot')}) com {god_roll.get('rv')}% RV\n"
                if isinstance(cursed_roll, dict):
                    luck_info_str += f"Cursed Roll: Peça de {cursed_roll.get('char_name')} ({cursed_roll.get('slot')}) com apenas {cursed_roll.get('rv')}% RV\n"
        except Exception as l_err:
            print(f"[WARN] Erro ao buscar luck index para o roast: {l_err}")

        for chunk in rag.generate_account_roast_stream(
            game_id=game_id,
            account_summary=account_summary,
            trash_relics_info=trash_info_str,
            luck_info=luck_info_str
        ):
            yield "data: " + json.dumps({"token": chunk}) + "\n\n"
            
    except Exception as roast_err:
        yield "data: " + json.dumps({"error": f"Erro no servidor ao preparar o Roast: {roast_err}"}) + "\n\n"
