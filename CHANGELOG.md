# 📝 Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/) e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Não lançado]

### 🐛 Corrigido
- **Fallback web no Auto-Updater contra `403/429 rate limit` (`updater.py`, `tests/test_updater_suite.py`):** quando `api.github.com` atingir o limite público de 60 req/h por IP, `check_for_updates()` recorre automaticamente ao redirect web de `https://github.com/Lacas0010/Cabeca_de_Droid/releases/latest` para resolver a tag e o asset `.zip` sem erro (`329 testes aprovados`).

### 📝 Documentação
- Atualização completa de `README.md`, `README.en.md`, `CONTRIBUTING.md`, `SECURITY.md` e `.gitignore` refletindo todas as entregas da `v1.4.0`/`v1.4.1` (329 testes, Radar de Resets, Daily Notes completo, Chefes/Buffs no Endgame, `Ctrl+K` e convenção correta dos horários de virada de banners).

---

## [5.8.1] / Release Standalone [v1.4.1] - 2026-11-24

### 🐛 Corrigido
- **Migração automática de `current_banners.json` e ícones versionados no `.exe` (`core/paths.py`, `services/gacha_service.py`):** `seed_bundled_resources()` agora detecta troca de versão via `.bundle_version` e atualiza automaticamente `static_data/current_banners.json` (quando em schema legado da `v1.3.4` ou mais antigo que o bundle) e os ícones oficiais em `assets/{icons,resources,endgame,elements}/`, preservando integralmente `.db`, `.enc` e `.env`; `get_current_banners()` também identifica caches legados sem `duration_type`/`end_date`, migra do bundle ou re-executa o scraper, e `_compute_banner_timing()` aplica fallback de parse de datas.
- **Empacotamento offline completo no CI (`.github/workflows/release.yml`):** prefetch automático dos 4 conjuntos de ícones oficiais (`element`, `role`, `resource` e `endgame`) antes do build PyInstaller (`328 testes aprovados`).

---

## [5.8.0] / Release Standalone [v1.4.0] - 2026-11-24

### ✨ Adicionado
- **Ícones oficiais de Endgame, Caminhos, Armas, Especialidades e Recursos (`scrapers/endgame_icons_scraper.py`, `scrapers/role_icons_scraper.py`, `scrapers/resource_icons_scraper.py`, `services/media_service.py`, `routers/system.py`):**
  - Coleta dinâmica via APIs oficiais (**StarRailRes**, **HoYoWiki**, **Prydwen**) com cache offline em `static_data/*.json` e rotas locais `/assets/endgame/`, `/assets/icons/` e `/assets/resources/` + fallback `onerror` seguro.
  - Aplicados nos filtros do Roster, cards/linhas de personagens, `#build-inspector`, painéis de Endgame, **Monitor de Energia** (Resina Original, Poder de Desbravamento e Bateria) e **Simulador de Gacha / Índice de Sorte** (moedas e passes oficiais).
- **Ícones de Chefes e Buffs nos Cards de Endgame (`endgame_extractor.py`, `services/endgame_service.py`, `static/js/modules/endgame.js`, `static/css/endgame_strategy.css`):**
  - Extração estruturada dos chefes oficiais da **Sombra Apocalíptica** (Lados 1, 2 e 3), buffs de fase da **Ficção Pura**, **Bênçãos Brilhantes** (com nível e descrição limpa de tags HoYoLAB) + Eventos do **Teatro Imaginário** e chefes/buffs do **Assalto Mortal (ZZZ)**, com backfill automático sob demanda para bancos legados e tooltips estilizados responsivos.
- **Radar Unificado de Resets & Virada de Banners na Home (`routers/endgame.py`, `services/endgame_service.py`, `schemas/team_matcher.py`, `static/js/modules/endgame.js`, `static/js/modules/gacha_sim.js`):**
  - Novo endpoint `GET /api/endgame/reset-radar` agregando os **7 modos de endgame** ordenados por urgência (destaque âmbar para pendências a `<= 72h` do reset), timers ao vivo de **Reset Diário (04:00)** e **Semanal (Segunda 04:00)** no fuso do servidor, e navegação direta para o modo clicado.
  - Subseção **Virada de Banners Ativos** na Home agrupada por data/hora real de término (separando `1ª Fase`, `2ª Fase` e `Patch Inteiro`), alerta `< 48h` e clique preenchendo automaticamente jogo, aba e personagem alvo no Simulador de Gacha.
