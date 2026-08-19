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
    "electric": "el-electric", "ether": "el-ether", "lumiflux": "el-lumiflux",
    // HoYoLAB API Enum Codes
    "element_100": "el-physical", "element 100": "el-physical",
    "element_200": "el-fire", "element 200": "el-fire",
    "element_300": "el-lumiflux", "element 300": "el-lumiflux",
    "element_400": "el-electric", "element 400": "el-electric",
    "element_500": "el-ether", "element 500": "el-ether"
};

// Helper global para formatar o nome de exibição de elementos (ex: ELEMENT_300 -> Lumiflux)
function formatElementDisplayName(rawElem) {
    if (!rawElem) return "Físico";
    const str = String(rawElem).trim();
    const upper = str.toUpperCase();
    if (upper === "ELEMENT_300" || upper === "ELEMENT 300") return "Lumiflux";
    if (upper === "ELEMENT_100" || upper === "ELEMENT 100") return "Físico";
    if (upper === "ELEMENT_200" || upper === "ELEMENT 200") return "Fogo";
    if (upper === "ELEMENT_400" || upper === "ELEMENT 400") return "Elétrico";
    if (upper === "ELEMENT_500" || upper === "ELEMENT 500") return "Éter";
    return str;
}

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

// Helper global para verificar se um atributo é recomendado dinamicamente para determinado personagem
function isStatRecommendedForChar(statKey, char) {
    if (!statKey || !char) return false;
    const lowerKey = statKey.toLowerCase();
    
    let normKey = "";
    if (lowerKey.includes("quebra") || lowerKey.includes("break")) normKey = "break_effect";
    else if (lowerKey.includes("taxa crit") || lowerKey.includes("crit rate") || lowerKey.includes("taxa")) normKey = "crit_rate";
    else if (lowerKey.includes("dano crit") || lowerKey.includes("crit dmg") || lowerKey.includes("dano")) normKey = "crit_dmg";
    else if (lowerKey.includes("vel") || lowerKey.includes("spd") || lowerKey.includes("velocidade")) normKey = "spd";
    else if (lowerKey.includes("prof. anomalia") || lowerKey.includes("anomalia prof") || lowerKey.includes("anomaly prof") || lowerKey.includes("proficiência de anomalia") || lowerKey.includes("anomalia")) normKey = "anomaly_prof";
    else if (lowerKey.includes("maest") || lowerKey.includes("anomaly mas")) normKey = "anomaly_mas";
    else if (lowerKey.includes("prof") || lowerKey.includes("em") || lowerKey.includes("mastery")) normKey = "em";
    else if (lowerKey.includes("perfura") || lowerKey.includes("pen")) normKey = "pen_flat";
    else if (lowerKey.includes("recarga") || lowerKey.includes("recharge") || lowerKey.includes("er") || lowerKey.includes("recup")) normKey = "er";
    else if (lowerKey.includes("acerto") || lowerKey.includes("ehr")) normKey = "ehr";
    else if (lowerKey.includes("res") || lowerKey.includes("resist")) normKey = "res";
    else if (lowerKey.includes("atq") || lowerKey.includes("atk") || lowerKey.includes("ataque")) normKey = "atk_pct";
    else if (lowerKey.includes("pv") || lowerKey.includes("hp") || lowerKey.includes("vida")) normKey = "hp_pct";
    else if (lowerKey.includes("def")) normKey = "def_pct";
    else if (lowerKey.includes("impact")) normKey = "impact";

    const recWeights = char.recommended_weights || {};
    const subPriorities = char.substats_priority || [];

    // 1. Verificação via pesos dinâmicos do guia (recWeights)
    if (Object.keys(recWeights).length > 0) {
        const w = recWeights[normKey] || recWeights[normKey.replace("_pct", "_flat")];
        if (w && w > 0.35) return true;
    }

    // 2. Verificação via lista substats_priority
    if (subPriorities.length > 0) {
        if (subPriorities.includes(normKey) || subPriorities.some(p => p.includes(normKey) || normKey.includes(p))) {
            return true;
        }
    }

    // 3. Fallbacks contextuais específicos por personagem
    const cName = (char.name || "").toLowerCase();
    if (cName.includes("vaga-lume") || cName.includes("firefly") || cName.includes("boothill") || cName.includes("rappa")) {
        if (normKey === "break_effect" || normKey === "spd" || normKey === "atk_pct") return true;
    }
    if (cName.includes("remielle")) {
        if (normKey === "anomaly_prof" || normKey === "atk_pct" || normKey === "pen_flat" || normKey === "er") return true;
    }

    return false;
}

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
    setupSidebarToggle();
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
// CONTROLE DO MENU LATERAL (RETRÁTIL & MOBILE)
// ==========================================================================
function setupSidebarToggle() {
    const sidebar = document.getElementById("sidebar");
    const sidebarOverlay = document.getElementById("sidebar-overlay");
    const mobileMenuBtn = document.getElementById("mobile-menu-btn");
    const sidebarCloseBtn = document.getElementById("sidebar-close-btn");
    const sidebarToggleDesktopBtn = document.getElementById("sidebar-toggle-desktop-btn");

    function openMobileSidebar() {
        if (sidebar) sidebar.classList.add("open");
        if (sidebarOverlay) sidebarOverlay.classList.add("active");
    }

    function closeMobileSidebar() {
        if (sidebar) sidebar.classList.remove("open");
        if (sidebarOverlay) sidebarOverlay.classList.remove("active");
    }

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener("click", openMobileSidebar);
    }

    if (sidebarCloseBtn) {
        sidebarCloseBtn.addEventListener("click", closeMobileSidebar);
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener("click", closeMobileSidebar);
    }

    if (sidebarToggleDesktopBtn) {
        sidebarToggleDesktopBtn.addEventListener("click", () => {
            if (sidebar) {
                sidebar.classList.toggle("collapsed");
                localStorage.setItem("sidebarCollapsed", sidebar.classList.contains("collapsed"));
            }
        });

        if (localStorage.getItem("sidebarCollapsed") === "true") {
            if (sidebar) sidebar.classList.add("collapsed");
        }
    }
}

function closeInspector() {
    try {
        const drawer = document.getElementById("inspector-drawer") || document.getElementById("build-inspector");
        if (drawer) drawer.style.display = "none";
        const overlay = document.getElementById("inspector-overlay");
        if (overlay) overlay.style.display = "none";
    } catch (e) {}
}

