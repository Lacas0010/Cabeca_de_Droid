// ==========================================================================
// Módulo: gacha_sim.js
// Cabeça de Droid - Vanilla ES6 Module
// ==========================================================================

// ==========================================
// SIMULADOR DE GACHA ULTRA PREMIUM LOGIC
// ==========================================

window.GACHA_TERMS = {
    genshin: {
        gameName: "Genshin Impact",
        currency: "Gemas",
        gemCostPerPull: 160,
        term: "Constelação",
        termPlural: "Constelações",
        prefix: "C",
        unownedLabel: "Não possui (0 cópias)",
        ranks: [
            { val: 0, label: "C0 (Personagem Base)" },
            { val: 1, label: "C1 (1ª Constelação)" },
            { val: 2, label: "C2 (2ª Constelação)" },
            { val: 3, label: "C3 (3ª Constelação)" },
            { val: 4, label: "C4 (4ª Constelação)" },
            { val: 5, label: "C5 (5ª Constelação)" },
            { val: 6, label: "C6 (Constelação Máxima)" }
        ],
        character: {
            term: "Constelação",
            termPlural: "Constelações",
            prefix: "C",
            unownedLabel: "Não possui (0 cópias)",
            maxPity: 89,
            pityTitle: "Pity de Personagem (0-89):",
            guaranteedNormal: "50/50 Ativo (Normal)",
            guaranteedWon: "Garantido (Perdeu 50/50 anterior)",
            ranks: [
                { val: 0, label: "C0 (Personagem Base)" },
                { val: 1, label: "C1 (1ª Constelação)" },
                { val: 2, label: "C2 (2ª Constelação)" },
                { val: 3, label: "C3 (3ª Constelação)" },
                { val: 4, label: "C4 (4ª Constelação)" },
                { val: 5, label: "C5 (5ª Constelação)" },
                { val: 6, label: "C6 (Constelação Máxima)" }
            ]
        },
        weapon: {
            term: "Refinamento",
            termPlural: "Refinamentos",
            prefix: "R",
            unownedLabel: "Não possui a arma (0 cópias)",
            maxPity: 79,
            pityTitle: "Pity de Arma (0-79):",
            guaranteedNormal: "Caminho Divino / 75/25 Ativo",
            guaranteedWon: "Garantido (Destino / 100%)",
            ranks: [
                { val: 0, label: "R1 (Arma Base)" },
                { val: 1, label: "R2 (Refinamento 2)" },
                { val: 2, label: "R3 (Refinamento 3)" },
                { val: 3, label: "R4 (Refinamento 4)" },
                { val: 4, label: "R5 (Refinamento Máximo)" }
            ]
        }
    },
    hsr: {
        gameName: "Honkai: Star Rail",
        currency: "Jades",
        gemCostPerPull: 160,
        term: "Eidolon",
        termPlural: "Eidolons",
        prefix: "E",
        unownedLabel: "Não possui (0 cópias)",
        ranks: [
            { val: 0, label: "E0 (Personagem Base)" },
            { val: 1, label: "E1 (1º Eidolon)" },
            { val: 2, label: "E2 (2º Eidolon)" },
            { val: 3, label: "E3 (3º Eidolon)" },
            { val: 4, label: "E4 (4º Eidolon)" },
            { val: 5, label: "E5 (5º Eidolon)" },
            { val: 6, label: "E6 (Eidolon Máximo)" }
        ],
        character: {
            term: "Eidolon",
            termPlural: "Eidolons",
            prefix: "E",
            unownedLabel: "Não possui (0 cópias)",
            maxPity: 89,
            pityTitle: "Pity de Personagem (0-89):",
            guaranteedNormal: "50/50 Ativo (Normal)",
            guaranteedWon: "Garantido (Perdeu 50/50 anterior)",
            ranks: [
                { val: 0, label: "E0 (Personagem Base)" },
                { val: 1, label: "E1 (1º Eidolon)" },
                { val: 2, label: "E2 (2º Eidolon)" },
                { val: 3, label: "E3 (3º Eidolon)" },
                { val: 4, label: "E4 (4º Eidolon)" },
                { val: 5, label: "E5 (5º Eidolon)" },
                { val: 6, label: "E6 (Eidolon Máximo)" }
            ]
        },
        weapon: {
            term: "Sobreposição",
            termPlural: "Sobreposições",
            prefix: "S",
            unownedLabel: "Não possui o Cone de Luz (0 cópias)",
            maxPity: 79,
            pityTitle: "Pity de Cone de Luz (0-79):",
            guaranteedNormal: "75/25 Ativo (Normal)",
            guaranteedWon: "Garantido (Perdeu 75/25 anterior)",
            ranks: [
                { val: 0, label: "S1 (Cone de Luz Base)" },
                { val: 1, label: "S2 (Sobreposição 2)" },
                { val: 2, label: "S3 (Sobreposição 3)" },
                { val: 3, label: "S4 (Sobreposição 4)" },
                { val: 4, label: "S5 (Sobreposição Máxima)" }
            ]
        }
    },
    zzz: {
        gameName: "Zenless Zone Zero",
        currency: "Policromos",
        gemCostPerPull: 160,
        term: "Mindscape Cinema",
        termPlural: "Mindscapes",
        prefix: "M",
        unownedLabel: "Não possui (0 cópias)",
        ranks: [
            { val: 0, label: "M0 (Agente Base)" },
            { val: 1, label: "M1 (1º Cinema)" },
            { val: 2, label: "M2 (2º Cinema)" },
            { val: 3, label: "M3 (3º Cinema)" },
            { val: 4, label: "M4 (4º Cinema)" },
            { val: 5, label: "M5 (5º Cinema)" },
            { val: 6, label: "M6 (Mindscape Máximo)" }
        ],
        character: {
            term: "Mindscape Cinema",
            termPlural: "Mindscapes",
            prefix: "M",
            unownedLabel: "Não possui (0 cópias)",
            maxPity: 89,
            pityTitle: "Pity de Agente (0-89):",
            guaranteedNormal: "50/50 Ativo (Normal)",
            guaranteedWon: "Garantido (Perdeu 50/50 anterior)",
            ranks: [
                { val: 0, label: "M0 (Agente Base)" },
                { val: 1, label: "M1 (1º Cinema)" },
                { val: 2, label: "M2 (2º Cinema)" },
                { val: 3, label: "M3 (3º Cinema)" },
                { val: 4, label: "M4 (4º Cinema)" },
                { val: 5, label: "M5 (5º Cinema)" },
                { val: 6, label: "M6 (Mindscape Máximo)" }
            ]
        },
        weapon: {
            term: "Modificação de Motor",
            termPlural: "Modificações",
            prefix: "★",
            unownedLabel: "Não possui o Motor-W (0 cópias)",
            maxPity: 79,
            pityTitle: "Pity de Motor-W (0-79):",
            guaranteedNormal: "75/25 Ativo (Normal)",
            guaranteedWon: "Garantido (Perdeu 75/25 anterior)",
            ranks: [
                { val: 0, label: "★1 (Motor-W Base)" },
                { val: 1, label: "★2 (Modificação 2)" },
                { val: 2, label: "★3 (Modificação 3)" },
                { val: 3, label: "★4 (Modificação 4)" },
                { val: 4, label: "★5 (Modificação Máxima)" }
            ]
        }
    }
};

window.getGachaTerms = function(gameId, bannerType = "character") {
    const g = window.GACHA_TERMS[gameId] || window.GACHA_TERMS.genshin;
    const bType = (bannerType || "character").toLowerCase();
    const typeTerms = g[bType] || g.character || g;
    return {
        gameName: g.gameName,
        currency: g.currency,
        gemCostPerPull: g.gemCostPerPull,
        term: typeTerms.term,
        termPlural: typeTerms.termPlural,
        prefix: typeTerms.prefix,
        unownedLabel: typeTerms.unownedLabel,
        maxPity: typeTerms.maxPity || 89,
        pityTitle: typeTerms.pityTitle || "Pity Atual (0-89):",
        guaranteedNormal: typeTerms.guaranteedNormal || "50/50 Ativo (Normal)",
        guaranteedWon: typeTerms.guaranteedWon || "Garantido",
        ranks: typeTerms.ranks || []
    };
};

window.gachaState = {
    gameId: "genshin",
    bannerType: "character",
    charList: [],
    selectedChar: null
};

window.addGachaPulls = function(amount) {
    const pullInput = document.getElementById("tab-gacha-pulls");
    if (!pullInput) return;
    const current = parseInt(pullInput.value) || 0;
    pullInput.value = current + amount;
    window.updateGachaGemConversion();
};

window.updateGachaGemConversion = function() {
    const gameId = document.getElementById("tab-gacha-game-select")?.value || "genshin";
    const terms = window.GACHA_TERMS[gameId] || window.GACHA_TERMS.genshin;
    const pulls = parseInt(document.getElementById("tab-gacha-pulls")?.value) || 0;
    const gems = pulls * terms.gemCostPerPull;
    const convertLbl = document.getElementById("gacha-gems-convert-lbl");
    if (convertLbl) {
        convertLbl.innerText = `(Equivale a ${gems.toLocaleString()} ${terms.currency})`;
    }
};

window.initGachaSimulator = async function() {
    const gamePills = document.querySelectorAll("#gacha-game-pills .gacha-game-pill");
    const gameSelectHidden = document.getElementById("tab-gacha-game-select");
    const simTypePills = document.querySelectorAll("#gacha-sim-type-pills .sim-type-btn");
    const bannerTypeHidden = document.getElementById("tab-gacha-banner-type");
    const charSelect = document.getElementById("tab-gacha-char-select");
    const currentRankSelect = document.getElementById("tab-gacha-current-rank");
    const pullsInput = document.getElementById("tab-gacha-pulls");
    const runBtn = document.getElementById("tab-btn-run-gacha-sim");

    if (pullsInput) {
        pullsInput.addEventListener("input", window.updateGachaGemConversion);
    }

    // Toggle de Jogos (Genshin, HSR, ZZZ)
    gamePills.forEach(pill => {
        pill.addEventListener("click", async () => {
            gamePills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            const gameId = pill.dataset.game;
            if (gameSelectHidden) gameSelectHidden.value = gameId;
            window.gachaState.gameId = gameId;
            const bType = bannerTypeHidden ? bannerTypeHidden.value : "character";
            window.updateGachaLabels(gameId, bType);
            await window.loadGachaCharacters(gameId, bType);
            window.updateGachaGemConversion();
        });
    });

    // Toggle de Categoria de Banner (Personagens vs Armas/Cones/Motores-W)
    simTypePills.forEach(pill => {
        pill.addEventListener("click", async () => {
            simTypePills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            const bType = pill.dataset.type || "character";
            if (bannerTypeHidden) bannerTypeHidden.value = bType;
            window.gachaState.bannerType = bType;
            const gameId = gameSelectHidden ? gameSelectHidden.value : "genshin";
            window.updateGachaLabels(gameId, bType);
            await window.loadGachaCharacters(gameId, bType);
        });
    });

    if (charSelect) {
        charSelect.addEventListener("change", () => {
            const charName = charSelect.value;
            window.updateGachaCharPreview(charName);
        });
    }

    if (currentRankSelect) {
        currentRankSelect.addEventListener("change", () => {
            window.updateTargetRankOptions();
        });
    }

    if (runBtn) {
        runBtn.onclick = window.runGachaSimulation;
    }

    const wishBtn = document.getElementById("tab-btn-open-wish-anim");
    if (wishBtn) {
        wishBtn.onclick = (e) => {
            if (e) e.preventDefault();
            window.startWishAnimation(1);
        };
    }

    window.updateGachaLabels("genshin", "character");
    await window.loadGachaCharacters("genshin", "character");
    window.updateGachaGemConversion();
};

window.updateGachaLabels = function(gameId, bannerType = "character") {
    const terms = window.getGachaTerms(gameId, bannerType);
    
    const lblCurrent = document.getElementById("lbl-gacha-current-rank");
    const lblTarget = document.getElementById("lbl-gacha-target-rank");
    if (lblCurrent) lblCurrent.innerText = `${terms.term} Atual:`;
    if (lblTarget) lblTarget.innerText = `Meta de ${terms.term}:`;

    const lblPity = document.getElementById("lbl-gacha-pity-title");
    if (lblPity) lblPity.innerText = terms.pityTitle;

    const lblGuaranteed = document.getElementById("lbl-gacha-guaranteed-title");
    if (lblGuaranteed) {
        lblGuaranteed.innerText = bannerType === "weapon" ? "Garantido / Caminho Divino:" : "Estado do 50/50:";
    }

    const pityInput = document.getElementById("tab-gacha-pity");
    if (pityInput) {
        pityInput.max = String(terms.maxPity);
    }

    const guaranteedSelect = document.getElementById("tab-gacha-guaranteed");
    if (guaranteedSelect) {
        const curVal = guaranteedSelect.value;
        guaranteedSelect.innerHTML = `
            <option value="false">${terms.guaranteedNormal}</option>
            <option value="true">${terms.guaranteedWon}</option>
        `;
        guaranteedSelect.value = curVal;
    }

    const currentRankSelect = document.getElementById("tab-gacha-current-rank");
    if (currentRankSelect) {
        currentRankSelect.innerHTML = `<option value="-1">${terms.unownedLabel}</option>`;
        terms.ranks.forEach(r => {
            const opt = document.createElement("option");
            opt.value = r.val;
            opt.innerText = r.label;
            currentRankSelect.appendChild(opt);
        });
    }

    window.updateTargetRankOptions();
};

window.updateTargetRankOptions = function() {
    const gameId = document.getElementById("tab-gacha-game-select")?.value || "genshin";
    const bannerType = document.getElementById("tab-gacha-banner-type")?.value || "character";
    const terms = window.getGachaTerms(gameId, bannerType);
    const currentRank = parseInt(document.getElementById("tab-gacha-current-rank")?.value ?? -1);
    const targetRankSelect = document.getElementById("tab-gacha-target-rank");

    if (!targetRankSelect) return;
    const prevTargetVal = parseInt(targetRankSelect.value ?? (bannerType === "weapon" ? 4 : 6));

    targetRankSelect.innerHTML = "";
    terms.ranks.forEach(r => {
        if (r.val > currentRank || (currentRank === -1 && r.val >= 0)) {
            const opt = document.createElement("option");
            opt.value = r.val;
            
            let extraStr = "";
            if (currentRank < 0) {
                extraStr = r.val === 0 
                    ? (bannerType === "weapon" ? " (Garantir 1ª Arma/Cone)" : " (Garantir 1º Personagem)") 
                    : ` (+${r.val + 1} cópias)`;
            } else {
                const needed = r.val - currentRank;
                extraStr = needed === 1 ? " (+1 cópia adicional)" : ` (+${needed} cópias adicionais)`;
            }
            opt.innerText = `${terms.prefix}${bannerType === "weapon" ? r.val + 1 : r.val}${extraStr}`;
            targetRankSelect.appendChild(opt);
        }
    });

    if (prevTargetVal > currentRank) {
        targetRankSelect.value = prevTargetVal;
    } else {
        const lastOpt = targetRankSelect.options[targetRankSelect.options.length - 1];
        if (lastOpt) targetRankSelect.value = lastOpt.value;
    }
};

