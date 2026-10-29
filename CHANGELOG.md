# 📝 Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [5.3.0] - 2026-10-28

### ✨ Adicionado
- **Suporte Completo a Bilinguismo & Internacionalização Integral (i18n - PT-BR / EN-US):**
  - Módulo cliente dedicado `static/js/modules/i18n.js` com dicionário bilíngue exaustivo (mais de 200 chaves de tradução) cobrindo **100% da interface gráfica e todos os seus 20 módulos em 8 etapas**:
    - **Etapa 1 (Início & Dashboard Global)**: Banner de boas-vindas, monitor de energia/resina/bateria, ordem de farm prioritária, ferramentas rápidas e briefing do perfil ativo.
    - **Etapa 2 (Abas de Jogos - Genshin, HSR, ZZZ)**: Sub-navegação, badges de filtro por elemento e raridade, barras de pesquisa, checkboxes de sincronização e galeria do elenco.
    - **Etapa 3 (Inspetor de Builds & Roll Value)**: Título e notas de pontuação de relíquias/artefatos/discos, Main Stat Forgiveness, Flat Stat Fallback, detalhes de rolls, custos de ascensão e comparador de metas.
    - **Etapa 4 (Desafios de Endgame)**: Visão focada e completa de Abismo Espiral, Memória do Caos, Ficção Pura, Sombra Apocalíptica, Shiyu Defense e Team Matcher inteligente.
    - **Etapa 5 (Simulador de Tiros & Gacha Forecast)**: Simulação Monte Carlo de 10.000 invocações, painel de metas salvas com cronômetro em tempo real, selector de fase com horários oficiais e rastreador UIGF/SRGF.
    - **Etapa 6 (Central de Farm, Relíquias Lixo, Índice de Sorte & Tier List/Audit)**: Rotação de materiais diários, identificador de peças lixo para descarte, estatísticas de RNG (God Roll, Most Cursed) e diagnóstico de lacunas da conta.
    - **Etapa 7 (Construtor de Card de Time HD & Sinergia)**: Seleção visual de equipe, exportação Canvas 2x PNG e badges de sinergia.
    - **Etapa 8 (Linha do Tempo, Códigos Promocionais, Configurações & Central de Ajuda)**: Histórico de snapshots de evolução, gerenciador de códigos com resgate automático a cada 3h, proteção por PIN, cofre DPAPI, isolamento LAN e central com 20 cards de recursos com busca dinâmica.
  - Seletor de idioma visual com estilo "pill" integrado na barra lateral desktop (`.sidebar-lang-selector`), botão dinâmico de alternância no cabeçalho mobile (`.lang-btn-mobile`) e seletor persistente na aba de Configurações (`#tab-config`).
  - Persistência reativa do idioma ativo no `localStorage` (`app_lang`) e sincronização transparente com o backend através da API `/api/config` (`language: "pt" | "en"`).
  - Atualização dinâmica em tempo real com preservação de estado via atributos `data-i18n`, `data-i18n-placeholder` e listeners ao evento `app:languageChanged` em todos os módulos ES6.
    - **Endgame Bilíngue Completo (HSR, Genshin, ZZZ)**:
      - Nomes oficiais de modos traduzidos dinamicamente no frontend e backend (`Memory of Chaos`, `Pure Fiction`, `Apocalyptic Shadow`, `Spiral Abyss`, `Imaginarium Theater`, `Shiyu Defense`, `Deadly Assault`, `Hollow Zero`).
      - Fases, andares e nós localizados (`Floor`, `Chamber`, `Critical Node`, `Stable Node`, `Disputed Node`, `Arcane Challenge`, `Season`, `Crossing the Beyond`, `Star Mode`, `Act`).
      - Métricas de combate (`Cycles Used`, `Cycles`, `Score`, `Points`, `Floor Stars`, `Side 1 / Side 2`, `Deployed`, `Enemy Lv.`).
      - Team Matcher totalmente traduzido com sugestão funcional de substitutos (`Same tactical role`, `and same element`, `battle-ready`).
    - **Localização Completa de Zenless Zone Zero (ZZZ)**:
      - Elementos traduzidos em filtros, gráficos, galeria e comparador: `Electric`, `Ether`, `Fire`, `Ice`, `Physical`, `Lumiflux`.
      - Raridades de agentes em gráficos de distribuição: `S-Rank` e `A-Rank` (substituindo `Classe S` e `Classe A`).
      - Discos de acionamento em comparadores e sandbox: `Disc 1` .. `Disc 6`.
      - Materiais de farm e unidades padronizados: `Dennys`, `Official Investigator Log`, `Skills`, `Basic/Advanced/Specialized Skill Chips`, `Higher Dimensional Data`, `Hamster Cage Pass`, `W-Engine Power Supply`, `pcs.`.
    - **Central de Farm & Ordem Diária**:
      - Dias da semana no calendário de domínios traduzidos (`Monday`, `Tuesday`, `Wednesday`, `Thursday`, `Friday`, `Saturday`, `Sunday`).
      - Seções informativas traduzidas (`Level Up & Character Ascension`, `Open Today (Field Boss & Specialties 24/7)`, `Local Specialty`).

  - **Serviço de Tradução Bidirecional (`services/translation_service.py`):**
  - Mapeamento reverso automático com suporte ao parâmetro `lang="pt" | "en"` na função `traduzir_item`.
  - Contrato Pydantic v2 atualizado em `schemas/config.py` (`ConfigSaveRequest.language`) e endpoint `/api/config` estendido para leitura e gravação da preferência de idioma.
