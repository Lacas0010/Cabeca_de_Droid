// ==========================================================================
// Módulo: quick_search.js
// Busca Rápida Global (Ctrl+K / Cmd+K) - Cabeça de Droid (Vanilla ES6)
// ==========================================================================

(function () {
    "use strict";

    let _isOpen = false;
    let _activeIndex = 0;
    let _filteredItems = [];
    let _lastFocusedEl = null;

    const GAME_META = {
        hsr: { label: "HSR", full: "Honkai: Star Rail", icon: "/assets/hsr_icon.png" },
        genshin: { label: "Genshin", full: "Genshin Impact", icon: "/assets/genshin_icon.png" },
        zzz: { label: "ZZZ", full: "Zenless Zone Zero", icon: "/assets/zzz_icon.png" },
    };

    const ENDGAME_MODES_INDEX = [
        {
            gameId: "hsr",
            modeId: "moc",
            titlePt: "Caos da Memória (MoC)",
            titleEn: "Memory of Chaos (MoC)",
            icon: "/assets/endgame/hsr_moc.png",
            fallbackFa: "fa-trophy",
            keywords: "moc caos memoria memory chaos hsr star rail endgame",
        },
        {
            gameId: "hsr",
            modeId: "pure_fiction",
            titlePt: "Ficção Pura",
            titleEn: "Pure Fiction",
            icon: "/assets/endgame/hsr_pure_fiction.png",
            fallbackFa: "fa-wand-magic-sparkles",
            keywords: "pf ficcao pura pure fiction hsr star rail endgame",
        },
        {
            gameId: "hsr",
            modeId: "apocalyptic_shadow",
            titlePt: "Sombra Apocalíptica",
            titleEn: "Apocalyptic Shadow",
            icon: "/assets/endgame/hsr_apocalyptic_shadow.png",
            fallbackFa: "fa-skull",
            keywords: "as sombra apocaliptica apocalyptic shadow hsr star rail endgame",
        },
        {
            gameId: "genshin",
            modeId: "spiral_abyss",
            titlePt: "Abismo Espiral",
            titleEn: "Spiral Abyss",
            icon: "/assets/endgame/genshin_spiral_abyss.png",
            fallbackFa: "fa-dungeon",
            keywords: "abyss abismo espiral spiral genshin impact endgame",
        },
        {
            gameId: "genshin",
            modeId: "imaginarium_theater",
            titlePt: "Teatro Imaginário",
            titleEn: "Imaginarium Theater",
            icon: "/assets/endgame/genshin_imaginarium_theater.png",
            fallbackFa: "fa-masks-theater",
            keywords: "teatro imaginario imaginarium theater genshin impact endgame",
        },
        {
            gameId: "zzz",
            modeId: "shiyu_defense",
            titlePt: "Defesa Shiyu",
            titleEn: "Shiyu Defense",
            icon: "/assets/endgame/zzz_shiyu_defense.png",
            fallbackFa: "fa-shield-halved",
            keywords: "shiyu defesa defense zzz zenless zone zero endgame",
        },
        {
            gameId: "zzz",
            modeId: "deadly_assault",
            titlePt: "Assalto Mortal",
            titleEn: "Deadly Assault",
            icon: "/assets/endgame/zzz_deadly_assault.png",
            fallbackFa: "fa-fire-flame-curved",
            keywords: "da assalto mortal deadly assault investida fatal zzz zenless endgame",
        },
    ];

    const APP_TABS_INDEX = [
        { tab: "home", titlePt: "Início (Dashboard)", titleEn: "Home (Dashboard)", subPt: "Monitor de Energia, Daily Notes e Radar de Resets", subEn: "Energy Monitor, Daily Notes & Reset Radar", fa: "fa-house", color: "#38bdf8", keywords: "home inicio dashboard energia resina radar resets daily notes" },
        { tab: "genshin", titlePt: "Genshin Impact", titleEn: "Genshin Impact", subPt: "Galeria, Builds, Artefatos e Endgame", subEn: "Gallery, Builds, Artifacts & Endgame", img: "/assets/genshin_icon.png", keywords: "genshin impact roster galeria personagens artefatos" },
        { tab: "hsr", titlePt: "Honkai: Star Rail", titleEn: "Honkai: Star Rail", subPt: "Galeria, Relíquias, Cones de Luz e Endgame", subEn: "Gallery, Relics, Light Cones & Endgame", img: "/assets/hsr_icon.png", keywords: "hsr honkai star rail roster galeria reliquias cones" },
        { tab: "zzz", titlePt: "Zenless Zone Zero", titleEn: "Zenless Zone Zero", subPt: "Agentes, Discos, Motores-W e Endgame", subEn: "Agents, Discs, W-Engines & Endgame", img: "/assets/zzz_icon.png", keywords: "zzz zenless zone zero agentes discos motores" },
        { tab: "gacha", titlePt: "Simulador de Gacha", titleEn: "Gacha Simulator", subPt: "Banners Ativos, Monte Carlo, Forecast e Histórico", subEn: "Active Banners, Monte Carlo, Forecast & History", fa: "fa-wand-magic-sparkles", color: "#f59e0b", keywords: "gacha simulador banner pity forecast metas tiros gemas jades" },
        { tab: "farm", titlePt: "Central de Farm", titleEn: "Farm Hub", subPt: "Domínios abertos hoje e checklist diário", subEn: "Today's open domains & daily checklist", fa: "fa-wheat-awn", color: "#10b981", keywords: "farm central dominios materiais talentos hoje" },
        { tab: "trash", titlePt: "Filtro de Descarte", titleEn: "Gear Discard Filter", subPt: "Identificar relíquias, artefatos e discos descartáveis", subEn: "Spot fodder relics, artifacts & drive discs", fa: "fa-trash-can", color: "#ef4444", keywords: "trash descarte lixo filtro artefatos reliquias discos" },
        { tab: "luck", titlePt: "Índice de Sorte", titleEn: "Luck Index", subPt: "Eficiência de rolamentos e estatísticas de pulls", subEn: "Roll efficiency & pull statistics", fa: "fa-clover", color: "#10b981", keywords: "luck sorte eficiencia pulls 50/50 historico" },
        { tab: "audit", titlePt: "Tier List & Audit", titleEn: "Tier List & Audit", subPt: "Auditoria de builds e ranking do metagame", subEn: "Build audit & metagame tier list", fa: "fa-trophy", color: "#a855f7", keywords: "tier list audit auditoria meta ranking builds" },
        { tab: "history", titlePt: "Linha do Tempo (Evolução)", titleEn: "Timeline (Evolution)", subPt: "Histórico de evolução da conta e builds", subEn: "Account & build progression history", fa: "fa-chart-line", color: "#ec4899", keywords: "history linha tempo evolucao snapshot historico" },
        { tab: "codes", titlePt: "Códigos Promocionais", titleEn: "Redeem Codes", subPt: "Códigos ativos e resgate automático", subEn: "Active promo codes & auto-redeem", fa: "fa-gift", color: "#f59e0b", keywords: "codes codigos promocionais gemas jades policromos resgate" },
        { tab: "config", titlePt: "Configurações", titleEn: "Settings", subPt: "Contas HoYoLAB, credenciais e webhooks", subEn: "HoYoLAB accounts, credentials & webhooks", fa: "fa-gear", color: "#94a3b8", keywords: "config configuracoes settings cookies conta uid pin webhook" },
        { tab: "help", titlePt: "Como Usar", titleEn: "How to Use", subPt: "Guia rápido e segurança do aplicativo", subEn: "Quick guide & app security", fa: "fa-circle-question", color: "#38bdf8", keywords: "help ajuda tutorial como usar seguranca" },
    ];

    function _norm(str) {
        return String(str || "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .trim();
    }

    function _esc(str) {
        return String(str == null ? "" : str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");
    }

    function _highlight(text, query) {
        const safeText = _esc(text);
        const q = _norm(query);
        if (!q) return safeText;
        const normText = _norm(text);
        const idx = normText.indexOf(q);
        if (idx < 0) return safeText;
        const orig = String(text || "");
        const before = orig.slice(0, idx);
        const match = orig.slice(idx, idx + query.trim().length);
        const after = orig.slice(idx + query.trim().length);
        return `${_esc(before)}<mark class="qs-match">${_esc(match)}</mark>${_esc(after)}`;
    }

    function _scoreItem(item, normQuery) {
        if (!normQuery) return item.defaultPriority || 0;
        const title = _norm(item.title);
        const sub = _norm(item.subtitle);
        const kw = _norm(item.keywords);

        if (title === normQuery) return 1000;
        if (title.startsWith(normQuery)) return 850;
        if (title.split(/[\s\-•()]+/).some(w => w.startsWith(normQuery))) return 720;
        if (title.includes(normQuery)) return 600;
        if (sub.includes(normQuery)) return 420;
        if (kw.includes(normQuery)) return 320;

        // Suporte a busca multi-palavra (ex: "hsr acheron" ou "genshin teatro")
        const tokens = normQuery.split(/\s+/).filter(Boolean);
        if (tokens.length > 1) {
            const haystack = `${title} ${sub} ${kw}`;
            if (tokens.every(t => haystack.includes(t))) {
                return 520;
            }
        }
        return -1;
    }

    function _buildCatalog(isEn) {
        const items = [];

        // 1. Personagens dinâmicos do Roster (globalRoster)
        const rosterMap = (typeof globalRoster !== "undefined" && globalRoster) ? globalRoster : (window.globalRoster || {});
        ["hsr", "genshin", "zzz"].forEach(gid => {
            const chars = Array.isArray(rosterMap[gid]) ? rosterMap[gid] : [];
            const gMeta = GAME_META[gid];
            chars.forEach(char => {
                if (!char || !char.name) return;
                const displayName = typeof window.formatCharacterName === "function"
                    ? window.formatCharacterName(char.name)
                    : char.name;
                const lvl = char.level ? `${isEn ? "Lv." : "Nv."}${char.level}` : "";
                const rank = char.rank_str || "";
                const elem = char.element || "";
                const role = char.path || char.weapon_type || char.specialty || "";
                const subParts = [gMeta.label, lvl, rank, elem, role].filter(Boolean);
                let iconUrl = char.icon || gMeta.icon;
                if (iconUrl.startsWith("http://") || iconUrl.startsWith("https://")) {
                    iconUrl = `/api/proxy_image?url=${encodeURIComponent(iconUrl)}&w=64&format=webp`;
                }

                items.push({
                    category: "character",
                    categoryLabel: isEn ? "Characters (Build Inspector)" : "Personagens (Build Inspector)",
                    gameId: gid,
                    gameLabel: gMeta.label,
                    title: displayName,
                    subtitle: subParts.join(" · "),
                    iconType: "avatar",
                    icon: iconUrl,
                    fallbackIcon: gMeta.icon,
                    rarity: char.rarity,
                    keywords: `${char.name} ${displayName} ${gid} ${gMeta.full} ${elem} ${role} ${rank} build inspector`,
                    defaultPriority: (Number(char.rarity) === 5 || String(char.rarity).toUpperCase() === "S") ? 35 : 20,
                    action: () => {
                        const navBtn = document.querySelector(`.nav-btn[data-tab="${gid}"]`);
                        if (navBtn) navBtn.click();
                        if (typeof window.activateGameSubview === "function") {
                            const section = document.getElementById(`tab-${gid}`);
                            const tabsEl = section?.querySelector(`sakuga-tabs.sk-game-subnav[data-game="${gid}"]`);
                            if (tabsEl) tabsEl.selected = 0;
                            window.activateGameSubview(gid, "gallery");
                        }
                        if (typeof window.inspectCharacter === "function") {
                            window.inspectCharacter(gid, char);
                        }
                    },
                });
            });
        });

        // 2. Os 7 Modos de Endgame
        ENDGAME_MODES_INDEX.forEach((m, idx) => {
            const gMeta = GAME_META[m.gameId];
            const title = isEn ? m.titleEn : m.titlePt;
            items.push({
                category: "endgame",
                categoryLabel: isEn ? "Endgame Modes" : "Modos de Endgame",
                gameId: m.gameId,
                gameLabel: gMeta.label,
                title,
                subtitle: `${gMeta.full} · ${isEn ? "Endgame Challenges" : "Desafios de Endgame"}`,
                iconType: "mode",
                icon: m.icon,
                fallbackFa: m.fallbackFa,
                keywords: `${m.titlePt} ${m.titleEn} ${m.keywords}`,
                defaultPriority: 80 - idx,
                action: () => {
                    if (typeof window.navigateToEndgameMode === "function") {
                        window.navigateToEndgameMode(m.gameId, m.modeId);
                    } else {
                        document.querySelector(`.nav-btn[data-tab="${m.gameId}"]`)?.click();
                    }
                },
            });
        });

        // 3. Abas e Ferramentas da Aplicação
        APP_TABS_INDEX.forEach((t, idx) => {
            items.push({
                category: "tab",
                categoryLabel: isEn ? "Tabs & Tools" : "Abas & Ferramentas",
                gameId: ["hsr", "genshin", "zzz"].includes(t.tab) ? t.tab : "",
                gameLabel: isEn ? "Tab" : "Aba",
                title: isEn ? t.titleEn : t.titlePt,
                subtitle: isEn ? t.subEn : t.subPt,
                iconType: t.img ? "img" : "fa",
                icon: t.img || "",
                fallbackFa: t.fa || "fa-compass",
                faColor: t.color || "#38bdf8",
                keywords: `${t.titlePt} ${t.titleEn} ${t.keywords}`,
                defaultPriority: 60 - idx,
                action: () => {
                    const navBtn = document.querySelector(`.nav-btn[data-tab="${t.tab}"]`);
                    if (navBtn) navBtn.click();
                },
            });
        });

        return items;
    }

    function _renderIcon(item) {
        if (item.iconType === "avatar") {
            const rarityCls = (Number(item.rarity) === 5 || String(item.rarity).toUpperCase() === "S") ? "is-5star" : "is-4star";
            return `
                <span class="qs-item-icon is-avatar ${rarityCls}">
                    <img src="${_esc(item.icon)}" alt="" width="32" height="32" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='${_esc(item.fallbackIcon)}';" />
                </span>
            `;
        }
        if (item.iconType === "mode" || item.iconType === "img") {
            const fbFa = item.fallbackFa || "fa-award";
            return `
                <span class="qs-item-icon is-mode ${item.gameId ? `game-${_esc(item.gameId)}` : ""}">
                    <img src="${_esc(item.icon)}" alt="" width="24" height="24" loading="lazy" decoding="async" onerror="this.style.display='none'; if (this.nextElementSibling) this.nextElementSibling.style.display='inline-flex';" />
                    <i class="fa-solid ${fbFa} qs-icon-fallback" style="display:none;"></i>
                </span>
            `;
        }
        return `
            <span class="qs-item-icon is-fa">
                <i class="fa-solid ${item.fallbackFa || "fa-compass"}" style="color: ${_esc(item.faColor || "#38bdf8")};"></i>
            </span>
        `;
    }

    function _renderResults(query) {
        const listEl = document.getElementById("quick-search-results");
        const countEl = document.getElementById("quick-search-count");
        const clearBtn = document.getElementById("quick-search-clear-btn");
        if (!listEl) return;

        const isEn = Boolean(window.isEn);
        const rawQuery = String(query || "");
        const normQuery = _norm(rawQuery);
        if (clearBtn) clearBtn.style.display = rawQuery.trim() ? "inline-flex" : "none";

        const catalog = _buildCatalog(isEn);
        let ranked = [];

        if (!normQuery) {
            // Sugestões iniciais organizadas: Modos Endgame (4), Abas principais (5), Personagens do Roster (6)
            const endgames = catalog.filter(i => i.category === "endgame").slice(0, 4);
            const tabs = catalog.filter(i => i.category === "tab").slice(0, 5);
            const chars = catalog.filter(i => i.category === "character").slice(0, 6);
            ranked = [...chars, ...endgames, ...tabs];
        } else {
            ranked = catalog
                .map(item => ({ item, score: _scoreItem(item, normQuery) }))
                .filter(entry => entry.score >= 0)
                .sort((a, b) => b.score - a.score || a.item.title.localeCompare(b.item.title))
                .slice(0, 24)
                .map(entry => entry.item);
        }

        _filteredItems = ranked;
        _activeIndex = 0;

        if (countEl) {
            countEl.textContent = normQuery
                ? (isEn ? `${ranked.length} result(s)` : `${ranked.length} resultado(s)`)
                : (isEn ? "Quick suggestions" : "Sugestões rápidas");
        }

        if (ranked.length === 0) {
            listEl.innerHTML = `
                <div class="qs-empty-state">
                    <i class="fa-solid fa-magnifying-glass"></i>
                    <p>${isEn ? `No matches found for "${_esc(rawQuery.trim())}".` : `Nenhum resultado encontrado para "${_esc(rawQuery.trim())}".`}</p>
                    <span>${isEn ? "Try searching by character name, game (HSR, Genshin, ZZZ), tab, or endgame mode (MoC, Abyss, Shiyu)." : "Tente buscar pelo nome de um personagem, jogo (HSR, Genshin, ZZZ), aba ou modo endgame (MoC, Abismo, Shiyu)."}</span>
                </div>
            `;
            return;
        }

        // Agrupa mantendo ordem por categoria para leitura instantânea
        const groupOrder = ["character", "endgame", "tab"];
        const grouped = new Map();
        groupOrder.forEach(cat => grouped.set(cat, []));
        ranked.forEach((item) => {
            if (!grouped.has(item.category)) grouped.set(item.category, []);
            grouped.get(item.category).push(item);
        });

        // Reordena _filteredItems exatamente na ordem visual renderizada para sincronizar ↑/↓ e Enter
        const orderedFlat = [];
        let html = "";
        grouped.forEach((groupItems) => {
            if (!groupItems.length) return;
            html += `<div class="qs-group-label">${_esc(groupItems[0].categoryLabel)}</div>`;
            groupItems.forEach((item) => {
                const idx = orderedFlat.length;
                orderedFlat.push(item);
                const activeCls = idx === 0 ? "active" : "";
                const badgeCls = item.gameId ? `game-${_esc(item.gameId)}` : "is-tab";
                html += `
                    <button type="button"
                        class="quick-search-item ${activeCls}"
                        role="option"
                        aria-selected="${idx === 0 ? "true" : "false"}"
                        data-qs-idx="${idx}">
                        ${_renderIcon(item)}
                        <div class="qs-item-body">
                            <span class="qs-item-title">${_highlight(item.title, rawQuery)}</span>
                            <span class="qs-item-sub">${_esc(item.subtitle)}</span>
                        </div>
                        <span class="qs-item-badge ${badgeCls}">${_esc(item.gameLabel)}</span>
                        <span class="qs-item-enter" aria-hidden="true"><i class="fa-solid fa-turn-down fa-rotate-90"></i></span>
                    </button>
                `;
            });
        });

        _filteredItems = orderedFlat;
        listEl.innerHTML = html;

        listEl.querySelectorAll(".quick-search-item").forEach((btn) => {
            btn.addEventListener("mouseenter", () => {
                const idx = parseInt(btn.getAttribute("data-qs-idx"), 10);
                if (!Number.isNaN(idx)) _setActiveIndex(idx, false);
            });
            btn.addEventListener("click", () => {
                const idx = parseInt(btn.getAttribute("data-qs-idx"), 10);
                if (!Number.isNaN(idx)) _executeItem(idx);
            });
        });
    }

    function _setActiveIndex(nextIdx, shouldScroll = true) {
        const listEl = document.getElementById("quick-search-results");
        if (!listEl || !_filteredItems.length) return;
        const total = _filteredItems.length;
        _activeIndex = ((nextIdx % total) + total) % total;

        listEl.querySelectorAll(".quick-search-item").forEach((el) => {
            const idx = parseInt(el.getAttribute("data-qs-idx"), 10);
            const isActive = idx === _activeIndex;
            el.classList.toggle("active", isActive);
            el.setAttribute("aria-selected", isActive ? "true" : "false");
            if (isActive && shouldScroll) {
                el.scrollIntoView({ block: "nearest" });
            }
        });
    }

    function _executeItem(idx) {
        const item = _filteredItems[idx];
        if (!item || typeof item.action !== "function") return;
        closeQuickSearch(false);
        try {
            item.action();
        } catch (err) {
            console.error("[QUICK-SEARCH] Erro ao executar ação:", err);
        }
    }

    function openQuickSearch(initialQuery = "") {
        const overlay = document.getElementById("quick-search-overlay");
        const input = document.getElementById("quick-search-input");
        if (!overlay || !input) return;

        _lastFocusedEl = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        _isOpen = true;
        overlay.classList.add("open");
        overlay.setAttribute("aria-hidden", "false");

        if (window.SakugaFX?.clearTransient) {
            window.SakugaFX.clearTransient();
        }

        input.value = initialQuery;
        _renderResults(initialQuery);
        requestAnimationFrame(() => {
            input.focus();
            input.select();
        });
    }

    function closeQuickSearch(restoreFocus = true) {
        const overlay = document.getElementById("quick-search-overlay");
        if (!overlay || !_isOpen) return;
        _isOpen = false;
        overlay.classList.remove("open");
        overlay.setAttribute("aria-hidden", "true");
        if (restoreFocus && _lastFocusedEl && typeof _lastFocusedEl.focus === "function") {
            try {
                _lastFocusedEl.focus();
            } catch (_) {}
        }
        _lastFocusedEl = null;
    }

    function setupQuickSearch() {
        const overlay = document.getElementById("quick-search-overlay");
        const input = document.getElementById("quick-search-input");
        const clearBtn = document.getElementById("quick-search-clear-btn");
        const triggerDesktop = document.getElementById("btn-open-quick-search");
        const triggerMobile = document.getElementById("btn-open-quick-search-mobile");
        if (!overlay || !input || overlay.dataset.bound === "true") return;
        overlay.dataset.bound = "true";

        if (triggerDesktop) {
            triggerDesktop.addEventListener("click", () => openQuickSearch(""));
        }
        if (triggerMobile) {
            triggerMobile.addEventListener("click", () => openQuickSearch(""));
        }
        if (clearBtn) {
            clearBtn.addEventListener("click", () => {
                input.value = "";
                _renderResults("");
                input.focus();
            });
        }

        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) closeQuickSearch(true);
        });

        input.addEventListener("input", () => {
            _renderResults(input.value);
        });

        input.addEventListener("keydown", (e) => {
            if (e.key === "ArrowDown") {
                e.preventDefault();
                _setActiveIndex(_activeIndex + 1, true);
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                _setActiveIndex(_activeIndex - 1, true);
            } else if (e.key === "Enter") {
                if (_filteredItems.length > 0) {
                    e.preventDefault();
                    _executeItem(_activeIndex);
                }
            } else if (e.key === "Escape") {
                e.preventDefault();
                closeQuickSearch(true);
            }
        });

        document.addEventListener("keydown", (e) => {
            const isShortcut = (e.ctrlKey || e.metaKey) && String(e.key || "").toLowerCase() === "k";
            if (isShortcut) {
                e.preventDefault();
                if (_isOpen) {
                    closeQuickSearch(true);
                } else {
                    openQuickSearch("");
                }
                return;
            }
            if (e.key === "Escape" && _isOpen) {
                e.preventDefault();
                closeQuickSearch(true);
            }
        });

        window.addEventListener("app:languageChanged", () => {
            if (_isOpen) {
                _renderResults(input.value);
            }
        });
    }

    window.setupQuickSearch = setupQuickSearch;
    window.openQuickSearch = openQuickSearch;
    window.closeQuickSearch = closeQuickSearch;
})();
