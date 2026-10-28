// ==========================================================================
// Módulo: chat_rag.js
// Cabeça de Droid - Vanilla ES6 Module
// ==========================================================================

// ==========================================================================
// ASSISTENTE DE CHAT IA RAG (GROQ ENGINE)
// ==========================================================================
function setupChatSystem() {
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("chat-send-btn");
    const messagesArea = document.getElementById("chat-messages");

    // Auto-ajuste de altura do Textarea
    chatInput.addEventListener("input", function() {
        this.style.height = "auto";
        this.style.height = (this.scrollHeight) + "px";
    });

    const triggerSend = async () => {
        const message = chatInput.value.trim();
        if (!message) return;
        
        chatInput.value = "";
        chatInput.style.height = "auto";
        
        // 1. Renderiza mensagem do usuário no Chat
        appendChatMessage("user", message);
        messagesArea.scrollTop = messagesArea.scrollHeight;
        
        // 2. Insere balão de "Pensando..."
        const typingId = appendChatMessage("assistant", `<div class="typing-loader"><span></span><span></span><span></span></div>`);
        messagesArea.scrollTop = messagesArea.scrollHeight;
        
        // 3. Monta o payload do histórico
        const contextSelect = document.getElementById("chat-context-select");
        const game_id = contextSelect.value;
        
        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message,
                    game_id,
                    history: chatHistory
                })
            });
            
            // Remove o balão de digitando
            document.getElementById(typingId).remove();
            
            if (!res.ok) {
                appendChatMessage("assistant", `<i class="fa-solid fa-circle-xmark" style="color: var(--color-danger); margin-right: 6px;"></i> Erro na API do Chat.`);
                messagesArea.scrollTop = messagesArea.scrollHeight;
                return;
            }
            
            // Cria um balão vazio para receber a resposta de forma incremental (streaming)
            const responseId = appendChatMessage("assistant", "");
            const responseEl = document.getElementById(responseId).querySelector(".msg-content");
            
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let rawText = "";
            let buffer = "";
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                // Salva a última linha incompleta de volta no buffer
                buffer = lines.pop();
                
                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const parsed = JSON.parse(line.substring(6));
                            if (parsed.token) {
                                rawText += parsed.token;
                                responseEl.innerHTML = marked.parse(rawText);
                                messagesArea.scrollTop = messagesArea.scrollHeight;
                            } else if (parsed.error) {
                                rawText += `\n\n<i class="fa-solid fa-circle-xmark" style="color: var(--color-danger); margin-right: 6px;"></i> Erro: ${parsed.error}`;
                                responseEl.innerHTML = marked.parse(rawText);
                            }
                        } catch (e) {
                            // Ignora erros parciais
                        }
                    }
                }
            }
            
            // Grava no histórico de memória
            chatHistory.push({ role: "user", text: message });
            chatHistory.push({ role: "model", text: rawText });
            
            // Limita histórico local para no máximo 10 mensagens
            if (chatHistory.length > 20) {
                chatHistory = chatHistory.slice(-20);
            }
            messagesArea.scrollTop = messagesArea.scrollHeight;
        } catch (err) {
            document.getElementById(typingId).remove();
            appendChatMessage("assistant", `<i class="fa-solid fa-circle-xmark" style="color: var(--color-danger); margin-right: 6px;"></i> Falha ao conectar ao processador Groq: ${err.message}`);
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }
    };

    sendBtn.addEventListener("click", triggerSend);
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            triggerSend();
        }
    });

    // ==========================================
    // PERSISTÊNCIA E LIMPEZA DO HISTÓRICO DO CHAT
    // ==========================================
    const contextSelect = document.getElementById("chat-context-select");
    const clearHistoryBtn = document.getElementById("btn-clear-chat-history");

    const defaultWelcomeHTML = `
        <div class="chat-msg assistant">
            <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="msg-content">
                <p>Olá! Eu sou o assistente de IA integrado com o seu banco de dados local da HoYoLAB, Prydwen e KQM. Como posso te ajudar hoje?</p>
                <ul>
                    <li><em>"Qual time de HSR você me sugere com o que eu tenho no Roster?"</em></li>
                    <li><em>"Com base nos meus artefatos de Genshin, como posso melhorar o meu dano?"</em></li>
                    <li><em>"Quais são os melhores discos para o agente que escolhi no ZZZ?"</em></li>
                </ul>
            </div>
        </div>
    `;

    const loadPersistedChatHistory = async (gameId) => {
        try {
            const res = await fetch(`/api/chat/history/${encodeURIComponent(gameId || 'todos')}`);
            if (!res.ok) return;
            const data = await res.json();
            const messages = data.messages || [];

            messagesArea.innerHTML = "";
            chatHistory = [];

            if (messages.length === 0) {
                messagesArea.innerHTML = defaultWelcomeHTML;
            } else {
                messages.forEach(m => {
                    const role = m.role === "assistant" ? "assistant" : "user";
                    const content = role === "assistant" && typeof marked !== "undefined" ? marked.parse(m.content) : m.content;
                    appendChatMessage(role, content);
                    chatHistory.push({
                        role: role === "assistant" ? "model" : "user",
                        text: m.content
                    });
                });
                if (chatHistory.length > 20) {
                    chatHistory = chatHistory.slice(-20);
                }
            }
            messagesArea.scrollTop = messagesArea.scrollHeight;
        } catch (e) {
            console.warn("[CHAT] Erro ao carregar histórico persistido:", e);
        }
    };

    if (contextSelect) {
        contextSelect.addEventListener("change", (e) => {
            loadPersistedChatHistory(e.target.value);
        });
    }

    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener("click", async () => {
            const currentGame = contextSelect ? contextSelect.value : "todos";
            const confirmMsg = currentGame === "todos" 
                ? "Deseja apagar TODO o histórico global de conversas com a IA?" 
                : `Deseja apagar o histórico de conversas do ${currentGame.toUpperCase()}?`;
            
            if (!confirm(confirmMsg)) return;

            try {
                const res = await fetch(`/api/chat/history/${encodeURIComponent(currentGame)}`, {
                    method: "DELETE"
                });
                if (res.ok) {
                    chatHistory = [];
                    messagesArea.innerHTML = defaultWelcomeHTML;
                    showToast("Histórico de conversa apagado com sucesso!", "success");
                } else {
                    showToast("Falha ao apagar histórico.", "error");
                }
            } catch (err) {
                showToast("Erro de rede ao apagar histórico.", "error");
            }
        });
    }

    // Carrega o histórico na inicialização com o contexto atual
    if (contextSelect) {
        loadPersistedChatHistory(contextSelect.value);
    }

    // ==========================================
    // CONFIGURAÇÃO DO MONTADOR DE TIMES (TEAM BUILDER)
    // ==========================================
    const teamGameSelect = document.getElementById("team-game-select");
    const teamAnalyzeBtn = document.getElementById("team-analyze-btn");
    
    if (teamGameSelect) {
        teamGameSelect.addEventListener("change", (e) => {
            updateTeamBuilderGrid(e.target.value);
        });
        
        // Inicializa com o valor padrão do select após carregamento
        setTimeout(() => {
            updateTeamBuilderGrid(teamGameSelect.value);
        }, 1500);
    }
    
    if (teamAnalyzeBtn) {
        teamAnalyzeBtn.addEventListener("click", async () => {
            if (selectedTeam.length === 0) return;
            const gameId = teamGameSelect.value;
            const message = `Análise do Time: ${selectedTeam.join(", ")}`;
            
            appendChatMessage("user", `Fazer análise de sinergia da equipe: **${selectedTeam.join(", ")}**`);
            messagesArea.scrollTop = messagesArea.scrollHeight;
            
            const typingId = appendChatMessage("assistant", `<div class="typing-loader"><span></span><span></span><span></span></div>`);
            messagesArea.scrollTop = messagesArea.scrollHeight;
            
            try {
                const res = await fetch("/api/team/analyze", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        game_id: gameId,
                        characters: selectedTeam
                    })
                });
                
                document.getElementById(typingId).remove();
                
                if (!res.ok) {
                    appendChatMessage("assistant", `<i class="fa-solid fa-circle-xmark" style="color: var(--color-danger); margin-right: 6px;"></i> Erro ao analisar sinergia.`);
                    messagesArea.scrollTop = messagesArea.scrollHeight;
                    return;
                }
                
                const responseId = appendChatMessage("assistant", "");
                const responseEl = document.getElementById(responseId).querySelector(".msg-content");
                
                const reader = res.body.getReader();
                const decoder = new TextDecoder();
                let rawText = "";
                let buffer = "";
                
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
                                    rawText += parsed.token;
                                    responseEl.innerHTML = marked.parse(rawText);
                                    messagesArea.scrollTop = messagesArea.scrollHeight;
                                } else if (parsed.error) {
                                    rawText += `\n\n<i class="fa-solid fa-circle-xmark" style="color: var(--color-danger); margin-right: 6px;"></i> Erro: ${parsed.error}`;
                                    responseEl.innerHTML = marked.parse(rawText);
                                }
                            } catch (e) {}
                        }
                    }
                }
                
                chatHistory.push({ role: "user", text: message });
                chatHistory.push({ role: "model", text: rawText });
                
            } catch (err) {
                document.getElementById(typingId).remove();
                appendChatMessage("assistant", `<i class="fa-solid fa-circle-xmark" style="color: var(--color-danger); margin-right: 6px;"></i> Erro ao processar: ${err.message}`);
                messagesArea.scrollTop = messagesArea.scrollHeight;
            }
        });
    }
}