// ==========================================================================
// GERENCIAMENTO DE ABAS (TABS)
// ==========================================================================
function setupTabSwitching() {
    const navButtons = document.querySelectorAll(".nav-btn");
    const sidebar = document.getElementById("sidebar");
    const sidebarOverlay = document.getElementById("sidebar-overlay");

    navButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            if (!targetTab) return;
            
            navButtons.forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-pane").forEach(pane => pane.classList.remove("active"));
            
            btn.classList.add("active");
            const targetPane = document.getElementById(`tab-${targetTab}`);
            if (targetPane) {
                targetPane.classList.add("active");
                if (targetTab === 'gacha' && window.initGachaSimulator) {
                    window.initGachaSimulator();
                }
                if (targetTab === 'luck' && window.initLuckDashboard) {
                    window.initLuckDashboard();
                }
            } else {
                console.warn("Aba não encontrada:", `tab-${targetTab}`);
            }
            
            closeInspector();

            if (window.innerWidth <= 768) {
                if (sidebar) sidebar.classList.remove("open");
                if (sidebarOverlay) sidebarOverlay.classList.remove("active");
            }
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
                const charElemLower = (char.element || "").toLowerCase();
                const filterLower = activeElementFilter.toLowerCase();
                const isLumifluxMatch = filterLower === "lumiflux" && (charElemLower === "lumiflux" || charElemLower === "element_300" || charElemLower === "element 300");
                const matchesElement = activeElementFilter === "all" || charElemLower === filterLower || isLumifluxMatch;
                
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
                const defaultFallback = `/assets/${gameId}_icon.png`;
                const avatarSrc = char.icon || defaultFallback;
                card.innerHTML = `
                    <div class="char-avatar-container">
                        ${char.overall_grade ? `<div class="char-grade-badge badge-${char.overall_grade.toLowerCase()}">${char.overall_grade}</div>` : ''}
                        <img class="char-avatar" src="${avatarSrc}" onerror="this.onerror=null; this.src='${defaultFallback}';" alt="${char.name}">
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
    const inspectorOverlay = document.getElementById("inspector-overlay");
    if (inspector) inspector.classList.add("open");
    if (inspectorOverlay) inspectorOverlay.classList.add("active");
    
    activeInspectGame = gameId;
    activeInspectChar = char;
    
    // Força reset para a aba de build
    const btnBuild = document.getElementById("ins-tab-build");
    if (btnBuild) btnBuild.click();
    
    const defaultFallback = `/assets/${gameId}_icon.png`;
    const insAvatarEl = document.getElementById("ins-avatar");
    if (insAvatarEl) {
        insAvatarEl.src = char.icon || defaultFallback;
        insAvatarEl.onerror = function() {
            this.onerror = null;
            this.src = defaultFallback;
        };
    }
    window.currentInspectorChar = char;
    window.currentInspectorGameId = gameId;

    
    document.getElementById("ins-name").innerText = char.name;
    
    const elemKey = (char.element || "").toLowerCase();
    const displayElem = formatElementDisplayName(char.element);
    const elemHtml = `<img src="/assets/elements/${gameId}_${elemKey}.png" class="element-icon-inline" style="width:14px; height:14px;" onerror="this.style.display='none';"> ${displayElem.toUpperCase()}`;
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
    
    // Configura opções do nível alvo baseadas no jogo (90 para Genshin, 80 para HSR, 60 para ZZZ)
    const maxGameLvl = gameId === "genshin" ? 90 : (gameId === "hsr" ? 80 : 60);
    const availableLvls = [90, 80, 70, 60, 50, 40, 30, 20].filter(l => l <= maxGameLvl);
    ascTargetSelect.innerHTML = availableLvls.map(l => `<option value="${l}">Nível ${l}</option>`).join("");
    ascTargetSelect.value = maxGameLvl.toString();
    
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
                         Custos Estimados (${char.level} ➔ ${targetLvl})
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
            // Ordena os status para colocar os recomendados em primeiro lugar
            const sortedKeys = [...statsKeys].sort((a, b) => {
                const aRec = isStatRecommendedForChar(a, char);
                const bRec = isStatRecommendedForChar(b, char);
                if (aRec && !bRec) return -1;
                if (!aRec && bRec) return 1;
                return 0;
            });
            
            sortedKeys.forEach(key => {
                const isRec = isStatRecommendedForChar(key, char);
                const statCard = document.createElement("div");
                statCard.className = "stat-card" + (isRec ? " stat-card--crit" : "");
                statCard.innerHTML = `
                    <span class="stat-label">${sanitizeStatName(key)}</span>
                    <span class="stat-value${isRec ? ' stat-value--crit' : ''}">${build.stats[key]}</span>
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
        
function getSlotIcon(slotName) {
    if (!slotName) return '<i class="fa-solid fa-shield-halved" style="color: #6366f1;"></i>';
    const s = String(slotName).toLowerCase();
    if (s.includes("flor") || s.includes("bracer") || s.includes("head") || s.includes("cabeça") || s.includes("1"))
        return '<i class="fa-solid fa-clover" style="color: #10b981;"></i>';
    if (s.includes("pluma") || s.includes("necklace") || s.includes("mão") || s.includes("hands") || s.includes("2"))
        return '<i class="fa-solid fa-feather-pointed" style="color: #3b82f6;"></i>';
    if (s.includes("areia") || s.includes("shoes") || s.includes("corpo") || s.includes("body") || s.includes("3"))
        return '<i class="fa-solid fa-hourglass-half" style="color: #f59e0b;"></i>';
    if (s.includes("cálice") || s.includes("calice") || s.includes("ring") || s.includes("esfera") || s.includes("feet") || s.includes("pés") || s.includes("4") || s.includes("5"))
        return '<i class="fa-solid fa-wine-glass" style="color: #ec4899;"></i>';
    if (s.includes("tiara") || s.includes("dress") || s.includes("corda") || s.includes("rope") || s.includes("6"))
        return '<i class="fa-solid fa-crown" style="color: #a855f7;"></i>';
    return '<i class="fa-solid fa-shield-halved" style="color: #6366f1;"></i>';
}

        if (build.pieces && build.pieces.length > 0) {
            build.pieces.forEach(piece => {
                const row = document.createElement("div");
                row.className = "relic-piece-row";
                
                // Encontra a peça equivalente local para extrair o ícone
                const equivalentLocalPiece = localRelics.find(p => 
                    (p.slot && piece.slot && getNormalizedSlot(p.slot) === getNormalizedSlot(piece.slot)) ||
                    (p.name && piece.name && p.name.toLowerCase().includes(piece.name.toLowerCase()))
                );
                
                const slotIconHtml = getSlotIcon(piece.slot);
                const safePieceFn = getSafeFileName(piece.name);
                const cachedPiecePath = `/assets/relics/${gameId}/${safePieceFn}`;
                
                const rawIcon = (equivalentLocalPiece && equivalentLocalPiece.icon) ? equivalentLocalPiece.icon : (piece.icon || cachedPiecePath);
                
                const iconHtml = `
                    <div style="width: 36px; height: 36px; border-radius: 8px; background: rgba(255, 255, 255, 0.05); display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; overflow: hidden; position: relative;">
                        <img class="relic-piece-icon" src="${rawIcon}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" style="width: 100%; height: 100%; object-fit: cover;" alt="${piece.slot || ''}">
                        <div style="display: none; width: 100%; height: 100%; align-items: center; justify-content: center; font-size: 16px;">${slotIconHtml}</div>
                    </div>
                `;

                
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
    const inspector = document.getElementById("build-inspector");
    const inspectorOverlay = document.getElementById("inspector-overlay");
    if (inspector) inspector.classList.remove("open");
    if (inspectorOverlay) inspectorOverlay.classList.remove("active");
}

const btnCloseInspector = document.getElementById("btn-close-inspector");
if (btnCloseInspector) btnCloseInspector.addEventListener("click", closeInspector);
const inspectorOverlay = document.getElementById("inspector-overlay");
if (inspectorOverlay) inspectorOverlay.addEventListener("click", closeInspector);

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
        const defaultFallback = `/assets/${gameId}_icon.png`;
        const avatarSrc = char.icon || defaultFallback;
        return `
            <div class="team-char-select-card" data-name="${char.name}" style="position: relative; aspect-ratio: 1; cursor: pointer; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06); overflow: hidden; background: rgba(0,0,0,0.3); transition: all 0.2s;" onclick="toggleCharacterInTeam(this, '${char.name.replace(/'/g, "\\'")}', '${gameId}')">
                <img src="${avatarSrc}" onerror="this.onerror=null; this.src='${defaultFallback}';" style="width: 100%; height: 100%; object-fit: cover;" alt="${char.name}">
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
        
        // Dicionário de tradução Português <-> Inglês estendido para itens/sets comuns de Genshin, Star Rail e ZZZ
        const translationDict = {
            // Genshin Weapons
            "os sete éditos da poeira e luz": "angelos' heptades",
            "angelos' heptades": "os sete éditos da poeira e luz",
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
            "falcão": "aquila favonia",
            "elegia do suspiro final": "elegy for the end",
            "báculo de goma": "staff of homa",
            "báculo de homa": "staff of homa",

            // Genshin Sets
            "dádiva celestial": "song of days past",
            "song of days past": "dádiva celestial",
            "pergaminho do herói da cidade incandescente": "scroll of the hero of the cinder city",
            "scroll of the hero of the cinder city": "pergaminho do herói da cidade incandescente",
            "códice de obsidiana": "obsidian codex",
            "obsidian codex": "códice de obsidiana",
            "sombra verde": "viridescent venerer",
            "viridescent venerer": "sombra verde",
            "millelith firmes": "tenacity of the millelith",
            "selo da insulação": "emblem of severed fate",
            "herói invernal": "blizzard strayer",
            "caçador das sombras": "marechaussee hunter",
            "trupe dourada": "golden troupe",
            "memórias da floresta": "deepwood memories",
            "sonhos dourados": "gilded dreams",
            "antigo ritual real": "noblesse oblige",
            "noblesse oblige": "antigo ritual real",
            "serenata das estrelas e da lua": "serenade of stars and moon",
            "noite da revelação do céu": "night of the sky's unveiling",
            "juramento da noite eterna": "oath of the eternal night",
            "pedra arcaica": "archaic petra",
            "último juramento do gladiador": "gladiator's finale",
            "ascensão zéfira": "a day carved from rising winds",

            // HSR Sets & Weapons
            "como o navegador isee vê": "as navigator isee sees it",
            "ancoradouro da estrela caída": "fallen star anchorage",
            "lushaka, os mares afundados": "lushaka's waterside",
            "profeta de alcance distante": "scholar lost in erudition",
            "menina mágica sempre gloriosa": "pioneer diver of dead waters",
            "antes do amanhecer": "before dawn",
            "noite sobre a via láctea": "night on the milky way",
            "repouso dos gênios": "geniuses' repose",
            "cálculo eterno": "eternal calculus",
            "hoje também é um dia pacífico": "today is another peaceful day",

            // ZZZ Sets & Weapons
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
            "harmonia das sombras": "shockstar disco"
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
            "ferro": "iron", "cavalaria": "cavalry", "praga": "scourge", "ninjutsu": "ninjutsu",
            "inscrição": "inscription", "deslumbrante": "dazzling", "mal": "evil", "reino": "kingdom",
            "banditismo": "banditry", "duke": "duque", "amanhecer": "dawn", "antes": "before",
            "luz": "light", "estrelas": "stars", "lua": "moon", "sombra": "shadow", "verde": "green",
            "venerer": "venerer", "millelith": "millelith", "firmes": "tenacity", "insulação": "severed",
            "selo": "emblem", "invernal": "blizzard", "herói": "hero", "caçador": "hunter",
            "sombras": "shadows", "dourada": "golden", "trupe": "troupe", "floresta": "deepwood",
            "memórias": "memories", "sonhos": "dreams", "dourados": "gilded", "ritual": "noblesse",
            "real": "oblige", "incandescente": "cinder", "cidade": "city", "pergaminho": "scroll",
            "obsidiana": "obsidian", "códice": "codex", "dádiva": "gift", "celestial": "song",
            "revelação": "unveiling", "céu": "sky", "noite": "night", "eterna": "eternal",
            "juramento": "oath", "pedra": "stone", "arcaica": "archaic", "gladiador": "gladiator"
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
            if (intersection.length >= 1) {
                return true;
            }
            return false;
        }

        function getUnifiedSlotKey(slotStr) {
            if (!slotStr) return "";
            const s = String(slotStr).toLowerCase().replace(/[^a-z0-9]/g, "").trim();
            if (s === "1" || s.includes("flor") || s.includes("flower")) return "flower";
            if (s === "2" || s.includes("pena") || s.includes("plume") || s.includes("feather")) return "plume";
            if (s === "3" || s.includes("areia") || s.includes("relogio") || s.includes("ampulheta") || s.includes("sands")) return "sands";
            if (s === "4" || s.includes("copo") || s.includes("calice") || s.includes("goblet")) return "goblet";
            if (s === "5" || s.includes("tiara") || s.includes("coroa") || s.includes("circlet")) return "circlet";

            if (s === "1" || s.includes("cabeca") || s.includes("head")) return "head";
            if (s === "2" || s.includes("mao") || s.includes("maos") || s.includes("hands")) return "hands";
            if (s === "3" || s.includes("corpo") || s.includes("body")) return "body";
            if (s === "4" || s.includes("pe") || s.includes("pes") || s.includes("bota") || s.includes("feet")) return "feet";
            if (s === "5" || s.includes("esfera") || s.includes("sphere")) return "planar_sphere";
            if (s === "6" || s.includes("corda") || s.includes("rope")) return "link_rope";

            if (s === "1" || s.includes("disco1") || s.includes("slot1")) return "slot_1";
            if (s === "2" || s.includes("disco2") || s.includes("slot2")) return "slot_2";
            if (s === "3" || s.includes("disco3") || s.includes("slot3")) return "slot_3";
            if (s === "4" || s.includes("disco4") || s.includes("slot4")) return "slot_4";
            if (s === "5" || s.includes("disco5") || s.includes("slot5")) return "slot_5";
            if (s === "6" || s.includes("disco6") || s.includes("slot6")) return "slot_6";

            return s;
        }

        function normalizeStatTerm(str) {
            if (!str) return "";
            let s = String(str).toLowerCase()
                .replace(/\([^)]*\)/g, "") // Remove números entre parênteses ex: (46.6%)
                .replace(/[0-9.,%+]/g, "")
                .trim();
                
            if (s.includes("quebra") || s.includes("break")) return "break";
            if (s.includes("taxa") || s.includes("rate")) return "crit_rate";
            if (s.includes("dano crit") || s.includes("crit dmg") || s.includes("dano crt")) return "crit_dmg";
            if (s.includes("crit")) return "crit";
            if (s.includes("recarga") || s.includes("recharge") || s.includes("regen") || s.includes("er")) return "er";
            if (s.includes("prof") || s.includes("mastery") || s.includes("em") || s.includes("anomalia")) return "em";
            if (s.includes("atq") || s.includes("atk") || s.includes("ataque")) return "atk";
            if (s.includes("pv") || s.includes("hp") || s.includes("vida")) return "hp";
            if (s.includes("def") || s.includes("defesa")) return "def";
            if (s.includes("vel") || s.includes("spd") || s.includes("velocidade")) return "speed";
            if (s.includes("cura") || s.includes("healing")) return "healing";
            if (s.includes("dano") || s.includes("bonus") || s.includes("dmg")) return "elemental_dmg";
            if (s.includes("perfura") || s.includes("pen")) return "pen";

            return s;
        }
        
        let html = "";
        
        // 1. Arma (com verificação de múltiplos substitutos e tradução)
        const cleanPlayerWeapon = (build.weapon || "").replace(/\(Nv\..*?\)/gi, "").replace(/\(R[1-5]\)/gi, "").trim();
        const recommendedWeapons = target.weapons && target.weapons.length > 0 ? target.weapons : [target.weapon];
        const hasWeaponMatch = recommendedWeapons.some(w => checkFuzzyMatch(cleanPlayerWeapon, w));
        
        let weaponClass = "comparison-neutral";
        if (target.weapon !== "Não informado") {
            if (hasWeaponMatch) {
                weaponClass = "comparison-match";
            } else if (cleanPlayerWeapon && cleanPlayerWeapon !== "Não informado") {
                // Marca como alternativa viável para evitar falso-positivo em vermelho
                weaponClass = "comparison-warning";
            } else {
                weaponClass = "comparison-mismatch";
            }
        }
        
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
            if (hasSetMatch) {
                setsClass = "comparison-match";
            } else if (build.sets.some(s => s.includes("4 peças") || s.includes("4p") || s.includes("2 peças"))) {
                setsClass = "comparison-warning";
            } else {
                setsClass = "comparison-mismatch";
            }
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
        
        if (targetStatsKeys.length > 0) {
            targetStatsKeys.forEach(key => {
                let playerVal = "Não equipado";
                let statClass = "comparison-mismatch";
                
                // Tenta encontrar a peça correspondente ao slot normalizado
                const matchedPiece = (build.pieces || []).find(p => {
                    const pKey = getUnifiedSlotKey(p.slot);
                    const tKey = getUnifiedSlotKey(key);
                    return (pKey && tKey && pKey === tKey) || p.slot.toLowerCase().trim().includes(key.toLowerCase().trim()) || key.toLowerCase().trim().includes(p.slot.toLowerCase().trim());
                });
                
                if (matchedPiece) {
                    playerVal = matchedPiece.main;
                    const targetValLower = target.stats[key].toLowerCase();
                    const options = targetValLower.split(/[=/>]|\bou\b/).map(s => s.trim());
                    
                    const isMatch = options.some(opt => {
                        if (!opt) return false;
                        const optNorm = normalizeStatTerm(opt);
                        const mainNorm = normalizeStatTerm(matchedPiece.main);
                        return mainNorm === optNorm || mainNorm.includes(optNorm) || optNorm.includes(mainNorm);
                    });
                    
                    statClass = isMatch ? "comparison-match" : "comparison-warning";
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
                            return pKNorm === optNorm || pKNorm.includes(optNorm) || optNorm.includes(pKNorm);
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
        "wind": "Vento",
        "lumiflux": "Lumiflux",
        "element_300": "Lumiflux",
        "element 300": "Lumiflux"
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
    if (!elementKey) return "Desconhecido";
    const kLower = elementKey.toLowerCase().trim();
    if (kLower === "element_300" || kLower === "element 300" || kLower === "lumiflux") return "Lumiflux";
    if (kLower === "element_100" || kLower === "element 100") return "Físico";
    if (kLower === "element_200" || kLower === "element 200") return "Fogo";
    if (kLower === "element_400" || kLower === "element 400") return "Elétrico";
    if (kLower === "element_500" || kLower === "element 500") return "Éter";
    const gameLabels = ELEMENT_LABELS[gameId] || {};
    return gameLabels[kLower] || elementKey.charAt(0).toUpperCase() + elementKey.slice(1);
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
        "ether": "#db2777", "éter": "#db2777",
        "lumiflux": "#f472b6", "element_300": "#f472b6", "element 300": "#f472b6"
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
    const noAccents = String(name).normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    const clean = noAccents.toLowerCase().trim();
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
        "jane": "jane-doe",
        "koleda belobog": "koleda",
        "nicole demara": "nicole-demara",
        "nicole": "nicole-demara",
        "orphie & magus": "orphie-and-magus",
        "orphie and magus": "orphie-and-magus",
        "orfeu & magus": "orphie-and-magus",
        "orfeu e magus": "orphie-and-magus",
        "piper wheel": "piper",
        "seth lowell": "seth",
        "soldier 11": "soldier-11",
        "n. 11": "soldier-11",
        "n.º 11": "soldier-11",
        "n.o 11": "soldier-11",
        "von lycaon": "lycaon",
        "zhu yuan": "zhu-yuan",

        // Mapeamento PT-BR de ZZZ
        "císsia": "cissia",
        "cissia": "cissia",
        "caesar": "caesar",
        "caesar king": "caesar",
        "luciana": "lucy",
        "luciana de montefio": "lucy",
        "lucy": "lucy",
        "vovó": "lucy",
        "vovo": "lucy",
        "soukaku": "soukaku",
        "burnice": "burnice",
        "burnice white": "burnice",
        "lighter": "lighter",
        "yanagi": "yanagi",
        "tsukishiro yanagi": "yanagi",
        "miyabi": "miyabi",
        "harumasa": "harumasa",
        "evelyn": "evelyn",
        "evelyn chevalier": "evelyn",
        "pulchra": "pulchra",
        "koleda": "koleda"
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
        const iconStr = String(char.icon || "");
        const gArtStr = String(char.gacha_art || "");
        const checkStr = iconStr + " " + gArtStr + " " + String(char.splash_art || "");
        const skinMatch = checkStr.match(/(?:role_square_avatar|role_vertical_painting)_(\d+)_(\d{7,})\.png/);
        if (skinMatch) {
            splashUrl = `https://act-webstatic.hoyoverse.com/game_record/zzzv2/role_vertical_painting/role_vertical_painting_${skinMatch[1]}_${skinMatch[2]}.png`;
        } else {
            const zzzSlug = getZzzPrydwenSlug(char.name);
            if (zzzSlug) {
                splashUrl = `https://cdn.prydwen.gg/images/zenless-zone-zero/characters/${zzzSlug}_full.webp`;
            }
        }
    } else if (gameId === 'genshin') {
        const checkIcon = char.gacha_art || char.icon || splashUrl || "";
        let rawCheck = decodeURIComponent(checkIcon);
        rawCheck = rawCheck.replace(/\.png\.png$/i, ".png").replace(/\/(UI_AvatarIcon_|UI_Gacha_AvatarImg_|UI_Costume_)ide_/, "/$1");
        if (rawCheck.includes("UI_AvatarIcon_")) {
            if (rawCheck.includes("Costume")) {
                const costumeMatch = rawCheck.match(/(UI_AvatarIcon_[A-Za-z0-9_]+Costume[A-Za-z0-9_]*)/);
                if (costumeMatch) {
                    const costumeArt = costumeMatch[1].replace("UI_AvatarIcon_", "UI_Costume_");
                    splashUrl = `/api/proxy_image?url=${encodeURIComponent(`https://enka.network/ui/${costumeArt}.png`)}`;
                } else {
                    splashUrl = rawCheck.replace("UI_AvatarIcon_", "UI_Costume_");
                }
            } else {
                splashUrl = rawCheck.replace("UI_AvatarIcon_", "UI_Gacha_AvatarImg_");
            }
        } else if (rawCheck.includes("UI_Costume_")) {
            splashUrl = rawCheck;
        }
    }

    const defaultFallbackUrl = `/assets/${gameId}_icon.png`;

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
        let rawEnka = decodeURIComponent(enkaGacha);
        if (rawEnka.includes("UI_AvatarIcon_")) {
            if (rawEnka.includes("Costume")) {
                const match = rawEnka.match(/(UI_AvatarIcon_[A-Za-z0-9_]+Costume[A-Za-z0-9_]*)/);
                if (match) {
                    const cArt = match[1].replace("UI_AvatarIcon_", "UI_Costume_");
                    enkaGacha = `/api/proxy_image?url=${encodeURIComponent(`https://enka.network/ui/${cArt}.png`)}`;
                }
            }
        }
        if (enkaGacha !== char.icon) {
            charImg = await loadImage(enkaGacha);
        }
    }

    if (!charImg) {
        charImg = await loadImage(char.icon) || await loadImage(defaultFallbackUrl);
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

            if (splashUrl && splashUrl.includes("role_vertical_painting")) {
                // Enquadramento inteligente para pinturas verticais de skins do HoYoLAB (evita cortar chapéu/óculos/cabeça)
                drawW = targetW * 1.12;
                drawH = drawW / cropRatio;
                drawX = (hx + 2) - (drawW - targetW) / 2;
                drawY = hy + 45;
            } else {
                // Escala a altura para preencher todo o container (611px), garantindo o personagem grande e em destaque
                drawH = targetH;
                drawW = targetH * cropRatio;
                drawX = (hx + 2) - (drawW - targetW) / 2;
                drawY = hy + 2;
            }

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
    const elemName = formatElementDisplayName(char.element || "Físico").toUpperCase();
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



        // Ordena para que os status recomendados apareçam primeiro no grid do Card
        const sortedStatKeys = [...statKeys].sort((a, b) => {
            const aRec = isStatRecommendedForChar(a, char);
            const bRec = isStatRecommendedForChar(b, char);
            if (aRec && !bRec) return -1;
            if (!aRec && bRec) return 1;
            return 0;
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
            const isRec = isStatRecommendedForChar(key, char);
            const val = charStats[key];

            // Mini card glassmorphism com Highlight Dourado Dinâmico para atributos recomendados
            const cardBg = isRec ? "rgba(245, 158, 11, 0.12)" : "rgba(15, 23, 42, 0.55)";
            const cardBorder = isRec ? "rgba(245, 158, 11, 0.35)" : "rgba(255, 255, 255, 0.06)";
            drawRoundedRect(cx, cy, cellW - 4, cellH - 4, 5, cardBg, cardBorder, 1);

            // Label do Atributo
            ctx.font = "500 9px sans-serif";
            ctx.fillStyle = isRec ? "#d97706" : "#64748b";
            ctx.textAlign = "left";
            const cleanKey = sanitizeStatName(key);
            const shortKey = cleanKey.length > 12 ? cleanKey.substring(0, 11) + "." : cleanKey;
            ctx.fillText(shortKey.toUpperCase(), cx + 5, cy + 13);

            // Valor do Atributo
            ctx.font = "bold 12px sans-serif";
            ctx.fillStyle = isRec ? "#fbbf24" : "#e2e8f0";
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

    const charSkills = char.skills || [];
    if (charSkills.length > 0) {
        const skillsSummary = charSkills.map(s => `${s.level || 1}`).join(" / ");
        const textX = (weapon && weapon.name) ? wx + 92 : wx + 14;
        ctx.font = "bold 11px sans-serif";
        ctx.fillStyle = "#a855f7";
        ctx.fillText(`Habilidades: ${skillsSummary}`, textX, wy + 94);
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

// Função para gerar Canvas HD da Tier List da Conta
window.generateTierListCardCanvas = async (gameId, auditData) => {
    const gameNames = { hsr: "HONKAI: STAR RAIL", genshin: "GENSHIN IMPACT", zzz: "ZENLESS ZONE ZERO" };
    const themeColors = { hsr: "#ec4899", genshin: "#38bdf8", zzz: "#f59e0b" };
    const themeColor = themeColors[gameId] || "#a855f7";
    const tierList = (auditData && auditData.tier_list) || {};
    const tierKeys = ["S+", "S", "A", "B", "C/D"];
    const tierColors = { "S+": "#ef4444", "S": "#f59e0b", "A": "#10b981", "B": "#38bdf8", "C/D": "#94a3b8" };

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
            img.onerror = () => resolve(null);
            img.src = finalUrl;
        });
    }

    function drawRoundedRect(ctx, x, y, w, h, r, fillStyle, strokeStyle, lineWidth = 1) {
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

    const logoImg = (await loadImage(`/assets/${gameId}_icon.png`)) || (await loadImage("/assets/logo.svg"));

    const avatarPromises = [];
    const charImgMap = {};

    tierKeys.forEach((tier) => {
        const chars = tierList[tier] || [];
        chars.forEach((c) => {
            if (c.icon) {
                avatarPromises.push(
                    loadImage(c.icon).then((img) => {
                        if (img) charImgMap[c.icon] = img;
                    })
                );
            }
        });
    });

    await Promise.all(avatarPromises);

    const width = 1200;
    const charsPerRow = 5;
    const charW = 202;
    const charH = 58;

    let totalTierRowsH = 0;
    const tierRowHeights = {};

    tierKeys.forEach((tier) => {
        const chars = tierList[tier] || [];
        const rowCount = Math.max(1, Math.ceil(chars.length / charsPerRow));
        const rH = Math.max(76, rowCount * (charH + 8) + 14);
        tierRowHeights[tier] = rH;
        totalTierRowsH += rH + 14;
    });

    const headerH = 150;
    const footerH = 50;
    const height = Math.max(620, headerH + totalTierRowsH + footerH);

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext("2d");

    const bgGrad = ctx.createLinearGradient(0, 0, width, height);
    bgGrad.addColorStop(0, "#080c16");
    bgGrad.addColorStop(0.5, "#0e1626");
    bgGrad.addColorStop(1, "#060810");
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, width, height);

    drawRoundedRect(ctx, 10, 10, width - 20, height - 20, 16, "transparent", "rgba(255, 255, 255, 0.1)", 1.5);

    let titleX = 30;
    if (logoImg) {
        ctx.drawImage(logoImg, 30, 28, 30, 30);
        titleX = 70;
    }

    ctx.font = "bold 12px sans-serif";
    ctx.fillStyle = themeColor;
    ctx.fillText(`${gameNames[gameId] || gameId.toUpperCase()} • CABEÇA DE DROID v4.0`, titleX, 42);

    ctx.font = "bold 24px sans-serif";
    ctx.fillStyle = "#ffffff";
    ctx.fillText("Tier List de Builds (Roll Value)", 30, 80);

    ctx.font = "500 12px sans-serif";
    ctx.fillStyle = "#94a3b8";
    ctx.fillText("Classificação dos seus personagens baseada no score matemático das relíquias", 30, 100);

    const kpis = [
        { label: "TOTAL PERSONAGENS", val: `${auditData.total_characters || 0}`, color: "#38bdf8" },
        { label: "MÉDIA DE NOTA (RV)", val: `${auditData.avg_rv || 0}%`, color: "#f59e0b" },
        { label: "BUILDS S / SSS", val: `${auditData.s_count || 0}`, color: "#10b981" }
    ];

    const kpiW = 125;
    const kpiH = 56;
    const kpiY = 28;
    kpis.forEach((kpi, idx) => {
        const kpiX = width - 30 - (3 - idx) * (kpiW + 10);
        drawRoundedRect(ctx, kpiX, kpiY, kpiW, kpiH, 10, "rgba(15, 23, 42, 0.8)", "rgba(255, 255, 255, 0.08)", 1);

        ctx.font = "bold 9px sans-serif";
        ctx.fillStyle = "#94a3b8";
        ctx.textAlign = "center";
        ctx.fillText(kpi.label, kpiX + kpiW / 2, kpiY + 18);

        ctx.font = "bold 17px sans-serif";
        ctx.fillStyle = kpi.color;
        ctx.fillText(kpi.val, kpiX + kpiW / 2, kpiY + 41);
        ctx.textAlign = "left";
    });

    ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(30, 122);
    ctx.lineTo(width - 30, 122);
    ctx.stroke();

    let currentY = 138;

    tierKeys.forEach((tier) => {
        const chars = tierList[tier] || [];
        const color = tierColors[tier] || "#94a3b8";
        const rowH = tierRowHeights[tier];

        drawRoundedRect(ctx, 30, currentY, width - 60, rowH, 12, "rgba(15, 23, 42, 0.65)", "rgba(255, 255, 255, 0.06)", 1);

        const badgeW = 58;
        const badgeH = rowH - 16;
        const badgeX = 38;
        const badgeY = currentY + 8;

        drawRoundedRect(ctx, badgeX, badgeY, badgeW, badgeH, 10, color, "transparent", 0);

        ctx.font = "bold 22px sans-serif";
        ctx.fillStyle = "#000000";
        ctx.textAlign = "center";
        ctx.fillText(tier, badgeX + badgeW / 2, badgeY + badgeH / 2 + 7);
        ctx.textAlign = "left";

        const charStartX = badgeX + badgeW + 14;

        if (chars.length === 0) {
            ctx.font = "italic 13px sans-serif";
            ctx.fillStyle = "#64748b";
            ctx.fillText("Nenhum personagem nesta categoria", charStartX, currentY + rowH / 2 + 4);
        } else {
            chars.forEach((c, idx) => {
                const col = idx % charsPerRow;
                const row = Math.floor(idx / charsPerRow);

                const cx = charStartX + col * (charW + 10);
                const cy = currentY + 9 + row * (charH + 8);

                drawRoundedRect(ctx, cx, cy, charW, charH, 10, "rgba(255, 255, 255, 0.05)", "rgba(255, 255, 255, 0.09)", 1);

                const avatarSize = 42;
                const avatarX = cx + 8;
                const avatarY = cy + (charH - avatarSize) / 2;
                const cImg = charImgMap[c.icon];

                if (cImg) {
                    ctx.save();
                    ctx.beginPath();
                    ctx.arc(avatarX + avatarSize / 2, avatarY + avatarSize / 2, avatarSize / 2, 0, Math.PI * 2);
                    ctx.clip();
                    ctx.drawImage(cImg, avatarX, avatarY, avatarSize, avatarSize);
                    ctx.restore();

                    ctx.beginPath();
                    ctx.arc(avatarX + avatarSize / 2, avatarY + avatarSize / 2, avatarSize / 2, 0, Math.PI * 2);
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }

                const textX = avatarX + avatarSize + 10;
                ctx.font = "bold 12px sans-serif";
                ctx.fillStyle = "#ffffff";
                const cName = c.name.length > 14 ? c.name.substring(0, 13) + "." : c.name;
                ctx.fillText(cName, textX, cy + 23);

                ctx.font = "bold 11px sans-serif";
                ctx.fillStyle = color;
                const scoreStr = `${c.score.toFixed(1)}%`;
                ctx.fillText(scoreStr, textX, cy + 42);

                const gradeStr = c.grade || "D";
                const gradeBadgeX = textX + ctx.measureText(scoreStr).width + 6;
                drawRoundedRect(ctx, gradeBadgeX, cy + 30, 30, 16, 4, "rgba(255, 255, 255, 0.12)", "transparent", 0);
                ctx.font = "bold 10px sans-serif";
                ctx.fillStyle = "#ffffff";
                ctx.textAlign = "center";
                ctx.fillText(gradeStr, gradeBadgeX + 15, cy + 42);
                ctx.textAlign = "left";
            });
        }

        currentY += rowH + 14;
    });

    const nowStr = new Date().toLocaleDateString("pt-BR") + " " + new Date().toLocaleTimeString("pt-BR", { hour: '2-digit', minute: '2-digit' });
    ctx.font = "bold 11px sans-serif";
    ctx.fillStyle = themeColor;
    ctx.fillText("CABEÇA DE DROID v4.0", 30, height - 20);

    ctx.font = "500 11px sans-serif";
    ctx.fillStyle = "#64748b";
    ctx.textAlign = "right";
    ctx.fillText(`Gerado em ${nowStr}`, width - 30, height - 20);
    ctx.textAlign = "left";

    return canvas;
};

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
    let currentGeneratedBlob = null;

    const openExportModalHandler = async () => {
        if (!window.currentInspectorChar || !window.currentInspectorGameId) {
            showToast("Erro: Nenhum personagem selecionado.");
            return;
        }

        window.currentExportCardName = `Build_${getSafeFileName(window.currentInspectorChar.name)}_${(window.currentInspectorGameId || "hoyo").toUpperCase()}`;
        modalExportCard.style.display = "flex";
        exportCardStatus.style.display = "flex";
        exportCardStatus.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Gerando card HD da build...</span>`;
        exportPreviewImg.style.display = "none";
        btnDownloadCardImg.disabled = true;
        btnCopyCardImg.disabled = true;

        try {
            currentGeneratedCanvas = await generateBuildCardCanvas(window.currentInspectorChar, window.currentInspectorGameId);
            currentGeneratedBlob = await new Promise(resolve => currentGeneratedCanvas.toBlob(resolve, "image/png"));
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

    const openExportTierListModalHandler = async (targetGameId) => {
        const activeTabBtn = document.querySelector(".tab-audit-game-btn.active") || document.querySelector(".audit-game-tab.active");
        const gameId = targetGameId || (activeTabBtn ? activeTabBtn.dataset.game : null) || window.currentAuditGameId || window.activeGameTab || "hsr";
        window.currentExportCardName = `TierList_${gameId.toUpperCase()}`;
        modalExportCard.style.display = "flex";
        exportCardStatus.style.display = "flex";
        exportCardStatus.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> <span>Gerando imagem HD da Tier List (${gameId.toUpperCase()})...</span>`;
        exportPreviewImg.style.display = "none";
        btnDownloadCardImg.disabled = true;
        btnCopyCardImg.disabled = true;

        try {
            const res = await fetch(`/api/audit/${gameId}`);
            const auditData = await res.json();
            currentGeneratedCanvas = await window.generateTierListCardCanvas(gameId, auditData);
            currentGeneratedBlob = await new Promise(resolve => currentGeneratedCanvas.toBlob(resolve, "image/png"));
            const dataUrl = currentGeneratedCanvas.toDataURL("image/png");
            exportPreviewImg.src = dataUrl;
            exportPreviewImg.style.display = "block";
            exportCardStatus.style.display = "none";
            btnDownloadCardImg.disabled = false;
            btnCopyCardImg.disabled = false;
        } catch (err) {
            console.error("Erro ao gerar imagem da Tier List:", err);
            exportCardStatus.innerHTML = `<span style="color: var(--color-danger);">Erro ao gerar imagem da Tier List: ${err.message}</span>`;
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
            if (e.target && e.target.closest(".trigger-export-tierlist")) {
                const btn = e.target.closest(".trigger-export-tierlist");
                const activeTabBtn = document.querySelector(".tab-audit-game-btn.active") || document.querySelector(".audit-game-tab.active");
                const gId = btn.dataset.game || (activeTabBtn ? activeTabBtn.dataset.game : null) || window.currentAuditGameId || "hsr";
                openExportTierListModalHandler(gId);
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
                const fileName = window.currentExportCardName ? window.currentExportCardName : `Build_${getSafeFileName(charName)}_${gameId.toUpperCase()}`;
                const link = document.createElement("a");
                link.download = `${fileName}.png`;
                link.href = currentGeneratedCanvas.toDataURL("image/png");
                link.click();
                showToast("Download da imagem iniciado!");
            });
        }

        if (btnCopyCardImg) {
            btnCopyCardImg.addEventListener("click", async () => {
                if (!currentGeneratedCanvas) return;

                if (navigator.clipboard && window.ClipboardItem && navigator.clipboard.write) {
                    try {
                        if (!currentGeneratedBlob) {
                            currentGeneratedBlob = await new Promise(resolve => currentGeneratedCanvas.toBlob(resolve, "image/png"));
                        }
                        const item = new ClipboardItem({ "image/png": currentGeneratedBlob });
                        await navigator.clipboard.write([item]);
                        showToast("Imagem copiada para a área de transferência! (Pressione Ctrl+V no Discord/WhatsApp)");
                        return;
                    } catch (clipErr) {
                        console.warn("navigator.clipboard.write falhou:", clipErr);
                    }
                }

                showToast("Navegadores em conexões HTTP de celular/rede local bloqueiam a cópia direta. Baixando PNG...");
                const charName = window.currentInspectorChar ? window.currentInspectorChar.name : "Personagem";
                const gameId = window.currentInspectorGameId || "hoyo";
                const link = document.createElement("a");
                link.download = `Build_${getSafeFileName(charName)}_${gameId.toUpperCase()}.png`;
                link.href = currentGeneratedCanvas.toDataURL("image/png");
                link.click();
            });
        }
    }

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
                document.getElementById("gacha-chance-lbl").innerText = `Chance de Sucesso: ${data.success_rate}%`;
                document.getElementById("gacha-avg-lbl").innerText = data.avg_pulls_spent 
                    ? `Média de Tiros Gastos nas vitórias: ${data.avg_pulls_spent} tiros` 
                    : "Quantidade de tiros insuficiente para garantir a meta com alta frequência.";

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

    // 2. CENTRAL DE FARM DIÁRIO
    window.loadFarmData = async (gameId, targetContainerId = "farm-content-body") => {
        const body = document.getElementById(targetContainerId);
        if (!body) return;
        body.innerHTML = "<div style='color:#94a3b8; padding: 20px; text-align: center;'><i class='fa-solid fa-spinner fa-spin'></i> Carregando calendário, lista de personagens e recomendações...</div>";
        
        try {
            const storageKey = `hoyo_farm_selected_${gameId}`;
            let savedSelected = null;
            try {
                const rawSaved = localStorage.getItem(storageKey);
                if (rawSaved) savedSelected = JSON.parse(rawSaved);
            } catch(e) {}

            let apiUrl = `/api/farming/today/${gameId}`;
            if (savedSelected && Array.isArray(savedSelected)) {
                apiUrl += `?selected_chars=${encodeURIComponent(savedSelected.join(","))}`;
            }

            const res = await fetch(apiUrl);
            const data = await res.json();
            const cal = data.calendar_info || {};
            const allRosterNames = data.all_roster_names || [];
            const targets = data.priority_targets || [];
            const maxLvl = data.max_level || (gameId === "genshin" ? 90 : (gameId === "hsr" ? 80 : 60));

            let selectedSet;
            if (savedSelected && Array.isArray(savedSelected)) {
                selectedSet = new Set(savedSelected);
            } else {
                selectedSet = new Set(allRosterNames);
            }

            let html = `
                <!-- CALENDÁRIO DO DIA -->
                <div style="padding:14px; background:rgba(255,255,255,0.03); border-radius:10px; margin-bottom:16px; border:1px solid var(--border-color);">
                    <h4 style="margin:0 0 6px 0; color:#10b981; font-size:15px; display:flex; align-items:center; gap:8px;">
                        <i class="fa-solid fa-calendar-day"></i> Calendário do Dia (${cal.days || 'Hoje'})
                        <span style="font-size:11px; background:rgba(16,185,129,0.15); color:#10b981; padding:2px 8px; border-radius:12px; margin-left:auto;">Nv. Máximo do Jogo: ${maxLvl}</span>
                    </h4>
            `;
            if (cal.talents) html += `<div style="font-size:13px; color:#cbd5e1; margin-top:4px;"><strong>Livros de Talento / Mat.:</strong> ${cal.talents.join(", ")}</div>`;
            if (cal.weapons) html += `<div style="font-size:13px; color:#cbd5e1; margin-top:4px;"><strong>Armas / Elevação:</strong> ${cal.weapons.join(", ")}</div>`;
            if (cal.note) html += `<div style="font-size:13px; color:#f59e0b; margin-top:4px;"><strong>Nota Especial:</strong> ${cal.note}</div>`;
            html += `</div>`;

            // PAINEL DE SELEÇÃO DE PERSONAGENS
            html += `
                <div style="padding:12px; background:rgba(15,23,42,0.7); border-radius:10px; margin-bottom:16px; border:1px solid rgba(255,255,255,0.08);">
                    <div style="display:flex; justify-content:space-between; align-items:center; cursor:pointer;" onclick="const el=document.getElementById('${targetContainerId}-char-selector'); el.style.display = el.style.display==='none'?'block':'none';">
                        <strong style="color:#e2e8f0; font-size:13px; display:flex; align-items:center; gap:6px;">
                            <i class="fa-solid fa-user-check" style="color:#38bdf8;"></i> Personagens Alvo do Farm (${selectedSet.size}/${allRosterNames.length})
                        </strong>
                        <span style="font-size:11px; color:#38bdf8; text-decoration:underline;"> Selecionar Personagens</span>
                    </div>
                    <div id="${targetContainerId}-char-selector" style="display:none; margin-top:12px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.06);">
                        <div style="display:flex; gap:10px; margin-bottom:10px;">
                            <button id="${targetContainerId}-select-all" style="font-size:11px; padding:4px 8px; background:rgba(56,189,248,0.15); color:#38bdf8; border:1px solid rgba(56,189,248,0.3); border-radius:6px; cursor:pointer;">Selecionar Todos</button>
                            <button id="${targetContainerId}-deselect-all" style="font-size:11px; padding:4px 8px; background:rgba(239,68,68,0.15); color:#f87171; border:1px solid rgba(239,68,68,0.3); border-radius:6px; cursor:pointer;">Desmarcar Todos</button>
                        </div>
                        <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap:6px; max-height:160px; overflow-y:auto; padding-right:4px;">
            `;

            allRosterNames.forEach(cName => {
                const isChecked = selectedSet.has(cName);
                html += `
                    <label style="display:flex; align-items:center; gap:6px; font-size:12px; color:#cbd5e1; background:rgba(0,0,0,0.3); padding:4px 8px; border-radius:6px; cursor:pointer; user-select:none;">
                        <input type="checkbox" class="${targetContainerId}-char-cb" data-char="${cName}" ${isChecked ? 'checked' : ''}>
                        <span style="white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${cName}</span>
                    </label>
                `;
            });

            html += `
                        </div>
                    </div>
                </div>
            `;

            // RECOMENDAÇÕES E DETALHAMENTO DE ITENS
            let farmableOnlyKey = `hoyo_farmable_only_${gameId}`;
            let isFarmableOnly = localStorage.getItem(farmableOnlyKey) === "true";

            html += `
                <div style="display:flex; justify-content:space-between; align-items:center; margin:16px 0 10px 0;">
                    <h4 style="margin:0; color:#f59e0b; font-size:15px; display:flex; align-items:center; gap:6px;">
                        <i class="fa-solid fa-bullseye"></i> Sugestões e Itens de Farm Detalhados
                    </h4>
                    ${gameId === "genshin" ? `
                        <label style="font-size:12px; color:#38bdf8; display:flex; align-items:center; gap:6px; background:rgba(56,189,248,0.1); padding:4px 10px; border-radius:8px; cursor:pointer; border:1px solid rgba(56,189,248,0.25);">
                            <input type="checkbox" id="${targetContainerId}-farmable-only" ${isFarmableOnly ? 'checked' : ''}>
                            <span> Apenas Materiais Abertos Hoje</span>
                        </label>
                    ` : ''}
                </div>
            `;

            let displayTargets = targets;
            if (gameId === "genshin" && isFarmableOnly) {
                displayTargets = targets.filter(t => t.farmable_today !== false);
            }

            if (displayTargets.length === 0) {
                html += `<div style="padding:16px; background:rgba(255,255,255,0.02); border-radius:8px; font-size:13px; color:#94a3b8; text-align:center;">Nenhum personagem selecionado precisa de ascensão no momento ou tem materiais abertos hoje! Todos os selecionados estão no nível máximo (${maxLvl}) com talentos e armas atualizados.</div>`;
            } else {
                const elementGlows = {
                    pyro: { color: "#ef4444", bg: "rgba(239,68,68,0.08)", border: "rgba(239,68,68,0.3)" },
                    fire: { color: "#ef4444", bg: "rgba(239,68,68,0.08)", border: "rgba(239,68,68,0.3)" },
                    hydro: { color: "#38bdf8", bg: "rgba(56,189,248,0.08)", border: "rgba(56,189,248,0.3)" },
                    ice: { color: "#06b6d4", bg: "rgba(6,182,212,0.08)", border: "rgba(6,182,212,0.3)" },
                    cryo: { color: "#06b6d4", bg: "rgba(6,182,212,0.08)", border: "rgba(6,182,212,0.3)" },
                    electro: { color: "#a855f7", bg: "rgba(168,85,247,0.08)", border: "rgba(168,85,247,0.3)" },
                    anemo: { color: "#10b981", bg: "rgba(16,185,129,0.08)", border: "rgba(16,185,129,0.3)" },
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
                                                ${t.element || 'Elemento'}
                                            </span>
                                        </div>
                                        <div style="font-size:12px; color:#cbd5e1; margin-top:3px; display:flex; align-items:center; gap:8px;">
                                            <span>Nv. ${t.level}/${t.max_level}</span>
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
                                             Prioridade Prydwen: ${t.talent_priority}
                                        </span>
                                    ` : ''}
                                    <span style="font-size:11px; padding:4px 10px; border-radius:12px; background:${t.level < t.max_level ? 'rgba(239,68,68,0.15)' : 'rgba(16,185,129,0.15)'}; color:${t.level < t.max_level ? '#f87171' : '#34d399'}; font-weight:600;">
                                        ${t.level < t.max_level ? `Ascensão Nv. ${t.level}/${t.max_level}` : `Nível ${t.max_level} OK`}
                                    </span>
                                    <span style="font-size:11px; padding:4px 10px; border-radius:12px; background:rgba(255,255,255,0.05); color:${gColor}; font-weight:bold; border:1px solid ${gColor}44;">
                                        Nota ${t.grade} (${t.score.toFixed(1)}%)
                                    </span>
                                </div>
                            </div>

                            <!-- Lista de Itens Detalhados -->
                            <div style="display:flex; flex-direction:column; gap:8px; font-size:12px;">
                    `;

                    const gameIdStr = (t.game_id || gameId || "genshin").toLowerCase().trim();
                    const ic = (t.items_needed && t.items_needed.icons) || {};

                    const defaultTermsByGame = {
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
                            mora: "https://act-webstatic.hoyoverse.com/game_record/genshin/equip/UI_ItemIcon_202.png",
                            xp: "https://act-webstatic.hoyoverse.com/game_record/genshin/equip/UI_ItemIcon_104003.png",
                            talent_book: "https://act-webstatic.hoyoverse.com/game_record/genshin/equip/UI_ItemIcon_104303.png",
                            boss: "https://act-webstatic.hoyoverse.com/game_record/genshin/equip/UI_ItemIcon_113001.png",
                            weekly_boss: "https://act-webstatic.hoyoverse.com/game_record/genshin/equip/UI_ItemIcon_113021.png",
                            crown: "https://act-webstatic.hoyoverse.com/game_record/genshin/equip/UI_ItemIcon_104319.png",
                            weapon_ore: "https://act-webstatic.hoyoverse.com/game_record/genshin/equip/UI_ItemIcon_104013.png"
                        }
                    };

                    const finalIcons = Object.assign({}, defaultIconsByGame[gameIdStr] || defaultIconsByGame.genshin, ic);

                    const moraIcon = `<img src="${finalIcons.mora}" style="width:18px; height:18px; vertical-align:middle; margin-right:4px; object-fit:contain;" onerror="this.onerror=null; this.outerHTML=' ';">`;
                    const xpIcon = `<img src="${finalIcons.xp}" style="width:18px; height:18px; vertical-align:middle; margin-right:4px; object-fit:contain;" onerror="this.onerror=null; this.outerHTML=' ';">`;
                    const talentIcon = `<img src="${finalIcons.talent_book}" style="width:18px; height:18px; vertical-align:middle; margin-right:4px; object-fit:contain;" onerror="this.onerror=null; this.outerHTML=' ';">`;
                    const bossIcon = `<img src="${finalIcons.boss}" style="width:18px; height:18px; vertical-align:middle; margin-right:4px; object-fit:contain;" onerror="this.onerror=null; this.outerHTML=' ';">`;
                    const weeklyIcon = `<img src="${finalIcons.weekly_boss}" style="width:18px; height:18px; vertical-align:middle; margin-right:4px; object-fit:contain;" onerror="this.onerror=null; this.outerHTML=' ';">`;
                    const crownIcon = `<img src="${finalIcons.crown}" style="width:18px; height:18px; vertical-align:middle; margin-right:4px; object-fit:contain;" onerror="this.onerror=null; this.outerHTML=' ';">`;
                    const oreIcon = `<img src="${finalIcons.weapon_ore}" style="width:18px; height:18px; vertical-align:middle; margin-right:4px; object-fit:contain;" onerror="this.onerror=null; this.outerHTML=' ';">`;

                    // 1. Ascensão de Personagem
                    if (t.items_needed && t.items_needed.ascension) {
                        const asc = t.items_needed.ascension;
                        html += `
                            <div style="background:rgba(239,68,68,0.05); padding:10px 12px; border-radius:8px; border-left:3px solid #ef4444;">
                                <strong style="color:#f87171; display:flex; align-items:center; gap:6px; margin-bottom:6px; font-size:13px;">
                                     Elevação de Nível & Ascensão do Personagem (Nv. ${t.level} ➔ Nv. ${t.max_level})
                                </strong>
                                <div style="color:#cbd5e1; line-height:1.6; font-size:12px; display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:6px;">
                                    <div>${xpIcon} <strong>${terms.xp_book_name}:</strong> ${asc.xp_needed.toLocaleString()} EXP (~${asc.xp_books_purple} un. Roxos)</div>
                                    <div>${moraIcon} <strong>${terms.currency_name}:</strong> ${asc.currency_needed.toLocaleString()}</div>
                                    ${asc.boss_items_needed > 0 ? `<div>${bossIcon} <strong>${asc.boss_item_name}:</strong> ${asc.boss_items_needed} un.</div>` : ''}
                                </div>
                            </div>
                        `;
                    }

                    // 2. Talentos / Habilidades
                    if (t.items_needed && t.items_needed.talent_upgrade_details && t.items_needed.talent_upgrade_details.length > 0) {
                        html += `
                            <div style="background:rgba(56,189,248,0.05); padding:10px 12px; border-radius:8px; border-left:3px solid #38bdf8;">
                                <strong style="color:#38bdf8; display:flex; align-items:center; gap:6px; margin-bottom:8px; font-size:13px;">
                                     Elevação de ${terms.talent_category} Detalhada por Habilidade:
                                </strong>
                                <div style="display:flex; flex-direction:column; gap:6px;">
                        `;
                        t.items_needed.talent_upgrade_details.forEach(td => {
                            let matsList = [];
                            if (td.green_books > 0) matsList.push(`${talentIcon} ${td.green_books}x ${terms.green_book}`);
                            if (td.blue_books > 0) matsList.push(`${talentIcon} ${td.blue_books}x ${terms.blue_book}`);
                            if (td.purple_books > 0) matsList.push(`${talentIcon} ${td.purple_books}x ${terms.purple_book}`);
                            if (td.enemy_tier1 > 0) matsList.push(`${bossIcon} ${td.enemy_tier1}x ${terms.enemy_t1 || 'Drop Inimigo (1★)'}`);
                            if (td.enemy_tier2 > 0) matsList.push(`${bossIcon} ${td.enemy_tier2}x ${terms.enemy_t2 || 'Drop Inimigo (2★)'}`);
                            if (td.enemy_tier3 > 0) matsList.push(`${bossIcon} ${td.enemy_tier3}x ${terms.enemy_t3 || 'Drop Inimigo (3★)'}`);
                            if (td.weekly_boss_mats > 0) matsList.push(`${weeklyIcon} ${td.weekly_boss_mats}x ${terms.weekly_boss_mat}`);
                            if (td.crowns_needed > 0) matsList.push(`${crownIcon} ${td.crowns_needed}x ${terms.crown_mat}`);

                            const skillIconHtml = td.skill_icon ? `<img src="${td.skill_icon}" style="width:20px; height:20px; vertical-align:middle; margin-right:6px; object-fit:contain; border-radius:4px; background:rgba(0,0,0,0.3); padding:2px;">` : talentIcon;

                            html += `
                                <div style="background:rgba(0,0,0,0.3); padding:8px 12px; border-radius:6px; border:1px solid rgba(255,255,255,0.05);">
                                    <div style="font-weight:600; color:#f1f5f9; display:flex; justify-content:space-between; align-items:center; font-size:12px;">
                                        <span style="display:flex; align-items:center; gap:4px;">${skillIconHtml} ${td.skill_name}</span>
                                        <span style="font-size:11px; color:#38bdf8; background:rgba(56,189,248,0.15); padding:2px 8px; border-radius:12px; font-weight:600;">
                                            Nv. ${td.current_level} ➔ Nv. ${td.target_level}
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
                        if (wd.ores_needed > 0) wMats.push(`<div>${oreIcon} <strong>${terms.ore_name}:</strong> ~${wd.ores_needed} un.</div>`);
                        if (wd.w_mat_green > 0) wMats.push(`<div>${talentIcon} <strong>${terms.w_mat_green || 'Mat. Domínio Arma (2★)'}:</strong> ${wd.w_mat_green} un.</div>`);
                        if (wd.w_mat_blue > 0) wMats.push(`<div>${talentIcon} <strong>${terms.w_mat_blue || 'Mat. Domínio Arma (3★)'}:</strong> ${wd.w_mat_blue} un.</div>`);
                        if (wd.w_mat_purple > 0) wMats.push(`<div>${talentIcon} <strong>${terms.w_mat_purple || 'Mat. Domínio Arma (4★)'}:</strong> ${wd.w_mat_purple} un.</div>`);
                        if (wd.w_mat_gold > 0) wMats.push(`<div>${talentIcon} <strong>${terms.w_mat_gold || 'Mat. Domínio Arma (5★)'}:</strong> ${wd.w_mat_gold} un.</div>`);
                        if (wd.w_enemy_t1 > 0) wMats.push(`<div>${bossIcon} <strong>${terms.enemy_t1 || 'Drop Inimigo (1★)'}:</strong> ${wd.w_enemy_t1} un.</div>`);
                        if (wd.w_enemy_t2 > 0) wMats.push(`<div>${bossIcon} <strong>${terms.enemy_t2 || 'Drop Inimigo (2★)'}:</strong> ${wd.w_enemy_t2} un.</div>`);
                        if (wd.w_enemy_t3 > 0) wMats.push(`<div>${bossIcon} <strong>${terms.enemy_t3 || 'Drop Inimigo (3★)'}:</strong> ${wd.w_enemy_t3} un.</div>`);
                        if (wd.currency_needed > 0) wMats.push(`<div>${moraIcon} <strong>${terms.currency_name}:</strong> ${wd.currency_needed.toLocaleString()}</div>`);

                        html += `
                            <div style="background:rgba(16,185,129,0.05); padding:10px 12px; border-radius:8px; border-left:3px solid #10b981;">
                                <strong style="color:#34d399; display:flex; align-items:center; gap:8px; margin-bottom:6px; font-size:13px;">
                                    ${wIconImg} Elevação da Arma Equipada (${wd.weapon_name}) - Nv. ${wd.current_level} ➔ Nv. ${wd.target_level}
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
                                <strong style="color:#f59e0b; display:block; margin-bottom:2px;"> Relíquias & Equipamentos:</strong>
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

            const saveAndReload = () => {
                const checkedCbs = document.querySelectorAll(`.${targetContainerId}-char-cb:checked`);
                const newSelected = Array.from(checkedCbs).map(cb => cb.dataset.char);
                localStorage.setItem(storageKey, JSON.stringify(newSelected));
                window.loadFarmData(gameId, targetContainerId);
            };

            document.querySelectorAll(`.${targetContainerId}-char-cb`).forEach(cb => {
                cb.addEventListener("change", saveAndReload);
            });

            const btnSelAll = document.getElementById(`${targetContainerId}-select-all`);
            if (btnSelAll) {
                btnSelAll.onclick = () => {
                    localStorage.setItem(storageKey, JSON.stringify(allRosterNames));
                    window.loadFarmData(gameId, targetContainerId);
                };
            }

            const btnDeselAll = document.getElementById(`${targetContainerId}-deselect-all`);
            if (btnDeselAll) {
                btnDeselAll.onclick = () => {
                    localStorage.setItem(storageKey, JSON.stringify([]));
                    window.loadFarmData(gameId, targetContainerId);
                };
            }

        } catch (e) {
            console.error(e);
            body.innerHTML = "<div style='color:#ef4444; padding:16px;'>Erro ao carregar dados da Central de Farm.</div>";
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

    // 3. RELÍQUIAS LIXO (TRASH FINDER)
    window.loadTrashRelics = async (gameId, targetContainerId = "trash-relics-body") => {
        const body = document.getElementById(targetContainerId);
        if (!body) return;
        body.innerHTML = "<div style='color:#94a3b8;'>Analisando banco de relíquias contra o metagame...</div>";
        try {
            const res = await fetch(`/api/relics/trash/${gameId}`);
            const data = await res.json();
            
            let html = "";
            if (!data.total_analyzed || data.total_analyzed === 0) {
                html = `
                    <div style="padding:16px; background:rgba(245, 158, 11, 0.08); border-radius:10px; border:1px solid rgba(245, 158, 11, 0.3); color:#f59e0b; font-size:13px; line-height:1.5;">
                        <strong style="font-size:14px; display:block; margin-bottom:4px;"> Nenhum dado de relíquias/artefatos encontrado no banco de dados.</strong>
                        Sincronize seu perfil e lista de personagens no painel principal via HoyoLab / UID para importar suas relíquias equipadas para análise.
                    </div>
                `;
            } else {
                html = `
                    <div style="padding:14px; background:rgba(239, 68, 68, 0.08); border-radius:10px; margin-bottom:16px; border:1px solid rgba(239, 68, 68, 0.3);">
                        <div style="font-size:15px; font-weight:bold; color:#ef4444;">${data.trash_count} peça(s) lixo encontradas de ${data.total_analyzed} analisadas</div>
                        <div style="font-size:12px; color:#94a3b8; margin-top:3px;">Estas peças possuem combinações de Atributos Principais e Substatus que nenhum personagem do meta aproveita.</div>
                    </div>
                `;

                const trashList = data.trash_relics || [];
                if (trashList.length === 0) {
                    html += `<div style="font-size:13px; color:#10b981;">Nenhuma relíquia lixo detectada! Seu inventário está limpo.</div>`;
                } else {
                trashList.forEach(r => {
                    html += `
                        <div style="padding:12px; background:rgba(15,23,42,0.6); border-radius:8px; margin-bottom:10px; border:1px solid rgba(255,255,255,0.06); font-size:13px;">
                            <div style="display:flex; justify-content:space-between;">
                                <strong style="color:#ffffff;">${r.name} (${r.slot})</strong>
                                <span style="color:#ef4444; font-weight:bold; font-size:12px;">${r.main_stat}</span>
                            </div>
                            <div style="color:#94a3b8; font-size:12px; margin-top:4px;">Substatus: ${r.substats ? r.substats.join(", ") : "Nenhum"}</div>
                            <div style="color:#f59e0b; font-size:12px; margin-top:3px;">Motivo: ${r.reason}</div>
                        </div>
                    `;
                });
            }
        }
        body.innerHTML = html;
        } catch (e) {
            body.innerHTML = "<div style='color:#ef4444;'>Erro ao analisar relíquias lixo.</div>";
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
                        <span style="font-size:12px; color:#94a3b8;">Total Personagens</span>
                        <h3 style="margin:4px 0 0 0; color:#38bdf8; font-size:20px;">${data.total_characters}</h3>
                    </div>
                    <div style="padding:12px; background:rgba(255,255,255,0.03); border-radius:10px; text-align:center; border:1px solid var(--border-color);">
                        <span style="font-size:12px; color:#94a3b8;">Média de Nota RV</span>
                        <h3 style="margin:4px 0 0 0; color:#f59e0b; font-size:20px;">${data.avg_rv}%</h3>
                    </div>
                    <div style="padding:12px; background:rgba(255,255,255,0.03); border-radius:10px; text-align:center; border:1px solid var(--border-color);">
                        <span style="font-size:12px; color:#94a3b8;">Builds Nota S/SSS</span>
                        <h3 style="margin:4px 0 0 0; color:#10b981; font-size:20px;">${data.s_count}</h3>
                    </div>
                </div>
                <h4 style="margin:0 0 12px 0; color:#a855f7; font-size:16px;"> Tier List dos seus Personagens por Nota RV</h4>
            `;

            const tierColors = { "S+": "#ef4444", "S": "#f59e0b", "A": "#10b981", "B": "#38bdf8", "C/D": "#94a3b8" };
            const tierList = data.tier_list || {};

            for (const [tier, chars] of Object.entries(tierList)) {
                const color = tierColors[tier] || '#94a3b8';
                html += `
                    <div style="display:flex; align-items:center; gap:14px; margin-bottom:12px; padding:12px; background:rgba(15,23,42,0.6); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">
                        <div style="width:54px; min-width:54px; height:54px; background:${color}; color:#000; font-weight:800; display:flex; align-items:center; justify-content:center; border-radius:10px; font-size:18px; box-shadow: 0 4px 12px ${color}44;">${tier}</div>
                        <div style="display:flex; flex-wrap:wrap; gap:10px; flex:1; align-items:center;">
                `;
                if (!chars || chars.length === 0) {
                    html += `<span style="font-size:13px; color:#64748b; font-style:italic;">Nenhum personagem nesta categoria</span>`;
                } else {
                    chars.forEach(c => {
                        const iconSrc = c.icon || '';
                        const iconHtml = iconSrc ? `<img src="${iconSrc}" alt="${c.name}" style="width:52px; height:52px; border-radius:10px; object-fit:cover; border:2px solid ${color}; background:rgba(0,0,0,0.5); flex-shrink:0;" onerror="this.style.display='none'">` : '';
                        html += `
                            <div style="display:flex; align-items:center; gap:10px; padding:8px 14px; background:rgba(255,255,255,0.06); border-radius:10px; border:1px solid rgba(255,255,255,0.1); min-height:64px; transition:all 0.2s ease;" onmouseover="this.style.borderColor='${color}'; this.style.transform='translateY(-2px)'" onmouseout="this.style.borderColor='rgba(255,255,255,0.1)'; this.style.transform='none'">
                                ${iconHtml}
                                <div style="display:flex; flex-direction:column; justify-content:center;">
                                    <strong style="color:#ffffff; font-size:13px; font-weight:600; line-height:1.2;">${c.name}</strong>
                                    <div style="display:flex; align-items:center; gap:6px; margin-top:3px;">
                                        <span style="color:${color}; font-weight:700; font-size:12px;">${c.score.toFixed(1)}%</span>
                                        <span style="font-size:10px; color:#ffffff; font-weight:bold; background:rgba(255,255,255,0.12); padding:1px 6px; border-radius:4px;">${c.grade}</span>
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
                    alert(data.message || "Pastas e banco de dados apagados com sucesso!");
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

    const name = cData.name || "Personagem";
    iconEl.src = cData.icon || "/assets/logo.svg";
    nameEl.textContent = name;

    const base = cData.base || {};
    const target = cData.target || {};
    const diffs = cData.diffs || {};

    if (cData.is_new) {
        subEl.innerHTML = `<span style="color: #f59e0b; font-weight: 700;">★ Novo Personagem Adquirido!</span>`;
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

    html += `<div class="diff-section-title"><i class="fa-solid fa-wand-magic-sparkles"></i> Arma / Cone de Luz / W-Engine Equipado</div>`;
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
                    ` : `<span style="font-size: 12px; color: var(--text-muted); font-style: italic;">Nenhuma arma no snapshot anterior</span>`}
                </div>
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 11px; color: #10b981; font-weight: 700;">SNAPSHOT ATUAL (COMPARADO)</span>
                        ${weaponSwapped ? `<span class="diff-arrow-badge">Arma Trocada</span>` : (weaponLeveled ? `<span class="diff-badge-gain">Evoluída</span>` : '')}
                    </div>
                    ${wTarget && wTarget.name ? `
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <img src="${wTarget.icon || '/assets/logo.svg'}" style="width: 44px; height: 44px; border-radius: 8px; object-fit: cover; border: 2px solid ${weaponSwapped ? '#ec4899' : '#10b981'}; box-shadow: 0 0 10px ${weaponSwapped ? 'rgba(236,72,153,0.3)' : 'rgba(16,185,129,0.3)'};" onerror="this.src='/assets/logo.svg'">
                            <div>
                                <strong style="font-size: 13px; color: #fff; display: block;">${wTarget.name}</strong>
                                <span style="font-size: 11px; color: #10b981; font-weight: 600;">Nv. ${wTarget.level || 1} ${wTarget.rank ? `• Refinamento R${wTarget.rank}` : ''}</span>
                            </div>
                        </div>
                    ` : `<span style="font-size: 12px; color: var(--text-muted); font-style: italic;">Nenhuma arma registrada</span>`}
                </div>
            </div>
        `;
    } else {
        html += `<p style="font-size: 12px; color: var(--text-muted); font-style: italic;">Informações de arma não disponíveis.</p>`;
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
        html += `<div class="diff-section-title"><i class="fa-solid fa-chart-line"></i> Status Gerais do Personagem (Atributos Finais)</div>`;
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

    html += `<div class="diff-section-title"><i class="fa-solid fa-gem"></i> Comparativo de Artefatos & Relíquias Equipados</div>`;
    
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
        html += `<p style="font-size: 12px; color: var(--text-muted); font-style: italic;">Detalhes de relíquias não salvos no snapshot base/comparado.</p>`;
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

// ==========================================
// GERADOR DE CARD DE COMPARATIVO DE BUILD (PNG)
// ==========================================

window.generateAndOpenDiffCardModal = async function() {
    const cData = window.currentDiffDataCache;
    if (!cData) {
        showToast("Nenhum comparativo selecionado para gerar card.");
        return;
    }

    const modal = document.getElementById("modal-export-diff-card");
    const container = document.getElementById("diff-card-preview-container");
    const downloadBtn = document.getElementById("btn-download-diff-card-png");
    const copyBtn = document.getElementById("btn-copy-diff-card-png");

    if (!modal || !container) return;

    modal.style.display = "flex";
    container.innerHTML = `<p style="color: var(--text-muted); padding: 40px; font-size: 14px;"><i class="fa-solid fa-spinner fa-spin fa-2x" style="color: #ec4899; margin-bottom: 12px; display: block;"></i> Renderizando Card em Alta Resolução...</p>`;

    try {
        const canvas = await generateDiffCardCanvas(cData);
        container.innerHTML = "";
        
        const img = document.createElement("img");
        img.src = canvas.toDataURL("image/png");
        img.style.maxWidth = "100%";
        img.style.maxHeight = "60vh";
        img.style.borderRadius = "10px";
        img.style.boxShadow = "0 10px 30px rgba(0,0,0,0.5)";
        container.appendChild(img);

        if (downloadBtn) {
            downloadBtn.href = img.src;
            downloadBtn.download = `comparativo_${(cData.name || 'personagem').toLowerCase().replace(/\s+/g, '_')}.png`;
        }

        if (copyBtn) {
            copyBtn.onclick = async () => {
                try {
                    canvas.toBlob(async (blob) => {
                        if (!blob) throw new Error("Falha ao criar blob.");
                        await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
                        showToast("Card de comparativo copiado para a área de transferência!", "success");
                    });
                } catch (err) {
                    showToast("Erro ao copiar imagem: " + err.message);
                }
            };
        }
    } catch (err) {
        console.error("Erro ao gerar card:", err);
        container.innerHTML = `<p style="color: #ef4444; padding: 20px;"><i class="fa-solid fa-triangle-exclamation"></i> Ocorreu um erro ao gerar o card da comparação: ${err.message}</p>`;
    }
};

async function generateDiffCardCanvas(cData) {
    const canvas = document.createElement("canvas");
    const width = 1200;
    const height = 860;
    canvas.width = width * 2;
    canvas.height = height * 2;
    const ctx = canvas.getContext("2d");
    ctx.scale(2, 2);

    // Helpers de desenho no Canvas
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
            img.onerror = () => resolve(null);
            img.src = finalUrl;
        });
    }

    // Fundo Gradiente Escuro Elegante
    const bgGrad = ctx.createLinearGradient(0, 0, width, height);
    bgGrad.addColorStop(0, "#0b0f19");
    bgGrad.addColorStop(0.5, "#0f172a");
    bgGrad.addColorStop(1, "#180a22");
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, width, height);

    // Glow de Destaque Rosa/Violeta
    const glowGrad = ctx.createRadialGradient(200, 150, 20, 200, 150, 600);
    glowGrad.addColorStop(0, "rgba(236, 72, 153, 0.18)");
    glowGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
    ctx.fillStyle = glowGrad;
    ctx.fillRect(0, 0, width, height);

    // Carrega Imagem do Personagem
    const charImg = await loadImage(cData.icon);

    const base = cData.base || {};
    const target = cData.target || {};
    const diffs = cData.diffs || {};

    // 1. CABEÇALHO DO CARD
    drawRoundedRect(30, 24, width - 60, 110, 16, "rgba(15, 23, 42, 0.8)", "rgba(236, 72, 153, 0.4)", 1.5);

    if (charImg) {
        ctx.save();
        ctx.beginPath();
        ctx.arc(85, 79, 40, 0, Math.PI * 2);
        ctx.closePath();
        ctx.clip();
        ctx.drawImage(charImg, 45, 39, 80, 80);
        ctx.restore();

        ctx.beginPath();
        ctx.arc(85, 79, 40, 0, Math.PI * 2);
        ctx.strokeStyle = "#ec4899";
        ctx.lineWidth = 3;
        ctx.stroke();
    }

    ctx.fillStyle = "#fff";
    ctx.font = "bold 24px sans-serif";
    ctx.fillText(cData.name || "Personagem", 145, 62);

    ctx.fillStyle = "rgba(255, 255, 255, 0.6)";
    ctx.font = "14px sans-serif";
    ctx.fillText(`EVOLUÇÃO DE BUILD • ${cData.rarity || 5}★ ${cData.element || ''}`, 145, 86);

    const scorePrev = base.score || 0.0;
    const scoreCurr = target.score || 0.0;
    const scoreDiff = diffs.score_diff !== undefined ? diffs.score_diff : (scoreCurr - scorePrev).toFixed(1);

    // KPI Badge no Canto do Cabeçalho
    drawRoundedRect(width - 240, 42, 190, 74, 12, "rgba(236, 72, 153, 0.15)", "rgba(236, 72, 153, 0.4)");
    ctx.fillStyle = "#ec4899";
    ctx.font = "bold 11px sans-serif";
    ctx.fillText("EVOLUÇÃO RV (BUILD SCORE)", width - 225, 62);
    ctx.fillStyle = "#fff";
    ctx.font = "bold 20px sans-serif";
    ctx.fillText(`${scorePrev ? scorePrev + '% ➔ ' : ''}${scoreCurr}%`, width - 225, 90);
    if (parseFloat(scoreDiff) > 0) {
        ctx.fillStyle = "#10b981";
        ctx.font = "bold 13px sans-serif";
        ctx.fillText(`+${scoreDiff}%`, width - 85, 90);
    }

    // 2. SEÇÃO DA ARMA
    drawRoundedRect(30, 150, 560, 95, 12, "rgba(0, 0, 0, 0.4)", "rgba(255, 255, 255, 0.1)");
    ctx.fillStyle = "#38bdf8";
    ctx.font = "bold 13px sans-serif";
    ctx.fillText("ARMA / CONE DE LUZ / W-ENGINE", 45, 170);

    const wBase = base.weapon || (base.weapon_name ? { name: base.weapon_name, level: base.weapon_level, icon: base.weapon_icon } : null);
    const wTarget = target.weapon || (target.weapon_name ? { name: target.weapon_name, level: target.weapon_level, icon: target.weapon_icon } : null);

    const wBaseImg = await loadImage(wBase?.icon);
    const wTargetImg = await loadImage(wTarget?.icon);

    if (wBaseImg) ctx.drawImage(wBaseImg, 45, 180, 42, 42);
    ctx.fillStyle = "#94a3b8";
    ctx.font = "12px sans-serif";
    ctx.fillText(wBase?.name || "Nenhuma", 98, 197);
    ctx.font = "11px sans-serif";
    ctx.fillText(`Nv. ${wBase?.level || 1}`, 98, 213);

    ctx.fillStyle = "#ec4899";
    ctx.font = "bold 16px sans-serif";
    ctx.fillText("➔", 285, 205);

    if (wTargetImg) ctx.drawImage(wTargetImg, 315, 180, 42, 42);
    ctx.fillStyle = "#fff";
    ctx.font = "bold 13px sans-serif";
    ctx.fillText(wTarget?.name || "Nenhuma", 368, 197);
    ctx.fillStyle = "#10b981";
    ctx.font = "11px sans-serif";
    ctx.fillText(`Nv. ${wTarget?.level || 1}`, 368, 213);

    // 2.5. SEÇÃO DE HABILIDADES E TALENTOS
    drawRoundedRect(30, 255, 560, 130, 12, "rgba(0, 0, 0, 0.4)", "rgba(255, 255, 255, 0.1)");
    ctx.fillStyle = "#38bdf8";
    ctx.font = "bold 13px sans-serif";
    ctx.fillText("EVOLUÇÃO DE HABILIDADES & TALENTOS", 45, 275);

    const skillsBase = base.skills || [];
    const skillsTarget = target.skills || [];
    const allSkillNames = listUniqueSkillKeys(skillsBase, skillsTarget).slice(0, 6);

    // Carrega em paralelo os ícones de todas as habilidades para desenhar no card
    const skillImgMap = {};
    await Promise.all(allSkillNames.map(async sName => {
        const sb = skillsBase.find(x => (x.name || x.skill_name) === sName);
        const st = skillsTarget.find(x => (x.name || x.skill_name) === sName);
        const iconUrl = (st || sb || {}).icon;
        if (iconUrl) {
            const img = await loadImage(iconUrl);
            if (img) skillImgMap[sName] = img;
        }
    }));

    if (allSkillNames.length === 0) {
        ctx.fillStyle = "#94a3b8";
        ctx.font = "italic 11px sans-serif";
        ctx.fillText("Sem dados de habilidades para comparar", 60, 315);
    } else {
        for (let idx = 0; idx < allSkillNames.length; idx++) {
            const sName = allSkillNames[idx];
            const sb = skillsBase.find(x => (x.name || x.skill_name) === sName);
            const st = skillsTarget.find(x => (x.name || x.skill_name) === sName);
            const lvlB = sb ? (sb.level || sb.lvl || 0) : 0;
            const lvlT = st ? (st.level || st.lvl || 0) : 0;
            const diff = lvlT - lvlB;

            const col = idx % 2;
            const row = Math.floor(idx / 2);

            const xPill = col === 0 ? 45 : 315;
            const yPill = 287 + row * 28;

            drawRoundedRect(xPill, yPill, 255, 24, 6, "rgba(15, 23, 42, 0.8)", "rgba(255, 255, 255, 0.05)");

            const sImg = skillImgMap[sName];
            let xText = xPill + 10;
            if (sImg) {
                ctx.save();
                ctx.beginPath();
                ctx.arc(xPill + 16, yPill + 12, 9, 0, Math.PI * 2);
                ctx.closePath();
                ctx.clip();
                ctx.drawImage(sImg, xPill + 7, yPill + 3, 18, 18);
                ctx.restore();
                xText = xPill + 30;
            }

            const maxNameLen = sImg ? 14 : 17;
            const displayName = sName.length > maxNameLen ? sName.substring(0, maxNameLen - 2) + '...' : sName;
            ctx.fillStyle = "#cbd5e1";
            ctx.font = "11px sans-serif";
            ctx.fillText(displayName, xText, yPill + 16);

            ctx.fillStyle = "#fff";
            ctx.font = "bold 11px sans-serif";
            const lvlText = `${lvlB ? lvlB + ' ➔ ' : ''}Nv. ${lvlT}`;
            ctx.fillText(lvlText, xPill + 160, yPill + 16);

            if (diff > 0) {
                ctx.fillStyle = "#10b981";
                ctx.font = "bold 10px sans-serif";
                ctx.fillText(`+${diff}`, xPill + 232, yPill + 16);
            }
        }
    }

    // 3. ATRIBUTOS GERAIS
    drawRoundedRect(30, 395, 560, 435, 12, "rgba(0, 0, 0, 0.4)", "rgba(255, 255, 255, 0.1)");
    ctx.fillStyle = "#38bdf8";
    ctx.font = "bold 13px sans-serif";
    ctx.fillText("ATRIBUTOS FINAIS COMPARADOS", 45, 417);

    const statsBase = base.stats || {};
    const statsTarget = target.stats || {};
    const keys = listUniqueDictKeys(statsBase, statsTarget).slice(0, 10);

    let yStat = 432;
    if (keys.length === 0) {
        ctx.fillStyle = "#94a3b8";
        ctx.font = "italic 12px sans-serif";
        ctx.fillText("Sem atributos comparativos registrados", 60, yStat + 20);
    } else {
        keys.forEach(k => {
            const valB = statsBase[k] !== undefined ? String(statsBase[k]) : 'N/A';
            const valT = statsTarget[k] !== undefined ? String(statsTarget[k]) : 'N/A';

            drawRoundedRect(45, yStat, 530, 34, 8, "rgba(15, 23, 42, 0.8)", "rgba(255,255,255,0.05)");
            ctx.fillStyle = "#94a3b8";
            ctx.font = "11px sans-serif";
            ctx.fillText(k, 60, yStat + 21);

            ctx.fillStyle = "#fff";
            ctx.font = "bold 11px sans-serif";
            const valStr = `${valB !== 'N/A' && valB !== valT ? valB + ' ➔ ' : ''}${valT}`;
            ctx.fillText(valStr, 320, yStat + 21);

            const numB = parseFloat(valB.replace(/[^0-9.-]/g, ''));
            const numT = parseFloat(valT.replace(/[^0-9.-]/g, ''));
            if (!isNaN(numB) && !isNaN(numT) && numB !== numT) {
                const diffVal = (numT - numB).toFixed(1);
                const isPct = valT.includes('%');
                ctx.fillStyle = parseFloat(diffVal) > 0 ? "#10b981" : "#ef4444";
                ctx.font = "bold 11px sans-serif";
                ctx.fillText(`${parseFloat(diffVal) > 0 ? '+' : ''}${diffVal}${isPct ? '%' : ''}`, 490, yStat + 21);
            } else if (valB === valT && valT !== 'N/A') {
                ctx.fillStyle = "#64748b";
                ctx.font = "10px sans-serif";
                ctx.fillText("Mantido", 495, yStat + 21);
            }

            yStat += 38;
        });
    }

    // 4. COMPARATIVO DE ARTEFATOS (PAINEL DIREITO "FOI DESSE PRA ESSE" COM SUBSTATUS)
    drawRoundedRect(610, 150, 560, 680, 12, "rgba(0, 0, 0, 0.4)", "rgba(255, 255, 255, 0.1)");
    ctx.fillStyle = "#38bdf8";
    ctx.font = "bold 13px sans-serif";
    ctx.fillText("ARTEFATOS & RELÍQUIAS (DE ➔ PARA)", 625, 175);

    const relicsBase = base.relics || [];
    const relicsTarget = target.relics || [];
    const pairs = buildRelicSlotPairs(relicsBase, relicsTarget).slice(0, 6);

    let yRelic = 192;
    for (let i = 0; i < pairs.length; i++) {
        const p = pairs[i];
        const rb = p.base || {};
        const rt = p.target || {};
        const isReplaced = rb.name && rt.name && (rb.name !== rt.name || rb.main !== rt.main);

        const subListB = parseSubstats(rb.sub);
        const subListT = parseSubstats(rt.sub);

        drawRoundedRect(625, yRelic, 530, 98, 10, isReplaced ? "rgba(236, 72, 153, 0.08)" : "rgba(15, 23, 42, 0.8)", isReplaced ? "rgba(236, 72, 153, 0.3)" : "rgba(255, 255, 255, 0.06)");

        ctx.fillStyle = isReplaced ? "#ec4899" : "#38bdf8";
        ctx.font = "bold 11px sans-serif";
        ctx.fillText(`${p.slot.toUpperCase()} ${isReplaced ? '• PEÇA TROCADA' : '• MANTIDA'}`, 638, yRelic + 16);

        const rBaseImg = await loadImage(rb.icon);
        const rTargetImg = await loadImage(rt.icon);

        if (isReplaced) {
            // EXIBE COMPARATIVO ANTERIOR (BASE) ➔ ATUAL (TARGET)
            if (rBaseImg) ctx.drawImage(rBaseImg, 638, yRelic + 22, 34, 34);
            ctx.fillStyle = "#94a3b8";
            ctx.font = "10px sans-serif";
            const nameB = (rb.name || "Vazio");
            ctx.fillText(nameB.length > 22 ? nameB.substring(0, 20) + '...' : nameB, 678, yRelic + 34);
            ctx.fillStyle = "#f59e0b";
            ctx.font = "bold 10px sans-serif";
            ctx.fillText(rb.main || "", 678, yRelic + 48);

            // Substats Base
            if (subListB.length > 0) {
                let subY = yRelic + 62;
                ctx.font = "9px sans-serif";
                const line1 = subListB.slice(0, 2);
                const line2 = subListB.slice(2, 4);

                if (line1.length > 0) {
                    let offX = 678;
                    line1.forEach(s => {
                        ctx.fillStyle = s.isCrit ? "#f59e0b" : "#94a3b8";
                        ctx.fillText(s.text, offX, subY);
                        offX += ctx.measureText(s.text).width + 8;
                    });
                }
                if (line2.length > 0) {
                    subY += 12;
                    let offX = 678;
                    line2.forEach(s => {
                        ctx.fillStyle = s.isCrit ? "#f59e0b" : "#94a3b8";
                        ctx.fillText(s.text, offX, subY);
                        offX += ctx.measureText(s.text).width + 8;
                    });
                }
            }

            // Seta Central de Troca
            ctx.fillStyle = "#ec4899";
            ctx.font = "bold 15px sans-serif";
            ctx.fillText("➔", 876, yRelic + 42);

            // Item Atual (Target)
            if (rTargetImg) ctx.drawImage(rTargetImg, 898, yRelic + 22, 34, 34);
            ctx.fillStyle = "#fff";
            ctx.font = "bold 10px sans-serif";
            const nameT = (rt.name || "Vazio");
            ctx.fillText(nameT.length > 22 ? nameT.substring(0, 20) + '...' : nameT, 938, yRelic + 34);
            ctx.fillStyle = "#10b981";
            ctx.font = "bold 10px sans-serif";
            ctx.fillText(rt.main || "", 938, yRelic + 48);

            // Substats Target
            if (subListT.length > 0) {
                let subY = yRelic + 62;
                ctx.font = "9px sans-serif";
                const line1 = subListT.slice(0, 2);
                const line2 = subListT.slice(2, 4);

                if (line1.length > 0) {
                    let offX = 938;
                    line1.forEach(s => {
                        ctx.fillStyle = s.isCrit ? "#f59e0b" : "#cbd5e1";
                        ctx.fillText(s.text, offX, subY);
                        offX += ctx.measureText(s.text).width + 8;
                    });
                }
                if (line2.length > 0) {
                    subY += 12;
                    let offX = 938;
                    line2.forEach(s => {
                        ctx.fillStyle = s.isCrit ? "#f59e0b" : "#cbd5e1";
                        ctx.fillText(s.text, offX, subY);
                        offX += ctx.measureText(s.text).width + 8;
                    });
                }
            }
        } else {
            // ARTEFATO MANTIDO (EXIBE DETALHADO DO ATUAL OU BASE)
            const itemObj = rt.name ? rt : rb;
            const rImg = rTargetImg || rBaseImg;
            const subList = subListT.length > 0 ? subListT : subListB;

            if (rImg) ctx.drawImage(rImg, 638, yRelic + 22, 38, 38);
            ctx.fillStyle = "#fff";
            ctx.font = "bold 11px sans-serif";
            ctx.fillText(itemObj.name || "Vazio", 684, yRelic + 34);
            ctx.fillStyle = "#10b981";
            ctx.font = "bold 10px sans-serif";
            ctx.fillText(itemObj.main || "", 684, yRelic + 48);

            // Substats Mantidos (Dispostos em 2 linhas horizontais organizadas)
            if (subList.length > 0) {
                ctx.font = "10px sans-serif";
                const line1 = subList.slice(0, 2);
                const line2 = subList.slice(2, 4);

                if (line1.length > 0) {
                    let offX = 684;
                    line1.forEach(s => {
                        ctx.fillStyle = s.isCrit ? "#f59e0b" : "#94a3b8";
                        ctx.fillText(s.text, offX, yRelic + 64);
                        offX += ctx.measureText(s.text).width + 16;
                    });
                }
                if (line2.length > 0) {
                    let offX = 684;
                    line2.forEach(s => {
                        ctx.fillStyle = s.isCrit ? "#f59e0b" : "#94a3b8";
                        ctx.fillText(s.text, offX, yRelic + 80);
                        offX += ctx.measureText(s.text).width + 16;
                    });
                }
            }
        }

        yRelic += 105;
    }

    // Rodapé Marca D'água
    ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
    ctx.font = "11px sans-serif";
    ctx.fillText("Gerado via HoYo Hub • Comparativo Automático de Snapshots de Evolução", 30, height - 12);

    return canvas;
}

function listUniqueSkillKeys(arrA, arrB) {
    const set = new Set();
    (arrA || []).forEach(x => { if (x && (x.name || x.skill_name)) set.add(x.name || x.skill_name); });
    (arrB || []).forEach(x => { if (x && (x.name || x.skill_name)) set.add(x.name || x.skill_name); });
    return Array.from(set);
}

function listUniqueDictKeys(dictA, dictB) {
    const set = new Set();
    Object.keys(dictA || {}).forEach(k => set.add(k));
    Object.keys(dictB || {}).forEach(k => set.add(k));
    return Array.from(set);
}

window.loadAccountHistory = async (gameId = "hsr") => {
    const container = document.getElementById("tab-history-body");
    if (!container) return;

    const btnSnapshot = document.getElementById("btn-create-snapshot-now");
    if (btnSnapshot && !btnSnapshot.dataset.bound) {
        btnSnapshot.dataset.bound = "true";
        btnSnapshot.addEventListener("click", async () => {
            btnSnapshot.disabled = true;
            btnSnapshot.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Gerando Snapshot...`;
            try {
                const res = await fetch("/api/sync/global", { method: "POST" });
                const resData = await res.json();
                if (resData.success) {
                    showToast("Snapshot de evolução criado com sucesso!", "success");
                    window.loadAccountHistory(currentGameIdHistory || gameId);
                } else {
                    showToast("Erro ao criar snapshot: " + (resData.message || "Erro desconhecido"));
                }
            } catch (e) {
                showToast("Erro de rede ao criar snapshot.");
            } finally {
                btnSnapshot.disabled = false;
                btnSnapshot.innerHTML = `<i class="fa-solid fa-camera-retro"></i> Criar Novo Snapshot Agora`;
            }
        });
    }

    container.innerHTML = `
        <div style="padding: 40px; text-align: center; color: var(--text-secondary);">
            <i class="fa-solid fa-spinner fa-spin fa-2x" style="color: #ec4899;"></i>
            <p style="margin-top: 12px; font-weight: 500;">Buscando linha do tempo e realizando comparativo de evolução...</p>
        </div>
    `;

    try {
        const res = await fetch(`/api/history/${gameId}`);
        const data = await res.json();
        const rawHistory = data.history || [];

        if (!rawHistory.length) {
            container.innerHTML = `
                <div class="overview-card" style="padding: 40px; text-align: center; color: var(--text-secondary); border-left: 4px solid #ec4899;">
                    <i class="fa-solid fa-clock-rotate-left fa-3x" style="color: #ec4899; margin-bottom: 14px;"></i>
                    <h3 style="color: var(--text-primary); font-size: 18px; margin-bottom: 8px;">Nenhum Snapshot de Evolução Registrado</h3>
                    <p style="font-size: 13px; color: var(--text-muted); max-width: 500px; margin: 0 auto 18px auto; line-height: 1.5;">
                        Faça uma sincronização global de conta ou clique no botão acima para registrar a primeira fotografia (snapshot) dos seus personagens e acompanhar a sua progressão ao longo do tempo!
                    </p>
                </div>
            `;
            return;
        }

        const totalSnapshots = rawHistory.length;
        // Inverte para cronológico reverso
        const history = rawHistory.slice().reverse();
        window.historySnapshotsCache = history;

        // Renderiza Barra Superior de Comparativo Customizado
        let compareHeaderHtml = `
            <div class="overview-card history-compare-card" style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(236, 72, 153, 0.35); border-radius: 14px; padding: 16px 20px; margin-bottom: 24px; backdrop-filter: blur(10px);">
                <div class="history-compare-row" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
                    <div class="history-selects-group" style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap; width: 100%;">
                        <span style="font-size: 14px; font-weight: 700; color: #ec4899; display: flex; align-items: center; gap: 6px; white-space: nowrap;">
                            <i class="fa-solid fa-sliders"></i> Seleção de Comparativos:
                        </span>
                        <div class="snap-select-item" style="display: flex; align-items: center; gap: 6px;">
                            <label style="font-size: 12px; color: var(--text-secondary); white-space: nowrap;">Base:</label>
                            <select id="select-snap-base" class="snap-select">
                                ${rawHistory.map((s, i) => `
                                    <option value="${s.id}" ${i === Math.max(0, rawHistory.length - 2) ? 'selected' : ''}>
                                        Snapshot #${i + 1} (${s.created_at})
                                    </option>
                                `).join('')}
                            </select>
                        </div>
                        <span style="color: var(--text-muted);" class="snap-arrow-icon">➔</span>
                        <div class="snap-select-item" style="display: flex; align-items: center; gap: 6px;">
                            <label style="font-size: 12px; color: var(--text-secondary); white-space: nowrap;">Comparado:</label>
                            <select id="select-snap-target" class="snap-select">
                                ${rawHistory.map((s, i) => `
                                    <option value="${s.id}" ${i === rawHistory.length - 1 ? 'selected' : ''}>
                                        Snapshot #${i + 1} (${s.created_at}) ${i === rawHistory.length - 1 ? ' (Mais Recente)' : ''}
                                    </option>
                                `).join('')}
                            </select>
                        </div>
                        <button id="btn-run-snap-compare" class="primary-btn history-compare-btn" style="padding: 8px 16px; font-size: 12px; background: linear-gradient(135deg, #ec4899, #8b5cf6); border: none; cursor: pointer; border-radius: 8px; font-weight: 600;">
                            <i class="fa-solid fa-code-compare"></i> Comparar Diffs
                        </button>
                    </div>
                    <div id="snap-compare-status-badge" class="diff-badge-gain history-status-badge" style="font-size: 11px; padding: 4px 10px; white-space: nowrap;">
                        <i class="fa-solid fa-check"></i> Comparando Snapshots Selecionados
                    </div>
                </div>
            </div>
            <div id="custom-compare-results-container"></div>
        `;

        let timelineHtml = `
            <div style="margin-top: 10px; margin-bottom: 14px; font-size: 14px; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-clock-rotate-left" style="color: #38bdf8;"></i> Histórico Completo de Snapshots (${totalSnapshots})
            </div>
            <div class="timeline-stepper" style="position: relative; padding-left: 24px; border-left: 3px solid rgba(236, 72, 153, 0.3); display: flex; flex-direction: column; gap: 28px; margin-left: 10px;">
                ${history.map((item, idx) => {
                    const details = item.details || {};
                    const topBuilt = details.top_built_characters || [];
                    const allChars = details.all_characters || topBuilt;
                    const readiness = details.endgame_readiness_pct || 0.0;
                    const rawDiffs = item.char_diffs || [];
                    const onlyChanged = window.historyOnlyChanged || false;

                    const diffs = onlyChanged 
                        ? rawDiffs.filter(d => d.is_new || d.is_modified || (d.score_diff && d.score_diff !== 0) || (d.diffs && (d.diffs.score_diff !== 0 || d.diffs.level_diff > 0 || d.diffs.rank_changed)))
                        : rawDiffs;

                    const changedCharNames = new Set(rawDiffs.map(d => d.name));
                    const filteredChars = onlyChanged
                        ? allChars.filter(c => changedCharNames.has(c.name) || c.is_new || c.has_changes)
                        : allChars;

                    const isLatest = idx === 0;
                    const snapshotNum = totalSnapshots - idx;

                    return `
                        <div class="timeline-item" style="position: relative;">
                            <div class="timeline-bullet" style="position: absolute; left: -33px; top: 18px; width: 16px; height: 16px; border-radius: 50%; background: ${isLatest ? '#ec4899' : '#38bdf8'}; border: 3px solid #0f172a; box-shadow: 0 0 12px ${isLatest ? 'rgba(236, 72, 153, 0.8)' : 'rgba(56, 189, 248, 0.8)'};"></div>

                            <div class="overview-card timeline-card" style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(255, 255, 255, 0.08); border-top: 3px solid ${isLatest ? '#ec4899' : 'rgba(56, 189, 248, 0.6)'}; border-radius: 14px; padding: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); backdrop-filter: blur(10px);">
                                
                                <div class="timeline-card-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px; border-bottom: 1px solid rgba(255,255,255,0.07); padding-bottom: 16px; margin-bottom: 16px;">
                                    <div>
                                        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                            <span style="font-size: 11px; font-weight: 700; background: ${isLatest ? 'linear-gradient(135deg, #ec4899, #8b5cf6)' : 'rgba(255,255,255,0.1)'}; color: #fff; padding: 3px 10px; border-radius: 12px;">
                                                Snapshot #${snapshotNum} ${isLatest ? ' (Mais Recente)' : ''}
                                            </span>
                                            <span style="font-size: 12px; color: var(--text-muted);"><i class="fa-regular fa-clock"></i> ${item.created_at}</span>
                                        </div>
                                        <h3 style="margin: 8px 0 0 0; color: var(--text-primary); font-size: 17px; font-weight: 700;">
                                            Progresso da Conta <span style="font-size: 13px; color: var(--text-secondary); font-weight: 400;">(UID: ${item.uid})</span>
                                        </h3>
                                    </div>

                                    <div class="timeline-stats-boxes" style="display: flex; gap: 14px; flex-wrap: wrap;">
                                        <div class="timeline-stat-box" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); padding: 8px 14px; border-radius: 10px; text-align: center; flex: 1; min-width: 90px;">
                                            <span style="display: block; font-size: 10px; color: var(--text-secondary); font-weight: 600; text-transform: uppercase;">Personagens</span>
                                            <strong style="font-size: 15px; color: #38bdf8;">${item.character_count}</strong>
                                            <span style="font-size: 10px; color: var(--text-muted); display: block;"> (${details.five_stars || 0}★ 5★ / ${details.four_stars || 0}★ 4★)</span>
                                            ${item.delta_chars > 0 ? `<span style="font-size: 10px; color: #10b981; font-weight: 700; display: block;">+${item.delta_chars} novos</span>` : ''}
                                        </div>
                                        <div class="timeline-stat-box" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); padding: 8px 14px; border-radius: 10px; text-align: center; flex: 1; min-width: 90px;">
                                            <span style="display: block; font-size: 10px; color: var(--text-secondary); font-weight: 600; text-transform: uppercase;">Média Build (RV)</span>
                                            <strong style="font-size: 15px; color: #10b981;">${item.average_build_score}%</strong>
                                            ${item.delta_avg_score > 0 ? `<span style="font-size: 10px; color: #10b981; font-weight: 700; display: block;">+${item.delta_avg_score}%</span>` : (item.delta_avg_score < 0 ? `<span style="font-size: 10px; color: #ef4444; font-weight: 700; display: block;">${item.delta_avg_score}%</span>` : '')}
                                        </div>
                                        <div class="timeline-stat-box" style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.06); padding: 8px 14px; border-radius: 10px; text-align: center; flex: 1; min-width: 90px;">
                                            <span style="display: block; font-size: 10px; color: var(--text-secondary); font-weight: 600; text-transform: uppercase;">Prontidão Endgame</span>
                                            <strong style="font-size: 15px; color: #f59e0b;">${readiness}%</strong>
                                            <span style="font-size: 10px; color: var(--text-muted); display: block;">${details.endgame_ready_count || 0} prontos</span>
                                        </div>
                                    </div>
                                </div>

                                ${diffs.length > 0 ? `
                                    <div style="background: rgba(236, 72, 153, 0.05); border: 1px solid rgba(236, 72, 153, 0.2); border-radius: 12px; padding: 14px; margin-bottom: 16px;">
                                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;">
                                            <span style="font-size: 13px; font-weight: 700; color: #ec4899; display: flex; align-items: center; gap: 6px;">
                                                <i class="fa-solid fa-chart-line"></i> Alterações e Evoluções Detectadas (${diffs.length})
                                            </span>
                                            <span style="font-size: 11px; color: var(--text-muted);">Clique no card para expandir a build completa</span>
                                        </div>

                                        <div class="timeline-diff-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 240px), 1fr)); gap: 12px;">
                                            ${diffs.map((d, dIdx) => {
                                                const dJson = JSON.stringify(d).replace(/"/g, '&quot;');
                                                return `
                                                    <div onclick="window.openCharacterDiffModal(JSON.parse(this.dataset.cdiff))" data-cdiff="${dJson}" class="diff-card-clickable" style="background: rgba(15, 23, 42, 0.9); border: 1px solid ${d.is_new ? 'rgba(245, 158, 11, 0.5)' : 'rgba(255, 255, 255, 0.1)'}; border-radius: 10px; padding: 12px; display: flex; gap: 12px; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                                                        <div style="position: relative; flex-shrink: 0;">
                                                            <img src="${d.icon || '/assets/logo.svg'}" style="width: 46px; height: 46px; border-radius: 50%; object-fit: cover; border: 2px solid ${d.is_new ? '#f59e0b' : '#38bdf8'}; box-shadow: 0 0 10px ${d.is_new ? 'rgba(245, 158, 11, 0.4)' : 'rgba(56, 189, 248, 0.3)'};" onerror="this.src='/assets/logo.svg'">
                                                            ${d.is_new ? `<span style="position: absolute; bottom: -4px; right: -4px; background: #f59e0b; color: #000; font-size: 9px; font-weight: 900; padding: 1px 5px; border-radius: 6px;">NEW</span>` : ''}
                                                        </div>

                                                        <div style="flex: 1; min-width: 0;">
                                                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                                                <strong style="display: block; font-size: 13px; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${d.name}</strong>
                                                            </div>

                                                            <div style="display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-secondary); margin-top: 2px;">
                                                                <span>Nv. ${d.level_curr || d.level_prev || '?'}</span>
                                                                <span>•</span>
                                                                <span style="color: #f59e0b; font-weight: 600;">${d.rank_curr || 'E0/C0'}</span>
                                                            </div>

                                                            <div style="margin-top: 4px; display: flex; align-items: center; gap: 6px;">
                                                                ${d.is_new ? `
                                                                    <span style="font-size: 10px; font-weight: 700; background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(16, 185, 129, 0.4);">
                                                                        Score: ${d.score_curr}% (${d.grade_curr})
                                                                    </span>
                                                                ` : `
                                                                    ${d.score_diff > 0 ? `
                                                                        <span style="font-size: 10px; font-weight: 700; background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(16, 185, 129, 0.4);">
                                                                            Score +${d.score_diff}% ➔ ${d.score_curr}%
                                                                        </span>
                                                                    ` : `
                                                                        <span style="font-size: 10px; font-weight: 600; color: var(--text-muted);">
                                                                            Score: ${d.score_curr}% (${d.grade_curr})
                                                                        </span>
                                                                    `}
                                                                `}
                                                            </div>
                                                        </div>
                                                    </div>
                                                `;
                                            }).join('')}
                                        </div>
                                    </div>
                                ` : (idx > 0 ? `<p style="font-size: 12px; color: var(--text-muted); font-style: italic; margin-bottom: 12px;"><i class="fa-solid fa-check-circle" style="color: #10b981;"></i> Nenhuma alteração de atributos ou novos personagens detectados em relação ao snapshot anterior.</p>` : '')}

                                <details style="background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 10px 14px;">
                                    <summary style="font-size: 12px; font-weight: 600; color: #38bdf8; cursor: pointer; user-select: none; display: flex; align-items: center; gap: 6px;">
                                        <i class="fa-solid fa-users"></i> ${onlyChanged ? `Ver ${filteredChars.length} Personagem(ns) Alterado(s)` : `Ver Todos os ${allChars.length} Personagens`} do Snapshot #${snapshotNum}
                                    </summary>
                                    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 150px), 1fr)); gap: 10px; margin-top: 14px;">
                                        ${filteredChars.map(c => `
                                            <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 8px 10px; display: flex; align-items: center; gap: 10px;">
                                                <img src="${c.icon || '/assets/logo.svg'}" style="width: 34px; height: 34px; border-radius: 50%; object-fit: cover; border: 2px solid ${c.rarity >= 5 ? '#f59e0b' : '#a855f7'};" onerror="this.src='/assets/logo.svg'">
                                                <div style="overflow: hidden; flex: 1; min-width: 0;">
                                                    <strong style="display: block; font-size: 12px; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${c.name}</strong>
                                                    <div style="display: flex; justify-content: space-between; font-size: 10px; color: var(--text-secondary); margin-top: 2px;">
                                                        <span>Nv. ${c.level} • ${c.rank_str || 'E0/C0'}</span>
                                                        <span style="color: #10b981; font-weight: 700;">${c.score || 0}% (${c.grade || 'D'})</span>
                                                    </div>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </details>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        container.innerHTML = compareHeaderHtml + timelineHtml;

        // Função interna para executar comparativo customizado entre quaisquer dois snapshots
        const runCustomCompare = async () => {
            const selBase = document.getElementById("select-snap-base");
            const selTarget = document.getElementById("select-snap-target");
            const resContainer = document.getElementById("custom-compare-results-container");

            if (!selBase || !selTarget || !resContainer) return;

            const idA = selBase.value;
            const idB = selTarget.value;

            if (idA === idB) {
                resContainer.innerHTML = `<div style="padding: 14px; border-radius: 10px; background: rgba(245,158,11,0.1); border: 1px solid #f59e0b; color: #f59e0b; font-size: 13px; margin-bottom: 20px;"><i class="fa-solid fa-triangle-exclamation"></i> Selecione dois snapshots diferentes para visualizar as diferenças.</div>`;
                return;
            }

            resContainer.innerHTML = `<div style="padding: 20px; text-align: center; color: var(--text-secondary);"><i class="fa-solid fa-spinner fa-spin"></i> Calculando diff minuciosa dos snapshots...</div>`;

            try {
                const cRes = await fetch(`/api/history/${gameId}/compare/${idA}/${idB}`);
                const cData = await cRes.json();
                const sumDiff = cData.summary_diff || {};
                const rawCDiffs = cData.char_diffs || [];
                const cDiffs = window.historyOnlyChanged
                    ? rawCDiffs.filter(d => d.is_new || d.is_modified || (d.diffs && (d.diffs.score_diff !== 0 || d.diffs.level_diff > 0 || d.diffs.rank_changed)))
                    : rawCDiffs;

                let resHtml = `
                    <div style="background: rgba(236, 72, 153, 0.08); border: 1px solid rgba(236, 72, 153, 0.3); border-radius: 14px; padding: 18px; margin-bottom: 24px;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 14px;">
                            <h3 style="margin: 0; font-size: 15px; color: #ec4899; display: flex; align-items: center; gap: 8px; word-break: break-word;">
                                <i class="fa-solid fa-code-compare"></i> Resultado da Comparação (Snapshot #${cData.snap_a.id} ➔ Snapshot #${cData.snap_b.id})
                            </h3>
                            <span style="font-size: 11px; color: var(--text-muted); display: block;">${cData.snap_a.created_at} ➔ ${cData.snap_b.created_at}</span>
                        </div>

                        <!-- KPIs Comparativos -->
                        <div class="diff-modal-kpi-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 130px), 1fr)); gap: 10px; margin-bottom: 16px;">
                            <div style="background: rgba(0,0,0,0.3); padding: 10px 6px; border-radius: 8px; text-align: center;">
                                <span style="font-size: 9px; color: var(--text-secondary); text-transform: uppercase; display: block;">Personagens</span>
                                <strong style="display: block; font-size: 13px; color: #38bdf8;">${cData.snap_a.character_count} ➔ ${cData.snap_b.character_count}</strong>
                                ${sumDiff.delta_chars > 0 ? `<span class="diff-badge-gain" style="font-size: 9px;">+${sumDiff.delta_chars} novos</span>` : ''}
                            </div>
                            <div style="background: rgba(0,0,0,0.3); padding: 10px 6px; border-radius: 8px; text-align: center;">
                                <span style="font-size: 9px; color: var(--text-secondary); text-transform: uppercase; display: block;">Score Médio (RV)</span>
                                <strong style="display: block; font-size: 13px; color: #10b981;">${cData.snap_a.average_build_score}% ➔ ${cData.snap_b.average_build_score}%</strong>
                                ${sumDiff.delta_avg_score > 0 ? `<span class="diff-badge-gain" style="font-size: 9px;">+${sumDiff.delta_avg_score}%</span>` : (sumDiff.delta_avg_score < 0 ? `<span class="diff-badge-loss" style="font-size: 9px;">${sumDiff.delta_avg_score}%</span>` : '')}
                            </div>
                            <div style="background: rgba(0,0,0,0.3); padding: 10px 6px; border-radius: 8px; text-align: center;">
                                <span style="font-size: 9px; color: var(--text-secondary); text-transform: uppercase; display: block;">Prontidão Endgame</span>
                                <strong style="display: block; font-size: 13px; color: #f59e0b;">${cData.snap_a.endgame_readiness_pct}% ➔ ${cData.snap_b.endgame_readiness_pct}%</strong>
                                ${sumDiff.delta_readiness > 0 ? `<span class="diff-badge-gain" style="font-size: 9px;">+${sumDiff.delta_readiness}%</span>` : ''}
                            </div>
                        </div>

                        <!-- Lista de Cards de Personagens para Abrir Modal -->
                        <div style="font-size: 13px; font-weight: 700; color: #fff; margin-bottom: 12px; display: flex; flex-direction: column; gap: 4px;">
                            <span><i class="fa-solid fa-users-gear"></i> Todos os Personagens no Período (${cDiffs.length})</span>
                            <span style="font-size: 11px; color: #ec4899; font-weight: 400;">★ Clique em qualquer card para expandir a build completa</span>
                        </div>
                        <div class="timeline-diff-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 240px), 1fr)); gap: 12px;">
                            ${cDiffs.map(d => {
                                const dJson = JSON.stringify(d).replace(/"/g, '&quot;');
                                const scoreD = d.diffs ? d.diffs.score_diff : 0;
                                const lvlD = d.diffs ? d.diffs.level_diff : 0;
                                const rankChg = d.diffs ? d.diffs.rank_changed : false;
                                return `
                                    <div onclick="window.openCharacterDiffModal(JSON.parse(this.dataset.cdiff))" data-cdiff="${dJson}" class="diff-card-clickable" style="background: rgba(15, 23, 42, 0.95); border: 1px solid ${d.is_new ? 'rgba(245, 158, 11, 0.6)' : (d.is_modified ? 'rgba(56, 189, 248, 0.4)' : 'rgba(255,255,255,0.06)')}; border-radius: 10px; padding: 12px; display: flex; gap: 12px; align-items: center;">
                                        <img src="${d.icon || '/assets/logo.svg'}" style="width: 44px; height: 44px; border-radius: 50%; object-fit: cover; border: 2px solid ${d.is_new ? '#f59e0b' : '#38bdf8'};" onerror="this.src='/assets/logo.svg'">
                                        <div style="flex: 1; min-width: 0;">
                                            <strong style="display: block; font-size: 13px; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${d.name}</strong>
                                            <div style="display: flex; gap: 6px; font-size: 11px; color: var(--text-secondary); margin-top: 2px;">
                                                <span>Nv. ${(d.target || d.base || {}).level || '?'}</span>
                                                <span>•</span>
                                                <span style="color: #f59e0b;">${(d.target || d.base || {}).rank_str || 'E0/C0'}</span>
                                            </div>
                                            <div style="margin-top: 4px; display: flex; flex-wrap: wrap; gap: 4px;">
                                                ${d.is_new ? `<span class="diff-badge-gain">Novo!</span>` : ''}
                                                ${scoreD > 0 ? `<span class="diff-badge-gain">+${scoreD}% RV</span>` : ''}
                                                ${rankChg ? `<span class="diff-badge-gain">Constelação+</span>` : ''}
                                                ${!d.is_new && !scoreD && !rankChg ? `<span class="diff-badge-same">Sem alterações</span>` : ''}
                                            </div>
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                `;

                resContainer.innerHTML = resHtml;
            } catch (err) {
                console.error("Erro ao executar comparativo:", err);
                resContainer.innerHTML = `<div style="padding: 14px; color: #ef4444;">Erro ao comparar os snapshots selecionados.</div>`;
            }
        };

        // Vincula evento no botão de comparar
        const btnCompare = document.getElementById("btn-run-snap-compare");
        if (btnCompare) {
            btnCompare.addEventListener("click", runCustomCompare);
        }

        // Executa comparativo inicial com os selecionados por padrão
        runCustomCompare();

    } catch (err) {
        console.error("Erro ao carregar histórico:", err);
        container.innerHTML = `<div style="padding: 20px; text-align: center; color: #ef4444;">Falha ao carregar o histórico de evolução da conta.</div>`;
    }
};

window.loadPromoCodes = async (gameId = "hsr") => {
    const container = document.getElementById("tab-codes-body");
    if (!container) return;
    container.innerHTML = `<div style="padding: 20px; text-align: center; color: var(--text-secondary);"><i class="fa-solid fa-spinner fa-spin fa-2x"></i><p style="margin-top: 10px;">Buscando códigos promocionais ativos...</p></div>`;

    try {
        const res = await fetch(`/api/codes/${gameId}`);
        const data = await res.json();
        const codes = data.codes || [];

        if (!codes.length) {
            container.innerHTML = `<div style="padding: 20px; text-align: center; color: var(--text-secondary);"><p>Nenhum código ativo encontrado para ${gameId.toUpperCase()}.</p></div>`;
            return;
        }

        let html = `
            <div style="display: flex; flex-direction: column; gap: 12px;">
                ${codes.map(c => `
                    <div style="background: rgba(0,0,0,0.25); border: 1px solid var(--border-color); border-radius: 10px; padding: 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <div>
                            <code style="font-size: 16px; font-weight: 700; color: #f59e0b; background: rgba(245, 158, 11, 0.1); padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(245, 158, 11, 0.3);">${c.code}</code>
                            <span style="display: block; font-size: 12px; color: var(--text-secondary); margin-top: 6px;"> Recompensas: ${c.rewards}</span>
                            <span style="display: block; font-size: 10px; color: #10b981; margin-top: 2px;">• ${c.status}</span>
                        </div>
                        <button class="action-btn btn-redeem-single" data-game="${gameId}" data-code="${c.code}" style="padding: 8px 14px; font-size: 12px; background: rgba(245, 158, 11, 0.15); border-color: rgba(245, 158, 11, 0.4); color: #fbbf24; border-radius: 6px; cursor: pointer;">
                            <i class="fa-solid fa-gift"></i> Resgatar Este
                        </button>
                    </div>
                `).join('')}
            </div>
            <div id="codes-redeem-status" style="margin-top: 16px; font-size: 12px;"></div>
        `;
        container.innerHTML = html;

        document.querySelectorAll(".btn-redeem-single").forEach(btn => {
            btn.addEventListener("click", async () => {
                const code = btn.getAttribute("data-code");
                const game = btn.getAttribute("data-game");
                btn.disabled = true;
                btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Resgatando...`;
                try {
                    const r = await fetch("/api/codes/redeem", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ game_id: game, code: code })
                    });
                    const resData = await r.json();
                    const statusBox = document.getElementById("codes-redeem-status");
                    if (resData.results && resData.results.length) {
                        const item = resData.results[0];
                        statusBox.innerHTML = `<div style="padding: 10px; border-radius: 6px; background: rgba(16,185,129,0.1); border: 1px solid #10b981; color: #4ade80;">${item.message}</div>`;
                    }
                } catch (e) {
                    showToast("Erro ao resgatar código.");
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = `<i class="fa-solid fa-gift"></i> Resgatar Este`;
                }
            });
        });

    } catch (err) {
        console.error("Erro ao carregar códigos:", err);
        container.innerHTML = `<div style="padding: 20px; text-align: center; color: #ef4444;">Falha ao carregar códigos promocionais.</div>`;
    }
};

window.loadAppConfiguration = async () => {
    try {
        const res = await fetch("/api/config");
        const data = await res.json();

        const groqKeyInput = document.getElementById("cfg-groq-key");
        if (groqKeyInput && data.groq_api_key) {
            groqKeyInput.value = data.groq_api_key;
        }

        const cookiesInput = document.getElementById("cfg-hoyolab-cookies");
        if (cookiesInput && data.cookies_raw) {
            cookiesInput.value = data.cookies_raw;
        }

        const cbEnabled = document.getElementById("cfg-auto-sync-enabled");
        if (cbEnabled) {
            cbEnabled.checked = data.auto_sync_enabled !== false;
        }

        const inputTime = document.getElementById("cfg-auto-sync-time");
        if (inputTime) {
            inputTime.value = data.auto_sync_time || "04:00";
        }

        const cbRoster = document.getElementById("cfg-auto-sync-roster");
        if (cbRoster) {
            cbRoster.checked = data.auto_sync_roster !== false;
        }

        const cbGuides = document.getElementById("cfg-auto-sync-guides");
        if (cbGuides) {
            cbGuides.checked = data.auto_sync_guides !== false;
        }

        const statusEl = document.getElementById("cfg-auto-sync-status");
        if (statusEl) {
            const lastDate = data.last_auto_sync_date;
            statusEl.innerHTML = `<i class="fa-solid fa-circle-info" style="color: #38bdf8;"></i> Agendado diariamente para o horário <strong>${data.auto_sync_time || "04:00"}</strong>. ${lastDate ? `Última atualização executada em: <strong>${lastDate}</strong>.` : 'Ainda não executado hoje.'}`;
        }
    } catch (err) {
        console.error("Erro ao carregar configurações:", err);
    }
};

window.saveAppConfiguration = async () => {
    const groqKey = document.getElementById("cfg-groq-key")?.value || "";
    const cookiesRaw = document.getElementById("cfg-hoyolab-cookies")?.value || "";
    const autoSyncEnabled = document.getElementById("cfg-auto-sync-enabled")?.checked ?? true;
    const autoSyncTime = document.getElementById("cfg-auto-sync-time")?.value || "04:00";
    const autoSyncRoster = document.getElementById("cfg-auto-sync-roster")?.checked ?? true;
    const autoSyncGuides = document.getElementById("cfg-auto-sync-guides")?.checked ?? true;

    try {
        const res = await fetch("/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                groq_api_key: groqKey,
                cookies_raw: cookiesRaw,
                auto_sync_enabled: autoSyncEnabled,
                auto_sync_time: autoSyncTime,
                auto_sync_roster: autoSyncRoster,
                auto_sync_guides: autoSyncGuides
            })
        });
        const data = await res.json();
        showToast("Configurações atualizadas!", "success");
    } catch (e) {
        showToast("Erro ao salvar configurações.");
    }
};

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
});

// ==========================================
// SIMULADOR DE GACHA ULTRA PREMIUM LOGIC
// ==========================================

window.GACHA_TERMS = {
    genshin: {
        gameName: "Genshin Impact",
        term: "Constelação",
        termPlural: "Constelações",
        prefix: "C",
        currency: "Gemas",
        gemCostPerPull: 160,
        unownedLabel: "Não possui (0 cópias)",
        ranks: [
            { val: 0, label: "C0 (Personagem Base)" },
            { val: 1, label: "C1 (1ª Constelação)" },
            { val: 2, label: "C2 (2ª Constelação)" },
            { val: 3, label: "C3 (3ª Constelação)" },
            { val: 4, label: "C4 (4ª Constelação)" },
            { val: 5, label: "C5 (5ª Constelação)" },
            { val: 6, label: "C6 (Constelação Máxima)" }
        ]
    },
    hsr: {
        gameName: "Honkai: Star Rail",
        term: "Eidolon",
        termPlural: "Eidolons",
        prefix: "E",
        currency: "Jades",
        gemCostPerPull: 160,
        unownedLabel: "Não possui (0 cópias)",
        ranks: [
            { val: 0, label: "E0 (Personagem Base)" },
            { val: 1, label: "E1 (1º Eidolon)" },
            { val: 2, label: "E2 (2º Eidolon)" },
            { val: 3, label: "E3 (3º Eidolon)" },
            { val: 4, label: "E4 (4º Eidolon)" },
            { val: 5, label: "E5 (5º Eidolon)" },
            { val: 6, label: "E6 (Eidolon Máximo)" }
        ]
    },
    zzz: {
        gameName: "Zenless Zone Zero",
        term: "Mindscape Cinema",
        termPlural: "Mindscapes",
        prefix: "M",
        currency: "Policromos",
        gemCostPerPull: 160,
        unownedLabel: "Não possui (0 cópias)",
        ranks: [
            { val: 0, label: "M0 (Agente Base)" },
            { val: 1, label: "M1 (1º Cinema)" },
            { val: 2, label: "M2 (2º Cinema)" },
            { val: 3, label: "M3 (3º Cinema)" },
            { val: 4, label: "M4 (4º Cinema)" },
            { val: 5, label: "M5 (5º Cinema)" },
            { val: 6, label: "M6 (Mindscape Máximo)" }
        ]
    }
};

window.gachaState = {
    gameId: "genshin",
    charList: [],
    selectedChar: null
};

window.addGachaPulls = function(amount) {
    const pullInput = document.getElementById("tab-gacha-pulls");
    if (!pullInput) return;
    const current = parseInt(pullInput.value) || 0;
    pullInput.value = current + amount;
    window.updateGachaGemConversion();
};

window.updateGachaGemConversion = function() {
    const gameId = document.getElementById("tab-gacha-game-select")?.value || "genshin";
    const terms = window.GACHA_TERMS[gameId] || window.GACHA_TERMS.genshin;
    const pulls = parseInt(document.getElementById("tab-gacha-pulls")?.value) || 0;
    const gems = pulls * terms.gemCostPerPull;
    const convertLbl = document.getElementById("gacha-gems-convert-lbl");
    if (convertLbl) {
        convertLbl.innerText = `(Equivale a ${gems.toLocaleString()} ${terms.currency})`;
    }
};

window.initGachaSimulator = async function() {
    const gamePills = document.querySelectorAll("#gacha-game-pills .gacha-game-pill");
    const gameSelectHidden = document.getElementById("tab-gacha-game-select");
    const charSelect = document.getElementById("tab-gacha-char-select");
    const currentRankSelect = document.getElementById("tab-gacha-current-rank");
    const pullsInput = document.getElementById("tab-gacha-pulls");
    const runBtn = document.getElementById("tab-btn-run-gacha-sim");

    if (pullsInput) {
        pullsInput.addEventListener("input", window.updateGachaGemConversion);
    }

    gamePills.forEach(pill => {
        pill.addEventListener("click", async () => {
            gamePills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            const gameId = pill.dataset.game;
            if (gameSelectHidden) gameSelectHidden.value = gameId;
            window.gachaState.gameId = gameId;
            window.updateGachaLabels(gameId);
            await window.loadGachaCharacters(gameId);
            window.updateGachaGemConversion();
        });
    });

    if (charSelect) {
        charSelect.addEventListener("change", () => {
            const charName = charSelect.value;
            window.updateGachaCharPreview(charName);
        });
    }

    if (currentRankSelect) {
        currentRankSelect.addEventListener("change", () => {
            window.updateTargetRankOptions();
        });
    }

    if (runBtn) {
        runBtn.onclick = window.runGachaSimulation;
    }

    const wishBtn = document.getElementById("tab-btn-open-wish-anim");
    if (wishBtn) {
        wishBtn.onclick = (e) => {
            if (e) e.preventDefault();
            window.startWishAnimation(1);
        };
    }

    window.updateGachaLabels("genshin");
    await window.loadGachaCharacters("genshin");
    window.updateGachaGemConversion();
};

window.updateGachaLabels = function(gameId) {
    const terms = window.GACHA_TERMS[gameId] || window.GACHA_TERMS.genshin;
    
    const lblCurrent = document.getElementById("lbl-gacha-current-rank");
    const lblTarget = document.getElementById("lbl-gacha-target-rank");
    if (lblCurrent) lblCurrent.innerText = `${terms.term} Atual:`;
    if (lblTarget) lblTarget.innerText = `Meta de ${terms.term}:`;

    const currentRankSelect = document.getElementById("tab-gacha-current-rank");
    if (currentRankSelect) {
        currentRankSelect.innerHTML = `<option value="-1">${terms.unownedLabel}</option>`;
        terms.ranks.forEach(r => {
            const opt = document.createElement("option");
            opt.value = r.val;
            opt.innerText = r.label;
            currentRankSelect.appendChild(opt);
        });
    }

    window.updateTargetRankOptions();
};

window.updateTargetRankOptions = function() {
    const gameId = document.getElementById("tab-gacha-game-select")?.value || "genshin";
    const terms = window.GACHA_TERMS[gameId] || window.GACHA_TERMS.genshin;
    const currentRank = parseInt(document.getElementById("tab-gacha-current-rank")?.value ?? -1);
    const targetRankSelect = document.getElementById("tab-gacha-target-rank");

    if (!targetRankSelect) return;
    const prevTargetVal = parseInt(targetRankSelect.value ?? 6);

    targetRankSelect.innerHTML = "";
    terms.ranks.forEach(r => {
        if (r.val > currentRank || (currentRank === -1 && r.val >= 0)) {
            const opt = document.createElement("option");
            opt.value = r.val;
            
            let extraStr = "";
            if (currentRank < 0) {
                extraStr = r.val === 0 ? " (Garantir 1º Personagem)" : ` (+${r.val + 1} cópias)`;
            } else {
                const needed = r.val - currentRank;
                extraStr = needed === 1 ? " (+1 cópia adicional)" : ` (+${needed} cópias adicionais)`;
            }
            opt.innerText = `${terms.prefix}${r.val}${extraStr}`;
            targetRankSelect.appendChild(opt);
        }
    });

    if (prevTargetVal > currentRank) {
        targetRankSelect.value = prevTargetVal;
    } else {
        const lastOpt = targetRankSelect.options[targetRankSelect.options.length - 1];
        if (lastOpt) targetRankSelect.value = lastOpt.value;
    }
};

window.loadGachaCharacters = async function(gameId) {
    const charSelect = document.getElementById("tab-gacha-char-select");
    if (!charSelect) return;

    charSelect.innerHTML = `<option value="">Carregando lista de personagens 5★...</option>`;

    try {
        const res = await fetch(`/api/gacha/characters/${gameId}`);
        const data = await res.json();
        const chars = data.characters || [];
        window.gachaState.charList = chars;

        charSelect.innerHTML = "";

        const genericOpt = document.createElement("option");
        genericOpt.value = "";
        genericOpt.innerText = "✨ Personagem 5★ Genérico / Qualquer Banner";
        charSelect.appendChild(genericOpt);

        const ownedChars = chars.filter(c => c.owned);
        const unownedChars = chars.filter(c => !c.owned);

        if (ownedChars.length > 0) {
            const grpOwned = document.createElement("optgroup");
            grpOwned.label = "🟢 Seus Personagens 5★ (no Roster)";
            ownedChars.forEach(c => {
                const opt = document.createElement("option");
                opt.value = c.name;
                opt.innerText = `✓ ${c.name} (Nv. ${c.level} • ${c.rank_str || 'C0'})`;
                grpOwned.appendChild(opt);
            });
            charSelect.appendChild(grpOwned);
        }

        if (unownedChars.length > 0) {
            const grpUnowned = document.createElement("optgroup");
            grpUnowned.label = "⚪ Outros Personagens 5★ do Jogo";
            unownedChars.forEach(c => {
                const opt = document.createElement("option");
                opt.value = c.name;
                opt.innerText = `${c.name} (Não Obtido)`;
                grpUnowned.appendChild(opt);
            });
            charSelect.appendChild(grpUnowned);
        }

        if (ownedChars.length > 0) {
            charSelect.value = ownedChars[0].name;
            window.updateGachaCharPreview(ownedChars[0].name);
        } else {
            charSelect.value = "";
            window.updateGachaCharPreview("");
        }

    } catch (e) {
        console.error("Erro ao carregar lista de personagens gacha:", e);
        charSelect.innerHTML = `<option value="">Erro ao carregar personagens</option>`;
    }
};

window.updateGachaCharPreview = function(charName) {
    const gameId = document.getElementById("tab-gacha-game-select")?.value || "genshin";
    const terms = window.GACHA_TERMS[gameId] || window.GACHA_TERMS.genshin;
    const chars = window.gachaState.charList || [];
    const char = chars.find(c => c.name === charName);

    const nameLbl = document.getElementById("gacha-hero-name");
    const starsLbl = document.getElementById("gacha-hero-stars");
    const badgeEl = document.getElementById("gacha-hero-badge");
    const bgEl = document.getElementById("gacha-hero-bg");
    const avatarImg = document.getElementById("gacha-hero-avatar-img");
    const avatarFallback = document.getElementById("gacha-hero-avatar-fallback");
    const currentRankSelect = document.getElementById("tab-gacha-current-rank");

    if (!char) {
        if (nameLbl) nameLbl.innerText = "Personagem 5★ Genérico";
        if (starsLbl) starsLbl.innerText = "★★★★★";
        if (badgeEl) {
            badgeEl.className = "gacha-char-badge-unowned";
            badgeEl.innerHTML = `<i class="fa-solid fa-circle-plus"></i> Não possui (0 cópias)`;
        }
        if (bgEl) bgEl.style.backgroundImage = "none";
        if (avatarImg) avatarImg.style.display = "none";
        if (avatarFallback) avatarFallback.style.display = "flex";
        if (currentRankSelect) currentRankSelect.value = "-1";
        window.updateTargetRankOptions();
        return;
    }

    if (nameLbl) nameLbl.innerText = char.name;
    if (starsLbl) starsLbl.innerText = "★".repeat(char.rarity || 5);

    const splash = char.gacha_art || char.icon || "";
    const avatar = char.icon || char.gacha_art || "";

    if (bgEl && splash) {
        bgEl.style.backgroundImage = `url('${splash}')`;
    } else if (bgEl) {
        bgEl.style.backgroundImage = "none";
    }

    if (avatarImg && avatar) {
        avatarImg.onerror = () => {
            avatarImg.style.display = "none";
            if (avatarFallback) avatarFallback.style.display = "flex";
        };
        avatarImg.src = avatar;
        avatarImg.style.display = "block";
        if (avatarFallback) avatarFallback.style.display = "none";
    } else {
        if (avatarImg) avatarImg.style.display = "none";
        if (avatarFallback) avatarFallback.style.display = "flex";
    }

    if (char.owned) {
        const rankNum = char.current_rank >= 0 ? char.current_rank : 0;
        const rankStr = char.rank_str || `${terms.prefix}${rankNum}`;
        if (badgeEl) {
            badgeEl.className = "gacha-char-badge-owned";
            badgeEl.innerHTML = `<i class="fa-solid fa-circle-check"></i> No seu Roster: ${rankStr} (Nível ${char.level})`;
        }
        if (currentRankSelect) currentRankSelect.value = String(rankNum);
    } else {
        if (badgeEl) {
            badgeEl.className = "gacha-char-badge-unowned";
            badgeEl.innerHTML = `<i class="fa-solid fa-circle-plus"></i> Não possui (0 cópias)`;
        }
        if (currentRankSelect) currentRankSelect.value = "-1";
    }

    window.updateTargetRankOptions();
};

window.runGachaSimulation = async function() {
    const gameId = document.getElementById("tab-gacha-game-select")?.value || "genshin";
    const charSelect = document.getElementById("tab-gacha-char-select");
    const charName = charSelect ? charSelect.value : "";
    const currentRank = parseInt(document.getElementById("tab-gacha-current-rank")?.value ?? -1);
    const targetRank = parseInt(document.getElementById("tab-gacha-target-rank")?.value ?? 6);
    const currentPity = parseInt(document.getElementById("tab-gacha-pity")?.value) || 0;
    const isGuaranteed = document.getElementById("tab-gacha-guaranteed")?.value === "true";
    const pullsAvailable = parseInt(document.getElementById("tab-gacha-pulls")?.value) || 0;

    const runBtn = document.getElementById("tab-btn-run-gacha-sim");
    if (runBtn) {
        runBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Simulando 10.000 iterações...`;
        runBtn.disabled = true;
    }

    try {
        const res = await fetch("/api/gacha/calculate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                game_id: gameId,
                current_pity: currentPity,
                is_guaranteed: isGuaranteed,
                pulls_available: pullsAvailable,
                current_rank: currentRank,
                target_rank: targetRank,
                char_name: charName
            })
        });
        const data = await res.json();
        
        const resultsBox = document.getElementById("tab-gacha-results-box");
        if (resultsBox) resultsBox.style.display = "block";

        const chanceLbl = document.getElementById("tab-gacha-chance-lbl");
        if (chanceLbl) {
            chanceLbl.innerText = `${data.success_rate}%`;
            chanceLbl.className = "gacha-gauge-val " + (
                data.success_rate >= 80 ? "success-high" :
                (data.success_rate >= 50 ? "success-med" : "success-low")
            );
        }

        const summaryEl = document.getElementById("tab-gacha-target-summary");
        const terms = window.GACHA_TERMS[gameId] || window.GACHA_TERMS.genshin;
        const charTitle = charName ? `<b>${charName}</b>` : "Personagem Alvo";
        if (summaryEl) {
            if (data.needed_new_copies === 0) {
                summaryEl.innerHTML = `🎉 Você já possui a meta <b>${data.target_rank_str}</b>!`;
            } else {
                summaryEl.innerHTML = `Probabilidade de evoluir ${charTitle} de <b>${data.current_rank_str}</b> até <b>${data.target_rank_str}</b> (+${data.needed_new_copies} cópias) com <b>${pullsAvailable} tiros</b>.`;
            }
        }

        const avgLbl = document.getElementById("tab-gacha-avg-lbl");
        if (avgLbl) {
            avgLbl.innerText = data.avg_pulls_spent 
                ? `${data.avg_pulls_spent} tiros` 
                : "Tiros insuficientes";
        }

        const gemsSpentLbl = document.getElementById("tab-gacha-gems-spent-lbl");
        if (gemsSpentLbl) {
            if (data.avg_pulls_spent) {
                const gemsAvg = Math.round(data.avg_pulls_spent * terms.gemCostPerPull);
                gemsSpentLbl.innerText = `~${gemsAvg.toLocaleString()} ${terms.currency}`;
            } else {
                gemsSpentLbl.innerText = "N/A";
            }
        }

        const distList = document.getElementById("tab-gacha-dist-list");
        if (distList) {
            distList.innerHTML = "";
            for (const [k, v] of Object.entries(data.distribution || {})) {
                const item = document.createElement("div");
                item.className = "gacha-dist-item";
                
                const isGoal = k.includes("Meta") || k.includes("Batida") || k.includes("alcançada");
                
                item.innerHTML = `
                    <div class="gacha-dist-header">
                        <span>${k}</span>
                        <strong style="color: ${isGoal ? '#34d399' : '#fbbf24'};">${v}%</strong>
                    </div>
                    <div class="gacha-dist-bar-track">
                        <div class="gacha-dist-bar-fill ${isGoal ? 'target-reached' : ''}" style="width: ${v}%;"></div>
                    </div>
                `;
                distList.appendChild(item);
            }
        }
    } catch (err) {
        console.error(err);
        if (typeof showToast === "function") showToast("Erro ao executar simulação de Gacha.");
    } finally {
        if (runBtn) {
            runBtn.innerHTML = `<i class="fa-solid fa-play"></i> Executar Simulação Monte Carlo (10.000 Tiros)`;
            runBtn.disabled = false;
        }
    }
};

// ==========================================================================
// CONTROLADOR DO ÍNDICE DE SORTE & EFICIÊNCIA DE ROLAGENS (LUCK DASHBOARD)
// ==========================================================================
window.initLuckDashboard = function() {
    const btns = document.querySelectorAll(".tab-luck-game-btn");
    btns.forEach(btn => {
        btn.onclick = () => {
            btns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const gameId = btn.getAttribute("data-game");
            window.loadLuckDashboard(gameId);
        };
    });

    const activeBtn = document.querySelector(".tab-luck-game-btn.active");
    const gameId = activeBtn ? activeBtn.getAttribute("data-game") : "genshin";
    window.loadLuckDashboard(gameId);
};

window.loadLuckDashboard = async function(gameId) {
    const bodyEl = document.getElementById("tab-luck-body");
    if (!bodyEl) return;

    bodyEl.innerHTML = `
        <div style="text-align: center; padding: 60px 20px;">
            <i class="fa-solid fa-spinner fa-spin" style="font-size: 32px; color: #10b981; margin-bottom: 16px;"></i>
            <p style="color: #94a3b8; font-size: 15px;">Analisando qualidade das rolagens das relíquias do ${gameId.toUpperCase()}...</p>
        </div>
    `;

    try {
        const res = await fetch(`/api/luck-index/${gameId}`);
        const data = await res.json();
        window.renderLuckDashboard(data);
    } catch (e) {
        console.error("Erro ao carregar dashboard de sorte:", e);
        bodyEl.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #ef4444;">
                <i class="fa-solid fa-triangle-exclamation" style="font-size: 32px; margin-bottom: 12px;"></i>
                <p>Erro ao carregar dados do Índice de Sorte.</p>
            </div>
        `;
    }
};

function renderSubstatsPillList(substatsAnalyzed, rawFallbackStr) {
    if (substatsAnalyzed && substatsAnalyzed.length > 0) {
        return `
            <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;">
                ${substatsAnalyzed.map(sub => `
                    <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid ${sub.status_color}55; border-radius: 8px; padding: 4px 8px; font-size: 11px; display: inline-flex; align-items: center; gap: 6px;">
                        <span style="color: #f8fafc; font-weight: 600;">${sub.raw_text}</span>
                        <span style="color: ${sub.status_color}; font-weight: 700; background: ${sub.status_color}22; padding: 2px 6px; border-radius: 4px; font-size: 10px; border: 1px solid ${sub.status_color}44;">
                            ${sub.status_badge}
                        </span>
                    </div>
                `).join('')}
            </div>
        `;
    }
    return `<div style="font-size: 11px; color: #cbd5e1; margin-top: 4px;">${rawFallbackStr}</div>`;
}

window.renderLuckDashboard = function(data) {
    const bodyEl = document.getElementById("tab-luck-body");
    if (!bodyEl) return;

    if (!data || data.total_relics_analyzed === 0) {
        bodyEl.innerHTML = `
            <div style="text-align: center; padding: 60px 20px;" class="overview-card">
                <i class="fa-solid fa-shield-halved" style="font-size: 40px; color: #64748b; margin-bottom: 16px;"></i>
                <h3 style="color: #f8fafc; margin-bottom: 8px;">Nenhuma Relíquia Encontrada</h3>
                <p style="color: #94a3b8; max-width: 500px; margin: 0 auto 20px auto;">
                    Sincronize seu Roster com o HoYoLAB para analisar a sorte e a eficiência das rolagens de atributos dos seus equipamentos.
                </p>
            </div>
        `;
        return;
    }

    const god = data.god_roll;
    const cursed = data.cursed_roll;

    let html = `
        <!-- HERO CARDS (3 COLUNAS) -->
        <div class="luck-hero-grid">
            <!-- CARD 1: SORTE GERAL DA CONTA -->
            <div class="luck-overview-card">
                <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; display: flex; align-items: center; justify-content: space-between;">
                    <span>Pontuação de Sorte da Conta</span>
                    <i class="fa-solid fa-clover" style="color: #10b981;"></i>
                </div>
                <div class="luck-gauge-box">
                    <div class="luck-gauge-value">${data.overall_account_luck}%</div>
                    <div style="font-size: 14px; font-weight: 700; color: #f8fafc; margin-top: 4px;">${data.luck_title}</div>
                    <div style="display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); margin-top: 8px;">
                        ${data.luck_badge}
                    </div>
                </div>
                <div style="font-size: 12px; color: #64748b; text-align: center;">
                    Baseado em ${data.total_relics_analyzed} relíquias equipadas
                </div>
            </div>

            <!-- CARD 2: GOD ROLL DA CONTA -->
            <div class="luck-overview-card god-roll-card">
                <div style="font-size: 12px; color: #fbbf24; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; display: flex; align-items: center; justify-content: space-between;">
                    <span>🏆 A Peça Mais Sortuda (God Roll)</span>
                    <span style="font-size: 11px; background: rgba(245, 158, 11, 0.2); color: #fbbf24; padding: 2px 8px; border-radius: 12px;">Top #1</span>
                </div>
                ${god ? `
                <div style="display: flex; align-items: center; gap: 14px; margin: 12px 0;">
                    <img src="${god.character_icon || '/assets/logo.svg'}" style="width: 54px; height: 54px; border-radius: 50%; border: 2px solid #f59e0b; object-fit: cover; flex-shrink: 0;">
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-size: 16px; font-weight: bold; color: #f8fafc;">${god.character_name}</div>
                        <div style="display: flex; align-items: center; gap: 8px; margin: 6px 0; flex-wrap: wrap;">
                            ${god.relic_icon ? `<img src="${god.relic_icon}" style="width: 32px; height: 32px; object-fit: contain; background: rgba(0,0,0,0.4); border-radius: 6px; border: 1px solid rgba(245, 158, 11, 0.4); padding: 2px;">` : ''}
                            <span style="font-size: 12px; font-weight: 800; color: #fbbf24; background: rgba(245, 158, 11, 0.2); padding: 3px 10px; border-radius: 6px; border: 1px solid rgba(245, 158, 11, 0.4); display: inline-flex; align-items: center; gap: 4px;">
                                ${god.slot_display || god.slot}
                            </span>
                            <span style="font-size: 12px; color: #e2e8f0; font-weight: 500;">${god.relic_name}</span>
                        </div>
                        <div style="font-size: 11px; color: #cbd5e1;">Atributo Principal: <strong style="color: #38bdf8;">${god.main_stat}</strong></div>
                    </div>
                </div>
                <div style="background: rgba(0, 0, 0, 0.3); padding: 10px; border-radius: 10px; font-size: 11px; color: #e2e8f0; margin-bottom: 10px;">
                    <div style="font-weight: 700; color: #94a3b8; margin-bottom: 4px;">Avaliação de Substatus & Rolagens:</div>
                    ${renderSubstatsPillList(god.substats_analyzed, god.substats_str)}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 12px; color: #34d399; font-weight: bold;">Sorte: ${god.luck_score}% (${god.luck_badge})</span>
                    <span style="font-size: 11px; color: #94a3b8;">Roll Value (RV): ${god.total_rv}</span>
                </div>
                ` : '<div style="color:#94a3b8;">Nenhuma peça encontrada</div>'}
            </div>

            <!-- CARD 3: CURSED ROLL DA CONTA -->
            <div class="luck-overview-card cursed-roll-card">
                <div style="font-size: 12px; color: #f87171; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; display: flex; align-items: center; justify-content: space-between;">
                    <span>💀 A Peça Mais Amaldiçoada</span>
                    <span style="font-size: 11px; background: rgba(239, 68, 68, 0.2); color: #f87171; padding: 2px 8px; border-radius: 12px;">Cursed</span>
                </div>
                ${cursed ? `
                <div style="display: flex; align-items: center; gap: 14px; margin: 12px 0;">
                    <img src="${cursed.character_icon || '/assets/logo.svg'}" style="width: 54px; height: 54px; border-radius: 50%; border: 2px solid #ef4444; object-fit: cover; flex-shrink: 0;">
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-size: 16px; font-weight: bold; color: #f8fafc;">${cursed.character_name}</div>
                        <div style="display: flex; align-items: center; gap: 8px; margin: 6px 0; flex-wrap: wrap;">
                            ${cursed.relic_icon ? `<img src="${cursed.relic_icon}" style="width: 32px; height: 32px; object-fit: contain; background: rgba(0,0,0,0.4); border-radius: 6px; border: 1px solid rgba(239, 68, 68, 0.4); padding: 2px;">` : ''}
                            <span style="font-size: 12px; font-weight: 800; color: #f87171; background: rgba(239, 68, 68, 0.2); padding: 3px 10px; border-radius: 6px; border: 1px solid rgba(239, 68, 68, 0.4); display: inline-flex; align-items: center; gap: 4px;">
                                ${cursed.slot_display || cursed.slot}
                            </span>
                            <span style="font-size: 12px; color: #e2e8f0; font-weight: 500;">${cursed.relic_name}</span>
                        </div>
                        <div style="font-size: 11px; color: #cbd5e1;">Atributo Principal: <strong style="color: #f87171;">${cursed.main_stat}</strong></div>
                    </div>
                </div>
                <div style="background: rgba(0, 0, 0, 0.3); padding: 10px; border-radius: 10px; font-size: 11px; color: #e2e8f0; margin-bottom: 10px;">
                    <div style="font-weight: 700; color: #94a3b8; margin-bottom: 4px;">Avaliação de Substatus & Rolagens:</div>
                    ${renderSubstatsPillList(cursed.substats_analyzed, cursed.substats_str)}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 12px; color: #ef4444; font-weight: bold;">Sorte: ${cursed.luck_score}% (${cursed.luck_badge})</span>
                    <span style="font-size: 11px; color: #94a3b8;">Roll Value (RV): ${cursed.total_rv}</span>
                </div>
                ` : '<div style="color:#94a3b8;">Nenhuma peça encontrada</div>'}
            </div>
        </div>

        <!-- PERSONAGENS MAIS SORTUDOS E MENOS SORTUDOS -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px;">
            ${data.luckiest_character ? `
            <div class="overview-card" style="border-left: 4px solid #10b981; margin:0;">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <img src="${data.luckiest_character.character_icon || '/assets/logo.svg'}" style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid #10b981; object-fit: cover;">
                    <div style="flex: 1;">
                        <div style="font-size: 11px; color: #34d399; font-weight: 700; text-transform: uppercase;">🌟 Personagem Mais Sortudo</div>
                        <div style="font-size: 16px; font-weight: bold; color: #fff;">${data.luckiest_character.character_name}</div>
                        <div style="font-size: 12px; color: #94a3b8;">Média de Sorte: <strong style="color: #34d399;">${data.luckiest_character.avg_luck}%</strong> (${data.luckiest_character.relic_count} relíquias)</div>
                    </div>
                </div>
            </div>
            ` : ''}

            ${data.cursed_character ? `
            <div class="overview-card" style="border-left: 4px solid #ef4444; margin:0;">
                <div style="display: flex; align-items: center; gap: 14px;">
                    <img src="${data.cursed_character.character_icon || '/assets/logo.svg'}" style="width: 48px; height: 48px; border-radius: 50%; border: 2px solid #ef4444; object-fit: cover;">
                    <div style="flex: 1;">
                        <div style="font-size: 11px; color: #f87171; font-weight: 700; text-transform: uppercase;">🌧️ Personagem Mais Azarado</div>
                        <div style="font-size: 16px; font-weight: bold; color: #fff;">${data.cursed_character.character_name}</div>
                        <div style="font-size: 12px; color: #94a3b8;">Média de Sorte: <strong style="color: #f87171;">${data.cursed_character.avg_luck}%</strong> (${data.cursed_character.relic_count} relíquias)</div>
                    </div>
                </div>
            </div>
            ` : ''}
        </div>

        <!-- LISTA DE SORTE POR PERSONAGEM -->
        <div class="overview-card" style="margin-bottom: 24px;">
            <h3 style="margin: 0 0 16px 0; font-size: 16px; color: #f8fafc; display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-users-gear" style="color: #10b981;"></i> Ranking de Sorte dos Personagens do Roster
            </h3>
            <div style="display: flex; flex-direction: column; gap: 8px;">
                ${(data.character_breakdown || []).map(c => {
                    const luckClass = c.avg_luck >= 75 ? 'high' : (c.avg_luck >= 50 ? 'mid' : 'low');
                    const color = c.avg_luck >= 75 ? '#34d399' : (c.avg_luck >= 50 ? '#fbbf24' : '#f87171');
                    return `
                    <div class="luck-char-row">
                        <img src="${c.character_icon || '/assets/logo.svg'}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid ${color};">
                        <div style="flex: 1;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                                <span style="font-weight: 600; color: #f8fafc; font-size: 14px;">${c.character_name} <small style="color: #94a3b8; font-weight: normal;">(Nv. ${c.level} • ${c.rank_str})</small></span>
                                <strong style="color: ${color}; font-size: 14px;">${c.avg_luck}%</strong>
                            </div>
                            <div class="luck-bar-bg">
                                <div class="luck-bar-fill ${luckClass}" style="width: ${c.avg_luck}%;"></div>
                            </div>
                        </div>
                    </div>
                    `;
                }).join('')}
            </div>
        </div>

        <!-- TABELA DAS MELHORES RELÍQUIAS DO INVENTÁRIO -->
        <div class="overview-card">
            <h3 style="margin: 0 0 16px 0; font-size: 16px; color: #f8fafc; display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-gem" style="color: #fbbf24;"></i> Top Relíquias mais Sortudas do Inventário (Roll Value)
            </h3>
            <div style="display: flex; flex-direction: column; gap: 10px;">
                ${(data.all_relics || []).map((r, idx) => `
                <div style="display: flex; align-items: center; gap: 14px; padding: 12px 14px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px;">
                    <div style="font-weight: 900; font-size: 16px; color: ${idx < 3 ? '#fbbf24' : '#64748b'}; width: 28px; text-align: center;">#${idx + 1}</div>
                    <img src="${r.character_icon || '/assets/logo.svg'}" style="width: 42px; height: 42px; border-radius: 50%; object-fit: cover; flex-shrink: 0;">
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-size: 13px; font-weight: bold; color: #f8fafc; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                            ${r.relic_icon ? `<img src="${r.relic_icon}" style="width: 28px; height: 28px; object-fit: contain; background: rgba(0,0,0,0.4); border-radius: 6px; border: 1px solid rgba(245, 158, 11, 0.3); padding: 2px;">` : ''}
                            <span style="color: #fbbf24; font-size: 11px; font-weight: 700; background: rgba(245, 158, 11, 0.15); padding: 2px 8px; border-radius: 6px; border: 1px solid rgba(245, 158, 11, 0.3);">
                                ${r.slot_display || r.slot}
                            </span>
                            <span>${r.relic_name}</span>
                            <span style="font-weight: normal; color: #94a3b8;">(${r.character_name})</span>
                        </div>
                        ${renderSubstatsPillList(r.substats_analyzed, r.substats_str)}
                    </div>
                    <div style="text-align: right; flex-shrink: 0;">
                        <div style="font-size: 15px; font-weight: bold; color: ${r.luck_score >= 75 ? '#34d399' : '#fbbf24'};">${r.luck_score}%</div>
                        <div style="font-size: 10px; color: #94a3b8;">${r.luck_badge}</div>
                    </div>
                </div>
                `).join('')}
            </div>
        </div>
    `;

    bodyEl.innerHTML = html;
};

// ==========================================================================
// MOTOR DE ANIMAÇÃO INTERATIVA E SINTETIZADOR DE WISH / GACHA
// ==========================================================================

let wishAudioCtx = null;
let wishAnimId = null;
let wishAnimRunning = false;
let wishAnimTimeout = null;

// 1. Sintetizador de Áudio da Web Audio API
function playWishSound(type, rarity) {
    try {
        if (!wishAudioCtx) {
            wishAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (wishAudioCtx.state === 'suspended') {
            wishAudioCtx.resume();
        }

        const now = wishAudioCtx.currentTime;
        if (type === 'launch') {
            const osc = wishAudioCtx.createOscillator();
            const gain = wishAudioCtx.createGain();
            osc.connect(gain);
            gain.connect(wishAudioCtx.destination);
            osc.type = 'sine';
            osc.frequency.setValueAtTime(150, now);
            osc.frequency.exponentialRampToValueAtTime(800, now + 1.2);
            gain.gain.setValueAtTime(0.05, now);
            gain.gain.linearRampToValueAtTime(0.2, now + 0.8);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 1.5);
            osc.start(now);
            osc.stop(now + 1.5);
        } else if (type === 'reveal') {
            const freqMap = {
                5: [523.25, 659.25, 783.99, 1046.50],
                4: [440.00, 554.37, 659.25],
                3: [329.63, 392.00]
            };
            const freqs = freqMap[rarity] || freqMap[3];
            
            freqs.forEach((f, idx) => {
                const subOsc = wishAudioCtx.createOscillator();
                const subGain = wishAudioCtx.createGain();
                subOsc.type = rarity === 5 ? 'triangle' : 'sine';
                subOsc.frequency.setValueAtTime(f, now + idx * 0.08);
                subGain.connect(wishAudioCtx.destination);
                subOsc.connect(subGain);

                subGain.gain.setValueAtTime(0.01, now + idx * 0.08);
                subGain.gain.linearRampToValueAtTime(rarity === 5 ? 0.25 : 0.15, now + idx * 0.08 + 0.1);
                subGain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.08 + 1.8);

                subOsc.start(now + idx * 0.08);
                subOsc.stop(now + idx * 0.08 + 1.8);
            });
        }
    } catch (e) {
        console.warn("[Wish Sound] AudioContext não disponível:", e);
    }
}

