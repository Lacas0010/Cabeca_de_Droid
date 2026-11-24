import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from main import app
from scrapers import role_icons_scraper as scraper
from services import media_service


class TestRoleIconsSuite(unittest.TestCase):
    """Testes offline da Etapa 1 (v1.4.0): ícones oficiais de Caminhos (HSR), Armas (Genshin) e Especialidades (ZZZ)."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_role_icons_scraper_discovers_all_games_from_apis(self):
        class _FakeResp:
            def __init__(self, status_code=200, payload=None, text=""):
                self.status_code = status_code
                self._payload = payload
                self.text = text

            def json(self):
                return self._payload

        class _FakeSession:
            def get(self, url, headers=None, timeout=12):
                if "StarRailRes" in url:
                    return _FakeResp(
                        200,
                        payload=[
                            {"name": f"{name}.png", "download_url": f"https://cdn.example/hsr/{name}.png"}
                            for name in (
                                "Destruction",
                                "Hunt",
                                "Erudition",
                                "Harmony",
                                "Nihility",
                                "Preservation",
                                "Abundance",
                                "Remembrance",
                                "Elation",
                            )
                        ],
                    )
                if "genshin-impact/characters" in url:
                    html = " ".join(
                        f"https://cdn.prydwen.gg/images/genshin-impact/icons/weapon_{w}.webp"
                        for w in ("sword", "claymore", "polearm", "bow", "catalyst")
                    )
                    return _FakeResp(200, text=html)
                if "zenless/characters" in url:
                    html = " ".join(
                        f"https://cdn.prydwen.gg/images/zenless-zone-zero/icons/style_{s}.webp"
                        for s in ("attack", "stun", "anomaly", "support", "defence", "rupture", "armorer")
                    )
                    return _FakeResp(200, text=html)
                return _FakeResp(404)

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch.object(scraper, "_role_icons_json_path", return_value=os.path.join(tmpdir, "role_icons.json")),
            patch.object(scraper, "load_saved_role_icons", return_value={}),
        ):
            merged = scraper.sync_role_icons(session=_FakeSession())
            self.assertEqual(len(merged["hsr"]), 9)
            self.assertEqual(merged["hsr"]["remembrance"], "https://cdn.example/hsr/Remembrance.png")
            self.assertEqual(merged["hsr"]["elation"], "https://cdn.example/hsr/Elation.png")
            self.assertEqual(
                set(merged["genshin"].keys()),
                {"sword", "claymore", "polearm", "bow", "catalyst"},
            )
            self.assertEqual(
                set(merged["zzz"].keys()),
                {"attack", "stun", "anomaly", "support", "defense", "rupture", "armorer"},
            )
            self.assertTrue(os.path.isfile(os.path.join(tmpdir, "role_icons.json")))

    def test_role_filename_normalization_handles_pt_and_en_aliases(self):
        self.assertEqual(media_service._normalize_role_filename("hsr_recordação.png"), "hsr_remembrance.png")
        self.assertEqual(media_service._normalize_role_filename("hsr_a caça.png"), "hsr_hunt.png")
        self.assertEqual(media_service._normalize_role_filename("hsr_júbilo.png"), "hsr_elation.png")
        self.assertEqual(media_service._normalize_role_filename("genshin_espadão.png"), "genshin_claymore.png")
        self.assertEqual(media_service._normalize_role_filename("zzz_defence.png"), "zzz_defense.png")
        self.assertEqual(media_service._normalize_role_filename("zzz_atordoamento.png"), "zzz_stun.png")

    def test_assets_icons_route_serves_cached_png_and_offline_svg_fallback(self):
        png_bytes = b"\x89PNG\r\n\x1a\n" + (b"\x00" * 32)
        fake_resp = MagicMock(status_code=200, content=png_bytes)

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("services.media_service.get_data_path", side_effect=lambda rel: os.path.join(tmpdir, rel)),
            patch("services.media_service.get_resource_path", side_effect=lambda rel: os.path.join(tmpdir, "res", rel)),
            patch(
                "services.media_service.load_role_icons_map",
                return_value={"hsr": {"remembrance": "https://cdn.example/Remembrance.png"}},
            ),
            patch("curl_cffi.requests.get", return_value=fake_resp) as mock_get,
        ):
            r1 = self.client.get("/assets/icons/hsr_remembrance.png")
            self.assertEqual(r1.status_code, 200)
            self.assertEqual(r1.headers.get("content-type"), "image/png")
            self.assertEqual(r1.content, png_bytes)
            self.assertEqual(mock_get.call_count, 1)

            # Segunda requisição deve vir direto do cache local sem HTTP
            r2 = self.client.get("/assets/icons/hsr_recordacao.png")
            self.assertEqual(r2.status_code, 200)
            self.assertEqual(mock_get.call_count, 1)

            # Sem URL nem cache local -> fallback SVG limpo sem 404
            r_svg = self.client.get("/assets/icons/zzz_desconhecido.png")
            self.assertEqual(r_svg.status_code, 200)
            self.assertEqual(r_svg.headers.get("content-type"), "image/svg+xml")
            self.assertIn(b"<svg", r_svg.content)

            # Nome inválido -> 400
            r_bad = self.client.get("/assets/icons/invalid.txt")
            self.assertEqual(r_bad.status_code, 400)

    def test_frontend_role_icons_wiring_in_filters_cards_and_inspector(self):
        root = Path(__file__).resolve().parent.parent
        api_client_js = (root / "static" / "js" / "modules" / "api_client.js").read_text(encoding="utf-8")
        roster_js = (root / "static" / "js" / "modules" / "roster.js").read_text(encoding="utf-8")
        index_html = (root / "static" / "index.html").read_text(encoding="utf-8")
        style_css = (root / "static" / "style.css").read_text(encoding="utf-8")

        self.assertIn("function renderRoleIconBadge", api_client_js)
        self.assertIn("/assets/icons/${g}_${canon}.png?v=2", api_client_js)

        for token in ("char-meta-row", "char-role-chip", "char-role-pill", "ins-meta-chips", "ins-chip-role"):
            self.assertIn(token, roster_js)
            self.assertIn(f".{token}", style_css)

        for role_asset in (
            "/assets/icons/hsr_remembrance.png?v=2",
            "/assets/icons/genshin_claymore.png?v=2",
            "/assets/icons/zzz_rupture.png?v=2",
        ):
            self.assertIn(role_asset, index_html)


if __name__ == "__main__":
    unittest.main()