// Funções globais auxiliares do Montador de Times (Chat IA)
let selectedTeam = [];

function updateTeamBuilderGrid(gameId) {
    const grid = document.getElementById("team-characters-grid");
    if (!grid) return;
    
    selectedTeam = [];
    const btn = document.getElementById("team-analyze-btn");
    if (btn) btn.disabled = true;
    
    const roster = (window.globalRoster && window.globalRoster[gameId]) || globalRoster[gameId] || [];
    if (roster.length === 0) {
        grid.innerHTML = `<div style="grid-column: span 4; font-size: 10px; color: var(--text-secondary); text-align: center; padding: 12px;">Roster do ${gameId.toUpperCase()} não sincronizado.</div>`;
        return;
    }
    
    grid.innerHTML = roster.map(char => {
        const defaultFallback = `/assets/${gameId}_icon.png`;
        const avatarSrc = char.icon || defaultFallback;
        const safeDataName = (char.name || "").replace(/"/g, "&quot;");
        return `
            <div class="team-char-select-card" data-name="${safeDataName}" style="position: relative; aspect-ratio: 1; cursor: pointer; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06); overflow: hidden; background: rgba(0,0,0,0.3); transition: all 0.2s;" onclick="window.toggleChatTeamCharacter(this, this.dataset.name, '${gameId}')">
                <img src="${avatarSrc}" onerror="this.onerror=null; this.src='${defaultFallback}';" style="width: 100%; height: 100%; object-fit: cover;" alt="${safeDataName}">
                <div class="char-select-overlay" style="position: absolute; inset: 0; background: rgba(167, 139, 250, 0.45); display: none; align-items: center; justify-content: center; font-size: 14px; color: #fff; text-shadow: 0 1px 3px rgba(0,0,0,0.5);">
                    <i class="fa-solid fa-check"></i>
                </div>
                <div class="char-select-name" style="position: absolute; bottom: 0; left: 0; right: 0; font-size: 8px; background: rgba(0,0,0,0.85); color: #fff; text-align: center; padding: 2px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 500;">${char.name}</div>
            </div>
        `;
    }).join('');
}

function toggleChatTeamCharacter(element, charName, gameId) {
    if (!element || typeof element.querySelector !== "function") return;
    const overlay = element.querySelector(".char-select-overlay");
    const maxSelect = gameId === "zzz" ? 3 : 4;
    
    if (selectedTeam.includes(charName)) {
        selectedTeam = selectedTeam.filter(name => name !== charName);
        element.style.borderColor = "rgba(255,255,255,0.06)";
        element.style.boxShadow = "none";
        if (overlay) overlay.style.display = "none";
    } else {
        if (selectedTeam.length >= maxSelect) {
            alert(`Você só pode selecionar até ${maxSelect} personagens para o time de ${gameId.toUpperCase()}!`);
            return;
        }
        selectedTeam.push(charName);
        element.style.borderColor = "#a78bfa";
        element.style.boxShadow = "0 0 8px rgba(167, 139, 250, 0.3)";
        if (overlay) overlay.style.display = "flex";
    }
    
    const btn = document.getElementById("team-analyze-btn");
    if (btn) btn.disabled = selectedTeam.length === 0;
}
window.toggleChatTeamCharacter = toggleChatTeamCharacter;

function appendChatMessage(role, content) {
    const messagesArea = document.getElementById("chat-messages");
    const msgDiv = document.createElement("div");
    const msgId = "msg-" + Math.random().toString(36).substr(2, 9);
    
    msgDiv.id = msgId;
    msgDiv.className = `chat-msg ${role}`;
    
    const avatar = role === "user" 
        ? '<i class="fa-solid fa-user"></i>' 
        : '<i class="fa-solid fa-robot"></i>';
    
    msgDiv.innerHTML = `
        <div class="msg-avatar">${avatar}</div>
        <div class="msg-content">${content}</div>
    `;
    
    messagesArea.appendChild(msgDiv);
    return msgId;
}


// ==========================================================================
// SISTEMA DE MONTAGEM E EXPORTAÇÃO DE CARD DE TIME & BUILDS (GLASSMORPHISM)
// ==========================================================================

const teamBuilderState = {
    genshin: {
        teamName: "Hypercarry Mavuika Overvape",
        members: []
    },
    hsr: {
        teamName: "Acheron Nihility Supreme",
        members: []
    },
    zzz: {
        teamName: "Section 6 Disorder Anomaly",
        members: []
    }
};

// Limites estritos de cada jogo
const TEAM_MAX_MEMBERS = {
    genshin: 4,
    hsr: 4,
    zzz: 3
};

// 1. Alterna personagem no time (compatível tanto com Montar Card de Time quanto com Chat IA)
function toggleCharacterInTeam(arg1, arg2, arg3) {
    // Se o primeiro argumento for um elemento DOM, veio do seletor lateral do Chat IA: (element, charName, gameId)
    if (arg1 && typeof arg1 === "object" && typeof arg1.querySelector === "function") {
        return toggleChatTeamCharacter(arg1, arg2, arg3);
    }

    const gameId = String(arg1 || "").toLowerCase().trim();
    const charName = String(arg2 || "").trim();
    if (!gameId || !charName) return;

    const roster = (window.globalRoster && window.globalRoster[gameId]) || (typeof globalRoster !== "undefined" ? globalRoster[gameId] : []) || [];
    const char = roster.find(c => c.name === charName || (c.name || "").trim() === charName);
    if (!char) return;

    const team = teamBuilderState[gameId];
    if (!team) return;

    const maxSlots = TEAM_MAX_MEMBERS[gameId] || 4;
    const existingIdx = team.members.findIndex(m => m.name === char.name);

    if (existingIdx !== -1) {
        team.members.splice(existingIdx, 1);
        if (typeof showToast === "function") {
            showToast(`${char.name} removido do time.`, "info");
        }
    } else {
        if (team.members.length >= maxSlots) {
            if (typeof showToast === "function") {
                showToast(`Limite de ${maxSlots} slots para ${gameId.toUpperCase()} atingido! Remova um personagem para adicionar outro.`, "warning");
            }
            return;
        }
        team.members.push(char);
        if (typeof showToast === "function") {
            showToast(`${char.name} adicionado ao time (#${team.members.length})!`, "success");
        }
        ensureCharacterBuildData(gameId, char);
    }

    updateTeamUI(gameId);
}
window.toggleCharacterInTeam = toggleCharacterInTeam;

// 2. Remove membro do time por índice de slot
window.removeTeamMember = function(gameId, slotIndex) {
    const team = teamBuilderState[gameId];
    if (!team || !team.members[slotIndex]) return;

    const removed = team.members.splice(slotIndex, 1);
    if (removed.length > 0 && typeof showToast === "function") {
        showToast(`${removed[0].name} removido do time.`, "info");
    }
    updateTeamUI(gameId);
};

// 3. Limpa o time inteiro
window.clearTeam = function(gameId) {
    const team = teamBuilderState[gameId];
    if (!team) return;
    team.members = [];
    if (typeof showToast === "function") {
        showToast("Time esvaziado com sucesso.", "info");
    }
    updateTeamUI(gameId);
};

// 4. Atualiza o nome do time digitado no input
window.updateTeamName = function(gameId, newTitle) {
    const team = teamBuilderState[gameId];
    if (!team) return;
    team.teamName = newTitle || "Composição Personalizada";
    const titleEl = document.getElementById(`team-title-display-${gameId}`);
    if (titleEl) {
        titleEl.textContent = team.teamName;
    }
};

// 5. Filtra a grade visual de avatares obtidos
window.filterTeamRoster = function(gameId, query) {
    const q = (query || "").toLowerCase().trim();
    const items = document.querySelectorAll(`#team-roster-grid-${gameId} .team-picker-item`);
    items.forEach(el => {
        const name = (el.dataset.name || "").toLowerCase();
        if (!q || name.includes(q)) {
            el.style.display = "flex";
        } else {
            el.style.display = "none";
        }
    });
};

// 6. Garante carregamento das informações detalhadas de build caso necessário
async function ensureCharacterBuildData(gameId, char) {
    if (char._buildLoaded) return;
    try {
        const res = await fetch(`/api/build/${gameId}/${encodeURIComponent(char.name)}`);
        if (res.ok) {
            const b = await res.json();
            if (b) {
                if (b.stats && Object.keys(b.stats).length > 0) char.stats = b.stats;
                if (b.sets && b.sets.length > 0) char.sets = b.sets;
                if (b.pieces && b.pieces.length > 0) char.relics = b.pieces;
                if (b.weapon && typeof b.weapon === "object") char.weapon = b.weapon;
            }
        }
    } catch (err) {
        console.warn("Erro ao buscar detalhes de build:", err);
    } finally {
        char._buildLoaded = true;
        renderTeamExportCard(gameId);
    }
}

// 7. Atualiza toda a interface em tempo real
function updateTeamUI(gameId) {
    const team = teamBuilderState[gameId];
    if (!team) return;

    const maxSlots = TEAM_MAX_MEMBERS[gameId] || 4;
    const currentCount = team.members.length;

    // Atualiza contadores
    const badgeSubnav = document.getElementById(`team-badge-count-${gameId}`);
    if (badgeSubnav) badgeSubnav.textContent = `${currentCount}/${maxSlots}`;

    const counterPanel = document.getElementById(`team-counter-${gameId}`);
    if (counterPanel) counterPanel.textContent = `${currentCount} / ${maxSlots}`;

    // Atualiza badges e classes na grade de avatares do seletor
    const pickerItems = document.querySelectorAll(`#team-roster-grid-${gameId} .team-picker-item`);
    pickerItems.forEach(item => {
        const cName = item.dataset.name;
        const idx = team.members.findIndex(m => m.name === cName);
        const existingBadge = item.querySelector(".team-picker-pos-badge");
        if (idx !== -1) {
            item.classList.add("in-team");
            if (existingBadge) {
                existingBadge.textContent = idx + 1;
            } else {
                const badge = document.createElement("div");
                badge.className = "team-picker-pos-badge";
                badge.textContent = idx + 1;
                item.appendChild(badge);
            }
        } else {
            item.classList.remove("in-team");
            if (existingBadge) existingBadge.remove();
        }
    });

    // Atualiza badges e bordas na galeria principal se estiver renderizada
    const galleryCards = document.querySelectorAll(`#gallery-${gameId} .char-card`);
    galleryCards.forEach(card => {
        const nameEl = card.querySelector(".char-name");
        if (!nameEl) return;
        const cName = nameEl.innerText.trim();
        const idx = team.members.findIndex(m => m.name === cName);
        const existingBadge = card.querySelector(".gallery-team-badge");
        if (idx !== -1) {
            card.classList.add("in-team-selected");
            if (existingBadge) {
                existingBadge.innerHTML = `<i class="fa-solid fa-users"></i> #${idx + 1}`;
            } else {
                const b = document.createElement("div");
                b.className = "gallery-team-badge";
                b.innerHTML = `<i class="fa-solid fa-users"></i> #${idx + 1}`;
                const avBox = card.querySelector(".char-avatar-container");
                if (avBox) avBox.appendChild(b);
            }
        } else {
            card.classList.remove("in-team-selected");
            if (existingBadge) existingBadge.remove();
        }
    });

    // Renderiza o Card Exportável
    renderTeamExportCard(gameId);
}

// 8. Renderiza a Grade de Avatares Obtidos
window.renderTeamRosterSelector = function(gameId) {
    const container = document.getElementById(`team-roster-grid-${gameId}`);
    if (!container) return;

    const roster = (window.globalRoster && window.globalRoster[gameId]) || (typeof globalRoster !== "undefined" ? globalRoster[gameId] : []) || [];
    if (roster.length === 0) {
        container.innerHTML = `<div style="padding: 12px; color: var(--text-muted); font-size: 12px;">Carregando elenco sincronizado...</div>`;
        fetch(`/api/roster/${gameId}`)
            .then(res => res.ok ? res.json() : [])
            .then(data => {
                if (Array.isArray(data) && data.length > 0) {
                    if (!window.globalRoster) window.globalRoster = {};
                    window.globalRoster[gameId] = data;
                    if (typeof globalRoster !== "undefined") globalRoster[gameId] = data;
                    window.renderTeamRosterSelector(gameId);
                    updateTeamUI(gameId);
                } else {
                    container.innerHTML = `<div style="padding: 12px; color: var(--text-muted); font-size: 12px;">Nenhum personagem carregado. Sincronize a conta acima.</div>`;
                }
            })
            .catch(() => {
                container.innerHTML = `<div style="padding: 12px; color: var(--text-muted); font-size: 12px;">Nenhum personagem carregado. Sincronize a conta acima.</div>`;
            });
        return;
    }

    const team = teamBuilderState[gameId] || { members: [] };

    container.innerHTML = roster.map(char => {
        const teamIdx = team.members.findIndex(m => m.name === char.name);
        const inTeam = teamIdx !== -1;
        const rarityNum = Number(char.rarity);
        const isFiveStar = rarityNum === 5 || char.rarity === "5" || String(char.rarity).toUpperCase() === "S";
        const rarityClass = isFiveStar ? "rarity-5" : "rarity-4";
        const defaultFallback = `/assets/${gameId}_icon.png`;
        const avatarSrc = char.icon || defaultFallback;
        const elemKey = (char.element || "").toLowerCase();
        const elemIconUrl = `/assets/elements/${gameId}_${elemKey}.png`;
        const safeDataName = String(char.name || "").replace(/"/g, "&quot;");

        return `
            <div class="team-picker-item ${inTeam ? 'in-team' : ''}" data-name="${safeDataName}" onclick="window.toggleCharacterInTeam('${gameId}', this.dataset.name)">
                <div class="team-picker-avatar-box ${rarityClass}">
                    <img class="team-picker-avatar-img" src="${avatarSrc}" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='${defaultFallback}';" alt="${safeDataName}">
                    <img class="team-picker-elem-icon" src="${elemIconUrl}" loading="lazy" decoding="async" onerror="this.style.display='none';" alt="">
                </div>
                ${inTeam ? `<div class="team-picker-pos-badge">${teamIdx + 1}</div>` : ''}
                <span class="team-picker-name" title="${safeDataName}">${char.name}</span>
                <span class="team-picker-rank">${char.rank_str || 'C0'} • Nv.${char.level}</span>
            </div>
        `;
    }).join("");
};

// 9. Extração Inteligente de 8 Atributos Finais (Grid 2x4)
function extractTeamCardStats(gameId, char) {
    const raw = char.stats || {};
    const findStat = (candidates, fallback = "-") => {
        for (const cand of candidates) {
            for (const [k, v] of Object.entries(raw)) {
                if (k.toLowerCase().trim() === cand.toLowerCase().trim()) return v;
            }
        }
        for (const cand of candidates) {
            for (const [k, v] of Object.entries(raw)) {
                if (k.toLowerCase().includes(cand.toLowerCase())) return v;
            }
        }
        return fallback;
    };

    if (gameId === "genshin") {
        let elemBonusLabel = "Dano Elem";
        let elemBonusVal = "-";
        for (const [k, v] of Object.entries(raw)) {
            const lk = k.toLowerCase();
            if (lk.includes("bônus de cura") || lk.includes("cura")) {
                elemBonusLabel = "Cura";
                elemBonusVal = v;
                break;
            }
            if (lk.includes("bônus de dano")) {
                if (lk.includes("pyro")) elemBonusLabel = "D. Pyro";
                else if (lk.includes("hydro")) elemBonusLabel = "D. Hydro";
                else if (lk.includes("cryo")) elemBonusLabel = "D. Cryo";
                else if (lk.includes("electro")) elemBonusLabel = "D. Electro";
                else if (lk.includes("anemo")) elemBonusLabel = "D. Anemo";
                else if (lk.includes("geo")) elemBonusLabel = "D. Geo";
                else if (lk.includes("dendro")) elemBonusLabel = "D. Dendro";
                else if (lk.includes("físico")) elemBonusLabel = "D. Físico";
                else elemBonusLabel = "Dano Elem";
                elemBonusVal = v;
                break;
            }
        }
        if (elemBonusVal === "-") {
            elemBonusVal = findStat(["Dano Elem", "Bônus de Dano Elemental", "Bônus de Dano Físico"], "0.0%");
        }

        return [
            { label: "Vida", val: findStat(["Vida Máxima", "Vida", "PV"], "0") },
            { label: "ATQ", val: findStat(["ATQ", "Ataque"], "0"), highlight: true },
            { label: "DEF", val: findStat(["DEF", "Defesa"], "0") },
            { label: "EM", val: findStat(["Proficiência Elemental", "Proficiência Elementar", "EM"], "0") },
            { label: "Tx. CR", val: findStat(["Taxa Crítica", "Taxa CRIT", "Taxa"], "5.0%"), crit: true },
            { label: "Dano CR", val: findStat(["Dano Crítico", "Dano CRIT", "Dano"], "50.0%"), crit: true },
            { label: "Recarga", val: findStat(["Recarga de Energia", "Recarga", "ER"], "100.0%"), highlight: true },
            { label: elemBonusLabel, val: elemBonusVal, highlight: true }
        ];
    } else if (gameId === "hsr") {
        return [
            { label: "Vida", val: findStat(["PV", "Vida Máxima", "Vida", "HP"], "0") },
            { label: "ATQ", val: findStat(["ATQ", "Ataque", "ATK"], "0"), highlight: true },
            { label: "DEF", val: findStat(["DEF", "Defesa"], "0") },
            { label: "VEL", val: findStat(["VEL", "Velocidade", "SPD"], "0"), highlight: true },
            { label: "Tx. CR", val: findStat(["Taxa CRIT", "Taxa Crítica", "Taxa", "CRIT Rate"], "5.0%"), crit: true },
            { label: "Dano CR", val: findStat(["Dano CRIT", "Dano Crítico", "Dano", "CRIT DMG"], "50.0%"), crit: true },
            { label: "Quebra", val: findStat(["Quebra", "Efeito de Quebra", "Break Effect"], "0.0%") },
            { label: "EHR / ERR", val: findStat(["Acerto Efeito", "Taxa de Acerto de Efeito", "Regen. Energia", "Taxa de Regeneração de Energia"], "0.0%"), highlight: true }
        ];
    } else if (gameId === "zzz") {
        return [
            { label: "Vida", val: findStat(["PV", "Vida", "HP"], "0") },
            { label: "ATQ", val: findStat(["ATQ", "Ataque", "ATK"], "0"), highlight: true },
            { label: "DEF", val: findStat(["DEF", "Defesa"], "0") },
            { label: "Impacto", val: findStat(["Impacto", "Impactoo", "Impact"], "0"), highlight: true },
            { label: "Tx. CR", val: findStat(["Taxa CRIT", "Taxa Crítica", "CRIT Rate"], "5.0%"), crit: true },
            { label: "Dano CR", val: findStat(["Dano CRIT", "Dano Crítico", "CRIT DMG"], "50.0%"), crit: true },
            { label: "Prof. Anom", val: findStat(["Prof. Anomalia", "Proficiência de Anomalia", "Anomaly Proficiency"], "0"), highlight: true },
            { label: "PEN / Recup", val: findStat(["Perfuração", "Taxa de Perfuração", "Recup. Energia", "Recuperação de Energia"], "0"), highlight: true }
        ];
    }
    return [];
}

// 10. Extração de Equipamento Real
function extractTeamCardWeapon(gameId, char) {
    const w = char.weapon || {};
    const wName = typeof w === "string" ? w : (w.name || "Não equipado");
    const wLvl = typeof w === "object" ? (w.level || (gameId === "genshin" ? 90 : (gameId === "hsr" ? 80 : 60))) : 90;
    const rawRank = typeof w === "object" ? (w.rank || 1) : 1;
    let rankPrefix = "R";
    if (gameId === "hsr") rankPrefix = "S";
    if (gameId === "zzz") rankPrefix = "★";

    const safeWFn = getSafeFileName(wName);
    const cachedPath = `/assets/weapons/${gameId}/${safeWFn}`;
    const iconUrl = (typeof w === "object" && w.icon) ? w.icon : cachedPath;

    return {
        name: wName,
        level: `Nv. ${wLvl}`,
        refine: `${rankPrefix}${rawRank}`,
        icon: iconUrl
    };
}

// Helper para obter a Splash Art vertical completa em alta definição para o Card de Time
function getCharacterSplashArt(gameId, char) {
    if (!char) return `/assets/${gameId}_icon.png`;

    const proxyUrl = (url) => {
        if (!url || typeof url !== "string") return null;
        if (url.startsWith("/api/proxy_image") || url.startsWith("/assets/") || url.startsWith("data:")) return url;
        if (url.startsWith("http")) return `/api/proxy_image?url=${encodeURIComponent(url)}`;
        return url;
    };

    // 1. Splash / Gacha / Portrait já presente no objeto do personagem (populado pelo backend)
    const directArt = char.splash_art || char.gacha_art || char.portrait || char.draw || char.art_url;
    if (directArt && directArt !== "None" && typeof directArt === "string" && directArt.length > 5) {
        return proxyUrl(directArt);
    }

    // 2. Resoluções específicas por jogo
    if (gameId === 'hsr') {
        const charId = char.id || char.character_id;
        if (charId) {
            return proxyUrl(`https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/character_portrait/${charId}.png`);
        }
    } else if (gameId === 'zzz') {
        if (typeof getZzzPrydwenSlug === 'function') {
            const slug = getZzzPrydwenSlug(char.name);
            if (slug) {
                return proxyUrl(`https://cdn.prydwen.gg/images/zenless-zone-zero/characters/${slug}_full.webp`);
            }
        }
    } else if (gameId === 'genshin') {
        if (char.icon && char.icon.includes("UI_AvatarIcon_")) {
            const rawGacha = char.icon.replace("UI_AvatarIcon_", "UI_Gacha_AvatarImg_");
            return proxyUrl(rawGacha);
        }
    }

    // 3. Fallback inteligente via getWishCharacterSplash
    if (typeof getWishCharacterSplash === "function") {
        const wishArt = getWishCharacterSplash(gameId, char.name);
        if (wishArt && !wishArt.includes("logo.svg")) {
            return proxyUrl(wishArt);
        }
    }

    return proxyUrl(char.icon) || `/assets/${gameId}_icon.png`;
}

// 11. Extração de Conjuntos, Ícones Representativos e Atributos Principais
function extractTeamCardRelics(gameId, char) {
    const relics = char.relics || char.artifacts || char.discs || char.pieces || [];
    let rawSets = char.sets || [];

    // Filtra e formata sets excluindo 1 peça avulsa e padronizando notação concisa (4p / 2p)
    let validSets = [];
    if (rawSets && rawSets.length > 0) {
        rawSets.forEach(s => {
            const str = String(s).trim();
            // Ignora peças avulsas de 1 peça (não formam conjunto ativo)
            if (/\(1\s*[^)]*\)/i.test(str) || /^1x\s+/i.test(str)) {
                return;
            }
            let clean = str.replace(/\s*\(([24])\s*[^)]*\)/i, ' ($1p)');
            clean = clean.replace(/^([24])x\s+/i, '$1p ');
            validSets.push(clean.trim());
        });
    }

    if (validSets.length === 0 && relics && relics.length > 0) {
        const counts = {};
        relics.forEach(r => {
            let sName = r.set_name || r.name;
            if (sName) {
                sName = sName.replace(/\s*\[\d+\]$/, '').replace(/\s+\d+$/, '').trim();
                counts[sName] = (counts[sName] || 0) + 1;
            }
        });
        for (const [k, count] of Object.entries(counts)) {
            if (count >= 4) validSets.push(`${k} (4p)`);
            else if (count >= 2) validSets.push(`${k} (2p)`);
        }
    }

    const setLines = validSets.length > 0 ? validSets.slice(0, 2) : ["Sem conjunto ativo"];
    const setTitle = setLines.join(" + ");

    const proxyIcon = (url) => {
        if (!url || typeof url !== "string") return null;
        if (url.startsWith("/api/proxy_image") || url.startsWith("/assets/") || url.startsWith("data:")) return url;
        if (url.startsWith("http")) return `/api/proxy_image?url=${encodeURIComponent(url)}`;
        return url;
    };

    // Extração do ícone representativo do set
    const setIcons = [];
    if (relics.length > 0) {
        if (gameId === "hsr") {
            const head = relics.find(r => String(r.slot).toLowerCase().includes("cabeça") || r.slot === "1" || r.slot === 1) || relics[0];
            const sphere = relics.find(r => String(r.slot).toLowerCase().includes("esfera") || r.slot === "5" || r.slot === 5);
            if (head && head.icon) setIcons.push(proxyIcon(head.icon));
            if (sphere && sphere.icon && sphere.icon !== (head && head.icon)) setIcons.push(proxyIcon(sphere.icon));
        } else if (gameId === "genshin") {
            const flower = relics.find(r => r.slot === "1" || r.slot === 1 || String(r.slot).toLowerCase().includes("flor")) || relics[0];
            if (flower && flower.icon) setIcons.push(proxyIcon(flower.icon));
            if (setLines.length > 1) {
                const other = relics.find(r => r.icon && r.icon !== (flower && flower.icon));
                if (other && other.icon) setIcons.push(proxyIcon(other.icon));
            }
        } else if (gameId === "zzz") {
            const d1 = relics.find(r => String(r.slot).includes("1")) || relics[0];
            const d5 = relics.find(r => String(r.slot).includes("5"));
            if (d1 && d1.icon) setIcons.push(proxyIcon(d1.icon));
            if (d5 && d5.icon && d5.icon !== (d1 && d1.icon)) setIcons.push(proxyIcon(d5.icon));
        }

        if (setIcons.length === 0) {
            const first = relics.find(r => r.icon);
            if (first && first.icon) setIcons.push(proxyIcon(first.icon));
        }
    }
    const setIcon = setIcons.length > 0 ? setIcons[0] : null;

    const cleanChipStat = (raw) => {
        if (!raw) return "-";
        let s = String(raw).trim();
        const hasPct = s.includes("%");
        s = s.replace(/\s*\([^)]*\)/g, "").trim();
        s = sanitizeStatName(s);
        s = s.replace(/Taxa CRIT/i, "Taxa").replace(/Dano CRIT/i, "Dano");
        s = s.replace(/Recarga de Energia/i, "Recarga").replace(/Bônus de Cura/i, "Cura");
        s = s.replace(/Bônus de Dano ([A-Za-zÀ-ÿ]+)/i, "D. $1");
        if (hasPct && !s.includes("%")) s += "%";
        return s;
    };

    const chips = [];
    if (gameId === "genshin") {
        const sands = relics.find(r => r.slot === "3" || r.slot === "areia" || String(r.name).toLowerCase().includes("areia"));
        const goblet = relics.find(r => r.slot === "4" || r.slot === "calice" || r.slot === "cálice" || r.slot === "copo");
        const circlet = relics.find(r => r.slot === "5" || r.slot === "tiara" || r.slot === "coroa");
        chips.push({ slot: "A", val: cleanChipStat(sands ? sands.main : "ATQ%") });
        chips.push({ slot: "C", val: cleanChipStat(goblet ? goblet.main : "Dano Elem") });
        chips.push({ slot: "T", val: cleanChipStat(circlet ? circlet.main : "CRIT") });
    } else if (gameId === "hsr") {
        const body = relics.find(r => String(r.slot).toLowerCase().includes("corpo") || r.slot === "3");
        const feet = relics.find(r => String(r.slot).toLowerCase().includes("pés") || String(r.slot).toLowerCase().includes("bota") || r.slot === "4");
        const sphere = relics.find(r => String(r.slot).toLowerCase().includes("esfera") || r.slot === "5");
        const rope = relics.find(r => String(r.slot).toLowerCase().includes("corda") || r.slot === "6");
        chips.push({ slot: "C", val: cleanChipStat(body ? body.main : "CRIT") });
        chips.push({ slot: "P", val: cleanChipStat(feet ? feet.main : "VEL") });
        chips.push({ slot: "E", val: cleanChipStat(sphere ? sphere.main : "Dano Elem") });
        chips.push({ slot: "L", val: cleanChipStat(rope ? rope.main : "ERR/ATQ") });
    } else if (gameId === "zzz") {
        const d4 = relics.find(r => String(r.slot).includes("4"));
        const d5 = relics.find(r => String(r.slot).includes("5"));
        const d6 = relics.find(r => String(r.slot).includes("6"));
        chips.push({ slot: "4", val: cleanChipStat(d4 ? d4.main : "CRIT/ATQ") });
        chips.push({ slot: "5", val: cleanChipStat(d5 ? d5.main : "Dano Elem") });
        chips.push({ slot: "6", val: cleanChipStat(d6 ? d6.main : "Anomalia/ER") });
    }

    return { setTitle, setLines, setIcon, setIcons, chips };
}

