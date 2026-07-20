import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from gemini_rag import GeminiRAG

def main():
    print("Testing GeminiRAG Context Loading...")
    
    # Initialize without key for testing context loading only
    rag = GeminiRAG(api_key="TEST_KEY")
    
    for game in ["zzz", "genshin", "hsr", "todos"]:
        print(f"\n--- Loading context for: {game.upper()} ---")
        context = rag.load_game_context(game)
        print(f"Context length: {len(context)} characters")
        
        # Show first 300 characters of context
        print("Context preview:")
        print(context[:300])
        print("--------------------")

if __name__ == "__main__":
    main()
