// ==========================================================================
// Módulo: gacha_tracker.js
// Cabeça de Droid - Vanilla ES6 Module (v5.1+)
// Rastreamento Real de Tiros, Banners Específicos & Histórico com Miniaturas
// ==========================================================================

window.currentTrackerGame = "hsr";
window.currentHistoryPage = 1;
window.currentHistoryPageSize = 25;
window.currentHistoryTotal = 0;

/**
 * Alterna o jogo ativo no Gacha Tracker (Genshin, HSR ou ZZZ)
 */
window.switchGachaTrackerGame = function(gameId) {
    window.currentTrackerGame = gameId || "hsr";
    window.currentHistoryPage = 1;

    // Atualiza botões da interface
    document.querySelectorAll(".tracker-game-btn").forEach(btn => {
        if (btn.getAttribute("data-game") === window.currentTrackerGame) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    // Atualiza opções do select de filtro de banner para refletir o jogo selecionado
    updateBannerFilterOptions(window.currentTrackerGame);

    window.loadGachaTracker(window.currentTrackerGame);
};

/**
 * Atualiza dinamicamente as opções do select de filtro de histórico conforme o jogo
 */
function updateBannerFilterOptions(gameId) {
    const bannerSelect = document.getElementById("tracker-history-filter-banner");
    if (!bannerSelect) return;

    let optionsHtml = isEn ? `
        <option value="all">All Banners</option>
        <option value="character">Character / Agent</option>
        <option value="weapon">Weapon / Light Cone / W-Engine</option>
        <option value="standard">Standard / Wanderlust</option>
    ` : `
        <option value="all">Todos os Banners</option>
        <option value="character">Personagem / Agente</option>
        <option value="weapon">Arma / Cone / Motor-W</option>
        <option value="standard">Padrão / Mochileiro</option>
    `;

    if (gameId === "genshin") {
        optionsHtml += isEn ? `
            <option value="beginner">Beginners' Wish</option>
            <option value="chronicled">Chronicled Wish</option>
        ` : `
            <option value="beginner">Desejo dos Novatos (Iniciante)</option>
            <option value="chronicled">Oração das Crônicas (Regional)</option>
        `;
    } else if (gameId === "hsr") {
        optionsHtml += isEn ? `
            <option value="beginner">Departure Warp (Beginner)</option>
            <option value="collab">Collab Warp (Fate)</option>
        ` : `
            <option value="beginner">Salto de Partida (Iniciante)</option>
            <option value="collab">Salto de Colaboração (Fate)</option>
        `;
    } else if (gameId === "zzz") {
        optionsHtml += isEn ? `
            <option value="bangboo">Bangboo Channel (Boopon)</option>
        ` : `
            <option value="bangboo">Canal de Bangboos (Boopon)</option>
        `;
    }

    bannerSelect.innerHTML = optionsHtml;
}

/**
 * Carrega as métricas consolidadas e os banners específicos do jogo selecionado
 */
window.loadGachaTracker = async function(gameId) {
    const gid = gameId || window.currentTrackerGame || "hsr";
    const bannersContainer = document.getElementById("tracker-banners-container");
    if (bannersContainer) {
        bannersContainer.innerHTML = [1, 2, 3].map(() => `
            <div class="tracker-banner-card" style="min-height: 220px; justify-content: space-between;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div class="skeleton-box" style="width: 20px; height: 20px; border-radius: 4px;"></div>
                            <div class="skeleton-line" style="width: 140px; height: 16px;"></div>
                        </div>
                        <div class="skeleton-box" style="width: 80px; height: 20px; border-radius: 12px;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                        <div class="skeleton-line" style="width: 60px; height: 28px;"></div>
                        <div class="skeleton-line" style="width: 100px; height: 12px;"></div>
                    </div>
                    <div class="skeleton-box" style="width: 100%; height: 10px; border-radius: 6px; margin-bottom: 14px;"></div>
                </div>
                <div style="display: flex; gap: 6px;">
                    <div class="skeleton-box" style="width: 38px; height: 38px; border-radius: 8px;"></div>
                    <div class="skeleton-box" style="width: 38px; height: 38px; border-radius: 8px;"></div>
                    <div class="skeleton-box" style="width: 38px; height: 38px; border-radius: 8px;"></div>
                </div>
            </div>
        `).join("");
    }

    try {
        const res = await fetch(`/api/gacha/tracker/${gid}`);
        if (!res.ok) throw new Error("Falha ao carregar dados do rastreador");
        const data = await res.json();

        // 1. Métricas Globais de Sorte
        const totalPullsEl = document.getElementById("tracker-stat-total-pulls");
        const totalFivesEl = document.getElementById("tracker-stat-total-fives");
        const avgPityEl = document.getElementById("tracker-stat-avg-pity");
        const luckBadgeEl = document.getElementById("tracker-luck-badge");

        if (totalPullsEl) totalPullsEl.textContent = Number(data.total_pulls_all_banners || 0).toLocaleString();
        if (totalFivesEl) totalFivesEl.textContent = data.total_five_stars_all_banners || 0;
        if (avgPityEl) {
            const charB = data.character_banner || {};
            const avg = charB.avg_five_star_pity || 0;

    avgPityEl.textContent = avg > 0 ? (isEn ? `${avg} pulls` : `${avg} tiros`) : "--";
        }
        if (luckBadgeEl) {
            luckBadgeEl.innerHTML = `<i class="fa-solid fa-clover" style="color: #34d399;"></i> ${data.overall_luck_rating || 'Sem dados'}`;
        }

        // 2. Renderização Dinâmica dos Banners do Jogo Atual
        if (bannersContainer) {
            const bannerList = data.banners && data.banners.length > 0
                ? data.banners
                : [data.character_banner, data.weapon_banner, data.standard_banner].filter(Boolean);

            bannersContainer.innerHTML = bannerList.map(b => renderBannerCardHtml(gid, b)).join("");
        }

        // 3. Carrega o Histórico Detalhado Paginado
        await window.loadGachaTrackerHistory();

    } catch (err) {
        console.error("Erro ao carregar dados do Gacha Tracker:", err);
        if (bannersContainer) {
            bannersContainer.innerHTML = `
                <div style="grid-column: 1 / -1; padding: 30px 20px; text-align: center; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px;">
                    <i class="fa-solid fa-triangle-exclamation fa-2x" style="color: #ef4444; margin-bottom: 10px;"></i>
                    <h4 style="color: #f87171; margin: 0 0 6px 0; font-size: 15px;">${isEn ? "Failed to Load Gacha Tracker" : "Falha ao carregar o rastreador de gacha"}</h4>
                    <p style="color: var(--text-muted); font-size: 12px; margin: 0 0 14px 0;">${isEn ? "Could not retrieve pity and banner information." : "Não foi possível carregar os dados de pity e banners."}</p>
                    <button class="primary-btn" onclick="window.loadGachaTracker && window.loadGachaTracker('${gid}')" style="padding: 8px 18px; font-size: 12px; border-radius: 8px; cursor: pointer; font-weight: 600;">
                        <i class="fa-solid fa-arrow-rotate-right"></i> ${isEn ? "Try Again" : "Tentar de novo"}
                    </button>
                </div>
            `;
        }
    }
};

/**
 * Renderiza o template HTML de um Card de Banner individual com miniaturas de 5★
 */
function renderBannerCardHtml(gameId, banner) {
    if (!banner) return "";

    const cat = banner.banner_category || "character";
    const cap = banner.hard_pity_cap || 90;
    const softStart = banner.soft_pity_start || 74;
    const currentPity = banner.current_pity || 0;
    const pct = Math.min(100, Math.round((currentPity / cap) * 100));

    // Determina ícone, cores e badges por categoria
    let iconClass = "fa-user-astronaut";
    let iconColor = "#38bdf8";
    let customCardClass = "";
    let badgeText = "50/50";
    let badgeBg = "rgba(251, 191, 36, 0.15)";
    let badgeBorder = "rgba(251, 191, 36, 0.35)";
    let badgeColor = "#fbbf24";
    let progressBarBg = "linear-gradient(90deg, #38bdf8, #818cf8)";

    if (cat === "character") {
        iconClass = "fa-user-astronaut";
        iconColor = "#38bdf8";
        if (banner.is_guaranteed) {
            badgeText = "GARANTIDO (100%)";
            badgeBg = "rgba(52, 211, 153, 0.2)";
            badgeBorder = "rgba(52, 211, 153, 0.5)";
            badgeColor = "#34d399";
        } else {
            badgeText = "50/50 EM DISPUTA";
        }
    } else if (cat === "collab") {
        iconClass = "fa-burst";
        iconColor = "#f87171";
        customCardClass = "tracker-banner-collab";
        if (banner.is_guaranteed) {
            badgeText = "GARANTIDO (100%)";
            badgeBg = "rgba(52, 211, 153, 0.2)";
            badgeBorder = "rgba(52, 211, 153, 0.5)";
            badgeColor = "#34d399";
        } else {
            badgeText = "COLLAB 50/50";
            badgeBg = "rgba(239, 68, 68, 0.2)";
            badgeBorder = "rgba(239, 68, 68, 0.4)";
            badgeColor = "#f87171";
        }
        progressBarBg = "linear-gradient(90deg, #f87171, #fb923c)";
    } else if (cat === "weapon") {
        iconClass = "fa-wand-magic-sparkles";
        iconColor = "#c084fc";
        badgeText = gameId === "zzz" ? "75/25 MOTOR" : "75/25 CONE";
        badgeBg = "rgba(192, 132, 252, 0.15)";
        badgeBorder = "rgba(192, 132, 252, 0.35)";
        badgeColor = "#c084fc";
        progressBarBg = "linear-gradient(90deg, #c084fc, #ec4899)";
    } else if (cat === "bangboo") {
        iconClass = "fa-robot";
        iconColor = "#fbbf24";
        customCardClass = "tracker-banner-bangboo";
        badgeText = "100% GARANTIDO";
        badgeBg = "rgba(234, 179, 8, 0.2)";
        badgeBorder = "rgba(234, 179, 8, 0.5)";
        badgeColor = "#fbbf24";
        progressBarBg = "linear-gradient(90deg, #eab308, #f59e0b)";
    } else if (cat === "beginner") {
        iconClass = "fa-graduation-cap";
        iconColor = "#34d399";
        customCardClass = "tracker-banner-beginner";
        badgeText = gameId === "genshin" ? "20% OFF (NOELLE)" : "5★ GARANTIDO";
        badgeBg = "rgba(52, 211, 153, 0.2)";
        badgeBorder = "rgba(52, 211, 153, 0.5)";
        badgeColor = "#34d399";
        progressBarBg = "linear-gradient(90deg, #10b981, #34d399)";
    } else if (cat === "chronicled") {
        iconClass = "fa-book-bookmark";
        iconColor = "#e879f9";
        customCardClass = "tracker-banner-chronicled";
        badgeText = "ORÁCULO REGIONAL";
        badgeBg = "rgba(232, 121, 249, 0.2)";
        badgeBorder = "rgba(232, 121, 249, 0.4)";
        badgeColor = "#e879f9";
        progressBarBg = "linear-gradient(90deg, #e879f9, #a855f7)";
    } else {
        iconClass = "fa-compass";
        iconColor = "#94a3b8";
        badgeText = "PERMANENTE";
        badgeBg = "rgba(255, 255, 255, 0.08)";
        badgeBorder = "rgba(255, 255, 255, 0.2)";
        badgeColor = "#cbd5e1";
        progressBarBg = "linear-gradient(90deg, #94a3b8, #cbd5e1)";
    }

    // Alerta de Soft Pity ativo
    if (currentPity >= softStart) {
        progressBarBg = "linear-gradient(90deg, #f59e0b, #fbbf24)";
    }

    const softText = banner.next_soft_pity_in > 0
        ? (isEn ? `${banner.next_soft_pity_in} pulls until Soft Pity (${softStart})` : `Faltam ${banner.next_soft_pity_in} tiros para o Soft Pity (${softStart})`)
        : (isEn ? `🔥 Soft Pity Active! (+ accelerated rate)` : `🔥 Soft Pity Ativo! (+ chance acelerada)`);

    // Histórico dos 5★ com Miniatura
    const recents = banner.recent_five_stars || [];
    let recentsHtml = "";
    if (recents.length === 0) {
        recentsHtml = `<span style="font-size: 11px; color: var(--text-muted); font-style: italic;">${isEn ? "No 5★ records obtained on this banner." : "Nenhum registro de 5★ obtido neste banner."}</span>`;
    } else {
        recentsHtml = recents.map(f => {
            const winColor = f.is_win_5050 ? "#34d399" : "#f87171";
            const winLabel = f.is_win_5050 ? "Vitória" : "50/50 Perdido";
            const imgTag = f.icon
                ? `<img src="${f.icon}" alt="${f.name}" width="32" height="32" loading="lazy" decoding="async" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='inline-block';"><i class="fa-solid fa-star" style="display: none; color: #fbbf24; font-size: 14px;"></i>`
                : `<i class="fa-solid fa-star" style="color: #fbbf24; font-size: 14px;"></i>`;

            return `
                <div style="background: rgba(0,0,0,0.35); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 6px 10px; display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px; overflow: hidden;">
                        <div class="tracker-item-avatar-box rarity-5" style="width: 32px; height: 32px;">
                            ${imgTag}
                        </div>
                        <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            <strong style="color: #fbbf24; font-size: 12px; display: block; overflow: hidden; text-overflow: ellipsis;">${f.name}</strong>
                            <span style="font-size: 10px; color: var(--text-muted);">${f.time ? f.time.split(' ')[0] : ''}</span>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px; flex-shrink: 0;">
                        <span class="tracker-pity-tag pity-gold">Pity ${f.pity}</span>
                        ${cat === 'character' || cat === 'collab' ? `<span style="font-size: 10px; font-weight: 700; color: ${winColor};">${winLabel}</span>` : ''}
                    </div>
                </div>
            `;
        }).join("");
    }

    return `
        <div class="tracker-banner-card ${customCardClass}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 13px; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 6px;">
                    <i class="fa-solid ${iconClass}" style="color: ${iconColor};"></i> ${banner.display_name}
                </span>
                <span style="font-size: 10px; font-weight: 800; padding: 2px 8px; border-radius: 10px; background: ${badgeBg}; border: 1px solid ${badgeBorder}; color: ${badgeColor};">
                    ${badgeText}
                </span>
            </div>

            <!-- Contador de Pity Gigante -->
            <div style="text-align: center; padding: 10px 0;">
                <span style="font-size: 11px; color: var(--text-muted); display: block; text-transform: uppercase;">Pity Atual Acumulado</span>
                <div style="font-size: 42px; font-weight: 900; color: #fff; line-height: 1.1; margin: 4px 0;">
                    <span>${currentPity}</span><span style="font-size: 20px; color: #64748b;"> / ${cap}</span>
                </div>
                <span style="font-size: 11px; color: #94a3b8;">${softText}</span>
            </div>

            <!-- Barra de Progresso do Pity -->
            <div style="width: 100%; height: 8px; background: rgba(0,0,0,0.5); border-radius: 10px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1);">
                <div style="width: ${pct}%; height: 100%; background: ${progressBarBg}; border-radius: 10px; transition: width 0.4s ease;"></div>
            </div>

            <!-- Estatísticas Resumidas do Banner -->
            <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.25); border-radius: 8px; padding: 6px 10px; font-size: 11px;">
                <span style="color: var(--text-muted);">Total: <strong style="color: #fff;">${banner.total_pulls}</strong></span>
                <span style="color: var(--text-muted);">5★: <strong style="color: #fbbf24;">${banner.five_stars_count}</strong></span>
                <span style="color: var(--text-muted);">Média: <strong style="color: #38bdf8;">${banner.avg_five_star_pity || '--'}</strong></span>
            </div>

            <!-- Histórico dos Últimos 5★ com Miniaturas -->
            <div style="margin-top: 6px;">
                <span style="font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; display: block; margin-bottom: 6px;">
                    Últimos 5★ Obtidos:
                </span>
                <div style="display: flex; flex-direction: column; gap: 6px; max-height: 160px; overflow-y: auto;">
                    ${recentsHtml}
                </div>
            </div>
        </div>
    `;
}

let _trackerHistoryController = null;

/**
 * Consulta e renderiza o histórico detalhado paginado com imagens oficiais
 */
window.loadGachaTrackerHistory = async function() {
    if (_trackerHistoryController) {
        _trackerHistoryController.abort();
    }
    _trackerHistoryController = new AbortController();
    const signal = _trackerHistoryController.signal;

    const gid = window.currentTrackerGame || "hsr";
    const historyContainer = document.getElementById("tracker-history-container");
    if (!historyContainer) return;

    const bannerFilter = document.getElementById("tracker-history-filter-banner")?.value || "all";
    const rarityFilter = document.getElementById("tracker-history-filter-rarity")?.value || "all";

    const offset = (window.currentHistoryPage - 1) * window.currentHistoryPageSize;
    let url = `/api/gacha/tracker/history/${gid}?limit=${window.currentHistoryPageSize}&offset=${offset}`;

    if (bannerFilter && bannerFilter !== "all") {
        url += `&banner_category=${encodeURIComponent(bannerFilter)}`;
    }
    if (rarityFilter && rarityFilter !== "all") {
        url += `&rarity=${encodeURIComponent(rarityFilter)}`;
    }

    try {
        historyContainer.innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 8px; padding: 6px 0;">
                ${Array(5).fill(0).map(() => `
                    <div class="skeleton-row" style="height: 44px; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 10px; width: 50%;">
                            <div class="skeleton-box" style="width: 28px; height: 28px; border-radius: 4px;"></div>
                            <div class="skeleton-line" style="width: 60%; height: 12px;"></div>
                        </div>
                        <div class="skeleton-line" style="width: 20%; height: 10px;"></div>
                        <div class="skeleton-box" style="width: 45px; height: 18px; border-radius: 12px;"></div>
                    </div>
                `).join("")}
            </div>
        `;

        const res = await fetch(url, { signal });
        if (!res.ok) throw new Error("Erro ao consultar histórico de tiros");
        const data = await res.json();
        if (signal.aborted) return;

        window.currentHistoryTotal = data.total_pulls || 0;

        // Atualiza label de total
        const totalLabel = document.getElementById("tracker-history-total-label");
        if (totalLabel) {

    totalLabel.textContent = isEn ? `${window.currentHistoryTotal.toLocaleString()} pulls found in database` : `${window.currentHistoryTotal.toLocaleString()} tiros encontrados no banco de dados`;
        }

        // Atualiza controles de paginação
        const totalPages = Math.max(1, Math.ceil(window.currentHistoryTotal / window.currentHistoryPageSize));
        const pageInfoEl = document.getElementById("tracker-history-page-info");
        const prevBtn = document.getElementById("tracker-history-prev-btn");
        const nextBtn = document.getElementById("tracker-history-next-btn");

        if (pageInfoEl) pageInfoEl.textContent = `Página ${window.currentHistoryPage} de ${totalPages}`;
        if (prevBtn) prevBtn.disabled = window.currentHistoryPage <= 1;
        if (nextBtn) nextBtn.disabled = window.currentHistoryPage >= totalPages;

        const pulls = data.pulls || [];
        if (pulls.length === 0) {
            if (window.currentHistoryTotal === 0) {
                historyContainer.innerHTML = `
                    <div style="text-align: center; padding: 40px 20px; background: rgba(0,0,0,0.2); border-radius: 12px; max-width: 520px; margin: 10px auto;">
                        <i class="fa-solid fa-cloud-arrow-up" style="font-size: 32px; color: #38bdf8; margin-bottom: 12px;"></i>
                        <h4 style="margin: 0 0 6px 0; color: var(--text-primary); font-size: 15px;">${isEn ? "No Pulls in Database" : "Nenhum Tiro no Histórico"}</h4>
                        <p style="color: var(--text-muted); font-size: 13px; line-height: 1.5; margin: 0 0 16px 0;">
                            ${isEn ? "The Gacha Tracker consolidates your warp/wish history, current pity, and 50/50 status. Import your log via JSON (UIGF/SRGF) to view records." : "O Rastreador de Gacha consolida seu histórico de orações e saltos, taxa de pity e 50/50. Importe seu arquivo JSON (UIGF/SRGF) para visualizar todos os seus registros."}
                        </p>
                        <button class="primary-btn" onclick="document.getElementById('tracker-file-input')?.click()" style="padding: 8px 18px; font-size: 12px; border-radius: 8px; cursor: pointer; font-weight: 600;">
                            <i class="fa-solid fa-file-import"></i> ${isEn ? "Import JSON History" : "Importar Histórico (UIGF/SRGF)"}
                        </button>
                    </div>
                `;
            } else {
                historyContainer.innerHTML = `
                    <div style="text-align: center; padding: 30px 20px; background: rgba(0,0,0,0.2); border-radius: 12px;">
                        <i class="fa-solid fa-filter" style="font-size: 24px; color: #64748b; margin-bottom: 8px;"></i>
                        <p style="color: var(--text-muted); font-size: 13px; margin: 0 0 12px 0;">${isEn ? "No pulls match the selected filters." : "Nenhum tiro encontrado com os filtros selecionados."}</p>
                        <button class="secondary-btn" onclick="document.getElementById('tracker-history-filter-banner').value='all'; document.getElementById('tracker-history-filter-rarity').value='all'; window.loadGachaTrackerHistory();" style="padding: 6px 14px; font-size: 11px; border-radius: 6px; cursor: pointer;">
                            <i class="fa-solid fa-rotate-left"></i> ${isEn ? "Clear Filters" : "Limpar Filtros"}
                        </button>
                    </div>
                `;
            }
            return;
        }

        // Renderiza tabela com miniaturas de imagem
        historyContainer.innerHTML = `
            <table class="tracker-history-table">
                <thead>
                    <tr style="color: #94a3b8; font-size: 11px; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.08);">
                        <th style="padding: 6px 12px; text-align: left;">Item Conquistado</th>
                        <th style="padding: 6px 12px; text-align: left;">Tipo / Banner</th>
                        <th style="padding: 6px 12px; text-align: center;">Pity</th>
                        <th style="padding: 6px 12px; text-align: right;">Data e Hora</th>
                    </tr>
                </thead>
                <tbody>
                    ${pulls.map(p => renderHistoryRowHtml(p)).join("")}
                </tbody>
            </table>
        `;

    } catch (err) {
        if (err.name === "AbortError") {
            // Requisição anterior cancelada intencionalmente para dar lugar à mais recente
            return;
        }
        console.error("Erro ao carregar histórico detalhado:", err);
        historyContainer.innerHTML = `
            <div style="padding: 30px 20px; text-align: center; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; max-width: 480px; margin: 15px auto;">
                <i class="fa-solid fa-triangle-exclamation fa-2x" style="color: #ef4444; margin-bottom: 10px;"></i>
                <h4 style="color: #f87171; margin: 0 0 6px 0; font-size: 15px;">${isEn ? "Failed to Load Pull History" : "Falha ao carregar o histórico de tiros"}</h4>
                <p style="color: var(--text-muted); font-size: 12px; margin: 0 0 14px 0;">${isEn ? "Could not retrieve gacha logs." : "Não foi possível carregar os registros de histórico do gacha."}</p>
                <button class="primary-btn" onclick="window.loadGachaTrackerHistory && window.loadGachaTrackerHistory()" style="padding: 8px 18px; font-size: 12px; border-radius: 8px; cursor: pointer; font-weight: 600;">
                    <i class="fa-solid fa-arrow-rotate-right"></i> ${isEn ? "Try Again" : "Tentar de novo"}
                </button>
            </div>
        `;
    }
};

/**
 * Renderiza uma linha de puxada no histórico detalhado
 */
function renderHistoryRowHtml(pull) {
    const rarity = pull.rarity || 3;
    const rarityClass = rarity === 5 ? "rarity-5" : rarity === 4 ? "rarity-4" : "rarity-3";
    const nameColor = rarity === 5 ? "#fbbf24" : rarity === 4 ? "#c084fc" : "#38bdf8";
    const pityTagClass = rarity === 5 ? "pity-gold" : rarity === 4 ? "pity-purple" : "pity-blue";

    // Tipo legível
    let typeLabel = "Personagem";
    if (pull.item_type === "bangboo") typeLabel = "Bangboo";
    else if (pull.item_type === "weapon") typeLabel = "Arma / Cone / Motor";

    // Banner legível
    const bannerNames = {
        character: isEn ? "Character" : "Personagem",
        weapon: isEn ? "Weapon / Cone" : "Arma / Cone",
        standard: "Mochileiro",
        beginner: "Iniciante",
        collab: "Collab (Fate)",
        bangboo: "Bangboo",
        chronicled: "Crônica"
    };
    const bannerDisplay = bannerNames[pull.banner_category] || pull.banner_category;

    // Miniatura de imagem com fallback gracioso
    const defaultIconClass = pull.item_type === 'bangboo' ? 'fa-robot' : pull.item_type === 'weapon' ? 'fa-wand-magic-sparkles' : 'fa-user';
    const imgHtml = pull.icon
        ? `<img src="${pull.icon}" alt="${pull.name}" width="28" height="28" loading="lazy" decoding="async" onerror="this.style.display='none'; if(this.nextElementSibling) this.nextElementSibling.style.display='inline-block';"><i class="fa-solid ${defaultIconClass}" style="display: none; color: ${nameColor}; font-size: 14px;"></i>`
        : `<i class="fa-solid ${defaultIconClass}" style="color: ${nameColor}; font-size: 14px;"></i>`;

    const starsDisplay = "★".repeat(rarity);

    return `
        <tr class="tracker-history-row">
            <td class="tracker-history-cell">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div class="tracker-item-avatar-box ${rarityClass}">
                        ${imgHtml}
                    </div>
                    <div>
                        <strong style="color: ${nameColor}; font-size: 13px; display: block;">${pull.name}</strong>
                        <span style="font-size: 11px; color: ${nameColor}; letter-spacing: 1px;">${starsDisplay}</span>
                    </div>
                </div>
            </td>
            <td class="tracker-history-cell">
                <div style="display: flex; flex-direction: column;">
                    <span style="font-size: 12px; color: #fff; font-weight: 600;">${typeLabel}</span>
                    <span style="font-size: 10px; color: var(--text-muted);">${bannerDisplay}</span>
                </div>
            </td>
            <td class="tracker-history-cell" style="text-align: center;">
                <span class="tracker-pity-tag ${pityTagClass}">Pity ${pull.pity}</span>
            </td>
            <td class="tracker-history-cell" style="text-align: right;">
                <span style="font-size: 11px; color: var(--text-muted);">${pull.time || '--'}</span>
            </td>
        </tr>
    `;
}

/**
 * Disparado ao alterar qualquer select de filtro de histórico
 */
window.filterGachaTrackerHistory = function() {
    window.currentHistoryPage = 1;
    window.loadGachaTrackerHistory();
};

/**
 * Controla a navegação de páginas do histórico (-1 ou +1)
 */
window.paginateGachaHistory = function(direction) {
    const totalPages = Math.max(1, Math.ceil(window.currentHistoryTotal / window.currentHistoryPageSize));
    const newPage = window.currentHistoryPage + direction;
    if (newPage >= 1 && newPage <= totalPages) {
        window.currentHistoryPage = newPage;
        window.loadGachaTrackerHistory();
    }
};

/**
 * Manipula a importação de arquivos de histórico (.json UIGF v4 / legado)
 */
window.handleGachaLogFileImport = async function(inputEl) {
    if (!inputEl || !inputEl.files || inputEl.files.length === 0) return;
    const file = inputEl.files[0];
    const gid = window.currentTrackerGame || "hsr";

    try {
        if (typeof showToast === "function") {
            showToast(`Lendo arquivo ${file.name}...`, "info");
        }

        const text = await file.text();
        const jsonPayload = JSON.parse(text);

        const isMultiGame = jsonPayload && (jsonPayload.hk4e || jsonPayload.hkrpg || jsonPayload.nap);
        const endpoint = isMultiGame ? "/api/gacha/tracker/import" : `/api/gacha/tracker/import/${gid}`;

        const res = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ raw_data: jsonPayload })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Erro ao importar histórico");

        if (typeof showToast === "function") {

        showToast(data.message || (isEn ? `${data.total_imported} pulls imported successfully!` : `${data.total_imported} tiros importados com sucesso!`), "success");
        }

        window.loadGachaTracker(gid);
    } catch (err) {
        console.error("Erro ao importar arquivo de gacha:", err);
        if (typeof showToast === "function") {
            showToast("Falha ao importar arquivo JSON: " + err.message, "error");
        }
    } finally {
        inputEl.value = "";
    }
};

/**
 * Exporta backup de tiros no padrão comunitário UIGF v2.4
 */
window.exportGachaLogUIGF = async function() {
    const gid = window.currentTrackerGame || "hsr";
    try {
        const res = await fetch(`/api/gacha/tracker/export/${gid}`);
        if (!res.ok) throw new Error("Erro ao exportar histórico");
        const data = await res.json();

        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `UIGF_${gid.toUpperCase()}_${data.info ? data.info.uid : 'backup'}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        if (typeof showToast === "function") {

        showToast(isEn ? "UIGF backup downloaded successfully!" : "Backup UIGF baixado com sucesso!", "success");
        }
    } catch (err) {
        console.error("Erro ao exportar UIGF:", err);
        if (typeof showToast === "function") {
            showToast("Falha ao exportar backup: " + err.message, "error");
        }
    }
};

/**
 * Limpa o histórico de tiros do jogo ativo
 */
window.clearGachaLogHistory = async function() {
    const gid = window.currentTrackerGame || "hsr";

    if (!confirm(isEn ? `Are you sure you want to clear all pull history for ${gid.toUpperCase()} from local database?` : `Tem certeza que deseja apagar todo o histórico de tiros de ${gid.toUpperCase()} do banco local?`)) {
        return;
    }

    try {
        const res = await fetch(`/api/gacha/tracker/${gid}`, { method: "DELETE" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Erro ao limpar histórico");

        if (typeof showToast === "function") {

        showToast(data.message || (isEn ? "Pull history cleared successfully." : "Histórico de tiros limpo com sucesso."), "success");
        }
        window.loadGachaTracker(gid);
    } catch (err) {
        console.error("Erro ao limpar histórico:", err);
        if (typeof showToast === "function") {
            showToast("Falha ao limpar histórico: " + err.message, "error");
        }
    }
};


window.addEventListener("app:languageChanged", () => {
    if (typeof updateBannerFilterOptions === "function") {
        updateBannerFilterOptions(window.currentTrackerGame || "hsr");
    }
    if (typeof window.loadGachaTracker === "function") {
        window.loadGachaTracker(window.currentTrackerGame || "hsr");
    }
});
