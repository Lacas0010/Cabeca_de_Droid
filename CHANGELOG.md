# 📝 Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [5.0.0] - 2026-09-30

### 🚀 Destaques da Versão (Clean Architecture & Modularização Total)
Esta versão representa a maior evolução estrutural do Cabeça de Droid desde a sua concepção, convertendo o monólito remanescente em uma arquitetura limpa em camadas (FastAPI Clean Architecture), desacoplando regras de negócio, introduzindo tipagem estrita com Pydantic v2 e adicionando 62 testes unitários automatizados.

### ✨ Adicionado
- **Arquitetura Modular em Camadas:**
  - `core/`: Configurações centralizadas (`config.py`) e infraestrutura de segurança/sanitização (`security.py`).
  - `schemas/`: Modelos Pydantic tipados com validação estrita para todas as entradas e saídas de API (`auth_security.py`, `config.py`, `chat.py`, `sync.py`, `gacha.py`, `farming.py`, `codes.py`, `stats.py`).
  - `services/`: Camada de regras de negócio desacoplada (`sync_service.py`, `checkin_service.py`, `promo_codes_service.py`, `roster_service.py`, `endgame_service.py`, `gacha_service.py`, `roast_service.py`, `media_service.py`, `translation_service.py`).
  - `routers/`: 15 controladores modulares com `APIRouter` (`security.py`, `config.py`, `sync.py`, `roster.py`, `endgame.py`, `gacha.py`, `farming.py`, `relics.py`, `strategy.py`, `codes.py`, `history.py`, `checkin.py`, `chat.py`, `static_data.py`, `system.py`).
  - `static_data/`: Catálogo e regras de metagame em arquivos JSON puros (`character_elements.json`, `known_4star_characters.json`, `prydwen_slug_mappings.json`, `element_icons.json`, `*_manifest.json`).
- **Novos Recursos & Endpoints:**
  - **Ordem de Serviço Diária:** Algoritmo de roteirização inteligente de resina e energia com checklist dinâmico (`/api/farm/order-of-day/{game_id}`).
  - **Previsão de Gacha & Metas Monte Carlo:** Projeção temporal de acúmulo de gemas/tiros e persistência de metas de invocação no SQLite (`/api/gacha/forecast/calculate` e `/api/gacha/goals`).
  - **Diagnóstico de Lacunas da Conta (Account Gaps):** Avaliação de cobertura de elementos e funções (DPS/Sustento/Buffer) com consultoria estratégica da IA Groq Llama 3.3 70B (`/api/strategy/account-gaps/{game_id}`).
  - **Recomendador de Artesanato de Relíquias (Relic Crafting):** Sugestão de síntese de peças com Resina Automodeladora ou Elixir Santificador com base nas piores peças do time principal (`/api/relics/craft-recommendations/{game_id}`).
  - **Morning Briefing Matinal:** Sumário executivo consolidando os 3 jogos com disparo para Discord Webhooks e Telegram Bot (`/api/briefing/today` e `/api/briefing/send-now`).
  - **Resgate Autônomo de Códigos 3h:** Rotina assíncrona que varre novos códigos na web e efetua o resgate automático na HoYoverse.
  - **Central de Ajuda v5.0 (Help Hub):** Interface visual interativa com 20 cards detalhados, busca em tempo real e 7 filtros por categoria.
- **Suíte de Testes Automatizados:**
  - 62 testes unitários cobrindo segurança, persistência SQLite, RAG, simulador Monte Carlo, scrapers, endpoints de API e validação de schemas.
- **Melhorias de Usabilidade Mobile v5.0:**
  - Empilhamento vertical fluido do Chat IA e do Montador de Times em telas $\le 860\text{px}$.
  - Grid de cards da Central de Ajuda adaptado para 1 coluna única em smartphones.
  - Modais com limite de `95vw` e botões de rodapé empilhados para toque confortável.
  - Suporte a *Safe Area Insets* (`env(safe-area-inset-bottom)`) para iPhones e telas com notch.

### 🔄 Modificado
- `server.py`: Reduzido de 3.232 linhas para 206 linhas, atuando estritamente como orquestrador do ciclo de vida FastAPI com retrocompatibilidade de re-exports.
- `requirements.txt`: Atualizado com organização por categorias e inclusão de `httpx>=0.26.0`.
- `README.md`: Reformulado com diagramas Clean Architecture em Mermaid, tabela de 20 recursos e guia de endpoints.
- `.gitignore`: Atualizado para proteger credenciais (`*.enc`, `*.key`) e ignorar caches, mantendo os testes rastreados.

