// ==========================================================================
// Módulo: sync_manager.js
// Cabeça de Droid - Vanilla ES6 Module
// ==========================================================================

// ==========================================================================
// CONTROLES DE SINCRONIZAÇÃO E LOGS EM TEMPO REAL
// ==========================================================================
function setupSyncControls() {
    // Sincronizações individuais de jogos
    const syncGameButtons = document.querySelectorAll(".sync-game-btn");
    syncGameButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const gameId = btn.getAttribute("data-game");
            const run_roster = document.getElementById(`sync-roster-${gameId}`).checked;
            const run_guides = document.getElementById(`sync-guides-${gameId}`).checked;
            const run_meta = document.getElementById(`sync-meta-${gameId}`).checked;
            
            triggerSync(gameId, run_roster, run_guides, run_meta);
        });
    });

    // Sincronização global (todos os 3 jogos)
    const syncAllBtn = document.getElementById("btn-sync-all");
    syncAllBtn.addEventListener("click", () => {
        syncAllBtn.disabled = true;
        syncAllBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sincronização em Lote Iniciada';
        
        triggerSync("zzz", true, true, true);
        triggerSync("genshin", true, true, true);
        triggerSync("hsr", true, true, true);
        
        setTimeout(() => {
            syncAllBtn.disabled = false;
            syncAllBtn.innerHTML = '<i class="fa-solid fa-rotate"></i> Sincronização Global';
            if (typeof syncAllBtn.done === "function") syncAllBtn.done();
        }, 8000);
    });
}

