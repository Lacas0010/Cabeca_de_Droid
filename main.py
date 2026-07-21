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

setup_playwright()

from gui import App

def main():
    """
    Função principal que atua como ponto de entrada da aplicação.
    Instancia a classe App do módulo gui e inicia o loop principal da interface.
    """
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
