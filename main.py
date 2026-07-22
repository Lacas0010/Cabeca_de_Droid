import os
import sys
import subprocess

def setup_playwright():
    # Se estiver rodando compilado pelo PyInstaller, o Playwright tenta buscar o 
    # navegador na pasta temporária extraída (_MEIPASS). Como não embutimos os 200MB+ 
    # do Chromium no .exe, forçamos o Playwright a usar a pasta padrão do usuário.
    local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
    pw_path = os.path.join(local_app_data, "ms-playwright")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = pw_path

    # Verifica se já existe um chromium baixado lá
    has_browser = False
    if os.path.exists(pw_path):
        for f in os.listdir(pw_path):
            if f.startswith("chromium-"):
                has_browser = True
                break

    # Se não houver navegador, vamos invocar silenciosamente o CLI nativo do Playwright para instalar
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
                creationflags=creationflags
            )
        except Exception as e:
            pass # Falha silenciosa, o usuário verá erro no login depois

import threading
import time
import webbrowser
import uvicorn

setup_playwright()

from server import app

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

def main():
    """
    Função principal que atua como ponto de entrada da aplicação.
    Inicia o servidor FastAPI local e abre o navegador padrão do sistema.
    """
    # Cria a thread do uvicorn
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Espera o servidor iniciar
    time.sleep(3.5)
    
    # Abre o navegador padrão na porta 8000
    print("[INFO] Iniciando Cabeça de Droid...")
    print("[INFO] Abrindo navegador em: http://127.0.0.1:8000")
    webbrowser.open("http://127.0.0.1:8000")
    
    # Mantém a thread principal ativa
    try:
        while server_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Servidor local encerrado pelo usuário.")

if __name__ == "__main__":
    main()
