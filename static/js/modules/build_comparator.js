// ==========================================================================
// Módulo: build_comparator.js
// Cabeça de Droid - Vanilla ES6 Module
// ==========================================================================

// ==========================================================================
// ABAS E COMPARADOR DO BUILD INSPECTOR
// ==========================================================================
function setupInspectorTabs() {
    const btnBuild = document.getElementById("ins-tab-build");
    const btnCompare = document.getElementById("ins-tab-compare");
    const panelBuild = document.getElementById("panel-build");
    const panelCompare = document.getElementById("panel-compare");
    
    if (!btnBuild || !btnCompare) return;
    
    btnBuild.addEventListener("click", () => {
        btnBuild.classList.add("active");
        btnCompare.classList.remove("active");
        
        panelBuild.style.display = "block";
        panelCompare.style.display = "none";
    });
    
    btnCompare.addEventListener("click", () => {
        btnCompare.classList.add("active");
        btnBuild.classList.remove("active");
        
        panelBuild.style.display = "none";
        panelCompare.style.display = "block";
        
        loadBuildComparison();
    });
}

// ==========================================================================
// GRÁFICO RADAR: MINHA BUILD VS. BENCHMARK META (SVG INTERATIVO)
// ==========================================================================
function _escapeRadarHtml(val) {
    return String(val ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function _getRadarStatusColor(status) {
    if (status === "ok") return "var(--radar-status-ok, #10b981)";
    if (status === "close") return "var(--radar-status-warn, #fbbf24)";
    if (status === "low") return "var(--radar-status-low, #f87171)";
    if (status === "flex") return "var(--radar-status-flex, #38bdf8)";
    return "var(--text-muted, #94a3b8)";
}

function _renderRadarTagChips(tags, t) {
    if (!Array.isArray(tags) || tags.length === 0) return "";
    const tagMap = {
        in_combat: t("radar_tag_in_combat", "Em combate"),
        pre_combat: t("radar_tag_pre_combat", "Fora de combate"),
        base_ok: t("radar_tag_base_ok", "VEL Base OK"),
        optional: t("radar_tag_optional", "Opcional"),
        flex: t("radar_tag_flex", "Flexível"),
        relative: t("radar_tag_relative", "Relativo"),
        range: t("radar_tag_range", "Faixa"),
        cap: t("radar_tag_cap", "Cap Ideal"),
        overcap: t("radar_tag_overcap", "Overcap"),
    };
    const seen = new Set();
    return tags
        .filter(tag => tagMap[tag] && !seen.has(tag) && seen.add(tag))
        .map(tag => `<span class="meta-radar-tag tag-${_escapeRadarHtml(tag)}">${_escapeRadarHtml(tagMap[tag])}</span>`)
        .join("");
}

function renderMetaRadarChart(metaRadar, gameId) {
    const card = document.getElementById("ins-meta-radar-card");
    const svgWrap = document.getElementById("ins-radar-svg-wrap");
    const readoutEl = document.getElementById("ins-radar-readout");
    const breakdownEl = document.getElementById("ins-radar-breakdown");
    const summaryPill = document.getElementById("ins-radar-summary-pill");
    const flexNotesEl = document.getElementById("ins-radar-flex-notes");

    if (!card || !svgWrap || !breakdownEl) return;

    const axes = Array.isArray(metaRadar?.axes) ? metaRadar.axes : [];
    const flexNotes = Array.isArray(metaRadar?.flex_notes) ? metaRadar.flex_notes : [];
    const summary = metaRadar?.summary || {};

    if (axes.length === 0 && flexNotes.length === 0) {
        card.style.display = "none";
        return;
    }

    const isEn = Boolean(window.isEn || (window.getCurrentLanguage && window.getCurrentLanguage() === "en") || window.currentLang === "en");
    const t = (k, fb) => (window.t ? window.t(k) : fb);

    card.style.display = "block";

    // Pill de resumo no cabeçalho do Radar
    if (summaryPill) {
        const met = (summary.met_count || 0) + (summary.flex_count || 0);
        const total = summary.total_scored || axes.length + flexNotes.length;
        const avg = summary.avg_ratio_pct ? ` • ${isEn ? "Avg" : "Média"} ${Math.round(summary.avg_ratio_pct)}%` : "";
        summaryPill.textContent = `${met}/${total} ${isEn ? "Targets OK" : "Metas OK"}${avg}`;
    }

    const plottedAxes = axes.filter(a => a.plot_on_radar);
    const defaultHint = t("radar_hint_hover", isEn ? "Hover an axis or stat row for exact delta details." : "Passe o mouse em um eixo ou atributo para ver detalhes.");

    const setReadout = (axis) => {
        if (!readoutEl) return;
        if (!axis) {
            readoutEl.innerHTML = `<span><i class="fa-solid fa-crosshairs" style="color:#38bdf8; margin-right:5px;"></i>${_escapeRadarHtml(defaultHint)}</span>`;
            return;
        }
        const lbl = isEn ? (axis.label_en || axis.label_pt) : (axis.label_pt || axis.label_en);
        const targetDisp = isEn ? (axis.target_display_en || axis.target_display) : (axis.target_display_pt || axis.target_display);
        const col = _getRadarStatusColor(axis.status);
        const pctTxt = axis.actual_num !== null && axis.actual_num !== undefined ? `${Math.round(axis.ratio_pct || 0)}%` : "—";
        const diffTxt = axis.diff_display ? ` (${axis.diff_display})` : "";
        const noteHtml = axis.tooltip_note
            ? `<span style="width:100%; font-size:10px; color:var(--text-muted); line-height:1.35;">${_escapeRadarHtml(axis.tooltip_note)}</span>`
            : "";
        readoutEl.innerHTML = `
            <strong style="color:${col};">${_escapeRadarHtml(lbl)}</strong>
            <span>${_escapeRadarHtml(axis.actual_display)} / ${_escapeRadarHtml(targetDisp)}</span>
            <span style="color:${col}; font-weight:700;">${_escapeRadarHtml(pctTxt + diffTxt)}</span>
            ${noteHtml}
        `;
    };
    setReadout(null);

    // 1. RENDERIZA VISUAL ESQUERDO: POLÍGONO RADAR SVG (>= 3 EIXOS) OU MEDIDORES DE ALVO (1–2 EIXOS)
    if (plottedAxes.length >= 3) {
        const W = 330;
        const H = 276;
        const cx = W / 2;
        const cy = H / 2;
        const maxScale = 1.20;
        const maxR = 86;
        const n = plottedAxes.length;

        const ptFor = (idx, ratioVal) => {
            const angle = -Math.PI / 2 + (idx * 2 * Math.PI) / n;
            const r = (Math.min(maxScale, Math.max(0.05, ratioVal)) / maxScale) * maxR;
            return {
                x: cx + r * Math.cos(angle),
                y: cy + r * Math.sin(angle),
                angle,
            };
        };

        const ringLevels = [0.40, 0.70, 1.00, 1.20];
        const ringsSvg = ringLevels.map(lvl => {
            const pts = Array.from({ length: n }, (_, i) => {
                const p = ptFor(i, lvl);
                return `${p.x.toFixed(1)},${p.y.toFixed(1)}`;
            }).join(" ");
            const isMeta = lvl === 1.00;
            return `<polygon points="${pts}" fill="${isMeta ? "rgba(245, 158, 11, 0.08)" : "none"}" stroke="${isMeta ? "var(--radar-target-stroke, #f59e0b)" : "var(--radar-grid-stroke, rgba(148, 163, 184, 0.22))"}" stroke-width="${isMeta ? "1.6" : "1"}" ${isMeta ? 'stroke-dasharray="5 3"' : ""}></polygon>`;
        }).join("");

        const spokesSvg = Array.from({ length: n }, (_, i) => {
            const p = ptFor(i, maxScale);
            return `<line x1="${cx}" y1="${cy}" x2="${p.x.toFixed(1)}" y2="${p.y.toFixed(1)}" stroke="var(--radar-grid-stroke, rgba(148, 163, 184, 0.2))" stroke-width="1"></line>`;
        }).join("");

        const playerPts = plottedAxes.map((ax, i) => {
            const p = ptFor(i, ax.radar_ratio || 0.1);
            return `${p.x.toFixed(1)},${p.y.toFixed(1)}`;
        }).join(" ");

        // Sempre usa ciano/tema em alto contraste contra o anel Meta âmbar (evita sobreposição laranja-no-laranja no ZZZ)
        const gradColor = gameId === "genshin" ? "var(--color-genshin, #10b981)" : (gameId === "hsr" ? "var(--color-hsr, #6366f1)" : "var(--radar-player-stroke, #38bdf8)");
        const strokeColor = "var(--radar-player-stroke, #38bdf8)";

        const verticesSvg = plottedAxes.map((ax, i) => {
            const p = ptFor(i, ax.radar_ratio || 0.1);
            const col = _getRadarStatusColor(ax.status);
            return `
                <g class="meta-radar-vertex-group" data-radar-idx="${i}">
                    <circle class="meta-radar-vertex" data-radar-idx="${i}" cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4.8" fill="${col}" stroke="var(--bg-main, #050507)" stroke-width="1.8" style="color:${col};"></circle>
                    <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="15" fill="transparent" style="cursor:pointer;" data-radar-idx="${i}"></circle>
                </g>
            `;
        }).join("");

        const labelsSvg = plottedAxes.map((ax, i) => {
            const angle = -Math.PI / 2 + (i * 2 * Math.PI) / n;
            const labelR = maxR + 22;
            const lx = cx + labelR * Math.cos(angle);
            const ly = cy + labelR * Math.sin(angle);
            const cosA = Math.cos(angle);
            const sinA = Math.sin(angle);
            const anchor = Math.abs(cosA) < 0.22 ? "middle" : (cosA > 0 ? "start" : "end");
            const dyName = sinA < -0.5 ? -3 : (sinA > 0.5 ? 6 : 0);
            const shortLbl = isEn ? (ax.short_en || ax.label_en) : (ax.short_pt || ax.label_pt);
            const col = _getRadarStatusColor(ax.status);
            const pctStr = `${Math.round(ax.ratio_pct || 0)}%`;
            return `
                <g class="meta-radar-label-group" data-radar-idx="${i}">
                    <text class="meta-radar-axis-label" data-radar-idx="${i}" x="${lx.toFixed(1)}" y="${(ly + dyName).toFixed(1)}" text-anchor="${anchor}">${_escapeRadarHtml(shortLbl)}</text>
                    <text class="meta-radar-axis-pct" data-radar-idx="${i}" x="${lx.toFixed(1)}" y="${(ly + dyName + 12).toFixed(1)}" text-anchor="${anchor}" fill="${col}">${_escapeRadarHtml(pctStr)}</text>
                </g>
            `;
        }).join("");

        // Rótulo discreto "100%" deslocado à direita do eixo superior para nunca colidir com o vértice do topo
        const metaTagX = cx + 16;
        const metaTagY = cy - (1.00 / maxScale) * maxR + 15;

        svgWrap.innerHTML = `
            <svg class="meta-radar-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${_escapeRadarHtml(t("radar_meta_title", "Radar Meta"))}">
                <defs>
                    <radialGradient id="insRadarPlayerGrad" cx="50%" cy="50%" r="60%">
                        <stop offset="0%" style="stop-color:${gradColor}; stop-opacity:0.42;"></stop>
                        <stop offset="100%" style="stop-color:var(--radar-player-stroke, #38bdf8); stop-opacity:0.16;"></stop>
                    </radialGradient>
                </defs>
                ${ringsSvg}
                ${spokesSvg}
                <text x="${metaTagX.toFixed(1)}" y="${metaTagY.toFixed(1)}" font-size="8.5" font-weight="700" fill="var(--radar-target-stroke, #f59e0b)" opacity="0.9">100%</text>
                <polygon points="${playerPts}" fill="url(#insRadarPlayerGrad)" stroke="${strokeColor}" stroke-width="2.2" stroke-linejoin="round"></polygon>
                ${verticesSvg}
                ${labelsSvg}
            </svg>
        `;
    } else if (plottedAxes.length > 0) {
        // Fallback elegante para personagens com 1 ou 2 benchmarks numéricos (ex.: Kazuha, Zhongli, Xilonen)
        svgWrap.innerHTML = `
            <div class="meta-radar-gauge-list">
                ${plottedAxes.map((ax, i) => {
                    const lbl = isEn ? (ax.label_en || ax.label_pt) : (ax.label_pt || ax.label_en);
                    const col = _getRadarStatusColor(ax.status);
                    const barPct = Math.min(100, Math.max(4, ((ax.radar_ratio || 0) / 1.20) * 100));
                    const metaTickPct = (1.00 / 1.20) * 100;
                    return `
                        <div class="meta-radar-gauge-item" data-radar-idx="${i}">
                            <div class="meta-radar-gauge-head">
                                <span>${_escapeRadarHtml(lbl)}</span>
                                <span style="color:${col};">${Math.round(ax.ratio_pct || 0)}% (${_escapeRadarHtml(ax.actual_display)})</span>
                            </div>
                            <div class="meta-radar-gauge-bar">
                                <div class="meta-radar-gauge-fill" style="width:${barPct.toFixed(1)}%; background:${col};"></div>
                                <div class="meta-radar-gauge-marker" style="left:${metaTickPct.toFixed(1)}%;" title="Meta 100%"></div>
                            </div>
                        </div>
                    `;
                }).join("")}
            </div>
        `;
    } else {
        svgWrap.innerHTML = "";
    }

    // 2. RENDERIZA BREAKDOWN DETALHADO (COLUNA DIREITA)
    let plotIdxCounter = 0;
    const axisPlotIndexMap = new Map();
    axes.forEach((ax, idx) => {
        if (ax.plot_on_radar) {
            axisPlotIndexMap.set(idx, plotIdxCounter++);
        }
    });

    breakdownEl.innerHTML = axes.map((ax, idx) => {
        const lbl = isEn ? (ax.label_en || ax.label_pt) : (ax.label_pt || ax.label_en);
        const targetDisp = isEn ? (ax.target_display_en || ax.target_display) : (ax.target_display_pt || ax.target_display);
        const col = _getRadarStatusColor(ax.status);
        const barPct = Math.min(100, Math.max(0, ((ax.radar_ratio || 0) / 1.20) * 100));
        const metaTickPct = (1.00 / 1.20) * 100;
        const plotIdx = axisPlotIndexMap.has(idx) ? axisPlotIndexMap.get(idx) : -1;

        let badgeClass = "neutral";
        let badgeIcon = "fa-circle-info";
        let badgeText = "";
        const isBaseOkRow = ax.status === "ok" && (ax.tags || []).includes("base_ok") && (ax.diff_num || 0) < 0;
        const isInCombatCloseRow = ax.status === "close" && (ax.tags || []).includes("in_combat");

        if (ax.status === "ok") {
            badgeClass = "match";
            badgeIcon = "fa-check";
            badgeText = isBaseOkRow
                ? t("radar_tag_base_ok", "VEL Base OK")
                : `${t("comp_badge_meta_ok", "Meta OK")}${ax.diff_display ? ` (${ax.diff_display})` : ""}`;
        } else if (isInCombatCloseRow) {
            badgeClass = "warning";
            badgeIcon = "fa-bolt";
            badgeText = isEn ? `Combat buffs apply (${ax.actual_display})` : `Conta buffs em batalha`;
        } else if (ax.status === "close") {
            badgeClass = "warning";
            badgeIcon = "fa-triangle-exclamation";
            badgeText = `${t("comp_badge_meta_close", "Próximo")}${ax.diff_display ? ` (${ax.diff_display})` : ""}`;
        } else if (ax.status === "flex") {
            badgeClass = "match";
            badgeIcon = "fa-sparkles";
            badgeText = t("radar_tag_flex", "Flexível");
        } else if (ax.status === "missing") {
            badgeClass = "neutral";
            badgeIcon = "fa-circle-question";
            badgeText = t("comp_badge_not_found", "Não encontrado");
        } else {
            badgeClass = "mismatch";
            badgeIcon = "fa-arrow-down";
            badgeText = ax.diff_display || `${Math.round(ax.ratio_pct || 0)}%`;
        }

        // Evita duplicar pill de tag quando o badge principal já exibe o mesmo rótulo (ex.: VEL Base OK)
        const visibleTags = (ax.tags || []).filter(tg => {
            if (tg === "range") return false;
            if (tg === "base_ok" && isBaseOkRow) return false;
            return true;
        });
        const tagsHtml = _renderRadarTagChips(visibleTags, t);
        const titleAttr = ax.tooltip_note ? ` title="${_escapeRadarHtml(ax.tooltip_note)}"` : "";

        return `
            <div class="meta-radar-row" data-axis-idx="${idx}" data-radar-idx="${plotIdx}"${titleAttr}>
                <div class="meta-radar-row-top">
                    <span class="meta-radar-row-name">
                        <span class="meta-radar-status-dot status-${_escapeRadarHtml(ax.status)}"></span>
                        ${_escapeRadarHtml(lbl)}
                    </span>
                    <span class="meta-radar-row-values">
                        <span class="meta-radar-val-actual" style="color:${col};">${_escapeRadarHtml(ax.actual_display)}</span>
                        <span class="meta-radar-val-sep">/</span>
                        <span class="meta-radar-val-target">${_escapeRadarHtml(targetDisp)}</span>
                    </span>
                </div>
                <div class="meta-radar-row-bottom">
                    <div class="meta-radar-mini-track">
                        <div class="meta-radar-mini-fill" style="width:${barPct.toFixed(1)}%; background:${col};"></div>
                        <div class="meta-radar-mini-tick" style="left:${metaTickPct.toFixed(1)}%;"></div>
                    </div>
                    <div class="meta-radar-tags-wrap">
                        ${tagsHtml}
                        <span class="comparison-badge ${badgeClass}"><i class="fa-solid ${badgeIcon}"></i> ${_escapeRadarHtml(badgeText)}</span>
                    </div>
                </div>
            </div>
        `;
    }).join("");

    // 3. CHIPS DE REGRAS FLEXÍVEIS / RELATIVAS (EX.: ANYTHING, BASE, 1-2 SPD SLOWER)
    if (flexNotesEl) {
        if (flexNotes.length > 0) {
            flexNotesEl.style.display = "flex";
            const hdr = t("radar_flex_header", isEn ? "Flexible / Contextual Rules:" : "Regras Flexíveis / Contextuais:");
            flexNotesEl.innerHTML = `
                <span style="font-weight:600; color:var(--text-muted);">${_escapeRadarHtml(hdr)}</span>
                ${flexNotes.map(fn => {
                    const lbl = isEn ? (fn.label_en || fn.label_pt) : (fn.label_pt || fn.label_en);
                    const tgt = isEn ? (fn.target_display_en || fn.target_display) : (fn.target_display_pt || fn.target_display);
                    const actualPart = fn.actual_display ? `${_escapeRadarHtml(fn.actual_display)} <span style="opacity:0.7;">•</span> ` : "";
                    return `<span class="meta-radar-flex-chip"><i class="fa-solid fa-sliders"></i><strong>${_escapeRadarHtml(lbl)}:</strong> ${actualPart}${_escapeRadarHtml(tgt)}</span>`;
                }).join("")}
            `;
        } else {
            flexNotesEl.style.display = "none";
            flexNotesEl.innerHTML = "";
        }
    }

    // 4. SINCRONIZAÇÃO DE HOVER ENTRE VÉRTICES SVG E LINHAS DO BREAKDOWN
    const highlightPlotIdx = (pIdx) => {
        svgWrap.querySelectorAll(".is-highlighted").forEach(el => el.classList.remove("is-highlighted"));
        breakdownEl.querySelectorAll(".is-highlighted").forEach(el => el.classList.remove("is-highlighted"));
        if (pIdx === null || pIdx < 0 || !plottedAxes[pIdx]) {
            setReadout(null);
            return;
        }
        svgWrap.querySelectorAll(`[data-radar-idx="${pIdx}"]`).forEach(el => el.classList.add("is-highlighted"));
        breakdownEl.querySelectorAll(`[data-radar-idx="${pIdx}"]`).forEach(el => el.classList.add("is-highlighted"));
        setReadout(plottedAxes[pIdx]);
    };

    svgWrap.querySelectorAll("[data-radar-idx]").forEach(el => {
        const pIdx = Number(el.getAttribute("data-radar-idx"));
        if (Number.isNaN(pIdx) || pIdx < 0) return;
        el.addEventListener("mouseenter", () => highlightPlotIdx(pIdx));
        el.addEventListener("mouseleave", () => highlightPlotIdx(null));
    });

    breakdownEl.querySelectorAll(".meta-radar-row").forEach(row => {
        const pIdx = Number(row.getAttribute("data-radar-idx"));
        const aIdx = Number(row.getAttribute("data-axis-idx"));
        row.addEventListener("mouseenter", () => {
            if (pIdx >= 0) {
                highlightPlotIdx(pIdx);
            } else if (axes[aIdx]) {
                row.classList.add("is-highlighted");
                setReadout(axes[aIdx]);
            }
        });
        row.addEventListener("mouseleave", () => {
            row.classList.remove("is-highlighted");
            highlightPlotIdx(null);
        });
    });
}
window.renderMetaRadarChart = renderMetaRadarChart;

let _compareController = null;
let _compareReqId = 0;

async function loadBuildComparison() {
    const rowsContainer = document.getElementById("ins-comparison-rows");
    const scoreCard = document.getElementById("ins-meta-score-card");
    const tierBadge = document.getElementById("ins-meta-tier-badge");
    const scorePctEl = document.getElementById("ins-meta-score-pct");
    const scoreBar = document.getElementById("ins-meta-score-bar");
    const feedbackList = document.getElementById("ins-meta-feedback");
    const gameTag = document.getElementById("ins-compare-game-tag");
    
    if (!rowsContainer || !activeInspectChar) return;

    if (_compareController) {
        _compareController.abort();
    }
    _compareController = new AbortController();
    const reqId = ++_compareReqId;
    const { signal } = _compareController;

    const t = (k, fb) => (window.t ? window.t(k) : fb);
    const isEn = Boolean(window.isEn || (window.getCurrentLanguage && window.getCurrentLanguage() === "en") || window.currentLang === "en");
    
    if (gameTag) {
        gameTag.textContent = `${activeInspectGame.toUpperCase()} • METAGAME BENCHMARK`;
    }
    
    rowsContainer.innerHTML = Array(5).fill(0).map((_, i) => `
        <tr class="skeleton-table-row">
            <td class="comparison-row-title">
                <div class="skeleton-line" style="width: ${i % 2 === 0 ? '70%' : '55%'}; height: 14px;"></div>
            </td>
            <td class="comparison-val-current">
                <div style="display: flex; flex-direction: column; gap: 4px;">
                    <div class="skeleton-line" style="width: 80%; height: 14px;"></div>
                    <div class="skeleton-line" style="width: 45%; height: 10px;"></div>
                </div>
            </td>
            <td class="comparison-val-target">
                <div style="display: flex; justify-content: flex-end;">
                    <div class="skeleton-line" style="width: 75%; height: 14px;"></div>
                </div>
            </td>
        </tr>
    `).join("");
    if (scoreCard) scoreCard.style.display = "none";
    const radarCardEl = document.getElementById("ins-meta-radar-card");
    if (radarCardEl) radarCardEl.style.display = "none";
    
    try {
        const res = await fetch(`/api/compare/${activeInspectGame}/${encodeURIComponent(activeInspectChar.name)}`, { signal });
        const data = await res.json();
        if (reqId !== _compareReqId || signal.aborted) return;
        
        const build = data.player_build || {};
        const target = data.meta_target || {};
        const metaRadar = data.meta_radar || null;

        if ((!build.weapon || build.weapon === "Não informado") && (!build.sets || build.sets.length === 0) && (!target.weapon || target.weapon === "Não informado")) {
            rowsContainer.innerHTML = `
                <tr>
                    <td colspan="3" style="padding: 30px 15px; text-align: center;">
                        <div style="max-width: 440px; margin: 0 auto; color: var(--text-secondary);">
                            <i class="fa-solid fa-code-compare fa-2x" style="color: #38bdf8; margin-bottom: 10px;"></i>
                            <h4 style="margin: 0 0 6px 0; font-size: 14px; color: var(--text-primary);">${isEn ? "No Build Data Found" : "Nenhum Dado de Build Encontrado"}</h4>
                            <p style="font-size: 12px; color: var(--text-muted); line-height: 1.4; margin-bottom: 14px;">
                                ${isEn ? "The Metagame Comparator matches your character's weapons, sets, and benchmarks against community guidelines. Sync your roster to populate your build." : "O Comparador de Metagame avalia armas, relíquias e atributos contra referências oficiais do meta. Sincronize seu roster com o HoYoLAB para carregar as builds da sua conta."}
                            </p>
                            <sakuga-button class="sk-sm" onclick="document.querySelector('.sync-game-btn[data-game=\\'${activeInspectGame}\\']')?.click() || (window.syncRoster && window.syncRoster('${activeInspectGame}'))">
                                <i class="fa-solid fa-arrows-rotate"></i> ${isEn ? "Sync Characters Now" : "Sincronizar Personagens Agora"}
                            </sakuga-button>
                        </div>
                    </td>
                </tr>
            `;
            if (scoreCard) scoreCard.style.display = "none";
            return;
        }
        
        // Dicionário de tradução bidirecional Português <-> Inglês estendido para itens/sets comuns
        const translationDict = {
            // Genshin Weapons
            "luz lazuli": "azurelight",
            "luz lazúli": "azurelight",
            "azurelight": "luz lazúli",
            "galerias da sombra da onda": "finale of the deep galleries",
            "finale of the deep galleries": "galerias da sombra da onda",
            "calamidade de eshu": "calamity of eshu",
            "calamity of eshu": "calamidade de eshu",
            "alvorecer da tecela da lua": "moonweaver's dawn",
            "alvorecer da tecelã da lua": "moonweaver's dawn",
            "moonweaver's dawn": "alvorecer da tecelã da lua",
            "sinfonista dos aromas": "symphonist of scents",
            "symphonist of scents": "sinfonista dos aromas",
            "hino do turbilhao": "hymn of the maelstrom",
            "hino do turbilhão": "hymn of the maelstrom",
            "hymn of the maelstrom": "hino do turbilhão",
            "historias de tamayuratei": "tamayuratei no ohanashi",
            "histórias de tamayuratei": "tamayuratei no ohanashi",
            "tamayuratei no ohanashi": "histórias de tamayuratei",
            "mil sois ardentes": "a thousand blazing suns",
            "mil sóis ardentes": "a thousand blazing suns",
            "a thousand blazing suns": "mil sóis ardentes",
            "cancao da patrulha do pico": "peak patrol song",
            "canção da patrulha do pico": "peak patrol song",
            "peak patrol song": "canção da patrulha do pico",
            "plumagem escarlate do abutre astral": "astral vulture's crimson plumage",
            "astral vulture's crimson plumage": "plumagem escarlate do abutre astral",
            "presa do rei da montanha": "fang of the mountain king",
            "fang of the mountain king": "presa do rei da montanha",
            "prancha pronta": "surf's up",
            "surf's up": "prancha pronta",
            "observador do chamador das estrelas": "starcaller's watch",
            "starcaller's watch": "observador do chamador das estrelas",
            "harmonia das chuvas prateadas": "silvershower heartstrings",
            "silvershower heartstrings": "harmonia das chuvas prateadas",
            "absolvicao": "absolution",
            "absolvição": "absolution",
            "absolution": "absolvição",
            "semblante da lua carmesim": "crimson moon's semblance",
            "crimson moon's semblance": "semblante da lua carmesim",
            "elegia de lumidouce": "lumidouce elegy",
            "lumidouce elegy": "elegia de lumidouce",
            "uraku misugiri": "uraku misugiri",
            "veredito": "verdict",
            "verdict": "veredito",
            "rito do fluxo eterno": "tome of the eternal flow",
            "tome of the eternal flow": "rito do fluxo eterno",
            "supervisao do fluxo de caixa": "cashflow supervision",
            "supervisão do fluxo de caixa": "cashflow supervision",
            "cashflow supervision": "supervisão do fluxo de caixa",
            "sinal dos mares de juncos": "beacon of the reed sea",
            "beacon of the reed sea": "sinal dos mares de juncos",
            "luz das folhas cortadas": "light of foliar incision",
            "light of foliar incision": "luz das folhas cortadas",
            "sonhos flutuantes das mil noites": "a thousand floating dreams",
            "a thousand floating dreams": "sonhos flutuantes das mil noites",
            "caminho do cacador": "hunter's path",
            "caminho do caçador": "hunter's path",
            "hunter's path": "caminho do caçador",
            "mingua de haran geppaku": "haran geppaku futsu",
            "míngua de haran geppaku": "haran geppaku futsu",
            "haran geppaku futsu": "míngua de haran geppaku",
            "prova de kagura": "kagura's verity",
            "kagura's verity": "prova de kagura",
            "chifres vermelhos destruidores de pedras": "redhorn stonethresher",
            "redhorn stonethresher": "chifres vermelhos destruidores de pedras",
            "luz do cortador de grama": "engulfing lightning",
            "engulfing lightning": "luz do cortador de grama",
            "agitacao trovejante": "thundering pulse",
            "agitação trovejante": "thundering pulse",
            "thundering pulse": "agitação trovejante",
            "juramento pela liberdade": "freedom-sworn",
            "freedom-sworn": "juramento pela liberdade",
            "cancao dos pinhos": "song of broken pines",
            "canção dos pinhos": "song of broken pines",
            "song of broken pines": "canção dos pinhos",
            "lanca de jade primitiva": "primordial jade winged-spear",
            "lança de jade primitiva": "primordial jade winged-spear",
            "primordial jade winged-spear": "lança de jade primitiva",
            "arco de amos": "amos' bow",
            "amos' bow": "arco de amos",
            "memoria da poeira": "memory of dust",
            "memória da poeira": "memory of dust",
            "memory of dust": "memória da poeira",
            "perfuradora prismatica": "vortex vanquisher",
            "perfuradora prismática": "vortex vanquisher",
            "vortex vanquisher": "perfuradora prismática",
            "espadao cornigero": "the unforged",
            "espadão cornígero": "the unforged",
            "the unforged": "espadão cornígero",
            "abalador da terra": "earth shaker",
            "earth shaker": "abalador da terra",
            "os sete éditos da poeira e luz": "angelos' heptades",
            "angelos' heptades": "os sete éditos da poeira e luz",
            "cortadora da neblina reforjada": "mistsplitter reforged",
            "mistsplitter reforged": "cortadora da neblina reforjada",
            "asa gelada do lago branco": "whitelake frostfeather",
            "whitelake frostfeather": "asa gelada do lago branco",
            "espada primordial de jade": "primordial jade cutter",
            "primordial jade cutter": "espada primordial de jade",
            "luz lunar de xiphos": "xiphos' moonlight",
            "espinha dorsal da serpente": "serpent spine",
            "esplendor das águas silenciosas": "splendor of silent waters",
            "splendor of silent waters": "esplendor das águas silenciosas",
            "splendor of tranquil waters": "esplendor das águas silenciosas",
            "memórias de sacrifício": "sacrificial fragments",
            "chave de hierofania": "key of khaj-nisut",
            "subjugadora de calamidades": "calamity queller",
            "aqua simulacra": "aqua simulacra",
            "oração perdida aos ventos sagrados": "lost prayer to the sacred winds",
            "histórias extraordinárias de caçadores de dragões": "thrilling tales of dragon slayers",
            "a fisgada": "the catch",
            "arcana original": "the first great magic",
            "espada de favonius": "favonius sword",
            "lâmina amenoma kageuchi": "amenoma kageuchi",
            "amenoma kageuchi": "lâmina amenoma kageuchi",
            "prenúncio do alvorecer": "harbinger of dawn",
            "falcão": "aquila favonia",
            "elegia do suspiro final": "elegy for the end",
            "báculo de homa": "staff of homa",
            "báculo das areias escarlates": "staff of the scarlet sands",
            "túmulo do lobo": "wolf's gravestone",
            "sombra da maré": "tidal shadow",

            // Genshin Sets
            "coração forjado": "heart of the furnace",
            "heart of the furnace": "coração forjado",
            "desencantamento nas sombras profundas": "disenchantment in deep shadow",
            "disenchantment in deep shadow": "desencantamento nas sombras profundas",
            "dádiva celestial": "song of days past",
            "song of days past": "dádiva celestial",
            "pergaminho do herói da cidade incandescente": "scroll of the hero of the cinder city",
            "scroll of the hero of the cinder city": "pergaminho do herói da cidade incandescente",
            "códice de obsidiana": "obsidian codex",
            "obsidian codex": "códice de obsidiana",
            "sombra verde": "viridescent venerer",
            "viridescent venerer": "sombra verde",
            "millelith firmes": "tenacity of the millelith",
            "tenacity of the millelith": "millelith firmes",
            "selo da insulação": "emblem of severed fate",
            "emblem of severed fate": "selo da insulação",
            "herói invernal": "blizzard strayer",
            "caçador das sombras": "marechaussee hunter",
            "trupe dourada": "golden troupe",
            "memórias da floresta": "deepwood memories",
            "sonhos dourados": "gilded dreams",
            "antigo ritual real": "noblesse oblige",
            "noblesse oblige": "antigo ritual real",
            "serenata das estrelas e da lua": "serenade of stars and moon",
            "noite da revelação do céu": "night of the sky's unveiling",
            "juramento da noite eterna": "oath of the eternal night",
            "pedra arcaica": "archaic petra",
            "último juramento do gladiador": "gladiator's finale",

            // HSR Sets & Weapons
            "rumo ao amanhã cor-de-rosa": "fly into a pink tomorrow",
            "fly into a pink tomorrow": "rumo ao amanhã cor-de-rosa",
            "instante de eterno amor": "this love, forever",
            "this love, forever": "instante de eterno amor",
            "as cortinas da memória nunca caem": "memory's curtain never falls",
            "a cortina da memória nunca cai": "memory's curtain never falls",
            "memory's curtain never falls": "as cortinas da memória nunca caem",
            "que os arco-íris adornem o céu": "long may rainbows adorn the sky",
            "long may rainbows adorn the sky": "que os arco-íris adornem o céu",
            "a próxima página da história": "the story's next page",
            "vitória em um piscar de olhos": "victory in a blink",
            "herói da melodia triunfante": "world-remaking deliverer",
            "portador da reconstrução do mundo": "world-remaking deliverer",
            "world-remaking deliverer": "herói da melodia triunfante",
            "lushaka, os mares afundados": "lushaka, the sunken seas",
            "lushaka, the sunken seas": "lushaka, os mares afundados",
            "amphoreus, a terra eterna": "amphoreus, the eternal land",
            "amphoreus, the eternal land": "amphoreus, a terra eterna",
            "mergulhador pioneiro das águas mortas": "pioneer diver of dead waters",
            "pioneer diver of dead waters": "mergulhador pioneiro das águas mortas",
            "profeta de alcance distante": "scholar lost in erudition",
            "scholar lost in erudition": "profeta de alcance distante",
            "provação renascida de sacerdos": "sacerdos' relived ordeal",
            "sacerdos' relived ordeal": "provação renascida de sacerdos",
            "arauto que racha o espaço": "herald of space fracturing",
            "ao véu inalcançável": "along the passing shore",
            "along the passing shore": "ao véu inalcançável",
            "antes do amanhecer": "before dawn",
            "noite sobre a via láctea": "night on the milky way",
            "repouso dos gênios": "geniuses' repose",
            "cálculo eterno": "eternal calculus",
            "hoje também é um dia pacífico": "today is another peaceful day",
            "salsotto inerte": "inert salsotto",
            "izumo gensei e reino divino de takama": "izumo gensei and takama divine realm",
            "fronteira do firmamento: glamoth": "firmament frontline: glamoth",
            "estação de vedação de espaço": "space sealing station",

            // ZZZ Sets & Weapons
            "motor da constelação": "starlight engine",
            "starlight engine": "motor da constelação",
            "lamento das estrelas": "weeping gemini",
            "weeping gemini": "lamento das estrelas",
            "eco rítmico": "rhythm echo",
            "ode ao cavaleiro lunar": "knight's extolment",
            "knight's extolment": "ode ao cavaleiro lunar",
            "o enxofre": "the brimstone",
            "the brimstone": "o enxofre",
            "inocência cortada": "severed innocence",
            "perfeição praticada": "practiced perfection",
            "practiced perfection": "perfeição praticada",
            "ferrão afiado": "sharpened stinger",
            "compilador de fusão": "fusion compiler",
            "brilho labial elétrico": "electro-lip gloss",
            "punk hormonal": "hormone punk",
            "hormone punk": "punk hormonal",
            "techno baiacu": "puffer electro",
            "puffer electro": "techno baiacu",
            "blues livre": "freedom blues",
            "freedom blues": "blues livre",
            "metal presa": "fanged metal",
            "fanged metal": "metal presa",
            "destino emplumado": "feathered fate",
            "feathered fate": "destino emplumado",
            "salão sibilante": "wuthering salon",
            "voz astral": "astral voice",
            "jazz do caos": "chaos jazz",
            "jazz com swing": "swing jazz",
            "metal infernal": "infernal metal",
            "metal polar": "polar metal"
        };
        
        function normalizeStrForMatch(str) {
            if (!str) return "";
            return str.toLowerCase()
                .normalize("NFD").replace(/[\u0300-\u036f]/g, "") // Remove acentos
                .replace(/\([^)]*\)/g, "") // Remove parênteses e níveis
                .replace(/•/g, "")
                .replace(/[^a-z0-9\s]/g, " ")
                .replace(/\s+/g, " ")
                .trim();
        }
        
        function checkFuzzyMatch(name1, name2) {
            if (!name1 || !name2) return false;
            const norm1 = normalizeStrForMatch(name1);
            const norm2 = normalizeStrForMatch(name2);
            
            if (norm1 === norm2 || norm1.includes(norm2) || norm2.includes(norm1)) {
                return true;
            }
            
            // Checa correspondência via dicionário de tradução
            const trans1 = translationDict[norm1] || translationDict[name1.toLowerCase().trim()] || "";
            const trans2 = translationDict[norm2] || translationDict[name2.toLowerCase().trim()] || "";
            
            if (trans1 && (normalizeStrForMatch(trans1) === norm2 || normalizeStrForMatch(trans1).includes(norm2) || norm2.includes(normalizeStrForMatch(trans1)))) {
                return true;
            }
            if (trans2 && (normalizeStrForMatch(trans2) === norm1 || normalizeStrForMatch(trans2).includes(norm1) || norm1.includes(normalizeStrForMatch(trans2)))) {
                return true;
            }
            
            // Checa intersecção de palavras-chave significativas
            const words1 = norm1.split(" ").filter(w => w.length > 3);
            const words2 = norm2.split(" ").filter(w => w.length > 3);
            const overlap = words1.filter(w => words2.includes(w));
            if (overlap.length >= 2 || (words1.length === 1 && words2.length === 1 && overlap.length === 1)) {
                return true;
            }
            return false;
        }

        function getUnifiedSlotKey(slotStr, gameId) {
            if (!slotStr) return "";
            const s = String(slotStr).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]/g, "").trim();
            const g = (gameId || activeInspectGame || "").toLowerCase();
            
            if (g === "genshin") {
                if (s === "1" || s.includes("flor") || s.includes("flower")) return "flower";
                if (s === "2" || s.includes("pena") || s.includes("plume") || s.includes("pluma") || s.includes("feather")) return "plume";
                if (s === "3" || s.includes("areia") || s.includes("relogio") || s.includes("ampulheta") || s.includes("sands")) return "sands";
                if (s === "4" || s.includes("copo") || s.includes("calice") || s.includes("goblet")) return "goblet";
                if (s === "5" || s.includes("tiara") || s.includes("coroa") || s.includes("circlet")) return "circlet";
            } else if (g === "hsr") {
                if (s === "1" || s.includes("cabeca") || s.includes("head")) return "head";
                if (s === "2" || s.includes("mao") || s.includes("maos") || s.includes("hands")) return "hands";
                if (s === "3" || s.includes("corpo") || s.includes("body")) return "body";
                if (s === "4" || s.includes("pe") || s.includes("pes") || s.includes("bota") || s.includes("feet")) return "feet";
                if (s === "5" || s.includes("esfera") || s.includes("sphere")) return "planar_sphere";
                if (s === "6" || s.includes("corda") || s.includes("rope")) return "link_rope";
            } else if (g === "zzz") {
                for (let i = 1; i <= 6; i++) {
                    if (s === String(i) || s.includes(`disco${i}`) || s.includes(`disk${i}`) || s.includes(`slot${i}`)) {
                        return `slot_${i}`;
                    }
                }
            }

            // Mapeamento genérico
            if (s.includes("corpo") || s.includes("body")) return "body";
            if (s.includes("bota") || s.includes("pes") || s.includes("feet")) return "feet";
            if (s.includes("esfera") || s.includes("sphere")) return "planar_sphere";
            if (s.includes("corda") || s.includes("rope")) return "link_rope";
            if (s.includes("areia") || s.includes("ampulheta") || s.includes("sands")) return "sands";
            if (s.includes("copo") || s.includes("calice") || s.includes("goblet")) return "goblet";
            if (s.includes("tiara") || s.includes("circlet")) return "circlet";
            if (s.includes("flor") || s.includes("flower")) return "flower";
            if (s.includes("pena") || s.includes("plume")) return "plume";

            return s;
        }

        function normalizeStatTerm(str) {
            if (!str) return "";
            let s = String(str).toLowerCase()
                .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
                .replace(/\([^)]*\)/g, "") // Remove números entre parênteses ex: (46.6%)
                .replace(/[0-9.,%+]/g, "")
                .trim();
                
            if (s === "anything" || s === "any" || s.includes("qualquer") || s === "flex" || s === "flexible") return "anything";
            if (s.includes("quebra") || s.includes("break")) return "break";
            if (s.includes("taxa") || s.includes("rate") || s.includes("chance")) return "crit_rate";
            if (s.includes("dano crit") || s.includes("crit dmg") || s.includes("dano crt")) return "crit_dmg";
            if (s.includes("crit")) return "crit";
            if (s.includes("recarga") || s.includes("recharge") || s.includes("regen") || s.includes("recup") || s.includes("er") || s.includes("err")) return "er";
            if (s.includes("prof") || s.includes("mastery") || s.includes("em") || s.includes("anomalia")) return "em";
            if (s.includes("atq") || s.includes("atk") || s.includes("ataque")) return "atk";
            if (s.includes("pv") || s.includes("hp") || s.includes("vida")) return "hp";
            if (s.includes("def") || s.includes("defesa")) return "def";
            if (s.includes("vel") || s.includes("spd") || s.includes("velocidade")) return "speed";
            if (s.includes("cura") || s.includes("healing")) return "healing";
            if (s.includes("perfura") || s.includes("pen")) return "pen";
            if (s.includes("impact") || s.includes("impacto")) return "impact";
            if (s.includes("dano") || s.includes("bonus") || s.includes("dmg")) return "elemental_dmg";

            return s;
        }
        
        let scoreTotal = 0;
        let scoreMax = 100;
        let feedbackBullets = [];
        
        let html = "";
        
        // ==========================================
        // 1. AVALIAÇÃO DE ARMA / CONE / W-ENGINE (25 pts)
        // ==========================================
        const rawPlayerWeapon = build.weapon || "Não informado";
        const cleanPlayerWeapon = (build.weapon_clean || rawPlayerWeapon).replace(/\(Nv\..*?\)/gi, "").replace(/\(R[1-5]\)/gi, "").replace(/\(Sobreposição \d\)/gi, "").trim();
        const recommendedWeapons = target.weapons && target.weapons.length > 0 ? target.weapons : (target.weapon !== "Não informado" ? [target.weapon] : []);
        
        let weaponMatchTier = 0; // 0: None, 1: Bis (1st), 2: Alternate, 3: Viable
        if (recommendedWeapons.length > 0 && cleanPlayerWeapon && cleanPlayerWeapon !== "Não informado") {
            if (checkFuzzyMatch(cleanPlayerWeapon, recommendedWeapons[0])) {
                weaponMatchTier = 1; // Best in Slot
            } else if (recommendedWeapons.slice(1).some(w => checkFuzzyMatch(cleanPlayerWeapon, w))) {
                weaponMatchTier = 2; // Recomendada na lista
            } else if (cleanPlayerWeapon.length > 3) {
                weaponMatchTier = 3; // Alternativa equipada
            }
        }
        
        let weaponBadgeHtml = "";
        let weaponScore = 0;
        if (weaponMatchTier === 1) {
            weaponScore = 25;
            weaponBadgeHtml = `<span class="comparison-badge match"><i class="fa-solid fa-crown"></i> ${t("comp_badge_bis", "Ideal (BIS)")}</span>`;
            feedbackBullets.push(isEn 
                ? `<strong>Weapon:</strong> <span style="color: #10b981;">Ideal (Best in Slot)</span> successfully equipped.`
                : (isEn ? `<strong>Weapon:</strong> <span style="color: #10b981;">Best in Slot equipped</span> successfully.` : `<strong>Arma:</strong> <span style="color: #10b981;">Ideal (Best in Slot) equipada</span> com sucesso.`));
        } else if (weaponMatchTier === 2) {
            weaponScore = 20;
            weaponBadgeHtml = `<span class="comparison-badge match"><i class="fa-solid fa-check"></i> ${t("comp_badge_rec", "Recomendada")}</span>`;
            feedbackBullets.push(isEn 
                ? `<strong>Weapon:</strong> <span style="color: #38bdf8;">Recommended option</span> equipped.`
                : (isEn ? `<strong>Weapon:</strong> <span style="color: #38bdf8;">Recommended option</span> equipped.` : `<strong>Arma:</strong> <span style="color: #38bdf8;">Opção recomendada</span> pelo metagame equipada.`));
        } else if (weaponMatchTier === 3) {
            weaponScore = 12;
            weaponBadgeHtml = `<span class="comparison-badge warning"><i class="fa-solid fa-triangle-exclamation"></i> ${t("comp_badge_alt", "Alternativa")}</span>`;
            feedbackBullets.push(isEn 
                ? `<strong>Weapon:</strong> Using a viable alternative. The ideal pick is <em>${recommendedWeapons[0] || 'BIS weapon'}</em>.`
                : (isEn ? `<strong>Weapon:</strong> Using viable alternative. Optimal for peak damage/support is <em>${recommendedWeapons[0] || 'BIS weapon'}</em>.` : `<strong>Arma:</strong> Usando alternativa viável. O ideal para pico de dano/suporte é <em>${recommendedWeapons[0] || 'arma BIS'}</em>.`));
        } else {
            weaponScore = 0;
            weaponBadgeHtml = `<span class="comparison-badge mismatch"><i class="fa-solid fa-xmark"></i> ${t("comp_badge_sub", "Subótimo")}</span>`;
            feedbackBullets.push(isEn 
                ? `<strong>Weapon:</strong> No meta weapon identified. Recommended to acquire <em>${recommendedWeapons[0] || 'recommended weapon'}</em>.`
                : (isEn ? `<strong>Weapon:</strong> No meta weapon identified. Recommended to obtain <em>${recommendedWeapons[0] || 'recommended weapon'}</em>.` : `<strong>Arma:</strong> Nenhuma arma meta identificada. Recomendado buscar <em>${recommendedWeapons[0] || 'arma recomendada'}</em>.`));
        }
        scoreTotal += weaponScore;
        
        const displayTargetWeapon = translationDict[String(target.weapon || '').toLowerCase().trim()] || target.weapon;
        
        html += `
            <tr class="comparison-section-header"><td colspan="3"><i class="fa-solid fa-shield-halved" style="margin-right: 6px; color: var(--color-hsr);"></i> ${t("comp_sec_equip", "Equipamentos e Conjuntos")}</td></tr>
            <tr>
                <td class="comparison-row-title"><i class="fa-solid fa-wand-magic-sparkles" style="margin-right: 6px; opacity: 0.7;"></i> ${t("comp_weapon", "Arma / Cone")}</td>
                <td>
                    <div style="display: flex; flex-direction: column; gap: 3px;">
                        <span style="font-weight: 600; color: var(--text-primary);">${rawPlayerWeapon}</span>
                        ${weaponBadgeHtml}
                    </div>
                </td>
                <td class="comparison-val-target">
                    <strong style="color: var(--text-primary);">${displayTargetWeapon}</strong>
                    ${recommendedWeapons.length > 1 ? `<div style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">+ ${recommendedWeapons.length - 1} ${isEn ? "viable options" : "opções viáveis"}</div>` : ''}
                </td>
            </tr>
        `;
        
        // ==========================================
        // 2. AVALIAÇÃO DE CONJUNTOS / SETS (25 pts)
        // ==========================================
        const playerSets = build.sets || [];

        const currentSetsStr = playerSets.join(" + ") || (isEn ? "No active set bonus" : "Nenhum conjunto ativo");
        const recommendedSets = target.all_sets && target.all_sets.length > 0 ? target.all_sets : (target.sets && target.sets[0] !== "Não informado" ? target.sets : []);
        const targetSetsStr = target.sets && target.sets[0] !== "Não informado" ? target.sets.join(" / ") : "Não informado";
        
        let setMatchTier = 0; // 0: None, 1: 4p Bis, 2: 2p+2p / Sub, 3: Active
        if (playerSets.length > 0 && recommendedSets.length > 0) {
            const hasBisMatch = playerSets.some(pS => checkFuzzyMatch(pS, recommendedSets[0]));
            const hasAnyRecMatch = playerSets.some(pS => recommendedSets.some(rS => checkFuzzyMatch(pS, rS)));
            
            if (hasBisMatch && playerSets.some(pS => pS.includes("4 peças") || pS.includes("4p"))) {
                setMatchTier = 1; // 4p BIS
            } else if (hasAnyRecMatch) {
                setMatchTier = 2; // 2p recomendado
            } else if (playerSets.some(pS => pS.includes("4 peças") || pS.includes("2 peças"))) {
                setMatchTier = 3; // Conjunto ativo genérico
            }
        }
        
        let setBadgeHtml = "";
        let setScore = 0;
        if (setMatchTier === 1) {
            setScore = 25;
            setBadgeHtml = `<span class="comparison-badge match"><i class="fa-solid fa-circle-check"></i> ${t("comp_badge_set_bis", "4p BIS Ideal")}</span>`;
            feedbackBullets.push(isEn 
                ? `<strong>Set:</strong> <span style="color: #10b981;">Ideal 4-piece bonus</span> active.`
                : `<strong>Conjunto:</strong> <span style="color: #10b981;">Bônus de 4 peças ideal</span> ativo.`);
        } else if (setMatchTier === 2) {
            setScore = 20;
            setBadgeHtml = `<span class="comparison-badge match"><i class="fa-solid fa-check"></i> ${t("comp_badge_set_meta", "Conjunto Meta")}</span>`;
            feedbackBullets.push(isEn 
                ? `<strong>Set:</strong> <span style="color: #38bdf8;">Recommended set</span> equipped.`
                : (isEn ? `<strong>Set:</strong> <span style="color: #38bdf8;">Recommended set</span> equipped.` : `<strong>Conjunto:</strong> <span style="color: #38bdf8;">Conjunto recomendado</span> equipado.`));
        } else if (setMatchTier === 3) {
            setScore = 12;
            setBadgeHtml = `<span class="comparison-badge warning"><i class="fa-solid fa-triangle-exclamation"></i> ${t("comp_badge_set_alt", "Alternativo")}</span>`;
            feedbackBullets.push(isEn 
                ? `<strong>Set:</strong> Bonus active, but recommended set is <em>${recommendedSets[0] || 'meta 4pc set'}</em>.`
                : (isEn ? `<strong>Set:</strong> Active bonus, but ideal recommended set is <em>${recommendedSets[0] || 'meta 4-PC set'}</em>.` : `<strong>Conjunto:</strong> Bônus ativo, mas conjunto ideal recomendado é <em>${recommendedSets[0] || 'o set 4p do meta'}</em>.`));
        } else {
            setScore = 0;
            setBadgeHtml = `<span class="comparison-badge mismatch"><i class="fa-solid fa-xmark"></i> ${t("comp_badge_set_inc", "Incompleto")}</span>`;
            feedbackBullets.push(isEn 
                ? `<strong>Set:</strong> No recommended set bonus active.`
                : `<strong>Conjunto:</strong> Sem bônus de conjunto ideal ativo.`);
        }
        scoreTotal += setScore;
        
        html += `
            <tr>
                <td class="comparison-row-title"><i class="fa-solid fa-gem" style="margin-right: 6px; opacity: 0.7;"></i> ${t("comp_sets", "Conjuntos")}</td>
                <td>
                    <div style="display: flex; flex-direction: column; gap: 3px;">
                        <span style="font-weight: 500; color: var(--text-primary);">${currentSetsStr}</span>
                        ${setBadgeHtml}
                    </div>
                </td>
                <td class="comparison-val-target">
                    <strong style="color: var(--text-primary);">${targetSetsStr}</strong>
                    ${recommendedSets.length > 1 ? `<div style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">+ combinações 2p/planares</div>` : ''}
                </td>
            </tr>
        `;
        
        // ==========================================
        // 3. ATRIBUTOS PRINCIPAIS POR SLOT (30 pts)
        // ==========================================
        const targetStatsKeys = Object.keys(target.stats || {});
        
        if (targetStatsKeys.length > 0) {
            html += `
                <tr class="comparison-section-header"><td colspan="3"><i class="fa-solid fa-bullseye" style="margin-right: 6px; color: #f59e0b;"></i> ${t("comp_sec_main", "Atributos Principais por Slot (Main Stats)")}</td></tr>
            `;
            
            const pointsPerSlot = 30 / targetStatsKeys.length;
            let slotIssues = [];
            
            targetStatsKeys.forEach(key => {
                let playerVal = isEn ? "Not equipped" : "Não equipado";
                let statClass = "comparison-mismatch";
                let slotBadgeHtml = "";
                
                // Mapeia peça correspondente ao slot
                const matchedPiece = (build.pieces || []).find(p => {
                    const pKey = getUnifiedSlotKey(p.slot, activeInspectGame);
                    const tKey = getUnifiedSlotKey(key, activeInspectGame);
                    return (pKey && tKey && pKey === tKey) || p.slot.toLowerCase().trim().includes(key.toLowerCase().trim()) || key.toLowerCase().trim().includes(p.slot.toLowerCase().trim());
                });
                
                if (matchedPiece && matchedPiece.main) {
                    playerVal = matchedPiece.main;
                    const rawTargetSlot = String(target.stats[key] || "");
                    const targetValLower = rawTargetSlot.toLowerCase();
                    const options = targetValLower.split(/[=/>|]|\bou\b/).map(s => s.trim()).filter(Boolean);
                    
                    const mainNorm = normalizeStatTerm(matchedPiece.main);
                    const hasFlexMarker = /\b(?:anything|any|qualquer|flex(?:ible|ivel)?)\b/i.test(
                        rawTargetSlot.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
                    );
                    const isWildcardTarget = hasFlexMarker || options.some(opt => normalizeStatTerm(opt) === "anything");

                    // Match exato com a primeira opção (Prioridade máxima) ou curinga (Qualquer/Flex/Anything)
                    const firstOptNorm = normalizeStatTerm(options[0] || "");
                    const isFirstMatch = isWildcardTarget || (firstOptNorm && (mainNorm === firstOptNorm || mainNorm.includes(firstOptNorm) || firstOptNorm.includes(mainNorm)));
                    
                    // Match com qualquer opção alternativa
                    const isAnyMatch = isFirstMatch || options.slice(1).some(opt => {
                        const optNorm = normalizeStatTerm(opt);
                        return optNorm && (mainNorm === optNorm || mainNorm.includes(optNorm) || optNorm.includes(mainNorm));
                    });
                    
                    if (isFirstMatch) {
                        scoreTotal += pointsPerSlot;
                        statClass = "comparison-match";
                        const slotLabel = isWildcardTarget && (!firstOptNorm || firstOptNorm === "anything" || options.length === 1)
                            ? t("comp_badge_slot_flex", "Flexível")
                            : t("comp_badge_slot_ideal", "Ideal");
                        slotBadgeHtml = `<span class="comparison-badge match" style="margin-left: 6px;"><i class="fa-solid fa-check"></i> ${slotLabel}</span>`;
                    } else if (isAnyMatch) {
                        scoreTotal += pointsPerSlot * 0.75;
                        statClass = "comparison-warning";
                        slotBadgeHtml = `<span class="comparison-badge warning" style="margin-left: 6px;"><i class="fa-solid fa-check-double"></i> ${t("comp_badge_slot_valid", "Válido")}</span>`;
                    } else {
                        statClass = "comparison-mismatch";
                        slotBadgeHtml = `<span class="comparison-badge mismatch" style="margin-left: 6px;"><i class="fa-solid fa-xmark"></i> ${t("comp_badge_slot_mismatch", "Incompatível")}</span>`;
                        slotIssues.push(`${key} (${rawTargetSlot})`);
                    }
                } else {
                    slotBadgeHtml = `<span class="comparison-badge mismatch" style="margin-left: 6px;"><i class="fa-solid fa-circle-question"></i> ${t("comp_badge_slot_empty", "Vazio")}</span>`;
                    slotIssues.push(key);
                }
                
                const displaySlotTarget = isEn
                    ? String(target.stats[key] || "").replace(/Qualquer\s*\(Flex\)/gi, "Any (Flex)")
                    : String(target.stats[key] || "");
                html += `
                    <tr>
                        <td class="comparison-row-title">• ${key}</td>
                        <td class="${statClass}">
                            <div style="display: flex; align-items: center; justify-content: space-between;">
                                <span>${playerVal}</span>
                                ${slotBadgeHtml}
                            </div>
                        </td>
                        <td class="comparison-val-target">${displaySlotTarget}</td>
                    </tr>
                `;
            });
            
            if (slotIssues.length === 0) {
                feedbackBullets.push(isEn ? `<strong>Main Stats:</strong> <span style="color: #10b981;">All key slots</span> have ideal main stats.` : `<strong>Main Stats:</strong> <span style="color: #10b981;">Todos os slots chave</span> possuem os atributos principais ideais.`);
            } else {
                feedbackBullets.push(isEn ? `<strong>Main Stats:</strong> Prioritize replacing pieces with incorrect main stats on: <em>${slotIssues.join(", ")}</em>.` : `<strong>Main Stats:</strong> Priorize trocar peças com main stats incorretos em: <em>${slotIssues.join(", ")}</em>.`);
            }
        }
        
        // ==========================================
        // 4. GRÁFICO RADAR DE BENCHMARKS META (20 pts — substitui linhas planas na tabela)
        // ==========================================
        if (metaRadar && ((metaRadar.axes && metaRadar.axes.length > 0) || (metaRadar.flex_notes && metaRadar.flex_notes.length > 0))) {
            renderMetaRadarChart(metaRadar, activeInspectGame);
            const radarSummary = metaRadar.summary || {};
            scoreTotal += Number(radarSummary.benchmark_score_20 || 0);

            const lagging = (metaRadar.axes || []).filter(ax => ax.status === "low" || ax.status === "close");
            if (lagging.length === 0) {
                feedbackBullets.push(
                    isEn
                        ? `<strong>Meta Benchmarks:</strong> <span style="color: #10b981;">All target stats reached</span> on the Radar.`
                        : `<strong>Benchmarks Meta:</strong> <span style="color: #10b981;">Todos os alvos de atributos atingidos</span> no Radar.`
                );
            } else {
                const lagNames = lagging.slice(0, 3).map(ax => {
                    const lbl = isEn ? (ax.label_en || ax.label_pt) : (ax.label_pt || ax.label_en);
                    if ((ax.tags || []).includes("in_combat")) {
                        return isEn
                            ? `${lbl} (${ax.actual_display} out of combat / in-combat target)`
                            : `${lbl} (${ax.actual_display} na tela — meta em combate)`;
                    }
                    return ax.diff_display ? `${lbl} (${ax.diff_display})` : lbl;
                });
                feedbackBullets.push(
                    isEn
                        ? `<strong>Meta Benchmarks:</strong> Focus on improving: <em>${lagNames.join(", ")}</em>.`
                        : `<strong>Benchmarks Meta:</strong> Foque em melhorar: <em>${lagNames.join(", ")}</em>.`
                );
            }
        } else {
            renderMetaRadarChart(null, activeInspectGame);
        }
        
        rowsContainer.innerHTML = html;
        
        // ==========================================
        // 5. RENDERIZA CARD DE SCORE EXECUTIVO
        // ==========================================
        const finalScorePct = Math.min(100, Math.max(0, Math.round(scoreTotal)));
        
        if (scoreCard && tierBadge && scorePctEl && scoreBar && feedbackList) {
            scoreCard.style.display = "block";
            scorePctEl.textContent = `${finalScorePct}%`;
            scoreBar.style.width = `${finalScorePct}%`;
            
            if (finalScorePct >= 85) {
                tierBadge.textContent = "S-Tier";
                tierBadge.style.background = "rgba(16, 185, 129, 0.2)";
                tierBadge.style.color = "#10b981";
                tierBadge.style.borderColor = "#10b981";
                scorePctEl.style.color = "#10b981";
                scoreBar.style.background = "linear-gradient(90deg, #10b981, #059669)";
            } else if (finalScorePct >= 70) {
                tierBadge.textContent = "A-Tier";
                tierBadge.style.background = "rgba(56, 189, 248, 0.2)";
                tierBadge.style.color = "#38bdf8";
                tierBadge.style.borderColor = "#38bdf8";
                scorePctEl.style.color = "#38bdf8";
                scoreBar.style.background = "linear-gradient(90deg, #38bdf8, #0284c7)";
            } else if (finalScorePct >= 50) {
                tierBadge.textContent = "B-Tier";
                tierBadge.style.background = "rgba(245, 158, 11, 0.2)";
                tierBadge.style.color = "#f59e0b";
                tierBadge.style.borderColor = "#f59e0b";
                scorePctEl.style.color = "#f59e0b";
                scoreBar.style.background = "linear-gradient(90deg, #f59e0b, #d97706)";
            } else {
                tierBadge.textContent = "C-Tier";
                tierBadge.style.background = "rgba(239, 68, 68, 0.2)";
                tierBadge.style.color = "#ef4444";
                tierBadge.style.borderColor = "#ef4444";
                scorePctEl.style.color = "#ef4444";
                scoreBar.style.background = "linear-gradient(90deg, #ef4444, #b91c1c)";
            }
            
            feedbackList.innerHTML = feedbackBullets.map(b => `<div style="display: flex; gap: 6px; align-items: flex-start;"><span style="color: var(--color-hsr);">•</span> <span>${b}</span></div>`).join("");
        }
        
    } catch(err) {
        if (err?.name === "AbortError" || reqId !== _compareReqId) return;
        console.error("Erro ao carregar comparação de builds:", err);
        const safeCharName = (activeInspectChar?.name || "").replace(/'/g, "\\'");
        rowsContainer.innerHTML = `
            <tr>
                <td colspan="3" style="padding: 30px 15px; text-align: center;">
                    <div style="max-width: 420px; margin: 0 auto; color: var(--text-secondary);">
                        <i class="fa-solid fa-circle-exclamation fa-2x" style="color: #ef4444; margin-bottom: 10px;"></i>
                        <h4 style="margin: 0 0 6px 0; font-size: 14px; color: #f87171;">${isEn ? "Failed to Load Metagame Comparison" : "Não foi possível carregar o comparativo de metagame"}</h4>
                        <p style="font-size: 12px; color: var(--text-muted); line-height: 1.4; margin-bottom: 14px;">
                            ${isEn ? "Could not retrieve meta targets or player build. Please check your connection." : "Não foi possível consultar os alvos do meta ou os dados do personagem. Verifique sua conexão e tente novamente."}
                        </p>
                        <sakuga-button class="sk-sm sk-accent-danger" onclick="window.loadComparison && window.loadComparison('${safeCharName}', '${activeInspectGame}')">
                            <i class="fa-solid fa-arrow-rotate-right"></i> ${isEn ? "Try Again" : "Tentar de novo"}
                        </sakuga-button>
                    </div>
                </td>
            </tr>
        `;
    }
}


// ==========================================
// GERADOR DE CARD DE COMPARATIVO DE BUILD (PNG)
// ==========================================

window.generateAndOpenDiffCardModal = async function() {
    const cData = window.currentDiffDataCache;
    if (!cData) {

    showToast(isEn ? "No comparison selected to generate card." : "Nenhum comparativo selecionado para gerar card.");
        return;
    }

    const modal = document.getElementById("modal-export-diff-card");
    const container = document.getElementById("diff-card-preview-container");
    const downloadBtn = document.getElementById("btn-download-diff-card-png");
    const copyBtn = document.getElementById("btn-copy-diff-card-png");

    if (!modal || !container) return;

    modal.style.display = "flex";
    container.innerHTML = `<p style="color: var(--text-muted); padding: 40px; font-size: 14px;"><i class="fa-solid fa-spinner fa-spin fa-2x" style="color: #ec4899; margin-bottom: 12px; display: block;"></i> Renderizando Card em Alta Resolução...</p>`;

    try {
        const canvas = await generateDiffCardCanvas(cData);
        container.innerHTML = "";
        
        const img = document.createElement("img");
        img.src = canvas.toDataURL("image/png");
        img.style.maxWidth = "100%";
        img.style.maxHeight = "60vh";
        img.style.borderRadius = "10px";
        img.style.boxShadow = "0 10px 30px rgba(0,0,0,0.5)";
        container.appendChild(img);

        if (downloadBtn) {
            downloadBtn.href = img.src;

        downloadBtn.download = `comparison_${(cData.name || (isEn ? 'character' : 'personagem')).toLowerCase().replace(/\s+/g, '_')}.png`;
        }

        if (copyBtn) {
            copyBtn.onclick = async () => {
                try {
                    canvas.toBlob(async (blob) => {
                        if (!blob) throw new Error("Falha ao criar blob.");
                        await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
                        if (typeof copyBtn.done === "function") copyBtn.done();
                        showToast("Card de comparativo copiado para a área de transferência!", "success");
                    });
                } catch (err) {
                    showToast("Erro ao copiar imagem: " + err.message);
                }
            };
        }
    } catch (err) {
        console.error("Erro ao gerar card:", err);
        container.innerHTML = `<p style="color: #ef4444; padding: 20px;"><i class="fa-solid fa-triangle-exclamation"></i> Ocorreu um erro ao gerar o card da comparação: ${err.message}</p>`;
    }
};

async function generateDiffCardCanvas(cData) {
    const canvas = document.createElement("canvas");
    const width = 1200;
    const height = 860;
    canvas.width = width * 2;
    canvas.height = height * 2;
    const ctx = canvas.getContext("2d");
    ctx.scale(2, 2);

    // Helpers de desenho no Canvas
    function drawRoundedRect(x, y, w, h, r, fillStyle, strokeStyle, lineWidth = 1) {
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + w - r, y);
        ctx.quadraticCurveTo(x + w, y, x + w, y + r);
        ctx.lineTo(x + w, y + h - r);
        ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
        ctx.lineTo(x + r, y + h);
        ctx.quadraticCurveTo(x, y + h, x, y + h - r);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.closePath();
        if (fillStyle) {
            ctx.fillStyle = fillStyle;
            ctx.fill();
        }
        if (strokeStyle) {
            ctx.strokeStyle = strokeStyle;
            ctx.lineWidth = lineWidth;
            ctx.stroke();
        }
    }

    function loadImage(url) {
        return new Promise((resolve) => {
            if (!url) return resolve(null);
            let finalUrl = url;
            if (url.startsWith("http://") || url.startsWith("https://")) {
                finalUrl = `/api/proxy_image?url=${encodeURIComponent(url)}`;
            }
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => resolve(img);
            img.onerror = () => resolve(null);
            img.src = finalUrl;
        });
    }

    // Fundo Gradiente Escuro Elegante
    const bgGrad = ctx.createLinearGradient(0, 0, width, height);
    bgGrad.addColorStop(0, "#0b0f19");
    bgGrad.addColorStop(0.5, "#0f172a");
    bgGrad.addColorStop(1, "#180a22");
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, width, height);

    // Glow de Destaque Rosa/Violeta
    const glowGrad = ctx.createRadialGradient(200, 150, 20, 200, 150, 600);
    glowGrad.addColorStop(0, "rgba(236, 72, 153, 0.18)");
    glowGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = glowGrad;
    ctx.fillRect(0, 0, width, height);

    // Carrega Imagem do Personagem
    const charImg = await loadImage(cData.icon);

    const base = cData.base || {};
    const target = cData.target || {};
    const diffs = cData.diffs || {};

    // 1. CABEÇALHO DO CARD
    drawRoundedRect(30, 24, width - 60, 110, 16, "rgba(15, 23, 42, 0.8)", "rgba(236, 72, 153, 0.4)", 1.5);

    if (charImg) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(85, 79, 40, 0, Math.PI * 2);
        ctx.closePath();
        ctx.clip();
        ctx.drawImage(charImg, 45, 39, 80, 80);
        ctx.restore();

        ctx.beginPath();
        ctx.arc(85, 79, 40, 0, Math.PI * 2);
        ctx.strokeStyle = "#ec4899";
        ctx.lineWidth = 3;
        ctx.stroke();
    }

    ctx.fillStyle = "#fff";
    ctx.font = "bold 24px sans-serif";
    ctx.fillText(cData.name || "Personagem", 145, 62);

    ctx.fillStyle = "rgba(255, 255, 255, 0.6)";
    ctx.font = "14px sans-serif";
    ctx.fillText(`EVOLUÇÃO DE BUILD • ${cData.rarity || 5}★ ${cData.element || ''}`, 145, 86);

    const scorePrev = base.score || 0.0;
    const scoreCurr = target.score || 0.0;
    const scoreDiff = diffs.score_diff !== undefined ? diffs.score_diff : (scoreCurr - scorePrev).toFixed(1);

    // KPI Badge no Canto do Cabeçalho
    drawRoundedRect(width - 240, 42, 190, 74, 12, "rgba(236, 72, 153, 0.15)", "rgba(236, 72, 153, 0.4)");
    ctx.fillStyle = "#ec4899";
    ctx.font = "bold 11px sans-serif";
    ctx.fillText("EVOLUÇÃO RV (BUILD SCORE)", width - 225, 62);
    ctx.fillStyle = "#fff";
    ctx.font = "bold 20px sans-serif";
    ctx.fillText(`${scorePrev ? scorePrev + '% ➔ ' : ''}${scoreCurr}%`, width - 225, 90);
    if (parseFloat(scoreDiff) > 0) {
        ctx.fillStyle = "#10b981";
        ctx.font = "bold 13px sans-serif";
        ctx.fillText(`+${scoreDiff}%`, width - 85, 90);
    }

    // 2. SEÇÃO DA ARMA
    drawRoundedRect(30, 150, 560, 95, 12, "rgba(0, 0, 0, 0.4)", "rgba(255, 255, 255, 0.1)");
    ctx.fillStyle = "#38bdf8";
    ctx.font = "bold 13px sans-serif";

    ctx.fillText(isEn ? "WEAPON / LIGHT CONE / W-ENGINE" : "ARMA / CONE DE LUZ / W-ENGINE", 45, 170);

    const wBase = base.weapon || (base.weapon_name ? { name: base.weapon_name, level: base.weapon_level, icon: base.weapon_icon } : null);
    const wTarget = target.weapon || (target.weapon_name ? { name: target.weapon_name, level: target.weapon_level, icon: target.weapon_icon } : null);

    const wBaseImg = await loadImage(wBase?.icon);
    const wTargetImg = await loadImage(wTarget?.icon);

    if (wBaseImg) ctx.drawImage(wBaseImg, 45, 180, 42, 42);
    ctx.fillStyle = "#94a3b8";
    ctx.font = "12px sans-serif";
    ctx.fillText(wBase?.name || (isEn ? "None" : "Nenhuma"), 98, 197);
    ctx.font = "11px sans-serif";
    ctx.fillText(`Nv. ${wBase?.level || 1}`, 98, 213);

    ctx.fillStyle = "#ec4899";
    ctx.font = "bold 16px sans-serif";
    ctx.fillText("➔", 285, 205);

    if (wTargetImg) ctx.drawImage(wTargetImg, 315, 180, 42, 42);
    ctx.fillStyle = "#fff";
    ctx.font = "bold 13px sans-serif";
    ctx.fillText(wTarget?.name || (isEn ? "None" : "Nenhuma"), 368, 197);
    ctx.fillStyle = "#10b981";
    ctx.font = "11px sans-serif";
    ctx.fillText(`Nv. ${wTarget?.level || 1}`, 368, 213);

    // 2.5. SEÇÃO DE HABILIDADES E TALENTOS
    drawRoundedRect(30, 255, 560, 130, 12, "rgba(0, 0, 0, 0.4)", "rgba(255, 255, 255, 0.1)");
    ctx.fillStyle = "#38bdf8";
    ctx.font = "bold 13px sans-serif";
    ctx.fillText("EVOLUÇÃO DE HABILIDADES & TALENTOS", 45, 275);

    const skillsBase = base.skills || [];
    const skillsTarget = target.skills || [];
    const allSkillNames = listUniqueSkillKeys(skillsBase, skillsTarget).slice(0, 6);

    // Carrega em paralelo os ícones de todas as habilidades para desenhar no card
    const skillImgMap = {};
    await Promise.all(allSkillNames.map(async sName => {
        const sb = skillsBase.find(x => (x.name || x.skill_name) === sName);
        const st = skillsTarget.find(x => (x.name || x.skill_name) === sName);
        const iconUrl = (st || sb || {}).icon;
        if (iconUrl) {
            const img = await loadImage(iconUrl);
            if (img) skillImgMap[sName] = img;
        }
    }));

    if (allSkillNames.length === 0) {
        ctx.fillStyle = "#94a3b8";
        ctx.font = "italic 11px sans-serif";
        ctx.fillText("Sem dados de habilidades para comparar", 60, 315);
    } else {
        for (let idx = 0; idx < allSkillNames.length; idx++) {
            const sName = allSkillNames[idx];
            const sb = skillsBase.find(x => (x.name || x.skill_name) === sName);
            const st = skillsTarget.find(x => (x.name || x.skill_name) === sName);
            const lvlB = sb ? (sb.level || sb.lvl || 0) : 0;
            const lvlT = st ? (st.level || st.lvl || 0) : 0;
            const diff = lvlT - lvlB;

            const col = idx % 2;
            const row = Math.floor(idx / 2);

            const xPill = col === 0 ? 45 : 315;
            const yPill = 287 + row * 28;

            drawRoundedRect(xPill, yPill, 255, 24, 6, "rgba(15, 23, 42, 0.8)", "rgba(255, 255, 255, 0.05)");

            const sImg = skillImgMap[sName];
            let xText = xPill + 10;
            if (sImg) {
                ctx.save();
                ctx.beginPath();
                ctx.arc(xPill + 16, yPill + 12, 9, 0, Math.PI * 2);
                ctx.closePath();
                ctx.clip();
                ctx.drawImage(sImg, xPill + 7, yPill + 3, 18, 18);
                ctx.restore();
                xText = xPill + 30;
            }

            const maxNameLen = sImg ? 14 : 17;
            const displayName = sName.length > maxNameLen ? sName.substring(0, maxNameLen - 2) + '...' : sName;
            ctx.fillStyle = "#cbd5e1";
            ctx.font = "11px sans-serif";
            ctx.fillText(displayName, xText, yPill + 16);

            ctx.fillStyle = "#fff";
            ctx.font = "bold 11px sans-serif";
            const lvlText = `${lvlB ? lvlB + ' ➔ ' : ''}Nv. ${lvlT}`;
            ctx.fillText(lvlText, xPill + 160, yPill + 16);

            if (diff > 0) {
                ctx.fillStyle = "#10b981";
                ctx.font = "bold 10px sans-serif";
                ctx.fillText(`+${diff}`, xPill + 232, yPill + 16);
            }
        }
    }

    // 3. ATRIBUTOS GERAIS
    drawRoundedRect(30, 395, 560, 435, 12, "rgba(0, 0, 0, 0.4)", "rgba(255, 255, 255, 0.1)");
    ctx.fillStyle = "#38bdf8";
    ctx.font = "bold 13px sans-serif";
    ctx.fillText("ATRIBUTOS FINAIS COMPARADOS", 45, 417);

    const statsBase = base.stats || {};
    const statsTarget = target.stats || {};
    const keys = listUniqueDictKeys(statsBase, statsTarget).slice(0, 10);

    let yStat = 432;
    if (keys.length === 0) {
        ctx.fillStyle = "#94a3b8";
        ctx.font = "italic 12px sans-serif";
        ctx.fillText("Sem atributos comparativos registrados", 60, yStat + 20);
    } else {
        keys.forEach(k => {
            const valB = statsBase[k] !== undefined ? String(statsBase[k]) : 'N/A';
            const valT = statsTarget[k] !== undefined ? String(statsTarget[k]) : 'N/A';

            drawRoundedRect(45, yStat, 530, 34, 8, "rgba(15, 23, 42, 0.8)", "rgba(255,255,255,0.05)");
            ctx.fillStyle = "#94a3b8";
            ctx.font = "11px sans-serif";
            ctx.fillText(k, 60, yStat + 21);

            ctx.fillStyle = "#fff";
            ctx.font = "bold 11px sans-serif";
            const valStr = `${valB !== 'N/A' && valB !== valT ? valB + ' ➔ ' : ''}${valT}`;
            ctx.fillText(valStr, 320, yStat + 21);

            const numB = parseFloat(valB.replace(/[^0-9.-]/g, ''));
            const numT = parseFloat(valT.replace(/[^0-9.-]/g, ''));
            if (!isNaN(numB) && !isNaN(numT) && numB !== numT) {
                const diffVal = (numT - numB).toFixed(1);
                const isPct = valT.includes('%');
                ctx.fillStyle = parseFloat(diffVal) > 0 ? "#10b981" : "#ef4444";
                ctx.font = "bold 11px sans-serif";
                ctx.fillText(`${parseFloat(diffVal) > 0 ? '+' : ''}${diffVal}${isPct ? '%' : ''}`, 490, yStat + 21);
            } else if (valB === valT && valT !== 'N/A') {
                ctx.fillStyle = "#64748b";
                ctx.font = "10px sans-serif";
                ctx.fillText("Mantido", 495, yStat + 21);
            }

            yStat += 38;
        });
    }

    // 4. COMPARATIVO DE ARTEFATOS (PAINEL DIREITO "FOI DESSE PRA ESSE" COM SUBSTATUS)
    drawRoundedRect(610, 150, 560, 680, 12, "rgba(0, 0, 0, 0.4)", "rgba(255, 255, 255, 0.1)");
    ctx.fillStyle = "#38bdf8";
    ctx.font = "bold 13px sans-serif";
    ctx.fillText(isEn ? "ARTIFACTS & RELICS (FROM ➔ TO)" : "ARTEFATOS & RELÍQUIAS (DE ➔ PARA)", 625, 175);

    const relicsBase = base.relics || [];
    const relicsTarget = target.relics || [];
    const pairs = buildRelicSlotPairs(relicsBase, relicsTarget).slice(0, 6);

    let yRelic = 192;
    for (let i = 0; i < pairs.length; i++) {
        const p = pairs[i];
        const rb = p.base || {};
        const rt = p.target || {};
        const isReplaced = rb.name && rt.name && (rb.name !== rt.name || rb.main !== rt.main);

        const subListB = parseSubstats(rb.sub);
        const subListT = parseSubstats(rt.sub);

        drawRoundedRect(625, yRelic, 530, 98, 10, isReplaced ? "rgba(236, 72, 153, 0.08)" : "rgba(15, 23, 42, 0.8)", isReplaced ? "rgba(236, 72, 153, 0.3)" : "rgba(255, 255, 255, 0.06)");

        ctx.fillStyle = isReplaced ? "#ec4899" : "#38bdf8";
        ctx.font = "bold 11px sans-serif";
        ctx.fillText(`${p.slot.toUpperCase()} ${isReplaced ? '• PEÇA TROCADA' : '• MANTIDA'}`, 638, yRelic + 16);

        const rBaseImg = await loadImage(rb.icon);
        const rTargetImg = await loadImage(rt.icon);

        if (isReplaced) {
            // EXIBE COMPARATIVO ANTERIOR (BASE) ➔ ATUAL (TARGET)
            if (rBaseImg) ctx.drawImage(rBaseImg, 638, yRelic + 22, 34, 34);
            ctx.fillStyle = "#94a3b8";
            ctx.font = "10px sans-serif";
            const nameB = (rb.name || "Vazio");
            ctx.fillText(nameB.length > 22 ? nameB.substring(0, 20) + '...' : nameB, 678, yRelic + 34);
            ctx.fillStyle = "#f59e0b";
            ctx.font = "bold 10px sans-serif";
            ctx.fillText(rb.main || "", 678, yRelic + 48);

            // Substats Base
            if (subListB.length > 0) {
                let subY = yRelic + 62;
                ctx.font = "9px sans-serif";
                const line1 = subListB.slice(0, 2);
                const line2 = subListB.slice(2, 4);

                if (line1.length > 0) {
                    let offX = 678;
                    line1.forEach(s => {
                        ctx.fillStyle = s.isCrit ? "#f59e0b" : "#94a3b8";
                        ctx.fillText(s.text, offX, subY);
                        offX += ctx.measureText(s.text).width + 8;
                    });
                }
                if (line2.length > 0) {
                    subY += 12;
                    let offX = 678;
                    line2.forEach(s => {
                        ctx.fillStyle = s.isCrit ? "#f59e0b" : "#94a3b8";
                        ctx.fillText(s.text, offX, subY);
                        offX += ctx.measureText(s.text).width + 8;
                    });
                }
            }

            // Seta Central de Troca
            ctx.fillStyle = "#ec4899";
            ctx.font = "bold 15px sans-serif";
            ctx.fillText("➔", 876, yRelic + 42);

            // Item Atual (Target)
            if (rTargetImg) ctx.drawImage(rTargetImg, 898, yRelic + 22, 34, 34);
            ctx.fillStyle = "#fff";
            ctx.font = "bold 10px sans-serif";
            const nameT = (rt.name || "Vazio");
            ctx.fillText(nameT.length > 22 ? nameT.substring(0, 20) + '...' : nameT, 938, yRelic + 34);
            ctx.fillStyle = "#10b981";
            ctx.font = "bold 10px sans-serif";
            ctx.fillText(rt.main || "", 938, yRelic + 48);

            // Substats Target
            if (subListT.length > 0) {
                let subY = yRelic + 62;
                ctx.font = "9px sans-serif";
                const line1 = subListT.slice(0, 2);
                const line2 = subListT.slice(2, 4);

                if (line1.length > 0) {
                    let offX = 938;
                    line1.forEach(s => {
                        ctx.fillStyle = s.isCrit ? "#f59e0b" : "#cbd5e1";
                        ctx.fillText(s.text, offX, subY);
                        offX += ctx.measureText(s.text).width + 8;
                    });
                }
                if (line2.length > 0) {
                    subY += 12;
                    let offX = 938;
                    line2.forEach(s => {
                        ctx.fillStyle = s.isCrit ? "#f59e0b" : "#cbd5e1";
                        ctx.fillText(s.text, offX, subY);
                        offX += ctx.measureText(s.text).width + 8;
                    });
                }
            }
        } else {
            // ARTEFATO MANTIDO (EXIBE DETALHADO DO ATUAL OU BASE)
            const itemObj = rt.name ? rt : rb;
            const rImg = rTargetImg || rBaseImg;
            const subList = subListT.length > 0 ? subListT : subListB;

            if (rImg) ctx.drawImage(rImg, 638, yRelic + 22, 38, 38);
            ctx.fillStyle = "#fff";
            ctx.font = "bold 11px sans-serif";
            ctx.fillText(itemObj.name || "Vazio", 684, yRelic + 34);
            ctx.fillStyle = "#10b981";
            ctx.font = "bold 10px sans-serif";
            ctx.fillText(itemObj.main || "", 684, yRelic + 48);

            // Substats Mantidos (Dispostos em 2 linhas horizontais organizadas)
            if (subList.length > 0) {
                ctx.font = "10px sans-serif";
                const line1 = subList.slice(0, 2);
                const line2 = subList.slice(2, 4);

                if (line1.length > 0) {
                    let offX = 684;
                    line1.forEach(s => {
                        ctx.fillStyle = s.isCrit ? "#f59e0b" : "#94a3b8";
                        ctx.fillText(s.text, offX, yRelic + 64);
                        offX += ctx.measureText(s.text).width + 16;
                    });
                }
                if (line2.length > 0) {
                    let offX = 684;
                    line2.forEach(s => {
                        ctx.fillStyle = s.isCrit ? "#f59e0b" : "#94a3b8";
                        ctx.fillText(s.text, offX, yRelic + 80);
                        offX += ctx.measureText(s.text).width + 16;
                    });
                }
            }
        }

        yRelic += 105;
    }

    // Rodapé Marca D'água
    ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
    ctx.font = "11px sans-serif";
    ctx.fillText("Gerado via HoYo Hub • Comparativo Automático de Snapshots de Evolução", 30, height - 12);

    return canvas;
}

function listUniqueSkillKeys(arrA, arrB) {
    const set = new Set();
    (arrA || []).forEach(x => { if (x && (x.name || x.skill_name)) set.add(x.name || x.skill_name); });
    (arrB || []).forEach(x => { if (x && (x.name || x.skill_name)) set.add(x.name || x.skill_name); });
    return Array.from(set);
}

function listUniqueDictKeys(dictA, dictB) {
    const set = new Set();
    Object.keys(dictA || {}).forEach(k => set.add(k));
    Object.keys(dictB || {}).forEach(k => set.add(k));
    return Array.from(set);
}

window.loadAccountHistory = async (gameId = "hsr") => {
    window.currentGameIdHistory = gameId;
    const container = document.getElementById("tab-history-body");
    if (!container) return;

    const btnSnapshot = document.getElementById("btn-create-snapshot-now");
    if (btnSnapshot && !btnSnapshot.dataset.bound) {
        btnSnapshot.dataset.bound = "true";
        btnSnapshot.addEventListener("click", async () => {
            const historyTabs = document.getElementById("history-game-tabs");
            const activeTabBtn = document.querySelector(".tab-history-game-btn.active");
            const targetGame = historyTabs?.value || (activeTabBtn && activeTabBtn.dataset.game) || window.currentGameIdHistory || gameId || "hsr";
            btnSnapshot.disabled = true;
            btnSnapshot.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${window.t ? window.t("history_btn_creating") : "Gerando Snapshot..."}`;
            try {
                const res = await fetch(`/api/history/${encodeURIComponent(targetGame)}/snapshot`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ refresh_from_hoyolab: true })
                });
                const resData = await res.json().catch(() => ({}));
                if (res.ok && resData.success) {
                    if (typeof btnSnapshot.done === "function") btnSnapshot.done();
                    showToast(window.t ? window.t("history_toast_created") : "Snapshot de evolução criado com sucesso!", "success");
                    window.loadAccountHistory(targetGame);
                } else {
                    showToast("Erro ao criar snapshot: " + (resData.detail || resData.message || "Erro desconhecido"));
                }
            } catch (e) {
                showToast("Erro de rede ao criar snapshot.");
            } finally {
                btnSnapshot.disabled = false;
                btnSnapshot.innerHTML = `<i class="fa-solid fa-camera-retro"></i> ${window.t ? window.t("history_btn_create") : "Criar Novo Snapshot Agora"}`;
            }
        });
    }

    container.innerHTML = `
        <div class="history-compare-card" style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(236, 72, 153, 0.2); border-radius: 14px; padding: 16px 20px; margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; align-items: center; gap: 12px; flex: 1;">
                    <div class="skeleton-line" style="width: 140px; height: 16px;"></div>
                    <div class="skeleton-box" style="width: 160px; height: 32px; border-radius: 6px;"></div>
                    <div class="skeleton-line" style="width: 20px; height: 16px;"></div>
                    <div class="skeleton-box" style="width: 160px; height: 32px; border-radius: 6px;"></div>
                </div>
                <div class="skeleton-box" style="width: 130px; height: 32px; border-radius: 8px;"></div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
            <div class="skeleton-line" style="width: 220px; height: 16px;"></div>
        </div>
        <div class="timeline-stepper" style="position: relative; padding-left: 24px; border-left: 3px solid rgba(236, 72, 153, 0.3); display: flex; flex-direction: column; gap: 28px; margin-left: 10px;">
            ${[1, 2].map(() => `
                <div class="timeline-item" style="position: relative;">
                    <div style="position: absolute; left: -33px; top: 18px; width: 16px; height: 16px; border-radius: 50%; background: rgba(56, 189, 248, 0.5); border: 3px solid #0f172a;"></div>
                    <div class="skeleton-timeline-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px; border-bottom: 1px solid rgba(255,255,255,0.07); padding-bottom: 16px; margin-bottom: 16px;">
                            <div style="width: 45%;">
                                <div class="skeleton-line" style="width: 120px; height: 16px; margin-bottom: 8px;"></div>
                                <div class="skeleton-line" style="width: 180px; height: 20px;"></div>
                            </div>
                            <div style="display: flex; gap: 12px; flex: 1; justify-content: flex-end;">
                                <div class="skeleton-box" style="width: 90px; height: 50px; border-radius: 10px;"></div>
                                <div class="skeleton-box" style="width: 90px; height: 50px; border-radius: 10px;"></div>
                                <div class="skeleton-box" style="width: 90px; height: 50px; border-radius: 10px;"></div>
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 240px), 1fr)); gap: 12px;">
                            <div class="skeleton-box" style="height: 60px; border-radius: 10px;"></div>
                            <div class="skeleton-box" style="height: 60px; border-radius: 10px;"></div>
                            <div class="skeleton-box" style="height: 60px; border-radius: 10px;"></div>
                        </div>
                    </div>
                </div>
            `).join("")}
        </div>
    `;

    try {
        const res = await fetch(`/api/history/${gameId}`);
        const data = await res.json();
        const rawHistory = data.history || [];

        if (!rawHistory.length) {
            container.innerHTML = `
                <div class="overview-card" style="padding: 40px; text-align: center; color: var(--text-secondary); border-left: 4px solid #ec4899;">
                    <i class="fa-solid fa-clock-rotate-left fa-3x" style="color: #ec4899; margin-bottom: 14px;"></i>
                    <h3 style="color: var(--text-primary); font-size: 18px; margin-bottom: 8px;">${window.t ? window.t("history_empty_title") : "Nenhum Snapshot de Evolução Registrado"}</h3>
                    <p style="font-size: 13px; color: var(--text-muted); max-width: 500px; margin: 0 auto 18px auto; line-height: 1.5;">
                        ${window.t ? window.t("history_empty_desc") : "A Linha do Tempo fotografa a progressão e builds da sua conta para comparar evolução com o passar das semanas. Crie seu primeiro snapshot agora!"}
                    </p>
                    <sakuga-button id="btn-empty-create-snapshot" class="sk-sm sk-accent-pink" onclick="document.getElementById('btn-create-snapshot-now')?.click()">
                        <i class="fa-solid fa-camera-retro"></i> ${window.t ? window.t("history_btn_create") : "Criar Primeiro Snapshot Agora"}
                    </sakuga-button>
                </div>
            `;
            return;
        }

        const totalSnapshots = Number(data.total_count || rawHistory.length);
        const startSnapNum = Math.max(1, totalSnapshots - rawHistory.length + 1);
        // Inverte para cronológico reverso
        const history = rawHistory.slice().reverse();
        window.historySnapshotsCache = history;

        // Renderiza Barra Superior de Comparativo Customizado
        let compareHeaderHtml = `
            <div class="overview-card history-compare-card" style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(236, 72, 153, 0.35); border-radius: 14px; padding: 16px 20px; margin-bottom: 24px; backdrop-filter: blur(10px);">
                <div class="history-compare-row" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
                    <div class="history-selects-group" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap; width: 100%;">
                        <span style="font-size: 14px; font-weight: 700; color: #ec4899; display: flex; align-items: center; gap: 6px; white-space: nowrap;">
                            <i class="fa-solid fa-sliders"></i> Seleção de Comparativos:
                        </span>
                        <div class="snap-select-item" style="display: flex; align-items: center; gap: 6px;">
                            <label style="font-size: 12px; color: var(--text-secondary); white-space: nowrap;">Base:</label>
                            <select id="select-snap-base" class="snap-select">
                                ${rawHistory.map((s, i) => `
                                    <option value="${s.id}" ${i === Math.max(0, rawHistory.length - 2) ? 'selected' : ''}>
                                        Snapshot #${startSnapNum + i} (${s.created_at})
                                    </option>
                                `).join('')}
                            </select>
                        </div>
                        <span style="color: var(--text-muted);" class="snap-arrow-icon">➔</span>
                        <div class="snap-select-item" style="display: flex; align-items: center; gap: 6px;">
                            <label style="font-size: 12px; color: var(--text-secondary); white-space: nowrap;">Comparado:</label>
                            <select id="select-snap-target" class="snap-select">
                                ${rawHistory.map((s, i) => `
                                    <option value="${s.id}" ${i === rawHistory.length - 1 ? 'selected' : ''}>
                                        Snapshot #${startSnapNum + i} (${s.created_at}) ${i === rawHistory.length - 1 ? ' (Mais Recente)' : ''}
                                    </option>
                                `).join('')}
                            </select>
                        </div>
                        <sakuga-button id="btn-run-snap-compare" class="history-compare-btn sk-sm sk-accent-pink">
                            <i class="fa-solid fa-code-compare"></i> Comparar Diffs
                        </sakuga-button>
                    </div>
                    <div id="snap-compare-status-badge" class="diff-badge-gain history-status-badge" style="font-size: 11px; padding: 4px 10px; white-space: nowrap;">
                        <i class="fa-solid fa-check"></i> Comparando Snapshots Selecionados
                    </div>
                </div>
            </div>
            <div id="custom-compare-results-container"></div>
        `;

        let timelineHtml = `
            <div style="margin-top: 10px; margin-bottom: 14px; font-size: 14px; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-clock-rotate-left" style="color: #38bdf8;"></i> Histórico Completo de Snapshots (${totalSnapshots})
            </div>
            <div class="timeline-stepper" style="position: relative; padding-left: 24px; border-left: 3px solid rgba(236, 72, 153, 0.3); display: flex; flex-direction: column; gap: 28px; margin-left: 10px;">
                ${history.map((item, idx) => {
                    const details = item.details || {};
                    const topBuilt = details.top_built_characters || [];
                    const allChars = details.all_characters || topBuilt;
                    const readiness = details.endgame_readiness_pct || 0.0;
                    const rawDiffs = item.char_diffs || [];
                    const onlyChanged = window.historyOnlyChanged || false;

                    const diffs = onlyChanged 
                        ? rawDiffs.filter(d => d.is_new || d.is_modified || (d.score_diff && d.score_diff !== 0) || (d.diffs && (d.diffs.score_diff !== 0 || d.diffs.level_diff > 0 || d.diffs.rank_changed)))
                        : rawDiffs;

                    const changedCharNames = new Set(rawDiffs.map(d => d.name));
                    const filteredChars = onlyChanged
                        ? allChars.filter(c => changedCharNames.has(c.name) || c.is_new || c.has_changes)
                        : allChars;

                    const isLatest = idx === 0;
                    const snapshotNum = totalSnapshots - idx;

                    return `
                        <div class="timeline-item" style="position: relative;">
                            <div class="timeline-bullet" style="position: absolute; left: -33px; top: 18px; width: 16px; height: 16px; border-radius: 50%; background: ${isLatest ? '#ec4899' : '#38bdf8'}; border: 3px solid #0f172a; box-shadow: 0 0 12px ${isLatest ? 'rgba(236, 72, 153, 0.8)' : 'rgba(56, 189, 248, 0.8)'};"></div>

                            <div class="overview-card timeline-card" style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.08); border-top: 3px solid ${isLatest ? '#ec4899' : 'rgba(56, 189, 248, 0.6)'}; border-radius: 14px; padding: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); backdrop-filter: blur(10px);">
                                
                                <div class="timeline-card-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px; border-bottom: 1px solid rgba(255,255,255,0.07); padding-bottom: 16px; margin-bottom: 16px;">
                                    <div>
                                        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                            <span style="font-size: 11px; font-weight: 700; background: ${isLatest ? 'linear-gradient(135deg, #ec4899, #8b5cf6)' : 'rgba(255,255,255,0.1)'}; color: #fff; padding: 3px 10px; border-radius: 12px;">
                                                Snapshot #${snapshotNum} ${isLatest ? ' (Mais Recente)' : ''}
                                            </span>
                                            <span style="font-size: 12px; color: var(--text-muted);"><i class="fa-regular fa-clock"></i> ${item.created_at}</span>
                                        </div>
                                        <h3 style="margin: 8px 0 0 0; color: var(--text-primary); font-size: 17px; font-weight: 700;">
                                            Progresso da Conta <span style="font-size: 13px; color: var(--text-secondary); font-weight: 400;">(UID: ${item.uid})</span>
                                        </h3>
                                    </div>

                                    <div class="timeline-stats-boxes" style="display: flex; gap: 14px; flex-wrap: wrap;">
                                        <div class="timeline-stat-box" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); padding: 8px 14px; border-radius: 10px; text-align: center; flex: 1; min-width: 90px;">
                                            <span style="display: block; font-size: 10px; color: var(--text-secondary); font-weight: 600; text-transform: uppercase;">Personagens</span>
                                            <strong style="font-size: 15px; color: #38bdf8;">${item.character_count}</strong>
                                            <span style="font-size: 10px; color: var(--text-muted); display: block;"> (${details.five_stars || 0}★ 5★ / ${details.four_stars || 0}★ 4★)</span>
                                            ${item.delta_chars > 0 ? `<span style="font-size: 10px; color: #10b981; font-weight: 700; display: block;">+${item.delta_chars} novos</span>` : ''}
                                        </div>
                                        <div class="timeline-stat-box" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); padding: 8px 14px; border-radius: 10px; text-align: center; flex: 1; min-width: 90px;">
                                            <span style="display: block; font-size: 10px; color: var(--text-secondary); font-weight: 600; text-transform: uppercase;">Média Build (RV)</span>
                                            <strong style="font-size: 15px; color: #10b981;">${item.average_build_score}%</strong>
                                            ${item.delta_avg_score > 0 ? `<span style="font-size: 10px; color: #10b981; font-weight: 700; display: block;">+${item.delta_avg_score}%</span>` : (item.delta_avg_score < 0 ? `<span style="font-size: 10px; color: #ef4444; font-weight: 700; display: block;">${item.delta_avg_score}%</span>` : '')}
                                        </div>
                                        <div class="timeline-stat-box" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); padding: 8px 14px; border-radius: 10px; text-align: center; flex: 1; min-width: 90px;">
                                            <span style="display: block; font-size: 10px; color: var(--text-secondary); font-weight: 600; text-transform: uppercase;">Prontidão Endgame</span>
                                            <strong style="font-size: 15px; color: #f59e0b;">${readiness}%</strong>
                                            <span style="font-size: 10px; color: var(--text-muted); display: block;">${details.endgame_ready_count || 0} prontos</span>
                                        </div>
                                    </div>
                                </div>

                                ${diffs.length > 0 ? `
                                    <div style="background: rgba(236, 72, 153, 0.05); border: 1px solid rgba(236, 72, 153, 0.2); border-radius: 12px; padding: 14px; margin-bottom: 16px;">
                                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;">
                                            <span style="font-size: 13px; font-weight: 700; color: #ec4899; display: flex; align-items: center; gap: 6px;">
                                                <i class="fa-solid fa-chart-line"></i> Alterações e Evoluções Detectadas (${diffs.length})
                                            </span>
                                            <span style="font-size: 11px; color: var(--text-muted);">Clique no card para expandir a build completa</span>
                                        </div>

                                        <div class="timeline-diff-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 240px), 1fr)); gap: 12px;">
                                            ${diffs.map((d, dIdx) => {
                                                const dJson = JSON.stringify(d).replace(/"/g, '&quot;');
                                                return `
                                                    <div onclick="window.openCharacterDiffModal(JSON.parse(this.dataset.cdiff))" data-cdiff="${dJson}" class="diff-card-clickable" style="background: rgba(15, 23, 42, 0.9); border: 1px solid ${d.is_new ? 'rgba(245, 158, 11, 0.5)' : 'rgba(255, 255, 255, 0.1)'}; border-radius: 10px; padding: 12px; display: flex; gap: 12px; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                                                        <div style="position: relative; flex-shrink: 0;">
                                                            <img src="${d.icon || '/assets/logo.png'}" width="46" height="46" loading="lazy" decoding="async" style="width: 46px; height: 46px; border-radius: 50%; object-fit: cover; border: 2px solid ${d.is_new ? '#f59e0b' : '#38bdf8'}; box-shadow: 0 0 10px ${d.is_new ? 'rgba(245, 158, 11, 0.4)' : 'rgba(56, 189, 248, 0.3)'};" onerror="this.src='/assets/logo.png'">
                                                            ${d.is_new ? `<span style="position: absolute; bottom: -4px; right: -4px; background: #f59e0b; color: #000; font-size: 9px; font-weight: 900; padding: 1px 5px; border-radius: 6px;">NEW</span>` : ''}
                                                        </div>

                                                        <div style="flex: 1; min-width: 0;">
                                                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                                                <strong style="display: block; font-size: 13px; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${d.name}</strong>
                                                            </div>

                                                            <div style="display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-secondary); margin-top: 2px;">
                                                                <span>Nv. ${d.level_curr || d.level_prev || '?'}</span>
                                                                <span>•</span>
                                                                <span style="color: #f59e0b; font-weight: 600;">${d.rank_curr || 'E0/C0'}</span>
                                                            </div>

                                                            <div style="margin-top: 4px; display: flex; align-items: center; gap: 6px;">
                                                                ${d.is_new ? `
                                                                    <span style="font-size: 10px; font-weight: 700; background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(16, 185, 129, 0.4);">
                                                                        Score: ${d.score_curr}% (${d.grade_curr})
                                                                    </span>
                                                                ` : `
                                                                    ${d.score_diff > 0 ? `
                                                                        <span style="font-size: 10px; font-weight: 700; background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(16, 185, 129, 0.4);">
                                                                            Score +${d.score_diff}% ➔ ${d.score_curr}%
                                                                        </span>
                                                                    ` : `
                                                                        <span style="font-size: 10px; font-weight: 600; color: var(--text-muted);">
                                                                            Score: ${d.score_curr}% (${d.grade_curr})
                                                                        </span>
                                                                    `}
                                                                `}
                                                            </div>
                                                        </div>
                                                    </div>
                                                `;
                                            }).join('')}
                                        </div>
                                    </div>
                                ` : (idx > 0 ? `<p style="font-size: 12px; color: var(--text-muted); font-style: italic; margin-bottom: 12px;"><i class="fa-solid fa-check-circle" style="color: #10b981;"></i> ${isEn ? "No attribute changes or new characters detected compared to previous snapshot." : "Nenhuma alteração de atributos ou novos personagens detectados em relação ao snapshot anterior."}</p>` : '')}

                                <details style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 10px 14px;">
                                    <summary style="font-size: 12px; font-weight: 600; color: #38bdf8; cursor: pointer; user-select: none; display: flex; align-items: center; gap: 6px;">
                                        <i class="fa-solid fa-users"></i> ${onlyChanged ? (isEn ? `View ${filteredChars.length} Changed Character(s)` : `Ver ${filteredChars.length} Personagem(ns) Alterado(s)`) : (isEn ? `View All ${allChars.length} Characters` : `Ver Todos os ${allChars.length} Personagens`)} ${isEn ? "from Snapshot #" : "do Snapshot #"}${snapshotNum}
                                    </summary>
                                    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 150px), 1fr)); gap: 10px; margin-top: 14px;">
                                        ${filteredChars.map(c => `
                                            <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 8px 10px; display: flex; align-items: center; gap: 10px;">
                                                <img src="${c.icon || '/assets/logo.png'}" width="34" height="34" loading="lazy" decoding="async" style="width: 34px; height: 34px; border-radius: 50%; object-fit: cover; border: 2px solid ${c.rarity >= 5 ? '#f59e0b' : '#a855f7'};" onerror="this.src='/assets/logo.png'">
                                                <div style="overflow: hidden; flex: 1; min-width: 0;">
                                                    <strong style="display: block; font-size: 12px; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${c.name}</strong>
                                                    <div style="display: flex; justify-content: space-between; font-size: 10px; color: var(--text-secondary); margin-top: 2px;">
                                                        <span>Nv. ${c.level} • ${c.rank_str || 'E0/C0'}</span>
                                                        <span style="color: #10b981; font-weight: 700;">${c.score || 0}% (${c.grade || 'D'})</span>
                                                    </div>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </details>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        container.innerHTML = compareHeaderHtml + timelineHtml;

        // Função interna para executar comparativo customizado entre quaisquer dois snapshots
        const runCustomCompare = async () => {
            const selBase = document.getElementById("select-snap-base");
            const selTarget = document.getElementById("select-snap-target");
            const resContainer = document.getElementById("custom-compare-results-container");

            if (!selBase || !selTarget || !resContainer) return;

            const idA = selBase.value;
            const idB = selTarget.value;

            if (idA === idB) {
                resContainer.innerHTML = `<div style="padding: 14px; border-radius: 10px; background: rgba(245,158,11,0.1); border: 1px solid #f59e0b; color: #f59e0b; font-size: 13px; margin-bottom: 20px;"><i class="fa-solid fa-triangle-exclamation"></i> Selecione dois snapshots diferentes para visualizar as diferenças.</div>`;
                return;
            }

            resContainer.innerHTML = `<div style="padding: 20px; text-align: center; color: var(--text-secondary);"><i class="fa-solid fa-spinner fa-spin"></i> Calculando diff minuciosa dos snapshots...</div>`;

            try {
                const cRes = await fetch(`/api/history/${gameId}/compare/${idA}/${idB}`);
                const cData = await cRes.json();
                const sumDiff = cData.summary_diff || {};
                const rawCDiffs = cData.char_diffs || [];
                const cDiffs = window.historyOnlyChanged
                    ? rawCDiffs.filter(d => d.is_new || d.is_modified || (d.diffs && (d.diffs.score_diff !== 0 || d.diffs.level_diff > 0 || d.diffs.rank_changed)))
                    : rawCDiffs;

                let resHtml = `
                    <div style="background: rgba(236, 72, 153, 0.08); border: 1px solid rgba(236, 72, 153, 0.3); border-radius: 14px; padding: 18px; margin-bottom: 24px;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 14px;">
                            <h3 style="margin: 0; font-size: 15px; color: #ec4899; display: flex; align-items: center; gap: 8px; word-break: break-word;">
                                <i class="fa-solid fa-code-compare"></i> Resultado da Comparação (Snapshot #${cData.snap_a.id} ➔ Snapshot #${cData.snap_b.id})
                            </h3>
                            <span style="font-size: 11px; color: var(--text-muted); display: block;">${cData.snap_a.created_at} ➔ ${cData.snap_b.created_at}</span>
                        </div>

                        <!-- KPIs Comparativos -->
                        <div class="diff-modal-kpi-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 130px), 1fr)); gap: 10px; margin-bottom: 16px;">
                            <div style="background: rgba(0,0,0,0.3); padding: 10px 6px; border-radius: 8px; text-align: center;">
                                <span style="font-size: 9px; color: var(--text-secondary); text-transform: uppercase; display: block;">Personagens</span>
                                <strong style="display: block; font-size: 13px; color: #38bdf8;">${cData.snap_a.character_count} ➔ ${cData.snap_b.character_count}</strong>
                                ${sumDiff.delta_chars > 0 ? `<span class="diff-badge-gain" style="font-size: 9px;">+${sumDiff.delta_chars} novos</span>` : ''}
                            </div>
                            <div style="background: rgba(0,0,0,0.3); padding: 10px 6px; border-radius: 8px; text-align: center;">
                                <span style="font-size: 9px; color: var(--text-secondary); text-transform: uppercase; display: block;">Score Médio (RV)</span>
                                <strong style="display: block; font-size: 13px; color: #10b981;">${cData.snap_a.average_build_score}% ➔ ${cData.snap_b.average_build_score}%</strong>
                                ${sumDiff.delta_avg_score > 0 ? `<span class="diff-badge-gain" style="font-size: 9px;">+${sumDiff.delta_avg_score}%</span>` : (sumDiff.delta_avg_score < 0 ? `<span class="diff-badge-loss" style="font-size: 9px;">${sumDiff.delta_avg_score}%</span>` : '')}
                            </div>
                            <div style="background: rgba(0,0,0,0.3); padding: 10px 6px; border-radius: 8px; text-align: center;">
                                <span style="font-size: 9px; color: var(--text-secondary); text-transform: uppercase; display: block;">Prontidão Endgame</span>
                                <strong style="display: block; font-size: 13px; color: #f59e0b;">${cData.snap_a.endgame_readiness_pct}% ➔ ${cData.snap_b.endgame_readiness_pct}%</strong>
                                ${sumDiff.delta_readiness > 0 ? `<span class="diff-badge-gain" style="font-size: 9px;">+${sumDiff.delta_readiness}%</span>` : ''}
                            </div>
                        </div>

                        <!-- Lista de Cards de Personagens para Abrir Modal -->
                        <div style="font-size: 13px; font-weight: 700; color: #fff; margin-bottom: 12px; display: flex; flex-direction: column; gap: 4px;">
                            <span><i class="fa-solid fa-users-gear"></i> Todos os Personagens no Período (${cDiffs.length})</span>
                            <span style="font-size: 11px; color: #ec4899; font-weight: 400;">★ Clique em qualquer card para expandir a build completa</span>
                        </div>
                        <div class="timeline-diff-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 240px), 1fr)); gap: 12px;">
                            ${cDiffs.map(d => {
                                const dJson = JSON.stringify(d).replace(/"/g, '&quot;');
                                const scoreD = d.diffs ? d.diffs.score_diff : 0;
                                const lvlD = d.diffs ? d.diffs.level_diff : 0;
                                const rankChg = d.diffs ? d.diffs.rank_changed : false;
                                return `
                                    <div onclick="window.openCharacterDiffModal(JSON.parse(this.dataset.cdiff))" data-cdiff="${dJson}" class="diff-card-clickable" style="background: rgba(15, 23, 42, 0.95); border: 1px solid ${d.is_new ? 'rgba(245, 158, 11, 0.6)' : (d.is_modified ? 'rgba(56, 189, 248, 0.4)' : 'rgba(255,255,255,0.06)')}; border-radius: 10px; padding: 12px; display: flex; gap: 12px; align-items: center;">
                                        <img src="${d.icon || '/assets/logo.png'}" width="44" height="44" loading="lazy" decoding="async" style="width: 44px; height: 44px; border-radius: 50%; object-fit: cover; border: 2px solid ${d.is_new ? '#f59e0b' : '#38bdf8'};" onerror="this.src='/assets/logo.png'">
                                        <div style="flex: 1; min-width: 0;">
                                            <strong style="display: block; font-size: 13px; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${d.name}</strong>
                                            <div style="display: flex; gap: 6px; font-size: 11px; color: var(--text-secondary); margin-top: 2px;">
                                                <span>Nv. ${(d.target || d.base || {}).level || '?'}</span>
                                                <span>•</span>
                                                <span style="color: #f59e0b;">${(d.target || d.base || {}).rank_str || 'E0/C0'}</span>
                                            </div>
                                            <div style="margin-top: 4px; display: flex; flex-wrap: wrap; gap: 4px;">
                                                ${d.is_new ? `<span class="diff-badge-gain">Novo!</span>` : ''}
                                                ${scoreD > 0 ? `<span class="diff-badge-gain">+${scoreD}% RV</span>` : ''}
                                                ${rankChg ? `<span class="diff-badge-gain">Constelação+</span>` : ''}
                                                ${!d.is_new && !scoreD && !rankChg ? `<span class="diff-badge-same">Sem alterações</span>` : ''}
                                            </div>
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                `;

                resContainer.innerHTML = resHtml;
            } catch (err) {
                console.error("Erro ao executar comparativo:", err);
                resContainer.innerHTML = `<div style="padding: 14px; color: #ef4444;">Erro ao comparar os snapshots selecionados.</div>`;
            }
        };

        // Vincula evento no botão de comparar
        const btnCompare = document.getElementById("btn-run-snap-compare");
        if (btnCompare) {
            btnCompare.addEventListener("click", runCustomCompare);
        }

        // Executa comparativo inicial com os selecionados por padrão
        runCustomCompare();

    } catch (err) {
        console.error("Erro ao carregar histórico:", err);
        container.innerHTML = `
            <div style="padding: 30px 20px; text-align: center; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; max-width: 460px; margin: 20px auto;">
                <i class="fa-solid fa-triangle-exclamation fa-2x" style="color: #ef4444; margin-bottom: 10px;"></i>
                <h4 style="color: #f87171; margin: 0 0 6px 0; font-size: 15px;">${isEn ? "Failed to Load Timeline" : "Falha ao carregar a linha do tempo"}</h4>
                <p style="color: var(--text-muted); font-size: 12px; margin: 0 0 14px 0;">${isEn ? "Could not retrieve account snapshots. Please try again." : "Não foi possível carregar os snapshots de evolução da conta."}</p>
                <sakuga-button class="sk-sm sk-accent-danger" onclick="window.loadAccountHistory && window.loadAccountHistory('${gameId}')">
                    <i class="fa-solid fa-arrow-rotate-right"></i> ${isEn ? "Try Again" : "Tentar de novo"}
                </sakuga-button>
            </div>
        `;
    }
};

window.loadPromoCodes = async (gameId = "hsr") => {
    const container = document.getElementById("tab-codes-body");
    if (!container) return;
    container.innerHTML = `
        <div style="margin-bottom: 24px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                <div class="skeleton-line" style="width: 220px; height: 16px;"></div>
            </div>
            <div style="display: flex; flex-direction: column; gap: 12px;">
                ${[1, 2, 3].map(() => `
                    <div class="skeleton-code-card">
                        <div>
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div class="skeleton-box" style="width: 140px; height: 28px; border-radius: 6px;"></div>
                                <div class="skeleton-box" style="width: 75px; height: 22px; border-radius: 6px;"></div>
                            </div>
                            <div class="skeleton-line" style="width: 200px; height: 12px; margin-top: 8px;"></div>
                            <div class="skeleton-line" style="width: 100px; height: 10px; margin-top: 4px;"></div>
                        </div>
                        <div class="skeleton-box" style="width: 110px; height: 34px; border-radius: 6px;"></div>
                    </div>
                `).join("")}
            </div>
        </div>
    `;

    try {
        const [resCodes, resHistory] = await Promise.all([
            fetch(`/api/codes/${gameId}`).then(r => r.json()).catch(() => ({ codes: [] })),
            fetch(`/api/codes/history/${gameId}`).then(r => r.json()).catch(() => ({ history: [] }))
        ]);

        const codes = resCodes.codes || [];
        const history = resHistory.history || [];
        const historyMap = {};
        history.forEach(h => {
            historyMap[h.code.toUpperCase()] = h;
        });

        if (!codes.length && !history.length) {
            container.innerHTML = `
                <div class="overview-card" style="padding: 40px 20px; text-align: center; color: var(--text-secondary); max-width: 500px; margin: 20px auto;">
                    <i class="fa-solid fa-gift fa-3x" style="color: #f59e0b; margin-bottom: 14px;"></i>
                    <h3 style="color: var(--text-primary); font-size: 17px; margin-bottom: 8px;">${window.t ? window.t("codes_empty_title") : "Nenhum Código Ativo no Momento"}</h3>
                    <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5; margin-bottom: 18px;">
                        ${window.t ? window.t("codes_empty_desc") : `A Central de Códigos monitora cupons promocionais oficiais de Gemas, Jades Estelares e Polycromes para resgate direto. Não foram encontrados novos códigos ativos para ${gameId.toUpperCase()}.`}
                    </p>
                    <sakuga-button class="sk-sm sk-accent-amber" onclick="window.loadPromoCodes && window.loadPromoCodes('${gameId}')">
                        <i class="fa-solid fa-arrow-rotate-right"></i> ${isEn ? "Check for New Codes" : "Verificar Novos Códigos"}
                    </sakuga-button>
                </div>
            `;
            return;
        }

        let html = `
            <!-- CÓDIGOS ATIVOS -->
            <div style="margin-bottom: 24px;">
                <h4 style="color: #f59e0b; margin-top: 0; margin-bottom: 12px; font-size: 14px; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-fire"></i> ${window.t ? window.t("codes_available_title") : "Códigos Promocionais Disponíveis"} (${codes.length})
                </h4>
                <div style="display: flex; flex-direction: column; gap: 12px;">
                    ${codes.map(c => {
                        const hEntry = historyMap[c.code.toUpperCase()];
                        const isClaimed = hEntry && (hEntry.status === "claimed" || hEntry.status === "success");
                        const isInvalid = hEntry && hEntry.status === "invalid";

                        let badgeHtml = "";
                        if (isClaimed) {
                            badgeHtml = `<span style="font-size: 11px; background: rgba(16, 185, 129, 0.15); color: #34d399; padding: 3px 8px; border-radius: 6px; font-weight: 700; border: 1px solid rgba(16, 185, 129, 0.3);"><i class="fa-solid fa-check"></i> ${window.t ? window.t("codes_status_claimed") : "Resgatado"}</span>`;
                        } else if (isInvalid) {
                            badgeHtml = `<span style="font-size: 11px; background: rgba(239, 68, 68, 0.15); color: #f87171; padding: 3px 8px; border-radius: 6px; font-weight: 700; border: 1px solid rgba(239, 68, 68, 0.3);"><i class="fa-solid fa-xmark"></i> ${window.t ? window.t("codes_status_expired") : "Expirado"}</span>`;
                        }

                        return `
                            <div style="background: rgba(0,0,0,0.25); border: 1px solid var(--border-color); border-radius: 10px; padding: 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                                <div>
                                    <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                                        <code style="font-size: 16px; font-weight: 700; color: #f59e0b; background: rgba(245, 158, 11, 0.1); padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(245, 158, 11, 0.3);">${c.code}</code>
                                        ${badgeHtml}
                                    </div>
                                    <span style="display: block; font-size: 12px; color: var(--text-secondary); margin-top: 6px;"> ${window.t ? window.t("codes_rewards_label") : "Recompensas:"} ${c.rewards}</span>
                                    <span style="display: block; font-size: 10px; color: #10b981; margin-top: 2px;">• ${c.status}</span>
                                </div>
                                <sakuga-button variant="${isClaimed ? 'secondary' : 'primary'}" class="btn-redeem-single sk-xs ${isClaimed ? '' : 'sk-accent-amber'}" data-game="${gameId}" data-code="${c.code}">
                                    <i class="fa-solid fa-gift"></i> ${isClaimed ? (window.t ? window.t('codes_btn_redeem_again') : 'Resgatar Novamente') : (window.t ? window.t('codes_btn_redeem') : 'Resgatar Este')}
                                </sakuga-button>
                            </div>
                        `;
                    }).join('')}
                </div>
                <div id="codes-redeem-status" style="margin-top: 16px; font-size: 12px;"></div>
            </div>

            <!-- HISTÓRICO DE RESGATES AUTO-REDEEM -->
            ${history.length > 0 ? `
                <details style="background: rgba(0,0,0,0.2); border: 1px solid var(--border-color); border-radius: 10px; padding: 14px; margin-top: 20px;">
                    <summary style="font-size: 13px; font-weight: 700; color: #38bdf8; cursor: pointer; display: flex; align-items: center; gap: 8px;">
                        <i class="fa-solid fa-clock-rotate-left"></i> ${window.t ? window.t("codes_history_title") : "Histórico de Resgates Registrados"} (${history.length})
                    </summary>
                    <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 12px;">
                        ${history.map(h => {
                            const isOk = h.status === 'success' || h.status === 'claimed';
                            return `
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: rgba(255,255,255,0.02); border-radius: 6px; border-left: 3px solid ${isOk ? '#10b981' : '#ef4444'}; font-size: 12px; flex-wrap: wrap; gap: 6px;">
                                    <div style="display: flex; align-items: center; gap: 8px;">
                                        <strong style="color: #fff; font-family: monospace;">${h.code}</strong>
                                        <span style="color: var(--text-muted); font-size: 11px;">(UID: ${h.uid})</span>
                                    </div>
                                    <div style="display: flex; align-items: center; gap: 10px;">
                                        <span style="color: ${isOk ? '#34d399' : '#f87171'}; font-size: 11px;">${h.message}</span>
                                        <span style="color: var(--text-muted); font-size: 10px;">${h.redeemed_at.replace('T', ' ').substring(0, 19)}</span>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </details>
            ` : ''}
        `;
        container.innerHTML = html;

        document.querySelectorAll(".btn-redeem-single").forEach(btn => {
            btn.addEventListener("click", async () => {
                const code = btn.getAttribute("data-code");
                const game = btn.getAttribute("data-game");
                const origBtnHtml = btn.innerHTML;
                btn.disabled = true;
                btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${window.isEn ? "Redeeming..." : "Resgatando..."}`;
                try {
                    const r = await fetch("/api/codes/redeem", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ game_id: game, code: code })
                    });
                    const resData = await r.json();
                    const statusBox = document.getElementById("codes-redeem-status");
                    if (resData.results && resData.results.length) {
                        const item = resData.results[0];
                        if (r.ok && typeof btn.done === "function") btn.done();
                        statusBox.innerHTML = `<div style="padding: 10px; border-radius: 6px; background: rgba(16,185,129,0.1); border: 1px solid #10b981; color: #4ade80;">${item.message}</div>`;
                        // Recarrega lista para atualizar badges
                        setTimeout(() => window.loadPromoCodes(game), 1500);
                    }
                } catch (e) {
                    showToast(window.isEn ? "Error redeeming code." : "Erro ao resgatar código.");
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = origBtnHtml;
                }
            });
        });

    } catch (err) {
        console.error("Erro ao carregar códigos:", err);
        container.innerHTML = `
            <div style="padding: 30px 20px; text-align: center; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; max-width: 460px; margin: 20px auto;">
                <i class="fa-solid fa-circle-exclamation fa-2x" style="color: #ef4444; margin-bottom: 10px;"></i>
                <h4 style="color: #f87171; margin: 0 0 6px 0; font-size: 15px;">${isEn ? "Failed to Load Promo Codes" : "Falha ao carregar códigos promocionais"}</h4>
                <p style="color: var(--text-muted); font-size: 12px; margin: 0 0 14px 0;">${isEn ? "Could not connect to server to fetch promo codes." : "Não foi possível conectar ao servidor para buscar os códigos promocionais ativos."}</p>
                <sakuga-button class="sk-sm sk-accent-danger" onclick="window.loadPromoCodes && window.loadPromoCodes('${gameId}')">
                    <i class="fa-solid fa-arrow-rotate-right"></i> ${isEn ? "Try Again" : "Tentar de novo"}
                </sakuga-button>
            </div>
        `;
    }
};

