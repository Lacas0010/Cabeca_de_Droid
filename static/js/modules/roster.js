// ==========================================================================
// Módulo: roster.js
// Cabeça de Droid - Vanilla ES6 Module
// ==========================================================================

// ==========================================================================
// RENDERIZAÇÃO DA GALERIA DE PERSONAGENS
// ==========================================================================
function getCharacterPath(char) {
    if (char && char.path) return String(char.path);
    const nameLower = (char && char.name ? char.name : "").toLowerCase().trim();
    if (nameLower.includes("desbrav") || nameLower.includes("trailblazer")) {
        const elem = (char && char.element ? char.element : "").toLowerCase();
        if (elem.includes("ice") || elem.includes("gelo")) return "Remembrance";
        if (elem.includes("fire") || elem.includes("fogo")) return "Preservation";
        if (elem.includes("imaginary") || elem.includes("imagin")) return "Harmony";
        if (elem.includes("physical") || elem.includes("físic") || elem.includes("fisic")) return "Destruction";
    }
    return "";
}

function getCharacterWeapon(char) {
    if (char && char.weapon_type) return String(char.weapon_type);
    if (char && char.path && ["sword", "claymore", "polearm", "bow", "catalyst"].includes(String(char.path).toLowerCase())) return String(char.path);
    const wName = (typeof char.weapon === "object" && char.weapon ? char.weapon.name : char.weapon_name) || "";
    if (wName) {
        const wLower = String(wName).toLowerCase();
        if (wLower.includes("arco") || wLower.includes("bow") || wLower.includes("cordas") || wLower.includes("asa gelada") || wLower.includes("estilingue") || wLower.includes("harpa") || wLower.includes("caçador")) return "Bow";
        if (wLower.includes("lança") || wLower.includes("lanca") || wLower.includes("polearm") || wLower.includes("spear") || wLower.includes("borla") || wLower.includes("dragão") || wLower.includes("dragao") || wLower.includes("subjugadora") || wLower.includes("perdição") || wLower.includes("perdicao")) return "Polearm";
        if (wLower.includes("espadão") || wLower.includes("espadao") || wLower.includes("claymore") || wLower.includes("grande espada") || wLower.includes("túmulo") || wLower.includes("tumulo") || wLower.includes("sombra branca")) return "Claymore";
        if (wLower.includes("espada") || wLower.includes("sword") || wLower.includes("lâmina") || wLower.includes("lamina") || wLower.includes("farpa") || wLower.includes("espinho") || wLower.includes("chuva floral") || wLower.includes("cortadora") || wLower.includes("falcão") || wLower.includes("falcao")) return "Sword";
        if (wLower.includes("catalisador") || wLower.includes("catalyst") || wLower.includes("guia") || wLower.includes("sinfonia") || wLower.includes("contos") || wLower.includes("atlas") || wLower.includes("oração") || wLower.includes("oracao") || wLower.includes("olho") || wLower.includes("éditos") || wLower.includes("editos") || wLower.includes("memórias") || wLower.includes("memorias") || wLower.includes("codex") || wLower.includes("protótipo âmbar") || wLower.includes("prototipo ambar")) return "Catalyst";
    }
    return "";
}

// ==========================================================================
// METADADOS E HELPERS DE AUDITORIA DE BUILD E ORDENAÇÃO
// ==========================================================================
const GENSHIN_CHAR_REGIONS = {
    "albedo": "mondstadt", "amber": "mondstadt", "barbara": "mondstadt", "bennett": "mondstadt",
    "diluc": "mondstadt", "diona": "mondstadt", "eula": "mondstadt", "fischl": "mondstadt",
    "jean": "mondstadt", "kaeya": "mondstadt", "klee": "mondstadt", "lisa": "mondstadt",
    "mika": "mondstadt", "mona": "mondstadt", "noelle": "mondstadt", "razor": "mondstadt",
    "rosaria": "mondstadt", "sucrose": "mondstadt", "venti": "mondstadt", "durin": "mondstadt",
    "dahlia": "mondstadt", "aloy": "mondstadt",
    "baizhu": "liyue", "beidou": "liyue", "chongyun": "liyue", "gaming": "liyue",
    "ganyu": "liyue", "hu tao": "liyue", "hu_tao": "liyue", "hutao": "liyue",
    "keqing": "liyue", "lan yan": "liyue", "lan_yan": "liyue", "ningguang": "liyue",
    "qiqi": "liyue", "shenhe": "liyue", "xiangling": "liyue", "xianyun": "liyue",
    "xiao": "liyue", "xingqiu": "liyue", "xinyan": "liyue", "yanfei": "liyue",
    "yaoyao": "liyue", "yelan": "liyue", "yun jin": "liyue", "yun_jin": "liyue", "yunjin": "liyue",
    "zhongli": "liyue",
    "arataki itto": "inazuma", "arataki_itto": "inazuma", "itto": "inazuma",
    "kamisato ayaka": "inazuma", "kamisato_ayaka": "inazuma", "ayaka": "inazuma",
    "kamisato ayato": "inazuma", "kamisato_ayato": "inazuma", "ayato": "inazuma",
    "chiori": "inazuma", "gorou": "inazuma", "kirara": "inazuma",
    "kujou sara": "inazuma", "kujou_sara": "inazuma", "sara": "inazuma",
    "kuki shinobu": "inazuma", "kuki_shinobu": "inazuma", "shinobu": "inazuma",
    "raiden shogun": "inazuma", "raiden_shogun": "inazuma", "shogun raiden": "inazuma", "raiden": "inazuma",
    "sangonomiya kokomi": "inazuma", "sangonomiya_kokomi": "inazuma", "kokomi": "inazuma",
    "sayu": "inazuma", "shikanoin heizou": "inazuma", "shikanoin_heizou": "inazuma", "heizou": "inazuma",
    "thoma": "inazuma", "yae miko": "inazuma", "yae_miko": "inazuma", "yae": "inazuma", "yoimiya": "inazuma",
    "yumemizuki mizuki": "inazuma", "yumemizuki_mizuki": "inazuma",
    "alhaitham": "sumeru", "candace": "sumeru", "collei": "sumeru", "cyno": "sumeru",
    "dehya": "sumeru", "dori": "sumeru", "faruzan": "sumeru", "kaveh": "sumeru",
    "layla": "sumeru", "nahida": "sumeru", "nilou": "sumeru", "sethos": "sumeru",
    "tighnari": "sumeru", "wanderer": "sumeru", "andarilho": "sumeru", "scaramouche": "sumeru",
    "arlecchino": "fontaine", "arlequino": "fontaine", "charlotte": "fontaine",
    "chevreuse": "fontaine", "clorinde": "fontaine", "emilie": "fontaine",
    "freminet": "fontaine", "furina": "fontaine", "lynette": "fontaine",
    "lyney": "fontaine", "navia": "fontaine", "neuvillette": "fontaine",
    "sigewinne": "fontaine", "wriothesley": "fontaine", "escoffier": "fontaine",
    "chasca": "natlan", "citlali": "natlan", "iansan": "natlan", "kachina": "natlan",
    "kinich": "natlan", "mavuika": "natlan", "mualani": "natlan", "ororon": "natlan",
    "xilonen": "natlan", "varesa": "natlan", "ifa": "natlan",
    "tartaglia": "snezhnaya", "childe": "snezhnaya", "columbina": "snezhnaya", "alyosha": "snezhnaya"
};

const GENSHIN_NIGHTSOUL_CHARS = new Set([
    "chasca", "citlali", "iansan", "kachina", "kinich", "mavuika", "mualani", "ororon", "xilonen", "varesa", "ifa"
]);

const GENSHIN_PNEUMA_CHARS = new Set([
    "furina", "neuvillette", "lyney", "freminet", "navia", "charlotte", "chiori", "emilie", "escoffier"
]);

const GENSHIN_OUSIA_CHARS = new Set([
    "furina", "lynette", "wriothesley", "clorinde", "chevreuse", "sigewinne"
]);

const ZZZ_FACTIONS = {
    "cunning_hares": ["anby", "billy", "nicole", "nekomata"],
    "belobog": ["koleda", "anton", "ben", "grace"],
    "victoria": ["ellen", "lycaon", "corin", "rina"],
    "section6": ["miyabi", "yanagi", "harumasa", "soukaku", "hoshimi miyabi", "asaba harumasa", "tsukishiro yanagi"],
    "calydon": ["caesar", "burnice", "lighter", "lucy", "piper", "caesar king", "burnice white"],
    "public_security": ["zhu yuan", "zhu_yuan", "qingyi", "jane", "jane doe", "jane_doe", "seth"],
    "defense_force": ["soldado 11", "soldier 11", "soldado_11", "soldier_11"],
    "new_eridu": ["astra yao", "astra", "evelyn"]
};

function getGenshinCharacterRegion(name) {
    if (!name) return "";
    const clean = String(name).toLowerCase().trim().replace(/_/g, " ");
    if (GENSHIN_CHAR_REGIONS[clean]) return GENSHIN_CHAR_REGIONS[clean];
    const slug = clean.replace(/\s+/g, "_");
    if (GENSHIN_CHAR_REGIONS[slug]) return GENSHIN_CHAR_REGIONS[slug];
    for (const [k, reg] of Object.entries(GENSHIN_CHAR_REGIONS)) {
        if (clean.includes(k) || k.includes(clean)) return reg;
    }
    return "";
}

function matchGenshinScale(char, scale) {
    if (!char) return true;
    const prio = (char.substats_priority || []).map(s => String(s).toLowerCase());
    const weights = char.recommended_weights || {};
    const n = (char.name || "").toLowerCase();
    if (scale === "atk") {
        return prio.includes("atk_pct") || (weights.atk_pct && weights.atk_pct >= 0.7);
    }
    if (scale === "hp") {
        return prio.includes("hp_pct") || (weights.hp_pct && weights.hp_pct >= 0.7) ||
            ["furina", "neuvillette", "hu tao", "zhongli", "baizhu", "yelan", "nilou", "columbina", "diona"].some(k => n.includes(k));
    }
    if (scale === "def") {
        return prio.includes("def_pct") || (weights.def_pct && weights.def_pct >= 0.7) ||
            ["albedo", "itto", "noelle", "xilonen", "chiori", "kachina", "gorou", "yun jin", "yunjin", "zibai"].some(k => n.includes(k));
    }
    if (scale === "em") {
        return prio.includes("em") || (weights.em && weights.em >= 0.7) ||
            ["nahida", "alhaitham", "kazuha", "sucrose", "tighnari", "sethos", "nilou", "cyno"].some(k => n.includes(k));
    }
    return true;
}

function matchGenshinMainStat(char, mainStat) {
    const relics = char.relics || char.artifacts || [];
    return relics.some(r => {
        const slot = String(r.slot || "");
        if (!["3", "4", "5", "Areia", "Cálice", "Tiara"].some(s => slot.includes(s))) return false;
        const main = String(r.main || "").toLowerCase();
        if (mainStat === "er") return main.includes("recarga") || main.includes("energy");
        if (mainStat === "em") return main.includes("proficiência") || main.includes("proficiencia") || main.includes("mastery");
        if (mainStat === "elem_dmg") return main.includes("dano ") || main.includes("dmg");
        if (mainStat === "crit") return main.includes("crit");
        if (mainStat === "atk") return main.includes("atq") && main.includes("%");
        if (mainStat === "hp") return (main.includes("vida") || main.includes("pv")) && main.includes("%");
        if (mainStat === "def") return main.includes("def") && main.includes("%");
        return false;
    });
}

function matchZZZFaction(charName, faction) {
    if (!charName || !faction) return true;
    const nameLower = charName.toLowerCase().trim();
    const members = ZZZ_FACTIONS[faction] || [];
    return members.some(m => nameLower.includes(m) || m.includes(nameLower));
}

function matchZZZArchetype(char, arch) {
    if (!char) return true;
    const spec = String(char.specialty || char.role || "").toLowerCase();
    const prio = (char.substats_priority || []).map(s => String(s).toLowerCase());
    if (arch === "anomaly") {
        return spec.includes("anomaly") || prio.some(p => p.includes("anomaly") || p.includes("anomalia"));
    }
    if (arch === "crit") {
        return spec.includes("attack") || spec.includes("stun") || prio.some(p => p.includes("crit"));
    }
    return true;
}

function matchZZZDiscsMain(char, filterVal) {
    const discs = char.relics || char.discs || [];
    return discs.some(d => {
        const slot = String(d.slot || "").toLowerCase();
        const is456 = slot.includes("4") || slot.includes("5") || slot.includes("6");
        if (!is456) return false;
        const main = String(d.main || "").toLowerCase();
        if (filterVal === "crit") return main.includes("crit");
        if (filterVal === "anomaly") return main.includes("anomalia") || main.includes("prof");
        if (filterVal === "elem_dmg") return main.includes("dano ") || main.includes("fogo") || main.includes("elétrico") || main.includes("eletrico") || main.includes("gelo") || main.includes("físico") || main.includes("fisico") || main.includes("éter") || main.includes("eter");
        if (filterVal === "er") return main.includes("energia");
        if (filterVal === "impact") return main.includes("impacto");
        if (filterVal === "atk") return main.includes("atq");
        if (filterVal === "pen") return main.includes("perfuração") || main.includes("perfuracao") || main.includes("pen");
        return false;
    });
}

function getCharacterSetIntegrity(char) {
    if (!char) return "broken";
    const sets = Array.isArray(char.sets) ? char.sets : [];
    if (sets.some(s => typeof s === 'string' && (s.startsWith("4p") || s.includes("4p ") || s.includes("4-peça") || s.includes("4-piece")))) {
        return "4p";
    }
    const twoPieceSets = sets.filter(s => typeof s === 'string' && (s.startsWith("2p") || s.includes("2p ") || s.includes("2-peça") || s.includes("2-piece")));
    if (twoPieceSets.length >= 2) {
        return "2p+2p";
    }
    const relics = char.relics || char.artifacts || char.discs || [];
    if (relics.length >= 4) {
        const counts = {};
        relics.forEach(r => {
            const rawName = (r.set_name || r.name || "").replace(/\s*\[\d+\]\s*$/, "").trim();
            if (rawName) counts[rawName] = (counts[rawName] || 0) + 1;
        });
        const maxCount = Math.max(0, ...Object.values(counts));
        if (maxCount >= 4) return "4p";
        const twoOrMore = Object.values(counts).filter(c => c >= 2).length;
        if (twoOrMore >= 2) return "2p+2p";
    }
    return "broken";
}

function getWorstPieceScore(char) {
    const relics = char.relics || char.artifacts || char.discs || [];
    if (!relics || relics.length === 0) return 9999;
    const scores = relics.map(r => {
        if (typeof r.score === 'number') return r.score;
        const parsed = parseFloat(r.score);
        return isNaN(parsed) ? 0 : parsed;
    });
    return scores.length > 0 ? Math.min(...scores) : 9999;
}

function sortCharacters(list, sortMode) {
    if (!Array.isArray(list) || list.length <= 1) return list;
    const copy = list.slice();

    if (sortMode === "score_desc") {
        return copy.sort((a, b) => (b.overall_score ?? 0) - (a.overall_score ?? 0));
    }
    if (sortMode === "score_asc") {
        return copy.sort((a, b) => (a.overall_score ?? 0) - (b.overall_score ?? 0));
    }
    if (sortMode === "worst_piece_asc") {
        return copy.sort((a, b) => {
            const wA = getWorstPieceScore(a);
            const wB = getWorstPieceScore(b);
            if (wA !== wB) return wA - wB;
            return (b.overall_score ?? 0) - (a.overall_score ?? 0);
        });
    }
    if (sortMode === "rank_desc") {
        const getRank = (c) => parseInt(String(c.rank_str || "").match(/\d+/)?.[0] || "0", 10);
        return copy.sort((a, b) => {
            const diff = getRank(b) - getRank(a);
            if (diff !== 0) return diff;
            return (b.overall_score ?? 0) - (a.overall_score ?? 0);
        });
    }
    if (sortMode === "rank_asc") {
        const getRank = (c) => parseInt(String(c.rank_str || "").match(/\d+/)?.[0] || "0", 10);
        return copy.sort((a, b) => {
            const diff = getRank(a) - getRank(b);
            if (diff !== 0) return diff;
            return (b.overall_score ?? 0) - (a.overall_score ?? 0);
        });
    }
    if (sortMode === "level_desc") {
        return copy.sort((a, b) => {
            const diff = (b.level ?? 0) - (a.level ?? 0);
            if (diff !== 0) return diff;
            return (b.overall_score ?? 0) - (a.overall_score ?? 0);
        });
    }
    if (sortMode === "level_asc") {
        return copy.sort((a, b) => {
            const diff = (a.level ?? 0) - (b.level ?? 0);
            if (diff !== 0) return diff;
            return (a.level ?? 0) - (b.level ?? 0);
        });
    }
    if (sortMode === "name_asc") {
        return copy.sort((a, b) => {
            const nameA = typeof formatCharacterName === 'function' ? formatCharacterName(a.name || '') : (a.name || '');
            const nameB = typeof formatCharacterName === 'function' ? formatCharacterName(b.name || '') : (b.name || '');
            return nameA.localeCompare(nameB, undefined, { sensitivity: 'base' });
        });
    }
    if (sortMode === "name_desc") {
        return copy.sort((a, b) => {
            const nameA = typeof formatCharacterName === 'function' ? formatCharacterName(a.name || '') : (a.name || '');
            const nameB = typeof formatCharacterName === 'function' ? formatCharacterName(b.name || '') : (b.name || '');
            return nameB.localeCompare(nameA, undefined, { sensitivity: 'base' });
        });
    }
    return copy;
}

