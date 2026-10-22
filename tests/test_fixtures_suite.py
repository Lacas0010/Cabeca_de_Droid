import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from tests.fixtures import load_fixture


class TestFixturesSuite(unittest.TestCase):
    def test_load_hoyolab_hsr_roster(self):
        """Valida que a fixture de roster do HSR possui a estrutura esperada pelo extrator."""
        data = load_fixture("hoyolab_hsr_roster.json")
        self.assertEqual(data["retcode"], 0)
        self.assertIn("data", data)
        self.assertIn("avatar_list", data["data"])
        self.assertGreater(len(data["data"]["avatar_list"]), 0)

        acheron = data["data"]["avatar_list"][0]
        self.assertEqual(acheron["name"], "Acheron")
        self.assertEqual(acheron["element"], "lightning")
        self.assertIn("equip", acheron)
        self.assertIn("relics", acheron)
        self.assertIn("ornaments", acheron)
        self.assertIn("skills", acheron)

    def test_load_hoyolab_zzz_notes(self):
        """Valida que a fixture de notas do ZZZ possui bateria, energia e status de engajamento."""
        data = load_fixture("hoyolab_zzz_notes.json")
        self.assertEqual(data["retcode"], 0)
        self.assertIn("data", data)
        z_data = data["data"]
        self.assertIn("energy", z_data)
        self.assertIn("battery_charge", z_data)
        self.assertIn("video_store_state", z_data)
        self.assertIn("card_sign", z_data)
        self.assertEqual(z_data["energy"]["progress"]["max"], 240)

    def test_load_prydwen_genshin_builds(self):
        """Valida que a fixture de builds do Genshin do Prydwen contém guias e benchmarks estruturados."""
        data = load_fixture("prydwen_genshin_builds.json")
        self.assertEqual(data["game"], "genshin")
        self.assertIn("characters", data)
        self.assertIn("furina", data["characters"])

        furina = data["characters"]["furina"]
        self.assertEqual(furina["name"], "Furina")
        self.assertIn("weapons", furina)
        self.assertIn("artifacts", furina)
        self.assertIn("stats_main", furina)
        self.assertIn("benchmarks", furina)


if __name__ == "__main__":
    unittest.main()