window.loadAppConfiguration = async () => {
    try {
        const res = await fetch("/api/config");
        const data = await res.json();

        const cookiesInput = document.getElementById("cfg-hoyolab-cookies");
        if (cookiesInput && data.cookies_raw) {
            cookiesInput.value = data.cookies_raw;
        }

        const cbEnabled = document.getElementById("cfg-auto-sync-enabled");
        if (cbEnabled) {
            cbEnabled.checked = data.auto_sync_enabled !== false;
        }

        const inputTime = document.getElementById("cfg-auto-sync-time");
        if (inputTime) {
            inputTime.value = data.auto_sync_time || "04:00";
        }

        const cbRoster = document.getElementById("cfg-auto-sync-roster");
        if (cbRoster) {
            cbRoster.checked = data.auto_sync_roster !== false;
        }

        const cbGuides = document.getElementById("cfg-auto-sync-guides");
        if (cbGuides) {
            cbGuides.checked = data.auto_sync_guides !== false;
        }

        const statusEl = document.getElementById("cfg-auto-sync-status");
        if (statusEl) {
            const lastDate = data.last_auto_sync_date;
            statusEl.innerHTML = `<i class="fa-solid fa-circle-info" style="color: #38bdf8;"></i> Agendado diariamente para o horário <strong>${data.auto_sync_time || "04:00"}</strong>. ${lastDate ? `Última atualização executada em: <strong>${lastDate}</strong>.` : 'Ainda não executado hoje.'}`;
        }

        // Carregamento das Notificações Proativas
        const notifEnabled = document.getElementById("cfg-notif-enabled");
        if (notifEnabled) notifEnabled.checked = !!data.notifications_enabled;

        const discordUrl = document.getElementById("cfg-notif-discord-url");
        if (discordUrl && data.discord_webhook_url) discordUrl.value = data.discord_webhook_url;

        const tgToken = document.getElementById("cfg-notif-telegram-token");
        if (tgToken && data.telegram_bot_token) tgToken.value = data.telegram_bot_token;

        const tgChat = document.getElementById("cfg-notif-telegram-chat-id");
        if (tgChat && data.telegram_chat_id) tgChat.value = data.telegram_chat_id;

        const notifCheckin = document.getElementById("cfg-notif-checkin");
        if (notifCheckin) notifCheckin.checked = data.notify_on_checkin !== false;

        const notifEnergy = document.getElementById("cfg-notif-energy");
        if (notifEnergy) notifEnergy.checked = data.notify_on_energy_cap !== false;

        const notifThreshold = document.getElementById("cfg-notif-energy-threshold");
        if (notifThreshold && data.energy_cap_threshold_pct) notifThreshold.value = String(data.energy_cap_threshold_pct);

        const notifEndgame = document.getElementById("cfg-notif-endgame");
        if (notifEndgame) notifEndgame.checked = data.notify_on_endgame !== false;

        const notifCodes = document.getElementById("cfg-notif-codes");
        if (notifCodes) notifCodes.checked = data.notify_on_codes !== false;

        const notifQuietHours = document.getElementById("cfg-notif-quiet-hours-enabled");
        if (notifQuietHours) notifQuietHours.checked = !!data.quiet_hours_enabled;

        const notifQuietStart = document.getElementById("cfg-notif-quiet-hours-start");
        if (notifQuietStart && data.quiet_hours_start) notifQuietStart.value = data.quiet_hours_start;

        const notifQuietEnd = document.getElementById("cfg-notif-quiet-hours-end");
        if (notifQuietEnd && data.quiet_hours_end) notifQuietEnd.value = data.quiet_hours_end;

        const notifWinToast = document.getElementById("cfg-notif-windows-toast");
        if (notifWinToast) notifWinToast.checked = data.notify_windows_toast !== false;

        if (typeof window.updateWebNotificationBadge === "function") {
            window.updateWebNotificationBadge();
        }

    } catch (err) {
        console.error("Erro ao carregar configurações:", err);
    }
};

