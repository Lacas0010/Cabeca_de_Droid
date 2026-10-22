// ==========================================================================
// Módulo: config_manager.js
// Cabeça de Droid - Vanilla ES6 Module
// ==========================================================================

// ==========================================================================
// SISTEMA DE CONFIGURAÇÃO (API KEYS & COOKIES & SEGURANÇA DPAPI)
// ==========================================================================
async function fetchConfig() {
    try {
        const [cfgRes, secRes] = await Promise.all([
            fetch("/api/config"),
            fetch("/api/security/status")
        ]);

        const config = await cfgRes.json();
        let secStatus = {};
        if (secRes.ok) {
            secStatus = await secRes.json();
        }
        
        // 1. Chave IA Groq (Tratada com máscara ou em branco para segurança)
        const groqInput = document.getElementById("cfg-groq-key");
        if (groqInput) {
            if (config.has_api_key) {
                groqInput.value = "";
                groqInput.placeholder = config.groq_api_key || "gsk_... (Chave configurada)";
            } else {
                groqInput.value = "";
                groqInput.placeholder = "gsk_...";
            }
        }

        // 2. Máscara de Cookies (Zero-Exposure de tokens no frontend)
        const previewEl = document.getElementById("cfg-cookies-preview-text");
        const previewTag = document.getElementById("cfg-cookies-status-tag");
        if (previewEl) {
            if (config.has_cookies && config.cookies_preview) {
                previewEl.innerHTML = `<i class="fa-solid fa-shield-halved" style="color: #34d399; margin-right: 6px;"></i><code>${config.cookies_preview}</code>`;
                if (previewTag) previewTag.style.display = "inline-block";
            } else {
                previewEl.innerHTML = `<i class="fa-solid fa-lock" style="margin-right: 6px;"></i>Nenhum cookie configurado no cofre.`;
                if (previewTag) previewTag.style.display = "none";
            }
        }

        // Campo de entrada de novos cookies (sempre limpo para gravação descartável)
        const hoyoInput = document.getElementById("cfg-hoyolab-cookies");
        if (hoyoInput) hoyoInput.value = "";

        // 3. Vault Badge
        const vaultBadge = document.getElementById("cfg-vault-badge");
        if (vaultBadge && secStatus.storage_backend) {
            if (secStatus.dpapi_available) {
                vaultBadge.innerHTML = `<i class="fa-solid fa-shield-halved"></i> <span>Proteção Windows DPAPI Ativa</span>`;
            } else {
                vaultBadge.innerHTML = `<i class="fa-solid fa-shield"></i> <span>Cofre Criptografado Ativo</span>`;
            }
        }

        // 4. PIN de Segurança
        const pinCheckbox = document.getElementById("cfg-pin-enabled");
        const pinBox = document.getElementById("cfg-pin-config-box");
        const disablePinBtn = document.getElementById("btn-disable-pin");
        const newPinInput = document.getElementById("cfg-new-pin");
        if (pinCheckbox) {
            pinCheckbox.checked = !!secStatus.pin_enabled;
        }
        if (pinBox) {
            pinBox.style.display = secStatus.pin_enabled ? "block" : "none";
        }
        if (disablePinBtn) {
            disablePinBtn.style.display = secStatus.pin_enabled ? "inline-flex" : "none";
        }
        if (newPinInput) {
            newPinInput.value = "";
            newPinInput.placeholder = secStatus.pin_enabled ? "PIN Ativo (Alterar)" : "Digite 4 a 6 dígitos";
        }

        // 5. Controle de Acesso LAN
        const lanToggle = document.getElementById("cfg-lan-access-toggle");
        const lanStatusMsg = document.getElementById("cfg-lan-status-msg");
        if (lanToggle) {
            lanToggle.checked = !!secStatus.allow_lan_access;
        }
        if (lanStatusMsg) {
            lanStatusMsg.innerText = secStatus.allow_lan_access 
                ? "Acesso LAN ativo: Celular/tablet na mesma rede Wi-Fi podem acessar." 
                : "Isolamento seguro ativo: Apenas este computador tem acesso às APIs e aos dados.";
        }
        
        updateApiStatusIndicator(config.has_api_key && config.has_cookies);
    } catch (err) {
        console.error("Erro ao buscar configurações:", err);
    }
}

function updateApiStatusIndicator(online) {
    const dot = document.getElementById("api-status-dot");
    const text = document.getElementById("api-status-text");
    if (dot && text) {
        if (online) {
            dot.className = "status-dot online";
            text.innerText = "IA & Cookies Conectados";
        } else {
            dot.className = "status-dot offline";
            text.innerText = "Configuração pendente";
        }
    }
}