- **Daily Notes Completo no Monitor de Energia (`services/checkin_service.py`, `static/js/modules/sync_manager.js`, `static/style.css`):**
  - Cálculo e exibição do **horário exato de lotação** da energia no fuso local (`Lota hoje/amanhã às HH:MM`).
  - Pílulas compactas por jogo: Comissões, Expedições com timer, Chefes Semanais, Transformador Paramétrico e Bule (Genshin); Poder de Reserva, Treino Diário, SU/DU, Eco da Guerra e Expedições (HSR); Engajamento, Raspadinha, Café, Locadora (`VideoStoreState.*`) e Cavidade Zero (ZZZ).
- **Busca Rápida Global `Ctrl+K` (`static/js/modules/quick_search.js`, `static/index.html`, `static/style.css`):**
  - Modal Vanilla JS leve acionável por `Ctrl+K` / `Cmd+K`, botão na Sidebar e lupa no cabeçalho Mobile, com busca sem acentos ranqueada e navegação completa por teclado (`↑`, `↓`, `Enter`, `Esc`) para pular direto para qualquer personagem no Build Inspector, modo endgame ou aba.

### 🐛 Corrigido
- **Cronograma e horários de virada de banners (`scrapers/scraper_prydwen.py`, `services/gacha_service.py`, `schemas/gacha.py`, `static/js/modules/gacha_sim.js`, `static/css/gacha.css`):** detecção individual por banner de `1ª Fase` (`20:00` Genshin / `14:00` HSR e ZZZ) vs `2ª Fase` / `Patch Inteiro` (`23:30` virada de atualização), timer ao vivo por banner e correção de overflow horizontal no Simulador de Gacha em telas mobile (`<= 768px`).
- **Retratos de personagens e ícone da Resina Original (`services/gacha_service.py`, `services/gacha_tracker_service.py`, `scrapers/resource_icons_scraper.py`):** priorização de ícones oficiais de `static_data_manager` (StarRailRes/Enka), correção da CDN Prydwen HSR (`honkai-star-rail`), limpeza de slugs com `•`/`.` (`silver-wolf-lv-999`), sufixo `_card.webp` no ZZZ e filtro de entradas de tutorial no HoYoWiki para a Resina Original azul (`327 testes aprovados`).

---

## [5.7.4] / Release Standalone [v1.3.4] - 2026-11-19

### 🐛 Corrigido
- **Auto-reparo de `meta_data_{game}.json` no `.exe` e sync estático (`build_calculator.py`, `routers/static_data.py`, `server.py`):** `get_meta_data()` agora detecta automaticamente quando `meta_data_{game}.json` está mais antigo que `hoyolab_mappings.json` ou contém entradas corrompidas (`crit_dmg` em Cálice, stubs vazios ou Genshin sem `substats_priority`) e regenera o cache na hora; o sync estático (no startup e em `/api/static-data/sync`) também regenera `meta_data_{game}.json` e invalida o cache do roster.
- **Avaliação de slots flex e substatus inferidos (`build_calculator.py`):** `_clean_main_slot_stats()` preserva `"any"` quando `Anything` é opção explícita (`/`), mantendo pontuação máxima de Main Stat em slots flex (ex.: *Mona*, *Bennett*, *Citlali*, *Faruzan*), e `_infer_genshin_substats()` passa a incluir Recarga de Energia (`er`) nos guias baseados apenas em estatísticas de uso do Enka (ex.: *Ayaka*, *Kazuha*, *Kokomi*).
- **Tipo de arma dinâmico para personagens recentes do Genshin (`scrapers/scraper_genshin.py`, `static_data_manager.py`, `services/roster_service.py`):** `PrydwenGenshinScraper.get_character_list()` extrai `weapon`, `element` e `rarity` dos cards do Prydwen, `_sync_genshin()` mescla esse catálogo no `genshin_manifest.json` (147 personagens) e foi removida a heurística incorreta de `"asa gelada"` como Arco, corrigindo *Odette* para **Espada (`Sword`)** (`287 testes aprovados`).

---

## [5.7.3] / Release Standalone [v1.3.3] - 2026-11-19

