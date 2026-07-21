import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from groq_rag import GroqRAG

def main():
    print("=== Testing GroqRAG Integration ===")
    
    # 1. Test initialization (will fallback to gemini_api_key in config.json if groq_api_key is absent)
    rag = GroqRAG()
    print(f"GroqRAG initialized. Client active: {rag.client is not None}")
    print(f"API Key loaded (first 5 chars): {rag.api_key[:5] if rag.api_key else 'None'}")
    
    # 2. Test context loading
    for game in ["zzz", "genshin", "hsr", "todos"]:
        print(f"\n--- Loading context for: {game.upper()} ---")
        context = rag.load_game_context(game, "Quais os melhores times que eu posso fazer na minha conta?")
        print(f"Context length: {len(context)} characters")
        print("Context preview (first 150 chars):")
        print(context[:150].strip())
        print("--------------------")
        
    # 3. Test connection (will fail with invalid/Gemini API key, which is good to test error catching)
    print("\n--- Testing API Connection ---")
    success, msg = rag.test_connection()
    print(f"Connection Success: {success}")
    print(f"Connection Status Message: {msg}")

    # 4. Test ask_assistant query and error handling
    print("\n--- Testing ask_assistant (expecting Groq error / fallback behavior) ---")
    test_context = "O jogador possui uma Firefly C6 equipada com cone de luz assinatura."
    test_history = [
        {"role": "user", "text": "Olá assistente!"},
        {"role": "model", "text": "Olá! Sou o assistente especializado em jogos da HoYoverse. Como posso ajudar?"}
    ]
    response = rag.ask_assistant(
        prompt_usuario="Qual personagem o jogador possui e qual sua build?",
        contexto_rag=test_context,
        historico_chat=test_history
    )
    print("Assistant response:")
    print(response)
    print("===================================")

if __name__ == "__main__":
    main()