async function triggerSync(gameId, run_roster, run_guides, run_meta) {
    const loggerDiv = document.getElementById(`sync-logger-${gameId}`);
    loggerDiv.style.display = "flex";
    const skProg = document.getElementById(`sync-progress-${gameId}`);
    if (skProg && typeof skProg.reset === "function") skProg.reset();
    
    try {
        const res = await fetch(`/api/sync/${gameId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ run_roster, run_guides, run_meta })
        });
        
        if (res.ok) {
            const syncBtn = document.querySelector(`.sync-game-btn[data-game="${gameId}"]`);
            if (syncBtn && typeof syncBtn.done === "function" && syncBtn.getBoundingClientRect().width > 0) syncBtn.done(1.2);
            startPollingStatus(gameId);
        } else {
            const errData = await res.json();
            const msgEl = loggerDiv.querySelector(".logger-message");
            msgEl.innerText = `Erro ao iniciar: ${errData.message || "Erro desconhecido"}`;
        }
    } catch (err) {
        console.error(`Erro ao sincronizar ${gameId}:`, err);
    }
}

function startPollingStatus(gameId) {
    if (activePolling[gameId]) {
        clearInterval(activePolling[gameId]);
    }
    
    const loggerDiv = document.getElementById(`sync-logger-${gameId}`);
    const bar = loggerDiv.querySelector(".logger-progress-bar");
    const skProg = document.getElementById(`sync-progress-${gameId}`);
    const perc = loggerDiv.querySelector(".logger-percentage");
    const msg = loggerDiv.querySelector(".logger-message");
    const term = loggerDiv.querySelector(".logger-terminal");
    
    let consecutiveErrors = 0;
    const MAX_POLL_ERRORS = 10;

    activePolling[gameId] = setInterval(async () => {
        try {
            const res = await fetch(`/api/status/${gameId}`);
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }
            const status = await res.json();
            consecutiveErrors = 0;
            
            const rawProgress = Math.max(0, Math.min(1, Number(status.progress) || 0));
            const progressPct = Math.round(rawProgress * 100);
            if (bar) bar.style.width = `${progressPct}%`;
            if (skProg && typeof skProg.set === "function") skProg.set(rawProgress);
            perc.innerText = `${progressPct}%`;
            msg.innerText = status.message;
            
            // Une e exibe a lista de logs no console retrátil
            term.innerText = (status.logs || []).join("\n");
            term.scrollTop = term.scrollHeight; // Auto-scroll
            
            if (!status.running) {
                clearInterval(activePolling[gameId]);
                activePolling[gameId] = null;
                if (skProg && typeof skProg.set === "function") skProg.set(1.0);
                const syncBtn = document.querySelector(`.sync-game-btn[data-game="${gameId}"]`);
                if (syncBtn && typeof syncBtn.done === "function" && syncBtn.getBoundingClientRect().width > 0) syncBtn.done();
                // Recarrega o roster visual e endgame do jogo que acabou de sincronizar
                setTimeout(() => {
                    loadRoster(gameId);
                    loadEndgame(gameId);
                    loadOverview();
                }, 1000);
            }
        } catch (err) {
            consecutiveErrors += 1;
            console.error(`Erro ao consultar status de ${gameId} (${consecutiveErrors}/${MAX_POLL_ERRORS}):`, err);
            if (consecutiveErrors >= MAX_POLL_ERRORS) {
                clearInterval(activePolling[gameId]);
                activePolling[gameId] = null;
                const errText = window.isEn
                    ? "Connection lost while checking sync status."
                    : "Conexão perdida ao acompanhar o status da sincronização.";
                if (msg) msg.innerText = errText;
                if (typeof showToast === "function") showToast(errText, "error");
            }
        }
    }, 1000);
}


// ==========================================================================
// FUNÇÕES DO MONITOR DE ENERGIA (RESINA / PODER / BATERIA) & DAILY NOTES
// ==========================================================================
let _lastDailyNotesPayload = null;

function _escapeDnHtml(str) {
    return String(str == null ? "" : str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function _parseNotesSeconds(notes) {
    if (!notes) return 0;
    const direct = Number(notes.recovery_seconds ?? notes.extra_info?.recovery_seconds);
    if (!Number.isNaN(direct) && direct >= 0 && (notes.recovery_seconds !== undefined || notes.extra_info?.recovery_seconds !== undefined)) {
        return Math.floor(direct);
    }
    const fullAt = notes.full_at || notes.extra_info?.full_at;
    if (fullAt) {
        const ms = Date.parse(fullAt);
        if (!Number.isNaN(ms)) return Math.max(0, Math.floor((ms - Date.now()) / 1000));
    }
    const raw = String(notes.recovery_time || "").trim();
    if (!raw || raw === "0" || raw === "0:00:00") return 0;
    if (/^\d+$/.test(raw)) return parseInt(raw, 10);
    const tdMatch = raw.match(/^(?:(\d+)\s+days?,\s*)?(\d+):(\d+):(\d+)/i);
    if (tdMatch) {
        return (parseInt(tdMatch[1] || "0", 10) * 86400)
            + (parseInt(tdMatch[2] || "0", 10) * 3600)
            + (parseInt(tdMatch[3] || "0", 10) * 60)
            + parseInt(tdMatch[4] || "0", 10);
    }
    return 0;
}

function _formatCompactDuration(totalSeconds) {
    const sec = Math.max(0, Math.floor(Number(totalSeconds) || 0));
    if (sec <= 0) return "0m";
    const days = Math.floor(sec / 86400);
    const hours = Math.floor((sec % 86400) / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${String(mins).padStart(2, "0")}m`;
    return `${Math.max(1, mins)}m`;
}

function formatEnergyFullAt(fullAtIso, fallbackSeconds, isEn) {
    let targetDate = null;
    if (fullAtIso) {
        const ms = Date.parse(fullAtIso);
        if (!Number.isNaN(ms) && ms > Date.now()) {
            targetDate = new Date(ms);
        }
    }
    if (!targetDate && fallbackSeconds > 0) {
        targetDate = new Date(Date.now() + fallbackSeconds * 1000);
    }
    if (!targetDate) return "";

    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const targetDayStart = new Date(targetDate.getFullYear(), targetDate.getMonth(), targetDate.getDate()).getTime();
    const dayDiff = Math.round((targetDayStart - todayStart) / 86400000);

    const timePart = new Intl.DateTimeFormat(isEn ? "en-US" : "pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
    }).format(targetDate);

    if (dayDiff === 0) {
        return isEn ? `Full today at ${timePart}` : `Lota hoje às ${timePart}`;
    }
    if (dayDiff === 1) {
        return isEn ? `Full tomorrow at ${timePart}` : `Lota amanhã às ${timePart}`;
    }
    const datePart = new Intl.DateTimeFormat(isEn ? "en-US" : "pt-BR", {
        day: "2-digit",
        month: "2-digit",
    }).format(targetDate);
    return isEn ? `Full ${datePart} at ${timePart}` : `Lota ${datePart} às ${timePart}`;
}

function _formatKNumber(num) {
    const n = Number(num) || 0;
    if (n >= 1000) {
        const k = n / 1000;
        return Number.isInteger(k) ? `${k}k` : `${k.toFixed(1)}k`;
    }
    return String(n);
}

function _buildDnPill({ icon, label, value, tone = "neutral", tooltip = "" }) {
    const safeTip = _escapeDnHtml(tooltip || `${label}: ${value}`);
    return `
        <span class="dn-pill dn-${tone}" title="${safeTip}">
            <i class="fa-solid ${icon} dn-pill-icon" aria-hidden="true"></i>
            <span class="dn-pill-label">${_escapeDnHtml(label)}</span>
            <strong class="dn-pill-val">${_escapeDnHtml(value)}</strong>
        </span>
    `;
}

function _buildExpeditionPill(expeditions, maxExp, isEn) {
    const list = Array.isArray(expeditions) ? expeditions : [];
    const total = list.length;
    const cap = Number(maxExp) || (total > 0 ? total : 4);
    if (total === 0) {
        return _buildDnPill({
            icon: "fa-compass",
            label: isEn ? "Exped." : "Exped.",
            value: `0/${cap}`,
            tone: "alert",
            tooltip: isEn
                ? `No active expeditions (0/${cap}). Dispatch characters in-game!`
                : `Nenhuma expedição ativa (0/${cap}). Envie personagens no jogo!`,
        });
    }

    let finishedCount = 0;
    let maxRemSec = 0;
    let nextRemSec = Infinity;
    const tipLines = [];

    list.forEach((exp, idx) => {
        const statusStr = String(exp.status || "").toLowerCase();
        let remSec = Number(exp.remaining_seconds);
        if (Number.isNaN(remSec)) {
            if (exp.finish_at) {
                const ms = Date.parse(exp.finish_at);
                remSec = !Number.isNaN(ms) ? Math.max(0, Math.floor((ms - Date.now()) / 1000)) : 0;
            } else {
                remSec = 0;
            }
        }
        const isDone = statusStr.includes("finish") || remSec <= 0;
        if (isDone) {
            finishedCount += 1;
            tipLines.push(`${exp.name || `#${idx + 1}`}: ${isEn ? "Ready to claim!" : "Pronta para coletar!"}`);
        } else {
            if (remSec > maxRemSec) maxRemSec = remSec;
            if (remSec < nextRemSec) nextRemSec = remSec;
            const endClock = formatEnergyFullAt(exp.finish_at, remSec, isEn);
            tipLines.push(`${exp.name || `#${idx + 1}`}: ${_formatCompactDuration(remSec)}${endClock ? ` (${endClock})` : ""}`);
        }
    });

    if (finishedCount === total) {
        return _buildDnPill({
            icon: "fa-compass",
            label: isEn ? "Exped." : "Exped.",
            value: isEn ? `${total}/${cap} Ready` : `${total}/${cap} Prontas`,
            tone: "alert",
            tooltip: `${isEn ? "All expeditions finished!" : "Todas as expedições concluídas!"}\n${tipLines.join("\n")}`,
        });
    }

    if (finishedCount > 0) {
        return _buildDnPill({
            icon: "fa-compass",
            label: isEn ? "Exped." : "Exped.",
            value: `${finishedCount}/${total} · ${_formatCompactDuration(maxRemSec)}`,
            tone: "alert",
            tooltip: `${isEn ? `${finishedCount} ready to claim` : `${finishedCount} pronta(s) para coletar`}\n${tipLines.join("\n")}`,
        });
    }

    const soonestSec = Number.isFinite(nextRemSec) ? nextRemSec : maxRemSec;
    return _buildDnPill({
        icon: "fa-compass",
        label: isEn ? "Exped." : "Exped.",
        value: `${total}/${cap} · ${_formatCompactDuration(soonestSec)}`,
        tone: "info",
        tooltip: tipLines.join("\n"),
    });
}

function renderDailyNotesPills(gameId, notes) {
    const slot = document.getElementById(`daily-notes-slot-${gameId}`);
    if (!slot) return;
    if (!notes || !notes.extra_info || typeof notes.extra_info !== "object") {
        slot.innerHTML = "";
        return;
    }

    const isEn = Boolean(window.isEn);
    const ex = notes.extra_info;
    const pills = [];

    if (gameId === "genshin") {
        // 1. Comissões Diárias
        const comp = Number(ex.completed_commissions ?? 0);
        const maxComp = Number(ex.max_commissions ?? 4);
        const claimed = Boolean(ex.claimed_commission_reward);
        const commTone = claimed ? "done" : (comp >= maxComp ? "alert" : "neutral");
        const commVal = claimed ? `${comp}/${maxComp} ✓` : (comp >= maxComp ? (isEn ? "Claim!" : "Resgatar!") : `${comp}/${maxComp}`);
        pills.push(_buildDnPill({
            icon: "fa-scroll",
            label: isEn ? "Commissions" : "Comissões",
            value: commVal,
            tone: commTone,
            tooltip: isEn
                ? `Daily Commissions: ${comp}/${maxComp} • Katheryne bonus: ${claimed ? "Claimed" : "Pending"}`
                : `Comissões Diárias: ${comp}/${maxComp} • Bônus Katheryne: ${claimed ? "Resgatado" : "Pendente"}`,
        }));

        // 2. Expedições com timer
        pills.push(_buildExpeditionPill(ex.expeditions, ex.max_expeditions ?? 5, isEn));

        // 3. Chefes Semanais
        if (ex.max_resin_discounts !== undefined || ex.remaining_resin_discounts !== undefined) {
            const maxBoss = Number(ex.max_resin_discounts ?? 3);
            const remBoss = Number(ex.remaining_resin_discounts ?? 0);
            const usedBoss = Math.max(0, maxBoss - remBoss);
            pills.push(_buildDnPill({
                icon: "fa-dragon",
                label: isEn ? "Weekly Boss" : "Chefes Sem.",
                value: remBoss === 0 ? `${usedBoss}/${maxBoss} ✓` : `${usedBoss}/${maxBoss}`,
                tone: remBoss === 0 ? "done" : "neutral",
                tooltip: isEn
                    ? `Weekly Boss Resin Discounts: ${usedBoss}/${maxBoss} used (${remBoss} remaining)`
                    : `Chefes Semanais (desconto de Resina): ${usedBoss}/${maxBoss} feitos (restam ${remBoss})`,
            }));
        }

        // 4. Transformador Paramétrico
        if (ex.transformer_available) {
            const tSec = Number(ex.transformer_seconds ?? 0);
            const tReady = tSec <= 0;
            const tReadyClock = !tReady ? formatEnergyFullAt(ex.transformer_ready_at, tSec, isEn) : "";
            pills.push(_buildDnPill({
                icon: "fa-atom",
                label: isEn ? "Transformer" : "Transformador",
                value: tReady ? (isEn ? "Ready!" : "Pronto!") : _formatCompactDuration(tSec),
                tone: tReady ? "alert" : "done",
                tooltip: tReady
                    ? (isEn ? "Parametric Transformer is ready to use!" : "Transformador Paramétrico pronto para uso!")
                    : (isEn ? `Parametric Transformer cooldown: ${_formatCompactDuration(tSec)} (${tReadyClock})` : `Recarga do Transformador: ${_formatCompactDuration(tSec)} (${tReadyClock})`),
            }));
        }

        // 5. Bule de Relachá
        const curRealm = Number(ex.current_realm_currency ?? 0);
        const maxRealm = Number(ex.max_realm_currency ?? 2400);
        const realmPct = maxRealm > 0 ? curRealm / maxRealm : 0;
        const realmFullClock = ex.realm_currency_recovery_seconds > 0
            ? formatEnergyFullAt(ex.realm_currency_full_at, ex.realm_currency_recovery_seconds, isEn)
            : "";
        pills.push(_buildDnPill({
            icon: "fa-mug-hot",
            label: isEn ? "Teapot" : "Bule",
            value: `${curRealm}/${maxRealm}`,
            tone: realmPct >= 0.9 ? "alert" : "info",
            tooltip: realmPct >= 1
                ? (isEn ? `Serenitea Pot currency is FULL (${curRealm}/${maxRealm})!` : `Moedas do Bule LOTADAS (${curRealm}/${maxRealm})!`)
                : `${isEn ? "Serenitea Pot" : "Bule de Relachá"}: ${curRealm}/${maxRealm}${realmFullClock ? ` • ${realmFullClock}` : ""}`,
        }));

    } else if (gameId === "hsr") {
        // 1. Poder de Reserva
        const resCur = Number(ex.current_reserve_stamina ?? 0);
        const resMax = Number(ex.max_reserve_stamina ?? 2400);
        const resFull = Boolean(ex.is_reserve_stamina_full) || resCur >= resMax;
        pills.push(_buildDnPill({
            icon: "fa-battery-half",
            label: isEn ? "Reserve" : "Reserva",
            value: `${resCur}/${resMax}`,
            tone: resFull ? "alert" : (resCur > 0 ? "info" : "neutral"),
            tooltip: isEn
                ? `Reserved Trailblaze Power: ${resCur}/${resMax}`
                : `Poder de Desbravamento de Reserva: ${resCur}/${resMax}`,
        }));

        // 2. Treino Diário
        const trCur = Number(ex.current_train_score ?? 0);
        const trMax = Number(ex.max_train_score ?? 500);
        const trDone = trCur >= trMax && trMax > 0;
        pills.push(_buildDnPill({
            icon: "fa-list-check",
            label: isEn ? "Daily Train" : "Treino Diário",
            value: trDone ? `${trCur}/${trMax} ✓` : `${trCur}/${trMax}`,
            tone: trDone ? "done" : "neutral",
            tooltip: isEn
                ? `Daily Training: ${trCur}/${trMax}`
                : `Treino Diário: ${trCur}/${trMax}`,
        }));

        // 3. Universo Simulado / Divergente (SU/DU)
        const suCur = Number(ex.current_rogue_score ?? 0);
        const suMax = Number(ex.max_rogue_score ?? 14000);
        const suDone = suCur >= suMax && suMax > 0;
        pills.push(_buildDnPill({
            icon: "fa-meteor",
            label: "SU/DU",
            value: suDone ? `${_formatKNumber(suCur)}/${_formatKNumber(suMax)} ✓` : `${_formatKNumber(suCur)}/${_formatKNumber(suMax)}`,
            tone: suDone ? "done" : "neutral",
            tooltip: isEn
                ? `Simulated / Divergent Universe Weekly Points: ${suCur.toLocaleString("en-US")}/${suMax.toLocaleString("en-US")}`
                : `Pontos Semanais SU / DU: ${suCur.toLocaleString("pt-BR")}/${suMax.toLocaleString("pt-BR")}`,
        }));

        // 4. Eco da Guerra (Chefes Semanais)
        if (ex.max_weekly_discounts !== undefined || ex.remaining_weekly_discounts !== undefined) {
            const maxEco = Number(ex.max_weekly_discounts ?? 3);
            const remEco = Number(ex.remaining_weekly_discounts ?? 0);
            const usedEco = Math.max(0, maxEco - remEco);
            pills.push(_buildDnPill({
                icon: "fa-skull-crossbones",
                label: isEn ? "Echo of War" : "Eco Guerra",
                value: remEco === 0 ? `${usedEco}/${maxEco} ✓` : `${usedEco}/${maxEco}`,
                tone: remEco === 0 ? "done" : "neutral",
                tooltip: isEn
                    ? `Echo of War Weekly Clears: ${usedEco}/${maxEco} (${remEco} left)`
                    : `Eco da Guerra (Chefes Semanais): ${usedEco}/${maxEco} feitos (restam ${remEco})`,
            }));
        }

        // 5. Expedições com timer
        pills.push(_buildExpeditionPill(ex.expeditions, ex.total_expedition_num ?? 4, isEn));

    } else if (gameId === "zzz") {
        // 1. Engajamento Diário
        const engCur = Number(ex.engagement ?? 0);
        const engMax = Number(ex.max_engagement ?? 400);
        const engDone = engCur >= engMax && engMax > 0;
        pills.push(_buildDnPill({
            icon: "fa-bolt",
            label: isEn ? "Engagement" : "Engajamento",
            value: engDone ? `${engCur}/${engMax} ✓` : `${engCur}/${engMax}`,
            tone: engDone ? "done" : "neutral",
            tooltip: isEn
                ? `Daily Engagement: ${engCur}/${engMax}`
                : `Engajamento Diário: ${engCur}/${engMax}`,
        }));

        // 2. Raspadinha
        const scratchDone = Boolean(ex.scratch_card_completed);
        pills.push(_buildDnPill({
            icon: "fa-ticket",
            label: isEn ? "Scratch Card" : "Raspadinha",
            value: scratchDone ? (isEn ? "Done ✓" : "Feita ✓") : (isEn ? "Pending" : "Pendente"),
            tone: scratchDone ? "done" : "alert",
            tooltip: scratchDone
                ? (isEn ? "Daily Scratch Card already claimed today." : "Raspadinha do Quiosque já resgatada hoje.")
                : (isEn ? "Daily Scratch Card still available at Howl's Newsstand!" : "Raspadinha diária disponível no Quiosque do Uivo!"),
        }));

        // 3. Café (Coff Cafe)
        const coffeeState = String(ex.coffee_state || "unknown").toLowerCase();
        let coffeeVal = isEn ? "Check in-game" : "Ver no jogo";
        let coffeeTone = "neutral";
        let coffeeTip = isEn
            ? "Coff Cafe daily bonus (+60 Battery) — check in-game (not exposed by current HoYoLAB API)."
            : "Café diário (+60 Bateria) — conferir no jogo (status não retornado pela API atual da HoYoLAB).";
        if (coffeeState === "claimed" || coffeeState === "overcap") {
            coffeeVal = coffeeState === "overcap" ? "+60 ✓" : (isEn ? "Claimed ✓" : "Tomado ✓");
            coffeeTone = "done";
            coffeeTip = isEn ? "Daily Coff Cafe bonus active/claimed." : "Café diário já tomado / bateria extra ativa.";
        } else if (coffeeState === "available") {
            coffeeVal = isEn ? "Available" : "Disponível";
            coffeeTone = "alert";
            coffeeTip = isEn ? "Daily Coff Cafe (+60 Battery) is available!" : "Café diário (+60 Bateria) disponível!";
        }
        pills.push(_buildDnPill({
            icon: "fa-mug-saucer",
            label: isEn ? "Coffee" : "Café",
            value: coffeeVal,
            tone: coffeeTone,
            tooltip: coffeeTip,
        }));

        // 4. Locadora (Random Play)
        const storeRaw = String(ex.video_store_state || "");
        const storeUp = storeRaw.toUpperCase();
        let storeVal = isEn ? "Unknown" : "N/A";
        let storeTone = "neutral";
        let storeTip = isEn ? `Video Store state: ${storeRaw}` : `Status da Locadora: ${storeRaw}`;
        if (storeUp.includes("DONE") || storeUp.includes("REVENUE_AVAILABLE")) {
            storeVal = isEn ? "Collect!" : "Coletar!";
            storeTone = "alert";
            storeTip = isEn ? "Video Store revenue ready to collect!" : "Receita da Locadora pronta para coletar!";
        } else if (storeUp.includes("DOING") || storeUp.includes("CURRENTLY_OPEN") || (storeUp.includes("OPEN") && !storeUp.includes("WAITING"))) {
            storeVal = isEn ? "Open ✓" : "Aberta ✓";
            storeTone = "done";
            storeTip = isEn ? "Video Store currently open and earning." : "Locadora aberta e gerando receita.";
        } else if (storeUp.includes("SALESTATENO") || storeUp.includes("WAITING_TO_OPEN") || storeUp.includes("CLOSED")) {
            storeVal = isEn ? "Closed" : "Fechada";
            storeTone = "alert";
            storeTip = isEn ? "Video Store is closed — open it in-game!" : "Locadora fechada — abra a loja no jogo!";
        }
        pills.push(_buildDnPill({
            icon: "fa-film",
            label: isEn ? "Video Store" : "Locadora",
            value: storeVal,
            tone: storeTone,
            tooltip: storeTip,
        }));

        // 5. Cavidade Zero Semanal (se disponível)
        if (ex.hollow_zero_bounty_max && Number(ex.hollow_zero_bounty_max) > 0) {
            const hzCur = Number(ex.hollow_zero_bounty_current ?? 0);
            const hzMax = Number(ex.hollow_zero_bounty_max);
            const hzDone = hzCur >= hzMax;
            pills.push(_buildDnPill({
                icon: "fa-radiation",
                label: isEn ? "Hollow Zero" : "Cavidade 0",
                value: hzDone ? `${_formatKNumber(hzCur)}/${_formatKNumber(hzMax)} ✓` : `${_formatKNumber(hzCur)}/${_formatKNumber(hzMax)}`,
                tone: hzDone ? "done" : "neutral",
                tooltip: isEn
                    ? `Hollow Zero Bounty Commissions: ${hzCur}/${hzMax}`
                    : `Recompensas Semanais da Cavidade Zero: ${hzCur}/${hzMax}`,
            }));
        }
    }

    slot.innerHTML = pills.join("");
}

function renderAllEnergyMonitorData(data) {
    if (!data || typeof data !== "object") return;
    const isEn = Boolean(window.isEn);
    const txtFull = window.t ? window.t("energy_fully_charged", "Totalmente carregada") : "Totalmente carregada";
    const txtRecov = window.t ? window.t("energy_recovery", "Recuperação: ") : "Recuperação: ";
    const txtNoData = window.t ? window.t("energy_no_data", "Sem dados sincronizados") : "Sem dados sincronizados";

    const defaultsMax = { genshin: 200, hsr: 300, zzz: 240 };

    ["genshin", "hsr", "zzz"].forEach(gid => {
        const notes = data[gid];
        if (!notes) {
            updateEnergyCircle(gid, 0, defaultsMax[gid], txtNoData, "");
            renderDailyNotesPills(gid, null);
            return;
        }
        const cur = Number(notes.current_energy ?? 0);
        const max = Number(notes.max_energy ?? defaultsMax[gid]) || defaultsMax[gid];
        const recSec = _parseNotesSeconds(notes);
        const fullAtIso = notes.full_at || notes.extra_info?.full_at || null;

        let mainText = txtFull;
        let capClockText = "";
        if (recSec > 0 && cur < max) {
            mainText = `${txtRecov}${_formatCompactDuration(recSec)}`;
            capClockText = formatEnergyFullAt(fullAtIso, recSec, isEn);
        }
        updateEnergyCircle(gid, cur, max, mainText, capClockText);
        renderDailyNotesPills(gid, notes);
    });
}

async function setupEnergyMonitor() {
    const fetchNotes = async () => {
        try {
            const res = await fetch("/api/notes");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            _lastDailyNotesPayload = data;
            renderAllEnergyMonitorData(data);
        } catch (err) {
            console.error("Erro ao carregar notas diárias:", err);
        }
    };
    
    fetchNotes();
    setInterval(fetchNotes, 60000); // Atualiza a cada 1 minuto
    window.addEventListener("app:languageChanged", () => {
        if (_lastDailyNotesPayload) {
            renderAllEnergyMonitorData(_lastDailyNotesPayload);
        } else {
            fetchNotes();
        }
        if (typeof window.refreshCheckinLogs === "function") {
            window.refreshCheckinLogs();
        }
    });
}

function updateEnergyCircle(gameId, current, max, remainText, fullAtText = "") {
    const ring = document.getElementById(`ring-${gameId}`);
    const valEl = document.getElementById(`lbl-${gameId}-val`);
    const timeEl = document.getElementById(`lbl-${gameId}-time`);
    if (!ring || !valEl || !timeEl) return;
    
    valEl.innerText = `${current}/${max}`;
    if (fullAtText) {
        timeEl.innerHTML = `<span class="energy-time-main">${_escapeDnHtml(remainText)}</span><span class="energy-full-at"><i class="fa-regular fa-clock" aria-hidden="true"></i> ${_escapeDnHtml(fullAtText)}</span>`;
    } else {
        timeEl.textContent = remainText;
    }
    
    const pct = Math.min(Math.max(current / max, 0), 1);
    const offset = 213.6 - (pct * 213.6);
    ring.style.strokeDashoffset = offset;
}

// ==========================================================================
// FUNÇÕES DO AUTO-CHECKIN DIÁRIO
// ==========================================================================
function setupCheckinSystem() {
    const checkinBtn = document.getElementById("btn-manual-checkin");
    const container = document.getElementById("checkin-logs-container");
    const list = document.getElementById("checkin-logs-list");
    if (!checkinBtn) return;
    
    const loadLogs = async () => {
        try {
            const res = await fetch("/api/checkin/today");
            const logs = await res.json();
            if (logs && logs.length > 0) {
                container.style.display = "block";
                list.innerHTML = logs.map(l => {
                    const time = l.timestamp ? l.timestamp.substring(11, 19) : "";
                    const gameName = l.game_id.toUpperCase();
                    let statusColor = "var(--color-success)";
                    if (l.status === "ERROR") statusColor = "var(--color-danger)";
                    else if (l.status === "ALREADY_CLAIMED") statusColor = "var(--text-muted)";
                    
                    let msg = l.message || "";
                    if (window.isEn) {
                        if (l.status === "ALREADY_CLAIMED" || msg.includes("já foi resgatada") || msg.includes("jǿ foi resgatada")) {
                            msg = "Daily check-in reward already claimed today.";
                        } else if (msg.startsWith("Check-in realizado com sucesso! Recompensa:")) {
                            msg = msg.replace("Check-in realizado com sucesso! Recompensa:", "Check-in successful! Reward:");
                        } else if (msg.startsWith("Erro no check-in:")) {
                            msg = msg.replace("Erro no check-in:", "Check-in error:");
                        }
                    }
                    return `<li style="margin-bottom: 4px;">[${time}] <strong>${gameName}</strong>: <span style="color: ${statusColor}">${msg}</span></li>`;
                }).join('');
            }
        } catch(e) {
            console.error("Erro ao ler logs de checkin:", e);
        }
    };
    
    checkinBtn.addEventListener("click", async () => {
        checkinBtn.disabled = true;
        checkinBtn.innerHTML = window.isEn
            ? '<i class="fa-solid fa-spinner fa-spin"></i> Claiming...'
            : '<i class="fa-solid fa-spinner fa-spin"></i> Resgatando...';
        try {
            const res = await fetch("/api/checkin/run", { method: "POST" });
            if (res.ok) {
                if (typeof checkinBtn.done === "function") checkinBtn.done();
                await loadLogs();
            }
        } catch (e) {
            console.error("Erro ao rodar checkin manual:", e);
        } finally {
            checkinBtn.disabled = false;
            checkinBtn.innerHTML = window.isEn
                ? '<i class="fa-solid fa-gift"></i> Claim Rewards Now'
                : '<i class="fa-solid fa-gift"></i> Resgatar Recompensas Agora';
        }
    });
    
    window.refreshCheckinLogs = loadLogs;
    loadLogs();
}


// ==========================================================================
// SUPORTE A WEB NOTIFICATIONS API (NAVEGADOR / MOBILE LAN)
// ==========================================================================
window.updateWebNotificationBadge = function() {
    const badge = document.getElementById("web-notif-badge");
    if (!badge) return;
    if (!("Notification" in window)) {
        badge.textContent = "Não suportado";
        badge.style.background = "rgba(239, 68, 68, 0.2)";
        badge.style.color = "#ef4444";
    } else if (Notification.permission === "granted") {
        badge.textContent = "Autorizado ✅";
        badge.style.background = "rgba(16, 185, 129, 0.2)";
        badge.style.color = "#10b981";
    } else if (Notification.permission === "denied") {
        badge.textContent = "Bloqueado ❌";
        badge.style.background = "rgba(239, 68, 68, 0.2)";
        badge.style.color = "#ef4444";
    } else {
        badge.textContent = "Pendente ⚠️";
        badge.style.background = "rgba(245, 158, 11, 0.2)";
        badge.style.color = "#f59e0b";
    }
};

window.triggerBrowserNotification = function(title, message, icon) {
    if (!("Notification" in window) || Notification.permission !== "granted") return;
    try {
        const n = new Notification(title, {
            body: message,
            icon: icon || "/assets/logo.webp"
        });
        n.onclick = () => {
            window.focus();
            n.close();
        };
    } catch (e) {
        console.warn("Erro ao emitir Web Notification:", e);
    }
};

// Handler para Teste Imediato de Notificações
document.addEventListener("DOMContentLoaded", () => {
    // Botão de permissão de notificações Web
    const btnWebNotif = document.getElementById("btn-request-web-notif");
    if (btnWebNotif && !btnWebNotif.dataset.bound) {
        btnWebNotif.dataset.bound = "true";
        btnWebNotif.addEventListener("click", async () => {
            if (!("Notification" in window)) {
                showToast("Seu navegador não suporta a Web Notification API.", "error");
                return;
            }
            try {
                const perm = await Notification.requestPermission();
                window.updateWebNotificationBadge();
                if (perm === "granted") {

        showToast(isEn ? "Browser notifications authorized successfully!" : "Notificações no navegador autorizadas com sucesso!", "success");
                    window.triggerBrowserNotification(
                        "🔔 Cabeça de Droid • Alerta Web",
                        "Suas notificações no navegador estão ativas e funcionando perfeitamente!"
                    );
                } else if (perm === "denied") {
                    showToast("Permissão de notificações bloqueada no navegador.", "error");
                }
            } catch (err) {
                console.error("Erro ao solicitar permissão de notificações:", err);
            }
        });
    }

    const btnTestNotif = document.getElementById("btn-test-notifications");
    if (btnTestNotif && !btnTestNotif.dataset.bound) {
        btnTestNotif.dataset.bound = "true";
        btnTestNotif.addEventListener("click", async () => {
            const discordUrl = document.getElementById("cfg-notif-discord-url")?.value || "";
            const tgToken = document.getElementById("cfg-notif-telegram-token")?.value || "";
            const tgChat = document.getElementById("cfg-notif-telegram-chat-id")?.value || "";
            const testWinToast = document.getElementById("cfg-notif-windows-toast")?.checked ?? true;
            const statusBox = document.getElementById("notif-test-status-box");

            btnTestNotif.disabled = true;
            btnTestNotif.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Disparando Teste...`;
            if (statusBox) {
                statusBox.style.display = "block";
                statusBox.innerHTML = `<div style="padding: 10px; border-radius: 6px; background: rgba(56,189,248,0.1); border: 1px solid #38bdf8; color: #38bdf8;"><i class="fa-solid fa-spinner fa-spin"></i> Enviando mensagens de teste para os canais configurados...</div>`;
            }

            // Se tiver permissão no navegador, dispara teste web local também
            if ("Notification" in window && Notification.permission === "granted") {
                window.triggerBrowserNotification(
                    "🔔 Teste de Notificação • Cabeça de Droid",
                    isEn ? "Web Alerts channel verified successfully!" : "Canal de Alertas Web verificado com sucesso!"
                );
            }

            try {
                const res = await fetch("/api/notifications/test", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        discord_webhook_url: discordUrl,
                        telegram_bot_token: tgToken,
                        telegram_chat_id: tgChat,
                        test_windows: testWinToast
                    })
                });
                const data = await res.json();
                const r = data.results || {};

                let html = `<div style="display: flex; flex-direction: column; gap: 8px; margin-top: 8px;">`;
                
                if (r.windows_toast && r.windows_toast.attempted) {
                    const wOk = r.windows_toast.success;
                    html += `
                        <div style="padding: 10px 14px; border-radius: 8px; background: ${wOk ? 'rgba(56,189,248,0.12)' : 'rgba(239,68,68,0.12)'}; border: 1px solid ${wOk ? '#38bdf8' : '#ef4444'}; color: ${wOk ? '#38bdf8' : '#f87171'}; display: flex; align-items: center; gap: 10px;">
                            <i class="fa-brands fa-windows" style="font-size: 16px;"></i>
                            <div><strong>Windows Toast:</strong> ${r.windows_toast.message}</div>
                        </div>
                    `;
                }

                if (r.discord && r.discord.attempted) {
                    const dOk = r.discord.success;
                    html += `
                        <div style="padding: 10px 14px; border-radius: 8px; background: ${dOk ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)'}; border: 1px solid ${dOk ? '#10b981' : '#ef4444'}; color: ${dOk ? '#4ade80' : '#f87171'}; display: flex; align-items: center; gap: 10px;">
                            <i class="fa-brands fa-discord" style="font-size: 16px;"></i>
                            <div><strong>Discord:</strong> ${r.discord.message}</div>
                        </div>
                    `;
                }

                if (r.telegram && r.telegram.attempted) {
                    const tOk = r.telegram.success;
                    html += `
                        <div style="padding: 10px 14px; border-radius: 8px; background: ${tOk ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)'}; border: 1px solid ${tOk ? '#10b981' : '#ef4444'}; color: ${tOk ? '#4ade80' : '#f87171'}; display: flex; align-items: center; gap: 10px;">
                            <i class="fa-brands fa-telegram" style="font-size: 16px;"></i>
                            <div><strong>Telegram:</strong> ${r.telegram.message}</div>
                        </div>
                    `;
                }

                html += `</div>`;
                if (statusBox) statusBox.innerHTML = html;
                if (res.ok && typeof btnTestNotif.done === "function") btnTestNotif.done();
            } catch (err) {
                console.error("Erro no teste de notificações:", err);

        if (statusBox) statusBox.innerHTML = `<div style="padding: 10px; border-radius: 6px; background: rgba(239,68,68,0.15); border: 1px solid #ef4444; color: #f87171;">${isEn ? "Failed to communicate with server to test notifications." : "Falha ao comunicar com o servidor para testar notificações."}</div>`;
            } finally {
                btnTestNotif.disabled = false;
                btnTestNotif.innerHTML = `<i class="fa-solid fa-paper-plane"></i> Testar Notificações Agora`;
            }
        });
    }


    // Handlers para Sincronização de Dados Estáticos & Datamines
    window.loadStaticDataStatus = async () => {
        try {
            const res = await fetch("/api/static-data/status");
            const data = await res.json();
            if (data.status === "success" && data.summary) {
                const s = data.summary;
                
                // Genshin
                const gTag = document.getElementById("static-status-genshin-tag");
                const gDesc = document.getElementById("static-status-genshin-desc");
                if (gTag && gDesc && s.genshin) {
                    gTag.innerText = s.genshin.offline_ready ? "Pronto (Offline)" : "Pendente";
                    gTag.style.background = s.genshin.offline_ready ? "rgba(16,185,129,0.2)" : "rgba(245,158,11,0.2)";
                    gTag.style.color = s.genshin.offline_ready ? "#34d399" : "#fbbf24";

        gDesc.innerHTML = `<strong>${s.genshin.characters}</strong> ${isEn ? "characters indexed" : "personagens indexados"}.<br><span style="color:#64748b; font-size:10px;">${isEn ? "Source:" : "Origem:"} ${s.genshin.manifest?.source || (isEn ? "Local Seed" : "Seed Local")}</span>`;
                }

                // HSR
                const hTag = document.getElementById("static-status-hsr-tag");
                const hDesc = document.getElementById("static-status-hsr-desc");
                if (hTag && hDesc && s.hsr) {
                    hTag.innerText = s.hsr.offline_ready ? "Pronto (Offline)" : "Pendente";
                    hTag.style.background = s.hsr.offline_ready ? "rgba(16,185,129,0.2)" : "rgba(245,158,11,0.2)";
                    hTag.style.color = s.hsr.offline_ready ? "#34d399" : "#fbbf24";

        hDesc.innerHTML = `<strong>${s.hsr.characters}</strong> ${isEn ? "characters indexed" : "personagens indexados"}.<br><span style="color:#64748b; font-size:10px;">${isEn ? "Source:" : "Origem:"} ${s.hsr.manifest?.source || (isEn ? "Local Seed" : "Seed Local")}</span>`;
                }

                // ZZZ
                const zTag = document.getElementById("static-status-zzz-tag");
                const zDesc = document.getElementById("static-status-zzz-desc");
                if (zTag && zDesc && s.zzz) {
                    zTag.innerText = s.zzz.offline_ready ? "Pronto (Offline)" : "Pendente";
                    zTag.style.background = s.zzz.offline_ready ? "rgba(16,185,129,0.2)" : "rgba(245,158,11,0.2)";
                    zTag.style.color = s.zzz.offline_ready ? "#34d399" : "#fbbf24";

        zDesc.innerHTML = `<strong>${s.zzz.characters}</strong> ${isEn ? "agents indexed" : "agentes indexados"}.<br><span style="color:#64748b; font-size:10px;">${isEn ? "Source:" : "Origem:"} ${s.zzz.manifest?.source || (isEn ? "Local Seed" : "Seed Local")}</span>`;
                }
            }
        } catch (err) {
            console.error("Erro ao carregar status de dados estáticos:", err);
        }
    };

    const btnSyncStatic = document.getElementById("btn-sync-static-data");
    const staticSyncResult = document.getElementById("static-sync-result-box");
    if (btnSyncStatic) {
        btnSyncStatic.addEventListener("click", async () => {
            btnSyncStatic.disabled = true;
            btnSyncStatic.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Sincronizando Datamines...`;
            const staticProg = document.getElementById("static-sync-progress");
            if (staticProg) {
                staticProg.style.display = "block";
                if (typeof staticProg.reset === "function") staticProg.reset();
                if (typeof staticProg.set === "function") staticProg.set(0.35);
            }
            if (staticSyncResult) {
                staticSyncResult.style.display = "block";
                staticSyncResult.innerHTML = `<div style="padding: 10px; border-radius: 6px; background: rgba(16,185,129,0.1); border: 1px solid #10b981; color: #34d399;"><i class="fa-solid fa-spinner fa-spin"></i> Conectando com repositórios GitHub e HoYoWiki para atualizar JSONs...</div>`;
            }

            try {
                const res = await fetch("/api/static-data/sync", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({})
                });
                const data = await res.json();
                if (data.status === "success") {
                    if (staticSyncResult) staticSyncResult.innerHTML = `<div style="padding: 10px; border-radius: 6px; background: rgba(16,185,129,0.12); border: 1px solid #10b981; color: #34d399;"><strong><i class="fa-solid fa-check"></i> ${isEn ? "Sync completed successfully!" : "Sincronização concluída com sucesso!"}</strong><ul style="margin: 6px 0 0 16px; font-size: 11px;">`;
                    let html = staticSyncResult ? staticSyncResult.innerHTML : "";
                    for (const [gid, info] of Object.entries(data.results || {})) {
                        html += `<li><strong>${gid.toUpperCase()}:</strong> ${info.character_count} ${isEn ? "characters updated via" : "personagens atualizados via"} ${info.source || 'Seed'} (${info.status})</li>`;
                    }
                    html += `</ul></div>`;
                    if (staticSyncResult) staticSyncResult.innerHTML = html;
                    if (staticProg && typeof staticProg.set === "function") staticProg.set(1.0);
                    if (res.ok && typeof btnSyncStatic.done === "function") btnSyncStatic.done();
                    window.loadStaticDataStatus();
                } else {
                    if (staticProg) staticProg.style.display = "none";

        if (staticSyncResult) staticSyncResult.innerHTML = `<div style="padding: 10px; border-radius: 6px; background: rgba(239,68,68,0.15); border: 1px solid #ef4444; color: #f87171;">${isEn ? `Sync error: ${data.detail || "Unknown error"}` : `Erro na sincronização: ${data.detail || "Falha desconhecida"}`}</div>`;
                }
            } catch (err) {
                console.error("Erro ao sincronizar dados estáticos:", err);

        if (staticSyncResult) staticSyncResult.innerHTML = `<div style="padding: 10px; border-radius: 6px; background: rgba(239,68,68,0.15); border: 1px solid #ef4444; color: #f87171;">${isEn ? "Failed to communicate with server. Offline cache remains active." : "Falha ao comunicar com o servidor. O cache offline permanece ativo."}</div>`;
            } finally {
                btnSyncStatic.disabled = false;
                btnSyncStatic.innerHTML = `<i class="fa-solid fa-rotate"></i> Sincronizar Datamines Agora`;
            }
        });
    }

    // Inicializa o status dos dados estáticos e Ordem de Farm na inicialização
    window.loadStaticDataStatus();
    if (window.loadDailyFarmOrder) {
        window.loadDailyFarmOrder("genshin");
    }
});

/* ==========================================================================
   HELP HUB INTERACTIVE LOGIC (SEARCH & FILTER & ACCORDION TOGGLE)
   ========================================================================== */
window.initHelpHubHandlers = () => {
    const searchInput = document.getElementById("help-search-input");
    const pills = document.querySelectorAll(".help-pill");
    const cards = document.querySelectorAll(".help-card");

    if (!searchInput && pills.length === 0) return;

    let activeCategory = "all";

    const executeFilterCards = (query, signal) => {
        if (signal?.aborted) return;
        const rawVal = (query || "").toLowerCase().trim();
        const activeQuery = rawVal.length >= 2 ? rawVal : "";

        cards.forEach(card => {
            const categoryMatch = activeCategory === "all" || card.dataset.category === activeCategory;
            const cardText = card.textContent.toLowerCase();
            const searchMatch = !activeQuery || cardText.includes(activeQuery);

            if (categoryMatch && searchMatch) {
                card.style.display = "flex";
            } else {
                card.style.display = "none";
            }
        });
    };

    const filterCards = () => {
        const query = searchInput ? searchInput.value : "";
        executeFilterCards(query);
    };

    if (searchInput) {
        const debouncedHelpSearch = window.createDebouncedSearch((val, signal) => {
            executeFilterCards(val, signal);
        }, { delay: 300, minLength: 2, immediateOnEmpty: true });

        searchInput.addEventListener("input", (e) => {
            const rawVal = e.target.value.trim();
            if (rawVal.length > 0 && rawVal.length < 2) {
                debouncedHelpSearch.cancel();
                executeFilterCards("");
                return;
            }
            debouncedHelpSearch(e.target.value);
        });
    }

    pills.forEach(pill => {
        pill.addEventListener("click", () => {
            pills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            activeCategory = pill.dataset.category || "all";
            filterCards();
        });
    });

    document.addEventListener("click", (e) => {
        const toggleBtn = e.target.closest(".help-toggle-details-btn");
        if (toggleBtn) {
            e.preventDefault();
            e.stopPropagation();
            const card = toggleBtn.closest(".help-card");
            const details = card?.querySelector(".help-card-details");
            if (details) {
                const isOpen = details.classList.contains("open");
                const isEn = Boolean(window.isEn || (window.getLanguage && window.getLanguage() === "en") || (localStorage.getItem("app_lang") === "en"));
                if (isOpen) {
                    details.classList.remove("open");
                    toggleBtn.innerHTML = `<i class="fa-solid fa-chevron-down"></i> <span data-i18n="help_btn_details">${isEn ? "Details" : "Detalhes"}</span>`;
                } else {
                    details.classList.add("open");
                    toggleBtn.innerHTML = `<i class="fa-solid fa-chevron-up"></i> <span data-i18n="help_btn_collapse">${isEn ? "Collapse" : "Recolher"}</span>`;
                }
            }
        }
    });
};

document.addEventListener("DOMContentLoaded", () => {
    window.initHelpHubHandlers();
    if (window.initGachaSimulator) {
        window.initGachaSimulator();
    }
    if (window.initGachaNavigation) {
        window.initGachaNavigation();
    }
    if (window.updateGoalsCountBadge) {
        window.updateGoalsCountBadge();
    }
});



// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
if (typeof setupCheckinSystem !== 'undefined') window.setupCheckinSystem = setupCheckinSystem;
if (typeof setupEnergyMonitor !== 'undefined') window.setupEnergyMonitor = setupEnergyMonitor;
if (typeof setupSyncControls !== 'undefined') window.setupSyncControls = setupSyncControls;
if (typeof startPollingStatus !== 'undefined') window.startPollingStatus = startPollingStatus;
if (typeof triggerSync !== 'undefined') window.triggerSync = triggerSync;
if (typeof updateEnergyCircle !== 'undefined') window.updateEnergyCircle = updateEnergyCircle;