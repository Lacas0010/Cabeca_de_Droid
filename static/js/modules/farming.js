
function formatFarmingDay(dayStr) {
    if (!dayStr) return (window.isEn || window.currentLang === "en") ? "Today" : "Hoje";
    const isEn = Boolean(window.isEn || (window.getCurrentLanguage && window.getCurrentLanguage() === 'en') || window.currentLang === 'en');
    if (!isEn) return dayStr;
    const dayMap = {
        "Segunda-feira": "Monday",
        "Terça-feira": "Tuesday",
        "Quarta-feira": "Wednesday",
        "Quinta-feira": "Thursday",
        "Sexta-feira": "Friday",
        "Sábado": "Saturday",
        "Domingo": "Sunday",
        "Hoje": "Today"
    };
    return dayMap[dayStr] || dayStr;
}

function formatFarmingNote(noteStr) {
    if (!noteStr) return "";
    const isEn = Boolean(window.isEn || (window.getCurrentLanguage && window.getCurrentLanguage() === 'en') || window.currentLang === 'en');
    if (!isEn) return noteStr;
    let s = String(noteStr);
    return s.replace(/Reset Semanal do Notorious Hunt \(3x Caça aos Chefes de Dano\)\./gi, "Weekly Reset of Notorious Hunt (3x Boss Hunt).")
            .replace(/Reset Semanal do Universo Simulado e Eco da Guerra \(3x recompensas\)\./gi, "Weekly Reset of Simulated Universe and Echo of War (3x rewards).")
            .replace(/Calyx de Traço & Ascensão com drop normal\./gi, "Trace & Ascension Calyx with normal drop.")
            .replace(/Calyx de Traço & Ascensão\./gi, "Trace & Ascension Calyx.")
            .replace(/Foco recomendado:\s*Farm de Túnel de Relíquias\./gi, "Recommended focus: Relic Tunnel Farming.")
            .replace(/Foco recomendado:\s*Ornamentos Planares \(Universo Divergente\/Simulado\)\./gi, "Recommended focus: Planar Ornaments (Divergent/Simulated Universe).")
            .replace(/Farm livre de Relíquias e Materiais de Ascensão\./gi, "Free farming of Relics and Ascension Materials.")
            .replace(/Preparação de Energia para o Reset de Segunda\./gi, "Stamina preparation for Monday Reset.")
            .replace(/Foco recomendado:\s*HIA Club - Chips de Atributo de Especialidade\./gi, "Recommended focus: HIA Club - Specialty Attribute Chips.")
            .replace(/Foco recomendado:\s*HIA Club - Certificados de Promoção\./gi, "Recommended focus: HIA Club - Promotion Seals.")
            .replace(/Foco recomendado:\s*Drive Disc Tuning & Limpeza de Rótulo\./gi, "Recommended focus: Drive Disc Tuning & Label Cleanup.")
            .replace(/HIA Club - Materiais de Agente\./gi, "HIA Club - Agent Materials.")
            .replace(/Farm livre de Discos e Materiais na Cavidade Zero\./gi, "Free farming of Drive Discs and Hollow Zero Materials.")
            .replace(/Preparação de Bateria para o Reset Semanal\./gi, "Battery preparation for Weekly Reset.")
            .replace(/Todos os materiais abertos/gi, "All materials open");
}

