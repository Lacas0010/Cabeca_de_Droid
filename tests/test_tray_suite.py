import unittest
from unittest.mock import patch, MagicMock
from PIL import Image

from core.tray import SystemTrayManager


class TestSystemTraySuite(unittest.TestCase):
    def setUp(self):
        self.stop_called = False

        def on_stop():
            self.stop_called = True

        self.tray = SystemTrayManager(port=8000, host="127.0.0.1", on_stop=on_stop)

    def test_get_icon_image_fallback_and_existing(self):
        """Garante que a imagem do ícone é retornada como um objeto Image do Pillow."""
        img = self.tray._get_icon_image()
        self.assertIsInstance(img, Image.Image)
        self.assertGreater(img.size[0], 0)
        self.assertGreater(img.size[1], 0)

    @patch("core.tray.get_resource_path")
    def test_get_icon_image_procedural_fallback(self, mock_path):
        """Valida que quando o arquivo .ico não existe, o fallback procedural é gerado."""
        mock_path.return_value = "/caminho/inexistente/icone.ico"
        img = self.tray._get_icon_image()
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (64, 64))

    def test_build_menu_structure(self):
        """Garante que o menu de contexto é construído com os itens esperados."""
        menu = self.tray.build_menu()
        self.assertIsNotNone(menu)
        items = list(menu.items)
        labels = [str(item.text) for item in items if hasattr(item, "text")]

        self.assertTrue(any("Dashboard" in l for l in labels))
        self.assertTrue(any("Sincronizar" in l for l in labels))
        self.assertTrue(any("Notificações" in l for l in labels))
        self.assertTrue(any("Encerrar" in l for l in labels))

    @patch("core.tray.webbrowser.open")
    def test_on_open_dashboard(self, mock_open):
        """Testa o disparo do navegador com a URL do dashboard."""
        self.tray._on_open_dashboard(None, None)
        mock_open.assert_called_once_with("http://127.0.0.1:8000/")

    @patch("core.tray.security_vault.save_secure_config")
    @patch("core.tray.get_config")
    def test_on_toggle_notifications(self, mock_get_cfg, mock_save_cfg):
        """Testa a alternância do status de notificações na bandeja."""
        mock_get_cfg.return_value = {"notifications_enabled": True}
        self.tray._on_toggle_notifications(None, None)

        mock_save_cfg.assert_called_once()
        saved_cfg = mock_save_cfg.call_args[0][0]
        self.assertFalse(saved_cfg["notifications_enabled"])

    def test_on_stop_callback(self):
        """Valida que o método stop chama o callback de parada da aplicação."""
        self.assertFalse(self.stop_called)
        self.tray.stop()
        self.assertTrue(self.stop_called)

    @patch("core.tray.sys")
    @patch("core.tray.os")
    def test_is_gui_supported_headless(self, mock_os, mock_sys):
        """Verifica que sistemas sem display gráfico são identificados como headless."""
        mock_sys.platform = "linux"
        mock_os.environ = {}
        self.assertFalse(self.tray.is_gui_supported())

    @patch.object(SystemTrayManager, "is_gui_supported", return_value=False)
    def test_start_headless_graceful(self, mock_gui):
        """Garante que start() retorna False graciosamente em ambiente headless sem lançar erro."""
        started = self.tray.start()
        self.assertFalse(started)
        self.assertFalse(self.tray._is_running)


if __name__ == "__main__":
    unittest.main()
