// ==========================================================================
// Ponto de Entrada Principal (ES6 Entry Point) - Cabeça de Droid
// ==========================================================================

// Importação ordenada dos módulos desacoplados
import "./modules/api_client.js?v=23.5";
import "./modules/modal.js?v=23.5";
import "./modules/navigation.js?v=23.5";
import "./modules/config_manager.js?v=23.5";
import "./modules/sync_manager.js?v=23.5";
import "./modules/endgame.js?v=23.5";
import "./modules/roster.js?v=23.5";
import "./modules/build_comparator.js?v=23.5";
import "./modules/chat_rag.js?v=23.5";
import "./modules/farming.js?v=23.5";
import "./modules/gacha_sim.js?v=23.5";
import "./modules/gacha_tracker.js?v=23.5";

// Inicialização da Aplicação
// ==========================================================================
// INICIALIZAÇÃO DA APLICAÇÃO
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    setupSidebarToggle();
    setupTabSwitching();
    setupConfigForm();
    setupSyncControls();
    setupChatSystem();
    setupEnergyMonitor();
    setupCheckinSystem();
    setupInspectorTabs();
    setupSubnavTabs();
    setupPinSecurityUI();
    
    // Carrega dados iniciais
    fetchConfig();
    loadOverview();
    if (typeof loadAccountsManagement === "function") {
        loadAccountsManagement();
    }
    loadRoster("zzz");
    loadRoster("genshin");
    loadRoster("hsr");
    loadEndgame("zzz");
    loadEndgame("genshin");
    loadEndgame("hsr");
});

async function loadOverview() {
    try {
        // Busca simultaneamente o overview agregado e a lista detalhada de contas salvas
        const [resOverview, resAccounts] = await Promise.allSettled([
            fetch("/api/overview").then(r => r.json()),
            fetch("/api/accounts").then(r => r.json())
        ]);

        const overview = resOverview.status === "fulfilled" ? resOverview.value : {};
        
        let accountsList = [];
        let activeAccountsMap = {};
        if (resAccounts.status === "fulfilled" && resAccounts.value) {
            if (Array.isArray(resAccounts.value)) {
                accountsList = resAccounts.value;
            } else if (resAccounts.value.accounts) {
                accountsList = resAccounts.value.accounts;
                activeAccountsMap = resAccounts.value.active_accounts || {};
            }
        }

        // Mapeia contas por jogo (priorizando conta ativa configurada no SQLite, ou maior nível)
        const accountByGame = {};
        accountsList.forEach(acc => {
            const gid = acc.game_id;
            const lvl = parseInt(acc.level) || 0;
            const isActive = (activeAccountsMap[gid] && String(activeAccountsMap[gid]) === String(acc.uid)) || acc.is_active;

            if (!accountByGame[gid]) {
                accountByGame[gid] = acc;
            } else if (isActive) {
                accountByGame[gid] = acc;
            } else if (!accountByGame[gid].is_active && lvl > (parseInt(accountByGame[gid].level) || 0)) {
                accountByGame[gid] = acc;
            }
        });

        // Mescla dados de nickname e UID com o overview
        ["zzz", "genshin", "hsr"].forEach(gid => {
            if (!overview[gid]) overview[gid] = {};
            if (accountByGame[gid]) {
                if (accountByGame[gid].nickname && !overview[gid].nickname) {
                    overview[gid].nickname = accountByGame[gid].nickname;
                }
                if (accountByGame[gid].uid && (!overview[gid].uid || overview[gid].uid === "Não sincronizado")) {
                    overview[gid].uid = accountByGame[gid].uid;
                }
                if (accountByGame[gid].level && (!overview[gid].level || overview[gid].level === "N/A")) {
                    overview[gid].level = String(accountByGame[gid].level);
                }
            }
        });

        window.globalOverview = overview;
        window.globalAccounts = accountByGame;
        
        // ZZZ
        if (overview.zzz) {
            const zNick = overview.zzz.nickname ? `${overview.zzz.nickname} • ` : "";
            const zUidEl = document.getElementById("ov-zzz-uid");
            if (zUidEl) zUidEl.innerText = overview.zzz.uid && overview.zzz.uid !== "Não sincronizado" ? `${zNick}UID: ${overview.zzz.uid}` : "Não sincronizado";
            const zLvlEl = document.getElementById("ov-zzz-lvl");
            if (zLvlEl) zLvlEl.innerText = overview.zzz.level || "N/A";
            const zCharsEl = document.getElementById("ov-zzz-chars");
            if (zCharsEl) zCharsEl.innerText = overview.zzz.char_count || 0;
        }
        
        // Genshin
        if (overview.genshin) {
            const gNick = overview.genshin.nickname ? `${overview.genshin.nickname} • ` : "";
            const gUidEl = document.getElementById("ov-genshin-uid");
            if (gUidEl) gUidEl.innerText = overview.genshin.uid && overview.genshin.uid !== "Não sincronizado" ? `${gNick}UID: ${overview.genshin.uid}` : "Não sincronizado";
            const gLvlEl = document.getElementById("ov-genshin-lvl");
            if (gLvlEl) gLvlEl.innerText = overview.genshin.level || "N/A";
            const gCharsEl = document.getElementById("ov-genshin-chars");
            if (gCharsEl) gCharsEl.innerText = overview.genshin.char_count || 0;
        }
        
        // HSR
        if (overview.hsr) {
            const hNick = overview.hsr.nickname ? `${overview.hsr.nickname} • ` : "";
            const hUidEl = document.getElementById("ov-hsr-uid");
            if (hUidEl) hUidEl.innerText = overview.hsr.uid && overview.hsr.uid !== "Não sincronizado" ? `${hNick}UID: ${overview.hsr.uid}` : "Não sincronizado";
            const hLvlEl = document.getElementById("ov-hsr-lvl");
            if (hLvlEl) hLvlEl.innerText = overview.hsr.level || "N/A";
            const hCharsEl = document.getElementById("ov-hsr-chars");
            if (hCharsEl) hCharsEl.innerText = overview.hsr.char_count || 0;
        }

        // Se houver cards de time renderizados na interface, atualiza o nome e UID do jogador
        ["zzz", "genshin", "hsr"].forEach(g => {
            const acc = overview[g];
            if (acc) {
                const nickEl = document.getElementById(`team-player-name-${g}`);
                if (nickEl && acc.nickname) nickEl.innerText = acc.nickname;
                const uidEl = document.getElementById(`team-player-uid-${g}`);
                if (uidEl && acc.uid && acc.uid !== "Não sincronizado") uidEl.innerText = `UID: ${acc.uid}`;
            }
        });
    } catch (err) {
        console.error("Erro ao carregar visão geral:", err);
    }
}


