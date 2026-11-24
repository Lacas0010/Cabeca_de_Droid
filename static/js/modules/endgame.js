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
const _pendingEndgameModeId = { hsr: null, genshin: null, zzz: null };
let _cachedResetRadar = null;
let _resetRadarInflight = null;

const ENDGAME_MODE_EN_MAP = {
    "Caos da Memória (MoC)": "Memory of Chaos (MoC)",
    "Caos da Memória": "Memory of Chaos",
    "Ficção Pura": "Pure Fiction",
    "Sombra Apocalíptica": "Apocalyptic Shadow",
    "Abismo Espiral": "Spiral Abyss",
    "Teatro Imaginário": "Imaginarium Theater",
    "Defesa Shiyu (Shiyu Defense)": "Shiyu Defense",
    "Defesa Shiyu": "Shiyu Defense",
    "Assalto Mortal": "Deadly Assault",
    "Investida Fatal": "Deadly Assault",
    "Cavidade Zero": "Hollow Zero"
};

function formatEndgameModeName(name) {
    if (!Boolean(window.isEn) || !name) return name;
    if (ENDGAME_MODE_EN_MAP[name]) return ENDGAME_MODE_EN_MAP[name];
    let res = String(name);
    for (const [pt, en] of Object.entries(ENDGAME_MODE_EN_MAP)) {
        if (res.includes(pt)) res = res.replace(pt, en);
    }
    return res;
}

function formatEndgameStage(stage) {
    if (!Boolean(window.isEn) || !stage) return stage;
    let s = String(stage);
    return s.replace(/Piso\s*(\d+)/gi, 'Floor $1')
            .replace(/Câmara\s*(\d+)/gi, 'Chamber $1')
            .replace(/Desafio Arcano\s*(\d+)/gi, 'Arcane Challenge $1')
            .replace(/Temporada Atual/gi, 'Current Season')
            .replace(/Temporada\s*(\d+)/gi, 'Season $1')
            .replace(/Cruzando o Além/gi, 'Crossing the Beyond')
            .replace(/Modo Estelar/gi, 'Star Mode')
            .replace(/Palavras Imaginadas/gi, 'Imagined Words')
            .replace(/Dominação do Esquecimento/gi, 'Dominance of Oblivion')
            .replace(/Fronteira Crítica/gi, 'Critical Node')
            .replace(/Fronteira Estável/gi, 'Stable Node')
            .replace(/Nó Crítico/gi, 'Critical Node')
            .replace(/Zona Disputada/gi, 'Disputed Node')
            .replace(/Ato\s*(\d+)/gi, 'Act $1');
}

function formatEndgameTeamName(teamName) {
    if (!Boolean(window.isEn) || !teamName) return teamName;
    let t = String(teamName);
    return t.replace(/Lado\s*(\d+)/gi, 'Side $1')
            .replace(/Primeira Metade/gi, 'First Half')
            .replace(/Segunda Metade/gi, 'Second Half')
            .replace(/Ato\s*(\d+)/gi, 'Act $1')
            .replace(/Elenco Principal\s*\/\s*Destaques/gi, 'Main Cast / Highlights')
            .replace(/Agentes da Rotação/gi, 'Rotation Agents');
}

function formatEndgameRole(role) {
    if (!Boolean(window.isEn) || !role) return role;
    const rLower = String(role).toLowerCase().trim();
    const roleMap = {
        'dps principal': 'Main DPS',
        'dps': 'DPS',
        'sub-dps': 'Sub-DPS',
        'suporte': 'Support',
        'sustentação': 'Sustain',
        'sustentacao': 'Sustain',
        'amplificador': 'Buffer',
        'atordoador': 'Stunner',
        'anomalia': 'Anomaly',
        'defesa': 'Defense',
        'ataque': 'Attack',
        'buffer': 'Buffer',
        'debuffer': 'Debuffer',
        'healer': 'Healer',
        'shielder': 'Shielder'
    };
    return roleMap[rLower] || role;
}

function formatSynergyReason(reason) {
    if (!Boolean(window.isEn) || !reason) return reason;
    let r = String(reason);
    return r.replace(/Mesmo papel tático/gi, 'Same tactical role')
            .replace(/e mesmo elemento/gi, 'and same element')
            .replace(/já preparado/gi, 'battle-ready')
            .replace(/Substituto BiS/gi, 'BiS Substitute')
            .replace(/Opção Viável/gi, 'Viable Option')
            .replace(/Sinergia de Elemento/gi, 'Element Synergy')
            .replace(/Mesmo Elemento/gi, 'Same Element')
            .replace(/Mesma Função/gi, 'Same Role')
            .replace(/Nv\.\s*/gi, 'Lv. ');
}


function getEndgameModeIcon(modeId) {
    if (modeId === "moc") return "fa-trophy";
    if (modeId === "pure_fiction") return "fa-wand-magic-sparkles";
    if (modeId === "apocalyptic_shadow") return "fa-skull";
    if (modeId === "spiral_abyss") return "fa-dungeon";
    if (modeId === "imaginarium_theater") return "fa-masks-theater";
    if (modeId === "shiyu_defense") return "fa-shield-halved";
    if (modeId === "deadly_assault") return "fa-fire-flame-curved";
    return "fa-award";
}