window.saveAppConfiguration = async () => {
        const cookiesRaw = document.getElementById("cfg-hoyolab-cookies")?.value || "";
    const autoSyncEnabled = document.getElementById("cfg-auto-sync-enabled")?.checked ?? true;
    const autoSyncTime = document.getElementById("cfg-auto-sync-time")?.value || "04:00";
    const autoSyncRoster = document.getElementById("cfg-auto-sync-roster")?.checked ?? true;
    const autoSyncGuides = document.getElementById("cfg-auto-sync-guides")?.checked ?? true;

    const notifEnabled = document.getElementById("cfg-notif-enabled")?.checked ?? false;
    const discordUrl = document.getElementById("cfg-notif-discord-url")?.value || "";
    const tgToken = document.getElementById("cfg-notif-telegram-token")?.value || "";
    const tgChat = document.getElementById("cfg-notif-telegram-chat-id")?.value || "";
    const notifCheckin = document.getElementById("cfg-notif-checkin")?.checked ?? true;
    const notifEnergy = document.getElementById("cfg-notif-energy")?.checked ?? true;
    const energyThreshold = parseInt(document.getElementById("cfg-notif-energy-threshold")?.value || "90", 10);
    const notifEndgame = document.getElementById("cfg-notif-endgame")?.checked ?? true;
    const notifCodes = document.getElementById("cfg-notif-codes")?.checked ?? true;
    const quietHoursEnabled = document.getElementById("cfg-notif-quiet-hours-enabled")?.checked ?? false;
    const quietHoursStart = document.getElementById("cfg-notif-quiet-hours-start")?.value || "23:00";
    const quietHoursEnd = document.getElementById("cfg-notif-quiet-hours-end")?.value || "07:00";
    const notifyWinToast = document.getElementById("cfg-notif-windows-toast")?.checked ?? true;

    try {
        const res = await fetch("/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                                cookies_raw: cookiesRaw,
                auto_sync_enabled: autoSyncEnabled,
                auto_sync_time: autoSyncTime,
                auto_sync_roster: autoSyncRoster,
                auto_sync_guides: autoSyncGuides,
                notifications_enabled: notifEnabled,
                discord_webhook_url: discordUrl,
                telegram_bot_token: tgToken,
                telegram_chat_id: tgChat,
                notify_on_checkin: notifCheckin,
                notify_on_energy_cap: notifEnergy,
                energy_cap_threshold_pct: energyThreshold,
                notify_on_endgame: notifEndgame,
                notify_on_codes: notifCodes,
                quiet_hours_enabled: quietHoursEnabled,
                quiet_hours_start: quietHoursStart,
                quiet_hours_end: quietHoursEnd,
                notify_windows_toast: notifyWinToast
            })
        });
        const data = await res.json();
        showToast("Configurações atualizadas!", "success");
    } catch (e) {

        showToast(isEn ? "Error saving settings." : "Erro ao salvar configurações.");
    }
};


