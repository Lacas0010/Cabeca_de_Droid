import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app
from scrapers import resource_icons_scraper as scraper


class TestResourceIconsSuite(unittest.TestCase):
    """Testes offline da Etapa 2 (v1.4.0): ícones oficiais de Energia, Moedas e Passes."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_resource_icons_scraper_discovers_all_games_from_hoyowiki(self):
        class _FakeResp:
            def __init__(self, payload, status_code=200):
                self._payload = payload
                self.status_code = status_code

            def json(self):
                return self._payload

        class _FakeSession:
            def get(self, url, params=None, headers=None, timeout=10):
                if "hoyowiki" in url:
                    kw = (params or {}).get("keyword", "")
                    slug = kw.lower().replace(" ", "_")
                    app_name = (headers or {}).get("x-rpc-wiki_app", "game")
                    return _FakeResp(
                        {
                            "data": {
                                "list": [
                                    {"name": "Other Item", "icon_url": "https://cdn.example/wrong.png"},
                                    {"name": kw, "icon_url": f"https://cdn.example/{app_name}_{slug}.png"},
                                ]
                            }
                        }
                    )
                return _FakeResp({}, status_code=404)

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch.object(scraper, "_resource_icons_json_path", return_value=os.path.join(tmpdir, "resource_icons.json")),
            patch.object(scraper, "load_saved_resource_icons", return_value={}),
        ):
            merged = scraper.sync_resource_icons(session=_FakeSession())
            self.assertEqual(set(merged["genshin"].keys()), {"energy", "currency", "ticket"})
            self.assertEqual(set(merged["hsr"].keys()), {"energy", "reserve", "currency", "ticket"})
            self.assertEqual(set(merged["zzz"].keys()), {"energy", "currency", "ticket"})
            self.assertEqual(merged["genshin"]["energy"], "https://cdn.example/genshin_original_resin.png")
            self.assertEqual(merged["hsr"]["currency"], "https://cdn.example/hsr_stellar_jade.png")
            self.assertEqual(merged["zzz"]["ticket"], "https://cdn.example/zzz_encrypted_master_tape.png")
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, "resource_icons.json")))

    def test_assets_resources_route_caches_png_and_falls_back_to_svg(self):
        png_bytes = b"\x89PNG\r\n\x1a\n" + (b"\x00" * 32)
        fake_resp = MagicMock(status_code=200, content=png_bytes)

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("services.media_service.get_data_path", side_effect=lambda rel: os.path.join(tmpdir, rel)),
            patch("services.media_service.get_resource_path", side_effect=lambda rel: os.path.join(tmpdir, "res", rel)),
            patch(
                "services.media_service.load_resource_icons_map",
                return_value={"genshin": {"energy": "https://cdn.example/resin.png"}},
            ),
            patch("curl_cffi.requests.get", return_value=fake_resp) as mock_get,
        ):
            r1 = self.client.get("/assets/resources/genshin_energy.png")
            self.assertEqual(r1.status_code, 200)
            self.assertEqual(r1.headers.get("content-type"), "image/png")
            self.assertEqual(r1.content, png_bytes)
            self.assertEqual(mock_get.call_count, 1)

            r2 = self.client.get("/assets/resources/genshin_energy.png")
            self.assertEqual(r2.status_code, 200)
            self.assertEqual(mock_get.call_count, 1)

            r_svg = self.client.get("/assets/resources/zzz_unknown.png")
            self.assertEqual(r_svg.status_code, 200)
            self.assertEqual(r_svg.headers.get("content-type"), "image/svg+xml")
            self.assertIn(b"<svg", r_svg.content)

            r_bad = self.client.get("/assets/resources/bad.txt")
            self.assertEqual(r_bad.status_code, 400)

    def test_frontend_energy_monitor_daily_notes_slots_and_gacha_resource_icons(self):
        root = Path(__file__).resolve().parent.parent
        html = (root / "static" / "index.html").read_text(encoding="utf-8")
        style_css = (root / "static" / "style.css").read_text(encoding="utf-8")
        gacha_css = (root / "static" / "css" / "gacha.css").read_text(encoding="utf-8")
        api_js = (root / "static" / "js" / "modules" / "api_client.js").read_text(encoding="utf-8")
        gacha_sim = (root / "static" / "js" / "modules" / "gacha_sim.js").read_text(encoding="utf-8")
        gacha_tracker = (root / "static" / "js" / "modules" / "gacha_tracker.js").read_text(encoding="utf-8")

        # Energy Monitor + slots preparados para Etapa 5
        for token in (
            "/assets/resources/genshin_energy.png?v=2",
            "/assets/resources/hsr_energy.png?v=1",
            "/assets/resources/zzz_energy.png?v=1",
            'id="daily-notes-slot-genshin"',
            'id="daily-notes-slot-hsr"',
            'id="daily-notes-slot-zzz"',
            "energy-ring-emblem",
            "gacha-pulls-ticket-icon",
            "gacha-form-grid-2",
            "gacha-action-grid-3",
            "gacha-banner-header-row",
            "gacha-banner-countdown-badge",
        ):
            self.assertIn(token, html)

        self.assertIn(".energy-daily-notes-slot", style_css)
        self.assertIn(".energy-resource-icon-wrap", style_css)
        self.assertIn(".gacha-currency-convert-chip", gacha_css)
        self.assertIn(".tracker-kpi-currency-sub", gacha_css)
        self.assertIn(".luck-resource-strip", gacha_css)
        self.assertIn(".gacha-banner-ingame-caption", gacha_css)
        self.assertIn(".gacha-banner-countdown-badge", gacha_css)
        self.assertIn(".gacha-banner-tab-cd", gacha_css)
        self.assertIn(".gacha-form-grid-2", gacha_css)
        self.assertIn(".gacha-action-grid-3", gacha_css)
        self.assertIn("function getResourceIconUrl", api_js)
        self.assertIn("function renderResourceIcon", api_js)
        self.assertIn("window.syncGachaResourceIcons", gacha_sim)
        self.assertIn("function formatBannerScheduleBadge", gacha_sim)
        self.assertIn("function formatBannerCountdown", gacha_sim)
        self.assertIn("function ensureActiveBannerCountdownTicker", gacha_sim)
        self.assertIn("luck-resource-strip", gacha_sim)
        self.assertIn("tracker-kpi-currency-sub", gacha_tracker)

    def test_hoyowiki_skips_tutorial_entry_for_original_resin(self):
        """Garante que o scraper rejeite o verbete de Tutorial e selecione o item Materials de Original Resin."""
        class _FakeResp:
            status_code = 200

            def json(self):
                return {
                    "data": {
                        "list": [
                            {
                                "name": "Original Resin",
                                "icon_url": "https://cdn.example/tutorial_question_mark.png",
                                "menu": {"style": "adventure_guide", "sub_menus": [{"style": "tutorial"}]},
                            },
                            {
                                "name": "Original Resin",
                                "icon_url": "https://cdn.example/original_resin_real.png",
                                "menu": {"style": "wuchanzhi", "sub_menus": [{"style": "object"}]},
                            },
                        ]
                    }
                }

        fake_session = MagicMock()
        fake_session.get.return_value = _FakeResp()
        icon_url = scraper._query_hoyowiki_exact_icon(fake_session, "genshin", "Original Resin")
        self.assertEqual(icon_url, "https://cdn.example/original_resin_real.png")

    def test_prydwen_banner_schedule_distinguishes_phases_full_patch_and_collab(self):
        """Valida extração individual de 1ª Fase, 2ª Fase, Atualização Inteira e Collab por card de banner."""
        from bs4 import BeautifulSoup
        from scrapers.scraper_prydwen import PrydwenScraper

        ps = PrydwenScraper()
        card_full = BeautifulSoup(
            '<div class="banner-card">5-star | Aha | Patch 4.7 | Nov 11, 2026 – Dec 22, 2026 | debuting for the entirety of Patch 4.7</div>',
            "html.parser",
        )
        card_p1 = BeautifulSoup(
            '<div class="banner-card">5-star | Sparxie | Patch 4.7 Phase 1 | Nov 11, 2026 – Dec 2, 2026 | rerunning</div>',
            "html.parser",
        )
        card_p2 = BeautifulSoup(
            '<div class="banner-card">S-Rank | Severian | Patch 3.3 Phase 2 | Nov 11, 2026 – Dec 1, 2026 | debuting in Phase 2 of Patch 3.3</div>',
            "html.parser",
        )
        card_collab = BeautifulSoup(
            '<div class="banner-card">5-star | collab | Gilgamesh | Patch 4.4 | From Jul 24, 2026 | Fate Collaboration</div>',
            "html.parser",
        )

        m_full = ps._extract_banner_schedule_meta(card_full, "Patch 4.7 Nov 11, 2026 – Dec 22, 2026")
        self.assertEqual(m_full["duration_type"], "full_patch")
        self.assertTrue(m_full["is_full_patch"])
        self.assertIsNone(m_full["phase"])
        self.assertEqual(m_full["start_date"], "2026-11-11")
        self.assertEqual(m_full["end_date"], "2026-12-22")

        m_p1 = ps._extract_banner_schedule_meta(card_p1, "Patch 4.7 Nov 11, 2026 – Dec 22, 2026")
        self.assertEqual(m_p1["duration_type"], "phase_1")
        self.assertEqual(m_p1["phase"], 1)
        self.assertEqual(m_p1["end_date"], "2026-12-02")

        m_p2 = ps._extract_banner_schedule_meta(card_p2, "Patch 3.3 Phase 2 Nov 11, 2026 – Dec 1, 2026")
        self.assertEqual(m_p2["duration_type"], "phase_2")
        self.assertEqual(m_p2["phase"], 2)
        self.assertEqual(m_p2["end_date"], "2026-12-01")

        m_collab = ps._extract_banner_schedule_meta(card_collab, "Patch 4.7 Nov 11, 2026 – Dec 22, 2026")
        self.assertEqual(m_collab["duration_type"], "collab")
        self.assertIsNone(m_collab["phase"])
        self.assertIsNone(m_collab["end_date"])

    def test_banner_turnover_times_differ_between_phase1_and_patch_end(self):
        """Valida que 1ª Fase vira no horário da 2ª Fase (20:00 GI / 14:00 HSR-ZZZ) e 2ª Fase/Full Patch vira na att (23:30)."""
        from services import gacha_service

        mock_banners = {
            "hsr": {
                "game_id": "hsr",
                "patch_info": "Patch 4.7 Nov 11, 2026 – Dec 22, 2026",
                "banners": [
                    {
                        "character_name": "Aha",
                        "banner_image": "",
                        "featured_4stars": [],
                        "is_primary": True,
                        "duration_type": "full_patch",
                        "is_full_patch": True,
                        "phase": None,
                        "start_date": "2026-11-11",
                        "end_date": "2026-12-22",
                    },
                    {
                        "character_name": "Sparxie",
                        "banner_image": "",
                        "featured_4stars": [],
                        "is_primary": False,
                        "duration_type": "phase_1",
                        "is_full_patch": False,
                        "phase": 1,
                        "start_date": "2026-11-11",
                        "end_date": "2026-12-02",
                    },
                ],
                "weapon_banners": [],
            },
            "genshin": {
                "game_id": "genshin",
                "patch_info": "Patch 7.2 Phase 1",
                "banners": [
                    {
                        "character_name": "Mitya",
                        "banner_image": "",
                        "featured_4stars": [],
                        "is_primary": True,
                        "duration_type": "phase_1",
                        "phase": 1,
                        "start_date": "2026-11-04",
                        "end_date": "2026-11-24",
                    }
                ],
                "weapon_banners": [],
            },
            "zzz": {
                "game_id": "zzz",
                "patch_info": "Patch 3.3 Phase 2",
                "banners": [
                    {
                        "character_name": "Severian",
                        "banner_image": "",
                        "featured_4stars": [],
                        "is_primary": True,
                        "duration_type": "phase_2",
                        "phase": 2,
                        "start_date": "2026-11-11",
                        "end_date": "2026-12-01",
                    }
                ],
                "weapon_banners": [],
            },
        }

        with (
            patch("services.gacha_service.get_current_banners", side_effect=lambda g: mock_banners[g]),
            patch("services.gacha_service.get_character_mini_info", return_value={"name": "X", "icon": "", "rarity": 5}),
            patch("services.gacha_tracker_service.calculate_gacha_tracker_stats", return_value=None),
        ):
            hsr_d = gacha_service.get_gacha_simulator_defaults("hsr")
            by_hsr = {b["character_name"]: b for b in hsr_d["available_banners"]}
            self.assertEqual(by_hsr["Aha"]["banner_time"], "23:30")
            self.assertEqual(by_hsr["Aha"]["end_at"], "2026-12-23T02:30:00Z")
            self.assertEqual(by_hsr["Sparxie"]["banner_time"], "14:00")
            self.assertEqual(by_hsr["Sparxie"]["end_at"], "2026-12-02T17:00:00Z")

            gi_d = gacha_service.get_gacha_simulator_defaults("genshin")
            self.assertEqual(gi_d["available_banners"][0]["banner_time"], "20:00")
            self.assertEqual(gi_d["available_banners"][0]["end_at"], "2026-11-24T23:00:00Z")

            zzz_d = gacha_service.get_gacha_simulator_defaults("zzz")
            self.assertEqual(zzz_d["available_banners"][0]["banner_time"], "23:30")
            self.assertEqual(zzz_d["available_banners"][0]["end_at"], "2026-12-02T02:30:00Z")


if __name__ == "__main__":
    unittest.main()