// Helper para gerar URL de Splash Art / Card do Personagem via Proxy
function getWishCharacterSplash(gameId, charName) {
    if (!charName) return "/assets/logo.svg";
    let clean = charName.replace(/\s*\(.*?\)/g, '').trim();
    
    let slug = clean.toLowerCase()
        .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
        
    const slugFixes = {
        "yumemizuki-mizuki": "mizuki",
        "yumemizukimizuki": "mizuki",
        "mizuki": "mizuki",
        "dan-heng-imbibitor-lunae": "imbibitor-lunae",
        "march-7th": "march-7th",
        "trailblazer": "trailblazer-physical",
        "nekoma": "nekomata",
        "nekomata": "nekomata",
        "soldier-11": "soldier-11",
        "soldier11": "soldier-11",
        "lycaon": "von-lycaon",
        "von-lycaon": "von-lycaon"
    };
    if (slugFixes[slug]) slug = slugFixes[slug];

    if (gameId === "genshin") {
        return `/api/proxy_image?url=${encodeURIComponent('https://cdn.prydwen.gg/images/genshin-impact/characters/' + slug + '_card.webp')}`;
    } else if (gameId === "hsr") {
        return `/api/proxy_image?url=${encodeURIComponent('https://cdn.prydwen.gg/images/star-rail/characters/' + slug + '_card.webp')}`;
    } else if (gameId === "zzz") {
        return `/api/proxy_image?url=${encodeURIComponent('https://cdn.prydwen.gg/images/zenless-zone-zero/characters/' + slug + '_full.webp')}`;
    }
    return "/assets/logo.svg";
}

