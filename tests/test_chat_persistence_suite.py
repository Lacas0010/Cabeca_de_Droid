import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from server import app
import database


class TestChatPersistenceSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        database.init_db()

    def setUp(self):
        database.clear_chat_history("all")

    def tearDown(self):
        database.clear_chat_history("all")

    def test_database_chat_crud_operations(self):
        """Valida inserção, consulta e exclusão isolada por jogo no SQLite."""
        # 1. Inserir mensagens para HSR
        m1_id = database.save_chat_message("hsr", "user", "Melhor build da Acheron?")
        m2_id = database.save_chat_message("hsr", "assistant", "Use o set Pioneiro do Mergulho!")
        self.assertIsNotNone(m1_id)
        self.assertIsNotNone(m2_id)

        # 2. Inserir mensagem para ZZZ
        database.save_chat_message("zzz", "user", "Como buildar a Ellen Joe?")

        # 3. Consultar histórico isolado de HSR
        hsr_history = database.get_chat_history("hsr")
        self.assertEqual(len(hsr_history), 2)
        self.assertEqual(hsr_history[0]["role"], "user")
        self.assertIn("Acheron", hsr_history[0]["content"])
        self.assertEqual(hsr_history[1]["role"], "assistant")
        self.assertIn("Pioneiro", hsr_history[1]["content"])

        # 4. Consultar histórico isolado de ZZZ
        zzz_history = database.get_chat_history("zzz")
        self.assertEqual(len(zzz_history), 1)
        self.assertIn("Ellen", zzz_history[0]["content"])

        # 5. Consultar histórico global (all / todos)
        all_history = database.get_chat_history("all")
        self.assertEqual(len(all_history), 3)

        # 6. Limpar apenas HSR
        deleted_count = database.clear_chat_history("hsr")
        self.assertEqual(deleted_count, 2)
        self.assertEqual(len(database.get_chat_history("hsr")), 0)
        self.assertEqual(len(database.get_chat_history("zzz")), 1)

        # 7. Limpar global
        database.clear_chat_history("all")
        self.assertEqual(len(database.get_chat_history("all")), 0)

    def test_endpoints_chat_history_get_and_delete(self):
        """Valida os endpoints HTTP REST GET e DELETE para o histórico de chat."""
        # Prepara dados no banco
        database.save_chat_message("genshin", "user", "Qual o melhor time pro Neuvillette?")
        database.save_chat_message("genshin", "assistant", "Furina, Kazuha e Baizhu!")

        # GET /api/chat/history/genshin
        response = self.client.get("/api/chat/history/genshin")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["game_id"], "genshin")
        self.assertEqual(len(data["messages"]), 2)
        self.assertEqual(data["messages"][0]["role"], "user")
        self.assertEqual(data["messages"][1]["role"], "assistant")

        # DELETE /api/chat/history/genshin
        del_resp = self.client.delete("/api/chat/history/genshin")
        self.assertEqual(del_resp.status_code, 200)
        del_data = del_resp.json()
        self.assertEqual(del_data["status"], "success")
        self.assertEqual(del_data["deleted_count"], 2)

        # Verifica se o GET posterior retorna lista vazia
        empty_resp = self.client.get("/api/chat/history/genshin")
        self.assertEqual(empty_resp.status_code, 200)
        self.assertEqual(len(empty_resp.json()["messages"]), 0)

    @patch("routers.chat.get_config")
    @patch("routers.chat.GroqRAG")
    def test_chat_interaction_streaming_persists_messages(self, mock_rag_class, mock_get_config):
        """Valida que o endpoint de streaming /api/chat salva a pergunta e resposta completa no SQLite."""
        mock_get_config.return_value = {"groq_api_key": "gsk_dummy_valid_test_key"}

        mock_rag_instance = MagicMock()
        mock_rag_instance.load_game_context.return_value = "Contexto mockado do jogo"
        mock_rag_instance.ask_assistant_stream.return_value = ["Olá! ", "Aqui está ", "sua resposta de teste."]
        mock_rag_class.return_value = mock_rag_instance

        payload = {"message": "Qual é a melhor arma para o Jing Yuan?", "game_id": "hsr", "history": []}

        response = self.client.post("/api/chat", json=payload)
        self.assertEqual(response.status_code, 200)

        # Consome o stream de dados SSE para acionar a persistência ao término
        content = response.text
        self.assertIn("Olá!", content)
        self.assertIn("sua resposta de teste.", content)

        # Verifica persistência no SQLite
        history = database.get_chat_history("hsr")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], "Qual é a melhor arma para o Jing Yuan?")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], "Olá! Aqui está sua resposta de teste.")


if __name__ == "__main__":
    unittest.main()
