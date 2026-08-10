import os
import json
import time
from groq import Groq
import groq

class GroqRAG:
    def __init__(self, api_key: str = None):
        """
        Inicializa o assistente Groq RAG.
        Carrega a chave do argumento, arquivo config.json ou variável de ambiente.
        """
        self.api_key = api_key
        
        # Tenta carregar do config.json se não fornecida por parâmetro
        if not self.api_key:
            config_path = "config.json"
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                        # Busca por groq_api_key e faz fallback para gemini_api_key para facilitar migração
                        self.api_key = config.get("groq_api_key") or config.get("gemini_api_key")
                except Exception as e:
                    print(f"[WARN] Erro ao ler config.json no GroqRAG: {e}")
                    
        # Tenta carregar da variável de ambiente
        if not self.api_key:
            self.api_key = os.environ.get("GROQ_API_KEY")
            
        self.client = None
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"[ERROR] Erro ao instanciar o cliente Groq: {e}")

    def test_connection(self) -> tuple[bool, str]:
        """
        Testa a conexão com a API da Groq fazendo uma chamada simples.
        Retorna uma tupla (sucesso: bool, mensagem: str).
        """
        if not self.api_key:
            return False, "Chave API não configurada. Configure e salve a chave nas Configurações."
            
        try:
            # Garante que o cliente esteja instanciado com a chave fornecida
            test_client = Groq(api_key=self.api_key)
            
            # Executa uma chamada rápida de teste
            completion = test_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": "ping"}
                ],
                max_tokens=5,
                temperature=0.0
            )
            
            if completion and completion.choices:
                self.client = test_client # Atualiza o cliente ativo
                return True, "Conexão com a Groq estabelecida com sucesso!"
            else:
                return False, "A API da Groq retornou uma resposta sem conteúdo."
                
        except (groq.APIStatusError, groq.APIConnectionError, groq.APIError, groq.RateLimitError) as e:
            err_msg = f"Erro na API Groq: {e.message if hasattr(e, 'message') else str(e)}"
            print(f"[ERROR] Falha de conexão: {err_msg}")
            return False, err_msg
        except Exception as e:
            err_msg = f"Erro inesperado de conexão: {str(e)}"
            print(f"[ERROR] Falha inesperada: {err_msg}")
            return False, err_msg

    def load_game_context(self, game_id: str, query: str = None) -> str:
        """
        Lê e consolida os arquivos de contexto relevantes ao jogo e à pergunta do usuário,
        mantendo o tamanho estritamente dentro dos limites da cota básica da Groq (máx 6000 tokens).
        """
        game_id = game_id.lower().strip()
        
        # Define os limites de caracteres (orçamento de tokens) para evitar estouro de limite da API
        if game_id == "todos":
            # Limites ultra-conservadores para consolidar todos os 3 jogos sem truncar
            roster_limit = 1800
            meta_limit = 1200
            guide_limit = 1800
            
            contexts = []
            for g in ["genshin", "hsr", "zzz"]:
                # Chamada interna para cada jogo passando limites customizados
                contexts.append(self._load_single_game_context(g, query, roster_limit, meta_limit, guide_limit))
            return "\n\n=========================================\n\n".join(contexts)
        else:
            # Limites mais amplos para um jogo individual
            return self._load_single_game_context(game_id, query, roster_limit=6000, meta_limit=8000, guide_limit=6000)

    def _load_single_game_context(self, game_id: str, query: str, roster_limit: int, meta_limit: int, guide_limit: int) -> str:
        lines = []
        lines.append(f"# CONTEXTO DO JOGO: {game_id.upper()}")
        
        # 1. Roster do jogador (Otimizado: tabela filtrada para nível >= 70, builds detalhadas sob demanda)
        roster_path = f"{game_id}/roster_{game_id}.md"
        if os.path.exists(roster_path):
            try:
                with open(roster_path, "r", encoding="utf-8") as f:
                    roster_content = f.read()
                    
                # Separa tabela de detalhes das builds
                parts = roster_content.split("## Detalhes de Builds")
                overview = parts[0].strip()
                
                # Filtra a tabela geral para manter apenas personagens com nível >= 70 (reduz o overhead de 4 estrelas de nv baixo)
                filtered_rows = []
                for line in overview.split("\n"):
                    if "|" in line:
                        row_parts = [p.strip() for p in line.split("|")]
                        if len(row_parts) >= 3:
                            level_str = row_parts[2]  # A segunda coluna é o Nível
                            # Se for o cabeçalho ou a linha de separação
                            if level_str == "Nível" or level_str.startswith(":---") or level_str.startswith("---"):
                                filtered_rows.append(line)
                                continue
                            try:
                                level = int(level_str)
                                if level >= 70:
                                    filtered_rows.append(line)
                            except ValueError:
                                # Se não for um número inteiro, mantém
                                filtered_rows.append(line)
                        else:
                            filtered_rows.append(line)
                    else:
                        filtered_rows.append(line)
                
                filtered_overview = "\n".join(filtered_rows)
                lines.append("## INFORMAÇÕES DO ROSTER DO JOGADOR (TABELA DE PERSONAGENS ATIVOS >= NV. 70)")
                lines.append(filtered_overview[:roster_limit])
                
                # Verifica se o usuário pergunta por builds
                is_asking_build = False
                if query:
                    query_lower = query.lower()
                    build_keywords = ["build", "status", "reliquia", "relíquia", "cone", "equip", "status", "equipar", "detalhe", "melhorar", "artefato", "artefatos"]
                    if any(kw in query_lower for kw in build_keywords):
                        is_asking_build = True
                
                # Se estiver perguntando sobre builds, carrega as builds específicas dos personagens mencionados
                if is_asking_build and len(parts) > 1:
                    details = parts[1]
                    build_blocks = details.split("\n\n---\n\n")
                    mentioned_builds = []
                    
                    if query:
                        query_lower = query.lower()
                        for block in build_blocks:
                            if "**Personagem:**" in block:
                                header_line = block.split("\n")[0]
                                char_name = header_line.split("|")[0].replace("**Personagem:**", "").strip().lower()
                                # Se o personagem é mencionado na pergunta
                                if char_name in query_lower or char_name.replace("(a)", "").strip() in query_lower:
                                    mentioned_builds.append(block.strip())
                                    
                    if mentioned_builds:
                        lines.append("## DETALHES DE BUILDS DOS PERSONAGENS SELECIONADOS")
                        lines.append("\n\n---\n\n".join(mentioned_builds))
                    else:
                        # Fallback se não citou personagens específicos: adiciona as primeiras builds como amostra
                        lines.append("## DETALHES DE BUILDS (AMOSTRA)")
                        lines.append("\n\n---\n\n".join(build_blocks[:2]))
            except Exception as e:
                print(f"[WARN] Erro ao ler roster de {game_id}: {e}")
                
        # 2. Meta/Tier List
        meta_filename = f"meta_endgame_{game_id}.md"
        meta_path = f"{game_id}/{meta_filename}"
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    lines.append("## INFORMAÇÕES DE METAGAME E TIER LIST")
                    lines.append(f.read(meta_limit))
            except Exception as e:
                print(f"[WARN] Erro ao ler meta de {game_id}: {e}")
                
        # 3. Guias de Personagens (Busca inteligente e truncamento seguro)
        guias_dir = f"{game_id}/guias"
        loaded_specific_guide = False
        
        # Tenta carregar guias de personagens mencionados na pergunta ou roster ativo
        if query and os.path.exists(guias_dir) and os.path.isdir(guias_dir):
            query_normalized = query.lower()
            
            # A. Tenta carregar guias cujos nomes de arquivos estão na query
            for file in os.listdir(guias_dir):
                if file.endswith(".md"):
                    char_name = file[:-3].replace("_", " ").lower()
                    if char_name in query_normalized or (file[:-3].lower() in query_normalized):
                        try:
                            filepath = os.path.join(guias_dir, file)
                            with open(filepath, "r", encoding="utf-8") as f:
                                lines.append(f"## GUIA DO PERSONAGEM EM FOCO: {char_name.upper()}")
                                lines.append(f.read(guide_limit))
                            loaded_specific_guide = True
                            print(f"[INFO] Guia específico carregado para {char_name} no contexto ({game_id}).")
                        except Exception as e:
                            print(f"[WARN] Erro ao ler guia específico {file}: {e}")
            
            # B. Se não carregou nenhum guia específico e a pergunta for sobre times/comps,
            # busca automaticamente guias dos principais DPSs do meta que o jogador possui no roster
            if not loaded_specific_guide:
                team_keywords = ["time", "times", "comp", "comps", "equipe", "equipes", "sugestões", "melhores"]
                if any(kw in query_normalized for kw in team_keywords):
                    # Principais DPSs do meta de cada jogo
                    meta_chars = []
                    if game_id == "hsr":
                        meta_chars = ["acheron", "firefly", "vaga-lume", "feixiao", "jingliu", "clara", "seele"]
                    elif game_id == "genshin":
                        meta_chars = ["neuvillette", "arlecchino", "alhaitham", "raiden", "hu_tao", "ganyu"]
                    elif game_id == "zzz":
                        meta_chars = ["ellen", "zhu_yuan", "jane_doe", "miyabi", "caesar"]
                        
                    loaded_count = 0
                    for char in meta_chars:
                        # Extrai o texto do roster nas linhas anteriores para verificar posse
                        roster_text = "".join([l for l in lines if "ROSTER" in l or "personagens" in l.lower() or "agentes" in l.lower()])
                        
                        has_char = (char in roster_text.lower())
                        if char == "vaga-lume" and "firefly" in roster_text.lower():
                            has_char = True
                        if char == "firefly" and "vaga-lume" in roster_text.lower():
                            has_char = True
                            
                        if has_char and loaded_count < 2:  # Carrega no máximo 2 guias para economizar tokens
                            filename = f"{char}.md"
                            if char == "vaga-lume" or char == "firefly":
                                filename = "firefly.md"
                                
                            filepath = os.path.join(guias_dir, filename)
                            if os.path.exists(filepath):
                                try:
                                    with open(filepath, "r", encoding="utf-8") as f:
                                        lines.append(f"## GUIA DE PERSONAGEM POSSUÍDO (META DPS): {char.upper()}")
                                        lines.append(f.read(guide_limit))
                                    loaded_specific_guide = True
                                    loaded_count += 1
                                    print(f"[INFO] Guia meta auto-carregado para {char} no contexto ({game_id}).")
                                except Exception as e:
                                    print(f"[WARN] Erro ao ler guia auto-carregado {filename}: {e}")
                            
        if not loaded_specific_guide:
            bundled_path = f"{game_id}/todos_os_guias_{game_id}.md"
            if os.path.exists(bundled_path):
                try:
                    with open(bundled_path, "r", encoding="utf-8") as f:
                        lines.append("## DETALHES GERAIS DE GUIAS (AMOSTRA)")
                        lines.append(f.read(guide_limit))
                except Exception as e:
                    print(f"[WARN] Erro ao ler guias consolidados de {game_id}: {e}")
            elif os.path.exists(guias_dir) and os.path.isdir(guias_dir):
                lines.append("## DETALHES DE GUIAS INDIVIDUAIS DE PERSONAGENS (AMOSTRA)")
                count = 0
                for file in os.listdir(guias_dir):
                    if file.endswith(".md") and count < 1:
                        try:
                            filepath = os.path.join(guias_dir, file)
                            with open(filepath, "r", encoding="utf-8") as f:
                                lines.append(f"### Guia: {file[:-3]}")
                                lines.append(f.read(guide_limit))
                            count += 1
                        except Exception as e:
                            print(f"[WARN] Erro ao ler guia {file}: {e}")
                            
        return "\n\n".join(lines)

    def ask_assistant(self, prompt_usuario: str, contexto_rag: str | list, historico_chat: list = None) -> str:
        """
        Gera resposta utilizando a API da Groq com suporte a RAG, histórico e modelos de fallback.
        
        Parâmetros:
            - prompt_usuario (str): Pergunta do usuário.
            - contexto_rag (str ou list): Dados de contexto para embasar a resposta.
            - historico_chat (opcional): Lista contendo dicionários de histórico.
              Ex: [{"role": "user", "text": "olá"}, {"role": "model", "text": "olá! em que posso ajudar?"}]
              
        Retorna:
            - str: Texto puro da resposta gerada ou mensagem de erro formatada.
        """
        if not self.client:
            return "Erro: Chave API da Groq não configurada ou inválida. Por favor, configure e teste a chave na aba Configurações."

        # 1. Tratar o contexto_rag (pode ser str ou list)
        if isinstance(contexto_rag, list):
            contexto_str = "\n\n".join(contexto_rag)
        else:
            contexto_str = contexto_rag

        # 2. Definir o system prompt persona com o contexto local injetado
        system_prompt = (
            "Você é um assistente especializado nos jogos da HoYoverse (Genshin Impact, Honkai: Star Rail, Zenless Zone Zero). "
            "Responda com base no contexto fornecido e formate em Markdown claro para a interface gráfica.\n\n"
            "Você tem acesso aos recordes de Endgame (Caos da Memória / Abismo Espiral) do jogador. Se o jogador não tiver alcançado as 36 estrelas ou travado em um andar específico, analise os times e as builds fornecidas para dar conselhos táticos: sugira trocas de composição de time para quebrar fraquezas e indique qual personagem precisa de melhoria urgente para passar daquela fase."
        )
        
        if contexto_str.strip():
            system_prompt += f"\n\n## CONTEXTO DE DADOS LOCAIS DO JOGADOR E GUIAS:\n{contexto_str}"

        # Limite de segurança geral rígido para a API da Groq no plano básico/on_demand (Limite de 6000 tokens)
        MAX_SYSTEM_PROMPT_CHARS = 18000  # Aprox. 4.000 tokens
        if len(system_prompt) > MAX_SYSTEM_PROMPT_CHARS:
            print(f"[INFO] Truncando contexto de {len(system_prompt)} para {MAX_SYSTEM_PROMPT_CHARS} caracteres por segurança.")
            system_prompt = system_prompt[:MAX_SYSTEM_PROMPT_CHARS] + "\n\n... (Contexto local truncado por limite de tokens da API) ..."

        # 3. Formatar o histórico e mensagens
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if historico_chat:
            for msg in historico_chat:
                role = msg.get("role")
                # Mapeia roles do front (model/assistant) para o formato esperado pelo SDK
                role_mapped = "assistant" if role in ["model", "assistant"] else "user"
                content = msg.get("text") or msg.get("content", "")
                if content.strip():
                    messages.append({"role": role_mapped, "content": content})

        # Adiciona a mensagem atual
        messages.append({"role": "user", "content": prompt_usuario})

        # 4. Lista de modelos (Principal + Fallbacks em caso de instabilidade)
        modelos = [
            "openai/gpt-oss-120b",
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant"
        ]

        last_exception = None
        for model in modelos:
            try:
                print(f"[INFO] Chamando API da Groq com o modelo: {model}...")
                # Modelos de raciocínio como GPT-OSS funcionam melhor com temperaturas um pouco menores (ex: 0.6)
                temp = 0.1 if "gpt-oss" in model or "deepseek" in model else 0.1
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temp
                )
                if completion and completion.choices:
                    msg = completion.choices[0].message
                    response_text = msg.content
                    if response_text:
                        # Extrai o raciocínio se o modelo o expor como um campo separado (ex: GPT-OSS)
                        reasoning_text = getattr(msg, "reasoning", None) or getattr(msg, "reasoning_content", None)
                        if reasoning_text:
                            model_display = "GPT-OSS 120B" if "gpt-oss" in model else model.split("/")[-1].upper()
                            response_text = f"<details class='think-details'><summary>🧠 Ver Processo de Pensamento ({model_display})</summary><div class='think-content'>{reasoning_text}</div></details>\n\n" + response_text
                        
                        # Fallback para tags de pensamento embutidas no texto (ex: DeepSeek se reativado)
                        elif "<think>" in response_text and "</think>" in response_text:
                            response_text = response_text.replace(
                                "<think>", 
                                "<details class='think-details'><summary>🧠 Ver Processo de Pensamento</summary><div class='think-content'>"
                            ).replace(
                                "</think>", 
                                "</div></details>"
                            )
                        return response_text
                    else:
                        raise Exception("A resposta retornada estava vazia.")
            except (groq.RateLimitError, groq.APIError) as e:
                last_exception = e
                print(f"[WARN] Falha ou Rate Limit com o modelo {model}: {e}. Tentando fallback...")
                continue
            except Exception as e:
                last_exception = e
                print(f"[WARN] Erro inesperado com o modelo {model}: {e}. Tentando fallback...")
                continue

        # Se todos os modelos falharem, trata a última exceção capturada para evitar que o CustomTkinter UI trave
        if last_exception:
            if isinstance(last_exception, groq.RateLimitError):
                error_msg = f"Erro de Limite de Requisições (Rate Limit) na API da Groq: {last_exception}"
            elif isinstance(last_exception, groq.APIError):
                error_msg = f"Erro na API da Groq (APIError): {last_exception}"
            else:
                error_msg = f"Erro inesperado no assistente Groq: {last_exception}"
            print(f"[ERROR] {error_msg}")
            return error_msg

        return "Erro: Não foi possível obter resposta de nenhum modelo da Groq."

    def ask_assistant_stream(self, prompt_usuario: str, contexto_rag: str | list, historico_chat: list = None):
        """
        Gera resposta em formato streaming utilizando a API da Groq.
        Yields strings contendo os tokens gerados.
        """
        if not self.client:
            yield "Erro: Chave API da Groq não configurada ou inválida. Por favor, configure e teste a chave na aba Configurações."
            return

        # 1. Tratar o contexto_rag (pode ser str ou list)
        if isinstance(contexto_rag, list):
            contexto_str = "\n\n".join(contexto_rag)
        else:
            contexto_str = contexto_rag

        # 2. Definir o system prompt persona com o contexto local injetado
        system_prompt = (
            "Você é um assistente especializado nos jogos da HoYoverse (Genshin Impact, Honkai: Star Rail, Zenless Zone Zero). "
            "Responda com base no contexto fornecido e formate em Markdown claro para a interface gráfica.\n\n"
            "Você tem acesso aos recordes de Endgame (Caos da Memória / Abismo Espiral) do jogador. Se o jogador não tiver alcançado as 36 estrelas ou travado em um andar específico, analise os times e as builds fornecidas para dar conselhos táticos: sugira trocas de composição de time para quebrar fraquezas e indique qual personagem precisa de melhoria urgente para passar daquela fase."
        )
        
        if contexto_str.strip():
            system_prompt += f"\n\n## CONTEXTO DE DADOS LOCAIS DO JOGADOR E GUIAS:\n{contexto_str}"

        # Limite de segurança geral rígido para a API da Groq
        MAX_SYSTEM_PROMPT_CHARS = 18000
        if len(system_prompt) > MAX_SYSTEM_PROMPT_CHARS:
            print(f"[INFO] Truncando contexto de {len(system_prompt)} para {MAX_SYSTEM_PROMPT_CHARS} caracteres por segurança.")
            system_prompt = system_prompt[:MAX_SYSTEM_PROMPT_CHARS] + "\n\n... (Contexto local truncado por limite de tokens da API) ..."

        # 3. Formatar o histórico e mensagens
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        if historico_chat:
            for msg in historico_chat:
                role = msg.get("role")
                role_mapped = "assistant" if role in ["model", "assistant"] else "user"
                content = msg.get("text") or msg.get("content", "")
                if content.strip():
                    messages.append({"role": role_mapped, "content": content})

        # Adiciona a mensagem atual
        messages.append({"role": "user", "content": prompt_usuario})

        # 4. Lista de modelos compatíveis com streaming rápido
        modelos = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant"
        ]

        for model in modelos:
            try:
                print(f"[INFO] Iniciando stream com o modelo: {model}...")
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.1,
                    stream=True
                )
                
                # Iterar e retornar tokens em stream
                for chunk in completion:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception as e:
                print(f"[WARN] Falha de streaming com o modelo {model}: {e}. Tentando fallback...")
                continue
        
        yield "Erro: Não foi possível obter resposta de nenhum modelo de streaming da Groq."
