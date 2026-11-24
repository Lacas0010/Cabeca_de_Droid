import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT_DIR / "static"


class TestQuickSearchAndEtapa6AuditSuite(unittest.TestCase):
    """Testes unitários offline da revisão da Etapa 6 e da Etapa 7 (Busca Rápida Global Ctrl+K)."""

    def test_etapa6_gacha_prefill_uses_real_dom_selectors(self):
        gacha_js = (STATIC_DIR / "js" / "modules" / "gacha_sim.js").read_text(encoding="utf-8")
        self.assertIn("window.prefillGachaBannerTarget", gacha_js)
        self.assertIn('document.getElementById("gacha-subnav-tabs")', gacha_js)
        self.assertIn('document.getElementById("gacha-view-sim")', gacha_js)
        self.assertIn("#gacha-game-pills .gacha-game-pill", gacha_js)
        self.assertIn("#gacha-sim-type-pills .sim-type-btn", gacha_js)
        self.assertNotIn("#gacha-view-simulator", gacha_js)

    def test_quick_search_modal_and_triggers_present_in_html(self):
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="btn-open-quick-search"', html)
        self.assertIn('id="btn-open-quick-search-mobile"', html)
        self.assertIn('id="quick-search-overlay"', html)
        self.assertIn('id="quick-search-input"', html)
        self.assertIn('id="quick-search-results"', html)

    def test_quick_search_module_keyboard_and_navigation_contracts(self):
        qs_js = (STATIC_DIR / "js" / "modules" / "quick_search.js").read_text(encoding="utf-8")
        self.assertIn("function setupQuickSearch", qs_js)
        self.assertIn("window.openQuickSearch = openQuickSearch", qs_js)
        self.assertIn("window.closeQuickSearch = closeQuickSearch", qs_js)
        self.assertIn("ArrowDown", qs_js)
        self.assertIn("ArrowUp", qs_js)
        self.assertIn("Enter", qs_js)
        self.assertIn("Escape", qs_js)
        self.assertIn("inspectCharacter", qs_js)
        self.assertIn("navigateToEndgameMode", qs_js)
        self.assertIn("globalRoster", qs_js)
        self.assertIn("SakugaFX", qs_js)
        self.assertIn("onerror=", qs_js)

    def test_quick_search_styles_i18n_and_app_wiring(self):
        style_css = (STATIC_DIR / "style.css").read_text(encoding="utf-8")
        self.assertIn(".quick-search-overlay", style_css)
        self.assertIn(".quick-search-modal", style_css)
        self.assertIn(".quick-search-item", style_css)
        self.assertIn(".sidebar-quick-search-btn", style_css)
        self.assertIn(".mobile-quick-search-btn", style_css)

        i18n_js = (STATIC_DIR / "js" / "modules" / "i18n.js").read_text(encoding="utf-8")
        self.assertIn("quick_search_trigger:", i18n_js)
        self.assertIn("quick_search_placeholder:", i18n_js)

        app_js = (STATIC_DIR / "js" / "app.js").read_text(encoding="utf-8")
        self.assertIn('import "./modules/quick_search.js?v=1.0";', app_js)
        self.assertIn("setupQuickSearch();", app_js)


if __name__ == "__main__":
    unittest.main()
