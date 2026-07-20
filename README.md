# HoYoverse Multi-Game RAG Hub

Uma ferramenta poderosa com interface gráfica moderna desenvolvida em Python (**CustomTkinter**) projetada para centralizar a extração de dados de perfil/roster de jogos da HoYoverse via HoYoLAB, raspar guias analíticos e relatórios de meta dos sites **Prydwen.gg** (para Star Rail e Zenless Zone Zero), e sincronizar automaticamente todos os relatórios consolidados com o **Google NotebookLM** utilizando automação via Playwright.

O principal objetivo deste projeto é gerar fontes de texto denso em formato Markdown estruturado, idealmente otimizadas para alimentar sistemas de RAG (Retrieval-Augmented Generation) ou bases de conhecimento no NotebookLM.

---

## 🛠️ Tecnologias Utilizadas

- **Interface Gráfica:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (Aparência Dark Premium dinâmica)
- **Processamento de Imagem:** Pillow (manipulação de banners e gradientes dinâmicos na interface)
- **API HoYoLAB:** [genshin.py](https://github.com/thebowja/genshin.py)
- **Raspagem de Dados (Scraping):** BeautifulSoup4 & Requests (com cabeçalhos realistas anti-bloqueio)
- **Navegador e Automação:** Playwright (Python) para capturar cookies e fazer upload automático de fontes
- **Concorrência:** Multi-threading em Python (evita o travamento da interface durante tarefas pesadas de rede)

---

## 📂 Estrutura do Projeto

- `main.py`: Ponto de entrada do aplicativo que inicializa o loop principal da GUI.
- `gui.py`: Gerenciamento e design do layout da interface, console de logs em tempo real e orquestração de threads de trabalho.
- `auth.py`: Autenticação via navegador headed (visível) do Playwright para capturar cookies oficiais do HoYoLAB de forma simplificada.
- `extractor.py`: Extrator integrado utilizando a API do `genshin.py` para obter dados detalhados dos personagens ativos do jogador nos três jogos.
- `scraper_prydwen.py`: Raspador analítico de builds, prós/contras, e sinergias de personagens de **Honkai: Star Rail** do Prydwen.
- `scraper_zzz.py`: Raspador analítico de agentes, builds de W-Engines, Discos de Áudio e Cinema de Mente de **Zenless Zone Zero** do Prydwen.
- `scraper_meta.py`: Raspador de Tier Lists globais e estatísticas detalhadas de endgame (MoC, PF, AS, AA) para **Honkai: Star Rail**.
- `notebooklm_uploader.py`: Automação com Playwright que gerencia a consolidação de múltiplos guias em arquivos únicos e o upload direto nos respectivos cadernos do Google NotebookLM.

---

## 🚀 Instalação e Configuração

### 1. Pré-requisitos
Certifique-se de ter o Python 3.10 ou superior instalado na sua máquina.

### 2. Instalar Dependências
Crie um ambiente virtual e instale os pacotes necessários listados no `requirements.txt`:

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar o ambiente virtual (Windows)
.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Instalar o Navegador do Playwright
Para habilitar a captura automática de cookies e o sincronizador do NotebookLM, instale o navegador Chromium gerenciado pelo Playwright:

```bash
playwright install chromium
```

### 4. Executar a Aplicação
Inicie a interface gráfica:

```bash
python main.py
```

---

## 📖 Funcionalidades e Organização de Dados

A interface divide-se em abas de jogos à esquerda e um painel de Configurações globais:

### 🟡 Zenless Zone Zero (ZZZ)
- **Roster & Agentes:** Extrai o nível de Inter-nó, conquistas e detalhes de cada agente (nível, Cinema de Mente, W-Engine equipado, discos de áudio equipados e status consolidados). Salva em [roster_zzz.md](file:///c:/Users/07049770108/Documents/hoyo-projetos/zzz/roster_zzz.md).
- **Guias Individuais:** Raspa e traduz guias de build de agentes de ZZZ, salvando arquivos Markdown individuais na pasta `zzz/guias/`.
- **Tier List & Meta:** Compila e formata as recomendações de meta e ratings em [meta_endgame_zzz.md](file:///c:/Users/07049770108/Documents/hoyo-projetos/zzz/meta_endgame_zzz.md).

### 🟢 Genshin Impact
- **Roster & Personagens:** Extrai o nível de Aventura, conquistas, e fichas de personagens ativos (nível, constelações, arma equipada, conjunto de artefatos e atributos). Salva em `genshin/roster_genshin.md`.
- **Guias & Endgame:** *(Em desenvolvimento/planejado para builds futuras)*.

### 🟣 Honkai: Star Rail (HSR)
- **Roster & Personagens:** Extrai o nível de Desbravamento, conquistas, e detalhes de builds atuais de personagens (nível, eidolons, Cones de Luz equipados, conjuntos de relíquias e status finais). Salva em `hsr/roster_hsr.md`.
- **Guias Individuais:** Raspa guias completos de personagens HSR da Prydwen (salvos individualmente na pasta `hsr/guias/`).
- **Tier List & Relatório Endgame:** Extrai a tier list atual (`hsr/meta_e_tierlists_atual.md`) e estatísticas sazonais de modos como *Memory of Chaos (MoC)*, *Pure Fiction (PF)*, *Apocalyptic Shadow (AS)* e *Anomaly Arbitration (AA)* (`hsr/meta_endgame_report.md`). Consolida tudo em [meta_endgame_hsr.md](file:///c:/Users/07049770108/Documents/hoyo-projetos/hsr/meta_endgame_hsr.md).

---

## ⚙️ Painel de Configurações e Google NotebookLM Sync

1. **Credenciais HoYoLAB:** 
   - **Login Automático:** Abre o navegador com Playwright para que você entre no site oficial do HoYoLAB. O script detecta, extrai e salva os cookies localmente em `cookies.json` de forma segura.
   - **Manual:** Permite colar a string de cookies diretamente na caixa de entrada.
2. **URLs dos Cadernos do NotebookLM:**
   - Permite definir as URLs de compartilhamento específicas dos cadernos para ZZZ, Genshin e HSR de forma persistente (salvas no arquivo `config.json`).
3. **Sincronização em Massa:**
   - Consolida todos os guias de personagens individuais (da pasta `guias/`) em um único arquivo unificado (ex: `todos_os_guias_hsr.md` ou `todos_os_guias_zzz.md`). Isso é feito para evitar exceder o limite de 50 fontes do NotebookLM.
   - Faz o upload automático das fontes consolidadas (roster, meta e compilado de guias) para os respectivos cadernos do Google NotebookLM.
   - Os dados do perfil Google Chrome são persistidos de forma segura no diretório `./user_data_google/`, exigindo o login apenas na primeira sincronização.

---

## 🔒 Segurança e Privacidade
Todos os dados sensíveis como cookies do HoYoLAB (`cookies.json`), tokens e sessão do navegador Google (`./user_data_google/`) são armazenados **exclusivamente de forma local** no seu computador. Nenhuma informação é enviada a servidores externos além das APIs oficiais da HoYoverse e os servidores seguros da Google.