// ==========================================================================
// SANDBOX: SIMULADOR DE TROCA DE RELÍQUIAS / "E SE EU TROCASSE A PEÇA?" (ETAPA 7)
// ==========================================================================

let sandboxCurrentMode = "inventory"; // "inventory" | "custom"
let sandboxInventoryPool = [];

window.openRelicSandboxModal = async function() {
    const modal = document.getElementById("modal-relic-sandbox");
    if (!modal) return;

    // Obtém o personagem inspecionado ou fallback
    const char = window.currentInspectorChar || activeInspectChar;
    const gameId = activeInspectGame || window.currentInspectorGame || "hsr";

    if (!char) {
        if (typeof showToast === "function") {

    showToast(isEn ? "Select a character in the gallery to open the Swap Sandbox." : "Selecione um personagem na galeria para abrir o Sandbox de Troca.", "warning");
        }
        return;
    }

    const subtitleEl = document.getElementById("sandbox-char-subtitle");
    if (subtitleEl) {
        subtitleEl.innerHTML = isEn ? `Simulating for <strong>${char.name}</strong> (${gameId.toUpperCase()} • Lv. ${char.level || 80}) — Test relic swaps without spending in-game resources.` : `Simulando para <strong>${char.name}</strong> (${gameId.toUpperCase()} • Nv. ${char.level || 80}) — Teste substituições de relíquias sem gastar recursos in-game.`;
    }

    // Popula o seletor de Slots
    const slotSelect = document.getElementById("sandbox-slot-select");
    if (slotSelect) {
        slotSelect.innerHTML = "";
        const relics = char.relics || [];
        if (relics.length > 0) {
            relics.forEach((r, idx) => {
                const opt = document.createElement("option");
                opt.value = r.slot || `Slot ${idx + 1}`;
                opt.textContent = `${r.slot || 'Slot'}: ${r.name || 'Peça'} (${r.main || r.main_stat || 'Main Stat'})`;
                slotSelect.appendChild(opt);
            });
        } else {
            // Fallbacks padrão de slots por jogo
            const isEn = Boolean(window.isEn || (window.getCurrentLanguage && window.getCurrentLanguage() === 'en') || window.currentLang === 'en');
            const defaultSlots = gameId === "genshin" 
                ? (isEn ? ["Flower", "Plume", "Sands", "Goblet", "Circlet"] : ["Flor", "Pena", "Areia", "Cálice", "Tiara"])
                : (gameId === "zzz" 
                    ? (isEn ? ["Disc 1", "Disc 2", "Disc 3", "Disc 4", "Disc 5", "Disc 6"] : ["Disco 1", "Disco 2", "Disco 3", "Disco 4", "Disco 5", "Disco 6"])
                    : (isEn ? ["Head", "Hands", "Body", "Feet", "Planar Sphere", "Link Rope"] : ["Cabeça", "Mãos", "Corpo", "Pés", "Esfera", "Corda"]));
            defaultSlots.forEach(s => {
                const opt = document.createElement("option");
                opt.value = s;
                opt.textContent = s;
                slotSelect.appendChild(opt);
            });
        }
    }

    // Carrega peças do inventário para o jogo em questão
    sandboxInventoryPool = [];
    try {
        const roster = (globalRoster && globalRoster[gameId]) || [];
        roster.forEach(c => {
            (c.relics || []).forEach(r => {
                sandboxInventoryPool.push({
                    character_name: c.name,
                    slot: r.slot,
                    name: r.name,
                    main_stat: r.main || r.main_stat || "",
                    sub_stats: r.sub || r.sub_stats || "",
                    icon: r.icon || ""
                });
            });
        });
    } catch (e) {
        console.warn("Aviso ao carregar inventário para o Sandbox:", e);
    }

    window.setSandboxCandidateMode("inventory");
    window.onSandboxSlotChanged();

    modal.style.display = "flex";
};

