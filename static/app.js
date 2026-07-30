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

// Dicionário de sanitização e abreviação inteligente de nomes de atributos (Stats / Substats)
const STAT_SHORT_NAMES = {
    // Honkai: Star Rail (HSR)
    "Bônus de Dano de Fogo": "Dano Fogo",
    "Bônus de Dano Fogo": "Dano Fogo",
    "Bônus de Dano de Gelo": "Dano Gelo",
    "Bônus de Dano Gelo": "Dano Gelo",
    "Bônus de Dano de Raio": "Dano Raio",
    "Bônus de Dano Raio": "Dano Raio",
    "Bônus de Dano de Vento": "Dano Vento",
    "Bônus de Dano Vento": "Dano Vento",
    "Bônus de Dano Quântico": "Dano Quântico",
    "Bônus de Dano de Quântico": "Dano Quântico",
    "Bônus de Dano Imaginário": "Dano Imaginário",
    "Bônus de Dano de Imaginário": "Dano Imaginário",
    "Bônus de Dano Físico": "Dano Físico",
    "Bônus de Dano de Físico": "Dano Físico",
    "Taxa de Acerto de Efeito": "Acerto Efeito",
    "Resistência a Efeito": "RES Efeito",
    "RES a Efeito": "RES Efeito",
    "Efeito de Quebra": "Quebra",
    "Chance de CRIT": "Taxa CRIT",
    "Taxa de CRIT": "Taxa CRIT",
    "Taxa Crítica": "Taxa CRIT",
    "Dano de CRIT": "Dano CRIT",
    "Dano Crítico": "Dano CRIT",
    "Regeneração de Energia": "Regen. Energia",
    "Taxa de Reg. de Energia": "Regen. Energia",
    "Taxa de Regeneração de Energia": "Regen. Energia",

    // Genshin Impact
    "Proficiência Elemental": "Prof. Element.",
    "Recarga de Energia": "Recarga",
    "Bônus de Dano Anemo": "Dano Anemo",
    "Bônus de Dano Pyro": "Dano Pyro",
    "Bônus de Dano Hydro": "Dano Hydro",
    "Bônus de Dano Electro": "Dano Electro",
    "Bônus de Dano Cryo": "Dano Cryo",
    "Bônus de Dano Geo": "Dano Geo",
    "Bônus de Dano Dendro": "Dano Dendro",
    "Bônus de Dano Elemental": "Dano Elem.",

    // Zenless Zone Zero (ZZZ)
    "Proficiência de Anomalia": "Prof. Anomalia",
    "Taxa de Acerto de Anomalia": "Maest. Anomalia",
    "Maestria de Anomalia": "Maest. Anomalia",
    "Recuperação de Energia": "Recup. Energia",
    "Taxa de Recuperação de Energia": "Recup. Energia",
    "Taxa de Perfuração": "Perfuração",
    "Bônus de Dano Elétrico": "Dano Elétrico",
    "Bônus de Dano de Elétrico": "Dano Elétrico",
    "Bônus de Dano Éter": "Dano Éter",
    "Bônus de Dano de Éter": "Dano Éter",

    // Inglês (API HSR, ZZZ retorna em inglês em alguns idiomas)
    "CRIT Rate": "Taxa CRIT",
    "CRIT DMG": "Dano CRIT",
    "Effect Hit Rate": "Acerto Efeito",
    "Effect RES": "RES Efeito",
    "Break Effect": "Quebra",
    "Energy Regeneration Rate": "Regen. Energia",
    "Outgoing Healing Boost": "Cura Bônus",
    "Physical DMG Boost": "Dano Físico",
    "Fire DMG Boost": "Dano Fogo",
    "Ice DMG Boost": "Dano Gelo",
    "Lightning DMG Boost": "Dano Raio",
    "Wind DMG Boost": "Dano Vento",
    "Quantum DMG Boost": "Dano Quântico",
    "Imaginary DMG Boost": "Dano Imaginário",
    // ZZZ English
    "Anomaly Proficiency": "Prof. Anomalia",
    "Anomaly Mastery": "Maest. Anomalia",
    "PEN Ratio": "Perfuração",
    "Energy Regen": "Regen. Energia",
    "Impact": "Impacto",
    // Genshin English
    "Elemental Mastery": "Prof. Element.",
    "Energy Recharge": "Recarga",
    "Healing Bonus": "Cura Bônus",
    "Anemo DMG Bonus": "Dano Anemo",
    "Pyro DMG Bonus": "Dano Pyro",
    "Hydro DMG Bonus": "Dano Hydro",
    "Electro DMG Bonus": "Dano Electro",
    "Cryo DMG Bonus": "Dano Cryo",
    "Geo DMG Bonus": "Dano Geo",
    "Dendro DMG Bonus": "Dano Dendro"
};

