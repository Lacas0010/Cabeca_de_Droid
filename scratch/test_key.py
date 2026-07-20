import os
import json
from google import genai

def test_key():
    api_key = None
    config_path = "config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                api_key = config.get("gemini_api_key")
        except Exception as e:
            print("Erro ao ler config.json:", e)

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print("Erro: Chave API do Gemini não encontrada.")
        return

    print("Listando modelos disponiveis para esta chave...")
    try:
        client = genai.Client(api_key=api_key)
        
        # Lista os modelos
        models = client.models.list()
        for m in models:
            print(f"Model: {m.name} (Supported: {m.supported_actions})")
            
    except Exception as e:
        print("Erro ao listar modelos:", e)

if __name__ == "__main__":
    test_key()