async function setupConfigForm() {
    const saveBtn = document.getElementById("btn-save-config");
    const autoLoginBtn = document.getElementById("btn-auto-login");
    const statusMsg = document.getElementById("config-save-status");
    const clearCredsBtn = document.getElementById("btn-clear-credentials");
    const pinCheckbox = document.getElementById("cfg-pin-enabled");
    const savePinBtn = document.getElementById("btn-save-pin");
    const disablePinBtn = document.getElementById("btn-disable-pin");
    const lanToggle = document.getElementById("cfg-lan-access-toggle");

    // Salvar Configurações (Chave Groq + Cookies)
    if (saveBtn) {
        saveBtn.addEventListener("click", async () => {
            const groq_api_key = document.getElementById("cfg-groq-key")?.value || "";
            const cookies_raw = document.getElementById("cfg-hoyolab-cookies")?.value || "";
            
            if (statusMsg) {
                statusMsg.className = "status-msg";
                statusMsg.innerText = "Criptografando e salvando...";
            }
            
            try {
                const res = await fetch("/api/config", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ groq_api_key, cookies_raw })
                });
                const data = await res.json();
                
                if (res.ok) {
                    if (statusMsg) {
                        statusMsg.className = "status-msg success";
                        statusMsg.innerText = "Configurações salvas no cofre com sucesso!";
                    }
                    showToast("Configurações atualizadas e criptografadas!", "success");
                    fetchConfig();
                } else {
                    if (statusMsg) {
                        statusMsg.className = "status-msg error";
                        statusMsg.innerText = `Erro: ${data.detail || "Erro desconhecido"}`;
                    }
                }
            } catch (err) {
                if (statusMsg) {
                    statusMsg.className = "status-msg error";
                    statusMsg.innerText = "Erro ao conectar com o servidor.";
                }
            }
        });
    }

    // Auto Login Playwright
    if (autoLoginBtn) {
        autoLoginBtn.addEventListener("click", async () => {
            autoLoginBtn.disabled = true;
            autoLoginBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Aguardando login no navegador...';
            
            try {
                const res = await fetch("/api/login/auto", { method: "POST" });
                if (res.ok) {
                    let attempts = 0;
                    const interval = setInterval(async () => {
                        attempts++;
                        const checkRes = await fetch("/api/config");
                        const checkCfg = await checkRes.json();
                        if (checkCfg.has_cookies || attempts > 60) {
                            clearInterval(interval);
                            autoLoginBtn.disabled = false;
                            autoLoginBtn.innerHTML = '<i class="fa-solid fa-earth-americas"></i> Login Automático via Playwright';
                            showToast("Cookies capturados e criptografados com sucesso!", "success");
                            fetchConfig();
                        }
                    }, 2000);
                }
            } catch (err) {
                autoLoginBtn.disabled = false;
                autoLoginBtn.innerHTML = '<i class="fa-solid fa-earth-americas"></i> Login Automático via Playwright';
            }
        });
    }

    // Limpar Credenciais do Cofre
    if (clearCredsBtn) {
        clearCredsBtn.addEventListener("click", async () => {
            if (!confirm("Deseja realmente apagar todos os cookies e chaves de IA armazenados no cofre?")) return;
            try {
                const res = await fetch("/api/security/clear_credentials", { method: "POST" });
                if (res.ok) {
                    showToast("Credenciais e tokens removidos com sucesso.", "info");
                    fetchConfig();
                } else {
                    showToast("Erro ao limpar credenciais.", "error");
                }
            } catch (err) {
                showToast("Erro ao conectar com o servidor.", "error");
            }
        });
    }

    // Toggle de ativação do PIN
    if (pinCheckbox) {
        pinCheckbox.addEventListener("change", () => {
            const pinBox = document.getElementById("cfg-pin-config-box");
            if (pinCheckbox.checked) {
                if (pinBox) pinBox.style.display = "block";
                const newPinInput = document.getElementById("cfg-new-pin");
                if (newPinInput) newPinInput.focus();
            } else {
                if (disablePinBtn && disablePinBtn.style.display !== "none") {
                    disablePinBtn.click();
                } else {
                    if (pinBox) pinBox.style.display = "none";
                }
            }
        });
    }

    // Salvar novo PIN
    if (savePinBtn) {
        savePinBtn.addEventListener("click", async () => {
            const pinInput = document.getElementById("cfg-new-pin");
            const pin = (pinInput ? pinInput.value : "").trim();
            if (!pin || pin.length < 4 || pin.length > 6 || !/^\d+$/.test(pin)) {
                showToast("O PIN deve conter entre 4 e 6 dígitos numéricos.", "error");
                return;
            }

            try {
                const res = await fetch("/api/security/pin/set", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ pin })
                });
                const data = await res.json();
                if (res.ok) {
                    showToast("PIN de segurança configurado com sucesso!", "success");
                    fetchConfig();
                } else {
                    showToast(`Erro ao gravar PIN: ${data.detail || "Erro"}`, "error");
                }
            } catch (err) {
                showToast("Erro ao conectar com o servidor.", "error");
            }
        });
    }

    // Desativar PIN
    if (disablePinBtn) {
        disablePinBtn.addEventListener("click", async () => {
            if (!confirm("Deseja realmente desativar o bloqueio por PIN?")) {
                if (pinCheckbox) pinCheckbox.checked = true;
                return;
            }

            try {
                const res = await fetch("/api/security/pin/disable", { method: "POST" });
                if (res.ok) {
                    showToast("Bloqueio por PIN desativado.", "info");
                    fetchConfig();
                } else {
                    showToast("Erro ao desativar PIN.", "error");
                }
            } catch (err) {
                showToast("Erro ao conectar com o servidor.", "error");
            }
        });
    }

    // Toggle de Acesso LAN
    if (lanToggle) {
        lanToggle.addEventListener("change", async () => {
            const allow_lan = lanToggle.checked;
            try {
                const res = await fetch("/api/security/lan/toggle", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ allow_lan })
                });
                const data = await res.json();
                if (res.ok) {
                    showToast(data.message || "Configuração de rede atualizada.", "info");
                    const lanStatusMsg = document.getElementById("cfg-lan-status-msg");
                    if (lanStatusMsg) {
                        lanStatusMsg.innerText = allow_lan 
                            ? "Acesso LAN ativo: Celular/tablet na mesma rede Wi-Fi podem acessar." 
                            : "Isolamento seguro ativo: Apenas este computador tem acesso às APIs e aos dados.";
                    }
                } else {
                    showToast("Erro ao alterar configuração de LAN.", "error");
                    lanToggle.checked = !allow_lan;
                }
            } catch (err) {
                showToast("Erro ao conectar com o servidor.", "error");
                lanToggle.checked = !allow_lan;
            }
        });
    }
}


