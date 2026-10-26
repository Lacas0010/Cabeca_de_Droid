import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from scrapers.scraper_prydwen import PrydwenScraper
from services.gacha_service import get_current_banners, get_gacha_simulator_defaults
from build_calculator import extract_weights_from_guide, score_relic


class TestGachaDefaultsAndBannersSuite(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("scrapers.scraper_prydwen.requests.get")
    def test_scraper_get_current_banners(self, mock_get):
        """Valida a extração de banners atuais do HTML do Prydwen com mocks determinísticos."""
        sample_html = """
        <html>
            <body>
                <div class="section-header">
                    <h2>Current Character Banners</h2>
                </div>
                <div class="phase-summary">Patch 7.1 Phase 2</div>
                <div class="banner-grid">
                    <div class="banner-card">
                        <div class="banner-art">
                            <img src="https://cdn.prydwen.gg/images/genshin-impact/banners/hero1.webp" alt="Hero1 Banner Art" />
                        </div>
                        <a href="/characters/hero1">Hero1</a>
                        <div aria-label="Secondary Rate Up">
                            <a href="/characters/subhero1">SubHero1</a>
                            <a href="/characters/subhero2">SubHero2</a>
                        </div>
                    </div>
                    <div class="banner-card">
                        <div class="banner-art">
                            <img src="https://cdn.prydwen.gg/images/genshin-impact/banners/hero2.webp" alt="Hero2 Banner Art" />
                        </div>
                        <a href="/characters/hero2">Hero2</a>
                    </div>
                </div>
            </body>
        </html>
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = sample_html
        mock_get.return_value = mock_resp

        scraper = PrydwenScraper()
        result = scraper.get_current_banners("genshin")

        self.assertIn("banners", result)
        banners = result["banners"]
        self.assertGreaterEqual(len(banners), 2)
        self.assertEqual(banners[0]["character_name"], "Hero1")
        self.assertTrue(banners[0]["is_primary"])
        self.assertEqual(banners[0]["banner_image"], "https://cdn.prydwen.gg/images/genshin-impact/banners/hero1.webp")
        self.assertEqual(banners[0]["featured_4stars"], ["SubHero1", "SubHero2"])
        self.assertEqual(banners[1]["character_name"], "Hero2")
        self.assertFalse(banners[1]["is_primary"])

    @patch("services.gacha_tracker_service.calculate_gacha_tracker_stats")
    @patch("services.gacha_service.get_current_banners")
    def test_get_gacha_simulator_defaults(self, mock_banners, mock_tracker):
        """Valida a resolução de pity atual do jogador e banner ativo padrão."""
        mock_cb = MagicMock()
        mock_cb.current_pity = 60
        mock_cb.is_guaranteed = True

        mock_tracker_obj = MagicMock()
        mock_tracker_obj.character_banner = mock_cb
        mock_tracker.return_value = mock_tracker_obj

        mock_banners.return_value = {
            "game_id": "genshin",
            "patch_info": "Patch 7.1 Phase 2",
            "banners": [
                {
                    "character_name": "Escoffier",
                    "banner_image": "https://cdn.prydwen.gg/images/banner1.webp",
                    "featured_4stars": ["Bennett"],
                    "is_primary": True,
                }
            ],
        }

        defaults = get_gacha_simulator_defaults("genshin")
        self.assertEqual(defaults["current_pity"], 60)
        self.assertTrue(defaults["is_guaranteed"])
        self.assertEqual(defaults["active_banner_character"], "Escoffier")
        self.assertIn("/api/proxy_image?url=", defaults["active_banner_image"])
        self.assertEqual(len(defaults["available_banners"]), 1)

    def test_gacha_defaults_endpoint_api(self):
        """Valida o endpoint HTTP /api/gacha/defaults/{game_id} via TestClient."""
        response = self.client.get("/api/gacha/defaults/genshin")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["game_id"], "genshin")
        self.assertIn("current_pity", data)
        self.assertIn("is_guaranteed", data)
        self.assertIn("available_banners", data)
        self.assertIn("available_weapon_banners", data)
        self.assertIsInstance(data["available_banners"], list)
        self.assertIsInstance(data["available_weapon_banners"], list)

    @patch("services.gacha_tracker_service.calculate_gacha_tracker_stats")
    def test_get_gacha_simulator_defaults_weapon(self, mock_tracker):
        """Valida que banner_type='weapon' puxa corretamente o pity e garantido do banner de armas."""
        mock_wb = MagicMock()
        mock_wb.current_pity = 45
        mock_wb.is_guaranteed = True

        mock_cb = MagicMock()
        mock_cb.current_pity = 20
        mock_cb.is_guaranteed = False

        mock_tracker_obj = MagicMock()
        mock_tracker_obj.character_banner = mock_cb
        mock_tracker_obj.weapon_banner = mock_wb
        mock_tracker.return_value = mock_tracker_obj

        defaults = get_gacha_simulator_defaults("hsr", banner_type="weapon")
        self.assertEqual(defaults["game_id"], "hsr")
        self.assertEqual(defaults["banner_type"], "weapon")
        self.assertEqual(defaults["current_pity"], 45)
        self.assertTrue(defaults["is_guaranteed"])
        self.assertGreaterEqual(len(defaults["available_weapon_banners"]), 1)
        self.assertIn("Colors for Tomorrow", [b["character_name"] for b in defaults["available_weapon_banners"]])

    def test_gacha_simulation_weapon_monte_carlo(self):
        """Valida a simulação Monte Carlo para armas/cones com hard pity de 80 e ranks R1-R5."""
        from build_calculator import simulate_gacha_probabilities

        # Simula 1 cópia de arma no Genshin (80 tiros com pity inicial 40 garante até 120 pulls, cobrindo o Caminho Divino)
        res_genshin = simulate_gacha_probabilities(
            game_id="genshin",
            banner_type="weapon",
            current_pity=40,
            is_guaranteed=True,
            pulls_available=80,
            target_copies=1,
            current_rank=-1,
            target_rank=0,
        )
        self.assertEqual(res_genshin["game_id"], "genshin")
        self.assertEqual(res_genshin["banner_type"], "weapon")
        self.assertEqual(res_genshin["target_rank_str"], "R1")
        self.assertGreaterEqual(res_genshin["success_rate"], 65.0)

        # Simula Cone de Luz no HSR com rank S1 a S2
        res_hsr = simulate_gacha_probabilities(
            game_id="hsr",
            banner_type="weapon",
            current_pity=10,
            is_guaranteed=False,
            pulls_available=80,
            target_copies=1,
            current_rank=0,
            target_rank=1,
        )
        self.assertEqual(res_hsr["game_id"], "hsr")
        self.assertEqual(res_hsr["banner_type"], "weapon")
        self.assertEqual(res_hsr["target_rank_str"], "S2")

    def test_gacha_forecast_weapon(self):
        """Valida a projeção futura e Monte Carlo para banner de armas."""
        from build_calculator import calculate_gacha_forecast

        res_fc = calculate_gacha_forecast(
            game_id="genshin",
            banner_type="weapon",
            character_name="Epitome Invocation",
            current_pulls=50,
            current_pity=30,
            is_guaranteed=True,
            target_rank=0,
            current_rank=-1,
            target_days=21,
            has_daily_pass=True,
        )
        self.assertEqual(res_fc["banner_type"], "weapon")
        self.assertEqual(res_fc["target_rank_str"], "R1")
        self.assertIn("income_breakdown", res_fc)
        self.assertGreaterEqual(res_fc["success_rate"], 65.0)

    def test_character_score_calculation_reverted_to_21_oct(self):
        """Valida que o cálculo de notas retornou ao formato de 21/10/2026."""
        # Personagem inexistente ou sem guia deve retornar pesos do fallback original de 21/10
        fallback_weights = extract_weights_from_guide("genshin", "non_existent_hero_xyz")
        # O fallback original de 21/10 tem break_effect=0.5, def_flat=0.2 (sem anomaly_prof, impact, etc)
        self.assertEqual(fallback_weights.get("break_effect"), 0.5)
        self.assertEqual(fallback_weights.get("def_flat"), 0.2)
        self.assertNotIn("anomaly_prof", fallback_weights)
        self.assertNotIn("impact", fallback_weights)

        # score_relic determinístico
        grade, score = score_relic(
            "genshin",
            "generic_char",
            "flower",
            "HP",
            "Taxa Crítica: 3.9%, Dano Crítico: 7.8%, ATK%: 5.8%, Recarga de Energia: 6.5%",
        )
        self.assertIn(grade, ["SSS", "SS", "S", "A", "B", "C", "D"])
        self.assertGreater(score, 0.0)


if __name__ == "__main__":
    unittest.main()