// 12. Renderiza o Card de Time Exportável (1200px Glassmorphism)
function renderTeamExportCard(gameId) {
    const cardContainer = document.getElementById(`team-export-card-${gameId}`);
    if (!cardContainer) return;

    const team = teamBuilderState[gameId] || { teamName: "Time", members: [] };
    const maxSlots = TEAM_MAX_MEMBERS[gameId] || 4;
    const isThreeCol = maxSlots === 3;

    // Detecta elemento predominante
    const elemFreq = {};
    team.members.forEach(m => {
        const el = (m.element || "Neutro").toUpperCase();
        elemFreq[el] = (elemFreq[el] || 0) + 1;
    });
    let predElem = "EQUILIBRADO";
    let maxCount = 0;
    for (const [el, cnt] of Object.entries(elemFreq)) {
        if (cnt > maxCount) {
            maxCount = cnt;
            predElem = el;
        }
    }
    const elemTagText = maxCount >= 2 ? `RESSONÂNCIA ${predElem}` : `${predElem} FOCUS`;

    // Resumo de Pity / Investimento
    let fiveStarCount = 0;
    let totalRanks = 0;
    team.members.forEach(m => {
        const rNum = Number(m.rarity);
        if (rNum === 5 || m.rarity === "5" || String(m.rarity).toUpperCase() === "S") fiveStarCount++;
        const mRank = String(m.rank_str || "").match(/\d+/);
        if (mRank) totalRanks += parseInt(mRank[0]);
    });
    const rankLabel = gameId === "genshin" ? "Constelações" : (gameId === "zzz" ? "Mindscapes" : "Eidolons");
    const pitySummary = `Investimento: ${fiveStarCount}x 5★ | ${totalRanks}x ${rankLabel} Ativas`;

    // Identificação dinâmica do jogador via API/banco
    let playerNick = "Jogador";
    let playerUidText = "UID: Sincronizado";

    const acc = (window.globalOverview && window.globalOverview[gameId]) || null;
    if (acc) {
        if (acc.nickname) playerNick = acc.nickname;
        if (acc.uid && acc.uid !== "Não sincronizado") playerUidText = `UID: ${acc.uid}`;
    } else {
        const uidEl = document.getElementById(`ov-${gameId}-uid`);
        if (uidEl && uidEl.innerText) {
            const raw = uidEl.innerText.trim();
            if (raw.includes("•")) {
                const parts = raw.split("•").map(s => s.trim());
                if (parts[0] && parts[0] !== "Não sincronizado") playerNick = parts[0];
                if (parts[1]) playerUidText = parts[1];
            } else if (raw !== "Não sincronizado") {
                playerUidText = raw.startsWith("UID") ? raw : `UID: ${raw}`;
            }
        }
    }

    let gameBadgeLabel = "GENSHIN IMPACT";
    if (gameId === "hsr") gameBadgeLabel = "HONKAI: STAR RAIL";
    if (gameId === "zzz") gameBadgeLabel = "ZENLESS ZONE ZERO";

    // Gera os subcards de cada slot
    const slotsHtml = [];
    for (let i = 0; i < maxSlots; i++) {
        const char = team.members[i];
        if (char) {
            const rarityNum = Number(char.rarity);
            const isFiveStar = rarityNum === 5 || char.rarity === "5" || String(char.rarity).toUpperCase() === "S";
            const rarityColor = isFiveStar ? "#E9A13B" : "#A256E0";
            const rarityGlow = isFiveStar ? "rgba(233, 161, 59, 0.35)" : "rgba(162, 86, 224, 0.35)";

            const defaultFallback = `/assets/${gameId}_icon.png`;
            const avatarSrc = char.icon || defaultFallback;
            const splashSrc = getCharacterSplashArt(gameId, char);
            const elemKey = (char.element || "").toLowerCase();
            const elemIconUrl = `/assets/elements/${gameId}_${elemKey}.png`;

            const weapon = extractTeamCardWeapon(gameId, char);
            const relics = extractTeamCardRelics(gameId, char);
            const stats = extractTeamCardStats(gameId, char);

            let subRole = "Personagem";
            if (char.path) subRole = char.path;
            else if (char.specialty) subRole = char.specialty;
            else if (char.element) subRole = formatElementDisplayName(char.element);

            slotsHtml.push(`
                <div class="team-char-subcard" style="--char-border: rgba(255, 255, 255, 0.12); --char-elem-color: ${rarityColor}; --char-rarity-color: ${rarityColor}; --char-rarity-glow: ${rarityGlow};">
                    <!-- Splash Art de fundo cobrindo o card todo -->
                    <div class="subcard-splash-bg">
                        <img class="subcard-splash-img" src="${splashSrc}" decoding="async" onerror="this.onerror=null; this.src='${avatarSrc}';" alt="${char.name}">
                    </div>
                    <div class="subcard-splash-gradient"></div>

                    <!-- Botão de Remover Slot (Oculto na exportação PNG) -->
                    <button class="slot-remove-btn" title="Remover personagem do time" onclick="window.removeTeamMember('${gameId}', ${i})">
                        <i class="fa-solid fa-xmark"></i>
                    </button>

                    <!-- Topo Flutuante com Elemento, Nível e Rank -->
                    <div class="subcard-top-float-row">
                        <div class="subcard-elem-pill" title="Elemento: ${char.element || ''}">
                            <img src="${elemIconUrl}" onerror="this.style.display='none';" alt="" class="subcard-elem-pill-icon">
                            <span>${(char.element || '').toUpperCase()}</span>
                        </div>
                        <div class="subcard-top-right-badges">
                            <span class="subcard-lvl-pill">Nv. ${char.level}</span>
                            <span class="subcard-rank-badge">${char.rank_str || 'C0'}</span>
                        </div>
                    </div>

                    <!-- Espaço em branco na parte de cima para ver a parte superior da Splash Art -->
                    <div class="subcard-splash-view-spacer"></div>

                    <!-- Identificação do Personagem -->
                    <div class="subcard-hero-title-box">
                        <h4 class="subcard-char-name" title="${char.name}">${char.name}</h4>
                        <div class="subcard-char-submeta">
                            <span class="subcard-char-role">${subRole}</span>
                            <span class="subcard-char-stars">${'★'.repeat(Math.min(5, Math.max(4, isFiveStar ? 5 : 4)))}</span>
                        </div>
                    </div>

                    <!-- Equipamento / Arma -->
                    <div class="subcard-equip-strip">
                        <div class="subcard-equip-icon-box" style="--equip-border: ${rarityColor};">
                            <img src="${weapon.icon}" onerror="this.src='/assets/chat_icon.png';" alt="${weapon.name}">
                        </div>
                        <div class="subcard-equip-details">
                            <div class="subcard-equip-name-row">
                                <span class="subcard-equip-name" title="${weapon.name}">${weapon.name}</span>
                                <span class="subcard-equip-refine">${weapon.refine}</span>
                            </div>
                            <span class="subcard-equip-lvl">${weapon.level}</span>
                        </div>
                    </div>

                    <!-- Relíquias / Artefatos / Discos com Ícone do Set -->
                    <div class="subcard-relic-box">
                        <div class="subcard-relic-header">
                            ${relics.setIcon ? `
                                <div class="subcard-set-icon-box">
                                    <img src="${relics.setIcon}" class="subcard-set-icon-img" alt="${relics.setTitle}" onerror="this.parentElement.style.display='none';">
                                    ${relics.setIcons && relics.setIcons.length > 1 ? `
                                        <img src="${relics.setIcons[1]}" class="subcard-set-icon-img subcard-set-icon-secondary" alt="" onerror="this.style.display='none';">
                                    ` : ''}
                                </div>
                            ` : `
                                <span class="subcard-relic-dot"></span>
                            `}
                            <div class="subcard-relic-title-group">
                                <span class="subcard-relic-category-tag">${gameId === 'genshin' ? 'Artefatos' : (gameId === 'zzz' ? 'Discos' : 'Relíquias')}</span>
                                <div class="subcard-relic-title" title="${relics.setTitle}">
                                    ${(relics.setLines || [relics.setTitle]).map(line => `<span class="subcard-set-line-item">${line}</span>`).join(" <span class='subcard-set-sep'>+</span> ")}
                                </div>
                            </div>
                        </div>
                        <div class="subcard-mainstats-row">
                            ${relics.chips.map(chip => `
                                <div class="subcard-mainstat-chip" title="Slot ${chip.slot}">
                                    <span class="subcard-mainstat-slot">${chip.slot}:</span>
                                    <span>${chip.val}</span>
                                </div>
                            `).join("")}
                        </div>
                    </div>

                    <!-- Grid 2x4 de Atributos Finais -->
                    <div class="subcard-stats-matrix-2x4">
                        ${stats.map(st => `
                            <div class="subcard-stat-cell">
                                <span class="subcard-stat-label" title="${st.label}">${st.label}</span>
                                <span class="subcard-stat-val ${st.highlight ? 'highlight' : ''} ${st.crit ? 'crit' : ''}" title="${st.val}">${st.val}</span>
                            </div>
                        `).join("")}
                    </div>
                </div>
            `);
        } else {
            // Slot Vazio
            slotsHtml.push(`
                <div class="empty-slot-card" onclick="document.querySelector('#team-roster-grid-${gameId}').scrollIntoView({ behavior: 'smooth' })">
                    <i class="fa-solid fa-plus"></i>
                    <span>Slot ${i + 1} Vazio</span>
                    <small>Clique em um personagem acima para adicionar</small>
                </div>
            `);
        }
    }

    cardContainer.innerHTML = `
        <!-- Topbar -->
        <div class="team-topbar">
            <div class="team-topbar-left">
                <span class="game-title-badge">${gameBadgeLabel}</span>
                <h2 class="team-name-title">
                    <span id="team-title-display-${gameId}">${team.teamName}</span>
                    <span class="team-elem-pill">${elemTagText}</span>
                </h2>
            </div>
            <div class="team-topbar-right">
                <div class="team-player-name" id="team-player-name-${gameId}">${playerNick}</div>
                <div class="team-player-uid" id="team-player-uid-${gameId}">${playerUidText}</div>
            </div>
        </div>

        <!-- Grid de Slots -->
        <div class="team-slots-grid ${isThreeCol ? 'grid-3' : 'grid-4'}">
            ${slotsHtml.join("")}
        </div>

        <!-- Rodapé -->
        <div class="team-footer">
            <div class="team-footer-left">
                <span class="team-synergy-pill">Composição Ativa</span>
                <span class="team-synergy-desc">Builds sincronizadas com o banco local SQLite</span>
            </div>
            <div class="team-footer-right">
                <div class="team-pity-badge">${pitySummary}</div>
                <div class="team-watermark">Cabeça de Droid • HoYoverse Build Engine</div>
            </div>
        </div>
    `;

    // Sincroniza dados da conta via API caso ainda não estejam no cache global
    if (playerNick === "Jogador" || !playerNick || playerUidText.includes("Sincronizado")) {
        const applyAccountData = (accData) => {
            if (accData && accData.nickname) {
                if (!window.globalOverview) window.globalOverview = {};
                if (!window.globalOverview[gameId]) window.globalOverview[gameId] = {};
                window.globalOverview[gameId].nickname = accData.nickname;
                if (accData.uid && accData.uid !== "Não sincronizado") window.globalOverview[gameId].uid = accData.uid;

                const nickEl = document.getElementById(`team-player-name-${gameId}`);
                if (nickEl) nickEl.innerText = accData.nickname;
                const uidEl = document.getElementById(`team-player-uid-${gameId}`);
                if (uidEl && accData.uid && accData.uid !== "Não sincronizado") {
                    uidEl.innerText = `UID: ${accData.uid}`;
                }
            }
        };

        // Busca a conta uma única vez por jogo (promise em cache) — antes cada re-render disparava novas requisições
        window._accountFetchCache = window._accountFetchCache || {};
        if (!window._accountFetchCache[gameId]) {
            window._accountFetchCache[gameId] = fetch(`/api/account/${gameId}`)
                .then(res => {
                    if (!res.ok) throw new Error("Fallback para /api/accounts");
                    return res.json();
                })
                .catch(() => fetch("/api/accounts")
                    .then(res => res.json())
                    .then(accountsList => Array.isArray(accountsList)
                        ? accountsList
                            .filter(a => a.game_id === gameId)
                            .sort((a, b) => (parseInt(b.level) || 0) - (parseInt(a.level) || 0))[0] || null
                        : null))
                .catch(err => {
                    console.warn("Falha ao sincronizar conta via API:", err);
                    window._accountFetchCache[gameId] = null; // permite nova tentativa depois
                    return null;
                });
        }
        window._accountFetchCache[gameId].then(applyAccountData);
    }
}