function sanitizeStatName(statText) {
    if (!statText) return "";
    let s = String(statText).trim();
    if (STAT_SHORT_NAMES[s]) return STAT_SHORT_NAMES[s];
    for (const [k, v] of Object.entries(STAT_SHORT_NAMES)) {
        if (s.includes(k)) {
            s = s.replace(k, v);
        }
    }
    s = s.replace(/Bônus de Dano (?:de )?([A-Za-zÀ-ÿ]+)/gi, 'Dano $1');
    return s;
}

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
        let activeRarityFilter = "all";
        let searchQuery = "";
        
        const searchInput = document.querySelector(`.search-input[data-game="${gameId}"]`);
        
        const renderCards = () => {
            gallery.innerHTML = "";
            
            // Filtra a lista local baseado na busca de texto, elemento E raridade
            const filtered = roster.filter(char => {
                const matchesSearch = char.name.toLowerCase().includes(searchQuery);
                const matchesElement = activeElementFilter === "all" || 
                    (char.element || "").toLowerCase() === activeElementFilter.toLowerCase();
                
                let matchesRarity = true;
                if (activeRarityFilter !== "all") {
                    const rarityNum = Number(char.rarity);
                    const isFiveStar = rarityNum === 5 || char.rarity === "5" || String(char.rarity).toUpperCase() === "S";
                    if (activeRarityFilter === "5") {
                        matchesRarity = isFiveStar;
                    } else if (activeRarityFilter === "4") {
                        matchesRarity = !isFiveStar;
                    }
                }
                
                return matchesSearch && matchesElement && matchesRarity;
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
                        ${char.overall_grade ? `<div class="char-grade-badge badge-${char.overall_grade.toLowerCase()}">${char.overall_grade}</div>` : ''}
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
        const filterContainer = document.querySelector(`.element-filters[data-game="${gameId}"]:not(.rarity-filters)`);
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
        
        // Configura ouvintes de clique nos botões de filtro de raridade
        const rarityContainer = document.querySelector(`.rarity-filters[data-game="${gameId}"]`);
        if (rarityContainer) {
            const rarityBtns = rarityContainer.querySelectorAll(".filter-btn");
            rarityBtns.forEach(btn => {
                // Remove listeners anteriores
                const newBtn = btn.cloneNode(true);
                btn.parentNode.replaceChild(newBtn, btn);
            });
            
            // Adiciona novos listeners aos botões clonados
            const freshRarityBtns = rarityContainer.querySelectorAll(".filter-btn");
            freshRarityBtns.forEach(btn => {
                btn.addEventListener("click", () => {
                    freshRarityBtns.forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    activeRarityFilter = btn.getAttribute("data-rarity");
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
    window.currentInspectorChar = char;
    window.currentInspectorGameId = gameId;

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
    
    // Configura e limpa o card da Calculadora de Ascensão
    const ascResults = document.getElementById("ins-asc-results");
    const ascTargetSelect = document.getElementById("ins-asc-target");
    const btnCalculateAsc = document.getElementById("btn-ins-asc-calculate");
    
    ascResults.style.display = "none";
    ascResults.innerHTML = "";
    
    // Configura opções do nível alvo baseadas no jogo (90 para Genshin, 80 para HSR/ZZZ)
    ascTargetSelect.value = gameId === "genshin" ? "90" : "80";
    
    btnCalculateAsc.onclick = async () => {
        const targetLvl = parseInt(ascTargetSelect.value);
        if (char.level >= targetLvl) {
            ascResults.style.display = "block";
            ascResults.innerHTML = `<span style="color: #10b981; font-weight: 500;"><i class="fa-solid fa-circle-check"></i> Este personagem já está no nível ${char.level} ou superior!</span>`;
            return;
        }
        
        btnCalculateAsc.disabled = true;
        btnCalculateAsc.innerText = "Calculando...";
        
        try {
            const mRes = await fetch("/api/materials/calculate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    game_id: gameId,
                    char_name: char.name,
                    current_level: parseInt(char.level),
                    target_level: targetLvl
                })
            });
            const mData = await mRes.json();
            ascResults.style.display = "block";
            
            if (mData && mData.xp_needed !== undefined) {
                ascResults.innerHTML = `
                    <div style="margin-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 4px; font-weight: 600; color: var(--text-primary);">
                        📋 Custos Estimados (${char.level} ➔ ${targetLvl})
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 4px; padding-left: 4px;">
                        <div>• <strong>XP necessária:</strong> ${mData.xp_needed.toLocaleString()} (~${mData.xp_books_purple} livros roxos)</div>
                        <div>• <strong>${mData.currency_name}:</strong> ${mData.currency_needed.toLocaleString()}</div>
                        ${mData.boss_items_needed > 0 ? `<div>• <strong>${mData.boss_item_name}:</strong> ${mData.boss_items_needed} unidades</div>` : ''}
                    </div>
                `;
            } else {
                ascResults.innerHTML = `<span style="color: var(--color-danger);">Erro nos dados de retorno.</span>`;
            }
        } catch (err) {
            ascResults.style.display = "block";
            ascResults.innerHTML = `<span style="color: var(--color-danger);">Erro: ${err.message}</span>`;
        }
        btnCalculateAsc.disabled = false;
        btnCalculateAsc.innerText = "Calcular";
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
        
        // 3. Renderiza Painel de Status Finais (Combat Stats) - Glassmorphism Premium
        const statsGrid = document.getElementById("ins-stats-grid");
        statsGrid.innerHTML = "";
        
        const statsKeys = Object.keys(build.stats || {});
        if (statsKeys.length > 0) {
            // Define quais stats são "críticos" (destaque dourado/âmbar)
            const criticalStats = ['Taxa CRIT', 'Dano CRIT', 'CRIT Rate', 'CRIT DMG', 'SPD', 'VEL', 'Velocidade'];
            // Ordena: HP/ATK/DEF/SPD primeiro, depois CRIT, depois resto
            const orderedPriority = ['HP', 'ATQ', 'ATK', 'DEF', 'SPD', 'VEL', 'Taxa CRIT', 'CRIT Rate', 'Dano CRIT', 'CRIT DMG'];
            const sortedKeys = [...statsKeys].sort((a, b) => {
                const ai = orderedPriority.findIndex(p => a.includes(p) || a === p);
                const bi = orderedPriority.findIndex(p => b.includes(p) || b === p);
                if (ai === -1 && bi === -1) return 0;
                if (ai === -1) return 1;
                if (bi === -1) return -1;
                return ai - bi;
            });
            
            sortedKeys.forEach(key => {
                const isCrit = criticalStats.some(cs => key.includes(cs) || key === cs);
                const statCard = document.createElement("div");
                statCard.className = "stat-card" + (isCrit ? " stat-card--crit" : "");
                statCard.innerHTML = `
                    <span class="stat-label">${sanitizeStatName(key)}</span>
                    <span class="stat-value${isCrit ? ' stat-value--crit' : ''}">${build.stats[key]}</span>
                `;
                statsGrid.appendChild(statCard);
            });
        } else {
            statsGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 16px 0; color: var(--text-muted); font-size: 12px;">
                    <i class="fa-solid fa-rotate" style="margin-bottom: 8px; font-size: 24px; opacity: 0.4; display: block;"></i>
                    Status finais disponíveis após próxima sincronização do Roster.
                </div>
            `;
        }
        
        // Atualiza badge de contagem de stats
        const statsCountEl = document.getElementById("ins-stats-count");
        if (statsCountEl) {
            statsCountEl.textContent = statsKeys.length > 0 ? `(${statsKeys.length} atributos)` : "";
        }
        
        // Merge stats na referência do char atual para o canvas export
        if (statsKeys.length > 0 && window.currentInspectorChar) {
            window.currentInspectorChar.stats = build.stats;
        }
        
        // NOVO: Renderiza Comparação de Metas Gerais (Benchmarks)
        const benchmarksCard = document.getElementById("ins-benchmarks-card");
        const benchmarksList = document.getElementById("ins-benchmarks-list");
        
        if (benchmarksCard && benchmarksList) {
            benchmarksCard.style.display = "none";
            benchmarksList.innerHTML = "";
            
            if (statsKeys.length > 0) {
                try {
                    const evalRes = await fetch(`/api/evaluate-stats/${gameId}/${encodeURIComponent(char.name)}`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(build.stats)
                    });
                    if (evalRes.ok) {
                        const evalData = await evalRes.json();
                        if (evalData && evalData.length > 0) {
                            benchmarksCard.style.display = "block";
                            benchmarksList.innerHTML = evalData.map(item => {
                                const isGood = item.status === "GOOD";
                                const color = isGood ? "#10b981" : "#fca5a5";
                                const icon = isGood ? '<i class="fa-solid fa-circle-check"></i>' : '<i class="fa-solid fa-triangle-exclamation"></i>';
                                return `
                                    <div style="display: flex; align-items: flex-start; gap: 6px; color: ${color}; font-size: 11px; margin-bottom: 4px;">
                                        <span style="font-size: 11px; margin-top: 1px;">${icon}</span>
                                        <div>
                                            <strong style="color: var(--text-primary); font-size: 11px;">${item.stat}:</strong> ${item.message}
                                        </div>
                                    </div>
                                `;
                            }).join("");
                        }
                    }
                } catch (err) {
                    console.error("Erro ao avaliar metas gerais:", err);
                }
            }
        }
        
        // 4. Renderiza Peças Individuais combinando RAG MD e Local JSON
        const piecesList = document.getElementById("ins-relic-pieces");
        piecesList.innerHTML = "";
        
        // Elemento visual no topo com a Nota Geral da Build
        const overallGrade = (char.overall_grade || "D").toUpperCase();
        const overallScore = char.overall_score !== undefined ? char.overall_score : 0.0;
        const gradeClass = `badge-${overallGrade.toLowerCase()}`;
        const equippedInfo = (char.equipped_pieces !== undefined && char.max_pieces !== undefined) 
            ? ` (${char.equipped_pieces}/${char.max_pieces} peças equipadas)` 
            : '';
        
        const banner = document.createElement("div");
        banner.className = "overall-build-banner";
        banner.style.display = "flex";
        banner.style.justifyContent = "space-between";
        banner.style.alignItems = "center";
        banner.innerHTML = `
            <div>
                <div class="overall-build-title">
                    <i class="fa-solid fa-award" style="color: #f59e0b;"></i> Nota Geral da Build${equippedInfo}
                </div>
                <div style="margin-top: 6px;">
                    <button class="trigger-export-card action-btn" style="padding: 5px 12px; font-size: 11px; background: linear-gradient(135deg, rgba(245, 158, 11, 0.25), rgba(217, 119, 6, 0.35)); border: 1px solid rgba(245, 158, 11, 0.6); color: #fbbf24; border-radius: 6px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; font-weight: 600;">
                        <i class="fa-solid fa-camera"></i> Gerar Imagem da Build (Splash Art)
                    </button>
                </div>
            </div>
            <div class="overall-badge ${gradeClass}">
                ${overallGrade} (${overallScore} pts)
            </div>
        `;
        piecesList.appendChild(banner);
        
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
                        const cleanSub = sanitizeStatName(sub);
                        let name = cleanSub;
                        let value = "";
                        if (cleanSub.includes(":")) {
                            const parts = cleanSub.split(":");
                            name = parts[0].trim();
                            value = parts[1].trim();
                        } else if (cleanSub.includes("(")) {
                            const parts = cleanSub.split("(");
                            name = parts[0].trim();
                            value = parts[1].replace(")", "").trim();
                        }
                        
                        if (value) {
                            subsHtml += `
                                <div class="sub-item">
                                    <span class="sub-label">${name}</span>
                                    <span class="sub-value">${value}</span>
                                </div>
                            `;
                        } else {
                            subsHtml += `
                                <div class="sub-item">
                                    <span class="sub-label">${name}</span>
                                </div>
                            `;
                        }
                    });
                    subsHtml += `</div>`;
                } else {
                    subsHtml = `<span class="text-muted" style="font-size: 10px;">Sem substatus</span>`;
                }
                
                let gradeHtml = "";
                if (equivalentLocalPiece && equivalentLocalPiece.grade) {
                    gradeHtml = `<span class="badge-relic badge-relic-${equivalentLocalPiece.grade.toLowerCase()}">${equivalentLocalPiece.grade}</span><span style="font-size: 10px; color: var(--text-secondary); margin-left: 6px; font-weight: 500;">Score: ${equivalentLocalPiece.score || 0}</span>`;
                }
                
                const cleanMain = sanitizeStatName(piece.main);
                row.innerHTML = `
                    ${iconHtml}
                    <div class="relic-piece-details" style="flex: 1;">
                        <div class="relic-piece-title" style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; margin-bottom: 4px;">
                            <div>
                                <span class="piece-slot" style="font-weight: 600; color: var(--text-muted); margin-right: 4px;">[${piece.slot}]</span>
                                <span class="piece-name" style="font-weight: 500;">${piece.name}</span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 4px;">
                                ${gradeHtml}
                            </div>
                        </div>
                        <div class="piece-main" style="font-size: 11px; color: var(--text-secondary); margin-bottom: 6px;">Principal: <span class="main-stat-pill">${cleanMain}</span></div>
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

// Funções globais auxiliares do Montador de Times
let selectedTeam = [];

function updateTeamBuilderGrid(gameId) {
    const grid = document.getElementById("team-characters-grid");
    if (!grid) return;
    
    selectedTeam = [];
    const btn = document.getElementById("team-analyze-btn");
    if (btn) btn.disabled = true;
    
    const roster = globalRoster[gameId] || [];
    if (roster.length === 0) {
        grid.innerHTML = `<div style="grid-column: span 4; font-size: 10px; color: var(--text-secondary); text-align: center; padding: 12px;">Roster do ${gameId.toUpperCase()} não sincronizado.</div>`;
        return;
    }
    
    grid.innerHTML = roster.map(char => {
        const safeFn = getSafeFileName(char.name);
        const localAvatarPath = `/assets/avatars/${gameId}/${safeFn}`;
        return `
            <div class="team-char-select-card" data-name="${char.name}" style="position: relative; aspect-ratio: 1; cursor: pointer; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06); overflow: hidden; background: rgba(0,0,0,0.3); transition: all 0.2s;" onclick="toggleCharacterInTeam(this, '${char.name.replace(/'/g, "\\'")}', '${gameId}')">
                <img src="${localAvatarPath}" onerror="this.onerror=null; this.src='${char.icon || '/assets/config_icon.png'}';" style="width: 100%; height: 100%; object-fit: cover;" alt="${char.name}">
                <div class="char-select-overlay" style="position: absolute; inset: 0; background: rgba(167, 139, 250, 0.45); display: none; align-items: center; justify-content: center; font-size: 14px; color: #fff; text-shadow: 0 1px 3px rgba(0,0,0,0.5);">
                    <i class="fa-solid fa-check"></i>
                </div>
                <div class="char-select-name" style="position: absolute; bottom: 0; left: 0; right: 0; font-size: 8px; background: rgba(0,0,0,0.85); color: #fff; text-align: center; padding: 2px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: 500;">${char.name}</div>
            </div>
        `;
    }).join('');
}

function toggleCharacterInTeam(element, charName, gameId) {
    const overlay = element.querySelector(".char-select-overlay");
    const maxSelect = gameId === "zzz" ? 3 : 4;
    
    if (selectedTeam.includes(charName)) {
        selectedTeam = selectedTeam.filter(name => name !== charName);
        element.style.borderColor = "rgba(255,255,255,0.06)";
        element.style.boxShadow = "none";
        overlay.style.display = "none";
    } else {
        if (selectedTeam.length >= maxSelect) {
            alert(`Você só pode selecionar até ${maxSelect} personagens para o time de ${gameId.toUpperCase()}!`);
            return;
        }
        selectedTeam.push(charName);
        element.style.borderColor = "#a78bfa";
        element.style.boxShadow = "0 0 8px rgba(167, 139, 250, 0.3)";
        overlay.style.display = "flex";
    }
    
    const btn = document.getElementById("team-analyze-btn");
    if (btn) btn.disabled = selectedTeam.length === 0;
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
// Mapeamento de nomes de elementos localizados e oficiais por jogo
const ELEMENT_LABELS = {
    "zzz": {
        "electric": "Elétrico",
        "ether": "Éter",
        "fire": "Fogo",
        "ice": "Gelo",
        "physical": "Físico",
        "wind": "Vento"
    },
    "hsr": {
        "fire": "Fogo",
        "ice": "Gelo",
        "imaginary": "Imaginário",
        "lightning": "Raio",
        "physical": "Físico",
        "quantum": "Quântico",
        "wind": "Vento"
    },
    "genshin": {
        "pyro": "Pyro",
        "hydro": "Hydro",
        "anemo": "Anemo",
        "electro": "Electro",
        "dendro": "Dendro",
        "cryo": "Cryo",
        "geo": "Geo"
    }
};

function getElementLabel(gameId, elementKey) {
    const gameLabels = ELEMENT_LABELS[gameId] || {};
    return gameLabels[elementKey] || elementKey.charAt(0).toUpperCase() + elementKey.slice(1);
}

function renderRosterCharts() {
    renderGameCharts("zzz");
    renderGameCharts("genshin");
    renderGameCharts("hsr");
}

function renderGameCharts(gameId) {
    const chars = globalRoster[gameId] || [];
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
        const label = getElementLabel(gameId, el);
        return {
            label: label,
            value: elements[el],
            color: elementColors[el] || "#6b7280"
        };
    }).sort((a, b) => b.value - a.value);
    
    drawPieChart(`chart-elements-${gameId}`, `legend-elements-${gameId}`, elementData);
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

function getZzzPrydwenSlug(name) {
    if (!name) return "";
    const clean = String(name).toLowerCase().trim();
    const specialMap = {
        "anby demara": "anby-demara",
        "anby": "anby-demara",
        "anton ivanov": "anton",
        "astra yao": "astra-yao",
        "ben bigger": "ben",
        "billy kid": "billy-kid",
        "billy": "billy-kid",
        "grace howard": "grace-howard",
        "grace": "grace-howard",
        "hoshimi miyabi": "miyabi",
        "asaba harumasa": "harumasa",
        "jane doe": "jane-doe",
        "koleda belobog": "koleda",
        "nicole demara": "nicole-demara",
        "nicole": "nicole-demara",
        "piper wheel": "piper",
        "seth lowell": "seth",
        "soldier 11": "soldier-11",
        "von lycaon": "lycaon",
        "zhu yuan": "zhu-yuan"
    };
    if (specialMap[clean]) return specialMap[clean];
    for (const [k, v] of Object.entries(specialMap)) {
        if (clean === k || clean.includes(k)) return v;
    }
    return clean.replace(/\s+/g, '-').replace(/_/g, '-');
}

// ==========================================
// GERADOR DE CARD DE BUILD EM ALTA RESOLUÇÃO (PNG)
// ==========================================

async function generateBuildCardCanvas(char, gameId) {
    const canvas = document.createElement("canvas");
    const width = 1200;
    const height = 675;
    canvas.width = width * 2;   // 2x scale for 4K / Retina sharpness
    canvas.height = height * 2;
    const ctx = canvas.getContext("2d");
    ctx.scale(2, 2);

    const elemColors = {
        anemo: { primary: "#10b981", accent: "#059669", bg: "rgba(16, 185, 129, 0.15)", pill: "#059669" },
        pyro: { primary: "#ef4444", accent: "#dc2626", bg: "rgba(239, 68, 68, 0.15)", pill: "#dc2626" },
        hydro: { primary: "#3b82f6", accent: "#2563eb", bg: "rgba(59, 130, 246, 0.15)", pill: "#2563eb" },
        electro: { primary: "#a855f7", accent: "#9333ea", bg: "rgba(168, 85, 247, 0.15)", pill: "#9333ea" },
        cryo: { primary: "#38bdf8", accent: "#0284c7", bg: "rgba(56, 189, 248, 0.15)", pill: "#0284c7" },
        geo: { primary: "#f59e0b", accent: "#d97706", bg: "rgba(245, 158, 11, 0.15)", pill: "#d97706" },
        dendro: { primary: "#84cc16", accent: "#65a30d", bg: "rgba(132, 204, 22, 0.15)", pill: "#65a30d" },
        quantum: { primary: "#6366f1", accent: "#4f46e5", bg: "rgba(99, 102, 241, 0.15)", pill: "#4f46e5" },
        imaginary: { primary: "#eab308", accent: "#ca8a04", bg: "rgba(234, 179, 8, 0.15)", pill: "#ca8a04" },
        physical: { primary: "#94a3b8", accent: "#64748b", bg: "rgba(148, 163, 184, 0.15)", pill: "#64748b" },
        ether: { primary: "#c084fc", accent: "#a855f7", bg: "rgba(192, 132, 252, 0.15)", pill: "#a855f7" },
        fire: { primary: "#ef4444", accent: "#dc2626", bg: "rgba(239, 68, 68, 0.15)", pill: "#dc2626" },
        ice: { primary: "#38bdf8", accent: "#0284c7", bg: "rgba(56, 189, 248, 0.15)", pill: "#0284c7" },
        electric: { primary: "#a855f7", accent: "#9333ea", bg: "rgba(168, 85, 247, 0.15)", pill: "#9333ea" },
        wind: { primary: "#10b981", accent: "#059669", bg: "rgba(16, 185, 129, 0.15)", pill: "#059669" }
    };

    const elemKey = (char.element || "").toLowerCase();
    const theme = elemColors[elemKey] || elemColors.physical;

    function drawRoundedRect(x, y, w, h, r, fillStyle, strokeStyle, lineWidth = 1) {
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + w - r, y);
        ctx.quadraticCurveTo(x + w, y, x + w, y + r);
        ctx.lineTo(x + w, y + h - r);
        ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
        ctx.lineTo(x + r, y + h);
        ctx.quadraticCurveTo(x, y + h, x, y + h - r);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.closePath();
        if (fillStyle) {
            ctx.fillStyle = fillStyle;
            ctx.fill();
        }
        if (strokeStyle) {
            ctx.strokeStyle = strokeStyle;
            ctx.lineWidth = lineWidth;
            ctx.stroke();
        }
    }

    function loadImage(url) {
        return new Promise((resolve) => {
            if (!url) return resolve(null);
            let finalUrl = url;
            if (url.startsWith("http://") || url.startsWith("https://")) {
                finalUrl = `/api/proxy_image?url=${encodeURIComponent(url)}`;
            }
            const img = new Image();
            img.crossOrigin = "anonymous";
            img.onload = () => resolve(img);
            img.onerror = () => {
                if (finalUrl !== url) {
                    const fallbackImg = new Image();
                    fallbackImg.onload = () => resolve(fallbackImg);
                    fallbackImg.onerror = () => resolve(null);
                    fallbackImg.src = url;
                } else {
                    resolve(null);
                }
            };
            img.src = finalUrl;
        });
    }

    const logoImg = (await loadImage("/assets/logo.svg")) || (await loadImage("/assets/logo.ico"));

    // 1. Fundo do Banner Landscape (16:9)
    const bgGrad = ctx.createLinearGradient(0, 0, width, height);
    bgGrad.addColorStop(0, "#080b13");
    bgGrad.addColorStop(0.5, "#0f172a");
    bgGrad.addColorStop(1, "#05070e");
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, width, height);

    const glowGrad = ctx.createRadialGradient(220, 300, 20, 220, 300, 500);
    glowGrad.addColorStop(0, theme.bg.replace("0.15", "0.45"));
    glowGrad.addColorStop(1, "transparent");
    ctx.fillStyle = glowGrad;
    ctx.fillRect(0, 0, width, height);

    // Dados de notas e contagem de peças
    const overallGrade = (char.overall_grade || "D").toUpperCase();
    const overallScore = char.overall_score !== undefined ? char.overall_score : 0.0;
    const equippedPieces = char.equipped_pieces !== undefined ? char.equipped_pieces : (char.relics ? char.relics.length : 0);
    const maxPieces = char.max_pieces || (gameId === 'genshin' ? 5 : 6);

    const gradeColors = {
        SSS: { bg: "rgba(245, 158, 11, 0.25)", border: "#f59e0b", text: "#fbbf24" },
        SS: { bg: "rgba(236, 72, 153, 0.25)", border: "#ec4899", text: "#f472b6" },
        S: { bg: "rgba(245, 158, 11, 0.25)", border: "#f59e0b", text: "#fbbf24" },
        A: { bg: "rgba(139, 92, 246, 0.25)", border: "#8b5cf6", text: "#c084fc" },
        B: { bg: "rgba(59, 130, 246, 0.25)", border: "#3b82f6", text: "#60a5fa" },
        C: { bg: "rgba(107, 114, 128, 0.25)", border: "#6b7280", text: "#9ca3af" },
        D: { bg: "rgba(107, 114, 128, 0.25)", border: "#6b7280", text: "#9ca3af" }
    };
    const gc = gradeColors[overallGrade] || gradeColors.D;

    // ==========================================
    // 2. HERO COLUMN CONTINUA (COLUNA DA ESQUERDA)
    // ==========================================
    const hx = 30, hy = 25, hw = 390, hh = 615;
    
    // Container base da Hero Column
    drawRoundedRect(hx, hy, hw, hh, 16, "rgba(15, 23, 42, 0.65)", "rgba(255, 255, 255, 0.12)", 1.5);

    // Carregamento da Splash Art / Gacha Art
    let splashUrl = char.gacha_art || char.splash_art || char.portrait || char.draw || char.art_url || char.gacha_card || char.gacha_slice || char.display_image || char.image || char.banner_icon;
    if (gameId === 'hsr' && char.id && !char.gacha_art) {
        splashUrl = `https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/character_portrait/${char.id}.png`;
    } else if (gameId === 'zzz') {
        const isZzzSkin = splashUrl && splashUrl.split("_").some(part => /^\d{7,}$/.test(part.replace(".png", "")));
        if (!isZzzSkin) {
            const zzzSlug = getZzzPrydwenSlug(char.name);
            const zzzPrydwenUrl = zzzSlug ? `https://cdn.prydwen.gg/images/zenless-zone-zero/characters/${zzzSlug}_full.webp` : "";
            if (!splashUrl || splashUrl.includes("role_vertical_painting") || splashUrl.includes("role_square_avatar")) {
                splashUrl = zzzPrydwenUrl || splashUrl;
            }
        }
    } else if (gameId === 'genshin') {
        const checkIcon = char.gacha_art || char.icon || splashUrl || "";
        if (checkIcon.includes("UI_AvatarIcon_")) {
            if (checkIcon.includes("Costume")) {
                splashUrl = checkIcon.replace("UI_AvatarIcon_", "UI_Costume_");
            } else {
                splashUrl = checkIcon.replace("UI_AvatarIcon_", "UI_Gacha_AvatarImg_");
            }
        } else if (checkIcon.includes("UI_Costume_")) {
            splashUrl = checkIcon;
        } else if (!splashUrl && char.icon && char.icon.includes("UI_AvatarIcon_")) {
            if (char.icon.includes("Costume")) {
                splashUrl = char.icon.replace("UI_AvatarIcon_", "UI_Costume_");
            } else {
                splashUrl = char.icon.replace("UI_AvatarIcon_", "UI_Gacha_AvatarImg_");
            }
        }
    }

    const safeFn = getSafeFileName(char.name);
    const localAvatarUrl = `/assets/avatars/${gameId}/${safeFn}`;

    let isAvatarFallback = false;
    let charImg = await loadImage(splashUrl);

    if (!charImg && gameId === 'zzz' && char.name) {
        const zzzSlug = getZzzPrydwenSlug(char.name);
        if (zzzSlug) {
            charImg = await loadImage(`https://cdn.prydwen.gg/images/zenless-zone-zero/characters/${zzzSlug}_full.webp`);
        }
    }

    if (!charImg && splashUrl && splashUrl.includes("UI_Gacha_AvatarIcon_")) {
        charImg = await loadImage(splashUrl.replace("UI_Gacha_AvatarIcon_", "UI_Gacha_AvatarImg_"));
    }

    if (!charImg && gameId === 'genshin' && (char.icon || char.gacha_art)) {
        let enkaGacha = char.gacha_art || char.icon;
        if (enkaGacha.includes("UI_AvatarIcon_")) {
            if (enkaGacha.includes("Costume")) {
                enkaGacha = enkaGacha.replace("UI_AvatarIcon_", "UI_Costume_");
            } else {
                enkaGacha = enkaGacha.replace("UI_AvatarIcon_", "UI_Gacha_AvatarImg_");
            }
        }
        if (enkaGacha !== char.icon) {
            charImg = await loadImage(enkaGacha);
        }
    }

    if (!charImg) {
        charImg = await loadImage(char.icon) || await loadImage(localAvatarUrl);
        isAvatarFallback = true;
    } else {
        const imgRatio = charImg.width / charImg.height;
        if ((charImg.width <= 300 && charImg.height <= 300 && imgRatio >= 0.75 && imgRatio <= 1.3) ||
            (splashUrl && (splashUrl.includes("role_square_avatar") || splashUrl.includes("UI_AvatarIcon_")) && !splashUrl.includes("Gacha") && !splashUrl.includes("painting") && !splashUrl.includes("Costume"))) {
            isAvatarFallback = true;
        }
    }

    if (charImg) {
        ctx.save();
        ctx.beginPath();
        if (ctx.roundRect) {
            ctx.roundRect(hx + 2, hy + 2, hw - 4, hh - 4, 14);
        } else {
            ctx.rect(hx + 2, hy + 2, hw - 4, hh - 4);
        }
        ctx.clip();

        const imgW = charImg.width;
        const imgH = charImg.height;
        const imgRatio = imgW / imgH;
        const targetW = hw - 4;
        const targetH = hh - 4;

        if (isAvatarFallback) {
            // RENDERING ELEGANTE PARA FALLBACK DE AVATAR (NÃO ESTICA O ROSTO!)
            const avatarBg = ctx.createRadialGradient(hx + hw / 2, hy + 220, 20, hx + hw / 2, hy + 220, 260);
            avatarBg.addColorStop(0, theme.primary + "44");
            avatarBg.addColorStop(1, "rgba(15, 23, 42, 0.95)");
            ctx.fillStyle = avatarBg;
            ctx.fillRect(hx, hy, hw, hh);

            const avatarRadius = 90;
            const avatarCx = hx + hw / 2;
            const avatarCy = hy + 220;

            ctx.save();
            ctx.beginPath();
            ctx.arc(avatarCx, avatarCy, avatarRadius + 5, 0, Math.PI * 2);
            ctx.fillStyle = theme.primary;
            ctx.shadowColor = theme.primary;
            ctx.shadowBlur = 18;
            ctx.fill();

            ctx.beginPath();
            ctx.arc(avatarCx, avatarCy, avatarRadius, 0, Math.PI * 2);
            ctx.clip();
            ctx.drawImage(charImg, avatarCx - avatarRadius, avatarCy - avatarRadius, avatarRadius * 2, avatarRadius * 2);
            ctx.restore();
        } else {
            // RENDERING PARA PORTRAITS E SPLASH ARTS (Genshin, HSR, ZZZ)
            const cropRatio = imgW / imgH;
            let drawW, drawH, drawX, drawY;

            // Escala a altura para preencher todo o container (611px), garantindo o personagem grande e em destaque
            drawH = targetH;
            drawW = targetH * cropRatio;
            drawX = (hx + 2) - (drawW - targetW) / 2;
            drawY = hy + 2;

            ctx.drawImage(charImg, 0, 0, imgW, imgH, drawX, drawY, drawW, drawH);
        }

        // Gradiente escuro no topo para leitura do header
        const topGlow = ctx.createLinearGradient(hx, hy, hx, hy + 140);
        topGlow.addColorStop(0, "rgba(5, 8, 16, 0.90)");
        topGlow.addColorStop(1, "transparent");
        ctx.fillStyle = topGlow;
        ctx.fillRect(hx, hy, hw, 140);

        // Gradiente escuro intenso na base para fusão com a Arma
        const bottomGlow = ctx.createLinearGradient(hx, hy + 200, hx, hy + hh);
        bottomGlow.addColorStop(0, "transparent");
        bottomGlow.addColorStop(0.65, "rgba(9, 13, 22, 0.80)");
        bottomGlow.addColorStop(1, "rgba(9, 13, 22, 0.98)");
        ctx.fillStyle = bottomGlow;
        ctx.fillRect(hx, hy + 200, hw, hh - 200);

        ctx.restore();
    } else {
        ctx.font = "bold 64px sans-serif";
        ctx.fillStyle = theme.primary;
        ctx.textAlign = "center";
        ctx.fillText(char.name.charAt(0), hx + hw / 2, hy + 250);
        ctx.textAlign = "left";
    }

    // Header Sobreposto no Topo da Hero Column
    const gameNames = { hsr: "HONKAI: STAR RAIL", genshin: "GENSHIN IMPACT", zzz: "ZENLESS ZONE ZERO" };
    ctx.font = "bold 11px sans-serif";
    ctx.fillStyle = theme.primary;
    
    let headerTextX = hx + 18;
    if (logoImg) {
        ctx.drawImage(logoImg, hx + 18, hy + 13, 16, 16);
        headerTextX = hx + 40;
    }
    ctx.fillText((gameNames[gameId] || gameId.toUpperCase()) + " • CABEÇA DE DROID", headerTextX, hy + 26);

    ctx.font = "bold 26px sans-serif";
    ctx.fillStyle = "#ffffff";
    ctx.fillText(char.name.length > 15 ? char.name.substring(0, 15) + "..." : char.name, hx + 18, hy + 56);

    ctx.font = "500 13px sans-serif";
    ctx.fillStyle = "#cbd5e1";
    const elemName = (char.element || "Físico").toUpperCase();
    ctx.fillText(`Nv. ${char.level} • ${elemName}`, hx + 18, hy + 76);

    // Pill de Constelação / Eidolon em Vermelho Crimson (Red Badge)
    const rankStr = char.rank_str || "C0";
    drawRoundedRect(hx + 18, hy + 86, 56, 24, 6, "rgba(225, 29, 72, 0.9)", "#f43f5e", 1);
    ctx.font = "bold 12px sans-serif";
    ctx.fillStyle = "#ffffff";
    ctx.textAlign = "center";
    ctx.fillText(rankStr, hx + 46, hy + 102);
    ctx.textAlign = "left";

    // Badge de Nota Geral no canto superior direito da Hero Column
    drawRoundedRect(hx + hw - 108, hy + 16, 92, 42, 10, gc.bg, gc.border, 1.5);
    ctx.font = "bold 13px sans-serif";
    ctx.fillStyle = gc.text;
    ctx.textAlign = "center";
    ctx.fillText(`NOTA ${overallGrade}`, hx + hw - 62, hy + 34);

    ctx.font = "500 10px sans-serif";
    ctx.fillStyle = "#e2e8f0";
    ctx.fillText(`${overallScore} pts`, hx + hw - 62, hy + 49);
    ctx.textAlign = "left";

    // ==========================================
    // 2.5 PAINEL DE STATUS FINAIS (COMBAT STATS) — Hero Column
    // ==========================================
    const charStats = char.stats || {};
    const statKeys = Object.keys(charStats);
    if (statKeys.length > 0) {
        const statsPanelX = hx + 12;
        const statsPanelW = hw - 24;
        const statsPanelH = 110;
        const statsPanelY = hy + hh - 122 - statsPanelH - 12;

        // Background glassmorphism do painel
        drawRoundedRect(statsPanelX, statsPanelY, statsPanelW, statsPanelH, 12,
            "rgba(10, 15, 26, 0.80)", "rgba(255, 255, 255, 0.10)", 1);

        ctx.font = "bold 10px sans-serif";
        ctx.fillStyle = "#38bdf8";
        ctx.fillText("STATUS FINAIS DE COMBATE", statsPanelX + 14, statsPanelY + 20);

        // Define os stats prioritários para exibir (máx. 8 no espaço disponível)
        const priorityOrder = ['HP', 'ATQ', 'ATK', 'DEF', 'SPD', 'VEL', 'Taxa CRIT', 'CRIT Rate', 'Dano CRIT', 'CRIT DMG', 'Prof. Element.', 'Recarga', 'Impacto', 'Impact'];
        const criticalStatNames = ['Taxa CRIT', 'CRIT Rate', 'Dano CRIT', 'CRIT DMG', 'SPD', 'VEL'];

        const sortedStatKeys = [...statKeys].sort((a, b) => {
            const ai = priorityOrder.findIndex(p => a.includes(p) || a === p);
            const bi = priorityOrder.findIndex(p => b.includes(p) || b === p);
            if (ai === -1 && bi === -1) return 0;
            if (ai === -1) return 1;
            if (bi === -1) return -1;
            return ai - bi;
        });

        const displayStats = sortedStatKeys.slice(0, 8);
        const cols = 4;
        const rows = 2;
        const cellW = (statsPanelW - 28) / cols;
        const cellH = (statsPanelH - 30) / rows;

        displayStats.forEach((key, idx) => {
            const col = idx % cols;
            const row = Math.floor(idx / cols);
            const cx = statsPanelX + 14 + col * cellW;
            const cy = statsPanelY + 28 + row * cellH;
            const isCritStat = criticalStatNames.some(cs => key.includes(cs) || key === cs);
            const val = charStats[key];

            // Mini card glassmorphism
            const cardBg = isCritStat ? "rgba(245, 158, 11, 0.10)" : "rgba(15, 23, 42, 0.55)";
            const cardBorder = isCritStat ? "rgba(245, 158, 11, 0.30)" : "rgba(255,255,255,0.06)";
            drawRoundedRect(cx, cy, cellW - 4, cellH - 4, 5, cardBg, cardBorder, 1);

            // Label
            ctx.font = "500 9px sans-serif";
            ctx.fillStyle = isCritStat ? "#d97706" : "#64748b";
            ctx.textAlign = "left";
            const cleanKey = sanitizeStatName(key);
            const shortKey = cleanKey.length > 12 ? cleanKey.substring(0, 11) + "." : cleanKey;
            ctx.fillText(shortKey.toUpperCase(), cx + 5, cy + 13);

            // Value
            ctx.font = "bold 12px sans-serif";
            ctx.fillStyle = isCritStat ? "#fbbf24" : "#e2e8f0";
            ctx.fillText(val, cx + 5, cy + 29);
        });
    }

    // Card da Arma Acoplado na Base da Hero Column
    const wx = hx + 12, wy = hy + hh - 122, ww = hw - 24, wh = 110;
    drawRoundedRect(wx, wy, ww, wh, 12, "rgba(10, 15, 26, 0.85)", "rgba(255, 255, 255, 0.12)", 1);

    ctx.font = "bold 10px sans-serif";
    ctx.fillStyle = "#38bdf8";
    ctx.fillText("EQUIPAMENTO / ARMA", wx + 14, wy + 20);

    const weapon = char.weapon;
    if (weapon && weapon.name) {
        const safeWFn = getSafeFileName(weapon.name);
        const weaponUrl = `/assets/weapons/${gameId}/${safeWFn}`;
        const weaponImg = (await loadImage(weapon.icon)) || (await loadImage(weaponUrl));

        if (weaponImg) {
            drawRoundedRect(wx + 14, wy + 28, 68, 68, 8, "rgba(0,0,0,0.5)", "rgba(255,255,255,0.1)", 1);
            ctx.drawImage(weaponImg, wx + 16, wy + 30, 64, 64);
        }
        const textX = weaponImg ? wx + 92 : wx + 14;
        ctx.font = "bold 14px sans-serif";
        ctx.fillStyle = "#ffffff";
        ctx.fillText(weapon.name.length > 18 ? weapon.name.substring(0, 18) + "..." : weapon.name, textX, wy + 52);

        ctx.font = "500 12px sans-serif";
        ctx.fillStyle = "#cbd5e1";
        ctx.fillText(`Nível ${weapon.level || 90} • Refinamento R${weapon.rank || 1}`, textX, wy + 74);
    } else {
        ctx.font = "italic 12px sans-serif";
        ctx.fillStyle = "#64748b";
        ctx.fillText("Nenhuma arma equipada", wx + 14, wy + 55);
    }

    // ==========================================
    // 3. REDESIGN DO GRID DE ARTEFATOS (LINHAS HORIZONTAIS EMPILHADAS)
    // ==========================================
    const rx = 440, ry = 25, rw = 730, rh = 615;
    const relics = char.relics || char.artifacts || char.discs || [];

    const relicImgs = await Promise.all(relics.map(async r => {
        if (!r) return null;
        const iconUrl = r.icon || r.image || r.icon_url;
        const safeRName = getSafeFileName(r.name || "");
        const localUrl = `/assets/relics/${gameId}/${safeRName}`;
        return (await loadImage(iconUrl)) || (await loadImage(localUrl));
    }));

    // Define altura das linhas de acordo com o total de slots (5 para Genshin, 6 para HSR/ZZZ)
    const rowH = maxPieces === 5 ? 112 : 94;
    const gapY = maxPieces === 5 ? 10 : 8;

    for (let i = 0; i < maxPieces; i++) {
        const r = relics[i];
        const rImg = relicImgs[i];
        const rowX = rx;
        const rowY = ry + i * (rowH + gapY);

        if (r) {
            const relicGrade = (r.grade || "D").toUpperCase();
            const rgc = gradeColors[relicGrade] || gradeColors.D;

            // Linha horizontal base
            drawRoundedRect(rowX, rowY, rw, rowH, 12, "rgba(15, 23, 42, 0.65)", "rgba(255, 255, 255, 0.08)", 1);

            // Bloco 1: Ícone + Slot + Nome
            const iconBoxSize = 46;
            const iconBoxY = rowY + (rowH - iconBoxSize) / 2;
            drawRoundedRect(rowX + 10, iconBoxY, iconBoxSize, iconBoxSize, 8, "rgba(0,0,0,0.4)", "rgba(255,255,255,0.1)", 1);

            if (rImg) {
                ctx.drawImage(rImg, rowX + 12, iconBoxY + 2, 42, 42);
            }

            const slotName = r.slot ? (r.slot.length > 12 ? r.slot.substring(0,12) : r.slot) : `Peça ${i+1}`;
            ctx.font = "bold 11px sans-serif";
            ctx.fillStyle = theme.primary;
            ctx.fillText(`[${slotName}]`, rowX + 64, rowY + (rowH === 94 ? 32 : 38));

            ctx.font = "bold 13px sans-serif";
            ctx.fillStyle = "#ffffff";
            const cleanName = r.name || "Relíquia";
            ctx.fillText(cleanName.length > 16 ? cleanName.substring(0, 16) + "..." : cleanName, rowX + 64, rowY + (rowH === 94 ? 54 : 64));

            // Bloco 2: Main Stat em Destaque Dourado
            const rawMain = r.main || r.main_stat || "Desconhecido";
            const mainText = sanitizeStatName(rawMain);
            
            ctx.font = "bold 12px sans-serif";
            const measuredMainW = ctx.measureText(mainText).width + 24;
            const mainW = Math.max(140, Math.min(170, measuredMainW));
            const mainH = 32;
            const mainY = rowY + (rowH - mainH) / 2;
            drawRoundedRect(rowX + 210, mainY, mainW, mainH, 8, "rgba(245, 158, 11, 0.12)", "rgba(245, 158, 11, 0.3)", 1);
            
            ctx.fillStyle = "#fbbf24";
            ctx.textAlign = "center";
            ctx.fillText(mainText, rowX + 210 + mainW / 2, mainY + 20);
            ctx.textAlign = "left";

            // Bloco 3: Substats Embutidos (Grid 2x2 de Mini Badges Compactas)
            const subs = (r.sub || r.sub_stats || "").split(",");
            const pillW = 126;
            const pillH = 22;
            const subGridX = rowX + 365;
            const subGridY = rowY + (rowH - 48) / 2;

            for (let sIdx = 0; sIdx < 4; sIdx++) {
                const colIdx = sIdx % 2;
                const rowIdx = Math.floor(sIdx / 2);
                const px = subGridX + colIdx * (pillW + 6);
                const py = subGridY + rowIdx * (pillH + 4);

                const subStr = subs[sIdx] ? subs[sIdx].trim() : "";
                if (subStr) {
                    const cleanSub = sanitizeStatName(subStr);
                    let label = cleanSub;
                    let val = "";
                    if (cleanSub.includes(":")) {
                        const parts = cleanSub.split(":");
                        label = parts[0].trim();
                        val = parts[1].trim();
                    } else if (cleanSub.includes("(")) {
                        const parts = cleanSub.split("(");
                        label = parts[0].trim();
                        val = parts[1].replace(")", "").trim();
                    }

                    const isPriority = cleanSub.includes("CRIT") || cleanSub.includes("Recarga") || cleanSub.includes("ATQ") || cleanSub.includes("Quebra");
                    const pillBg = isPriority ? "rgba(255, 255, 255, 0.07)" : "rgba(255, 255, 255, 0.03)";
                    const pillBorder = isPriority ? "rgba(255, 255, 255, 0.15)" : "rgba(255, 255, 255, 0.06)";

                    drawRoundedRect(px, py, pillW, pillH, 5, pillBg, pillBorder, 1);
                    
                    if (val) {
                        // Label à esquerda
                        ctx.font = "500 10px sans-serif";
                        ctx.fillStyle = isPriority ? "#cbd5e1" : "#94a3b8";
                        ctx.textAlign = "left";
                        ctx.fillText(label.length > 12 ? label.substring(0, 11) + "." : label, px + 6, py + 15);
                        
                        // Valor à direita em negrito branco (NUNCA cortado!)
                        ctx.font = "bold 10px sans-serif";
                        ctx.fillStyle = "#ffffff";
                        ctx.textAlign = "right";
                        ctx.fillText(val, px + pillW - 6, py + 15);
                        ctx.textAlign = "left";
                    } else {
                        ctx.font = "500 10px sans-serif";
                        ctx.fillStyle = isPriority ? "#f8fafc" : "#94a3b8";
                        ctx.textAlign = "left";
                        ctx.fillText(label.length > 17 ? label.substring(0, 16) + "." : label, px + 6, py + 15);
                    }
                } else {
                    drawRoundedRect(px, py, pillW, pillH, 5, "rgba(255,255,255,0.01)", "rgba(255,255,255,0.03)", 1);
                }
            }

            // Bloco 4: RV Score / Grade Badge no extremo direito
            const scoreW = 78;
            const scoreH = 36;
            const scoreX = rowX + rw - scoreW - 12;
            const scoreY = rowY + (rowH - scoreH) / 2;

            drawRoundedRect(scoreX, scoreY, scoreW, scoreH, 8, rgc.bg, rgc.border, 1.5);
            ctx.font = "bold 13px sans-serif";
            ctx.fillStyle = rgc.text;
            ctx.textAlign = "center";
            ctx.fillText(relicGrade, scoreX + scoreW / 2, scoreY + 16);

            ctx.font = "bold 11px sans-serif";
            ctx.fillStyle = "#ffffff";
            ctx.fillText(`${r.score || 0}`, scoreX + scoreW / 2, scoreY + 30);
            ctx.textAlign = "left";

        } else {
            // Linha vazia
            drawRoundedRect(rowX, rowY, rw, rowH, 12, "rgba(15, 23, 42, 0.25)", "rgba(255, 255, 255, 0.04)", 1);
            ctx.font = "italic 12px sans-serif";
            ctx.fillStyle = "#475569";
            ctx.textAlign = "center";
            ctx.fillText(`[Slot ${i+1} Vazio]`, rowX + rw / 2, rowY + rowH / 2 + 4);
            ctx.textAlign = "left";
        }
    }

    // ==========================================
    // 4. RODAPÉ DO BANNER LANDSCAPE
    // ==========================================
    const nowStr = new Date().toLocaleDateString("pt-BR") + " " + new Date().toLocaleTimeString("pt-BR", { hour: '2-digit', minute: '2-digit' });
    ctx.font = "500 10px sans-serif";
    ctx.fillStyle = "#64748b";
    ctx.textAlign = "right";
    ctx.fillText(`Gerado em ${nowStr}`, width - 30, 658);
    ctx.textAlign = "left";

    return canvas;
}

// Configuração dos eventos do Modal de Exportação de Card
document.addEventListener("DOMContentLoaded", () => {
    const btnExportCard = document.getElementById("btn-export-card");
    const modalExportCard = document.getElementById("modal-export-card");
    const btnCloseExportModal = document.getElementById("btn-close-export-modal");
    const btnDownloadCardImg = document.getElementById("btn-download-card-img");
    const btnCopyCardImg = document.getElementById("btn-copy-card-img");
    const exportPreviewImg = document.getElementById("export-preview-img");
    const exportCardStatus = document.getElementById("export-card-status");

    let currentGeneratedCanvas = null;

    const openExportModalHandler = async () => {
        if (!window.currentInspectorChar || !window.currentInspectorGameId) {
            showToast("Erro: Nenhum personagem selecionado.");
            return;
        }

        modalExportCard.style.display = "flex";
        exportCardStatus.style.display = "flex";
        exportPreviewImg.style.display = "none";
        btnDownloadCardImg.disabled = true;
        btnCopyCardImg.disabled = true;

        try {
            currentGeneratedCanvas = await generateBuildCardCanvas(window.currentInspectorChar, window.currentInspectorGameId);
            const dataUrl = currentGeneratedCanvas.toDataURL("image/png");
            exportPreviewImg.src = dataUrl;
            exportPreviewImg.style.display = "block";
            exportCardStatus.style.display = "none";
            btnDownloadCardImg.disabled = false;
            btnCopyCardImg.disabled = false;
        } catch (err) {
            console.error("Erro ao gerar card de build:", err);
            exportCardStatus.innerHTML = `<span style="color: var(--color-danger);">Erro ao gerar imagem da build: ${err.message}</span>`;
        }
    };

    if (modalExportCard) {
        if (btnExportCard) {
            btnExportCard.addEventListener("click", openExportModalHandler);
        }

        document.addEventListener("click", (e) => {
            if (e.target && e.target.closest(".trigger-export-card")) {
                openExportModalHandler();
            }
        });

        if (btnCloseExportModal) {
            btnCloseExportModal.addEventListener("click", () => {
                modalExportCard.style.display = "none";
            });
        }

        modalExportCard.addEventListener("click", (e) => {
            if (e.target === modalExportCard) {
                modalExportCard.style.display = "none";
            }
        });

        if (btnDownloadCardImg) {
            btnDownloadCardImg.addEventListener("click", () => {
                if (!currentGeneratedCanvas) return;
                const charName = window.currentInspectorChar ? window.currentInspectorChar.name : "Personagem";
                const gameId = window.currentInspectorGameId || "hoyo";
                const link = document.createElement("a");
                link.download = `Build_${getSafeFileName(charName)}_${gameId.toUpperCase()}.png`;
                link.href = currentGeneratedCanvas.toDataURL("image/png");
                link.click();
                showToast("Download da imagem iniciado!");
            });
        }

        if (btnCopyCardImg) {
            btnCopyCardImg.addEventListener("click", () => {
                if (!currentGeneratedCanvas) return;
                currentGeneratedCanvas.toBlob(async (blob) => {
                    if (!blob) {
                        showToast("Erro ao processar imagem.");
                        return;
                    }
                    try {
                        await navigator.clipboard.write([
                            new ClipboardItem({ "image/png": blob })
                        ]);
                        showToast("Imagem copiada para a área de transferência! (Pressione Ctrl+V para colar)");
                    } catch (err) {
                        console.error("Erro ao copiar para clipboard:", err);
                        showToast("Não foi possível copiar automaticamente. Use o botão Baixar PNG.");
                    }
                }, "image/png");
            });
        }
    }
});

