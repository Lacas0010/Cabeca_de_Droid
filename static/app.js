// ==========================================================================
// CONFIGURAÇÕES GERAIS E ESTADO GLOBAL
// ==========================================================================
const API_URL = ""; // Relativo ao servidor que serve a página
let chatHistory = [];
let activePolling = { zzz: null, genshin: null, hsr: null };

// Dicionário de normalização de elementos para classes CSS
const ELEMENT_MAPPING = {
    // Honkai Star Rail
    "fire": "el-fire", "ice": "el-ice", "wind": "el-wind", "lightning": "el-lightning",
    "physical": "el-physical", "quantum": "el-quantum", "imaginary": "el-imaginary",
    "físico": "el-physical", "fogo": "el-fire", "gelo": "el-ice", "vento": "el-wind",
    "raio": "el-lightning", "imaginário": "el-imaginary",
    // Genshin Impact
    "pyro": "el-pyro", "cryo": "el-cryo", "anemo": "el-anemo", "electro": "el-electric",
    "geo": "el-geo", "dendro": "el-dendro", "hydro": "el-hydro",
    // Zenless Zone Zero
    "electric": "el-electric", "ether": "el-ether"
};

// Emojis de fallback para slots de relíquias / artefatos / discos
const SLOT_EMOJIS = {
    // HSR
    "cabeça": "🪖", "cabeça (head)": "🪖", "cabeça(head)": "🪖",
    "mãos": "🥊", "mãos (hands)": "🥊", "mãos(hands)": "🥊",
    "corpo": "🥼", "corpo (body)": "🥼", "corpo(body)": "🥼",
    "pés": "👟", "pés (feet)": "👟", "pés(feet)": "👟",
    "esfera plana": "🔮", "esfera plana (planar sphere)": "🔮", "esfera plana(planar sphere)": "🔮",
    "corda de ligação": "📿", "corda de ligação (link rope)": "📿", "corda de ligação(link rope)": "📿",
    // Genshin
    "flor da vida": "🌸", "flor da vida (flower)": "🌸", "flor da vida(flower)": "🌸",
    "pluma da morte": "🪶", "pluma da morte (plume)": "🪶", "pluma da morte(plume)": "🪶",
    "areia do tempo": "⏳", "areia do tempo (sands)": "⏳", "areia do tempo(sands)": "⏳",
    "cálice de eonothem": "🏆", "cálice de eonothem (goblet)": "🏆", "cálice de eonothem(goblet)": "🏆",
    "tiara de logos": "👑", "tiara de logos (circlet)": "👑", "tiara de logos(circlet)": "👑",
    // ZZZ
    "disco 1": "💿", "disco 2": "💿", "disco 3": "💿",
    "disco 4": "💿", "disco 5": "💿", "disco 6": "💿"
};

function getSlotEmoji(slotName) {
    const key = slotName.toLowerCase().trim();
    return SLOT_EMOJIS[key] || "🛡️";
}

function getSafeFileName(name) {
    return name.toLowerCase().replace(/[^a-zA-Z0-9]/g, "_") + ".png";
}

// ==========================================================================
// INICIALIZAÇÃO DA APLICAÇÃO
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
    setupTabSwitching();
    setupConfigForm();
    setupSyncControls();
    setupChatSystem();
    
    // Carrega dados iniciais
    fetchConfig();
    loadOverview();
    loadRoster("zzz");
    loadRoster("genshin");
    loadRoster("hsr");
});