// 2. Lógica do Sorteio Individual com Soft Pity e 50/50 Real
function rollSingleWishItem(gameId, pity, isGuaranteed, targetCharName) {
    pity = parseInt(pity) || 0;
    pity += 1;

    let base5StarChance = 0.006;
    if (pity >= 74) {
        base5StarChance += (pity - 73) * 0.06;
    }
    base5StarChance = Math.min(1.0, base5StarChance);

    const rand5Star = Math.random();
    if (rand5Star <= base5StarChance) {
        let won5050 = true;
        let cleanTarget = (targetCharName || "Personagem 5★ Limitado").replace(/\s*\(.*?\)/g, '').trim();
        let charName = cleanTarget;

        if (!isGuaranteed && Math.random() > 0.5) {
            won5050 = false;
            const standards = {
                genshin: ["Jean", "Keqing", "Qiqi", "Dehya", "Diluc", "Mona", "Tighnari", "Yumemizuki Mizuki"],
                hsr: ["Himeko", "Welt", "Bronya", "Gepard", "Clara", "Yanqing", "Bailu"],
                zzz: ["Nekomata", "Lycaon", "Soldier 11", "Koleda", "Grace", "Rina"]
            };
            const stdList = standards[gameId] || standards.genshin;
            charName = stdList[Math.floor(Math.random() * stdList.length)];
        } else {
            charName = cleanTarget;
        }

        return {
            rarity: 5,
            name: charName,
            pitySpent: pity,
            won5050: won5050,
            isGuaranteedNext: !won5050,
            newPity: 0,
            splashArt: getWishCharacterSplash(gameId, charName)
        };
    }

    const rand4Star = Math.random();
    if (rand4Star <= 0.051 || pity % 10 === 0) {
        const pool4Star = {
            genshin: [
                "Bennett", "Xingqiu", "Xiangling", "Fischl", "Sucrose", "Noelle", "Barbara", "Razor", 
                "Beidou", "Ningguang", "Chongyun", "Diona", "Xinyan", "Rosaria", "Yanfei", "Sayu", 
                "Kujou Sara", "Thoma", "Gorou", "Yunjin", "Kuki Shinobu", "Heizou", "Collei", "Dori", 
                "Candace", "Layla", "Faruzan", "Yaoyao", "Mika", "Kaveh", "Kirara", "Freminet", 
                "Charlotte", "Chevreuse", "Gaming", "Sethos", "Kachina", "Ororun", "Lanyan"
            ],
            hsr: [
                "March 7th", "Dan Heng", "Arlan", "Asta", "Herta", "Serval", "Natasha", "Pela", 
                "Sampo", "Hook", "Qingque", "Tingyun", "Sushang", "Yukong", "Luka", "Lynx", 
                "Guinaifen", "Hanya", "Xueyi", "Misha", "Gallagher", "Moze"
            ],
            zzz: [
                "Anby", "Billy", "Nicole", "Corin", "Anton", "Ben", "Soukaku", "Seth", "Lucy", "Piper", "Pulchra"
            ]
        };
        const list4 = pool4Star[gameId] || pool4Star.genshin;
        const char4Name = list4[Math.floor(Math.random() * list4.length)];

        return {
            rarity: 4,
            name: char4Name,
            pitySpent: pity,
            won5050: true,
            isGuaranteedNext: isGuaranteed,
            newPity: pity,
            splashArt: getWishCharacterSplash(gameId, char4Name)
        };
    }

    return {
        rarity: 3,
        name: "Arma 3★ (Mochileiro)",
        pitySpent: pity,
        won5050: true,
        isGuaranteedNext: isGuaranteed,
        newPity: pity,
        splashArt: "/assets/logo.svg"
    };
}

