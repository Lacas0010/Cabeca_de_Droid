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
    const isEn = Boolean(window.isEn || (window.getCurrentLanguage && window.getCurrentLanguage() === 'en') || window.currentLang === 'en' || (typeof localStorage !== 'undefined' && localStorage.getItem('app_language') === 'en'));
    if (!rawElem) return isEn ? "Physical" : "Físico";
    const str = String(rawElem).trim();
    const upper = str.toUpperCase();
    if (upper === "ELEMENT_300" || upper === "ELEMENT 300" || upper === "LUMIFLUX") return "Lumiflux";
    if (upper === "ELEMENT_100" || upper === "ELEMENT 100") return isEn ? "Physical" : "Físico";
    if (upper === "ELEMENT_200" || upper === "ELEMENT 200") return isEn ? "Fire" : "Fogo";
    if (upper === "ELEMENT_400" || upper === "ELEMENT 400") return isEn ? "Electric" : "Elétrico";
    if (upper === "ELEMENT_500" || upper === "ELEMENT 500") return isEn ? "Ether" : "Éter";
    if (isEn) {
        const enMap = {
            "físico": "Physical", "fisico": "Physical",
            "fogo": "Fire",
            "gelo": "Ice",
            "elétrico": "Electric", "eletrico": "Electric",
            "éter": "Ether", "eter": "Ether",
            "vento": "Wind",
            "raio": "Lightning",
            "quântico": "Quantum", "quantico": "Quantum",
            "imaginário": "Imaginary", "imaginario": "Imaginary"
        };
        const lower = str.toLowerCase();
        if (enMap[lower]) return enMap[lower];
    } else {
        const ptMap = {
            "physical": "Físico",
            "fire": "Fogo",
            "ice": "Gelo",
            "electric": "Elétrico",
            "ether": "Éter",
            "wind": "Vento",
            "lightning": "Raio",
            "quantum": "Quântico",
            "imaginary": "Imaginário"
        };
        const lower = str.toLowerCase();
        if (ptMap[lower]) return ptMap[lower];
    }
    return str;
}

