# 🤖 Cabeça de Droid (HoYo AI Assistant & Local RAG)

Uma ferramenta local moderna com interface gráfica **Web Premium** desenvolvida em **HTML5, CSS3, Vanilla JS** e servida por um backend local em Python (**FastAPI**). 

> [!NOTE]
> **Sobre o nome:** "Cabeça de Droid" é uma brincadeira e uma leve referência a Honkai: Star Rail — especificamente como a Herta carinhosamente chama o **Aeon Nous** (o Aeon da Erudição), que na lore é um supercomputador astral gigante que desenvolveu uma Inteligência Artificial Geral/Superinteligente (ASI) e ascendeu à divindade. A logo do projeto é justamente inspirada nessa grande inteligência robótica!

O assistente foi projetado para sincronizar rosters de personagens e recordes de Endgames via HoYoLAB, coletar guias analíticos de builds, tier lists e estatísticas do meta (KeqingMains, Prydwen, Game8), e rodar um **Assistente de Chat IA com RAG local integrado** usando a API da Groq ou modelos locais.

---

## 🌟 Principais Recursos e Interface (UI/UX)
 
- **📊 Mini-Dashboards da Conta:** Exibição em tempo real de estatísticas do jogador (UID, Nível da Conta, Total de Personagens e Personagens 5★/Rank S) no topo da tela de cada jogo.
- **📁 Interface Web Premium (Glassmorphism)**: Painel escuro elegante com tons correspondentes de cada jogo (ZZZ, Genshin, HSR) com efeitos de vidro fosco, transições fluidas e layout responsivo.
- **🎨 Interface Visual com Ícones (Font Awesome)**: Enriquecida com ícones dinâmicos modernos integrados que melhoram significativamente o visual e a interatividade dos menus e abas.
- **⚡ Status & Barra de Progresso Real (Logs em Tempo Real):** Barra de progresso percentual e terminal retrátil integrado para acompanhar os logs de raspagem e downloads de imagens linha por linha.
- **🗡️ Inspetor de Builds & Comparador Meta Avançado (Sidebar)**: Exibe a arma equipada, conjuntos de relíquias ativos, status finais consolidados e detalhes de substatus com ícones originais. Ao clicar em "Comparador Meta", exibe uma tabela de comparação lado a lado contra as metas ideais extraídas dos guias, destacando correspondências em verde e desvios em vermelho.
- **🌐 Dicionário de Tradução Inteligente Local (`traducoes.json`):** Mapeia armas, conjuntos de relíquias, discos e atributos de Inglês para Português (PT-BR) de forma local e extremamente veloz, permitindo match nativo contra os nomes oficiais do jogo.
- **🏷️ Peças Exclusivas por Jogo:** Mapeamento específico e exato para as peças de cada jogo (Cabeça/Mãos/Corpo/Bota/Esfera/Corda no HSR; Flor/Pena/Areia/Copo/Tiara no Genshin; Discos 1 a 6 no ZZZ).
- **📊 Comparador de Atributos Finais (Endgame Stats):** Analisa e compara os atributos de combate totais do jogador contra os valores ideais (nativos do ZZZ, ou calculados dinamicamente via gerador inteligente de benchmarks baseado em escala para HSR e Genshin).
- **👥 Resolução Inteligente Multi-Contas**: Seleção automática inteligente caso o usuário possua mais de uma conta vinculada por jogo, mantendo e exibindo no cache as informações da conta de maior nível.
- **🔋 Monitoramento Preciso de Energia (Daily Notes)**: Acompanhamento em tempo real da Bateria (ZZZ) e Resina (Genshin/HSR), com cálculo otimizado usando segundos restantes precisos para carga completa no ZZZ.
- **🔄 Mecanismo de Fallback para Visão Geral (Overview)**: Sincronização inteligente dos mini-dashboards que mescla registros de banco SQLite locais com caches em Markdown e JSON, servindo dados mesmo em caso de falha temporária na rede.
- **🎭 Suporte Dinâmico a Skins/Costumes**: Detecção de roupas cosméticas ativas equipadas no jogo. No HSR e ZZZ, renderiza os avatares de skin dinâmicos enviados pela API. No Genshin Impact, resolve e mapeia automaticamente os IDs de vestimentas de gacha/evento para suas respectivas URLs quadradas de rosto do Enka.Network, impedindo distorções de splash arts esticadas nos cards.
- **🤖 Assistente de Chat IA com RAG**: Chat interativo inteligente integrado ao RAG local (Llama 3.3) que já conhece seu Roster e guias de meta.
- **🔑 Login Automático HoYoLAB**: Painel de login facilitado que usa Playwright para capturar os cookies de sessão de forma segura.


