// ==========================================================================
// Módulo: card_exporter.js (Extraído de roster.js)
// Gerador de Cards HD (Build & Tier List) e Modal de Exportação PNG
// ==========================================================================

function _cardIsEn() {
    return Boolean(window.isEn || (window.getCurrentLanguage && window.getCurrentLanguage() === 'en') || window.currentLang === 'en');
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

    const isEn = _cardIsEn();
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
    const isEn = _cardIsEn();
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
        const isEn = _cardIsEn();
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
        const auditTabs = document.getElementById("audit-game-tabs");
        const activeTabBtn = document.querySelector(".tab-audit-game-btn.active") || document.querySelector(".audit-game-tab.active");
        const gameId = targetGameId || auditTabs?.value || (activeTabBtn ? activeTabBtn.dataset.game : null) || window.currentAuditGameId || window.activeGameTab || "hsr";
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
                const auditTabs = document.getElementById("audit-game-tabs");
                const activeTabBtn = document.querySelector(".tab-audit-game-btn.active") || document.querySelector(".audit-game-tab.active");
                const gId = btn.dataset.game || auditTabs?.value || (activeTabBtn ? activeTabBtn.dataset.game : null) || window.currentAuditGameId || "hsr";
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
                const isEn = _cardIsEn();

    const charName = window.currentInspectorChar ? window.currentInspectorChar.name : (isEn ? "Character" : "Personagem");
                const gameId = window.currentInspectorGameId || "hoyo";
                const fileName = window.currentExportCardName ? window.currentExportCardName : `Build_${getSafeFileName(charName)}_${gameId.toUpperCase()}`;
                const link = document.createElement("a");
                link.download = `${fileName}.png`;
                link.href = currentGeneratedCanvas.toDataURL("image/png");
                link.click();
                if (typeof btnDownloadCardImg.done === "function") btnDownloadCardImg.done();
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
                        if (typeof btnCopyCardImg.done === "function") btnCopyCardImg.done();
                        showToast("Imagem copiada para a área de transferência! (Pressione Ctrl+V no Discord/WhatsApp)");
                        return;
                    } catch (clipErr) {
                        console.warn("navigator.clipboard.write falhou:", clipErr);
                    }
                }

                showToast("Navegadores em conexões HTTP de celular/rede local bloqueiam a cópia direta. Baixando PNG...");
                const isEn = _cardIsEn();
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



if (typeof getZzzPrydwenSlug !== 'undefined') window.getZzzPrydwenSlug = getZzzPrydwenSlug;
if (typeof generateBuildCardCanvas !== 'undefined') window.generateBuildCardCanvas = generateBuildCardCanvas;