// Mapa de Tradução de Nomes de Personagens PT -> EN
const CHARACTER_NAME_MAP_EN = {
    // HSR
    "loba prateada": "Silver Wolf",
    "lobo prateado": "Silver Wolf",
    "loba prateada nv. 999": "Silver Wolf Lv. 999",
    "loba prateada nv 999": "Silver Wolf Lv. 999",
    "loba prateada (nv. 999)": "Silver Wolf (Lv. 999)",
    "loba prateada • nv. 999": "Silver Wolf • Lv. 999",
    "noite eterna": "Evernight",
    "7 de março (noite eterna)": "March 7th (Evernight)",
    "a dália": "The Dahlia",
    "a dalia": "The Dahlia",
    "desbravador": "Trailblazer",
    "desbravadora": "Trailblazer",
    "desbravador(a)": "Trailblazer",
    "desbravador (destruição)": "Trailblazer (Destruction)",
    "desbravador (preservação)": "Trailblazer (Preservation)",
    "desbravador (harmonia)": "Trailblazer (Harmony)",
    "desbravador (recordação)": "Trailblazer (Remembrance)",
    "desbravador (reminiscência)": "Trailblazer (Remembrance)",
    "desbravador • destruição": "Trailblazer • Destruction",
    "desbravador • preservação": "Trailblazer • Preservation",
    "desbravador • harmonia": "Trailblazer • Harmony",
    "desbravador • recordação": "Trailblazer • Remembrance",
    "desbravador • reminiscência": "Trailblazer • Remembrance",
    "desbravadora (destruição)": "Trailblazer (Destruction)",
    "desbravadora (preservação)": "Trailblazer (Preservation)",
    "desbravadora (harmonia)": "Trailblazer (Harmony)",
    "desbravadora (recordação)": "Trailblazer (Remembrance)",
    "desbravadora (reminiscência)": "Trailblazer (Remembrance)",
    "desbravadora • destruição": "Trailblazer • Destruction",
    "desbravadora • preservação": "Trailblazer • Preservation",
    "desbravadora • harmonia": "Trailblazer • Harmony",
    "desbravadora • recordação": "Trailblazer • Remembrance",
    "desbravadora • reminiscência": "Trailblazer • Remembrance",
    "7 de março": "March 7th",
    "7 de março (caça)": "March 7th (The Hunt)",
    "7 de março • a caça": "March 7th • The Hunt",
    "7 de março • caça": "March 7th • The Hunt",
    "7 de março (preservação)": "March 7th (Preservation)",
    "7 de março • preservação": "March 7th • Preservation",
    "cisne negro": "Black Swan",
    "vaga-lume": "Firefly",
    "vagalume": "Firefly",
    "faísca": "Sparkle",
    "faisca": "Sparkle",
    "aventurina": "Aventurine",
    "a herta": "The Herta",
    "topaz e dinheirinho": "Topaz & Numby",
    "topaz & dinheirinho": "Topaz & Numby",
    "topaz e dinhero": "Topaz & Numby",
    "topaz & dinhero": "Topaz & Numby",
    "dan heng • embebedor de luna": "Dan Heng • Imbibitor Lunae",
    "dan heng embebedor de luna": "Dan Heng • Imbibitor Lunae",
    "embebedor de luna": "Dan Heng • Imbibitor Lunae",
    "tingyun • fuga": "Tingyun • Fugue",
    "tingyun fuga": "Tingyun • Fugue",
    "doutor ratio": "Dr. Ratio",
    "dr ratio": "Dr. Ratio",
    "dr. ratio": "Dr. Ratio",
    "domingo": "Sunday",
    "aqueronte": "Acheron",
    // Genshin
    "viajante": "Traveler",
    "viajante (anemo)": "Traveler (Anemo)",
    "viajante (geo)": "Traveler (Geo)",
    "viajante (electro)": "Traveler (Electro)",
    "viajante (dendro)": "Traveler (Dendro)",
    "viajante (hydro)": "Traveler (Hydro)",
    "viajante (pyro)": "Traveler (Pyro)",
    "viajante (cryo)": "Traveler (Cryo)",
    "viajante anemo": "Traveler (Anemo)",
    "viajante geo": "Traveler (Geo)",
    "viajante electro": "Traveler (Electro)",
    "viajante dendro": "Traveler (Dendro)",
    "viajante hydro": "Traveler (Hydro)",
    "viajante pyro": "Traveler (Pyro)",
    "viajante cryo": "Traveler (Cryo)",
    "mochileiro": "Wanderer",
    "andarilho": "Wanderer",
    "trotamundos": "Wanderer",
    "shogun raiden": "Raiden Shogun",
    "arlequino": "Arlecchino",
    "manequina": "Mannequin",
    // ZZZ
    "soldado 11": "Soldier 11",
    "anby (soldado 0)": "Anby: Soldier 0",
    "anby: soldado 0": "Anby: Soldier 0",
    "n.º 11": "Soldier 11",
    "nº 11": "Soldier 11",
    "n° 11": "Soldier 11",
    "número 11": "Soldier 11",
    "numero 11": "Soldier 11",
    "císsia": "Cissia",
    "cissia": "Cissia",
    "orfeu & magus": "Orphie & Magus",
    "orfeu e magus": "Orphie & Magus"
};

function formatCharacterName(rawName) {
    if (!rawName) return "";
    const isEn = Boolean(window.isEn || (window.getCurrentLanguage && window.getCurrentLanguage() === 'en') || window.currentLang === 'en' || (typeof localStorage !== 'undefined' && localStorage.getItem('app_language') === 'en'));
    const str = String(rawName).trim();
    if (!isEn) return str;

    const lower = str.toLowerCase();
    if (CHARACTER_NAME_MAP_EN[lower]) return CHARACTER_NAME_MAP_EN[lower];

    const sortedEntries = Object.entries(CHARACTER_NAME_MAP_EN).sort((a, b) => b[0].length - a[0].length);
    for (const [ptKey, enVal] of sortedEntries) {
        if (lower.startsWith(ptKey)) {
            const remainder = str.slice(ptKey.length).replace(/\bNv\.\s*/gi, "Lv. ");
            return enVal + remainder;
        }
    }
    return str;
}