window.closeRelicSandboxModal = function() {
    const modal = document.getElementById("modal-relic-sandbox");
    if (modal) modal.style.display = "none";
};

window.setSandboxCandidateMode = function(mode) {
    sandboxCurrentMode = mode;
    const invBtn = document.getElementById("sandbox-mode-btn-inv");
    const customBtn = document.getElementById("sandbox-mode-btn-custom");
    const invBox = document.getElementById("sandbox-candidate-inv-box");
    const customBox = document.getElementById("sandbox-candidate-custom-box");

    if (mode === "inventory") {
        if (invBtn) {
            invBtn.style.border = "1px solid #38bdf8";
            invBtn.style.background = "rgba(56, 189, 248, 0.2)";
            invBtn.style.color = "#38bdf8";
        }
        if (customBtn) {
            customBtn.style.border = "1px solid rgba(255,255,255,0.15)";
            customBtn.style.background = "transparent";
            customBtn.style.color = "#94a3b8";
        }
        if (invBox) invBox.style.display = "block";
        if (customBox) customBox.style.display = "none";
    } else {
        if (customBtn) {
            customBtn.style.border = "1px solid #a855f7";
            customBtn.style.background = "rgba(168, 85, 247, 0.2)";
            customBtn.style.color = "#a855f7";
        }
        if (invBtn) {
            invBtn.style.border = "1px solid rgba(255,255,255,0.15)";
            invBtn.style.background = "transparent";
            invBtn.style.color = "#94a3b8";
        }
        if (invBox) invBox.style.display = "none";
        if (customBox) customBox.style.display = "block";
    }
};

