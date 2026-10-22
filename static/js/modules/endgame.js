// ==========================================================================
// Módulo: endgame.js
// Cabeça de Droid - Vanilla ES6 Module
// ==========================================================================

// ==========================================================================
// RENDERIZAÇÃO DO PAINEL DE ENDGAME COLETADO (HSR, GENSHIN, ZZZ)
// ==========================================================================
const activeEndgameModeIdx = { hsr: 0, genshin: 0, zzz: 0 };
const activeEndgameView = { hsr: "single", genshin: "single", zzz: "single" };
const cachedEndgameData = { hsr: null, genshin: null, zzz: null };

function getEndgameModeIcon(modeId) {
    if (modeId === "moc") return "fa-trophy";
    if (modeId === "pure_fiction") return "fa-wand-magic-sparkles";
    if (modeId === "apocalyptic_shadow") return "fa-skull";
    if (modeId === "spiral_abyss") return "fa-dungeon";
    if (modeId === "imaginarium_theater") return "fa-masks-theater";
    if (modeId === "shiyu_defense") return "fa-shield-halved";
    return "fa-award";
}

function normalizeEndgameChar(char, gameId) {
    if (!char) return char;
    let name = (char.name || "").trim();
    const id = String(char.id || "").trim();
    
    // Normaliza nomes desconhecidos do Desbravador e Viajante
    if (!name || name.toLowerCase().includes("desconhecido") || name.toLowerCase().includes("avatar")) {
        if (id.startsWith("800") || id.startsWith("801") || name.includes("8009") || name.includes("800")) {
            name = "Desbravador(a)";
            char.name = name;
            if (!char.element) char.element = "ice";
            char.rarity = 5;
        } else if (id === "10000005" || id === "10000007" || name.includes("1000000")) {
            name = "Viajante";
            char.name = name;
            char.rarity = 5;
        }
    }

    // Sanitiza URL de Genshin se contiver .png.png ou ide_
    if (char.icon && typeof char.icon === "string") {
        let cleanIcon = char.icon.replace(/\.png\.png/gi, ".png").replace(/\/(UI_AvatarIcon_|UI_Gacha_AvatarImg_|UI_Costume_)ide_/gi, "/$1");
        if (cleanIcon.includes("/api/proxy_image?url=")) {
            const parts = cleanIcon.split("/api/proxy_image?url=");
            let decoded = decodeURIComponent(parts[1] || "");
            if (decoded.includes("ide_") || decoded.includes(".png.png")) {
                decoded = decoded.replace(/\.png\.png/gi, ".png").replace(/\/(UI_AvatarIcon_|UI_Gacha_AvatarImg_|UI_Costume_)ide_/gi, "/$1");
                cleanIcon = `/api/proxy_image?url=${encodeURIComponent(decoded)}`;
            }
        }
        char.icon = cleanIcon;
    }

    const roster = globalRoster[gameId] || [];
    const found = roster.find(c => (c.name || "").toLowerCase() === name.toLowerCase());
    if (found) {
        if ((!char.icon || char.icon.includes(`${gameId}_icon.png`)) && found.icon) char.icon = found.icon;
        if (!char.element && found.element) char.element = found.element;
        if (!char.rarity && found.rarity) char.rarity = found.rarity;
        if (!char.rank_str && found.rank_str) char.rank_str = found.rank_str;
    }
    
    if (!char.icon) {
        if (name.toLowerCase().includes("desbravador") || name.toLowerCase().includes("trailblazer")) {
            char.icon = `/assets/hsr_icon.png`;
        } else if (name.toLowerCase().includes("viajante") || name.toLowerCase().includes("traveler")) {
            char.icon = `/assets/genshin_icon.png`;
        } else if (name.toLowerCase().includes("bangboo")) {
            char.icon = `/assets/zzz_icon.png`;
        } else {
            char.icon = `/assets/${gameId}_icon.png`;
        }
    }
    return char;
}