// ==========================================================================
// GERENCIADOR DE PERFIS E MULTI-UID (ETAPA 6)
// ==========================================================================

const GAME_DISPLAY_CONFIG = {
    zzz: { name: "Zenless Zone Zero", icon: "/assets/zzz_icon.png", color: "#fbbf24", badge: "ZZZ" },
    genshin: { name: "Genshin Impact", icon: "/assets/genshin_icon.png", color: "#38bdf8", badge: "GENSHIN" },
    hsr: { name: "Honkai: Star Rail", icon: "/assets/hsr_icon.png", color: "#c084fc", badge: "HSR" }
};

window.loadAccountsManagement = async function(showFeedback = false) {
    try {
        const res = await fetch("/api/accounts");
        if (!res.ok) throw new Error("Falha ao buscar contas salvas");
        const data = await res.json();
        
        const accounts = Array.isArray(data) ? data : (data.accounts || []);
        const activeAccounts = data.active_accounts || {};

        // 1. Atualiza a Barra Rápida de Seleção de Perfis (Home)
        const quickSelect = document.getElementById("quick-profile-select");
        const quickInfo = document.getElementById("quick-profile-info");
        
        if (quickSelect) {
            quickSelect.innerHTML = "";
            if (accounts.length === 0) {
                quickSelect.innerHTML = '<option value="">Nenhuma conta sincronizada</option>';
            } else {
                // Agrupa por jogo
                const games = ["zzz", "genshin", "hsr"];
                games.forEach(gid => {
                    const gameAccs = accounts.filter(a => a.game_id === gid);
                    if (gameAccs.length > 0) {
                        const optGroup = document.createElement("optgroup");
                        const cfg = GAME_DISPLAY_CONFIG[gid] || { name: gid.toUpperCase() };
                        optGroup.label = cfg.name;
                        
                        gameAccs.forEach(acc => {
                            const opt = document.createElement("option");
                            opt.value = `${acc.game_id}:${acc.uid}`;
                            const isAct = (activeAccounts[gid] && String(activeAccounts[gid]) === String(acc.uid)) || acc.is_active;
                            const activeMark = isAct ? " ★ [Ativo]" : "";
                            opt.textContent = `${acc.nickname || 'Jogador'} (Nv.${acc.level || 1} • UID: ${acc.uid})${activeMark}`;
                            if (isAct) {
                                opt.selected = true;
                            }
                            optGroup.appendChild(opt);
                        });
                        quickSelect.appendChild(optGroup);
                    }
                });
            }
        }

        if (quickInfo) {
            const count = accounts.length;
            quickInfo.innerHTML = count > 0 
                ? `<span style="display: inline-flex; align-items: center; gap: 6px;"><i class="fa-solid fa-check-circle" style="color: #34d399;"></i> ${count} perfil${count > 1 ? 's' : ''} registrado${count > 1 ? 's' : ''}</span>`
                : `<span style="color: #94a3b8;"><i class="fa-solid fa-circle-info"></i> Sincronize seus cookies no cofre para importar contas</span>`;
        }

        // 2. Atualiza a Lista de Perfis no Painel de Configurações
        const cfgContainer = document.getElementById("cfg-accounts-list-container");
        if (cfgContainer) {
            if (accounts.length === 0) {
                cfgContainer.innerHTML = `
                    <div style="background: rgba(15, 23, 42, 0.4); border: 1px dashed rgba(255,255,255,0.15); border-radius: 12px; padding: 24px; text-align: center; color: var(--text-muted);">
                        <i class="fa-solid fa-users-slash" style="font-size: 28px; margin-bottom: 8px; color: #64748b; display: block;"></i>
                        <span style="font-size: 13px;">Nenhuma conta salva localmente ainda.</span>
                        <p style="font-size: 11px; margin: 4px 0 0 0;">Insira seus cookies HoYoLAB ou faça login automático para detectar seus perfis.</p>
                    </div>
                `;
            } else {
                let html = "";
                accounts.forEach(acc => {
                    const cfg = GAME_DISPLAY_CONFIG[acc.game_id] || { name: acc.game_id.toUpperCase(), icon: "/assets/logo.svg", color: "#38bdf8", badge: acc.game_id.toUpperCase() };
                    const isAct = (activeAccounts[acc.game_id] && String(activeAccounts[acc.game_id]) === String(acc.uid)) || acc.is_active;
                    
                    html += `
                        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid ${isAct ? 'rgba(56, 189, 248, 0.4)' : 'rgba(255,255,255,0.08)'}; border-radius: 12px; padding: 14px 18px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px; box-shadow: ${isAct ? '0 0 15px rgba(56, 189, 248, 0.15)' : 'none'};">
                            <div style="display: flex; align-items: center; gap: 14px;">
                                <div style="position: relative;">
                                    <img src="${cfg.icon}" alt="${cfg.name}" style="width: 42px; height: 42px; border-radius: 10px; object-fit: contain; background: rgba(0,0,0,0.3); padding: 4px; border: 1px solid rgba(255,255,255,0.1);">
                                    <span style="position: absolute; bottom: -4px; right: -4px; font-size: 9px; font-weight: 800; padding: 1px 4px; border-radius: 4px; background: ${cfg.color}; color: #000;">${cfg.badge}</span>
                                </div>
                                <div>
                                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                        <h4 style="margin: 0; font-size: 15px; color: #fff; font-weight: 700;">${acc.nickname || 'Jogador'}</h4>
                                        <span style="font-size: 11px; font-weight: 700; color: #fbbf24; background: rgba(251, 191, 36, 0.15); border: 1px solid rgba(251, 191, 36, 0.3); padding: 1px 6px; border-radius: 6px;">Nv. ${acc.level || 1}</span>
                                        ${isAct ? `<span style="font-size: 11px; font-weight: 700; color: #34d399; background: rgba(52, 211, 153, 0.15); border: 1px solid rgba(52, 211, 153, 0.35); padding: 1px 8px; border-radius: 10px; display: inline-flex; align-items: center; gap: 4px;"><i class="fa-solid fa-check"></i> Ativa</span>` : ''}
                                    </div>
                                    <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                                        <span><i class="fa-solid fa-id-badge" style="color: #94a3b8;"></i> UID: <strong>${acc.uid}</strong></span>
                                        <span><i class="fa-solid fa-users" style="color: #a855f7;"></i> ${acc.char_count || 0} Personagens (${acc.five_stars_count || 0} de 5★)</span>
                                        ${acc.active_days ? `<span><i class="fa-solid fa-calendar-day" style="color: #38bdf8;"></i> ${acc.active_days} dias ativos</span>` : ''}
                                    </div>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                                ${!isAct ? `
                                    <button onclick="window.switchActiveAccount('${acc.game_id}', '${acc.uid}')" class="primary-btn" style="padding: 6px 14px; font-size: 12px; background: linear-gradient(135deg, #0284c7, #38bdf8); border: none; border-radius: 8px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;">
                                        <i class="fa-solid fa-right-left"></i> Ativar Conta
                                    </button>
                                ` : `
                                    <button disabled style="padding: 6px 14px; font-size: 12px; background: rgba(52, 211, 153, 0.15); color: #34d399; border: 1px solid rgba(52, 211, 153, 0.3); border-radius: 8px; cursor: default; display: inline-flex; align-items: center; gap: 6px;">
                                        <i class="fa-solid fa-check"></i> Conta Ativa
                                    </button>
                                `}
                                <button onclick="window.deleteAccountProfile('${acc.uid}')" title="Remover perfil do SQLite local" class="secondary-btn" style="padding: 6px 10px; font-size: 12px; border-color: rgba(239, 68, 68, 0.4); color: #f87171; background: rgba(239, 68, 68, 0.08); border-radius: 8px; cursor: pointer;">
                                    <i class="fa-solid fa-trash-can"></i>
                                </button>
                            </div>
                        </div>
                    `;
                });
                cfgContainer.innerHTML = html;
            }
        }

        if (showFeedback && typeof showToast === "function") {
            showToast("Lista de contas e perfis atualizada com sucesso!", "success");
        }
    } catch (err) {
        console.error("Erro ao carregar perfis de contas:", err);
        if (showFeedback && typeof showToast === "function") {
            showToast("Erro ao carregar lista de perfis: " + err.message, "error");
        }
    }
};

