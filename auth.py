import asyncio
from typing import Dict
from playwright.async_api import async_playwright, Error as PlaywrightError

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
        browser = await p.chromium.launch(headless=False)
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
                    if cookie['name'] in ('ltuid_v2', 'ltoken_v2', 'ltuid', 'ltoken', 'cookie_token_v2', 'cookie_token', 'account_id_v2', 'account_id'):
                        cookies_dict[cookie['name']] = cookie['value']
                
                has_v2 = 'ltuid_v2' in cookies_dict and 'ltoken_v2' in cookies_dict
                has_v1 = 'ltuid' in cookies_dict and 'ltoken' in cookies_dict
                has_token = 'cookie_token_v2' in cookies_dict or 'cookie_token' in cookies_dict
                
                if (has_v2 or has_v1) and (has_token or len(cookies_dict) >= 3):
                    break
                elif has_v2 or has_v1:
                    # Aguarda 2 segundos extras para garantir que cookie_token_v2 seja gravado após o login
                    await asyncio.sleep(2)
                    cookies = await context.cookies()
                    for cookie in cookies:
                        if cookie['name'] in ('ltuid_v2', 'ltoken_v2', 'ltuid', 'ltoken', 'cookie_token_v2', 'cookie_token', 'account_id_v2', 'account_id'):
                            cookies_dict[cookie['name']] = cookie['value']
                    break
                
                await asyncio.sleep(1)
                
        finally:
            await browser.close()
            
    is_valid_v2 = 'ltuid_v2' in cookies_dict and 'ltoken_v2' in cookies_dict
    is_valid_v1 = 'ltuid' in cookies_dict and 'ltoken' in cookies_dict
    if not (is_valid_v2 or is_valid_v1):
        raise Exception("Navegador fechado ou login não realizado.")
        
    return cookies_dict
