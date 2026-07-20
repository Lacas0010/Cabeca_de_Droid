import os
import json
import re
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError

SYSTEM_INSTRUCTION = """
Você é o "HoYo AI Assistant", um assistente de inteligência artificial especialista e par de jogos da HoYoverse: Genshin Impact, Honkai: Star Rail (HSR) e Zenless Zone Zero (ZZZ).
Seu objetivo é ajudar o usuário com análises de meta-jogo, sugestões de builds de personagens, composições de equipes e otimização geral de contas com base nas informações do contexto e do roster dele.

CONDIÇÕES IMPORTANTES:
1. Você tem acesso a dados de contexto contendo o Roster do próprio usuário (personagens obtidos, níveis, constelações/eidolons, armas equipadas e artefatos). Use essas informações para dar respostas personalizadas para os personagens que ele possui!
2. Você também tem acesso a guias e relatórios de meta (extraídos do KeqingMains, Prydwen e Game8) contidos no contexto. Use estas informações como referência definitiva de builds recomendadas e tier lists.
3. Responda em Português do Brasil de forma clara, prestativa e estruturada. Use formatação Markdown (tabelas, negritos, tópicos) para facilitar a leitura.
4. Caso o usuário faça perguntas fora do contexto dos jogos da HoYoverse, responda gentilmente que seu foco é apenas auxiliá-lo nos jogos Genshin Impact, Honkai: Star Rail e Zenless Zone Zero.
"""

MODEL_NAME = "gemini-1.5-flash"
MODELOS_CANDIDATOS = [
    "gemini-1.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash-lite"
]