### 🐛 Corrigido
- **Reconciliação dinâmica de IDs oficiais (`static_data_manager.py`, `build_calculator.py`):** `fetch_master_id_list()` agora prioriza fontes autoritativas (roster HoYoLAB, `genshin.py` `CHARACTER_NAMES` e manifestos sincronizados) antes de mapeamentos legados; `_sync_zzz()` passa a consumir `EnkaNetwork/API-docs` (`zzz/avatars.json` + `locs.json`) e `_sync_hoyolab_mappings()` reconcilia `static_data/hoyolab_mappings.json` automaticamente durante `sync_upstream_data()`, eliminando ~47 trocas de IDs nos 3 jogos (incluindo *Xilonen*, *Chasca*, *Mavuika*, *Citlali*, *Mualani*, *Kinich*, *Arlecchino*, *Firefly*, *Anaxa*, *Evernight*, *Miyabi*, *Astra Yao*, *Evelyn*, *Ellen* e *Billy*).
- **Extração de Main Stats e Substatus (`build_calculator.py`):** removido mapeamento indevido de `"dmg"` para `"crit_dmg"` (agora `"elemental_dmg"`, equivalente a qualquer bônus elemental no cálculo de RV), limpeza do token `"anything"` quando há stats concretos, filtro de stubs vazios/cross-game e inferência dinâmica de `substats_priority` a partir dos `main_stats` para guias do Genshin baseados apenas em estatísticas de uso do Enka (ex.: *Xianyun*, *Clorinde*, *Chiori*).
- **Scraper do Genshin (`scrapers/scraper_genshin.py`):** deduplicação de armas, artefatos e `main_stats` entre abas de builds, preservando a primeira `stat-priority-strip` (build principal) (`285 testes aprovados`).

---

## [5.7.2] / Release Standalone [v1.3.2] - 2026-11-19

### 🐛 Corrigido
- **Seleção de UID ativo padrão no SQLite (`database.py`):** quando `active_accounts` ainda não possui escolha explícita, `get_active_uid()` e `get_active_accounts_map()` agora priorizam contas com personagens sincronizados no banco e maior nível antes de considerar `updated_at`, evitando que contas secundárias Nv. 1 atualizadas pelo check-in escondam o roster principal do HSR.
- **Fallback completo de peças no Build Inspector (`services/roster_service.py`):** extraídos `_load_roster_json_records()`, `_match_character_in_roster()` e `_format_build_pieces()` para que `parse_character_build_data()` também recupere e pontue `pieces` (relíquias/artefatos/discos), arma e `sets` a partir de `roster_data_{game_id}.json` quando o SQLite estiver vazio para o UID ativo.
- **Exibição de peças e estado vazio no inspetor (`static/js/modules/roster.js`, `static/js/app.js`, `static/index.html`):** usa `localRelics` do roster como fallback se `build.pieces` vier vazio, preserva o banner geral quando não há equipamentos e substitui o aviso enganoso de indisponibilidade por `"Nenhuma peça equipada neste personagem."` / `"No pieces equipped on this character."` (`281 testes aprovados`).

---

## [5.7.1] / Release Standalone [v1.3.1] - 2026-11-19

### 🐛 Corrigido & Segurança
- **Cofre local & LAN (`security_vault.py`, `routers/config.py`, `core/security.py`, `routers/system.py`):** configurações sensíveis agora criptografadas em `config.enc` (com migração de `config.json`), máscara automática de webhooks fora do loopback, autenticação de sessão LAN em rotas mutáveis/sensíveis, restrição de `/api/reset-data` para `POST`/`DELETE` (limpando todas as 15 tabelas e órfãos) e proteção contra SSRF/race no `/api/proxy_image`.
- **Auto-Updater (`updater.py`):** validação de ZipSlip usando `is_relative_to()` e preferência pelo executável esperado.
- **Calculadoras & Serviços (`build_calculator.py`, `calculators/`, `services/`):** corrigidos os IDs trocados de *Neuvillette*, *Charlotte* e *Furina*, alinhadas chaves de ascensão e `find_trash_relics`, corrigido hard pity 90 no ZZZ (`1.0`), breakpoints em `160.1–200.0`, `simulate_relic_swap`, match de nomes compostos (*Ruan Mei*, *Kaedehara Kazuha*, *Jane Doe*), isolamento por `active_uid` no endgame e invalidação completa de caches.
- **Frontend (`static/js/modules/`):** removido `cloneNode(true)` em `<sakuga-button>` (preservando Shadow DOM/VFX), eliminados listeners duplicados no simulador de gacha, adicionados `AbortController`/tokens contra race conditions, padronizada a chave `app_lang` e pausado o timer de contagem regressiva quando oculto.