// 3. Controlador da Animação Pure CSS FX por Jogo (Genshin Meteoro, HSR Warp, ZZZ Signal Glitch)
function animateWishCSS(gameId, maxRarity, onComplete) {
    if (window.wishAnimTimeout) {
        clearTimeout(window.wishAnimTimeout);
        window.wishAnimTimeout = null;
    }

    const modal = document.getElementById("wish-animation-modal");
    const revealContainer = document.getElementById("wish-reveal-container");

    const fxGenshin = document.getElementById("wish-fx-genshin");
    const fxHsr = document.getElementById("wish-fx-hsr");
    const fxZzz = document.getElementById("wish-fx-zzz");

    if (modal) {
        modal.style.display = "flex";
        modal.style.opacity = "1";
        modal.style.visibility = "visible";
        modal.style.zIndex = "999999";
    }

    if (revealContainer) revealContainer.style.display = "none";

    if (fxGenshin) fxGenshin.style.display = "none";
    if (fxHsr) fxHsr.style.display = "none";
    if (fxZzz) fxZzz.style.display = "none";

    const rarityClass = maxRarity === 5 ? "gold" : (maxRarity === 4 ? "purple" : "blue");

    if (gameId === "genshin") {
        if (fxGenshin) fxGenshin.style.display = "block";
        const meteor = document.getElementById("wish-fx-meteor");
        const shockwave = document.getElementById("wish-fx-shockwave");
        if (meteor && shockwave) {
            meteor.className = "wish-fx-meteor";
            shockwave.className = "wish-fx-shockwave";
            void meteor.offsetWidth;
            meteor.className = `wish-fx-meteor animating ${rarityClass}`;
            shockwave.className = `wish-fx-shockwave animating ${rarityClass}`;
        }
    } else if (gameId === "hsr") {
        if (fxHsr) fxHsr.style.display = "block";
        const warpStar = document.getElementById("hsr-warp-star");
        if (warpStar) {
            warpStar.className = "hsr-warp-star-trail";
            void warpStar.offsetWidth;
            warpStar.className = `hsr-warp-star-trail animating ${rarityClass}`;
        }
    } else {
        if (fxZzz) fxZzz.style.display = "block";
        const signalBox = document.getElementById("zzz-signal-box");
        if (signalBox) {
            signalBox.className = "zzz-signal-box";
            void signalBox.offsetWidth;
            signalBox.className = `zzz-signal-box animating ${rarityClass}`;
        }
    }

    try { playWishSound('launch', maxRarity); } catch (e) {}

    window.wishAnimTimeout = setTimeout(() => {
        if (fxGenshin) fxGenshin.style.display = "none";
        if (fxHsr) fxHsr.style.display = "none";
        if (fxZzz) fxZzz.style.display = "none";

        if (onComplete) onComplete();
    }, 1200);
}