function renderEndgameModeIcon(modeId, iconUrl, sizeClass = "md", altLabel = "") {
    const fallbackFa = getEndgameModeIcon(modeId);
    const safeAlt = String(altLabel || modeId || "").replace(/"/g, "&quot;");
    if (iconUrl && typeof iconUrl === "string") {
        return `
            <span class="endgame-mode-icon-wrap icon-${sizeClass}" data-mode-id="${modeId || ""}">
                <img class="endgame-mode-icon-img" src="${iconUrl}" alt="${safeAlt}" loading="lazy" decoding="async" onerror="this.style.display='none'; if (this.nextElementSibling) this.nextElementSibling.style.display='inline-flex';" />
                <i class="fa-solid ${fallbackFa} endgame-mode-icon-fallback" style="display:none;"></i>
            </span>
        `;
    }
    return `<span class="endgame-mode-icon-wrap icon-${sizeClass} is-fallback" data-mode-id="${modeId || ""}"><i class="fa-solid ${fallbackFa} endgame-mode-icon-fallback"></i></span>`;
}

function formatEndgameCountdown(resetAtIso, isEn) {
    if (!resetAtIso) {
        return { text: isEn ? "Unavailable" : "Indisponível", state: "unknown" };
    }
    const targetMs = Date.parse(resetAtIso);
    if (Number.isNaN(targetMs)) {
        return { text: isEn ? "Unavailable" : "Indisponível", state: "unknown" };
    }
    const diffMs = targetMs - Date.now();
    if (diffMs <= 0) {
        return { text: isEn ? "Reset!" : "Resetado!", state: "expired" };
    }
    const totalSec = Math.floor(diffMs / 1000);
    const days = Math.floor(totalSec / 86400);
    const hours = Math.floor((totalSec % 86400) / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);
    const secs = totalSec % 60;
    const pad = (n) => String(n).padStart(2, "0");

    if (days >= 1) {
        return {
            text: `${days}d ${pad(hours)}h ${pad(mins)}m`,
            state: days < 3 ? "soon" : "normal",
        };
    }
    return {
        text: `${pad(hours)}h ${pad(mins)}m ${pad(secs)}s`,
        state: "urgent",
    };
}

function formatResetDateTooltip(resetAtIso, isEn) {
    if (!resetAtIso) return "";
    const dt = new Date(resetAtIso);
    if (Number.isNaN(dt.getTime())) return "";
    try {
        const formatted = new Intl.DateTimeFormat(isEn ? "en-US" : "pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        }).format(dt);
        return isEn ? `Resets on ${formatted}` : `Reseta em ${formatted}`;
    } catch (_) {
        return resetAtIso;
    }
}

function renderModeResetChip(resetAtIso, isEn) {
    if (!resetAtIso) return "";
    const cd = formatEndgameCountdown(resetAtIso, isEn);
    const tooltip = formatResetDateTooltip(resetAtIso, isEn);
    const prefix = isEn ? "Resets in" : "Reseta em";
    return `
        <span class="endgame-metric-chip reset-countdown countdown-${cd.state}" title="${tooltip}">
            <i class="fa-regular fa-clock"></i>
            <span class="endgame-reset-prefix">${prefix}</span>
            <strong class="endgame-countdown-value" data-reset-at="${resetAtIso}">${cd.text}</strong>
        </span>
    `;
}

function renderEndgameResetStrip(resetSchedules, gameId) {
    if (!Array.isArray(resetSchedules) || resetSchedules.length === 0) return "";
    const isEn = Boolean(window.isEn);
    const cardsHtml = resetSchedules.map((sched) => {
        const displayName = formatEndgameModeName(sched.name);
        const iconHtml = renderEndgameModeIcon(sched.id, sched.icon, "strip", displayName);
        const cd = formatEndgameCountdown(sched.reset_at, isEn);
        const tooltip = formatResetDateTooltip(sched.reset_at, isEn);
        const estTag = sched.source === "estimated"
            ? `<span class="endgame-reset-source-tag" title="${isEn ? 'Estimated from server schedule' : 'Estimado pelo ciclo do servidor'}">~</span>`
            : "";
        return `
            <div class="endgame-reset-card countdown-${cd.state}" data-mode-id="${sched.id}" title="${tooltip}">
                <div class="endgame-reset-card-head">
                    <span class="endgame-reset-mode-name">
                        ${iconHtml}
                        <span class="endgame-reset-mode-label">${displayName}</span>
                    </span>
                    ${sched.badge ? `<span class="endgame-reset-badge">${sched.badge}</span>` : ""}
                </div>
                <div class="endgame-reset-card-time">
                    <span class="endgame-reset-label">${isEn ? "Resets in" : "Reseta em"}</span>
                    <span class="endgame-countdown-value" ${sched.reset_at ? `data-reset-at="${sched.reset_at}"` : ""}>${estTag}${cd.text}</span>
                </div>
            </div>
        `;
    }).join("");

    return `
        <div class="endgame-reset-strip" data-game="${gameId}">
            ${cardsHtml}
        </div>
    `;
}

let _endgameCountdownTimer = null;
let _endgameCountdownVisBound = false;

function tickEndgameCountdowns() {
    if (document.hidden) return;
    const nodes = document.querySelectorAll(".endgame-countdown-value[data-reset-at]");
    if (!nodes.length) return;
    const isEn = Boolean(window.isEn);
    nodes.forEach((el) => {
        const iso = el.getAttribute("data-reset-at");
        if (!iso) return;
        const cd = formatEndgameCountdown(iso, isEn);
        const prefixTag = el.querySelector(".endgame-reset-source-tag");
        if (prefixTag) {
            el.innerHTML = `${prefixTag.outerHTML}${cd.text}`;
        } else {
            el.textContent = cd.text;
        }
        const host = el.closest(".endgame-reset-card, .endgame-metric-chip.reset-countdown, .reset-radar-item, .reset-cycle-pill, .banner-reset-item");
        if (host) {
            host.classList.remove("countdown-normal", "countdown-soon", "countdown-urgent", "countdown-expired", "countdown-unknown");
            host.classList.add(`countdown-${cd.state}`);
        }
    });
}

function ensureEndgameCountdownTicker() {
    if (!_endgameCountdownTimer) {
        _endgameCountdownTimer = setInterval(tickEndgameCountdowns, 1000);
    }
    if (!_endgameCountdownVisBound) {
        _endgameCountdownVisBound = true;
        document.addEventListener("visibilitychange", () => {
            if (!document.hidden) tickEndgameCountdowns();
        });
    }
}

function normalizeEndgameChar(char, gameId) {
    if (!char) return char;
    let name = (char.name || "").trim();
    const id = String(char.id || "").trim();
    
    // Normaliza nomes desconhecidos do Desbravador e Viajante
    if (!name || name.toLowerCase().includes("desconhecido") || name.toLowerCase().includes("avatar")) {
        if (id.startsWith("800") || id.startsWith("801") || name.includes("8009") || name.includes("800")) {
            name = Boolean(window.isEn) ? "Trailblazer" : "Desbravador(a)";
            char.name = name;
            if (!char.element) char.element = "ice";
            char.rarity = 5;
        } else if (id === "10000005" || id === "10000007" || name.includes("1000000")) {
            name = Boolean(window.isEn) ? "Traveler" : "Viajante";
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

function _escapeEndgameHtml(str) {
    return String(str == null ? "" : str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function _formatTacticalIconUrl(url, width = 64) {
    if (!url || typeof url !== "string") return "";
    const trimmed = url.trim();
    if (!trimmed) return "";
    if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
        return `/api/proxy_image?url=${encodeURIComponent(trimmed)}&w=${width}&format=webp`;
    }
    if (trimmed.includes("/api/proxy_image?") && !trimmed.includes("&w=")) {
        return `${trimmed}&w=${width}&format=webp`;
    }
    return trimmed;
}

function _getBuffKindMeta(kind, isEn) {
    if (kind === "blessing") {
        return {
            label: isEn ? "Brilliant Blessing" : "Bênção Brilhante",
            fallbackIcon: "fa-sparkles",
            cls: "kind-blessing",
        };
    }
    if (kind === "card") {
        return {
            label: isEn ? "Mystery Event" : "Evento do Teatro",
            fallbackIcon: "fa-layer-group",
            cls: "kind-card",
        };
    }
    return {
        label: isEn ? "Stage Buff" : "Buff de Fase",
        fallbackIcon: "fa-wand-magic-sparkles",
        cls: "kind-buff",
    };
}

function renderEndgameTacticalStrip(team, gameId) {
    const isEn = Boolean(window.isEn);
    const boss = team && team.boss && (team.boss.name || team.boss.icon) ? team.boss : null;
    const rawBuffs = Array.isArray(team && team.buffs)
        ? team.buffs.filter(b => b && (b.name || b.icon || b.desc))
        : [];

    if (!boss && rawBuffs.length === 0) return "";

    let bossHtml = "";
    if (boss) {
        const bName = _escapeEndgameHtml(boss.name || (isEn ? "Boss" : "Chefe"));
        const bLvl = boss.level ? ` (${isEn ? "Lv." : "Nv."}${_escapeEndgameHtml(boss.level)})` : "";
        const bIconUrl = _formatTacticalIconUrl(boss.icon, 64);
        const bossLabel = isEn ? "Boss" : "Chefe";
        const nativeTitle = `${bossLabel}: ${bName}${bLvl}`;

        bossHtml = `
            <div class="endgame-boss-pill" tabindex="0" title="${nativeTitle}">
                <span class="endgame-boss-icon-wrap">
                    ${bIconUrl
                        ? `<img class="endgame-boss-icon-img" src="${bIconUrl}" alt="${bName}" width="26" height="26" loading="lazy" decoding="async" onerror="this.style.display='none'; if (this.nextElementSibling) this.nextElementSibling.style.display='inline-flex';" /><i class="fa-solid fa-skull endgame-tactical-icon-fallback" style="display:none;"></i>`
                        : `<i class="fa-solid fa-skull endgame-tactical-icon-fallback"></i>`
                    }
                </span>
                <div class="endgame-boss-meta">
                    <span class="endgame-boss-label">${bossLabel}</span>
                    <span class="endgame-boss-name">${bName}${bLvl}</span>
                </div>
                <div class="endgame-tactical-tooltip" role="tooltip">
                    <div class="endgame-tooltip-head">
                        <span class="endgame-tooltip-kind is-boss">${bossLabel}</span>
                        <strong class="endgame-tooltip-title">${bName}${bLvl}</strong>
                    </div>
                </div>
            </div>
        `;
    }

    let buffsHtml = "";
    if (rawBuffs.length > 0) {
        const MAX_VISIBLE_BUFFS = 5;
        const visibleBuffs = rawBuffs.slice(0, MAX_VISIBLE_BUFFS);
        const hiddenBuffs = rawBuffs.slice(MAX_VISIBLE_BUFFS);

        const chipsHtml = visibleBuffs.map(buff => {
            const meta = _getBuffKindMeta(buff.kind, isEn);
            const name = _escapeEndgameHtml(buff.name || meta.label);
            const desc = _escapeEndgameHtml(buff.desc || buff.simple_desc || "");
            const lvlNum = Number(buff.level || 0);
            const lvlTag = lvlNum > 0
                ? `<span class="endgame-buff-lvl">${isEn ? "Lv." : "Nv."}${lvlNum}</span>`
                : "";
            const iconUrl = _formatTacticalIconUrl(buff.icon, 64);
            const nativeTooltip = desc
                ? `${buff.name || meta.label}${lvlNum > 0 ? ` (${isEn ? "Lv." : "Nv."}${lvlNum})` : ""} — ${buff.desc || buff.simple_desc}`
                : `${buff.name || meta.label}${lvlNum > 0 ? ` (${isEn ? "Lv." : "Nv."}${lvlNum})` : ""}`;

            return `
                <div class="endgame-buff-chip ${meta.cls}" tabindex="0" title="${_escapeEndgameHtml(nativeTooltip)}">
                    <span class="endgame-buff-icon-wrap">
                        ${iconUrl
                            ? `<img class="endgame-buff-icon-img" src="${iconUrl}" alt="${name}" width="20" height="20" loading="lazy" decoding="async" onerror="this.style.display='none'; if (this.nextElementSibling) this.nextElementSibling.style.display='inline-flex';" /><i class="fa-solid ${meta.fallbackIcon} endgame-tactical-icon-fallback" style="display:none;"></i>`
                            : `<i class="fa-solid ${meta.fallbackIcon} endgame-tactical-icon-fallback"></i>`
                        }
                    </span>
                    <span class="endgame-buff-name">${name}</span>
                    ${lvlTag}
                    <div class="endgame-tactical-tooltip" role="tooltip">
                        <div class="endgame-tooltip-head">
                            <span class="endgame-tooltip-kind ${meta.cls}">${meta.label}${lvlNum > 0 ? ` • ${isEn ? "Lv." : "Nv."}${lvlNum}` : ""}</span>
                            <strong class="endgame-tooltip-title">${name}</strong>
                        </div>
                        ${desc ? `<p class="endgame-tooltip-desc">${desc.replace(/\n/g, "<br>")}</p>` : ""}
                    </div>
                </div>
            `;
        }).join("");

        let overflowChipHtml = "";
        if (hiddenBuffs.length > 0) {
            const overflowLines = hiddenBuffs
                .map(b => {
                    const bLvl = Number(b.level || 0) > 0 ? ` (${isEn ? "Lv." : "Nv."}${b.level})` : "";
                    return `• ${b.name || "Buff"}${bLvl}`;
                })
                .join("\n");
            const moreLabel = isEn ? `+${hiddenBuffs.length} more` : `+${hiddenBuffs.length} mais`;
            overflowChipHtml = `
                <div class="endgame-buff-chip is-overflow" tabindex="0" title="${_escapeEndgameHtml(overflowLines)}">
                    <span class="endgame-buff-name">${moreLabel}</span>
                    <div class="endgame-tactical-tooltip" role="tooltip">
                        <div class="endgame-tooltip-head">
                            <span class="endgame-tooltip-kind kind-card">${isEn ? "Additional Effects" : "Efeitos Adicionais"}</span>
                        </div>
                        <p class="endgame-tooltip-desc">${_escapeEndgameHtml(overflowLines).replace(/\n/g, "<br>")}</p>
                    </div>
                </div>
            `;
        }

        buffsHtml = `<div class="endgame-buff-row">${chipsHtml}${overflowChipHtml}</div>`;
    }

    return `
        <div class="endgame-tactical-strip" data-game="${gameId}">
            ${bossHtml}
            ${buffsHtml}
        </div>
    `;
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
            let avatarSrc = char.icon || fallbackIcon;
            if (avatarSrc.startsWith("http://") || avatarSrc.startsWith("https://")) {
                avatarSrc = `/api/proxy_image?url=${encodeURIComponent(avatarSrc)}&w=80&format=webp`;
            } else if (avatarSrc.includes("/api/proxy_image?") && !avatarSrc.includes("&w=")) {
                avatarSrc = `${avatarSrc}&w=80&format=webp`;
            }
            const rankBadge = char.rank_str ? `<span class="endgame-char-rank-badge">${char.rank_str}</span>` : "";

            const endgameCharName = typeof formatCharacterName === 'function' ? formatCharacterName(char.name) : char.name;
            charsHtml += `
                <div class="endgame-char-mini ${elemClass} ${rarityClass}" data-char-name="${char.name}" title="${endgameCharName} (${Boolean(window.isEn) ? 'Lv.' : 'Nv.'} ${char.level || 80}) • ${Boolean(window.isEn) ? 'Inspect Build' : 'Inspecionar Build'}">
                    <div class="endgame-char-avatar-box" style="position: relative; width: 38px; height: 38px; min-width: 38px; min-height: 38px; max-width: 38px; max-height: 38px; flex-shrink: 0; display: inline-block;">
                        <img src="${avatarSrc}" class="endgame-char-avatar" width="38" height="38" loading="lazy" decoding="async" style="width: 38px; height: 38px; min-width: 38px; min-height: 38px; max-width: 38px; max-height: 38px; border-radius: 50%; object-fit: cover; display: block;" onerror="this.onerror=null; this.src='${fallbackIcon}';" alt="${endgameCharName}">
                        ${elemKey && elemKey !== "bangboo" ? `<img src="${typeof getElementIconUrl === 'function' ? getElementIconUrl(gameId, char.element || elemKey) : `/assets/elements/${gameId}_${elemKey}.png?v=2`}" class="endgame-char-elem-icon" width="14" height="14" loading="lazy" decoding="async" style="position: absolute; bottom: -2px; right: -2px; width: 14px; height: 14px; min-width: 14px; min-height: 14px; max-width: 14px; max-height: 14px; border-radius: 50%; padding: 1px; object-fit: contain;" onerror="this.style.display='none';" alt="">` : ""}
                        ${rankBadge}
                    </div>
                    <span class="endgame-char-name-label">${endgameCharName}</span>
                    <span class="endgame-char-lvl-label">${Boolean(window.isEn) ? 'Lv.' : 'Nv.'} ${char.level || 80}</span>
                </div>
            `;
        });
        charsHtml += `</div>`;
    }

    const tacticalHtml = renderEndgameTacticalStrip(team, gameId);

    let monstersHtml = "";
    const filteredMonsters = Array.isArray(team.monsters)
        ? team.monsters.filter(m => !(team.boss && m && m.name && team.boss.name && m.name === team.boss.name))
        : [];
    if (filteredMonsters.length > 0) {
        monstersHtml = `<div class="endgame-enemies-row">`;
        filteredMonsters.forEach(m => {
            const mName = _escapeEndgameHtml(m.name || (Boolean(window.isEn) ? "Enemy" : "Inimigo"));
            const mLvl = m.level ? ` (${Boolean(window.isEn) ? 'Lv.' : 'Nv.'}${_escapeEndgameHtml(m.level)})` : "";
            const mIconUrl = _formatTacticalIconUrl(m.icon, 48);
            const iconPart = mIconUrl
                ? `<img class="endgame-enemy-icon" src="${mIconUrl}" alt="" width="15" height="15" loading="lazy" decoding="async" onerror="this.style.display='none'; if (this.nextElementSibling) this.nextElementSibling.style.display='inline-block';" /><i class="fa-solid fa-skull" style="display:none;"></i>`
                : `<i class="fa-solid fa-skull"></i>`;
            monstersHtml += `<span class="endgame-enemy-chip" title="${mName}${mLvl}">${iconPart} <span class="endgame-enemy-label">${mName}${mLvl}</span></span>`;
        });
        monstersHtml += `</div>`;
    }

    return `
        <div class="endgame-team-node">
            <div class="endgame-team-node-header">
                <div class="endgame-team-title-left">
                    <span class="endgame-side-dot"></span>
                    <span>${formatEndgameTeamName(team.name)}</span>
                </div>
                <span style="font-size: 10.5px; color: #94a3b8; font-weight: 500;">${(team.characters || []).length} ${Boolean(window.isEn) ? "Deployed" : "Mobilizados"}</span>
            </div>
            ${tacticalHtml}
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

    if (!container.innerHTML.trim() || container.querySelector(".endgame-empty-state")) {
        container.innerHTML = `
            <div style="display: flex; flex-direction: column; gap: 14px; padding: 12px 0;">
                <div class="skeleton-row" style="height: 120px; flex-direction: column; align-items: flex-start; justify-content: space-around; padding: 16px;">
                    <div class="skeleton-line" style="width: 35%; height: 18px;"></div>
                    <div class="skeleton-line" style="width: 70%; height: 12px;"></div>
                    <div style="display: flex; gap: 10px; width: 100%; margin-top: 8px;">
                        <div class="skeleton-box" style="width: 50px; height: 50px; border-radius: 50%;"></div>
                        <div class="skeleton-box" style="width: 50px; height: 50px; border-radius: 50%;"></div>
                        <div class="skeleton-box" style="width: 50px; height: 50px; border-radius: 50%;"></div>
                        <div class="skeleton-box" style="width: 50px; height: 50px; border-radius: 50%;"></div>
                    </div>
                </div>
                <div class="skeleton-row" style="height: 120px; flex-direction: column; align-items: flex-start; justify-content: space-around; padding: 16px;">
                    <div class="skeleton-line" style="width: 40%; height: 18px;"></div>
                    <div class="skeleton-line" style="width: 60%; height: 12px;"></div>
                    <div style="display: flex; gap: 10px; width: 100%; margin-top: 8px;">
                        <div class="skeleton-box" style="width: 50px; height: 50px; border-radius: 50%;"></div>
                        <div class="skeleton-box" style="width: 50px; height: 50px; border-radius: 50%;"></div>
                    </div>
                </div>
            </div>
        `;
    }

    try {
        const res = await fetch(`/api/endgame/${gameId}?lang=${Boolean(window.isEn) ? "en" : "pt"}`);
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
                    <sakuga-button class="endgame-empty-action-btn sk-sm" onclick="document.querySelector('.sync-game-btn[data-game=\\'${gameId}\\']')?.click()">
                        <i class="fa-solid fa-rotate"></i> Tentar Sincronizar
                    </sakuga-button>
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
        const isEn = Boolean(window.isEn);
        if (data && Array.isArray(data.reset_schedules)) {
            cachedEndgameData[gameId] = data;
        }
        if (badgeEl) badgeEl.innerText = isEn ? "No Data" : "Sem Dados";
        const gameNames = { hsr: "Honkai: Star Rail", genshin: "Genshin Impact", zzz: "Zenless Zone Zero" };
        const modeExamples = isEn ? {
            hsr: "Memory of Chaos (MoC), Pure Fiction or Apocalyptic Shadow",
            genshin: "Spiral Abyss or Imaginarium Theater",
            zzz: "Shiyu Defense or Deadly Assault"
        } : {
            hsr: "Caos da Memória (MoC), Ficção Pura ou Sombra Apocalíptica",
            genshin: "Abismo Espiral ou Teatro Imaginário",
            zzz: "Defesa Shiyu ou Assalto Mortal"
        };
        const emptyResetStripHtml = renderEndgameResetStrip(data?.reset_schedules || [], gameId);
        container.innerHTML = `
            ${emptyResetStripHtml}
            <div class="endgame-empty-state">
                <i class="fa-solid fa-hourglass-half"></i>
                <p>${isEn ? `No recent Endgame records collected for ${gameNames[gameId] || gameId.toUpperCase()}.` : `Nenhum registro de Endgame recente coletado para ${gameNames[gameId] || gameId.toUpperCase()}.`}</p>
                <span>${isEn ? `Clear stages of ${modeExamples[gameId] || "Endgame"} in-game and sync your Roster to view teams and scores here!` : `Conclua andares do ${modeExamples[gameId] || "Endgame"} no jogo e sincronize seu Roster para visualizar os times e pontuações aqui!`}</span>
                <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin-top: 12px;">
                    <sakuga-button class="endgame-empty-action-btn sk-sm" onclick="document.querySelector('.sync-game-btn[data-game=\\'${gameId}\\']')?.click()">
                        <i class="fa-solid fa-rotate"></i> ${isEn ? `Sync ${gameId.toUpperCase()} Now` : `Sincronizar ${gameId.toUpperCase()} Agora`}
                    </sakuga-button>
                    <sakuga-button class="endgame-empty-action-btn sk-sm sk-accent-cyan" onclick="activeEndgameView['${gameId}'] = 'team_matcher'; renderEndgame('${gameId}', { has_data: true, modes: [], reset_schedules: cachedEndgameData['${gameId}']?.reset_schedules || [] });">
                        <i class="fa-solid fa-people-group"></i> ${isEn ? "View Recommended Teams (Team Matcher)" : "Ver Times Recomendados (Team Matcher)"}
                    </sakuga-button>
                </div>
            </div>
        `;
        if (emptyResetStripHtml) ensureEndgameCountdownTicker();
        return;
    }

    cachedEndgameData[gameId] = data;

    // Aplica seleção pendente disparada pelo Radar Unificado de Resets (ou Ctrl+K futuro)
    if (_pendingEndgameModeId[gameId] && Array.isArray(data.modes) && data.modes.length > 0) {
        const targetIdx = data.modes.findIndex(m => m && m.id === _pendingEndgameModeId[gameId]);
        if (targetIdx >= 0) {
            activeEndgameView[gameId] = "single";
            activeEndgameModeIdx[gameId] = targetIdx;
        }
        _pendingEndgameModeId[gameId] = null;
    }

    // Métricas Totais
    const totalStars = data.modes ? data.modes.reduce((acc, m) => acc + (typeof m.stars === 'number' ? m.stars : 0), 0) : 0;
    const maxTotalStars = data.modes ? data.modes.reduce((acc, m) => acc + (typeof m.max_stars === 'number' ? m.max_stars : 0), 0) : 0;

    // Atualiza badge de resumo no botão da sub-navegação
    if (badgeEl) {
        if (totalStars > 0) {
            badgeEl.innerHTML = `<i class="fa-solid fa-star" style="color: #facc15;"></i> ${totalStars}★ (${data.modes.length} ${isEn ? "Modes" : "Modos"})`;
        } else {
            badgeEl.innerText = `${(data.modes || []).length} ${isEn ? "Modes" : "Modos"}`;
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
                    <span class="endgame-summary-chip gold" title="${isEn ? "Total Stars Collected Across All Modes" : "Total de Estrelas Coletadas em Todos os Modos"}">
                        <i class="fa-solid fa-star"></i> ${starsDisplay}
                    </span>
                    <span class="endgame-summary-chip cyan" title="${isEn ? "Active Modes with Records" : "Modos Ativos com Registros"}">
                        <i class="fa-solid fa-circle-check"></i> ${(data.modes || []).length} ${(data.modes || []).length === 1 ? (isEn ? "Active Mode" : "Modo") : (isEn ? "Active Modes" : "Modos Ativos")}
                    </span>
                    ${data.uid ? `<span class="endgame-summary-chip purple" title="UID da Conta"><i class="fa-solid fa-id-card"></i> UID ${data.uid}</span>` : ''}
                </div>
            </div>
            <div class="endgame-view-toggle-group">
                <sakuga-button variant="secondary" class="endgame-view-toggle-btn sk-xs ${currentView === 'single' ? 'active' : ''}" data-view="single" data-game="${gameId}">
                    <i class="fa-solid fa-table-columns"></i> ${isEn ? "Focused Mode" : "Modo Focado"}
                </sakuga-button>
                <sakuga-button variant="secondary" class="endgame-view-toggle-btn sk-xs ${currentView === 'all' ? 'active' : ''}" data-view="all" data-game="${gameId}">
                    <i class="fa-solid fa-list-ul"></i> ${isEn ? "Overview" : "Visão Geral"} (${(data.modes || []).length})
                </sakuga-button>
                <sakuga-button variant="secondary" class="endgame-view-toggle-btn sk-xs sk-accent-cyan ${currentView === 'team_matcher' ? 'active' : ''}" data-view="team_matcher" data-game="${gameId}">
                    <i class="fa-solid fa-people-group" style="color: #38bdf8;"></i> Team Matcher
                </sakuga-button>
            </div>
        </div>
    `;

    // 2. BARRA DE SELEÇÃO DE MODOS (SEGMENTED TABS)
    let pillsHtml = `<div class="endgame-mode-selector-bar">`;
    
    // Botão Visão Geral
    pillsHtml += `
        <sakuga-button variant="secondary" class="endgame-mode-tab-btn sk-xs ${currentView === 'all' ? 'active' : ''}" data-mode-idx="all" data-game="${gameId}">
            <i class="fa-solid fa-list-ul"></i>
            <span>${isEn ? "All Modes" : "Todos os Modos"}</span>
            <span class="tab-star-pill">${starsDisplay}</span>
        </sakuga-button>
    `;

    data.modes.forEach((mode, idx) => {
        const displayName = formatEndgameModeName(mode.name);
        const iconHtml = renderEndgameModeIcon(mode.id, mode.icon, "sm", displayName);
        let starPill = "";
        if (mode.stars !== null && mode.stars !== undefined && mode.stars !== "?") {
            starPill = `<span class="tab-star-pill">⭐ ${mode.stars}${mode.max_stars ? `/${mode.max_stars}` : ''}</span>`;
        }

        const isActive = (currentView === "single" && idx === currentIdx) ? "active" : "";
        pillsHtml += `
            <sakuga-button variant="secondary" class="endgame-mode-tab-btn sk-xs ${isActive}" data-mode-idx="${idx}" data-game="${gameId}">
                ${iconHtml}
                <span>${displayName}</span>
                ${starPill}
            </sakuga-button>
        `;
    });
    pillsHtml += `</div>`;

    // 3. CONTEÚDO PRINCIPAL (VISÃO INDIVIDUAL OU VISÃO GERAL)
    let contentHtml = "";

    if (currentView === "all") {
        // VISÃO GERAL: TODOS OS MODOS EM LISTA (UM EMBAIXO DO OUTRO)
        let overviewCardsHtml = `<div class="endgame-overview-matrix">`;
        data.modes.forEach((mode, mIdx) => {
            const displayName = formatEndgameModeName(mode.name);
            const iconHtml = renderEndgameModeIcon(mode.id, mode.icon, "md", displayName);
            let modeMetrics = "";
            if (mode.stars !== null && mode.stars !== undefined && mode.stars !== "?") {
                modeMetrics += `<span class="endgame-metric-chip gold-stars"><i class="fa-solid fa-star"></i> ${mode.stars}${mode.max_stars ? `/${mode.max_stars}` : ''}</span>`;
            }
            if (mode.metric_label && mode.metric_value && mode.metric_value !== "?" && mode.metric_value !== "None") {
                const isScore = mode.metric_label.toLowerCase().includes("pontuação") || mode.metric_label.toLowerCase().includes("score");
                const isRounds = mode.metric_label.toLowerCase().includes("rodada") || mode.metric_label.toLowerCase().includes("round");
                const chipClass = isScore ? "blue-score" : (isRounds ? "purple-rounds" : "");
                const chipIcon = isScore ? "fa-bolt" : (isRounds ? "fa-clock-rotate-left" : "fa-award");
                modeMetrics += `<span class="endgame-metric-chip ${chipClass}"><i class="fa-solid ${chipIcon}"></i> ${mode.metric_value} ${!isScore && !isRounds ? "" : (isRounds ? (isEn ? "Cycles" : "Rodadas") : (isEn ? "Points" : "Pontos"))}</span>`;
            }
            if (mode.reset_at) {
                modeMetrics += renderModeResetChip(mode.reset_at, isEn);
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
                            ${iconHtml}
                            <span>${displayName}</span>
                            ${mode.badge ? `<span style="font-size: 10px; padding: 2px 6px; border-radius: 5px; background: rgba(255,255,255,0.08); font-weight: 700;">${mode.badge}</span>` : ""}
                            ${mode.stage ? `<span class="endgame-mode-stage-desc">${formatEndgameStage(mode.stage)}</span>` : ""}
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
                    <i class="fa-solid fa-star"></i> ${activeMode.stars}${activeMode.max_stars ? `/${activeMode.max_stars}` : ""} ${isEn ? "Stars" : "Estrelas"}
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
                    <i class="fa-solid ${chipIcon}"></i> ${activeMode.metric_value} ${!isScore && !isRounds ? "" : (isRounds ? (isEn ? "Cycles" : "Rodadas") : (isEn ? "Points" : "Pontos"))}
                </span>
            `;
        }
        if (activeMode.reset_at) {
            metricsHtml += renderModeResetChip(activeMode.reset_at, isEn);
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

        const activeDisplayName = formatEndgameModeName(activeMode.name);
        const activeIconHtml = renderEndgameModeIcon(activeMode.id, activeMode.icon, "lg", activeDisplayName);
        contentHtml = `
            <div class="endgame-active-mode-pane">
                <div class="endgame-mode-meta-header">
                    <div class="endgame-mode-title-area">
                        <div class="endgame-mode-main-title">
                            ${activeIconHtml}
                            <span>${activeDisplayName}</span>
                            ${activeMode.badge ? `<span style="font-size: 10px; padding: 2px 6px; border-radius: 5px; background: rgba(255,255,255,0.08); font-weight: 700;">${activeMode.badge}</span>` : ""}
                        </div>
                        ${activeMode.stage ? `<span class="endgame-mode-stage-desc">${formatEndgameStage(activeMode.stage)}</span>` : ""}
                    </div>
                    <div class="endgame-metrics-group">
                        ${metricsHtml}
                    </div>
                </div>
                ${teamsHtml}
            </div>
        `;
    }

    const resetStripHtml = renderEndgameResetStrip(data.reset_schedules || [], gameId);

    if (currentView === "team_matcher") {
        container.innerHTML = masterHeaderHtml + resetStripHtml + `<div id="team-matcher-container-${gameId}"><div class="endgame-loading-spinner"><i class="fa-solid fa-spinner fa-spin"></i> ${isEn ? "Loading team compatibility..." : "Carregando compatibilidade de equipes..."}</div></div>`;
        renderTeamMatcher(gameId);
    } else {
        container.innerHTML = masterHeaderHtml + resetStripHtml + pillsHtml + contentHtml;
    }
    ensureEndgameCountdownTicker();

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
        let url = `/api/endgame/team-match/${gameId}?min_match=${state.minMatch}&lang=${Boolean(window.isEn) ? "en" : "pt"}`;
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
    const isEn = Boolean(window.isEn);
    const modesList = data.available_modes || [];
    
    // Barra de Filtros
    let filterBarHtml = `
        <div class="team-matcher-filter-bar">
            <div class="team-matcher-filter-group">
                <span style="font-size: 12px; font-weight: 700; color: #94a3b8;"><i class="fa-solid fa-filter"></i> ${isEn ? "Filter:" : "Filtrar:"}</span>
                <select class="team-matcher-select" id="matcher-mode-select-${gameId}">
                    <option value="" ${state.mode === "" ? "selected" : ""}>${isEn ? "All Modes" : "Todos os Modos"} (${modesList.length})</option>
                    ${modesList.map(m => `<option value="${m}" ${state.mode === m ? "selected" : ""}>${formatEndgameModeName(m)}</option>`).join("")}
                </select>
                <select class="team-matcher-select" id="matcher-compat-select-${gameId}">
                    <option value="0" ${state.minMatch == 0 ? "selected" : ""}>${isEn ? "All Compositions" : "Todas as Composições"}</option>
                    <option value="50" ${state.minMatch == 50 ? "selected" : ""}>${isEn ? "Viable (≥ 50%)" : "Viáveis (≥ 50%)"}</option>
                    <option value="75" ${state.minMatch == 75 ? "selected" : ""}>${isEn ? "Nearly Ready (≥ 75%)" : "Quase Prontas (≥ 75%)"}</option>
                    <option value="100" ${state.minMatch == 100 ? "selected" : ""}>${isEn ? "100% Complete (Ready)" : "100% Completas (Prontas)"}</option>
                </select>
            </div>
            <div class="team-matcher-filter-group">
                <span style="font-size: 11.5px; color: #38bdf8; font-weight: 700;">
                    <i class="fa-solid fa-circle-check"></i> ${data.ready_teams_count} ${isEn ? "Ready" : "Prontas"}
                </span>
                <span style="font-size: 11.5px; color: #94a3b8;">
                    ${isEn ? "of" : "de"} ${data.total_teams} ${isEn ? "analyzed" : "analisadas"}
                </span>
            </div>
        </div>
    `;

    if (!data.teams || data.teams.length === 0) {
        container.innerHTML = filterBarHtml + `
            <div class="endgame-empty-state" style="margin-top: 16px;">
                <i class="fa-solid fa-users-slash"></i>
                <p>${isEn ? "No metagame teams found with the selected filters." : "Nenhuma equipe metagame encontrada com os filtros selecionados."}</p><span>${isEn ? "Try lowering the minimum compatibility filter to view teams with substitute recommendations." : "Tente reduzir o filtro de compatibilidade mínima para visualizar equipes com sugestão de substitutos."}</span>
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

    const statusText = isReady100 ? (isEn ? "Complete Team" : "Equipe Completa") : `${team.owned_count}/${team.total_count} ${isEn ? "Members" : "Membros"}`;

    let slotsHtml = `<div class="team-matcher-slots-grid">`;
    team.members.forEach(m => {
        const fallbackIcon = `/assets/${gameId}_icon.png`;
        let avatarSrc = m.icon || fallbackIcon;
        if (avatarSrc.startsWith("http://") || avatarSrc.startsWith("https://")) {
            avatarSrc = `/api/proxy_image?url=${encodeURIComponent(avatarSrc)}&w=80&format=webp`;
        } else if (avatarSrc.includes("/api/proxy_image?") && !avatarSrc.includes("&w=")) {
            avatarSrc = `${avatarSrc}&w=80&format=webp`;
        }
        const elemKey = (m.element || "").toLowerCase();
        const elemClass = ELEMENT_MAPPING[elemKey] || "el-physical";
        const rarityClass = (m.rarity === 5 || m.rarity === "5" || String(m.rarity).toUpperCase() === "S") ? "rarity-5" : "rarity-4";

        const mDisplayName = typeof formatCharacterName === 'function' ? formatCharacterName(m.name) : m.name;
        if (m.is_owned) {
            slotsHtml += `
                <div class="team-matcher-slot owned" title="${mDisplayName} (Nv. ${m.level || 80} ${m.rank_str || ''}) • ${isEn ? "In your Roster" : "No seu Roster"}">
                    <div class="team-matcher-avatar-box ${elemClass} ${rarityClass}">
                        <img src="${avatarSrc}" width="38" height="38" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='${fallbackIcon}';" alt="${mDisplayName}">
                    </div>
                    <span class="team-matcher-slot-name">${mDisplayName}</span>
                    <span class="team-matcher-slot-role">${formatEndgameRole(m.role)}</span>
                    <span class="team-matcher-slot-badge owned">${isEn ? "Lv." : "Nv."} ${m.level || 80}</span>
                </div>
            `;
        } else {
            slotsHtml += `
                <div class="team-matcher-slot missing" title="${mDisplayName} • ${isEn ? "Not Owned" : "Não Possuído"}">
                    <div class="team-matcher-avatar-box">
                        <img src="${avatarSrc}" width="38" height="38" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='${fallbackIcon}';" alt="${mDisplayName}">
                    </div>
                    <span class="team-matcher-slot-name">${mDisplayName}</span>
                    <span class="team-matcher-slot-role">${formatEndgameRole(m.role)}</span>
                    <span class="team-matcher-slot-badge missing"><i class="fa-solid fa-xmark"></i> ${isEn ? "Missing" : "Faltando"}</span>
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
                    <i class="fa-solid fa-arrows-rotate"></i> ${isEn ? "Recommended Substitutes in your Roster:" : "Substitutos Recomendados no seu Roster:"}
                </div>
                <div class="team-matcher-subs-list">
                    ${missingWithSubs.map(m => `
                        <div>
                            <span style="font-size: 11px; color: #f87171; font-weight: 600;">${isEn ? `For the slot of ${typeof formatCharacterName === 'function' ? formatCharacterName(m.name) : m.name} (${formatEndgameRole(m.role)}):` : `Para o slot de ${m.name} (${m.role}):`}</span>
                            <div style="display: flex; flex-direction: column; gap: 4px; margin-top: 4px;">
                                ${m.substitutes.map(sub => `
                                    <div class="team-matcher-sub-chip">
                                        <div class="team-matcher-sub-info">
                                            <img src="${sub.icon || `/assets/${gameId}_icon.png`}" class="team-matcher-sub-avatar" width="28" height="28" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='/assets/${gameId}_icon.png';">
                                            <div>
                                                <strong style="color: #f8fafc;">${typeof formatCharacterName === 'function' ? formatCharacterName(sub.name) : sub.name}</strong> 
                                                <span style="color: #94a3b8; font-size: 10px;">(${isEn ? "Lv." : "Nv."} ${sub.level} • ${sub.rank_str})</span>
                                            </div>
                                        </div>
                                        <span style="font-size: 10px; color: #38bdf8; text-align: right;">${formatSynergyReason(sub.synergy_reason)}</span>
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
                        <span class="endgame-summary-chip cyan"><i class="fa-solid fa-location-crosshairs"></i> ${formatEndgameModeName(team.mode)}</span>
                        ${team.tier_or_rank ? `<span class="endgame-summary-chip gold"><i class="fa-solid fa-trophy"></i> ${team.tier_or_rank}</span>` : ''}
                        ${team.avg_performance ? `<span class="endgame-summary-chip purple"><i class="fa-solid fa-gauge-high"></i> ${team.avg_performance}</span>` : ''}
                        ${team.usage_rate ? `<span class="endgame-summary-chip"><i class="fa-solid fa-chart-simple"></i> ${isEn ? "Usage:" : "Uso:"} ${team.usage_rate}</span>` : ''}
                    </div>
                </div>
                <div class="team-match-badge ${badgeClass}" title="${isEn ? 'Direct compatibility of owned characters' : 'Compatibilidade direta de personagens possuídos'}">
                    <i class="fa-solid ${badgeIcon}"></i> ${team.match_percentage}% (${statusText})
                </div>
            </div>

            ${slotsHtml}
            ${subsHtml}

            ${team.synergy_notes ? `
                <div class="team-matcher-synergy-text">
                    <strong><i class="fa-solid fa-bolt" style="color: #fbbf24;"></i> ${isEn ? "Combat Strategy:" : "Estratégia de Combate:"}</strong> ${team.synergy_notes}
                    ${team.recommended_buffs_bosses ? `<br><span style="color: #94a3b8; font-size: 11px;"><strong>${isEn ? "Ideal Bosses / Stages:" : "Chefes / Fases Ideais:"}</strong> ${team.recommended_buffs_bosses}</span>` : ''}
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

// ==========================================================================
// RADAR UNIFICADO DE RESETS NA HOME (7 MODOS + DIÁRIO 04:00 / SEMANAL SEG 04:00)
// ==========================================================================
function loadHomeResetRadar(forceRefresh = false) {
    if (_resetRadarInflight && !forceRefresh) return _resetRadarInflight;
    const strip = document.getElementById("home-reset-radar-strip");
    if (!strip) return Promise.resolve();

    const isEn = Boolean(window.isEn);
    if (!strip.querySelector(".reset-radar-item") || forceRefresh) {
        strip.innerHTML = `
            <div class="reset-radar-loading">
                <i class="fa-solid fa-spinner fa-spin"></i>
                <span>${isEn ? "Syncing schedule for all 7 endgame modes..." : "Sincronizando cronograma dos 7 modos de endgame..."}</span>
            </div>
        `;
    }

    _resetRadarInflight = fetch(`/api/endgame/reset-radar?lang=${isEn ? "en" : "pt"}`)
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(data => {
            _cachedResetRadar = data;
            renderHomeResetRadar(data);
        })
        .catch(err => {
            console.error("[RADAR] Erro ao carregar Radar Unificado de Resets:", err);
            const currEn = Boolean(window.isEn);
            strip.innerHTML = `
                <div class="reset-radar-error">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <span>${currEn ? "Could not load the unified reset schedule." : "Não foi possível carregar o cronograma unificado de resets."}</span>
                    <sakuga-button class="sk-xs" variant="secondary" onclick="window.loadHomeResetRadar && window.loadHomeResetRadar(true)">
                        <i class="fa-solid fa-rotate"></i> ${currEn ? "Retry" : "Tentar Novamente"}
                    </sakuga-button>
                </div>
            `;
        })
        .finally(() => {
            _resetRadarInflight = null;
        });

    return _resetRadarInflight;
}

function _renderRadarStatusBadge(item, isEn) {
    const hasStars = item.stars !== null && item.stars !== undefined && item.max_stars;
    const progressText = hasStars
        ? `${item.stars}/${item.max_stars}★`
        : (item.metric_value && item.metric_value !== "?" && item.metric_value !== "None" ? _escapeEndgameHtml(item.metric_value) : "");

    if (item.status === "completed") {
        const lbl = isEn ? "Completed" : "Concluído";
        return `
            <span class="reset-radar-status status-completed">
                <i class="fa-solid fa-circle-check"></i>
                <span>${lbl}${progressText ? ` · ${progressText}` : ""}</span>
            </span>
        `;
    }
    if (item.status === "in_progress") {
        const lbl = isEn ? "In Progress" : "Em Progresso";
        return `
            <span class="reset-radar-status status-in-progress ${item.is_urgent_pending ? "is-amber-alert" : ""}">
                <i class="fa-solid ${item.is_urgent_pending ? "fa-triangle-exclamation" : "fa-hourglass-half"}"></i>
                <span>${lbl}${progressText ? ` · ${progressText}` : ""}</span>
            </span>
        `;
    }
    const pendingLbl = item.is_urgent_pending
        ? (isEn ? "Pending · Soon!" : "Pendente · Urgente")
        : (isEn ? "Pending" : "Pendente");
    return `
        <span class="reset-radar-status status-pending ${item.is_urgent_pending ? "is-amber-alert" : ""}">
            <i class="fa-solid ${item.is_urgent_pending ? "fa-triangle-exclamation" : "fa-circle-dot"}"></i>
            <span>${pendingLbl}</span>
        </span>
    `;
}

function renderHomeResetRadar(data) {
    const strip = document.getElementById("home-reset-radar-strip");
    const summaryEl = document.getElementById("home-reset-radar-summary");
    if (!strip || !data) return;

    const isEn = Boolean(window.isEn);

    // 1. Atualiza timers de ciclos do servidor (Diário 04:00 e Semanal Seg 04:00)
    const srv = data.server_resets || {};
    const tzInfo = srv.server_tz_label ? ` (${srv.server_tz_label})` : "";
    const dailyEl = document.getElementById("radar-daily-countdown");
    const dailyPill = document.getElementById("radar-daily-cycle-pill");
    if (dailyEl && srv.daily_reset_at) {
        const cdDaily = formatEndgameCountdown(srv.daily_reset_at, isEn);
        dailyEl.setAttribute("data-reset-at", srv.daily_reset_at);
        dailyEl.textContent = cdDaily.text;
        if (dailyPill) {
            dailyPill.title = `${formatResetDateTooltip(srv.daily_reset_at, isEn)}${tzInfo}`;
        }
    }
    const weeklyEl = document.getElementById("radar-weekly-countdown");
    const weeklyPill = document.getElementById("radar-weekly-cycle-pill");
    if (weeklyEl && srv.weekly_reset_at) {
        const cdWeekly = formatEndgameCountdown(srv.weekly_reset_at, isEn);
        weeklyEl.setAttribute("data-reset-at", srv.weekly_reset_at);
        weeklyEl.textContent = cdWeekly.text;
        if (weeklyPill) {
            weeklyPill.title = `${formatResetDateTooltip(srv.weekly_reset_at, isEn)}${tzInfo}`;
        }
    }

    // 2. Pills de resumo no cabeçalho
    const items = Array.isArray(data.items) ? data.items : [];
    const summary = data.summary || {};
    const total = summary.total_modes ?? items.length;
    const completed = summary.completed_count ?? items.filter(i => i.status === "completed").length;
    const pending = summary.pending_count ?? Math.max(0, total - completed);
    const urgentPending = summary.urgent_pending_count ?? items.filter(i => i.is_urgent_pending).length;

    if (summaryEl) {
        summaryEl.innerHTML = `
            <span class="reset-radar-meta-pill is-done">
                <i class="fa-solid fa-check"></i> ${completed}/${total} ${isEn ? "Cleared" : "Concluídos"}
            </span>
            ${pending > 0 ? `
                <span class="reset-radar-meta-pill ${urgentPending > 0 ? "is-amber" : "is-pending"}">
                    <i class="fa-solid ${urgentPending > 0 ? "fa-bell" : "fa-clock"}"></i>
                    ${urgentPending > 0
                        ? (isEn ? `${urgentPending} Urgent` : `${urgentPending} Próximo(s)`)
                        : `${pending} ${isEn ? "Pending" : "Pendente(s)"}`
                    }
                </span>
            ` : ""}
        `;
    }

    if (items.length === 0) {
        strip.innerHTML = `
            <div class="reset-radar-empty">
                <i class="fa-regular fa-calendar-xmark"></i>
                <span>${isEn ? "No endgame modes available yet." : "Nenhum modo endgame disponível no momento."}</span>
            </div>
        `;
        return;
    }

    // 3. Renderiza os 7 modos ordenados por urgência
    strip.innerHTML = items.map(item => {
        const displayName = formatEndgameModeName(item.name);
        const iconHtml = renderEndgameModeIcon(item.id, item.icon, "strip", displayName);
        const cd = formatEndgameCountdown(item.reset_at, isEn);
        const dateTip = formatResetDateTooltip(item.reset_at, isEn);
        const estTag = item.source === "estimated"
            ? `<span class="endgame-reset-source-tag" title="${isEn ? "Estimated from server cycle" : "Estimado pelo ciclo do servidor"}">~</span>`
            : "";
        const statusCls = item.status === "completed"
            ? "is-completed"
            : (item.is_urgent_pending ? "is-urgent-pending" : "is-pending");
        const navHint = isEn
            ? `Click to open ${displayName} (${item.game_label})`
            : `Clique para abrir ${displayName} (${item.game_label})`;
        const fullTitle = dateTip ? `${displayName} • ${dateTip} • ${navHint}` : `${displayName} • ${navHint}`;

        return `
            <button type="button"
                class="reset-radar-item game-${_escapeEndgameHtml(item.game_id)} ${statusCls} countdown-${cd.state}"
                data-game="${_escapeEndgameHtml(item.game_id)}"
                data-mode-id="${_escapeEndgameHtml(item.id)}"
                title="${_escapeEndgameHtml(fullTitle)}">
                <div class="reset-radar-item-top">
                    <div class="reset-radar-item-id">
                        ${iconHtml}
                        <div class="reset-radar-item-titles">
                            <span class="reset-radar-mode-name">${_escapeEndgameHtml(displayName)}</span>
                            <span class="reset-radar-game-tag game-${_escapeEndgameHtml(item.game_id)}">${_escapeEndgameHtml(item.game_label)} · ${_escapeEndgameHtml(item.badge || "")}</span>
                        </div>
                    </div>
                    <span class="reset-radar-jump-icon" aria-hidden="true"><i class="fa-solid fa-arrow-right"></i></span>
                </div>
                <div class="reset-radar-item-timer">
                    <span class="reset-radar-timer-label">${isEn ? "Resets in" : "Reseta em"}</span>
                    <strong class="endgame-countdown-value" ${item.reset_at ? `data-reset-at="${_escapeEndgameHtml(item.reset_at)}"` : ""}>${estTag}${cd.text}</strong>
                </div>
                <div class="reset-radar-item-foot">
                    ${_renderRadarStatusBadge(item, isEn)}
                </div>
            </button>
        `;
    }).join("");

    strip.querySelectorAll(".reset-radar-item").forEach(btn => {
        btn.addEventListener("click", () => {
            const gid = btn.getAttribute("data-game");
            const mid = btn.getAttribute("data-mode-id");
            if (gid) navigateToEndgameMode(gid, mid);
        });
    });

    // 4. Renderiza a subseção de Virada de Banners Ativos na Home
    renderHomeBannerResets(Array.isArray(data.banners) ? data.banners : [], isEn);

    ensureEndgameCountdownTicker();
}

function _formatRadarBannerPhaseLabel(banner, isEn) {
    const dt = String(banner?.duration_type || "").toLowerCase();
    const bTime = banner?.banner_time || "";
    if (dt === "full_patch") {
        const lbl = isEn ? "Full Patch" : "Patch Inteiro";
        return bTime ? `${lbl} · ${isEn ? "Att" : "Att"} ${bTime}` : lbl;
    }
    if (dt === "phase_2" || Number(banner?.phase) === 2) {
        const lbl = isEn ? "Phase 2" : "2ª Fase";
        return bTime ? `${lbl} · ${isEn ? "Att" : "Att"} ${bTime}` : lbl;
    }
    const lbl = isEn ? "Phase 1" : "1ª Fase";
    return bTime ? `${lbl} · ${bTime}` : lbl;
}

function renderHomeBannerResets(banners, isEn) {
    const section = document.getElementById("home-banner-reset-section");
    const strip = document.getElementById("home-banner-reset-strip");
    if (!section || !strip) return;

    if (!Array.isArray(banners) || banners.length === 0) {
        section.style.display = "none";
        strip.innerHTML = "";
        return;
    }

    section.style.display = "";
    strip.innerHTML = banners.map(b => {
        const gid = String(b.game_id || "genshin").toLowerCase();
        const fallbackGameIcon = `/assets/${gid}_icon.png`;
        const chars = Array.isArray(b.characters) ? b.characters.slice(0, 3) : [];
        const avatarsHtml = chars.map(c => {
            const cName = _escapeEndgameHtml(c.name || b.primary_character || "");
            const cIcon = _formatTacticalIconUrl(c.icon, 64) || fallbackGameIcon;
            return `<img class="banner-reset-avatar" src="${cIcon}" alt="${cName}" width="28" height="28" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='${fallbackGameIcon}';" />`;
        }).join("");

        const cd = formatEndgameCountdown(b.end_at, isEn);
        const dateTip = formatResetDateTooltip(b.end_at, isEn);
        const phaseMeta = _formatRadarBannerPhaseLabel(b, isEn);
        const endingSoonCls = b.is_ending_soon ? "is-ending-soon" : "";
        const endingSoonBadge = b.is_ending_soon
            ? `<span class="banner-reset-urgent-pill"><i class="fa-solid fa-fire"></i> ${isEn ? "< 48h" : "< 48h"}</span>`
            : "";
        const simHint = isEn ? "Simulate in Gacha" : "Simular no Gacha";
        const fullTitle = `${b.title} (${b.game_label} · ${phaseMeta})${dateTip ? ` • ${dateTip}` : ""} • ${simHint}`;

        return `
            <button type="button"
                class="banner-reset-item game-${_escapeEndgameHtml(gid)} ${endingSoonCls} countdown-${cd.state}"
                data-game="${_escapeEndgameHtml(gid)}"
                data-char="${_escapeEndgameHtml(b.primary_character || "")}"
                title="${_escapeEndgameHtml(fullTitle)}">
                <div class="banner-reset-top">
                    <div class="banner-reset-avatars">${avatarsHtml}</div>
                    <div class="banner-reset-titles">
                        <span class="banner-reset-names">${_escapeEndgameHtml(b.title || b.primary_character || "")}</span>
                        <span class="banner-reset-sub game-${_escapeEndgameHtml(gid)}">${_escapeEndgameHtml(b.game_label)} · ${_escapeEndgameHtml(phaseMeta)}</span>
                    </div>
                    <span class="banner-reset-jump" aria-hidden="true"><i class="fa-solid fa-wand-sparkles"></i></span>
                </div>
                <div class="banner-reset-bottom">
                    <div class="banner-reset-cd-wrap">
                        <span class="banner-reset-cd-label">${isEn ? "Ends in" : "Vira em"}</span>
                        <strong class="endgame-countdown-value" ${b.end_at ? `data-reset-at="${_escapeEndgameHtml(b.end_at)}"` : ""}>${cd.text}</strong>
                    </div>
                    ${endingSoonBadge}
                </div>
            </button>
        `;
    }).join("");

    strip.querySelectorAll(".banner-reset-item").forEach(btn => {
        btn.addEventListener("click", () => {
            const gid = btn.getAttribute("data-game");
            const charName = btn.getAttribute("data-char");
            if (gid) navigateToBannerSimulator(gid, charName);
        });
    });
}

function navigateToBannerSimulator(gameId, characterName) {
    const cleanGame = String(gameId || "genshin").toLowerCase().trim();
    const targetChar = String(characterName || "").trim();

    const gachaNavBtn = document.querySelector('.nav-btn[data-tab="gacha"]');
    if (gachaNavBtn) {
        gachaNavBtn.click();
    }

    const applyTarget = () => {
        if (typeof window.prefillGachaBannerTarget === "function") {
            window.prefillGachaBannerTarget(cleanGame, targetChar, "character");
        }
    };

    if (typeof window.loadGachaModules === "function") {
        window.loadGachaModules().then(applyTarget).catch(() => {});
    } else {
        setTimeout(applyTarget, 150);
    }
}

function navigateToEndgameMode(gameId, modeId) {
    const cleanGame = String(gameId || "").toLowerCase().trim();
    if (!["hsr", "genshin", "zzz"].includes(cleanGame)) return;

    // 1. Ativa a aba principal do jogo
    const navBtn = document.querySelector(`.nav-btn[data-tab="${cleanGame}"]`);
    if (navBtn) {
        navBtn.click();
    }

    // 2. Seleciona a sub-aba Endgame no componente sakuga-tabs e ativa o subview
    const section = document.getElementById(`tab-${cleanGame}`);
    if (section) {
        const tabsEl = section.querySelector(`sakuga-tabs.sk-game-subnav[data-game="${cleanGame}"]`);
        if (tabsEl) {
            const opts = Array.from(tabsEl.querySelectorAll("option"));
            const endgameIdx = opts.findIndex(o => o.value === "endgame");
            if (endgameIdx >= 0) {
                tabsEl.selected = endgameIdx;
            }
        }
        section.querySelectorAll(".game-subnav-btn").forEach(b => {
            b.classList.toggle("active", b.getAttribute("data-view") === "endgame");
        });
    }
    if (typeof window.activateGameSubview === "function") {
        window.activateGameSubview(cleanGame, "endgame");
    } else {
        const subEl = document.getElementById(`view-endgame-${cleanGame}`);
        if (section && subEl) {
            section.querySelectorAll(".game-subview").forEach(v => v.classList.remove("active"));
            subEl.classList.add("active");
        }
    }

    // 3. Foca no modo específico (se já carregado) ou agenda foco assim que terminar o fetch
    if (modeId) {
        activeEndgameView[cleanGame] = "single";
        const cached = cachedEndgameData[cleanGame];
        if (cached && Array.isArray(cached.modes) && cached.modes.length > 0) {
            const idx = cached.modes.findIndex(m => m && m.id === modeId);
            if (idx >= 0) {
                activeEndgameModeIdx[cleanGame] = idx;
            }
            _pendingEndgameModeId[cleanGame] = null;
            renderEndgame(cleanGame, cached);
        } else {
            _pendingEndgameModeId[cleanGame] = modeId;
            loadEndgame(cleanGame);
        }
    } else if (!cachedEndgameData[cleanGame]) {
        loadEndgame(cleanGame);
    }

    // 4. Rola suavemente até o painel de endgame
    const endgameView = document.getElementById(`view-endgame-${cleanGame}`);
    if (endgameView) {
        requestAnimationFrame(() => {
            endgameView.scrollIntoView({ behavior: "smooth", block: "start" });
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
if (typeof loadHomeResetRadar !== 'undefined') window.loadHomeResetRadar = loadHomeResetRadar;
if (typeof navigateToBannerSimulator !== 'undefined') window.navigateToBannerSimulator = navigateToBannerSimulator;
if (typeof navigateToEndgameMode !== 'undefined') window.navigateToEndgameMode = navigateToEndgameMode;
if (typeof normalizeEndgameChar !== 'undefined') window.normalizeEndgameChar = normalizeEndgameChar;
if (typeof renderEndgame !== 'undefined') window.renderEndgame = renderEndgame;
if (typeof renderEndgameTeamCard !== 'undefined') window.renderEndgameTeamCard = renderEndgameTeamCard;
if (typeof renderHomeResetRadar !== 'undefined') window.renderHomeResetRadar = renderHomeResetRadar;
if (typeof renderTeamMatcher !== 'undefined') window.renderTeamMatcher = renderTeamMatcher;
if (typeof teamMatcherFilterState !== 'undefined') window.teamMatcherFilterState = teamMatcherFilterState;


window.addEventListener("app:languageChanged", () => {
    ["hsr", "genshin", "zzz"].forEach(gId => {
        if (typeof cachedEndgameData !== "undefined" && cachedEndgameData[gId]) {
            renderEndgame(gId, cachedEndgameData[gId]);
        }
    });
    const homePane = document.getElementById("tab-home");
    if (homePane && homePane.classList.contains("active")) {
        loadHomeResetRadar(true);
    } else if (_cachedResetRadar) {
        window._dirtyLangTabs = window._dirtyLangTabs || {};
        window._dirtyLangTabs.homeRadar = true;
    }
});
