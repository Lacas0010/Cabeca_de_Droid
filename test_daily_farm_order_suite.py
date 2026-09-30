import sys
import os
import unittest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient

import server
import database
from build_calculator import generate_daily_farm_order, get_daily_farm_recommendations
from static_data_manager import static_data_manager

class TestDailyFarmOrderSuite(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(server.app)
        database.init_db()

    def test_database_farm_task_persistence(self):
        today = datetime.now().strftime("%Y-%m-%d")
        database.clear_completed_farm_tasks(today, "genshin")
        
        # Inicialmente vazio
        completed = database.get_completed_farm_tasks(today, "genshin")
        self.assertEqual(len(completed), 0)

        # Marca uma tarefa como concluída
        task_id = "talent_Furina_Justica"
        res_set = database.set_farm_task_completed(today, "genshin", task_id, True)
        self.assertTrue(res_set)

        completed_after = database.get_completed_farm_tasks(today, "genshin")
        self.assertIn(task_id, completed_after)

        # Desmarca a tarefa
        res_unset = database.set_farm_task_completed(today, "genshin", task_id, False)
        self.assertFalse(res_unset)

        completed_final = database.get_completed_farm_tasks(today, "genshin")
        self.assertNotIn(task_id, completed_final)

    def test_generate_daily_farm_order_genshin_with_roster(self):
        mock_roster = [
            {
                "name": "Furina",
                "level": 70,
                "rarity": 5,
                "element": "Hydro",
                "icon": "/assets/furina.png",
                "skills": [
                    {"name": "Ataque Normal", "level": 1, "max_level": 10},
                    {"name": "Salon Solitaire", "level": 6, "max_level": 10},
                    {"name": "Povo Alegre", "level": 6, "max_level": 10}
                ],
                "weapon": {"name": "Esplendor das Águas Silenciosas", "level": 70, "max_level": 90},
                "relics": []
            }
        ]

        mock_meta = {
            "furina": {
                "name": "Furina",
                "tier": "SSS",
                "relics": ["Golden Troupe"],
                "talent_priority": "Burst > Skill > Normal"
            }
        }

        # Simula Terça-feira (weekday=1), dia em que Justiça está aberta
        order = generate_daily_farm_order(
            game_id="genshin",
            roster=mock_roster,
            meta_data=mock_meta,
            current_energy=160,
            max_energy=200,
            weekday=1
        )

        self.assertEqual(order["game_id"], "genshin")
        self.assertEqual(order["weekday_name"], "Terça-feira")
        self.assertEqual(order["energy"]["current"], 160)
        self.assertEqual(order["energy"]["max"], 200)
        self.assertTrue(len(order["tasks"]) > 0)

        # Verifica se o primeiro passo é o Domínio de Talentos aberto hoje para Furina
        first_task = order["tasks"][0]
        self.assertEqual(first_task["type"], "talent_domain")
        self.assertEqual(first_task["target_character"], "Furina")
        self.assertIn("Justiça", first_task["material_name"])
        self.assertTrue(first_task["available_now"])
        self.assertEqual(first_task["time_estimate"], "Disponível Agora")

        # Verifica se o texto sumarizado está gerado
        self.assertIn("ORDEM DE SERVIÇO DO DIA", order["quick_summary_text"].upper())
        self.assertIn("Furina", order["quick_summary_text"])

    def test_generate_daily_farm_order_energy_deficit_estimates(self):
        mock_roster = [
            {
                "name": "Acheron",
                "level": 60,
                "rarity": 5,
                "element": "Lightning",
                "icon": "/assets/acheron.png",
                "skills": [
                    {"name": "Ataque Básico", "level": 1, "max_level": 6},
                    {"name": "Perícia", "level": 4, "max_level": 10},
                    {"name": "Perua Suprema", "level": 4, "max_level": 10}
                ],
                "weapon": {"name": "Ao Longo da Margem Passada", "level": 60, "max_level": 80},
                "relics": []
            }
        ]

        # Jogador com apenas 30 de energia atual (menos que os passos cumulativos)
        order = generate_daily_farm_order(
            game_id="hsr",
            roster=mock_roster,
            meta_data={},
            current_energy=30,
            max_energy=300
        )

        self.assertEqual(order["game_id"], "hsr")
        self.assertTrue(len(order["tasks"]) >= 2)

        # Primeiro passo gasta 60 ou 30 energia -> se gasto > 30, o segundo passo já terá estimativa de espera
        last_task = order["tasks"][-1]
        self.assertFalse(last_task["available_now"])
        self.assertIn("Disponível às", last_task["time_estimate"])

    def test_generate_daily_farm_order_empty_roster_fallback(self):
        # Quando o jogador não possui personagens pendentes
        order = generate_daily_farm_order(
            game_id="zzz",
            roster=[],
            meta_data={},
            current_energy=120,
            max_energy=240
        )

        self.assertEqual(order["game_id"], "zzz")
        self.assertEqual(len(order["tasks"]), 1)
        self.assertEqual(order["tasks"][0]["type"], "currency")
        self.assertEqual(order["tasks"][0]["material_name"], "Dennys")

    def test_rest_api_farm_order_endpoints(self):
        # 1. GET /api/farm/order-of-day/genshin
        res = self.client.get("/api/farm/order-of-day/genshin")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["game_id"], "genshin")
        self.assertIn("tasks", data)
        self.assertIn("energy", data)
        self.assertIn("quick_summary_text", data)

        # 2. POST /api/farm/order-of-day/toggle-step
        if data["tasks"]:
            test_task_id = data["tasks"][0]["id"]
            toggle_res = self.client.post("/api/farm/order-of-day/toggle-step", json={
                "game_id": "genshin",
                "task_id": test_task_id,
                "completed": True
            })
            self.assertEqual(toggle_res.status_code, 200)
            self.assertTrue(toggle_res.json()["completed"])

            # Desmarca novamente
            toggle_res_off = self.client.post("/api/farm/order-of-day/toggle-step", json={
                "game_id": "genshin",
                "task_id": test_task_id,
                "completed": False
            })
            self.assertEqual(toggle_res_off.status_code, 200)
            self.assertFalse(toggle_res_off.json()["completed"])

        # 3. POST /api/farm/order-of-day/send-notification
        with patch.object(server.notifier, "send_notification", return_value={"status": "mock_sent", "results": {}}):
            notify_res = self.client.post("/api/farm/order-of-day/send-notification", json={
                "game_id": "genshin"
            })
            self.assertEqual(notify_res.status_code, 200)
            self.assertEqual(notify_res.json()["status"], "success")

if __name__ == "__main__":
    unittest.main()
