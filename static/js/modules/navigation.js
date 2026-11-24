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
                if (targetTab !== "gacha" && window.stopGoalsLiveCountdown) {
                    window.stopGoalsLiveCountdown();
                }
                if (["zzz", "genshin", "hsr"].includes(targetTab) && window._flushDirtyRosterLang) {
                    window._flushDirtyRosterLang(targetTab);
                }
                if (targetTab === 'gacha') {
                    const onGachaReady = () => {
                        if (window.initGachaNavigation) window.initGachaNavigation();
                        if (window.initGachaSimulator) window.initGachaSimulator();
                        const goalsView = document.getElementById("gacha-view-goals");
                        if (goalsView?.classList.contains("active")) {
                            if (window._dirtyLangTabs?.gachaGoals) {
                                window._dirtyLangTabs.gachaGoals = false;
                                window.loadGachaGoals?.("all");
                            } else if (document.querySelector(".gacha-goal-live-card")) {
                                window.startGoalsLiveCountdown?.();
                            }
                        }
                    };
                    if (window.loadGachaModules) {
                        window.loadGachaModules().then(onGachaReady).catch(err => {
                            console.error("[NAV] Falha ao carregar módulos de Gacha:", err);
                            if (typeof showToast === "function") {
                                showToast(window.isEn ? "Failed to load Gacha module. Please reload." : "Falha ao carregar o módulo de Gacha. Tente recarregar.", "error");
                            }
                        });
                    } else {
                        onGachaReady();
                    }
                }
                if (targetTab === 'luck') {
                    if (window.loadGachaModules) {
                        window.loadGachaModules().then(() => {
                            if (window._dirtyLangTabs?.luck) window._dirtyLangTabs.luck = false;
                            if (window.initLuckDashboard) window.initLuckDashboard();
                        }).catch(err => {
                            console.error("[NAV] Falha ao carregar módulo Luck:", err);
                            if (typeof showToast === "function") {
                                showToast(window.isEn ? "Failed to load Roll Efficiency module." : "Falha ao carregar o módulo Roll Efficiency.", "error");
                            }
                        });
                    } else if (window.initLuckDashboard) {
                        if (window._dirtyLangTabs?.luck) window._dirtyLangTabs.luck = false;
                        window.initLuckDashboard();
                    }
                }
                if (targetTab === 'home') {
                    if (window.loadDailyFarmOrder) window.loadDailyFarmOrder(window.currentFarmOrderGame || 'genshin');
                    if (window.loadAccountsManagement) window.loadAccountsManagement();
                    if (window._dirtyLangTabs?.homeBriefing && typeof window.loadMorningBriefing === "function") {
                        window._dirtyLangTabs.homeBriefing = false;
                        window.loadMorningBriefing();
                    }
                    if (window._dirtyLangTabs?.homeRadar && typeof window.loadHomeResetRadar === "function") {
                        window._dirtyLangTabs.homeRadar = false;
                        window.loadHomeResetRadar(true);
                    }
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
function activateGameSubview(gameId, targetView) {
    if (!gameId || !targetView) return;
    const section = document.getElementById(`tab-${gameId}`);
    if (!section) return;

    section.querySelectorAll(".game-subview").forEach(v => v.classList.remove("active"));
    const targetEl = document.getElementById(`view-${targetView}-${gameId}`);
    if (targetEl) {
        targetEl.classList.add("active");
    }

    if (targetView === "charts") {
        renderRosterCharts();
    }
    if (targetView === "teamcard" && window.renderTeamBuilderView) {
        window.renderTeamBuilderView(gameId);
    }
}

function setupSubnavTabs() {
    document.querySelectorAll("sakuga-tabs.sk-game-subnav").forEach(tabsEl => {
        tabsEl.addEventListener("change", (e) => {
            const gameId = tabsEl.getAttribute("data-game");
            const targetView = e?.detail?.value || tabsEl.value;
            activateGameSubview(gameId, targetView);
        });
    });

    document.querySelectorAll(".game-subnav-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const gameId = btn.getAttribute("data-game");
            const targetView = btn.getAttribute("data-view");
            if (!gameId || !targetView) return;

            const section = document.getElementById(`tab-${gameId}`);
            if (!section) return;

            section.querySelectorAll(".game-subnav-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activateGameSubview(gameId, targetView);
        });
    });
}



// Exposição explícita para compatibilidade com handlers inline HTML e outros módulos
if (typeof activateGameSubview !== 'undefined') window.activateGameSubview = activateGameSubview;
if (typeof closeInspector !== 'undefined') window.closeInspector = closeInspector;
if (typeof setupSidebarToggle !== 'undefined') window.setupSidebarToggle = setupSidebarToggle;
if (typeof setupSubnavTabs !== 'undefined') window.setupSubnavTabs = setupSubnavTabs;
if (typeof setupTabSwitching !== 'undefined') window.setupTabSwitching = setupTabSwitching;