window.loadGachaCharacters = async function(gameId, requestedBannerType = null) {
    const charSelect = document.getElementById("tab-gacha-char-select");
    const lblTargetItem = document.getElementById("lbl-gacha-target-item");
    if (!charSelect) return;

    const bannerType = requestedBannerType || document.getElementById("tab-gacha-banner-type")?.value || "character";
    if (lblTargetItem) {
        lblTargetItem.innerText = bannerType === "weapon" ? "Arma / Cone de Luz / Motor-W Alvo:" : "Personagem Alvo:";
    }
    charSelect.innerHTML = `<option value="">Carregando dados do simulador e banner atual (${bannerType === 'weapon' ? 'Armas' : 'Personagens'})...</option>`;

    try {
        const [charsRes, defaultsRes] = await Promise.allSettled([
            fetch(`/api/gacha/characters/${gameId}`).then(r => r.json()),
            fetch(`/api/gacha/defaults/${gameId}?banner_type=${bannerType}`).then(r => r.json())
        ]);

        const charsData = charsRes.status === "fulfilled" ? charsRes.value : {};
        const defaultsData = defaultsRes.status === "fulfilled" ? defaultsRes.value : {};
        window.gachaState.currentBannerData = defaultsData;
        window.gachaState.bannerType = bannerType;

        // 1. Atualiza Pity Atual e Status 50/50 ou 75/25 com dados reais da conta
        const pityInput = document.getElementById("tab-gacha-pity");
        const guaranteedSelect = document.getElementById("tab-gacha-guaranteed");
        const pityBadge = document.getElementById("gacha-pity-source-badge");

        const curPity = bannerType === "weapon" ? (defaultsData.weapon_pity ?? defaultsData.current_pity ?? 0) : (defaultsData.character_pity ?? defaultsData.current_pity ?? 0);
        const curGuaranteed = bannerType === "weapon" ? !!(defaultsData.weapon_guaranteed ?? defaultsData.is_guaranteed) : !!(defaultsData.character_guaranteed ?? defaultsData.is_guaranteed);

        if (pityInput) {
            pityInput.value = curPity;
            pityInput.max = bannerType === "weapon" ? "79" : "89";
        }
        if (guaranteedSelect) {
            guaranteedSelect.value = curGuaranteed ? "true" : "false";
        }
        if (pityBadge) {
            pityBadge.textContent = curPity > 0 
                ? `Sincronizado: ${curPity} tiros (${bannerType === 'weapon' ? 'Arma/Cone' : 'Personagem'})`
                : `Sincronizado (0 Tiros • ${bannerType === 'weapon' ? 'Arma/Cone' : 'Personagem'})`;
        }

        // 2. Atualiza Card Visual do Banner Oficial Promocional In-Game
        window.renderActiveBannerCard(defaultsData, 0, bannerType);

        // 3. Monta Opções do Select de Itens
        charSelect.innerHTML = "";

        if (bannerType === "weapon") {
            const genericOpt = document.createElement("option");
            genericOpt.value = "";
            genericOpt.innerText = "⚔️ Arma / Cone de Luz / Motor-W 5★ Genérico";
            charSelect.appendChild(genericOpt);

            const weaponBanners = defaultsData.available_weapon_banners || [];
            if (weaponBanners.length > 0) {
                const grpWeapon = document.createElement("optgroup");
                grpWeapon.label = "⚔️ Banners de Armas/Cones em Destaque";
                weaponBanners.forEach(b => {
                    const opt = document.createElement("option");
                    opt.value = b.character_name;
                    opt.innerText = `⚔️ ${b.character_name}${b.banner_title ? ` (${b.banner_title})` : ''} (Banner In-Game)`;
                    grpWeapon.appendChild(opt);
                });
                charSelect.appendChild(grpWeapon);
            }

            const defaultWeapon = weaponBanners[0]?.character_name || "";
            charSelect.value = defaultWeapon;
            window.updateGachaCharPreview(defaultWeapon);

        } else {
            const chars = charsData.characters || [];
            const activeCharName = defaultsData.active_banner_character;

            const bannerChars = defaultsData.available_banners || [];
            bannerChars.forEach(b => {
                const bName = b.character_name;
                if (!bName) return;
                const exists = chars.some(c => c.name.toLowerCase() === bName.toLowerCase());
                if (!exists) {
                    chars.push({
                        name: bName,
                        rarity: 5,
                        element: b.character_info?.element || "",
                        icon: b.character_info?.icon || b.banner_image || "",
                        gacha_art: b.banner_image || "",
                        owned: false,
                        current_rank: -1,
                        rank_str: null,
                        level: 0,
                        is_current_banner: true
                    });
                } else {
                    const existing = chars.find(c => c.name.toLowerCase() === bName.toLowerCase());
                    if (existing) {
                        existing.is_current_banner = true;
                        if (!existing.gacha_art) existing.gacha_art = b.banner_image;
                    }
                }
            });
            window.gachaState.charList = chars;

            const genericOpt = document.createElement("option");
            genericOpt.value = "";
            genericOpt.innerText = "✨ Personagem 5★ Genérico / Qualquer Banner";
            charSelect.appendChild(genericOpt);

            if (bannerChars.length > 0) {
                const grpBanner = document.createElement("optgroup");
                grpBanner.label = "⭐ Banners Oficiais Ativos (Destaque Atual)";
                bannerChars.forEach(b => {
                    const opt = document.createElement("option");
                    opt.value = b.character_name;
                    opt.innerText = `⭐ ${b.character_name}${b.banner_title ? ` (${b.banner_title})` : ''} (Banner In-Game)`;
                    grpBanner.appendChild(opt);
                });
                charSelect.appendChild(grpBanner);
            }

            const ownedChars = chars.filter(c => c.owned);
            const unownedChars = chars.filter(c => !c.owned);

            if (ownedChars.length > 0) {
                const grpOwned = document.createElement("optgroup");
                grpOwned.label = "🟢 Seus Personagens 5★ (no Roster)";
                ownedChars.forEach(c => {
                    const opt = document.createElement("option");
                    opt.value = c.name;
                    opt.innerText = `✓ ${c.name} (Nv. ${c.level} • ${c.rank_str || 'C0'})`;
                    grpOwned.appendChild(opt);
                });
                charSelect.appendChild(grpOwned);
            }

            if (unownedChars.length > 0) {
                const grpUnowned = document.createElement("optgroup");
                grpUnowned.label = "⚪ Outros Personagens 5★ do Jogo";
                unownedChars.forEach(c => {
                    const opt = document.createElement("option");
                    opt.value = c.name;
                    opt.innerText = `${c.name} (Não Obtido)`;
                    grpUnowned.appendChild(opt);
                });
                charSelect.appendChild(grpUnowned);
            }

            let selectedDefault = "";
            if (activeCharName && chars.some(c => c.name.toLowerCase() === activeCharName.toLowerCase())) {
                const found = chars.find(c => c.name.toLowerCase() === activeCharName.toLowerCase());
                selectedDefault = found ? found.name : activeCharName;
            } else if (ownedChars.length > 0) {
                selectedDefault = ownedChars[0].name;
            }

            charSelect.value = selectedDefault;
            window.updateGachaCharPreview(selectedDefault);
        }

    } catch (e) {
        console.error("Erro ao carregar lista de itens gacha:", e);
        charSelect.innerHTML = `<option value="">Erro ao carregar itens</option>`;
    }
};

window.renderActiveBannerCard = function(defaultsData, selectedIndex = 0, bannerTypeOverride = null) {
    if (!defaultsData) return;
    window.gachaState.currentBannerData = defaultsData;
    window.gachaState.activeBannerIndex = selectedIndex;

    const bannerType = bannerTypeOverride || document.getElementById("tab-gacha-banner-type")?.value || "character";
    const availableBanners = bannerType === "weapon"
        ? (defaultsData.available_weapon_banners || [])
        : (defaultsData.available_banners || []);

    const currentBanner = availableBanners[selectedIndex] || (availableBanners.length > 0 ? availableBanners[0] : (defaultsData.active_banner_character ? {
        character_name: defaultsData.active_banner_character,
        banner_title: defaultsData.active_banner_title,
        banner_image: defaultsData.active_banner_image,
        character_info: defaultsData.active_character_info,
        featured_4stars: defaultsData.featured_4stars,
        featured_4stars_info: defaultsData.featured_4stars_info
    } : null));

    if (!currentBanner) return;

    // 1. Badge de Patch/Fase e Horário Oficial do Banner
    const patchBadge = document.getElementById("gacha-banner-patch-badge");
    if (patchBadge) {
        const schedTime = defaultsData.banner_time || (defaultsData.banner_phase === 2 ? (defaultsData.game_id === 'genshin' ? '20:00' : '14:00') : '23:30');
        patchBadge.textContent = `${defaultsData.patch_info || "Fase Ativa"} • Horário Oficial: ${schedTime}`;
    }

    // 2. Seletor de Banners da Fase (Tabs/Pills)
    const switcherEl = document.getElementById("gacha-banner-switcher");
    if (switcherEl) {
        if (availableBanners.length > 1) {
            switcherEl.style.display = "flex";
            switcherEl.innerHTML = "";
            availableBanners.forEach((b, idx) => {
                const btn = document.createElement("button");
                btn.type = "button";
                btn.className = `gacha-banner-tab-btn ${idx === selectedIndex ? "active" : ""}`;
                const iconClass = bannerType === "weapon" ? "fa-shield-halved" : "fa-star";
                btn.title = b.banner_title ? `${b.character_name} (${b.banner_title})` : b.character_name;
                btn.innerHTML = `<i class="fa-solid ${iconClass}"></i> ${b.character_name}`;
                btn.onclick = () => {
                    window.renderActiveBannerCard(defaultsData, idx, bannerType);
                    const charSelect = document.getElementById("tab-gacha-char-select");
                    if (charSelect) {
                        charSelect.value = b.character_name;
                        window.updateGachaCharPreview(b.character_name);
                    }
                };
                switcherEl.appendChild(btn);
            });
        } else {
            switcherEl.style.display = "none";
        }
    }

    // 3. Imagem Oficial In-Game e Títulos
    const bannerArtImg = document.getElementById("gacha-banner-art-img");
    const bannerTitle = document.getElementById("gacha-banner-char-title");
    const bannerSubtitle = document.getElementById("gacha-banner-subtitle");
    const bannerTypeBadge = document.getElementById("gacha-banner-type-badge");

    if (bannerTitle) {
        bannerTitle.textContent = currentBanner.banner_title || currentBanner.character_name;
    }
    if (bannerSubtitle) {
        bannerSubtitle.textContent = bannerType === "weapon"
            ? `Taxa Aumentada de Arma / Cone 5★ • ${currentBanner.character_name}`
            : `Taxa Aumentada de 5★ • ${currentBanner.character_name}`;
    }
    if (bannerTypeBadge) {
        if (bannerType === "weapon") {
            bannerTypeBadge.textContent = defaultsData.game_id === "hsr" ? "Fixação Brilhante (Cones)" : (defaultsData.game_id === "zzz" ? "Sonata Dissonante (Motores-W)" : "Invocação do Epítome (Armas)");
        } else {
            bannerTypeBadge.textContent = defaultsData.game_id === "hsr" ? "Salto de Evento" : (defaultsData.game_id === "zzz" ? "Busca de Sinal" : "Oração de Evento");
        }
    }
    if (currentBanner.banner_image && bannerArtImg) {
        bannerArtImg.src = currentBanner.banner_image;
        bannerArtImg.style.display = "block";
        bannerArtImg.onerror = () => { bannerArtImg.style.display = "none"; };
    } else if (bannerArtImg) {
        bannerArtImg.style.display = "none";
    }

    // 4. Avatar e Detalhes do Item 5★ Promocional
    const avatar5Star = document.getElementById("gacha-banner-5star-avatar");
    const name5Star = document.getElementById("gacha-banner-5star-name");

    if (name5Star) {
        name5Star.textContent = currentBanner.character_name;
    }
    const charIcon = currentBanner.character_info?.icon || "";
    if (avatar5Star && charIcon) {
        avatar5Star.src = charIcon;
        avatar5Star.style.display = "block";
        avatar5Star.onerror = () => { avatar5Star.style.display = "none"; };
    } else if (avatar5Star) {
        avatar5Star.style.display = "none";
    }

    // 5. Grid de Itens 4★ Ativos
    const fourStarsGrid = document.getElementById("gacha-banner-4stars-grid");
    if (fourStarsGrid) {
        fourStarsGrid.innerHTML = "";
        const f4List = currentBanner.featured_4stars_info || [];
        if (f4List.length > 0) {
            f4List.forEach(f4 => {
                const pill = document.createElement("div");
                pill.className = "gacha-banner-4star-pill";
                pill.title = `${f4.name} (Taxa Aumentada de 4★)`;
                pill.innerHTML = `
                    <div class="gacha-banner-4star-img-box">
                        <img src="${f4.icon}" alt="${f4.name}" onerror="this.src='/assets/unknown_avatar.png';">
                    </div>
                    <div class="gacha-banner-4star-info">
                        <span class="gacha-banner-4star-name">${f4.name}</span>
                        <span class="gacha-banner-4star-stars">★★★★</span>
                    </div>
                `;
                fourStarsGrid.appendChild(pill);
            });
        } else if (currentBanner.featured_4stars && currentBanner.featured_4stars.length > 0) {
            currentBanner.featured_4stars.forEach(name => {
                const pill = document.createElement("div");
                pill.className = "gacha-banner-4star-pill";
                pill.innerHTML = `
                    <div class="gacha-banner-4star-info" style="padding: 2px 6px;">
                        <span class="gacha-banner-4star-name">${name}</span>
                        <span class="gacha-banner-4star-stars">★★★★</span>
                    </div>
                `;
                fourStarsGrid.appendChild(pill);
            });
        } else {
            fourStarsGrid.innerHTML = `<span style="font-size: 11px; color: var(--text-muted); font-style: italic;">Pool oficial da fase</span>`;
        }
    }
};

window.selectActiveBannerChar = function() {
    const data = window.gachaState.currentBannerData;
    if (!data) return;
    const bannerType = document.getElementById("tab-gacha-banner-type")?.value || "character";
    const availableBanners = bannerType === "weapon" ? (data.available_weapon_banners || []) : (data.available_banners || []);
    const idx = window.gachaState.activeBannerIndex || 0;
    const b = availableBanners[idx] || availableBanners[0] || { character_name: data.active_banner_character };
    const charName = b.character_name;
    if (charName) {
        const charSelect = document.getElementById("tab-gacha-char-select");
        if (charSelect) {
            charSelect.value = charName;
            window.updateGachaCharPreview(charName);
        }
    }
};

