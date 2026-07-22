# 🤖 Cabeça de Droid (HoYo AI Assistant & Local RAG)

Uma ferramenta local moderna com interface gráfica **Web Premium** desenvolvida em **HTML5, CSS3, Vanilla JS** e servida por um backend local em Python (**FastAPI**). 

> [!NOTE]
> **Sobre o nome:** "Cabeça de Droid" é uma brincadeira e uma leve referência a Honkai: Star Rail — especificamente como a Herta carinhosamente chama o **Aeon Nous** (o Aeon da Erudição), que na lore é um supercomputador astral gigante que desenvolveu uma Inteligência Artificial Geral/Superinteligente (ASI) e ascendeu à divindade. A logo do projeto é justamente inspirada nessa grande inteligência robótica!

O assistente foi projetado para sincronizar rosters de personagens e recordes de Endgames via HoYoLAB, coletar guias analíticos de builds, tier lists e estatísticas do meta (KeqingMains, Prydwen, Game8), e rodar um **Assistente de Chat IA com RAG local integrado** usando a API da Groq ou modelos locais.

---

## 🌟 Principais Recursos e Interface (UI/UX)

- **📊 Mini-Dashboards da Conta:** Exibição em tempo real de estatísticas do jogador (UID, Nível da Conta, Total de Personagens e Personagens 5★/Rank S) no topo da tela de cada jogo.
- **📁 Interface Web Premium (Glassmorphism)**: Painel escuro elegante com tons correspondentes de cada jogo (ZZZ, Genshin, HSR) com efeitos de vidro fosco, transições fluidas e layout responsivo.
- **⚡ Status & Barra de Progresso Real (Logs em Tempo Real):** Barra de progresso percentual e terminal retrátil integrado para acompanhar os logs de raspagem e downloads de imagens linha por linha.
- **🗡️ Inspetor de Builds Avançado (Sidebar)**: Ao clicar nos cards dos personagens, uma barra lateral se expande exibindo a arma equipada, conjuntos de relíquias ativos, status finais consolidados e detalhes peça-a-peça de substatus com ícones originais.
- **🤖 Assistente de Chat IA com RAG**: Chat interativo inteligente integrado ao RAG local (Llama 3.3) que já conhece seu Roster e guias de meta.
- **🔑 Login Automático HoYoLAB**: Painel de login facilitado que usa Playwright para capturar os cookies de sessão de forma segura.

---

## 🛠️ Tecnologias Utilizadas

- **Servidor & Backend:** [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) (Python)
- **Interface Gráfica (Frontend):** HTML5, CSS3 (Vanilla) e JavaScript Puro (Vanilla) - *Sem dependências de Node.js ou compilações externas*.
- **Modelos de IA e RAG:** Integração oficial com a `groq` (Llama 3.3 70B Versatile).
- **API HoYoLAB:** [genshin.py](https://github.com/seriaati/genshin.py) com suporte a Endgames estendidos (3 times no MoC / Shiyu / Abismo).
- **Coleta de Dados:** BeautifulSoup4 & Requests HTTP resilientes com estratégias de retry automático.
- **Autenticação:** [Playwright](https://playwright.dev/) para captura automatizada e segura de cookies HoYoLAB.

---

## 📂 Estrutura do Projeto

- `main.py`: Ponto de entrada unificado que sobe o servidor FastAPI e abre o navegador automaticamente.
- `server.py`: Servidor FastAPI com as rotas estáticas e APIs REST de sincronização, chat RAG e configurações.
- `static/`: Diretório do frontend contendo `index.html`, `style.css` e `app.js`.
- `assets/`: Imagens estáticas locais (ícones dos jogos, banners) e pastas onde são salvos os downloads em cache.
- `groq_rag.py`: Módulo RAG que consolida e indexa dinamicamente arquivos Markdown locais como contexto para a IA da Groq.
- `auth.py`: Autenticação via navegador do Playwright para capturar os cookies oficiais da sua conta HoYoLAB.
- `extractor.py` & `endgame_extractor.py`: Extratores de Roster e Endgames da API do HoYoLAB.
- `scraper_kqm.py`, `scraper_genshin_meta.py`: Módulos de sincronização de guias e meta para Genshin Impact (KQM e Game8).
- `scraper_prydwen.py`, `scraper_meta.py`: Módulos de sincronização para Honkai: Star Rail (Prydwen).
- `scraper_zzz.py`: Módulos de sincronização para Zenless Zone Zero (Prydwen).

---

## 🚀 Instalação e Execução (Desenvolvimento)

### 1. Criar Ambiente Virtual e Instalar Dependências
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Instalar o Navegador do Playwright
```bash
playwright install chromium
```

### 3. Executar o Aplicativo
```bash
python main.py
```
O aplicativo abrirá automaticamente o navegador padrão no endereço: **`http://127.0.0.1:8000`**.

---

## 🔒 Segurança e Privacidade
Todos os cookies (`cookies.json`), chaves de API (`config.json`) e arquivos markdown gerados são armazenados **exclusivamente no seu computador**. O app é 100% user-level e não requer privilégios de Administrador no Windows.