---

## [4.5.0] - 2026-09-21

### ✨ Adicionado
- **Cofre de Segurança Local com Windows DPAPI:** Criptografia nativa em repouso de tokens e credenciais (`cookies.enc`) vinculada ao perfil de usuário do sistema operacional.
- **Autenticação por PIN Local:** Bloqueio opcional de 4 a 6 dígitos com derivação `PBKDF2-HMAC-SHA256` (120.000 iterações com salt individual) para computadores compartilhados.
- **Simulador Monte Carlo de Gacha:** Motor estocástico com 10.000 iterações, modelo real de Soft Pity (74+), cálculo de desconto de cópias do Roster e animações de invocação (Meteoro, Passagem Estelar, Glitch CRT).
- **Índice de Sorte & Eficiência de Rolagens (Luck Score):** Módulo estatístico para avaliar a qualidade dos artefatos da conta, com detecção de God Roll #1 e Cursed Roll.
- **Linha do Tempo & Snapshots Periódicos:** Histórico de evolução da conta com comparador gráfico de diffs e filtro de personagens alterados.
- **Analisador de Relíquias Lixo (Trash Finder):** Identificação de peças de artefatos/discos com atributos incompatíveis com o metagame para reciclagem segura.
- **Modo Roast da Conta por IA:** Crítica bem-humorada e ácida gerada pelo Groq Llama 3.3 70B sobre as escolhas de pulls e investimentos do jogador.

### 🔄 Modificado
- Migração de cookies em texto claro para formato cifrado `.enc` com exclusão automática de arquivos legados.
- Otimização do cálculo de Roll Value (RV) com Main Stat Forgiveness (+40%) e peso parcial para atributos Flat (50%).

---

## [4.0.0] - 2026-09-01

### ✨ Adicionado
- **Higienizador de Logs em Tempo Real (`log_sanitizer.py`):** Filtro regex no terminal e logs de sincronização para censurar tokens `ltoken_v2`, `ltuid_v2` e chaves de API `gsk_...`.
- **Acesso Wi-Fi & Rede Local (LAN):** Opção de alternância sob demanda para binding em `0.0.0.0:8000`, viabilizando o uso no celular ou tablet.
- **Auto Check-in HoYoLAB a cada 6 Horas:** Rotina em background com gravação de histórico de tentativas no SQLite (`daily_checkin_logs`).
- **Suporte Completo a Zenless Zone Zero (ZZZ):** Integração de agentes, discos, atributos de Anomalia e novo elemento *Lumiflux*.
- **Proxy Anti-CORS de Imagens:** Endpoint `/api/proxy_image` para contornar bloqueios de CORS e permitir renderização em Canvas 2D.

---

## [3.0.0] - 2026-08-15

### ✨ Adicionado
- **Assistente RAG com Groq Cloud API:** Integração do modelo Llama 3.3 70B Versatile contextualizado com os guias de metagame e dados do Roster.
- **Montador de Times com Análise de Sinergia:** Ferramenta visual de seleção de até 4 personagens com streaming de análise via Server-Sent Events (SSE).
- **Exportação de Cards em Imagem HD:** Renderizador Canvas 2D em resolução 4K (2400 × 1350 px) para compartilhamento no Discord.
- **Calculadora de Ascensão:** Estimativa de materiais de chefe, Mora e livros de talento para níveis 60, 70, 80 e 90.

---

## [2.0.0] - 2026-08-01

### ✨ Adicionado
- **Integração com Prydwen.gg:** Scrapers assíncronos com perfis de navegador anti-403 via `curl_cffi` para Genshin Impact, Honkai: Star Rail e Zenless Zone Zero.
- **Tracker de Endgame:** Suporte para Abismo Espiral, Teatro Imaginário, Memória do Caos (MoC), Pura Ficção, Sombra Apocalíptica e Defesa Shiyu.
- **Persistência em Banco SQLite (`hoyo_app.db`):** Migração de arquivos temporários para banco relacional estruturado com modo WAL.

---

## [1.0.0] - 2026-07-15

### ✨ Adicionado
- Lançamento inicial da suíte Cabeça de Droid.
- Dashboard unificado para visualização de personagens e atributos.
- Extração de dados da HoYoLAB via cookies de sessão (`genshin.py`).
- Autenticação automatizada via navegador headless Playwright Chromium.
- Sistema de tradução de termos de metagame Inglês $\rightarrow$ PT-BR.