- **Documentação Bilíngue Completa:**
  - Criação de `README.en.md` contendo a tradução integral da documentação em inglês (Quick Start, 28 recursos, arquitetura, zero-exposure security, fórmulas do Roll Value com as 5 regras de pontuação e referência REST API).
  - Barra superior de alternância de idioma adicionada em `README.md` e `README.en.md`.
- **Suíte de Testes para i18n (`tests/test_i18n_translation_suite.py`):**
  - Novos testes unitários validando a tradução de atributos nos dois sentidos, persistência na API `/api/config`, validação de schemas Pydantic e integridade estrutural do módulo `i18n.js`.
  - Tradução bidirecional completa de nomes de personagens (ex: Silver Wolf, Trailblazer, Traveler, Firefly, Black Swan), caminhos/especialidades (Destruction, Harmony, Nihility, Stun, Sword) e atributos de status (SPD, CRIT Rate, CRIT DMG).
  - Suíte total de testes unitários executada com 159 testes e 100% de aprovação.

---

## [5.2.0] - 2026-10-28

### ✨ Adicionado
- **Metas de Banners Salvas com Cronômetro Regressivo em Tempo Real:**
  - Persistência no SQLite (`gacha_forecast_goals`) com data/hora de criação (`created_at`), data/hora de chegada do banner (`target_date`) e fase (`banner_phase`).
  - Painel de cronômetro regressivo com contagem ativa segundo a segundo (`window.tickGachaGoalsCountdown`), barra de progresso temporal e estimativa dinâmica de tiros acumulados até o presente.
  - Sincronização dos **Horários Oficiais de Lançamento dos Banners**:
    - **1ª Fase (os 3 jogos: Genshin, HSR e ZZZ)**: `23:30` (horário de término da manutenção do patch).
    - **2ª Fase**: `20:00` no Genshin Impact; `14:00` no Honkai: Star Rail e Zenless Zone Zero.
  - Seletor de Fase no painel de planejamento do Gacha Forecast (`1ª Fase (23:30)` e `2ª Fase (20h / 14h)`), com labels dinâmicos que se adaptam automaticamente ao jogo ativo.
  - Rotina autônoma de migração e atualização de metas existentes ([`database.update_all_saved_goals_schedule`](database.py)), garantindo que qualquer meta salva anteriormente receba o horário oficial no banco.
- **Montador de Card de Time & Exportador HD (Glassmorphism):**
  - Construtor visual de composições com suporte a 4 slots (Genshin, HSR) e 3 slots (ZZZ).
  - Seletor de elenco com lazy-loading automático (`/api/roster/{game_id}`), badges de posição de equipe (`#1`, `#2`, `#3`, `#4`) e busca em tempo real.
  - Exportação em alta resolução (PNG 2x) via `html2canvas` com pré-cálculo geométrico de aspect ratio ("cover") no DOM clonado, eliminando distorções em artes de corpo inteiro e splash art panorâmica.
  - Botão de cópia direta para a área de transferência (`navigator.clipboard.write` com blob `image/png`) para compartilhamento imediato no Discord ou WhatsApp.