async function loadOverview() {
    try {
        const res = await fetch("/api/overview");
        const overview = await res.json();
        
        // ZZZ
        if (overview.zzz) {
            document.getElementById("ov-zzz-uid").innerText = overview.zzz.uid !== "Não sincronizado" ? `UID: ${overview.zzz.uid}` : "Não sincronizado";
            document.getElementById("ov-zzz-lvl").innerText = overview.zzz.level;
            document.getElementById("ov-zzz-chars").innerText = overview.zzz.char_count;
        }
        
        // Genshin
        if (overview.genshin) {
            document.getElementById("ov-genshin-uid").innerText = overview.genshin.uid !== "Não sincronizado" ? `UID: ${overview.genshin.uid}` : "Não sincronizado";
            document.getElementById("ov-genshin-lvl").innerText = overview.genshin.level;
            document.getElementById("ov-genshin-chars").innerText = overview.genshin.char_count;
        }
        
        // HSR
        if (overview.hsr) {
            document.getElementById("ov-hsr-uid").innerText = overview.hsr.uid !== "Não sincronizado" ? `UID: ${overview.hsr.uid}` : "Não sincronizado";
            document.getElementById("ov-hsr-lvl").innerText = overview.hsr.level;
            document.getElementById("ov-hsr-chars").innerText = overview.hsr.char_count;
        }
    } catch (err) {
        console.error("Erro ao carregar visão geral:", err);
    }
}

// ==========================================================================
// GERENCIAMENTO DE ABAS (TABS)
// ==========================================================================
function setupTabSwitching() {
    const navButtons = document.querySelectorAll(".nav-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            
            navButtons.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(pane => pane.classList.remove("active"));
            
            btn.classList.add("active");
            document.getElementById(`tab-${targetTab}`).classList.add("active");
            
            // Fecha o inspetor de build ao mudar de aba
            closeInspector();
        });
    });
}

// ==========================================================================
// SISTEMA DE CONFIGURAÇÃO (API KEYS & COOKIES)
// ==========================================================================
async function fetchConfig() {
    try {
        const res = await fetch("/api/config");
        const config = await res.json();
        
        document.getElementById("cfg-groq-key").value = config.groq_api_key;
        document.getElementById("cfg-hoyolab-cookies").value = config.cookies_raw;
        
        updateApiStatusIndicator(config.has_api_key && config.has_cookies);
    } catch (err) {
        console.error("Erro ao buscar configurações:", err);
    }
}

function updateApiStatusIndicator(online) {
    const dot = document.getElementById("api-status-dot");
    const text = document.getElementById("api-status-text");
    if (online) {
        dot.className = "status-dot online";
        text.innerText = "IA & Cookies Conectados";
    } else {
        dot.className = "status-dot offline";
        text.innerText = "Configuração pendente";
    }
}

async function setupConfigForm() {
    const saveBtn = document.getElementById("btn-save-config");
    const autoLoginBtn = document.getElementById("btn-auto-login");
    const statusMsg = document.getElementById("config-save-status");

    saveBtn.addEventListener("click", async () => {
        const groq_api_key = document.getElementById("cfg-groq-key").value;
        const cookies_raw = document.getElementById("cfg-hoyolab-cookies").value;
        
        statusMsg.className = "status-msg";
        statusMsg.innerText = "Salvando...";
        
        try {
            const res = await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ groq_api_key, cookies_raw })
            });
            const data = await res.json();
            
            if (res.ok) {
                statusMsg.className = "status-msg success";
                statusMsg.innerText = "Configurações salvas localmente!";
                fetchConfig();
            } else {
                statusMsg.className = "status-msg error";
                statusMsg.innerText = `Erro: ${data.detail}`;
            }
        } catch (err) {
            statusMsg.className = "status-msg error";
            statusMsg.innerText = "Erro ao conectar com o servidor.";
        }
    });

    autoLoginBtn.addEventListener("click", async () => {
        autoLoginBtn.disabled = true;
        autoLoginBtn.innerText = "Aguardando login no navegador...";
        
        try {
            const res = await fetch("/api/login/auto", { method: "POST" });
            if (res.ok) {
                // Monitora o status das configurações para ver se os cookies mudaram para "has_cookies: true"
                let attempts = 0;
                const interval = setInterval(async () => {
                    attempts++;
                    const checkRes = await fetch("/api/config");
                    const checkCfg = await checkRes.json();
                    if (checkCfg.has_cookies || attempts > 60) {
                        clearInterval(interval);
                        autoLoginBtn.disabled = false;
                        autoLoginBtn.innerText = "🌐 Login Automático via Playwright";
                        fetchConfig();
                    }
                }, 2000);
            }
        } catch (err) {
            autoLoginBtn.disabled = false;
            autoLoginBtn.innerText = "🌐 Login Automático via Playwright";
        }
    });
}

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
        syncAllBtn.innerText = "🚀 Sincronização em Lote Iniciada";
        
        triggerSync("zzz", true, true, true);
        triggerSync("genshin", true, true, true);
        triggerSync("hsr", true, true, true);
        
        setTimeout(() => {
            syncAllBtn.disabled = false;
            syncAllBtn.innerText = "🚀 Sincronização Global";
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
                // Recarrega o roster visual do jogo que acabou de sincronizar
                setTimeout(() => {
                    loadRoster(gameId);
                    loadOverview();
                }, 1000);
            }
        } catch (err) {
            console.error(`Erro ao consultar status de ${gameId}:`, err);
        }
    }, 1000);
}

