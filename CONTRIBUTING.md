# 🤝 Guia de Contribuição (Contributing Guide)

Obrigado pelo seu interesse em contribuir com o **Cabeça de Droid**! Este documento orienta desenvolvedores e colaboradores sobre a arquitetura do projeto, fluxo de trabalho, padrões de código e procedimentos para submissão de melhorias.

---

## 📑 Índice
1. [Visão Geral & Filosofia de Código](#-visão-geral--filosofia-de-código)
2. [Evolução Arquitetural: Mudanças da v4.5 para a v5.0](#-evolução-arquitetural-mudanças-da-v45-para-a-v50)
3. [Configuração do Ambiente de Desenvolvimento](#-configuração-do-ambiente-de-desenvolvimento)
4. [Estrutura do Projeto & Responsabilidades](#-estrutura-do-projeto--responsabilidades)
5. [Padrões de Código & Diretrizes](#-padrões-de-código--diretrizes)
6. [Execução e Criação de Testes Unitários](#-execução-e-criação-de-testes-unitários)
7. [Padrões de Commit & Fluxo de Pull Request](#-padrões-de-commit--fluxo-de-pull-request)

---

## 💡 Visão Geral & Filosofia de Código

O Cabeça de Droid é projetado como uma suíte **100% local, autônoma, resiliente e segura**. Nossas premissas inegociáveis são:
- **Privacidade & Segurança em Primeiro Lugar:** Tokens e cookies de sessão nunca devem trafegar para serviços de terceiros e devem ser criptografados em repouso no Windows com DPAPI e no Linux com AES-256 derivado da máquina.
- **Zero Regressão:** Todos os **230 testes unitários automatizados** (`30` suítes em `tests/`) devem continuar passando a cada modificação.
- **Clean Architecture:** Desacoplamento estrito entre a camada de apresentação (`routers/`), contratos de dados (`schemas/`), regras de negócio (`services/`) e persistência/segurança (`core/`, `database.py`, `updater.py`).
- **Zero Hardcoding & Automação de Dados:** É proibido criar dicionários hardcoded com dados voláteis no código Python (tier lists, personagens, multiplicadores). Toda ingestão deve vir dinamicamente de scrapers para arquivos JSON em `static_data/`.
- **Performance & Eficiência de Consultas:** Nunca utilize `SELECT *` em dados voláteis ou de crescimento contínuo; utilize projeções explícitas de colunas e paginação obrigatória (`LIMIT ? OFFSET ?`). Aplique virtualização nativa CSS onde aplicável sem gerar thrashing de scroll e respeite as políticas de cache em memória com invalidação reativa.
- **Resiliência Offline:** O sistema deve sempre conter fallbacks e sementes locais (`static_data/` e `static/vendor/sakuga-vfx/`) para inicializar e operar mesmo sem conexão com a internet.

---

## 📊 Evolução Arquitetural: Da v4.5 à v5.6

A versão **5.6** (empacotamento standalone **v1.2.0**) consolida a interface 100% offline em **Sakuga VFX**, o empacotamento standalone Windows com fallback de auto-login e auto-shutdown ao fechar a aba no desktop, além do **Auto-Updater via GitHub Releases** e **230 testes unitários** aprovados.

### Comparativo Arquitetural

| **Aspecto** | **Versão 4.5** | **Versão 5.0 - 5.5** | **Versão 5.6 (Atual)** |
| :--- | :--- | :--- | :--- |
| **Ponto Central (`server.py`)** | Monólito com >3.200 linhas | Orquestrador enxuto com `GZipMiddleware` e `X-Process-Time` | Lifespan com `browser_lifecycle_service` (auto-shutdown apenas quando `sys.frozen`) |
| **Camada de Roteamento** | Endpoints misturados em funções soltas | 15 módulos `APIRouter` em [`routers/`](routers/) | **16 módulos `APIRouter`** incluindo [`routers/updater.py`](routers/updater.py) |
| **Contratos & Tipagem** | Dicionários `dict` brutos | Modelos Pydantic v2 em [`schemas/`](schemas/) | **16 arquivos de contrato** Pydantic v2 ponta a ponta |
| **Regras de Negócio & Cache** | Lógica acoplada nos handlers | Serviços isolados com cache TTL (60s) | **15 módulos de serviço** + `updater.py` com verificação GitHub e troca via `.bat` |
| **Banco de Dados (SQLite)** | Consultas N+1 e `SELECT *` | SQLite em lote (`WHERE uid IN (...)`), sem N+1 e backfill | Suporte a `ex_ranks_json` (Affinitive Eidolons HSR), `weapon_rarity`, `sets_json` e metas de banner |
| **Frontend Web** | Script monolítico `app.js` | 12 módulos ES6, modo Lista Opção C, fontes WOFF2 | **14 módulos ES6** + **11 Web Components Sakuga VFX locais**, grade horizontal desktop e modal de Auto-Updater |
| **Distribuição & Releases** | Apenas execução Python local | Script manual e systemd | PyInstaller (`build.py`), Bandeja Windows (`pystray`), CI GitHub Actions e Auto-Updater `version.py` |
| **Testes Automatizados** | 2 arquivos isolados | 181 testes unitários | **230 testes unitários automatizados** em **30 suítes** com 100% de aprovação |

### Novos Recursos Adicionados na v5.0
1. **Ordem de Serviço Diária (`routers/farming.py`):** Roteiro automatizado de gasto de resina e checklist de energia diário.
2. **Previsão de Gacha & Metas Monte Carlo (`routers/gacha.py`):** Simulação de acúmulo de gemas e persistência de metas futuras.
3. **Diagnóstico de Lacunas da Conta (`routers/strategy.py`):** Mapeamento determinístico de ausência de arquétipos e elementos.
4. **Recomendador de Síntese (`routers/relics.py`):** Sugestão de criação de artefatos com Resina Automodeladora / Elixir Santificador.
5. **Morning Briefing Matinal (`routers/system.py`):** Relatório unificado dos 3 jogos com suporte a Discord Webhook e Telegram.
6. **Resgate Autônomo 3h (`services/promo_codes_service.py`):** Busca contínua e ativação de novos códigos promocionais.
7. **Central de Ajuda v5.0 (`static/index.html`):** 20 cards interativos com 7 categorias e busca em tempo real.

---

## 🛠️ Configuração do Ambiente de Desenvolvimento

### 1. Clonar o Repositório
```bash
git clone https://github.com/Lacas0010/Cabeca_de_Droid.git
cd Cabeca_de_Droid
```

### 2. Criar e Ativar o Ambiente Virtual (Python 3.10+)
* **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
* **Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Instalar Dependências e Chromium do Playwright
```bash
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

---

## 📂 Estrutura do Projeto & Responsabilidades

```
hoyo-projetos/
├── core/                    # Infraestrutura, paths (sys._MEIPASS / %APPDATA%), tray e segurança
│   ├── config.py            # Configurações globais e resolução de recursos
│   ├── paths.py             # Caminhos empacotados vs desenvolvimento
│   ├── tray.py              # Ícone na bandeja do sistema Windows (pystray)
│   └── security.py          # Windows DPAPI, AES-GCM, PBKDF2 e sanitização de logs
├── schemas/                 # 16 contratos Pydantic v2 (Entrada/Saída de API)
├── services/                # 15 módulos de Regras de Negócio e Ciclo de Vida
├── routers/                 # 16 controladores REST FastAPI (inclui updater.py)
├── static_data/             # Bases de dados estáticas desacopladas (JSON puro)
├── static/                  # Frontend Web SPA (HTML5, Vanilla CSS, ES6+ e Sakuga VFX)
│   ├── vendor/sakuga-vfx/   # 11 Web Components locais (100% offline)
│   ├── js/
│   │   ├── app.js           # Ponto de entrada e orquestrador de eventos
│   │   └── modules/         # 14 submódulos ES6 desacoplados (inclui updater_ui.js)
│   ├── style.css            # Variáveis :root, tema escuro Sakuga --sk-* e responsividade
│   └── index.html           # Documento principal da SPA
├── assets/                  # Ícones estáticos e avatares oficiais
├── scrapers/                # Raspadores de metagame e guias (Prydwen, Genshin, ZZZ)
├── scripts/                 # Scripts utilitários, Nginx e serviço systemd
├── tests/                   # 30 suítes (230 testes unitários offline via unittest)
├── .github/workflows/       # Pipeline release.yml (carimbo version.py + build Windows)
├── build.py                 # Gerador PyInstaller e Cabeca_de_Droid-Windows-x64.zip
├── version.py               # Fonte única da versão da aplicação
├── updater.py               # Verificação GitHub Releases e instalador seguro Windows
├── server.py                # Orquestrador FastAPI modular e ciclo de vida
└── main.py                  # Entrypoint principal de execução
```

---

## 📏 Padrões de Código & Diretrizes

1. **Python (PEP 8 & Clean Code):**
   - Utilize tipagem estrita com *Type Hints* (`from typing import Optional, List, Dict, Any`).
   - Todos os novos endpoints devem definir `response_model` ou utilizar contratos Pydantic em `schemas/`.
   - Evite lógica de negócio dentro dos routers; delegue o processamento para a camada `services/`.
   - Trate exceções com `try/except` adequados e retorne códigos HTTP semânticos via `HTTPException`.

2. **Segurança & Higienização:**
   - **Nunca** exiba tokens brutos (`ltoken_v2`, `ltuid_v2`, `cookie_token_v2`) ou chaves de API nos logs ou respostas de API. Utilize o `mask_token` do [`core/security.py`](core/security.py).
   - Não armazene arquivos de credenciais em texto claro; utilize o cofre `security_vault`.

3. **Frontend (Vanilla HTML5 / CSS3 / JavaScript ES6+ & Sakuga VFX):**
   - Não utilize frameworks pesados (React, Vue, Tailwind) nem CDNs externas.
   - Use sempre os Web Components locais em `static/vendor/sakuga-vfx/` (`<sakuga-button>`, `<sakuga-input>`, `<sakuga-toggle>`, `<sakuga-checkbox>`, `<sakuga-radio>`, `<sakuga-slider>`, `<sakuga-tabs>`, `<sakuga-progress>`, `<sakuga-rating>`, `<sakuga-toast>`, `<sakuga-tooltip>`).
   - Mantenha `overflow: visible` nos ancestrais próximos de `<sakuga-button>` / `<sakuga-progress>` para não cortar bursts e fumaças, e mantenha modais abaixo de `canvas.sakuga-fx` (`z-index < 2147483000`).
   - Todo código JavaScript novo deve ser estruturado em submódulos dentro de `static/js/modules/` e importado pelo `app.js` com query string de cache-busting (ex: `?v=31.0`).
   - Utilize variáveis CSS de tokens definidas em `:root` no [`static/style.css`](static/style.css).
   - Todo novo componente deve possuir media query responsiva para telas verticais de smartphones ($\le 768\text{px}$).

4. **Horários Oficiais de Lançamento de Banners:**
   - Ao manipular datas de término ou chegada de banners:
     - **1ª Fase (os 3 jogos)**: `23:30`.
     - **2ª Fase**: Genshin `20:00`; HSR `14:00`; ZZZ `14:00`.

---

## 🧪 Execução e Criação de Testes Unitários

Todos os testes utilizam o módulo nativo `unittest` do Python, dispensando bibliotecas adicionais:

```bash
# Executar toda a suíte de testes (230 testes)
python -m unittest discover tests

# Executar uma suíte de teste específica
python -m unittest tests.test_security_suite
python -m unittest tests.test_updater_suite
python -m unittest tests.test_packaging_suite
```

### Regras para Novos Testes
* Toda nova funcionalidade ou rota adicionada **deve** vir acompanhada de um teste unitário correspondente na pasta `tests/`.
* Testes que envolvem chamadas de rede externas (HoYoLAB, Prydwen, GitHub Releases) **devem utilizar mocks** (`unittest.mock.patch`) para execução 100% determinística e offline.

---

## 🚀 Deploy Automatizado na VM Oracle (Deploy & CI/CD)

Ao atualizar a aplicação e publicar na VM remota:
1. Valide a integridade local: `python -m unittest discover tests`.
2. Commit e push para o GitHub: `git push origin main`.
3. Dispare a atualização remota via SSH:
   - **Sem novas dependências:**
     ```bash
     ssh -i "path/to/ssh-key.key" ubuntu@147.15.40.30 "cd ~/Cabeca_de_Droid && git pull origin main && sudo systemctl restart cabeca-de-droid"
     ```
   - **Se houver alterações em `requirements.txt`:**
     ```bash
     ssh -i "path/to/ssh-key.key" ubuntu@147.15.40.30 "cd ~/Cabeca_de_Droid && git pull origin main && source venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart cabeca-de-droid"
     ```
4. Verifique o status ativo do serviço:
   ```bash
   ssh -i "path/to/ssh-key.key" ubuntu@147.15.40.30 "sudo systemctl is-active cabeca-de-droid && sudo journalctl -u cabeca-de-droid -n 15 --no-pager"
   ```

---

## 📌 Padrões de Commit & Fluxo de Pull Request

Utilizamos a convenção de [Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/):

| Prefixo | Finalidade | Exemplo |
| :--- | :--- | :--- |
| `feat:` | Nova funcionalidade para o usuário | `feat: add relic crafting recommendations endpoint` |
| `fix:` | Correção de bug ou falha de comportamento | `fix: handle character name normalization for new ZZZ agents` |
| `refactor:` | Alteração de código sem mudança de comportamento | `refactor: extract promo code auto redeem into dedicated service` |
| `docs:` | Atualizações de documentação | `docs: update API endpoints table in README` |
| `test:` | Adição ou correção de testes automatizados | `test: add unit tests for account gaps evaluation` |
| `chore:` | Tarefas de manutenção ou dependências | `chore: update requirements.txt with httpx dependency` |

### Checklist para Submissão de Pull Request (PR)
- [ ] O código segue os padrões do PEP 8 e da Clean Architecture.
- [ ] O comando `python -m unittest discover tests` passa com **zero falhas** (150 testes).
- [ ] O código foi testado no modo desktop e mobile.
- [ ] Nenhum arquivo de credencial (`config.json`, `cookies.enc`, `*.key`) foi commitado.
- [ ] As alterações relevantes foram refletidas no `README.md` e `CHANGELOG.md`.
