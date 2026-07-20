# HSR Roster Extractor & Prydwen Scraper

Uma ferramenta poderosa com interface gráfica desenvolvida em Python (CustomTkinter) projetada para extrair dados detalhados de personagens de **Honkai: Star Rail** do HoYoLAB, raspar guias, builds e análises de meta sazonais do site **Prydwen.gg**, e sincronizar tudo automaticamente com o **Google NotebookLM** usando Playwright.

O principal objetivo deste projeto é gerar relatórios de texto denso em linguagem natural, otimizados para alimentar sistemas de RAG (Retrieval-Augmented Generation) no NotebookLM.

---

## 🛠️ Tecnologias Utilizadas

- **Interface Gráfica:** [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (Aparência Dark Mode Premium)
- **API HoYoLAB:** [genshin.py](https://github.com/thebowja/genshin.py)
- **Raspagem de Dados (Scraping):** BeautifulSoup4 & Requests
- **Navegador e Automação:** Playwright (Python)
- **Concorrência:** Multi-threading em Python (evita congelamento da GUI)

---

## 📂 Estrutura do Projeto

- `main.py`: Ponto de entrada do aplicativo.
- `gui.py`: Gerenciamento e layout da interface gráfica CustomTkinter.
- `auth.py`: Autenticação via Playwright headed para captura e validação de cookies do HoYoLAB.
- `extractor.py`: Integração com a API do HoYoLAB (`genshin.py`) para buscar e traduzir as informações dos personagens ativos.
- `scraper_prydwen.py`: Raspador analítico de guias e builds dos personagens do Prydwen.
- `scraper_meta.py`: Raspador de Tier Lists globais e relatórios analíticos de endgame (MoC, PF, AS, AA).
- `notebooklm_uploader.py`: Automação com Playwright para sincronizar os dados gerados diretamente em um notebook do NotebookLM.

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

### 3. Instalar Navegador do Playwright
Para habilitar o módulo de autenticação e o uploader automático, instale o navegador Chromium gerenciado pelo Playwright:

```bash
playwright install chromium
```

### 4. Executar a Aplicação
Inicie a interface gráfica:

```bash
python main.py
```

---

## 📖 Funcionalidades e Guias de Uso

A interface é dividida em três abas principais:

### 1. HoYoLAB Extractor
- **Login no HoYoLAB:** Abre um navegador para você se autenticar na sua conta do HoYoLAB. Após a conclusão, os cookies são validados e salvos localmente em `cookies.json` para que você não precise logar todas as vezes.
- **Gerar Arquivo Markdown:** Consulta as APIs oficiais e monta um relatório contendo o nível de desbravamento, conquistas, e informações detalhadas de nível, eidolons, cones equipados, conjuntos de relíquias e status finais de todos os personagens. Salva o resultado em `meus_personagens_hsr.md`.

### 2. Prydwen Scraper
- **Baixar Guias de Builds:** Baixa o guia completo de um personagem específico ou de todos do jogo de uma só vez. A análise raspa prós/contras, descrição detalhada do kit, justificativa mecânica de cada equipamento e análises de sinergias (salvando individualmente em `guias_prydwen/`).
- **Atualizar Tier Lists e Meta Sazonal:** Sincroniza a tier list global (em `meta_e_tierlists_atual.md`) e os relatórios de endgame (em `meta_endgame_report.md`), cobrando estatísticas detalhadas de uso e as equipes mais rápidas dos modos **Memory of Chaos (MoC)**, **Pure Fiction (PF)**, **Apocalyptic Shadow (AS)** e **Anomaly Arbitration (AA)**.

### 3. NotebookLM Sync
- **URL do Notebook:** Insira o link do seu notebook de trabalho do NotebookLM (esta URL fica salva de forma persistente no arquivo local `config.json`).
- **Sincronizar com NotebookLM:**
  - O script detecta todos os arquivos Markdown gerados.
  - Consolida todos os guias de personagens individuais da pasta `guias_prydwen/` em um único arquivo mestre: `todos_os_guias_prydwen.md` (evitando ultrapassar o limite de 50 fontes do NotebookLM).
  - Executa o upload de no máximo **4 fontes consolidadas** através de automação Playwright heads-up.
  - Salva e persiste a sua conta Google na pasta local `./user_data_google/`, exigindo o login apenas uma vez.

---

## 🔒 Segurança e Privacidade
Os cookies do HoYoLAB e os dados de login da sua conta Google são armazenados localmente e de forma restrita na pasta do projeto (`cookies.json` e `./user_data_google/`). O código não compartilha informações com servidores de terceiros.