const _rosterResetCallbacks = {};
window.clearRosterFilters = function(g) {
    if (g && _rosterResetCallbacks[g]) {
        _rosterResetCallbacks[g]();
    }
};

// ==========================================================================
// CONTROLE DE MODO DE VISUALIZAÇÃO: GRADE (GRID) OU LISTA (LIST)
// ==========================================================================
let currentRosterViewMode = (typeof localStorage !== "undefined" && localStorage.getItem("roster_view_mode")) || "grid";
const _rosterRenderers = {};

function setupRosterViewModeToggle() {
    document.querySelectorAll(".view-mode-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const mode = btn.getAttribute("data-mode");
            window.setRosterViewMode(mode);
        });
    });

    window.setRosterViewMode(currentRosterViewMode, false);
}

window.setRosterViewMode = function(mode, shouldRerender = true) {
    currentRosterViewMode = mode === "list" ? "list" : "grid";
    try {
        localStorage.setItem("roster_view_mode", currentRosterViewMode);
    } catch(e) {}

    // Sincroniza estado visual dos botões
    document.querySelectorAll(".view-mode-btn").forEach(btn => {
        if (btn.getAttribute("data-mode") === currentRosterViewMode) {
            btn.classList.add("active");
        } else {
            btn.classList.remove("active");
        }
    });

    // Atualiza classes CSS das galerias e dispara re-render imediato
    ["zzz", "genshin", "hsr"].forEach(g => {
        const gal = document.getElementById(`gallery-${g}`);
        if (gal) {
            if (currentRosterViewMode === "list") {
                gal.classList.add("list-view");
            } else {
                gal.classList.remove("list-view");
            }
        }
        if (shouldRerender && typeof _rosterRenderers[g] === "function") {
            _rosterRenderers[g]();
        }
    });
};

// ==========================================================================
// HELPERS DE EXTRAÇÃO PARA O MODO LISTA (OPÇÃO C: EQUILIBRADO / COMPLETO)
// ==========================================================================
const ROSTER_SET_STOPWORDS = new Set([
    'de', 'da', 'do', 'das', 'dos', 'no', 'na', 'nos', 'nas',
    'e', 'o', 'a', 'os', 'as', 'em', 'para', 'com', 'que', 'ao', 'aos', 'à', 'às'
]);

function extractRosterWeapon(char, gameId, isEn) {
    if (!char) return null;
    let weaponObj = null;
    if (char.weapon && typeof char.weapon === 'object') {
        weaponObj = { ...char.weapon };
    } else if (typeof char.weapon === 'string' && char.weapon.trim()) {
        weaponObj = { name: char.weapon.trim() };
    } else if (char.weapon_name) {
        weaponObj = {
            name: char.weapon_name,
            level: char.weapon_level,
            rank: char.weapon_rank,
            icon: char.weapon_icon,
            rarity: char.weapon_rarity
        };
    }
    if (!weaponObj || !weaponObj.name) return null;

    const name = weaponObj.name;
    const lvlPrefix = isEn ? 'Lv.' : 'Nv.';
    const levelStr = weaponObj.level ? `${lvlPrefix} ${weaponObj.level}` : '';

    // Prefixo de refinamento/sobreposição: S (HSR), W (ZZZ), R (Genshin)
    const rankPrefix = gameId === 'hsr' ? 'S' : (gameId === 'zzz' ? 'W' : 'R');
    const rawRank = weaponObj.rank !== undefined ? weaponObj.rank : (weaponObj.affix !== undefined ? weaponObj.affix : (weaponObj.refinement !== undefined ? weaponObj.refinement : null));
    const rankStr = (rawRank !== null && rawRank !== undefined && String(rawRank).trim() !== '') ? `${rankPrefix}${rawRank}` : '';

    let rarity = Number(weaponObj.rarity || (char && char.weapon_rarity)) || 0;
    if (!rarity || rarity <= 0) {
        rarity = 4;
    }

    const rarityBadge = gameId === 'zzz' ? (rarity === 5 ? 'Rank S' : (rarity === 3 ? 'Rank B' : 'Rank A')) : `${rarity}★`;
    const detailStr = [rarityBadge, rankStr, levelStr].filter(Boolean).join(' • ');

    let iconSrc = weaponObj.icon || '';
    if (iconSrc.startsWith('http://') || iconSrc.startsWith('https://')) {
        iconSrc = `/api/proxy_image?url=${encodeURIComponent(iconSrc)}&w=80&format=webp`;
    } else if (iconSrc.includes('/api/proxy_image?') && !iconSrc.includes('&w=')) {
        iconSrc = `${iconSrc}&w=80&format=webp`;
    }
    if (!iconSrc) {
        const safeWFn = typeof getSafeFileName === 'function' ? getSafeFileName(name) : name.replace(/[^a-zA-Z0-9_-]/g, '_');
        iconSrc = `/assets/weapons/${gameId}/${safeWFn}`;
    }

    const rarityClass = rarity === 5 ? 'rarity-5' : (rarity === 3 ? 'rarity-3' : (rarity === 1 ? 'rarity-1' : 'rarity-4'));

    return {
        name,
        detailStr,
        iconSrc,
        rarity,
        rarityClass
    };
}

function extractRosterKeyStats(char, gameId, isEn) {
    const stats = char && char.stats ? char.stats : null;
    if (!stats || typeof stats !== 'object' || Object.keys(stats).length === 0) {
        return null;
    }

    const keys = Object.keys(stats);
    const getVal = (patterns) => {
        for (const pat of patterns) {
            const pLower = pat.toLowerCase();
            for (const k of keys) {
                const kLower = k.toLowerCase();
                if (kLower === pLower || kLower.includes(pLower)) {
                    return { key: k, val: stats[k] };
                }
            }
        }
        return null;
    };

    const items = [];

    // 1. Taxa e Dano CRIT (CRIT Ratio)
    const critRate = getVal(['taxa crit', 'chance de crit', 'crit rate', 'taxa']);
    const critDmg = getVal(['dano crit', 'crit dmg', 'dano']);

    if (critRate && critDmg) {
        items.push({
            icon: '🎯',
            label: 'CRIT',
            value: `${critRate.val} / ${critDmg.val}`,
            highlight: true
        });
    } else if (critRate) {
        items.push({
            icon: '🎯',
            label: 'CRIT Rate',
            value: critRate.val,
            highlight: true
        });
    } else if (critDmg) {
        items.push({
            icon: '💥',
            label: 'CRIT DMG',
            value: critDmg.val,
            highlight: true
        });
    }

    // 2. Velocidade ou Impacto
    const spd = getVal(['vel', 'spd', 'velocidade']);
    const impact = getVal(['impactoo', 'impacto', 'impact']);

    if (spd) {
        items.push({
            icon: '⚡',
            label: 'VEL',
            value: spd.val,
            highlight: false
        });
    } else if (impact) {
        items.push({
            icon: '🔨',
            label: isEn ? 'Impact' : 'Impacto',
            value: impact.val,
            highlight: false
        });
    }

    // 3. Atributo de Escala Principal (Quebra, Anomalia, ATQ, PV, DEF ou Recarga)
    const breakEff = getVal(['quebra', 'break effect', 'break']);
    const anomaly = getVal(['prof. anomalia', 'anomaly prof', 'maest. anomalia', 'proficiência de anomalia']);
    const atk = getVal(['atq', 'atk', 'ataque']);
    const hp = getVal(['pv', 'hp', 'vida']);
    const def = getVal(['def', 'defesa']);
    const er = getVal(['recarga', 'recharge', 'recup. energia', 'regen. energia', 'er']);

    const cName = ((char && char.name) || '').toLowerCase();
    const isBreak = cName.includes('vaga-lume') || cName.includes('firefly') || cName.includes('boothill') || cName.includes('rappa');
    const isDefScaler = cName.includes('aventurine') || cName.includes('gepard') || cName.includes('noelle') || cName.includes('itto') || cName.includes('xilonen') || cName.includes('ben');
    const isHpScaler = cName.includes('blade') || cName.includes('fu xuan') || cName.includes('furina') || cName.includes('neuvillette') || cName.includes('hu tao') || cName.includes('hutao');
    const isAnomaly = anomaly !== null;

    let thirdStat = null;
    if (isBreak && breakEff) {
        thirdStat = { icon: '🌀', label: isEn ? 'Break' : 'Quebra', value: breakEff.val, highlight: true };
    } else if (isAnomaly && anomaly) {
        thirdStat = { icon: '🧪', label: isEn ? 'Anomaly' : 'Anomalia', value: anomaly.val, highlight: true };
    } else if (isDefScaler && def) {
        thirdStat = { icon: '🛡️', label: 'DEF', value: def.val, highlight: false };
    } else if (isHpScaler && hp) {
        thirdStat = { icon: '❤️', label: 'HP', value: hp.val, highlight: false };
    } else if (atk) {
        thirdStat = { icon: '⚔️', label: 'ATQ', value: atk.val, highlight: false };
    } else if (hp) {
        thirdStat = { icon: '❤️', label: 'HP', value: hp.val, highlight: false };
    } else if (def) {
        thirdStat = { icon: '🛡️', label: 'DEF', value: def.val, highlight: false };
    } else if (breakEff) {
        thirdStat = { icon: '🌀', label: isEn ? 'Break' : 'Quebra', value: breakEff.val, highlight: false };
    } else if (er) {
        thirdStat = { icon: '🔄', label: isEn ? 'Energy' : 'Recarga', value: er.val, highlight: false };
    }

    if (thirdStat) {
        items.push(thirdStat);
    }

    // Se ainda tiver menos de 3 status, completa com o primeiro status disponível que não foi usado
    if (items.length < 3) {
        for (const k of keys) {
            const kLower = k.toLowerCase();
            const alreadyUsed = items.some(it => it.label.toLowerCase() === kLower || kLower.includes(it.label.toLowerCase()));
            if (!alreadyUsed) {
                items.push({
                    icon: '📊',
                    label: k.length > 8 ? k.slice(0, 7) + '.' : k,
                    value: stats[k],
                    highlight: false
                });
                if (items.length >= 3) break;
            }
        }
    }

    return items.slice(0, 3);
}

function extractRosterSets(char, gameId, isEn) {
    const rawSets = [];

    // 1. Se char.sets já veio pronto
    if (Array.isArray(char.sets) && char.sets.length > 0) {
        char.sets.forEach(s => {
            if (typeof s === 'string' && s.trim()) {
                const mP = s.match(/^(.*?)\s*\((\d+)\s*(?:peças|pieces|pcs)\)$/i);
                if (mP) {
                    const count = Number(mP[2]);
                    const fullSetName = mP[1].trim();
                    if (count >= 2) {
                        rawSets.push(`${count}p ${fullSetName}`);
                    }
                } else {
                    const mCount = s.match(/^(\d+)p\s+(.*)$/i);
                    if (mCount) {
                        const count = Number(mCount[1]);
                        const fullSetName = mCount[2].trim();
                        if (count >= 2) {
                            rawSets.push(`${count}p ${fullSetName}`);
                        }
                    }
                }
            }
        });
    }

    // 2. Extração a partir das peças equipadas (se char.sets estiver vazio)
    const relics = char.relics || char.artifacts || char.discs || [];
    if (rawSets.length === 0 && relics.length > 0) {
        // A) Se as peças têm set_name preenchido diretamente
        const setCountMap = {};
        relics.forEach(r => {
            if (r && typeof r === 'object') {
                const sName = r.set_name || '';
                if (sName) {
                    setCountMap[sName] = (setCountMap[sName] || 0) + 1;
                }
            }
        });

        if (Object.keys(setCountMap).length > 0) {
            Object.entries(setCountMap)
                .sort((a, b) => b[1] - a[1])
                .forEach(([setName, count]) => {
                    if (count >= 4) rawSets.push(`4p ${setName}`);
                    else if (count >= 2) rawSets.push(`2p ${setName}`);
                });
        } else {
            // B) Formato ZZZ com índice entre colchetes: "Punk Hormonal [2]", "Techno Baiacu [1]"
            const names = relics.map(r => (typeof r === 'object' && r ? r.name || '' : String(r))).filter(Boolean);
            const discCounts = {};
            let isDisc = false;
            names.forEach(name => {
                const m = name.match(/^(.*?)\s*\[\d+\]$/);
                if (m) {
                    isDisc = true;
                    const setBase = m[1].trim();
                    discCounts[setBase] = (discCounts[setBase] || 0) + 1;
                }
            });

            if (isDisc) {
                Object.entries(discCounts)
                    .sort((a, b) => b[1] - a[1])
                    .forEach(([setName, count]) => {
                        if (count >= 4) rawSets.push(`4p ${setName}`);
                        else if (count >= 2) rawSets.push(`2p ${setName}`);
                    });
            }
        }
    }

    const eqCount = char.equipped_pieces !== undefined ? Number(char.equipped_pieces) : relics.length;
    const maxSlots = char.max_pieces !== undefined ? Number(char.max_pieces) : (gameId === 'genshin' ? 5 : 6);

    return {
        sets: rawSets.slice(0, 3),
        eqCount,
        maxSlots
    };
}

function extractRosterRelicPieces(char, gameId, isEn) {
    const relics = (char && (char.relics || char.artifacts || char.discs)) || [];
    const maxSlots = char && char.max_pieces !== undefined ? Number(char.max_pieces) : (gameId === 'genshin' ? 5 : 6);

    const pieces = [];
    for (let i = 0; i < maxSlots; i++) {
        if (i < relics.length && relics[i]) {
            const r = relics[i];
            const name = r.name || (isEn ? `Piece ${i + 1}` : `Peça ${i + 1}`);
            const slot = r.slot || String(i + 1);
            const main = r.main || r.main_stat || '';
            const sub = r.sub || r.sub_stats || '';
            const grade = r.grade || '';
            const rarity = Number(r.rarity) || 5;

            let iconSrc = r.icon || '';
            if (iconSrc.startsWith('http://') || iconSrc.startsWith('https://')) {
                iconSrc = `/api/proxy_image?url=${encodeURIComponent(iconSrc)}&w=64&format=webp`;
            } else if (iconSrc.includes('/api/proxy_image?') && !iconSrc.includes('&w=')) {
                iconSrc = `${iconSrc}&w=64&format=webp`;
            }

            const gradeClass = grade ? `grade-${grade.toLowerCase()}` : '';
            const rarityClass = rarity === 5 ? 'rarity-5' : (rarity === 4 ? 'rarity-4' : (rarity === 3 ? 'rarity-3' : (rarity === 1 ? 'rarity-1' : 'rarity-5')));

            const mainLabel = isEn ? 'Main' : 'Principal';
            const subLabel = isEn ? 'Sub' : 'Substatus';
            const gradeLabel = isEn ? 'Roll Value' : 'Avaliação';
            const starsStr = gameId === 'zzz' ? (rarity === 5 ? 'Rank S' : (rarity === 3 ? 'Rank B' : 'Rank A')) : '★'.repeat(rarity || 5);
            const tooltipParts = [
                `${starsStr} • ${slot ? slot + ': ' : ''}${name}`,
                main ? `${mainLabel}: ${main}` : '',
                sub ? `${subLabel}: ${sub}` : '',
                grade ? `${gradeLabel}: ${grade}` : ''
            ].filter(Boolean);

            pieces.push({
                isEquipped: true,
                name,
                slot,
                iconSrc,
                grade,
                gradeClass,
                rarity,
                rarityClass,
                tooltip: tooltipParts.join('\n')
            });
        } else {
            pieces.push({
                isEquipped: false,
                slotNum: i + 1,
                gradeClass: 'slot-empty',
                rarityClass: 'slot-empty',
                tooltip: isEn ? `Slot ${i + 1}: Not equipped` : `Slot ${i + 1}: Não equipado`
            });
        }
    }

    return {
        pieces,
        totalEquipped: relics.length,
        maxSlots
    };
}

