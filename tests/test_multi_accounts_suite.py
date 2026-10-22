import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from server import app
import database


class TestMultiAccountsSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        # Cria um banco SQLite temporário isolado para testes
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_path = self.temp_db_file.name
        self.temp_db_file.close()

        # Salva o caminho original do banco e redireciona
        self.orig_db_file = database.DATABASE_NAME
        database.DATABASE_NAME = self.temp_db_path
        database.init_db()

    def tearDown(self):
        # Restaura e remove banco temporário
        database.DATABASE_NAME = self.orig_db_file
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_set_and_get_active_account(self):
        """Valida gravação e recuperação do UID ativo por jogo."""
        self.assertIsNone(database.get_active_uid("hsr"))

        # Define HSR ativo como 700123456
        res = database.set_active_account("hsr", "700123456")
        self.assertTrue(res)
        self.assertEqual(database.get_active_uid("hsr"), "700123456")

        # Atualiza para outro UID
        database.set_active_account("hsr", "700999999")
        self.assertEqual(database.get_active_uid("hsr"), "700999999")

        # Outro jogo deve permanecer independente
        self.assertIsNone(database.get_active_uid("genshin"))
        database.set_active_account("genshin", "800111222")
        self.assertEqual(database.get_active_uid("genshin"), "800111222")
        self.assertEqual(database.get_active_uid("hsr"), "700999999")

    def test_get_active_accounts_map(self):
        """Valida que get_active_accounts_map retorna o dicionário completo."""
        database.set_active_account("hsr", "10001")
        database.set_active_account("zzz", "20002")

        active_map = database.get_active_accounts_map()
        self.assertEqual(active_map.get("hsr"), "10001")
        self.assertEqual(active_map.get("zzz"), "20002")
        self.assertNotIn("genshin", active_map)

    def test_get_all_saved_accounts_with_is_active_flag(self):
        """Valida que get_all_saved_accounts seta is_active=True na conta selecionada."""
        # Insere duas contas de HSR: save_game_account(uid, game_id, nickname, level, active_days)
        database.save_game_account("700000001", "hsr", "Desbravador 1", level=70, active_days=200)
        database.save_game_account("700000002", "hsr", "Desbravador Smurf", level=45, active_days=30)

        # Define a segunda conta como ativa
        database.set_active_account("hsr", "700000002")

        accounts = database.get_all_saved_accounts()
        self.assertEqual(len(accounts), 2)

        acc1 = next(a for a in accounts if a["uid"] == "700000001")
        acc2 = next(a for a in accounts if a["uid"] == "700000002")

        self.assertFalse(acc1["is_active"])
        self.assertTrue(acc2["is_active"])

    def test_get_roster_data_uid_isolation(self):
        """Garante que get_roster_data filtra personagens por UID sem misturar contas."""
        # Salva personagens para UID 111
        database.save_character(
            uid="111",
            game_id="hsr",
            name="Seele",
            level=80,
            rarity=5,
            rank_str="E0",
            element="Quantum",
            icon="/icons/seele.png",
            weapon_name="Na Noite",
            weapon_level=80,
            weapon_rank=1,
            weapon_icon="/icons/cone.png",
            raw_md="",
        )

        # Salva personagens para UID 222
        database.save_character(
            uid="222",
            game_id="hsr",
            name="Kafka",
            level=80,
            rarity=5,
            rank_str="E1",
            element="Lightning",
            icon="/icons/kafka.png",
            weapon_name="Paciência",
            weapon_level=80,
            weapon_rank=1,
            weapon_icon="/icons/cone2.png",
            raw_md="",
        )
        database.save_character(
            uid="222",
            game_id="hsr",
            name="Blade",
            level=80,
            rarity=5,
            rank_str="E0",
            element="Wind",
            icon="/icons/blade.png",
            weapon_name="Margem Inalcançável",
            weapon_level=80,
            weapon_rank=1,
            weapon_icon="/icons/cone3.png",
            raw_md="",
        )

        # Consulta com UID explícito
        roster_111 = database.get_roster_data("hsr", uid="111")
        roster_222 = database.get_roster_data("hsr", uid="222")

        self.assertEqual(len(roster_111), 1)
        self.assertEqual(roster_111[0]["name"], "Seele")

        self.assertEqual(len(roster_222), 2)
        names_222 = [c["name"] for c in roster_222]
        self.assertIn("Kafka", names_222)
        self.assertIn("Blade", names_222)

        # Consulta sem UID especificado, usando a conta ativa do SQLite
        database.set_active_account("hsr", "222")
        roster_active = database.get_roster_data("hsr")
        self.assertEqual(len(roster_active), 2)

        database.set_active_account("hsr", "111")
        roster_active_switched = database.get_roster_data("hsr")
        self.assertEqual(len(roster_active_switched), 1)
        self.assertEqual(roster_active_switched[0]["name"], "Seele")

    def test_delete_account_profile(self):
        """Valida remoção completa de um perfil e seus dados associados."""
        database.save_game_account("800999888", "genshin", "Viajante", level=60)
        database.set_active_account("genshin", "800999888")

        database.save_character(
            uid="800999888",
            game_id="genshin",
            name="Furina",
            level=90,
            rarity=5,
            rank_str="C2",
            element="Hydro",
            icon="/icons/furina.png",
            weapon_name="Esplendor das Águas",
            weapon_level=90,
            weapon_rank=1,
            weapon_icon="/icons/espada.png",
            raw_md="",
        )

        self.assertEqual(database.get_active_uid("genshin"), "800999888")
        self.assertEqual(len(database.get_roster_data("genshin", uid="800999888")), 1)

        # Deleta perfil
        deleted_count = database.delete_account_profile("800999888")
        self.assertGreater(deleted_count, 0)

        # Deve ter sido desativado e o roster zerado
        self.assertIsNone(database.get_active_uid("genshin"))
        self.assertEqual(len(database.get_roster_data("genshin", uid="800999888")), 0)
        self.assertEqual(len(database.get_all_saved_accounts()), 0)

    def test_api_accounts_endpoints(self):
        """Valida os endpoints REST: GET /api/accounts, POST /api/accounts/switch e DELETE /api/accounts/{uid}."""
        # 1. Popula banco
        database.save_game_account("7001", "hsr", "Conta Main", level=70)
        database.save_game_account("7002", "hsr", "Conta Alt", level=50)

        # 2. GET /api/accounts
        res = self.client.get("/api/accounts")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("accounts", data)
        self.assertIn("active_accounts", data)
        self.assertEqual(len(data["accounts"]), 2)

        # 3. POST /api/accounts/switch
        switch_res = self.client.post("/api/accounts/switch", json={"game_id": "hsr", "uid": "7002"})
        self.assertEqual(switch_res.status_code, 200)
        switch_data = switch_res.json()
        self.assertTrue(switch_data["success"])
        self.assertEqual(switch_data["active_uid"], "7002")

        # Verifica se o GET agora reflete a conta ativa
        res_after = self.client.get("/api/accounts")
        data_after = res_after.json()
        self.assertEqual(data_after["active_accounts"].get("hsr"), "7002")

        # 4. DELETE /api/accounts/{uid}
        del_res = self.client.delete("/api/accounts/7002")
        self.assertEqual(del_res.status_code, 200)
        del_data = del_res.json()
        self.assertTrue(del_data["success"])

        # Verifica se a lista foi reduzida
        res_final = self.client.get("/api/accounts")
        data_final = res_final.json()
        self.assertEqual(len(data_final["accounts"]), 1)
        self.assertEqual(data_final["accounts"][0]["uid"], "7001")


if __name__ == "__main__":
    unittest.main()
