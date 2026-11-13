import asyncio
import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
import extractor
from services import roster_service


SAMPLE_ACHERON_RAW = {
    "avatar_list": [
        {
            "id": 1308,
            "level": 80,
            "name": "Acheron",
            "element": "lightning",
            "icon": "https://act-webstatic.hoyoverse.com/darkmatter/hkrpg/prod_gf_cn/item_icon_ubd4re/c071bbe4c455985e206fa702b6a56723.png",
            "rarity": 5,
            "rank": 1,
            "image": "https://act-webstatic.hoyoverse.com/game_record/hkrpg/custom/avatar_image/1308@2x.png",
            "equip": {
                "id": 23024,
                "level": 80,
                "rank": 1,
                "name": "Ao Longo da Margem Transitória",
                "desc": "Cone assinatura.",
                "icon": "https://act-webstatic.hoyoverse.com/cone.png",
                "rarity": 5,
            },
            "relics": [],
            "ornaments": [],
            "ranks": [
                {
                    "id": 130801,
                    "pos": 1,
                    "name": "Céus Silenciosos",
                    "desc": "Aumenta Chance CRIT.",
                    "icon": "https://act-webstatic.hoyoverse.com/e1.png",
                    "is_unlocked": True,
                }
            ],
            "properties": [
                {
                    "property_type": 27,
                    "base": "1125",
                    "add": "2000",
                    "final": "3125",
                    "info": {"property_type": 27, "name": "PV", "icon": "", "property_name_filter": "hp"},
                }
            ],
            "skills": [],
            "base_type": 5,
            "figure_path": "",
            "element_id": 8,
            "ex_ranks": [
                {
                    "id": 130801,
                    "pos": 0,
                    "name": "Um Olhar Através da Geada até os Ossos",
                    "icon": "https://act-webstatic.hoyoverse.com/darkmatter/hkrpg/prod_gf_cn/item_icon_ubd4re/1dc01d9d7d1c7bcba3bd8e80a7a69b66.png",
                    "desc": "<color=#FFFFFF>Quando um aliado ataca</color> um inimigo-alvo com \"Nó Rubro\", desfere Ataque Extra.",
                    "is_unlocked": True,
                }
            ],
        }
    ]
}


