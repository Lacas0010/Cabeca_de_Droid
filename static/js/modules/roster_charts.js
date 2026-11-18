// ==========================================================================
// Módulo: roster_charts.js (Extraído de roster.js)
// Gráficos SVG de distribuição elemental e de raridade do Roster
// ==========================================================================

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


if (typeof ELEMENT_LABELS !== 'undefined') window.ELEMENT_LABELS = ELEMENT_LABELS;
if (typeof getElementLabel !== 'undefined') window.getElementLabel = getElementLabel;
if (typeof renderRosterCharts !== 'undefined') window.renderRosterCharts = renderRosterCharts;
if (typeof renderGameCharts !== 'undefined') window.renderGameCharts = renderGameCharts;
if (typeof drawPieChart !== 'undefined') window.drawPieChart = drawPieChart;