// 13. Renderiza a tela do Construtor de Time
window.renderTeamBuilderView = function(gameId) {
    window.renderTeamRosterSelector(gameId);
    window.updateTeamUI(gameId);
};

// Helper para preparar o documento clonado antes da rasterização do html2canvas
function prepareClonedTeamCard(clonedDoc, gameId, origCardEl) {
    const clonedCard = clonedDoc.getElementById(`team-export-card-${gameId}`);
    if (!clonedCard) return;

    // 1. Oculta botões de remoção de slots e retira sombras para exportação nítida
    clonedCard.querySelectorAll(".slot-remove-btn").forEach(b => b.style.display = "none");
    clonedCard.style.boxShadow = "none";

    // 2. Corrige a distorção do html2canvas: html2canvas NÃO suporta a propriedade CSS "object-fit: cover"
    // em tags <img>, o que faz com que splash arts panorâmicas (16:9 ou quadradas) sejam comprimidas
    // na horizontal ao preencher um subcard alto e estreito.
    // Calculamos e injetamos as dimensões matemáticas exatas de "cover" no DOM clonado:
    const origSubcards = origCardEl.querySelectorAll(".team-char-subcard");
    const clonedSubcards = clonedCard.querySelectorAll(".team-char-subcard");

    origSubcards.forEach((origSubcard, idx) => {
        const clonedSubcard = clonedSubcards[idx];
        if (!clonedSubcard) return;

        const origImg = origSubcard.querySelector(".subcard-splash-img");
        const clonedImg = clonedSubcard.querySelector(".subcard-splash-img");
        if (!origImg || !clonedImg) return;

        const bgContainer = origSubcard.querySelector(".subcard-splash-bg");
        const cWidth = bgContainer ? bgContainer.offsetWidth : (origSubcard.offsetWidth || 260);
        const cHeight = bgContainer ? bgContainer.offsetHeight : (origSubcard.offsetHeight || 580);

        const nWidth = origImg.naturalWidth || cWidth;
        const nHeight = origImg.naturalHeight || cHeight;

        if (nWidth > 0 && nHeight > 0 && cWidth > 0 && cHeight > 0) {
            const imgAspect = nWidth / nHeight;
            const containerAspect = cWidth / cHeight;

            let renderedW, renderedH, leftOffset, topOffset;

            if (imgAspect > containerAspect) {
                // A imagem é mais larga que o container: fixa a altura do card e escala a largura mantendo o aspect ratio
                renderedH = cHeight;
                renderedW = cHeight * imgAspect;
                leftOffset = (cWidth - renderedW) / 2;
                topOffset = 0;
            } else {
                // A imagem é mais alta que o container: fixa a largura do card e escala a altura proporcionalmente
                renderedW = cWidth;
                renderedH = cWidth / imgAspect;
                leftOffset = 0;
                topOffset = 0;
            }

            clonedImg.style.width = `${Math.round(renderedW)}px`;
            clonedImg.style.height = `${Math.round(renderedH)}px`;
            clonedImg.style.position = "absolute";
            clonedImg.style.left = `${Math.round(leftOffset)}px`;
            clonedImg.style.top = `${Math.round(topOffset)}px`;
            clonedImg.style.maxWidth = "none";
            clonedImg.style.maxHeight = "none";
            clonedImg.style.objectFit = "fill";
            clonedImg.style.transform = "none";
        }
    });
}

