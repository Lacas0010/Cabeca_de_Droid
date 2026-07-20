import asyncio
import json
import os
from extractor import HSRExtractor, GenshinExtractor, ZZZExtractor

async def testar_conexao_multi_jogo():
    # 1. Carrega os cookies salvos pelo auth.py
    cookie_file = "cookies.json"
    if not os.path.exists(cookie_file):
        print(f"[ERRO] Arquivo {cookie_file} nao encontrado. Faca login na GUI primeiro.")
        return

    try:
        with open(cookie_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)
    except Exception as e:
        print(f"[ERRO] Erro ao ler cookies.json: {e}")
        return

    print("[INFO] Inicializando extratores...")
    
    # 2. Testa o mapeamento de contas e a extração para cada jogo
    # --- Honkai: Star Rail ---
    print("\n[TESTE] Testando Honkai: Star Rail...")
    try:
        hsr = HSRExtractor(cookies)
        acc = await hsr.get_account("hkrpg")
        if acc:
            print(f"[OK] Conta de HSR encontrada! UID: {acc.uid} | Nivel: {acc.level} | Servidor: {acc.server_name}")
            print("[INFO] Extraindo e gerando relatorio Markdown para HSR...")
            filename = await hsr.extrair_e_salvar("hsr/teste_personagens_hsr.md")
            print(f"[OK] Relatorio gerado com sucesso: {filename}")
        else:
            print("[AVISO] Nenhuma conta de HSR encontrada para este perfil.")
    except Exception as e:
        print(f"[ERRO] Falha no teste de HSR: {e}")

    # --- Genshin Impact ---
    print("\n[TESTE] Testando Genshin Impact...")
    try:
        genshin_ext = GenshinExtractor(cookies)
        acc = await genshin_ext.get_account("hk4e")
        if acc:
            print(f"[OK] Conta de Genshin encontrada! UID: {acc.uid} | Nivel: {acc.level} | Servidor: {acc.server_name}")
            print("[INFO] Extraindo e gerando relatorio Markdown para Genshin...")
            filename = await genshin_ext.extrair_e_salvar("genshin/teste_personagens_genshin.md")
            print(f"[OK] Relatorio gerado com sucesso: {filename}")
        else:
            print("[AVISO] Nenhuma conta de Genshin encontrada para este perfil.")
    except Exception as e:
        print(f"[ERRO] Falha no teste de Genshin: {e}")

    # --- Zenless Zone Zero (ZZZ) ---
    print("\n[TESTE] Testando Zenless Zone Zero...")
    try:
        zzz = ZZZExtractor(cookies)
        acc = await zzz.get_account("nap")
        if acc:
            print(f"[OK] Conta de ZZZ encontrada! UID: {acc.uid} | Nivel: {acc.level} | Servidor: {acc.server_name}")
            print("[INFO] Extraindo e gerando relatorio Markdown para ZZZ...")
            filename = await zzz.extrair_e_salvar("zzz/teste_agentes_zzz.md")
            print(f"[OK] Relatorio gerado com sucesso: {filename}")
        else:
            print("[AVISO] Nenhuma conta de ZZZ encontrada para este perfil.")
    except Exception as e:
        print(f"[ERRO] Falha no teste de ZZZ: {e}")

if __name__ == "__main__":
    asyncio.run(testar_conexao_multi_jogo())