window.handleQuickProfileSwitch = function(compositeVal) {
    if (!compositeVal || !compositeVal.includes(":")) return;
    const [gameId, uid] = compositeVal.split(":");
    window.switchActiveAccount(gameId, uid);
};

window.switchActiveAccount = async function(gameId, uid) {
    try {
        if (typeof showToast === "function") {
            showToast(`Alternando para perfil UID ${uid}...`, "info");
        }
        
        const res = await fetch("/api/accounts/switch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ game_id: gameId, uid: uid })
        });
        
        const json = await res.json();
        if (!res.ok) throw new Error(json.detail || "Erro ao alternar perfil");
        
        // Atualiza a interface completa
        await Promise.allSettled([
            loadOverview(),
            typeof loadRoster === "function" ? loadRoster(gameId) : Promise.resolve(),
            typeof loadEndgame === "function" ? loadEndgame(gameId) : Promise.resolve(),
            window.loadAccountsManagement(false)
        ]);

        if (typeof showToast === "function") {
            showToast(`Perfil ${uid} (${gameId.toUpperCase()}) ativado com sucesso!`, "success");
        }
    } catch (err) {
        console.error("Erro ao alternar perfil ativo:", err);
        if (typeof showToast === "function") {
            showToast("Falha ao alternar perfil: " + err.message, "error");
        }
    }
};