### ⚡ Otimizado
- **SQLite & Backend (`database.py`, `server.py`, `core/static_cache.py`, `extractor.py`, `scrapers/`):** removida execução dupla de `init_db()` e `PRAGMA WAL` por query, adicionados índices compostos, cache em memória para configurações de segurança e mtimes estáticos, gravação em lote via `save_relics_batch()`, regexes pré-compiladas e offload via `asyncio.to_thread`.
- **Frontend (`static/index.html`, `static/style.css`, `static/css/gacha.css`, `static/js/`):** chamadas paralelas no inspetor (`Promise.allSettled`), re-renderização de cache na troca de idioma sem refetches ocultos, throttling `requestAnimationFrame` no chat SSE e remoção de código/CSS mortos (`279 testes aprovados`).

---

## [5.7.0] / Release Standalone [v1.3.0] - 2026-11-18

### ✨ Adicionado
- **Filtros rápidos de especialidades no ZZZ (`static/index.html`, `static/js/modules/roster.js`, `static/js/modules/i18n.js`):** barra de filtros rápidos com todas as especialidades (*Ataque*, *Atordoamento*, *Anomalia*, *Suporte*, *Defesa*, *Ruptura* e *Armeiro*) sincronizada com os filtros avançados do ZZZ.
- **Ícones oficiais no lugar dos genéricos (`assets/icons/`, `static/index.html`, `static/js/modules/api_client.js`, `static/js/modules/roster.js`):** 21 ícones oficiais transparentes (PNG 34×34) para especialidades do ZZZ, caminhos do HSR e armas do Genshin nos filtros, lista de personagens e `#build-inspector`.

### ♻️ Melhorado & Modularizado
- **Extração dinâmica de especialidades do Prydwen (`scrapers/scraper_zzz.py`, `static_data_manager.py`):** `get_agent_list()` e `_sync_zzz()` passam a extrair especialidade, elemento e raridade reais dos cards do Prydwen em vez de cair no fallback `"Attack"` / `"Physical"`.
- **Modularização do backend e frontend (`calculators/`, `static_data/`, `static/css/`, `static/js/modules/`):**
  - Calculadoras de gacha, breakpoints de velocidade/status e lacunas de conta separadas em `calculators/` e catálogos estáticos movidos de `static_data_manager.py` para JSONs em `static_data/`.
  - Gráficos e exportação de imagem movidos de `roster.js` para `roster_charts.js` e `card_exporter.js`; CSS dividido em `gacha.css`, `help_security.css`, `endgame_strategy.css` e `team_card.css`.
  - Redução de texto repetido e jargões na documentação, interface (PT/EN) e logs, mantendo intactas todas as nomenclaturas dos 3 jogos.

### 🐛 Corrigido
- **Ícones de elementos dos 3 jogos (`assets/elements/`, `services/media_service.py`, `static/js/modules/api_client.js`):** substituição da fonte antiga (403 no Wikia) pelos ícones corretos do Prydwen, adição de `zzz_wind`, normalização PT-BR e cache-busting (`?v=2`).
- **Compatibilidade CSS `line-clamp` (`static/style.css`):** adicionada a propriedade padrão `line-clamp` junto a `-webkit-line-clamp` no card de Affinitive Eidolons (desktop e mobile).

---

## [5.6.4] / Release Standalone [v1.2.4] - 2026-11-18

### 🐛 Corrigido
- **Auto-Shutdown apenas ao Fechar a Aba do Navegador (`services/browser_lifecycle_service.py`, `static/js/app.js`):**
  - Removida a expiração por timeout de heartbeat (`heartbeat_timeout_sec=None` por padrão) que encerrava o servidor quando a aba/janela ficava em segundo plano ou fora de foco (devido ao throttling/congelamento de timers pelos navegadores).
  - O servidor desktop agora só é encerrado automaticamente quando o navegador fecha efetivamente todas as abas locais (`pagehide` / `beforeunload` via `sendBeacon`), mantendo a tolerância de 4s para recarregamentos via `F5` e renovando o sinal ao retornar o foco (`visibilitychange` / `focus` / `resume`).

---