// ==========================================================================
// Módulo: farming.js
// Cabeça de Droid - Vanilla ES6 Module
// ==========================================================================

    // ==========================================
    // LOGICA DOS 8 NOVOS MÓDULOS AVANÇADOS
    // ==========================================

    // Solicitar permissão para Notificações Web
    if ("Notification" in window && Notification.permission !== "granted" && Notification.permission !== "denied") {
        Notification.requestPermission();
    }

    // 1. SIMULADOR DE GACHA
    const btnRunGacha = document.getElementById("btn-run-gacha-sim");
    if (btnRunGacha) {
        btnRunGacha.addEventListener("click", async () => {
            const gameId = document.getElementById("gacha-game-select").value;
            const currentPity = parseInt(document.getElementById("gacha-pity").value) || 0;
            const isGuaranteed = document.getElementById("gacha-guaranteed").value === "true";
            const pullsAvailable = parseInt(document.getElementById("gacha-pulls").value) || 0;
            const targetCopies = parseInt(document.getElementById("gacha-target-copies").value) || 1;

            btnRunGacha.innerText = "Simulando...";
            btnRunGacha.disabled = true;

            try {
                const res = await fetch("/api/gacha/calculate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        game_id: gameId,
                        current_pity: currentPity,
                        is_guaranteed: isGuaranteed,
                        pulls_available: pullsAvailable,
                        target_copies: targetCopies
                    })
                });
                const data = await res.json();
                
                document.getElementById("gacha-results-box").style.display = "block";

                document.getElementById("gacha-chance-lbl").innerText = `${isEn ? "Success Chance:" : "Chance de Sucesso:"} ${data.success_rate}%`;
                document.getElementById("gacha-avg-lbl").innerText = data.avg_pulls_spent 
                    ? (isEn ? `Average Pulls Spent in wins: ${data.avg_pulls_spent} pulls` : `Média de Tiros Gastos nas vitórias: ${data.avg_pulls_spent} tiros`) 
                    : (isEn ? "Insufficient pulls to guarantee goal frequently." : "Quantidade de tiros insuficiente para garantir a meta com alta frequência.");

                const distList = document.getElementById("gacha-dist-list");
                distList.innerHTML = "";
                for (const [k, v] of Object.entries(data.distribution || {})) {
                    const row = document.createElement("div");
                    row.style.display = "flex";
                    row.style.justifyContent = "space-between";
                    row.innerHTML = `<span>${k}:</span> <strong style="color:#f59e0b;">${v}%</strong>`;
                    distList.appendChild(row);
                }
            } catch (err) {
                showToast("Erro ao executar simulação de Gacha.");
            } finally {
                btnRunGacha.innerText = "Simular 10.000 Tentativas";
                btnRunGacha.disabled = false;
            }
        });
    }

    window.farmRosterCache = window.farmRosterCache || {};
    window.currentFarmModalGame = "genshin";
    window.currentFarmModalContainer = "tab-farm-content-body";
    window.farmModalSelectedSet = new Set();
    window.currentFarmFilterPill = "all";

    // 2. CENTRAL DE FARM DIÁRIO
    window.loadFarmData = async (gameId, targetContainerId = "farm-content-body") => {
        const body = document.getElementById(targetContainerId);
        if (!body) return;

        body.innerHTML = `<div style='color:#94a3b8; padding: 20px; text-align: center;'><i class='fa-solid fa-spinner fa-spin'></i> ${isEn ? "Loading calendar, character list, and recommendations..." : "Carregando calendário, lista de personagens e recomendações..."}</div>`;
        
        try {
            const storageKey = `hoyo_farm_selected_${gameId}`;
            let savedSelected = null;
            try {
                const rawSaved = localStorage.getItem(storageKey);
                if (rawSaved) {
                    const parsed = JSON.parse(rawSaved);
                    if (Array.isArray(parsed)) {
                        savedSelected = parsed;
                    }
                }
            } catch(e) {}

            let apiUrl = `/api/farming/today/${gameId}?lang=${isEn ? "en" : "pt"}`;
            if (savedSelected && Array.isArray(savedSelected) && savedSelected.length > 0 && !savedSelected.includes("__none__")) {
                apiUrl += `?selected_chars=${encodeURIComponent(savedSelected.join(","))}`;
            } else if (savedSelected && savedSelected.includes("__none__")) {
                apiUrl += `?selected_chars=__none__`;
            }

            const res = await fetch(apiUrl);
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `Erro HTTP ${res.status}`);
            }
            const data = await res.json();
            const cal = data.calendar_info || {};
            const allRosterNames = data.all_roster_names || [];
            const allRosterChars = data.all_roster_characters || allRosterNames.map(n => ({ name: n, level: 90, rarity: 5, icon: '' }));
            const targets = data.priority_targets || [];
            const maxLvl = data.max_level || (gameId === "genshin" ? 90 : (gameId === "hsr" ? 80 : 60));

            // Salva no cache para o seletor modal
            window.farmRosterCache[gameId] = allRosterChars;

            let selectedSet;
            if (savedSelected && Array.isArray(savedSelected)) {
                if (savedSelected.includes("__none__")) {
                    selectedSet = new Set();
                } else {
                    selectedSet = new Set(savedSelected);
                }
            } else {
                selectedSet = new Set(allRosterNames);
            }

            // Mapa para buscar ícone rápido
            const charIconMap = {};
            allRosterChars.forEach(c => {
                if (c.name) charIconMap[c.name] = c.icon || '';
            });

            let html = `
                <!-- CALENDÁRIO DO DIA -->
                <div style="padding:14px; background:rgba(255,255,255,0.03); border-radius:10px; margin-bottom:16px; border:1px solid var(--border-color);">
                    <h4 style="margin:0 0 6px 0; color:#10b981; font-size:15px; display:flex; align-items:center; gap:8px;">
                        <i class="fa-solid fa-calendar-day"></i> ${isEn ? "Today's Schedule" : "Calendário do Dia"} (${formatFarmingDay(cal.days)})
                        <span style="font-size:11px; background:rgba(16,185,129,0.15); color:#10b981; padding:2px 8px; border-radius:12px; margin-left:auto;">${isEn ? "Max Game Level:" : "Nv. Máximo do Jogo:"} ${maxLvl}</span>
                    </h4>
            `;
            if (cal.talents) html += `<div style="font-size:13px; color:#cbd5e1; margin-top:4px;"><strong>${isEn ? "Talent Books / Mat.:" : "Livros de Talento / Mat.:"}</strong> ${cal.talents.join(", ")}</div>`;
            if (cal.weapons) html += `<div style="font-size:13px; color:#cbd5e1; margin-top:4px;"><strong>${isEn ? "Weapons / Ascension:" : "Armas / Elevação:"}</strong> ${cal.weapons.join(", ")}</div>`;
            if (cal.note) html += `<div style="font-size:13px; color:#f59e0b; margin-top:4px;"><strong>${isEn ? "Special Note:" : "Nota Especial:"}</strong> ${formatFarmingNote(cal.note)}</div>`;
            html += `</div>`;

            // PAINEL / TRAY DE SELEÇÃO VISUAL DE PERSONAGENS ALVO
            html += `
                <div style="padding:14px; background:rgba(15,23,42,0.8); border-radius:12px; margin-bottom:16px; border:1px solid rgba(16,185,129,0.25); box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <strong style="color:#ffffff; font-size:14px; display:flex; align-items:center; gap:6px;">
                                <i class="fa-solid fa-crosshairs" style="color:#10b981;"></i> ${isEn ? "Active Farming Focus" : "Foco de Farm Ativo"}
                            </strong>
                            <span style="font-size:11px; background:rgba(56,189,248,0.15); color:#38bdf8; font-weight:700; padding:2px 8px; border-radius:12px; border:1px solid rgba(56,189,248,0.3);">
                                ${selectedSet.size} ${isEn ? "of" : "de"} ${allRosterNames.length} ${isEn ? "characters" : "personagens"}
                            </span>
                        </div>
                        <div style="display:flex; gap:6px; align-items:center;">
                            <button onclick="window.openFarmCharSelectorModal('${gameId}', '${targetContainerId}')" style="padding:6px 14px; font-size:12px; font-weight:700; background:linear-gradient(135deg, #10b981, #059669); color:#fff; border:none; border-radius:8px; cursor:pointer; display:flex; align-items:center; gap:6px; box-shadow: 0 2px 10px rgba(16,185,129,0.35);">
                                <i class="fa-solid fa-user-pen"></i> ${isEn ? "Select Target Characters" : "Escolher Personagens Alvo"}
                            </button>
                            <button onclick="window.quickSelectAllFarm('${gameId}', '${targetContainerId}')" style="font-size:11px; padding:5px 9px; background:rgba(56,189,248,0.12); color:#38bdf8; border:1px solid rgba(56,189,248,0.3); border-radius:6px; cursor:pointer; font-weight:600;">${isEn ? "All" : "Todos"}</button>
                            <button onclick="window.quickDeselectAllFarm('${gameId}', '${targetContainerId}')" style="font-size:11px; padding:5px 9px; background:rgba(239,68,68,0.12); color:#f87171; border:1px solid rgba(239,68,68,0.3); border-radius:6px; cursor:pointer; font-weight:600;">${isEn ? "Deselect" : "Desmarcar"}</button>
                        </div>
                    </div>

                    <!-- Horizontal Chips Tray of Selected Characters -->
                    <div style="display:flex; gap:8px; overflow-x:auto; padding:6px 2px; max-height:85px; align-items:center;">
            `;

            if (selectedSet.size === 0) {
                html += `
                    <div style="font-size:12px; color:#f87171; width:100%; padding:8px 12px; background:rgba(239,68,68,0.08); border-radius:8px; border:1px solid rgba(239,68,68,0.2); display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px;">
                        <span><i class="fa-solid fa-circle-exclamation"></i> Nenhum personagem focado no momento. O Farm e a Ordem Diária estão sem metas ativas.</span>
                        <button onclick="window.openFarmCharSelectorModal('${gameId}', '${targetContainerId}')" style="font-size:11px; padding:4px 10px; background:#10b981; color:#fff; border:none; border-radius:6px; font-weight:700; cursor:pointer;">Selecionar Alvos</button>
                    </div>
                `;
            } else {
                Array.from(selectedSet).forEach(cName => {
                    const cIcon = charIconMap[cName] || '';
                    html += `
                        <div class="farm-target-chip">
                            ${cIcon ? `<img src="${cIcon}" onerror="this.src='/assets/logo.svg'">` : `<i class="fa-solid fa-user" style="font-size:11px; color:#38bdf8;"></i>`}
                            <span>${typeof formatCharacterName === 'function' ? formatCharacterName(cName) : cName}</span>
                            <button class="btn-remove-chip" title="${isEn ? 'Remove focus' : 'Remover foco'}" onclick="window.quickRemoveFarmTarget('${gameId}', '${cName}', '${targetContainerId}')">✕</button>
                        </div>
                    `;
                });
            }

            html += `
                    </div>
                </div>
            `;

            // RECOMENDAÇÕES E DETALHAMENTO DE ITENS
            let farmableOnlyKey = `hoyo_farmable_only_${gameId}`;
            let isFarmableOnly = localStorage.getItem(farmableOnlyKey) === "true";

            html += `
                <div style="display:flex; justify-content:space-between; align-items:center; margin:16px 0 10px 0;">
                    <h4 style="margin:0; color:#f59e0b; font-size:15px; display:flex; align-items:center; gap:6px;">
                        <i class="fa-solid fa-bullseye"></i> ${isEn ? "Detailed Farming Suggestions & Materials" : "Sugestões e Itens de Farm Detalhados"}
                    </h4>
                    ${gameId === "genshin" ? `
                        <label style="font-size:12px; color:#38bdf8; display:flex; align-items:center; gap:6px; background:rgba(56,189,248,0.1); padding:4px 10px; border-radius:8px; cursor:pointer; border:1px solid rgba(56,189,248,0.25);">
                            <input type="checkbox" id="${targetContainerId}-farmable-only" ${isFarmableOnly ? 'checked' : ''}>
                            <span> ${isEn ? "Only Materials Open Today" : "Apenas Materiais Abertos Hoje"}</span>
                        </label>
                    ` : ''}
                </div>
            `;

            let displayTargets = targets;
            if (gameId === "genshin" && isFarmableOnly) {
                displayTargets = targets.filter(t => t.farmable_today !== false);
            }

            if (displayTargets.length === 0) {
                if (targets.length > 0 && isFarmableOnly) {
                    html += `
                        <div style="padding:18px; background:rgba(234,179,8,0.08); border:1px solid rgba(234,179,8,0.25); border-radius:10px; font-size:13px; color:#fde047; text-align:center; line-height:1.6;">
                            <i class="fa-solid fa-calendar-xmark" style="font-size:18px; margin-bottom:6px; display:block; color:#facc15;"></i>
                            <strong>${isEn ? "Talent domains for selected characters are closed today!" : "Os domínios de talento dos personagens selecionados estão fechados hoje!"}</strong><br>
                            <span style="font-size:12px; color:#94a3b8;">${isEn ? "Uncheck the option above to view all ascension, boss and talent materials even when domains are closed." : "Desmarque a opção <strong>\"Apenas Materiais Abertos Hoje\"</strong> acima para visualizar todos os materiais de ascensão, chefes e talentos mesmo com o domínio fechado."}</span>
                        </div>
                    `;
                } else {
                    html += `
                        <div style="padding:18px; background:rgba(255,255,255,0.02); border-radius:10px; font-size:13px; color:#94a3b8; text-align:center;">
                            <i class="fa-solid fa-circle-check" style="color:#10b981; margin-right:6px;"></i>
                            ${isEn ? `No selected characters need ascension at the moment. All selected are at maximum level (${maxLvl}) with up-to-date talents and weapons!` : `Nenhum personagem selecionado precisa de ascensão no momento. Todos os selecionados estão no nível máximo (${maxLvl}) com talentos e armas atualizados!`}
                        </div>
                    `;
                }
            } else {
                const elementGlows = {
                    pyro: { color: "#ef4444", bg: "rgba(239,68,68,0.08)", border: "rgba(239,68,68,0.3)" },
                    fire: { color: "#ef4444", bg: "rgba(239,68,68,0.08)", border: "rgba(239,68,68,0.3)" },
                    hydro: { color: "#38bdf8", bg: "rgba(56,189,248,0.08)", border: "rgba(56,189,248,0.3)" },
                    ice: { color: "#06b6d4", bg: "rgba(6,182,212,0.08)", border: "rgba(6,182,212,0.3)" },
                    cryo: { color: "#06b6d4", bg: "rgba(6,182,212,0.08)", border: "rgba(6,182,212,0.3)" },
                    electro: { color: "#a855f7", bg: "rgba(168,85,247,0.08)", border: "rgba(168,85,247,0.3)" },
                    anemo: { color: "#10b981", bg: "rgba(168,185,129,0.08)", border: "rgba(16,185,129,0.3)" },
                    geo: { color: "#f59e0b", bg: "rgba(245,158,11,0.08)", border: "rgba(245,158,11,0.3)" },
                    physical: { color: "#94a3b8", bg: "rgba(148,163,184,0.08)", border: "rgba(148,163,184,0.3)" },
                    dendro: { color: "#84cc16", bg: "rgba(132,204,22,0.08)", border: "rgba(132,204,22,0.3)" },
                    quantum: { color: "#6366f1", bg: "rgba(99,102,241,0.08)", border: "rgba(99,102,241,0.3)" },
                    imaginary: { color: "#eab308", bg: "rgba(234,179,8,0.08)", border: "rgba(234,179,8,0.3)" },
                    ether: { color: "#eab308", bg: "rgba(234,179,8,0.08)", border: "rgba(234,179,8,0.3)" }
                };

                displayTargets.forEach(t => {
                    const gradeColors = { SSS: "#f59e0b", SS: "#ec4899", S: "#10b981", A: "#3b82f6", B: "#8b5cf6", C: "#6b7280", D: "#ef4444" };
                    const gColor = gradeColors[t.grade] || "#94a3b8";
                    const elemKey = (t.element || "").toLowerCase().trim();
                    const elemTheme = elementGlows[elemKey] || { color: "#38bdf8", bg: "rgba(15,23,42,0.8)", border: "rgba(255,255,255,0.1)" };
                    const pct = Math.min(100, Math.round((t.level / t.max_level) * 100));

                    html += `
                        <div style="padding:14px; background:${elemTheme.bg}; border-radius:12px; margin-bottom:16px; border:1px solid ${elemTheme.border}; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                            <!-- Cabeçalho do Personagem com Tema Elemental -->
                            <div style="display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.06); padding-bottom:10px; margin-bottom:12px; flex-wrap:wrap; gap:8px;">
                                <div style="display:flex; align-items:center; gap:12px;">
                                    ${t.icon ? `<img src="${t.icon}" style="width:44px; height:44px; border-radius:50%; background:rgba(0,0,0,0.5); object-fit:cover; border:2px solid ${elemTheme.color}; box-shadow:0 0 10px ${elemTheme.color}66;">` : ''}
                                    <div>
                                        <div style="display:flex; align-items:center; gap:8px;">
                                            <strong style="color:#ffffff; font-size:16px;">${t.name}</strong>
                                            <span style="font-size:11px; padding:2px 8px; border-radius:10px; background:${elemTheme.color}22; color:${elemTheme.color}; font-weight:700; border:1px solid ${elemTheme.color}44;">
                                                ${window.formatElementDisplayName ? window.formatElementDisplayName(t.element) : (t.element || (isEn ? "Element" : "Elemento"))}
                                            </span>
                                        </div>
                                        <div style="font-size:12px; color:#cbd5e1; margin-top:3px; display:flex; align-items:center; gap:8px;">
                                            <span>${isEn ? "Lv." : "Nv."} ${t.level}/${t.max_level}</span>
                                            <div style="width:80px; height:6px; background:rgba(255,255,255,0.1); border-radius:3px; overflow:hidden;">
                                                <div style="width:${pct}%; height:100%; background:${elemTheme.color};"></div>
                                            </div>
                                            <span style="font-size:11px; color:#94a3b8;">${pct}%</span>
                                        </div>
                                    </div>
                                </div>
                                <div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap;">
                                    ${t.talent_priority ? `
                                        <span style="font-size:11px; padding:4px 10px; border-radius:12px; background:rgba(168,85,247,0.15); color:#c084fc; font-weight:600; border:1px solid rgba(168,85,247,0.3);">
                                             ${isEn ? "Prydwen Priority:" : "Prioridade Prydwen:"} ${t.talent_priority}
                                        </span>
                                    ` : ''}
                                    <span style="font-size:11px; padding:4px 10px; border-radius:12px; background:${t.level < t.max_level ? 'rgba(239,68,68,0.15)' : 'rgba(16,185,129,0.15)'}; color:${t.level < t.max_level ? '#f87171' : '#34d399'}; font-weight:600;">
                                        ${t.level < t.max_level ? (isEn ? `Ascension Lv. ${t.level}/${t.max_level}` : `Ascensão Nv. ${t.level}/${t.max_level}`) : (isEn ? `Level ${t.max_level} OK` : `Nível ${t.max_level} OK`)}
                                    </span>
                                    <span style="font-size:11px; padding:4px 10px; border-radius:12px; background:rgba(255,255,255,0.05); color:${gColor}; font-weight:bold; border:1px solid ${gColor}44;">
                                        ${isEn ? "Grade" : "Nota"} ${t.grade} (${t.score.toFixed(1)}%)
                                    </span>
                                </div>
                            </div>

                            <!-- Lista de Itens Detalhados -->
                            <div style="display:flex; flex-direction:column; gap:8px; font-size:12px;">
                    `;

                    const gameIdStr = (t.game_id || gameId || "genshin").toLowerCase().trim();
                    const ic = (t.items_needed && t.items_needed.icons) || {};

                    const defaultTermsByGame = isEn ? {
                        genshin: {
                            currency_name: "Mora",
                            xp_book_name: "Hero's Wit",
                            talent_category: "Talents",
                            green_book: "Teachings (2★)",
                            blue_book: "Guide (3★)",
                            purple_book: "Philosophies (4★)",
                            enemy_t1: "Common Enemy Drop (1★)",
                            enemy_t2: "Uncommon Enemy Drop (2★)",
                            enemy_t3: "Rare Enemy Drop (3★)",
                            boss_mat: "Field Boss Material",
                            weekly_boss_mat: "Weekly Boss Material",
                            crown_mat: "Crown of Insight",
                            ore_name: "Mystic Enhancement Ore",
                            w_mat_green: "Weapon Domain Mat. (2★)",
                            w_mat_blue: "Weapon Domain Mat. (3★)",
                            w_mat_purple: "Weapon Domain Mat. (4★)",
                            w_mat_gold: "Weapon Domain Mat. (5★)"
                        },
                        hsr: {
                            currency_name: "Credits",
                            xp_book_name: "Traveler's Guide",
                            talent_category: "Traces",
                            green_book: "Trace Material (2★)",
                            blue_book: "Trace Material (3★)",
                            purple_book: "Trace Material (4★)",
                            enemy_t1: "Enemy Component (1★)",
                            enemy_t2: "Enemy Core (2★)",
                            enemy_t3: "Enemy Essence (3★)",
                            boss_mat: "Stagnant Shadow Material",
                            weekly_boss_mat: "Echo of War Material",
                            crown_mat: "Tracks of Destiny",
                            ore_name: "Refined Aether",
                            w_mat_green: "Light Cone Material (2★)",
                            w_mat_blue: "Light Cone Material (3★)",
                            w_mat_purple: "Light Cone Material (4★)",
                            w_mat_gold: "Light Cone Material (5★)"
                        },
                        zzz: {
                            currency_name: "Dennys",
                            xp_book_name: "Official Investigator Log",
                            talent_category: "Skills",
                            green_book: "Basic Skill Chip (2★)",
                            blue_book: "Advanced Skill Chip (3★)",
                            purple_book: "Specialized Skill Chip (4★)",
                            enemy_t1: "Basic Certification Seal (1★)",
                            enemy_t2: "Advanced Certification Seal (2★)",
                            enemy_t3: "Specialized Certification Seal (3★)",
                            boss_mat: "Higher Dimensional Data",
                            weekly_boss_mat: "Notorious Hunt Material",
                            crown_mat: "Hamster Cage Pass",
                            ore_name: "W-Engine Power Supply",
                            w_mat_green: "Basic W-Engine Component (2★)",
                            w_mat_blue: "Advanced W-Engine Component (3★)",
                            w_mat_purple: "Specialized Component (4★)",
                            w_mat_gold: "Master Component (5★)"
                        }
                    } : {
                        genshin: {
                            currency_name: "Mora",
                            xp_book_name: "EXP do Herói",
                            talent_category: "Talentos",
                            green_book: "Ensinamentos (2★)",
                            blue_book: "Guia (3★)",
                            purple_book: "Filosofias (4★)",
                            enemy_t1: "Drop Inimigo Comum (1★)",
                            enemy_t2: "Drop Inimigo Incomum (2★)",
                            enemy_t3: "Drop Inimigo Raro (3★)",
                            boss_mat: "Material de Chefe de Campo",
                            weekly_boss_mat: "Material de Chefe Semanal",
                            crown_mat: "Coroa da Sabedoria",
                            ore_name: "Minério de Amplificação Místico",
                            w_mat_green: "Material de Domínio de Arma (2★)",
                            w_mat_blue: "Material de Domínio de Arma (3★)",
                            w_mat_purple: "Material de Domínio de Arma (4★)",
                            w_mat_gold: "Material de Domínio de Arma (5★)"
                        },
                        hsr: {
                            currency_name: "Créditos",
                            xp_book_name: "Guia do Mochileiro",
                            talent_category: "Rastros",
                            green_book: "Esboço / Mat. de Traço (2★)",
                            blue_book: "Dinâmica / Mat. de Traço (3★)",
                            purple_book: "Conhecimento / Mat. de Traço (4★)",
                            enemy_t1: "Componente de Inimigo (1★)",
                            enemy_t2: "Núcleo de Inimigo (2★)",
                            enemy_t3: "Essência de Inimigo (3★)",
                            boss_mat: "Material de Sombra Estagnada",
                            weekly_boss_mat: "Material do Eco da Guerra",
                            crown_mat: "Rastro do Destino",
                            ore_name: "Éter Refinado",
                            w_mat_green: "Componente de Cone de Luz (2★)",
                            w_mat_blue: "Módulo de Cone de Luz (3★)",
                            w_mat_purple: "Núcleo de Cone de Luz (4★)",
                            w_mat_gold: "Matriz de Cone de Luz (5★)"
                        },
                        zzz: {
                            currency_name: "Dennys",
                            xp_book_name: "Registro Oficial de Investigador",
                            talent_category: "Habilidades",
                            green_book: "Chip Básico de Habilidade (2★)",
                            blue_book: "Chip Avançado de Habilidade (3★)",
                            purple_book: "Chip Especializado de Habilidade (4★)",
                            enemy_t1: "Sinalizador Básico (1★)",
                            enemy_t2: "Sinalizador Avançado (2★)",
                            enemy_t3: "Sinalizador Especializado (3★)",
                            boss_mat: "Dado de Alta Dimensão",
                            weekly_boss_mat: "Material de Caça Notória",
                            crown_mat: "Passaporte da Gaiola de Hamster",
                            ore_name: "Fonte de Alimentação de W-Engine",
                            w_mat_green: "Componente Básico de W-Engine (2★)",
                            w_mat_blue: "Componente Avançado de W-Engine (3★)",
                            w_mat_purple: "Componente Especializado (4★)",
                            w_mat_gold: "Componente Mestre (5★)"
                        }
                    };

                    const terms = Object.assign({}, defaultTermsByGame[gameIdStr] || defaultTermsByGame.genshin, (t.items_needed && t.items_needed.terms) || {});

                    const defaultIconsByGame = {
                        genshin: {
                            mora: "https://enka.network/ui/UI_ItemIcon_202.png",
                            xp: "https://enka.network/ui/UI_ItemIcon_104003.png",
                            talent_book: "https://enka.network/ui/UI_ItemIcon_104303.png",
                            boss: "https://enka.network/ui/UI_ItemIcon_113001.png",
                            weekly_boss: "https://enka.network/ui/UI_ItemIcon_113021.png",
                            crown: "https://enka.network/ui/UI_ItemIcon_104319.png",
                            weapon_ore: "https://enka.network/ui/UI_ItemIcon_104013.png"
                        },
                        hsr: {
                            mora: "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/2.png",
                            xp: "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/22.png",
                            talent_book: "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/110.png",
                            boss: "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/201.png",
                            weekly_boss: "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/3.png",
                            crown: "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/11.png",
                            weapon_ore: "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/icon/item/102.png"
                        },
                        zzz: {
                            mora: "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4fde02b5f3a4c790dcbef6c74cb4fabf.png",
                            xp: "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/55c259888e808554c02a3161944d7868.png",
                            talent_book: "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/ba07d11da190b24386fca2f75b4581a0.png",
                            boss: "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/e1c89620556d60ab11c7b143162d0f4a.png",
                            weekly_boss: "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/2196659ee41fc22d1533519c53644f37.png",
                            crown: "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/faeebca44b20e03ee23b610c4f8ea03d.png",
                            weapon_ore: "https://act-webstatic.hoyoverse.com/darkmatter/nap/prod_gf_cn/item_icon_u8d5de/4f1444b51f52e8e0ad4a8dc13432b04f.png"
                        }
                    };

                    const finalIcons = Object.assign({}, defaultIconsByGame[gameIdStr] || defaultIconsByGame.genshin, ic);

                    const moraIcon = `<img src="${finalIcons.mora}" style="width:18px; height:18px; vertical-align:middle; margin-right:4px; object-fit:contain;" onerror="this.onerror=null; this.outerHTML=' ';">`;
                    const xpIcon = `<img src="${finalIcons.xp}" style="width:18px; height:18px; vertical-align:middle; margin-right:4px; object-fit:contain;" onerror="this.onerror=null; this.outerHTML=' ';">`;
                    const talentIcon = `<img src="${finalIcons.talent_book}" style="width:18px; height:18px; vertical-align:middle; margin-right:4px; object-fit:contain;" onerror="this.onerror=null; this.outerHTML=' ';">`;
                    const bossIcon = `<img src="${finalIcons.boss}" style="width:18px; height:18px; vertical-align:middle; margin-right:4px; object-fit:contain;" onerror="this.onerror=null; this.outerHTML=' ';">`;

                    // Helper para renderizar ícone com fallback seguro
                    const makeMatIcon = (src, fallbackSrc, size = 18) => {
                        const effectiveSrc = src || fallbackSrc;
                        return `<img src="${effectiveSrc}" style="width:${size}px; height:${size}px; vertical-align:middle; margin-right:4px; object-fit:contain; border-radius:3px;" onerror="this.onerror=null; this.src='${fallbackSrc}';">`;
                    };

                    // 1. Ascensão de Personagem
                    if (t.items_needed && t.items_needed.ascension) {
                        const asc = t.items_needed.ascension;
                        const bIconHtml = makeMatIcon(asc.boss_item_icon, finalIcons.boss);
                        const specIconHtml = makeMatIcon(asc.specialty_icon, finalIcons.boss);
                        html += `
                            <div style="background:rgba(239,68,68,0.05); padding:10px 12px; border-radius:8px; border-left:3px solid #ef4444;">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; flex-wrap:wrap; gap:6px;">
                                    <strong style="color:#f87171; display:flex; align-items:center; gap:6px; font-size:13px;">
                                         ${isEn ? "Level Up & Character Ascension" : "Elevação de Nível & Ascensão do Personagem"} (${isEn ? "Lv." : "Nv."} ${t.level} ➔ ${isEn ? "Lv." : "Nv."} ${t.max_level})
                                    </strong>
                                    <span style="font-size:11px; padding:2px 8px; border-radius:6px; background:rgba(16,185,129,0.15); color:#34d399; font-weight:600;">
                                        <i class="fa-solid fa-earth-americas"></i> ${isEn ? "Open Today (Field Boss & Specialties 24/7)" : "Aberto Hoje (Chefe de Campo & Especialidades 24/7)"}
                                    </span>
                                </div>
                                <div style="color:#cbd5e1; line-height:1.6; font-size:12px; display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:6px;">
                                    <div>${xpIcon} <strong>${terms.xp_book_name}:</strong> ${asc.xp_needed.toLocaleString()} EXP (~${asc.xp_books_purple} ${isEn ? "Purples" : "un. Roxos"})</div>
                                    <div>${moraIcon} <strong>${terms.currency_name}:</strong> ${asc.currency_needed.toLocaleString()}</div>
                                    ${asc.boss_items_needed > 0 ? `<div>${bIconHtml} <strong>${asc.boss_item_name || terms.boss_mat}:</strong> ${asc.boss_items_needed} ${isEn ? "pcs." : "un."}</div>` : ''}
                                    ${asc.local_specialty ? `<div>${specIconHtml} <strong>${asc.local_specialty}:</strong> ${isEn ? "Local Specialty" : "Especialidade Local"}</div>` : ''}
                                </div>
                            </div>
                        `;
                    }

                    // 2. Talentos / Habilidades
                    if (t.items_needed && t.items_needed.talent_upgrade_details && t.items_needed.talent_upgrade_details.length > 0) {
                        const isTalentOpen = t.talent_domain_open !== false;
                        html += `
                            <div style="background:rgba(56,189,248,0.05); padding:10px 12px; border-radius:8px; border-left:3px solid #38bdf8;">
                                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; flex-wrap:wrap; gap:6px;">
                                    <strong style="color:#38bdf8; display:flex; align-items:center; gap:6px; font-size:13px;">
                                         ${isEn ? `Detailed ${terms.talent_category} Upgrades:` : `Elevação de ${terms.talent_category} Detalhada por Habilidade:`}
                                    </strong>
                                    ${gameIdStr === "genshin" ? `
                                        <span style="font-size:11px; padding:2px 8px; border-radius:6px; background:${isTalentOpen ? 'rgba(56,189,248,0.15)' : 'rgba(234,179,8,0.15)'}; color:${isTalentOpen ? '#38bdf8' : '#fde047'}; font-weight:600;">
                                            <i class="fa-solid ${isTalentOpen ? 'fa-door-open' : 'fa-clock'}"></i> ${isTalentOpen ? (isEn ? 'Domain Open Today!' : 'Domínio Aberto Hoje!') : (isEn ? 'Domain Closed Today' : 'Domínio Fechado Hoje')}
                                        </span>
                                    ` : ''}
                                </div>
                                <div style="display:flex; flex-direction:column; gap:6px;">
                        `;
                        t.items_needed.talent_upgrade_details.forEach(td => {
                            let matsList = [];
                            if (td.green_books > 0) matsList.push(`${makeMatIcon(td.green_book_icon, finalIcons.talent_book)} ${td.green_books}x ${td.green_book_name || terms.green_book}`);
                            if (td.blue_books > 0) matsList.push(`${makeMatIcon(td.blue_book_icon, finalIcons.talent_book)} ${td.blue_books}x ${td.blue_book_name || terms.blue_book}`);
                            if (td.purple_books > 0) matsList.push(`${makeMatIcon(td.purple_book_icon, finalIcons.talent_book)} ${td.purple_books}x ${td.purple_book_name || terms.purple_book}`);
                            if (td.enemy_tier1 > 0) matsList.push(`${makeMatIcon(td.enemy_t1_icon, finalIcons.boss)} ${td.enemy_tier1}x ${td.enemy_t1_name || terms.enemy_t1 || 'Drop Inimigo (1★)'}`);
                            if (td.enemy_tier2 > 0) matsList.push(`${makeMatIcon(td.enemy_t2_icon, finalIcons.boss)} ${td.enemy_tier2}x ${td.enemy_t2_name || terms.enemy_t2 || 'Drop Inimigo (2★)'}`);
                            if (td.enemy_tier3 > 0) matsList.push(`${makeMatIcon(td.enemy_t3_icon, finalIcons.boss)} ${td.enemy_tier3}x ${td.enemy_t3_name || terms.enemy_t3 || 'Drop Inimigo (3★)'}`);
                            if (td.weekly_boss_mats > 0) matsList.push(`${makeMatIcon(td.weekly_boss_mat_icon, finalIcons.weekly_boss)} ${td.weekly_boss_mats}x ${td.weekly_boss_mat_name || terms.weekly_boss_mat}`);
                            if (td.crowns_needed > 0) matsList.push(`${makeMatIcon(td.crown_icon, finalIcons.crown)} ${td.crowns_needed}x ${td.crown_mat_name || terms.crown_mat}`);

                            const skillIconHtml = td.skill_icon ? `<img src="${td.skill_icon}" style="width:20px; height:20px; vertical-align:middle; margin-right:6px; object-fit:contain; border-radius:4px; background:rgba(0,0,0,0.3); padding:2px;">` : talentIcon;

                            html += `
                                <div style="background:rgba(0,0,0,0.3); padding:8px 12px; border-radius:6px; border:1px solid rgba(255,255,255,0.05);">
                                    <div style="font-weight:600; color:#f1f5f9; display:flex; justify-content:space-between; align-items:center; font-size:12px;">
                                        <span style="display:flex; align-items:center; gap:4px;">${skillIconHtml} ${td.skill_name}</span>
                                        <span style="font-size:11px; color:#38bdf8; background:rgba(56,189,248,0.15); padding:2px 8px; border-radius:12px; font-weight:600;">
                                            ${isEn ? "Lv." : "Nv."} ${td.current_level} ➔ ${isEn ? "Lv." : "Nv."} ${td.target_level}
                                        </span>
                                    </div>
                                    <div style="font-size:11px; color:#cbd5e1; margin-top:5px; display:flex; gap:12px; flex-wrap:wrap; align-items:center;">
                                        <span>${moraIcon} <strong>${terms.currency_name}:</strong> ${td.currency_needed.toLocaleString()}</span>
                                        ${matsList.length > 0 ? `<span style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">${matsList.join(" • ")}</span>` : ''}
                                    </div>
                                </div>
                            `;
                        });
                        html += `
                                </div>
                            </div>
                        `;
                    }

                    // 3. Arma / W-Engine Equipado
                    if (t.items_needed && t.items_needed.weapon_upgrade_details) {
                        const wd = t.items_needed.weapon_upgrade_details;
                        const wIconImg = wd.weapon_icon ? `<img src="${wd.weapon_icon}" style="width:24px; height:24px; object-fit:contain; background:rgba(0,0,0,0.4); border-radius:4px; padding:2px; border:1px solid rgba(255,255,255,0.1);">` : '';

                        let wMats = [];
                        if (wd.ores_needed > 0) wMats.push(`<div>${makeMatIcon(wd.ore_icon, finalIcons.weapon_ore)} <strong>${wd.ore_name || terms.ore_name}:</strong> ~${wd.ores_needed} un.</div>`);
                        if (wd.w_mat_green > 0) wMats.push(`<div>${makeMatIcon(wd.w_mat_green_icon, finalIcons.weapon_mat)} <strong>${wd.w_mat_green_name || terms.w_mat_green || (isEn ? 'Weapon Domain Mat. (2★)' : 'Mat. Domínio Arma (2★)')}:</strong> ${wd.w_mat_green} un.</div>`);
                        if (wd.w_mat_blue > 0) wMats.push(`<div>${makeMatIcon(wd.w_mat_blue_icon, finalIcons.weapon_mat)} <strong>${wd.w_mat_blue_name || terms.w_mat_blue || (isEn ? 'Weapon Domain Mat. (3★)' : 'Mat. Domínio Arma (3★)')}:</strong> ${wd.w_mat_blue} un.</div>`);
                        if (wd.w_mat_purple > 0) wMats.push(`<div>${makeMatIcon(wd.w_mat_purple_icon, finalIcons.weapon_mat)} <strong>${wd.w_mat_purple_name || terms.w_mat_purple || (isEn ? 'Weapon Domain Mat. (4★)' : 'Mat. Domínio Arma (4★)')}:</strong> ${wd.w_mat_purple} un.</div>`);
                        if (wd.w_mat_gold > 0) wMats.push(`<div>${makeMatIcon(wd.w_mat_gold_icon, finalIcons.weapon_mat)} <strong>${wd.w_mat_gold_name || terms.w_mat_gold || (isEn ? 'Weapon Domain Mat. (5★)' : 'Mat. Domínio Arma (5★)')}:</strong> ${wd.w_mat_gold} un.</div>`);
                        if (wd.w_enemy_t1 > 0) wMats.push(`<div>${makeMatIcon(wd.w_enemy_t1_icon, finalIcons.boss)} <strong>${wd.w_enemy_t1_name || terms.enemy_t1 || 'Drop Inimigo (1★)'}:</strong> ${wd.w_enemy_t1} un.</div>`);
                        if (wd.w_enemy_t2 > 0) wMats.push(`<div>${makeMatIcon(wd.w_enemy_t2_icon, finalIcons.boss)} <strong>${wd.w_enemy_t2_name || terms.enemy_t2 || 'Drop Inimigo (2★)'}:</strong> ${wd.w_enemy_t2} un.</div>`);
                        if (wd.w_enemy_t3 > 0) wMats.push(`<div>${makeMatIcon(wd.w_enemy_t3_icon, finalIcons.boss)} <strong>${wd.w_enemy_t3_name || terms.enemy_t3 || 'Drop Inimigo (3★)'}:</strong> ${wd.w_enemy_t3} un.</div>`);
                        if (wd.currency_needed > 0) wMats.push(`<div>${moraIcon} <strong>${terms.currency_name}:</strong> ${wd.currency_needed.toLocaleString()}</div>`);

                        html += `
                            <div style="background:rgba(16,185,129,0.05); padding:10px 12px; border-radius:8px; border-left:3px solid #10b981;">
                                <strong style="color:#34d399; display:flex; align-items:center; gap:8px; margin-bottom:6px; font-size:13px;">
                                    ${wIconImg} ${isEn ? "Equipped Weapon Ascension" : "Elevação da Arma Equipada"} (${wd.weapon_name}) - ${isEn ? "Lv." : "Nv."} ${wd.current_level} ➔ ${isEn ? "Lv." : "Nv."} ${wd.target_level}
                                </strong>
                                <div style="color:#cbd5e1; line-height:1.6; font-size:12px; display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:6px;">
                                    ${wMats.join("")}
                                </div>
                            </div>
                        `;
                    }

                    // 4. Relíquias / Discos
                    if (t.items_needed && t.items_needed.relics) {
                        html += `
                            <div style="background:rgba(245,158,11,0.05); padding:8px 10px; border-radius:6px; border-left:3px solid #f59e0b;">
                                <strong style="color:#f59e0b; display:block; margin-bottom:2px;"> ${isEn ? (gameIdStr === "zzz" ? "Drive Discs & Equipment:" : "Relics & Equipment:") : (gameIdStr === "zzz" ? "Discos de Acionamento & Equipamentos:" : "Relíquias & Equipamentos:")}</strong>
                                <div style="color:#cbd5e1;">${t.items_needed.relics}</div>
                            </div>
                        `;
                    }

                    html += `
                            </div>
                        </div>
                    `;
                });
            }

            body.innerHTML = html;

            // Event Listener para Filtro do Dia Genshin
            const cbFarmable = document.getElementById(`${targetContainerId}-farmable-only`);
            if (cbFarmable) {
                cbFarmable.addEventListener("change", (e) => {
                    localStorage.setItem(farmableOnlyKey, e.target.checked ? "true" : "false");
                    window.loadFarmData(gameId, targetContainerId);
                });
            }

        } catch (e) {
            console.error("Erro na Central de Farm:", e);
            body.innerHTML = `
                <div style='color:#ef4444; padding:20px; text-align:center; background:rgba(239,68,68,0.08); border-radius:10px; border:1px solid rgba(239,68,68,0.3);'>
                    <i class='fa-solid fa-triangle-exclamation fa-2x' style='margin-bottom:8px; display:block;'></i>
                    <strong style='font-size:14px; display:block; margin-bottom:4px;'>Erro ao carregar dados da Central de Farm</strong>
                    <span style='font-size:12px; color:#cbd5e1; display:block; margin-bottom:12px;'>${e.message || e}</span>
                    <button onclick="window.loadFarmData('${gameId}', '${targetContainerId}')" style="padding:6px 14px; background:rgba(56,189,248,0.2); color:#38bdf8; border:1px solid rgba(56,189,248,0.4); border-radius:6px; cursor:pointer; font-size:12px;">
                        <i class="fa-solid fa-rotate-right"></i> Tentar Novamente
                    </button>
                </div>
            `;
        }
    };

    // ==========================================
    // 2.0 CONTROLADOR DO SELETOR VISUAL DE PERSONAGENS ALVO DO FARM
    // ==========================================
    window.openFarmCharSelectorModal = async (gameId = "genshin", targetContainerId = "farm-content-body") => {
        window.currentFarmModalGame = gameId;
        window.currentFarmModalContainer = targetContainerId;

        const modal = document.getElementById("modal-farm-char-selector");
        if (!modal) return;

        // Atualiza abas do modal
        document.querySelectorAll(".farm-modal-game-btn").forEach(btn => {
            if (btn.dataset.game === gameId) {
                btn.classList.add("active");
                btn.style.background = "#10b981";
                btn.style.color = "#fff";
                btn.style.fontWeight = "700";
            } else {
                btn.classList.remove("active");
                btn.style.background = "transparent";
                btn.style.color = "#94a3b8";
                btn.style.fontWeight = "normal";
            }
        });

        // Carrega seleção salva
        const storageKey = `hoyo_farm_selected_${gameId}`;
        let savedSelected = null;
        try {
            const rawSaved = localStorage.getItem(storageKey);
            if (rawSaved) {
                const parsed = JSON.parse(rawSaved);
                if (Array.isArray(parsed)) savedSelected = parsed;
            }
        } catch(e) {}

        // Busca lista de personagens do cache ou API
        let rosterList = window.farmRosterCache[gameId] || [];
        if (rosterList.length === 0) {
            try {
                const res = await fetch(`/api/farming/today/${gameId}`);
                if (res.ok) {
                    const d = await res.json();
                    rosterList = d.all_roster_characters || (d.all_roster_names || []).map(n => ({ name: n, level: 90, rarity: 5, icon: '' }));
                    window.farmRosterCache[gameId] = rosterList;
                }
            } catch(e) {}
        }

        if (savedSelected && Array.isArray(savedSelected)) {
            if (savedSelected.includes("__none__")) {
                window.farmModalSelectedSet = new Set();
            } else {
                window.farmModalSelectedSet = new Set(savedSelected);
            }
        } else {
            window.farmModalSelectedSet = new Set(rosterList.map(c => c.name));
        }

        // Reseta campo de busca e filtros
        const searchInput = document.getElementById("farm-char-search-input");
        if (searchInput) searchInput.value = "";
        window.currentFarmFilterPill = "all";
        document.querySelectorAll(".farm-filter-pill").forEach(p => {
            if (p.dataset.filter === "all") p.classList.add("active");
            else p.classList.remove("active");
        });

        window.renderFarmModalGrid();
        modal.style.display = "flex";
    };

    window.closeFarmCharSelectorModal = () => {
        const modal = document.getElementById("modal-farm-char-selector");
        if (modal) modal.style.display = "none";
    };

    window.switchFarmModalGame = (gameId) => {
        window.currentFarmModalGame = gameId;
        window.openFarmCharSelectorModal(gameId, window.currentFarmModalContainer);
    };

    window.renderFarmModalGrid = () => {
        const grid = document.getElementById("farm-modal-char-grid");
        const countEl = document.getElementById("farm-modal-selection-count");
        if (!grid) return;

        const gameId = window.currentFarmModalGame || "genshin";
        const rosterList = window.farmRosterCache[gameId] || [];
        const searchVal = (document.getElementById("farm-char-search-input")?.value || "").toLowerCase().trim();
        const filterType = window.currentFarmFilterPill || "all";

        let filtered = rosterList.filter(c => {
            const nameMatch = !searchVal || (c.name || "").toLowerCase().includes(searchVal) || (typeof formatCharacterName === 'function' && formatCharacterName(c.name).toLowerCase().includes(searchVal));
            if (!nameMatch) return false;

            const rarityNum = parseInt(c.rarity) || (String(c.rarity).includes("5") || String(c.rarity).toUpperCase() === "S" ? 5 : 4);
            if (filterType === "5star" && rarityNum !== 5) return false;
            if (filterType === "4star" && rarityNum !== 4) return false;
            if (filterType === "pending" && !c.needs_ascension) return false;
            if (filterType === "needs_build" && !c.needs_relics) return false;

            return true;
        });

        if (countEl) {
            countEl.innerText = `${window.farmModalSelectedSet.size} / ${rosterList.length} ${isEn ? "selected" : "selecionados"}`;
        }

        if (filtered.length === 0) {
            grid.innerHTML = `<div style="grid-column: 1 / -1; padding: 24px; text-align: center; color: #94a3b8; font-size: 13px;">${isEn ? "No characters found matching the applied filters." : "Nenhum personagem encontrado com os filtros aplicados."}</div>`;
            return;
        }

        const gradeColors = { SSS: "#f59e0b", SS: "#ec4899", S: "#10b981", A: "#3b82f6", B: "#8b5cf6", C: "#6b7280", D: "#ef4444" };

        let html = "";
        filtered.forEach(c => {
            const isSelected = window.farmModalSelectedSet.has(c.name);
            const isFiveStar = (parseInt(c.rarity) === 5) || String(c.rarity).includes("5") || String(c.rarity).toUpperCase() === "S";
            const gColor = gradeColors[c.grade] || "#94a3b8";

            html += `
                <div class="farm-char-card ${isSelected ? 'selected' : ''} ${isFiveStar ? 'five-star' : 'four-star'}" onclick="window.toggleFarmModalCharCard('${c.name.replace(/'/g, "\\'")}')">
                    <div class="card-check-badge">
                        <i class="fa-solid fa-check"></i>
                    </div>
                    <div class="avatar-wrapper">
                        <img src="${c.icon || '/assets/logo.svg'}" onerror="this.src='/assets/logo.svg'" style="width: 100%; height: 100%; object-fit: cover;">
                    </div>
                    <div style="font-weight: 700; color: #fff; font-size: 12px; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; width: 100%;">
                        ${typeof formatCharacterName === 'function' ? formatCharacterName(c.name) : c.name}
                    </div>
                    <div style="display: flex; gap: 4px; align-items: center; justify-content: center; flex-wrap: wrap;">
                        <span style="font-size: 9px; padding: 1px 5px; border-radius: 4px; background: rgba(255,255,255,0.08); color: #cbd5e1;">${isEn ? 'Lv.' : 'Nv.'} ${c.level}</span>
                        ${c.grade && c.grade !== 'N/A' ? `<span style="font-size: 9px; padding: 1px 5px; border-radius: 4px; background: ${gColor}22; color: ${gColor}; font-weight: 700; border: 1px solid ${gColor}44;">${c.grade}</span>` : ''}
                    </div>
                </div>
            `;
        });

        grid.innerHTML = html;
    };

    window.toggleFarmModalCharCard = (charName) => {
        if (window.farmModalSelectedSet.has(charName)) {
            window.farmModalSelectedSet.delete(charName);
        } else {
            window.farmModalSelectedSet.add(charName);
        }
        window.renderFarmModalGrid();
    };

    window.selectAllFarmModalChars = () => {
        const gameId = window.currentFarmModalGame || "genshin";
        const rosterList = window.farmRosterCache[gameId] || [];
        rosterList.forEach(c => window.farmModalSelectedSet.add(c.name));
        window.renderFarmModalGrid();
    };

    window.deselectAllFarmModalChars = () => {
        window.farmModalSelectedSet.clear();
        window.renderFarmModalGrid();
    };

    window.selectMetaPicksFarmModal = () => {
        const gameId = window.currentFarmModalGame || "genshin";
        const rosterList = window.farmRosterCache[gameId] || [];
        window.farmModalSelectedSet.clear();
        rosterList.forEach(c => {
            const isFiveStar = (parseInt(c.rarity) === 5) || String(c.rarity).includes("5") || String(c.rarity).toUpperCase() === "S";
            if (isFiveStar || c.needs_ascension || c.needs_relics) {
                window.farmModalSelectedSet.add(c.name);
            }
        });
        window.renderFarmModalGrid();
    };

    window.setFarmFilterPill = (filterType) => {
        window.currentFarmFilterPill = filterType;
        document.querySelectorAll(".farm-filter-pill").forEach(btn => {
            if (btn.dataset.filter === filterType) btn.classList.add("active");
            else btn.classList.remove("active");
        });
        window.renderFarmModalGrid();
    };

    window.filterFarmCharCards = () => {
        window.renderFarmModalGrid();
    };

    window.saveAndApplyFarmCharSelection = () => {
        const gameId = window.currentFarmModalGame || "genshin";
        const storageKey = `hoyo_farm_selected_${gameId}`;
        const selectedArr = Array.from(window.farmModalSelectedSet);
        localStorage.setItem(storageKey, JSON.stringify(selectedArr.length > 0 ? selectedArr : ["__none__"]));
        window.closeFarmCharSelectorModal();
        window.loadFarmData(gameId, window.currentFarmModalContainer);
        if (typeof window.loadDailyFarmOrder === "function") {
            window.loadDailyFarmOrder(gameId);
        }
    };

    window.quickRemoveFarmTarget = (gameId, charName, targetContainerId) => {
        const storageKey = `hoyo_farm_selected_${gameId}`;
        let savedSelected = [];
        try {
            const raw = localStorage.getItem(storageKey);
            if (raw) savedSelected = JSON.parse(raw);
            if (!Array.isArray(savedSelected)) savedSelected = [];
        } catch(e) {}

        const rosterList = window.farmRosterCache[gameId] || [];
        if (savedSelected.length === 0 || savedSelected.includes("__none__")) {
            savedSelected = rosterList.map(c => c.name);
        }

        const newSelected = savedSelected.filter(n => n !== charName);
        localStorage.setItem(storageKey, JSON.stringify(newSelected.length > 0 ? newSelected : ["__none__"]));
        window.loadFarmData(gameId, targetContainerId);
        if (typeof window.loadDailyFarmOrder === "function") {
            window.loadDailyFarmOrder(gameId);
        }
    };

    window.quickSelectAllFarm = (gameId, targetContainerId) => {
        const storageKey = `hoyo_farm_selected_${gameId}`;
        const rosterList = window.farmRosterCache[gameId] || [];
        const allNames = rosterList.map(c => c.name);
        localStorage.setItem(storageKey, JSON.stringify(allNames));
        window.loadFarmData(gameId, targetContainerId);
        if (typeof window.loadDailyFarmOrder === "function") {
            window.loadDailyFarmOrder(gameId);
        }
    };

    window.quickDeselectAllFarm = (gameId, targetContainerId) => {
        const storageKey = `hoyo_farm_selected_${gameId}`;
        localStorage.setItem(storageKey, JSON.stringify(["__none__"]));
        window.loadFarmData(gameId, targetContainerId);
        if (typeof window.loadDailyFarmOrder === "function") {
            window.loadDailyFarmOrder(gameId);
        }
    };

    document.querySelectorAll(".farm-game-tab, .tab-farm-game-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const containerClass = btn.classList.contains("tab-farm-game-btn") ? ".tab-farm-game-btn" : ".farm-game-tab";
            const targetContainer = btn.classList.contains("tab-farm-game-btn") ? "tab-farm-content-body" : "farm-content-body";
            document.querySelectorAll(containerClass).forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            window.loadFarmData(btn.dataset.game, targetContainer);
        });
    });

    // ==========================================
    // 2.1 ORDEM DE SERVIÇO DO DIA (ROTEIRO DE ENERGIA)
    // ==========================================
    window.currentFarmOrderGame = "genshin";
    window.lastLoadedFarmOrder = null;

    window.loadDailyFarmOrder = async (gameId = window.currentFarmOrderGame || "genshin") => {
        window.currentFarmOrderGame = gameId;
        const container = document.getElementById("farm-order-tasks-list");
        if (!container) return;

        const weekdayTag = document.getElementById("farm-order-weekday-tag");
        const energyVal = document.getElementById("farm-order-energy-val");
        const energyBar = document.getElementById("farm-order-energy-bar");
        const progressText = document.getElementById("farm-order-progress-text");
        const progressBar = document.getElementById("farm-order-progress-bar");

        // Atualiza abas ativas
        document.querySelectorAll(".farm-order-game-btn").forEach(btn => {
            if (btn.dataset.game === gameId) {
                btn.classList.add("active");
                btn.style.background = "linear-gradient(135deg, #10b981, #059669)";
                btn.style.color = "#ffffff";
                btn.style.fontWeight = "700";
            } else {
                btn.classList.remove("active");
                btn.style.background = "transparent";
                btn.style.color = "#94a3b8";
                btn.style.fontWeight = "normal";
            }
        });

        const optimizingText = isEn ? "Optimizing daily energy schedule..." : "Otimizando roteiro diário de energia...";
        container.innerHTML = `<div style='color: #94a3b8; text-align: center; padding: 20px;'><i class='fa-solid fa-spinner fa-spin'></i> ${optimizingText}</div>`;

        try {
            const farmLang = window.isEn ? 'en' : 'pt';
            const res = await fetch(`/api/farm/order-of-day/${gameId}?lang=${farmLang}`);
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `Erro HTTP ${res.status}`);
            }
            const data = await res.json();
            window.lastLoadedFarmOrder = data;

            const WEEKDAY_DICT = {
                "Segunda-feira": "Monday",
                "Terça-feira": "Tuesday",
                "Quarta-feira": "Wednesday",
                "Quinta-feira": "Thursday",
                "Sexta-feira": "Friday",
                "Sábado": "Saturday",
                "Domingo": "Sunday"
            };
            const ENERGY_DICT = {
                "Resina Original": "Original Resin",
                "Poder de Desbravamento": "Trailblaze Power",
                "Carga de Bateria": "Battery Charge"
            };
            const TYPE_DICT = {
                "Chefe de Ascensão": "Ascension Boss",
                "Domínio de Livros de Talento": "Talent Book Domain",
                "Livros de Talento": "Talent Books",
                "Domínio de Artefatos": "Artifact Domain",
                "Domínio de Artefatos Recomendado": "Recommended Artifact Domain",
                "Cálice (Materiais)": "Calyx (Materials)",
                "Sombra Estagnada": "Stagnant Shadow",
                "Caverna da Corrosão": "Cavern of Corrosion",
                "Limpeza de Rotina": "Routine Cleanup",
                "Limpeza Periódica": "Periodic Cleanup",
                "Caçada Notória": "Notorious Hunt",
                "Especialidade Local": "Local Specialty"
            };

            const displayWk = (window.isEn && WEEKDAY_DICT[data.weekday_name]) ? WEEKDAY_DICT[data.weekday_name] : (data.weekday_name || (window.isEn ? 'Today' : 'Hoje'));
            if (weekdayTag) weekdayTag.innerText = displayWk;
            
            const energy = data.energy || {};
            const eName = (window.isEn && ENERGY_DICT[energy.name]) ? ENERGY_DICT[energy.name] : (energy.name || '');
            if (energyVal) energyVal.innerText = `${energy.current || 0} / ${energy.max || 0} ${eName}`;
            if (energyBar) energyBar.style.width = `${energy.usage_pct || 0}%`;

            const compCount = data.completed_count || 0;
            const totTasks = data.total_tasks || 0;
            const compPct = data.completion_percentage || 0;

            if (progressText) progressText.innerText = `${compCount}/${totTasks} (${compPct}%)`;
            if (progressBar) progressBar.style.width = `${compPct}%`;

            const tasks = data.tasks || [];
            if (tasks.length === 0) {
                const noTasksText = isEn ? "No pending recommendations for today!" : "Nenhuma recomendação pendente para hoje!";
                container.innerHTML = `<div style='color: #94a3b8; text-align: center; padding: 16px; background: rgba(255,255,255,0.02); border-radius: 8px;'>${noTasksText}</div>`;
                return;
            }

            let html = "";
            const stepWord = isEn ? "Step" : "Passo";
            const costWord = isEn ? "Cost" : "Custo";
            tasks.forEach(t => {
                const isDone = !!t.completed;
                const isAvail = !!t.available_now;
                const badgeBg = t.badge_color ? `${t.badge_color}22` : 'rgba(16,185,129,0.15)';
                const badgeColor = t.badge_color || '#10b981';
                const statusColor = isAvail ? '#10b981' : '#f59e0b';
                const statusBg = isAvail ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)';

                let curTypeLabel = (window.isEn && TYPE_DICT[t.type_label]) ? TYPE_DICT[t.type_label] : t.type_label;
                let curPBadge = t.priority_badge;
                let curEstimate = t.time_estimate;
                let curLoc = t.location;
                let curDesc = t.description;
                let curEnergyName = (window.isEn && ENERGY_DICT[t.energy_name]) ? ENERGY_DICT[t.energy_name] : t.energy_name;

                if (window.isEn) {
                    if (curPBadge && curPBadge.includes("Aberto Hoje")) curPBadge = "⭐ Open Today";
                    if (curPBadge && curPBadge.includes("Ascensão Pendente")) curPBadge = "🔥 Pending Ascension";
                    if (curPBadge && curPBadge.includes("Otimização de Build")) curPBadge = "💎 Build Optimization";
                    if (curEstimate && curEstimate.includes("Disponível Agora")) curEstimate = "Available Now";
                    if (curEstimate && curEstimate.includes("Disponível às")) curEstimate = curEstimate.replace("Disponível às", "Available at");
                    if (curEstimate && curEstimate.includes("Aguardando Energia")) curEstimate = "Waiting for Energy";
                    if (curLoc) {
                        curLoc = curLoc
                            .replace("Chefe de Ascensão", "Ascension Boss")
                            .replace("Domínio de Livros de Talento", "Talent Book Domain")
                            .replace("Domínio de Artefatos Recomendado", "Recommended Artifact Domain")
                            .replace("Domínio de Artefatos", "Artifact Domain")
                            .replace("Cálice Rubro", "Crimson Calyx")
                            .replace("Treinamento de Habilidades", "Skill Training");
                    }
                    if (curDesc) {
                        if (curDesc.startsWith("Derrote")) {
                            curDesc = curDesc
                                .replace("Derrote", "Defeat")
                                .replace("Chefe de Ascensão", "Ascension Boss")
                                .replace("para avançar", "to advance")
                                .replace("do Nv.", "from Lv.")
                                .replace("rumo ao Nv.", "towards Lv.");
                        } else if (curDesc.startsWith("Faça")) {
                            curDesc = curDesc
                                .replace("Faça", "Run")
                                .replace("Domínio de Livros de Talento", "Talent Book Domain")
                                .replace("Domínio de Artefatos Recomendado", "Recommended Artifact Domain")
                                .replace("para obter", "to obtain")
                                .replace("e avançar os talentos prioritários de", "and advance priority talents for")
                                .replace("para farmar o conjunto ideal para", "to farm recommended set for")
                                .replace("Nota", "Grade");
                        } else if (curDesc.startsWith("Realize")) {
                            curDesc = curDesc
                                .replace("Realize", "Run")
                                .replace("Domínio de Artefatos", "Artifact Domain")
                                .replace("buscando peças com Atributos Ideais para maximizar a nota de", "seeking optimal main and sub-stats to maximize the rating of");
                        }
                    }
                }

                html += `
                    <div class="farm-order-step-item" id="order-step-item-${t.id}" style="display: flex; align-items: flex-start; gap: 12px; padding: 12px 14px; background: ${isDone ? 'rgba(16, 185, 129, 0.08)' : 'rgba(15, 23, 42, 0.7)'}; border: 1px solid ${isDone ? 'rgba(16, 185, 129, 0.4)' : 'rgba(255, 255, 255, 0.06)'}; border-radius: 12px; transition: all 0.25s ease; ${isDone ? 'opacity: 0.75;' : ''}">
                        <!-- Checkbox de Conclusão -->
                        <div style="padding-top: 2px;">
                            <input type="checkbox" class="farm-order-step-cb" data-game="${gameId}" data-task-id="${t.id}" ${isDone ? 'checked' : ''} style="width: 18px; height: 18px; cursor: pointer; accent-color: #10b981;">
                        </div>

                        <!-- Avatar do Personagem ou Ícone -->
                        <div style="width: 38px; height: 38px; border-radius: 10px; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; flex-shrink: 0; overflow: hidden; position: relative;">
                            ${t.character_icon ? `<img src="${t.character_icon}" style="width: 100%; height: 100%; object-fit: cover;">` : `<i class="fa-solid ${t.type_icon || 'fa-seedling'}" style="color: #38bdf8; font-size: 16px;"></i>`}
                            ${t.character_grade ? `<span style="position: absolute; bottom: 0; right: 0; font-size: 8px; font-weight: 800; background: rgba(0,0,0,0.8); color: #f59e0b; padding: 1px 3px; border-top-left-radius: 4px;">${t.character_grade}</span>` : ''}
                        </div>

                        <!-- Detalhes do Passo -->
                        <div style="flex: 1; min-width: 0;">
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px;">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <strong style="font-size: 13px; color: ${isDone ? '#94a3b8' : '#ffffff'}; ${isDone ? 'text-decoration: line-through;' : ''}">${stepWord} ${t.step}: ${t.target_character} • ${curTypeLabel}</strong>
                                    <span style="font-size: 10px; background: ${badgeBg}; color: ${badgeColor}; padding: 1px 6px; border-radius: 4px; font-weight: 600;">${curPBadge}</span>
                                </div>
                                <span style="font-size: 10px; background: ${statusBg}; color: ${statusColor}; padding: 2px 8px; border-radius: 10px; font-weight: 700;">
                                    <i class="fa-solid ${isAvail ? 'fa-circle-check' : 'fa-clock'}"></i> ${curEstimate}
                                </span>
                            </div>

                            <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px;">
                                <span style="color: #38bdf8; font-weight: 600;">${t.material_name}</span> • <span style="color: var(--text-muted);">${curLoc}</span>
                            </div>

                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px; font-size: 11px; color: var(--text-muted); flex-wrap: wrap; gap: 6px;">
                                <span>${curDesc}</span>
                                <span style="color: #e2e8f0; background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px;">
                                    <i class="fa-solid fa-bolt" style="color: #38bdf8;"></i> ${costWord}: <strong>${t.cost_energy} ${curEnergyName}</strong> (${t.runs}x)
                                </span>
                            </div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;

            // Listeners nos Checkboxes de Conclusão
            container.querySelectorAll(".farm-order-step-cb").forEach(cb => {
                cb.addEventListener("change", async (e) => {
                    const taskId = e.target.dataset.taskId;
                    const gId = e.target.dataset.game;
                    const isChecked = e.target.checked;
                    const stepEl = document.getElementById(`order-step-item-${taskId}`);

                    if (stepEl) {
                        stepEl.style.opacity = isChecked ? "0.75" : "1";
                        stepEl.style.background = isChecked ? "rgba(16, 185, 129, 0.08)" : "rgba(15, 23, 42, 0.7)";
                        stepEl.style.borderColor = isChecked ? "rgba(16, 185, 129, 0.4)" : "rgba(255, 255, 255, 0.06)";
                    }

                    try {
                        await fetch("/api/farm/order-of-day/toggle-step", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                game_id: gId,
                                task_id: taskId,
                                completed: isChecked
                            })
                        });
                        // Recarrega contadores
                        window.loadDailyFarmOrder(gId);
                    } catch (err) {
                        console.error("Erro ao salvar conclusão de tarefa de farm:", err);
                    }
                });
            });

        } catch (e) {
            console.error("Erro ao carregar Ordem de Serviço:", e);
            container.innerHTML = "<div style='color: #ef4444; padding: 14px;'>Erro ao calcular a Ordem de Serviço do dia.</div>";
        }
    };

    // Listeners dos Botões da Ordem do Dia
    document.querySelectorAll(".farm-order-game-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            window.loadDailyFarmOrder(btn.dataset.game);
        });
    });

    const btnCopyOrder = document.getElementById("btn-copy-farm-order");
    if (btnCopyOrder) {
        btnCopyOrder.addEventListener("click", () => {
            const textToCopy = window.lastLoadedFarmOrder?.quick_summary_text;
            if (textToCopy) {
                navigator.clipboard.writeText(textToCopy).then(() => {
                    const origHtml = btnCopyOrder.innerHTML;
                    btnCopyOrder.innerHTML = `<i class="fa-solid fa-check"></i> Roteiro Copiado!`;
                    btnCopyOrder.style.borderColor = "#10b981";
                    btnCopyOrder.style.color = "#4ade80";
                    setTimeout(() => {
                        btnCopyOrder.innerHTML = origHtml;
                        btnCopyOrder.style.borderColor = "rgba(56,189,248,0.4)";
                        btnCopyOrder.style.color = "#38bdf8";
                    }, 2500);
                }).catch(err => {
                    console.error("Erro ao copiar texto:", err);
                });
            }
        });
    }

    const btnSendOrderNotif = document.getElementById("btn-send-farm-order-notif");
    if (btnSendOrderNotif) {
        btnSendOrderNotif.addEventListener("click", async () => {
            btnSendOrderNotif.disabled = true;
            btnSendOrderNotif.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Enviando...`;
            try {
                const res = await fetch("/api/farm/order-of-day/send-notification", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ game_id: window.currentFarmOrderGame || "genshin" })
                });
                const data = await res.json();
                if (data.status === "success") {
                    btnSendOrderNotif.innerHTML = `<i class="fa-solid fa-check"></i> Notificação Enviada!`;
                    btnSendOrderNotif.style.color = "#4ade80";
                    setTimeout(() => {
                        btnSendOrderNotif.disabled = false;
                        btnSendOrderNotif.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Enviar p/ Discord/Telegram`;
                        btnSendOrderNotif.style.color = "#10b981";
                    }, 3000);
                } else {
                    alert("Aviso: Notificações estão desativadas nas Configurações ou os Webhooks não foram configurados.");
                    btnSendOrderNotif.disabled = false;
                    btnSendOrderNotif.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Enviar p/ Discord/Telegram`;
                }
            } catch (err) {
                console.error("Erro ao enviar notificação de farm:", err);
                btnSendOrderNotif.disabled = false;
                btnSendOrderNotif.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Enviar p/ Discord/Telegram`;
            }
        });
    }

    const btnRefreshOrder = document.getElementById("btn-refresh-farm-order");
    if (btnRefreshOrder) {
        btnRefreshOrder.addEventListener("click", () => {
            window.loadDailyFarmOrder(window.currentFarmOrderGame);
        });
    }

    // Inicializa a Ordem do Dia na inicialização
    setTimeout(() => {
        if (document.getElementById("farm-order-tasks-list")) {
            window.loadDailyFarmOrder("genshin");
        }
    }, 600);

    window.addEventListener("app:languageChanged", () => {
        if (document.getElementById("farm-order-tasks-list") && typeof window.loadDailyFarmOrder === "function") {
            window.loadDailyFarmOrder(window.currentFarmOrderGame || "genshin");
        }
    });

    // 3. RELÍQUIAS LIXO (TRASH FINDER)
    window.loadTrashRelics = async (gameId, targetContainerId = "trash-relics-body") => {
        const body = document.getElementById(targetContainerId);
        if (!body) return;

        body.innerHTML = `<div style='color:#94a3b8; padding: 20px; text-align: center;'><i class='fa-solid fa-spinner fa-spin' style='margin-right: 8px;'></i> ${isEn ? "Analyzing relic inventory and calculating Crit Values against the metagame..." : "Analisando inventário de relíquias e calculando Crit Values contra o metagame..."}</div>`;
        try {
            const res = await fetch(`/api/relics/trash/${gameId}`);
            const data = await res.json();
            
            let html = "";
            if (!data.total_analyzed || data.total_analyzed === 0) {
                html = `
                    <div style="padding:16px; background:rgba(245, 158, 11, 0.08); border-radius:10px; border:1px solid rgba(245, 158, 11, 0.3); color:#f59e0b; font-size:13px; line-height:1.5;">
                        <strong style="font-size:14px; display:block; margin-bottom:4px;"><i class="fa-solid fa-triangle-exclamation"></i> Nenhum dado de relíquias/artefatos encontrado no banco de dados.</strong>
                        Sincronize seu perfil e lista de personagens no painel principal via HoyoLab / UID para importar suas relíquias equipadas para análise.
                    </div>
                `;
            } else {
                // Header Resumo Duplo: Peças Coringa Protegidas & Peças Lixo
                html = `
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin-bottom: 20px;">
                        <div style="padding: 14px 16px; background: linear-gradient(135deg, rgba(168, 85, 247, 0.15), rgba(234, 179, 8, 0.10)); border-radius: 10px; border: 1px solid rgba(168, 85, 247, 0.4); box-shadow: 0 4px 15px rgba(168, 85, 247, 0.08);">
                            <div style="display: flex; align-items: center; justify-content: space-between;">
                                <span style="font-size: 15px; font-weight: 700; color: #c084fc; display: flex; align-items: center; gap: 8px;">
                                    <i class="fa-solid fa-crown" style="color: #fbbf24;"></i> ${data.coringa_count} ${isEn ? "Protected Wildcard Pieces" : "Peças Coringa Protegidas"}
                                </span>
                                <span style="font-size: 11px; padding: 2px 8px; border-radius: 12px; background: rgba(168, 85, 247, 0.25); color: #e9d5ff; font-weight: 600;">Off-Piece Safe</span>
                            </div>
                            <div style="font-size: 12px; color: #cbd5e1; margin-top: 6px; line-height: 1.4;">
                                ${isEn ? "Double-crit or high Crit Value pieces protected against accidental disposal for universal 2pc+2pc or off-piece builds." : "Peças com Duplo Crítico ou Crit Value superior salvas contra descarte acidental para uso universal ou composições 2pc+2pc / off-piece."}
                            </div>
                        </div>

                        <div style="padding: 14px 16px; background: rgba(239, 68, 68, 0.08); border-radius: 10px; border: 1px solid rgba(239, 68, 68, 0.3);">
                            <div style="display: flex; align-items: center; justify-content: space-between;">
                                <span style="font-size: 15px; font-weight: 700; color: #ef4444; display: flex; align-items: center; gap: 8px;">
                                    <i class="fa-solid fa-trash-can"></i> ${data.trash_count} ${isEn ? "Trash Relic(s)" : "Peça(s) Lixo"}
                                </span>
                                <span style="font-size: 11px; padding: 2px 8px; border-radius: 12px; background: rgba(239, 68, 68, 0.2); color: #fca5a5; font-weight: 600;">Total: ${data.total_analyzed}</span>
                            </div>
                            <div style="font-size: 12px; color: #94a3b8; margin-top: 6px; line-height: 1.4;">
                                ${isEn ? "Pieces with zero meta synergy, no crits and multiple flat stats recommended for EXP or salvage." : "Peças sem sinergia com o meta, sem críticos e com múltiplos atributos planos recomendadas para conversão em EXP ou síntese."}
                            </div>
                        </div>
                    </div>
                `;

                // 1. Bloco de Peças Coringa Protegidas
                const coringaList = data.coringa_relics || [];
                html += `
                    <div style="margin-bottom: 24px;">
                        <h3 style="font-size: 14px; color: #e2e8f0; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                            <i class="fa-solid fa-gem" style="color: #a855f7;"></i> ${isEn ? "Wildcard Treasures & Off-Piece Items Identified" : "Tesouros Coringa & Peças Off-Piece Identificadas"} (${coringaList.length})
                        </h3>
                `;

                if (coringaList.length === 0) {
                    html += `
                        <div style="padding: 12px; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px dashed rgba(255,255,255,0.1); font-size: 12px; color: #94a3b8;">
                            Nenhuma peça com Duplo Crítico ou Crit Value extremo identificada no momento.
                        </div>
                    `;
                } else {
                    html += `<div style="display: flex; flex-direction: column; gap: 10px;">`;
                    coringaList.forEach(r => {
                        const cvBadge = r.crit_value 
                            ? `<span style="padding: 2px 8px; border-radius: 6px; background: rgba(234, 179, 8, 0.15); border: 1px solid rgba(234, 179, 8, 0.4); color: #fde047; font-weight: 700; font-size: 11px;">CV: ${r.crit_value}</span>` 
                            : "";
                        const charBadge = r.character_name 
                            ? `<span style="font-size: 11px; color: #a78bfa; background: rgba(167, 139, 250, 0.1); padding: 2px 6px; border-radius: 4px;"><i class="fa-solid fa-user-check" style="margin-right: 4px;"></i>${r.character_name}</span>`
                            : "";
                        const iconImg = r.icon 
                            ? `<img src="${r.icon}" style="width: 36px; height: 36px; border-radius: 6px; object-fit: cover; border: 1px solid rgba(168, 85, 247, 0.3); background: rgba(0,0,0,0.4);" alt="${r.name}">` 
                            : `<div style="width: 36px; height: 36px; border-radius: 6px; background: rgba(168, 85, 247, 0.15); display: flex; align-items: center; justify-content: center; color: #c084fc;"><i class="fa-solid fa-shield-halved"></i></div>`;

                        // Destaque nos substatus
                        const subFormatted = (r.substats || []).map(s => {
                            if (/crit|taxa|dano|vel|spd/i.test(s)) {
                                return `<span style="color: #fde047; font-weight: 600;">${s}</span>`;
                            }
                            return `<span>${s}</span>`;
                        }).join(" • ");

                        html += `
                            <div style="padding: 12px 14px; background: rgba(15, 23, 42, 0.7); border-radius: 8px; border: 1px solid rgba(168, 85, 247, 0.25); display: flex; gap: 12px; align-items: center; transition: all 0.2s ease;">
                                ${iconImg}
                                <div style="flex: 1; min-width: 0;">
                                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 6px;">
                                        <div style="display: flex; align-items: center; gap: 8px;">
                                            <strong style="color: #ffffff; font-size: 13px;">${r.name}</strong>
                                            <span style="color: #94a3b8; font-size: 12px;">(${r.slot})</span>
                                            ${charBadge}
                                        </div>
                                        <div style="display: flex; align-items: center; gap: 6px;">
                                            ${cvBadge}
                                            <span style="padding: 2px 8px; border-radius: 9999px; background: linear-gradient(90deg, rgba(168, 85, 247, 0.3), rgba(234, 179, 8, 0.2)); border: 1px solid rgba(168, 85, 247, 0.4); color: #f5d0fe; font-size: 11px; font-weight: 600;">${r.coringa_tier}</span>
                                        </div>
                                    </div>
                                    <div style="margin-top: 4px; font-size: 12px; color: #cbd5e1;">
                                        <span style="color: #38bdf8; font-weight: 600;">${isEn ? "Main:" : "Principal:"}</span> ${r.main_stat} | <span style="color: #94a3b8;">Sub:</span> ${subFormatted || (isEn ? "None" : "Nenhum")}
                                    </div>
                                    <div style="margin-top: 4px; font-size: 11px; color: #a3e635; display: flex; align-items: center; gap: 4px;">
                                        <i class="fa-solid fa-shield" style="font-size: 10px;"></i> ${r.reason}
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    html += `</div>`;
                }
                html += `</div>`;

                // 2. Bloco de Relíquias Lixo (Desmanche Seguro)
                const trashList = data.trash_relics || [];
                html += `
                    <div>
                        <h3 style="font-size: 14px; color: #e2e8f0; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                            <i class="fa-solid fa-recycle" style="color: #ef4444;"></i> ${isEn ? "Trash Pieces Recommended for Salvage" : "Peças Lixo Recomendadas para Desmanche"} (${trashList.length})
                        </h3>
                `;

                if (trashList.length === 0) {
                    html += `<div style="font-size:13px; color:#10b981; padding: 12px; background: rgba(16, 185, 129, 0.08); border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.3);"><i class="fa-solid fa-circle-check" style="margin-right: 6px;"></i> ${isEn ? "No trash relics detected! Your inventory is clean." : "Nenhuma relíquia lixo detectada! Seu inventário está limpo."}</div>`;
                } else {
                    html += `<div style="display: flex; flex-direction: column; gap: 10px;">`;
                    trashList.forEach(r => {
                        const iconImg = r.icon 
                            ? `<img src="${r.icon}" style="width: 34px; height: 34px; border-radius: 6px; object-fit: cover; border: 1px solid rgba(239, 68, 68, 0.3); background: rgba(0,0,0,0.4);" alt="${r.name}">` 
                            : `<div style="width: 34px; height: 34px; border-radius: 6px; background: rgba(239, 68, 68, 0.15); display: flex; align-items: center; justify-content: center; color: #f87171;"><i class="fa-solid fa-trash-can"></i></div>`;
                        const charBadge = r.character_name 
                            ? `<span style="font-size: 11px; color: #94a3b8; background: rgba(255, 255, 255, 0.05); padding: 2px 6px; border-radius: 4px;">Em: ${r.character_name}</span>`
                            : "";

                        html += `
                            <div style="padding:12px; background:rgba(15,23,42,0.6); border-radius:8px; border:1px solid rgba(255,255,255,0.06); font-size:13px; display: flex; gap: 12px; align-items: center;">
                                ${iconImg}
                                <div style="flex: 1; min-width: 0;">
                                    <div style="display:flex; justify-content:space-between; align-items: center;">
                                        <div style="display: flex; align-items: center; gap: 8px;">
                                            <strong style="color:#ffffff;">${r.name} (${r.slot})</strong>
                                            ${charBadge}
                                        </div>
                                        <span style="color:#ef4444; font-weight:bold; font-size:12px;">${r.main_stat}</span>
                                    </div>
                                    <div style="color:#94a3b8; font-size:12px; margin-top:4px;">${isEn ? "Substats:" : "Substatus:"} ${r.substats ? r.substats.join(", ") : (isEn ? "None" : "Nenhum")}</div>
                                    <div style="color:#f59e0b; font-size:12px; margin-top:3px;"><i class="fa-solid fa-circle-exclamation" style="margin-right: 4px;"></i> Motivo: ${r.reason}</div>
                                </div>
                            </div>
                        `;
                    });
                    html += `</div>`;
                }
                html += `</div>`;
            }
            body.innerHTML = html;
        } catch (e) {
            body.innerHTML = `<div style='color:#ef4444; padding: 12px;'>${isEn ? "Error analyzing trash relics and flex pieces." : "Erro ao analisar relíquias lixo e peças coringa."}</div>`;
        }
    };

    document.querySelectorAll(".trash-game-tab, .tab-trash-game-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const containerClass = btn.classList.contains("tab-trash-game-btn") ? ".tab-trash-game-btn" : ".trash-game-tab";
            const targetContainer = btn.classList.contains("tab-trash-game-btn") ? "tab-trash-relics-body" : "trash-relics-body";
            document.querySelectorAll(containerClass).forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            window.loadTrashRelics(btn.dataset.game, targetContainer);
        });
    });

    // 4. TIER LIST & AUDIT REPORT
    window.loadAuditReport = async (gameId, targetContainerId = "audit-report-body") => {
        window.currentAuditGameId = gameId;
        const body = document.getElementById(targetContainerId);
        if (!body) return;

        body.innerHTML = "<div style='color:#94a3b8;'>Gerando relatório de auditoria e Tier List da conta...</div>";
        try {
            const res = await fetch(`/api/audit/${gameId}`);
            const data = await res.json();
            
            let html = `
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin-bottom:20px;">
                    <div style="padding:12px; background:rgba(255,255,255,0.03); border-radius:10px; text-align:center; border:1px solid var(--border-color);">
                        <span style="font-size:12px; color:#94a3b8;">${isEn ? "Total Characters" : "Total Personagens"}</span>
                        <h3 style="margin:4px 0 0 0; color:#38bdf8; font-size:20px;">${data.total_characters}</h3>
                    </div>
                    <div style="padding:12px; background:rgba(255,255,255,0.03); border-radius:10px; text-align:center; border:1px solid var(--border-color);">
                        <span style="font-size:12px; color:#94a3b8;">${isEn ? "Average RV Grade" : "Média de Nota RV"}</span>
                        <h3 style="margin:4px 0 0 0; color:#f59e0b; font-size:20px;">${data.avg_rv}%</h3>
                    </div>
                    <div style="padding:12px; background:rgba(255,255,255,0.03); border-radius:10px; text-align:center; border:1px solid var(--border-color);">
                        <span style="font-size:12px; color:#94a3b8;">${isEn ? "S/SSS Builds" : "Builds Nota S/SSS"}</span>
                        <h3 style="margin:4px 0 0 0; color:#10b981; font-size:20px;">${data.s_count}</h3>
                    </div>
                </div>
                <h4 style="margin:0 0 12px 0; color:#a855f7; font-size:16px;">🏆 ${isEn ? "Character Tier List by RV Grade" : "Tier List dos seus Personagens por Nota RV"}</h4>
            `;

            const tierColors = { "S+": "#ef4444", "S": "#f59e0b", "A": "#10b981", "B": "#38bdf8", "C/D": "#94a3b8", "Sem Equipamento": "#64748b" };
            const tierList = data.tier_list || {};

            for (const [tier, chars] of Object.entries(tierList)) {
                if (tier === "Sem Equipamento" && (!chars || chars.length === 0)) continue;
                const isUnequipped = tier === "Sem Equipamento";
                const color = tierColors[tier] || '#94a3b8';
                const badgeLabel = isUnequipped ? '<i class="fa-solid fa-box-open" style="font-size:16px;"></i>' : tier;
                html += `
                    <div style="display:flex; align-items:center; gap:14px; margin-bottom:12px; padding:12px; background:rgba(15,23,42,0.6); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">
                        <div style="width:54px; min-width:54px; height:54px; background:${color}; color:#fff; font-weight:800; display:flex; align-items:center; justify-content:center; border-radius:10px; font-size:${isUnequipped ? '14px' : '18px'}; box-shadow: 0 4px 12px ${color}44;" title="${isUnequipped ? 'Sem Equipamentos' : tier}">${badgeLabel}</div>
                        <div style="display:flex; flex-wrap:wrap; gap:10px; flex:1; align-items:center;">
                `;
                if (!chars || chars.length === 0) {
                    html += `<span style="font-size:13px; color:#64748b; font-style:italic;">${isEn ? "No characters in this category" : "Nenhum personagem nesta categoria"}</span>`;
                } else {
                    chars.forEach(c => {
                        const iconSrc = c.icon || '';
                        const iconHtml = iconSrc ? `<img src="${iconSrc}" alt="${c.name}" style="width:52px; height:52px; border-radius:10px; object-fit:cover; border:2px solid ${color}; background:rgba(0,0,0,0.5); flex-shrink:0;" onerror="this.style.display='none'">` : '';
                        html += `
                            <div style="display:flex; align-items:center; gap:10px; padding:8px 14px; background:rgba(255,255,255,0.06); border-radius:10px; border:1px solid rgba(255,255,255,0.1); min-height:64px; transition:all 0.2s ease;" onmouseover="this.style.borderColor='${color}'; this.style.transform='translateY(-2px)'" onmouseout="this.style.borderColor='rgba(255,255,255,0.1)'; this.style.transform='none'">
                                ${iconHtml}
                                <div style="display:flex; flex-direction:column; justify-content:center;">
                                    <strong style="color:#ffffff; font-size:13px; font-weight:600; line-height:1.2;">${typeof formatCharacterName === 'function' ? formatCharacterName(c.name) : c.name}</strong>
                                    <div style="display:flex; align-items:center; gap:6px; margin-top:3px;">
                                        ${isUnequipped ? `<span style="color:#94a3b8; font-size:11px; font-weight:500;">Sem Equipamento</span>` : `<span style="color:${color}; font-weight:700; font-size:12px;">${c.score.toFixed(1)}%</span><span style="font-size:10px; color:#ffffff; font-weight:bold; background:rgba(255,255,255,0.12); padding:1px 6px; border-radius:4px;">${c.grade}</span>`}
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                }
                html += `</div></div>`;
            }
            body.innerHTML = html;
        } catch (e) {
            body.innerHTML = "<div style='color:#ef4444;'>Erro ao gerar auditoria da conta.</div>";
        }
    };

    document.querySelectorAll(".audit-game-tab, .tab-audit-game-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const containerClass = btn.classList.contains("tab-audit-game-btn") ? ".tab-audit-game-btn" : ".audit-game-tab";
            const targetContainer = btn.classList.contains("tab-audit-game-btn") ? "tab-audit-report-body" : "audit-report-body";
            document.querySelectorAll(containerClass).forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            window.loadAuditReport(btn.dataset.game, targetContainer);
        });
    });

    // Initialize upgraded Gacha Simulator handlers
    if (window.initGachaSimulator) {
        window.initGachaSimulator();
    }

    // Event listener para o botão de apagar pastas e banco de dados (Zona de Perigo)
    const btnResetData = document.getElementById("btn-reset-data");
    if (btnResetData) {
        btnResetData.addEventListener("click", async () => {
            const confirmed = confirm("ATENÇÃO: Deseja realmente apagar as 3 pastas (zzz, hsr, genshin) e todo o banco de dados? Esta ação não pode ser desfeita.");
            if (!confirmed) return;

            btnResetData.disabled = true;
            btnResetData.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Apagando dados...';

            try {
                const res = await fetch("/api/reset-data", { method: "POST" });
                const data = await res.json();
                if (res.ok) {

    alert(data.message || (isEn ? "Folders and database deleted successfully!" : "Pastas e banco de dados apagados com sucesso!"));
                    window.location.reload();
                } else {
                    alert("Erro ao apagar dados: " + (data.detail || "Erro desconhecido."));
                }
            } catch (err) {
                console.error("Erro ao apagar dados:", err);
                alert("Falha na comunicação com o servidor ao tentar apagar os dados.");
            } finally {
                btnResetData.disabled = false;
                btnResetData.innerHTML = '<i class="fa-solid fa-trash-can"></i> Apagar Pastas e Banco de Dados';
            }
        });
    }



    document.querySelectorAll(".tab-history-game-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-history-game-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            window.loadAccountHistory(btn.dataset.game);
        });
    });

    const btnToggleChanged = document.getElementById("btn-toggle-changed-only");
    if (btnToggleChanged && !btnToggleChanged.dataset.bound) {
        btnToggleChanged.dataset.bound = "true";
        btnToggleChanged.addEventListener("click", () => {
            window.historyOnlyChanged = !window.historyOnlyChanged;
            if (window.historyOnlyChanged) {
                btnToggleChanged.classList.add("active");
                btnToggleChanged.style.background = "#ec4899";
                btnToggleChanged.style.color = "#fff";
            } else {
                btnToggleChanged.classList.remove("active");
                btnToggleChanged.style.background = "";
                btnToggleChanged.style.color = "#f472b6";
            }
            const activeBtn = document.querySelector(".tab-history-game-btn.active");
            const gameId = activeBtn ? activeBtn.dataset.game : "hsr";
            window.loadAccountHistory(gameId);
        });
    }

    document.querySelectorAll(".tab-codes-game-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-codes-game-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            window.loadPromoCodes(btn.dataset.game);
        });
    });

    const btnRedeemAllCodes = document.getElementById("btn-redeem-all-codes");
    if (btnRedeemAllCodes) {
        btnRedeemAllCodes.addEventListener("click", async () => {
            const activeBtn = document.querySelector(".tab-codes-game-btn.active");
            const gameId = activeBtn ? activeBtn.dataset.game : "hsr";
            btnRedeemAllCodes.disabled = true;
            btnRedeemAllCodes.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Resgatando Lote...`;
            try {
                const res = await fetch("/api/codes/redeem", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ game_id: gameId })
                });
                const data = await res.json();
                const statusBox = document.getElementById("codes-redeem-status");
                if (data.results && data.results.length) {
                    statusBox.innerHTML = `<div style="padding: 12px; border-radius: 8px; background: rgba(16,185,129,0.1); border: 1px solid #10b981; color: #4ade80;">
                        <strong>Resultados do Resgate (${gameId.toUpperCase()}):</strong>
                        <ul style="margin-left: 16px; margin-top: 6px;">
                            ${data.results.map(r => `<li>${r.code}: ${r.message}</li>`).join('')}
                        </ul>
                    </div>`;
                }
            } catch (e) {
                showToast("Erro ao resgatar lote de códigos.");
            } finally {
                btnRedeemAllCodes.disabled = false;
                btnRedeemAllCodes.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> Resgatar Todos os Códigos`;
            }
        });
    }

    // Auto-carregamento inicial de dados quando as abas são ativadas
    document.querySelectorAll(".nav-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const tab = btn.getAttribute("data-tab");
            if (tab === "farm") window.loadFarmData("genshin", "tab-farm-content-body");
            if (tab === "trash") window.loadTrashRelics("genshin", "tab-trash-relics-body");
            if (tab === "audit") window.loadAuditReport("hsr", "tab-audit-report-body");
            if (tab === "history") window.loadAccountHistory("hsr");
        });
    });

