import unittest
import os
import sys
from fastapi.testclient import TestClient

# Garante importação dos módulos locais da raiz
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
            num_simulations=2000,
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
            target_rank=1,  # E1
            current_rank=0,  # E0 já possuído
            target_days=42,
            has_daily_pass=True,
            has_battle_pass=True,
            include_shop_resets=True,
            include_events_estimate=True,
            character_name="Sunday",
            num_simulations=2000,
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
            target_rank=2,  # M2 (3 cópias no total)
            current_rank=-1,  # Não possui
            target_days=21,
            has_daily_pass=False,
            character_name="Miyabi",
            num_simulations=1000,
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
            notes="Teste automatizado de meta",
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
            "include_events_estimate": True,
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
            "notes": "Planejamento Jane Doe",
        }
        resp_post = self.client.post("/api/gacha/goals", json=post_payload)
        self.assertEqual(resp_post.status_code, 200)
        goal_id = resp_post.json().get("goal_id")
        self.assertIsNotNone(goal_id)

        # 2. GET
        resp_get = self.client.get("/api/gacha/goals/zzz")
        self.assertEqual(resp_get.status_code, 200)
        goals_list = resp_get.json().get("goals", [])
        matched = next((g for g in goals_list if g["id"] == goal_id), None)
        self.assertIsNotNone(matched)
        self.assertIn("created_at", matched)
        self.assertIn("target_date", matched)
        self.assertIn("days_remaining", matched)
        self.assertIn("seconds_remaining", matched)
        self.assertIn("time_progress_pct", matched)
        self.assertIn("is_arrived", matched)
        self.assertIn("accumulated_pulls_now", matched)

        # 3. DELETE
        resp_del = self.client.delete(f"/api/gacha/goals/{goal_id}")
        self.assertEqual(resp_del.status_code, 200)
        self.assertEqual(resp_del.json().get("status"), "deleted")

    def test_goal_time_progression_and_arrival(self):
        """Valida contagem regressiva (correr do tempo) desde o dia criado até o dia da atualização do banner."""
        from datetime import datetime, timedelta

        base_created = datetime(2026, 10, 1, 12, 0, 0)
        target_dt = base_created + timedelta(days=20)

        goal_id = database.save_gacha_goal(
            game_id="hsr",
            character_name="Castorice",
            target_rank_str="E0",
            current_pulls=40,
            current_pity=10,
            is_guaranteed=False,
            target_days=20,
            has_daily_pass=True,
            success_rate=91.0,
            projected_pulls=80,
            notes="Teste de contagem regressiva",
            created_at=base_created.isoformat(),
            target_date=target_dt.isoformat(),
        )

        try:
            # Simula metade do tempo decorrido (10 dias após a criação)
            mid_now = base_created + timedelta(days=10)
            goal_mid = {
                "created_at": base_created.isoformat(),
                "target_date": target_dt.isoformat(),
                "target_days": 20,
                "current_pulls": 40,
                "projected_pulls": 80,
            }
            database.compute_goal_time_metrics(goal_mid, now_dt=mid_now)
            self.assertEqual(goal_mid["days_elapsed"], 10)
            self.assertEqual(goal_mid["days_remaining"], 10)
            self.assertAlmostEqual(goal_mid["time_progress_pct"], 50.0, places=1)
            self.assertFalse(goal_mid["is_arrived"])
            self.assertEqual(goal_mid["accumulated_pulls_now"], 60)

            # Simula chegada do dia da atualização/banner (20 dias completos)
            arrived_now = base_created + timedelta(days=21)
            goal_done = {
                "created_at": base_created.isoformat(),
                "target_date": target_dt.isoformat(),
                "target_days": 20,
                "current_pulls": 40,
                "projected_pulls": 80,
            }
            database.compute_goal_time_metrics(goal_done, now_dt=arrived_now)
            self.assertEqual(goal_done["days_elapsed"], 20)
            self.assertEqual(goal_done["days_remaining"], 0)
            self.assertEqual(goal_done["seconds_remaining"], 0)
            self.assertEqual(goal_done["time_progress_pct"], 100.0)
            self.assertTrue(goal_done["is_arrived"])
            self.assertEqual(goal_done["accumulated_pulls_now"], 80)
        finally:
            database.delete_gacha_goal(goal_id)

    def test_banner_schedule_hours_phase1_and_phase2(self):
        """Valida horários oficiais dos banners:
        - 1ª Fase (os 3 jogos): 23:30
        - 2ª Fase Genshin: 20:00
        - 2ª Fase HSR: 14:00
        - 2ª Fase ZZZ: 14:00
        """
        # 1ª Fase: todos os 3 jogos devem retornar 23:30
        self.assertEqual(database.get_banner_schedule_time("genshin", phase=1), (23, 30))
        self.assertEqual(database.get_banner_schedule_time("hsr", phase=1), (23, 30))
        self.assertEqual(database.get_banner_schedule_time("zzz", phase=1), (23, 30))

        # 2ª Fase: Genshin 20h, HSR e ZZZ 14h
        self.assertEqual(database.get_banner_schedule_time("genshin", phase=2), (20, 0))
        self.assertEqual(database.get_banner_schedule_time("hsr", phase=2), (14, 0))
        self.assertEqual(database.get_banner_schedule_time("zzz", phase=2), (14, 0))

    def test_save_goal_with_banner_phase_and_target_date_schedule(self):
        """Valida que salvar meta com banner_phase preserva os horários oficiais nos endpoints e no banco."""
        # 1. Meta Genshin 2ª Fase (deve chegar às 20:00)
        resp = self.client.post(
            "/api/gacha/goals",
            json={
                "game_id": "genshin",
                "character_name": "Mavuika",
                "target_rank_str": "C2",
                "current_pulls": 50,
                "current_pity": 20,
                "is_guaranteed": True,
                "target_days": 21,
                "has_daily_pass": True,
                "success_rate": 88.5,
                "projected_pulls": 140,
                "banner_phase": 2,
                "target_date": "2026-11-20T20:00:00",
            },
        )
        self.assertEqual(resp.status_code, 200)
        goal_id = resp.json().get("goal_id")

        try:
            resp_get = self.client.get("/api/gacha/goals/genshin")
            self.assertEqual(resp_get.status_code, 200)
            goals = resp_get.json().get("goals", [])
            saved = next((g for g in goals if g["id"] == goal_id), None)
            self.assertIsNotNone(saved)
            self.assertEqual(saved["banner_phase"], 2)
            self.assertEqual(saved["banner_time"], "20:00")
            self.assertTrue(saved["target_date"].endswith("20:00:00") or "20:00" in saved["target_date"])
        finally:
            database.delete_gacha_goal(goal_id)

        # 2. Meta HSR 2ª Fase (deve chegar às 14:00)
        resp_hsr = self.client.post(
            "/api/gacha/goals",
            json={
                "game_id": "hsr",
                "character_name": "Sunday",
                "target_rank_str": "E1",
                "current_pulls": 30,
                "current_pity": 10,
                "is_guaranteed": False,
                "target_days": 21,
                "has_daily_pass": True,
                "success_rate": 75.0,
                "projected_pulls": 110,
                "banner_phase": 2,
                "target_date": "2026-11-20T14:00:00",
            },
        )
        self.assertEqual(resp_hsr.status_code, 200)
        hsr_goal_id = resp_hsr.json().get("goal_id")

        try:
            resp_get_hsr = self.client.get("/api/gacha/goals/hsr")
            self.assertEqual(resp_get_hsr.status_code, 200)
            hsr_goals = resp_get_hsr.json().get("goals", [])
            saved_hsr = next((g for g in hsr_goals if g["id"] == hsr_goal_id), None)
            self.assertIsNotNone(saved_hsr)
            self.assertEqual(saved_hsr["banner_phase"], 2)
            self.assertEqual(saved_hsr["banner_time"], "14:00")
        finally:
            database.delete_gacha_goal(hsr_goal_id)

    def test_update_all_saved_goals_schedule(self):
        """Valida a função de atualização em lote das metas já salvas para os horários oficiais."""
        # Cria uma meta sem target_date definido
        gid = database.save_gacha_goal(
            game_id="zzz",
            character_name="Miyabi",
            target_rank_str="M0",
            current_pulls=20,
            current_pity=0,
            is_guaranteed=False,
            target_days=21,
            has_daily_pass=False,
            success_rate=60.0,
            projected_pulls=70,
            notes="Meta antiga sem horário fixo",
            banner_phase=2,
        )

        try:
            count = database.update_all_saved_goals_schedule()
            self.assertGreaterEqual(count, 1)

            goals = database.get_gacha_goals("zzz")
            matched = next((g for g in goals if g["id"] == gid), None)
            self.assertIsNotNone(matched)
            self.assertEqual(matched["banner_phase"], 2)
            self.assertEqual(matched["banner_time"], "14:00")
            self.assertIn("14:00:00", matched["target_date"])
        finally:
            database.delete_gacha_goal(gid)


if __name__ == "__main__":
    unittest.main()