window.deleteAccountProfile = async function(uid) {
    if (!confirm(`Tem certeza que deseja excluir o perfil UID ${uid} do banco de dados local?\nIsso removerá os personagens e relíquias salvos deste perfil no SQLite.`)) {
        return;
    }

    try {
        const res = await fetch(`/api/accounts/${encodeURIComponent(uid)}`, {
            method: "DELETE"
        });
        const json = await res.json();
        if (!res.ok) throw new Error(json.detail || "Erro ao excluir perfil");

        await Promise.allSettled([
            loadOverview(),
            window.loadAccountsManagement(false)
        ]);

        if (typeof showToast === "function") {
            showToast(`Perfil UID ${uid} removido com sucesso.`, "success");
        }
    } catch (err) {
        console.error("Erro ao excluir perfil:", err);
        if (typeof showToast === "function") {
            showToast("Falha ao excluir perfil: " + err.message, "error");
        }
    }
};



// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
if (typeof GAME_DISPLAY_CONFIG !== 'undefined') window.GAME_DISPLAY_CONFIG = GAME_DISPLAY_CONFIG;
if (typeof fetchConfig !== 'undefined') window.fetchConfig = fetchConfig;
if (typeof setupConfigForm !== 'undefined') window.setupConfigForm = setupConfigForm;
if (typeof updateApiStatusIndicator !== 'undefined') window.updateApiStatusIndicator = updateApiStatusIndicator;