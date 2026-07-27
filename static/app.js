// ==========================================================================
// CONFIGURAÇÕES GERAIS E ESTADO GLOBAL
// ==========================================================================
const API_URL = ""; // Relativo ao servidor que serve a página
let chatHistory = [];
let activePolling = { zzz: null, genshin: null, hsr: null };
let globalRoster = { zzz: [], genshin: [], hsr: [] };
let activeInspectGame = "";
let activeInspectChar = null;

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

// Helper para normalizar slots de relíquias / artefatos / discos de todos os jogos
function getNormalizedSlot(slot) {
    if (!slot) return "";
    const s = slot.toLowerCase().trim();
    if (s.includes("bota") || s.includes("pés") || s.includes("pes") || s.includes("feet")) return "bota";
    if (s.includes("esfera") || s.includes("sphere")) return "esfera";
    if (s.includes("corda") || s.includes("rope")) return "corda";
    if (s.includes("flor") || s.includes("flower")) return "flor";
    if (s.includes("pena") || s.includes("pluma") || s.includes("plume")) return "pena";
    if (s.includes("areia") || s.includes("sands")) return "areia";
    if (s.includes("copo") || s.includes("cálice") || s.includes("calice") || s.includes("goblet")) return "copo";
    if (s.includes("tiara") || s.includes("logos") || s.includes("circlet")) return "tiara";
    if (s.includes("cabeça") || s.includes("cabeca") || s.includes("head")) return "cabeça";
    if (s.includes("mãos") || s.includes("maos") || s.includes("hands")) return "mãos";
    if (s.includes("corpo") || s.includes("body")) return "corpo";
    if (s.includes("disco 1") || s.includes("disk 1") || s === "1") return "disco 1";
    if (s.includes("disco 2") || s.includes("disk 2") || s === "2") return "disco 2";
    if (s.includes("disco 3") || s.includes("disk 3") || s === "3") return "disco 3";
    if (s.includes("disco 4") || s.includes("disk 4") || s === "4") return "disco 4";
    if (s.includes("disco 5") || s.includes("disk 5") || s === "5") return "disco 5";
    if (s.includes("disco 6") || s.includes("disk 6") || s === "6") return "disco 6";
    return s;
}

// Classes de ícones de fallback (FontAwesome) para slots de relíquias / artefatos / discos
const SLOT_ICONS = {
    // HSR / Genshin
    "cabeça": "fa-solid fa-helmet-safety",
    "mãos": "fa-solid fa-hand-fist",
    "corpo": "fa-solid fa-shirt",
    "bota": "fa-solid fa-shoe-prints",
    "esfera": "fa-solid fa-globe",
    "corda": "fa-solid fa-link",
    "flor": "fa-solid fa-seedling",
    "pena": "fa-solid fa-feather",
    "areia": "fa-solid fa-hourglass-half",
    "copo": "fa-solid fa-glass-water",
    "tiara": "fa-solid fa-crown",
    // ZZZ
    "disco 1": "fa-solid fa-compact-disc",
    "disco 2": "fa-solid fa-compact-disc",
    "disco 3": "fa-solid fa-compact-disc",
    "disco 4": "fa-solid fa-compact-disc",
    "disco 5": "fa-solid fa-compact-disc",
    "disco 6": "fa-solid fa-compact-disc"
};