window.currentDiffDataCache = null;

window.openCharacterDiffModal = function(cData) {
    if (!cData) return;
    window.currentDiffDataCache = cData;

    const modal = document.getElementById("modal-character-diff-detail");
    const iconEl = document.getElementById("diff-modal-char-icon");
    const nameEl = document.getElementById("diff-modal-char-name");
    const subEl = document.getElementById("diff-modal-char-sub");
    const bodyEl = document.getElementById("character-diff-detail-body");

    if (!modal || !bodyEl) return;

    const name = cData.name || (isEn ? "Character" : "Personagem");
    iconEl.src = cData.icon || "/assets/logo.svg";
    nameEl.textContent = name;

    const base = cData.base || {};
    const target = cData.target || {};
    const diffs = cData.diffs || {};

    if (cData.is_new) {
        subEl.innerHTML = isEn ? `<span style="color: #f59e0b; font-weight: 700;">★ New Character Acquired!</span>` : `<span style="color: #f59e0b; font-weight: 700;">★ Novo Personagem Adquirido!</span>`;
    } else {
        subEl.innerHTML = `Comparativo de Evolução de Build (${cData.rarity || 4}★ ${cData.element || ''})`;
    }

    let html = '';

    // KPI Header Cards
    const levelPrev = base.level || 0;
    const levelCurr = target.level || 0;
    const levelDiff = diffs.level_diff !== undefined ? diffs.level_diff : (levelCurr - levelPrev);

    const rankPrev = base.rank_str || 'E0/C0';
    const rankCurr = target.rank_str || 'E0/C0';

    const scorePrev = base.score || 0.0;
    const scoreCurr = target.score || 0.0;
    const scoreDiff = diffs.score_diff !== undefined ? diffs.score_diff : (scoreCurr - scorePrev).toFixed(1);

    html += `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px;">
            <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.08); padding: 12px; border-radius: 10px; text-align: center;">
                <span style="font-size: 11px; color: var(--text-secondary); display: block; font-weight: 600; text-transform: uppercase;">Nível</span>
                <strong style="font-size: 16px; color: #fff;">${levelPrev ? `Nv. ${levelPrev} ➔ ` : ''}Nv. ${levelCurr}</strong>
                ${levelDiff > 0 ? `<span class="diff-badge-gain" style="display: inline-block; margin-top: 4px;">+${levelDiff} Níveis</span>` : ''}
            </div>
            <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.08); padding: 12px; border-radius: 10px; text-align: center;">
                <span style="font-size: 11px; color: var(--text-secondary); display: block; font-weight: 600; text-transform: uppercase;">Constelação / Rank</span>
                <strong style="font-size: 16px; color: #f59e0b;">${rankPrev !== rankCurr ? `${rankPrev} ➔ ${rankCurr}` : rankCurr}</strong>
                ${diffs.rank_changed ? `<span class="diff-badge-gain" style="display: inline-block; margin-top: 4px;">Evoluiu!</span>` : ''}
            </div>
            <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.08); padding: 12px; border-radius: 10px; text-align: center;">
                <span style="font-size: 11px; color: var(--text-secondary); display: block; font-weight: 600; text-transform: uppercase;">Build Score (RV)</span>
                <strong style="font-size: 16px; color: #10b981;">${scorePrev ? `${scorePrev}% ➔ ` : ''}${scoreCurr}%</strong>
                ${scoreDiff > 0 ? `<span class="diff-badge-gain" style="display: inline-block; margin-top: 4px;">+${scoreDiff}%</span>` : (scoreDiff < 0 ? `<span class="diff-badge-loss" style="display: inline-block; margin-top: 4px;">${scoreDiff}%</span>` : '')}
            </div>
        </div>
    `;

    // 1. ARMA / CONE DE LUZ / W-ENGINE
    const wBase = base.weapon || (base.weapon_name ? { name: base.weapon_name, level: base.weapon_level, rank: base.weapon_rank, icon: base.weapon_icon } : null);
    const wTarget = target.weapon || (target.weapon_name ? { name: target.weapon_name, level: target.weapon_level, rank: target.weapon_rank, icon: target.weapon_icon } : null);

    html += `<div class="diff-section-title"><i class="fa-solid fa-wand-magic-sparkles"></i> ${isEn ? "Equipped Weapon / Light Cone / W-Engine" : "Arma / Cone de Luz / W-Engine Equipado"}</div>`;
    if (wBase || wTarget) {
        const weaponSwapped = (wBase?.name || '') !== (wTarget?.name || '');
        const weaponLeveled = (wBase?.level || 0) !== (wTarget?.level || 0) || (wBase?.rank || 1) !== (wTarget?.rank || 1);

        html += `
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; background: rgba(0,0,0,0.25); padding: 14px; border-radius: 12px; border: 1px solid ${weaponSwapped ? 'rgba(236,72,153,0.4)' : 'rgba(255,255,255,0.06)'};">
                <div style="border-right: 1px solid rgba(255,255,255,0.08); padding-right: 10px;">
                    <span style="font-size: 11px; color: #ef4444; display: block; margin-bottom: 6px; font-weight: 700;">SNAPSHOT ANTERIOR (BASE)</span>
                    ${wBase && wBase.name ? `
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <img src="${wBase.icon || '/assets/logo.svg'}" style="width: 44px; height: 44px; border-radius: 8px; object-fit: cover; border: 1px solid rgba(255,255,255,0.15);" onerror="this.src='/assets/logo.svg'">
                            <div>
                                <strong style="font-size: 13px; color: var(--text-primary); display: block;">${wBase.name}</strong>
                                <span style="font-size: 11px; color: var(--text-secondary);">Nv. ${wBase.level || 1} ${wBase.rank ? `• Refinamento R${wBase.rank}` : ''}</span>
                            </div>
                        </div>
                    ` : `<span style="font-size: 12px; color: var(--text-muted); font-style: italic;">${isEn ? "No weapon in previous snapshot" : "Nenhuma arma no snapshot anterior"}</span>`}
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 11px; color: #10b981; font-weight: 700;">SNAPSHOT ATUAL (COMPARADO)</span>
                        ${weaponSwapped ? `<span class="diff-arrow-badge">${isEn ? "Weapon Swapped" : "Arma Trocada"}</span>` : (weaponLeveled ? `<span class="diff-badge-gain">${isEn ? "Leveled Up" : "Evoluída"}</span>` : '')}
                    </div>
                    ${wTarget && wTarget.name ? `
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <img src="${wTarget.icon || '/assets/logo.svg'}" style="width: 44px; height: 44px; border-radius: 8px; object-fit: cover; border: 2px solid ${weaponSwapped ? '#ec4899' : '#10b981'}; box-shadow: 0 0 10px ${weaponSwapped ? 'rgba(236,72,153,0.3)' : 'rgba(16,185,129,0.3)'};" onerror="this.src='/assets/logo.svg'">
                            <div>
                                <strong style="font-size: 13px; color: #fff; display: block;">${wTarget.name}</strong>
                                <span style="font-size: 11px; color: #10b981; font-weight: 600;">Nv. ${wTarget.level || 1} ${wTarget.rank ? `• Refinamento R${wTarget.rank}` : ''}</span>
                            </div>
                        </div>
                    ` : `<span style="font-size: 12px; color: var(--text-muted); font-style: italic;">${isEn ? "No weapon recorded" : "Nenhuma arma registrada"}</span>`}
                </div>
            </div>
        `;
    } else {
        html += `<p style="font-size: 12px; color: var(--text-muted); font-style: italic;">${isEn ? "Weapon information unavailable." : "Informações de arma não disponíveis."}</p>`;
    }

    // 2. TALENTOS E HABILIDADES
    const skillsBase = base.skills || [];
    const skillsTarget = target.skills || [];
    if (skillsTarget.length > 0 || skillsBase.length > 0) {
        html += `<div class="diff-section-title"><i class="fa-solid fa-bolt"></i> Evolução de Habilidades e Talentos</div>`;
        html += `<div style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 12px;">`;

        const allSkillNames = listUniqueSkillKeys(skillsBase, skillsTarget);
        html += `<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 10px;">`;
        allSkillNames.forEach(sName => {
            const sb = skillsBase.find(x => (x.name || x.skill_name) === sName);
            const st = skillsTarget.find(x => (x.name || x.skill_name) === sName);
            const lvlB = sb ? (sb.level || sb.lvl || 0) : 0;
            const lvlT = st ? (st.level || st.lvl || 0) : 0;
            const diff = lvlT - lvlB;
            const icon = (st || sb || {}).icon || "";

            html += `
                <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        ${icon ? `<img src="${icon}" style="width: 24px; height: 24px; border-radius: 50%;" onerror="this.style.display='none'">` : ''}
                        <span style="font-size: 12px; color: var(--text-primary); font-weight: 500;">${sName}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="font-size: 12px; color: var(--text-secondary);">${lvlB ? `Nv. ${lvlB} ➔ ` : ''}Nv. ${lvlT}</span>
                        ${diff > 0 ? `<span class="diff-badge-gain">+${diff}</span>` : ''}
                    </div>
                </div>
            `;
        });
        html += `</div></div>`;
    }

    // 3. STATUS GERAIS DO PERSONAGEM (DETALHADO E CATEGORIZADO)
    const statsBase = base.stats || {};
    const statsTarget = target.stats || {};
    const allStatKeys = listUniqueDictKeys(statsBase, statsTarget);

    if (allStatKeys.length > 0) {
        html += `<div class="diff-section-title"><i class="fa-solid fa-chart-line"></i> ${isEn ? "General Character Stats (Final Attributes)" : "Status Gerais do Personagem (Atributos Finais)"}</div>`;
        html += `<div class="diff-stats-category-card">`;
        html += `<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 10px;">`;

        allStatKeys.forEach(key => {
            const valB = statsBase[key] !== undefined ? String(statsBase[key]) : 'N/A';
            const valT = statsTarget[key] !== undefined ? String(statsTarget[key]) : 'N/A';
            
            let diffBadge = '';
            const numB = parseFloat(valB.replace(/[^0-9.-]/g, ''));
            const numT = parseFloat(valT.replace(/[^0-9.-]/g, ''));

            if (!isNaN(numB) && !isNaN(numT) && numB !== numT) {
                const diffVal = (numT - numB).toFixed(1);
                const isPct = valT.includes('%');
                if (parseFloat(diffVal) > 0) {
                    diffBadge = `<span class="diff-badge-gain">+${diffVal}${isPct ? '%' : ''}</span>`;
                } else if (parseFloat(diffVal) < 0) {
                    diffBadge = `<span class="diff-badge-loss">${diffVal}${isPct ? '%' : ''}</span>`;
                }
            } else if (valB === valT && valT !== 'N/A') {
                diffBadge = `<span class="diff-badge-same">Inalterado</span>`;
            }

            // Define ícone para cada status
            let statIcon = 'fa-chart-simple';
            const kLower = key.toLowerCase();
            if (kLower.includes('hp') || kLower.includes('vida')) statIcon = 'fa-heart';
            else if (kLower.includes('atq') || kLower.includes('atk') || kLower.includes('ataque')) statIcon = 'fa-hand-fist';
            else if (kLower.includes('def') || kLower.includes('defesa')) statIcon = 'fa-shield-halved';
            else if (kLower.includes('taxa') || kLower.includes('crit_rate')) statIcon = 'fa-crosshair';
            else if (kLower.includes('dano crit') || kLower.includes('crit_dmg')) statIcon = 'fa-burst';
            else if (kLower.includes('recarga') || kLower.includes('energy')) statIcon = 'fa-bolt';
            else if (kLower.includes('prof') || kLower.includes('mastery')) statIcon = 'fa-wand-magic-sparkles';
            else if (kLower.includes('cura') || kLower.includes('heal')) statIcon = 'fa-notes-medical';

            html += `
                <div class="diff-stat-row-item">
                    <div style="display: flex; align-items: center; gap: 8px; min-width: 0;">
                        <i class="fa-solid ${statIcon}" style="color: #38bdf8; font-size: 13px; width: 16px; text-align: center;"></i>
                        <span style="font-size: 11px; color: var(--text-secondary); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${key}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; flex-shrink: 0;">
                        <span style="font-size: 12px; font-weight: 700; color: #fff;">${valB !== 'N/A' && valB !== valT ? `${valB} ➔ ` : ''}${valT}</span>
                        ${diffBadge}
                    </div>
                </div>
            `;
        });
        html += `</div></div>`;
    }

    // 4. RELÍQUIAS / ARTEFATOS / DISCOS ("FOI DESSE PRA ESSE")
    const relicsBase = base.relics || [];
    const relicsTarget = target.relics || [];

    html += `<div class="diff-section-title"><i class="fa-solid fa-gem"></i> ${isEn ? "Comparison of Equipped Artifacts & Relics" : "Comparativo de Artefatos & Relíquias Equipados"}</div>`;
    
    // Mapeia todas as peças por Slot
    const slotPairs = buildRelicSlotPairs(relicsBase, relicsTarget);

    if (slotPairs.length > 0) {
        html += `<div style="display: flex; flex-direction: column; gap: 14px;">`;

        slotPairs.forEach((pair, pIdx) => {
            const rb = pair.base || {};
            const rt = pair.target || {};
            const slotName = pair.slot || `Slot #${pIdx + 1}`;

            const nameB = rb.name || '';
            const mainB = rb.main || rb.main_stat || '';
            const subListB = parseSubstats(rb.sub);

            const nameT = rt.name || '';
            const mainT = rt.main || rt.main_stat || '';
            const subListT = parseSubstats(rt.sub);

            const isReplaced = nameB && nameT && (nameB !== nameT || mainB !== mainT);
            const isNew = !nameB && nameT;
            const isRemoved = nameB && !nameT;

            let cardStateClass = 'state-kept';
            let badgeHtml = `<span class="diff-badge-same">Mantida</span>`;

            if (isReplaced) {
                cardStateClass = 'state-replaced';
                badgeHtml = `<span class="diff-arrow-badge"><i class="fa-solid fa-rotate"></i> Peça Trocada</span>`;
            } else if (isNew) {
                cardStateClass = 'state-new';
                badgeHtml = `<span class="diff-badge-gain" style="background: rgba(245, 158, 11, 0.2); color: #f59e0b; border-color: rgba(245, 158, 11, 0.4);">★ Nova Peça</span>`;
            } else if (isRemoved) {
                cardStateClass = 'state-replaced';
                badgeHtml = `<span class="diff-badge-loss">Removida</span>`;
            }

            html += `
                <div class="diff-relic-card ${cardStateClass}">
                    <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.06); margin-bottom: 8px;">
                        <span style="font-size: 12px; font-weight: 800; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.5px;">
                            <i class="fa-regular fa-square-minus" style="margin-right: 4px;"></i> ${slotName}
                        </span>
                        ${badgeHtml}
                    </div>

                    ${isReplaced ? `
                        <!-- VISUALIZADOR DE TRANSIÇÃO: FOI DESSE PRA ESSE -->
                        <div class="diff-relic-transition-grid">
                            <!-- ANTERIOR (BASE) -->
                            <div class="diff-relic-box box-anterior">
                                <div class="diff-relic-box-header">
                                    <span><i class="fa-solid fa-clock-rotate-left"></i> Anterior (Base)</span>
                                </div>
                                <div class="diff-relic-item-header">
                                    <img src="${rb.icon || '/assets/logo.svg'}" class="diff-relic-thumb" onerror="this.src='/assets/logo.svg'">
                                    <div>
                                        <div class="diff-relic-name-text" style="color: var(--text-muted); text-decoration: line-through;">${nameB}</div>
                                        <span class="diff-relic-mainstat-pill" style="opacity: 0.8;">${mainB || 'Sem Main'}</span>
                                    </div>
                                </div>
                                ${subListB.length ? `
                                    <div class="diff-relic-substats-list">
                                        ${subListB.map(s => `<span class="diff-substat-pill ${s.isCrit ? 'is-crit' : ''}">${s.text}</span>`).join('')}
                                    </div>
                                ` : ''}
                            </div>

                            <!-- ÍCONE DE TRANSIÇÃO DA TROCA -->
                            <div class="diff-arrow-indicator">
                                <i class="fa-solid fa-right-long" style="font-size: 20px;"></i>
                                <span class="diff-arrow-badge">TROCADO POR</span>
                            </div>

                            <!-- ATUAL (COMPARADO) -->
                            <div class="diff-relic-box box-atual">
                                <div class="diff-relic-box-header">
                                    <span><i class="fa-solid fa-sparkles"></i> Atual (Comparado)</span>
                                </div>
                                <div class="diff-relic-item-header">
                                    <img src="${rt.icon || '/assets/logo.svg'}" class="diff-relic-thumb thumb-active" onerror="this.src='/assets/logo.svg'">
                                    <div>
                                        <div class="diff-relic-name-text">${nameT}</div>
                                        <span class="diff-relic-mainstat-pill">${mainT}</span>
                                    </div>
                                </div>
                                ${subListT.length ? `
                                    <div class="diff-relic-substats-list">
                                        ${subListT.map(s => `<span class="diff-substat-pill ${s.isCrit ? 'is-crit' : ''}">${s.text}</span>`).join('')}
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    ` : (isNew ? `
                        <div class="diff-relic-transition-grid">
                            <div class="diff-relic-box box-anterior" style="justify-content: center; align-items: center; min-height: 80px;">
                                <span style="font-size: 11px; color: var(--text-muted); font-style: italic;">Nenhum artefato neste slot</span>
                            </div>
                            <div class="diff-arrow-indicator">
                                <i class="fa-solid fa-right-long" style="font-size: 18px;"></i>
                            </div>
                            <div class="diff-relic-box box-atual">
                                <div class="diff-relic-item-header">
                                    <img src="${rt.icon || '/assets/logo.svg'}" class="diff-relic-thumb thumb-active" onerror="this.src='/assets/logo.svg'">
                                    <div>
                                        <div class="diff-relic-name-text">${nameT}</div>
                                        <span class="diff-relic-mainstat-pill">${mainT}</span>
                                    </div>
                                </div>
                                ${subListT.length ? `
                                    <div class="diff-relic-substats-list">
                                        ${subListT.map(s => `<span class="diff-substat-pill ${s.isCrit ? 'is-crit' : ''}">${s.text}</span>`).join('')}
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    ` : `
                        <!-- ARTEFATO MANTIDO (EXIBE DETALHADO DO ATUAL) -->
                        <div style="display: flex; gap: 12px; align-items: flex-start; margin-top: 4px;">
                            <img src="${rt.icon || rb.icon || '/assets/logo.svg'}" class="diff-relic-thumb" onerror="this.src='/assets/logo.svg'">
                            <div style="flex: 1; min-width: 0;">
                                <strong style="font-size: 13px; color: #fff; display: block;">${nameT || nameB}</strong>
                                <span class="diff-relic-mainstat-pill" style="margin-top: 4px;">${mainT || mainB}</span>
                                ${subListT.length ? `
                                    <div class="diff-relic-substats-list" style="margin-top: 6px;">
                                        ${subListT.map(s => `<span class="diff-substat-pill ${s.isCrit ? 'is-crit' : ''}">${s.text}</span>`).join('')}
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    `)}
                </div>
            `;
        });
        html += `</div>`;
    } else {
        html += `<p style="font-size: 12px; color: var(--text-muted); font-style: italic;">${isEn ? "Relic details not saved in base/compared snapshot." : "Detalhes de relíquias não salvos no snapshot base/comparado."}</p>`;
    }

    bodyEl.innerHTML = html;
    modal.style.display = "flex";
};

function buildRelicSlotPairs(relicsBase, relicsTarget) {
    const pairs = [];
    const maxLen = Math.max((relicsBase || []).length, (relicsTarget || []).length);
    for (let i = 0; i < maxLen; i++) {
        const rb = (relicsBase || [])[i] || null;
        const rt = (relicsTarget || [])[i] || null;
        const slotName = (rt && rt.slot) || (rb && rb.slot) || `Slot #${i + 1}`;
        pairs.push({ slot: slotName, base: rb, target: rt });
    }
    return pairs;
}

function parseSubstats(subData) {
    if (!subData) return [];
    let items = [];
    if (typeof subData === 'string') {
        items = subData.split(',').map(s => s.trim()).filter(Boolean);
    } else if (Array.isArray(subData)) {
        items = subData.map(s => {
            if (typeof s === 'object' && s !== null) {
                return `${s.name || s.prop || ''}: ${s.val || s.value || ''}`;
            }
            return String(s);
        }).filter(Boolean);
    }
    return items.map(str => {
        const sLower = str.toLowerCase();
        const isCrit = sLower.includes('crit') || sLower.includes('taxa') || sLower.includes('dano');
        return { text: str, isCrit };
    });
}


// =========================================================================
// PARTE 6: ASSISTENTE ESTRATÉGICO & DIAGNÓSTICO DE LACUNAS DA CONTA (GAPS)
// =========================================================================

window.currentGapsGame = "hsr";
window.lastGapsAnalysis = null;

window.switchAuditSubView = function(viewName) {
    const btnTierlist = document.getElementById("btn-subnav-audit-tierlist");
    const btnGaps = document.getElementById("btn-subnav-audit-gaps");
    const viewTierlist = document.getElementById("audit-view-tierlist");
    const viewGaps = document.getElementById("audit-view-gaps");

    if (viewName === "tierlist") {
        if (viewTierlist) viewTierlist.style.display = "block";
        if (viewGaps) viewGaps.style.display = "none";
        if (btnTierlist) {
            btnTierlist.className = "subnav-btn active";
            btnTierlist.style.border = "1px solid rgba(168, 85, 247, 0.4)";
            btnTierlist.style.background = "rgba(168, 85, 247, 0.15)";
            btnTierlist.style.color = "#c084fc";
        }
        if (btnGaps) {
            btnGaps.className = "subnav-btn";
            btnGaps.style.border = "1px solid rgba(255,255,255,0.1)";
            btnGaps.style.background = "rgba(0,0,0,0.2)";
            btnGaps.style.color = "var(--text-muted)";
        }
    } else {
        if (viewTierlist) viewTierlist.style.display = "none";
        if (viewGaps) viewGaps.style.display = "block";
        if (btnTierlist) {
            btnTierlist.className = "subnav-btn";
            btnTierlist.style.border = "1px solid rgba(255,255,255,0.1)";
            btnTierlist.style.background = "rgba(0,0,0,0.2)";
            btnTierlist.style.color = "var(--text-muted)";
        }
        if (btnGaps) {
            btnGaps.className = "subnav-btn active";
            btnGaps.style.border = "1px solid rgba(56, 189, 248, 0.4)";
            btnGaps.style.background = "rgba(56, 189, 248, 0.15)";
            btnGaps.style.color = "#38bdf8";
        }
        window.loadAccountGapsAnalysis(window.currentGapsGame || "hsr");
    }
};

window.loadAccountGapsAnalysis = async function(gameId) {
    window.currentGapsGame = gameId;
    const bodyEl = document.getElementById("tab-gaps-content-body");
    if (!bodyEl) return;

    // Atualiza pills de jogo ativas
    document.querySelectorAll(".tab-gaps-game-btn").forEach(btn => {
        if (btn.getAttribute("data-game") === gameId) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    bodyEl.innerHTML = `
        <div style="text-align: center; color: var(--text-muted); padding: 40px;">
            <i class="fa-solid fa-spinner fa-spin fa-2x" style="color: #38bdf8;"></i>
            <p style="margin-top: 12px; font-size: 13px;">Auditando Roster, Sinergias e Cobertura de ${gameId.toUpperCase()}...</p>
        </div>
    `;

    try {
        const res = await fetch(`/api/strategy/account-gaps/${gameId}`);
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `Erro na API (${res.status})`);
        }
        const data = await res.json();
        window.lastGapsAnalysis = data;
        window.renderAccountGapsResult(data);
    } catch (err) {
        console.error("Erro ao carregar análise de lacunas:", err);
        bodyEl.innerHTML = `
            <div style="padding: 24px; text-align: center; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px;">
                <i class="fa-solid fa-triangle-exclamation" style="color: #f87171; font-size: 24px;"></i>
                <h4 style="color: #fca5a5; margin: 8px 0;">Falha na Auditoria Estratégica</h4>
                <p style="color: var(--text-muted); font-size: 12px;">${err.message}</p>
                <button onclick="window.loadAccountGapsAnalysis('${gameId}')" class="primary-btn" style="margin-top: 10px; padding: 6px 14px; font-size: 12px;">Tentar Novamente</button>
            </div>
        `;
    }
};

window.renderAccountGapsResult = function(data) {
    const bodyEl = document.getElementById("tab-gaps-content-body");
    if (!bodyEl || !data) return;

    const score = data.overall_score || 0;
    const grade = data.score_grade || "B";
    const label = data.score_label || "";
    const color = data.score_color || "#38bdf8";

    // 1. Header KPI
    let html = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr)); gap: 14px; margin-bottom: 20px;">
            <!-- CARD DE PONTUAÇÃO DE SAÚDE DA CONTA -->
            <div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.6)); border: 1px solid ${color}44; border-radius: 16px; padding: 20px; display: flex; align-items: center; gap: 18px; position: relative; overflow: hidden; box-shadow: 0 4px 20px ${color}15;">
                <div style="position: absolute; right: -15px; bottom: -15px; font-size: 90px; color: ${color}0d; pointer-events: none; font-weight: 900;">${grade}</div>
                <div style="width: 75px; height: 75px; border-radius: 50%; border: 4px solid ${color}; display: flex; flex-direction: column; align-items: center; justify-content: center; background: ${color}15; flex-shrink: 0;">
                    <span style="font-size: 22px; font-weight: 800; color: ${color}; line-height: 1;">${score}</span>
                    <span style="font-size: 9px; color: var(--text-muted); text-transform: uppercase; font-weight: 700; margin-top: 2px;">/100</span>
                </div>
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                        <span style="background: ${color}22; color: ${color}; border: 1px solid ${color}66; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 800;">RANK ${grade}</span>
                        <h3 style="margin: 0; font-size: 16px; color: var(--text-primary);">Saúde da Conta</h3>
                    </div>
                    <p style="margin: 0; font-size: 12px; color: var(--text-secondary); line-height: 1.4;">${label}</p>
                </div>
            </div>

            <!-- CARD PRONTIDÃO DE ENDGAME -->
            <div style="background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(30, 41, 59, 0.6)); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 20px; display: flex; flex-direction: column; justify-content: space-between;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <span style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 4px;">Prontidão de Endgame</span>
                        <h4 style="margin: 0; font-size: 17px; color: #38bdf8; display: flex; align-items: center; gap: 8px;">
                            <i class="fa-solid fa-swords"></i> ${data.endgame_readiness?.status || '1/2 Equipes'}
                        </h4>
                    </div>
                    <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700;">
                        ${data.built_characters} / ${data.total_characters} Prontos
                    </span>
                </div>
                <p style="margin: 8px 0 0 0; font-size: 12px; color: var(--text-secondary); line-height: 1.4;">${data.endgame_readiness?.summary || ''}</p>
            </div>
        </div>
    `;

    // 2. Grid de Arquétipos
    html += `
        <div style="margin-bottom: 24px;">
            <h4 style="margin: 0 0 12px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; color: #cbd5e1; display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-shield-cat" style="color: #a855f7;"></i> Cobertura de Arquétipos Essenciais
            </h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: 12px;">
    `;

    (data.archetypes_summary || []).forEach(arch => {
        const charListHtml = (arch.owned_characters && arch.owned_characters.length > 0)
            ? arch.owned_characters.map(c => `<span style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); padding: 2px 7px; border-radius: 6px; font-size: 11px; color: #e2e8f0;">${c}</span>`).join(" ")
            : `<span style="color: #fca5a5; font-size: 11px; font-style: italic;">${isEn ? "None identified" : "Nenhum identificado"}</span>`;

        html += `
            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.07); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 13px; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 6px;">
                            <i class="fa-solid ${arch.icon || 'fa-star'}" style="color: ${arch.status_color || '#38bdf8'};"></i> ${arch.title}
                        </span>
                        <span style="background: ${arch.status_color}22; color: ${arch.status_color}; border: 1px solid ${arch.status_color}55; padding: 2px 7px; border-radius: 6px; font-size: 10px; font-weight: 700;">
                            ${arch.status} (${arch.owned_count}/${arch.target_count})
                        </span>
                    </div>
                    <p style="margin: 0 0 10px 0; font-size: 11px; color: var(--text-muted); line-height: 1.3;">${arch.description}</p>
                </div>
                <div>
                    <div style="font-size: 10px; color: var(--text-muted); text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">Possuídos na Função:</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 4px;">${charListHtml}</div>
                </div>
            </div>
        `;
    });
    html += `</div></div>`;

    // 3. Matriz de Cobertura Elemental
    if (data.elemental_coverage && data.elemental_coverage.length > 0) {
        html += `
            <div style="margin-bottom: 24px;">
                <h4 style="margin: 0 0 12px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; color: #cbd5e1; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-atom" style="color: #38bdf8;"></i> Matriz de Cobertura Elemental
                </h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 140px), 1fr)); gap: 8px;">
        `;
        data.elemental_coverage.forEach(el => {
            const stCol = el.status === "Forte" ? "#10b981" : (el.status === "Moderado" ? "#f59e0b" : "#ef4444");
            html += `
                <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 10px 12px; text-align: center;">
                    <div style="display: flex; align-items: center; justify-content: center; gap: 6px; margin-bottom: 4px;">
                        <i class="fa-solid ${el.icon}" style="color: ${el.color}; font-size: 13px;"></i>
                        <strong style="font-size: 12px; color: var(--text-primary);">${el.element}</strong>
                    </div>
                    <div style="font-size: 11px; color: ${stCol}; font-weight: 700;">
                        ${el.built_count} Prontos (${el.count} total)
                    </div>
                </div>
            `;
        });
        html += `</div></div>`;
    }

    // 4. Lacunas Críticas & Gargalos
    html += `
        <div style="margin-bottom: 24px;">
            <h4 style="margin: 0 0 12px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; color: #cbd5e1; display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-triangle-exclamation" style="color: #ef4444;"></i> Gargalos & Lacunas Estratégicas Detectadas
            </h4>
    `;

    if (!data.critical_gaps || data.critical_gaps.length === 0) {
        html += `
            <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 18px; text-align: center; color: #34d399;">
                <i class="fa-solid fa-circle-check fa-2x" style="margin-bottom: 8px;"></i>
                <h4 style="margin: 0 0 4px 0;">Nenhuma Lacuna Crítica Detectada!</h4>
                <p style="margin: 0; font-size: 12px; color: var(--text-secondary);">Sua conta possui excelente equilíbrio em todas as funções essenciais para o Endgame.</p>
            </div>
        `;
    } else {
        html += `<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 320px), 1fr)); gap: 12px;">`;
        data.critical_gaps.forEach(gap => {
            const sevColor = gap.severity_color || "#ef4444";
            const recCharsHtml = (gap.recommended_characters || []).map(rc => `<strong style="color: #38bdf8;">${rc}</strong>`).join(", ");
            html += `
                <div style="background: rgba(15, 23, 42, 0.75); border: 1px solid ${sevColor}44; border-left: 4px solid ${sevColor}; border-radius: 12px; padding: 14px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 11px; font-weight: 800; color: ${sevColor}; text-transform: uppercase;">[${gap.severity}] ${gap.badge || ''}</span>
                    </div>
                    <h4 style="margin: 0 0 6px 0; font-size: 14px; color: var(--text-primary);">${gap.title}</h4>
                    <p style="margin: 0 0 8px 0; font-size: 12px; color: var(--text-secondary); line-height: 1.4;">${gap.description}</p>
                    <div style="background: rgba(0,0,0,0.3); padding: 8px 10px; border-radius: 8px; font-size: 11px; line-height: 1.4; border: 1px solid rgba(255,255,255,0.04);">
                        <div style="color: #fca5a5; margin-bottom: 4px;"><strong>Impacto no Endgame:</strong> ${gap.endgame_impact}</div>
                        <div style="color: #cbd5e1;"><strong>Alvos Sugeridos:</strong> ${recCharsHtml}</div>
                    </div>
                </div>
            `;
        });
        html += `</div>`;
    }
    html += `</div>`;

    // 5. Recomendações Ranqueadas de Puxadas (Gacha Strategy)
    if (data.pull_recommendations && data.pull_recommendations.length > 0) {
        html += `
            <div style="margin-bottom: 24px;">
                <h4 style="margin: 0 0 12px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; color: #cbd5e1; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-wand-magic-sparkles" style="color: #f59e0b;"></i> Prioridades Estratégicas no Gacha & Banners Futuros
                </h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); gap: 12px;">
        `;
        data.pull_recommendations.forEach(rec => {
            const charTags = (rec.characters || []).map(c => `<span style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); color: #fbbf24; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 6px;">${c}</span>`).join(" ");
            html += `
                <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.9)); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 14px; position: relative;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="background: linear-gradient(135deg, #f59e0b, #d97706); color: #020617; font-weight: 800; font-size: 10px; padding: 2px 8px; border-radius: 10px;">
                            #${rec.priority_rank} ${rec.badge || (isEn ? "Priority" : "Prioridade")}
                        </span>
                        <span style="font-size: 11px; color: #34d399; font-weight: 700;">${rec.impact_score || ''}</span>
                    </div>
                    <h4 style="margin: 0 0 6px 0; font-size: 14px; color: #f8fafc;">${rec.archetype}</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px;">${charTags}</div>
                    <p style="margin: 0; font-size: 11px; color: var(--text-secondary); line-height: 1.4;">${rec.reason}</p>
                </div>
            `;
        });
        html += `</div></div>`;
    }

    // 6. Box de Parecer da IA & Ação Rápida
    html += `
        <div id="ai-strategic-verdict-box" style="display: none; background: linear-gradient(135deg, rgba(2, 132, 199, 0.12), rgba(15, 23, 42, 0.9)); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 16px; padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 36px; height: 36px; border-radius: 10px; background: rgba(56, 189, 248, 0.2); display: flex; align-items: center; justify-content: center; color: #38bdf8;">
                        <i class="fa-solid fa-brain" style="font-size: 18px;"></i>
                    </div>
                    <div>
                        <h4 style="margin: 0; font-size: 15px; color: var(--text-primary);">Parecer Estratégico da Conta</h4>
                        <span style="font-size: 11px; color: var(--text-muted);">Recomendações customizadas em tempo real alimentadas pelo seu Roster</span>
                    </div>
                </div>
                <button id="btn-request-ai-verdict" onclick="window.consultAiAccountGaps()" class="primary-btn" style="padding: 8px 16px; font-size: 12px; background: linear-gradient(135deg, #0284c7, #38bdf8); border: none; cursor: pointer; border-radius: 8px; font-weight: 700; display: inline-flex; align-items: center; gap: 6px;">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> Gerar Parecer Completo da IA
                </button>
            </div>

            <div id="ai-verdict-content-area" style="font-size: 13px; color: #cbd5e1; line-height: 1.6;">
                <p style="margin: 0; color: var(--text-muted); font-style: italic;">
                    Clique no botão acima para que a inteligência artificial analise suas lacunas e formule o plano ideal de composições de times e banners prioritários.
                </p>
            </div>
        </div>
    `;

    bodyEl.innerHTML = html;
};