---

## ⚙️ Como Funciona o Sistema

O **Cabeça de Droid** opera como um ecossistema local híbrido composto por três pilares principais:

### 1. Coleta e Sincronização de Dados
* **API HoYoLAB (Python):** Utiliza a biblioteca `genshin.py` para consultar as APIs oficiais do HoYoLAB a partir dos cookies do usuário. Ele extrai informações do perfil ativo, lista de personagens, equipamentos, substatus de artefatos/discos/relíquias e estatísticas de progresso nos modos endgame (Abismo Espiral, Salão Esquecido/Pura Ficção/Apocalipse Sombrio e Defesa Shiyu).
* **Web Scraping Dinâmico:** Raspadores dedicados em Python vasculham guias meta e tier lists atualizadas (como *Prydwen* e *KeqingMains*), salvando esses benchmarks ideais localmente.

### 2. Armazenamento, Metadados Indexados por ID e Tradução Local
* **Banco SQLite (`hoyo_app.db`):** Os dados brutos das contas e builds são salvos localmente em um banco SQLite relacional com suporte a `char_id`, permitindo velocidade instantânea no carregamento e persistência das contas sincronizadas.
* **Arquivos Meta Estruturados por ID (`meta_data_<jogo>.json`):** Arquivos JSON onde a chave primária de cada personagem é o seu **Character ID numérico oficial** (ex: `"1310"` para Firefly, `"10000047"` para Kazuha). Em Honkai: Star Rail e Zenless Zone Zero, estes arquivos são gerados a partir do parse dos guias locais. Em Genshin Impact, o script `game8_scraper.py` realiza a extração automatizada via Game8, garantindo 100% de precisão nos main stats e substats.
* **Documentos Markdown de Cache:** O roster estruturado e os guias analíticos de cada jogo são exportados em arquivos markdown dentro de diretórios correspondentes (`/genshin`, `/hsr`, `/zzz`), servindo como contexto RAG para os LLMs.
* **Dicionário de Tradução (`traducoes.json`):** Mapeia de forma extremamente veloz os termos de atributos, armas e artefatos de Inglês para Português (PT-BR), fornecendo uma interface localizada uniforme.

### 3. Assistente de Chat Inteligente (RAG Local)
* Quando você faz uma pergunta na aba de Chat, a inteligência local entra em ação usando a classe `GroqRAG` (`groq_rag.py`):
  * **Interseção Inteligente:** O sistema varre sua pergunta em busca de nomes de personagens ou termos relacionados a builds e times.
  * **Ingestão Otimizada:** Ele lê os arquivos Markdown locais do seu roster, filtrando apenas personagens ativos (nível 70+) e carregando apenas o guia específico (`/guias/<personagem>.md`) e a build do personagem que você perguntou. Isso otimiza drasticamente os limites de tokens da API da Groq/Gemini.
  * **Prompt Enriquecido:** A pergunta do usuário é encapsulada em um superprompt contendo a sua build real + o benchmark ideal do metagame + a tier list. O LLM (Llama 3.3 ou Gemini) responde então com um nível de precisão cirúrgico focado na sua conta de jogo real.

## 📊 Sistema de Pontuação de Equipamentos & Cálculo de Ascensão

O **Cabeça de Droid** possui mecanismos matemáticos locais integrados para ajudar o jogador a gerenciar recursos e otimizar builds:

### 1. Calculadora de Pontuação de Relíquias (Relic / Disc Scorer Agnostic por ID)
O sistema opera de forma 100% agnóstica de idioma usando a chave primária `char_id`:
* **Matriz de Pesos Dinâmicos por ID:** A função `extract_weights_from_guide` busca diretamente no cache `meta_data_<jogo>.json` pela chave do `char_id` (ex: `"1310"`) e recupera a prioridade sanitizada pela whitelist (`VALID_SUBSTATS`), atribuindo pesos decrescentes de `0.0` a `1.0`.
* **Cálculo por Roll Value (RV):** Em vez de avaliar valores brutos, o motor calcula o RV de cada substatus dividindo seu valor real pelo **valor máximo de um roll perfeito de 5★ / S-Rank** para aquele jogo específico (Genshin, HSR ou ZZZ):
  $$RV = \frac{\text{Valor Real}}{\text{Valor Máximo do Roll}}$$
  O score final da peça é a soma ponderada de todos os RVs dos substatus:
  $$\text{Score Real} = \sum (RV_i \times \text{Peso}_i)$$
