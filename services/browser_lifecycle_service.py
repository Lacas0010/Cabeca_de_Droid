import threading
import time
from typing import Any, Callable, Dict, Optional


class BrowserLifecycleManager:
    """
    Gerencia o ciclo de vida das abas/janelas locais do navegador no modo desktop.
    Quando habilitado, encerra automaticamente o servidor caso todas as abas locais
    sejam fechadas (com tolerância de alguns segundos para recarregamentos via F5).
    Permanece desativado em servidores headless (--no-browser), como a VM Oracle.
    """

    def __init__(
        self,
        disconnect_grace_sec: float = 4.0,
        heartbeat_timeout_sec: Optional[float] = None,
    ):
        self.disconnect_grace_sec = disconnect_grace_sec
        self.heartbeat_timeout_sec = heartbeat_timeout_sec
        self._lock = threading.Lock()
        self.enabled: bool = False
        self.has_seen_client: bool = False
        self.active_clients: Dict[str, float] = {}
        self._on_shutdown: Optional[Callable[[], None]] = None
        self._pending_timer: Optional[threading.Timer] = None
        self._reaper_stop = threading.Event()
        self._reaper_thread: Optional[threading.Thread] = None

    def configure(self, enabled: bool, on_shutdown: Optional[Callable[[], None]] = None) -> None:
        """Ativa ou desativa o encerramento automático ao fechar o navegador."""
        with self._lock:
            self.enabled = bool(enabled)
            self._on_shutdown = on_shutdown
            self._cancel_pending_timer_locked()

            timeout_enabled = (
                self.heartbeat_timeout_sec is not None and self.heartbeat_timeout_sec > 0
            )
            if (
                self.enabled
                and timeout_enabled
                and (self._reaper_thread is None or not self._reaper_thread.is_alive())
            ):
                self._reaper_stop.clear()
                self._reaper_thread = threading.Thread(target=self._reaper_loop, daemon=True)
                self._reaper_thread.start()

    def _cancel_pending_timer_locked(self) -> None:
        if self._pending_timer is not None:
            self._pending_timer.cancel()
            self._pending_timer = None

    def _schedule_shutdown_locked(self) -> None:
        self._cancel_pending_timer_locked()
        timer = threading.Timer(self.disconnect_grace_sec, self._trigger_shutdown_if_empty)
        timer.daemon = True
        self._pending_timer = timer
        timer.start()

    def _trigger_shutdown_if_empty(self) -> None:
        callback = None
        with self._lock:
            self._pending_timer = None
            if self.enabled and self.has_seen_client and not self.active_clients:
                callback = self._on_shutdown
        if callback is not None:
            print("[INFO] Todas as janelas do navegador foram fechadas. Encerrando servidor...")
            callback()

    def register_heartbeat(self, client_id: str, is_loopback: bool = True) -> Dict[str, Any]:
        """Registra um sinal de vida da aba local e cancela desligamentos pendentes (ex: F5)."""
        with self._lock:
            if not self.enabled or not is_loopback:
                return {"watchdog": False, "active_clients": len(self.active_clients)}

            self.active_clients[client_id] = time.monotonic()
            self.has_seen_client = True
            self._cancel_pending_timer_locked()
            return {"watchdog": True, "active_clients": len(self.active_clients)}

    def register_disconnect(self, client_id: str, is_loopback: bool = True) -> Dict[str, Any]:
        """Remove a aba desconectada e agenda o encerramento se nenhuma outra restar aberta."""
        with self._lock:
            if not self.enabled or not is_loopback:
                return {"watchdog": False, "active_clients": len(self.active_clients), "shutdown_scheduled": False}

            self.active_clients.pop(client_id, None)
            shutdown_scheduled = False
            if self.has_seen_client and not self.active_clients:
                self._schedule_shutdown_locked()
                shutdown_scheduled = True

            return {
                "watchdog": True,
                "active_clients": len(self.active_clients),
                "shutdown_scheduled": shutdown_scheduled,
            }

    def check_stale_clients(self, now: Optional[float] = None) -> bool:
        """
        Expira clientes apenas se `heartbeat_timeout_sec` estiver explicitamente
        configurado (> 0). Por padrão permanece desativado para que abas em
        segundo plano ou fora de foco (onde navegadores congelam timers) não
        encerrem o servidor antes de o usuário fechar a aba.
        """
        if self.heartbeat_timeout_sec is None or self.heartbeat_timeout_sec <= 0:
            return False

        callback = None
        current = time.monotonic() if now is None else now
        with self._lock:
            if not self.enabled or not self.has_seen_client:
                return False

            stale_ids = [
                cid for cid, last_seen in self.active_clients.items() if current - last_seen > self.heartbeat_timeout_sec
            ]
            for cid in stale_ids:
                del self.active_clients[cid]

            if not self.active_clients and self._pending_timer is None:
                callback = self._on_shutdown

        if callback is not None:
            print("[INFO] Nenhum navegador ativo detectado (timeout de heartbeat). Encerrando servidor...")
            callback()
            return True
        return False

    def _reaper_loop(self) -> None:
        while not self._reaper_stop.wait(5.0):
            if not self.enabled:
                break
            self.check_stale_clients()

    def shutdown(self) -> None:
        """Limpa temporizadores e interrompe a thread de monitoramento."""
        self._reaper_stop.set()
        with self._lock:
            self._cancel_pending_timer_locked()


browser_lifecycle_manager = BrowserLifecycleManager()