// 14. Exportação Canvas HD via html2canvas (scale: 2, useCORS: true)
window.exportTeamCardPNG = async function(gameId) {
    const cardEl = document.getElementById(`team-export-card-${gameId}`);
    if (!cardEl) return;

    const team = teamBuilderState[gameId];
    if (!team || team.members.length === 0) {
        if (typeof showToast === "function") {
            showToast("Adicione pelo menos 1 personagem ao time antes de exportar!", "warning");
        }
        return;
    }

    const exportBtn = document.querySelector(`#view-teamcard-${gameId} .export-team-btn`);
    const origHtml = exportBtn ? exportBtn.innerHTML : "";
    if (exportBtn) {
        exportBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Gerando PNG 2x...';
        exportBtn.disabled = true;
    }

    try {
        await document.fonts.ready;
        const imgs = Array.from(cardEl.querySelectorAll("img"));
        await Promise.all(imgs.map(img => {
            if (img.complete && img.naturalWidth > 0) return Promise.resolve();
            return new Promise(resolve => {
                img.addEventListener("load", resolve, { once: true });
                img.addEventListener("error", resolve, { once: true });
                setTimeout(resolve, 1500);
            });
        }));

        const canvas = await html2canvas(cardEl, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: "#0a0d14",
            logging: false,
            onclone: (clonedDoc) => {
                prepareClonedTeamCard(clonedDoc, gameId, cardEl);
            }
        });

        const safeTeamName = getSafeFileName(team.teamName || "Team");
        const link = document.createElement("a");
        link.download = `Card_Time_${gameId.toUpperCase()}_${safeTeamName}_${Date.now()}.png`;
        link.href = canvas.toDataURL("image/png");
        link.click();
        if (typeof showToast === "function") {
            showToast("Card de time exportado com sucesso em alta definição (PNG 2x)!", "success");
        }
    } catch (err) {
        console.error("Erro na exportação do card de time:", err);
        if (typeof showToast === "function") {
            showToast(`Erro ao exportar card: ${err.message}`, "error");
        }
    } finally {
        if (exportBtn) {
            exportBtn.innerHTML = origHtml;
            exportBtn.disabled = false;
        }
    }
};

