import json
import asyncio
import genshin
from typing import Dict, Any, List

def extrair_build_detalhada(dados_raw_api: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrai e normaliza os equipamentos (Artefatos/Relíquias/Discos) dos dados brutos da API
    (seja Enka.Network, Mihomo, HoyoLab ou adaptadores ZZZ).
    
    Lida graciosamente com dados ausentes, peças não equipadas ou mal formatadas.
    
    Args:
        dados_raw_api (dict): Dicionário contendo os dados brutos retornados pela API.
        
    Returns:
        dict: Estrutura padronizada contendo a build detalhada do personagem.
    """
    # Inicializa a estrutura de retorno padronizada
    build_detalhada = {
        "personagem": dados_raw_api.get("name", "Personagem Desconhecido"),
        "nivel": dados_raw_api.get("level", "N/A"),
        "equipamentos": []
    }
    
    # Busca a lista de equipamentos dependendo da API 
    # (Genshin/Enka usa 'equipList', HSR/Mihomo usa 'relics' ou 'equipments')
    equipamentos_raw = (
        dados_raw_api.get("equipList") or 
        dados_raw_api.get("relics") or 
        dados_raw_api.get("equipments") or []
    )
    
    for equip in equipamentos_raw:
        try:
            # 1. Ignorar armas/cones de luz/motores se estiverem misturados na lista
            equip_type = equip.get("type") or equip.get("flat", {}).get("itemType", "")
            if "Weapon" in str(equip_type) or "LightCone" in str(equip_type):
                continue
                
            # 2. Extração segura dos dados da peça (Suporte a formato flat da Enka)
            dados_item = equip.get("flat", equip)
            
            # Identificação da Peça
            tipo_peca = dados_item.get("equipType", dados_item.get("type", "Peça Desconhecida"))
            nome_set = dados_item.get("setNameText", dados_item.get("setName", "Set Desconhecido"))
            
            # 3. Extração do Atributo Principal (mainstat)
            main_stat_dict = dados_item.get("reliquaryMainstat") or equip.get("mainstat") or {}
            
            ms_nome = main_stat_dict.get("mainPropId", main_stat_dict.get("name", "Atributo Desconhecido"))
            ms_valor = main_stat_dict.get("statValue", main_stat_dict.get("value", 0))
            
            # Formata o valor principal (pode ser string "31.1%" ou float 31.1 dependendo da API)
            atributo_principal = f"{ms_nome}: {ms_valor}"
            
            # 4. Extração dos Subatributos (substats)
            sub_stats_raw = dados_item.get("reliquarySubstats") or equip.get("substats") or []
            lista_subatributos = []
            
            for sub in sub_stats_raw:
                sub_nome = sub.get("appendPropId", sub.get("name", "Desconhecido"))
                sub_valor = sub.get("statValue", sub.get("value", 0))
                
                # Se for número positivo, adiciona '+' para ficar no formato in-game
                prefixo = "+" if isinstance(sub_valor, (int, float)) and sub_valor > 0 else ""
                lista_subatributos.append(f"{sub_nome}: {prefixo}{sub_valor}")
                
            # 5. Montagem do Dicionário Final da Peça
            peca_extraida = {
                "tipo_peca": tipo_peca,
                "nome_set": nome_set,
                "atributo_principal": atributo_principal,
                # Caso o array venha vazio (ex: artefato level 0)
                "subatributos": lista_subatributos if lista_subatributos else ["Nenhum subatributo (Peça nv. 0?)"]
            }
            
            build_detalhada["equipamentos"].append(peca_extraida)
            
        except AttributeError:
            # Caso algum campo venha nulo/None ao invés de dicionário
            continue
        except Exception as e:
            # Fallback seguro para evitar que um artefato bugado crashe todo o parser
            print(f"[Aviso] Falha ao processar peça de equipamento para {build_detalhada['personagem']}: {str(e)}")
            continue
            
    return build_detalhada


def formatar_contexto_build_rag(dados_personagem: Dict[str, Any]) -> str:
    """
    Converte a estrutura normalizada da build em um bloco Markdown limpo, 
    altamente otimizado para ser injetado no contexto de um modelo LLM (RAG).
    
    Args:
        dados_personagem (dict): Retorno da função `extrair_build_detalhada`.
        
    Returns:
        str: String formatada em Markdown pronta para envio ao Groq/Llama/DeepSeek.
    """
    if not dados_personagem or not dados_personagem.get("equipamentos"):
        return "Nenhum dado de equipamento encontrado para este personagem."
        
    md_lines = []
    md_lines.append(f"## Análise de Build Detalhada - {dados_personagem.get('personagem')}")
    md_lines.append(f"**Nível:** {dados_personagem.get('nivel', 'N/A')}\n")
    md_lines.append("### Equipamentos (Artefatos / Relíquias / Discos)")
    
    for i, peca in enumerate(dados_personagem["equipamentos"], 1):
        md_lines.append(f"\n#### Peça {i}: {peca.get('tipo_peca')} - Set: `{peca.get('nome_set')}`")
        md_lines.append(f"- **Atributo Principal:** {peca.get('atributo_principal')}")
        md_lines.append("- **Subatributos:**")
        
        for sub in peca.get("subatributos", []):
            md_lines.append(f"  • {sub}")
            
    return "\n".join(md_lines)


# ==========================================
# SYSTEM PROMPT PARA A LLM (RAG)
# ==========================================

SYSTEM_PROMPT = """Você é um Especialista Meta-Analista de Jogos da HoYoverse (Genshin Impact, Honkai: Star Rail, Zenless Zone Zero).
Sua tarefa é analisar os dados de equipamento (Artefatos, Relíquias ou Discos) de um personagem fornecidos no contexto e fornecer uma auditoria técnica de otimização de build para o jogador.

Ao analisar a build detalhada recebida, siga rigidamente as seguintes diretrizes:

1. AVALIAÇÃO DE ATRIBUTOS PRINCIPAIS:
   - Verifique se os atributos principais de cada peça estão corretos para o melhor arquétipo do personagem (ex: DPS, Suporte, Healer).

2. BALANÇO DE SUBATRIBUTOS (SUBSTATS):
   - Avalie a distribuição geral. Verifique proporções importantes (como Taxa/Dano Crítico 1:2), Recarga de Energia mínima necessária ou Speed/Velocidade para alcançar os breakpoints de turnos.

3. IDENTIFICAÇÃO DE "STATUS MORTOS" (DEAD STATS):
   - Aponte claramente quais subatributos estão desperdiçados e não agregam ao kit do personagem (ex: DEF plana ou HP em um DPS hypercarry focado em ATK).
   
4. VEREDITO - SUBSTITUIÇÃO PRIORITÁRIA:
   - Identifique e indique EXATAMENTE qual é a pior peça da build atual que precisa de substituição imediata.
   - Justifique sua escolha explicando o porquê essa peça é a pior (ex: muitos "rolls" em status mortos ou atributo principal quebrado).

Formate sua resposta em Markdown de maneira clara e profissional, utilizando tópicos (bullet points) e negrito para destacar nomes de peças e os atributos mencionados. Seja direto, técnico e focado na otimização de resultado final (dano, sobrevida ou buffs).
"""

async def extrair_builds_completas_hoyolab(cookie_v2_ltoken: str, cookie_v2_ltuid: str, uid_game: int):
    """
    Conecta na HoYoLAB via Cookie, varre todos os personagens 
    e extrai os substatus exatos de cada relíquia equipada.
    """
    client = genshin.Client()
    
    # Define os cookies de sessão do usuário
    client.set_cookies({
        "ltuid_v2": cookie_v2_ltuid,
        "ltoken_v2": cookie_v2_ltoken
    })
    
    texto_rag_formatado = "=== DETALHAMENTO DE RELÍQUIAS E SUBSTATUS (HOYOLAB) ===\n\n"

    try:
        # Puxa os personagens da conta
        characters = await client.get_starrail_characters(uid_game)
        
        for char in characters.avatar_list:
            # Puxa o detalhamento profundo do personagem
            detail = await client.get_starrail_character_details(char.id)
            
            if not detail.relics:
                continue # Pula se o personagem não tiver relíquias equipadas
                
            texto_rag_formatado += f"👤 PERSONAGEM: {char.name} (Nível {char.level})\n"
            
            for relic in detail.relics:
                nome_peca = relic.name
                posicao = relic.pos # 1: Cabeça, 2: Mãos, 3: Corpo, 4: Pés, 5: Esfera, 6: Cordão
                main_stat = f"{relic.main_property.name} ({relic.main_property.value})"
                
                # Monta a lista de substatus
                substats = [f"{sub.name}: {sub.value}" for sub in relic.sub_properties]
                substats_str = ", ".join(substats) if substats else "Sem substatus"
                
                texto_rag_formatado += f"  • [Slot {posicao}] {nome_peca}\n"
                texto_rag_formatado += f"    - Principal: {main_stat}\n"
                texto_rag_formatado += f"    - Substatus: {substats_str}\n"
            
            texto_rag_formatado += "\n" + "-"*40 + "\n\n"

        return texto_rag_formatado

    except Exception as e:
        print(f"Erro ao extrair dados via HoYoLAB: {e}")
        return None