window.consultAiAccountGaps = async function(customQuestion) {
    const gameId = window.currentGapsGame || "hsr";
    const contentArea = document.getElementById("ai-verdict-content-area");
    const reqBtn = document.getElementById("btn-request-ai-verdict");
    const topBtn = document.getElementById("btn-ask-ai-gaps-action");

    if (contentArea) {
        contentArea.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px; padding: 16px 0; color: #38bdf8;">
                <i class="fa-solid fa-spinner fa-spin fa-lg"></i>
                <span>Avaliando combinações de times, Roster e metagame...</span>
            </div>
        `;
    }

    if (reqBtn) reqBtn.disabled = true;
    if (topBtn) topBtn.disabled = true;

    try {
        const res = await fetch("/api/strategy/ask-ai-gaps", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                game_id: gameId,
                custom_question: customQuestion || null
            })
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `Erro (${res.status})`);
        }

        const data = await res.json();
        if (contentArea) {
            const parsedMd = typeof marked !== "undefined" ? marked.parse(data.ai_response || "") : data.ai_response;
            contentArea.innerHTML = `
                <div class="ai-rendered-response" style="line-height: 1.6; color: #e2e8f0;">
                    ${parsedMd}
                </div>
            `;
        }
    } catch (err) {
        console.error("Erro ao consultar IA sobre lacunas:", err);
        if (contentArea) {
            contentArea.innerHTML = `
                <div style="color: #fca5a5; padding: 10px 0;">
                    <i class="fa-solid fa-triangle-exclamation"></i> Não foi possível obter o parecer da IA: ${err.message}
                </div>
            `;
        }
    } finally {
        if (reqBtn) reqBtn.disabled = false;
        if (topBtn) topBtn.disabled = false;
    }
};

// Vinculação de eventos para as pills de jogo de lacunas
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".tab-gaps-game-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const g = btn.getAttribute("data-game");
            if (g) window.loadAccountGapsAnalysis(g);
        });
    });

    // Carrega o Morning Briefing automaticamente ao abrir a aplicação
    setTimeout(() => {
        if (typeof window.loadMorningBriefing === "function") {
            window.loadMorningBriefing();
        }
    }, 800);
});

// =========================================================================
// PARTE 7: MORNING BRIEFING & CONSELHEIRO DE SÍNTESE / RESINA AUTOMODELADORA
// =========================================================================

window.loadMorningBriefing = async function() {
    const gridEl = document.getElementById("briefing-content-grid");
    const dateLbl = document.getElementById("briefing-date-lbl");
    const weekdayTag = document.getElementById("briefing-weekday-tag");
    if (!gridEl) return;

    try {
        const briefingLang = window.isEn ? 'en' : 'pt';
        const res = await fetch(`/api/briefing/today?lang=${briefingLang}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        const consolidatedText = isEn ? "Consolidated Tasks & Goals" : "Tarefas e Metas Consolidadas";
        const highPrioText = window.t ? window.t("briefing_high_prio", "Alta Prioridade") : "Alta Prioridade";
        const craftTitle = window.t ? window.t("briefing_craft_title", "Síntese Recomendada") : "Síntese Recomendada";
        const gachaTitle = window.t ? window.t("briefing_gacha_title", "Metas de Gacha") : "Metas de Gacha";
        const openGalleryText = window.t ? window.t("briefing_open_gallery_btn", "Abrir Galeria & Resina ➔") : "Abrir Galeria & Resina ➔";
        const viewSimText = window.t ? window.t("briefing_view_sim_btn", "Ver Simulador & Forecast ➔") : "Ver Simulador & Forecast ➔";
        const viewCraftText = window.t ? window.t("briefing_view_craft_btn", "Ver Conselheiro de Síntese ➔") : "Ver Conselheiro de Síntese ➔";
        const gainText = window.t ? window.t("briefing_craft_gain", "Ganho:") : "Ganho:";
        const craftVerb = isEn ? "Craft" : "Fabricar";
        const forWord = isEn ? "for" : "para";

        const BRIEFING_WEEKDAY_DICT = {
            "Segunda-feira": "Monday",
            "Terça-feira": "Tuesday",
            "Quarta-feira": "Wednesday",
            "Quinta-feira": "Thursday",
            "Sexta-feira": "Friday",
            "Sábado": "Saturday",
            "Domingo": "Sunday"
        };
        const BRIEFING_DOMAIN_DICT = {
            "Talentos": "Talents",
            "Livros de Talento": "Talent Books",
            "Rastros": "Traces",
            "Habilidades": "Skills",
            "Chefe de Ascensão": "Ascension Boss",
            "Domínio de Artefatos": "Artifact Domain",
            "Caverna da Corrosão": "Cavern of Corrosion",
            "Livre": "Free"
        };

        const displayWkBriefing = (window.isEn && BRIEFING_WEEKDAY_DICT[data.weekday]) ? BRIEFING_WEEKDAY_DICT[data.weekday] : data.weekday;

        if (dateLbl) dateLbl.innerText = `${displayWkBriefing}, ${data.date} • ${consolidatedText}`;
        if (weekdayTag) weekdayTag.innerText = displayWkBriefing;

        let html = "";

        // 1. Cards de Tarefas dos 3 Jogos
        (data.games || []).forEach(g => {
            let curDomainType = (window.isEn && BRIEFING_DOMAIN_DICT[g.domain_type]) ? BRIEFING_DOMAIN_DICT[g.domain_type] : g.domain_type;
            let curTopTask = g.top_task || "";
            if (window.isEn) {
                if (curTopTask.startsWith("Derrote")) {
                    curTopTask = curTopTask
                        .replace("Derrote", "Defeat")
                        .replace("Chefe de Ascensão", "Ascension Boss")
                        .replace("para avançar", "to advance")
                        .replace("do Nv.", "from Lv.")
                        .replace("rumo ao Nv.", "towards Lv.");
                } else if (curTopTask.startsWith("Faça")) {
                    curTopTask = curTopTask
                        .replace("Faça", "Run")
                        .replace("Domínio de Livros de Talento", "Talent Book Domain")
                        .replace("Domínio de Artefatos Recomendado", "Recommended Artifact Domain")
                        .replace("para obter", "to obtain")
                        .replace("e avançar os talentos prioritários de", "and advance priority talents for")
                        .replace("para farmar o conjunto ideal para", "to farm recommended set for")
                        .replace("Nota", "Grade");
                }
            }

            html += `
                <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 13px; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 6px;">
                            <span>${g.icon}</span> ${g.game_name}
                        </span>
                        <span style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; font-size: 10px; padding: 2px 7px; border-radius: 10px; font-weight: 700;">
                            ${g.characters_count} chars
                        </span>
                    </div>
                    <div style="font-size: 12px; color: #cbd5e1; line-height: 1.4; margin-bottom: 10px;">
                        <strong style="color: #fbbf24; font-size: 11px; text-transform: uppercase; display: block; margin-bottom: 2px;">${curDomainType}:</strong>
                        ${curTopTask}
                    </div>
                    <button onclick="document.querySelector('[data-tab=${g.game_id}]')?.click()" class="secondary-btn" style="padding: 5px 10px; font-size: 11px; width: 100%; border-radius: 6px; cursor: pointer;">
                        ${openGalleryText}
                    </button>
                </div>
            `;
        });

        // 2. Card de Metas de Gacha Forecast
        if (data.gacha_goals && data.gacha_goals.length > 0) {
            let goalsHtml = data.gacha_goals.map(gl => `
                <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.25); padding: 6px 8px; border-radius: 6px; margin-bottom: 4px; font-size: 11px;">
                    <strong style="color: #f8fafc;">${gl.character_name} (${gl.target_rank_str})</strong>
                    <span style="color: ${gl.success_rate >= 75 ? '#34d399' : '#fbbf24'}; font-weight: 800;">${gl.success_rate}% (${gl.target_days}d)</span>
                </div>
            `).join("");

            html += `
                <div style="background: linear-gradient(135deg, rgba(168, 85, 247, 0.12), rgba(15, 23, 42, 0.7)); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 13px; font-weight: 700; color: #c084fc; display: flex; align-items: center; gap: 6px;">
                                <i class="fa-solid fa-wand-magic-sparkles"></i> ${gachaTitle}
                            </span>
                            <span style="font-size: 10px; color: var(--text-muted);">Monte Carlo</span>
                        </div>
                        <div>${goalsHtml}</div>
                    </div>
                    <button onclick="document.querySelector('[data-tab=gacha]')?.click()" class="secondary-btn" style="padding: 5px 10px; font-size: 11px; width: 100%; border-radius: 6px; cursor: pointer; margin-top: 8px;">
                        ${viewSimText}
                    </button>
                </div>
            `;
        }

        // 3. Card de Dica de Síntese
        if (data.top_craft) {
            const tc = data.top_craft;
            let displaySlotName = tc.slot_name || "";
            let displayMainStat = tc.recommended_main_stat || "";
            let displayGain = tc.expected_gain || "";
            if (window.isEn) {
                displaySlotName = displaySlotName
                    .replace("Corda de Recuperação de Energia", "Energy Regen Rope")
                    .replace("Corda de Ligação", "Link Rope")
                    .replace("Esfera Plana", "Planar Sphere")
                    .replace("Pés de SPD", "SPD Boots")
                    .replace("Botas de SPD", "SPD Boots")
                    .replace("Botas", "Boots")
                    .replace("Pés", "Boots")
                    .replace("Corpo", "Body")
                    .replace("Cabeça", "Head")
                    .replace("Mãos", "Hands")
                    .replace("Tiara", "Circlet")
                    .replace("Cálice", "Goblet")
                    .replace("Ampulheta", "Sands")
                    .replace("Pluma", "Plume")
                    .replace("Flor", "Flower")
                    .replace(" ou ", " or ");

                displayMainStat = displayMainStat
                    .replace("Recuperação de Energia", "Energy Regeneration")
                    .replace("Taxa Crítica", "CRIT Rate")
                    .replace("Dano Crítico", "CRIT DMG")
                    .replace("Bônus Elemental", "Elemental DMG Bonus")
                    .replace("Bônus de Cura", "Healing Bonus")
                    .replace("Acerto de Efeito", "Effect Hit Rate");

                displayGain = displayGain
                    .replace("Substitui peça sem status úteis", "Replaces piece with no useful stats")
                    .replace("Substitui peça com atributos fracos", "Replaces piece with weak attributes")
                    .replace("Peça BiS", "BiS Piece");
            }

            html += `
                <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.12), rgba(15, 23, 42, 0.7)); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 13px; font-weight: 700; color: #fbbf24; display: flex; align-items: center; gap: 6px;">
                                <i class="fa-solid fa-cube"></i> ${craftTitle}
                            </span>
                            <span style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; font-size: 10px; padding: 2px 7px; border-radius: 10px; font-weight: 700;">${highPrioText}</span>
                        </div>
                        <div style="font-size: 12px; color: #e2e8f0; line-height: 1.4;">
                            ${craftVerb} <strong>${displaySlotName}</strong> (${displayMainStat}) ${forWord} <strong style="color: #38bdf8;">${tc.character_name}</strong>.
                            <div style="color: #34d399; font-size: 11px; margin-top: 4px;"><strong>${gainText}</strong> ${displayGain}</div>
                        </div>
                    </div>
                    <button onclick="document.querySelector('[data-tab=trash]')?.click(); window.switchTrashSubView('craft');" class="secondary-btn" style="padding: 5px 10px; font-size: 11px; width: 100%; border-radius: 6px; cursor: pointer; margin-top: 8px;">
                        ${viewCraftText}
                    </button>
                </div>
            `;
        }

        gridEl.innerHTML = html;

    } catch (err) {
        console.error("Erro ao carregar Morning Briefing:", err);
        const errText = window.t ? window.t("briefing_error_load", "Não foi possível carregar o resumo matinal automaticamente.") : "Não foi possível carregar o resumo matinal automaticamente.";
        const reloadText = window.t ? window.t("briefing_btn_reload", "Recarregar") : "Recarregar";
        gridEl.innerHTML = `
            <div style="text-align: center; color: var(--text-muted); padding: 20px; grid-column: 1 / -1;">
                <p style="margin: 0; font-size: 12px;">${errText}</p>
                <button onclick="window.loadMorningBriefing()" class="secondary-btn" style="margin-top: 6px; padding: 4px 10px; font-size: 11px;">${reloadText}</button>
            </div>
        `;
    }
};

