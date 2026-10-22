// ==========================================================================
// Módulo: gacha_tracker.js
// Cabeça de Droid - Vanilla ES6 Module
// ==========================================================================

// ==========================================================================
// RASTREADOR REAL DE TIROS & PITY OFICIAL (ETAPA 8)
// ==========================================================================

window.currentTrackerGame = "hsr";

window.switchGachaTrackerGame = function(gameId) {
    window.currentTrackerGame = gameId;
    document.querySelectorAll(".tracker-game-btn").forEach(btn => {
        if (btn.getAttribute("data-game") === gameId) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });
    window.loadGachaTracker(gameId);
};

window.loadGachaTracker = async function(gameId) {
    const gid = gameId || window.currentTrackerGame || "hsr";
    try {
        const res = await fetch(`/api/gacha/tracker/${gid}`);
        if (!res.ok) throw new Error("Falha ao carregar dados do rastreador");
        const data = await res.json();

        // 1. Métricas Globais de Sorte
        const totalPullsEl = document.getElementById("tracker-stat-total-pulls");
        const totalFivesEl = document.getElementById("tracker-stat-total-fives");
        const avgPityEl = document.getElementById("tracker-stat-avg-pity");
        const luckBadgeEl = document.getElementById("tracker-luck-badge");

        if (totalPullsEl) totalPullsEl.textContent = data.total_pulls_all_banners || 0;
        if (totalFivesEl) totalFivesEl.textContent = data.total_five_stars_all_banners || 0;
        if (avgPityEl) {
            const avg = data.character_banner ? data.character_banner.avg_five_star_pity : 0;
            avgPityEl.textContent = avg > 0 ? `${avg} tiros` : "--";
        }
        if (luckBadgeEl) {
            luckBadgeEl.innerHTML = `<i class="fa-solid fa-clover" style="color: #34d399;"></i> ${data.overall_luck_rating || 'Sem dados'}`;
        }

        // 2. Banner de Personagem
        const cb = data.character_banner || {};
        const charPityCurrent = document.getElementById("tracker-char-pity-current");
        const charSoftPityText = document.getElementById("tracker-char-soft-pity-text");
        const charPityBar = document.getElementById("tracker-char-pity-bar");
        const charStatusBadge = document.getElementById("tracker-char-status-badge");
        const charHistoryList = document.getElementById("tracker-char-history-list");

        const curCharPity = cb.current_pity || 0;
        if (charPityCurrent) charPityCurrent.textContent = curCharPity;
        if (charSoftPityText) {
            charSoftPityText.textContent = cb.next_soft_pity_in > 0 
                ? `Faltam ${cb.next_soft_pity_in} tiros para o Soft Pity (74)`
                : `🔥 Soft Pity Ativo! (+6% de chance por tiro)`;
        }
        if (charPityBar) {
            const pct = Math.min(100, Math.round((curCharPity / 90) * 100));
            charPityBar.style.width = `${pct}%`;
            if (curCharPity >= 74) {
                charPityBar.style.background = "linear-gradient(90deg, #f59e0b, #fbbf24)";
                charPityBar.style.boxShadow = "0 0 10px rgba(251, 191, 36, 0.5)";
            } else {
                charPityBar.style.background = "linear-gradient(90deg, #38bdf8, #818cf8)";
                charPityBar.style.boxShadow = "none";
            }
        }
        if (charStatusBadge) {
            if (cb.is_guaranteed) {
                charStatusBadge.style.background = "rgba(52, 211, 153, 0.2)";
                charStatusBadge.style.border = "1px solid rgba(52, 211, 153, 0.5)";
                charStatusBadge.style.color = "#34d399";
                charStatusBadge.innerHTML = `<i class="fa-solid fa-shield"></i> GARANTIDO (100%)`;
            } else {
                charStatusBadge.style.background = "rgba(251, 191, 36, 0.15)";
                charStatusBadge.style.border = "1px solid rgba(251, 191, 36, 0.35)";
                charStatusBadge.style.color = "#fbbf24";
                charStatusBadge.innerHTML = `<i class="fa-solid fa-scale-balanced"></i> 50/50 EM DISPUTA`;
            }
        }
        if (charHistoryList) {
            const recents = cb.recent_five_stars || [];
            if (recents.length === 0) {
                charHistoryList.innerHTML = `<span style="font-size: 11px; color: var(--text-muted); font-style: italic;">Nenhum registro de 5★ ainda.</span>`;
            } else {
                charHistoryList.innerHTML = recents.map(f => {
                    const winColor = f.is_win_5050 ? "#34d399" : "#f87171";
                    const winLabel = f.is_win_5050 ? "Vitória" : "Derrota";
                    return `
                        <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 6px 10px; display: flex; align-items: center; justify-content: space-between;">
                            <div>
                                <strong style="color: #fbbf24; font-size: 12px;">${f.name}</strong>
                                <span style="font-size: 10px; color: var(--text-muted); margin-left: 6px;">${f.time ? f.time.split(' ')[0] : ''}</span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 6px;">
                                <span style="font-size: 11px; font-weight: 800; background: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 1px 6px; border-radius: 6px;">Pity ${f.pity}</span>
                                <span style="font-size: 10px; font-weight: 700; color: ${winColor};">${winLabel}</span>
                            </div>
                        </div>
                    `;
                }).join("");
            }
        }

        // 3. Banner de Armas
        const wb = data.weapon_banner || {};
        const weaponPityCurrent = document.getElementById("tracker-weapon-pity-current");
        const weaponSoftPityText = document.getElementById("tracker-weapon-soft-pity-text");
        const weaponPityBar = document.getElementById("tracker-weapon-pity-bar");
        const weaponHistoryList = document.getElementById("tracker-weapon-history-list");

        const curWpPity = wb.current_pity || 0;
        if (weaponPityCurrent) weaponPityCurrent.textContent = curWpPity;
        if (weaponSoftPityText) {
            weaponSoftPityText.textContent = wb.next_soft_pity_in > 0 
                ? `Faltam ${wb.next_soft_pity_in} tiros para o Soft Pity (64)`
                : `🔥 Soft Pity Ativo!`;
        }
        if (weaponPityBar) {
            const pct = Math.min(100, Math.round((curWpPity / 80) * 100));
            weaponPityBar.style.width = `${pct}%`;
        }
        if (weaponHistoryList) {
            const recents = wb.recent_five_stars || [];
            if (recents.length === 0) {
                weaponHistoryList.innerHTML = `<span style="font-size: 11px; color: var(--text-muted); font-style: italic;">Nenhum registro de 5★ ainda.</span>`;
            } else {
                weaponHistoryList.innerHTML = recents.map(f => `
                    <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 6px 10px; display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <strong style="color: #c084fc; font-size: 12px;">${f.name}</strong>
                            <span style="font-size: 10px; color: var(--text-muted); margin-left: 6px;">${f.time ? f.time.split(' ')[0] : ''}</span>
                        </div>
                        <span style="font-size: 11px; font-weight: 800; background: rgba(192, 132, 252, 0.2); color: #c084fc; padding: 1px 6px; border-radius: 6px;">Pity ${f.pity}</span>
                    </div>
                `).join("");
            }
        }

        // 4. Banner Padrão
        const sb = data.standard_banner || {};
        const stdPityCurrent = document.getElementById("tracker-standard-pity-current");
        const stdSoftPityText = document.getElementById("tracker-standard-soft-pity-text");
        const stdPityBar = document.getElementById("tracker-standard-pity-bar");
        const stdHistoryList = document.getElementById("tracker-standard-history-list");

        const curStdPity = sb.current_pity || 0;
        if (stdPityCurrent) stdPityCurrent.textContent = curStdPity;
        if (stdSoftPityText) {
            stdSoftPityText.textContent = sb.next_soft_pity_in > 0 
                ? `Faltam ${sb.next_soft_pity_in} tiros para o Soft Pity (74)`
                : `🔥 Soft Pity Ativo!`;
        }
        if (stdPityBar) {
            const pct = Math.min(100, Math.round((curStdPity / 90) * 100));
            stdPityBar.style.width = `${pct}%`;
        }
        if (stdHistoryList) {
            const recents = sb.recent_five_stars || [];
            if (recents.length === 0) {
                stdHistoryList.innerHTML = `<span style="font-size: 11px; color: var(--text-muted); font-style: italic;">Nenhum registro de 5★ ainda.</span>`;
            } else {
                stdHistoryList.innerHTML = recents.map(f => `
                    <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 6px 10px; display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <strong style="color: #cbd5e1; font-size: 12px;">${f.name}</strong>
                            <span style="font-size: 10px; color: var(--text-muted); margin-left: 6px;">${f.time ? f.time.split(' ')[0] : ''}</span>
                        </div>
                        <span style="font-size: 11px; font-weight: 800; background: rgba(255,255,255,0.1); color: #fff; padding: 1px 6px; border-radius: 6px;">Pity ${f.pity}</span>
                    </div>
                `).join("");
            }
        }
    } catch (err) {
        console.error("Erro ao carregar dados do Gacha Tracker:", err);
    }
};

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

        const res = await fetch(`/api/gacha/tracker/import/${gid}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ raw_data: jsonPayload })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Erro ao importar histórico");

        if (typeof showToast === "function") {
            showToast(data.message || `${data.total_imported} tiros importados com sucesso!`, "success");
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
            showToast("Backup UIGF baixado com sucesso!", "success");
        }
    } catch (err) {
        console.error("Erro ao exportar UIGF:", err);
        if (typeof showToast === "function") {
            showToast("Falha ao exportar backup: " + err.message, "error");
        }
    }
};

window.clearGachaLogHistory = async function() {
    const gid = window.currentTrackerGame || "hsr";
    if (!confirm(`Tem certeza que deseja apagar todo o histórico de tiros de ${gid.toUpperCase()} do banco local?`)) {
        return;
    }

    try {
        const res = await fetch(`/api/gacha/tracker/${gid}`, { method: "DELETE" });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Erro ao limpar histórico");

        if (typeof showToast === "function") {
            showToast(data.message || "Histórico de tiros limpo com sucesso.", "success");
        }
        window.loadGachaTracker(gid);
    } catch (err) {
        console.error("Erro ao limpar histórico:", err);
        if (typeof showToast === "function") {
            showToast("Falha ao limpar histórico: " + err.message, "error");
        }
    }
};













// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