window.updateGachaCharPreview = function(charName) {
    const gameId = document.getElementById("tab-gacha-game-select")?.value || "genshin";
    const bannerType = document.getElementById("tab-gacha-banner-type")?.value || "character";
    const terms = window.getGachaTerms(gameId, bannerType);
    const chars = window.gachaState.charList || [];
    const char = chars.find(c => c.name === charName);

    const nameLbl = document.getElementById("gacha-hero-name");
    const starsLbl = document.getElementById("gacha-hero-stars");
    const badgeEl = document.getElementById("gacha-hero-badge");
    const bgEl = document.getElementById("gacha-hero-bg");
    const avatarImg = document.getElementById("gacha-hero-avatar-img");
    const avatarFallback = document.getElementById("gacha-hero-avatar-fallback");
    const currentRankSelect = document.getElementById("tab-gacha-current-rank");

    if (bannerType === "weapon") {
        if (nameLbl) nameLbl.innerText = charName || "Arma / Cone 5★ Genérico";
        if (starsLbl) starsLbl.innerText = "★★★★★";
        if (badgeEl) {
            badgeEl.className = "gacha-char-badge-unowned";
            badgeEl.innerHTML = `<i class="fa-solid fa-shield-halved"></i> Banner de Armas / Cones de Luz`;
        }
        if (bgEl) bgEl.style.backgroundImage = "none";
        if (avatarImg) avatarImg.style.display = "none";
        if (avatarFallback) {
            avatarFallback.style.display = "flex";
            avatarFallback.innerHTML = `<i class="fa-solid fa-shield-halved"></i>`;
        }
        if (currentRankSelect) currentRankSelect.value = "-1";
        
        // Sincroniza arte do banner se corresponder
        const availableWeapons = window.gachaState.currentBannerData?.available_weapon_banners || [];
        const matchedBanner = availableWeapons.find(b => b.character_name.toLowerCase() === (charName || "").toLowerCase());
        const bannerArtImg = document.getElementById("gacha-banner-art-img");
        const bannerTitle = document.getElementById("gacha-banner-char-title");

        if (matchedBanner && matchedBanner.banner_image && bannerArtImg) {
            bannerArtImg.src = matchedBanner.banner_image;
            bannerArtImg.style.display = "block";
            if (bannerTitle) bannerTitle.textContent = `Banner: ${matchedBanner.character_name}`;
        }

        window.updateTargetRankOptions();
        return;
    }

    if (!char && charName) {
        const availableBanners = window.gachaState.currentBannerData?.available_banners || [];
        const matched = availableBanners.find(b => b.character_name.toLowerCase() === charName.toLowerCase());
        if (matched) {
            char = {
                name: matched.character_name,
                rarity: 5,
                element: matched.character_info?.element || "",
                icon: matched.character_info?.icon || matched.banner_image || "",
                gacha_art: matched.banner_image || "",
                owned: false,
                current_rank: -1,
                rank_str: null,
                level: 0
            };
        }
    }

    if (!char) {
        if (nameLbl) nameLbl.innerText = "Personagem 5★ Genérico";
        if (starsLbl) starsLbl.innerText = "★★★★★";
        if (badgeEl) {
            badgeEl.className = "gacha-char-badge-unowned";
            badgeEl.innerHTML = `<i class="fa-solid fa-circle-plus"></i> Não possui (0 cópias)`;
        }
        if (bgEl) bgEl.style.backgroundImage = "none";
        if (avatarImg) avatarImg.style.display = "none";
        if (avatarFallback) avatarFallback.style.display = "flex";
        if (currentRankSelect) currentRankSelect.value = "-1";
        window.updateTargetRankOptions();
        return;
    }

    if (nameLbl) nameLbl.innerText = char.name;
    if (starsLbl) starsLbl.innerText = "★".repeat(char.rarity || 5);

    const splash = char.gacha_art || char.icon || "";
    const avatar = char.icon || char.gacha_art || "";

    if (bgEl && splash) {
        bgEl.style.backgroundImage = `url('${splash}')`;
    } else if (bgEl) {
        bgEl.style.backgroundImage = "none";
    }

    if (avatarImg && avatar) {
        avatarImg.onerror = () => {
            avatarImg.style.display = "none";
            if (avatarFallback) avatarFallback.style.display = "flex";
        };
        avatarImg.src = avatar;
        avatarImg.style.display = "block";
        if (avatarFallback) avatarFallback.style.display = "none";
    } else {
        if (avatarImg) avatarImg.style.display = "none";
        if (avatarFallback) avatarFallback.style.display = "flex";
    }

    if (char.owned) {
        const rankNum = char.current_rank >= 0 ? char.current_rank : 0;
        const rankStr = char.rank_str || `${terms.prefix}${rankNum}`;
        if (badgeEl) {
            badgeEl.className = "gacha-char-badge-owned";
            badgeEl.innerHTML = `<i class="fa-solid fa-circle-check"></i> No seu Roster: ${rankStr} (Nível ${char.level})`;
        }
        if (currentRankSelect) currentRankSelect.value = String(rankNum);
    } else {
        if (badgeEl) {
            badgeEl.className = "gacha-char-badge-unowned";
            badgeEl.innerHTML = `<i class="fa-solid fa-circle-plus"></i> Não possui (0 cópias)`;
        }
        if (currentRankSelect) currentRankSelect.value = "-1";
    }

    window.updateTargetRankOptions();
};

