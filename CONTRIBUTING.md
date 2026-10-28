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
- **Zero Regressão:** Todos os 150 testes unitários automatizados devem continuar passando a cada modificação.
- **Clean Architecture:** Desacoplamento estrito entre a camada de apresentação (`routers/`), contratos de dados (`schemas/`), regras de negócio (`services/`) e persistência/segurança (`core/` e `database.py`).
- **Zero Hardcoding & Automação de Dados:** É proibido criar dicionários hardcoded com dados voláteis no código Python (tier lists, personagens, multiplicadores). Toda ingestão deve vir dinamicamente de scrapers para arquivos JSON em `static_data/`.
- **Resiliência Offline:** O sistema deve sempre conter fallbacks e sementes locais (`static_data/`) para inicializar e operar mesmo sem conexão com a internet.

---

## 📊 Evolução Arquitetural: Da v4.5 à v5.2

A versão **5.2** consolida a modularização total tanto no backend quanto no frontend, adicionando módulos estocásticos de previsão de banners, contagem regressiva em tempo real e montador de times HD.

### Comparativo Arquitetural

| **Aspecto** | **Versão 4.5** | **Versão 5.x / 5.2 (Atual)** |
| :--- | :--- | :--- |
| **Ponto Central (`server.py`)** | Monólito com >3.200 linhas contendo rotas, lógica e SQL | Orquestrador limpo de ciclo de vida com ~200 linhas |
| **Camada de Roteamento** | Endpoints misturados em funções soltas | 15 módulos `APIRouter` especializados em [`routers/`](routers/) |
| **Contratos & Tipagem** | Dicionários `dict` brutos sem validação estrita | Modelos tipados [Pydantic v2](schemas/) em [`schemas/`](schemas/) |
| **Regras de Negócio** | Lógica acoplada dentro dos handlers HTTP | Serviços isolados e testáveis em [`services/`](services/) |
| **Frontend Web** | Script monolítico `app.js` | 12 módulos ES6 desacoplados em [`static/js/modules/`](static/js/modules/) com cache-busting |
| **Metas de Gacha & Banners** | Ausente | Projeção Monte Carlo com cronômetro em tempo real e horários oficiais (23:30 / 20h / 14h) |
| **Montador de Times** | Apenas recomendador de texto | Construtor visual de card de time HD, glassmorphism e cópia para Clipboard |
| **Testes Automatizados** | 2 arquivos de teste isolados | 150 testes unitários em suítes automatizadas passando 100% |

### Novos Recursos Adicionados na v5.0
1. **Ordem de Serviço Diária (`routers/farming.py`):** Roteiro automatizado de gasto de resina e checklist de energia diário.
2. **Previsão de Gacha & Metas Monte Carlo (`routers/gacha.py`):** Simulação de acúmulo de gemas e persistência de metas futuras.
3. **Diagnóstico de Lacunas da Conta (`routers/strategy.py`):** Mapeamento de ausência de arquétipos com parecer Groq 70B.
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
├── core/                    # Infraestrutura, configurações globais e segurança
│   ├── config.py            # Paths, leitura de cofre e resolução de recursos
│   └── security.py          # Windows DPAPI, AES-GCM, PBKDF2 e sanitização de logs
├── schemas/                 # Contratos Pydantic (Type Hints & Validação de Entrada/Saída)
│   ├── auth_security.py     # Modelos de PIN e status de segurança
│   ├── config.py            # Modelos de configuração, webhooks e agendador
│   ├── chat.py              # Modelos de requisições RAG e montador de times
│   ├── gacha.py             # Modelos de cálculo Monte Carlo, previsões e metas
│   ├── farming.py           # Modelos de ordem de serviço, cálculo de XP e passos
│   └── ...
├── services/                # Regras de Negócio (Lógica desacoplada e reutilizável)
│   ├── sync_service.py      # Sincronização assíncrona de metagame e rosters
│   ├── checkin_service.py   # Automação do check-in diário no HoYoLAB
│   ├── promo_codes_service.py # Varredura e resgate autônomo de códigos promocionais
│   ├── gacha_service.py     # Simulações estocásticas e metas de banners
│   ├── roast_service.py     # Análise e geração de pareceres via Groq Llama 3.3 70B
│   └── ...
├── routers/                 # Controladores REST FastAPI (Definição de Rotas e Endpoints)
│   ├── security.py          # Rotas de cofre, PIN e controle de rede LAN
│   ├── gacha.py             # Rotas do simulador de tiros e metas
│   ├── farming.py           # Rotas de farm diário e ordem de serviço
│   └── ...
├── static_data/             # Bases de dados estáticas desacopladas (JSON puro)
├── static/                  # Frontend Web SPA (HTML5, Vanilla CSS, JS ES6+)
│   ├── js/
│   │   ├── app.js           # Ponto de entrada e orquestrador de eventos
│   │   └── modules/         # 12 submódulos desacoplados (api_client, chat_rag, gacha_sim, etc.)
│   ├── style.css            # Folha de estilos Glassmorphism e responsividade
│   └── index.html           # Documento principal da SPA
├── assets/                  # Ícones estáticos e avatares oficiais
├── scrapers/                # Raspadores de metagame e guias do Prydwen (HSR, Genshin, ZZZ)
├── scripts/                 # Scripts utilitários e serviços do sistema (systemd)
├── tests/                   # Suíte de 150 testes unitários automatizados
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

3. **Frontend (Vanilla HTML5 / CSS3 / JavaScript ES6+):**
   - Não utilize frameworks pesados (React, Vue, Tailwind) para manter o carregamento instantâneo.
   - Todo código JavaScript novo deve ser estruturado em submódulos dentro de `static/js/modules/` e importado pelo `app.js` com query string de cache-busting (ex: `?v=23.5`).
   - Utilize variáveis CSS de tokens definidas em `:root` no [`static/style.css`](static/style.css).
   - Todo novo componente deve possuir media query responsiva para telas verticais de smartphones ($\le 768\text{px}$ e $\le 480\text{px}$).

4. **Horários Oficiais de Lançamento de Banners:**
   - Ao manipular datas de término ou chegada de banners:
     - **1ª Fase (os 3 jogos)**: `23:30`.
     - **2ª Fase**: Genshin `20:00`; HSR `14:00`; ZZZ `14:00`.

---

## 🧪 Execução e Criação de Testes Unitários

Todos os testes utilizam o módulo nativo `unittest` do Python, dispensando bibliotecas adicionais:

```bash
# Executar toda a suíte de testes (150 testes)
python -m unittest discover tests

# Executar uma suíte de teste específica
python -m unittest tests.test_security_suite
python -m unittest tests.test_gacha_forecast_suite
python -m unittest tests.test_static_data_suite
```

### Regras para Novos Testes
* Toda nova funcionalidade ou rota adicionada **deve** vir acompanhada de um teste unitário correspondente na pasta `tests/`.
* Testes que envolvem chamadas de rede externas (HoYoLAB, Groq, Prydwen) **devem utilizar mocks** (`unittest.mock.patch`) para execução 100% determinística e offline.

---

## 🚀 Deploy Automatizado na VM Oracle (Deploy & CI/CD)

Ao atualizar a aplicação e publicar na VM remota:
1. Valide a integridade local: `python -m unittest discover tests`.
2. Commit e push para o GitHub: `git push origin main`.
3. Dispare a atualização remota via SSH:
   ```bash
   ssh -i "path/to/ssh-key.key" ubuntu@147.15.40.30 "cd ~/Cabeca_de_Droid && git pull origin main && sudo systemctl restart cabeca-de-droid"
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
