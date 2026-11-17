import os
import sys
import asyncio
import subprocess
from typing import Dict
from playwright.async_api import async_playwright, Browser, Playwright, Error as PlaywrightError


def _install_playwright_chromium_sync() -> None:
    """Baixa o binário Chromium gerenciado pelo Playwright caso nenhum navegador compatível esteja disponível."""
    from playwright._impl._driver import compute_driver_executable, get_driver_env

    driver_executable, driver_cli = compute_driver_executable()
    env = get_driver_env()
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
        env.setdefault("PLAYWRIGHT_BROWSERS_PATH", os.path.join(local_app_data, "ms-playwright"))

    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
    proc = subprocess.run(
        [driver_executable, driver_cli, "install", "chromium"],
        env=env,
        creationflags=creationflags,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Falha ao instalar Chromium do Playwright (código {proc.returncode}).")


async def _launch_login_browser(p: Playwright) -> Browser:
    """
    Inicia um navegador Chromium em modo visível com fallback resiliente para builds empacotadas:
    1. Chromium gerenciado pelo Playwright (se já presente no disco);
    2. Google Chrome ou Microsoft Edge instalados no sistema (instantâneo no Windows);
    3. Download sob demanda do Chromium do Playwright caso nenhum navegador seja encontrado.
    """
    bundled_exec = getattr(p.chromium, "executable_path", "")
    if bundled_exec and os.path.exists(bundled_exec):
        return await p.chromium.launch(headless=False)

    last_err: Exception | None = None
    for channel in ("chrome", "msedge"):
        try:
            print(f"[INFO] Chromium do Playwright ausente; abrindo login via navegador do sistema ({channel})...")
            return await p.chromium.launch(channel=channel, headless=False)
        except Exception as exc:
            last_err = exc

    print("[INFO] Nenhum navegador Chromium encontrado no sistema; baixando Chromium do Playwright sob demanda...")
    try:
        await asyncio.to_thread(_install_playwright_chromium_sync)
        return await p.chromium.launch(headless=False)
    except Exception as install_err:
        raise RuntimeError(
            f"Não foi possível iniciar o navegador para login HoYoLAB ({install_err}; último fallback: {last_err})."
        ) from install_err


async def capturar_cookies_hoyolab() -> Dict[str, str]:
    """
    Abre o navegador Chromium visível (headed), navega até a página de login
    do HoYoLAB e aguarda a autenticação manual do usuário. Monitora os
    cookies do contexto e captura os valores quando disponíveis.

    Retorna:
        Dict[str, str]: Dicionário contendo os cookies capturados (ltuid_v2, ltoken_v2, ltuid, ltoken).

    Lança:
        Exception: Caso o usuário feche a janela ou ocorra falha na autenticação.
    """
    cookies_dict: Dict[str, str] = {}

    async with async_playwright() as p:
        browser = await _launch_login_browser(p)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto("https://www.hoyolab.com", wait_until="domcontentloaded")

            while True:
                if page.is_closed():
                    break

                try:
                    cookies = await context.cookies()
                except PlaywrightError:
                    break

                for cookie in cookies:
                    if cookie["name"] in (
                        "ltuid_v2",
                        "ltoken_v2",
                        "ltuid",
                        "ltoken",
                        "cookie_token_v2",
                        "cookie_token",
                        "account_id_v2",
                        "account_id",
                    ):
                        cookies_dict[cookie["name"]] = cookie["value"]

                has_v2 = "ltuid_v2" in cookies_dict and "ltoken_v2" in cookies_dict
                has_v1 = "ltuid" in cookies_dict and "ltoken" in cookies_dict
                has_token = "cookie_token_v2" in cookies_dict or "cookie_token" in cookies_dict

                if (has_v2 or has_v1) and (has_token or len(cookies_dict) >= 3):
                    break
                elif has_v2 or has_v1:
                    # Aguarda 2 segundos extras para garantir que cookie_token_v2 seja gravado após o login
                    await asyncio.sleep(2)
                    cookies = await context.cookies()
                    for cookie in cookies:
                        if cookie["name"] in (
                            "ltuid_v2",
                            "ltoken_v2",
                            "ltuid",
                            "ltoken",
                            "cookie_token_v2",
                            "cookie_token",
                            "account_id_v2",
                            "account_id",
                        ):
                            cookies_dict[cookie["name"]] = cookie["value"]
                    break

                await asyncio.sleep(1)

        finally:
            await browser.close()

    is_valid_v2 = "ltuid_v2" in cookies_dict and "ltoken_v2" in cookies_dict
    is_valid_v1 = "ltuid" in cookies_dict and "ltoken" in cookies_dict
    if not (is_valid_v2 or is_valid_v1):
        raise Exception("Navegador fechado ou login não realizado.")

    return cookies_dict
