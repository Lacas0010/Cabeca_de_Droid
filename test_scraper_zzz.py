import sys
import os
from scraper_zzz import PrydwenZZZScraper

def test_zzz_scraper():
    print("[INFO] Inicializando scraper de ZZZ...")
    scraper = PrydwenZZZScraper()
    
    print("[TESTE] Buscando lista de agentes ZZZ...")
    try:
        agents = scraper.get_agent_list()
        print(f"[OK] Encontrados {len(agents)} agentes no Prydwen.")
        print(f"Exemplo de agente: {agents[0]['name']} -> {agents[0]['url']}")
    except Exception as e:
        print(f"[ERRO] Falha ao obter lista de agentes: {e}")
        return

    # Busca o guia de Anby Demara na lista
    anby = next((a for a in agents if "anby" in a["name"].lower()), None)
    if not anby:
        # Se não achar pelo nome, tenta usar um fallback
        anby = {"name": "Anby", "url": "https://www.prydwen.gg/zenless/characters/anby-demara"}
        print("[AVISO] Anby nao encontrada na lista raspada. Usando fallback.")

    print(f"\n[TESTE] Raspando guia para {anby['name']} ({anby['url']})...")
    try:
        data = scraper.scrape_agent_guide(anby['name'], anby['url'])
        print("[OK] Guia raspado com sucesso!")
        print(f" - Quantidade de habilidades ativas: {len(data['skills_active'])}")
        print(f" - Quantidade de passivas: {len(data['skills_passives'])}")
        print(f" - Quantidade de mindscapes: {len(data['skills_mindscapes'])}")
        print(f" - Quantidade de W-Engines: {len(data['w_engines'])}")
        print(f" - Quantidade de conjuntos de discos: {len(data['disk_sets'])}")
        print(f" - Quantidade de status de endgame: {len(data['stats_endgame'])}")
        
        print("\n[INFO] Gravando guia em Markdown...")
        filename = scraper.save_to_markdown(anby['name'], data)
        print(f"[OK] Guia salvo com sucesso em: {filename}")
        
        if os.path.exists(filename):
            print(f"[OK] Arquivo verificado no disco: {filename} (tamanho: {os.path.getsize(filename)} bytes)")
    except Exception as e:
        print(f"[ERRO] Falha ao raspar/salvar guia: {e}")

if __name__ == "__main__":
    test_zzz_scraper()