const PATH_MAP_EN = {
    "destruição": "Destruction", "destruicao": "Destruction",
    "a caça": "The Hunt", "caça": "The Hunt", "caca": "The Hunt",
    "erudição": "Erudition", "erudicao": "Erudition",
    "harmonia": "Harmony",
    "inexistência": "Nihility", "inexistencia": "Nihility",
    "preservação": "Preservation", "preservacao": "Preservation",
    "abundância": "Abundance", "abundancia": "Abundance",
    "reminiscência": "Remembrance", "reminiscencia": "Remembrance",
    "recordação": "Remembrance", "recordacao": "Remembrance",
    "euforia": "Elation", "júbilo": "Elation", "jubilo": "Elation",
    "ataque": "Attack",
    "atordoamento": "Stun",
    "anomalia": "Anomaly",
    "suporte": "Support",
    "defesa": "Defense",
    "espada": "Sword",
    "espadão": "Claymore", "espadao": "Claymore", "espada larga": "Claymore",
    "lança": "Polearm", "lanca": "Polearm",
    "arco": "Bow",
    "catalisador": "Catalyst"
};

const PATH_MAP_PT = {
    "destruction": "Destruição",
    "the hunt": "A Caça", "hunt": "A Caça",
    "erudition": "Erudição",
    "harmony": "Harmonia",
    "nihility": "Inexistência",
    "preservation": "Preservação",
    "abundance": "Abundância",
    "remembrance": "Reminiscência",
    "elation": "Euforia",
    "attack": "Ataque",
    "stun": "Atordoamento",
    "anomaly": "Anomalia",
    "support": "Suporte",
    "defense": "Defesa",
    "sword": "Espada",
    "claymore": "Espadão",
    "polearm": "Lança",
    "bow": "Arco",
    "catalyst": "Catalisador"
};

function formatPathName(rawPath, gameId) {
    if (!rawPath) return "";
    const isEn = Boolean(window.isEn || (window.getCurrentLanguage && window.getCurrentLanguage() === 'en') || window.currentLang === 'en' || (typeof localStorage !== 'undefined' && localStorage.getItem('app_language') === 'en'));
    const str = String(rawPath).trim();
    const lower = str.toLowerCase();
    if (isEn) {
        return PATH_MAP_EN[lower] || (str.charAt(0).toUpperCase() + str.slice(1));
    } else {
        return PATH_MAP_PT[lower] || str;
    }
}