class TestHSRAffinitiveEidolons(unittest.TestCase):
    def setUp(self):
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_path = self.temp_db_file.name
        self.temp_db_file.close()

        self.orig_db_file = database.DATABASE_NAME
        database.DATABASE_NAME = self.temp_db_path
        database.init_db()
        roster_service.invalidate_roster_cache("hsr")

    def tearDown(self):
        roster_service.invalidate_roster_cache("hsr")
        database.DATABASE_NAME = self.orig_db_file
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_extract_hsr_character_ex_ranks(self):
        """Valida a normalização de ex_ranks vindos do payload bruto da API HoYoLAB."""
        dummy_char = SimpleNamespace(name="Acheron", id=1308)
        ex_ranks = extractor.extract_hsr_character_ex_ranks(
            dummy_char,
            raw_ex_ranks=SAMPLE_ACHERON_RAW["avatar_list"][0]["ex_ranks"],
        )
        self.assertEqual(len(ex_ranks), 1)
        item = ex_ranks[0]
        self.assertEqual(item["name"], "Um Olhar Através da Geada até os Ossos")
        self.assertEqual(item["pos"], 0)
        self.assertTrue(item["is_unlocked"])
        self.assertEqual(item["type"], "affinitive")
        self.assertNotIn("<color", item["desc"])
        self.assertIn("Quando um aliado ataca", item["desc"])

        self.assertEqual(extractor.extract_hsr_character_ex_ranks(dummy_char, raw_ex_ranks=[]), [])

    def test_database_roundtrip_ex_ranks(self):
        """Valida persistência e leitura de ex_ranks_json no SQLite."""
        ex_payload = [
            {
                "id": 130801,
                "pos": 0,
                "name": "Um Olhar Através da Geada até os Ossos",
                "icon": "https://act-webstatic.hoyoverse.com/ex.png",
                "desc": "Ataque Extra quando aliado ataca.",
                "is_unlocked": True,
                "type": "affinitive",
            }
        ]
        database.save_game_account("600000001", "hsr", "Tester", 70, 100)
        database.set_active_account("hsr", "600000001")
        database.save_character(
            uid="600000001",
            game_id="hsr",
            char_id="1308",
            name="Acheron",
            level=80,
            rarity=5,
            rank_str="E1",
            element="lightning",
            icon="https://act-webstatic.hoyoverse.com/acheron.png",
            weapon_name="Ao Longo da Margem Transitória",
            weapon_level=80,
            weapon_rank=1,
            weapon_icon="https://act-webstatic.hoyoverse.com/cone.png",
            raw_md="**Personagem:** Acheron",
            ranks_json=json.dumps([]),
            ex_ranks_json=json.dumps(ex_payload, ensure_ascii=False),
        )

        roster = database.get_roster_data("hsr")
        self.assertEqual(len(roster), 1)
        self.assertEqual(len(roster[0]["ex_ranks"]), 1)
        self.assertEqual(roster[0]["ex_ranks"][0]["name"], "Um Olhar Através da Geada até os Ossos")
        self.assertTrue(roster[0]["ex_ranks"][0]["is_unlocked"])

    def test_roster_service_returns_enriched_ex_ranks(self):
        """Valida que get_roster e parse_character_build_data expõem e fazem proxy de ex_ranks."""
        ex_payload = [
            {
                "id": 130801,
                "pos": 0,
                "name": "Um Olhar Através da Geada até os Ossos",
                "icon": "https://act-webstatic.hoyoverse.com/ex.png",
                "desc": "<color=#fff>Ataque Extra</color>",
                "is_unlocked": True,
                "type": "affinitive",
            }
        ]
        database.save_game_account("600000001", "hsr", "Tester", 70, 100)
        database.set_active_account("hsr", "600000001")
        database.save_character(
            uid="600000001",
            game_id="hsr",
            char_id="1308",
            name="Acheron",
            level=80,
            rarity=5,
            rank_str="E1",
            element="lightning",
            icon="https://act-webstatic.hoyoverse.com/acheron.png",
            weapon_name="Ao Longo da Margem Transitória",
            weapon_level=80,
            weapon_rank=1,
            weapon_icon="https://act-webstatic.hoyoverse.com/cone.png",
            raw_md="**Personagem:** Acheron | **Nível:** 80 | **Eidolon:** E1",
            ranks_json=json.dumps([]),
            ex_ranks_json=json.dumps(ex_payload, ensure_ascii=False),
        )

        roster = asyncio.run(roster_service.get_roster("hsr"))
        self.assertEqual(len(roster), 1)
        acheron = roster[0]
        self.assertIn("ex_ranks", acheron)
        self.assertEqual(len(acheron["ex_ranks"]), 1)
        self.assertTrue(acheron["ex_ranks"][0]["icon"].startswith("/api/proxy_image?url="))
        self.assertEqual(acheron["ex_ranks"][0]["desc"], "Ataque Extra")

        build = roster_service.parse_character_build_data("hsr", "Acheron")
        self.assertEqual(len(build.get("ex_ranks", [])), 1)
        self.assertTrue(build["ex_ranks"][0]["icon"].startswith("/api/proxy_image?url="))
        self.assertTrue(build["ex_ranks"][0]["is_unlocked"])

    def test_hsr_extractor_writes_affinitive_eidolon_to_markdown_and_db(self):
        """Valida extração mockada do HSRExtractor gravando ex_ranks no roster_hsr.md, JSON e SQLite."""
        mock_user = SimpleNamespace(
            info=SimpleNamespace(nickname="Lacas", level=70),
            stats=SimpleNamespace(
                active_days=100,
                avatar_num=1,
                achievement_num=50,
                chest_num=200,
                abyss_process="XII",
            ),
        )
        mock_char = SimpleNamespace(
            id=1308,
            name="Acheron",
            level=80,
            rarity=5,
            rank=1,
            path=SimpleNamespace(name="Nihility"),
            element="lightning",
            icon="https://act-webstatic.hoyoverse.com/acheron.png",
            image="https://act-webstatic.hoyoverse.com/acheron_full.png",
            figure_path="",
            equip=SimpleNamespace(
                name="Ao Longo da Margem Transitória",
                level=80,
                rank=1,
                rarity=5,
                icon="https://act-webstatic.hoyoverse.com/cone.png",
            ),
            relics=[],
            ornaments=[],
            ranks=[],
            skills=[],
            properties=[],
        )
        mock_parsed = SimpleNamespace(avatar_list=[mock_char])

        orig_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            try:
                ext = extractor.HSRExtractor({"ltuid_v2": "1", "ltoken_v2": "x"})
                ext.get_account = AsyncMock(return_value=SimpleNamespace(uid=600000001))
                ext.client.get_starrail_user = AsyncMock(return_value=mock_user)
                ext.client._request_starrail_record = AsyncMock(return_value=SAMPLE_ACHERON_RAW)
                ext.client.get_starrail_character_details = AsyncMock(side_effect=Exception("skip"))

                with patch("extractor.genshin.models.StarRailDetailCharacterResponse", return_value=mock_parsed), \
                     patch("extractor.endgame_extractor.extrair_endgame_hsr_data", AsyncMock(return_value=("", []))), \
                     patch("extractor.requests.get", return_value=MagicMock(status_code=404)):
                    asyncio.run(ext.extrair_e_salvar("hsr/roster_hsr.md"))

                with open("hsr/roster_hsr.md", "r", encoding="utf-8") as mf:
                    md_text = mf.read()
                self.assertIn("| Acheron | 80 | ⭐⭐⭐⭐⭐ | E1 + Affinitive | Inexistência | lightning |", md_text)
                self.assertIn("- **Affinitive Eidolon:** Um Olhar Através da Geada até os Ossos (Ativo)", md_text)

                with open("hsr/roster_data_hsr.json", "r", encoding="utf-8") as jf:
                    jdata = json.load(jf)
                self.assertEqual(len(jdata), 1)
                self.assertEqual(len(jdata[0]["ex_ranks"]), 1)
                self.assertTrue(jdata[0]["ex_ranks"][0]["is_unlocked"])

                roster_db = database.get_roster_data("hsr", uid="600000001")
                self.assertEqual(len(roster_db), 1)
                self.assertEqual(len(roster_db[0]["ex_ranks"]), 1)
            finally:
                os.chdir(orig_cwd)


if __name__ == "__main__":
    unittest.main()
