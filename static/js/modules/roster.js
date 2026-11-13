// ==========================================================================
// Módulo: roster.js
// Cabeça de Droid - Vanilla ES6 Module
// ==========================================================================

// ==========================================================================
// RENDERIZAÇÃO DA GALERIA DE PERSONAGENS
// ==========================================================================
const HSR_CHAR_PATHS = {"acheron": "Nihility", "firefly": "Destruction", "feixiao": "Hunt", "robin": "Harmony", "ruan_mei": "Harmony", "ruan mei": "Harmony", "aventurine": "Preservation", "black_swan": "Nihility", "black swan": "Nihility", "sparkle": "Harmony", "sunday": "Harmony", "fugue": "Nihility", "castorice": "Remembrance", "boothill": "Hunt", "dr_ratio": "Hunt", "dr. ratio": "Hunt", "topaz": "Hunt", "topaz & dinheirinho": "Hunt", "jingliu": "Destruction", "dan_heng_il": "Destruction", "dan heng • embebidor lunae": "Destruction", "blade": "Destruction", "kafka": "Nihility", "silver_wolf": "Nihility", "loba prateada (silver wolf)": "Nihility", "seele": "Hunt", "jing_yuan": "Erudition", "jing yuan": "Erudition", "luocha": "Abundance", "huohuo": "Abundance", "lingsha": "Abundance", "jiaoqiu": "Nihility", "bronya": "Harmony", "tingyun": "Harmony", "clara": "Destruction", "gepard": "Preservation", "bailu": "Abundance", "himeko": "Erudition", "welt": "Nihility", "7_de_março": "Hunt", "7 de março": "Hunt", "dan_heng": "Hunt", "dan heng": "Hunt", "loba_prateada": "Nihility", "loba prateada": "Nihility", "arlan": "Destruction", "asta": "Harmony", "herta": "Erudition", "saber": "Destruction", "archer": "Hunt", "serval": "Erudition", "natasha": "Abundance", "pela": "Nihility", "sampo": "Nihility", "hook": "Destruction", "lynx": "Abundance", "luka": "Nihility", "topaz_e_dinheirinho": "Hunt", "topaz e dinheirinho": "Hunt", "qingque": "Erudition", "sushang": "Hunt", "yukong": "Harmony", "fu_xuan": "Preservation", "fu xuan": "Preservation", "yanqing": "Hunt", "guinaifen": "Nihility", "dan_heng_-_embebidor_lunae": "Destruction", "dan heng - embebidor lunae": "Destruction", "xueyi": "Destruction", "hanya": "Harmony", "yunli": "Destruction", "moze": "Hunt", "gallagher": "Abundance", "argenti": "Erudition", "dr._ratio": "Hunt", "cisne_negro": "Nihility", "cisne negro": "Nihility", "vaga-lume": "Destruction", "misha": "Destruction", "jade": "Erudition", "rappa": "Erudition", "a_dália": "Nihility", "a dália": "Nihility", "a_herta": "Erudition", "a herta": "Erudition", "aglaea": "Remembrance", "tribbie": "Harmony", "mydei": "Destruction", "anaxa": "Erudition", "cipher": "Nihility", "phainon": "Destruction", "hyacine": "Remembrance", "hysilens": "Nihility", "cerydra": "Harmony", "noite_eterna": "Remembrance", "noite eterna": "Remembrance", "dan_heng_-_permansor_terrae": "Preservation", "dan heng - permansor terrae": "Preservation", "cyrene": "Remembrance", "sparxie": "Elation", "yao_guang": "Elation", "yao guang": "Elation", "pearl": "Elation", "ashveil": "Hunt", "evanescia": "Elation", "loba_prateada_nv._999": "Elation", "loba prateada nv. 999": "Elation", "mortenax_blade": "Nihility", "mortenax blade": "Nihility", "rin_tohsaka": "Erudition", "rin tohsaka": "Erudition", "gilgamesh": "Destruction", "himeko_-_nova": "Erudition", "himeko - nova": "Erudition", "robin_-_summeretto": "Remembrance", "robin - summeretto": "Harmony", "aventurine_-_veraneio": "Elation", "aventurine - veraneio": "Elation", "{nickname}": "Elation", "novo_personagem_teste": "Destruction", "novo personagem teste": "Destruction", "vagalume": "Destruction", "luciernaga": "Destruction", "cisne": "Nihility", "dr ratio": "Hunt", "doutor ratio": "Hunt", "doctor ratio": "Hunt", "ratio": "Hunt", "aqueronte": "Nihility", "danheng": "Hunt", "lobo prateado": "Nihility", "loba plateada": "Nihility", "silver wolf": "Nihility", "aventurina": "Preservation", "faísca": "Harmony", "faisca": "Harmony", "hanabi": "Harmony", "domingo": "Harmony", "robin summeretto": "Harmony", "robin_summeretto": "Harmony", "himeko nova": "Erudition", "himeko_nova": "Erudition"};
const GENSHIN_CHAR_WEAPONS = {"albedo": "Sword", "aloy": "Bow", "amber": "Bow", "barbara": "Catalyst", "bennett": "Sword", "diluc": "Claymore", "diona": "Bow", "eula": "Claymore", "fischl": "Bow", "jean": "Sword", "kaeya": "Sword", "klee": "Catalyst", "lisa": "Catalyst", "mika": "Polearm", "mona": "Catalyst", "noelle": "Claymore", "razor": "Claymore", "rosaria": "Polearm", "sucrose": "Catalyst", "venti": "Bow", "baizhu": "Catalyst", "beidou": "Claymore", "chongyun": "Claymore", "gaming": "Claymore", "ganyu": "Bow", "hu_tao": "Polearm", "hu tao": "Polearm", "kaedehara_kazuha": "Sword", "kaedehara kazuha": "Sword", "kazuha": "Sword", "keqing": "Sword", "lan_yan": "Catalyst", "lan yan": "Catalyst", "ningguang": "Catalyst", "qiqi": "Sword", "shenhe": "Polearm", "xiangling": "Polearm", "xianyun": "Catalyst", "xiao": "Polearm", "xingqiu": "Sword", "xinyan": "Claymore", "yanfei": "Catalyst", "yaoyao": "Polearm", "yelan": "Bow", "yun_jin": "Polearm", "yun jin": "Polearm", "yunjin": "Polearm", "zhongli": "Polearm", "arataki_itto": "Claymore", "arataki itto": "Claymore", "itto": "Claymore", "kamisato_ayaka": "Sword", "kamisato ayaka": "Sword", "ayaka": "Sword", "kamisato_ayato": "Sword", "kamisato ayato": "Sword", "ayato": "Sword", "chiori": "Sword", "gorou": "Bow", "kirara": "Sword", "kujou_sara": "Bow", "kujou sara": "Bow", "sara": "Bow", "kuki_shinobu": "Sword", "kuki shinobu": "Sword", "shinobu": "Sword", "raiden_shogun": "Polearm", "raiden shogun": "Polearm", "sangonomiya_kokomi": "Catalyst", "sangonomiya kokomi": "Catalyst", "kokomi": "Catalyst", "sayu": "Claymore", "shikanoin_heizou": "Catalyst", "shikanoin heizou": "Catalyst", "heizou": "Catalyst", "thoma": "Polearm", "yae_miko": "Catalyst", "yae miko": "Catalyst", "yoimiya": "Bow", "alhaitham": "Sword", "candace": "Polearm", "collei": "Bow", "cyno": "Polearm", "dehya": "Claymore", "dori": "Claymore", "faruzan": "Bow", "kaveh": "Claymore", "layla": "Sword", "nahida": "Catalyst", "nilou": "Sword", "sethos": "Bow", "tighnari": "Bow", "wanderer": "Catalyst", "andarilho": "Catalyst", "arlecchino": "Polearm", "charlotte": "Catalyst", "chevreuse": "Polearm", "clorinde": "Sword", "emilie": "Polearm", "freminet": "Claymore", "furina": "Sword", "lynette": "Sword", "lyney": "Bow", "navia": "Claymore", "neuvillette": "Catalyst", "sigewinne": "Bow", "wriothesley": "Catalyst", "chasca": "Bow", "citlali": "Catalyst", "iansan": "Polearm", "kachina": "Polearm", "kinich": "Claymore", "mavuika": "Claymore", "mualani": "Catalyst", "ororon": "Bow", "xilonen": "Sword", "tartaglia": "Bow", "viajante": "Sword", "hutao": "Polearm", "shogun_raiden": "Polearm", "shogun raiden": "Polearm", "yumemizuki_mizuki": "Catalyst", "yumemizuki mizuki": "Catalyst", "varesa": "Catalyst", "escoffier": "Polearm", "ifa": "Catalyst", "skirk": "Sword", "dahlia": "Sword", "ineffa": "Polearm", "lauma": "Catalyst", "flins": "Polearm", "aino": "Claymore", "nefer": "Catalyst", "durin": "Sword", "jahoda": "Bow", "mavuika_(teste)": "Claymore", "mavuika (teste)": "Claymore", "hutao_(teste)": "Polearm", "hutao (teste)": "Polearm", "columbina": "Catalyst", "arconte_pyro_(teste)": "Claymore", "arconte pyro (teste)": "Claymore", "raiden": "Polearm", "yae": "Catalyst", "mochileiro": "Catalyst", "trotamundos": "Catalyst", "scaramouche": "Catalyst", "arlequino": "Polearm"};