// 15. Cópia da Imagem do Time para Clipboard
window.copyTeamCardClipboard = async function(gameId) {
    const cardEl = document.getElementById(`team-export-card-${gameId}`);
    if (!cardEl) return;

    const team = teamBuilderState[gameId];
    if (!team || team.members.length === 0) {
        if (typeof showToast === "function") {
            showToast("Adicione pelo menos 1 personagem ao time antes de copiar!", "warning");
        }
        return;
    }

    const copyBtn = document.querySelector(`#view-teamcard-${gameId} .copy-team-btn`);
    const origHtml = copyBtn ? copyBtn.innerHTML : "";
    if (copyBtn) {
        copyBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Renderizando...';
        copyBtn.disabled = true;
    }

    try {
        await document.fonts.ready;
        const imgs = Array.from(cardEl.querySelectorAll("img"));
        await Promise.all(imgs.map(img => {
            if (img.complete && img.naturalWidth > 0) return Promise.resolve();
            return new Promise(resolve => {
                img.addEventListener("load", resolve, { once: true });
                img.addEventListener("error", resolve, { once: true });
                setTimeout(resolve, 1500);
            });
        }));

        const canvas = await html2canvas(cardEl, {
            scale: 2,
            useCORS: true,
            allowTaint: true,
            backgroundColor: "#0a0d14",
            logging: false,
            onclone: (clonedDoc) => {
                prepareClonedTeamCard(clonedDoc, gameId, cardEl);
            }
        });

        if (navigator.clipboard && window.ClipboardItem && navigator.clipboard.write) {
            const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/png"));
            const item = new ClipboardItem({ "image/png": blob });
            await navigator.clipboard.write([item]);
            if (typeof showToast === "function") {
                showToast("Imagem do time copiada para a área de transferência! Cole no Discord ou WhatsApp.", "success");
            }
        } else {
            window.exportTeamCardPNG(gameId);
        }
    } catch (err) {
        console.error("Erro ao copiar para clipboard:", err);
        window.exportTeamCardPNG(gameId);
    } finally {
        if (copyBtn) {
            copyBtn.innerHTML = origHtml;
            copyBtn.disabled = false;
        }
    }
};



// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
if (typeof TEAM_MAX_MEMBERS !== 'undefined') window.TEAM_MAX_MEMBERS = TEAM_MAX_MEMBERS;
if (typeof appendChatMessage !== 'undefined') window.appendChatMessage = appendChatMessage;
if (typeof ensureCharacterBuildData !== 'undefined') window.ensureCharacterBuildData = ensureCharacterBuildData;
if (typeof extractTeamCardRelics !== 'undefined') window.extractTeamCardRelics = extractTeamCardRelics;
if (typeof extractTeamCardStats !== 'undefined') window.extractTeamCardStats = extractTeamCardStats;
if (typeof extractTeamCardWeapon !== 'undefined') window.extractTeamCardWeapon = extractTeamCardWeapon;
if (typeof getCharacterSplashArt !== 'undefined') window.getCharacterSplashArt = getCharacterSplashArt;
if (typeof prepareClonedTeamCard !== 'undefined') window.prepareClonedTeamCard = prepareClonedTeamCard;
if (typeof renderTeamExportCard !== 'undefined') window.renderTeamExportCard = renderTeamExportCard;
if (typeof selectedTeam !== 'undefined') window.selectedTeam = selectedTeam;
if (typeof setupChatSystem !== 'undefined') window.setupChatSystem = setupChatSystem;
if (typeof teamBuilderState !== 'undefined') window.teamBuilderState = teamBuilderState;
if (typeof toggleCharacterInTeam !== 'undefined') window.toggleCharacterInTeam = toggleCharacterInTeam;
if (typeof updateTeamBuilderGrid !== 'undefined') window.updateTeamBuilderGrid = updateTeamBuilderGrid;
if (typeof updateTeamUI !== 'undefined') window.updateTeamUI = updateTeamUI;