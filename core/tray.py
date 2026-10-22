import os
import sys
import threading
import webbrowser
import subprocess
from typing import Optional, Callable
from PIL import Image, ImageDraw

from core.config import get_resource_path, get_config
import security_vault


class SystemTrayManager:
    """
    Gerenciador do Ícone na Bandeja do Sistema (Windows System Tray)
    Permite executar o Cabeça de Droid minimizado em segundo plano com menu interativo.
    """

    def __init__(self, port: int = 8000, host: str = "127.0.0.1", on_stop: Optional[Callable[[], None]] = None):
        self.port = port
        self.host = host
        self.on_stop = on_stop
        self.dashboard_url = f"http://127.0.0.1:{port}/"
        self._icon = None
        self._is_running = False

    def is_gui_supported(self) -> bool:
        """Verifica se o ambiente atual possui suporte a interface gráfica de bandeja."""
        if sys.platform == "win32":
            return True
        # Em Linux/macOS, exige a variável de ambiente DISPLAY ou WAYLAND_DISPLAY
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))

    def _get_icon_image(self) -> Image.Image:
        """Carrega o ícone oficial .ico do projeto ou cria um fallback elegante via Pillow."""
        ico_path = get_resource_path("assets/logo.ico")
        if os.path.exists(ico_path):
            try:
                with Image.open(ico_path) as img:
                    return img.copy()
            except Exception as e:
                print(f"[WARN] Falha ao carregar logo.ico para a bandeja: {e}")

        # Fallback gerado proceduralmente: círculo ciano/azul escuro moderno com letra 'D'
        size = (64, 64)
        image = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        # Fundo circular
        draw.ellipse([2, 2, 62, 62], fill=(15, 23, 42, 255), outline=(56, 189, 248, 255), width=3)
        # Núcleo brilhante
        draw.ellipse([18, 18, 46, 46], fill=(56, 189, 248, 255))
        return image

    def _on_open_dashboard(self, icon, item):
        """Ação: Abrir o dashboard no navegador padrão."""
        try:
            webbrowser.open(self.dashboard_url)
        except Exception as e:
            print(f"[WARN] Erro ao abrir dashboard a partir da bandeja: {e}")

    def _on_copy_url(self, icon, item):
        """Ação: Copiar URL local para a área de transferência."""
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", f"Set-Clipboard -Value '{self.dashboard_url}'"],
                    check=False,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
        except Exception as e:
            print(f"[WARN] Erro ao copiar URL: {e}")

    def _on_toggle_notifications(self, icon, item):
        """Ação: Alternar notificações ativas / horário de silêncio."""
        try:
            cfg = get_config()
            current_state = cfg.get("notifications_enabled", True)
            new_state = not current_state
            cfg["notifications_enabled"] = new_state
            security_vault.save_secure_config(cfg)
        except Exception as e:
            print(f"[WARN] Erro ao alternar notificações: {e}")

    def _is_notifications_enabled(self, item) -> bool:
        """Verifica se as notificações estão habilitadas para marcar o menu."""
        try:
            cfg = get_config()
            return cfg.get("notifications_enabled", True)
        except Exception:
            return True

    def _on_trigger_sync(self, icon, item):
        """Ação: Disparar sincronização em segundo plano."""
        try:
            from services.sync_service import _bg_sync_thread

            threading.Thread(target=_bg_sync_thread, args=("hsr", True, False, False), daemon=True).start()
        except Exception as e:
            print(f"[WARN] Erro ao disparar sincronização da bandeja: {e}")

    def _on_exit(self, icon, item):
        """Ação: Encerrar a aplicação de forma limpa."""
        self.stop()

    def build_menu(self):
        """Constrói a estrutura do menu de contexto com pystray."""
        import pystray

        return pystray.Menu(
            pystray.MenuItem("Cabeça de Droid (Dashboard)", self._on_open_dashboard, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Sincronizar Roster Agora", self._on_trigger_sync),
            pystray.MenuItem(
                "Notificações Ativas", self._on_toggle_notifications, checked=self._is_notifications_enabled
            ),
            pystray.MenuItem("Copiar Link do Painel", self._on_copy_url),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Encerrar Servidor", self._on_exit),
        )

    def start(self) -> bool:
        """
        Inicia o ícone na bandeja em modo não bloqueante (run_detached).
        Retorna True se inicializado com sucesso ou False caso o ambiente seja headless.
        """
        if not self.is_gui_supported():
            print("[INFO] Ambiente sem interface gráfica/headless detectado. Ícone de bandeja desativado.")
            return False

        try:
            import pystray

            image = self._get_icon_image()
            menu = self.build_menu()

            self._icon = pystray.Icon(
                name="cabeca_de_droid", icon=image, title=f"Cabeça de Droid (Porta {self.port})", menu=menu
            )

            self._icon.run_detached()
            self._is_running = True
            print("[INFO] Ícone na bandeja do sistema inicializado com sucesso.")
            return True
        except Exception as e:
            print(f"[INFO] Modo headless ou sem suporte a pystray: {e}. Execução prossegue normalmente.")
            return False

    def stop(self):
        """Interrompe o ícone da bandeja e notifica o callback de encerramento."""
        self._is_running = False
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None

        if self.on_stop and callable(self.on_stop):
            try:
                self.on_stop()
            except Exception:
                pass
