// ==========================================================================
// Módulo: api_client.js
// Cabeça de Droid - Vanilla ES6 Module
// ==========================================================================

// ==========================================================================
// CONFIGURAÇÕES GERAIS E ESTADO GLOBAL
// ==========================================================================
const API_URL = ""; // Relativo ao servidor que serve a página
let chatHistory = [];
let activePolling = { zzz: null, genshin: null, hsr: null };
let globalRoster = { zzz: [], genshin: [], hsr: [] };
let activeInspectGame = "";
let activeInspectChar = null;

// ==========================================================================
// INTERCEPTOR GLOBAL DE FETCH (SEGURANÇA & PIN 423)
// ==========================================================================
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    const response = await originalFetch.apply(this, args);
    if (response.status === 423) {
        showPinLockModal();
    }
    return response;
};

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
    "Proficiência Elemental": "Prof. Elementar",
    "Proficiência Elementar": "Prof. Elementar",
    "Recarga de Energia": "Recarga",
    "Bônus de Cura Recebida": "Cura Recebida",
    "Bônus de Cura": "Bônus Cura",
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




// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
if (typeof API_URL !== 'undefined') window.API_URL = API_URL;
if (typeof ELEMENT_MAPPING !== 'undefined') window.ELEMENT_MAPPING = ELEMENT_MAPPING;
if (typeof SLOT_ICONS !== 'undefined') window.SLOT_ICONS = SLOT_ICONS;
if (typeof STAT_SHORT_NAMES !== 'undefined') window.STAT_SHORT_NAMES = STAT_SHORT_NAMES;
if (typeof activeInspectChar !== 'undefined') window.activeInspectChar = activeInspectChar;
if (typeof activeInspectGame !== 'undefined') window.activeInspectGame = activeInspectGame;
if (typeof activePolling !== 'undefined') window.activePolling = activePolling;
if (typeof chatHistory !== 'undefined') window.chatHistory = chatHistory;
if (typeof formatElementDisplayName !== 'undefined') window.formatElementDisplayName = formatElementDisplayName;
if (typeof getNormalizedSlot !== 'undefined') window.getNormalizedSlot = getNormalizedSlot;
if (typeof getSafeFileName !== 'undefined') window.getSafeFileName = getSafeFileName;
if (typeof getSlotIcon !== 'undefined') window.getSlotIcon = getSlotIcon;
if (typeof globalRoster !== 'undefined') window.globalRoster = globalRoster;
if (typeof isStatRecommendedForChar !== 'undefined') window.isStatRecommendedForChar = isStatRecommendedForChar;
if (typeof originalFetch !== 'undefined') window.originalFetch = originalFetch;
if (typeof sanitizeStatName !== 'undefined') window.sanitizeStatName = sanitizeStatName;