window.onSandboxSlotChanged = function() {
    const char = window.currentInspectorChar || activeInspectChar;
    const slotSelect = document.getElementById("sandbox-slot-select");
    const currentBox = document.getElementById("sandbox-current-piece-box");
    if (!slotSelect || !char || !currentBox) return;

    const selectedSlot = slotSelect.value;
    const currentRelic = (char.relics || []).find(r => 
        (r.slot || "").toLowerCase().includes(selectedSlot.toLowerCase()) || 
        selectedSlot.toLowerCase().includes((r.slot || "").toLowerCase())
    );

    if (currentRelic) {
        currentBox.innerHTML = `
            <div style="font-weight: 700; color: #fff; font-size: 13px;">${currentRelic.name || 'Peça Atual'}</div>
            <div style="color: #fbbf24; font-size: 11px; margin-top: 2px;">Main: <strong>${currentRelic.main || currentRelic.main_stat || 'N/A'}</strong></div>
            <div style="color: var(--text-muted); font-size: 11px; margin-top: 2px;">${isEn ? "Substats:" : "Substatus:"} ${currentRelic.sub || currentRelic.sub_stats || (isEn ? "None" : "Nenhum")}</div>
        `;
    } else {
        currentBox.innerHTML = `<span style="color: #64748b; font-style: italic;">${isEn ? "No relic currently equipped in this slot." : "Nenhuma relíquia equipada neste slot atualmente."}</span>`;
    }

    // Filtra o select de inventário para o slot selecionado
    const invSelect = document.getElementById("sandbox-inventory-select");
    if (invSelect) {
        invSelect.innerHTML = "";
        const matchingPieces = sandboxInventoryPool.filter(p => 
            (p.slot || "").toLowerCase().includes(selectedSlot.toLowerCase()) ||
            selectedSlot.toLowerCase().includes((p.slot || "").toLowerCase())
        );

        if (matchingPieces.length === 0) {
            invSelect.innerHTML = `<option value="">${isEn ? `No other piece found for ${selectedSlot}` : `Nenhuma outra peça encontrada para ${selectedSlot}`}</option>`;
        } else {
            matchingPieces.forEach((p, idx) => {
                const opt = document.createElement("option");
                opt.value = idx;
                opt.textContent = `[${p.character_name}] ${p.name || 'Peça'} • ${p.main_stat} (${p.sub_stats})`;
                invSelect.appendChild(opt);
            });
        }
    }
};

