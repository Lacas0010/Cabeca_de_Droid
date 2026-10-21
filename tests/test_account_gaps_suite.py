import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from server import app
from build_calculator import analyze_account_gaps

class TestAccountGapsSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_genshin_gaps_detection_starter_roster(self):
        """Valida detecção correta de lacunas graves em conta iniciante de Genshin."""
        # Conta sem sustentador T0, sem aplicador hydro e sem Kazuha/Sucrose
        starter_roster = [
            {"name": "Diluc", "level": 80, "rarity": 5, "element": "Pyro"},
            {"name": "Amber", "level": 20, "rarity": 4, "element": "Pyro"},
            {"name": "Kaeya", "level": 50, "rarity": 4, "element": "Cryo"},
            {"name": "Lisa", "level": 20, "rarity": 4, "element": "Electro"},
            {"name": "Barbara", "level": 60, "rarity": 4, "element": "Hydro"}
        ]
        
        result = analyze_account_gaps("genshin", starter_roster)
        
        self.assertEqual(result["game_id"], "genshin")
        self.assertLess(result["overall_score"], 70)
        self.assertIn(result["score_grade"], ["B", "C"])
        
        # Verifica se as lacunas críticas foram apontadas
        gap_ids = [g["id"] for g in result["critical_gaps"]]
        self.assertIn("genshin_no_t0_sustain", gap_ids)
        self.assertIn("genshin_lack_hydro", gap_ids)
        self.assertIn("genshin_no_vv_shred", gap_ids)
        
        # Recomendações de pull devem conter suportes e sustentação
        self.assertTrue(len(result["pull_recommendations"]) > 0)
        self.assertTrue(any("Sustentador" in pr["archetype"] or "Buffer" in pr["archetype"] for pr in result["pull_recommendations"]))

    def test_genshin_meta_roster_high_readiness(self):
        """Valida que uma conta veterana e meta de Genshin recebe pontuação de Rank S."""
        meta_roster = [
            {"name": "Neuvillette", "level": 90, "rarity": 5, "element": "Hydro"},
            {"name": "Furina", "level": 90, "rarity": 5, "element": "Hydro"},
            {"name": "Kaedehara Kazuha", "level": 90, "rarity": 5, "element": "Anemo"},
            {"name": "Zhongli", "level": 90, "rarity": 5, "element": "Geo"},
            {"name": "Arlecchino", "level": 90, "rarity": 5, "element": "Pyro"},
            {"name": "Yelan", "level": 90, "rarity": 5, "element": "Hydro"},
            {"name": "Bennett", "level": 90, "rarity": 4, "element": "Pyro"},
            {"name": "Xiangling", "level": 90, "rarity": 4, "element": "Pyro"},
            {"name": "Nahida", "level": 90, "rarity": 5, "element": "Dendro"},
            {"name": "Kuki Shinobu", "level": 90, "rarity": 4, "element": "Electro"}
        ]
        
        result = analyze_account_gaps("genshin", meta_roster)
        
        self.assertGreaterEqual(result["overall_score"], 85)
        self.assertEqual(result["score_grade"], "S")
        self.assertEqual(result["endgame_readiness"]["teams_ready"], 2)
        self.assertEqual(len(result["critical_gaps"]), 0)

    def test_hsr_gaps_detection_missing_harmony_and_sustain(self):
        """Valida detecção de lacuna crítica de Harmonia Tier 0 e Sustentação 5★ em HSR."""
        roster = [
            {"name": "Dan Heng", "level": 70, "rarity": 4, "element": "Wind"},
            {"name": "Serval", "level": 70, "rarity": 4, "element": "Lightning"},
            {"name": "Natasha", "level": 70, "rarity": 4, "element": "Physical"},
            {"name": "March 7th", "level": 60, "rarity": 4, "element": "Ice"}
        ]
        
        result = analyze_account_gaps("hsr", roster)
        
        self.assertEqual(result["game_id"], "hsr")
        self.assertLess(result["overall_score"], 60)
        
        gap_ids = [g["id"] for g in result["critical_gaps"]]
        self.assertIn("hsr_lack_tier0_harmony", gap_ids)
        self.assertIn("hsr_lack_5star_sustain", gap_ids)
        
        # Puxadas recomendadas devem listar Robin, Sunday ou Ruan Mei
        rec_chars = [c for pr in result["pull_recommendations"] for c in pr["characters"]]
        self.assertTrue(any(ch in rec_chars for ch in ["Robin", "Sunday", "Ruan Mei"]))

    def test_zzz_gaps_detection_no_s_rank_stunner(self):
        """Valida que a falta de Atordoador S-Rank em ZZZ é sinalizada com precisão."""
        roster = [
            {"name": "Billy", "level": 50, "rarity": 4},
            {"name": "Anby", "level": 50, "rarity": 4},
            {"name": "Nicole", "level": 50, "rarity": 4},
            {"name": "Corin", "level": 40, "rarity": 4}
        ]
        
        result = analyze_account_gaps("zzz", roster)
        
        self.assertEqual(result["game_id"], "zzz")
        gap_ids = [g["id"] for g in result["critical_gaps"]]
        self.assertIn("zzz_no_s_stunner", gap_ids)
        
        # Qingyi e Caesar devem ser recomendadas
        rec_chars = [c for pr in result["pull_recommendations"] for c in pr["characters"]]
        self.assertTrue("Qingyi" in rec_chars or "Caesar" in rec_chars)

    def test_api_account_gaps_endpoint(self):
        """Testa o endpoint GET /api/strategy/account-gaps/{game_id}."""
        # Teste para Genshin
        res_genshin = self.client.get("/api/strategy/account-gaps/genshin")
        self.assertEqual(res_genshin.status_code, 200)
        data_g = res_genshin.json()
        self.assertEqual(data_g["game_id"], "genshin")
        self.assertIn("overall_score", data_g)
        self.assertIn("critical_gaps", data_g)
        self.assertIn("pull_recommendations", data_g)

        # Teste para HSR
        res_hsr = self.client.get("/api/strategy/account-gaps/hsr")
        self.assertEqual(res_hsr.status_code, 200)
        data_h = res_hsr.json()
        self.assertEqual(data_h["game_id"], "hsr")

        # Teste para jogo inválido
        res_invalid = self.client.get("/api/strategy/account-gaps/invalid_game")
        self.assertEqual(res_invalid.status_code, 400)

    @patch("server.GroqRAG")
    def test_api_ask_ai_gaps_endpoint(self, mock_groq_rag_class):
        """Testa o endpoint POST /api/strategy/ask-ai-gaps com mock de IA."""
        mock_instance = MagicMock()
        mock_instance.client = MagicMock()
        mock_instance.ask_assistant.return_value = "Plano Estratégico: Priorize Robin no próximo banner para fechar o time com Feixiao."
        mock_groq_rag_class.return_value = mock_instance

        payload = {
            "game_id": "hsr",
            "custom_question": "Quem devo puxar na próxima versão?"
        }
        res = self.client.post("/api/strategy/ask-ai-gaps", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("has_ai"))
        self.assertIn("Plano Estratégico", data.get("ai_response"))
        self.assertIn("analysis", data)

if __name__ == "__main__":
    unittest.main()