- **Modularização do Frontend Vanilla ES6 (`static/js/modules/`):**
  - Desacoplamento do antigo monólito `app.js` em 12 submódulos especializados:
    - `api_client.js`: Cliente HTTP centralizado e tratamento de erros.
    - `modal.js`: Controle de janelas modais flutuantes e backdrops.
    - `navigation.js`: Roteamento de abas e sub-navegação por jogo.
    - `config_manager.js`: Gestão de formulários, cofre DPAPI e status de credenciais.
    - `sync_manager.js`: Controles de sincronização assíncrona e stream SSE.
    - `endgame.js`: Roteamento de registros de Abismo, MoC, Ficção Pura e Shiyu.
    - `roster.js`: Renderização de galeria, gráficos SVG e filtros por elemento/raridade.
    - `build_comparator.js`: Inspetor de builds, Roll Value e comparador com meta.
    - `chat_rag.js`: Chat RAG inteligente, orquestração de SSE e construtor de times.
    - `farming.js`: Ordem de serviço diária e calendário de rotação de domínios.
    - `gacha_sim.js`: Simulador Monte Carlo, Gacha Forecast e metas salvas com cronômetro.
    - `gacha_tracker.js`: Rastreador universal UIGF/SRGF e importador de histórico de tiros.
  - Cache-busting estrito nos imports ES6 (`?v=23.5`) para invalidar caches antigos no navegador.
- **Expansão da Suíte de Testes Automatizados para 150 Testes:**
  - Adição de testes unitários em `tests/test_gacha_forecast_suite.py` cobrindo cálculo de horários por fase/jogo, persistência temporal, avanço do relógio, chegada de banner e migração de metas.
  - 100% de aprovação na execução do módulo nativo `unittest`.

### 🔄 Modificado
- **Desambiguação de Funções de Seleção de Time (`static/js/modules/chat_rag.js`):**
  - Separação estrita entre `toggleChatTeamCharacter` (seletor lateral do Chat IA) e `toggleCharacterInTeam` (Montar Card de Time), corrigindo colisão de escopo global.
  - Utilização de `this.dataset.name` com sanitização de caracteres especiais/apóstrofos no seletor de personagens.
- **Deploy Contínuo na VM Oracle Cloud:**
  - Fluxo padronizado de CI/CD via SSH com validação de testes locais antes do push, pull remoto na VM e reinicialização com verificação de logs no `systemd`.

---

## [Unreleased] - 2026-10-21

### ✨ Adicionado
- **Consolidação Modular de Diretórios:**
  - `scrapers/`: Centralização dos raspadores de metagame (`scraper_genshin.py`, `scraper_meta.py`, `scraper_prydwen.py`, `scraper_zzz.py`) com headers anti-403 via `curl_cffi` e sementes locais.
  - `scripts/`: Centralização de utilitários de sistema e serviços Linux em background (`cabeca-de-droid.service` e `setup_service.sh`).
  - `tests/`: Reorganização completa da suíte em 10 módulos padronizados com `tests/__init__.py` garantindo injeção limpa de `sys.path`.
- **Manifesto Estático de Personagens Zenless Zone Zero (`static_data/zzz_manifest.json`):**
  - Mapeamento completo de atributos base, papéis táticos (Atacante, Anomalia, Atordoamento, Suporte, Defensor), elementos (incluindo *Lumiflux*) e especialidades para agentes de ZZZ.
- **Expansão da Cobertura de Testes (74 Testes Automatizados):**
  - Adição de testes unitários abrangentes para sincronização de dados estáticos (`test_static_data_suite.py`), previsões de gacha (`test_gacha_forecast_suite.py`), briefing executivo e sintetizador de relíquias (`test_briefing_crafting_suite.py`).
- **Controlador e Endpoints de Dados Estáticos (`routers/static_data.py`):**
  - Endpoints dedicados para status dos manifestos (`/api/static-data/status`), sincronização (`/api/static-data/sync`), calendário diário de farm (`/api/static-data/schedule/{game_id}`) e catálogo completo de personagens com perfil detalhado.