## [5.6.3] / Release Standalone [v1.2.3] - 2026-11-18

### 🐛 Corrigido
- **Localização PT-BR do Caminho Recordação no HSR (`services/translation_service.py`, `static/js/modules/i18n.js`, `static/js/modules/api_client.js`, `static/js/modules/roster.js`, `static/index.html`, `build_calculator.py`):**
  - Substituído o termo incorreto `"Reminiscência"`/`"Rememoração"` por `"Recordação"` na tradução do Caminho `Remembrance`, nos filtros de caminhos do Roster (HTML/i18n), no mapa de exibição do `api_client.js` e no nome do Desbravador em `build_calculator.py`.
  - Atualizado o filtro `roster.js` para reconhecer `"recorda"` além de `"remembr"`/`"reminisc"`.

---

## [5.6.2] / Release Standalone [v1.2.2] - 2026-11-18

### 🐛 Corrigido
- **Substituição do Executável e Reinício Automático no PyInstaller `--onefile` (`updater.py`, `static/js/modules/updater_ui.js`):**
  - O script `.bat` de atualização agora aguarda tanto o processo filho (`os.getpid()`) quanto o bootloader pai do PyInstaller (`os.getppid()`), evitando bloqueio de arquivo pelo `_MEI`.
  - Substituído `timeout` (incompatível com processos sem console) por `ping -n`, limitado `robocopy` a `/R:3 /W:1` e adicionado loop de substituição resiliente do `.exe` (`copy /Y` + fallback `move /Y` para `.old`) com suporte a pastas com espaços/parênteses e UTF-8 (`chcp 65001`).
  - Sanitização completa de variáveis internas `_PYI_*` / `_MEIPASS*` e entrada `_MEI` do `PATH` antes de reiniciar o novo executável (`start "" /D "%DST_DIR%" "%EXE_PATH%"`), além de reload automático da aba web assim que o servidor atualizado responde.

---

## [5.6.1] / Release Standalone [v1.2.1] - 2026-11-18

### 🐛 Corrigido
- **Scroll no Inspetor de Builds, Modais e Layout Mobile (`static/style.css`):** removidas regras globais de `overflow: visible` que bloqueavam a rolagem em `.inspector-body` e `.modal-card-content`, adicionado `flex-shrink: 0` em `.inspector-tabs`/`.inspector-panel`, corrigido o ajuste de altura de `.main-content` em telas móveis (`<= 768px`) e removido `content-visibility: auto` em `.char-card` para eliminar saltos na barra de rolagem.
- **Sobreposição de VFX Sakuga sobre Janelas de Personagens (`static/vendor/sakuga-vfx/button.js`, `progress.js`, `static/js/modules/roster.js`):** adicionada verificação `SakugaFX.isOccluded()` e `SakugaFX.clearTransient()` impedindo que barras de progresso (`<sakuga-progress>`) ou cliques em botões de fundo pintem nuvens/linhas por cima de `#build-inspector` ou modais abertos.
- **Status e Preview de Cookies via Tailscale / LAN (`static/js/modules/config_manager.js`):** fallback automático para `cookies_summary` de `GET /api/security/status` quando `/api/config` exige sessão LAN (`401`), exibindo corretamente `Cookies Conectados` e o preview mascarado no cofre.

---

## [5.6.0] / Release Standalone [v1.2.0] - 2026-11-17

### ✨ Adicionado
- **Sistema Completo de Auto-Updater via GitHub Releases (`version.py`, `updater.py`, `routers/updater.py`):**
  - Fonte única da versão em `version.py`, carimbada automaticamente pelo workflow do GitHub Actions (`.github/workflows/release.yml`) a partir da tag disparada antes do build do PyInstaller.
  - Endpoints `/api/updater/check`, `/api/updater/start` e `/api/updater/status` com consulta assíncrona não bloqueante (timeout 5s), comparação semântica via `packaging.version`, rastreamento de progresso (`0.0` a `1.0`), proteção contra ZipSlip e allowlist estrita de domínios oficiais do GitHub.
  - Substituição segura no Windows contornando trava de executável via script `.bat` desanexado em `%TEMP%` que aguarda o encerramento do PID atual, preserva banco SQLite, cofre criptográfico, `.env` e caches de jogos, reinicia o novo `.exe` e remove os temporários.
  - Modal interativo em Sakuga VFX (`#modal-sakuga-updater`), badge discreta da versão atual (`#app-version-badge`) e botão manual **Atualizar** no rodapé da barra lateral (`static/js/modules/updater_ui.js`).
