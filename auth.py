import asyncio
from playwright.async_api import async_playwright, Error as PlaywrightError

async def capturar_cookies_hoyolab() -> dict:
    """
    Abre o navegador de forma visível (headed), navega até a página de login
    do HoYoLAB e aguarda a autenticação manual do usuário. Monitora os
    cookies do contexto e captura os valores quando disponíveis.

    Retorna:
        dict: Dicionário contendo os cookies capturados (ltuid_v2, ltoken_v2, ltuid, ltoken).

    Lança:
        Exception: Caso o usuário feche a janela ou ocorra uma falha antes do login.
    """
    cookies_dict = {}
    
    async with async_playwright() as p:
        # Iniciamos o navegador visível (headed)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Abre a página principal do HoYoLAB
            await page.goto("https://www.hoyolab.com")
            
            # Loop de monitoramento de cookies
            while True:
                # Se o usuário fechar a página manualmente
                if page.is_closed():
                    break
                
                try:
                    cookies = await context.cookies()
                except PlaywrightError:
                    # Se o navegador foi fechado de alguma outra forma
                    break
                
                # Procura pelos cookies de login específicos
                for cookie in cookies:
                    if cookie['name'] in ('ltuid_v2', 'ltoken_v2', 'ltuid', 'ltoken'):
                        cookies_dict[cookie['name']] = cookie['value']
                
                # Verifica se pelo menos um par completo de login (v2 ou v1) foi capturado
                has_v2 = 'ltuid_v2' in cookies_dict and 'ltoken_v2' in cookies_dict
                has_v1 = 'ltuid' in cookies_dict and 'ltoken' in cookies_dict
                if has_v2 or has_v1:
                    break
                
                # Aguarda 1 segundo antes da próxima varificação
                await asyncio.sleep(1)
                
        finally:
            # Garante que o navegador seja fechado após o término ou erro
            await browser.close()
            
    # Lança exceção caso o login não tenha sido capturado
    is_valid_v2 = 'ltuid_v2' in cookies_dict and 'ltoken_v2' in cookies_dict
    is_valid_v1 = 'ltuid' in cookies_dict and 'ltoken' in cookies_dict
    if not (is_valid_v2 or is_valid_v1):
        raise Exception("Navegador fechado ou login não realizado.")
        
    return cookies_dict
