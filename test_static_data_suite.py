import sys
import os
import unittest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

import server
import database
from static_data_manager import static_data_manager, StaticDataManager, GENSHIN_CHARACTERS_SEED, HSR_CHARACTERS_SEED, ZZZ_CHARACTERS_SEED
from build_calculator import calculate_ascension

class TestStaticDataSuite(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(server.app)
        database.init_db()

    def test_static_data_manager_offline_seed_load(self):
        # 1. Verifica integridade do seed carregado
        status = static_data_manager.get_sync_status()
        self.assertTrue(status["genshin"]["offline_ready"])
        self.assertTrue(status["genshin"]["characters"] >= len(GENSHIN_CHARACTERS_SEED))
        self.assertTrue(status["hsr"]["characters"] >= len(HSR_CHARACTERS_SEED))
        self.assertTrue(status["zzz"]["characters"] >= len(ZZZ_CHARACTERS_SEED))

    def test_character_profile_queries(self):
        # Genshin
        furina = static_data_manager.get_character_profile("genshin", "furina")
        self.assertIsNotNone(furina)
        self.assertEqual(furina["name"], "Furina")
        self.assertIn("Justiça", furina["talent_book"])
        self.assertEqual(furina["boss_mat"], "Gota d'Água Não Envelhecida")

        # HSR
        acheron = static_data_manager.get_character_profile("hsr", "acheron")
        self.assertIsNotNone(acheron)
        self.assertEqual(acheron["name"], "Acheron")
        self.assertEqual(acheron["path"], "Nihility")

        # ZZZ
        miyabi = static_data_manager.get_character_profile("zzz", "miyabi")
        self.assertIsNotNone(miyabi)
        self.assertEqual(miyabi["specialty"], "Anomaly")

        # Personagem inexistente
        fake = static_data_manager.get_character_profile("genshin", "personagem_inexistente_xyz")
        self.assertIsNone(fake)

    def test_daily_farm_schedules(self):
        # 1. Genshin - Segunda-feira (weekday=0)
        sch_mon = static_data_manager.get_daily_farm_schedule("genshin", weekday=0)
        self.assertEqual(sch_mon["weekday"], 0)
        self.assertEqual(sch_mon["weekday_name"], "Segunda-feira")
        self.assertFalse(sch_mon["is_all_open_sunday"])
        self.assertTrue(len(sch_mon["open_talents"]) > 0)
        talent_names_mon = [t["material"] for t in sch_mon["open_talents"]]
        self.assertTrue(any("Liberdade" in t for t in talent_names_mon))
        self.assertTrue(any("Prosperidade" in t for t in talent_names_mon))

        # 2. Genshin - Domingo (weekday=6)
        sch_sun = static_data_manager.get_daily_farm_schedule("genshin", weekday=6)
        self.assertEqual(sch_sun["weekday"], 6)
        self.assertTrue(sch_sun["is_all_open_sunday"])
        self.assertTrue(len(sch_sun["farmable_characters"]) >= len(GENSHIN_CHARACTERS_SEED))

        # 3. HSR & ZZZ - Daily
        sch_hsr = static_data_manager.get_daily_farm_schedule("hsr")
        self.assertEqual(sch_hsr["game_id"], "hsr")
        self.assertTrue(len(sch_hsr["farmable_characters"]) > 0)

        sch_zzz = static_data_manager.get_daily_farm_schedule("zzz")
        self.assertEqual(sch_zzz["game_id"], "zzz")
        self.assertTrue(len(sch_zzz["farmable_characters"]) > 0)

    def test_sync_upstream_with_mock_and_fallback(self):
        # Simula resposta bem-sucedida de GitHub/CDN para HSR
        mock_hsr_upstream = {
            "9999": {
                "name": "Novo Personagem Teste",
                "rarity": 5,
                "element": "Fire",
                "path": "Destruction"
            }
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_hsr_upstream

        with patch("requests.get", return_value=mock_resp):
            sync_res = static_data_manager.sync_upstream_data("hsr")
            self.assertEqual(sync_res["hsr"]["status"], "success")
            self.assertIn("StarRailRes", sync_res["hsr"]["source"])

            # Verifica se o personagem integrado pode ser consultado
            new_char = static_data_manager.get_character_profile("hsr", "Novo Personagem Teste")
            self.assertIsNotNone(new_char)
            self.assertEqual(new_char["element"], "Fire")

        # Simula falha de rede/timeout -> Graceful fallback
        with patch("requests.get", side_effect=Exception("Connection timed out")):
            sync_fallback = static_data_manager.sync_upstream_data("hsr")
            self.assertIn(sync_fallback["hsr"]["status"], ["offline_ready", "success"])
            # Continua funcionando 100% offline
            acheron = static_data_manager.get_character_profile("hsr", "acheron")
            self.assertIsNotNone(acheron)

    def test_database_static_data_manifests(self):
        # 1. Salva manifesto no banco de dados SQLite
        database.save_static_data_manifest("genshin", "v1.2.0", 85, "success", "HoYoWiki CDN")
        
        # 2. Consulta manifesto específico
        manifest = database.get_static_data_manifest("genshin")
        self.assertIsNotNone(manifest)
        self.assertEqual(manifest["game_id"], "genshin")
        self.assertEqual(manifest["version"], "v1.2.0")
        self.assertEqual(manifest["item_count"], 85)

        # 3. Consulta todos os manifestos
        all_manifests = database.get_static_data_manifests()
        self.assertTrue(len(all_manifests) >= 1)
        self.assertTrue(any(m["game_id"] == "genshin" for m in all_manifests))

    def test_calculate_ascension_enriched_with_static_data(self):
        # Cálculo básico sem personagem
        res_generic = calculate_ascension("genshin", 20, 90)
        self.assertIsNotNone(res_generic)
        self.assertEqual(res_generic["boss_item_name"], "Materiais de Chefe")

        # Cálculo enriquecido com personagem Furina
        res_furina = calculate_ascension("genshin", 20, 90, char_name="Furina")
        self.assertIsNotNone(res_furina)
        self.assertEqual(res_furina["boss_item_name"], "Gota d'Água Não Envelhecida")
        self.assertEqual(res_furina["local_specialty"], "Lírio de Lakelight")
        self.assertIn("Justiça", res_furina["talent_material"])
        self.assertIn(1, res_furina["domain_days"]) # Terça

    def test_rest_api_static_data_endpoints(self):
        # 1. GET /api/static-data/status
        res_status = self.client.get("/api/static-data/status")
        self.assertEqual(res_status.status_code, 200)
        data_status = res_status.json()
        self.assertEqual(data_status["status"], "success")
        self.assertIn("summary", data_status)

        # 2. POST /api/static-data/sync
        res_sync = self.client.post("/api/static-data/sync", json={"game_id": "genshin"})
        self.assertEqual(res_sync.status_code, 200)
        data_sync = res_sync.json()
        self.assertEqual(data_sync["status"], "success")
        self.assertIn("genshin", data_sync["results"])

        # 3. GET /api/static-data/schedule/genshin
        res_sch = self.client.get("/api/static-data/schedule/genshin?weekday=1")
        self.assertEqual(res_sch.status_code, 200)
        data_sch = res_sch.json()
        self.assertEqual(data_sch["weekday_name"], "Terça-feira")

        # 4. GET /api/static-data/character/genshin/furina
        res_char = self.client.get("/api/static-data/character/genshin/furina")
        self.assertEqual(res_char.status_code, 200)
        data_char = res_char.json()
        self.assertEqual(data_char["name"], "Furina")

        # 5. GET /api/static-data/all-characters/hsr
        res_all = self.client.get("/api/static-data/all-characters/hsr")
        self.assertEqual(res_all.status_code, 200)
        data_all = res_all.json()
        self.assertTrue(data_all["total"] > 0)

        # 6. POST /api/materials/calculate com enriquecimento
        res_mat = self.client.post("/api/materials/calculate", json={
            "game_id": "genshin",
            "char_name": "Furina",
            "current_level": 50,
            "target_level": 90
        })
        self.assertEqual(res_mat.status_code, 200)
        mat_data = res_mat.json()
        self.assertEqual(mat_data["boss_item_name"], "Gota d'Água Não Envelhecida")
        self.assertEqual(mat_data["local_specialty"], "Lírio de Lakelight")

if __name__ == "__main__":
    unittest.main()