const STAT_SHORT_NAMES_EN = {
    "velocidade": "Speed", "vel": "SPD",
    "vida": "HP", "pv": "HP", "vida máx": "Max HP", "vida máx.": "Max HP", "pv máx.": "Max HP", "vida máxima": "Max HP",
    "ataque": "ATK", "atq": "ATK",
    "defesa": "DEF", "def": "DEF",
    "taxa crit": "CRIT Rate", "taxa de crit": "CRIT Rate", "taxa crítica": "CRIT Rate", "chance de crit": "CRIT Rate", "tx. cr": "CRIT Rate", "tx. crítica": "CRIT Rate", "tx. crit": "CRIT Rate",
    "dano crit": "CRIT DMG", "dano de crit": "CRIT DMG", "dano crítico": "CRIT DMG", "dano cr": "CRIT DMG",
    "efeito de quebra": "Break Effect", "quebra": "Break Effect",
    "taxa de acerto de efeito": "Effect Hit Rate", "acerto efeito": "Effect Hit Rate", "acerto de efeito": "Effect Hit Rate",
    "resistência a efeito": "Effect RES", "res a efeito": "Effect RES", "res efeito": "Effect RES",
    "taxa de regeneração de energia": "Energy Regen", "taxa de reg. de energia": "Energy Regen", "taxa de regen. energia": "Energy Regen", "taxa de regen de energia": "Energy Regen", "regeneração de energia": "Energy Regen", "regen. energia": "Energy Regen", "energy regeneration rate": "Energy Regen", "energy regen rate": "Energy Regen", "energy regen": "Energy Regen", "energy recharge": "Energy Recharge", "elemental mastery": "Elemental Mastery", "outgoing healing boost": "Healing Bonus", "break effect": "Break Effect", "effect hit rate": "Effect Hit Rate", "effect res": "Effect RES", "anomaly proficiency": "Anomaly Prof.", "anomaly mastery": "Anomaly Mastery", "pen ratio": "PEN Ratio",
    "recuperação de energia": "Energy Regen", "recup. energia": "Energy Regen",
    "recarga de energia": "Energy Recharge", "recarga": "Energy Recharge",
    "proficiência elemental": "Elemental Mastery", "proficiência elementar": "Elemental Mastery", "prof. elementar": "Elemental Mastery", "prof. element.": "Elemental Mastery",
    "bônus de cura": "Healing Bonus", "bônus cura": "Healing Bonus", "cura bônus": "Healing Bonus", "bônus de cura recebida": "Incoming Healing", "cura recebida": "Incoming Healing",
    "proficiência de anomalia": "Anomaly Prof.", "prof. anomalia": "Anomaly Prof.", "prof. anom": "Anomaly Prof.",
    "taxa de acerto de anomalia": "Anomaly Mastery", "maestria de anomalia": "Anomaly Mastery", "maest. anomalia": "Anomaly Mastery",
    "taxa de perfuração": "PEN Ratio", "perfuração": "PEN Ratio",
    "impacto": "Impact",
    "bônus de dano de fogo": "Fire DMG", "bônus de dano fogo": "Fire DMG", "dano fogo": "Fire DMG",
    "bônus de dano de gelo": "Ice DMG", "bônus de dano gelo": "Ice DMG", "dano gelo": "Ice DMG",
    "bônus de dano de raio": "Lightning DMG", "bônus de dano raio": "Lightning DMG", "dano raio": "Lightning DMG",
    "bônus de dano de vento": "Wind DMG", "bônus de dano vento": "Wind DMG", "dano vento": "Wind DMG",
    "bônus de dano quântico": "Quantum DMG", "bônus de dano de quântico": "Quantum DMG", "dano quântico": "Quantum DMG",
    "bônus de dano imaginário": "Imaginary DMG", "bônus de dano de imaginário": "Imaginary DMG", "dano imaginário": "Imaginary DMG",
    "bônus de dano físico": "Physical DMG", "bônus de dano de físico": "Physical DMG", "dano físico": "Physical DMG",
    "bônus de dano anemo": "Anemo DMG", "dano anemo": "Anemo DMG",
    "bônus de dano pyro": "Pyro DMG", "dano pyro": "Pyro DMG",
    "bônus de dano hydro": "Hydro DMG", "dano hydro": "Hydro DMG",
    "bônus de dano electro": "Electro DMG", "dano electro": "Electro DMG",
    "bônus de dano cryo": "Cryo DMG", "dano cryo": "Cryo DMG",
    "bônus de dano geo": "Geo DMG", "dano geo": "Geo DMG",
    "bônus de dano dendro": "Dendro DMG", "dano dendro": "Dendro DMG",
    "bônus de dano elétrico": "Electric DMG", "bônus de dano de elétrico": "Electric DMG", "dano elétrico": "Electric DMG",
    "bônus de dano éter": "Ether DMG", "bônus de dano de éter": "Ether DMG", "dano éter": "Ether DMG"
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
    "Taxa de Regen. Energia": "Regen. Energia",
    "Taxa de Regen de Energia": "Regen. Energia",

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
    const isEn = Boolean(window.isEn || (window.getCurrentLanguage && window.getCurrentLanguage() === 'en') || window.currentLang === 'en' || (typeof localStorage !== 'undefined' && localStorage.getItem('app_language') === 'en'));
    let s = String(statText).trim();
    if (isEn) {
        const lower = s.toLowerCase();
        if (STAT_SHORT_NAMES_EN[lower]) return STAT_SHORT_NAMES_EN[lower];
        for (const [k, v] of Object.entries(STAT_SHORT_NAMES_EN)) {
            if (lower === k || lower.startsWith(k)) {
                return v;
            }
        }
        s = s.replace(/Bônus de Dano (?:de )?([A-Za-zÀ-ÿ]+)/gi, (m, elem) => formatElementDisplayName(elem) + ' DMG');
        s = s.replace(/Dano ([A-Za-zÀ-ÿ]+)/gi, (m, elem) => formatElementDisplayName(elem) + ' DMG');
        return s;
    }

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
if (typeof formatCharacterName !== 'undefined') window.formatCharacterName = formatCharacterName;
if (typeof formatPathName !== 'undefined') window.formatPathName = formatPathName;
