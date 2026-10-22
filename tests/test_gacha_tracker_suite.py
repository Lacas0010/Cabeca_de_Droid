import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from server import app
import database
from services.gacha_tracker_service import (
    normalize_banner_category,
    is_standard_5_star,
    calculate_gacha_tracker_stats,
    import_gacha_log_data,
    export_gacha_log_uigf,
)


class TestGachaTrackerSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        # Banco SQLite temporário isolado
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_path = self.temp_db_file.name
        self.temp_db_file.close()

        self.orig_db_name = database.DATABASE_NAME
        database.DATABASE_NAME = self.temp_db_path
        database.init_db()

    def tearDown(self):
        database.DATABASE_NAME = self.orig_db_name
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_normalize_banner_category(self):
        """Valida mapeamento de gacha_type oficial para categorias canônicas."""
        # Genshin
        self.assertEqual(normalize_banner_category("genshin", "301"), "character")
        self.assertEqual(normalize_banner_category("genshin", "400"), "character")
        self.assertEqual(normalize_banner_category("genshin", "302"), "weapon")
        self.assertEqual(normalize_banner_category("genshin", "200"), "standard")

        # HSR
        self.assertEqual(normalize_banner_category("hsr", "11"), "character")
        self.assertEqual(normalize_banner_category("hsr", "12"), "weapon")
        self.assertEqual(normalize_banner_category("hsr", "1"), "standard")

        # ZZZ
        self.assertEqual(normalize_banner_category("zzz", "2001"), "character")
        self.assertEqual(normalize_banner_category("zzz", "3001"), "weapon")
        self.assertEqual(normalize_banner_category("zzz", "1001"), "standard")

    def test_is_standard_5_star(self):
        """Valida identificação de 5★ do mochileiro permanente."""
        # Genshin
        self.assertTrue(is_standard_5_star("genshin", "Diluc"))
        self.assertTrue(is_standard_5_star("genshin", "Qiqi"))
        self.assertFalse(is_standard_5_star("genshin", "Furina"))

        # HSR
        self.assertTrue(is_standard_5_star("hsr", "Bailu"))
        self.assertTrue(is_standard_5_star("hsr", "Gepard"))
        self.assertFalse(is_standard_5_star("hsr", "Acheron"))

        # ZZZ
        self.assertTrue(is_standard_5_star("zzz", "Koleda"))
        self.assertTrue(is_standard_5_star("zzz", "Soldier 11"))
        self.assertFalse(is_standard_5_star("zzz", "Jane Doe"))

    def test_save_and_get_gacha_pulls(self):
        """Valida inserção de puxadas, ordenação cronológica e deduplicação."""
        pulls = [
            {"id": "p1", "name": "Flechas", "rarity": 3, "time": "2026-01-01 10:00:00", "gacha_type": "11"},
            {"id": "p2", "name": "Dan Heng", "rarity": 4, "time": "2026-01-01 10:01:00", "gacha_type": "11"},
        ]
        inserted, ignored = database.save_gacha_pulls("hsr", "700123", pulls)
        self.assertEqual(inserted, 2)
        self.assertEqual(ignored, 0)

        # Reinsere para testar deduplicação
        ins2, ign2 = database.save_gacha_pulls("hsr", "700123", pulls)
        self.assertEqual(ins2, 0)
        self.assertEqual(ign2, 2)

        # Consulta
        saved = database.get_gacha_pulls("hsr", uid="700123")
        self.assertEqual(len(saved), 2)
        self.assertEqual(saved[0]["id"], "p1")
        self.assertEqual(saved[1]["id"], "p2")

    def test_calculate_pity_and_5050_guaranteed_after_loss(self):
        """
        Simula histórico onde o jogador perde o 50/50 para Bailu no tiro 75,
        e dá mais 30 tiros. Pity atual deve ser 30 e o próximo 5★ GARANTIDO!
        """
        pulls = []
        # 74 tiros de 3★
        for i in range(1, 75):
            pulls.append(
                {
                    "id": f"p_3s_{i}",
                    "name": "Arma 3 Estrelas",
                    "rarity": 3,
                    "time": f"2026-01-01 10:{i:02d}:00",
                    "gacha_type": "11",
                    "banner_category": "character",
                }
            )
        # Tiro 75: Bailu (Derrota no 50/50)
        pulls.append(
            {
                "id": "p_bailu_75",
                "name": "Bailu",
                "rarity": 5,
                "time": "2026-01-01 11:30:00",
                "gacha_type": "11",
                "banner_category": "character",
            }
        )
        # Mais 30 tiros após a Bailu
        for i in range(1, 31):
            pulls.append(
                {
                    "id": f"p_after_{i}",
                    "name": "Arma 3 Estrelas",
                    "rarity": 3,
                    "time": f"2026-01-02 10:{i:02d}:00",
                    "gacha_type": "11",
                    "banner_category": "character",
                }
            )

        database.save_gacha_pulls("hsr", "700999", pulls)
        database.set_active_account("hsr", "700999")

        stats = calculate_gacha_tracker_stats("hsr", uid="700999")
        char_banner = stats.character_banner

        # Pity atual deve ser 30
        self.assertEqual(char_banner.current_pity, 30)
        # Próximo 5★ está GARANTIDO (perdeu o 50/50 anterior)
        self.assertTrue(char_banner.is_guaranteed)
        # Total de tiros no banner
        self.assertEqual(char_banner.total_pulls, 105)
        # 1 personagem 5★ obtido com pity 75
        self.assertEqual(char_banner.five_stars_count, 1)
        self.assertEqual(char_banner.recent_five_stars[0].name, "Bailu")
        self.assertEqual(char_banner.recent_five_stars[0].pity, 75)
        self.assertFalse(char_banner.recent_five_stars[0].is_win_5050)
        # Faltam 44 para soft pity (74 - 30) e 60 para hard pity (90 - 30)
        self.assertEqual(char_banner.next_soft_pity_in, 44)
        self.assertEqual(char_banner.pulls_to_hard_pity, 60)

    def test_guaranteed_consumed_on_rate_up(self):
        """Valida que tirar o personagem do banner consome o garantido e volta para 50/50."""
        pulls = [
            # Tiro 10: Bailu (Perdeu 50/50 -> Garantido = True)
            {
                "id": "p1",
                "name": "Bailu",
                "rarity": 5,
                "time": "2026-01-01 10:00:00",
                "gacha_type": "11",
                "banner_category": "character",
            },
            # Tiro 20: Acheron (Limitada -> Consumiu o garantido -> Garantido = False)
            {
                "id": "p2",
                "name": "Acheron",
                "rarity": 5,
                "time": "2026-01-01 10:10:00",
                "gacha_type": "11",
                "banner_category": "character",
            },
            # Mais 5 tiros
            {
                "id": "p3",
                "name": "Arma",
                "rarity": 3,
                "time": "2026-01-01 10:15:00",
                "gacha_type": "11",
                "banner_category": "character",
            },
        ]
        database.save_gacha_pulls("hsr", "700888", pulls)

        stats = calculate_gacha_tracker_stats("hsr", uid="700888")
        char_banner = stats.character_banner

        self.assertEqual(char_banner.current_pity, 1)
        # Garantido foi consumido na Acheron, agora volta para 50/50!
        self.assertFalse(char_banner.is_guaranteed)
        self.assertEqual(char_banner.five_stars_count, 2)

    def test_import_and_export_uigf(self):
        """Valida importação de arquivo UIGF e exportação compatível com o padrão universal."""
        uigf_data = {
            "info": {"uid": "800123456", "lang": "pt-br", "uigf_version": "v2.4"},
            "list": [
                {
                    "id": "1001",
                    "time": "2026-01-05 12:00:00",
                    "name": "Furina",
                    "item_type": "Personagem",
                    "rank_type": "5",
                    "gacha_type": "301",
                },
                {
                    "id": "1002",
                    "time": "2026-01-05 12:01:00",
                    "name": "Espada de Madeira",
                    "item_type": "Arma",
                    "rank_type": "3",
                    "gacha_type": "301",
                },
            ],
        }

        # Importa
        res_import = import_gacha_log_data("genshin", uigf_data)
        self.assertTrue(res_import.success)
        self.assertEqual(res_import.total_imported, 2)
        self.assertEqual(res_import.uid, "800123456")

        # Exporta
        exported = export_gacha_log_uigf("genshin", uid="800123456")
        self.assertIn("info", exported)
        self.assertEqual(exported["info"]["uigf_version"], "v2.4")
        self.assertEqual(exported["info"]["uid"], "800123456")
        self.assertEqual(len(exported["list"]), 2)
        self.assertEqual(exported["list"][0]["name"], "Furina")

    def test_api_tracker_endpoints(self):
        """Valida requisições HTTP aos endpoints GET, POST import, GET export e DELETE."""
        database.save_game_account("700777", "hsr", "Desbravador Teste", level=70)
        database.set_active_account("hsr", "700777")

        # 1. POST import
        payload = {
            "uid": "700777",
            "pulls_list": [
                {"id": "api_p1", "name": "Robin", "rarity": 5, "time": "2026-01-10 10:00:00", "gacha_type": "11"}
            ],
        }
        res_post = self.client.post("/api/gacha/tracker/import/hsr", json=payload)
        self.assertEqual(res_post.status_code, 200)
        self.assertTrue(res_post.json()["success"])

        # 2. GET overview
        res_get = self.client.get("/api/gacha/tracker/hsr?uid=700777")
        self.assertEqual(res_get.status_code, 200)
        overview = res_get.json()
        self.assertEqual(overview["uid"], "700777")
        self.assertEqual(overview["character_banner"]["five_stars_count"], 1)

        # 3. GET export
        res_export = self.client.get("/api/gacha/tracker/export/hsr?uid=700777")
        self.assertEqual(res_export.status_code, 200)
        exp_data = res_export.json()
        self.assertEqual(len(exp_data["list"]), 1)

        # 4. DELETE
        res_del = self.client.delete("/api/gacha/tracker/hsr?uid=700777")
        self.assertEqual(res_del.status_code, 200)
        self.assertEqual(res_del.json()["deleted_pulls"], 1)

        # Verifica limpeza
        res_after_del = self.client.get("/api/gacha/tracker/hsr?uid=700777")
        self.assertEqual(res_after_del.json()["character_banner"]["total_pulls"], 0)


if __name__ == "__main__":
    unittest.main()
