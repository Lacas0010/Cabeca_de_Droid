# HoYo AI Assistant (Gemini RAG Local)

Uma ferramenta de desktop moderna com interface gráfica premium desenvolvida em Python (**CustomTkinter**) projetada para extrair rosters de jogo via HoYoLAB, raspar guias analíticos de builds, tier lists e estatísticas do meta (via BeautifulSoup/Requests), e rodar um **Assistente de Chat IA com RAG local integrado** usando a API oficial do Google Gemini.

O principal objetivo deste projeto é centralizar e processar o roster da sua conta HoYoverse junto com as fontes mais confiáveis de guias (KeqingMains, Prydwen, Game8), fornecendo um assistente RAG local completo para recomendar composições de equipes, builds de artefatos/relíquias e rotações sem precisar enviar dados para plataformas em nuvem externas como o NotebookLM.

---

## 🛠️ Tecnologias Utilizadas

- **Interface Gráfica:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (Aparência Dark Premium)
- **Modelos de IA e RAG:** SDK Oficial `google-genai` com suporte dinâmico e inteligente para os modelos `gemini-1.5-flash`, `gemini-2.0-flash` e `gemini-2.5-flash`.
- **API HoYoLAB:** [genshin.py](https://github.com/thebowja/genshin.py)
- **Raspagem de Dados (Scraping):** BeautifulSoup4 & Requests (com cabeçalhos realistas anti-bloqueio, retentativas exponenciais com backoff e mapeamento PT-BR de aliases).
- **Concorrência:** Multi-threading em Python (evita o travamento da interface do CustomTkinter durante chamadas de rede à API Gemini ou tarefas de scraping).

---

## 📂 Estrutura do Projeto

- `main.py`: Ponto de entrada que inicia o loop principal da GUI.
- `gui.py`: Gerenciamento e design do layout da interface, console de logs em tempo real e orquestração de threads.
- `gemini_rag.py` [Novo]: Módulo RAG que carrega chaves, consolida e indexa dinamicamente arquivos Markdown locais como contexto para a API do Gemini e executa conversas com histórico estruturado.
- `auth.py`: Autenticação via navegador do Playwright para capturar os cookies oficiais da sua conta HoYoLAB de forma automatizada.
- `extractor.py`: Extrator integrado utilizando a API do `genshin.py` para obter dados detalhados do perfil de jogo (UID, personagens ativos, níveis, constelações, etc.).
- `scraper_kqm.py` [Novo]: Raspador resiliente para o **KeqingMains** (Genshin Impact), extraindo guias analíticos detalhados de personagens com suporte dinâmico a Quick Guides.
- `scraper_genshin_meta.py` [Novo]: Raspador analítico para o **Game8** (Genshin Impact), obtendo a Tier List atualizada e relatórios de endgame do Abismo Espiral e Teatro Imaginário.
- `scraper_prydwen.py`: Raspador de guias completos de build de personagens do **Prydwen** (Honkai: Star Rail).
- `scraper_zzz.py`: Raspador de guias completos de agentes, discos de áudio e W-Engines de **Prydwen** (Zenless Zone Zero).
- `scraper_meta.py`: Raspador de Tier Lists e relatórios sazonais de endgame (MoC, PF, AS, AA) do **Prydwen** (Honkai: Star Rail).

---

## 🚀 Instalação e Configuração

### 1. Instalar Dependências
Crie um ambiente virtual e instale os pacotes listados no `requirements.txt`:

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar o ambiente virtual (Windows)
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Instalar o Navegador do Playwright
Para habilitar a captura automática de cookies do HoYoLAB, instale o navegador Chromium gerenciado pelo Playwright:

```bash
playwright install chromium
```

### 3. Executar a Aplicação
Inicie a interface gráfica:

```bash
python main.py
```

---

## 📖 Funcionalidades e Organização de Dados

### 🔵 Zenless Zone Zero (ZZZ)
- **Roster & Agentes:** Extrai nível de Inter-nó, conquistas e detalhes de agentes obtidos salvando em `zzz/roster_zzz.md`.
- **Guias & Meta:** Raspa guias individuais e compila em `zzz/meta_endgame_zzz.md`. Consolida em `zzz/todos_os_guias_zzz.md`.

### 🟢 Genshin Impact
- **Roster & Personagens:** Extrai nível de Aventura, conquistas e atributos consolidados em `genshin/roster_genshin.md`.
- **Guias do KQM:** Raspa guias completos e rápidos do KeqingMains salvando em `genshin/guias/` e compila em `genshin/todos_os_guias_genshin.md`.
- **Meta & Endgame:** Extrai a Tier List Game8 e relatórios de Abismo/Teatro em `genshin/meta_kqm_genshin.md`.

### 🟣 Honkai: Star Rail (HSR)
- **Roster & Personagens:** Extrai nível de Desbravamento e status de relíquias e Eidolons salvando em `hsr/roster_hsr.md`.
- **Guias & Meta:** Raspa guias do Prydwen e compila as estatísticas do MoC/PF/AS/AA em `hsr/meta_endgame_hsr.md` e `hsr/todos_os_guias_hsr.md`.

---

## ⚙️ Painel do Assistente IA RAG e Configurações

1. **Credenciais HoYoLAB:** Autenticação automática ou manual salvando os cookies locais em `cookies.json`.
2. **Chave API do Google Gemini:** Configure sua `GEMINI_API_KEY` na aba de Configurações globais de forma mascarada. O sistema valida a conexão salvando em `config.json`.
3. **Resolução de Modelos e Fallbacks:** O RAG tenta usar `gemini-1.5-flash`, `gemini-2.0-flash` ou `gemini-flash-latest`. Se houver limitações ou cotas excedidas, ele gerencia automaticamente sem travar a UI.
4. **Chat IA Integrado:**
   - Filtre o contexto por aba (`[ Todos ]`, `[ ZZZ ]`, `[ Genshin ]`, `[ HSR ]`).
   - O chat carrega o roster correspondente e os guias consolidados locais automaticamente para responder perguntas ultra-específicas de forma inteligente.
   - Tratamento de cotas integrado: caso a chave do plano gratuito atinja a cota de requisições por minuto (erro 429), o RAG aguarda 12 segundos e repete a chamada sem derrubar a conversa.

---

## 🔒 Segurança e Privacidade
Todos os dados sensíveis como cookies do HoYoLAB (`cookies.json`), configurações locais (`config.json`) e base de guias raspadas são armazenados **exclusivamente localmente** na máquina do usuário.