window.addEventListener("app:languageChanged", () => {
    if (typeof window.loadMorningBriefing === "function") {
        window.loadMorningBriefing();
    }
});

window.sendMorningBriefingNow = async function() {
    const btn = document.getElementById("btn-send-briefing-webhook");
    if (btn) {
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Enviando...`;
        btn.disabled = true;
    }

    try {
        const res = await fetch("/api/briefing/send-now", { method: "POST" });
        const data = await res.json();
        if (typeof showToast === "function") {
    showToast(isEn ? "☀️ Morning Briefing successfully sent to your configured Webhooks!" : "☀️ Morning Briefing enviado com sucesso para seus Webhooks configurados!");
        } else {
    alert(isEn ? "Morning Briefing sent successfully!" : "Morning Briefing enviado com sucesso!");
        }
    } catch (err) {
        console.error("Erro ao enviar Morning Briefing:", err);
        if (typeof showToast === "function") showToast("Erro ao enviar webhook: " + err.message);
    } finally {
        if (btn) {
            btn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Enviar p/ Discord & Telegram`;
            btn.disabled = false;
        }
    }
};

window.currentTrashSubView = "finder";
window.currentTrashGame = "hsr";

window.switchTrashSubView = function(viewName) {
    window.currentTrashSubView = viewName;
    const btnFinder = document.getElementById("btn-subnav-trash-finder");
    const btnCraft = document.getElementById("btn-subnav-trash-craft");
    const viewFinder = document.getElementById("trash-view-finder");
    const viewCraft = document.getElementById("trash-view-craft");

    if (viewName === "finder") {
        if (viewFinder) viewFinder.style.display = "block";
        if (viewCraft) viewCraft.style.display = "none";
        if (btnFinder) {
            btnFinder.className = "subnav-btn active";
            btnFinder.style.border = "1px solid rgba(239, 68, 68, 0.4)";
            btnFinder.style.background = "rgba(239, 68, 68, 0.15)";
            btnFinder.style.color = "#f87171";
        }
        if (btnCraft) {
            btnCraft.className = "subnav-btn";
            btnCraft.style.border = "1px solid rgba(255,255,255,0.1)";
            btnCraft.style.background = "rgba(0,0,0,0.2)";
            btnCraft.style.color = "var(--text-muted)";
        }
    } else {
        if (viewFinder) viewFinder.style.display = "none";
        if (viewCraft) viewCraft.style.display = "block";
        if (btnFinder) {
            btnFinder.className = "subnav-btn";
            btnFinder.style.border = "1px solid rgba(255,255,255,0.1)";
            btnFinder.style.background = "rgba(0,0,0,0.2)";
            btnFinder.style.color = "var(--text-muted)";
        }
        if (btnCraft) {
            btnCraft.className = "subnav-btn active";
            btnCraft.style.border = "1px solid rgba(245, 158, 11, 0.4)";
            btnCraft.style.background = "rgba(245, 158, 11, 0.15)";
            btnCraft.style.color = "#fbbf24";
        }
        window.loadCraftRecommendations(window.currentTrashGame || "hsr");
    }
};