// ==========================================================================
// RENDERIZAÇÃO DA GALERIA DE PERSONAGENS
// ==========================================================================
async function loadRoster(gameId) {
    const gallery = document.getElementById(`gallery-${gameId}`);
    gallery.innerHTML = Array(12).fill(0).map(() => `
        <div class="skeleton-card">
            <div class="skeleton-avatar"></div>
            <div class="skeleton-info">
                <div class="skeleton-name"></div>
                <div class="skeleton-lvl"></div>
            </div>
        </div>
    `).join('');
    
    try {
        const res = await fetch(`/api/roster/${gameId}`);
        const roster = await res.json();
        
        if (!roster || roster.length === 0) {
            gallery.innerHTML = `
                <div class="empty-gallery">
                    <p>Nenhum personagem extraído localmente.</p>
                    <span>Marque "Roster" e clique em "Sincronizar ${gameId.toUpperCase()}" acima para carregar sua conta!</span>
                </div>
            `;
            return;
        }
        
        gallery.innerHTML = ""; // Limpa spinner
        
        // Estado dos filtros combinados
        let activeElementFilter = "all";
        let searchQuery = "";
        
        const searchInput = document.querySelector(`.search-input[data-game="${gameId}"]`);
        
        const renderCards = () => {
            gallery.innerHTML = "";
            
            // Filtra a lista local baseado na busca de texto E elemento
            const filtered = roster.filter(char => {
                const matchesSearch = char.name.toLowerCase().includes(searchQuery);
                const matchesElement = activeElementFilter === "all" || 
                    (char.element || "").toLowerCase() === activeElementFilter.toLowerCase();
                return matchesSearch && matchesElement;
            });
            
            if (filtered.length === 0) {
                gallery.innerHTML = `
                    <div class="empty-gallery" style="grid-column: 1 / -1; padding: 40px 0;">
                        <p>Nenhum personagem encontrado com os filtros ativos.</p>
                    </div>
                `;
                return;
            }
            
            filtered.forEach(char => {
                const card = document.createElement("div");
                
                // Normaliza o elemento para a classe CSS de borda colorida
                const elemKey = (char.element || "").toLowerCase();
                const elemClass = ELEMENT_MAPPING[elemKey] || "el-physical";
                
                card.className = `char-card ${elemClass}`;
                
                const safeFn = getSafeFileName(char.name);
                const localAvatarPath = `/assets/avatars/${gameId}/${safeFn}`;
                
                // Estrutura o HTML do Card incluindo o ícone do Elemento ao lado do nome
                card.innerHTML = `
                    <div class="char-avatar-container">
                        <img class="char-avatar" src="${localAvatarPath}" onerror="this.onerror=null; this.src='${char.icon || '/assets/config_icon.png'}';" alt="${char.name}">
                        <div class="char-rank-badge">${char.rank_str || 'C0'}</div>
                    </div>
                    <div class="char-info">
                        <div class="char-name" title="${char.name}">
                            <img src="/assets/elements/${gameId}_${elemKey}.png" class="element-icon-inline" onerror="this.style.display='none';" alt="">
                            ${char.name}
                        </div>
                        <div class="char-lvl">Nível ${char.level}</div>
                    </div>
                `;
                
                // Clique para abrir detalhes no Build Inspector lateral
                card.addEventListener("click", () => {
                    inspectCharacter(gameId, char);
                });
                
                gallery.appendChild(card);
            });
        };
        
        // Configura ouvintes de clique nos botões de filtro de elementos
        const filterContainer = document.querySelector(`.element-filters[data-game="${gameId}"]`);
        if (filterContainer) {
            const filterBtns = filterContainer.querySelectorAll(".filter-btn");
            filterBtns.forEach(btn => {
                // Remove listeners anteriores
                const newBtn = btn.cloneNode(true);
                btn.parentNode.replaceChild(newBtn, btn);
            });
            
            // Adiciona novos listeners aos botões clonados
            const freshBtns = filterContainer.querySelectorAll(".filter-btn");
            freshBtns.forEach(btn => {
                btn.addEventListener("click", () => {
                    freshBtns.forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    activeElementFilter = btn.getAttribute("data-filter");
                    renderCards();
                });
            });
        }
        
        // Evento de busca em tempo real
        searchInput.replaceWith(searchInput.cloneNode(true)); // Limpa listeners antigos
        const newSearchInput = document.querySelector(`.search-input[data-game="${gameId}"]`);
        newSearchInput.addEventListener("input", (e) => {
            searchQuery = e.target.value.toLowerCase().trim();
            renderCards();
        });
        
        // Renderização inicial do Grid
        renderCards();
        
    } catch (err) {
        gallery.innerHTML = `<div class="error-msg">Erro ao carregar roster: ${err.message}</div>`;
    }
}