window.runGachaSimulation = async function() {
    const gameId = document.getElementById("tab-gacha-game-select")?.value || "genshin";
    const bannerType = document.getElementById("tab-gacha-banner-type")?.value || "character";
    const charSelect = document.getElementById("tab-gacha-char-select");
    const charName = charSelect ? charSelect.value : "";
    const currentRank = parseInt(document.getElementById("tab-gacha-current-rank")?.value ?? -1);
    const targetRank = parseInt(document.getElementById("tab-gacha-target-rank")?.value ?? (bannerType === "weapon" ? 4 : 6));
    const currentPity = parseInt(document.getElementById("tab-gacha-pity")?.value) || 0;
    const isGuaranteed = document.getElementById("tab-gacha-guaranteed")?.value === "true";
    const pullsAvailable = parseInt(document.getElementById("tab-gacha-pulls")?.value) || 0;

    const runBtn = document.getElementById("tab-btn-run-gacha-sim");
    if (runBtn) {
        runBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Simulando 10.000 iterações...`;
        runBtn.disabled = true;
    }

    try {
        const res = await fetch("/api/gacha/calculate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                game_id: gameId,
                banner_type: bannerType,
                current_pity: currentPity,
                is_guaranteed: isGuaranteed,
                pulls_available: pullsAvailable,
                current_rank: currentRank,
                target_rank: targetRank,
                char_name: charName
            })
        });
        const data = await res.json();
        
        const resultsBox = document.getElementById("tab-gacha-results-box");
        if (resultsBox) resultsBox.style.display = "block";

        const chanceLbl = document.getElementById("tab-gacha-chance-lbl");
        if (chanceLbl) {
            chanceLbl.innerText = `${data.success_rate}%`;
            chanceLbl.className = "gacha-gauge-val " + (
                data.success_rate >= 80 ? "success-high" :
                (data.success_rate >= 50 ? "success-med" : "success-low")
            );
        }

        const summaryEl = document.getElementById("tab-gacha-target-summary");
        const terms = window.getGachaTerms(gameId, bannerType);
        const charTitle = charName ? `<b>${charName}</b>` : (bannerType === "weapon" ? "Arma/Cone Alvo" : "Personagem Alvo");
        if (summaryEl) {
            if (data.needed_new_copies === 0) {
                summaryEl.innerHTML = `🎉 Você já possui a meta <b>${data.target_rank_str}</b>!`;
            } else {
                summaryEl.innerHTML = `Probabilidade de evoluir ${charTitle} de <b>${data.current_rank_str}</b> até <b>${data.target_rank_str}</b> (+${data.needed_new_copies} cópias) com <b>${pullsAvailable} tiros</b>.`;
            }
        }

        const avgLbl = document.getElementById("tab-gacha-avg-lbl");
        if (avgLbl) {
            avgLbl.innerText = data.avg_pulls_spent 
                ? `${data.avg_pulls_spent} tiros` 
                : "Tiros insuficientes";
        }

        const gemsSpentLbl = document.getElementById("tab-gacha-gems-spent-lbl");
        if (gemsSpentLbl) {
            if (data.avg_pulls_spent) {
                const gemsAvg = Math.round(data.avg_pulls_spent * terms.gemCostPerPull);
                gemsSpentLbl.innerText = `~${gemsAvg.toLocaleString()} ${terms.currency}`;
            } else {
                gemsSpentLbl.innerText = "N/A";
            }
        }

        const distList = document.getElementById("tab-gacha-dist-list");
        if (distList) {
            distList.innerHTML = "";
            for (const [k, v] of Object.entries(data.distribution || {})) {
                const item = document.createElement("div");
                item.className = "gacha-dist-item";
                
                const isGoal = k.includes("Meta") || k.includes("Batida") || k.includes("alcançada");
                
                item.innerHTML = `
                    <div class="gacha-dist-header">
                        <span>${k}</span>
                        <strong style="color: ${isGoal ? '#34d399' : '#fbbf24'};">${v}%</strong>
                    </div>
                    <div class="gacha-dist-bar-track">
                        <div class="gacha-dist-bar-fill ${isGoal ? 'target-reached' : ''}" style="width: ${v}%;"></div>
                    </div>
                `;
                distList.appendChild(item);
            }
        }
    } catch (err) {
        console.error(err);
        if (typeof showToast === "function") showToast("Erro ao executar simulação de Gacha.");
    } finally {
        if (runBtn) {
            runBtn.innerHTML = `<i class="fa-solid fa-dice"></i> Monte Carlo`;
            runBtn.disabled = false;
        }
    }
};

// ==========================================================================
// GACHA FORECAST & PLANEJADOR DE BANNERS FUTUROS FRONTEND LOGIC
// ==========================================================================

window.getBannerScheduleTime = function(gameId, phase = 1) {
    const g = String(gameId || "genshin").toLowerCase().trim();
    const p = parseInt(phase) || 1;
    if (p === 2) {
        if (g === "genshin") {
            return { hour: 20, minute: 0, str: "20:00", label: "2ª Fase (20h)" };
        }
        return { hour: 14, minute: 0, str: "14:00", label: "2ª Fase (14h)" };
    }
    return { hour: 23, minute: 30, str: "23:30", label: "1ª Fase (23:30)" };
};

window.lastForecastResult = null;
window.forecastState = {
    gameId: "genshin",
    bannerType: "character",
    bannerPhase: 1,
    charList: []
};

window.initGachaNavigation = function() {
    const viewBtns = document.querySelectorAll(".gacha-view-btn");
    viewBtns.forEach(btn => {
        btn.onclick = () => {
            viewBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const viewTarget = btn.dataset.view;

            document.querySelectorAll(".gacha-subview").forEach(sv => {
                sv.style.display = "none";
                sv.classList.remove("active");
            });

            const activeView = document.getElementById(`gacha-view-${viewTarget}`);
            if (activeView) {
                activeView.style.display = "block";
                activeView.classList.add("active");
            }

            if (viewTarget === "forecast") {
                window.initGachaForecast();
            } else if (viewTarget === "goals") {
                window.loadGachaGoals("all");
            } else if (viewTarget === "tracker") {
                window.loadGachaTracker(window.currentTrackerGame || "hsr");
            }
        };
    });
};

window.initGachaForecast = async function() {
    const gameBtns = document.querySelectorAll(".forecast-game-btn");
    const typeBtns = document.querySelectorAll("#forecast-type-pills .forecast-type-btn");
    const phaseBtns = document.querySelectorAll(".forecast-phase-btn");
    const hiddenType = document.getElementById("forecast-banner-type");
    const slider = document.getElementById("forecast-days-slider");
    const sliderVal = document.getElementById("forecast-days-val");
    const quickDayBtns = document.querySelectorAll(".forecast-quick-day-btn");
    const curRankSelect = document.getElementById("forecast-current-rank");
    const runBtn = document.getElementById("btn-run-forecast-calc");
    const saveGoalBtn = document.getElementById("btn-save-forecast-goal");

    gameBtns.forEach(btn => {
        btn.onclick = async () => {
            gameBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const gId = btn.dataset.game;
            window.forecastState.gameId = gId;
            const bType = hiddenType ? hiddenType.value : "character";
            window.updateForecastRankLabels(gId, bType);
            window.syncForecastDaysAndDate(slider ? slider.value : 21);
            await window.loadForecastCharacters(gId, bType);
            window.runGachaForecastCalculation();
        };
    });

    typeBtns.forEach(btn => {
        btn.onclick = async () => {
            typeBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const bType = btn.dataset.type || "character";
            if (hiddenType) hiddenType.value = bType;
            window.forecastState.bannerType = bType;
            const gId = window.forecastState.gameId || "genshin";
            window.updateForecastRankLabels(gId, bType);
            await window.loadForecastCharacters(gId, bType);
            window.runGachaForecastCalculation();
        };
    });

    phaseBtns.forEach(btn => {
        btn.onclick = () => {
            phaseBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            window.forecastState.bannerPhase = parseInt(btn.dataset.phase) || 1;
            window.syncForecastDaysAndDate(slider ? slider.value : 21);
            window.runGachaForecastCalculation();
        };
    });

    const dateInput = document.getElementById("forecast-target-date-input");

    window.syncForecastDaysAndDate = function(daysVal) {
        const d = Math.max(1, parseInt(daysVal) || 21);
        if (slider) slider.value = d;
        if (sliderVal) sliderVal.innerText = `${d} ${d === 1 ? 'dia' : 'dias'}`;

        const gId = window.forecastState.gameId || "genshin";
        const curPhase = window.forecastState.bannerPhase || 1;
        const sched = window.getBannerScheduleTime(gId, curPhase);

        const targetDt = new Date(Date.now() + d * 86400000);
        targetDt.setHours(sched.hour, sched.minute, 0, 0);

        const dd = String(targetDt.getDate()).padStart(2, '0');
        const mm = String(targetDt.getMonth() + 1).padStart(2, '0');
        const yyyy = targetDt.getFullYear();
        const hh = String(targetDt.getHours()).padStart(2, '0');
        const min = String(targetDt.getMinutes()).padStart(2, '0');

        const dateLbl = document.getElementById("forecast-target-date-lbl");
        if (dateLbl) {
            dateLbl.innerText = `Chegada: ${dd}/${mm}/${yyyy} às ${hh}:${min}`;
        }
        if (dateInput) {
            dateInput.value = `${yyyy}-${mm}-${dd}`;
            const tomorrow = new Date(Date.now() + 86400000);
            const tY = tomorrow.getFullYear();
            const tM = String(tomorrow.getMonth() + 1).padStart(2, '0');
            const tD = String(tomorrow.getDate()).padStart(2, '0');
            dateInput.min = `${tY}-${tM}-${tD}`;
        }

        quickDayBtns.forEach(b => {
            if (parseInt(b.dataset.days) === d) {
                b.classList.add("active");
            } else {
                b.classList.remove("active");
            }
        });
    };

    if (slider && sliderVal) {
        slider.oninput = () => {
            window.syncForecastDaysAndDate(slider.value);
        };
    }

    if (dateInput) {
        dateInput.onchange = () => {
            if (!dateInput.value) return;
            const [y, m, day] = dateInput.value.split("-").map(Number);
            const gId = window.forecastState.gameId || "genshin";
            const curPhase = window.forecastState.bannerPhase || 1;
            const sched = window.getBannerScheduleTime(gId, curPhase);
            const picked = new Date(y, m - 1, day, sched.hour, sched.minute, 0);
            const diffDays = Math.max(1, Math.min(180, Math.ceil((picked.getTime() - Date.now()) / 86400000)));
            window.syncForecastDaysAndDate(diffDays);
            window.runGachaForecastCalculation();
        };
    }

    quickDayBtns.forEach(btn => {
        btn.onclick = () => {
            const days = parseInt(btn.dataset.days);
            window.syncForecastDaysAndDate(days);
            window.runGachaForecastCalculation();
        };
    });

    window.syncForecastDaysAndDate(slider ? slider.value : 21);

    if (curRankSelect) {
        curRankSelect.onchange = () => {
            window.updateForecastTargetRankOptions();
        };
    }

    if (runBtn) {
        runBtn.onclick = window.runGachaForecastCalculation;
    }

    if (saveGoalBtn) {
        saveGoalBtn.onclick = window.saveCurrentGachaGoal;
    }

    // Inicialização do Jogo e Tipo do Forecast
    const activeBtn = document.querySelector(".forecast-game-btn.active");
    const curGame = activeBtn ? activeBtn.dataset.game : "genshin";
    const curType = hiddenType ? hiddenType.value : "character";
    window.forecastState.gameId = curGame;
    window.forecastState.bannerType = curType;
    window.updateForecastRankLabels(curGame, curType);
    await window.loadForecastCharacters(curGame, curType);
    window.updateGoalsCountBadge();
    window.runGachaForecastCalculation();
};

window.updateForecastRankLabels = function(gameId, bannerType = "character") {
    const terms = window.getGachaTerms(gameId, bannerType);
    const lblCur = document.getElementById("lbl-forecast-current-rank");
    const lblTgt = document.getElementById("lbl-forecast-target-rank");
    if (lblCur) lblCur.innerText = `${terms.term} Atual:`;
    if (lblTgt) lblTgt.innerText = `Meta de ${terms.term}:`;

    // Atualiza o texto do botão da 2ª Fase conforme o jogo (Genshin: 20h; HSR/ZZZ: 14h)
    const phase2Label = document.getElementById("forecast-phase-2-label");
    if (phase2Label) {
        const schedPhase2 = window.getBannerScheduleTime(gameId, 2);
        phase2Label.innerText = schedPhase2.label;
    }

    const curSelect = document.getElementById("forecast-current-rank");
    if (curSelect) {
        curSelect.innerHTML = `<option value="-1">${terms.unownedLabel}</option>`;
        terms.ranks.forEach(r => {
            const opt = document.createElement("option");
            opt.value = r.val;
            opt.innerText = r.label;
            curSelect.appendChild(opt);
        });
    }

    window.updateForecastTargetRankOptions();
};

window.updateForecastTargetRankOptions = function() {
    const gameId = window.forecastState.gameId || "genshin";
    const bannerType = document.getElementById("forecast-banner-type")?.value || window.forecastState.bannerType || "character";
    const terms = window.getGachaTerms(gameId, bannerType);
    const curRank = parseInt(document.getElementById("forecast-current-rank")?.value ?? -1);
    const tgtSelect = document.getElementById("forecast-target-rank");
    if (!tgtSelect) return;

    const prevTgt = parseInt(tgtSelect.value ?? (bannerType === "weapon" ? 0 : 0));
    tgtSelect.innerHTML = "";

    terms.ranks.forEach(r => {
        if (r.val > curRank || (curRank === -1 && r.val >= 0)) {
            const opt = document.createElement("option");
            opt.value = r.val;
            const extra = curRank < 0
                ? (r.val === 0 
                    ? (bannerType === "weapon" ? " (Obter Arma/Cone Base)" : " (Obter Personagem Base)") 
                    : ` (+${r.val + 1} cópias)`)
                : ` (+${r.val - curRank} cópias)`;
            opt.innerText = `${terms.prefix}${bannerType === "weapon" ? r.val + 1 : r.val}${extra}`;
            tgtSelect.appendChild(opt);
        }
    });

    if (prevTgt > curRank) {
        tgtSelect.value = prevTgt;
    } else if (tgtSelect.options.length > 0) {
        tgtSelect.value = tgtSelect.options[0].value;
    }
};

window.loadForecastCharacters = async function(gameId, bannerType = "character") {
    const select = document.getElementById("forecast-char-select");
    const lblTargetItem = document.getElementById("lbl-forecast-target-item");
    if (!select) return;
    
    if (lblTargetItem) {
        lblTargetItem.innerText = bannerType === "weapon" ? "Arma / Cone de Luz / Motor-W Alvo:" : "Personagem Alvo:";
    }
    select.innerHTML = `<option value="">Buscando catálogo de ${bannerType === 'weapon' ? 'armas' : 'personagens'}...</option>`;

    try {
        const [charsRes, defaultsRes] = await Promise.allSettled([
            fetch(`/api/gacha/characters/${gameId}`).then(r => r.json()),
            fetch(`/api/gacha/defaults/${gameId}?banner_type=${bannerType}`).then(r => r.json())
        ]);
        const data = charsRes.status === "fulfilled" ? charsRes.value : {};
        const defaultsData = defaultsRes.status === "fulfilled" ? defaultsRes.value : {};

        // Sincroniza Pity do Forecast de acordo com a categoria selecionada
        const pityInput = document.getElementById("forecast-pity-cur");
        const guaranteedSelect = document.getElementById("forecast-guaranteed-cur");
        if (pityInput && defaultsData.current_pity !== undefined) {
            pityInput.value = bannerType === "weapon" ? (defaultsData.weapon_pity ?? defaultsData.current_pity) : (defaultsData.character_pity ?? defaultsData.current_pity);
            pityInput.max = bannerType === "weapon" ? "79" : "89";
        }
        if (guaranteedSelect) {
            const isG = bannerType === "weapon" ? !!defaultsData.weapon_guaranteed : !!defaultsData.is_guaranteed;
            guaranteedSelect.value = isG ? "true" : "false";
        }

        select.innerHTML = "";

        if (bannerType === "weapon") {
            const optGeneric = document.createElement("option");
            optGeneric.value = "Próxima Arma / Cone 5★ Limitado";
            optGeneric.innerText = "⚔️ Próximo Banner de Armas / Cones Limitado";
            select.appendChild(optGeneric);

            const weaponBanners = defaultsData.available_weapon_banners || [];
            if (weaponBanners.length > 0) {
                const grpWeapons = document.createElement("optgroup");
                grpWeapons.label = "⚔️ Armas / Cones em Destaque no Banner";
                weaponBanners.forEach(b => {
                    const opt = document.createElement("option");
                    opt.value = b.character_name;
                    opt.innerText = `⚔️ ${b.character_name}${b.banner_title ? ` (${b.banner_title})` : ''}`;
                    grpWeapons.appendChild(opt);
                });
                select.appendChild(grpWeapons);
            }

            select.onchange = () => {
                const curRankSel = document.getElementById("forecast-current-rank");
                if (curRankSel) curRankSel.value = "-1";
                window.updateForecastTargetRankOptions();
            };

        } else {
            const chars = data.characters || [];
            window.forecastState.charList = chars;

            const optGeneric = document.createElement("option");
            optGeneric.value = "Próximo Personagem 5★ Limitado";
            optGeneric.innerText = "✨ Próximo Banner Limitado / Novo Personagem";
            select.appendChild(optGeneric);

            const owned = chars.filter(c => c.owned);
            const unowned = chars.filter(c => !c.owned);

            if (unowned.length > 0) {
                const grpUnowned = document.createElement("optgroup");
                grpUnowned.label = "⚪ Personagens 5★ Não Obtidos";
                unowned.forEach(c => {
                    const opt = document.createElement("option");
                    opt.value = c.name;
                    opt.innerText = `${c.name} (Banner / Rerun)`;
                    grpUnowned.appendChild(opt);
                });
                select.appendChild(grpUnowned);
            }

            if (owned.length > 0) {
                const grpOwned = document.createElement("optgroup");
                grpOwned.label = "🟢 Personagens 5★ no Roster (Constelações/Eidolons)";
                owned.forEach(c => {
                    const opt = document.createElement("option");
                    opt.value = c.name;
                    opt.innerText = `✓ ${c.name} (${c.rank_str || 'C0'})`;
                    grpOwned.appendChild(opt);
                });
                select.appendChild(grpOwned);
            }

            select.onchange = () => {
                const cName = select.value;
                const cObj = chars.find(c => c.name === cName);
                const curRankSel = document.getElementById("forecast-current-rank");
                if (cObj && cObj.owned && curRankSel) {
                    curRankSel.value = String(cObj.current_rank >= 0 ? cObj.current_rank : 0);
                } else if (curRankSel) {
                    curRankSel.value = "-1";
                }
                window.updateForecastTargetRankOptions();
            };
        }

    } catch (e) {
        console.error("Erro ao carregar itens para forecast:", e);
        select.innerHTML = `<option value="Próximo Banner 5★">Próximo Banner 5★</option>`;
    }
};

window.runGachaForecastCalculation = async function() {
    const gameId = window.forecastState.gameId || "genshin";
    const bannerType = document.getElementById("forecast-banner-type")?.value || window.forecastState.bannerType || "character";
    const charSelect = document.getElementById("forecast-char-select");
    const charName = charSelect?.value || (bannerType === "weapon" ? "Arma 5★ Alvo" : "Personagem 5★ Alvo");
    const currentPulls = parseInt(document.getElementById("forecast-pulls-cur")?.value) || 0;
    const currentPity = parseInt(document.getElementById("forecast-pity-cur")?.value) || 0;
    const isGuaranteed = document.getElementById("forecast-guaranteed-cur")?.value === "true";
    const currentRank = parseInt(document.getElementById("forecast-current-rank")?.value ?? -1);
    const targetRank = parseInt(document.getElementById("forecast-target-rank")?.value ?? 0);
    const targetDays = parseInt(document.getElementById("forecast-days-slider")?.value) || 21;

    const hasDailyPass = document.getElementById("forecast-inc-pass")?.checked ?? false;
    const hasBattlePass = document.getElementById("forecast-inc-bp")?.checked ?? false;
    const incShop = document.getElementById("forecast-inc-shop")?.checked ?? true;
    const incEvents = document.getElementById("forecast-inc-events")?.checked ?? true;

    const runBtn = document.getElementById("btn-run-forecast-calc");
    if (runBtn) {
        runBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Projetando acúmulo de gemas & Monte Carlo...`;
        runBtn.disabled = true;
    }

    try {
        const res = await fetch("/api/gacha/forecast/calculate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                game_id: gameId,
                banner_type: bannerType,
                character_name: charName,
                current_pulls: currentPulls,
                current_pity: currentPity,
                is_guaranteed: isGuaranteed,
                current_rank: currentRank,
                target_rank: targetRank,
                target_days: targetDays,
                has_daily_pass: hasDailyPass,
                has_battle_pass: hasBattlePass,
                include_shop_resets: incShop,
                include_events_estimate: incEvents,
                include_endgame_resets: incEvents
            })
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `Erro na API (${res.status})`);
        }

        const data = await res.json();
        window.lastForecastResult = data;
        window.renderGachaForecastResult(data);

    } catch (err) {
        console.error("Erro no Gacha Forecast:", err);
        if (typeof showToast === "function") showToast("Erro ao calcular o Gacha Forecast: " + err.message);
    } finally {
        if (runBtn) {
            runBtn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Calcular Projeção & Monte Carlo`;
            runBtn.disabled = false;
        }
    }
};

window.renderGachaForecastResult = function(data) {
    if (!data) return;

    // 1. Parecer Estratégico
    const verdict = data.verdict || {};
    const badgeEl = document.getElementById("forecast-verdict-badge");
    const textEl = document.getElementById("forecast-verdict-text");
    const boxEl = document.getElementById("forecast-verdict-box");

    if (badgeEl) {
        badgeEl.innerText = verdict.badge || "Análise Concluída";
        badgeEl.style.color = verdict.color || "#34d399";
        badgeEl.style.background = `${verdict.color || '#34d399'}22`;
    }
    if (textEl) {
        textEl.innerHTML = `<strong>${data.character_name} (${data.target_rank_str}):</strong> ${verdict.text || ''}`;
    }
    if (boxEl) {
        boxEl.style.borderColor = `${verdict.color || '#34d399'}44`;
        boxEl.style.background = `${verdict.color || '#34d399'}11`;
    }

    // 2. KPIs Principais
    const kpiChance = document.getElementById("forecast-kpi-chance");
    const kpiF2P = document.getElementById("forecast-kpi-f2p-comp");
    const kpiTotal = document.getElementById("forecast-kpi-total-pulls");
    const kpiFuture = document.getElementById("forecast-kpi-future-add");
    const kpiWorst = document.getElementById("forecast-kpi-worst-case");
    const kpiMissing = document.getElementById("forecast-kpi-missing-pulls");

    if (kpiChance) {
        kpiChance.innerText = `${data.success_rate}%`;
        kpiChance.style.color = data.success_rate >= 75 ? "#34d399" : (data.success_rate >= 50 ? "#fbbf24" : "#f87171");
    }
    if (kpiF2P) {
        kpiF2P.innerText = `(F2P Puro: ${data.f2p_pure_success_rate}%)`;
    }
    if (kpiTotal) {
        kpiTotal.innerText = `${data.total_projected_pulls} tiros`;
    }
    if (kpiFuture) {
        kpiFuture.innerText = `+${Math.round(data.income_breakdown?.total_future_pulls || 0)} novos no período`;
    }
    if (kpiWorst) {
        kpiWorst.innerText = `${data.worst_case_pulls} tiros`;
    }
    if (kpiMissing) {
        if (data.pulls_needed_for_guarantee === 0) {
            kpiMissing.innerText = "✓ Garantido matematicamente!";
            kpiMissing.style.color = "#34d399";
        } else {
            kpiMissing.innerText = `Faltam ${data.pulls_needed_for_guarantee} tiros p/ 100%`;
            kpiMissing.style.color = "#fca5a5";
        }
    }

    // 3. Breakdown de Renda
    const inc = data.income_breakdown || {};
    const totalLbl = document.getElementById("forecast-breakdown-total-lbl");
    const listEl = document.getElementById("forecast-income-breakdown-list");

    if (totalLbl) {
        totalLbl.innerText = `${inc.total_projected_pulls} tiros (~${(inc.total_projected_gems_equiv || 0).toLocaleString()} gemas)`;
    }

    if (listEl) {
        const items = [
            { icon: "fa-solid fa-wallet", color: "#a855f7", label: `Saldo Atual Guardado`, pulls: inc.current_pulls, gems: inc.current_gems_equiv },
            { icon: "fa-solid fa-calendar-check", color: "#38bdf8", label: inc.daily_f2p?.label, pulls: inc.daily_f2p?.pulls, gems: inc.daily_f2p?.gems },
            ...(inc.daily_pass?.active ? [{ icon: "fa-solid fa-moon", color: "#fbbf24", label: inc.daily_pass?.label, pulls: inc.daily_pass?.pulls, gems: inc.daily_pass?.gems }] : []),
            ...(inc.battle_pass?.active ? [{ icon: "fa-solid fa-award", color: "#ec4899", label: inc.battle_pass?.label, pulls: inc.battle_pass?.pulls, gems: Math.round(inc.battle_pass?.pulls * 160) }] : []),
            ...(inc.shop_resets?.pulls > 0 ? [{ icon: "fa-solid fa-shop", color: "#10b981", label: inc.shop_resets?.label, pulls: inc.shop_resets?.pulls, gems: inc.shop_resets?.pulls * 160 }] : []),
            ...(inc.events?.gems > 0 ? [{ icon: "fa-solid fa-star", color: "#f59e0b", label: inc.events?.label, pulls: inc.events?.pulls, gems: inc.events?.gems }] : []),
            ...(inc.endgame?.gems > 0 ? [{ icon: "fa-solid fa-trophy", color: "#34d399", label: inc.endgame?.label, pulls: inc.endgame?.pulls, gems: inc.endgame?.gems }] : [])
        ];

        listEl.innerHTML = items.map(item => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 10px; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid rgba(255,255,255,0.04);">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <i class="${item.icon}" style="color: ${item.color}; font-size: 13px;"></i>
                    <span style="color: #cbd5e1;">${item.label}</span>
                </div>
                <div style="text-align: right;">
                    <strong style="color: #fff; font-size: 13px;">+${item.pulls} tiros</strong>
                    <span style="font-size: 10px; color: var(--text-muted); display: block;">(${item.gems?.toLocaleString()} gemas)</span>
                </div>
            </div>
        `).join('');
    }
};

