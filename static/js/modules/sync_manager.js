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
        }, 8000);
    });
}

async function triggerSync(gameId, run_roster, run_guides, run_meta) {
    const loggerDiv = document.getElementById(`sync-logger-${gameId}`);
    loggerDiv.style.display = "flex";
    
    try {
        const res = await fetch(`/api/sync/${gameId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ run_roster, run_guides, run_meta })
        });
        
        if (res.ok) {
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
    const perc = loggerDiv.querySelector(".logger-percentage");
    const msg = loggerDiv.querySelector(".logger-message");
    const term = loggerDiv.querySelector(".logger-terminal");
    
    activePolling[gameId] = setInterval(async () => {
        try {
            const res = await fetch(`/api/status/${gameId}`);
            const status = await res.json();
            
            const progressPct = Math.round(status.progress * 100);
            bar.style.width = `${progressPct}%`;
            perc.innerText = `${progressPct}%`;
            msg.innerText = status.message;
            
            // Une e exibe a lista de logs no console retrátil
            term.innerText = status.logs.join("\n");
            term.scrollTop = term.scrollHeight; // Auto-scroll
            
            if (!status.running) {
                clearInterval(activePolling[gameId]);
                activePolling[gameId] = null;
                // Recarrega o roster visual e endgame do jogo que acabou de sincronizar
                setTimeout(() => {
                    loadRoster(gameId);
                    loadEndgame(gameId);
                    loadOverview();
                }, 1000);
            }
        } catch (err) {
            console.error(`Erro ao consultar status de ${gameId}:`, err);
        }
    }, 1000);
}


// ==========================================================================
// FUNÇÕES DO MONITOR DE ENERGIA (RESINA / PODER / BATERIA)
// ==========================================================================
async function setupEnergyMonitor() {
    const fetchNotes = async () => {
        try {
            const res = await fetch("/api/notes");
            const data = await res.json();
            
            // Genshin
            if (data.genshin) {
                const notes = data.genshin;
                let timeStr = "Totalmente carregada";
                if (notes.recovery_time && notes.recovery_time !== "0:00:00" && notes.recovery_time !== "0") {
                    // Formata a string de tempo (ex: "1 day, 2:30:15" -> "1d 2h 30m" ou "2h 30m")
                    let displayTime = notes.recovery_time;
                    try {
                        const parts = notes.recovery_time.split(":");
                        if (parts.length >= 2) {
                            displayTime = `${parts[0]}h ${parts[1]}m`;
                        }
                    } catch(e) {}
                    timeStr = `Recuperação: ${displayTime}`;
                }
                updateEnergyCircle("genshin", notes.current_energy, notes.max_energy, timeStr);
            } else {
                updateEnergyCircle("genshin", 0, 200, "Sem dados sincronizados");
            }
            
            // HSR
            if (data.hsr) {
                const notes = data.hsr;
                let timeStr = "Totalmente carregado";
                if (notes.recovery_time && notes.recovery_time !== "0" && notes.recovery_time !== "0:00:00") {
                    let displayTime = notes.recovery_time;
                    try {
                        const sec = parseInt(notes.recovery_time);
                        if (!isNaN(sec) && sec > 0) {
                            const hrs = Math.floor(sec / 3600);
                            const mins = Math.floor((sec % 3600) / 60);
                            displayTime = `${hrs}h ${mins}m`;
                        }
                    } catch(e) {}
                    timeStr = `Recuperação: ${displayTime}`;
                }
                updateEnergyCircle("hsr", notes.current_energy, notes.max_energy, timeStr);
            } else {
                updateEnergyCircle("hsr", 0, 240, "Sem dados sincronizados");
            }
            
            // ZZZ
            if (data.zzz) {
                const notes = data.zzz;
                let timeStr = "Totalmente carregada";
                if (notes.recovery_time && notes.recovery_time !== "0" && notes.recovery_time !== "0:00:00") {
                    let displayTime = notes.recovery_time;
                    try {
                        const sec = parseInt(notes.recovery_time);
                        if (!isNaN(sec) && sec > 0) {
                            const hrs = Math.floor(sec / 3600);
                            const mins = Math.floor((sec % 3600) / 60);
                            displayTime = `${hrs}h ${mins}m`;
                        }
                    } catch(e) {}
                    timeStr = `Recuperação: ${displayTime}`;
                }
                updateEnergyCircle("zzz", notes.current_energy, notes.max_energy, timeStr);
            } else {
                updateEnergyCircle("zzz", 0, 240, "Sem dados sincronizados");
            }
        } catch (err) {
            console.error("Erro ao carregar notas diárias:", err);
        }
    };
    
    fetchNotes();
    setInterval(fetchNotes, 60000); // Atualiza a cada 1 minuto
}

function updateEnergyCircle(gameId, current, max, remainText) {
    const ring = document.getElementById(`ring-${gameId}`);
    const valEl = document.getElementById(`lbl-${gameId}-val`);
    const timeEl = document.getElementById(`lbl-${gameId}-time`);
    if (!ring || !valEl || !timeEl) return;
    
    valEl.innerText = `${current}/${max}`;
    timeEl.innerText = remainText;
    
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
                    
                    return `<li style="margin-bottom: 4px;">[${time}] <strong>${gameName}</strong>: <span style="color: ${statusColor}">${l.message}</span></li>`;
                }).join('');
            }
        } catch(e) {
            console.error("Erro ao ler logs de checkin:", e);
        }
    };
    
    checkinBtn.addEventListener("click", async () => {
        checkinBtn.disabled = true;
        checkinBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Resgatando...';
        try {
            const res = await fetch("/api/checkin/run", { method: "POST" });
            if (res.ok) {
                await loadLogs();
            }
        } catch (e) {
            console.error("Erro ao rodar checkin manual:", e);
        } finally {
            checkinBtn.disabled = false;
            checkinBtn.innerHTML = '<i class="fa-solid fa-gift"></i> Resgatar Recompensas Agora';
        }
    });
    
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
            icon: icon || "https://act.hoyolab.com/app/community-game-records/images/favicon.ico"
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
                    showToast("Notificações no navegador autorizadas com sucesso!", "success");
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
                    "Canal de Alertas Web verificado com sucesso!"
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
            } catch (err) {
                console.error("Erro no teste de notificações:", err);
                if (statusBox) statusBox.innerHTML = `<div style="padding: 10px; border-radius: 6px; background: rgba(239,68,68,0.15); border: 1px solid #ef4444; color: #f87171;">Falha ao comunicar com o servidor para testar notificações.</div>`;
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
                    gDesc.innerHTML = `<strong>${s.genshin.characters}</strong> personagens indexados.<br><span style="color:#64748b; font-size:10px;">Origem: ${s.genshin.manifest?.source || 'Seed Local'}</span>`;
                }

                // HSR
                const hTag = document.getElementById("static-status-hsr-tag");
                const hDesc = document.getElementById("static-status-hsr-desc");
                if (hTag && hDesc && s.hsr) {
                    hTag.innerText = s.hsr.offline_ready ? "Pronto (Offline)" : "Pendente";
                    hTag.style.background = s.hsr.offline_ready ? "rgba(16,185,129,0.2)" : "rgba(245,158,11,0.2)";
                    hTag.style.color = s.hsr.offline_ready ? "#34d399" : "#fbbf24";
                    hDesc.innerHTML = `<strong>${s.hsr.characters}</strong> personagens indexados.<br><span style="color:#64748b; font-size:10px;">Origem: ${s.hsr.manifest?.source || 'Seed Local'}</span>`;
                }

                // ZZZ
                const zTag = document.getElementById("static-status-zzz-tag");
                const zDesc = document.getElementById("static-status-zzz-desc");
                if (zTag && zDesc && s.zzz) {
                    zTag.innerText = s.zzz.offline_ready ? "Pronto (Offline)" : "Pendente";
                    zTag.style.background = s.zzz.offline_ready ? "rgba(16,185,129,0.2)" : "rgba(245,158,11,0.2)";
                    zTag.style.color = s.zzz.offline_ready ? "#34d399" : "#fbbf24";
                    zDesc.innerHTML = `<strong>${s.zzz.characters}</strong> agentes indexados.<br><span style="color:#64748b; font-size:10px;">Origem: ${s.zzz.manifest?.source || 'Seed Local'}</span>`;
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
                    let html = `<div style="padding: 10px 14px; border-radius: 8px; background: rgba(16,185,129,0.12); border: 1px solid #10b981; color: #4ade80;">`;
                    html += `<strong><i class="fa-solid fa-check"></i> Sincronização concluída com sucesso!</strong><ul style="margin: 6px 0 0 16px; font-size: 11px;">`;
                    for (const [gid, info] of Object.entries(data.results || {})) {
                        html += `<li><strong>${gid.toUpperCase()}:</strong> ${info.character_count} personagens atualizados via ${info.source || 'Seed'} (${info.status})</li>`;
                    }
                    html += `</ul></div>`;
                    if (staticSyncResult) staticSyncResult.innerHTML = html;
                    window.loadStaticDataStatus();
                } else {
                    if (staticSyncResult) staticSyncResult.innerHTML = `<div style="padding: 10px; border-radius: 6px; background: rgba(239,68,68,0.15); border: 1px solid #ef4444; color: #f87171;">Erro na sincronização: ${data.detail || 'Falha desconhecida'}</div>`;
                }
            } catch (err) {
                console.error("Erro ao sincronizar dados estáticos:", err);
                if (staticSyncResult) staticSyncResult.innerHTML = `<div style="padding: 10px; border-radius: 6px; background: rgba(239,68,68,0.15); border: 1px solid #ef4444; color: #f87171;">Falha ao comunicar com o servidor. O cache offline permanece ativo.</div>`;
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

    const filterCards = () => {
        const query = (searchInput?.value || "").toLowerCase().trim();

        cards.forEach(card => {
            const categoryMatch = activeCategory === "all" || card.dataset.category === activeCategory;
            const cardText = card.textContent.toLowerCase();
            const searchMatch = !query || cardText.includes(query);

            if (categoryMatch && searchMatch) {
                card.style.display = "flex";
            } else {
                card.style.display = "none";
            }
        });
    };

    if (searchInput) {
        searchInput.addEventListener("input", filterCards);
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
                if (isOpen) {
                    details.classList.remove("open");
                    toggleBtn.innerHTML = `<i class="fa-solid fa-chevron-down"></i> Detalhes`;
                } else {
                    details.classList.add("open");
                    toggleBtn.innerHTML = `<i class="fa-solid fa-chevron-up"></i> Recolher`;
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