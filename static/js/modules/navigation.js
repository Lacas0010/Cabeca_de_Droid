// ==========================================================================
// Módulo: navigation.js
// Cabeça de Droid - Vanilla ES6 Module
// ==========================================================================

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
        const inspector = document.getElementById("build-inspector");
        const overlay = document.getElementById("inspector-overlay");
        if (inspector) {
            inspector.classList.remove("open");
            inspector.style.display = "";
        }
        if (overlay) {
            overlay.classList.remove("active");
            overlay.style.display = "";
        }
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
                if (targetTab === 'home') {
                    if (window.loadDailyFarmOrder) window.loadDailyFarmOrder(window.currentFarmOrderGame || 'genshin');
                    if (window.loadAccountsManagement) window.loadAccountsManagement();
                }
                if (targetTab === 'config' && window.loadAccountsManagement) {
                    window.loadAccountsManagement();
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
// CONTROLE DE SUB-NAVEGAÇÃO DAS ABAS DE JOGO (GALERIA / ENDGAME / STATS)
// ==========================================================================
function setupSubnavTabs() {
    document.querySelectorAll(".game-subnav-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const gameId = btn.getAttribute("data-game");
            const targetView = btn.getAttribute("data-view");
            if (!gameId || !targetView) return;

            const section = document.getElementById(`tab-${gameId}`);
            if (!section) return;

            // Atualiza botões da sub-barra
            section.querySelectorAll(".game-subnav-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            // Alterna subviews
            section.querySelectorAll(".game-subview").forEach(v => v.classList.remove("active"));
            const targetEl = document.getElementById(`view-${targetView}-${gameId}`);
            if (targetEl) {
                targetEl.classList.add("active");
            }

            // Se mudou para charts, redesenha os gráficos SVG
            if (targetView === "charts") {
                renderRosterCharts();
            }
            if (targetView === "teamcard" && window.renderTeamBuilderView) {
                window.renderTeamBuilderView(gameId);
            }
        });
    });
}



// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
if (typeof closeInspector !== 'undefined') window.closeInspector = closeInspector;
if (typeof setupSidebarToggle !== 'undefined') window.setupSidebarToggle = setupSidebarToggle;
if (typeof setupSubnavTabs !== 'undefined') window.setupSubnavTabs = setupSubnavTabs;
if (typeof setupTabSwitching !== 'undefined') window.setupTabSwitching = setupTabSwitching;