if (typeof window !== 'undefined') {
    window.extractRosterWeapon = extractRosterWeapon;
    window.extractRosterKeyStats = extractRosterKeyStats;
    window.extractRosterSets = extractRosterSets;
    window.extractRosterRelicPieces = extractRosterRelicPieces;
}

// Deduplica requisições simultâneas de roster (startup + alternância rápida de abas)
const _rosterInflight = {};
const _rosterFilterActions = {};
const _dirtyRosterLang = {};
window._flushDirtyRosterLang = function(gameId) {
    if (_dirtyRosterLang[gameId] && typeof _rosterRenderers[gameId] === "function") {
        _dirtyRosterLang[gameId] = false;
        if (gameId === "hsr") {
            const allOpt = document.querySelector('#planar-filter-hsr option[value="all"]');
            if (allOpt) allOpt.textContent = window.isEn ? "All Planar Ornaments" : "Todos os Ornamentos Planares";
        }
        _rosterRenderers[gameId]();
    }
};
function loadRoster(gameId) {
    if (_rosterInflight[gameId]) return _rosterInflight[gameId];
    _rosterInflight[gameId] = _loadRosterImpl(gameId).finally(() => {
        _rosterInflight[gameId] = null;
    });
    return _rosterInflight[gameId];
}

async function _loadRosterImpl(gameId) {
    const gallery = document.getElementById(`gallery-${gameId}`);
    if (currentRosterViewMode === "list") {
        gallery.classList.add("list-view");
        gallery.innerHTML = Array(8).fill(0).map(() => `
            <div class="skeleton-row" style="height: 76px; padding: 10px 18px; border-radius: 12px; display: flex; align-items: center; justify-content: space-between; gap: 16px;">
                <div style="display: flex; align-items: center; gap: 14px; flex: 1.2;">
                    <div class="skeleton-box" style="width: 48px; height: 48px; border-radius: 10px;"></div>
                    <div style="display: flex; flex-direction: column; gap: 6px; width: 60%;">
                        <div class="skeleton-line" style="width: 70%; height: 14px;"></div>
                        <div class="skeleton-line" style="width: 40%; height: 10px;"></div>
                    </div>
                </div>
                <div class="skeleton-box" style="width: 140px; height: 38px; border-radius: 8px;"></div>
                <div class="skeleton-box" style="width: 120px; height: 28px; border-radius: 6px;"></div>
                <div class="skeleton-box" style="width: 70px; height: 28px; border-radius: 6px;"></div>
            </div>
        `).join('');
    } else {
        gallery.classList.remove("list-view");
        gallery.innerHTML = Array(12).fill(0).map(() => `
            <div class="skeleton-card">
                <div class="skeleton-avatar-container">
                    <div class="skeleton-badge"></div>
                    <div class="skeleton-avatar"></div>
                </div>
                <div class="skeleton-info">
                    <div class="skeleton-name"></div>
                    <div class="skeleton-lvl"></div>
                </div>
            </div>
        `).join('');
    }
    
    try {
        const res = await fetch(`/api/roster/${gameId}`);
        const roster = await res.json();
        
        // Garante preenchimento de path (HSR) e weapon_type (Genshin) mesmo sob cache local antigo
        if (Array.isArray(roster)) {
            roster.forEach(char => {
                if (gameId === 'hsr' && !char.path) char.path = getCharacterPath(char);
                if (gameId === 'genshin' && !char.weapon_type) char.weapon_type = getCharacterWeapon(char);
            });
        }
        
        // Salva no estado global e atualiza os gráficos SVG e endgame
        globalRoster[gameId] = roster || [];
        // Renderiza só os gráficos deste jogo (antes redesenhava os 3 jogos a cada roster carregado)
        if (typeof window.renderGameCharts === "function") window.renderGameCharts(gameId);
        loadEndgame(gameId);
        // Só monta o construtor de time se a subview estiver visível; ao abrir a aba ele é renderizado sob demanda
        const teamView = document.getElementById(`view-teamcard-${gameId}`);
        if (window.renderTeamBuilderView && teamView && teamView.classList.contains("active")) {
            window.renderTeamBuilderView(gameId);
        }
        
        if (!roster || roster.length === 0) {
            const gameNames = { hsr: "Honkai: Star Rail", genshin: "Genshin Impact", zzz: "Zenless Zone Zero" };
            const gName = gameNames[gameId] || gameId.toUpperCase();
            const emptyTitle = isEn 
                ? `${gName} Character Gallery` 
                : `Galeria de Personagens de ${gName}`;
            const emptyDesc = isEn
                ? `This is where you view all your account characters, ascension levels, constellations/mindscapes, and Roll Value gear scores.`
                : `Esta é a tela onde você visualiza todos os personagens da sua conta, níveis de ascensão, constelações e notas matemáticas de Roll Value dos equipamentos.`;
            const emptyBtnText = isEn
                ? `Sync ${gName} Characters Now`
                : `Sincronizar Personagens de ${gName} Agora`;

            gallery.innerHTML = `
                <div class="empty-state-box" style="grid-column: 1 / -1; padding: 48px 24px; text-align: center; background: rgba(15, 23, 42, 0.6); border: 1px dashed rgba(255, 255, 255, 0.15); border-radius: 16px; margin: 16px 0;">
                    <div style="width: 56px; height: 56px; border-radius: 50%; background: rgba(56, 189, 248, 0.15); display: inline-flex; align-items: center; justify-content: center; margin-bottom: 16px; color: #38bdf8; font-size: 24px;">
                        <i class="fa-solid fa-users"></i>
                    </div>
                    <h3 style="color: var(--text-primary); font-size: 18px; font-weight: 700; margin-bottom: 8px;">${emptyTitle}</h3>
                    <p style="color: var(--text-secondary); font-size: 13px; max-width: 480px; margin: 0 auto 20px auto; line-height: 1.5;">${emptyDesc}</p>
                    <sakuga-button class="sk-sm" onclick="const btn = document.querySelector('.sync-game-btn[data-game=\\'${gameId}\\']'); if (btn) btn.click(); else window.loadRoster('${gameId}');">
                        <i class="fa-solid fa-arrows-rotate"></i> ${emptyBtnText}
                    </sakuga-button>
                </div>
            `;
            return;
        }
        
        gallery.innerHTML = ""; // Limpa spinner
        
        // Estado dos filtros combinados e ordenação inteligente
        let activeSort = "default";
        let activeElementFilter = "all";
        let activeRarityFilter = "all";
        let activePathFilter = "all";
        let activeWeaponFilter = "all";
        let searchQuery = "";

        // Filtros de Auditoria Universais
        let activeSetFilter = "all";
        let activeSlotFilter = "all";
        let activeGradeFilter = "all";
        let activeWeaponStatusFilter = "all";

        // Filtros de Auditoria Específicos por Jogo
        let activeRegionFilter = "all";
        let activeMechanicFilter = "all";
        let activeScaleFilter = "all";
        let activeMainStatFilter = "all";

        let activeSpeedFilter = "all";
        let activePlanarFilter = "all";

        let activeSpecialtyFilter = "all";
        let activeFactionFilter = "all";
        let activeArchetypeFilter = "all";
        let activeDiscsMainFilter = "all";

        // Preenche o seletor de ornamentos planares para HSR
        if (gameId === "hsr") {
            const planarSelect = document.getElementById("planar-filter-hsr");
            if (planarSelect) {
                const setsSet = new Set();
                roster.forEach(c => {
                    (c.relics || []).forEach(r => {
                        const slot = String(r.slot || "").toLowerCase();
                        if (slot.includes("esfera") || slot.includes("corda") || slot === "5" || slot === "6") {
                            if (r.set_name) setsSet.add(r.set_name);
                        }
                    });
                });
                const currentVal = planarSelect.value || "all";
                const allLabel = isEn ? "All Planar Ornaments" : "Todos os Ornamentos Planares";
                let optsHtml = `<option value="all">${allLabel}</option>`;
                Array.from(setsSet).sort().forEach(setName => {
                    optsHtml += `<option value="${setName}">${setName}</option>`;
                });
                planarSelect.innerHTML = optsHtml;
                if (setsSet.has(currentVal)) planarSelect.value = currentVal;
            }
        }
        
        const searchInput = document.querySelector(`.search-input[data-game="${gameId}"]`);
        
        const renderCards = () => {
            gallery.innerHTML = "";
            if (currentRosterViewMode === "list") {
                gallery.classList.add("list-view");
            } else {
                gallery.classList.remove("list-view");
            }
            const frag = document.createDocumentFragment();

            const lvlLabel = isEn ? "Level" : "Nível";
            
            // 1. Aplica todos os filtros combinados (Universais + Específicos)
            const filtered = roster.filter(char => {
                // A) Busca textual
                const matchesSearch = char.name.toLowerCase().includes(searchQuery) || (typeof formatCharacterName === 'function' && formatCharacterName(char.name).toLowerCase().includes(searchQuery));
                
                // B) Elemento
                const charElemLower = (char.element || "").toLowerCase();
                const filterLower = activeElementFilter.toLowerCase();
                const isLumifluxMatch = filterLower === "lumiflux" && (charElemLower === "lumiflux" || charElemLower === "element_300" || charElemLower === "element 300");
                const matchesElement = activeElementFilter === "all" || charElemLower === filterLower || isLumifluxMatch;
                
                // C) Raridade
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
                
                // D) Caminho (HSR)
                let matchesPath = true;
                if (gameId === "hsr" && activePathFilter !== "all") {
                    const charPath = String(char.path || getCharacterPath(char) || "").toLowerCase();
                    const pLower = activePathFilter.toLowerCase();
                    if (pLower === "destruction") matchesPath = charPath.includes("destruc") || charPath.includes("destrui");
                    else if (pLower === "hunt") matchesPath = charPath.includes("hunt") || charPath.includes("caça") || charPath.includes("caca");
                    else if (pLower === "erudition") matchesPath = charPath.includes("erudi");
                    else if (pLower === "harmony") matchesPath = charPath.includes("harmon");
                    else if (pLower === "nihility") matchesPath = charPath.includes("nihil") || charPath.includes("inexist");
                    else if (pLower === "preservation") matchesPath = charPath.includes("preserv");
                    else if (pLower === "abundance") matchesPath = charPath.includes("abund");
                    else if (pLower === "remembrance") matchesPath = charPath.includes("remembr") || charPath.includes("recorda") || charPath.includes("reminisc");
                    else if (pLower === "elation") matchesPath = charPath.includes("elat") || charPath.includes("eufor") || charPath.includes("júbil") || charPath.includes("jubil");
                    else matchesPath = charPath === pLower;
                }

                // E) Arma (Genshin)
                let matchesWeapon = true;
                if (gameId === "genshin" && activeWeaponFilter !== "all") {
                    const charWeapon = String(char.weapon_type || getCharacterWeapon(char) || char.path || "").toLowerCase();
                    const wLower = activeWeaponFilter.toLowerCase();
                    if (wLower === "sword") matchesWeapon = (charWeapon.includes("sword") || charWeapon.includes("espada")) && !charWeapon.includes("espadão") && !charWeapon.includes("espadao");
                    else if (wLower === "claymore") matchesWeapon = charWeapon.includes("claymore") || charWeapon.includes("espadão") || charWeapon.includes("espadao");
                    else if (wLower === "polearm") matchesWeapon = charWeapon.includes("polearm") || charWeapon.includes("lança") || charWeapon.includes("lanca") || charWeapon.includes("spear");
                    else if (wLower === "bow") matchesWeapon = charWeapon.includes("bow") || charWeapon.includes("arco");
                    else if (wLower === "catalyst") matchesWeapon = charWeapon.includes("catalyst") || charWeapon.includes("catalisador");
                    else matchesWeapon = charWeapon === wLower;
                }

                // F) Integridade do Set (4p, 2p+2p, Sem Bônus/Quebrado)
                let matchesSet = true;
                if (activeSetFilter !== "all") {
                    matchesSet = getCharacterSetIntegrity(char) === activeSetFilter;
                }

                // G) Slots Incompletos / Completos
                let matchesSlots = true;
                if (activeSlotFilter !== "all") {
                    const maxSlots = char.max_pieces || (gameId === "genshin" ? 5 : 6);
                    const eqCount = char.equipped_pieces !== undefined ? char.equipped_pieces : (char.relics || char.artifacts || char.discs || []).length;
                    if (activeSlotFilter === "incomplete") matchesSlots = eqCount < maxSlots;
                    else if (activeSlotFilter === "complete") matchesSlots = eqCount >= maxSlots;
                }

                // H) Faixa de Rank da Build (SSS/SS, S, A, B, C/D)
                let matchesGrade = true;
                if (activeGradeFilter !== "all") {
                    const grade = (char.overall_grade || "").toUpperCase();
                    if (activeGradeFilter === "top") matchesGrade = ["SSS", "SS"].includes(grade);
                    else if (activeGradeFilter === "s") matchesGrade = grade === "S";
                    else if (activeGradeFilter === "a") matchesGrade = grade === "A";
                    else if (activeGradeFilter === "b") matchesGrade = grade === "B";
                    else if (activeGradeFilter === "cd") matchesGrade = ["C", "D"].includes(grade);
                }

                // I) Status da Arma / Cone / Motor-W
                let matchesWeaponStatus = true;
                if (activeWeaponStatusFilter !== "all") {
                    const w = char.weapon && typeof char.weapon === 'object' ? char.weapon : {
                        name: char.weapon_name, level: char.weapon_level, rank: char.weapon_rank, rarity: char.weapon_rarity
                    };
                    const wRarity = Number(w.rarity || char.weapon_rarity || 4);
                    const wLevel = Number(w.level || char.weapon_level || 1);
                    const rawRank = w.rank !== undefined ? w.rank : (w.affix !== undefined ? w.affix : (w.refinement !== undefined ? w.refinement : 1));
                    const wRank = Number(rawRank) || 1;
                    const maxGameLvl = gameId === "genshin" ? 90 : (gameId === "hsr" ? 80 : 60);

                    if (activeWeaponStatusFilter === "w5") matchesWeaponStatus = wRarity === 5;
                    else if (activeWeaponStatusFilter === "w4") matchesWeaponStatus = wRarity === 4;
                    else if (activeWeaponStatusFilter === "wr5") matchesWeaponStatus = wRank >= 5;
                    else if (activeWeaponStatusFilter === "wr1") matchesWeaponStatus = wRank === 1;
                    else if (activeWeaponStatusFilter === "w_underleveled") matchesWeaponStatus = wLevel < maxGameLvl;
                    else if (activeWeaponStatusFilter === "w_max") matchesWeaponStatus = wLevel >= maxGameLvl;
                }

                // J) Filtros Específicos: Genshin
                let matchesRegion = true;
                if (gameId === "genshin" && activeRegionFilter !== "all") {
                    matchesRegion = getGenshinCharacterRegion(char.name) === activeRegionFilter;
                }

                let matchesMechanic = true;
                if (gameId === "genshin" && activeMechanicFilter !== "all") {
                    const cleanN = char.name.toLowerCase().trim().replace(/_/g, " ");
                    if (activeMechanicFilter === "nightsoul") matchesMechanic = GENSHIN_NIGHTSOUL_CHARS.has(cleanN) || getGenshinCharacterRegion(cleanN) === "natlan";
                    else if (activeMechanicFilter === "pneuma") matchesMechanic = GENSHIN_PNEUMA_CHARS.has(cleanN);
                    else if (activeMechanicFilter === "ousia") matchesMechanic = GENSHIN_OUSIA_CHARS.has(cleanN);
                }

                let matchesScale = true;
                if (gameId === "genshin" && activeScaleFilter !== "all") {
                    matchesScale = matchGenshinScale(char, activeScaleFilter);
                }

                let matchesMainStat = true;
                if (gameId === "genshin" && activeMainStatFilter !== "all") {
                    matchesMainStat = matchGenshinMainStat(char, activeMainStatFilter);
                }

                // K) Filtros Específicos: HSR
                let matchesSpeed = true;
                if (gameId === "hsr" && activeSpeedFilter !== "all") {
                    const spd = parseInt(char.stats?.VEL || char.stats?.Velocidade || char.stats?.SPD || 0, 10);
                    if (activeSpeedFilter === "base") matchesSpeed = spd > 0 && spd < 134;
                    else if (activeSpeedFilter === "134") matchesSpeed = spd >= 134;
                    else if (activeSpeedFilter === "143") matchesSpeed = spd >= 143;
                    else if (activeSpeedFilter === "160") matchesSpeed = spd >= 160;
                }

                let matchesPlanar = true;
                if (gameId === "hsr" && activePlanarFilter !== "all") {
                    const relics = char.relics || [];
                    matchesPlanar = relics.some(r => {
                        const slot = String(r.slot || "").toLowerCase();
                        const isPlanarSlot = slot.includes("esfera") || slot.includes("corda") || slot === "5" || slot === "6";
                        return isPlanarSlot && (r.set_name || "").toLowerCase() === activePlanarFilter.toLowerCase();
                    });
                }

                // L) Filtros Específicos: ZZZ
                let matchesSpecialty = true;
                if (gameId === "zzz" && activeSpecialtyFilter !== "all") {
                    const specAliases = {
                        attack: ["attack", "ataque"],
                        stun: ["stun", "atordoamento"],
                        anomaly: ["anomaly", "anomalia"],
                        support: ["support", "suporte"],
                        defense: ["defense", "defesa", "defence"],
                        rupture: ["rupture", "ruptura"],
                        armorer: ["armorer", "armeiro"],
                    };
                    const spec = String(char.specialty || char.role || char.path || "").trim().toLowerCase();
                    const filterKey = activeSpecialtyFilter.toLowerCase();
                    const candidates = specAliases[filterKey] || [filterKey];
                    matchesSpecialty = candidates.some(alias => spec.includes(alias));
                }

                let matchesFaction = true;
                if (gameId === "zzz" && activeFactionFilter !== "all") {
                    matchesFaction = matchZZZFaction(char.name, activeFactionFilter);
                }

                let matchesArchetype = true;
                if (gameId === "zzz" && activeArchetypeFilter !== "all") {
                    matchesArchetype = matchZZZArchetype(char, activeArchetypeFilter);
                }

                let matchesDiscsMain = true;
                if (gameId === "zzz" && activeDiscsMainFilter !== "all") {
                    matchesDiscsMain = matchZZZDiscsMain(char, activeDiscsMainFilter);
                }
                
                return matchesSearch && matchesElement && matchesRarity && matchesPath && matchesWeapon &&
                       matchesSet && matchesSlots && matchesGrade && matchesWeaponStatus &&
                       matchesRegion && matchesMechanic && matchesScale && matchesMainStat &&
                       matchesSpeed && matchesPlanar && matchesSpecialty && matchesFaction &&
                       matchesArchetype && matchesDiscsMain;
            });

            // 2. Aplica Ordenação Inteligente
            const sorted = sortCharacters(filtered, activeSort);

            // 3. Atualiza Contador de Resultados em Tempo Real
            const counterEl = document.getElementById(`roster-counter-${gameId}`);
            if (counterEl) {
                const numEl = counterEl.querySelector(".counter-num");
                const totalEl = counterEl.querySelector(".counter-total");
                if (numEl) numEl.textContent = sorted.length;
                if (totalEl) totalEl.textContent = roster.length;
                if (sorted.length !== roster.length) {
                    counterEl.classList.add("has-filter");
                } else {
                    counterEl.classList.remove("has-filter");
                }
            }

            // 4. Atualiza Visibilidade do Botão "Limpar Filtros"
            const clearBtn = document.querySelector(`.btn-clear-filters[data-game="${gameId}"]`);
            const hasAnyActiveFilter = searchQuery !== "" ||
                activeElementFilter !== "all" ||
                activeRarityFilter !== "all" ||
                activePathFilter !== "all" ||
                activeWeaponFilter !== "all" ||
                activeSort !== "default" ||
                activeSetFilter !== "all" ||
                activeSlotFilter !== "all" ||
                activeGradeFilter !== "all" ||
                activeWeaponStatusFilter !== "all" ||
                activeRegionFilter !== "all" ||
                activeMechanicFilter !== "all" ||
                activeScaleFilter !== "all" ||
                activeMainStatFilter !== "all" ||
                activeSpeedFilter !== "all" ||
                activePlanarFilter !== "all" ||
                activeSpecialtyFilter !== "all" ||
                activeFactionFilter !== "all" ||
                activeArchetypeFilter !== "all" ||
                activeDiscsMainFilter !== "all";

            if (clearBtn) {
                clearBtn.style.display = hasAnyActiveFilter ? "inline-flex" : "none";
            }

            // 5. Atualiza Badge no Botão "Auditoria"
            const auditBadge = document.getElementById(`audit-badge-${gameId}`);
            let auditCount = 0;
            if (activeSetFilter !== "all") auditCount++;
            if (activeSlotFilter !== "all") auditCount++;
            if (activeGradeFilter !== "all") auditCount++;
            if (activeWeaponStatusFilter !== "all") auditCount++;
            if (activeRegionFilter !== "all") auditCount++;
            if (activeMechanicFilter !== "all") auditCount++;
            if (activeScaleFilter !== "all") auditCount++;
            if (activeMainStatFilter !== "all") auditCount++;
            if (activeSpeedFilter !== "all") auditCount++;
            if (activePlanarFilter !== "all") auditCount++;
            if (activeSpecialtyFilter !== "all") auditCount++;
            if (activeFactionFilter !== "all") auditCount++;
            if (activeArchetypeFilter !== "all") auditCount++;
            if (activeDiscsMainFilter !== "all") auditCount++;

            if (auditBadge) {
                if (auditCount > 0) {
                    auditBadge.textContent = auditCount;
                    auditBadge.style.display = "inline-flex";
                } else {
                    auditBadge.style.display = "none";
                }
            }
            
            if (sorted.length === 0) {
                const noMatchText = window.t ? window.t("roster_no_filter_match", "Nenhum personagem encontrado com os filtros ativos.") : "Nenhum personagem encontrado com os filtros ativos.";
                const clearText = window.t ? window.t("btn_clear_filters", "Limpar Filtros") : "Limpar Filtros";
                gallery.innerHTML = `
                    <div class="empty-gallery" style="grid-column: 1 / -1; padding: 40px 0; text-align: center;">
                        <p style="color: var(--text-secondary); margin-bottom: 14px;">${noMatchText}</p>
                        <sakuga-button class="sk-sm" onclick="window.clearRosterFilters('${gameId}')">
                            <i class="fa-solid fa-filter-circle-xmark"></i> ${clearText}
                        </sakuga-button>
                    </div>
                `;
                return;
            }
            
            sorted.forEach(char => {
                const card = document.createElement("div");
                
                // Normaliza o elemento para a classe CSS de borda colorida
                const elemKey = (char.element || "").toLowerCase();
                const elemClass = ELEMENT_MAPPING[elemKey] || "el-physical";
                
                // Identifica se o personagem está no time ativo
                const currentTeam = (typeof teamBuilderState !== "undefined" && teamBuilderState[gameId]) ? teamBuilderState[gameId].members : [];
                const teamPos = currentTeam.findIndex(m => m.name === char.name);
                const inTeamClass = teamPos !== -1 ? " in-team-selected" : "";
                
                const safeFn = getSafeFileName(char.name);
                const defaultFallback = `/assets/${gameId}_icon.png`;
                let avatarSrc = char.icon || defaultFallback;
                if (avatarSrc.startsWith("http://") || avatarSrc.startsWith("https://")) {
                    avatarSrc = `/api/proxy_image?url=${encodeURIComponent(avatarSrc)}&w=160&format=webp`;
                } else if (avatarSrc.includes("/api/proxy_image?") && !avatarSrc.includes("&w=")) {
                    avatarSrc = `${avatarSrc}&w=160&format=webp`;
                }

                const formattedName = typeof formatCharacterName === 'function' ? formatCharacterName(char.name) : char.name;
                const affEid = window.getUnlockedAffinitiveEidolon ? window.getUnlockedAffinitiveEidolon(char) : null;
                const affTitleAttr = affEid ? String(affEid.name || "Affinitive Eidolon").replace(/"/g, "&quot;") : "";

                let pathOrWeaponLabel = "";
                let rawPathOrWeapon = "";
                if (gameId === "hsr") {
                    rawPathOrWeapon = char.path || getCharacterPath(char) || "";
                    pathOrWeaponLabel = typeof formatPathName === "function" ? formatPathName(rawPathOrWeapon, "hsr") : rawPathOrWeapon;
                } else if (gameId === "genshin") {
                    rawPathOrWeapon = char.weapon_type || getCharacterWeapon(char) || "";
                    const wKey = String(rawPathOrWeapon || "").trim().toLowerCase();
                    pathOrWeaponLabel = (wKey && typeof window.t === "function") ? window.t(`weapon_${wKey}`, rawPathOrWeapon) : rawPathOrWeapon;
                } else if (gameId === "zzz") {
                    rawPathOrWeapon = char.specialty || char.role || "";
                    pathOrWeaponLabel = typeof formatPathName === "function" ? formatPathName(rawPathOrWeapon, "zzz") : rawPathOrWeapon;
                }

                if (currentRosterViewMode === "list") {
                    card.className = `char-card char-list-row ${elemClass}${inTeamClass}`;

                    const rarityNum = Number(char.rarity);
                    const isFiveStar = rarityNum === 5 || char.rarity === "5" || String(char.rarity).toUpperCase() === "S";
                    const elemDisplayName = typeof formatElementDisplayName === "function" ? formatElementDisplayName(char.element) : (char.element || "");
                    const listRoleBadgeHtml = (rawPathOrWeapon || pathOrWeaponLabel)
                        ? (typeof renderRoleIconBadge === "function"
                            ? renderRoleIconBadge(gameId, rawPathOrWeapon, pathOrWeaponLabel, { size: 14, className: "char-role-pill", title: pathOrWeaponLabel })
                            : `<span class="char-role-pill">${pathOrWeaponLabel}</span>`)
                        : "";

                    const rarityLabel = isFiveStar ? (gameId === 'zzz' ? 'Rank S' : '5★') : (gameId === 'zzz' ? 'Rank A' : '4★');

                    const weaponData = extractRosterWeapon(char, gameId, isEn);
                    const relicPiecesData = extractRosterRelicPieces(char, gameId, isEn);
                    const setsData = extractRosterSets(char, gameId, isEn);

                    let dotsHtml = '';
                    for (let i = 0; i < setsData.maxSlots; i++) {
                        dotsHtml += `<span class="char-relic-dot${i < setsData.eqCount ? ' filled' : ''}"></span>`;
                    }

                    const rawGrade = char.overall_grade || (setsData.eqCount === 0 ? "N/A" : "B");
                    const isUnequipped = rawGrade === "N/A" || setsData.eqCount === 0;
                    const gradeBadgeClass = isUnequipped ? "badge-na" : `badge-${rawGrade.toLowerCase()}`;
                    const gradeScore = char.overall_score !== undefined ? char.overall_score : null;

                    card.innerHTML = `
                        <!-- Coluna 1: Personagem -->
                        <div class="char-list-col-main">
                            <div class="char-list-avatar-wrap">
                                <img class="char-list-avatar" src="${avatarSrc}" width="48" height="48" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='${defaultFallback}';" alt="${char.name}">
                                <div class="char-list-rank-chip">${char.rank_str || 'C0'}</div>
                            </div>
                            <div class="char-list-info">
                                <div class="char-list-title-row">
                                    <span class="char-list-name" title="${formattedName}">${formattedName}</span>
                                    <span class="char-list-elem-tag">
                                        <img src="${getElementIconUrl(gameId, char.element || elemKey)}" width="14" height="14" loading="lazy" decoding="async" onerror="this.style.display='none';" alt="">
                                        ${elemDisplayName}
                                    </span>
                                    <span class="char-list-rarity-badge ${isFiveStar ? 'five-star' : 'four-star'}">${rarityLabel}</span>
                                    ${affEid ? `<span class="char-list-affinitive-pill" title="Affinitive Eidolon: ${affTitleAttr}">✦ Affinitive</span>` : ''}
                                    ${teamPos !== -1 ? `<span class="char-list-badge-team"><i class="fa-solid fa-users"></i> #${teamPos + 1}</span>` : ''}
                                </div>
                                <div class="char-list-details-row">
                                    <span class="char-list-badge-lvl">${lvlLabel} ${char.level}</span>
                                    ${listRoleBadgeHtml}
                                </div>
                            </div>
                        </div>

                        <!-- Coluna 2: Arma com Thumbnail Oficial -->
                        <div class="char-list-col-weapon">
                            ${weaponData ? `
                                <div class="char-list-weapon-wrap">
                                    <div class="char-list-weapon-icon-box ${weaponData.rarityClass}">
                                        <img src="${weaponData.iconSrc}" width="38" height="38" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='/assets/chat_icon.png';" alt="${weaponData.name}">
                                    </div>
                                    <div class="char-list-weapon-text">
                                        <div class="char-list-weapon-name" title="${weaponData.name}">${weaponData.name}</div>
                                        <div class="char-list-weapon-detail">${weaponData.detailStr || (isEn ? 'Equipped' : 'Equipada')}</div>
                                    </div>
                                </div>
                            ` : `
                                <div class="char-list-weapon-empty">
                                    <i class="fa-solid fa-shield-halved"></i>
                                    <span>${isEn ? 'No weapon noted' : 'Sem arma anotada'}</span>
                                </div>
                            `}
                        </div>

                        <!-- Coluna 3: Relíquias / Artefatos / Discos (Ícones Oficiais das Peças Equipadas) -->
                        <div class="char-list-col-relics" title="${relicPiecesData.totalEquipped}/${relicPiecesData.maxSlots} ${isEn ? 'pieces equipped' : 'peças equipadas'}">
                            <div class="char-relics-strip">
                                ${relicPiecesData.pieces.map((p, pIdx) => p.isEquipped ? `
                                    <div class="char-relic-piece-box ${p.rarityClass} ${p.gradeClass}" title="${p.tooltip}">
                                        <img src="${p.iconSrc}" width="34" height="34" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='/assets/chat_icon.png';" alt="${p.name}">
                                        ${p.grade && p.grade !== 'N/A' ? `<span class="piece-corner-grade piece-grade-${p.grade.toLowerCase()}">${p.grade}</span>` : ''}
                                    </div>
                                ` : `
                                    <div class="char-relic-piece-box slot-empty" title="${p.tooltip}">
                                        <span class="slot-empty-num">${p.slotNum || (pIdx + 1)}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>

                        <!-- Coluna 4: Conjuntos de Relíquias e Peças Equipadas -->
                        <div class="char-list-col-sets">
                            <div class="char-sets-tags">
                                ${setsData.sets && setsData.sets.length > 0 ? `
                                    ${setsData.sets.map(s => `
                                        <span class="char-set-tag" title="${s}">
                                            <i class="fa-solid fa-wand-magic-sparkles"></i> ${s}
                                        </span>
                                    `).join('')}
                                ` : `
                                    <span class="char-set-tag set-empty">
                                        <i class="fa-solid fa-layer-group"></i> ${isEn ? 'Individual pieces' : 'Peças avulsas'}
                                    </span>
                                `}
                            </div>
                            <div class="char-relic-slots-bar" title="${setsData.eqCount}/${setsData.maxSlots} ${isEn ? 'pieces equipped' : 'peças equipadas'}">
                                <div class="char-relic-dots">
                                    ${dotsHtml}
                                </div>
                                <span class="char-relic-slots-text">${setsData.eqCount}/${setsData.maxSlots} ${isEn ? 'Equipped' : 'Peças'}</span>
                            </div>
                        </div>

                        <!-- Coluna 5: Grade Roll Value e Ação -->
                        <div class="char-list-col-actions">
                            <div class="char-list-grade-wrap">
                                <span class="char-grade-badge ${gradeBadgeClass}">
                                    ${rawGrade}
                                </span>
                                ${gradeScore !== null ? `<span class="char-list-score-sub">${gradeScore} pts</span>` : ''}
                            </div>
                            <div class="char-list-btn-inspect" title="${isEn ? 'Inspect character' : 'Inspecionar personagem'}">
                                <span class="char-list-inspect-label">${isEn ? 'Inspect' : 'Inspecionar'}</span>
                                <i class="fa-solid fa-chevron-right char-list-chevron"></i>
                            </div>
                        </div>
                    `;
                } else {
                    const gridRoleBadgeHtml = (rawPathOrWeapon || pathOrWeaponLabel)
                        ? (typeof renderRoleIconBadge === "function"
                            ? renderRoleIconBadge(gameId, rawPathOrWeapon, pathOrWeaponLabel, { size: 12, className: "char-role-chip", title: pathOrWeaponLabel })
                            : `<span class="char-role-chip">${pathOrWeaponLabel}</span>`)
                        : "";
                    card.className = `char-card ${elemClass}${inTeamClass}`;
                    card.innerHTML = `
                        <div class="char-avatar-container">
                            ${teamPos !== -1 ? `<div class="gallery-team-badge"><i class="fa-solid fa-users"></i> #${teamPos + 1}</div>` : ''}
                            ${char.overall_grade ? `<div class="char-grade-badge badge-${char.overall_grade.toLowerCase()}">${char.overall_grade}</div>` : ''}
                            <img class="char-avatar" src="${avatarSrc}" width="68" height="68" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='${defaultFallback}';" alt="${char.name}">
                            <div class="char-rank-badge">${char.rank_str || 'C0'}</div>
                            ${affEid ? `<div class="char-affinitive-badge" title="Affinitive Eidolon: ${affTitleAttr}">✦ AE</div>` : ''}
                        </div>

                        <div class="char-info">
                            <div class="char-name" title="${formattedName}">
                                <img src="${getElementIconUrl(gameId, char.element || elemKey)}" class="element-icon-inline" width="16" height="16" loading="lazy" decoding="async" onerror="this.style.display='none';" alt="">
                                ${formattedName}
                            </div>
                            <div class="char-meta-row">
                                <span class="char-lvl">${lvlLabel} ${char.level}</span>
                                ${gridRoleBadgeHtml}
                            </div>
                        </div>
                    `;
                }
                
                // Clique para abrir detalhes no Build Inspector lateral
                card.addEventListener("click", () => {
                    inspectCharacter(gameId, char);
                });
                
                frag.appendChild(card);
            });
            // Um único reflow em vez de um por personagem
            gallery.appendChild(frag);
        };
        
        _rosterRenderers[gameId] = renderCards;

        const syncSpecialtyUI = (val) => {
            const specContainer = document.querySelector(`.specialty-filters[data-game="${gameId}"]`);
            if (specContainer) {
                specContainer.querySelectorAll(".filter-btn").forEach(b => {
                    b.classList.toggle("active", (b.getAttribute("data-specialty") || "all") === val);
                });
            }
            const specAuditGroup = document.querySelector(`#audit-panel-${gameId} .filter-pills[data-filter-type="specialty"]`);
            if (specAuditGroup) {
                specAuditGroup.querySelectorAll(".audit-pill").forEach(p => {
                    p.classList.toggle("active", (p.getAttribute("data-val") || "all") === val);
                });
            }
        };

        const filterContainer = document.querySelector(`.element-filters[data-game="${gameId}"]:not(.rarity-filters):not(.weapon-filters):not(.path-filters):not(.specialty-filters)`);
        const rarityContainer = document.querySelector(`.rarity-filters[data-game="${gameId}"]`);
        const pathContainer = document.querySelector(`.path-filters[data-game="${gameId}"]`);
        const weaponContainer = document.querySelector(`.weapon-filters[data-game="${gameId}"]`);
        const specialtyContainer = document.querySelector(`.specialty-filters[data-game="${gameId}"]`);
        const sortSelect = document.getElementById(`roster-sort-${gameId}`);
        const toggleAuditBtn = document.querySelector(`.btn-toggle-audit[data-game="${gameId}"]`);
        const auditPanel = document.getElementById(`audit-panel-${gameId}`);
        const clearBtn = document.querySelector(`.btn-clear-filters[data-game="${gameId}"]`);

        // Função para limpar todos os filtros ativos e resetar o estado
        const resetAllFilters = () => {
            searchQuery = "";
            if (searchInput) searchInput.value = "";
            if (debouncedRosterSearch && debouncedRosterSearch.cancel) debouncedRosterSearch.cancel();

            activeSort = "default";
            if (sortSelect) sortSelect.value = "default";

            activeElementFilter = "all";
            if (filterContainer) {
                filterContainer.querySelectorAll(".filter-btn").forEach(b => {
                    b.classList.toggle("active", b.getAttribute("data-filter") === "all");
                });
            }

            activeRarityFilter = "all";
            if (rarityContainer) {
                rarityContainer.querySelectorAll(".filter-btn").forEach(b => {
                    b.classList.toggle("active", b.getAttribute("data-rarity") === "all");
                });
            }

            activePathFilter = "all";
            if (pathContainer) {
                pathContainer.querySelectorAll(".filter-btn").forEach(b => {
                    b.classList.toggle("active", b.getAttribute("data-path") === "all");
                });
            }

            activeWeaponFilter = "all";
            if (weaponContainer) {
                weaponContainer.querySelectorAll(".filter-btn").forEach(b => {
                    b.classList.toggle("active", b.getAttribute("data-weapon") === "all");
                });
            }

            activeSpecialtyFilter = "all";
            syncSpecialtyUI("all");

            activeSetFilter = "all";
            activeSlotFilter = "all";
            activeGradeFilter = "all";
            activeWeaponStatusFilter = "all";
            activeRegionFilter = "all";
            activeMechanicFilter = "all";
            activeScaleFilter = "all";
            activeMainStatFilter = "all";
            activeSpeedFilter = "all";
            activePlanarFilter = "all";
            activeFactionFilter = "all";
            activeArchetypeFilter = "all";
            activeDiscsMainFilter = "all";

            if (auditPanel) {
                auditPanel.querySelectorAll(".audit-pill").forEach(p => {
                    p.classList.toggle("active", p.getAttribute("data-val") === "all");
                });
                auditPanel.querySelectorAll(".audit-select").forEach(s => s.value = "all");
            }

            renderCards();
        };

        _rosterResetCallbacks[gameId] = resetAllFilters;

        const debouncedRosterSearch = window.createDebouncedSearch((e, signal) => {
            if (signal?.aborted) return;
            const rawVal = e?.target?.value ?? (typeof e === "string" ? e : "");
            const trimmed = rawVal.toLowerCase().trim();
            searchQuery = trimmed.length >= 2 ? trimmed : "";
            renderCards();
        }, { delay: 300, minLength: 2, immediateOnEmpty: true });

        if (searchInput) {
            searchInput._onRosterSearchInput = (e) => {
                const rawVal = (e?.detail?.value ?? searchInput.value ?? "").trim();
                // Se o usuário apagou para < 2 caracteres mas não zero, reseta para lista cheia imediatamente
                if (rawVal.length > 0 && rawVal.length < 2) {
                    debouncedRosterSearch.cancel();
                    if (searchQuery !== "") {
                        searchQuery = "";
                        renderCards();
                    }
                    return;
                }
                debouncedRosterSearch(e);
            };
            if (!searchInput.dataset.searchBound) {
                searchInput.dataset.searchBound = "true";
                searchInput.addEventListener("input", (e) => {
                    if (typeof searchInput._onRosterSearchInput === "function") {
                        searchInput._onRosterSearchInput(e);
                    }
                });
            }
        }

        // Atualiza ações mutáveis para este gameId (evita cloneNode em <sakuga-button> e <select>)
        _rosterFilterActions[gameId] = {
            setElement: (val) => { activeElementFilter = val; renderCards(); },
            setRarity: (val) => { activeRarityFilter = val; renderCards(); },
            setPath: (val) => { activePathFilter = val || "all"; renderCards(); },
            setWeapon: (val) => { activeWeaponFilter = val || "all"; renderCards(); },
            setSpecialty: (val) => { activeSpecialtyFilter = val || "all"; syncSpecialtyUI(activeSpecialtyFilter); renderCards(); },
            setSort: (val) => { activeSort = val; renderCards(); },
            setAuditFilter: (filterType, val) => {
                if (filterType === "set") activeSetFilter = val;
                else if (filterType === "slot") activeSlotFilter = val;
                else if (filterType === "grade") activeGradeFilter = val;
                else if (filterType === "weapon-status") activeWeaponStatusFilter = val;
                else if (filterType === "region") activeRegionFilter = val;
                else if (filterType === "mechanic") activeMechanicFilter = val;
                else if (filterType === "scale") activeScaleFilter = val;
                else if (filterType === "main-stat") activeMainStatFilter = val;
                else if (filterType === "speed") activeSpeedFilter = val;
                else if (filterType === "specialty") {
                    activeSpecialtyFilter = val;
                    syncSpecialtyUI(val);
                }
                else if (filterType === "faction") activeFactionFilter = val;
                else if (filterType === "archetype") activeArchetypeFilter = val;
                else if (filterType === "discs-main") activeDiscsMainFilter = val;
                renderCards();
            },
            setAuditSelect: (fType, val) => {
                if (fType === "planar") activePlanarFilter = val;
                renderCards();
            },
            reset: resetAllFilters
        };

        // Vincula listeners uma única vez por container via dataset.bound + delegação de eventos
        const bindFilterGroup = (container, attrName, actionKey) => {
            if (!container || container.dataset.bound) return;
            container.dataset.bound = "true";
            container.addEventListener("click", (e) => {
                const btn = e.target.closest(".filter-btn");
                if (!btn || !container.contains(btn)) return;
                container.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                _rosterFilterActions[gameId]?.[actionKey]?.(btn.getAttribute(attrName));
            });
        };

        bindFilterGroup(filterContainer, "data-filter", "setElement");
        bindFilterGroup(rarityContainer, "data-rarity", "setRarity");
        bindFilterGroup(pathContainer, "data-path", "setPath");
        bindFilterGroup(weaponContainer, "data-weapon", "setWeapon");
        bindFilterGroup(specialtyContainer, "data-specialty", "setSpecialty");

        if (sortSelect) {
            sortSelect.value = activeSort;
            if (!sortSelect.dataset.bound) {
                sortSelect.dataset.bound = "true";
                sortSelect.addEventListener("change", (e) => {
                    _rosterFilterActions[gameId]?.setSort?.(e.target.value);
                });
            }
        }

        if (toggleAuditBtn && auditPanel && !toggleAuditBtn.dataset.bound) {
            toggleAuditBtn.dataset.bound = "true";
            toggleAuditBtn.addEventListener("click", () => {
                const isVisible = auditPanel.style.display !== "none";
                auditPanel.style.display = isVisible ? "none" : "flex";
                toggleAuditBtn.classList.toggle("active", !isVisible);
            });
        }

        if (auditPanel && !auditPanel.dataset.bound) {
            auditPanel.dataset.bound = "true";
            auditPanel.addEventListener("click", (e) => {
                const pill = e.target.closest(".audit-pill");
                if (!pill || !auditPanel.contains(pill)) return;
                const group = pill.closest(".filter-pills");
                if (!group) return;
                const filterType = group.getAttribute("data-filter-type");
                const val = pill.getAttribute("data-val") || "all";
                group.querySelectorAll(".audit-pill").forEach(p => p.classList.remove("active"));
                pill.classList.add("active");
                _rosterFilterActions[gameId]?.setAuditFilter?.(filterType, val);
            });
            auditPanel.addEventListener("change", (e) => {
                const sel = e.target.closest(".audit-select");
                if (!sel || !auditPanel.contains(sel)) return;
                _rosterFilterActions[gameId]?.setAuditSelect?.(sel.getAttribute("data-filter-type"), sel.value);
            });
        }

        if (clearBtn && !clearBtn.dataset.bound) {
            clearBtn.dataset.bound = "true";
            clearBtn.addEventListener("click", () => {
                _rosterFilterActions[gameId]?.reset?.();
            });
        }
        
        // Renderização inicial do Grid
        renderCards();
        
    } catch (err) {
        const errorTitle = isEn ? "Failed to load character roster" : "Não foi possível carregar os personagens";
        const errorDesc = isEn 
            ? "A temporary issue occurred while reading local data or account profile. Check your connection or retry."
            : "Ocorreu uma instabilidade ao consultar o banco local ou os dados do perfil. Verifique sua conexão e tente novamente.";
        const retryText = isEn ? "Try again" : "Tentar de novo";

        gallery.innerHTML = `
            <div class="error-state-box" style="grid-column: 1 / -1; padding: 40px 24px; text-align: center; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 16px; margin: 16px 0;">
                <div style="width: 50px; height: 50px; border-radius: 50%; background: rgba(239, 68, 68, 0.15); display: inline-flex; align-items: center; justify-content: center; margin-bottom: 14px; color: #ef4444; font-size: 22px;">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                </div>
                <h4 style="color: var(--text-primary); font-size: 16px; font-weight: 700; margin-bottom: 6px;">${errorTitle}</h4>
                <p style="color: var(--text-secondary); font-size: 13px; max-width: 460px; margin: 0 auto 18px auto; line-height: 1.4;">${errorDesc}</p>
                <sakuga-button class="sk-sm sk-accent-danger" onclick="window.loadRoster('${gameId}')">
                    <i class="fa-solid fa-rotate-right"></i> ${retryText}
                </sakuga-button>
            </div>
        `;
    }
}

// ==========================================================================
// COLLAPSIBLE BUILD INSPECTOR (DETALHES DA BUILD)
// ==========================================================================
function cleanHoyoverseText(str) {
    if (!str) return "";
    let clean = String(str);
    clean = clean.replace(/\\r/g, "")
                 .replace(/\\n/g, "\n")
                 .replace(/<br\s*\/?>/gi, "\n");
    clean = clean.replace(/\{M#([^}]*)\}\{F#([^}]*)\}/gi, "$1");
    clean = clean.replace(/\{F#([^}]*)\}/gi, "$1");
    clean = clean.replace(/\{M#([^}]*)\}/gi, "$1");
    clean = clean.replace(/\{LINK#[^}]*\}/gi, "");
    clean = clean.replace(/\{\/LINK\}/gi, "");
    clean = clean.replace(/\{[A-Z0-9_#]+(?::[^}]*)?\}/gi, "");
    clean = clean.replace(/<color=[^>]*>/gi, "");
    clean = clean.replace(/<\/color>/gi, "");
    clean = clean.replace(/<IconMap:[^>]+>/gi, "");
    clean = clean.replace(/<\/?Term(?:\s+[^>]*)?>/gi, "");
    clean = clean.replace(/<\/?[a-z0-9:_-]+(?:\s+[^>]*)?>/gi, "");
    clean = clean.replace(/&nbsp;/gi, " ")
                 .replace(/&quot;/gi, '"')
                 .replace(/&amp;/gi, "&")
                 .replace(/&lt;/gi, "<")
                 .replace(/&gt;/gi, ">")
                 .replace(/&#39;/gi, "'")
                 .replace(/&apos;/gi, "'");
    clean = clean.replace(/[ \t]+/g, " ");
    clean = clean.replace(/\n\s*\n\s*\n+/g, "\n\n");
    return clean.trim();
}

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

let hoyoTooltipInitialized = false;
function setupHoyoCustomTooltip() {
    if (hoyoTooltipInitialized) return;
    hoyoTooltipInitialized = true;

    let tooltipEl = document.getElementById("hoyo-custom-tooltip");
    if (!tooltipEl) {
        tooltipEl = document.createElement("div");
        tooltipEl.id = "hoyo-custom-tooltip";
        tooltipEl.className = "hoyo-hover-tooltip";
        document.body.appendChild(tooltipEl);
    }

    let activeTarget = null;

    document.addEventListener("mouseover", (e) => {
        const target = e.target.closest("[data-hoyo-tooltip]");
        if (!target) return;
        activeTarget = target;

        if (target.title) {
            target.dataset.originalTitle = target.title;
            target.title = "";
        }

        const title = target.getAttribute("data-tooltip-title") || "";
        const type = target.getAttribute("data-tooltip-type") || "";
        const status = target.getAttribute("data-tooltip-status") || "";
        const statusClass = target.getAttribute("data-tooltip-status-class") || "active";
        const desc = target.getAttribute("data-tooltip-desc") || "";

        tooltipEl.innerHTML = `
            <div class="hoyo-hover-tooltip__header">
                <div class="hoyo-hover-tooltip__title-group">
                    ${type ? `<span class="hoyo-hover-tooltip__type">${escapeHtml(type)}</span>` : ''}
                    <span class="hoyo-hover-tooltip__title">${escapeHtml(title)}</span>
                </div>
                ${status ? `<span class="hoyo-hover-tooltip__status hoyo-hover-tooltip__status--${statusClass}">${escapeHtml(status)}</span>` : ''}
            </div>
            ${desc ? `<div class="hoyo-hover-tooltip__body">${escapeHtml(desc)}</div>` : ''}
        `;

        tooltipEl.classList.add("visible");
        positionTooltip(e);
    }, true);

    // Throttle via requestAnimationFrame: no máximo 1 reposicionamento por frame
    let tooltipRaf = null;
    let lastMoveEvt = null;
    document.addEventListener("mousemove", (e) => {
        if (!activeTarget) return;
        lastMoveEvt = e;
        if (tooltipRaf) return;
        tooltipRaf = requestAnimationFrame(() => {
            tooltipRaf = null;
            if (activeTarget && lastMoveEvt) positionTooltip(lastMoveEvt);
        });
    }, { capture: true, passive: true });

    document.addEventListener("mouseout", (e) => {
        const target = e.target.closest("[data-hoyo-tooltip]");
        if (target) {
            if (target.dataset.originalTitle) {
                target.title = target.dataset.originalTitle;
                delete target.dataset.originalTitle;
            }
            if (target === activeTarget) {
                activeTarget = null;
                tooltipEl.classList.remove("visible");
            }
        }
    }, true);

    function positionTooltip(e) {
        const pad = 14;
        let x = e.clientX + 16;
        let y = e.clientY + 16;

        const w = tooltipEl.offsetWidth || 340;
        const h = tooltipEl.offsetHeight || 120;

        if (x + w > window.innerWidth - pad) {
            x = e.clientX - w - 16;
        }
        if (x < pad) x = pad;

        if (y + h > window.innerHeight - pad) {
            y = e.clientY - h - 16;
        }
        if (y < pad) y = pad;

        tooltipEl.style.left = `${x}px`;
        tooltipEl.style.top = `${y}px`;
    }
}

// Inicializa tooltip imediatamente
if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", setupHoyoCustomTooltip);
    } else {
        setupHoyoCustomTooltip();
    }
}

let _inspectController = null;
let _inspectReqId = 0;

async function inspectCharacter(gameId, char) {
    if (_inspectController) {
        _inspectController.abort();
    }
    _inspectController = new AbortController();
    const reqId = ++_inspectReqId;
    const { signal } = _inspectController;

    const inspector = document.getElementById("build-inspector");
    const inspectorOverlay = document.getElementById("inspector-overlay");
    if (inspector) inspector.classList.add("open");
    if (inspectorOverlay) inspectorOverlay.classList.add("active");
    if (window.SakugaFX?.clearTransient) {
        window.SakugaFX.clearTransient();
        requestAnimationFrame(() => window.SakugaFX?.clearTransient?.());
    }
    
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

    
    document.getElementById("ins-name").innerText = typeof formatCharacterName === 'function' ? formatCharacterName(char.name) : char.name;
    
    const elemKey = (char.element || "").toLowerCase();
    const displayElem = formatElementDisplayName(char.element);
    const elemChipHtml = `<span class="ins-meta-chip ins-chip-elem" title="${displayElem}"><img src="${getElementIconUrl(gameId, char.element || elemKey)}" class="element-icon-inline" width="14" height="14" loading="lazy" decoding="async" onerror="this.style.display='none';" alt=""><span>${displayElem.toUpperCase()}</span></span>`;

    let pathVal = "";
    let pathDisplay = "";
    if (gameId === "hsr") {
        pathVal = char.path || getCharacterPath(char) || "";
        pathDisplay = pathVal && typeof formatPathName === "function" ? formatPathName(pathVal, "hsr") : pathVal;
    } else if (gameId === "genshin") {
        pathVal = char.weapon_type || getCharacterWeapon(char) || "";
        const wKey = String(pathVal || "").trim().toLowerCase();
        pathDisplay = (wKey && typeof window.t === "function") ? window.t(`weapon_${wKey}`, pathVal) : pathVal;
    } else {
        pathVal = char.specialty || char.role || char.path || "";
        pathDisplay = pathVal && typeof formatPathName === "function" ? formatPathName(pathVal, gameId) : pathVal;
    }
    const roleChipHtml = (pathVal || pathDisplay)
        ? (typeof renderRoleIconBadge === "function"
            ? renderRoleIconBadge(gameId, pathVal, String(pathDisplay || pathVal).toUpperCase(), { size: 14, className: "ins-meta-chip ins-chip-role", title: pathDisplay || pathVal })
            : `<span class="ins-meta-chip ins-chip-role">${String(pathDisplay || pathVal).toUpperCase()}</span>`)
        : "";
    const insAffEid = window.getUnlockedAffinitiveEidolon ? window.getUnlockedAffinitiveEidolon(char) : null;
    const insAffHtml = insAffEid ? `<span class="ins-affinitive-pill" title="Affinitive Eidolon: ${String(insAffEid.name || "").replace(/"/g, "&quot;")}">✦ Affinitive</span>` : "";
    const insMetaEl = document.getElementById("ins-meta");
    if (insMetaEl) {
        insMetaEl.classList.add("ins-meta-chips");
        insMetaEl.innerHTML = `<span class="ins-meta-chip ins-chip-rank">${char.rank_str || "C0"}</span>${insAffHtml}${elemChipHtml}${roleChipHtml}<span class="ins-meta-chip ins-chip-level">${isEn ? "Lv." : "Nv."} ${char.level}</span>`;
    }
    
    // Configura e limpa o card do Otimizador IA
    const btnOptimize = document.getElementById("btn-ai-optimize");
    const aiLoading = document.getElementById("ins-ai-loading");
    const aiSuggestions = document.getElementById("ins-ai-suggestions");
    
    aiLoading.style.display = "none";
    aiSuggestions.style.display = "none";
    aiSuggestions.innerHTML = "";
    btnOptimize.disabled = false;
    btnOptimize.innerText = isEn ? "Analyze" : "Analisar";
    
    btnOptimize.onclick = async () => {
        btnOptimize.disabled = true;
        btnOptimize.innerText = isEn ? "Analyzing..." : "Analisando...";
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
                aiSuggestions.innerHTML = "<li>O módulo de recomendações por IA está temporariamente desabilitado.</li>";
                aiSuggestions.style.display = "block";
            }
        } catch (optErr) {
            console.error("Erro ao rodar otimizador IA:", optErr);
            aiLoading.style.display = "none";
            aiSuggestions.innerHTML = `<li>Erro ao contactar API: ${optErr.message}</li>`;
            aiSuggestions.style.display = "block";
        } finally {
            btnOptimize.disabled = false;
            btnOptimize.innerText = isEn ? "Re-analyze" : "Reanalisar";
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
    ascTargetSelect.innerHTML = availableLvls.map(l => `<option value="${l}">${isEn ? "Level" : "Nível"} ${l}</option>`).join("");
    ascTargetSelect.value = maxGameLvl.toString();
    
    btnCalculateAsc.onclick = async () => {
        const targetLvl = parseInt(ascTargetSelect.value);
        if (char.level >= targetLvl) {
            ascResults.style.display = "block";
            ascResults.innerHTML = `<span style="color: #10b981; font-weight: 500;"><i class="fa-solid fa-circle-check"></i> ${isEn ? `This character is already level ${char.level} or higher!` : `Este personagem já está no nível ${char.level} ou superior!`}</span>`;
            return;
        }
        
        btnCalculateAsc.disabled = true;
        btnCalculateAsc.innerText = isEn ? "Calculating..." : "Calculando...";
        
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
        btnCalculateAsc.innerText = isEn ? "Calculate" : "Calcular";
    };
    
    // Exibe esqueleto de loading na área de detalhes
    document.getElementById("ins-relic-sets").innerHTML = isEn ? "Loading sets..." : "Carregando conjuntos...";
    document.getElementById("ins-stats-grid").innerHTML = isEn ? "Loading stats..." : "Carregando atributos...";
    document.getElementById("ins-relic-pieces").innerHTML = isEn ? "Loading piece breakdown..." : "Carregando detalhes das peças...";
    
    // Abre a aba lateral
    inspector.classList.add("open");
    if (window.SakugaFX?.clearTransient) {
        window.SakugaFX.clearTransient();
        requestAnimationFrame(() => window.SakugaFX?.clearTransient?.());
    }
    
    try {
        const res = await fetch(`/api/build/${gameId}/${encodeURIComponent(char.name)}`, { signal });
        const build = await res.json();
        if (reqId !== _inspectReqId || signal.aborted) return;
        
        // 0. Renderiza Constelações / Eidolons / Mindscapes
        const ranksCardEl = document.getElementById("ins-ranks-card");
        const ranksTitleEl = document.getElementById("ins-ranks-title");
        const ranksBadgeEl = document.getElementById("ins-ranks-badge");
        const ranksGridEl = document.getElementById("ins-ranks-grid");

        let rankPrefix = "C";
        let rankGameTitle = `<i class="fa-solid fa-star-of-life"></i> ${isEn ? 'Constellations' : 'Constelações'}`;
        if (gameId === "hsr") {
            rankPrefix = "E";
            rankGameTitle = '<i class="fa-solid fa-dna"></i> Eidolons';
        } else if (gameId === "zzz") {
            rankPrefix = "M";
            rankGameTitle = '<i class="fa-solid fa-film"></i> Mindscapes';
        }
        if (ranksTitleEl) ranksTitleEl.innerHTML = rankGameTitle;

        let charRanks = build.ranks || char.ranks || char.constellations || char.mindscapes || [];
        const rankStrVal = char.rank_str || `${rankPrefix}0`;
        const mRank = String(rankStrVal).match(/\d+/);
        const unlockedCount = mRank ? parseInt(mRank[0]) : 0;

        if (!charRanks || charRanks.length === 0) {
            charRanks = [];
            const namePrefix = gameId === "genshin" ? "Constelação" : (gameId === "zzz" ? "Mindscape" : "Eidolon");
            for (let p = 1; p <= 6; p++) {
                charRanks.push({
                    pos: p,
                    name: `${namePrefix} ${p}`,
                    icon: "",
                    desc: "",
                    is_unlocked: p <= unlockedCount
                });
            }
        }
        
        // Atualiza referências locais e globais
        const charExRanks = Array.isArray(build.ex_ranks) && build.ex_ranks.length > 0
            ? build.ex_ranks
            : (Array.isArray(char.ex_ranks) ? char.ex_ranks : []);
        char.ranks = charRanks;
        char.ex_ranks = charExRanks;
        char.constellations = charRanks;
        char.mindscapes = charRanks;
        if (build.id) {
            char.id = build.id;
            char.character_id = build.id;
        }
        if (build.portrait) char.portrait = build.portrait;
        if (build.splash_art) char.splash_art = build.splash_art;
        if (build.eidolon_art) char.eidolon_art = build.eidolon_art;
        if (build.gacha_art) char.gacha_art = build.gacha_art;

        if (window.currentInspectorChar) {
            window.currentInspectorChar.ranks = charRanks;
            window.currentInspectorChar.ex_ranks = charExRanks;
            window.currentInspectorChar.constellations = charRanks;
            window.currentInspectorChar.mindscapes = charRanks;
            if (build.id) {
                window.currentInspectorChar.id = build.id;
                window.currentInspectorChar.character_id = build.id;
            }
            if (build.portrait) window.currentInspectorChar.portrait = build.portrait;
            if (build.splash_art) window.currentInspectorChar.splash_art = build.splash_art;
            if (build.eidolon_art) window.currentInspectorChar.eidolon_art = build.eidolon_art;
            if (build.gacha_art) window.currentInspectorChar.gacha_art = build.gacha_art;
        }

        const unlockedExList = charExRanks.filter(er => er && er.is_unlocked);
        const insMetaEl = document.getElementById("ins-meta");
        if (insMetaEl && unlockedExList.length > 0 && !insMetaEl.querySelector(".ins-affinitive-pill")) {
            const firstAffName = String(unlockedExList[0].name || "Affinitive Eidolon").replace(/"/g, "&quot;");
            const firstSpaceIdx = insMetaEl.innerHTML.indexOf(" • ");
            if (firstSpaceIdx !== -1) {
                insMetaEl.innerHTML = insMetaEl.innerHTML.slice(0, firstSpaceIdx)
                    + ` <span class="ins-affinitive-pill" title="Affinitive Eidolon: ${firstAffName}">✦ Affinitive</span>`
                    + insMetaEl.innerHTML.slice(firstSpaceIdx);
            }
        }

        if (ranksBadgeEl) {
            const exSuffix = unlockedExList.length > 0 ? ` • +${unlockedExList.length} Affinitive` : "";
            ranksBadgeEl.textContent = `${rankPrefix}${unlockedCount} / ${rankPrefix}6${exSuffix}`;
        }

        if (ranksGridEl) {
            ranksGridEl.innerHTML = "";
            charRanks.slice(0, 6).forEach((rk, idx) => {
                const posNum = rk.pos || (idx + 1);
                const isUnlocked = rk.is_unlocked !== undefined ? Boolean(rk.is_unlocked) : (posNum <= unlockedCount);
                const rkName = rk.name || `${rankPrefix}${posNum}`;
                const nodeCard = document.createElement("div");
                nodeCard.className = `rank-node-card ${isUnlocked ? 'rank-node--active' : 'rank-node--locked'}`;
                
                const cleanDesc = cleanHoyoverseText(rk.desc);
                const statusText = isUnlocked ? 'Ativo' : 'Bloqueado';
                const rankTypeLabel = gameId === 'genshin' ? 'Constelação' : (gameId === 'zzz' ? 'Cinema Mental' : 'Eidolon');

                nodeCard.setAttribute('data-hoyo-tooltip', 'true');
                nodeCard.setAttribute('data-tooltip-title', `${rankPrefix}${posNum} • ${rkName}`);
                nodeCard.setAttribute('data-tooltip-type', rankTypeLabel);
                nodeCard.setAttribute('data-tooltip-status', statusText);
                nodeCard.setAttribute('data-tooltip-status-class', isUnlocked ? 'active' : 'locked');

            nodeCard.setAttribute('data-tooltip-desc', cleanDesc || (isEn ? 'No additional details provided.' : 'Nenhum detalhe adicional informado.'));
                nodeCard.title = cleanDesc ? `${rankPrefix}${posNum} • ${rkName} (${statusText})\n\n${cleanDesc}` : `${rankPrefix}${posNum} • ${rkName} (${statusText})`;

                const elemKey = (char.element || "").toLowerCase();
                const defaultElemIcon = getElementIconUrl(gameId, char.element || elemKey);
                let iconSrc = rk.icon;
                if (!iconSrc || (gameId === 'zzz' && iconSrc.includes('/assets/elements/'))) {
                    iconSrc = gameId === 'zzz' ? `/assets/mindscapes/zzz/m${posNum}.png` : defaultElemIcon;
                }
                const rankFallbackIcon = gameId === 'zzz' ? `/assets/mindscapes/zzz/m${posNum}.png` : defaultElemIcon;
                const iconHtml = `<img src="${iconSrc}" class="rank-icon-img" alt="${rkName}" width="36" height="36" loading="lazy" decoding="async" onerror="if(!this.dataset.retried && !this.src.includes('/assets/elements/') && !this.src.includes('/assets/mindscapes/')){this.dataset.retried='1'; const orig=this.src; setTimeout(()=>{ this.src = orig + (orig.includes('?') ? '&retry=1' : '?retry=1'); }, 400);} else { this.onerror=null; this.src='${rankFallbackIcon}'; }">`;

                nodeCard.innerHTML = `
                    <div class="rank-icon-frame">
                        ${iconHtml}
                    </div>
                    <div class="rank-node-details">
                        <span class="rank-node-pos">${rankPrefix}${posNum}</span>
                        <span class="rank-node-name" title="${rkName}">${rkName}</span>
                        <span class="rank-status-pill ${isUnlocked ? 'rank-status-pill--active' : 'rank-status-pill--locked'}">
                            ${isUnlocked ? `<i class="fa-solid fa-circle-check"></i> ${isEn ? "Active" : "Ativo"}` : `<i class="fa-solid fa-lock"></i> ${isEn ? "Locked" : "Bloqueado"}`}
                        </span>
                    </div>
                `;
                ranksGridEl.appendChild(nodeCard);
            });

            // Affinitive Eidolons (ex_ranks do HSR)
            if (gameId === "hsr" && charExRanks.length > 0) {
                const elemKey = (char.element || "").toLowerCase();
                const defaultElemIcon = getElementIconUrl(gameId, char.element || elemKey);
                charExRanks.forEach((er) => {
                    if (!er || typeof er !== "object") return;
                    const isUnlocked = Boolean(er.is_unlocked);
                    const erName = er.name || "Affinitive Eidolon";
                    const cleanDesc = cleanHoyoverseText(er.desc);
                    const statusText = isUnlocked ? (isEn ? 'Active' : 'Ativo') : (isEn ? 'Locked' : 'Bloqueado');
                    const iconSrc = er.icon || defaultElemIcon;
                    const affCard = document.createElement("div");
                    affCard.className = `rank-node-card rank-node--affinitive ${isUnlocked ? 'rank-node--affinitive-active' : 'rank-node--locked'}`;
                    affCard.setAttribute('data-hoyo-tooltip', 'true');
                    affCard.setAttribute('data-tooltip-title', `✦ ${erName}`);
                    affCard.setAttribute('data-tooltip-type', 'Affinitive Eidolon');
                    affCard.setAttribute('data-tooltip-status', statusText);
                    affCard.setAttribute('data-tooltip-status-class', isUnlocked ? 'active' : 'locked');
                    affCard.setAttribute('data-tooltip-desc', cleanDesc || (isEn ? 'No additional details provided.' : 'Nenhum detalhe adicional informado.'));
                    affCard.title = cleanDesc ? `Affinitive Eidolon • ${erName} (${statusText})\n\n${cleanDesc}` : `Affinitive Eidolon • ${erName} (${statusText})`;

                    const iconHtml = `<img src="${iconSrc}" class="rank-icon-img" alt="${erName}" width="40" height="40" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='${defaultElemIcon}';">`;
                    affCard.innerHTML = `
                        <div class="rank-icon-frame rank-icon-frame--affinitive">
                            ${iconHtml}
                        </div>
                        <div class="rank-node-details">
                            <div class="rank-affinitive-header-row">
                                <span class="rank-node-pos rank-node-pos--affinitive">✦ AFFINITIVE EIDOLON</span>
                                <span class="rank-status-pill ${isUnlocked ? 'rank-status-pill--affinitive-active' : 'rank-status-pill--locked'}">
                                    ${isUnlocked ? `<i class="fa-solid fa-circle-check"></i> ${statusText}` : `<i class="fa-solid fa-lock"></i> ${statusText}`}
                                </span>
                            </div>
                            <span class="rank-node-name rank-node-name--affinitive" title="${erName}">${erName}</span>
                            ${cleanDesc ? `<span class="rank-affinitive-desc-preview">${cleanDesc}</span>` : ''}
                        </div>
                    `;
                    ranksGridEl.appendChild(affCard);
                });
            }
        }

        // 0.5 Renderiza Talentos & Habilidades / Traços
        const skillsTitleEl = document.getElementById("ins-skills-title");
        const skillsCountEl = document.getElementById("ins-skills-count");
        const skillsGridEl = document.getElementById("ins-skills-grid");

        let skillsTitleText = `<i class="fa-solid fa-wand-magic-sparkles"></i> ${isEn ? 'Talents' : 'Talentos'}`;
        if (gameId === "hsr") {
            skillsTitleText = `<i class="fa-solid fa-crosshairs"></i> ${isEn ? 'Traces' : 'Traços'}`;
        } else if (gameId === "zzz") {
            skillsTitleText = `<i class="fa-solid fa-bolt"></i> ${isEn ? 'Skills' : 'Habilidades'}`;
        }
        if (skillsTitleEl) skillsTitleEl.innerHTML = skillsTitleText;

        const charSkills = build.skills || char.skills || char.talents || char.traces || [];
        char.skills = charSkills;
        if (window.currentInspectorChar) {
            window.currentInspectorChar.skills = charSkills;
        }

        if (skillsCountEl) {
            skillsCountEl.textContent = charSkills.length > 0 ? `(${charSkills.length} ${isEn ? "skills" : "habilidades"})` : "";
        }

        if (skillsGridEl) {
            skillsGridEl.innerHTML = "";
            if (charSkills.length > 0) {
                charSkills.forEach((sk, sIdx) => {
                    const skCard = document.createElement("div");
                    skCard.className = "skill-card";
                    const skLvl = parseInt(sk.level) || 1;
                    const skMax = parseInt(sk.max_level) || (skLvl > 10 ? 15 : 10);
                    const isBoosted = skLvl >= 10;
                    const progressPct = Math.min(100, Math.round((skLvl / skMax) * 100));
                    const rawType = sk.type || "";

                    let fallbackSkillType = isEn ? "Skill" : "Habilidade";
                    if (gameId === "hsr") fallbackSkillType = isEn ? "Trace" : "Rastro";
                    else if (gameId === "genshin") fallbackSkillType = isEn ? "Talent" : "Talento";
                    else if (gameId === "zzz") fallbackSkillType = isEn ? "Skill" : "Habilidade";

                    const skType = (rawType && rawType !== "Habilidade" && !/^\d+$/.test(rawType)) ? rawType : fallbackSkillType;
                    const cleanSkDesc = cleanHoyoverseText(sk.desc);
                    const skillLvlText = `${isEn ? "Lv." : "Nv."} ${skLvl}${sk.max_level ? ` / ${skMax}` : ''}${isBoosted ? ' 👑' : ''}`;

        const descFallback = isEn ? `Enhancement of ${skType}. Current level: ${skLvl} of ${skMax} (${progressPct}% max progress).` : `Aprimoramento de ${skType}. Nível atual: ${skLvl} de ${skMax} (${progressPct}% do progresso máximo).`;
                    const effectiveDesc = cleanSkDesc || descFallback;

                    skCard.setAttribute('data-hoyo-tooltip', 'true');
                    skCard.setAttribute('data-tooltip-title', sk.name);
                    skCard.setAttribute('data-tooltip-type', skType);
                    skCard.setAttribute('data-tooltip-status', `${isEn ? "Lv." : "Nv."} ${skLvl}${sk.max_level ? ` / ${skMax}` : ''}`);
                    skCard.setAttribute('data-tooltip-status-class', isBoosted ? 'boosted' : 'active');
                    skCard.setAttribute('data-tooltip-desc', effectiveDesc);
                    skCard.title = `${skType} • ${sk.name} (${skillLvlText})\n\n${effectiveDesc}`;

                    let skIconSrc = sk.icon || "";
                    if (gameId === "zzz") {
                        const sLow = (sk.name || "").toLowerCase();
                        const tStr = String(sk.type || "");
                        if (!skIconSrc || skIconSrc.includes("sparkles") || skIconSrc.includes("magic") || !skIconSrc.startsWith("/")) {
                            if (sLow.includes("básico") || sLow.includes("basico") || tStr === "1" || sIdx === 0) {
                                skIconSrc = "/assets/skills/zzz/basic_attack.png";
                            } else if (sLow.includes("esquiva") || tStr === "2") {
                                skIconSrc = "/assets/skills/zzz/dodge.png";
                            } else if (sLow.includes("suporte") || sLow.includes("assist") || tStr === "3") {
                                skIconSrc = "/assets/skills/zzz/assist.png";
                            } else if (sLow.includes("especial") || tStr === "4") {
                                skIconSrc = "/assets/skills/zzz/special.png";
                            } else if (sLow.includes("cadeia") || sLow.includes("suprema") || tStr === "5") {
                                skIconSrc = "/assets/skills/zzz/ultimate.png";
                            } else if (sLow.includes("passiva") || sLow.includes("núcleo") || sLow.includes("principal") || tStr === "6") {
                                skIconSrc = "/assets/skills/zzz/core.png";
                            } else {
                                skIconSrc = "/assets/skills/zzz/basic_attack.png";
                            }
                        }
                    }

                    const iconHtml = skIconSrc
                        ? `<img src="${skIconSrc}" class="skill-icon-img" alt="${sk.name}" width="32" height="32" loading="lazy" decoding="async" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"><i class="fa-solid fa-wand-magic-sparkles" style="display:none; color: #c084fc; font-size: 16px;"></i>`
                        : `<i class="fa-solid fa-wand-magic-sparkles" style="color: #c084fc; font-size: 16px;"></i>`;

                    skCard.innerHTML = `
                        <div class="skill-icon-frame">
                            ${iconHtml}
                        </div>
                        <div class="skill-info">
                            <div class="skill-header-row">
                                <span class="skill-name" title="${sk.name}">${sk.name}</span>
                                <span class="skill-type-tag">${skType}</span>
                            </div>
                            <div class="skill-level-row">
                                <span class="skill-level-badge ${isBoosted ? 'skill-level--boosted' : ''}">
                                    ${isBoosted ? '<i class="fa-solid fa-crown"></i> ' : ''}${isEn ? "Lv." : "Nv."} ${skLvl}${sk.max_level ? ` / ${skMax}` : ''}
                                </span>
                                <div class="skill-progress-track">
                                    <div class="skill-progress-bar" style="width: ${progressPct}%;"></div>
                                </div>
                            </div>
                        </div>
                    `;
                    skillsGridEl.appendChild(skCard);
                });
            } else {
                skillsGridEl.innerHTML = `
                    <div style="text-align: center; padding: 12px; color: var(--text-muted); font-size: 11px;">
                        <i class="fa-solid fa-sparkles" style="margin-bottom: 4px; display: block; opacity: 0.5;"></i>
                        Detalhes de habilidades sincronizados no próximo refresh de dados.
                    </div>
                `;
            }
        }
        
        // 1. Renderiza Arma / Equipamento (com Hover Tooltip de Passiva)
        const weaponDetailEl = document.getElementById("ins-weapon-detail") || document.querySelector("#panel-build .weapon-detail");
        const weaponHintEl = document.getElementById("ins-weapon-hint");
        const lblWeaponName = document.getElementById("ins-weapon-name");
        const lblWeaponMeta = document.getElementById("ins-weapon-meta");
        const imgWeaponIcon = document.getElementById("ins-weapon-icon");

        const weaponInfo = (build && build.weapon_info) ? build.weapon_info : (char.weapon || null);
        const mergedWeapon = weaponInfo ? { ...(char.weapon || {}), ...weaponInfo } : null;

        if (mergedWeapon && mergedWeapon.name) {
            const wName = mergedWeapon.name;
            const wLvl = mergedWeapon.level || 1;
            const wRank = mergedWeapon.rank || 1;
            const rVal = mergedWeapon.rarity || char.weapon_rarity || (build && build.weapon_rarity);
            const rankPrefix = gameId === "hsr" ? "S" : (gameId === "zzz" ? "W" : "R");
            const refLabel = gameId === "hsr"
                ? (isEn ? "Superimposition: S" : "Sobreposição: S")
                : (gameId === "zzz" ? (isEn ? "W-Engine: W" : "Motor-W: W") : (isEn ? "Refinement: R" : "Refinamento: R"));
            const rStar = rVal ? (gameId === "zzz" ? (Number(rVal) === 5 ? "Rank S" : (Number(rVal) === 3 ? "Rank B" : "Rank A")) : `${rVal}★`) : "";
            const metaParts = [rStar, `${isEn ? "Level" : "Nível"} ${wLvl}`, `${refLabel}${wRank}`].filter(Boolean);

            lblWeaponName.innerText = wName;
            lblWeaponMeta.innerText = metaParts.join(" • ");

            const safeWFn = getSafeFileName(wName);
            imgWeaponIcon.src = `/assets/weapons/${gameId}/${safeWFn}`;
            imgWeaponIcon.onerror = function() {
                this.src = mergedWeapon.icon || '/assets/chat_icon.png';
            };

            if (weaponDetailEl) {
                const wTypeBase = gameId === "hsr"
                    ? (isEn ? "Light Cone" : "Cone de Luz")
                    : (gameId === "zzz" ? (isEn ? "W-Engine" : "Motor-W") : (isEn ? "Weapon" : "Arma"));
                const wTypeLabel = rStar ? `${wTypeBase} • ${rStar}` : wTypeBase;
                const wStatusBadge = `${isEn ? "Lv." : "Nv."} ${wLvl} • ${rankPrefix}${wRank}`;
                const cleanPassiveName = cleanHoyoverseText(mergedWeapon.passive_name || "");
                const cleanWeaponDesc = cleanHoyoverseText(mergedWeapon.desc || "");
                const statParts = [mergedWeapon.main_stat, mergedWeapon.sub_stat].filter(Boolean);

                const descChunks = [];
                if (statParts.length > 0) {
                    descChunks.push(statParts.join(" • "));
                }
                if (cleanPassiveName && cleanWeaponDesc) {
                    descChunks.push(`✦ ${cleanPassiveName}\n${cleanWeaponDesc}`);
                } else if (cleanWeaponDesc) {
                    descChunks.push(cleanWeaponDesc);
                } else if (Number(rVal) > 0 && Number(rVal) <= 2) {
                    descChunks.push(isEn ? "Base weapon with no special passive effect." : "Arma básica sem efeito passivo especial.");
                } else {
                    descChunks.push(isEn ? "Passive details will appear after syncing the equipment catalog." : "Detalhes da passiva disponíveis após sincronizar o catálogo de equipamentos.");
                }

                const fullTooltipDesc = descChunks.join("\n\n");
                weaponDetailEl.classList.add("weapon-detail--interactive");
                weaponDetailEl.setAttribute("data-hoyo-tooltip", "true");
                weaponDetailEl.setAttribute("data-tooltip-title", wName);
                weaponDetailEl.setAttribute("data-tooltip-type", wTypeLabel);
                weaponDetailEl.setAttribute("data-tooltip-status", wStatusBadge);
                weaponDetailEl.setAttribute("data-tooltip-status-class", (Number(rVal) >= 5 || Number(wRank) >= 5) ? "boosted" : "active");
                weaponDetailEl.setAttribute("data-tooltip-desc", fullTooltipDesc);
                weaponDetailEl.title = `${wTypeLabel} • ${wName} (${wStatusBadge})\n\n${fullTooltipDesc}`;
                if (weaponHintEl) weaponHintEl.style.display = "inline-flex";
            }
        } else {
            lblWeaponName.innerText = build.weapon || (isEn ? "Not specified" : "Não informado");
            lblWeaponMeta.innerText = isEn ? "Secondary level / Incomplete sync" : "Nível secundário / Sem sincronização completa";
            imgWeaponIcon.src = "/assets/chat_icon.png";
            if (weaponDetailEl) {
                weaponDetailEl.classList.remove("weapon-detail--interactive");
                weaponDetailEl.removeAttribute("data-hoyo-tooltip");
                weaponDetailEl.removeAttribute("data-tooltip-title");
                weaponDetailEl.removeAttribute("data-tooltip-type");
                weaponDetailEl.removeAttribute("data-tooltip-status");
                weaponDetailEl.removeAttribute("data-tooltip-status-class");
                weaponDetailEl.removeAttribute("data-tooltip-desc");
                weaponDetailEl.removeAttribute("title");
            }
            if (weaponHintEl) weaponHintEl.style.display = "none";
        }
        
        // 2. Renderiza Conjuntos de Relíquias / Artefatos / Discos (com Hover Tooltip 2p/4p)
        const setsList = document.getElementById("ins-relic-sets");
        setsList.innerHTML = "";
        
        const setsDetail = (build && Array.isArray(build.sets_detail) && build.sets_detail.length > 0)
            ? build.sets_detail
            : ((Array.isArray(char.sets_detail) && char.sets_detail.length > 0)
                ? char.sets_detail
                : (build.sets || []).map(rawLabel => ({ label: rawLabel, name: rawLabel, pieces: 2, two_pc: "", four_pc: "", is_planar: false })));

        if (setsDetail.length > 0) {
            setsDetail.forEach(sd => {
                const pieces = Number(sd.pieces) || 2;
                const setName = sd.name || sd.label || "";
                const displayLabel = sd.label || `${pieces}p ${setName}`;
                const twoPc = cleanHoyoverseText(sd.two_pc || "");
                const fourPc = cleanHoyoverseText(sd.four_pc || "");
                const isPlanar = Boolean(sd.is_planar);

                let setTypeLabel = isEn ? "Artifact Set" : "Conjunto de Artefatos";
                if (gameId === "hsr") {
                    setTypeLabel = isPlanar
                        ? (isEn ? "Planar Ornament" : "Ornamento Planar")
                        : (isEn ? "Relic Set" : "Conjunto de Relíquias");
                } else if (gameId === "zzz") {
                    setTypeLabel = isEn ? "Drive Disc Set" : "Conjunto de Discos";
                }

                const statusBadge = pieces < 2
                    ? `${pieces}${isEn ? "pc (Inactive)" : "p (Inativo)"}`
                    : `${pieces}${isEn ? "pc Active" : "p Ativo"}`;
                const statusClass = pieces < 2 ? "locked" : ((pieces >= 4 || isPlanar) ? "boosted" : "active");

                const activeTag = isEn ? "Active" : "Ativo";
                const inactiveTag = isEn ? "Inactive" : "Inativo";
                const descLines = [];
                if (twoPc) {
                    const st2 = pieces >= 2 ? activeTag : inactiveTag;
                    descLines.push(`${isEn ? "2-Piece" : "2 Peças"} (${st2}):\n${twoPc}`);
                }
                if (fourPc) {
                    const st4 = pieces >= 4 ? activeTag : inactiveTag;
                    descLines.push(`${isEn ? "4-Piece" : "4 Peças"} (${st4}):\n${fourPc}`);
                }
                const setTooltipDesc = descLines.length > 0
                    ? descLines.join("\n\n")
                    : (isEn ? "Set bonus details will appear after syncing the equipment catalog." : "Detalhes do conjunto disponíveis após sincronizar o catálogo de equipamentos.");

                const item = document.createElement("div");
                item.className = "set-item set-item--interactive";
                item.setAttribute("data-hoyo-tooltip", "true");
                item.setAttribute("data-tooltip-title", setName || displayLabel);
                item.setAttribute("data-tooltip-type", setTypeLabel);
                item.setAttribute("data-tooltip-status", statusBadge);
                item.setAttribute("data-tooltip-status-class", statusClass);
                item.setAttribute("data-tooltip-desc", setTooltipDesc);
                item.title = `${setTypeLabel} • ${setName || displayLabel} (${statusBadge})\n\n${setTooltipDesc}`;

                item.innerHTML = `
                    <span class="set-item-main">
                        <i class="fa-solid fa-wand-magic-sparkles set-item-spark"></i>
                        <span class="set-item-label">${escapeHtml(displayLabel)}</span>
                    </span>
                    <i class="fa-solid fa-circle-info equip-hover-hint" aria-hidden="true"></i>
                `;
                setsList.appendChild(item);
            });
        } else {
            setsList.innerHTML = `<span class="text-muted">${isEn ? "No active set bonuses." : "Nenhum bônus de conjunto ativo."}</span>`;
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
                    <span class="stat-label" title="${sanitizeStatName(key)}">${sanitizeStatName(key)}</span>
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
            statsCountEl.textContent = statsKeys.length > 0 ? `(${statsKeys.length} ${isEn ? "stats" : "atributos"})` : "";
        }
        
        // Merge stats na referência do char atual para o canvas export
        if (statsKeys.length > 0 && window.currentInspectorChar) {
            window.currentInspectorChar.stats = build.stats;
        }
        
        // NOVO: Renderiza Comparação de Metas Gerais (Benchmarks) & Breakpoints em paralelo
        const benchmarksCard = document.getElementById("ins-benchmarks-card");
        const benchmarksList = document.getElementById("ins-benchmarks-list");
        const bpCard = document.getElementById("ins-breakpoints-card");
        const bpList = document.getElementById("ins-breakpoints-list");
        const bpBadge = document.getElementById("ins-breakpoints-summary-badge");

        if (benchmarksCard && benchmarksList) {
            benchmarksCard.style.display = "none";
            benchmarksList.innerHTML = "";
        }
        if (bpCard && bpList) {
            bpCard.style.display = "none";
            bpList.innerHTML = "";
        }

        if (statsKeys.length > 0 && ((benchmarksCard && benchmarksList) || (bpCard && bpList))) {
            const evalPromise = (benchmarksCard && benchmarksList)
                ? fetch(`/api/evaluate-stats/${gameId}/${encodeURIComponent(char.name)}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(build.stats),
                    signal
                }).then(r => (r.ok ? r.json() : null))
                : Promise.resolve(null);

            const bpPromise = (bpCard && bpList)
                ? fetch("/api/stats/breakpoints", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        game_id: gameId,
                        char_name: char.name,
                        stats: build.stats
                    }),
                    signal
                }).then(r => (r.ok ? r.json() : null))
                : Promise.resolve(null);

            const [evalSettled, bpSettled] = await Promise.allSettled([evalPromise, bpPromise]);
            if (reqId !== _inspectReqId || signal.aborted) return;

            if (evalSettled.status === "fulfilled" && evalSettled.value && evalSettled.value.length > 0 && benchmarksCard && benchmarksList) {
                benchmarksCard.style.display = "block";
                benchmarksList.innerHTML = evalSettled.value.map(item => {
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
            } else if (evalSettled.status === "rejected" && evalSettled.reason?.name !== "AbortError") {
                console.error("Erro ao avaliar metas gerais:", evalSettled.reason);
            }

            if (bpSettled.status === "fulfilled" && bpSettled.value?.breakpoints?.length > 0 && bpCard && bpList) {
                const bpData = bpSettled.value;
                bpCard.style.display = "block";
                if (bpBadge) {
                    bpBadge.textContent = bpData.cycles_summary || `${bpData.breakpoints.length} Metas de Combate`;
                }
                bpList.innerHTML = bpData.breakpoints.map(b => {
                    const statusColor = b.is_reached ? "#10b981" : "#f59e0b";
                    const statusIcon = b.is_reached ? '<i class="fa-solid fa-circle-check"></i>' : '<i class="fa-solid fa-clock"></i>';
                    const barWidth = b.tier_progress !== undefined && b.tier_progress !== null ? Math.min(100, Math.max(0, b.tier_progress)) : 100;
                    const barColor = b.is_reached ? "linear-gradient(90deg, #10b981, #34d399)" : "linear-gradient(90deg, #38bdf8, #818cf8)";
                    
                    const tuningHtml = b.speed_tuning_tip ? `
                        <div style="font-size: 11px; color: #cbd5e1; background: rgba(0,0,0,0.3); border-left: 2px solid #38bdf8; padding: 5px 8px; border-radius: 4px; margin-top: 6px; line-height: 1.4;">
                            <i class="fa-solid fa-lightbulb" style="color: #fbbf24; margin-right: 4px;"></i><strong>${isEn ? "Tactical Sync:" : "Sincronia Tática:"}</strong> ${b.speed_tuning_tip}
                        </div>
                    ` : "";

                    return `
                        <div style="padding: 10px 12px; background: rgba(15, 23, 42, 0.6); border-radius: 8px; border: 1px solid rgba(255,255,255,0.06);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                <span style="font-weight: 600; color: #ffffff; font-size: 12px;">${b.stat}</span>
                                <span style="font-size: 12px; font-weight: 700; color: #38bdf8;">${b.current}</span>
                            </div>
                            <div style="display: flex; align-items: center; gap: 6px; font-size: 11px; color: ${statusColor}; margin-bottom: 6px;">
                                <span>${statusIcon}</span>
                                <span>${b.status}</span>
                            </div>
                            <div style="width: 100%; height: 5px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden; margin-bottom: 6px;">
                                <div style="width: ${barWidth}%; height: 100%; background: ${barColor}; border-radius: 4px; transition: width 0.3s ease;"></div>
                            </div>
                            <div style="font-size: 11px; color: #94a3b8; display: flex; justify-content: space-between;">
                                <span><i class="fa-solid fa-bullseye" style="margin-right: 4px; color: #eab308;"></i>${b.next_goal}</span>
                            </div>
                            ${tuningHtml}
                        </div>
                    `;
                }).join("");
            } else if (bpSettled.status === "rejected" && bpSettled.reason?.name !== "AbortError") {
                console.error("Erro ao carregar breakpoints:", bpSettled.reason);
            }
        }
        
        // 4. Renderiza Peças Individuais combinando RAG MD e Local JSON
        const piecesList = document.getElementById("ins-relic-pieces");
        piecesList.innerHTML = "";
        
        // Elemento visual no topo com a Nota Geral da Build
        const rawGrade = (char.overall_grade || (build && build.overall_grade) || "N/A").toUpperCase();
        const overallScore = char.overall_score !== undefined ? char.overall_score : ((build && build.overall_score !== undefined) ? build.overall_score : 0.0);
        const eqCount = char.equipped_pieces !== undefined ? char.equipped_pieces : (build && build.equipped_pieces !== undefined ? build.equipped_pieces : (char.relics ? char.relics.length : 0));
        const maxSlots = char.max_pieces !== undefined ? char.max_pieces : (build && build.max_pieces !== undefined ? build.max_pieces : (gameId === 'genshin' ? 5 : 6));
        const isUnequipped = eqCount === 0 || rawGrade === "N/A";
        const overallGrade = isUnequipped ? "N/A" : rawGrade;
        const gradeClass = isUnequipped ? "badge-na" : `badge-${overallGrade.toLowerCase()}`;
        const equippedInfo = ` (${eqCount}/${maxSlots} peças equipadas)`;
        const badgeContent = isUnequipped ? (isEn ? `No Gear (${eqCount}/${maxSlots})` : `Sem Equipamentos (${eqCount}/${maxSlots})`) : `${overallGrade} (${overallScore} pts)`;
        
        const banner = document.createElement("div");
        banner.className = "overall-build-banner";
        banner.style.display = "flex";
        banner.style.justifyContent = "space-between";
        banner.style.alignItems = "center";
        banner.innerHTML = `
            <div>
                <div class="overall-build-title">
                    <i class="fa-solid fa-award" style="color: #f59e0b;"></i> ${isEn ? "Overall Build Score" : "Nota Geral da Build"}${equippedInfo}
                </div>
                <div style="margin-top: 6px;">
                    <sakuga-button class="trigger-export-card sk-xs sk-accent-amber" variant="secondary">
                        <i class="fa-solid fa-camera"></i> ${isEn ? "Generate Build Card (Splash Art)" : "Gerar Imagem da Build (Splash Art)"}
                    </sakuga-button>
                </div>
            </div>
            <div class="overall-badge ${gradeClass}">
                ${badgeContent}
            </div>
        `;
        piecesList.appendChild(banner);
        
        // As peças do roster extraído via HoYoLAB local (contêm URLs originais dos ícones de cada peça!)
        const localRelics = char.relics || char.artifacts || char.discs || [];

        const effectivePieces = (build.pieces && build.pieces.length > 0) ? build.pieces : localRelics;

        if (effectivePieces && effectivePieces.length > 0) {
            effectivePieces.forEach(piece => {
                const row = document.createElement("div");
                row.className = "relic-piece-row";
                
                // Encontra a peça equivalente local para extrair o ícone
                const equivalentLocalPiece = localRelics.find(p => 
                    (p.slot && piece.slot && getNormalizedSlot(p.slot) === getNormalizedSlot(piece.slot)) ||
                    (p.name && piece.name && p.name.toLowerCase().includes(piece.name.toLowerCase()))
                );
                
                const slotIconHtml = window.getSlotIcon ? window.getSlotIcon(piece.slot) : "";
                const safePieceFn = getSafeFileName(piece.name);
                const cachedPiecePath = `/assets/relics/${gameId}/${safePieceFn}`;
                
                const rawIcon = (equivalentLocalPiece && equivalentLocalPiece.icon) ? equivalentLocalPiece.icon : (piece.icon || cachedPiecePath);
                
                const iconHtml = `
                    <div style="width: 36px; height: 36px; border-radius: 8px; background: rgba(255, 255, 255, 0.05); display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; overflow: hidden; position: relative;">
                        <img class="relic-piece-icon" src="${rawIcon}" width="36" height="36" loading="lazy" decoding="async" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" style="width: 100%; height: 100%; object-fit: cover;" alt="${piece.slot || ''}">
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
                    subsHtml = `<span class="text-muted" style="font-size: 10px;">${isEn ? "No substats" : "Sem substatus"}</span>`;
                }
                
                let pGrade = (equivalentLocalPiece && equivalentLocalPiece.grade) || piece.grade;
                let pScore = (equivalentLocalPiece && equivalentLocalPiece.score !== undefined) ? equivalentLocalPiece.score : (piece.score !== undefined ? piece.score : 0);
                let gradeHtml = "";
                if (pGrade && pGrade !== "N/A") {
                    gradeHtml = `<span class="badge-relic badge-relic-${pGrade.toLowerCase()}">${pGrade}</span><span style="font-size: 10px; color: var(--text-secondary); margin-left: 6px; font-weight: 500;">Score: ${pScore}</span>`;
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
                        <div class="piece-main" style="font-size: 11px; color: var(--text-secondary); margin-bottom: 6px;">${isEn ? "Main:" : "Principal:"} <span class="main-stat-pill">${cleanMain}</span></div>
                        <div class="piece-subs">${subsHtml}</div>
                    </div>
                `;
                piecesList.appendChild(row);
            });
        } else {
            const emptyPiecesEl = document.createElement("span");
            emptyPiecesEl.className = "text-muted";
            emptyPiecesEl.textContent = isEn ? "No pieces equipped on this character." : "Nenhuma peça equipada neste personagem.";
            piecesList.appendChild(emptyPiecesEl);
        }
        
    } catch (err) {
        if (err?.name === "AbortError" || reqId !== _inspectReqId) return;
        console.error("Erro ao inspecionar build:", err);
        document.getElementById("ins-relic-sets").innerHTML = "Erro ao carregar.";
        document.getElementById("ins-stats-grid").innerHTML = "Erro ao carregar.";
        document.getElementById("ins-relic-pieces").innerHTML = "Erro ao carregar.";
    }
}

const _closeIns = () => window.closeInspector?.();
const btnCloseInspector = document.getElementById("btn-close-inspector");
if (btnCloseInspector) btnCloseInspector.addEventListener("click", _closeIns);
const inspectorOverlay = document.getElementById("inspector-overlay");
if (inspectorOverlay) inspectorOverlay.addEventListener("click", _closeIns);

// Fechar modal ao pressionar a tecla Escape
window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        const inspector = document.getElementById("build-inspector");
        if (inspector && inspector.classList.contains("open")) {
            _closeIns();
        }
    }
});

window.addEventListener("app:languageChanged", () => {
    ["zzz", "genshin", "hsr"].forEach(g => {
        if (!globalRoster || !globalRoster[g] || globalRoster[g].length === 0) return;
        const tabEl = document.getElementById(`tab-${g}`);
        if (tabEl && tabEl.classList.contains("active")) {
            if (g === "hsr") {
                const allOpt = document.querySelector('#planar-filter-hsr option[value="all"]');
                if (allOpt) allOpt.textContent = window.isEn ? "All Planar Ornaments" : "Todos os Ornamentos Planares";
            }
            if (typeof _rosterRenderers[g] === "function") {
                _rosterRenderers[g]();
            }
        } else {
            _dirtyRosterLang[g] = true;
        }
    });
});

// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
if (typeof btnCloseInspector !== 'undefined') window.btnCloseInspector = btnCloseInspector;
if (typeof cleanHoyoverseText !== 'undefined') window.cleanHoyoverseText = cleanHoyoverseText;
if (typeof escapeHtml !== 'undefined') window.escapeHtml = escapeHtml;
if (typeof hoyoTooltipInitialized !== 'undefined') window.hoyoTooltipInitialized = hoyoTooltipInitialized;
if (typeof inspectCharacter !== 'undefined') window.inspectCharacter = inspectCharacter;
if (typeof inspectorOverlay !== 'undefined') window.inspectorOverlay = inspectorOverlay;
if (typeof loadRoster !== 'undefined') window.loadRoster = loadRoster;
if (typeof setupHoyoCustomTooltip !== 'undefined') window.setupHoyoCustomTooltip = setupHoyoCustomTooltip;
if (typeof setupRosterViewModeToggle !== 'undefined') window.setupRosterViewModeToggle = setupRosterViewModeToggle;
if (typeof setRosterViewMode !== 'undefined') window.setRosterViewMode = setRosterViewMode;