function renderEndgameTeamCard(team, gameId) {
    let charsHtml = "";
    if (team.characters && team.characters.length > 0) {
        charsHtml = `<div class="endgame-chars-row">`;
        team.characters.forEach(rawChar => {
            const char = normalizeEndgameChar(rawChar, gameId);
            const elemKey = (char.element || "").toLowerCase();
            const elemClass = ELEMENT_MAPPING[elemKey] || "el-physical";
            const rarityClass = (char.rarity === 5 || char.rarity === "5" || String(char.rarity).toUpperCase() === "S") ? "rarity-5" : "rarity-4";
            const fallbackIcon = `/assets/${gameId}_icon.png`;
            const avatarSrc = char.icon || fallbackIcon;
            const rankBadge = char.rank_str ? `<span class="endgame-char-rank-badge">${char.rank_str}</span>` : "";

            charsHtml += `
                <div class="endgame-char-mini ${elemClass} ${rarityClass}" data-char-name="${char.name}" title="${char.name} (Nv. ${char.level || 80}) • Inspecionar Build">
                    <div class="endgame-char-avatar-box" style="position: relative; width: 38px; height: 38px; min-width: 38px; min-height: 38px; max-width: 38px; max-height: 38px; flex-shrink: 0; display: inline-block;">
                        <img src="${avatarSrc}" class="endgame-char-avatar" style="width: 38px; height: 38px; min-width: 38px; min-height: 38px; max-width: 38px; max-height: 38px; border-radius: 50%; object-fit: cover; display: block;" onerror="this.onerror=null; this.src='${fallbackIcon}';" alt="${char.name}">
                        ${elemKey && elemKey !== "bangboo" ? `<img src="/assets/elements/${gameId}_${elemKey}.png" class="endgame-char-elem-icon" style="position: absolute; bottom: -2px; right: -2px; width: 14px; height: 14px; min-width: 14px; min-height: 14px; max-width: 14px; max-height: 14px; border-radius: 50%; padding: 1px; object-fit: contain;" onerror="this.style.display='none';" alt="">` : ""}
                        ${rankBadge}
                    </div>
                    <span class="endgame-char-name-label">${char.name}</span>
                    <span class="endgame-char-lvl-label">Nv. ${char.level || 80}</span>
                </div>
            `;
        });
        charsHtml += `</div>`;
    }

    let monstersHtml = "";
    if (team.monsters && team.monsters.length > 0) {
        monstersHtml = `<div class="endgame-enemies-row">`;
        team.monsters.forEach(m => {
            const mName = m.name || "Inimigo";
            const mLvl = m.level ? ` (Nv.${m.level})` : "";
            monstersHtml += `<span class="endgame-enemy-chip" title="${mName}${mLvl}"><i class="fa-solid fa-skull"></i> ${mName}${mLvl}</span>`;
        });
        monstersHtml += `</div>`;
    }

    return `
        <div class="endgame-team-node">
            <div class="endgame-team-node-header">
                <div class="endgame-team-title-left">
                    <span class="endgame-side-dot"></span>
                    <span>${team.name}</span>
                </div>
                <span style="font-size: 10.5px; color: #94a3b8; font-weight: 500;">${(team.characters || []).length} Mobilizados</span>
            </div>
            ${charsHtml}
            ${monstersHtml}
        </div>
    `;
}

// Deduplica requisições simultâneas de endgame (startup + loadRoster + polling chamavam em paralelo)
const _endgameInflight = {};
function loadEndgame(gameId) {
    if (_endgameInflight[gameId]) return _endgameInflight[gameId];
    _endgameInflight[gameId] = _loadEndgameImpl(gameId).finally(() => {
        _endgameInflight[gameId] = null;
    });
    return _endgameInflight[gameId];
}