* **Main Stat Forgiveness (Compensação de Main Stat):** Uma relíquia não pode ter seu Main Stat repetido nos substatus. O motor compensa isso: se o Main Stat da peça for útil (peso > 0) e não for um slot de Main Stat fixo (como Flor/Pena no Genshin ou Cabeça/Mão no HSR), esse atributo é removido da lista de possíveis substatus ao calcular a pontuação máxima teórica da peça. O teto máximo (denominador) é reduzido de forma justa, garantindo notas excelentes para botas de velocidade ou cordas de break effect.

As peças que atingem o grau máximo **SSS** (scores elevados de substatus perfeitos com $\ge 90\%$ do teto compensado) recebem um destaque visual pulsante na interface.

### 2. Calculadora de Materiais de Ascensão
Integrada diretamente no painel de inspeção de personagens, ela estima a quantidade total de recursos necessários para elevar o nível de um personagem da sua conta até o nível de destino selecionado (ex: Nível 80 no HSR/ZZZ, Nível 90 no Genshin).
O cálculo avalia a diferença acumulada e retorna o checklist detalhado de:
* Livros de XP (e estimativa de quantos livros roxos de 20k XP farmar).
* Moeda do jogo (Mora, Créditos ou Dennys).
* Quantidade exata de materiais de quebra de limite (Itens de Chefes mundiais).

---

## 🛠️ Tecnologias Utilizadas


