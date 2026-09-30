import sys
import os
import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

import server
import database
from notifications import notifier

class TestAutoRedeemSuite(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(server.app)
        database.init_db()
        with database.get_connection() as conn:
            conn.execute("DELETE FROM promo_code_history WHERE code LIKE 'AUTO%' OR code LIKE 'TEST%' OR code LIKE 'STARRAIL%' OR code LIKE 'EXPIRED%' OR code LIKE 'MANUAL%'")

    def test_database_code_redemptions(self):
        # 1. Salva resgates de teste
        database.save_code_redemption("hsr", "700111222", "STARRAILGIFT", "success", "Código STARRAILGIFT resgatado com sucesso!")
        database.save_code_redemption("hsr", "700111222", "EXPIREDCODE", "invalid", "Código expirado.")

        # 2. Verifica deduplicação (get_redeemed_codes)
        redeemed = database.get_redeemed_codes("hsr", "700111222")
        self.assertIn("STARRAILGIFT", redeemed)
        self.assertIn("EXPIREDCODE", redeemed)
        self.assertNotIn("NEWCODE123", redeemed)

        # 3. Verifica histórico
        history = database.get_code_redemption_history("hsr")
        self.assertTrue(len(history) >= 2)
        codes_in_history = [h["code"] for h in history]
        self.assertIn("STARRAILGIFT", codes_in_history)

    def test_perform_auto_promo_code_redeem(self):
        mock_accounts = [
            MagicMock(game_biz="hkrpg_global", uid=700999888, nickname="Trailblazer")
        ]
        mock_active_codes = [
            {"code": "AUTOTEST1", "rewards": "100 Stellar Jade", "status": "Ativo"},
            {"code": "AUTOTEST2", "rewards": "50 Stellar Jade", "status": "Ativo"}
        ]

        with patch("server.get_cookies", return_value={"ltuid_v2": "123", "ltoken_v2": "abc"}), \
             patch("genshin.Client.get_game_accounts", new_callable=AsyncMock, return_value=mock_accounts), \
             patch("build_calculator.fetch_active_promo_codes", return_value=mock_active_codes), \
             patch("extractor.redeem_promo_code", new_callable=AsyncMock) as mock_redeem, \
             patch.object(notifier, "notify_promo_codes") as mock_notify, \
             patch("asyncio.sleep", new_callable=AsyncMock):

            mock_redeem.side_effect = [
                {"code": "AUTOTEST1", "status": "success", "message": "Resgatado com sucesso!"},
                {"code": "AUTOTEST2", "status": "claimed", "message": "Já resgatado."}
            ]

            # Executa a rotina assíncrona
            res = asyncio.run(server.perform_auto_promo_code_redeem())
            self.assertEqual(res["status"], "success")
            self.assertIn("hsr", res["redeemed"])
            self.assertEqual(len(res["redeemed"]["hsr"]), 1)
            self.assertEqual(res["redeemed"]["hsr"][0]["code"], "AUTOTEST1")

            # Verifica que a notificação foi disparada
            mock_notify.assert_called_once()

            # Segunda execução: Como ambos já estão gravados no banco, não deve tentar resgatar nada
            mock_redeem.reset_mock()
            mock_notify.reset_mock()

            res2 = asyncio.run(server.perform_auto_promo_code_redeem())
            self.assertEqual(res2["status"], "success")
            self.assertEqual(res2["redeemed"], {})
            mock_redeem.assert_not_called()
            mock_notify.assert_not_called()

    def test_codes_rest_endpoints(self):
        # 1. GET /api/codes/hsr
        with patch("build_calculator.fetch_active_promo_codes", return_value=[{"code": "TESTCODE", "rewards": "60 Primogems", "status": "Ativo"}]):
            res = self.client.get("/api/codes/hsr")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["game_id"], "hsr")
            self.assertEqual(len(data["codes"]), 1)

        # 2. GET /api/codes/history/hsr
        res_hist = self.client.get("/api/codes/history/hsr")
        self.assertEqual(res_hist.status_code, 200)
        hist_data = res_hist.json()
        self.assertIn("history", hist_data)

        # 3. POST /api/codes/redeem
        with patch("server.get_cookies", return_value={"ltuid_v2": "123", "ltoken_v2": "abc"}), \
             patch("genshin.Client.get_game_accounts", new_callable=AsyncMock, return_value=[]), \
             patch("extractor.redeem_promo_code", new_callable=AsyncMock, return_value={"code": "MANUALTEST", "status": "success", "message": "Resgatado!"}), \
             patch("asyncio.sleep", new_callable=AsyncMock):

            redeem_res = self.client.post("/api/codes/redeem", json={"game_id": "hsr", "code": "MANUALTEST"})
            self.assertEqual(redeem_res.status_code, 200)
            self.assertEqual(redeem_res.json()["results"][0]["status"], "success")

            # Confirma que foi gravado no histórico
            redeemed_set = database.get_redeemed_codes("hsr", "default")
            self.assertIn("MANUALTEST", redeemed_set)

if __name__ == "__main__":
    unittest.main()
