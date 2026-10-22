import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from server import app
from build_calculator import find_trash_relics, extract_relic_substats_data, get_meta_data
import database


class TestTrashCoringaSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_extract_relic_substats_data(self):
        """Valida a extração de Crit Value (CV), detecção de duplo crítico e velocidade."""
        substats = [{"name": "Taxa CRIT: 8.4%"}, {"name": "Dano CRIT: 14.2%"}, {"name": "VEL: 5"}, {"name": "DEF: 16"}]
        info = extract_relic_substats_data(substats)
        self.assertTrue(info["has_double_crit"])
        self.assertEqual(info["crit_rate_val"], 8.4)
        self.assertEqual(info["crit_dmg_val"], 14.2)
        self.assertEqual(info["speed_val"], 5.0)
        # CV = (8.4 * 2) + 14.2 = 16.8 + 14.2 = 31.0
        self.assertAlmostEqual(info["cv"], 31.0, places=1)

    def test_coringa_double_crit_protection(self):
        """Garante que qualquer peça com Duplo Crítico NUNCA seja descartada como lixo."""
        meta_data = {
            "dan_heng": {
                "main_stats": {"Cabeça": ["hp_flat"], "Corpo": ["crit_rate"]},
                "substats": ["crit_rate", "crit_dmg", "spd", "atk_pct"],
            }
        }
        # Peça com Main Stat de DEF% (teoricamente ruim), mas com Duplo Crítico de 31.0 CV
        relics = [
            {
                "name": "Peitoral do Andarilho",
                "slot": "Corpo",
                "main_stat": "DEF (54.0%)",
                "substats": [
                    {"name": "Taxa CRIT: 9.2%"},
                    {"name": "Dano CRIT: 18.0%"},
                    {"name": "VEL: 3"},
                    {"name": "DEF: 21"},
                ],
                "character_name": "Gepard",
            }
        ]

        result = find_trash_relics("hsr", relics, meta_data)
        self.assertEqual(result["trash_count"], 0)
        self.assertEqual(result["coringa_count"], 1)
        self.assertEqual(len(result["coringa_relics"]), 1)

        coringa = result["coringa_relics"][0]
        self.assertIn("God-Tier Coringa", coringa["coringa_tier"])
        self.assertGreaterEqual(coringa["crit_value"], 30.0)
        self.assertIn("Duplo Crítico", coringa["reason"])
        self.assertEqual(coringa["character_name"], "Gepard")

    def test_coringa_noble_main_stat_protection(self):
        """Valida proteção para Cálice de Dano Elemental com crítico único em Genshin."""
        meta_data = {}
        relics = [
            {
                "name": "Cálice de Sangue Antigo",
                "slot": "Cálice",
                "main_stat": "Bônus de Dano Pyro (46.6%)",
                "substats": [{"name": "Taxa CRIT: 3.9%"}, {"name": "DEF: 19"}, {"name": "PV: 299"}],
                "character_name": "Hu Tao",
            }
        ]
        result = find_trash_relics("genshin", relics, meta_data)
        self.assertEqual(result["trash_count"], 0)
        self.assertEqual(result["coringa_count"], 1)
        self.assertIn("Off-Piece", result["coringa_relics"][0]["reason"])

    def test_actual_trash_relic_identified(self):
        """Garante que peças verdadeiramente lixo (sem crítico, flat pesadas) sejam marcadas para reciclagem."""
        meta_data = {
            "seele": {
                "main_stats": {"Corpo": ["crit_rate", "crit_dmg"]},
                "substats": ["crit_rate", "crit_dmg", "atk_pct", "spd"],
            }
        }
        relics = [
            {
                "name": "Armadura Obsoleta",
                "slot": "Corpo",
                "main_stat": "DEF (54%)",
                "substats": [{"name": "DEF: 42"}, {"name": "PV: 120"}],
            }
        ]
        result = find_trash_relics("hsr", relics, meta_data)
        self.assertEqual(result["trash_count"], 1)
        self.assertEqual(result["coringa_count"], 0)
        trash = result["trash_relics"][0]
        self.assertIn("DEF (54%)", trash["main_stat"])
        self.assertIn("EXP ou Reciclar", trash["recommendation"])

    @patch("routers.relics.database.get_roster_data")
    @patch("routers.relics.get_meta_data")
    def test_api_trash_relics_endpoint(self, mock_get_meta, mock_get_roster):
        """Valida que o endpoint GET /api/relics/trash/{game_id} retorna o contrato correto."""
        mock_get_roster.return_value = [
            {
                "name": "Acheron",
                "relics": [
                    {
                        "name": "Grinalda do Campeonato",
                        "slot": "Cabeça",
                        "main": "PV (705)",
                        "sub": "Taxa CRIT: 7.2%, Dano CRIT: 14.8%, VEL: 4",
                        "icon": "https://example.com/icon.png",
                    },
                    {
                        "name": "Peitoral Descartável",
                        "slot": "Corpo",
                        "main": "DEF (54%)",
                        "sub": "DEF: 38, PV: 110",
                        "icon": "https://example.com/icon2.png",
                    },
                ],
            }
        ]
        mock_get_meta.return_value = {}

        response = self.client.get("/api/relics/trash/hsr")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["game_id"], "hsr")
        self.assertEqual(data["total_analyzed"], 2)
        self.assertEqual(data["coringa_count"], 1)
        self.assertEqual(data["trash_count"], 1)

        coringa = data["coringa_relics"][0]
        self.assertEqual(coringa["name"], "Grinalda do Campeonato")
        self.assertEqual(coringa["character_name"], "Acheron")
        self.assertGreater(coringa["crit_value"], 25.0)

        trash = data["trash_relics"][0]
        self.assertEqual(trash["name"], "Peitoral Descartável")
        self.assertEqual(trash["character_name"], "Acheron")


if __name__ == "__main__":
    unittest.main()