### 🔄 Modificado
- **Extração de Builds sem Trava de Nível (`extractor.py`):**
  - Remoção do filtro rígido de nível mínimo 70 (`level >= 70`), permitindo cálculo de Roll Value (RV), scoring de atributos e acompanhamento de qualquer personagem da conta desde o nível 1.
- **Aprimoramentos de UI/UX no Dashboard Web Glassmorphism (`static/`):**
  - Otimizações na renderização do Roster, cards visuais e estilização de componentes do ecossistema HoYoLAB.

---

## [5.1.0] - 2026-10-08

- **Janela Modal Centralizada de Build & Dashboard 2 Colunas:**
  - Substituição da antiga aba lateral por uma janela modal flutuante centralizada na tela (`top: 50%; left: 50%`) com backdrop escuro e desfoque suave (`backdrop-filter: blur(14px)`).
  - Reorganização do layout interno em um dashboard de 2 colunas:
    - **Coluna Esquerda:** Equipamento/Arma, Status Finais de Combate com destaque CRIT/Velocidade, Conjuntos de Artefatos, Otimizador IA e Calculadora de Ascensão.
    - **Coluna Direita:** Constelações/Eidolons em grid 3×2 limpo, Talentos & Habilidades em 2 colunas com barras de progresso, e detalhamento completo de peças/substatus.
  - Fechamento intuitivo via botão `✕`, clique no overlay de fundo ou tecla `Escape` (`Esc`).
  - Totalmente responsivo para smartphones e tablets, convertendo suavemente para coluna única com scroll.
- **Eidolons com Shards Visuais (HSR):**
  - Nós de Eidolon no inspetor agora exibem os fragmentos visuais com a arte do rosto do personagem in-game em vez de ícones genéricos.
  - Suporte inteligente a splash arts alternativas para personagens com skins (ex: Sparkle, Robin).
- **Ícones Oficiais de ZZZ:**
  - Ícones oficiais padronizados para todas as 6 categorias de combate: Ataque Básico, Esquiva, Assistência/Suporte, Especial/EX, Suprema/Cadeia e Passiva Central.
  - Ícones customizados de nós de Cinema Mental (01 a 06) no estilo industrial neon cyberpunk (`assets/mindscapes/zzz/m1.png` a `m6.png`).
- **Tooltips Glassmorphism & Descrições Ricas:**
  - Hover action flutuante em glassmorphism com descrições detalhadas e completas de Talentos, Rastros e Habilidades.
  - Higienização e remoção total de tags internas (`<color>`, `{param}`, `{M#o}{F#a}`, etc.).
- **Bases Estáticas Offline & Fallbacks Resilientes:**
  - Datamines locais em português em `static_data/` para Genshin, HSR e ZZZ com enriquecimento automático caso a API não retorne o texto explicativo.
- **Testes Unitários:**
  - Suíte expandida para 74 testes unitários automatizados passando 100%.

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
  - **Diagnóstico de Lacunas da Conta (Account Gaps):** Avaliação determinística de cobertura de elementos e funções (DPS/Sustento/Buffer) (`/api/strategy/account-gaps/{game_id}`).
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

### 🔄 Modificado
- Migração de cookies em texto claro para formato cifrado `.enc` com exclusão automática de arquivos legados.
- Otimização do cálculo de Roll Value (RV) com Main Stat Forgiveness (+40%) e peso parcial para atributos Flat (50%).

---

## [4.0.0] - 2026-09-01

### ✨ Adicionado
- **Higienizador de Logs em Tempo Real (`log_sanitizer.py`):** Filtro regex no terminal e logs de sincronização para censurar tokens `ltoken_v2`, `ltuid_v2` e credenciais de sessão.
- **Acesso Wi-Fi & Rede Local (LAN):** Opção de alternância sob demanda para binding em `0.0.0.0:8000`, viabilizando o uso no celular ou tablet.
- **Auto Check-in HoYoLAB a cada 6 Horas:** Rotina em background com gravação de histórico de tentativas no SQLite (`daily_checkin_logs`).
- **Suporte Completo a Zenless Zone Zero (ZZZ):** Integração de agentes, discos, atributos de Anomalia e novo elemento *Lumiflux*.
- **Proxy Anti-CORS de Imagens:** Endpoint `/api/proxy_image` para contornar bloqueios de CORS e permitir renderização em Canvas 2D.

---

## [3.0.0] - 2026-08-15

### ✨ Adicionado
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