let wishCurrentResults = [];
window.wishCurrentIndex = 0;
let wishIsMultiPull = false;
let wishGameId = "genshin";

// 4. Controlador Principal da Animação do Wish
window.startWishAnimation = function(pullsCount = 1) {
    try {
        const activePill = document.querySelector("#gacha-game-pills .gacha-game-pill.active");
        const gameIdHidden = document.getElementById("tab-gacha-game-select")?.value;
        wishGameId = (activePill ? activePill.dataset.game : (gameIdHidden || "genshin")).toLowerCase();

        const pityInput = document.getElementById("tab-gacha-pity");
        const guatSelect = document.getElementById("tab-gacha-guaranteed");
        const charSelect = document.getElementById("tab-gacha-char-select");

        const currentPity = parseInt(pityInput?.value || 35);
        const isGuaranteed = guatSelect?.value === "true";
        
        let selectedCharName = "Personagem 5★ Limitado";
        if (charSelect && charSelect.selectedIndex >= 0 && charSelect.options[charSelect.selectedIndex]) {
            selectedCharName = charSelect.options[charSelect.selectedIndex].text;
        }

        wishCurrentResults = [];
        let curPity = currentPity;
        let curGuat = isGuaranteed;

        for (let i = 0; i < pullsCount; i++) {
            const item = rollSingleWishItem(wishGameId, curPity, curGuat, selectedCharName);
            wishCurrentResults.push(item);
            curPity = item.newPity;
            curGuat = item.isGuaranteedNext;
        }

        if (pityInput) pityInput.value = curPity;
        if (guatSelect) guatSelect.value = curGuat ? "true" : "false";

        window.wishCurrentIndex = 0;
        wishIsMultiPull = pullsCount > 1;
        const maxRarity = Math.max(...wishCurrentResults.map(r => r.rarity));

        animateWishCSS(wishGameId, maxRarity, () => {
            showWishItemAtIndex(0);
        });
    } catch (err) {
        console.error("[Wish Animation Error]", err);
    }
};