window.onSandboxInventoryPieceSelected = function() {
    // Pronto para simular
};

window.executeRelicSwapSimulation = async function() {
    const char = window.currentInspectorChar || activeInspectChar;
    const gameId = activeInspectGame || window.currentInspectorGame || "hsr";
    const slotSelect = document.getElementById("sandbox-slot-select");

    if (!char || !slotSelect) {
        if (typeof showToast === "function") {

        showToast(isEn ? "Insufficient character data for simulation." : "Dados do personagem insuficientes para simulação.", "error");
        }
        return;
    }

    const targetSlot = slotSelect.value;
    let replacementPiece = null;

    if (sandboxCurrentMode === "inventory") {
        const invSelect = document.getElementById("sandbox-inventory-select");
        const idx = invSelect ? parseInt(invSelect.value) : -1;
        const matchingPieces = sandboxInventoryPool.filter(p => 
            (p.slot || "").toLowerCase().includes(targetSlot.toLowerCase()) ||
            targetSlot.toLowerCase().includes((p.slot || "").toLowerCase())
        );

        if (isNaN(idx) || !matchingPieces[idx]) {
            if (typeof showToast === "function") {
                showToast("Selecione uma peça válida do inventário ou use o modo customizado.", "warning");
            }
            return;
        }

        const picked = matchingPieces[idx];
        replacementPiece = {
            slot: targetSlot,
            name: picked.name || "Peça do Inventário",
            main_stat: picked.main_stat,
            sub_stats: picked.sub_stats,
            icon: picked.icon || ""
        };
    } else {
        const mainInput = document.getElementById("sandbox-custom-main");
        const sub1 = document.getElementById("sandbox-custom-sub1");
        const sub2 = document.getElementById("sandbox-custom-sub2");
        const sub3 = document.getElementById("sandbox-custom-sub3");
        const sub4 = document.getElementById("sandbox-custom-sub4");

        const mainVal = (mainInput ? mainInput.value : "").trim();
        if (!mainVal) {
            if (typeof showToast === "function") {
                showToast("Preencha o Main Stat da peça teórica customizada (ex: VEL (25) ou Taxa CRIT (32.4%)).", "warning");
            }
            return;
        }

        const subs = [
            sub1 ? sub1.value.trim() : "",
            sub2 ? sub2.value.trim() : "",
            sub3 ? sub3.value.trim() : "",
            sub4 ? sub4.value.trim() : ""
        ].filter(Boolean).join(", ");

        replacementPiece = {
            slot: targetSlot,
            name: "Peça Teórica Customizada",
            main_stat: mainVal,
            sub_stats: subs
        };
    }

    const btnSim = document.getElementById("btn-run-sandbox-simulation");
    const origHtml = btnSim ? btnSim.innerHTML : "";
    if (btnSim) {
        btnSim.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Simulando...`;
        btnSim.disabled = true;
    }

    try {
        const payload = {
            game_id: gameId,
            char_name: char.name,
            target_slot: targetSlot,
            replacement_relic: replacementPiece,
            current_relics: (char.relics || []).map(r => ({
                slot: r.slot || "",
                name: r.name || "Relíquia",
                main_stat: r.main || r.main_stat || "",
                sub_stats: r.sub || r.sub_stats || "",
                icon: r.icon || ""
            })),
            current_stats: char.stats || {}
        };

        const res = await fetch("/api/relics/simulate-swap", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Erro ao processar simulação");
        }

        const data = await res.json();

        // 1. Renderiza Notas da Peça e da Build
        const oldPieceGradeEl = document.getElementById("sandbox-old-piece-grade");
        const newPieceGradeEl = document.getElementById("sandbox-new-piece-grade");
        const pieceScoreLbl = document.getElementById("sandbox-piece-score-lbl");

        if (oldPieceGradeEl) oldPieceGradeEl.textContent = data.old_piece_grade;
        if (newPieceGradeEl) newPieceGradeEl.textContent = data.new_piece_grade;
        if (pieceScoreLbl) pieceScoreLbl.textContent = `Score: ${data.old_piece_score}% ➔ ${data.new_piece_score}%`;

        const oldBuildGradeEl = document.getElementById("sandbox-old-build-grade");
        const newBuildGradeEl = document.getElementById("sandbox-new-build-grade");
        const buildScoreLbl = document.getElementById("sandbox-build-score-lbl");

        if (oldBuildGradeEl) oldBuildGradeEl.textContent = data.old_build_grade;
        if (newBuildGradeEl) newBuildGradeEl.textContent = data.new_build_grade;
        if (buildScoreLbl) buildScoreLbl.textContent = `Média: ${data.old_build_score}% ➔ ${data.new_build_score}%`;

        // 2. Badge de Delta
        const deltaBadge = document.getElementById("sandbox-delta-badge");
        if (deltaBadge) {
            deltaBadge.style.display = "inline-block";
            const diff = data.score_diff;
            if (diff > 0) {
                deltaBadge.style.background = "rgba(52, 211, 153, 0.2)";
                deltaBadge.style.color = "#34d399";
                deltaBadge.style.border = "1px solid rgba(52, 211, 153, 0.4)";
                deltaBadge.innerHTML = `<i class="fa-solid fa-arrow-trend-up"></i> +${diff}% Upgrade`;
            } else if (diff < 0) {
                deltaBadge.style.background = "rgba(239, 68, 68, 0.2)";
                deltaBadge.style.color = "#f87171";
                deltaBadge.style.border = "1px solid rgba(239, 68, 68, 0.4)";
                deltaBadge.innerHTML = `<i class="fa-solid fa-arrow-trend-down"></i> ${diff}% Downgrade`;
            } else {
                deltaBadge.style.background = "rgba(148, 163, 184, 0.2)";
                deltaBadge.style.color = "#94a3b8";
                deltaBadge.style.border = "1px solid rgba(148, 163, 184, 0.4)";
                deltaBadge.innerHTML = `Neutro (0%)`;
            }
        }

        // 3. Deltas de Atributos
        const statContainer = document.getElementById("sandbox-stat-diffs-container");
        if (statContainer) {
            if (!data.stat_diffs || data.stat_diffs.length === 0) {
                statContainer.innerHTML = `<span style="font-size: 11px; color: var(--text-muted);">Sem variação numérica nos atributos mapeados.</span>`;
            } else {
                statContainer.innerHTML = data.stat_diffs.map(d => {
                    const isPositive = d.diff > 0;
                    const isZero = d.diff === 0;
                    const color = isZero ? "#94a3b8" : (isPositive ? "#34d399" : "#f87171");
                    const bg = isZero ? "rgba(255,255,255,0.05)" : (isPositive ? "rgba(52, 211, 153, 0.15)" : "rgba(239, 68, 68, 0.15)");
                    return `
                        <div style="background: ${bg}; border: 1px solid ${color}40; padding: 3px 8px; border-radius: 6px; font-size: 11px; color: #fff; display: inline-flex; align-items: center; gap: 4px;">
                            <span>${d.stat_name}:</span>
                            <strong style="color: ${color};">${d.formatted_diff}</strong>
                        </div>
                    `;
                }).join("");
            }
        }

        // 4. Breakpoints & Speed Tuning
        const bpContainer = document.getElementById("sandbox-breakpoints-container");
        if (bpContainer) {
            if (!data.breakpoint_feedback || data.breakpoint_feedback.length === 0) {

    bpContainer.innerHTML = `<span style="color: var(--text-muted);">${isEn ? "No breakpoints affected." : "Nenhum breakpoint afetado."}</span>`;
            } else {
                bpContainer.innerHTML = data.breakpoint_feedback.map(fb => {
                    const isSuccess = fb.startsWith("✓") || fb.startsWith("⚡");
                    const iconColor = isSuccess ? "#34d399" : "#fbbf24";
                    return `<div style="display: flex; align-items: flex-start; gap: 6px; line-height: 1.3;"><i class="fa-solid fa-circle-check" style="color: ${iconColor}; font-size: 10px; margin-top: 3px;"></i><span>${fb}</span></div>`;
                }).join("");
            }
        }

        // 5. Veredito Executivo
        const verdictText = document.getElementById("sandbox-verdict-text");
        if (verdictText) {

    verdictText.textContent = data.verdict_summary || (isEn ? "Simulation completed successfully." : "Simulação concluída com sucesso.");
        }

        if (btnSim && typeof btnSim.done === "function") {
            btnSim.done();
        }
        if (typeof showToast === "function") {
            showToast(isEn ? "Swap simulation calculated successfully!" : "Simulação de troca calculada com sucesso!", "success");
        }
    } catch (err) {
        console.error("Erro na simulação do Sandbox:", err);
        if (typeof showToast === "function") {
            showToast("Falha ao simular troca: " + err.message, "error");
        }
    } finally {
        if (btnSim) {
            btnSim.innerHTML = origHtml;
            btnSim.disabled = false;
        }
    }
};



// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
if (typeof generateDiffCardCanvas !== 'undefined') window.generateDiffCardCanvas = generateDiffCardCanvas;
if (typeof listUniqueDictKeys !== 'undefined') window.listUniqueDictKeys = listUniqueDictKeys;
if (typeof listUniqueSkillKeys !== 'undefined') window.listUniqueSkillKeys = listUniqueSkillKeys;
if (typeof loadBuildComparison !== 'undefined') window.loadBuildComparison = loadBuildComparison;
if (typeof sandboxCurrentMode !== 'undefined') window.sandboxCurrentMode = sandboxCurrentMode;
if (typeof sandboxInventoryPool !== 'undefined') window.sandboxInventoryPool = sandboxInventoryPool;
if (typeof setupInspectorTabs !== 'undefined') window.setupInspectorTabs = setupInspectorTabs;

window.addEventListener("app:languageChanged", () => {
    const inspector = document.getElementById("build-inspector");
    const panelCompare = document.getElementById("panel-compare");
    if (inspector && inspector.classList.contains("open") && panelCompare && panelCompare.style.display !== "none") {
        if (typeof loadBuildComparison === "function") {
            loadBuildComparison();
        }
    }
    const tabHistory = document.getElementById("tab-history");
    if (tabHistory && tabHistory.classList.contains("active") && typeof window.loadAccountHistory === "function") {
        const historyGame = document.getElementById("history-game-tabs")?.value || document.querySelector(".tab-history-game-btn.active")?.dataset?.game || "hsr";
        window.loadAccountHistory(historyGame);
    }
    const tabCodes = document.getElementById("tab-codes");
    if (tabCodes && tabCodes.classList.contains("active") && typeof window.loadPromoCodes === "function") {
        const codeGame = document.getElementById("codes-game-tabs")?.value || document.querySelector(".tab-codes-game-btn.active")?.dataset?.game || "hsr";
        window.loadPromoCodes(codeGame);
    }
});
