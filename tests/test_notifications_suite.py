import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

import server
from notifications import NotificationService, notifier
import security_vault
import database

class TestNotificationSuite(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(server.app)
        self.service = NotificationService()

    def test_discord_webhook_formatting(self):
        with patch("curl_cffi.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 204
            mock_post.return_value = mock_resp

            res = self.service.send_discord_webhook(
                webhook_url="https://discord.com/api/webhooks/12345/abcdef",
                title="Teste Discord",
                description="Descrição de teste",
                color=0x10b981,
                fields=[{"name": "Campo 1", "value": "Valor 1", "inline": True}]
            )
            self.assertTrue(res["success"])
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            payload = kwargs["json"]
            self.assertEqual(payload["username"], "Cabeça de Droid (HoYoBot)")
            self.assertEqual(payload["embeds"][0]["title"], "Teste Discord")
            self.assertEqual(payload["embeds"][0]["color"], 0x10b981)

    def test_telegram_message_formatting(self):
        with patch("curl_cffi.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = '{"ok": true}'
            mock_resp.json.return_value = {"ok": True}
            mock_post.return_value = mock_resp

            res = self.service.send_telegram_message(
                bot_token="123456:TEST_TOKEN",
                chat_id="987654321",
                text="<b>Mensagem de Teste</b>"
            )
            self.assertTrue(res["success"])
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertIn("123456:TEST_TOKEN", args[0])
            self.assertEqual(kwargs["json"]["chat_id"], "987654321")

    def test_energy_alert_and_anti_spam(self):
        mock_notes = {
            "hsr": {
                "uid": "700123456",
                "current_energy": 225,
                "max_energy": 240,
                "recovery_time": "1h 30m"
            }
        }
        mock_config = {
            "notifications_enabled": True,
            "notify_on_energy_cap": True,
            "energy_cap_threshold_pct": 90,
            "discord_webhook_url": "https://discord.com/api/webhooks/123/abc"
        }

        with patch.object(self.service, "send_notification") as mock_send:
            # 1. Primeiro disparo: 225/240 = 93.75% -> Deve enviar notificação
            self.service.check_energy_and_alert(mock_notes, mock_config)
            mock_send.assert_called_once()
            self.assertTrue(self.service._energy_alert_tracker.get("hsr_700123456"))

            # 2. Segundo disparo no mesmo ciclo (ainda cheio): Não deve enviar spam repetido
            mock_send.reset_mock()
            self.service.check_energy_and_alert(mock_notes, mock_config)
            mock_send.assert_not_called()

            # 3. Usuário gastou energia (caiu para 120/240 = 50%): Reseta a trava
            mock_notes["hsr"]["current_energy"] = 120
            self.service.check_energy_and_alert(mock_notes, mock_config)
            self.assertFalse(self.service._energy_alert_tracker.get("hsr_700123456"))

            # 4. Encheu novamente (230/240 = 95.8%): Deve alertar novamente no novo ciclo
            mock_notes["hsr"]["current_energy"] = 230
            self.service.check_energy_and_alert(mock_notes, mock_config)
            mock_send.assert_called_once()

    def test_api_config_endpoints(self):
        # 1. Test GET /api/config
        get_res = self.client.get("/api/config")
        self.assertEqual(get_res.status_code, 200)
        data = get_res.json()
        self.assertIn("notifications_enabled", data)
        self.assertIn("discord_webhook_url", data)
        self.assertIn("energy_cap_threshold_pct", data)

        # 2. Test POST /api/config
        post_payload = {
            "notifications_enabled": True,
            "discord_webhook_url": "https://discord.com/api/webhooks/test/mock",
            "telegram_bot_token": "123456:BOT_TOKEN",
            "telegram_chat_id": "999888777",
            "notify_on_checkin": True,
            "notify_on_energy_cap": True,
            "energy_cap_threshold_pct": 95
        }
        save_res = self.client.post("/api/config", json=post_payload)
        self.assertEqual(save_res.status_code, 200)
        self.assertEqual(save_res.json()["status"], "success")

        # 3. Verify GET returns updated configuration with masked Telegram token
        get_res2 = self.client.get("/api/config")
        data2 = get_res2.json()
        self.assertTrue(data2["notifications_enabled"])
        self.assertEqual(data2["discord_webhook_url"], "https://discord.com/api/webhooks/test/mock")
        self.assertEqual(data2["telegram_chat_id"], "999888777")
        self.assertEqual(data2["energy_cap_threshold_pct"], 95)
        self.assertTrue(data2["telegram_bot_token"].startswith("1234***") or "***" in data2["telegram_bot_token"])

    def test_api_notifications_test_endpoint(self):
        with patch.object(notifier, "test_channels") as mock_test_channels:
            mock_test_channels.return_value = {
                "discord": {"attempted": True, "success": True, "message": "OK"},
                "telegram": {"attempted": True, "success": True, "message": "OK"}
            }

            resp = self.client.post("/api/notifications/test", json={
                "discord_webhook_url": "https://discord.com/api/webhooks/999/test",
                "telegram_bot_token": "123456:TEST",
                "telegram_chat_id": "111222333"
            })
            self.assertEqual(resp.status_code, 200)
            res_data = resp.json()
            self.assertEqual(res_data["status"], "success")
            self.assertTrue(res_data["results"]["discord"]["success"])
            self.assertTrue(res_data["results"]["telegram"]["success"])

if __name__ == "__main__":
    unittest.main()
