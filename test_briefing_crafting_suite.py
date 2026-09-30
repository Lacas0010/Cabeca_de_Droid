import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from server import app
from build_calculator import recommend_relic_crafting
from notifications import notifier

class TestBriefingCraftingSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_relic_craft_recommendations_hsr(self):
        """Valida que o conselheiro recomenda peças chave de ERR/SPD para suportes de HSR."""
        mock_roster = [
            {"name": "Robin", "level": 80, "rarity": 5, "overall_score": 55.0, "overall_grade": "C"},
            {"name": "Acheron", "level": 80, "rarity": 5, "overall_score": 60.0, "overall_grade": "B"},
            {"name": "March 7th", "level": 60, "rarity": 4, "overall_score": 40.0, "overall_grade": "D"}
        ]
        
        result = recommend_relic_crafting("hsr", mock_roster)
        self.assertEqual(result["game_id"], "hsr")
        self.assertIn("Resina Automodeladora", result["crafting_item_name"])
        self.assertTrue(len(result["recommendations"]) > 0)
        
        top_rec = result["recommendations"][0]
        self.assertIn("character_name", top_rec)
        self.assertIn("recommended_main_stat", top_rec)
        self.assertIn("expected_gain", top_rec)

    def test_relic_craft_recommendations_genshin(self):
        """Valida recomendações de Elixir Santificador para Genshin."""
        mock_roster = [
            {"name": "Neuvillette", "level": 90, "rarity": 5, "overall_score": 50.0, "overall_grade": "C"},
            {"name": "Furina", "level": 90, "rarity": 5, "overall_score": 58.0, "overall_grade": "C"}
        ]
        
        result = recommend_relic_crafting("genshin", mock_roster)
        self.assertEqual(result["game_id"], "genshin")
        self.assertIn("Elixir Santificador", result["crafting_item_name"])
        self.assertTrue(len(result["recommendations"]) > 0)
        self.assertTrue(any("Hydro" in r["recommended_main_stat"] or "Recarga" in r["recommended_main_stat"] for r in result["recommendations"]))

    def test_morning_briefing_generation(self):
        """Valida a consolidação correta do relatório Morning Briefing."""
        briefing = notifier.generate_morning_briefing()
        
        self.assertIn("title", briefing)
        self.assertIn("Morning Briefing", briefing["title"])
        self.assertIn("games", briefing)
        self.assertEqual(len(briefing["games"]), 3)
        self.assertIn("discord_fields", briefing)
        self.assertTrue(len(briefing["discord_fields"]) >= 1)

    def test_api_craft_recommendations_endpoint(self):
        """Testa o endpoint GET /api/relics/craft-recommendations/{game_id}."""
        res = self.client.get("/api/relics/craft-recommendations/hsr")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["game_id"], "hsr")
        self.assertIn("recommendations", data)

    def test_api_briefing_today_endpoint(self):
        """Testa o endpoint GET /api/briefing/today."""
        res = self.client.get("/api/briefing/today")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("title", data)
        self.assertIn("games", data)

    @patch("notifications.notifier.send_notification")
    def test_api_briefing_send_now_endpoint(self, mock_send):
        """Testa o endpoint POST /api/briefing/send-now com mock de notificação."""
        mock_send.return_value = {"success": True}
        res = self.client.post("/api/briefing/send-now")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("briefing", data)
        self.assertIn("delivery", data)

if __name__ == "__main__":
    unittest.main()
