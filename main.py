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

def start_server() -> None:
    """Inicia o servidor web FastAPI usando Uvicorn."""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

def main() -> None:
    """
    Ponto de entrada unificado da aplicação.
    Inicializa o servidor FastAPI local e abre a interface gráfica no navegador.
    """
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Aguarda o servidor aceitar conexões antes de abrir a aba no navegador
    time.sleep(3.5)
    
    print("[INFO] Iniciando Cabeça de Droid...")
    print("[INFO] Servidor rodando em: http://127.0.0.1:8000")
    webbrowser.open("http://127.0.0.1:8000")
    
    try:
        while server_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Servidor encerrado com sucesso pelo usuário.")

if __name__ == "__main__":
    main()