window.saveCurrentGachaGoal = async function() {
    const data = window.lastForecastResult;
    if (!data) {
        if (typeof showToast === "function") showToast("Calcule a projeção antes de salvar a meta.");
        return;
    }

    const saveBtn = document.getElementById("btn-save-forecast-goal");
    if (saveBtn) {
        saveBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Salvando no SQLite...`;
        saveBtn.disabled = true;
    }

    const nowDt = new Date();
    const daysPlanned = Math.max(1, parseInt(data.target_days) || 21);
    const curPhase = window.forecastState.bannerPhase || 1;
    const sched = window.getBannerScheduleTime(data.game_id, curPhase);
    const targetDt = new Date(nowDt.getTime() + daysPlanned * 86400000);
    targetDt.setHours(sched.hour, sched.minute, 0, 0);

    try {
        const res = await fetch("/api/gacha/goals", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                game_id: data.game_id,
                character_name: data.character_name,
                target_rank_str: data.target_rank_str,
                current_pulls: data.current_pulls,
                current_pity: data.current_pity,
                is_guaranteed: data.is_guaranteed,
                target_days: daysPlanned,
                has_daily_pass: Boolean(data.income_breakdown?.daily_pass?.active),
                success_rate: data.success_rate,
                projected_pulls: data.total_projected_pulls,
                notes: `Meta de banner planejada para ${daysPlanned} dias (${curPhase}ª Fase - chegada em ${window.formatGoalDateTimeBR(targetDt.toISOString(), true)}).`,
                created_at: nowDt.toISOString(),
                target_date: targetDt.toISOString(),
                banner_phase: curPhase
            })
        });

        if (res.ok) {
            if (typeof showToast === "function") {
                showToast(`Meta de ${data.character_name} salva! Contagem regressiva iniciada ⏳`);
            }
            window.updateGoalsCountBadge();
            if (saveBtn) {
                saveBtn.innerHTML = `<i class="fa-solid fa-check" style="color: #4ade80;"></i> Meta Salva & Tempo Correndo!`;
                setTimeout(() => {
                    saveBtn.innerHTML = `<i class="fa-solid fa-bookmark"></i> Salvar Esta Meta de Banner`;
                    saveBtn.disabled = false;
                }, 2200);
            }
        }
    } catch (e) {
        console.error("Erro ao salvar meta:", e);
        if (typeof showToast === "function") showToast("Erro ao salvar a meta no banco de dados.");
        if (saveBtn) {
            saveBtn.innerHTML = `<i class="fa-solid fa-bookmark"></i> Salvar Esta Meta de Banner`;
            saveBtn.disabled = false;
        }
    }
};

window.updateGoalsCountBadge = async function() {
    try {
        const res = await fetch("/api/gacha/goals/all");
        if (res.ok) {
            const data = await res.json();
            const count = (data.goals || []).length;
            const badge = document.getElementById("gacha-goals-count-badge");
            if (badge) badge.innerText = String(count);
        }
    } catch (e) {}
};

window.goalsCountdownTimerId = null;

window.formatGoalDateTimeBR = function(isoStr, includeTime = true) {
    if (!isoStr) return "N/A";
    const dt = new Date(isoStr);
    if (isNaN(dt.getTime())) return String(isoStr);
    const dd = String(dt.getDate()).padStart(2, '0');
    const mm = String(dt.getMonth() + 1).padStart(2, '0');
    const yyyy = dt.getFullYear();
    if (!includeTime) return `${dd}/${mm}/${yyyy}`;
    const hh = String(dt.getHours()).padStart(2, '0');
    const min = String(dt.getMinutes()).padStart(2, '0');
    return `${dd}/${mm}/${yyyy} às ${hh}:${min}`;
};

window.formatGoalLiveCountdown = function(remainingSeconds) {
    const sec = Math.max(0, Math.floor(remainingSeconds));
    const days = Math.floor(sec / 86400);
    const hours = Math.floor((sec % 86400) / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    const secs = sec % 60;
    const pad = n => String(n).padStart(2, '0');
    return `${days}d ${pad(hours)}h ${pad(mins)}m ${pad(secs)}s`;
};

window.tickGachaGoalsCountdown = function() {
    const cards = document.querySelectorAll(".gacha-goal-live-card");
    if (!cards.length) return;

    const nowMs = Date.now();
    cards.forEach(card => {
        const createdMs = parseFloat(card.dataset.createdMs || "0");
        const targetMs = parseFloat(card.dataset.targetMs || "0");
        const totalDays = Math.max(1, parseInt(card.dataset.targetDays || "21"));
        const curPulls = parseInt(card.dataset.curPulls || "0");
        const projPulls = parseInt(card.dataset.projPulls || "0");

        if (!createdMs || !targetMs) return;

        const totalSec = Math.max(1, (targetMs - createdMs) / 1000);
        const elapsedSec = Math.max(0, (nowMs - createdMs) / 1000);
        const remainingSec = Math.max(0, (targetMs - nowMs) / 1000);
        const ratio = Math.min(1, Math.max(0, elapsedSec / totalSec));
        const pct = (ratio * 100).toFixed(1);

        const daysElapsed = Math.min(totalDays, Math.floor(elapsedSec / 86400));
        const daysRemaining = remainingSec > 0 ? Math.max(0, Math.ceil(remainingSec / 86400)) : 0;
        const isArrived = remainingSec <= 0;
        const pullsNow = curPulls + Math.round(Math.max(0, projPulls - curPulls) * ratio);

        const timerEl = card.querySelector(".goal-live-countdown-val");
        const statusBadgeEl = card.querySelector(".goal-live-status-badge");
        const progressBarEl = card.querySelector(".goal-live-time-bar");
        const progressPctEl = card.querySelector(".goal-live-time-pct");
        const daysSummaryEl = card.querySelector(".goal-live-days-summary");
        const pullsNowEl = card.querySelector(".goal-live-pulls-now");

        if (isArrived) {
            if (timerEl) {
                timerEl.innerHTML = `<i class="fa-solid fa-champagne-glasses"></i> O DIA DA ATUALIZAÇÃO CHEGOU!`;
                timerEl.style.color = "#4ade80";
            }
            if (statusBadgeEl) {
                statusBadgeEl.innerHTML = `<i class="fa-solid fa-circle-check"></i> Banner Disponível!`;
                statusBadgeEl.style.background = "rgba(16, 185, 129, 0.22)";
                statusBadgeEl.style.color = "#4ade80";
                statusBadgeEl.style.borderColor = "rgba(16, 185, 129, 0.5)";
            }
            if (daysSummaryEl) {
                daysSummaryEl.innerText = `${totalDays}/${totalDays} dias concluídos • Atualização / Banner no ar!`;
            }
        } else {
            if (timerEl) {
                timerEl.innerText = window.formatGoalLiveCountdown(remainingSec);
            }
            if (daysSummaryEl) {
                daysSummaryEl.innerText = `${daysElapsed} de ${totalDays} dias decorridos • Faltam ${daysRemaining} ${daysRemaining === 1 ? 'dia' : 'dias'}`;
            }
        }

        if (progressBarEl) {
            progressBarEl.style.width = `${pct}%`;
        }
        if (progressPctEl) {
            progressPctEl.innerText = `${pct}%`;
        }
        if (pullsNowEl) {
            pullsNowEl.innerText = `~${pullsNow} tiros hoje`;
        }
    });
};

window.startGoalsLiveCountdown = function() {
    if (window.goalsCountdownTimerId) {
        clearInterval(window.goalsCountdownTimerId);
    }
    window.tickGachaGoalsCountdown();
    window.goalsCountdownTimerId = setInterval(window.tickGachaGoalsCountdown, 1000);
};

window.loadGachaGoals = async function(gameFilter = "all") {
    const grid = document.getElementById("gacha-saved-goals-grid");
    if (!grid) return;

    grid.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 40px; grid-column: 1 / -1;"><i class="fa-solid fa-spinner fa-spin fa-2x"></i><p style="margin-top: 10px;">Buscando metas salvas...</p></div>`;

    const goalFilterBtns = document.querySelectorAll(".goals-game-btn");
    goalFilterBtns.forEach(btn => {
        btn.onclick = () => {
            goalFilterBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            window.loadGachaGoals(btn.dataset.game);
        };
    });

    try {
        const res = await fetch(`/api/gacha/goals/${gameFilter === 'all' ? '' : gameFilter}`);
        const data = await res.json();
        const goals = data.goals || [];

        window.updateGoalsCountBadge();

        if (goals.length === 0) {
            if (window.goalsCountdownTimerId) {
                clearInterval(window.goalsCountdownTimerId);
                window.goalsCountdownTimerId = null;
            }
            grid.innerHTML = `
                <div style="text-align: center; color: var(--text-muted); padding: 50px 20px; grid-column: 1 / -1; background: rgba(0,0,0,0.2); border-radius: 14px; border: 1px dashed rgba(255,255,255,0.1);">
                    <i class="fa-solid fa-bullseye" style="font-size: 36px; color: #64748b; margin-bottom: 12px;"></i>
                    <h4 style="margin: 0 0 6px 0; color: #e2e8f0; font-size: 15px;">Nenhuma meta salva no momento</h4>
                    <p style="margin: 0; font-size: 12px; color: #94a3b8;">Acesse a aba <strong>Gacha Forecast</strong> para planejar seus próximos banners e salvar metas estratégicas.</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = goals.map(g => {
            const chance = g.success_rate;
            const col = chance >= 75 ? '#34d399' : (chance >= 50 ? '#fbbf24' : '#ef4444');
            const gameTitle = g.game_id === 'genshin' ? 'Genshin Impact' : (g.game_id === 'hsr' ? 'Honkai: Star Rail' : 'Zenless Zone Zero');

            const createdDt = g.created_at ? new Date(g.created_at) : new Date();
            const createdMs = isNaN(createdDt.getTime()) ? Date.now() : createdDt.getTime();
            const targetDays = Math.max(1, parseInt(g.target_days) || 21);
            const targetDt = g.target_date ? new Date(g.target_date) : new Date(createdMs + targetDays * 86400000);
            const targetMs = isNaN(targetDt.getTime()) ? (createdMs + targetDays * 86400000) : targetDt.getTime();

            const phaseNum = parseInt(g.banner_phase) || 1;
            const phaseSched = window.getBannerScheduleTime(g.game_id, phaseNum);
            const bannerTimeStr = g.banner_time || phaseSched.str;

            const createdFormatted = window.formatGoalDateTimeBR(createdDt.toISOString(), true);
            const targetFormatted = window.formatGoalDateTimeBR(targetDt.toISOString(), true);
            const isArrived = Boolean(g.is_arrived) || (targetMs <= Date.now());
            const timePct = g.time_progress_pct !== undefined ? g.time_progress_pct : 0;
            const pullsNow = g.accumulated_pulls_now !== undefined ? g.accumulated_pulls_now : g.current_pulls;
            const charIconHtml = g.character_icon
                ? `<img src="${g.character_icon}" alt="${g.character_name}" style="width: 42px; height: 42px; border-radius: 10px; object-fit: cover; border: 1px solid ${col}66; background: rgba(0,0,0,0.4);" onerror="this.style.display='none'">`
                : `<div style="width: 42px; height: 42px; border-radius: 10px; background: rgba(255,255,255,0.06); display: flex; align-items: center; justify-content: center; color: ${col};"><i class="fa-solid fa-star"></i></div>`;

            return `
                <div class="gacha-goal-live-card"
                     data-goal-id="${g.id}"
                     data-created-ms="${createdMs}"
                     data-target-ms="${targetMs}"
                     data-target-days="${targetDays}"
                     data-cur-pulls="${g.current_pulls || 0}"
                     data-proj-pulls="${g.projected_pulls || 0}"
                     style="background: rgba(15, 23, 42, 0.92); border: 1px solid rgba(255,255,255,0.08); border-top: 3px solid ${col}; border-radius: 14px; padding: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.35); display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <!-- Cabeçalho com Ícone e Meta -->
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 12px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                ${charIconHtml}
                                <div>
                                    <span style="font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; display: block;">${gameTitle}</span>
                                    <h4 style="margin: 2px 0 0 0; color: #fff; font-size: 16px; font-weight: 800; line-height: 1.2;">${g.character_name}</h4>
                                </div>
                            </div>
                            <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 4px;">
                                <span style="font-size: 12px; font-weight: 800; background: ${col}22; color: ${col}; padding: 4px 10px; border-radius: 8px; border: 1px solid ${col}44; white-space: nowrap;">
                                    Meta ${g.target_rank_str}
                                </span>
                                <span style="font-size: 10px; font-weight: 700; color: #fbbf24; background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.35); padding: 2px 8px; border-radius: 6px; white-space: nowrap;">
                                    <i class="fa-solid fa-clock"></i> ${phaseNum}ª Fase (${bannerTimeStr})
                                </span>
                            </div>
                        </div>

                        <!-- Painel do Cronômetro em Tempo Real (Correndo até a Atualização / Banner) -->
                        <div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(56, 189, 248, 0.08)); border: 1px solid rgba(56, 189, 248, 0.28); border-radius: 12px; padding: 12px; margin-bottom: 12px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; gap: 6px; flex-wrap: wrap;">
                                <span style="font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">
                                    <i class="fa-solid fa-stopwatch" style="color: #38bdf8;"></i> Tempo até o Banner / Atualização
                                </span>
                                <span class="goal-live-status-badge" style="font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 999px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.35);">
                                    <i class="fa-solid fa-hourglass-half fa-spin" style="animation-duration: 3s;"></i> Correndo o Tempo
                                </span>
                            </div>

                            <!-- Relógio Digital Regressivo -->
                            <div class="goal-live-countdown-val" style="font-family: 'Outfit', monospace; font-size: 20px; font-weight: 800; color: #f8fafc; letter-spacing: 0.5px; margin: 4px 0;">
                                ${isArrived ? '<i class="fa-solid fa-champagne-glasses"></i> O DIA DA ATUALIZAÇÃO CHEGOU!' : '--d --h --m --s'}
                            </div>
                            <div class="goal-live-days-summary" style="font-size: 11px; color: #94a3b8; margin-bottom: 8px;">
                                Calculando progresso diário...
                            </div>

                            <!-- Barra de Progresso do Tempo -->
                            <div>
                                <div style="display: flex; justify-content: space-between; font-size: 10px; color: #cbd5e1; margin-bottom: 3px;">
                                    <span>Progresso Temporal até a Atualização:</span>
                                    <strong class="goal-live-time-pct" style="color: #38bdf8;">${timePct}%</strong>
                                </div>
                                <div class="gacha-dist-bar-track" style="height: 6px; background: rgba(255,255,255,0.08);">
                                    <div class="gacha-dist-bar-fill goal-live-time-bar" style="width: ${timePct}%; background: linear-gradient(90deg, #38bdf8, #10b981); transition: width 0.5s ease;"></div>
                                </div>
                            </div>

                            <!-- Datas de Criação e de Chegada do Banner -->
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 10px; padding-top: 8px; border-top: 1px dashed rgba(255,255,255,0.1); font-size: 10px;">
                                <div>
                                    <span style="color: var(--text-muted); display: block;"><i class="fa-regular fa-calendar-plus" style="color: #94a3b8;"></i> Criado em:</span>
                                    <strong style="color: #e2e8f0;">${createdFormatted}</strong>
                                </div>
                                <div style="text-align: right;">
                                    <span style="color: var(--text-muted); display: block;"><i class="fa-solid fa-rocket" style="color: #fbbf24;"></i> Chegada do Banner:</span>
                                    <strong style="color: #fbbf24;">${targetFormatted}</strong>
                                </div>
                            </div>
                        </div>

                        <!-- Barra de Probabilidade Monte Carlo -->
                        <div style="margin: 10px 0 12px 0;">
                            <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                                <span style="color: var(--text-muted);">Probabilidade Calculada:</span>
                                <strong style="color: ${col};">${chance}%</strong>
                            </div>
                            <div class="gacha-dist-bar-track" style="height: 8px;">
                                <div class="gacha-dist-bar-fill target-reached" style="width: ${chance}%; background: ${col};"></div>
                            </div>
                        </div>

                        <!-- Resumo dos Dados -->
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 11px; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px; margin-bottom: 12px;">
                            <div>
                                <span style="color: var(--text-muted); display: block;">Tiros (Início ➔ Banner):</span>
                                <strong style="color: #fbbf24; font-size: 12px;">${g.current_pulls} ➔ ${g.projected_pulls} tiros</strong>
                                <span class="goal-live-pulls-now" style="display: block; font-size: 10px; color: #38bdf8; font-weight: 600;">~${pullsNow} tiros hoje</span>
                            </div>
                            <div>
                                <span style="color: var(--text-muted); display: block;">Prazo Planejado:</span>
                                <strong style="color: #38bdf8; font-size: 12px;">${targetDays} dias totais</strong>
                            </div>
                            <div>
                                <span style="color: var(--text-muted); display: block;">Pity Inicial:</span>
                                <strong style="color: #cbd5e1;">${g.current_pity} (${g.is_guaranteed ? 'Garantido' : '50/50'})</strong>
                            </div>
                            <div>
                                <span style="color: var(--text-muted); display: block;">Passe da Lua/Exp:</span>
                                <strong style="color: ${g.has_daily_pass ? '#34d399' : '#94a3b8'};">${g.has_daily_pass ? 'Ativo (+90/d)' : 'Inativo'}</strong>
                            </div>
                        </div>
                    </div>

                    <!-- Botões de Ação -->
                    <div style="display: flex; gap: 8px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 10px;">
                        <button onclick="window.deleteGachaGoal(${g.id})" class="secondary-btn" style="padding: 6px 10px; font-size: 11px; color: #f87171; border-color: rgba(239, 68, 68, 0.4); flex: 1;">
                            <i class="fa-solid fa-trash-can"></i> Excluir Meta
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        window.startGoalsLiveCountdown();

    } catch (e) {
        console.error("Erro ao carregar metas:", e);
        grid.innerHTML = `<div style="text-align: center; color: #ef4444; padding: 20px; grid-column: 1 / -1;">Erro ao carregar metas salvas.</div>`;
    }
};

window.deleteGachaGoal = async function(goalId) {
    if (!confirm("Deseja realmente excluir esta meta de banner?")) return;
    try {
        const res = await fetch(`/api/gacha/goals/${goalId}`, { method: "DELETE" });
        if (res.ok) {
            if (typeof showToast === "function") showToast("Meta excluída com sucesso.");
            const activeBtn = document.querySelector(".goals-game-btn.active");
            window.loadGachaGoals(activeBtn ? activeBtn.dataset.game : "all");
        }
    } catch (e) {
        console.error("Erro ao excluir meta:", e);
    }
};


// ==========================================================================
// CONTROLADOR DO ÍNDICE DE SORTE & EFICIÊNCIA DE ROLAGENS (LUCK DASHBOARD)
// ==========================================================================
window.initLuckDashboard = function() {
    const btns = document.querySelectorAll(".tab-luck-game-btn");
    btns.forEach(btn => {
        btn.onclick = () => {
            btns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const gameId = btn.getAttribute("data-game");
            window.loadLuckDashboard(gameId);
        };
    });

    const activeBtn = document.querySelector(".tab-luck-game-btn.active");
    const gameId = activeBtn ? activeBtn.getAttribute("data-game") : "genshin";
    window.loadLuckDashboard(gameId);
};

window.loadLuckDashboard = async function(gameId) {
    const bodyEl = document.getElementById("tab-luck-body");
    if (!bodyEl) return;

    bodyEl.innerHTML = `
        <div style="text-align: center; padding: 60px 20px;">
            <i class="fa-solid fa-spinner fa-spin" style="font-size: 32px; color: #10b981; margin-bottom: 16px;"></i>
            <p style="color: #94a3b8; font-size: 15px;">Analisando qualidade das rolagens das relíquias do ${gameId.toUpperCase()}...</p>
        </div>
    `;

    try {
        const res = await fetch(`/api/luck-index/${gameId}`);
        const data = await res.json();
        window.renderLuckDashboard(data);
    } catch (e) {
        console.error("Erro ao carregar dashboard de sorte:", e);
        bodyEl.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #ef4444;">
                <i class="fa-solid fa-triangle-exclamation" style="font-size: 32px; margin-bottom: 12px;"></i>
                <p>Erro ao carregar dados do Índice de Sorte.</p>
            </div>
        `;
    }
};

function renderSubstatsPillList(substatsAnalyzed, rawFallbackStr) {
    if (substatsAnalyzed && substatsAnalyzed.length > 0) {
        return `
            <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;">
                ${substatsAnalyzed.map(sub => `
                    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid ${sub.status_color}55; border-radius: 8px; padding: 4px 8px; font-size: 11px; display: inline-flex; align-items: center; gap: 6px;">
                        <span style="color: #f8fafc; font-weight: 600;">${sub.raw_text}</span>
                        <span style="color: ${sub.status_color}; font-weight: 700; background: ${sub.status_color}22; padding: 2px 6px; border-radius: 4px; font-size: 10px; border: 1px solid ${sub.status_color}44;">
                            ${sub.status_badge}
                        </span>
                    </div>
                `).join('')}
            </div>
        `;
    }
    return `<div style="font-size: 11px; color: #cbd5e1; margin-top: 4px;">${rawFallbackStr}</div>`;
}

window.renderLuckDashboard = function(data) {
    const bodyEl = document.getElementById("tab-luck-body");
    if (!bodyEl) return;

    if (!data || data.total_relics_analyzed === 0) {
        bodyEl.innerHTML = `
            <div style="text-align: center; padding: 60px 20px;" class="overview-card">
                <i class="fa-solid fa-shield-halved" style="font-size: 40px; color: #64748b; margin-bottom: 16px;"></i>
                <h3 style="color: #f8fafc; margin-bottom: 8px;">Nenhuma Relíquia Encontrada</h3>
                <p style="color: #94a3b8; max-width: 500px; margin: 0 auto 20px auto;">
                    Sincronize seu Roster com o HoYoLAB para analisar a sorte e a eficiência das rolagens de atributos dos seus equipamentos.
                </p>
            </div>
        `;
        return;
    }

    const god = data.god_roll;
    const cursed = data.cursed_roll;

    let html = `
        <!-- HERO CARDS (3 COLUNAS) -->
        <div class="luck-hero-grid">
            <!-- CARD 1: SORTE GERAL DA CONTA -->
            <div class="luck-overview-card">
                <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; display: flex; align-items: center; justify-content: space-between;">
                    <span>Pontuação de Sorte da Conta</span>
                    <i class="fa-solid fa-clover" style="color: #10b981;"></i>
                </div>
                <div class="luck-gauge-box">
                    <div class="luck-gauge-value">${data.overall_account_luck}%</div>
                    <div style="font-size: 14px; font-weight: 700; color: #f8fafc; margin-top: 4px;">${data.luck_title}</div>
                    <div style="display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); margin-top: 8px;">
                        ${data.luck_badge}
                    </div>
                </div>
                <div style="font-size: 12px; color: #64748b; text-align: center;">
                    Baseado em ${data.total_relics_analyzed} relíquias equipadas
                </div>
            </div>

            <!-- CARD 2: GOD ROLL DA CONTA -->
            <div class="luck-overview-card god-roll-card">
                <div style="font-size: 12px; color: #fbbf24; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; display: flex; align-items: center; justify-content: space-between;">
                    <span>🏆 A Peça Mais Sortuda (God Roll)</span>
                    <span style="font-size: 11px; background: rgba(245, 158, 11, 0.2); color: #fbbf24; padding: 2px 8px; border-radius: 12px;">Top #1</span>
                </div>
                ${god ? `
                <div style="display: flex; align-items: center; gap: 14px; margin: 12px 0;">
                    <img src="${god.character_icon || '/assets/logo.svg'}" style="width: 54px; height: 54px; border-radius: 50%; border: 2px solid #f59e0b; object-fit: cover; flex-shrink: 0;">
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-size: 16px; font-weight: bold; color: #f8fafc;">${god.character_name}</div>
                        <div style="display: flex; align-items: center; gap: 8px; margin: 6px 0; flex-wrap: wrap;">
                            ${god.relic_icon ? `<img src="${god.relic_icon}" style="width: 32px; height: 32px; object-fit: contain; background: rgba(0,0,0,0.4); border-radius: 6px; border: 1px solid rgba(245, 158, 11, 0.4); padding: 2px;">` : ''}
                            <span style="font-size: 12px; font-weight: 800; color: #fbbf24; background: rgba(245, 158, 11, 0.2); padding: 3px 10px; border-radius: 6px; border: 1px solid rgba(245, 158, 11, 0.4); display: inline-flex; align-items: center; gap: 4px;">
                                ${god.slot_display || god.slot}
                            </span>
                            <span style="font-size: 12px; color: #e2e8f0; font-weight: 500;">${god.relic_name}</span>
                        </div>
                        <div style="font-size: 11px; color: #cbd5e1;">Atributo Principal: <strong style="color: #38bdf8;">${god.main_stat}</strong></div>
                    </div>
                </div>
                <div style="background: rgba(0, 0, 0, 0.3); padding: 10px; border-radius: 10px; font-size: 11px; color: #e2e8f0; margin-bottom: 10px;">
                    <div style="font-weight: 700; color: #94a3b8; margin-bottom: 4px;">Avaliação de Substatus & Rolagens:</div>
                    ${renderSubstatsPillList(god.substats_analyzed, god.substats_str)}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 12px; color: #34d399; font-weight: bold;">Sorte: ${god.luck_score}% (${god.luck_badge})</span>
                    <span style="font-size: 11px; color: #94a3b8;">Roll Value (RV): ${god.total_rv}</span>
                </div>
                ` : '<div style="color:#94a3b8;">Nenhuma peça encontrada</div>'}
            </div>

            <!-- CARD 3: CURSED ROLL DA CONTA -->
            <div class="luck-overview-card cursed-roll-card">
                <div style="font-size: 12px; color: #f87171; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; display: flex; align-items: center; justify-content: space-between;">
                    <span>💀 A Peça Mais Amaldiçoada</span>
                    <span style="font-size: 11px; background: rgba(239, 68, 68, 0.2); color: #f87171; padding: 2px 8px; border-radius: 12px;">Cursed</span>
                </div>
                ${cursed ? `
                <div style="display: flex; align-items: center; gap: 14px; margin: 12px 0;">
                    <img src="${cursed.character_icon || '/assets/logo.svg'}" style="width: 54px; height: 54px; border-radius: 50%; border: 2px solid #ef4444; object-fit: cover; flex-shrink: 0;">
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-size: 16px; font-weight: bold; color: #f8fafc;">${cursed.character_name}</div>
                        <div style="display: flex; align-items: center; gap: 8px; margin: 6px 0; flex-wrap: wrap;">
                            ${cursed.relic_icon ? `<img src="${cursed.relic_icon}" style="width: 32px; height: 32px; object-fit: contain; background: rgba(0,0,0,0.4); border-radius: 6px; border: 1px solid rgba(239, 68, 68, 0.4); padding: 2px;">` : ''}
                            <span style="font-size: 12px; font-weight: 800; color: #f87171; background: rgba(239, 68, 68, 0.2); padding: 3px 10px; border-radius: 6px; border: 1px solid rgba(239, 68, 68, 0.4); display: inline-flex; align-items: center; gap: 4px;">
                                ${cursed.slot_display || cursed.slot}
                            </span>
                            <span style="font-size: 12px; color: #e2e8f0; font-weight: 500;">${cursed.relic_name}</span>
                        </div>
                        <div style="font-size: 11px; color: #cbd5e1;">Atributo Principal: <strong style="color: #f87171;">${cursed.main_stat}</strong></div>
                    </div>
                </div>
                <div style="background: rgba(0, 0, 0, 0.3); padding: 10px; border-radius: 10px; font-size: 11px; color: #e2e8f0; margin-bottom: 10px;">
                    <div style="font-weight: 700; color: #94a3b8; margin-bottom: 4px;">Avaliação de Substatus & Rolagens:</div>
                    ${renderSubstatsPillList(cursed.substats_analyzed, cursed.substats_str)}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 12px; color: #ef4444; font-weight: bold;">Sorte: ${cursed.luck_score}% (${cursed.luck_badge})</span>
                    <span style="font-size: 11px; color: #94a3b8;">Roll Value (RV): ${cursed.total_rv}</span>
                </div>
                ` : '<div style="color:#94a3b8;">Nenhuma peça encontrada</div>'}
            </div>
        </div>

        <!-- PERSONAGENS MAIS SORTUDOS E MENOS SORTUDOS -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
            ${data.luckiest_character ? `
            <div class="overview-card" style="border-left: 4px solid #10b981; margin:0;">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <img src="${data.luckiest_character.character_icon || '/assets/logo.svg'}" style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid #10b981; object-fit: cover;">
                    <div style="flex: 1;">
                        <div style="font-size: 11px; color: #34d399; font-weight: 700; text-transform: uppercase;">🌟 Personagem Mais Sortudo</div>
                        <div style="font-size: 16px; font-weight: bold; color: #fff;">${data.luckiest_character.character_name}</div>
                        <div style="font-size: 12px; color: #94a3b8;">Média de Sorte: <strong style="color: #34d399;">${data.luckiest_character.avg_luck}%</strong> (${data.luckiest_character.relic_count} relíquias)</div>
                    </div>
                </div>
            </div>
            ` : ''}

            ${data.cursed_character ? `
            <div class="overview-card" style="border-left: 4px solid #ef4444; margin:0;">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <img src="${data.cursed_character.character_icon || '/assets/logo.svg'}" style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid #ef4444; object-fit: cover;">
                    <div style="flex: 1;">
                        <div style="font-size: 11px; color: #f87171; font-weight: 700; text-transform: uppercase;">🌧️ Personagem Mais Azarado</div>
                        <div style="font-size: 16px; font-weight: bold; color: #fff;">${data.cursed_character.character_name}</div>
                        <div style="font-size: 12px; color: #94a3b8;">Média de Sorte: <strong style="color: #f87171;">${data.cursed_character.avg_luck}%</strong> (${data.cursed_character.relic_count} relíquias)</div>
                    </div>
                </div>
            </div>
            ` : ''}
        </div>

        <!-- LISTA DE SORTE POR PERSONAGEM -->
        <div class="overview-card" style="margin-bottom: 24px;">
            <h3 style="margin: 0 0 16px 0; font-size: 16px; color: #f8fafc; display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-users-gear" style="color: #10b981;"></i> Ranking de Sorte dos Personagens do Roster
            </h3>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                ${(data.character_breakdown || []).map(c => {
                    const luckClass = c.avg_luck >= 75 ? 'high' : (c.avg_luck >= 50 ? 'mid' : 'low');
                    const color = c.avg_luck >= 75 ? '#34d399' : (c.avg_luck >= 50 ? '#fbbf24' : '#f87171');
                    return `
                    <div class="luck-char-row">
                        <img src="${c.character_icon || '/assets/logo.svg'}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid ${color};">
                        <div style="flex: 1;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                                <span style="font-weight: 600; color: #f8fafc; font-size: 14px;">${c.character_name} <small style="color: #94a3b8; font-weight: normal;">(Nv. ${c.level} • ${c.rank_str})</small></span>
                                <strong style="color: ${color}; font-size: 14px;">${c.avg_luck}%</strong>
                            </div>
                            <div class="luck-bar-bg">
                                <div class="luck-bar-fill ${luckClass}" style="width: ${c.avg_luck}%;"></div>
                            </div>
                        </div>
                    </div>
                    `;
                }).join('')}
            </div>
        </div>

        <!-- TABELA DAS MELHORES RELÍQUIAS DO INVENTÁRIO -->
        <div class="overview-card">
            <h3 style="margin: 0 0 16px 0; font-size: 16px; color: #f8fafc; display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-gem" style="color: #fbbf24;"></i> Top Relíquias mais Sortudas do Inventário (Roll Value)
            </h3>
            <div style="display: flex; flex-direction: column; gap: 10px;">
                ${(data.all_relics || []).map((r, idx) => `
                <div style="display: flex; align-items: center; gap: 14px; padding: 12px 14px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px;">
                    <div style="font-weight: 900; font-size: 16px; color: ${idx < 3 ? '#fbbf24' : '#64748b'}; width: 28px; text-align: center;">#${idx + 1}</div>
                    <img src="${r.character_icon || '/assets/logo.svg'}" style="width: 42px; height: 42px; border-radius: 50%; object-fit: cover; flex-shrink: 0;">
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-size: 13px; font-weight: bold; color: #f8fafc; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                            ${r.relic_icon ? `<img src="${r.relic_icon}" style="width: 28px; height: 28px; object-fit: contain; background: rgba(0,0,0,0.4); border-radius: 6px; border: 1px solid rgba(245, 158, 11, 0.3); padding: 2px;">` : ''}
                            <span style="color: #fbbf24; font-size: 11px; font-weight: 700; background: rgba(245, 158, 11, 0.15); padding: 2px 8px; border-radius: 6px; border: 1px solid rgba(245, 158, 11, 0.3);">
                                ${r.slot_display || r.slot}
                            </span>
                            <span>${r.relic_name}</span>
                            <span style="font-weight: normal; color: #94a3b8;">(${r.character_name})</span>
                        </div>
                        ${renderSubstatsPillList(r.substats_analyzed, r.substats_str)}
                    </div>
                    <div style="text-align: right; flex-shrink: 0;">
                        <div style="font-size: 15px; font-weight: bold; color: ${r.luck_score >= 75 ? '#34d399' : '#fbbf24'};">${r.luck_score}%</div>
                        <div style="font-size: 10px; color: #94a3b8;">${r.luck_badge}</div>
                    </div>
                </div>
                `).join('')}
            </div>
        </div>
    `;

    bodyEl.innerHTML = html;
};

// ==========================================================================
// MOTOR DE ANIMAÇÃO INTERATIVA E SINTETIZADOR DE WISH / GACHA
// ==========================================================================

let wishAudioCtx = null;
let wishAnimId = null;
let wishAnimRunning = false;
let wishAnimTimeout = null;

// 1. Sintetizador de Áudio da Web Audio API
function playWishSound(type, rarity) {
    try {
        if (!wishAudioCtx) {
            wishAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (wishAudioCtx.state === 'suspended') {
            wishAudioCtx.resume();
        }

        const now = wishAudioCtx.currentTime;
        if (type === 'launch') {
            const osc = wishAudioCtx.createOscillator();
            const gain = wishAudioCtx.createGain();
            osc.connect(gain);
            gain.connect(wishAudioCtx.destination);
            osc.type = 'sine';
            osc.frequency.setValueAtTime(150, now);
            osc.frequency.exponentialRampToValueAtTime(800, now + 1.2);
            gain.gain.setValueAtTime(0.05, now);
            gain.gain.linearRampToValueAtTime(0.2, now + 0.8);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 1.5);
            osc.start(now);
            osc.stop(now + 1.5);
        } else if (type === 'reveal') {
            const freqMap = {
                5: [523.25, 659.25, 783.99, 1046.50],
                4: [440.00, 554.37, 659.25],
                3: [329.63, 392.00]
            };
            const freqs = freqMap[rarity] || freqMap[3];
            
            freqs.forEach((f, idx) => {
                const subOsc = wishAudioCtx.createOscillator();
                const subGain = wishAudioCtx.createGain();
                subOsc.type = rarity === 5 ? 'triangle' : 'sine';
                subOsc.frequency.setValueAtTime(f, now + idx * 0.08);
                subGain.connect(wishAudioCtx.destination);
                subOsc.connect(subGain);

                subGain.gain.setValueAtTime(0.01, now + idx * 0.08);
                subGain.gain.linearRampToValueAtTime(rarity === 5 ? 0.25 : 0.15, now + idx * 0.08 + 0.1);
                subGain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.08 + 1.8);

                subOsc.start(now + idx * 0.08);
                subOsc.stop(now + idx * 0.08 + 1.8);
            });
        }
    } catch (e) {
        console.warn("[Wish Sound] AudioContext não disponível:", e);
    }
}

// Helper para gerar URL de Splash Art / Card do Personagem via Proxy
function getWishCharacterSplash(gameId, charName) {
    if (!charName) return "/assets/logo.svg";
    let clean = charName.replace(/\s*\(.*?\)/g, '').trim();
    
    let slug = clean.toLowerCase()
        .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
        
    const slugFixes = {
        "yumemizuki-mizuki": "mizuki",
        "yumemizukimizuki": "mizuki",
        "mizuki": "mizuki",
        "dan-heng-imbibitor-lunae": "imbibitor-lunae",
        "march-7th": "march-7th",
        "trailblazer": "trailblazer-physical",
        "nekoma": "nekomata",
        "nekomata": "nekomata",
        "soldier-11": "soldier-11",
        "soldier11": "soldier-11",
        "lycaon": "von-lycaon",
        "von-lycaon": "von-lycaon"
    };
    if (slugFixes[slug]) slug = slugFixes[slug];

    if (gameId === "genshin") {
        return `/api/proxy_image?url=${encodeURIComponent('https://cdn.prydwen.gg/images/genshin-impact/characters/' + slug + '_card.webp')}`;
    } else if (gameId === "hsr") {
        return `/api/proxy_image?url=${encodeURIComponent('https://cdn.prydwen.gg/images/star-rail/characters/' + slug + '_card.webp')}`;
    } else if (gameId === "zzz") {
        return `/api/proxy_image?url=${encodeURIComponent('https://cdn.prydwen.gg/images/zenless-zone-zero/characters/' + slug + '_full.webp')}`;
    }
    return "/assets/logo.svg";
}

// 2. Lógica do Sorteio Individual com Soft Pity e 50/50 Real
function rollSingleWishItem(gameId, pity, isGuaranteed, targetCharName) {
    pity = parseInt(pity) || 0;
    pity += 1;

    let base5StarChance = 0.006;
    if (pity >= 74) {
        base5StarChance += (pity - 73) * 0.06;
    }
    base5StarChance = Math.min(1.0, base5StarChance);

    const rand5Star = Math.random();
    if (rand5Star <= base5StarChance) {
        let won5050 = true;
        let cleanTarget = (targetCharName || "Personagem 5★ Limitado").replace(/\s*\(.*?\)/g, '').trim();
        let charName = cleanTarget;

        if (!isGuaranteed && Math.random() > 0.5) {
            won5050 = false;
            const standards = {
                genshin: ["Jean", "Keqing", "Qiqi", "Dehya", "Diluc", "Mona", "Tighnari", "Yumemizuki Mizuki"],
                hsr: ["Himeko", "Welt", "Bronya", "Gepard", "Clara", "Yanqing", "Bailu"],
                zzz: ["Nekomata", "Lycaon", "Soldier 11", "Koleda", "Grace", "Rina"]
            };
            const stdList = standards[gameId] || standards.genshin;
            charName = stdList[Math.floor(Math.random() * stdList.length)];
        } else {
            charName = cleanTarget;
        }

        return {
            rarity: 5,
            name: charName,
            pitySpent: pity,
            won5050: won5050,
            isGuaranteedNext: !won5050,
            newPity: 0,
            splashArt: getWishCharacterSplash(gameId, charName)
        };
    }

    const rand4Star = Math.random();
    if (rand4Star <= 0.051 || pity % 10 === 0) {
        const pool4Star = {
            genshin: [
                "Bennett", "Xingqiu", "Xiangling", "Fischl", "Sucrose", "Noelle", "Barbara", "Razor", 
                "Beidou", "Ningguang", "Chongyun", "Diona", "Xinyan", "Rosaria", "Yanfei", "Sayu", 
                "Kujou Sara", "Thoma", "Gorou", "Yunjin", "Kuki Shinobu", "Heizou", "Collei", "Dori", 
                "Candace", "Layla", "Faruzan", "Yaoyao", "Mika", "Kaveh", "Kirara", "Freminet", 
                "Charlotte", "Chevreuse", "Gaming", "Sethos", "Kachina", "Ororun", "Lanyan"
            ],
            hsr: [
                "March 7th", "Dan Heng", "Arlan", "Asta", "Herta", "Serval", "Natasha", "Pela", 
                "Sampo", "Hook", "Qingque", "Tingyun", "Sushang", "Yukong", "Luka", "Lynx", 
                "Guinaifen", "Hanya", "Xueyi", "Misha", "Gallagher", "Moze"
            ],
            zzz: [
                "Anby", "Billy", "Nicole", "Corin", "Anton", "Ben", "Soukaku", "Seth", "Lucy", "Piper", "Pulchra"
            ]
        };
        const list4 = pool4Star[gameId] || pool4Star.genshin;
        const char4Name = list4[Math.floor(Math.random() * list4.length)];

        return {
            rarity: 4,
            name: char4Name,
            pitySpent: pity,
            won5050: true,
            isGuaranteedNext: isGuaranteed,
            newPity: pity,
            splashArt: getWishCharacterSplash(gameId, char4Name)
        };
    }

    return {
        rarity: 3,
        name: "Arma 3★ (Mochileiro)",
        pitySpent: pity,
        won5050: true,
        isGuaranteedNext: isGuaranteed,
        newPity: pity,
        splashArt: "/assets/logo.svg"
    };
}

// 3. Controlador da Animação Pure CSS FX por Jogo (Genshin Meteoro, HSR Warp, ZZZ Signal Glitch)
function animateWishCSS(gameId, maxRarity, onComplete) {
    if (window.wishAnimTimeout) {
        clearTimeout(window.wishAnimTimeout);
        window.wishAnimTimeout = null;
    }

    const modal = document.getElementById("wish-animation-modal");
    const revealContainer = document.getElementById("wish-reveal-container");

    const fxGenshin = document.getElementById("wish-fx-genshin");
    const fxHsr = document.getElementById("wish-fx-hsr");
    const fxZzz = document.getElementById("wish-fx-zzz");

    if (modal) {
        modal.style.display = "flex";
        modal.style.opacity = "1";
        modal.style.visibility = "visible";
        modal.style.zIndex = "999999";
    }

    if (revealContainer) revealContainer.style.display = "none";

    if (fxGenshin) fxGenshin.style.display = "none";
    if (fxHsr) fxHsr.style.display = "none";
    if (fxZzz) fxZzz.style.display = "none";

    const rarityClass = maxRarity === 5 ? "gold" : (maxRarity === 4 ? "purple" : "blue");

    if (gameId === "genshin") {
        if (fxGenshin) fxGenshin.style.display = "block";
        const meteor = document.getElementById("wish-fx-meteor");
        const shockwave = document.getElementById("wish-fx-shockwave");
        if (meteor && shockwave) {
            meteor.className = "wish-fx-meteor";
            shockwave.className = "wish-fx-shockwave";
            void meteor.offsetWidth;
            meteor.className = `wish-fx-meteor animating ${rarityClass}`;
            shockwave.className = `wish-fx-shockwave animating ${rarityClass}`;
        }
    } else if (gameId === "hsr") {
        if (fxHsr) fxHsr.style.display = "block";
        const warpStar = document.getElementById("hsr-warp-star");
        if (warpStar) {
            warpStar.className = "hsr-warp-star-trail";
            void warpStar.offsetWidth;
            warpStar.className = `hsr-warp-star-trail animating ${rarityClass}`;
        }
    } else {
        if (fxZzz) fxZzz.style.display = "block";
        const signalBox = document.getElementById("zzz-signal-box");
        if (signalBox) {
            signalBox.className = "zzz-signal-box";
            void signalBox.offsetWidth;
            signalBox.className = `zzz-signal-box animating ${rarityClass}`;
        }
    }

    try { playWishSound('launch', maxRarity); } catch (e) {}

    window.wishAnimTimeout = setTimeout(() => {
        if (fxGenshin) fxGenshin.style.display = "none";
        if (fxHsr) fxHsr.style.display = "none";
        if (fxZzz) fxZzz.style.display = "none";

        if (onComplete) onComplete();
    }, 1200);
}

let wishCurrentResults = [];
window.wishCurrentIndex = 0;
let wishIsMultiPull = false;
let wishGameId = "genshin";

// 4. Controlador Principal da Animação do Wish
window.startWishAnimation = function(pullsCount = 1) {
    try {
        const activePill = document.querySelector("#gacha-game-pills .gacha-game-pill.active");
        const gameIdHidden = document.getElementById("tab-gacha-game-select")?.value;
        wishGameId = (activePill ? activePill.dataset.game : (gameIdHidden || "genshin")).toLowerCase();

        const pityInput = document.getElementById("tab-gacha-pity");
        const guatSelect = document.getElementById("tab-gacha-guaranteed");
        const charSelect = document.getElementById("tab-gacha-char-select");

        const currentPity = parseInt(pityInput?.value || 35);
        const isGuaranteed = guatSelect?.value === "true";
        
        let selectedCharName = "Personagem 5★ Limitado";
        if (charSelect && charSelect.selectedIndex >= 0 && charSelect.options[charSelect.selectedIndex]) {
            selectedCharName = charSelect.options[charSelect.selectedIndex].text;
        }

        wishCurrentResults = [];
        let curPity = currentPity;
        let curGuat = isGuaranteed;

        for (let i = 0; i < pullsCount; i++) {
            const item = rollSingleWishItem(wishGameId, curPity, curGuat, selectedCharName);
            wishCurrentResults.push(item);
            curPity = item.newPity;
            curGuat = item.isGuaranteedNext;
        }

        if (pityInput) pityInput.value = curPity;
        if (guatSelect) guatSelect.value = curGuat ? "true" : "false";

        window.wishCurrentIndex = 0;
        wishIsMultiPull = pullsCount > 1;
        const maxRarity = Math.max(...wishCurrentResults.map(r => r.rarity));

        animateWishCSS(wishGameId, maxRarity, () => {
            showWishItemAtIndex(0);
        });
    } catch (err) {
        console.error("[Wish Animation Error]", err);
    }
};

// 5. Exibe Item Individual por Índice (Sequência Item por Item)
window.showWishItemAtIndex = function(index) {
    if (index >= wishCurrentResults.length) {
        showWishSummaryGrid();
        return;
    }

    window.wishCurrentIndex = index;
    const item = wishCurrentResults[index];
    const maxRarity = item.rarity;

    const revealContainer = document.getElementById("wish-reveal-container");
    const summaryContainer = document.getElementById("wish-summary-container");

    if (summaryContainer) summaryContainer.style.display = "none";

    if (revealContainer) {
        revealContainer.style.display = "flex";
        revealContainer.style.animation = 'none';
        void revealContainer.offsetWidth;
        revealContainer.style.animation = 'wishCardPop 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards';
    }

    try { playWishSound('reveal', maxRarity); } catch (e) {}

    const glow = document.getElementById("wish-card-glow");
    if (glow) {
        if (maxRarity === 5) {
            glow.style.background = "radial-gradient(circle, #f59e0b 0%, #fbbf24 45%, rgba(245, 158, 11, 0) 75%)";
        } else if (maxRarity === 4) {
            glow.style.background = "radial-gradient(circle, #a855f7 0%, #c084fc 45%, rgba(168, 85, 247, 0) 75%)";
        } else {
            glow.style.background = "radial-gradient(circle, #0284c7 0%, #38bdf8 45%, rgba(56, 189, 248, 0) 75%)";
        }
    }

    const gameBadge = document.getElementById("wish-card-game-badge");
    if (gameBadge) {
        const titles = { genshin: "Genshin Impact", hsr: "Honkai: Star Rail", zzz: "Zenless Zone Zero" };
        gameBadge.innerText = titles[wishGameId] || "Gacha Wish";
        if (maxRarity === 5) {
            gameBadge.style.color = "#fbbf24";
            gameBadge.style.borderColor = "rgba(245, 158, 11, 0.4)";
            gameBadge.style.background = "rgba(245, 158, 11, 0.2)";
        } else if (maxRarity === 4) {
            gameBadge.style.color = "#c084fc";
            gameBadge.style.borderColor = "rgba(168, 85, 247, 0.4)";
            gameBadge.style.background = "rgba(168, 85, 247, 0.2)";
        } else {
            gameBadge.style.color = "#38bdf8";
            gameBadge.style.borderColor = "rgba(56, 189, 248, 0.4)";
            gameBadge.style.background = "rgba(56, 189, 248, 0.2)";
        }
    }

    const cardArt = document.getElementById("wish-card-art");
    if (cardArt) {
        if (item.rarity >= 4) {
            cardArt.src = item.splashArt || getWishCharacterSplash(wishGameId, item.name);
        } else {
            cardArt.src = "/assets/logo.svg";
        }
    }

    const cardName = document.getElementById("wish-card-name");
    if (cardName) cardName.innerText = item.name;

    const cardStars = document.getElementById("wish-card-stars");
    if (cardStars) {
        cardStars.innerText = "★".repeat(item.rarity);
        cardStars.style.color = maxRarity === 5 ? "#fbbf24" : (maxRarity === 4 ? "#c084fc" : "#38bdf8");
    }

    const cardBadge = document.getElementById("wish-card-status-badge");
    if (cardBadge) {
        if (maxRarity === 5) {
            cardBadge.style.color = "#34d399";
            cardBadge.style.borderColor = "rgba(52, 211, 153, 0.35)";
            cardBadge.style.background = "rgba(52, 211, 153, 0.15)";
            cardBadge.innerHTML = `<i class="fa-solid fa-trophy" style="color: #fbbf24;"></i> ${item.won5050 ? '5★ LIMITADO ADQUIRIDO!' : '5★ MOCHILEIRO (Perdeu 50/50)'}`;
        } else if (maxRarity === 4) {
            cardBadge.style.color = "#c084fc";
            cardBadge.style.borderColor = "rgba(168, 85, 247, 0.35)";
            cardBadge.style.background = "rgba(168, 85, 247, 0.15)";
            cardBadge.innerHTML = `<i class="fa-solid fa-sparkles" style="color: #c084fc;"></i> PERSONAGEM 4★ ADQUIRIDO!`;
        } else {
            cardBadge.style.color = "#38bdf8";
            cardBadge.style.borderColor = "rgba(56, 189, 248, 0.35)";
            cardBadge.style.background = "rgba(56, 189, 248, 0.15)";
            cardBadge.innerHTML = `<i class="fa-solid fa-shield" style="color: #38bdf8;"></i> Item 3★ Adquirido`;
        }
    }

    const cardPity = document.getElementById("wish-card-pity-text");
    if (cardPity) {
        if (wishIsMultiPull) {
            cardPity.innerText = `Item ${index + 1} de ${wishCurrentResults.length} • Tiro nº ${item.pitySpent}`;
        } else {
            cardPity.innerText = `Tiro nº ${item.pitySpent} • ${item.pitySpent >= 74 ? 'Soft Pity Ativo' : 'Pity Normal'}`;
        }
    }

    const nextBtn = document.getElementById("wish-next-item-btn");
    const normalActions = document.getElementById("wish-single-actions-bar");

    if (wishIsMultiPull && wishCurrentResults.length > 1) {
        if (nextBtn) nextBtn.style.display = "flex";
        if (normalActions) normalActions.style.display = "none";
        
        const nextBtnLabel = document.getElementById("wish-next-btn-label");
        if (nextBtnLabel) {
            nextBtnLabel.innerText = index === wishCurrentResults.length - 1 ? "Ver Resumo dos 10 Tiros ➔" : `Próximo Item (${index + 1}/${wishCurrentResults.length}) ➔`;
        }
    } else {
        if (nextBtn) nextBtn.style.display = "none";
        if (normalActions) normalActions.style.display = "flex";
    }
};

// 6. Exibe a Tela de Resumo Final dos 10 Tiros (Lado a Lado)
window.showWishSummaryGrid = function() {
    const revealContainer = document.getElementById("wish-reveal-container");
    const summaryContainer = document.getElementById("wish-summary-container");
    const gridBox = document.getElementById("wish-summary-grid-box");

    if (revealContainer) revealContainer.style.display = "none";
    if (summaryContainer) {
        summaryContainer.style.display = "flex";
        summaryContainer.style.animation = 'none';
        void summaryContainer.offsetWidth;
        summaryContainer.style.animation = 'wishCardPop 0.4s ease-out forwards';
    }

    if (gridBox) {
        gridBox.innerHTML = wishCurrentResults.map((r, idx) => {
            const borderCol = r.rarity === 5 ? '#fbbf24' : (r.rarity === 4 ? '#a855f7' : '#38bdf8');
            const bgGradient = r.rarity === 5 
                ? 'linear-gradient(180deg, rgba(251, 191, 36, 0.3) 0%, rgba(15, 23, 42, 0.95) 100%)' 
                : (r.rarity === 4 
                    ? 'linear-gradient(180deg, rgba(168, 85, 247, 0.3) 0%, rgba(15, 23, 42, 0.95) 100%)' 
                    : 'linear-gradient(180deg, rgba(56, 189, 248, 0.2) 0%, rgba(15, 23, 42, 0.95) 100%)');

            const artUrl = r.rarity >= 4 ? (r.splashArt || getWishCharacterSplash(wishGameId, r.name)) : '/assets/logo.svg';

            return `
                <div style="position: relative; background: ${bgGradient}; border: 2px solid ${borderCol}; border-radius: 16px; padding: 14px 8px; display: flex; flex-direction: column; align-items: center; justify-content: space-between; text-align: center; box-shadow: 0 8px 20px rgba(0,0,0,0.6); transition: transform 0.2s;">
                    <div style="width: 72px; height: 92px; border-radius: 10px; overflow: hidden; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.2);">
                        <img src="${artUrl}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.src='/assets/logo.svg'">
                    </div>
                    <span style="font-size: 11px; font-weight: 800; color: #ffffff; line-height: 1.2; margin-bottom: 4px; max-width: 95px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${r.name}</span>
                    <div style="font-size: 12px; color: ${borderCol}; font-weight: bold;">${'★'.repeat(r.rarity)}</div>
                </div>
            `;
        }).join('');
    }
};

window.skipWishAnimation = function() {
    if (window.wishAnimTimeout) {
        clearTimeout(window.wishAnimTimeout);
        window.wishAnimTimeout = null;
    }

    const fxGenshin = document.getElementById("wish-fx-genshin");
    const fxHsr = document.getElementById("wish-fx-hsr");
    const fxZzz = document.getElementById("wish-fx-zzz");
    if (fxGenshin) fxGenshin.style.display = "none";
    if (fxHsr) fxHsr.style.display = "none";
    if (fxZzz) fxZzz.style.display = "none";

    if (wishIsMultiPull && wishCurrentResults.length > 1) {
        showWishSummaryGrid();
    } else {
        showWishItemAtIndex(0);
    }
};

window.closeWishModal = function() {
    if (window.wishAnimTimeout) {
        clearTimeout(window.wishAnimTimeout);
        window.wishAnimTimeout = null;
    }
    const modal = document.getElementById("wish-animation-modal");
    if (modal) modal.style.display = "none";
};

/* ==========================================================================
   ROAST MY ACCOUNT FUNCTIONALITY (HERTA & NOUS IA)
   ========================================================================== */
window.lastRoastMarkdown = "";

window.openRoastModal = async function(gameId) {
    const activeTabBtn = document.querySelector(".tab-audit-game-btn.active");
    const selectedGame = gameId || (activeTabBtn ? activeTabBtn.dataset.game : null) || window.currentAuditGameId || "hsr";
    
    const modal = document.getElementById("modal-roast");
    const bodyEl = document.getElementById("roast-content-body");
    
    if (!modal || !bodyEl) return;
    
    modal.style.display = "flex";
    window.lastRoastMarkdown = "";
    
    bodyEl.innerHTML = `
        <div class="roast-loading-box">
            <div class="roast-flame-spinner">
                <i class="fa-solid fa-fire-flame-curved"></i>
            </div>
            <h3 style="color: #ff4b2b; margin: 0; font-size: 18px;">Consultando a Herta e o Aeon Nous...</h3>
            <p style="color: #94a3b8; font-size: 13px; margin: 0;">Analisando suas relíquias lixo e rindo dos seus atributos flat...</p>
        </div>
    `;
    
    try {
        const res = await fetch(`/api/roast/${selectedGame}`);
        if (!res.ok) {
            bodyEl.innerHTML = `<p style="color: var(--color-danger); padding: 20px;">Falha na requisição HTTP: Status ${res.status}</p>`;
            return;
        }
        
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let rawText = "";
        let buffer = "";
        let isFirstToken = true;
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();
            
            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    try {
                        const parsed = JSON.parse(line.substring(6));
                        if (parsed.token) {
                            if (isFirstToken) {
                                bodyEl.innerHTML = "";
                                isFirstToken = false;
                            }
                            rawText += parsed.token;
                            window.lastRoastMarkdown = rawText;
                            bodyEl.innerHTML = typeof marked !== "undefined" ? marked.parse(rawText) : rawText;
                            bodyEl.scrollTop = bodyEl.scrollHeight;
                        } else if (parsed.error) {
                            if (isFirstToken) bodyEl.innerHTML = "";
                            rawText += `\n\n⚠️ Erro: ${parsed.error}`;
                            bodyEl.innerHTML = typeof marked !== "undefined" ? marked.parse(rawText) : rawText;
                        }
                    } catch (e) {
                        // Ignora JSONs parciais em fatias de streaming
                    }
                }
            }
        }
        
        if (!rawText.trim()) {
            bodyEl.innerHTML = `<p style="color: var(--color-danger); padding: 20px;">Nenhum conteúdo retornado pelo Roast. Verifique se sua chave API da Groq está configurada nas Configurações.</p>`;
        }
    } catch (err) {
        console.error("Erro no Roast:", err);
        bodyEl.innerHTML = `<p style="color: var(--color-danger); padding: 20px;">Ocorreu um erro ao gerar o Roast: ${err.message}</p>`;
    }
};

window.copyRoastToClipboard = function() {
    if (!window.lastRoastMarkdown) {
        alert("Nenhum Roast para copiar ainda!");
        return;
    }
    navigator.clipboard.writeText(window.lastRoastMarkdown).then(() => {
        const btn = document.getElementById("btn-copy-roast");
        if (btn) {
            const orig = btn.innerHTML;
            btn.innerHTML = `<i class="fa-solid fa-check" style="color: #4ade80;"></i> Copiado!`;
            setTimeout(() => { btn.innerHTML = orig; }, 2000);
        }
    }).catch(err => {
        console.error("Erro ao copiar:", err);
    });
};



// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
if (typeof animateWishCSS !== 'undefined') window.animateWishCSS = animateWishCSS;
if (typeof getWishCharacterSplash !== 'undefined') window.getWishCharacterSplash = getWishCharacterSplash;
if (typeof playWishSound !== 'undefined') window.playWishSound = playWishSound;
if (typeof renderSubstatsPillList !== 'undefined') window.renderSubstatsPillList = renderSubstatsPillList;
if (typeof rollSingleWishItem !== 'undefined') window.rollSingleWishItem = rollSingleWishItem;
if (typeof wishAnimId !== 'undefined') window.wishAnimId = wishAnimId;
if (typeof wishAnimRunning !== 'undefined') window.wishAnimRunning = wishAnimRunning;
if (typeof wishAnimTimeout !== 'undefined') window.wishAnimTimeout = wishAnimTimeout;
if (typeof wishAudioCtx !== 'undefined') window.wishAudioCtx = wishAudioCtx;
if (typeof wishCurrentResults !== 'undefined') window.wishCurrentResults = wishCurrentResults;
if (typeof wishGameId !== 'undefined') window.wishGameId = wishGameId;
if (typeof wishIsMultiPull !== 'undefined') window.wishIsMultiPull = wishIsMultiPull;