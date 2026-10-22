import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from server import app
from schemas.simulation import RelicPieceModel, SimulateSwapRequest
from services.simulation_service import (
    simulate_relic_swap,
    extract_stats_from_relic,
    parse_stat_line,
    map_score_to_grade,
)


class TestRelicSimulationSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_parse_stat_line(self):
        """Valida a extração de chaves e valores numéricos a partir de linhas de atributos."""
        k1, v1 = parse_stat_line("Taxa CRIT: 8.4%")
        self.assertEqual(k1, "crit_rate")
        self.assertEqual(v1, 8.4)

        k2, v2 = parse_stat_line("Dano CRIT: 16.2%")
        self.assertEqual(k2, "crit_dmg")
        self.assertEqual(v2, 16.2)

        k3, v3 = parse_stat_line("VEL: 25")
        self.assertEqual(k3, "speed")
        self.assertEqual(v3, 25.0)

        k4, v4 = parse_stat_line("Proficiência Anômala (AP): 30")
        self.assertEqual(k4, "ap")
        self.assertEqual(v4, 30.0)

    def test_extract_stats_from_relic(self):
        """Valida o mapeamento agregado de atributos numéricos de uma relíquia."""
        main_stat = "Taxa CRIT (32.4%)"
        sub_stats = "Dano CRIT: 12.0%, VEL: 4, ATK: 35, HP: 120"

        extracted = extract_stats_from_relic(main_stat, sub_stats)
        self.assertEqual(extracted.get("crit_rate"), 32.4)
        self.assertEqual(extracted.get("crit_dmg"), 12.0)
        self.assertEqual(extracted.get("speed"), 4.0)
        self.assertEqual(extracted.get("atk_flat"), 35.0)
        self.assertEqual(extracted.get("hp_flat"), 120.0)

    @patch("services.simulation_service.score_relic")
    def test_simulate_relic_swap_upgrade(self, mock_score_relic):
        """Valida simulação onde a troca eleva a nota e pontuação da build."""

        # mock score_relic: (grade, score)
        def mock_scoring(game, char, slot, main, subs):
            if "taxa crit" in main.lower() or "dano crit" in subs.lower():
                return "SS", 92.0
            return "C", 45.0

        mock_score_relic.side_effect = mock_scoring

        old_piece = RelicPieceModel(
            slot="Corpo", name="Peitoral Comum", main_stat="DEF (54.0%)", sub_stats="DEF: 15, HP: 120"
        )
        new_piece = RelicPieceModel(
            slot="Corpo", name="Peitoral Gracioso", main_stat="Taxa CRIT (32.4%)", sub_stats="Dano CRIT: 18.0%, VEL: 4"
        )

        req = SimulateSwapRequest(
            game_id="hsr",
            char_name="Seele",
            target_slot="Corpo",
            replacement_relic=new_piece,
            current_relics=[old_piece],
        )

        res = simulate_relic_swap(req)
        self.assertTrue(res.is_upgrade)
        self.assertGreater(res.score_diff, 0)
        self.assertEqual(res.new_piece_grade, "SS")
        self.assertEqual(res.old_piece_grade, "C")
        self.assertIn("Recomendado", res.verdict_summary)

    @patch("services.simulation_service.score_relic")
    def test_simulate_relic_swap_downgrade(self, mock_score_relic):
        """Valida simulação onde a peça candidata reduz o score da build."""

        def mock_scoring(game, char, slot, main, subs):
            if "taxa crit" in main.lower():
                return "SS", 90.0
            return "D", 20.0

        mock_score_relic.side_effect = mock_scoring

        old_piece = RelicPieceModel(
            slot="Corpo", name="Peitoral SS", main_stat="Taxa CRIT (32.4%)", sub_stats="Dano CRIT: 14.0%"
        )
        new_piece = RelicPieceModel(slot="Corpo", name="Peitoral Ruim", main_stat="DEF (40.0%)", sub_stats="DEF: 10")

        req = SimulateSwapRequest(
            game_id="hsr",
            char_name="Seele",
            target_slot="Corpo",
            replacement_relic=new_piece,
            current_relics=[old_piece],
        )

        res = simulate_relic_swap(req)
        self.assertFalse(res.is_upgrade)
        self.assertLess(res.score_diff, 0)
        self.assertIn("Não recomendado", res.verdict_summary)

    @patch("services.simulation_service.score_relic")
    def test_simulate_stat_deltas_and_speed_tuning_breakpoint(self, mock_score_relic):
        """Garante cálculo de delta de atributos e detecção de ativação de 134 SPD em HSR."""
        mock_score_relic.return_value = ("S", 75.0)

        # Bota antiga dava 20 SPD. Personagem atualmente tem 125 SPD.
        old_piece = RelicPieceModel(slot="Pés", main_stat="VEL (20)", sub_stats="HP: 50")
        # Bota nova dá 25 SPD + 4 SPD = 29 SPD (+9 SPD de ganho)
        new_piece = RelicPieceModel(slot="Pés", main_stat="VEL (25)", sub_stats="VEL: 4, Dano CRIT: 10.0%")

        req = SimulateSwapRequest(
            game_id="hsr",
            char_name="Acheron",
            target_slot="Pés",
            replacement_relic=new_piece,
            current_relics=[old_piece],
            current_stats={"speed": 125.0, "crit_rate": 60.0, "crit_dmg": 140.0},
        )

        res = simulate_relic_swap(req)

        # Verifica se o delta de velocidade foi calculado (+9.0)
        spd_diff = next((d for d in res.stat_diffs if d.stat_name == "VEL"), None)
        self.assertIsNotNone(spd_diff)
        self.assertEqual(spd_diff.diff, 9.0)
        self.assertEqual(spd_diff.formatted_diff, "+9.0")

        # Com 125 - 20 + 29 = 134 SPD, atingiu o breakpoint de Ciclo 0 de MoC (134 SPD)
        c0_found = any(
            "134" in str(fb) or "Ciclo 0" in str(fb) or "Action Value" in str(fb) for fb in res.breakpoint_feedback
        )
        self.assertTrue(c0_found)

    def test_api_simulate_swap_endpoint(self):
        """Valida requisição HTTP ao endpoint REST POST /api/relics/simulate-swap."""
        payload = {
            "game_id": "hsr",
            "char_name": "Seele",
            "target_slot": "feet",
            "replacement_relic": {
                "slot": "feet",
                "name": "Botas de Teste",
                "main_stat": "VEL (25)",
                "sub_stats": "Taxa CRIT: 6.0%, Dano CRIT: 12.0%",
            },
            "current_relics": [
                {"slot": "feet", "name": "Botas Antigas", "main_stat": "ATK (43.2%)", "sub_stats": "HP: 100"}
            ],
            "current_stats": {"speed": 115.0, "crit_rate": 55.0, "crit_dmg": 130.0},
        }

        res = self.client.post("/api/relics/simulate-swap", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("character_name", data)
        self.assertIn("target_slot", data)
        self.assertIn("old_build_score", data)
        self.assertIn("new_build_score", data)
        self.assertIn("score_diff", data)
        self.assertIn("stat_diffs", data)
        self.assertIn("verdict_summary", data)


if __name__ == "__main__":
    unittest.main()