- **Migração Integral da Interface para Sakuga VFX Offline-First (`static/vendor/sakuga-vfx/`):**
  - Integração local dos 11 Web Components (`button.js`, `checkbox.js`, `input.js`, `progress.js`, `radio.js`, `rating.js`, `slider.js`, `tabs.js`, `toast.js`, `toggle.js`, `tooltip.js`) garantindo funcionamento 100% sem internet no executável.
  - Revisão ponta a ponta corrigindo sobreposições (`overflow: visible`, camadas `z-index` abaixo de `canvas.sakuga-fx`), feedback imperativo (`done()`, `set()`) e filtragem para evitar renderização de fumaça/VFX em elementos ocultos na origem `(0, 0)`.
- **Empacotamento Standalone Windows & Automação CI/CD (`build.py`, `.github/workflows/release.yml`):**
  - Geração automática de `Cabeca_de_Droid.exe` (via PyInstaller sem console, com ícone na bandeja do sistema via `pystray` e resolução de caminhos em `%APPDATA%\Cabeca_de_Droid` / `sys._MEIPASS`) e artefato limpo `Cabeca_de_Droid-Windows-x64.zip`.
  - Pipeline automatizado no GitHub Actions para publicação de Releases ao enviar tags semânticas (`v*.*.*`) ou execução manual via `workflow_dispatch`.
- **Ciclo de Vida Desktop & Fallback de Auto-Login (`services/browser_lifecycle_service.py`, `auth.py`):**
  - Monitoramento de abas via heartbeat + `sendBeacon("/api/system/disconnect")`: quando empacotado (`.exe`), encerrar todas as janelas no navegador fecha automaticamente o servidor; em servidores contínuos/VM com `--no-browser`, o processo permanece online.
  - Fallback automático no auto-login HoYoLAB via Playwright usando Google Chrome ou Microsoft Edge do sistema caso o Chromium embutido não esteja presente na máquina do usuário.
- **Eidolons Adicionais no HSR (`ex_ranks_json`), Filtros & Ordenações do Roster:**
  - Extração e exibição de Affinitive Eidolons no inspetor, lista de personagens e card de time, além de resolução livre de colisões MD5 para variantes/Desbravadores.
  - Ordenação alfabética (A–Z / Z–A), filtros universais de auditoria de build, filtros específicos por jogo, endpoints manuais de snapshot (`POST /api/history/{game_id}/snapshot`) e sincronização global (`POST /api/sync/all`).

### ⚡ Otimizado & Corrigido
- **Desempenho de Scroll no Modo Lista:** Removidos passes pesados de blur/drop-shadow e thrashing de `content-visibility` durante rolagem contínua em galerias grandes.
- **Configurações em Layout Horizontal (Desktop):** Reorganização em grade horizontal na aba Configurações para melhor aproveitamento de tela em resoluções maiores que 768px.
- **Extração Endgame Prydwen:** Limpeza aprimorada de estatísticas flexíveis/qualificadas por personagem.