// ==========================================================================
// COLLAPSIBLE BUILD INSPECTOR (DETALHES DA BUILD)
// ==========================================================================
async function inspectCharacter(gameId, char) {
    const inspector = document.getElementById("build-inspector");
    
    // Preenche cabeçalho básico instantaneamente
    const safeAvatarFn = getSafeFileName(char.name);
    document.getElementById("ins-avatar").src = `/assets/avatars/${gameId}/${safeAvatarFn}`;
    document.getElementById("ins-avatar").onerror = function() {
        this.src = char.icon || '/assets/config_icon.png';
    };
    
    document.getElementById("ins-name").innerText = char.name;
    
    const elemKey = (char.element || "").toLowerCase();
    const elemHtml = `<img src="/assets/elements/${gameId}_${elemKey}.png" class="element-icon-inline" style="width:14px; height:14px;" onerror="this.style.display='none';"> ${(char.element || 'N/A').toUpperCase()}`;
    document.getElementById("ins-meta").innerHTML = `${char.rank_str || 'C0'} • ${elemHtml} • Nível ${char.level}`;
    
    // Configura e limpa o card do Otimizador IA
    const btnOptimize = document.getElementById("btn-ai-optimize");
    const aiLoading = document.getElementById("ins-ai-loading");
    const aiSuggestions = document.getElementById("ins-ai-suggestions");
    
    aiLoading.style.display = "none";
    aiSuggestions.style.display = "none";
    aiSuggestions.innerHTML = "";
    btnOptimize.disabled = false;
    btnOptimize.innerText = "Analisar";
    
    btnOptimize.onclick = async () => {
        btnOptimize.disabled = true;
        btnOptimize.innerText = "Analisando...";
        aiLoading.style.display = "flex";
        aiSuggestions.style.display = "none";
        aiSuggestions.innerHTML = "";
        
        try {
            const optRes = await fetch(`/api/optimize/${gameId}/${encodeURIComponent(char.name)}`);
            const optData = await optRes.json();
            
            aiLoading.style.display = "none";
            
            if (optData && optData.suggestions) {
                optData.suggestions.forEach(sug => {
                    const li = document.createElement("li");
                    li.style.marginBottom = "6px";
                    li.innerText = sug;
                    aiSuggestions.appendChild(li);
                });
                aiSuggestions.style.display = "block";
            } else {
                aiSuggestions.innerHTML = "<li>Não foi possível obter recomendações agora. Verifique a chave Groq.</li>";
                aiSuggestions.style.display = "block";
            }
        } catch (optErr) {
            console.error("Erro ao rodar otimizador IA:", optErr);
            aiLoading.style.display = "none";
            aiSuggestions.innerHTML = `<li>Erro ao contactar API: ${optErr.message}</li>`;
            aiSuggestions.style.display = "block";
        } finally {
            btnOptimize.disabled = false;
            btnOptimize.innerText = "Reanalisar";
        }
    };
    
    // Exibe esqueleto de loading na área de detalhes
    document.getElementById("ins-relic-sets").innerHTML = "Carregando conjuntos...";
    document.getElementById("ins-stats-grid").innerHTML = "Carregando atributos...";
    document.getElementById("ins-relic-pieces").innerHTML = "Carregando detalhes das peças...";
    
    // Abre a aba lateral
    inspector.classList.add("open");
    
    try {
        const res = await fetch(`/api/build/${gameId}/${encodeURIComponent(char.name)}`);
        const build = await res.json();
        
        // 1. Renderiza Arma / Equipamento
        const lblWeaponName = document.getElementById("ins-weapon-name");
        const lblWeaponMeta = document.getElementById("ins-weapon-meta");
        const imgWeaponIcon = document.getElementById("ins-weapon-icon");
        
        if (char.weapon) {
            lblWeaponName.innerText = char.weapon.name || "Não equipado";
            lblWeaponMeta.innerText = `Nível ${char.weapon.level || 1} • Refinamento: R${char.weapon.rank || 1}`;
            
            const safeWFn = getSafeFileName(char.weapon.name || "");
            imgWeaponIcon.src = `/assets/weapons/${gameId}/${safeWFn}`;
            imgWeaponIcon.onerror = function() {
                this.src = char.weapon.icon || '/assets/chat_icon.png';
            };
        } else {
            lblWeaponName.innerText = build.weapon || "Não informado";
            lblWeaponMeta.innerText = "Nível secundário / Sem sincronização completa";
            imgWeaponIcon.src = "/assets/chat_icon.png";
        }
        
        // 2. Renderiza Conjuntos de Relíquias (Sets)
        const setsList = document.getElementById("ins-relic-sets");
        setsList.innerHTML = "";
        
        if (build.sets && build.sets.length > 0) {
            build.sets.forEach(set => {
                const item = document.createElement("div");
                item.className = "set-item";
                item.innerHTML = `✨ ${set}`;
                setsList.appendChild(item);
            });
        } else {
            setsList.innerHTML = `<span class="text-muted">Nenhum bônus de conjunto ativo.</span>`;
        }
        
        // 3. Renderiza Atributos Consolidados (Stats)
        const statsGrid = document.getElementById("ins-stats-grid");
        statsGrid.innerHTML = "";
        
        const statsKeys = Object.keys(build.stats || {});
        if (statsKeys.length > 0) {
            statsKeys.forEach(key => {
                const statCard = document.createElement("div");
                statCard.className = "stat-card";
                statCard.innerHTML = `
                    <span class="stat-label">${key}</span>
                    <span class="stat-value">${build.stats[key]}</span>
                `;
                statsGrid.appendChild(statCard);
            });
        } else {
            statsGrid.innerHTML = `<span class="text-muted">Consolidação de status não disponível.</span>`;
        }
        
        // 4. Renderiza Peças Individuais combinando RAG MD e Local JSON
        const piecesList = document.getElementById("ins-relic-pieces");
        piecesList.innerHTML = "";
        
        // As peças do roster extraído via HoYoLAB local (contêm URLs originais dos ícones de cada peça!)
        const localRelics = char.relics || char.artifacts || char.discs || [];
        
        if (build.pieces && build.pieces.length > 0) {
            build.pieces.forEach(piece => {
                const row = document.createElement("div");
                row.className = "relic-piece-row";
                
                // Encontra a peça equivalente local para extrair o ícone
                const equivalentLocalPiece = localRelics.find(p => 
                    p.slot.toLowerCase().includes(piece.slot.toLowerCase()) || 
                    piece.slot.toLowerCase().includes(p.slot.toLowerCase()) ||
                    p.name.toLowerCase().includes(piece.name.toLowerCase())
                );
                
                const slotEmoji = getSlotEmoji(piece.slot);
                const safePieceFn = getSafeFileName(piece.name);
                const cachedPiecePath = `/assets/relics/${gameId}/${safePieceFn}`;
                
                const iconHtml = equivalentLocalPiece 
                    ? `<img class="relic-piece-icon" src="${cachedPiecePath}" onerror="this.onerror=null; this.src='${equivalentLocalPiece.icon}';" alt="${piece.slot}">`
                    : `<span class="relic-piece-icon" style="font-size:20px; display:flex; align-items:center; justify-content:center;">${slotEmoji}</span>`;
                
                row.innerHTML = `
                    ${iconHtml}
                    <div class="relic-piece-details">
                        <div class="relic-piece-title">
                            <span class="piece-slot">[${piece.slot}]</span>
                            <span class="piece-name">${piece.name}</span>
                        </div>
                        <div class="piece-main">Principal: ${piece.main}</div>
                        <div class="piece-subs">Substatus: ${piece.sub}</div>
                    </div>
                `;
                piecesList.appendChild(row);
            });
        } else {
            piecesList.innerHTML = `<span class="text-muted">Substatus e peças detalhadas indisponíveis para este nível de Roster.</span>`;
        }
        
    } catch (err) {
        console.error("Erro ao inspecionar build:", err);
        document.getElementById("ins-relic-sets").innerHTML = "Erro ao carregar.";
        document.getElementById("ins-stats-grid").innerHTML = "Erro ao carregar.";
        document.getElementById("ins-relic-pieces").innerHTML = "Erro ao carregar.";
    }
}

