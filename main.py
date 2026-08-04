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

def start_server() -> None:
    """Inicia o servidor web FastAPI usando Uvicorn."""
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

def main() -> None:
    """
    Ponto de entrada unificado da aplicação.
    Inicializa o servidor FastAPI e abre a interface gráfica no navegador.
    """
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Aguarda o servidor aceitar conexões antes de abrir a aba no navegador
    time.sleep(3.5)
    
    local_ip = get_local_ip()
    print("[INFO] Iniciando Cabeça de Droid v4.0...")
    print(f"[INFO] Servidor rodando localmente em: http://127.0.0.1:8000/?v=4.0")
    print(f"[INFO] Para acessar pelo celular ou outro dispositivo na mesma rede Wi-Fi, acesse: http://{local_ip}:8000/?v=4.0")
    webbrowser.open("http://127.0.0.1:8000/?v=4.0")

    
    try:
        while server_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Servidor encerrado com sucesso pelo usuário.")

if __name__ == "__main__":
    main()