// 5. Exibe Item Individual por Índice (Sequência Item por Item)
window.showWishItemAtIndex = function(index) {
    if (index >= wishCurrentResults.length) {
        showWishSummaryGrid();
        return;
    }

    window.wishCurrentIndex = index;
    const item = wishCurrentResults[index];
    const maxRarity = item.rarity;

    const revealContainer = document.getElementById("wish-reveal-container");
    const summaryContainer = document.getElementById("wish-summary-container");

    if (summaryContainer) summaryContainer.style.display = "none";

    if (revealContainer) {
        revealContainer.style.display = "flex";
        revealContainer.style.animation = 'none';
        void revealContainer.offsetWidth;
        revealContainer.style.animation = 'wishCardPop 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards';
    }

    try { playWishSound('reveal', maxRarity); } catch (e) {}

    const glow = document.getElementById("wish-card-glow");
    if (glow) {
        if (maxRarity === 5) {
            glow.style.background = "radial-gradient(circle, #f59e0b 0%, #fbbf24 45%, rgba(245, 158, 11, 0) 75%)";
        } else if (maxRarity === 4) {
            glow.style.background = "radial-gradient(circle, #a855f7 0%, #c084fc 45%, rgba(168, 85, 247, 0) 75%)";
        } else {
            glow.style.background = "radial-gradient(circle, #0284c7 0%, #38bdf8 45%, rgba(56, 189, 248, 0) 75%)";
        }
    }

    const gameBadge = document.getElementById("wish-card-game-badge");
    if (gameBadge) {
        const titles = { genshin: "Genshin Impact", hsr: "Honkai: Star Rail", zzz: "Zenless Zone Zero" };
        gameBadge.innerText = titles[wishGameId] || "Gacha Wish";
        if (maxRarity === 5) {
            gameBadge.style.color = "#fbbf24";
            gameBadge.style.borderColor = "rgba(245, 158, 11, 0.4)";
            gameBadge.style.background = "rgba(245, 158, 11, 0.2)";
        } else if (maxRarity === 4) {
            gameBadge.style.color = "#c084fc";
            gameBadge.style.borderColor = "rgba(168, 85, 247, 0.4)";
            gameBadge.style.background = "rgba(168, 85, 247, 0.2)";
        } else {
            gameBadge.style.color = "#38bdf8";
            gameBadge.style.borderColor = "rgba(56, 189, 248, 0.4)";
            gameBadge.style.background = "rgba(56, 189, 248, 0.2)";
        }
    }

    const cardArt = document.getElementById("wish-card-art");
    if (cardArt) {
        if (item.rarity >= 4) {
            cardArt.src = item.splashArt || getWishCharacterSplash(wishGameId, item.name);
        } else {
            cardArt.src = "/assets/logo.svg";
        }
    }

    const cardName = document.getElementById("wish-card-name");
    if (cardName) cardName.innerText = item.name;

    const cardStars = document.getElementById("wish-card-stars");
    if (cardStars) {
        cardStars.innerText = "★".repeat(item.rarity);
        cardStars.style.color = maxRarity === 5 ? "#fbbf24" : (maxRarity === 4 ? "#c084fc" : "#38bdf8");
    }

    const cardBadge = document.getElementById("wish-card-status-badge");
    if (cardBadge) {
        if (maxRarity === 5) {
            cardBadge.style.color = "#34d399";
            cardBadge.style.borderColor = "rgba(52, 211, 153, 0.35)";
            cardBadge.style.background = "rgba(52, 211, 153, 0.15)";
            cardBadge.innerHTML = `<i class="fa-solid fa-trophy" style="color: #fbbf24;"></i> ${item.won5050 ? '5★ LIMITADO ADQUIRIDO!' : '5★ MOCHILEIRO (Perdeu 50/50)'}`;
        } else if (maxRarity === 4) {
            cardBadge.style.color = "#c084fc";
            cardBadge.style.borderColor = "rgba(168, 85, 247, 0.35)";
            cardBadge.style.background = "rgba(168, 85, 247, 0.15)";
            cardBadge.innerHTML = `<i class="fa-solid fa-sparkles" style="color: #c084fc;"></i> PERSONAGEM 4★ ADQUIRIDO!`;
        } else {
            cardBadge.style.color = "#38bdf8";
            cardBadge.style.borderColor = "rgba(56, 189, 248, 0.35)";
            cardBadge.style.background = "rgba(56, 189, 248, 0.15)";
            cardBadge.innerHTML = `<i class="fa-solid fa-shield" style="color: #38bdf8;"></i> Item 3★ Adquirido`;
        }
    }

    const cardPity = document.getElementById("wish-card-pity-text");
    if (cardPity) {
        if (wishIsMultiPull) {
            cardPity.innerText = `Item ${index + 1} de ${wishCurrentResults.length} • Tiro nº ${item.pitySpent}`;
        } else {
            cardPity.innerText = `Tiro nº ${item.pitySpent} • ${item.pitySpent >= 74 ? 'Soft Pity Ativo' : 'Pity Normal'}`;
        }
    }

    const nextBtn = document.getElementById("wish-next-item-btn");
    const normalActions = document.getElementById("wish-single-actions-bar");

    if (wishIsMultiPull && wishCurrentResults.length > 1) {
        if (nextBtn) nextBtn.style.display = "flex";
        if (normalActions) normalActions.style.display = "none";
        
        const nextBtnLabel = document.getElementById("wish-next-btn-label");
        if (nextBtnLabel) {
            nextBtnLabel.innerText = index === wishCurrentResults.length - 1 ? "Ver Resumo dos 10 Tiros ➔" : `Próximo Item (${index + 1}/${wishCurrentResults.length}) ➔`;
        }
    } else {
        if (nextBtn) nextBtn.style.display = "none";
        if (normalActions) normalActions.style.display = "flex";
    }
};