class GeminiRAG:
    def __init__(self, api_key: str = None):
        """
        Inicializa o assistente Gemini RAG.
        Carrega a chave do argumento, variável de ambiente ou config.json.
        """
        self.api_key = api_key
        
        # Tenta carregar do config.json se não fornecida
        if not self.api_key:
            config_path = "config.json"
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                        self.api_key = config.get("gemini_api_key")
                except Exception:
                    pass
                    
        # Tenta carregar do ambiente
        if not self.api_key:
            self.api_key = os.environ.get("GEMINI_API_KEY")
            
        self.client = None
        self.model_name = MODEL_NAME # Default
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                self.model_name = self._resolve_model()
            except Exception:
                pass

    def _resolve_model(self) -> str:
        """
        Testa os modelos candidatos e retorna o primeiro operacional.
        Ignora erros 429 (ResourceExhausted), pois indicam que o modelo é suportado pelo plano.
        """
        if not self.client:
            return MODEL_NAME
        for model in MODELOS_CANDIDATOS:
            try:
                self.client.models.generate_content(
                    model=model,
                    contents="ping",
                    config=types.GenerateContentConfig(max_output_tokens=5)
                )
                return model
            except Exception as e:
                err_msg = str(e)
                # Erro 429/ResourceExhausted significa que o modelo existe e é suportado!
                if "429" in err_msg or "ResourceExhausted" in err_msg or "quota" in err_msg.lower():
                    return model
                continue
        return MODEL_NAME

    def _generate_with_retry(self, client, model: str, contents, config=None, max_retries: int = 3) -> str:
        """
        Executa a chamada generate_content com retentativa em caso de erro de cota (429 / ResourceExhausted).
        """
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
                if response and response.text:
                    return response.text
                return "O modelo respondeu com conteúdo vazio."
            except Exception as e:
                err_msg = str(e)
                # Verifica se é um erro de limite de cota (429 ou ResourceExhausted)
                is_rate_limit = ("429" in err_msg or 
                                 "ResourceExhausted" in err_msg or 
                                 "RESOURCE_EXHAUSTED" in err_msg or 
                                 "quota" in err_msg.lower() or
                                 "exhausted" in err_msg.lower())
                
                if is_rate_limit and attempt < max_retries - 1:
                    print(f"[INFO] Limite de requisições atingido. Aguardando 15s para tentar novamente ({attempt + 1}/{max_retries})...")
                    time.sleep(15)
                else:
                    raise e

    def test_connection(self) -> tuple[bool, str]:
        """
        Testa a autenticação da chave do Gemini API fazendo uma chamada simples.
        Retorna (sucesso, mensagem).
        """
        if not self.api_key:
            return False, "Chave API não configurada."
            
        try:
            # Força reinstanciação para testar chave fornecida
            test_client = genai.Client(api_key=self.api_key)
            
            resolved_model = None
            
            for model_name in MODELOS_CANDIDATOS:
                try:
                    test_client.models.generate_content(
                        model=model_name,
                        contents="ping",
                        config=types.GenerateContentConfig(max_output_tokens=5)
                    )
                    print(f"[SUCCESS] Conectado com sucesso usando {model_name}!")
                    resolved_model = model_name
                    break
                except Exception as e:
                    err_msg = str(e)
                    # Erro de autenticação (401/403 com erro de chave): aborta imediatamente
                    if "401" in err_msg or "UNAUTHENTICATED" in err_msg or "API key not valid" in err_msg.lower():
                        print(f"[ERROR] Chave API inválida ou não autorizada: {e}")
                        return False, f"Chave API inválida: {e}"
                        
                    # Erro 429 (cota) ou 404 (modelo não suportado/existente): tenta o próximo
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "ResourceExhausted" in err_msg or "quota" in err_msg.lower():
                        print(f"[WARN] Cota excedida para {model_name}. Tentando modelo alternativo...")
                    else:
                        print(f"[INFO] Modelo {model_name} indisponível ou não suportado (Erro: {err_msg}). Tentando alternativo...")
                    continue
            
            if not resolved_model:
                return False, "Falha na conexão: Cota excedida (429) em todos os modelos candidatos."

            # Tenta executar a resposta utilizando retry automático
            self._generate_with_retry(
                client=test_client,
                model=resolved_model,
                contents="Teste rápido. Responda apenas com 'OK'.",
                config=types.GenerateContentConfig(max_output_tokens=10)
            )
            
            self.client = test_client # Atualiza o cliente ativo
            self.model_name = resolved_model # Salva o modelo funcional resolvido
            return True, f"Conexão com Gemini estabelecida usando o modelo '{resolved_model}'!"
        except Exception as e:
            return False, f"Falha na conexão: {e}"

    def load_game_context(self, game_id: str) -> str:
        """
        Lê e consolida todos os arquivos de contexto de um jogo específico (Genshin, HSR, ZZZ).
        Retorna uma string consolidada de Markdown.
        """
        game_id = game_id.lower().strip()
        if game_id == "todos":
            # Consolida dados de todos os jogos
            contexts = []
            for g in ["genshin", "hsr", "zzz"]:
                contexts.append(self.load_game_context(g))
            return "\n\n=========================================\n\n".join(contexts)
            
        lines = []
        lines.append(f"# CONTEXTO DO JOGO: {game_id.upper()}")
        
        # 1. Roster
        roster_path = f"{game_id}/roster_{game_id}.md"
        if os.path.exists(roster_path):
            try:
                with open(roster_path, "r", encoding="utf-8") as f:
                    lines.append("## INFORMAÇÕES DO ROSTER DO JOGADOR")
                    lines.append(f.read())
            except Exception as e:
                print(f"Erro ao ler roster de {game_id}: {e}")
                
        # 2. Meta/Tier List
        meta_filename = "meta_kqm_genshin.md" if game_id == "genshin" else f"meta_endgame_{game_id}.md"
        meta_path = f"{game_id}/{meta_filename}"
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    lines.append("## INFORMAÇÕES DE METAGAME E TIER LIST")
                    lines.append(f.read())
            except Exception as e:
                print(f"Erro ao ler meta de {game_id}: {e}")
                
        # 3. Guias de Personagens (Bundled ou Individuais)
        bundled_path = f"{game_id}/todos_os_guias_{game_id}.md"
        if os.path.exists(bundled_path):
            try:
                with open(bundled_path, "r", encoding="utf-8") as f:
                    lines.append("## DETALHES DE GUIAS DE PERSONAGENS")
                    # Limita a leitura a 1.2M de caracteres para otimização de memória
                    lines.append(f.read(1200000))
            except Exception as e:
                print(f"Erro ao ler guias consolidados de {game_id}: {e}")
        else:
            guias_dir = f"{game_id}/guias"
            if os.path.exists(guias_dir) and os.path.isdir(guias_dir):
                lines.append("## DETALHES DE GUIAS INDIVIDUAIS DE PERSONAGENS")
                count = 0
                for file in os.listdir(guias_dir):
                    if file.endswith(".md") and count < 15:  # Pega até 15 guias
                        try:
                            filepath = os.path.join(guias_dir, file)
                            with open(filepath, "r", encoding="utf-8") as f:
                                lines.append(f"### Guia: {file}")
                                lines.append(f.read(80000))
                            count += 1
                        except Exception as e:
                            print(f"Erro ao ler guia {file}: {e}")
                            
        return "\n\n".join(lines)

    def ask_assistant(self, query: str, game_id: str, history: list) -> str:
        """
        Envia a mensagem do usuário ao Gemini com o contexto do jogo e histórico da conversa.
        `history` deve ser uma lista de dicionários contendo {"role": "user"|"model", "text": str}.
        """
        if not self.client:
            return "Erro: Chave API do Gemini não configurada ou inválida. Por favor, configure e teste a chave na aba Configurações."
            
        try:
            # 1. Carrega contexto do(s) jogo(s) selecionado(s)
            context_text = self.load_game_context(game_id)
            
            # 2. Constrói instrução de sistema injetando o contexto RAG
            full_system_instruction = SYSTEM_INSTRUCTION
            if context_text.strip():
                full_system_instruction += "\n\n## CONTEXTO DE DADOS LOCAIS DO JOGADOR E GUIAS:\n" + context_text
                
            # 3. Formata histórico para a API do Gemini
            contents = []
            for msg in history:
                role = msg["role"]
                role_mapped = "model" if role in ["assistant", "model"] else "user"
                contents.append(
                    types.Content(
                        role=role_mapped,
                        parts=[types.Part.from_text(text=msg["text"])]
                    )
                )
                
            # Adiciona a mensagem atual
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=query)]
                )
            )
            
            # 4. Configura e chama o modelo utilizando retry automático
            config = types.GenerateContentConfig(
                system_instruction=full_system_instruction,
                temperature=0.7
            )
            
            response_text = self._generate_with_retry(
                client=self.client,
                model=self.model_name,
                contents=contents,
                config=config
            )
            
            return response_text
            
        except Exception as e:
            return f"Erro ao gerar resposta do assistente Gemini: {e}"
