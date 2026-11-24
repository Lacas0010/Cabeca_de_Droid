import os
import re
import unittest
from pathlib import Path
from bs4 import BeautifulSoup


ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT_DIR / "static"
JS_DIR = STATIC_DIR / "js"
MODULES_DIR = JS_DIR / "modules"
CSS_DIR = STATIC_DIR / "css"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestFrontendOptimizationSuite(unittest.TestCase):
    """Regressão e verificação das correções e otimizações do frontend."""

    def test_dead_legacy_entrypoint_removed(self):
        self.assertFalse((STATIC_DIR / "app.js").exists())

    def test_no_clone_node_in_roster_and_sakuga_intact(self):
        roster_js = _read(MODULES_DIR / "roster.js")
        self.assertNotIn("cloneNode(", roster_js)
        self.assertNotIn("replaceChild(", roster_js)
        self.assertIn("dataset.bound", roster_js)
        self.assertIn("_rosterFilterActions", roster_js)

        sakuga_btn = _read(STATIC_DIR / "vendor" / "sakuga-vfx" / "button.js")
        self.assertIn("isOccluded", sakuga_btn)

    def test_gacha_simulator_one_time_guard_and_state_preservation(self):
        gacha_js = _read(MODULES_DIR / "gacha_sim.js")
        self.assertIn("_gachaSimulatorInitialized", gacha_js)
        self.assertNotIn("#tab-btn-open-wish-anim", gacha_js)
        # Deve inicializar a partir do estado/select atual, não sobrescrever para "genshin"/"character"
        self.assertIn("const initGame = gameSelectHidden?.value || window.gachaState?.gameId", gacha_js)
        self.assertIn("const initType = bannerTypeHidden?.value || window.gachaState?.bannerType", gacha_js)

    def test_lazy_imports_catch_rejections(self):
        app_js = _read(JS_DIR / "app.js")
        nav_js = _read(MODULES_DIR / "navigation.js")
        self.assertIn("loadGachaModules().catch", app_js)
        self.assertGreaterEqual(nav_js.count("loadGachaModules().then"), 2)
        self.assertGreaterEqual(nav_js.count(").catch("), 2)

    def test_async_race_conditions_guarded_with_abort_and_seq_ids(self):
        roster_js = _read(MODULES_DIR / "roster.js")
        self.assertIn("_inspectController", roster_js)
        self.assertIn("_inspectReqId", roster_js)

        comp_js = _read(MODULES_DIR / "build_comparator.js")
        self.assertIn("_compareController", comp_js)
        self.assertIn("_compareReqId", comp_js)

        gacha_js = _read(MODULES_DIR / "gacha_sim.js")
        self.assertIn("_gachaCharController", gacha_js)
        self.assertIn("_gachaCharReqId", gacha_js)

    def test_concurrent_inspector_stats_and_breakpoints(self):
        roster_js = _read(MODULES_DIR / "roster.js")
        inspect_body = roster_js.split("async function inspectCharacter", 1)[1]
        self.assertIn("Promise.allSettled([evalPromise, bpPromise])", inspect_body)
        self.assertIn("/api/evaluate-stats/", inspect_body)
        self.assertIn("/api/stats/breakpoints", inspect_body)

    def test_timers_capped_and_paused_when_hidden(self):
        sync_js = _read(MODULES_DIR / "sync_manager.js")
        self.assertIn("MAX_POLL_ERRORS", sync_js)
        self.assertIn("consecutiveErrors", sync_js)
        self.assertIn("if (!res.ok)", sync_js)

        gacha_js = _read(MODULES_DIR / "gacha_sim.js")
        self.assertIn("isGoalsViewVisible", gacha_js)
        self.assertIn("stopGoalsLiveCountdown", gacha_js)
        self.assertIn("visibilitychange", gacha_js)

    def test_language_storage_key_consistency_and_ui_fixes(self):
        for js_file in list(MODULES_DIR.glob("*.js")) + [JS_DIR / "app.js"]:
            content = _read(js_file)
            self.assertNotIn('"app_language"', content, f"Key errada em {js_file.name}")
            self.assertNotIn("'app_language'", content, f"Key errada em {js_file.name}")
            self.assertNotIn("hoyo_app_language", content, f"Key errada em {js_file.name}")

        chat_js = _read(MODULES_DIR / "chat_rag.js")
        self.assertNotIn("document.getElementById(typingId).remove()", chat_js)
        self.assertIn("document.getElementById(typingId)?.remove()", chat_js)
        self.assertNotIn("const defaultWelcomeHTML", chat_js)
        self.assertIn("requestAnimationFrame", chat_js)
        self.assertIn("streamChatResponse", chat_js)

        comp_js = _read(MODULES_DIR / "build_comparator.js")
        self.assertIn("const origBtnHtml = btn.innerHTML", comp_js)
        self.assertIn("btn.innerHTML = origBtnHtml", comp_js)

        gacha_js = _read(MODULES_DIR / "gacha_sim.js")
        self.assertIn("btn.dataset.origHtml", gacha_js)
        self.assertIn("clearTimeout(btn._copyTimeoutId)", gacha_js)

        farming_js = _read(MODULES_DIR / "farming.js")
        self.assertNotIn("Notification.requestPermission()", farming_js)
        self.assertNotIn("window.initGachaSimulator()", farming_js)

    def test_language_switch_uses_cached_roster_and_gates_hidden_tabs(self):
        roster_js = _read(MODULES_DIR / "roster.js")
        lang_section = roster_js.split('window.addEventListener("app:languageChanged"', 1)[1]
        self.assertNotIn("loadRoster(", lang_section)
        self.assertIn("_rosterRenderers[g]", lang_section)
        self.assertIn("_dirtyRosterLang", lang_section)

        farming_js = _read(MODULES_DIR / "farming.js")
        self.assertIn('tabFarm?.classList.contains("active")', farming_js)
        self.assertIn('tabTrash?.classList.contains("active")', farming_js)
        self.assertIn('tabAudit?.classList.contains("active")', farming_js)

        tracker_js = _read(MODULES_DIR / "gacha_tracker.js")
        self.assertIn('trackerView?.classList.contains("active")', tracker_js)

    def test_farm_modal_toggle_avoids_full_grid_rebuild(self):
        farming_js = _read(MODULES_DIR / "farming.js")
        m = re.search(
            r"window\.toggleFarmModalCharCard\s*=\s*\(charName\)\s*=>\s*\{(.*?)\};",
            farming_js,
            re.DOTALL,
        )
        self.assertIsNotNone(m)
        body = m.group(1)
        self.assertNotIn("renderFarmModalGrid()", body)
        self.assertIn('classList.toggle("selected"', body)

    def test_helper_deduplication_preserves_globals(self):
        nav_js = _read(MODULES_DIR / "navigation.js")
        roster_js = _read(MODULES_DIR / "roster.js")
        api_js = _read(MODULES_DIR / "api_client.js")
        card_js = _read(MODULES_DIR / "card_exporter.js")
        endgame_js = _read(MODULES_DIR / "endgame.js")

        self.assertIn("function closeInspector", nav_js)
        self.assertIn("window.closeInspector = closeInspector", nav_js)
        self.assertNotIn("function closeInspector", roster_js)

        self.assertIn("function getSlotIcon", api_js)
        self.assertIn("window.getSlotIcon = getSlotIcon", api_js)
        self.assertNotIn("function getSlotIcon", roster_js)

        self.assertNotIn("function _cardIsEn", card_js)
        self.assertNotIn("function checkIsEn", endgame_js)

    def test_html_and_css_cleanup_and_scroll_constraints(self):
        html = _read(STATIC_DIR / "index.html")
        soup = BeautifulSoup(html, "html.parser")
        self.assertIsNone(soup.find("style", id="wish-inline-fx-styles"))
        for card in soup.select(".start-guide-card"):
            style_attr = (card.get("style") or "").replace(" ", "").lower()
            self.assertNotIn("display:none", style_attr)

        style_css = _read(STATIC_DIR / "style.css")
        self.assertEqual(style_css.count(".badge-relic-sss"), 1)
        self.assertNotIn(".think-details", style_css)
        self.assertNotIn(".char-relics-empty", style_css)
        # Nenhum bloco .char-card pode usar content-visibility: auto
        style_no_comments = re.sub(r"/\*.*?\*/", "", style_css, flags=re.DOTALL)
        for m in re.finditer(r"([^{}]*\.char-card[^{}]*)\{([^}]*)\}", style_no_comments):
            self.assertNotIn("content-visibility: auto", m.group(2))
        # Scroll containers em #build-inspector (.inspector-body) e modais devem preservar overflow-y: auto
        inspector_body_m = re.search(r"(?:^|\n)\.inspector-body\s*\{([^}]*)\}", style_no_comments)
        self.assertIsNotNone(inspector_body_m)
        self.assertIn("overflow-y: auto", inspector_body_m.group(1))
        self.assertNotIn("overflow: visible", inspector_body_m.group(1))
        modal_content_m = re.search(r"(?:^|\n)\.modal-card-content\s*\{([^}]*)\}", style_no_comments)
        self.assertIsNotNone(modal_content_m)
        self.assertIn("overflow-y: auto", modal_content_m.group(1))
        self.assertIn("css/help_security.css?v=2.0", html)
        self.assertIn("css/gacha.css?v=2.3", html)
        self.assertIn("css/endgame_strategy.css?v=2.5", html)
        self.assertIn("css/team_card.css?v=2.0", html)
        self.assertIn("style.css?v=37.0", html)
        self.assertIn("js/app.js?v=54.0", html)

        gacha_css = _read(CSS_DIR / "gacha.css")
        self.assertEqual(gacha_css.count("@keyframes wishCardPop"), 1)
        self.assertNotIn(".wish-crt-overlay", gacha_css)
        self.assertNotIn(".wish-reveal-card", gacha_css)
        self.assertIn("#wish-skip-btn", gacha_css)

        team_css = _read(CSS_DIR / "team_card.css")
        self.assertIn("@media (max-width: 768px)", team_css)
        help_css = _read(CSS_DIR / "help_security.css")
        self.assertIn("@media (max-width: 768px)", help_css)

        app_js = _read(JS_DIR / "app.js")
        for mod_ver in [
            "i18n.js?v=32.0",
            "api_client.js?v=32.0",
            "navigation.js?v=27.0",
            "sync_manager.js?v=28.0",
            "endgame.js?v=31.0",
            "roster.js?v=33.0",
            "card_exporter.js?v=2.0",
            "build_comparator.js?v=28.0",
            "chat_rag.js?v=26.0",
            "farming.js?v=27.0",
            "quick_search.js?v=1.0",
            "gacha_sim.js?v=32.0",
            "gacha_tracker.js?v=26.0",
        ]:
            self.assertIn(mod_ver, app_js)


if __name__ == "__main__":
    unittest.main()