- **Servidor & Backend:** [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) (Python)
- **Interface Gráfica (Frontend):** HTML5, CSS3 (Vanilla) com ícones da biblioteca [Font Awesome](https://fontawesome.com/) e JavaScript Puro (Vanilla) - *Sem dependências de Node.js ou compilações externas*.
- **Modelos de IA e RAG:** Integração oficial com a `groq` (Llama 3.3 70B Versatile) e suporte para chaves Gemini via fallback (`gemini_api_key`) local.
- **API HoYoLAB:** [genshin.py](https://github.com/seriaati/genshin.py) com suporte a Endgames estendidos (3 times no MoC / Shiyu / Abismo).
- **Coleta de Dados:** BeautifulSoup4, Playwright Async API & Requests HTTP com estratégias de retry automático.
- **Autenticação:** [Playwright](https://playwright.dev/) para captura automatizada e segura de cookies HoYoLAB.
- **Compilação do Executável:** [PyInstaller](https://pyinstaller.org/) configurado para empacotamento local no Windows.


---

## 📂 Estrutura do Projeto

- `main.py`: Ponto de entrada unificado que sobe o servidor FastAPI e abre o navegador automaticamente.
- `server.py`: Servidor FastAPI com as rotas estáticas e APIs REST de sincronização, chat RAG e configurações.
- `build_calculator.py`: Motor matemático de scoring (RV, Main Stat Forgiveness), extração de pesos por ID e fonte mestre de IDs.
- `game8_scraper.py` & `scraper_game8.py`: Raspador automatizado de builds e metadados de Genshin Impact via Game8.
- `static/`: Diretório do frontend contendo `index.html`, `style.css` e `app.js`.
- `assets/`: Imagens estáticas locais (ícones dos jogos, banners) e pastas onde são salvos os downloads em cache.
- `groq_rag.py`: Módulo RAG que consolida e indexa dinamicamente arquivos Markdown locais como contexto para a IA da Groq.
- `auth.py`: Autenticação via navegador do Playwright para capturar os cookies oficiais da sua conta HoYoLAB.
- `extractor.py` & `endgame_extractor.py`: Extratores de Roster e Endgames da API do HoYoLAB com suporte a `char_id`.
- `scraper_kqm.py`, `scraper_genshin_meta.py`: Módulos de sincronização de guias e meta para Genshin Impact (KQM e Game8).
- `scraper_prydwen.py`, `scraper_meta.py`: Módulos de sincronização para Honkai: Star Rail (Prydwen).
- `scraper_zzz.py`: Módulos de sincronização para Zenless Zone Zero (Prydwen).

---

## 🚀 Instalação e Execução (Passo a Passo Detalhado)

Siga as instruções abaixo para preparar o ambiente e colocar o **Cabeça de Droid** para rodar localmente.

### 📋 Pré-requisitos
* **Python 3.10 ou superior** instalado no seu sistema.
* **Git** (opcional, para controle de versão).

---

### 1. Preparar o Ambiente Virtual (venv) e Instalar Dependências

O ambiente virtual isola as dependências do projeto para evitar conflitos com outros pacotes do Python.

1. Abra o terminal (PowerShell, CMD ou terminal do Linux/macOS) na pasta raiz do projeto.
2. Crie o ambiente virtual executando:
   ```bash
   python -m venv .venv
   ```
3. Ative o ambiente virtual conforme seu sistema operacional:
   * **Windows (PowerShell):**
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
     *(Se receber um erro de política de execução, execute `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` no terminal antes)*
   * **Windows (CMD):**
     ```cmd
     .venv\Scripts\activate.bat
     ```
   * **Linux / macOS:**
     ```bash
     source .venv/bin/activate
     ```
4. Atualize o gerenciador de pacotes (`pip`) e instale todas as dependências do arquivo `requirements.txt`:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

### 2. Instalar o Navegador Chromium do Playwright

O Playwright é utilizado para simular a janela do navegador e capturar os cookies do HoYoLAB automaticamente de forma segura durante o login.

Execute o comando abaixo para baixar a versão correta do Chromium usada pelo Playwright:
```bash
playwright install chromium
```

> [!NOTE]  
> A aplicação possui um mecanismo inteligente (`setup_playwright` no `main.py`) que tenta instalar o Chromium em segundo plano no primeiro início se ele não for detectado. No entanto, é altamente recomendado rodar o comando manual acima para garantir que não haja erros de conexão silenciosos.

---

### 3. Executar o Aplicativo

Com o ambiente virtual ativo e as dependências instaladas, inicialize o servidor local:
```bash
python main.py
```

**O que acontece a partir daqui:**
1. O backend inicia o banco de dados SQLite local `hoyo_app.db` automaticamente se for a primeira execução.
2. O servidor local **FastAPI + Uvicorn** é iniciado em `http://127.0.0.1:8000`.
3. O script aguarda 3.5 segundos e **abre automaticamente** o seu navegador de internet padrão nesse endereço.
4. Para fechar o programa, volte ao terminal e pressione `Ctrl + C`.

---

### 📦 4. Compilar para Executável (Opcional - Windows)

Se você deseja gerar um único executável portátil (`.exe`) que possa rodar com apenas dois cliques no Windows (sem depender da instalação do Python ou terminal aberto), você pode compilar a aplicação usando o [PyInstaller](https://pyinstaller.org/):

1. Com o ambiente virtual ativado, rode:
   ```bash
   pyinstaller main.spec
   ```
2. Após o término do processo, você encontrará a pasta `build/` e a pasta `dist/`.
3. O executável standalone compilado estará localizado dentro da pasta `dist/` (`dist/main.exe`).
4. Os recursos estáticos (como a interface web em `/static` e o ícone do robô em `/assets`) já são empacotados automaticamente para dentro do binário.


---

## 🔑 Configuração de Credenciais

Para o funcionamento completo de todas as funcionalidades da aplicação (sincronização do roster de personagens via HoYoLAB e Assistente de Chat IA com RAG), é necessário configurar suas credenciais. Isso pode ser feito de três maneiras:

### 1. Pela Interface Web (Recomendado)
Após iniciar o aplicativo com `python main.py` e acessar o endereço local no navegador, navegue até a seção de **Configurações**. Lá você poderá colar sua chave da Groq/Gemini e inserir seus cookies do HoYoLAB com facilidade. Os dados são salvos localmente de forma automática.

### 2. Manualmente via Arquivos na Raiz
Você pode criar ou editar os arquivos JSON diretamente na raiz do projeto:
- **`config.json`**: Contém as chaves de API dos modelos de IA. Exemplo de estrutura:
  ```json
  {
      "groq_api_key": "SUA_CHAVE_GROQ_AQUI",
      "gemini_api_key": "SUA_CHAVE_GEMINI_AQUI"
  }
  ```
- **`cookies.json`**: Contém seus cookies da sessão HoYoLAB salvos em formato de dicionário JSON.

### 3. Variáveis de Ambiente
Caso prefira não salvar a chave de API em arquivos locais, você pode exportar a variável de ambiente `GROQ_API_KEY` diretamente no seu terminal antes de iniciar a aplicação:
- **Windows (PowerShell):** `$env:GROQ_API_KEY="gsk_..."`
- **Windows (CMD):** `set GROQ_API_KEY=gsk_...`
- **Linux / macOS:** `export GROQ_API_KEY="gsk_..."`

Para obter mais detalhes sobre como gerar suas chaves e proteger seus tokens de sessão, consulte o arquivo [SECURITY.md](file:///c:/Users/07049770108/Documents/hoyo-projetos/SECURITY.md).

---

## 🔒 Segurança e Privacidade

Todos os cookies (`cookies.json`), chaves de API (`config.json`) e arquivos markdown gerados são armazenados **exclusivamente no seu computador**. O app é 100% user-level e não requer privilégios de Administrador no Windows. Ambos os arquivos `config.json` e `cookies.json` estão inclusos por padrão no arquivo [.gitignore](file:///c:/Users/07049770108/Documents/hoyo-projetos/.gitignore) para garantir que eles nunca sejam commitados acidentalmente.

