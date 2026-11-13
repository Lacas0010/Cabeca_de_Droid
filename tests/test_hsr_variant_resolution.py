import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import extractor
from services import roster_service


class TestHSRVariantResolution(unittest.TestCase):
    """Garante que variantes SP/Skins no HSR não colidam com personagens base nem com hashes MD5."""

    def test_resolve_hsr_variant_id_ignores_999_inside_md5_hash(self):
        march_id = extractor.resolve_hsr_variant_id(
            name="7 de Março",
            char_id="1224",
            icon="https://act-webstatic.hoyoverse.com/game_record/hkrpg/custom/f999b9c123456789abcdef.png",
            image="https://act-webstatic.hoyoverse.com/game_record/hkrpg/custom/a1b2c3999d4e5f6.png",
        )
        yukong_id = extractor.resolve_hsr_variant_id(
            name="Yukong",
            char_id="1207",
            icon="https://act-webstatic.hoyoverse.com/game_record/hkrpg/custom/8399906f112233445566.png",
        )
        self.assertEqual(march_id, "1224")
        self.assertEqual(yukong_id, "1207")

    def test_resolve_hsr_variant_id_distinguishes_base_and_variants(self):
        self.assertEqual(
            extractor.resolve_hsr_variant_id(
                name="Robin",
                char_id="1309",
                image="https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/character_portrait/1309.png",
            ),
            "1309",
        )
        self.assertEqual(
            extractor.resolve_hsr_variant_id(
                name="Robin - Summeretto",
                char_id="1512",
                image="https://act-webstatic.hoyoverse.com/game_record/hkrpg/custom/avatar_skin_image/1512@2x.png",
            ),
            "1512",
        )
        self.assertEqual(
            extractor.resolve_hsr_variant_id(
                name="Robin - Summeretto",
                char_id="1309",
            ),
            "1512",
        )
        self.assertEqual(
            extractor.resolve_hsr_variant_id(
                name="Loba Prateada Nv. 999",
                char_id="1506",
            ),
            "1506",
        )
        self.assertEqual(
            extractor.resolve_hsr_variant_id(
                name="Loba Prateada",
                char_id="1006",
            ),
            "1006",
        )

    def test_parse_character_build_data_prefers_exact_name_before_variants(self):
        mock_roster = [
            {
                "id": "1512",
                "name": "Robin - Summeretto",
                "element": "Físico",
                "rank_str": "E0",
                "weapon": {"name": "Arma Summeretto", "level": 80, "rank": 1},
                "gacha_art": "https://act-webstatic.hoyoverse.com/game_record/hkrpg/custom/avatar_skin_image/1512@2x.png",
                "relics": [],
                "stats": {},
            },
            {
                "id": "1309",
                "name": "Robin",
                "element": "Físico",
                "rank_str": "E1",
                "weapon": {"name": "Luzes da Noite", "level": 80, "rank": 1},
                "gacha_art": "https://raw.githubusercontent.com/Mar-7th/StarRailRes/master/image/character_portrait/1309.png",
                "relics": [],
                "stats": {},
            },
            {
                "id": "1510",
                "name": "Himeko - Nova",
                "element": "Fogo",
                "rank_str": "E0",
                "weapon": {"name": "Arma Himeko Nova", "level": 80, "rank": 1},
                "relics": [],
                "stats": {},
            },
            {
                "id": "1003",
                "name": "Himeko",
                "element": "Fogo",
                "rank_str": "E2",
                "weapon": {"name": "Antes do Amanhecer", "level": 80, "rank": 1},
                "relics": [],
                "stats": {},
            },
            {
                "id": "1506",
                "name": "Loba Prateada Nv. 999",
                "element": "Quântico",
                "rank_str": "E0",
                "weapon": {"name": "Arma Loba 999", "level": 80, "rank": 1},
                "relics": [],
                "stats": {},
            },
            {
                "id": "1006",
                "name": "Loba Prateada",
                "element": "Quântico",
                "rank_str": "E0",
                "weapon": {"name": "Chuva Constante", "level": 80, "rank": 1},
                "relics": [],
                "stats": {},
            },
            {
                "id": "1414",
                "name": "Dan Heng - Permansor Terrae",
                "element": "Vento",
                "rank_str": "E0",
                "weapon": {"name": "Arma Permansor", "level": 80, "rank": 1},
                "relics": [],
                "stats": {},
            },
            {
                "id": "1002",
                "name": "Dan Heng",
                "element": "Vento",
                "rank_str": "E6",
                "weapon": {"name": "Apenas o Silêncio", "level": 70, "rank": 5},
                "relics": [],
                "stats": {},
            },
            {
                "id": "1225",
                "name": "Fugue",
                "element": "Fogo",
                "rank_str": "E0",
                "weapon": {"name": "Caminho Longo", "level": 80, "rank": 1},
                "relics": [],
                "stats": {},
            },
            {
                "id": "1202",
                "name": "Tingyun",
                "element": "Raio",
                "rank_str": "E6",
                "weapon": {"name": "Dança! Dança! Dança!", "level": 80, "rank": 5},
                "relics": [],
                "stats": {},
            },
            {
                "id": "1401",
                "name": "A Herta",
                "element": "Gelo",
                "rank_str": "E0",
                "weapon": {"name": "Para o Véu Inalcançável", "level": 80, "rank": 1},
                "relics": [],
                "stats": {},
            },
            {
                "id": "1013",
                "name": "Herta",
                "element": "Gelo",
                "rank_str": "E6",
                "weapon": {"name": "Nascimento do Eu", "level": 70, "rank": 5},
                "relics": [],
                "stats": {},
            },
            {
                "id": "1413",
                "name": "Noite Eterna",
                "element": "Gelo",
                "rank_str": "E0",
                "weapon": {"name": "Arma Noite Eterna", "level": 80, "rank": 1},
                "relics": [],
                "stats": {},
            },
            {
                "id": "1224",
                "name": "7 de Março",
                "element": "Imaginário",
                "rank_str": "E6",
                "weapon": {"name": "Jogo de Espadas", "level": 80, "rank": 5},
                "relics": [],
                "stats": {},
            },
        ]

        expected_pairs = [
            ("Robin", "1309", "Luzes da Noite"),
            ("Robin - Summeretto", "1512", "Arma Summeretto"),
            ("Himeko", "1003", "Antes do Amanhecer"),
            ("Himeko - Nova", "1510", "Arma Himeko Nova"),
            ("Loba Prateada", "1006", "Chuva Constante"),
            ("Loba Prateada Nv. 999", "1506", "Arma Loba 999"),
            ("Dan Heng", "1002", "Apenas o Silêncio"),
            ("Dan Heng - Permansor Terrae", "1414", "Arma Permansor"),
            ("Tingyun", "1202", "Dança! Dança! Dança!"),
            ("Fugue", "1225", "Caminho Longo"),
            ("Herta", "1013", "Nascimento do Eu"),
            ("A Herta", "1401", "Para o Véu Inalcançável"),
            ("7 de Março", "1224", "Jogo de Espadas"),
            ("Noite Eterna", "1413", "Arma Noite Eterna"),
        ]

        with patch("services.roster_service.database.get_roster_data", return_value=mock_roster), patch(
            "services.roster_service.get_character_build_detail", return_value=""
        ), patch("services.roster_service.get_static_ranks_for_character", return_value=[]):
            for name, expected_id, expected_weapon in expected_pairs:
                with self.subTest(name=name):
                    res = roster_service.parse_character_build_data("hsr", name)
                    self.assertEqual(res.get("id"), expected_id)
                    self.assertEqual(res.get("weapon_clean"), expected_weapon)
                    if expected_id == "1309":
                        self.assertIn("1309.png", res.get("portrait", ""))
                        self.assertNotIn("1512", res.get("portrait", ""))

    def test_find_best_substring_rank_entry_picks_closest_length(self):
        fake_db = {
            "robin_summeretto": [{"pos": 1, "name": "Summeretto E1"}],
            "robin_alternate": [{"pos": 1, "name": "Alt E1"}],
            "robin_sp": [{"pos": 1, "name": "SP E1"}],
        }
        entry = roster_service._find_best_substring_rank_entry(fake_db, "robin", "")
        self.assertIsNotNone(entry)
        self.assertEqual(entry[0]["name"], "SP E1")


if __name__ == "__main__":
    unittest.main()