function getSlotIcon(slotName) {
    const key = getNormalizedSlot(slotName);
    const iconClass = SLOT_ICONS[key] || "fa-solid fa-shield-halved";
    return `<i class="${iconClass}"></i>`;
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
    setupEnergyMonitor();
    setupCheckinSystem();
    setupInspectorTabs();
    
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
        autoLoginBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Aguardando login no navegador...';
        
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
                        autoLoginBtn.innerHTML = '<i class="fa-solid fa-earth-americas"></i> Login Automático via Playwright';
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
        
        // Salva no estado global e atualiza os gráficos SVG
        globalRoster[gameId] = roster || [];
        renderRosterCharts();
        
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
    activeInspectGame = gameId;
    activeInspectChar = char;
    
    // Força reset para a aba de build
    const btnBuild = document.getElementById("ins-tab-build");
    if (btnBuild) btnBuild.click();
    
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
                item.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles" style="font-size: 11px; margin-right: 4px; color: var(--color-hsr);"></i> ${set}`;
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
                    (p.slot && piece.slot && getNormalizedSlot(p.slot) === getNormalizedSlot(piece.slot)) ||
                    (p.name && piece.name && p.name.toLowerCase().includes(piece.name.toLowerCase()))
                );
                
                const slotIcon = getSlotIcon(piece.slot);
                const safePieceFn = getSafeFileName(piece.name);
                const cachedPiecePath = `/assets/relics/${gameId}/${safePieceFn}`;
                
                const iconHtml = equivalentLocalPiece 
                    ? `<img class="relic-piece-icon" src="${cachedPiecePath}" onerror="this.onerror=null; this.src='${equivalentLocalPiece.icon}';" alt="${piece.slot}">`
                    : `<span class="relic-piece-icon" style="font-size:20px; display:flex; align-items:center; justify-content:center;">${slotIcon}</span>`;
                
                // Formata os substatus em grid de 2 colunas para melhor legibilidade
                const subsArray = (piece.sub || "").split(",")
                    .map(s => s.trim())
                    .filter(s => s && s.toLowerCase() !== "sem substatus");
                
                let subsHtml = "";
                if (subsArray.length > 0) {
                    subsHtml = `<div class="piece-subs-grid">`;
                    subsArray.forEach(sub => {
                        const parts = sub.split(":");
                        if (parts.length >= 2) {
                            const name = parts[0].trim();
                            const value = parts[1].trim();
                            subsHtml += `
                                <div class="sub-item">
                                    <span class="sub-label">${name}</span>
                                    <span class="sub-value">${value}</span>
                                </div>
                            `;
                        } else {
                            subsHtml += `
                                <div class="sub-item">
                                    <span class="sub-label">${sub}</span>
                                </div>
                            `;
                        }
                    });
                    subsHtml += `</div>`;
                } else {
                    subsHtml = `<span class="text-muted" style="font-size: 10px;">Sem substatus</span>`;
                }
                
                row.innerHTML = `
                    ${iconHtml}
                    <div class="relic-piece-details">
                        <div class="relic-piece-title">
                            <span class="piece-slot">[${piece.slot}]</span>
                            <span class="piece-name">${piece.name}</span>
                        </div>
                        <div class="piece-main">Principal: ${piece.main}</div>
                        <div class="piece-subs">${subsHtml}</div>
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
}

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
// ABAS E COMPARADOR DO BUILD INSPECTOR
// ==========================================================================
function setupInspectorTabs() {
    const btnBuild = document.getElementById("ins-tab-build");
    const btnCompare = document.getElementById("ins-tab-compare");
    const panelBuild = document.getElementById("panel-build");
    const panelCompare = document.getElementById("panel-compare");
    
    if (!btnBuild || !btnCompare) return;
    
    btnBuild.addEventListener("click", () => {
        btnBuild.classList.add("active");
        btnBuild.style.borderBottomColor = "var(--color-hsr)";
        btnCompare.classList.remove("active");
        btnCompare.style.borderBottomColor = "transparent";
        
        panelBuild.style.display = "block";
        panelCompare.style.display = "none";
    });
    
    btnCompare.addEventListener("click", () => {
        btnCompare.classList.add("active");
        btnCompare.style.borderBottomColor = "var(--color-hsr)";
        btnBuild.classList.remove("active");
        btnBuild.style.borderBottomColor = "transparent";
        
        panelBuild.style.display = "none";
        panelCompare.style.display = "block";
        
        loadBuildComparison();
    });
}

async function loadBuildComparison() {
    const rowsContainer = document.getElementById("ins-comparison-rows");
    if (!rowsContainer || !activeInspectChar) return;
    
    rowsContainer.innerHTML = `<tr><td colspan="3" style="text-align: center; padding: 20px 0; color: var(--text-muted);">Carregando comparação...</td></tr>`;
    
    try {
        const res = await fetch(`/api/compare/${activeInspectGame}/${encodeURIComponent(activeInspectChar.name)}`);
        const data = await res.json();
        
        const build = data.player_build;
        const target = data.meta_target;
        
        // Dicionário de tradução Português <-> Inglês para itens/sets comuns de Genshin, Star Rail e ZZZ
        const translationDict = {
            // ZZZ Sets
            "salão sibilante": "wuthering salon",
            "ode ao cavaleiro lunar": "ode to moonlight",
            "voz astral": "astral voice",
            "rei do monte": "woodpecker electro",
            "techno pica-pau": "woodpecker electro",
            "canção das ondas": "water ballad",
            "canção da espada de ramo": "branch sword",
            "metal infernal": "infernal metal",
            "metal polar": "polar metal",
            "jazz com swing": "swing jazz",
            "disco estrelante": "starlight engine",
            "punk hormonal": "hormone punk",
            "harmonia das sombras": "shockstar disco",
            // ZZZ Weapons
            "eco rítmico": "rhythmic wave",
            "perfuratriz - eixo vermelho": "red axis",
            "engrenagens infernais": "hellfire gears",
            "radiância das nuvens": "cloudcleave radiance",
            "caldeirão da lucidez": "lucid cauldron",
            "transmorfo original": "original transmuter",
            "motor da constelação": "constellation engine",
            "baú da fortuna": "lucky chest",
            "o restrito": "the restrained",
            "cozido a vapor": "steam oven",
            "rugido das chamas": "blazing roar",
            "gourmet tropical": "tropical gourmet",
            "exúvia solar": "solar exuvia",
            "núcleo sísmico": "seismic core",
            "canhão cabum": "kaboom cannon",
            "demônio bisonho": "bashful demon",
            "bateria da demara - tipo ii": "demara battery mark ii",
            "plenilúnio": "full moon",
            "tempestade magnética": "magnetic storm",
            // HSR Sets
            "como o navegador isee vê": "as navigator isee sees it",
            "ancoradouro da estrela caída": "fallen star anchorage",
            "lushaka, os mares afundados": "lushaka's waterside",
            "desfiladeiro aquático de lushaka": "lushaka's waterside",
            "pistas duplas de lushaka": "lushaka's waterside",
            "profeta de alcance distante": "scholar lost in erudition",
            "menina mágica sempre gloriosa": "pioneer diver of dead waters",
            "estágio zero de punklorde": "stage zero of punklorde",
            "grinalda do campeonato do herói": "hero of canyons",
            "braçadeiras douradas do herói": "hero of canyons",
            "armadura dourada galante do herói": "hero of canyons",
            "caneleiras perseguidoras das chamas do herói": "hero of canyons",
            "cidade do arco-íris de punklorde": "talia: kingdom of banditry",
            "fluxo de dados de punklorde": "talia: kingdom of banditry",
            // HSR Weapons
            "antes do amanhecer": "before dawn",
            "noite sobre a via láctea": "night on the milky way",
            "repouso dos gênios": "geniuses' repose",
            "cálculo eterno": "eternal calculus",
            "hoje também é um dia pacífico": "today is another peaceful day",
            "o dia em que o cosmos caiu": "the day the cosmos fell",
            "a seriedade do café da manhã": "the seriousness of breakfast",
            "ao véu inalcançável": "earthly escapade",
            "as aventuras do cogumelinho fofinho": "the adventure of mollusc",
            // Genshin Sets
            "sombra verde": "viridescent venerer",
            "millelith firmes": "tenacity of the millelith",
            "selo da insulação": "emblem of severed fate",
            "herói invernal": "blizzard strayer",
            "caçador das sombras": "marechaussee hunter",
            "trupe dourada": "golden troupe",
            "memórias da floresta": "deepwood memories",
            "sonhos dourados": "gilded dreams",
            "antigo ritual real": "noblesse oblige",
            "pergaminho do herói da cidade incandescente": "scroll of the hero of the cinder city",
            "códice de obsidiana": "obsidian codex",
            "dádiva celestial": "song of days past",
            "serenata das estrelas e da lua": "serenade of stars and moon",
            "noite da revelação do céu": "night of the sky's unveiling",
            "juramento da noite eterna": "oath of the eternal night",
            "pedra arcaica": "archaic petra",
            "último juramento do gladiador": "gladiator's finale",
            "ascensão zéfira": "a day carved from rising winds",
            // Genshin Weapons
            "cortadora da neblina reforjada": "mistsplitter reforged",
            "luz lunar de xiphos": "xiphos' moonlight",
            "espinha dorsal da serpente": "serpent spine",
            "esplendor das águas silenciosas": "splendor of silent waters",
            "memórias de sacrifício": "sacrificial fragments",
            "chave de hierofania": "key of khaj-nisut",
            "subjugadora de calamidades": "calamity queller",
            "aqua simulacra": "aqua simulacra",
            "oração perdida aos ventos sagrados": "lost prayer to the sacred winds",
            "histórias extraordinárias de caçadores de dragões": "thrilling tales of dragon slayers",
            "a fisgada": "the catch",
            "arcana original": "the first great magic",
            "espada de favonius": "favonius sword",
            "lâmina amenoma kageuchi": "amenoma kageuchi",
            "amenoma kageuchi": "amenoma kageuchi",
            "prenúncio do alvorecer": "harbinger of dawn",
            "falcão": "aquila favonia"
        };
        
        function translateToEnglish(name) {
            if (!name) return "";
            const clean = name.toLowerCase().replace(/\([^)]*\)/g, "").replace(/•/g, "").replace(/[^a-z0-9\s]/g, "").trim();
            for (const key in translationDict) {
                if (clean.includes(key) || key.includes(clean)) {
                    return translationDict[key];
                }
            }
            return clean;
        }
        
        const wordMappings = {
            "ferro": "iron",
            "cavalaria": "cavalry",
            "praga": "scourge",
            "ninjutsu": "ninjutsu",
            "inscrição": "inscription",
            "deslumbrante": "dazzling",
            "mal": "evil",
            "destruição": "destruição",
            "reino": "kingdom",
            "banditismo": "banditry",
            "duke": "duque",
            "ashblazing": "cinzas",
            "amanhecer": "dawn",
            "antes": "before",
            "luz": "light",
            "estrelas": "stars",
            "lua": "moon",
            "sombra": "shadow",
            "verde": "green",
            "venerer": "venerer",
            "millelith": "millelith",
            "firmes": "tenacity",
            "insulação": "severed",
            "selo": "emblem",
            "invernal": "blizzard",
            "herói": "hero",
            "caçador": "hunter",
            "sombras": "shadows",
            "dourada": "golden",
            "trupe": "troupe",
            "floresta": "deepwood",
            "memórias": "memories",
            "sonhos": "dreams",
            "dourados": "gilded",
            "ritual": "noblesse",
            "real": "oblige",
            "incandescente": "cinder",
            "cidade": "city",
            "pergaminho": "scroll",
            "obsidiana": "obsidian",
            "códice": "codex",
            "dádiva": "gift",
            "celestial": "song",
            "revelação": "unveiling",
            "céu": "sky",
            "noite": "night",
            "eterna": "eternal",
            "juramento": "oath",
            "pedra": "stone",
            "arcaica": "archaic",
            "gladiador": "gladiator",
            "último": "finale",
            "zéfira": "winds",
            "ascensão": "carved",
            "neblina": "mistsplitter",
            "reforjada": "reforged",
            "cortadora": "reforged",
            "xiphos": "xiphos",
            "serpente": "serpent",
            "espinha": "spine",
            "águas": "waters",
            "silenciosas": "silent",
            "esplendor": "splendor",
            "sacrifício": "sacrificial",
            "hierofania": "khaj",
            "calamidades": "calamity",
            "subjugadora": "queller",
            "oração": "prayer",
            "sagrados": "sacred",
            "ventos": "winds",
            "dragões": "dragon",
            "caçadores": "slayers",
            "fisgada": "catch",
            "lâmina": "blade",
            "alvorecer": "dawn",
            "falcão": "aquila",
            "navegador": "navigator",
            "vejo": "sees",
            "vê": "sees",
            "estrela": "star",
            "caída": "anchorage",
            "afundados": "waterside",
            "profeta": "scholar",
            "alcance": "erudition",
            "distante": "erudition",
            "menina": "pioneer",
            "mágica": "diver"
        };
        
        function checkFuzzyMatch(name1, name2) {
            if (!name1 || !name2) return false;
            const clean1 = translateToEnglish(name1).toLowerCase();
            const clean2 = translateToEnglish(name2).toLowerCase();
            
            if (clean1.includes(clean2) || clean2.includes(clean1)) {
                return true;
            }
            
            const words1 = clean1.split(/\s+/);
            const words2 = clean2.split(/\s+/);
            
            const mapped1 = words1.map(w => wordMappings[w] || w);
            const mapped2 = words2.map(w => wordMappings[w] || w);
            
            const sig1 = mapped1.filter(w => w.length > 3);
            const sig2 = mapped2.filter(w => w.length > 3);
            
            const intersection = sig1.filter(w => sig2.includes(w));
            if (intersection.length >= 2) {
                return true;
            }
            return false;
        }
        
        let html = "";
        
        // 1. Arma (com verificação de múltiplos substitutos e tradução)
        const recommendedWeapons = target.weapons && target.weapons.length > 0 ? target.weapons : [target.weapon];
        const hasWeaponMatch = recommendedWeapons.some(w => checkFuzzyMatch(build.weapon, w));
        
        const weaponClass = target.weapon === "Não informado" ? "comparison-neutral" : (hasWeaponMatch ? "comparison-match" : "comparison-mismatch");
        
        html += `
            <tr>
                <td class="comparison-row-title"><i class="fa-solid fa-wand-magic-sparkles" style="margin-right: 6px;"></i> Arma/Cone</td>
                <td class="${weaponClass}">${build.weapon}</td>
                <td class="comparison-val-target" style="text-align: right;">${target.weapon} ${recommendedWeapons.length > 1 ? '<br><small style="color: var(--text-muted); font-size: 10px;">(Ou substitutos recomendados)</small>' : ''}</td>
            </tr>
        `;
        
        // 2. Sets (com verificação de múltiplos substitutos e tradução)
        const currentSetsStr = build.sets.join(" / ") || "Nenhum";
        const targetSetsStr = target.sets.join(" / ") || "Não informado";
        
        let setsClass = "comparison-neutral";
        if (targetSetsStr !== "Não informado" && build.sets.length > 0) {
            const recommendedSets = target.all_sets && target.all_sets.length > 0 ? target.all_sets : target.sets;
            const hasSetMatch = build.sets.some(bSet => 
                recommendedSets.some(tSet => checkFuzzyMatch(bSet, tSet))
            );
            setsClass = hasSetMatch ? "comparison-match" : "comparison-mismatch";
        }
        
        html += `
            <tr>
                <td class="comparison-row-title"><i class="fa-solid fa-gem" style="margin-right: 6px;"></i> Sets</td>
                <td class="${setsClass}">${currentSetsStr}</td>
                <td class="comparison-val-target" style="text-align: right;">${targetSetsStr} ${target.all_sets && target.all_sets.length > 1 ? '<br><small style="color: var(--text-muted); font-size: 10px;">(Ou substitutos recomendados)</small>' : ''}</td>
            </tr>
        `;
        
        // 3. Status Alvo (Sands, Goblet, Circlet / Discos 4, 5, 6 / Corpo, Pés, Esfera, Corda)
        const targetStatsKeys = Object.keys(target.stats);
        
        function normalizeStatTerm(str) {
            if (!str) return "";
            return str.toLowerCase()
                .replace(/%/g, "")
                .replace(/\batk\b/g, "ataque")
                .replace(/\batq\b/g, "ataque")
                .replace(/\bhp\b/g, "vida")
                .replace(/\bpv\b/g, "vida")
                .replace(/\bdef\b/g, "defesa")
                .replace(/crítico/g, "crit")
                .replace(/crít/g, "crit")
                .replace(/crítica/g, "crit")
                .replace(/recharge/g, "recarga")
                .replace(/regen/g, "recarga")
                .replace(/recuperação de energia/g, "recarga")
                .replace(/recarga de energia/g, "recarga")
                .replace(/perfuração ratio/g, "perfuração")
                .replace(/taxa de perfuração/g, "perfuração")
                .trim();
        }
        
        if (targetStatsKeys.length > 0) {
            targetStatsKeys.forEach(key => {
                let playerVal = "Não equipado";
                let statClass = "comparison-mismatch";
                
                // Tenta encontrar a peça correspondente ao slot (rótulos agora são padronizados exatamente)
                const matchedPiece = (build.pieces || []).find(p => {
                    const slotLower = p.slot.toLowerCase().trim();
                    const keyLower = key.toLowerCase().trim();
                    return slotLower === keyLower || slotLower.includes(keyLower) || keyLower.includes(slotLower);
                });
                
                if (matchedPiece) {
                    playerVal = matchedPiece.main;
                    const targetValLower = target.stats[key].toLowerCase();
                    const options = targetValLower.split(/[=/>]|\bou\b/).map(s => s.trim());
                    
                    const isMatch = options.some(opt => {
                        if (!opt) return false;
                        const optNorm = normalizeStatTerm(opt);
                        const mainNorm = normalizeStatTerm(matchedPiece.main);
                        return mainNorm.includes(optNorm) || optNorm.includes(mainNorm);
                    });
                    
                    statClass = isMatch ? "comparison-match" : "comparison-mismatch";
                } else {
                    // Fallback para buscar nas estatísticas gerais do jogador
                    playerVal = "Não encontrado";
                    const targetValLower = target.stats[key].toLowerCase();
                    const playerStatsKeys = Object.keys(build.stats || {});
                    const options = targetValLower.split(/[=/>]|\bou\b/).map(s => s.trim());
                    
                    for (const opt of options) {
                        if (!opt) continue;
                        const matchedKey = playerStatsKeys.find(pK => {
                            const pKNorm = normalizeStatTerm(pK);
                            const optNorm = normalizeStatTerm(opt);
                            return pKNorm.includes(optNorm) || optNorm.includes(pKNorm);
                        });
                        
                        if (matchedKey) {
                            playerVal = build.stats[matchedKey];
                            statClass = "comparison-match";
                            break;
                        }
                    }
                }
                
                html += `
                    <tr>
                        <td class="comparison-row-title">• ${key}</td>
                        <td class="${statClass}">${playerVal}</td>
                        <td class="comparison-val-target" style="text-align: right;">${target.stats[key]}</td>
                    </tr>
                `;
            });
        } else {
            html += `
                <tr>
                    <td colspan="3" style="text-align: center; padding: 10px 0; color: var(--text-muted);">Nenhum detalhe de status alvo no guia.</td>
                </tr>
            `;
        }
        
        // 4. Atributos Finais Recomendados (Endgame Stats)
        const endgameStats = target.endgame_stats || {};
        const endgameKeys = Object.keys(endgameStats);
        if (endgameKeys.length > 0) {
            html += `
                <tr style="border-top: 1px solid var(--border-color); background: rgba(255,255,255,0.02);">
                    <td colspan="3" style="padding: 8px 0; font-weight: 700; color: var(--text-secondary); font-size: 11px;"><i class="fa-solid fa-chart-simple" style="margin-right: 6px;"></i> Atributos Finais (Endgame Stats)</td>
                </tr>
            `;
            
            endgameKeys.forEach(key => {
                let playerVal = "Não encontrado";
                let statClass = "comparison-neutral";
                
                const keyLower = key.toLowerCase();
                const playerStatsKeys = Object.keys(build.stats || {});
                
                const termMappings = {
                    "atk": ["ataque", "atk", "atq"],
                    "atq": ["ataque", "atk", "atq"],
                    "hp": ["vida", "hp", "pv", "vida máxima", "vida máx"],
                    "pv": ["vida", "hp", "pv", "vida máxima", "vida máx"],
                    "vida máxima": ["vida", "hp", "pv", "vida máxima", "vida máx"],
                    "def": ["defesa", "def"],
                    "defesa": ["defesa", "def"],
                    "proficiência de anomalia": ["proficiência de anomalia", "anomaly proficiency", "profic"],
                    "recuperação de energia": ["recuperação de energia", "energy regen", "rec. de energia", "taxa de regeneração de energia"],
                    "taxa de regeneração de energia": ["recuperação de energia", "energy regen", "rec. de energia", "taxa de regeneração de energia"],
                    "taxa crítica": ["taxa crítica", "crit rate", "taxa crít", "chance de crit", "taxa crt"],
                    "chance de crit": ["taxa crítica", "crit rate", "taxa crít", "chance de crit", "taxa crt", "chance de crítico"],
                    "dano crítico": ["dano crítico", "crit dmg", "dano crít", "dano crit", "dano crt"],
                    "dano crit": ["dano crítico", "crit dmg", "dano crít", "dano crit", "dano crt"],
                    "recarga de energia": ["recarga de energia", "energy recharge", "recarga"],
                    "efeito de quebra": ["efeito de quebra", "break effect", "quebra"],
                    "proficiência elemental": ["proficiência elemental", "elemental mastery", "proficiência"],
                    "vel": ["vel", "speed", "velocidade"],
                    "velocidade": ["vel", "speed", "velocidade"]
                };
                
                let searchTerms = [keyLower];
                for (const kMap in termMappings) {
                    if (keyLower.includes(kMap) || kMap.includes(keyLower)) {
                        searchTerms = searchTerms.concat(termMappings[kMap]);
                    }
                }
                
                const matchedKey = playerStatsKeys.find(pK => {
                    const pKLower = pK.toLowerCase();
                    return searchTerms.some(term => pKLower.includes(term) || term.includes(pKLower));
                });
                
                if (matchedKey) {
                    playerVal = build.stats[matchedKey];
                    const targetStr = endgameStats[key];
                    const playerNum = parseFloat(playerVal.replace(/[^0-9.]/g, ""));
                    const targetMinNum = parseFloat(targetStr.split(/[-+]/)[0].replace(/[^0-9.]/g, ""));
                    
                    if (!isNaN(playerNum) && !isNaN(targetMinNum)) {
                        statClass = playerNum >= targetMinNum ? "comparison-match" : "comparison-mismatch";
                    }
                }
                
                html += `
                    <tr>
                        <td class="comparison-row-title">• ${key}</td>
                        <td class="${statClass}">${playerVal}</td>
                        <td class="comparison-val-target" style="text-align: right;">${endgameStats[key]}</td>
                    </tr>
                `;
            });
        }
        
        rowsContainer.innerHTML = html;
    } catch(err) {
        console.error("Erro ao carregar comparação de builds:", err);
        rowsContainer.innerHTML = `<tr><td colspan="3" style="text-align: center; padding: 20px 0; color: var(--color-danger);">Erro ao carregar comparação.</td></tr>`;
    }
}

// ==========================================================================
// FUNÇÕES DOS GRÁFICOS SVG DO ROSTER (POR JOGO)
// ==========================================================================
function renderRosterCharts() {
    renderGameCharts("zzz", 50); // ZZZ Nv >= 50
    renderGameCharts("genshin", 70); // Genshin Nv >= 70
    renderGameCharts("hsr", 70); // HSR Nv >= 70
}

function renderGameCharts(gameId, levelThreshold) {
    const chars = (globalRoster[gameId] || []).filter(c => c.level >= levelThreshold);
    const chartsDiv = document.getElementById(`charts-${gameId}`);
    const svgElements = document.getElementById(`chart-elements-${gameId}`);
    const svgRarity = document.getElementById(`chart-rarity-${gameId}`);
    
    if (!chartsDiv || !svgElements || !svgRarity) return;
    
    if (chars.length === 0) {
        chartsDiv.style.display = "none";
        return;
    }
    
    // Exibe o card de estatísticas
    chartsDiv.style.display = "block";
    
    // 1. Gráfico de Raridade
    const rarities = {};
    if (gameId === "zzz") {
        rarities["Classe S"] = 0;
        rarities["Classe A"] = 0;
        chars.forEach(c => {
            const r = String(c.rarity || "").toUpperCase();
            if (r === "S" || r === "5") {
                rarities["Classe S"]++;
            } else {
                rarities["Classe A"]++;
            }
        });
        drawPieChart(`chart-rarity-${gameId}`, `legend-rarity-${gameId}`, [
            { label: "Classe S", value: rarities["Classe S"], color: "#f59e0b" },
            { label: "Classe A", value: rarities["Classe A"], color: "#a78bfa" }
        ]);
    } else {
        rarities["5★"] = 0;
        rarities["4★"] = 0;
        chars.forEach(c => {
            const r = Number(c.rarity);
            if (r === 5 || c.rarity === "5" || r === "S") {
                rarities["5★"]++;
            } else {
                rarities["4★"]++;
            }
        });
        drawPieChart(`chart-rarity-${gameId}`, `legend-rarity-${gameId}`, [
            { label: "5★ Lendário", value: rarities["5★"], color: "#f59e0b" },
            { label: "4★ Épico", value: rarities["4★"], color: "#8b5cf6" }
        ]);
    }
    
    // 2. Gráfico de Elementos
    const elements = {};
    chars.forEach(c => {
        const el = c.element ? c.element.toLowerCase().trim() : "desconhecido";
        elements[el] = (elements[el] || 0) + 1;
    });
    
    const elementColors = {
        "pyro": "#ef4444", "fogo": "#ef4444", "fire": "#ef4444",
        "hydro": "#3b82f6", "ice": "#60a5fa", "gelo": "#60a5fa",
        "anemo": "#10b981", "vento": "#10b981", "wind": "#10b981",
        "electro": "#a78bfa", "electric": "#a78bfa", "raio": "#a78bfa", "lightning": "#a78bfa",
        "dendro": "#22c55e",
        "geo": "#eab308",
        "cryo": "#93c5fd",
        "physical": "#9ca3af", "físico": "#9ca3af",
        "quantum": "#c084fc", "quântico": "#c084fc",
        "imaginary": "#fde047", "imaginário": "#fde047",
        "ether": "#f472b6", "éter": "#f472b6"
    };
    
    const elementData = Object.keys(elements).map(el => {
        const label = el.charAt(0).toUpperCase() + el.slice(1);
        return {
            label: label,
            value: elements[el],
            color: elementColors[el] || "#6b7280"
        };
    }).sort((a, b) => b.value - a.value);
    
    let chartData = elementData;
    if (elementData.length > 5) {
        const main = elementData.slice(0, 4);
        const othersVal = elementData.slice(4).reduce((sum, item) => sum + item.value, 0);
        main.push({ label: "Outros", value: othersVal, color: "#6b7280" });
        chartData = main;
    }
    
    drawPieChart(`chart-elements-${gameId}`, `legend-elements-${gameId}`, chartData);
}

function drawPieChart(svgId, legendId, data) {
    const svg = document.getElementById(svgId);
    const legend = document.getElementById(legendId);
    if (!svg || !legend) return;
    
    svg.innerHTML = "";
    legend.innerHTML = "";
    
    const total = data.reduce((sum, item) => sum + item.value, 0);
    if (total === 0) return;
    
    let startAngle = 0;
    
    if (data.filter(item => item.value > 0).length === 1) {
        const activeItem = data.find(item => item.value > 0);
        svg.innerHTML = `<circle cx="100" cy="100" r="70" fill="${activeItem.color}" />
                         <circle cx="100" cy="100" r="40" fill="#050507" />`;
        
        legend.innerHTML = `<div class="chart-legend-item">
                                <span class="chart-legend-color" style="background: ${activeItem.color}"></span>
                                <span>${activeItem.label}: ${activeItem.value} (${100}%)</span>
                            </div>`;
        return;
    }
    
    data.forEach(item => {
        if (item.value === 0) return;
        
        const angle = (item.value / total) * 360;
        const endAngle = startAngle + angle;
        
        const x1 = 100 + 70 * Math.cos((Math.PI * startAngle) / 180);
        const y1 = 100 + 70 * Math.sin((Math.PI * startAngle) / 180);
        const x2 = 100 + 70 * Math.cos((Math.PI * endAngle) / 180);
        const y2 = 100 + 70 * Math.sin((Math.PI * endAngle) / 180);
        
        const largeArcFlag = angle > 180 ? 1 : 0;
        
        const pathData = `
            M 100 100
            L ${x1} ${y1}
            A 70 70 0 ${largeArcFlag} 1 ${x2} ${y2}
            Z
        `;
        
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute("d", pathData);
        path.setAttribute("fill", item.color);
        path.setAttribute("stroke", "#050507");
        path.setAttribute("stroke-width", "2");
        svg.appendChild(path);
        
        const pct = Math.round((item.value / total) * 100);
        const legendItem = document.createElement("div");
        legendItem.className = "chart-legend-item";
        legendItem.innerHTML = `
            <span class="chart-legend-color" style="background: ${item.color}"></span>
            <span>${item.label}: ${item.value} (${pct}%)</span>
        `;
        legend.appendChild(legendItem);
        
        startAngle = endAngle;
    });
    
    const hole = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    hole.setAttribute("cx", "100");
    hole.setAttribute("cy", "100");
    hole.setAttribute("r", "40");
    hole.setAttribute("fill", "#050507");
    svg.appendChild(hole);
}