async function _loadEndgameImpl(gameId) {
    const container = document.getElementById(`endgame-container-${gameId}`);
    const badgeEl = document.getElementById(`endgame-badge-${gameId}`);
    if (!container) return;

    try {
        const res = await fetch(`/api/endgame/${gameId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        
        renderEndgame(gameId, data);
    } catch (err) {
        console.error(`Erro ao carregar endgame de ${gameId}:`, err);
        if (container) {
            container.innerHTML = `
                <div class="endgame-empty-state">
                    <i class="fa-solid fa-triangle-exclamation" style="color: #f87171;"></i>
                    <p>Erro ao carregar dados de endgame.</p>
                    <span>${err.message || "Tente sincronizar sua conta novamente."}</span>
                    <button class="endgame-empty-action-btn" onclick="document.querySelector('.sync-game-btn[data-game=\\'${gameId}\\']')?.click()">
                        <i class="fa-solid fa-rotate"></i> Tentar Sincronizar
                    </button>
                </div>
            `;
        }
    }
}

function renderEndgame(gameId, data) {
    const container = document.getElementById(`endgame-container-${gameId}`);
    const badgeEl = document.getElementById(`endgame-badge-${gameId}`);
    if (!container) return;

    if (!data || !data.has_data || !data.modes || data.modes.length === 0) {
        if (badgeEl) badgeEl.innerText = "Sem Dados";
        const gameNames = { hsr: "Honkai: Star Rail", genshin: "Genshin Impact", zzz: "Zenless Zone Zero" };
        const modeExamples = {
            hsr: "Caos da Memória (MoC), Ficção Pura ou Sombra Apocalíptica",
            genshin: "Abismo Espiral ou Teatro Imaginário",
            zzz: "Defesa Shiyu"
        };
        container.innerHTML = `
            <div class="endgame-empty-state">
                <i class="fa-solid fa-hourglass-half"></i>
                <p>Nenhum registro de Endgame recente coletado para ${gameNames[gameId] || gameId.toUpperCase()}.</p>
                <span>Conclua andares do ${modeExamples[gameId] || "Endgame"} no jogo e sincronize seu Roster para visualizar os times e pontuações aqui!</span>
                <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin-top: 12px;">
                    <button class="endgame-empty-action-btn" onclick="document.querySelector('.sync-game-btn[data-game=\\'${gameId}\\']')?.click()">
                        <i class="fa-solid fa-rotate"></i> Sincronizar ${gameId.toUpperCase()} Agora
                    </button>
                    <button class="endgame-empty-action-btn" style="background: linear-gradient(135deg, #0284c7, #38bdf8); border: none;" onclick="activeEndgameView['${gameId}'] = 'team_matcher'; renderEndgame('${gameId}', { has_data: true, modes: [] });">
                        <i class="fa-solid fa-people-group"></i> Ver Times Recomendados (Team Matcher)
                    </button>
                </div>
            </div>
        `;
        return;
    }

    cachedEndgameData[gameId] = data;

    // Métricas Totais
    const totalStars = data.modes ? data.modes.reduce((acc, m) => acc + (typeof m.stars === 'number' ? m.stars : 0), 0) : 0;
    const maxTotalStars = data.modes ? data.modes.reduce((acc, m) => acc + (typeof m.max_stars === 'number' ? m.max_stars : 0), 0) : 0;

    // Atualiza badge de resumo no botão da sub-navegação
    if (badgeEl) {
        if (totalStars > 0) {
            badgeEl.innerHTML = `<i class="fa-solid fa-star" style="color: #facc15;"></i> ${totalStars}★ (${data.modes.length} Modos)`;
        } else {
            badgeEl.innerText = `${(data.modes || []).length} Modos`;
        }
    }

    const currentView = activeEndgameView[gameId] || "single";
    const currentIdx = Math.min(activeEndgameModeIdx[gameId] || 0, Math.max(0, (data.modes ? data.modes.length - 1 : 0)));

    // 1. MASTER HEADER COM RESUMO E TOGGLE DE VISÃO
    const gameLabels = { hsr: "Honkai: Star Rail", genshin: "Genshin Impact", zzz: "Zenless Zone Zero" };
    let starsDisplay = `${totalStars}★`;
    if (maxTotalStars > 0) starsDisplay = `${totalStars}/${maxTotalStars}★`;

    let masterHeaderHtml = `
        <div class="endgame-master-header">
            <div class="endgame-master-title-area">
                <span class="endgame-game-badge">
                    <i class="fa-solid fa-shield-halved"></i> ${gameLabels[gameId] || gameId.toUpperCase()}
                </span>
                <div class="endgame-master-stats-group">
                    <span class="endgame-summary-chip gold" title="Total de Estrelas Coletadas em Todos os Modos">
                        <i class="fa-solid fa-star"></i> ${starsDisplay}
                    </span>
                    <span class="endgame-summary-chip cyan" title="Modos Ativos com Registros">
                        <i class="fa-solid fa-circle-check"></i> ${(data.modes || []).length} ${(data.modes || []).length === 1 ? 'Modo' : 'Modos Ativos'}
                    </span>
                    ${data.uid ? `<span class="endgame-summary-chip purple" title="UID da Conta"><i class="fa-solid fa-id-card"></i> UID ${data.uid}</span>` : ''}
                </div>
            </div>
            <div class="endgame-view-toggle-group">
                <button class="endgame-view-toggle-btn ${currentView === 'single' ? 'active' : ''}" data-view="single" data-game="${gameId}">
                    <i class="fa-solid fa-table-columns"></i> Modo Focado
                </button>
                <button class="endgame-view-toggle-btn ${currentView === 'all' ? 'active' : ''}" data-view="all" data-game="${gameId}">
                    <i class="fa-solid fa-list-ul"></i> Visão Geral (${(data.modes || []).length})
                </button>
                <button class="endgame-view-toggle-btn ${currentView === 'team_matcher' ? 'active' : ''}" data-view="team_matcher" data-game="${gameId}" style="border-left: 2px solid #38bdf8; font-weight: 700;">
                    <i class="fa-solid fa-people-group" style="color: #38bdf8;"></i> Team Matcher
                </button>
            </div>
        </div>
    `;

    // 2. BARRA DE SELEÇÃO DE MODOS (SEGMENTED TABS)
    let pillsHtml = `<div class="endgame-mode-selector-bar">`;
    
    // Botão Visão Geral
    pillsHtml += `
        <button class="endgame-mode-tab-btn ${currentView === 'all' ? 'active' : ''}" data-mode-idx="all" data-game="${gameId}">
            <i class="fa-solid fa-list-ul"></i>
            <span>Todos os Modos</span>
            <span class="tab-star-pill">${starsDisplay}</span>
        </button>
    `;

    data.modes.forEach((mode, idx) => {
        const icon = getEndgameModeIcon(mode.id);
        let starPill = "";
        if (mode.stars !== null && mode.stars !== undefined && mode.stars !== "?") {
            starPill = `<span class="tab-star-pill">⭐ ${mode.stars}${mode.max_stars ? `/${mode.max_stars}` : ''}</span>`;
        }

        const isActive = (currentView === "single" && idx === currentIdx) ? "active" : "";
        pillsHtml += `
            <button class="endgame-mode-tab-btn ${isActive}" data-mode-idx="${idx}" data-game="${gameId}">
                <i class="fa-solid ${icon}"></i>
                <span>${mode.name}</span>
                ${starPill}
            </button>
        `;
    });
    pillsHtml += `</div>`;

    // 3. CONTEÚDO PRINCIPAL (VISÃO INDIVIDUAL OU VISÃO GERAL)
    let contentHtml = "";

    if (currentView === "all") {
        // VISÃO GERAL: TODOS OS MODOS EM LISTA (UM EMBAIXO DO OUTRO)
        let overviewCardsHtml = `<div class="endgame-overview-matrix">`;
        data.modes.forEach((mode, mIdx) => {
            const icon = getEndgameModeIcon(mode.id);
            let modeMetrics = "";
            if (mode.stars !== null && mode.stars !== undefined && mode.stars !== "?") {
                modeMetrics += `<span class="endgame-metric-chip gold-stars"><i class="fa-solid fa-star"></i> ${mode.stars}${mode.max_stars ? `/${mode.max_stars}` : ''}</span>`;
            }
            if (mode.metric_label && mode.metric_value && mode.metric_value !== "?" && mode.metric_value !== "None") {
                const isScore = mode.metric_label.toLowerCase().includes("pontuação") || mode.metric_label.toLowerCase().includes("score");
                const isRounds = mode.metric_label.toLowerCase().includes("rodada") || mode.metric_label.toLowerCase().includes("round");
                const chipClass = isScore ? "blue-score" : (isRounds ? "purple-rounds" : "");
                const chipIcon = isScore ? "fa-bolt" : (isRounds ? "fa-clock-rotate-left" : "fa-award");
                modeMetrics += `<span class="endgame-metric-chip ${chipClass}"><i class="fa-solid ${chipIcon}"></i> ${mode.metric_value}</span>`;
            }

            let teamsListHtml = "";
            if (mode.teams && mode.teams.length > 0) {
                const teamCountClass = `teams-count-${mode.teams.length}`;
                teamsListHtml = `<div class="endgame-teams-grid ${teamCountClass}">`;
                mode.teams.forEach(team => {
                    teamsListHtml += renderEndgameTeamCard(team, gameId);
                });
                teamsListHtml += `</div>`;
            }

            overviewCardsHtml += `
                <div class="endgame-overview-mode-card">
                    <div class="endgame-overview-card-header">
                        <div class="endgame-overview-title">
                            <i class="fa-solid ${icon}"></i>
                            <span>${mode.name}</span>
                            ${mode.badge ? `<span style="font-size: 10px; padding: 2px 6px; border-radius: 5px; background: rgba(255,255,255,0.08); font-weight: 700;">${mode.badge}</span>` : ""}
                            ${mode.stage ? `<span class="endgame-mode-stage-desc">${mode.stage}</span>` : ""}
                        </div>
                        <div class="endgame-metrics-group">
                            ${modeMetrics}
                        </div>
                    </div>
                    ${teamsListHtml}
                </div>
            `;
        });
        overviewCardsHtml += `</div>`;
        contentHtml = overviewCardsHtml;

    } else {
        // VISÃO DETALHADA DO MODO SELECIONADO
        const activeMode = data.modes[currentIdx];
        let metricsHtml = "";
        if (activeMode.stars !== null && activeMode.stars !== undefined && activeMode.stars !== "?") {
            metricsHtml += `
                <span class="endgame-metric-chip gold-stars" title="Estrelas">
                    <i class="fa-solid fa-star"></i> ${activeMode.stars}${activeMode.max_stars ? `/${activeMode.max_stars}` : ''} Estrelas
                </span>
            `;
        }
        if (activeMode.metric_label && activeMode.metric_value && activeMode.metric_value !== "?" && activeMode.metric_value !== "None") {
            const isScore = activeMode.metric_label.toLowerCase().includes("pontuação") || activeMode.metric_label.toLowerCase().includes("score");
            const isRounds = activeMode.metric_label.toLowerCase().includes("rodada") || activeMode.metric_label.toLowerCase().includes("round");
            const chipClass = isScore ? "blue-score" : (isRounds ? "purple-rounds" : "");
            const chipIcon = isScore ? "fa-bolt" : (isRounds ? "fa-clock-rotate-left" : "fa-award");
            metricsHtml += `
                <span class="endgame-metric-chip ${chipClass}">
                    <i class="fa-solid ${chipIcon}"></i> ${activeMode.metric_value} ${!isScore && !isRounds ? "" : (isRounds ? "Rodadas" : "Pontos")}
                </span>
            `;
        }

        let teamsHtml = "";
        if (activeMode.teams && activeMode.teams.length > 0) {
            const teamCountClass = `teams-count-${activeMode.teams.length}`;
            teamsHtml = `<div class="endgame-teams-grid ${teamCountClass}">`;
            activeMode.teams.forEach(team => {
                teamsHtml += renderEndgameTeamCard(team, gameId);
            });
            teamsHtml += `</div>`;
        }

        const activeIcon = getEndgameModeIcon(activeMode.id);
        contentHtml = `
            <div class="endgame-active-mode-pane">
                <div class="endgame-mode-meta-header">
                    <div class="endgame-mode-title-area">
                        <div class="endgame-mode-main-title">
                            <i class="fa-solid ${activeIcon}"></i>
                            <span>${activeMode.name}</span>
                            ${activeMode.badge ? `<span style="font-size: 10px; padding: 2px 6px; border-radius: 5px; background: rgba(255,255,255,0.08); font-weight: 700;">${activeMode.badge}</span>` : ""}
                        </div>
                        ${activeMode.stage ? `<span class="endgame-mode-stage-desc">${activeMode.stage}</span>` : ""}
                    </div>
                    <div class="endgame-metrics-group">
                        ${metricsHtml}
                    </div>
                </div>
                ${teamsHtml}
            </div>
        `;
    }

    if (currentView === "team_matcher") {
        container.innerHTML = masterHeaderHtml + `<div id="team-matcher-container-${gameId}"><div class="endgame-loading-spinner"><i class="fa-solid fa-spinner fa-spin"></i> Carregando compatibilidade de equipes...</div></div>`;
        renderTeamMatcher(gameId);
    } else {
        container.innerHTML = masterHeaderHtml + pillsHtml + contentHtml;
    }

    // Configura botões de alternância de visão (Modo Focado vs Visão Geral vs Team Matcher)
    container.querySelectorAll(".endgame-view-toggle-btn").forEach(tBtn => {
        tBtn.addEventListener("click", () => {
            const view = tBtn.getAttribute("data-view");
            activeEndgameView[gameId] = view;
            renderEndgame(gameId, cachedEndgameData[gameId]);
        });
    });

    // Configura cliques nos botões da barra de modos
    container.querySelectorAll(".endgame-mode-tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const modeIdxAttr = btn.getAttribute("data-mode-idx");
            if (modeIdxAttr === "all") {
                activeEndgameView[gameId] = "all";
            } else {
                activeEndgameView[gameId] = "single";
                activeEndgameModeIdx[gameId] = parseInt(modeIdxAttr, 10);
            }
            renderEndgame(gameId, cachedEndgameData[gameId]);
        });
    });

    // Configura cliques nos mini-cards para abrir o Build Inspector
    container.querySelectorAll(".endgame-char-mini").forEach(miniBtn => {
        miniBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            const charName = miniBtn.getAttribute("data-char-name");
            if (!charName) return;

            const found = (globalRoster[gameId] || []).find(c => (c.name || "").toLowerCase() === charName.toLowerCase());
            if (found) {
                inspectCharacter(gameId, found);
            } else {
                const quickChar = {
                    name: charName,
                    level: 80,
                    rarity: 5,
                    element: "fire",
                    icon: `/assets/${gameId}_icon.png`,
                    rank_str: "E0"
                };
                inspectCharacter(gameId, quickChar);
            }
        });
    });
}

// ==========================================================================
// ENDGAME TEAM MATCHER (METAGAME X ROSTER REAL)
// ==========================================================================
const teamMatcherFilterState = {
    hsr: { mode: "", minMatch: 0 },
    genshin: { mode: "", minMatch: 0 },
    zzz: { mode: "", minMatch: 0 }
};

async function renderTeamMatcher(gameId) {
    const subContainer = document.getElementById(`team-matcher-container-${gameId}`);
    if (!subContainer) return;

    const state = teamMatcherFilterState[gameId] || { mode: "", minMatch: 0 };
    
    try {
        let url = `/api/endgame/team-match/${gameId}?min_match=${state.minMatch}`;
        if (state.mode) {
            url += `&mode=${encodeURIComponent(state.mode)}`;
        }
        
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        
        renderTeamMatcherContent(gameId, subContainer, data);
    } catch (err) {
        console.error(`Erro ao carregar Team Matcher para ${gameId}:`, err);
        subContainer.innerHTML = `
            <div class="endgame-empty-state">
                <i class="fa-solid fa-triangle-exclamation" style="color: #f87171;"></i>
                <p>Falha ao cruzar composições de endgame.</p>
                <span>${err.message}</span>
            </div>
        `;
    }
}

function renderTeamMatcherContent(gameId, container, data) {
    const state = teamMatcherFilterState[gameId] || { mode: "", minMatch: 0 };
    const modesList = data.available_modes || [];
    
    // Barra de Filtros
    let filterBarHtml = `
        <div class="team-matcher-filter-bar">
            <div class="team-matcher-filter-group">
                <span style="font-size: 12px; font-weight: 700; color: #94a3b8;"><i class="fa-solid fa-filter"></i> Filtrar:</span>
                <select class="team-matcher-select" id="matcher-mode-select-${gameId}">
                    <option value="" ${state.mode === "" ? "selected" : ""}>Todos os Modos (${modesList.length})</option>
                    ${modesList.map(m => `<option value="${m}" ${state.mode === m ? "selected" : ""}>${m}</option>`).join("")}
                </select>
                <select class="team-matcher-select" id="matcher-compat-select-${gameId}">
                    <option value="0" ${state.minMatch == 0 ? "selected" : ""}>Todas as Composições</option>
                    <option value="50" ${state.minMatch == 50 ? "selected" : ""}>Viáveis (≥ 50%)</option>
                    <option value="75" ${state.minMatch == 75 ? "selected" : ""}>Quase Prontas (≥ 75%)</option>
                    <option value="100" ${state.minMatch == 100 ? "selected" : ""}>100% Completas (Prontas)</option>
                </select>
            </div>
            <div class="team-matcher-filter-group">
                <span style="font-size: 11.5px; color: #38bdf8; font-weight: 700;">
                    <i class="fa-solid fa-circle-check"></i> ${data.ready_teams_count} Prontas
                </span>
                <span style="font-size: 11.5px; color: #94a3b8;">
                    de ${data.total_teams} analisadas
                </span>
            </div>
        </div>
    `;

    if (!data.teams || data.teams.length === 0) {
        container.innerHTML = filterBarHtml + `
            <div class="endgame-empty-state" style="margin-top: 16px;">
                <i class="fa-solid fa-users-slash"></i>
                <p>Nenhuma equipe metagame encontrada com os filtros selecionados.</p>
                <span>Tente reduzir o filtro de compatibilidade mínima para visualizar equipes com sugestão de substitutos.</span>
            </div>
        `;
        setupTeamMatcherEvents(gameId, container);
        return;
    }

    let cardsHtml = `<div class="team-matcher-grid" style="margin-top: 16px;">`;
    data.teams.forEach(team => {
        cardsHtml += renderTeamMatchCard(team, gameId);
    });
    cardsHtml += `</div>`;

    container.innerHTML = `<div class="team-matcher-section">${filterBarHtml}${cardsHtml}</div>`;
    setupTeamMatcherEvents(gameId, container);
}

function renderTeamMatchCard(team, gameId) {
    const isReady100 = team.match_percentage === 100;
    const badgeClass = isReady100 ? "pct-100" : (team.match_percentage >= 75 ? "pct-75" : "pct-mid");
    const badgeIcon = isReady100 ? "fa-circle-check" : "fa-shield-halved";
    const statusText = isReady100 ? "Equipe Completa" : `${team.owned_count}/${team.total_count} Membros`;

    let slotsHtml = `<div class="team-matcher-slots-grid">`;
    team.members.forEach(m => {
        const fallbackIcon = `/assets/${gameId}_icon.png`;
        const avatarSrc = m.icon || fallbackIcon;
        const elemKey = (m.element || "").toLowerCase();
        const elemClass = ELEMENT_MAPPING[elemKey] || "el-physical";
        const rarityClass = (m.rarity === 5 || m.rarity === "5" || String(m.rarity).toUpperCase() === "S") ? "rarity-5" : "rarity-4";

        if (m.is_owned) {
            slotsHtml += `
                <div class="team-matcher-slot owned" title="${m.name} (Nv. ${m.level || 80} ${m.rank_str || ''}) • No seu Roster">
                    <div class="team-matcher-avatar-box ${elemClass} ${rarityClass}">
                        <img src="${avatarSrc}" onerror="this.onerror=null; this.src='${fallbackIcon}';" alt="${m.name}">
                    </div>
                    <span class="team-matcher-slot-name">${m.name}</span>
                    <span class="team-matcher-slot-role">${m.role}</span>
                    <span class="team-matcher-slot-badge owned">Nv. ${m.level || 80}</span>
                </div>
            `;
        } else {
            slotsHtml += `
                <div class="team-matcher-slot missing" title="${m.name} • Não Possuído">
                    <div class="team-matcher-avatar-box">
                        <img src="${avatarSrc}" onerror="this.onerror=null; this.src='${fallbackIcon}';" alt="${m.name}">
                    </div>
                    <span class="team-matcher-slot-name">${m.name}</span>
                    <span class="team-matcher-slot-role">${m.role}</span>
                    <span class="team-matcher-slot-badge missing"><i class="fa-solid fa-xmark"></i> Faltando</span>
                </div>
            `;
        }
    });
    slotsHtml += `</div>`;

    // Seção de Substitutos Disponíveis no Roster do Jogador
    const missingWithSubs = team.members.filter(m => !m.is_owned && m.substitutes && m.substitutes.length > 0);
    let subsHtml = "";
    if (missingWithSubs.length > 0) {
        subsHtml = `
            <div class="team-matcher-substitutes-box">
                <div class="team-matcher-subs-header">
                    <i class="fa-solid fa-arrows-rotate"></i> Substitutos Recomendados no seu Roster:
                </div>
                <div class="team-matcher-subs-list">
                    ${missingWithSubs.map(m => `
                        <div>
                            <span style="font-size: 11px; color: #f87171; font-weight: 600;">Para o slot de ${m.name} (${m.role}):</span>
                            <div style="display: flex; flex-direction: column; gap: 4px; margin-top: 4px;">
                                ${m.substitutes.map(sub => `
                                    <div class="team-matcher-sub-chip">
                                        <div class="team-matcher-sub-info">
                                            <img src="${sub.icon || `/assets/${gameId}_icon.png`}" class="team-matcher-sub-avatar" onerror="this.onerror=null; this.src='/assets/${gameId}_icon.png';">
                                            <div>
                                                <strong style="color: #f8fafc;">${sub.name}</strong> 
                                                <span style="color: #94a3b8; font-size: 10px;">(Nv. ${sub.level} • ${sub.rank_str})</span>
                                            </div>
                                        </div>
                                        <span style="font-size: 10px; color: #38bdf8; text-align: right;">${sub.synergy_reason}</span>
                                    </div>
                                `).join("")}
                            </div>
                        </div>
                    `).join("")}
                </div>
            </div>
        `;
    }

    return `
        <div class="team-matcher-card ${isReady100 ? 'ready-100' : ''}">
            <div class="team-matcher-card-header">
                <div class="team-matcher-title-box">
                    <h4>
                        <i class="fa-solid fa-users" style="color: #38bdf8; font-size: 14px;"></i> ${team.team_name}
                    </h4>
                    <div class="team-matcher-meta-chips">
                        <span class="endgame-summary-chip cyan"><i class="fa-solid fa-location-crosshairs"></i> ${team.mode}</span>
                        ${team.tier_or_rank ? `<span class="endgame-summary-chip gold"><i class="fa-solid fa-trophy"></i> ${team.tier_or_rank}</span>` : ''}
                        ${team.avg_performance ? `<span class="endgame-summary-chip purple"><i class="fa-solid fa-gauge-high"></i> ${team.avg_performance}</span>` : ''}
                        ${team.usage_rate ? `<span class="endgame-summary-chip"><i class="fa-solid fa-chart-simple"></i> Uso: ${team.usage_rate}</span>` : ''}
                    </div>
                </div>
                <div class="team-match-badge ${badgeClass}" title="Compatibilidade direta de personagens possuídos">
                    <i class="fa-solid ${badgeIcon}"></i> ${team.match_percentage}% (${statusText})
                </div>
            </div>

            ${slotsHtml}
            ${subsHtml}

            ${team.synergy_notes ? `
                <div class="team-matcher-synergy-text">
                    <strong><i class="fa-solid fa-bolt" style="color: #fbbf24;"></i> Estratégia de Combate:</strong> ${team.synergy_notes}
                    ${team.recommended_buffs_bosses ? `<br><span style="color: #94a3b8; font-size: 11px;"><strong>Chefes / Fases Ideais:</strong> ${team.recommended_buffs_bosses}</span>` : ''}
                </div>
            ` : ''}
        </div>
    `;
}

function setupTeamMatcherEvents(gameId, container) {
    const modeSelect = container.querySelector(`#matcher-mode-select-${gameId}`);
    const compatSelect = container.querySelector(`#matcher-compat-select-${gameId}`);

    if (modeSelect) {
        modeSelect.addEventListener("change", () => {
            teamMatcherFilterState[gameId].mode = modeSelect.value;
            renderTeamMatcher(gameId);
        });
    }

    if (compatSelect) {
        compatSelect.addEventListener("change", () => {
            teamMatcherFilterState[gameId].minMatch = parseFloat(compatSelect.value || 0);
            renderTeamMatcher(gameId);
        });
    }
}

// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
if (typeof _endgameInflight !== 'undefined') window._endgameInflight = _endgameInflight;
if (typeof _loadEndgameImpl !== 'undefined') window._loadEndgameImpl = _loadEndgameImpl;
if (typeof activeEndgameModeIdx !== 'undefined') window.activeEndgameModeIdx = activeEndgameModeIdx;
if (typeof activeEndgameView !== 'undefined') window.activeEndgameView = activeEndgameView;
if (typeof cachedEndgameData !== 'undefined') window.cachedEndgameData = cachedEndgameData;
if (typeof getEndgameModeIcon !== 'undefined') window.getEndgameModeIcon = getEndgameModeIcon;
if (typeof loadEndgame !== 'undefined') window.loadEndgame = loadEndgame;
if (typeof normalizeEndgameChar !== 'undefined') window.normalizeEndgameChar = normalizeEndgameChar;
if (typeof renderEndgame !== 'undefined') window.renderEndgame = renderEndgame;
if (typeof renderEndgameTeamCard !== 'undefined') window.renderEndgameTeamCard = renderEndgameTeamCard;
if (typeof renderTeamMatcher !== 'undefined') window.renderTeamMatcher = renderTeamMatcher;
if (typeof teamMatcherFilterState !== 'undefined') window.teamMatcherFilterState = teamMatcherFilterState;