window.loadCraftRecommendations = async function(gameId) {
    window.currentTrashGame = gameId;
    const bodyEl = document.getElementById("tab-craft-recommendations-body");
    if (!bodyEl) return;

    bodyEl.innerHTML = `
        <div style="text-align: center; color: var(--text-muted); padding: 40px;">
            <i class="fa-solid fa-spinner fa-spin fa-2x" style="color: #f59e0b;"></i>
            <p style="margin-top: 10px; font-size: 13px;">Calculando os melhores alvos para uso de Resina Automodeladora / Elixir...</p>
        </div>
    `;

    try {
        const res = await fetch(`/api/relics/craft-recommendations/${gameId}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        let html = `
            <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(15, 23, 42, 0.9)); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 14px; padding: 18px; margin-bottom: 20px;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <div style="width: 36px; height: 36px; border-radius: 10px; background: rgba(245, 158, 11, 0.2); display: flex; align-items: center; justify-content: center; color: #fbbf24; font-size: 18px;">
                        <i class="fa-solid ${data.crafting_item_icon || 'fa-cube'}"></i>
                    </div>
                    <div>
                        <h3 style="margin: 0; font-size: 16px; color: var(--text-primary);">${data.crafting_item_name}</h3>
                        <span style="font-size: 11px; color: var(--text-muted);">${isEn ? "Recommendations based on worst pieces of meta characters in your Roster" : "Recomendações baseadas nas piores peças dos personagens meta do seu Roster"}</span>
                    </div>
                </div>
                <div style="font-size: 12px; color: #cbd5e1; line-height: 1.5; background: rgba(0,0,0,0.25); padding: 10px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);">
                    ${typeof marked !== "undefined" ? marked.parse(data.summary_tip || '') : data.summary_tip}
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 320px), 1fr)); gap: 14px;">
        `;

        (data.recommendations || []).forEach(rec => {
            const substatsHtml = (rec.recommended_substats || []).map(s => `<span style="background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px; font-size: 10px; color: #cbd5e1;">${s}</span>`).join(" ");

            html += `
                <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255,255,255,0.08); border-radius: 14px; padding: 16px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                ${rec.character_icon ? `<img src="${rec.character_icon}" style="width: 32px; height: 32px; border-radius: 50%; border: 1px solid #fbbf24;">` : ''}
                                <strong style="font-size: 15px; color: var(--text-primary);">${rec.character_name}</strong>
                            </div>
                            <span style="background: linear-gradient(135deg, #f59e0b, #d97706); color: #020617; font-size: 10px; font-weight: 800; padding: 2px 8px; border-radius: 10px;">
                                #${rec.priority_rank} ${rec.urgency}
                            </span>
                        </div>

                        <div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px; margin-bottom: 10px; border: 1px solid rgba(255,255,255,0.04);">
                            <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 4px;">${isEn ? "Target Set & Slot:" : "Set & Slot Alvo:"}</div>
                            <div style="font-size: 13px; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">
                                <i class="fa-solid ${rec.slot_icon || 'fa-gem'}" style="color: #fbbf24; margin-right: 4px;"></i> ${rec.target_set_name} • ${rec.slot_name}
                            </div>
                            <div style="font-size: 12px; color: #38bdf8; font-weight: 700; margin-bottom: 6px;">
                                🎯 ${isEn ? "Main Stat:" : "Atributo Principal:"} ${rec.recommended_main_stat}
                            </div>
                            <div style="display: flex; flex-wrap: wrap; gap: 4px;">${substatsHtml}</div>
                        </div>
                    </div>

                    <div>
                        <div style="font-size: 11px; color: #fca5a5; margin-bottom: 4px;">
                            <i class="fa-solid fa-circle-info"></i> ${rec.current_piece_status}
                        </div>
                        <div style="font-size: 11px; color: #34d399; font-weight: 700;">
                            ✨ ${rec.expected_gain}
                        </div>
                    </div>
                </div>
            `;
        });

        html += `</div>`;
        bodyEl.innerHTML = html;

    } catch (err) {
        console.error("Erro ao carregar recomendações de craft:", err);
        bodyEl.innerHTML = `
            <div style="padding: 20px; text-align: center; color: var(--text-muted);">
                <p>Não foi possível calcular as recomendações de síntese: ${err.message}</p>
            </div>
        `;
    }
};



// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
if (typeof buildRelicSlotPairs !== 'undefined') window.buildRelicSlotPairs = buildRelicSlotPairs;
if (typeof parseSubstats !== 'undefined') window.parseSubstats = parseSubstats;

window.addEventListener("app:languageChanged", () => {
    // Farm
    const activeFarmGameBtn = document.querySelector(".tab-farm-game-btn.active");
    if (activeFarmGameBtn && typeof window.loadFarmData === "function") {
        window.loadFarmData(activeFarmGameBtn.dataset.game || "genshin", "tab-farm-content-body");
    }

    // Trash & Craft
    const activeTrashGameBtn = document.querySelector(".tab-trash-game-btn.active");
    const trashGame = activeTrashGameBtn?.dataset?.game || window.currentTrashGame || "hsr";
    if (window.currentTrashSubView === "craft" && typeof window.loadCraftRecommendations === "function") {
        window.loadCraftRecommendations(trashGame);
    } else if (typeof window.loadTrashRelics === "function") {
        window.loadTrashRelics(trashGame, "tab-trash-relics-body");
    }

    // Audit
    const auditGame = window.currentAuditGameId || "hsr";
    if (typeof window.loadAuditReport === "function") {
        window.loadAuditReport(auditGame, "tab-audit-report-body");
    }
    const gapsGame = window.currentGapsGame || "hsr";
    if (typeof window.loadAccountGapsAnalysis === "function") {
        window.loadAccountGapsAnalysis(gapsGame);
    }
});