function getCharacterPath(char) {
    if (char && char.path) return String(char.path);
    const nameLower = (char && char.name ? char.name : "").toLowerCase().trim();
    const slug = nameLower.replace(/\s+/g, "_");
    if (HSR_CHAR_PATHS[slug]) return HSR_CHAR_PATHS[slug];
    if (HSR_CHAR_PATHS[nameLower]) return HSR_CHAR_PATHS[nameLower];
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
    const nameLower = (char && char.name ? char.name : "").toLowerCase().trim();
    const slug = nameLower.replace(/\s+/g, "_");
    if (GENSHIN_CHAR_WEAPONS[slug]) return GENSHIN_CHAR_WEAPONS[slug];
    if (GENSHIN_CHAR_WEAPONS[nameLower]) return GENSHIN_CHAR_WEAPONS[nameLower];
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
        renderGameCharts(gameId);
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
                    <button class="primary-btn" onclick="const btn = document.querySelector('.sync-game-btn[data-game=\\'${gameId}\\']'); if (btn) btn.click(); else window.loadRoster('${gameId}');" style="padding: 10px 22px; font-size: 13px; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; border-radius: 10px; cursor: pointer;">
                        <i class="fa-solid fa-arrows-rotate"></i> ${emptyBtnText}
                    </button>
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
                    else if (pLower === "remembrance") matchesPath = charPath.includes("remembr") || charPath.includes("reminisc");
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
                    const spec = String(char.specialty || char.role || "").toLowerCase();
                    matchesSpecialty = spec.includes(activeSpecialtyFilter.toLowerCase());
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
                        <button class="primary-btn" onclick="window.clearRosterFilters('${gameId}')" style="display: inline-flex; align-items: center; gap: 8px; padding: 8px 18px; font-size: 12px; border-radius: 8px; margin: 0 auto; cursor: pointer;">
                            <i class="fa-solid fa-filter-circle-xmark"></i> ${clearText}
                        </button>
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

                if (currentRosterViewMode === "list") {
                    card.className = `char-card char-list-row ${elemClass}${inTeamClass}`;

                    const rarityNum = Number(char.rarity);
                    const isFiveStar = rarityNum === 5 || char.rarity === "5" || String(char.rarity).toUpperCase() === "S";
                    const elemDisplayName = typeof formatElementDisplayName === "function" ? formatElementDisplayName(char.element) : (char.element || "");

                    let pathOrWeaponLabel = "";
                    if (gameId === "hsr") {
                        const rawP = char.path || getCharacterPath(char);
                        pathOrWeaponLabel = typeof formatPathName === "function" ? formatPathName(rawP, "hsr") : rawP;
                    } else if (gameId === "genshin") {
                        const rawW = char.weapon_type || getCharacterWeapon(char) || "";
                        pathOrWeaponLabel = typeof window.t === "function" ? window.t(`weapon_${rawW}`, rawW) : rawW;
                    } else if (gameId === "zzz") {
                        pathOrWeaponLabel = char.specialty || char.role || "";
                    }

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
                                        <img src="/assets/elements/${gameId}_${elemKey}.png" width="14" height="14" loading="lazy" decoding="async" onerror="this.style.display='none';" alt="">
                                        ${elemDisplayName}
                                    </span>
                                    <span class="char-list-rarity-badge ${isFiveStar ? 'five-star' : 'four-star'}">${rarityLabel}</span>
                                    ${affEid ? `<span class="char-list-affinitive-pill" title="Affinitive Eidolon: ${affTitleAttr}">✦ Affinitive</span>` : ''}
                                    ${teamPos !== -1 ? `<span class="char-list-badge-team"><i class="fa-solid fa-users"></i> #${teamPos + 1}</span>` : ''}
                                </div>
                                <div class="char-list-details-row">
                                    <span class="char-list-badge-lvl">${lvlLabel} ${char.level}</span>
                                    ${pathOrWeaponLabel ? `<span>• ${pathOrWeaponLabel}</span>` : ''}
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
                                <img src="/assets/elements/${gameId}_${elemKey}.png" class="element-icon-inline" width="16" height="16" loading="lazy" decoding="async" onerror="this.style.display='none';" alt="">
                                ${formattedName}
                            </div>
                            <div class="char-lvl">${lvlLabel} ${char.level}</div>
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
        
        // Configura ouvintes de clique nos botões de filtro de elementos
        const filterContainer = document.querySelector(`.element-filters[data-game="${gameId}"]:not(.rarity-filters):not(.weapon-filters):not(.path-filters)`);
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
        
        // Configura ouvintes de clique nos botões de filtro de caminho (HSR)
        const pathContainer = document.querySelector(`.path-filters[data-game="${gameId}"]`);
        if (pathContainer) {
            const pathBtns = pathContainer.querySelectorAll(".filter-btn");
            pathBtns.forEach(btn => {
                const newBtn = btn.cloneNode(true);
                btn.parentNode.replaceChild(newBtn, btn);
            });
            const freshPathBtns = pathContainer.querySelectorAll(".filter-btn");
            freshPathBtns.forEach(btn => {
                btn.addEventListener("click", () => {
                    freshPathBtns.forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    activePathFilter = btn.getAttribute("data-path") || "all";
                    renderCards();
                });
            });
        }

        // Configura ouvintes de clique nos botões de filtro de arma (Genshin)
        const weaponContainer = document.querySelector(`.weapon-filters[data-game="${gameId}"]`);
        if (weaponContainer) {
            const weaponBtns = weaponContainer.querySelectorAll(".filter-btn");
            weaponBtns.forEach(btn => {
                const newBtn = btn.cloneNode(true);
                btn.parentNode.replaceChild(newBtn, btn);
            });
            const freshWeaponBtns = weaponContainer.querySelectorAll(".filter-btn");
            freshWeaponBtns.forEach(btn => {
                btn.addEventListener("click", () => {
                    freshWeaponBtns.forEach(b => b.classList.remove("active"));
                    btn.classList.add("active");
                    activeWeaponFilter = btn.getAttribute("data-weapon") || "all";
                    renderCards();
                });
            });
        }
        
        // Evento de busca em tempo real com debounce de ~300ms, AbortController e guarda de min 2 caracteres
        searchInput.replaceWith(searchInput.cloneNode(true)); // Limpa listeners antigos
        const newSearchInput = document.querySelector(`.search-input[data-game="${gameId}"]`);
        
        const debouncedRosterSearch = window.createDebouncedSearch((e, signal) => {
            if (signal?.aborted) return;
            const rawVal = e?.target?.value ?? (typeof e === "string" ? e : "");
            const trimmed = rawVal.toLowerCase().trim();
            searchQuery = trimmed.length >= 2 ? trimmed : "";
            renderCards();
        }, { delay: 300, minLength: 2, immediateOnEmpty: true });

        newSearchInput.addEventListener("input", (e) => {
            const rawVal = e.target.value.trim();
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
        });

        // Configura seletor de ordenação inteligente
        const sortSelect = document.getElementById(`roster-sort-${gameId}`);
        if (sortSelect) {
            const newSelect = sortSelect.cloneNode(true);
            sortSelect.parentNode.replaceChild(newSelect, sortSelect);
            const freshSelect = document.getElementById(`roster-sort-${gameId}`);
            freshSelect.value = activeSort;
            freshSelect.addEventListener("change", (e) => {
                activeSort = e.target.value;
                renderCards();
            });
        }

        // Configura botão de alternar painel de auditoria
        const toggleAuditBtn = document.querySelector(`.btn-toggle-audit[data-game="${gameId}"]`);
        const auditPanel = document.getElementById(`audit-panel-${gameId}`);
        if (toggleAuditBtn && auditPanel) {
            const newToggle = toggleAuditBtn.cloneNode(true);
            toggleAuditBtn.parentNode.replaceChild(newToggle, toggleAuditBtn);
            const freshToggle = document.querySelector(`.btn-toggle-audit[data-game="${gameId}"]`);
            freshToggle.addEventListener("click", () => {
                const isVisible = auditPanel.style.display !== "none";
                auditPanel.style.display = isVisible ? "none" : "flex";
                if (!isVisible) freshToggle.classList.add("active");
                else freshToggle.classList.remove("active");
            });
        }

        // Configura pílulas e seletores do painel de auditoria
        if (auditPanel) {
            const pills = auditPanel.querySelectorAll(".audit-pill");
            pills.forEach(pill => {
                const newPill = pill.cloneNode(true);
                pill.parentNode.replaceChild(newPill, pill);
            });
            const freshPills = auditPanel.querySelectorAll(".audit-pill");
            freshPills.forEach(pill => {
                pill.addEventListener("click", () => {
                    const group = pill.closest(".filter-pills");
                    if (!group) return;
                    const filterType = group.getAttribute("data-filter-type");
                    const val = pill.getAttribute("data-val") || "all";
                    
                    group.querySelectorAll(".audit-pill").forEach(p => p.classList.remove("active"));
                    pill.classList.add("active");

                    if (filterType === "set") activeSetFilter = val;
                    else if (filterType === "slot") activeSlotFilter = val;
                    else if (filterType === "grade") activeGradeFilter = val;
                    else if (filterType === "weapon-status") activeWeaponStatusFilter = val;
                    else if (filterType === "region") activeRegionFilter = val;
                    else if (filterType === "mechanic") activeMechanicFilter = val;
                    else if (filterType === "scale") activeScaleFilter = val;
                    else if (filterType === "main-stat") activeMainStatFilter = val;
                    else if (filterType === "speed") activeSpeedFilter = val;
                    else if (filterType === "specialty") activeSpecialtyFilter = val;
                    else if (filterType === "faction") activeFactionFilter = val;
                    else if (filterType === "archetype") activeArchetypeFilter = val;
                    else if (filterType === "discs-main") activeDiscsMainFilter = val;

                    renderCards();
                });
            });

            const auditSelects = auditPanel.querySelectorAll(".audit-select");
            auditSelects.forEach(sel => {
                const newSel = sel.cloneNode(true);
                sel.parentNode.replaceChild(newSel, sel);
            });
            const freshSelects = auditPanel.querySelectorAll(".audit-select");
            freshSelects.forEach(sel => {
                sel.addEventListener("change", (e) => {
                    const fType = sel.getAttribute("data-filter-type");
                    if (fType === "planar") activePlanarFilter = sel.value;
                    renderCards();
                });
            });
        }

        // Função para limpar todos os filtros ativos e resetar o estado
        const resetAllFilters = () => {
            searchQuery = "";
            if (newSearchInput) newSearchInput.value = "";
            if (debouncedRosterSearch && debouncedRosterSearch.cancel) debouncedRosterSearch.cancel();

            activeSort = "default";
            const sortSel = document.getElementById(`roster-sort-${gameId}`);
            if (sortSel) sortSel.value = "default";

            activeElementFilter = "all";
            if (filterContainer) {
                filterContainer.querySelectorAll(".filter-btn").forEach(b => {
                    if (b.getAttribute("data-filter") === "all") b.classList.add("active");
                    else b.classList.remove("active");
                });
            }

            activeRarityFilter = "all";
            if (rarityContainer) {
                rarityContainer.querySelectorAll(".filter-btn").forEach(b => {
                    if (b.getAttribute("data-rarity") === "all") b.classList.add("active");
                    else b.classList.remove("active");
                });
            }

            activePathFilter = "all";
            if (pathContainer) {
                pathContainer.querySelectorAll(".filter-btn").forEach(b => {
                    if (b.getAttribute("data-path") === "all") b.classList.add("active");
                    else b.classList.remove("active");
                });
            }

            activeWeaponFilter = "all";
            if (weaponContainer) {
                weaponContainer.querySelectorAll(".filter-btn").forEach(b => {
                    if (b.getAttribute("data-weapon") === "all") b.classList.add("active");
                    else b.classList.remove("active");
                });
            }

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
            activeSpecialtyFilter = "all";
            activeFactionFilter = "all";
            activeArchetypeFilter = "all";
            activeDiscsMainFilter = "all";

            if (auditPanel) {
                auditPanel.querySelectorAll(".audit-pill").forEach(p => {
                    if (p.getAttribute("data-val") === "all") p.classList.add("active");
                    else p.classList.remove("active");
                });
                auditPanel.querySelectorAll(".audit-select").forEach(s => s.value = "all");
            }

            renderCards();
        };

        _rosterResetCallbacks[gameId] = resetAllFilters;

        // Configura botão de limpar filtros na barra de busca
        const clearBtn = document.querySelector(`.btn-clear-filters[data-game="${gameId}"]`);
        if (clearBtn) {
            const newClear = clearBtn.cloneNode(true);
            clearBtn.parentNode.replaceChild(newClear, clearBtn);
            const freshClear = document.querySelector(`.btn-clear-filters[data-game="${gameId}"]`);
            freshClear.addEventListener("click", () => {
                resetAllFilters();
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
                <button class="primary-btn" onclick="window.loadRoster('${gameId}')" style="padding: 8px 20px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; border-radius: 8px; cursor: pointer; background: #ef4444;">
                    <i class="fa-solid fa-rotate-right"></i> ${retryText}
                </button>
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

    
    document.getElementById("ins-name").innerText = typeof formatCharacterName === 'function' ? formatCharacterName(char.name) : char.name;
    
    const elemKey = (char.element || "").toLowerCase();
    const displayElem = formatElementDisplayName(char.element);
    const elemHtml = `<img src="/assets/elements/${gameId}_${elemKey}.png" class="element-icon-inline" width="14" height="14" loading="lazy" decoding="async" style="width:14px; height:14px;" onerror="this.style.display='none';"> ${displayElem.toUpperCase()}`;
    const pathVal = char.path || char.specialty || char.weapon_type || "";
    const pathDisplay = pathVal && typeof formatPathName === 'function' ? formatPathName(pathVal, gameId) : "";
    const pathHtml = pathDisplay ? ` • ${pathDisplay.toUpperCase()}` : "";
    const insAffEid = window.getUnlockedAffinitiveEidolon ? window.getUnlockedAffinitiveEidolon(char) : null;
    const insAffHtml = insAffEid ? ` <span class="ins-affinitive-pill" title="Affinitive Eidolon: ${String(insAffEid.name || "").replace(/"/g, "&quot;")}">✦ Affinitive</span>` : "";
    document.getElementById("ins-meta").innerHTML = `${char.rank_str || "C0"}${insAffHtml} • ${elemHtml}${pathHtml} • ${isEn ? "Level" : "Nível"} ${char.level}`;
    
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
    
    try {
        const res = await fetch(`/api/build/${gameId}/${encodeURIComponent(char.name)}`);
        const build = await res.json();
        
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
                const defaultElemIcon = `/assets/elements/${gameId}_${elemKey}.png`;
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
                const defaultElemIcon = `/assets/elements/${gameId}_${elemKey}.png`;
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
        
        // 1. Renderiza Arma / Equipamento
        const lblWeaponName = document.getElementById("ins-weapon-name");
        const lblWeaponMeta = document.getElementById("ins-weapon-meta");
        const imgWeaponIcon = document.getElementById("ins-weapon-icon");
        
        if (char.weapon) {
            lblWeaponName.innerText = char.weapon.name || (isEn ? "Not equipped" : "Não equipado");
            const refLabel = gameId === "hsr" ? (isEn ? "Superimposition: S" : "Sobreposição: S") : (gameId === "zzz" ? (isEn ? "W-Engine: W" : "Motor W: W") : (isEn ? "Refinement: R" : "Refinamento: R"));
            const rVal = char.weapon.rarity || char.weapon_rarity || (build && build.weapon_rarity);
            const rStar = rVal ? (gameId === "zzz" ? (Number(rVal) === 5 ? "Rank S" : "Rank A") : `${rVal}★`) : "";
            const metaParts = [rStar, `${isEn ? "Level" : "Nível"} ${char.weapon.level || 1}`, `${refLabel}${char.weapon.rank || 1}`].filter(Boolean);
            lblWeaponMeta.innerText = metaParts.join(" • ");
            
            const safeWFn = getSafeFileName(char.weapon.name || "");
            imgWeaponIcon.src = `/assets/weapons/${gameId}/${safeWFn}`;
            imgWeaponIcon.onerror = function() {
                this.src = char.weapon.icon || '/assets/chat_icon.png';
            };
        } else {
            lblWeaponName.innerText = build.weapon || (isEn ? "Not specified" : "Não informado");
            lblWeaponMeta.innerText = isEn ? "Secondary level / Incomplete sync" : "Nível secundário / Sem sincronização completa";
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

        // NOVO: Renderiza Breakpoints de Ação & Speed Tuning (MoC / Ciclos)
        const bpCard = document.getElementById("ins-breakpoints-card");
        const bpList = document.getElementById("ins-breakpoints-list");
        const bpBadge = document.getElementById("ins-breakpoints-summary-badge");

        if (bpCard && bpList) {
            bpCard.style.display = "none";
            bpList.innerHTML = "";
            if (statsKeys.length > 0) {
                try {
                    const bpRes = await fetch("/api/stats/breakpoints", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            game_id: gameId,
                            char_name: char.name,
                            stats: build.stats
                        })
                    });
                    if (bpRes.ok) {
                        const bpData = await bpRes.json();
                        if (bpData && bpData.breakpoints && bpData.breakpoints.length > 0) {
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
                        }
                    }
                } catch (bpErr) {
                    console.error("Erro ao carregar breakpoints:", bpErr);
                }
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
                    <button class="trigger-export-card action-btn" style="padding: 5px 12px; font-size: 11px; background: linear-gradient(135deg, rgba(245, 158, 11, 0.25), rgba(217, 119, 6, 0.35)); border: 1px solid rgba(245, 158, 11, 0.6); color: #fbbf24; border-radius: 6px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; font-weight: 600;">
                        <i class="fa-solid fa-camera"></i> ${isEn ? "Generate Build Card (Splash Art)" : "Gerar Imagem da Build (Splash Art)"}
                    </button>
                </div>
            </div>
            <div class="overall-badge ${gradeClass}">
                ${badgeContent}
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
            piecesList.innerHTML = `<span class="text-muted">${isEn ? "Substats and piece breakdown unavailable for this Roster level." : "Substatus e peças detalhadas indisponíveis para este nível de Roster."}</span>`;
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
    if (inspector) {
        inspector.classList.remove("open");
        inspector.style.display = "";
    }
    if (inspectorOverlay) {
        inspectorOverlay.classList.remove("active");
        inspectorOverlay.style.display = "";
    }
}

const btnCloseInspector = document.getElementById("btn-close-inspector");
if (btnCloseInspector) btnCloseInspector.addEventListener("click", closeInspector);
const inspectorOverlay = document.getElementById("inspector-overlay");
if (inspectorOverlay) inspectorOverlay.addEventListener("click", closeInspector);

// Fechar modal ao pressionar a tecla Escape
window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        const inspector = document.getElementById("build-inspector");
        if (inspector && inspector.classList.contains("open")) {
            closeInspector();
        }
    }
});


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

const ELEMENT_LABELS_EN = {
    "zzz": {
        "electric": "Electric",
        "ether": "Ether",
        "fire": "Fire",
        "ice": "Ice",
        "physical": "Physical",
        "wind": "Wind",
        "lumiflux": "Lumiflux",
        "element_300": "Lumiflux",
        "element 300": "Lumiflux"
    },
    "hsr": {
        "fire": "Fire",
        "ice": "Ice",
        "imaginary": "Imaginary",
        "lightning": "Lightning",
        "physical": "Physical",
        "quantum": "Quantum",
        "wind": "Wind"
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
    const isEn = Boolean(window.isEn || (window.getCurrentLanguage && window.getCurrentLanguage() === 'en') || window.currentLang === 'en');
    if (!elementKey) return isEn ? "Unknown" : "Desconhecido";
    const kLower = elementKey.toLowerCase().trim();
    if (kLower === "element_300" || kLower === "element 300" || kLower === "lumiflux") return "Lumiflux";
    if (kLower === "element_100" || kLower === "element 100") return isEn ? "Physical" : "Físico";
    if (kLower === "element_200" || kLower === "element 200") return isEn ? "Fire" : "Fogo";
    if (kLower === "element_400" || kLower === "element 400") return isEn ? "Electric" : "Elétrico";
    if (kLower === "element_500" || kLower === "element 500") return isEn ? "Ether" : "Éter";
    const dict = isEn ? ELEMENT_LABELS_EN : ELEMENT_LABELS;
    const gameLabels = dict[gameId] || {};
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
    const isEn = Boolean(window.isEn || (window.getCurrentLanguage && window.getCurrentLanguage() === 'en') || window.currentLang === 'en');
    const rarities = {};
    if (gameId === "zzz") {
        const sLabel = isEn ? "S-Rank" : "Classe S";
        const aLabel = isEn ? "A-Rank" : "Classe A";
        rarities[sLabel] = 0;
        rarities[aLabel] = 0;
        chars.forEach(c => {
            const r = String(c.rarity || "").toUpperCase();
            if (r === "S" || r === "5") {
                rarities[sLabel]++;
            } else {
                rarities[aLabel]++;
            }
        });
        drawPieChart(`chart-rarity-${gameId}`, `legend-rarity-${gameId}`, [
            { label: sLabel, value: rarities[sLabel], color: "#f59e0b" },
            { label: aLabel, value: rarities[aLabel], color: "#a78bfa" }
        ]);
    } else {
        const legLabel = isEn ? "5★ Legendary" : "5★ Lendário";
        const epicLabel = isEn ? "4★ Epic" : "4★ Épico";
        rarities[legLabel] = 0;
        rarities[epicLabel] = 0;
        chars.forEach(c => {
            const r = Number(c.rarity);
            if (r === 5 || c.rarity === "5" || r === "S") {
                rarities[legLabel]++;
            } else {
                rarities[epicLabel]++;
            }
        });
        drawPieChart(`chart-rarity-${gameId}`, `legend-rarity-${gameId}`, [
            { label: legLabel, value: rarities[legLabel], color: "#f59e0b" },
            { label: epicLabel, value: rarities[epicLabel], color: "#8b5cf6" }
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
            img.onerror = () => resolve(null);
            img.src = finalUrl;
        });
    }

    const logoImg = (await loadImage("/assets/logo.png")) || (await loadImage("/assets/logo.webp")) || (await loadImage("/assets/logo.ico"));

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
    const overallGrade = (char.overall_grade || "N/A").toUpperCase();
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
        D: { bg: "rgba(107, 114, 128, 0.25)", border: "#6b7280", text: "#9ca3af" },
        "N/A": { bg: "rgba(107, 114, 128, 0.25)", border: "#6b7280", text: "#9ca3af" }
    };
    const gc = gradeColors[overallGrade] || gradeColors["N/A"];

    // ==========================================
    // 2. HERO COLUMN CONTINUA (COLUNA DA ESQUERDA)
    // ==========================================
    const hx = 30, hy = 25, hw = 390, hh = 615;
    
    // Container base da Hero Column
    drawRoundedRect(hx, hy, hw, hh, 16, "rgba(15, 23, 42, 0.65)", "rgba(255, 255, 255, 0.12)", 1.5);

    // Carregamento da Splash Art / Gacha Art / Eidolon Art
    let splashUrl = char.portrait || char.splash_art || char.eidolon_art || char.gacha_art || char.draw || char.art_url || char.gacha_card || char.gacha_slice || char.display_image || char.image || char.banner_icon;
    let effectiveId = null;
    let skinId = null;

    if (gameId === 'hsr') {
        const rawGacha = String(char.gacha_art || char.splash_art || char.portrait || "");
        const charNameLower = String(char.name || "").toLowerCase();
        const artUrlStr = `${char.icon || ''} ${char.gacha_art || ''} ${char.portrait || ''} ${char.splash_art || ''}`.toLowerCase();

        // 1. Resolução automática de ID a partir das propriedades diretas do personagem
        if (char.id && String(char.id).trim().match(/^\d+$/)) {
            effectiveId = String(char.id).trim();
        } else if (char.character_id && String(char.character_id).trim().match(/^\d+$/)) {
            effectiveId = String(char.character_id).trim();
        }

        // 2. Resolução automática dinâmica via roster global em memória (correspondência exata por nome)
        if (!effectiveId && window.globalRoster && Array.isArray(window.globalRoster[gameId])) {
            const found = window.globalRoster[gameId].find(c => 
                c && (c.name === char.name || (char.name && c.name && c.name.toLowerCase().trim() === char.name.toLowerCase().trim()))
            );
            if (found && (found.id || found.character_id)) {
                effectiveId = String(found.id || found.character_id);
            }
        }

        // 3. Fallback buscando padrão de ID apenas em URLs estruturadas de arte oficial (evita falsos positivos em hashes MD5)
        if (!effectiveId) {
            const skinMatch = artUrlStr.match(/(?:avatar_(?:skin_)?image|character_(?:portrait|preview))\/[^\s"']*?\/?(150[1-9]|151[0-5]|1414|\d{4})(?:@|\.|\/|$)/);
            if (skinMatch) {
                skinId = skinMatch[1];
                effectiveId = skinMatch[1];
            }
        }

        if (rawGacha.includes("avatar_skin_image")) {
            splashUrl = rawGacha.startsWith("/api/proxy_image") ? rawGacha : `/api/proxy_image?url=${encodeURIComponent(rawGacha)}`;
        } else if (effectiveId === "1505" || effectiveId === "1501" || charNameLower.includes("evanescia") || charNameLower.includes("sparxie")) {
            const actId = (effectiveId === "1505" || charNameLower.includes("evanescia")) ? "1505" : "1501";
            splashUrl = `/api/proxy_image?url=${encodeURIComponent(`https://act-webstatic.hoyoverse.com/game_record/hkrpg/custom/avatar_skin_image/${actId}@2x.png`)}`;
        } else if (effectiveId) {
            const portraitUrl = `/api/proxy_image?url=${encodeURIComponent(`https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/character_portrait/${effectiveId}.png`)}`;
            const previewUrl = `/api/proxy_image?url=${encodeURIComponent(`https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/character_preview/${effectiveId}.png`)}`;
            splashUrl = portraitUrl || previewUrl || char.portrait || char.splash_art;
        } else if (char.portrait || char.splash_art) {
            splashUrl = char.portrait || char.splash_art;
        } else if (char.eidolon_art) {
            splashUrl = char.eidolon_art;
        }
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

    if (!charImg && gameId === 'hsr') {
        const charId = effectiveId || char.id || (char.character_id ? String(char.character_id) : null);
        const candidates = [];
        if (charId) {
            candidates.push(`/api/proxy_image?url=${encodeURIComponent(`https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/character_preview/${charId}.png`)}`);
            candidates.push(`/api/proxy_image?url=${encodeURIComponent(`https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/character_portrait/${charId}.png`)}`);
        }

        if (char.name) {
            const rawClean = char.name.replace(/\s*\(.*?\)/g, '').normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLowerCase();
            const slug = rawClean.replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
            const strippedSlug = slug.replace(/^(aeon|skin)-+/, "");
            candidates.push(`/api/proxy_image?url=${encodeURIComponent(`https://cdn.prydwen.gg/images/honkai-star-rail/characters/${slug}_full.webp`)}`);
            candidates.push(`/api/proxy_image?url=${encodeURIComponent(`https://cdn.prydwen.gg/images/honkai-star-rail/characters/${strippedSlug}_full.webp`)}`);
            candidates.push(`/api/proxy_image?url=${encodeURIComponent(`https://cdn.prydwen.gg/images/honkai-star-rail/characters/${slug}_card.webp`)}`);
            candidates.push(`/api/proxy_image?url=${encodeURIComponent(`https://cdn.prydwen.gg/images/honkai-star-rail/characters/${strippedSlug}_card.webp`)}`);
        }

        if (char.portrait && char.portrait !== splashUrl) candidates.push(char.portrait);
        if (char.splash_art && char.splash_art !== splashUrl) candidates.push(char.splash_art);
        if (char.gacha_art && char.gacha_art !== splashUrl) candidates.push(char.gacha_art);
        if (char.eidolon_art && char.eidolon_art !== splashUrl) candidates.push(char.eidolon_art);

        for (const cand of candidates) {
            if (cand) {
                charImg = await loadImage(cand);
                if (charImg) break;
            }
        }
    }

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
            (splashUrl && (splashUrl.includes("role_square_avatar") || splashUrl.includes("UI_AvatarIcon_")) && !splashUrl.includes("Gacha") && !splashUrl.includes("painting") && !splashUrl.includes("Costume") && !splashUrl.includes("character_preview") && !splashUrl.includes("character_portrait"))) {
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
    const charDisplayName = typeof formatCharacterName === 'function' ? formatCharacterName(char.name) : char.name;
    ctx.fillText(charDisplayName.length > 15 ? charDisplayName.substring(0, 15) + "..." : charDisplayName, hx + 18, hy + 56);

    ctx.font = "500 13px sans-serif";
    ctx.fillStyle = "#cbd5e1";
    const elemName = formatElementDisplayName(char.element || "Físico").toUpperCase();
    const pathValCanvas = char.path || char.specialty || char.weapon_type || "";
    const pathNameCanvas = pathValCanvas && typeof formatPathName === 'function' ? " • " + formatPathName(pathValCanvas, gameId).toUpperCase() : "";
    ctx.fillText(`${(window.isEn || window.currentLang === "en") ? "Lv." : "Nv."} ${char.level} • ${elemName}${pathNameCanvas}`, hx + 18, hy + 76);

    // 2.2 Constelações / Eidolons / Mindscapes (6 Nódulos Visuais com Ícones e Destaque Ativo/Inativo)
    const rankPrefix = gameId === "genshin" ? "C" : (gameId === "zzz" ? "M" : "E");
    const rankStrVal = char.rank_str || `${rankPrefix}0`;
    const mRank = String(rankStrVal).match(/\d+/);
    const unlockedNum = mRank ? parseInt(mRank[0]) : 0;

    let cardRanks = char.ranks || char.constellations || char.mindscapes || [];
    if (!cardRanks || cardRanks.length === 0) {
        cardRanks = [];
        const namePrefix = gameId === "genshin" ? "Constelação" : (gameId === "zzz" ? "Mindscape" : "Eidolon");
        for (let p = 1; p <= 6; p++) {
            cardRanks.push({
                pos: p,
                name: `${namePrefix} ${p}`,
                icon: "",
                desc: "",
                is_unlocked: p <= unlockedNum
            });
        }
    }

    const defaultElemIcon = `/assets/elements/${gameId}_${elemKey}.png`;
    const rankImgs = await Promise.all(cardRanks.slice(0, 6).map(async rk => {
        const iconUrl = rk && rk.icon ? rk.icon : defaultElemIcon;
        return (await loadImage(iconUrl)) || (await loadImage(defaultElemIcon));
    }));

    // Desenha os 6 nódulos de Constelação/Eidolon em uma barra horizontal elegante com base glassmorphism
    const rkBoxX = hx + 12;
    const rkBoxY = hy + 84;
    const rkTotalW = hw - 24;
    const rkNodeH = 34;
    const rkNodeW = Math.floor((rkTotalW - 5 * 6) / 6); // ~56px

    // Placa de fundo semi-transparente para destaque sobre a Splash Art
    drawRoundedRect(rkBoxX - 4, rkBoxY - 4, rkTotalW + 8, rkNodeH + 8, 10, "rgba(8, 12, 22, 0.78)", "rgba(255, 255, 255, 0.10)", 1);

    cardRanks.slice(0, 6).forEach((rk, idx) => {
        const pos = rk.pos || (idx + 1);
        const isUnlocked = rk.is_unlocked !== undefined ? Boolean(rk.is_unlocked) : (pos <= unlockedNum);
        const nx = rkBoxX + idx * (rkNodeW + 6);
        const ny = rkBoxY;
        const rkImg = rankImgs[idx];

        if (isUnlocked) {
            // Nódulo Desbloqueado: Cor total, borda temática e leve destaque (Glow)
            drawRoundedRect(nx, ny, rkNodeW, rkNodeH, 8, "rgba(245, 158, 11, 0.22)", "rgba(245, 158, 11, 0.85)", 1.5);
            
            if (rkImg) {
                ctx.save();
                ctx.drawImage(rkImg, nx + 4, ny + 4, 26, 26);
                ctx.restore();
            } else {
                ctx.font = "bold 11px sans-serif";
                ctx.fillStyle = "#fbbf24";
                ctx.textAlign = "center";
                ctx.fillText(`${rankPrefix}${pos}`, nx + 16, ny + 21);
                ctx.textAlign = "left";
            }

            // Indicador / Texto Pos
            ctx.font = "bold 10px sans-serif";
            ctx.fillStyle = "#fbbf24";
            ctx.textAlign = "center";
            ctx.fillText(`${rankPrefix}${pos}`, nx + rkNodeW - 13, ny + 21);
            ctx.textAlign = "left";

            // Ponto de luz no canto superior
            ctx.beginPath();
            ctx.arc(nx + rkNodeW - 6, ny + 6, 2.5, 0, Math.PI * 2);
            ctx.fillStyle = "#34d399";
            ctx.fill();
        } else {
            // Nódulo Bloqueado: Desaturado (grayscale), opacidade reduzida (~35%) e sem borda ativa
            drawRoundedRect(nx, ny, rkNodeW, rkNodeH, 8, "rgba(15, 23, 42, 0.45)", "rgba(255, 255, 255, 0.05)", 1);

            if (rkImg) {
                ctx.save();
                ctx.globalAlpha = 0.35;
                if (ctx.filter !== undefined) {
                    ctx.filter = "grayscale(100%)";
                }
                ctx.drawImage(rkImg, nx + 4, ny + 4, 26, 26);
                ctx.restore();
            } else {
                ctx.font = "bold 10px sans-serif";
                ctx.fillStyle = "rgba(148, 163, 184, 0.45)";
                ctx.textAlign = "center";
                ctx.fillText(`${rankPrefix}${pos}`, nx + 16, ny + 21);
                ctx.textAlign = "left";
            }

            ctx.font = "500 10px sans-serif";
            ctx.fillStyle = "rgba(148, 163, 184, 0.35)";
            ctx.textAlign = "center";
            ctx.fillText(`${rankPrefix}${pos}`, nx + rkNodeW - 13, ny + 21);
            ctx.textAlign = "left";
        }
    });

    // 2.2b Affinitive Eidolon Bar (HSR ex_ranks) no Card Exportável do Personagem
    const cardExRanks = gameId === "hsr" && Array.isArray(char.ex_ranks)
        ? char.ex_ranks.filter(er => er && er.is_unlocked)
        : [];
    if (cardExRanks.length > 0) {
        const affEr = cardExRanks[0];
        const affIconUrl = affEr.icon || defaultElemIcon;
        const affImg = (await loadImage(affIconUrl)) || (await loadImage(defaultElemIcon));
        const affBoxY = rkBoxY + rkNodeH + 10;
        const affBoxH = 30;
        drawRoundedRect(rkBoxX - 4, affBoxY, rkTotalW + 8, affBoxH, 9, "rgba(14, 116, 144, 0.32)", "rgba(56, 189, 248, 0.80)", 1.2);
        if (affImg) {
            ctx.save();
            ctx.drawImage(affImg, rkBoxX + 4, affBoxY + 4, 22, 22);
            ctx.restore();
        }
        ctx.font = "bold 9px sans-serif";
        ctx.fillStyle = "#38bdf8";
        ctx.fillText("✦ AFFINITIVE", rkBoxX + 32, affBoxY + 13);

        ctx.font = "bold 10.5px sans-serif";
        ctx.fillStyle = "#f1f5f9";
        let affNameTxt = affEr.name || "Affinitive Eidolon";
        const maxAffW = rkTotalW - 56;
        while (ctx.measureText(affNameTxt).width > maxAffW && affNameTxt.length > 4) {
            affNameTxt = affNameTxt.slice(0, -1);
        }
        if (affNameTxt !== (affEr.name || "Affinitive Eidolon")) affNameTxt = affNameTxt.trim() + "…";
        ctx.fillText(affNameTxt, rkBoxX + 32, affBoxY + 25);

        ctx.beginPath();
        ctx.arc(rkBoxX + rkTotalW - 6, affBoxY + affBoxH / 2, 3, 0, Math.PI * 2);
        ctx.fillStyle = "#34d399";
        ctx.fill();
    }

    // Badge de Nota Geral no canto superior direito da Hero Column
    drawRoundedRect(hx + hw - 108, hy + 16, 92, 42, 10, gc.bg, gc.border, 1.5);
    ctx.font = "bold 13px sans-serif";
    ctx.fillStyle = gc.text;
    ctx.textAlign = "center";
    const gradeLabel = overallGrade === "N/A" ? "N/A" : `NOTA ${overallGrade}`;
    ctx.fillText(gradeLabel, hx + hw - 62, hy + 34);

    ctx.font = "500 10px sans-serif";
    ctx.fillStyle = "#e2e8f0";
    const scoreLabel = overallGrade === "N/A" ? "SEM EQUIP." : `${overallScore} pts`;
    ctx.fillText(scoreLabel, hx + hw - 62, hy + 49);
    ctx.textAlign = "left";

    // ==========================================
    // 2.3 PAINEL DE STATUS FINAIS (COMBAT STATS) — Hero Column
    // ==========================================
    const charStats = char.stats || {};
    const statKeys = Object.keys(charStats);
    if (statKeys.length > 0) {
        const statsPanelX = hx + 12;
        const statsPanelW = hw - 24;
        const statsPanelH = 92;
        const statsPanelY = hy + hh - 276;

        // Background glassmorphism do painel
        drawRoundedRect(statsPanelX, statsPanelY, statsPanelW, statsPanelH, 10,
            "rgba(10, 15, 26, 0.80)", "rgba(255, 255, 255, 0.10)", 1);

        ctx.font = "bold 9px sans-serif";
        ctx.fillStyle = "#38bdf8";
        ctx.fillText("STATUS FINAIS DE COMBATE", statsPanelX + 12, statsPanelY + 16);

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
        const cellW = (statsPanelW - 24) / cols;
        const cellH = (statsPanelH - 24) / rows;

        displayStats.forEach((key, idx) => {
            const col = idx % cols;
            const row = Math.floor(idx / cols);
            const cx = statsPanelX + 12 + col * cellW;
            const cy = statsPanelY + 22 + row * cellH;
            const isRec = isStatRecommendedForChar(key, char);
            const val = charStats[key];

            const cardBg = isRec ? "rgba(245, 158, 11, 0.12)" : "rgba(15, 23, 42, 0.55)";
            const cardBorder = isRec ? "rgba(245, 158, 11, 0.35)" : "rgba(255, 255, 255, 0.06)";
            drawRoundedRect(cx, cy, cellW - 4, cellH - 4, 4, cardBg, cardBorder, 1);

            ctx.font = "500 8px sans-serif";
            ctx.fillStyle = isRec ? "#d97706" : "#64748b";
            ctx.textAlign = "left";
            const cleanKey = sanitizeStatName(key);
            const shortKey = cleanKey.length > 11 ? cleanKey.substring(0, 10) + "." : cleanKey;
            ctx.fillText(shortKey.toUpperCase(), cx + 4, cy + 11);

            ctx.font = "bold 11px sans-serif";
            ctx.fillStyle = isRec ? "#fbbf24" : "#e2e8f0";
            ctx.fillText(val, cx + 4, cy + 24);
        });
    }

    // ==========================================
    // 2.4 BARRA DE HABILIDADES / TALENTOS / TRAÇOS COM ÍCONES E NÍVEIS
    // ==========================================
    const charSkills = char.skills || [];
    const skillImgs = await Promise.all(charSkills.slice(0, 5).map(async sk => {
        if (!sk || !sk.icon) return null;
        return await loadImage(sk.icon);
    }));

    const kx = hx + 12;
    const ky = hy + hh - 176;
    const kw = hw - 24;
    const kh = 50;

    drawRoundedRect(kx, ky, kw, kh, 10, "rgba(10, 15, 26, 0.85)", "rgba(168, 85, 247, 0.25)", 1);

    let skillsMainTitle = "TALENTOS";
    let skillsSubTitle = "HABILIDADES";
    if (gameId === "hsr") {
        skillsMainTitle = "TRAÇOS";
        skillsSubTitle = "HABILIDADES";
    } else if (gameId === "zzz") {
        skillsMainTitle = "HABILIDADES";

    skillsSubTitle = isEn ? "AGENT" : "AGENTE";
    }

    ctx.font = "bold 9px sans-serif";
    ctx.fillStyle = "#c084fc";
    ctx.fillText(skillsMainTitle, kx + 12, ky + 19);

    ctx.font = "500 8px sans-serif";
    ctx.fillStyle = "#94a3b8";
    ctx.fillText(skillsSubTitle, kx + 12, ky + 33);

    const maxDisplaySkills = Math.min(5, charSkills.length);
    if (maxDisplaySkills > 0) {
        const skStart = kx + 88;
        const availW = kw - 96;
        const skW = Math.floor((availW - (maxDisplaySkills - 1) * 6) / maxDisplaySkills);

        charSkills.slice(0, maxDisplaySkills).forEach((sk, sIdx) => {
            const sx = skStart + sIdx * (skW + 6);
            const sy = ky + 6;
            const skImg = skillImgs[sIdx];
            const skLvl = parseInt(sk.level) || 1;
            const isBoosted = skLvl >= 10;

            const cardBorder = isBoosted ? "rgba(245, 158, 11, 0.5)" : "rgba(168, 85, 247, 0.3)";
            const cardBg = isBoosted ? "rgba(245, 158, 11, 0.15)" : "rgba(15, 23, 42, 0.75)";
            drawRoundedRect(sx, sy, skW, 38, 6, cardBg, cardBorder, 1);

            if (skImg) {
                ctx.drawImage(skImg, sx + (skW - 24) / 2, sy + 3, 24, 24);
            }

            // Badge de nível sobreposta na parte inferior do ícone
            const badgeW = 32;
            const badgeH = 13;
            const badgeX = sx + (skW - badgeW) / 2;
            const badgeY = sy + 23;
            const badgeBg = isBoosted ? "rgba(245, 158, 11, 0.95)" : "rgba(168, 85, 247, 0.9)";
            drawRoundedRect(badgeX, badgeY, badgeW, badgeH, 4, badgeBg, isBoosted ? "#fbbf24" : "#c084fc", 0.8);

            ctx.font = "bold 9px sans-serif";
            ctx.fillStyle = "#ffffff";
            ctx.textAlign = "center";
            ctx.fillText(`Nv.${skLvl}`, badgeX + badgeW / 2, badgeY + 10);
            ctx.textAlign = "left";
        });
    } else {
        ctx.font = "italic 10px sans-serif";
        ctx.fillStyle = "#64748b";
        ctx.fillText("Habilidades sincronizadas no roster", kx + 92, ky + 28);
    }

    // ==========================================
    // 2.5 CARD DA ARMA ACOPLADO NA BASE DA HERO COLUMN
    // ==========================================
    const wx = hx + 12, wy = hy + hh - 120, ww = hw - 24, wh = 56;
    drawRoundedRect(wx, wy, ww, wh, 10, "rgba(10, 15, 26, 0.85)", "rgba(255, 255, 255, 0.12)", 1);

    const weapon = char.weapon;
    if (weapon && weapon.name) {
        const safeWFn = getSafeFileName(weapon.name);
        const weaponUrl = `/assets/weapons/${gameId}/${safeWFn}`;
        const weaponImg = (await loadImage(weapon.icon)) || (await loadImage(weaponUrl));

        if (weaponImg) {
            drawRoundedRect(wx + 8, wy + 8, 40, 40, 6, "rgba(0,0,0,0.5)", "rgba(255,255,255,0.1)", 1);
            ctx.drawImage(weaponImg, wx + 10, wy + 10, 36, 36);
        }
        const textX = weaponImg ? wx + 54 : wx + 12;
        ctx.font = "bold 12px sans-serif";
        ctx.fillStyle = "#ffffff";
        ctx.fillText(weapon.name.length > 22 ? weapon.name.substring(0, 22) + "..." : weapon.name, textX, wy + 24);

        ctx.font = "500 11px sans-serif";
        ctx.fillStyle = "#cbd5e1";
        ctx.fillText(`Nv. ${weapon.level || 90} • Refinamento R${weapon.rank || 1}`, textX, wy + 42);
    } else {
        ctx.font = "italic 11px sans-serif";
        ctx.fillStyle = "#64748b";

    ctx.fillText(isEn ? "No weapon equipped" : "Nenhuma arma equipada", wx + 12, wy + 32);
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
            
            let mainFontSize = 12;
            ctx.font = `bold ${mainFontSize}px sans-serif`;
            while (ctx.measureText(mainText).width > mainW - 14 && mainFontSize > 8) {
                mainFontSize -= 0.5;
                ctx.font = `bold ${mainFontSize}px sans-serif`;
            }
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

    const logoImg = (await loadImage(`/assets/${gameId}_icon.png`)) || (await loadImage("/assets/logo.png"));

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

    ctx.fillText(isEn ? "Character ranking based on mathematical relic scoring" : "Classificação dos seus personagens baseada no score matemático das relíquias", 30, 100);

    const kpis = [
        { label: isEn ? "TOTAL CHARACTERS" : "TOTAL PERSONAGENS", val: `${auditData.total_characters || 0}`, color: "#38bdf8" },
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
            ctx.fillText(isEn ? "No characters in this category" : "Nenhum personagem nesta categoria", charStartX, currentY + rowH / 2 + 4);
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
                const cFormatted = typeof formatCharacterName === 'function' ? formatCharacterName(c.name) : c.name;
                const cName = cFormatted.length > 14 ? cFormatted.substring(0, 13) + "." : cFormatted;
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

    showToast(isEn ? "Error: No character selected." : "Erro: Nenhum personagem selecionado.");
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
            // Garante dados completos de ranks, skills e artwork caso ainda não sincronizados
            try {
                const bRes = await fetch(`/api/build/${window.currentInspectorGameId}/${encodeURIComponent(window.currentInspectorChar.name)}`);
                const bData = await bRes.json();
                if (bData) {
                    if (bData.ranks && bData.ranks.length > 0) window.currentInspectorChar.ranks = bData.ranks;
                    if (Array.isArray(bData.ex_ranks)) window.currentInspectorChar.ex_ranks = bData.ex_ranks;
                    if (bData.skills && bData.skills.length > 0) window.currentInspectorChar.skills = bData.skills;
                    if (bData.eidolon_art) window.currentInspectorChar.eidolon_art = bData.eidolon_art;
                    if (bData.portrait) window.currentInspectorChar.portrait = bData.portrait;
                    if (bData.splash_art) window.currentInspectorChar.splash_art = bData.splash_art;
                    if (bData.gacha_art) window.currentInspectorChar.gacha_art = bData.gacha_art;
                    if (bData.id) window.currentInspectorChar.id = bData.id;
                }
            } catch (bErr) {
                console.warn("Auto-sync build data for export:", bErr);
            }

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
            exportCardStatus.innerHTML = `<span style="color: var(--color-danger);"><i class="fa-solid fa-triangle-exclamation"></i> Erro ao gerar imagem da build: ${err.message}</span>`;
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

    const charName = window.currentInspectorChar ? window.currentInspectorChar.name : (isEn ? "Character" : "Personagem");
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

    const charName = window.currentInspectorChar ? window.currentInspectorChar.name : (isEn ? "Character" : "Personagem");
                const gameId = window.currentInspectorGameId || "hoyo";
                const link = document.createElement("a");
                link.download = `Build_${getSafeFileName(charName)}_${gameId.toUpperCase()}.png`;
                link.href = currentGeneratedCanvas.toDataURL("image/png");
                link.click();
            });
        }
    }
});



window.addEventListener("app:languageChanged", () => {
    ["zzz", "genshin", "hsr"].forEach(g => {
        const gal = document.getElementById(`gallery-${g}`);
        if (gal && globalRoster && globalRoster[g] && globalRoster[g].length > 0) {
            loadRoster(g);
        }
    });
});

// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
if (typeof ELEMENT_LABELS !== 'undefined') window.ELEMENT_LABELS = ELEMENT_LABELS;
if (typeof btnCloseInspector !== 'undefined') window.btnCloseInspector = btnCloseInspector;
if (typeof cleanHoyoverseText !== 'undefined') window.cleanHoyoverseText = cleanHoyoverseText;
if (typeof closeInspector !== 'undefined') window.closeInspector = closeInspector;
if (typeof drawPieChart !== 'undefined') window.drawPieChart = drawPieChart;
if (typeof escapeHtml !== 'undefined') window.escapeHtml = escapeHtml;
if (typeof generateBuildCardCanvas !== 'undefined') window.generateBuildCardCanvas = generateBuildCardCanvas;
if (typeof getElementLabel !== 'undefined') window.getElementLabel = getElementLabel;
if (typeof getSlotIcon !== 'undefined') window.getSlotIcon = getSlotIcon;
if (typeof getZzzPrydwenSlug !== 'undefined') window.getZzzPrydwenSlug = getZzzPrydwenSlug;
if (typeof hoyoTooltipInitialized !== 'undefined') window.hoyoTooltipInitialized = hoyoTooltipInitialized;
if (typeof inspectCharacter !== 'undefined') window.inspectCharacter = inspectCharacter;
if (typeof inspectorOverlay !== 'undefined') window.inspectorOverlay = inspectorOverlay;
if (typeof loadRoster !== 'undefined') window.loadRoster = loadRoster;
if (typeof renderGameCharts !== 'undefined') window.renderGameCharts = renderGameCharts;
if (typeof renderRosterCharts !== 'undefined') window.renderRosterCharts = renderRosterCharts;
if (typeof setupHoyoCustomTooltip !== 'undefined') window.setupHoyoCustomTooltip = setupHoyoCustomTooltip;
if (typeof setupRosterViewModeToggle !== 'undefined') window.setupRosterViewModeToggle = setupRosterViewModeToggle;
if (typeof setRosterViewMode !== 'undefined') window.setRosterViewMode = setRosterViewMode;