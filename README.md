# HoYo AI Assistant (Groq RAG Local)

Uma ferramenta de desktop moderna com interface gráfica premium desenvolvida em Python (**CustomTkinter**) projetada para extrair rosters de jogo e recordes de Endgames via HoYoLAB, raspar guias analíticos de builds, tier lists e estatísticas do meta (via BeautifulSoup/Requests), e rodar um **Assistente de Chat IA com RAG local integrado** usando a incrível e rápida API da Groq (Llama-3).

O principal objetivo deste projeto é centralizar e processar o roster da sua conta HoYoverse junto com as fontes mais confiáveis de guias (KeqingMains, Prydwen, Game8), fornecendo um assistente RAG local completo para atuar como seu 'Coach de Endgame', recomendando composições de equipes, avaliando suas builds e ajudando com o meta atual do jogo.

---

## 🛠️ Tecnologias Utilizadas

- **Interface Gráfica:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (Aparência Dark Premium)
- **Modelos de IA e RAG:** Integração oficial com a `groq` utilizando os modelos rápidos da família Llama-3.
- **API HoYoLAB:** [genshin.py](https://github.com/seriaati/genshin.py).
- **Raspagem de Dados (Scraping):** BeautifulSoup4 & Requests (com cabeçalhos realistas anti-bloqueio).
- **Concorrência:** Multi-threading em Python (evita o travamento da interface do CustomTkinter).

---

## 📂 Estrutura do Projeto

- `main.py`: Ponto de entrada que inicia o loop principal da GUI.
- `gui.py`: Gerenciamento e design do layout da interface, console de logs em tempo real, abas de ajuda e orquestração de threads.
- `groq_rag.py`: Módulo RAG que carrega chaves, consolida e indexa dinamicamente arquivos Markdown locais como contexto para a API da Groq (Coach de Endgame).
- `auth.py`: Autenticação via navegador do Playwright para capturar os cookies oficiais da sua conta HoYoLAB de forma automatizada.
- `extractor.py` & `endgame_extractor.py`: Extratores integrados utilizando a API do `genshin.py` para obter dados detalhados do perfil de jogo (Personagens ativos, níveis, constelações e extração de todos os Nodes do Endgame como MoC, Shiyu e Abismo).
- `scraper_kqm.py`, `scraper_genshin_meta.py`: Raspadores de meta para Genshin Impact (KQM e Game8).
- `scraper_prydwen.py`, `scraper_meta.py`: Raspadores de meta para Honkai: Star Rail (Prydwen).
- `scraper_zzz.py`: Raspadores de meta para Zenless Zone Zero (Prydwen).

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
- **Roster, Agentes & Endgame:** Extrai nível de Inter-nó, conquistas, detalhes de agentes obtidos e progressão de Defesa Shiyu salvando em `zzz/roster_zzz.md`.
- **Guias & Meta:** Raspa guias individuais e compila em `zzz/meta_endgame_zzz.md`. Consolida em `zzz/todos_os_guias_zzz.md`.

### 🟢 Genshin Impact
- **Roster, Personagens & Endgame:** Extrai nível de Aventura, atributos consolidados e os inimigos e times utilizados no último piso do Abismo Espiral e Teatro Imaginário em `genshin/roster_genshin.md`.
- **Guias & Meta:** Raspa guias do KeqingMains e Tier Lists do Game8.

### 🟣 Honkai: Star Rail (HSR)
- **Roster, Personagens & Endgame:** Extrai nível de Desbravamento, status de relíquias/Eidolons e todos os Times, Nós (incluindo o Node 3) e Pontuações do Caos da Memória, Ficção Pura e Sombra Apocalíptica em `hsr/roster_hsr.md`.
- **Guias & Meta:** Raspa guias do Prydwen e compila as estatísticas.

---

## ⚙️ Painel do Assistente IA RAG e Configurações

1. **Credenciais HoYoLAB:** Autenticação automática via botão na interface, salvando os cookies locais em `cookies.json`.
2. **Chave API Groq:** Configure sua `GROQ_API_KEY` na aba de Configurações globais de forma mascarada. O sistema valida a conexão salvando em `config.json`.
3. **Alternativa Google NotebookLM:** O uso da API interna é totalmente opcional! Se preferir, upe os arquivos `.md` gerados na sua pasta diretamente no [NotebookLM do Google](https://notebooklm.google.com/) para atuar como RAG!

---

## 🔒 Segurança e Privacidade
Todos os dados sensíveis como cookies do HoYoLAB (`cookies.json`), chaves de API (`config.json`) e base de guias raspadas são armazenados **exclusivamente localmente** na sua máquina. Nenhuma telemetria é enviada para fora do seu PC a não ser as requisições primárias oficiais paras as APIs (HoYoLAB e Groq).