### 🧪 Testes Unitários & Documentação
- Adicionadas suítes `tests/test_updater_suite.py`, `tests/test_packaging_suite.py`, `tests/test_tray_suite.py`, `tests/test_hsr_affinitive_eidolons.py`, `tests/test_hsr_variant_resolution.py` e `tests/test_prydwen_endgame_and_names.py`.
- Cobertura total ampliada para **230 testes unitários nativos aprovados** com mocks offline (`unittest`).
- Documentação completa atualizada (`README.md`, `README.pt-BR.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `docs/db_schema.md`, `requirements.txt`, `.gitignore`).

---

## [5.5.0] - 2026-11-12

### ✨ Visualização Avançada do Roster (Modo Grade & Lista Enriquecida)
- **Alternância Dinâmica de Modo (Grid vs List):**
  - Implementado seletor visual de alternância entre Modo Grade (cards verticais focados em arte) e Modo Lista (linhas horizontais de alta densidade informativa) no cabeçalho de cada jogo.
  - Persistência reativa da preferência do usuário no `localStorage` (`roster_view_mode`), com transições CSS suaves sem recarregamento de rede.
- **Layout de Linha Rica em 5 Colunas (Opção C):**
  - **Coluna 1 (Personagem & Identidade):** Avatar HD otimizado com borda temática elemental, badge de rank de ascensão (`C0-C6`, `E0-E6`, `M0-M6`), elemento oficial e caminho/classe tática.
  - **Coluna 2 (Arma / Cone de Luz / Motor W):** Thumbnail oficial do equipamento, nível atual, grau de refinamento/sobreposição (`S1-S5`, `R1-R5`, `W1-W5`) e badge explícita de raridade (`5★`, `4★`, `3★`, `1★` ou `Rank S / Rank A / Rank B`).
  - **Coluna 3 (Strip de Peças Equipadas):** Exibição em linha dos ícones oficiais de cada peça de relíquia/artefato/disco equipada, com borda e iluminação radial 100% fiéis à raridade do item (Dourado 5★, Roxo 4★, Azul 3★) e indicador minimalista no canto superior com a nota de rolagem (`SSS` a `D`).
  - **Coluna 4 (Conjuntos Ativos & Eficiência de Slots):** Tags de bônus de conjunto ativos (`4p` e `2p`) com barra de progresso visual de slots preenchidos.
  - **Coluna 5 (Avaliação & Ação):** Badge de Roll Value Grade geral da build com score em pontos e botão de inspeção direta no drawer lateral.

### 🛡️ Correção & Consolidação de Raridades de Equipamentos
- **Motores W (Zenless Zone Zero):**
  - Corrigida a classificação de `Motor da Constelação` (*Starlight Engine*) e `Perfuratriz - Eixo Vermelho` (*Drill Rig - Red Axis*) para **4★** (Rank A).
  - Corrigido `Espinhaço Afiado` (*Sharpened Stinger*, assinatura de Jane Doe) para **5★** (Rank S).
  - Normalização completa de todo o acervo de motores de ZZZ no manifesto `static_data/weapon_rarities.json`.
- **Cones de Luz (Honkai: Star Rail):**
  - Consolidados no manifesto cones 5★ de alta relevância (incluindo `Luzes Noturnas`, `Euforia Repleta de Bênçãos`, `Ao Longo da Margem Transitória`, `Onde os Sonhos Deveriam Repousar`, `Sono Profundo`, `Na Queda de Um Aeon`), bem como todas as linhas de 4★ e 3★.
- **Armas (Genshin Impact):**
  - Mapeamento exaustivo de armas 5★ (`Lira do Tecedor da Luz`, `Asa Gelada do Lago Branco`, etc.), 4★, 3★ e armas 1★ iniciais (`Espadão do Julgamento`, `Lâmina Sem Fio`, `Arco do Caçador`).
- **Resolução de Conflito de Borda CSS (Cascade Specificity):**
  - Corrigida a cascata no `style.css` onde classes de nota de rolagem (`.grade-s`, `.grade-a`) sobrescreviam as cores de borda de `.rarity-5`, eliminando o problema em que relíquias 5★ apareciam roxas ou azuis.
- **Sincronização e Backfill Automatizado no Banco:**
  - `backfill_roster_rarities_and_sets()` em `database.py` recalcula e persiste automaticamente no SQLite as raridades oficiais e conjuntos de todas as contas cadastradas.
  - Inclusão do campo `rarity` no detalhamento de peças retornado pelo serviço `services/roster_service.py`.

### 🔍 Otimizações de Busca & Interação com Debounce Reativo
- **Busca em Tempo Real com `createDebouncedSearch`:**
  - Utilitário integrado com debounce calibrado em 300ms, guarda de comprimento mínimo (2 caracteres) e cancelamento reativo via `AbortController` para requisições em trânsito.
- **Otimização de Consultas SQL:**
  - Eliminação de projeções `SELECT *` e resolução de consultas em lote nas tabelas de histórico e elenco.

### 🧪 Testes Unitários
- Adicionado `tests/test_roster_view_mode_suite.py` e `tests/test_search_debounce_suite.py`.
- Cobertura expandida para **181 testes unitários nativos aprovados** com 100% de sucesso.

---

## [5.4.0] - 2026-11-12

### ⚡ Otimizações & Auditoria Completa de Performance (17/17 Itens)
- **Compressão e Transferência de Rede:**
  - **Compressão HTTP Gzip:** Habilitado `GZipMiddleware(minimum_size=1000)` em `server.py`, reduzindo o tráfego de payloads JSON e estáticos em até 75%.
  - **Políticas de Cache-Control:** Implementada política de cache em `core/security.py` definindo `Cache-Control: public, max-age=86400` para assets estáticos e `no-cache, no-store, must-revalidate` para endpoints REST e HTML raiz.
  - **Prontidão para CDN de Borda:** Adicionado cabeçalho `CDN-Cache-Control: public, max-age=2592000` (30 dias) e criado template Nginx pronto para produção em `scripts/nginx-cabeca-de-droid.conf`.
  - **Remoção de Dependências Não Utilizadas:** Higienizado `requirements.txt` com a remoção dos pacotes obsoletos `urllib3` e `brotli`.
- **Otimização de Banco de Dados & Consultas SQLite:**
  - **Eliminação de Consultas N+1:** Em `database.py`, leitura em lote de relíquias (`WHERE uid IN (...)`) reduzindo de $N$ queries para 1 query por jogo; contagem de personagens agregada em lote via SQL único.
  - **Projeções de Colunas Específicas:** Substituídas todas as consultas `SELECT *` em tabelas críticas (`account_snapshots`, `roster_data`, `overview_data`, `daily_notes`) por seleções explícitas de colunas indexadas.
  - **Paginação em Listas com Crescimento Temporal:** Adicionados parâmetros `limit` e `offset` nas funções de banco e endpoints de histórico (`/api/history/{game_id}` e `/api/codes/history/{game_id}`) para conter o consumo de memória em bases com muitos snapshots.
- **Camada de Caching em Memória & Profiling de Requisições:**
  - **Cache em Memória de Roster e Endgame:** Implementado cache com TTL de 60 segundos em `services/roster_service.py` e `services/endgame_service.py`, com invalidação reativa automática ao sincronizar dados (`sync_service.py`), deletar contas ou alternar perfil ativo.
  - **Monitoramento de Latência em Tempo Real:** Adicionado middleware `request_latency_tracker_middleware` em `server.py` injetando o cabeçalho `X-Process-Time` e gerando logs de alerta `[PERF-WARN]` para requisições com tempo de processamento $>500\text{ms}$.
- **Performance e Carregamento no Frontend Vanilla Web:**
  - **Code-Splitting e Importação Dinâmica:** Módulos pesados de simulação e rastreamento de gacha (`gacha_sim.js`, `gacha_tracker.js`) desvinculados do carregamento inicial em `static/js/app.js` e carregados sob demanda via `window.loadGachaModules()` ou em tempo ocioso via `requestIdleCallback`.
  - **Desduplicação de Requisições em Voo:** Deduplicação inteligente de requisições simultâneas em `roster.js` e eliminação de chamadas redundantes a `/api/endgame` e `/api/overview`.
  - **Scripts de Terceiros Diferidos:** Atributo `defer` adicionado a `marked.min.js` e `html2canvas.min.js` em `static/index.html`.
  - **Skeletons de Carregamento (Zero-FOUC):** Implementados layouts animados de shimmer skeleton em CSS em `static/style.css` e aplicados nos fluxos de carregamento de Endgame, Ordem de Farm e Rastreador de Gacha.
  - **Fontes Auto-Hospedadas:** Tipografias `Inter` e `Outfit` baixadas localmente em formato otimizado WOFF2 (`static/fonts/`), configuradas com `@font-face` e `font-display: swap;`, eliminando conexões externas bloqueantes com o Google Fonts.
  - **Pipeline Dinâmico de Imagens WebP:** Rota `/api/proxy_image` em `routers/system.py` estendida com redimensionamento LANCZOS via Pillow e conversão WebP sob demanda (`&w=160&format=webp`), reduzindo o peso de avatares em até 95%.
  - **Virtualização Nativa CSS de Listas Longas:** Aplicadas regras de `content-visibility: auto` e `contain-intrinsic-size` em `.char-card` e `.timeline-item`, suprimindo o custo de cálculo de layout e renderização de cards fora da viewport.

### 🧪 Testes Unitários
- **Nova Suíte de Testes de Paginação:** Adicionado `tests/test_pagination_suite.py` cobrindo o fatiamento e limites das consultas no SQLite e endpoints HTTP.
- **Aprovação Total:** Cobertura expandida para **164 testes unitários automatizados** com 100% de sucesso.

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
