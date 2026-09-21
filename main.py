import os
import sys
import time
import threading
import subprocess
import webbrowser
import uvicorn

def setup_playwright() -> None:
    """
    Garante que o executável Chromium do Playwright esteja disponível no ambiente do usuário.
    Se estiver rodando empacotado via PyInstaller, força a busca na pasta AppData/Local padrão.
    """
    local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    pw_path = os.path.join(local_app_data, "ms-playwright")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = pw_path

    has_browser = False
    if os.path.exists(pw_path):
        for f in os.listdir(pw_path):
            if f.startswith("chromium-"):
                has_browser = True
                break

    if not has_browser:
        try:
            from playwright._impl._driver import compute_driver_executable, get_driver_env
            driver_executable, driver_cli = compute_driver_executable()
            env = get_driver_env()
            env["PLAYWRIGHT_BROWSERS_PATH"] = pw_path
            
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW
                
            subprocess.run(
                [driver_executable, driver_cli, "install", "chromium"], 
                env=env,
                creationflags=creationflags,
                check=False
            )
        except Exception as e:
            print(f"[WARN] Não foi possível verificar/instalar o Chromium do Playwright automaticamente: {e}")

setup_playwright()

from server import app

import socket

def get_local_ip() -> str:
    """Obtém o IP local da máquina na rede Wi-Fi/Ethernet."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_available_port(start_port: int = 8000, max_attempts: int = 20) -> int:
    """Encontra uma porta TCP disponível a partir da porta inicial informada."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return start_port

def wait_for_server(port: int, timeout: float = 10.0) -> bool:
    """Realiza polling ativamente até a API aceitar conexões TCP na porta especificada."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    return True
        except Exception:
            pass
        time.sleep(0.1)
    return False

import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Cabeça de Droid - Assistente HoYoLAB")
    parser.add_argument("--host", "-H", type=str, default=None, help="Endereço IP para bind do servidor (ex: 0.0.0.0 ou 127.0.0.1)")
    parser.add_argument("--port", "-p", type=int, default=None, help="Porta TCP do servidor (padrão: 8000)")
    parser.add_argument("--lan", "--allow-lan", "--tailscale", action="store_true", help="Permite acesso via rede local (LAN), Tailscale ou VPN")
    parser.add_argument("--no-browser", action="store_true", help="Não abre a janela do navegador automaticamente (ideal para servidores Linux/VMs)")
    return parser.parse_args()

def start_server(host: str, port: int) -> None:
    """Inicia o servidor web FastAPI usando Uvicorn com binding configurado."""
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    server.run()

def main() -> None:
    """
    Ponto de entrada unificado da aplicação.
    Inicializa o servidor FastAPI e abre a interface gráfica no navegador.
    """
    args = parse_args()
    from database import is_lan_access_allowed, set_lan_access

    if args.lan:
        os.environ["ALLOW_LAN"] = "1"
        try:
            set_lan_access(True)
        except Exception:
            pass

    allow_lan = is_lan_access_allowed() or args.lan or os.environ.get("ALLOW_LAN", "").lower() in ("1", "true", "yes", "on")

    # Define o host de binding
    if args.host:
        bind_host = args.host
        if bind_host in ("0.0.0.0", "::"):
            os.environ["ALLOW_LAN"] = "1"
            allow_lan = True
    elif os.environ.get("HOST"):
        bind_host = os.environ["HOST"]
        if bind_host in ("0.0.0.0", "::"):
            os.environ["ALLOW_LAN"] = "1"
            allow_lan = True
    else:
        bind_host = "0.0.0.0" if allow_lan else "127.0.0.1"

    # Define a porta
    if args.port:
        port = args.port
    elif os.environ.get("PORT"):
        port = int(os.environ["PORT"])
    else:
        port = find_available_port(8000)
    
    server_thread = threading.Thread(target=start_server, args=(bind_host, port), daemon=True)
    server_thread.start()
    
    # Aguarda ativamente o servidor responder no socket antes de prosseguir
    ready = wait_for_server(port)
    
    local_ip = get_local_ip()
    url_local = f"http://127.0.0.1:{port}/?v=4.0"
    url_rede = f"http://{local_ip}:{port}/?v=4.0"
    
    print("[INFO] Iniciando Cabeça de Droid v4.0 (Blindagem de Segurança Ativa)...")
    print(f"[INFO] Servidor escutando em: {bind_host}:{port}")
    print(f"[INFO] Acesso local: {url_local}")
    if allow_lan or bind_host == "0.0.0.0":
        print(f"[SUCCESS] Acesso LAN / Tailscale / VPN HABILITADO na porta {port} (IP local: {local_ip})")
    else:
        print(f"[SECURITY] Isolamento de Rede Ativo: Servidor vinculado exclusivamente a 127.0.0.1 (Loopback).")
        print(f"[TIP] Para liberar o acesso via Tailscale/VPN na VM, inicie com: python main.py --lan (ou --host 0.0.0.0)")
    
    should_open_browser = not args.no_browser and (sys.platform == "win32" or bool(os.environ.get("DISPLAY")))
    if ready and should_open_browser:
        try:
            webbrowser.open(url_local)
        except Exception:
            pass

    try:
        while server_thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[INFO] Servidor encerrado com sucesso pelo usuário.")

if __name__ == "__main__":
    main()