// 6. Exibe a Tela de Resumo Final dos 10 Tiros (Lado a Lado)
window.showWishSummaryGrid = function() {
    const revealContainer = document.getElementById("wish-reveal-container");
    const summaryContainer = document.getElementById("wish-summary-container");
    const gridBox = document.getElementById("wish-summary-grid-box");

    if (revealContainer) revealContainer.style.display = "none";
    if (summaryContainer) {
        summaryContainer.style.display = "flex";
        summaryContainer.style.animation = 'none';
        void summaryContainer.offsetWidth;
        summaryContainer.style.animation = 'wishCardPop 0.4s ease-out forwards';
    }

    if (gridBox) {
        gridBox.innerHTML = wishCurrentResults.map((r, idx) => {
            const borderCol = r.rarity === 5 ? '#fbbf24' : (r.rarity === 4 ? '#a855f7' : '#38bdf8');
            const bgGradient = r.rarity === 5 
                ? 'linear-gradient(180deg, rgba(251, 191, 36, 0.3) 0%, rgba(15, 23, 42, 0.95) 100%)' 
                : (r.rarity === 4 
                    ? 'linear-gradient(180deg, rgba(168, 85, 247, 0.3) 0%, rgba(15, 23, 42, 0.95) 100%)' 
                    : 'linear-gradient(180deg, rgba(56, 189, 248, 0.2) 0%, rgba(15, 23, 42, 0.95) 100%)');

            const artUrl = r.rarity >= 4 ? (r.splashArt || getWishCharacterSplash(wishGameId, r.name)) : '/assets/logo.svg';

            return `
                <div style="position: relative; background: ${bgGradient}; border: 2px solid ${borderCol}; border-radius: 16px; padding: 14px 8px; display: flex; flex-direction: column; align-items: center; justify-content: space-between; text-align: center; box-shadow: 0 8px 20px rgba(0,0,0,0.6); transition: transform 0.2s;">
                    <div style="width: 72px; height: 92px; border-radius: 10px; overflow: hidden; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.2);">
                        <img src="${artUrl}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.src='/assets/logo.svg'">
                    </div>
                    <span style="font-size: 11px; font-weight: 800; color: #ffffff; line-height: 1.2; margin-bottom: 4px; max-width: 95px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${r.name}</span>
                    <div style="font-size: 12px; color: ${borderCol}; font-weight: bold;">${'★'.repeat(r.rarity)}</div>
                </div>
            `;
        }).join('');
    }
};

window.skipWishAnimation = function() {
    if (window.wishAnimTimeout) {
        clearTimeout(window.wishAnimTimeout);
        window.wishAnimTimeout = null;
    }

    const fxGenshin = document.getElementById("wish-fx-genshin");
    const fxHsr = document.getElementById("wish-fx-hsr");
    const fxZzz = document.getElementById("wish-fx-zzz");
    if (fxGenshin) fxGenshin.style.display = "none";
    if (fxHsr) fxHsr.style.display = "none";
    if (fxZzz) fxZzz.style.display = "none";

    if (wishIsMultiPull && wishCurrentResults.length > 1) {
        showWishSummaryGrid();
    } else {
        showWishItemAtIndex(0);
    }
};

window.closeWishModal = function() {
    if (window.wishAnimTimeout) {
        clearTimeout(window.wishAnimTimeout);
        window.wishAnimTimeout = null;
    }
    const modal = document.getElementById("wish-animation-modal");
    if (modal) modal.style.display = "none";
};




