import os
import sys
# Adiciona o diretório do projeto ao path para poder importar
sys.path.append(os.path.abspath("."))

from scraper_zzz import PrydwenZZZScraper

def test_meta():
    print("[INFO] Inicializando scraper de meta ZZZ...")
    scraper = PrydwenZZZScraper()
    
    print("[TESTE] Carregando e salvando meta do ZZZ...")
    try:
        filepath = scraper.save_meta_to_markdown()
        print(f"[OK] Relatório gerado com sucesso em: {filepath}")
        if os.path.exists(filepath):
            print(f" - Tamanho do arquivo: {os.path.getsize(filepath)} bytes")
            # Mostra as primeiras 20 linhas do relatório
            print("\n--- Primeiras 20 linhas do arquivo ---")
            with open(filepath, "r", encoding="utf-8") as f:
                lines = [f.readline().strip() for _ in range(20)]
            for line in lines:
                print(line)
    except Exception as e:
        print(f"[ERRO] Falha ao executar o teste: {e}")

if __name__ == "__main__":
    test_meta()
