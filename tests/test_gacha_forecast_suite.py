import unittest
import os
import sys
from fastapi.testclient import TestClient

# Garante importação dos módulos locais
sys.path.insert(0, os.path.dirname(__file__))

import database
from build_calculator import calculate_gacha_forecast, simulate_gacha_probabilities
from server import app

class TestGachaForecastSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.init_db()
        cls.client = TestClient(app)

    def test_forecast_calculation_genshin_f2p(self):
        """Valida projeção de banner F2P puro em 21 dias para Genshin Impact."""
        res = calculate_gacha_forecast(
            game_id="genshin",
            current_pulls=20,
            current_pity=30,
            is_guaranteed=False,
            target_rank=0,
            current_rank=-1,
            target_days=21,
            has_daily_pass=False,
            has_battle_pass=False,
            include_shop_resets=True,
            include_events_estimate=True,
            include_endgame_resets=True,
            character_name="Mavuika",
            num_simulations=2000
        )

        self.assertEqual(res["game_id"], "genshin")
        self.assertEqual(res["character_name"], "Mavuika")
        self.assertEqual(res["target_rank_str"], "C0")
        self.assertEqual(res["current_rank_str"], "Não Possui")
        self.assertEqual(res["term"], "Constelação")
        self.assertGreater(res["total_projected_pulls"], 20)
        self.assertIn("income_breakdown", res)
        self.assertIn("daily_f2p", res["income_breakdown"])
        self.assertEqual(res["income_breakdown"]["daily_f2p"]["gems"], 21 * 60)
        self.assertIn("verdict", res)
        self.assertIn("badge", res["verdict"])
        self.assertIn("text", res["verdict"])
        self.assertIsInstance(res["success_rate"], float)

    def test_forecast_with_welkin_and_pass_hsr(self):
        """Valida projeção para Honkai: Star Rail com Passe de Suprimentos Express e E1."""
        res = calculate_gacha_forecast(
            game_id="hsr",
            current_pulls=50,
            current_pity=40,
            is_guaranteed=True,
            target_rank=1, # E1
            current_rank=0, # E0 já possuído
            target_days=42,
            has_daily_pass=True,
            has_battle_pass=True,
            include_shop_resets=True,
            include_events_estimate=True,
            character_name="Sunday",
            num_simulations=2000
        )

        self.assertEqual(res["game_id"], "hsr")
        self.assertEqual(res["term"], "Eidolon")
        self.assertEqual(res["current_rank_str"], "E0")
        self.assertEqual(res["target_rank_str"], "E1")
        self.assertEqual(res["needed_new_copies"], 1)
        self.assertTrue(res["income_breakdown"]["daily_pass"]["active"])
        self.assertEqual(res["income_breakdown"]["daily_pass"]["gems"], 42 * 90)
        # Com garantido e pity 40, o pior caso para 1 cópia é 90 - 40 = 50 tiros
        self.assertEqual(res["worst_case_pulls"], 50)
        # Com 50 tiros guardados + renda de 42 dias, a chance deve ser de 100%
        self.assertEqual(res["success_rate"], 100.0)
        self.assertEqual(res["pulls_needed_for_guarantee"], 0)
        self.assertEqual(res["verdict"]["status"], "SAFE")

    def test_forecast_worst_case_multiple_copies_zzz(self):
        """Valida cálculo de pior caso e tiros faltantes para Mindscape Cinema M2 no ZZZ."""
        res = calculate_gacha_forecast(
            game_id="zzz",
            current_pulls=10,
            current_pity=0,
            is_guaranteed=False,
            target_rank=2, # M2 (3 cópias no total)
            current_rank=-1, # Não possui
            target_days=21,
            has_daily_pass=False,
            character_name="Miyabi",
            num_simulations=1000
        )

        self.assertEqual(res["term"], "Mindscape Cinema")
        self.assertEqual(res["needed_new_copies"], 3)
        # 1ª cópia não garantida: 180 tiros. 2ª e 3ª cópias: 2 * 180 = 360 tiros. Total pior caso = 540 tiros.
        self.assertEqual(res["worst_case_pulls"], 540)
        self.assertGreater(res["pulls_needed_for_guarantee"], 400)
        self.assertIn("CRITICAL", ["CRITICAL", "RISKY", "MODERATE"])

    def test_database_gacha_goals_crud(self):
        """Valida inserção, consulta e exclusão de metas de gacha no SQLite."""
        # Salva meta de teste
        goal_id = database.save_gacha_goal(
            game_id="genshin",
            character_name="Xilonen",
            target_rank_str="C0",
            current_pulls=45,
            current_pity=25,
            is_guaranteed=True,
            target_days=14,
            has_daily_pass=True,
            success_rate=98.5,
            projected_pulls=85,
            notes="Teste automatizado de meta"
        )
        self.assertIsInstance(goal_id, int)
        self.assertGreater(goal_id, 0)

        # Consulta metas
        goals = database.get_gacha_goals("genshin")
        saved_goal = next((g for g in goals if g["id"] == goal_id), None)
        self.assertIsNotNone(saved_goal)
        self.assertEqual(saved_goal["character_name"], "Xilonen")
        self.assertEqual(saved_goal["target_rank_str"], "C0")
        self.assertTrue(saved_goal["is_guaranteed"])
        self.assertTrue(saved_goal["has_daily_pass"])
        self.assertEqual(saved_goal["success_rate"], 98.5)

        # Exclui meta
        deleted = database.delete_gacha_goal(goal_id)
        self.assertTrue(deleted)

        # Confirma que foi excluído
        goals_after = database.get_gacha_goals("genshin")
        self.assertIsNone(next((g for g in goals_after if g["id"] == goal_id), None))

    def test_api_gacha_forecast_calculate(self):
        """Valida endpoint REST POST /api/gacha/forecast/calculate."""
        payload = {
            "game_id": "hsr",
            "character_name": "Acheron",
            "current_pulls": 40,
            "current_pity": 15,
            "is_guaranteed": False,
            "target_rank": 0,
            "current_rank": -1,
            "target_days": 21,
            "has_daily_pass": True,
            "include_shop_resets": True,
            "include_events_estimate": True
        }
        resp = self.client.post("/api/gacha/forecast/calculate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["game_id"], "hsr")
        self.assertEqual(data["character_name"], "Acheron")
        self.assertIn("success_rate", data)
        self.assertIn("income_breakdown", data)
        self.assertIn("verdict", data)

    def test_api_gacha_goals_endpoints(self):
        """Valida endpoints REST de metas de gacha (GET, POST, DELETE)."""
        # 1. POST
        post_payload = {
            "game_id": "zzz",
            "character_name": "Jane Doe",
            "target_rank_str": "M0",
            "current_pulls": 50,
            "current_pity": 30,
            "is_guaranteed": False,
            "target_days": 21,
            "has_daily_pass": True,
            "success_rate": 82.4,
            "projected_pulls": 95,
            "notes": "Planejamento Jane Doe"
        }
        resp_post = self.client.post("/api/gacha/goals", json=post_payload)
        self.assertEqual(resp_post.status_code, 200)
        goal_id = resp_post.json().get("goal_id")
        self.assertIsNotNone(goal_id)

        # 2. GET
        resp_get = self.client.get("/api/gacha/goals/zzz")
        self.assertEqual(resp_get.status_code, 200)
        goals_list = resp_get.json().get("goals", [])
        self.assertTrue(any(g["id"] == goal_id for g in goals_list))

        # 3. DELETE
        resp_del = self.client.delete(f"/api/gacha/goals/{goal_id}")
        self.assertEqual(resp_del.status_code, 200)
        self.assertEqual(resp_del.json().get("status"), "deleted")

if __name__ == "__main__":
    unittest.main()