function closeInspector() {
    document.getElementById("build-inspector").classList.remove("open");
}

document.getElementById("btn-close-inspector").addEventListener("click", closeInspector);

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
            const data = await res.json();
            
            // Remove o balão de digitando
            document.getElementById(typingId).remove();
            
            if (res.ok) {
                // 4. Renderiza Markdown usando Marked.js
                const formattedResponse = marked.parse(data.response);
                appendChatMessage("assistant", formattedResponse);
                
                // Grava no histórico de memória
                chatHistory.push({ role: "user", text: message });
                chatHistory.push({ role: "model", text: data.response });
                
                // Limita histórico local para no máximo 10 mensagens para não estourar contexto
                if (chatHistory.length > 20) {
                    chatHistory = chatHistory.slice(-20);
                }
            } else {
                appendChatMessage("assistant", `❌ Erro na API do Chat: ${data.detail || "Erro inesperado"}`);
            }
            messagesArea.scrollTop = messagesArea.scrollHeight;
        } catch (err) {
            document.getElementById(typingId).remove();
            appendChatMessage("assistant", `❌ Falha ao conectar ao processador Groq.`);
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
}

function appendChatMessage(role, content) {
    const messagesArea = document.getElementById("chat-messages");
    const msgDiv = document.createElement("div");
    const msgId = "msg-" + Math.random().toString(36).substr(2, 9);
    
    msgDiv.id = msgId;
    msgDiv.className = `chat-msg ${role}`;
    
    const avatar = role === "user" ? "👤" : "🤖";
    
    msgDiv.innerHTML = `
        <div class="msg-avatar">${avatar}</div>
        <div class="msg-content">${content}</div>
    `;
    
    messagesArea.appendChild(msgDiv);
    return msgId;
}
