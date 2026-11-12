import unittest
import time
import os
import re
from unittest.mock import MagicMock

class TestSearchDebounceSuite(unittest.TestCase):
    """
    Suíte de testes unitários para validação de Debounce (~300ms),
    AbortController e salvaguarda de tamanho mínimo (>= 2 caracteres)
    em todos os campos de busca, filtro e salvamento do frontend.
    """

    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.api_client_path = os.path.join(self.base_dir, "static", "js", "modules", "api_client.js")
        self.roster_path = os.path.join(self.base_dir, "static", "js", "modules", "roster.js")
        self.chat_rag_path = os.path.join(self.base_dir, "static", "js", "modules", "chat_rag.js")
        self.farming_path = os.path.join(self.base_dir, "static", "js", "modules", "farming.js")
        self.sync_manager_path = os.path.join(self.base_dir, "static", "js", "modules", "sync_manager.js")
        self.gacha_tracker_path = os.path.join(self.base_dir, "static", "js", "modules", "gacha_tracker.js")

    def test_api_client_defines_create_debounced_search(self):
        """Valida se api_client.js define e exporta createDebouncedSearch com AbortController."""
        with open(self.api_client_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("function createDebouncedSearch", content)
        self.assertIn("window.createDebouncedSearch = createDebouncedSearch", content)
        self.assertIn("AbortController", content)
        self.assertIn("delay = 300", content)
        self.assertIn("minLength = 2", content)
        self.assertIn("immediateOnEmpty", content)
        self.assertIn("currentController.abort()", content)

    def test_roster_search_debounced(self):
        """Valida se o campo de busca de personagens no roster utiliza debounce de 300ms e min 2 caracteres."""
        with open(self.roster_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("window.createDebouncedSearch", content)
        self.assertIn("delay: 300", content)
        self.assertIn("minLength: 2", content)
        self.assertIn("debouncedRosterSearch", content)

    def test_team_builder_and_name_debounced(self):
        """Valida se o filtro de time e a edição do nome do time em chat_rag.js utilizam debouncing."""
        with open(self.chat_rag_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("_teamNameDebouncers", content)
        self.assertIn("_teamRosterDebouncers", content)
        self.assertIn("window.createDebouncedSearch", content)
        self.assertIn("delay: 300", content)
        self.assertIn("minLength: 2", content)

    def test_farming_character_search_debounced(self):
        """Valida se a busca de personagens no modal diário de farm possui debounce e proteção contra render repetido."""
        with open(self.farming_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("_farmCharDebouncer", content)
        self.assertIn("window.createDebouncedSearch", content)
        self.assertIn("delay: 300", content)
        self.assertIn("minLength: 2", content)

    def test_sync_manager_help_search_debounced(self):
        """Valida se o input de busca da Central de Ajuda implementa debounce de 300ms e minLength=2."""
        with open(self.sync_manager_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("debouncedHelpSearch", content)
        self.assertIn("window.createDebouncedSearch", content)
        self.assertIn("delay: 300", content)
        self.assertIn("minLength: 2", content)

    def test_gacha_tracker_abort_controller_integration(self):
        """Valida se o histórico do Gacha Tracker integra AbortController para cancelar requisições obsoletas."""
        with open(self.gacha_tracker_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("_trackerHistoryController", content)
        self.assertIn("new AbortController()", content)
        self.assertTrue("signal" in content)
        self.assertIn("AbortError", content)

    def test_debounce_behavioral_simulation_notebook_single_request(self):
        """
        Simulação comportamental:
        Ao digitar 'notebook' (8 teclas em intervalos rápidos de 30ms):
        - Apenas 1 requisição final deve ser despachada (após o término da digitação).
        - Tecla 'n' (< 2 caracteres) é descartada.
        - As 7 teclas intermediárias cancelam os timers anteriores sem emitir requisições.
        """
        dispatched_queries = []
        aborted_signals = []

        class MockAbortSignal:
            def __init__(self):
                self.aborted = False

        class MockAbortController:
            def __init__(self):
                self.signal = MockAbortSignal()
            def abort(self):
                self.signal.aborted = True

        class PythonDebouncedSearch:
            def __init__(self, fn, delay=300, min_length=2, immediate_on_empty=True):
                self.fn = fn
                self.delay = delay
                self.min_length = min_length
                self.immediate_on_empty = immediate_on_empty
                self.pending_timer_query = None
                self.current_controller = None

            def trigger(self, query):
                trimmed = (query or "").strip()

                # 1. Cancela timer anterior
                self.pending_timer_query = None

                # 2. Aborta requisição em voo
                if self.current_controller:
                    self.current_controller.abort()
                    aborted_signals.append(self.current_controller.signal)
                    self.current_controller = None

                # 3. Campo limpo
                if len(trimmed) == 0:
                    if self.immediate_on_empty:
                        self.current_controller = MockAbortController()
                        self.fn(query, self.current_controller.signal)
                    return

                # 4. Menos de min_length
                if len(trimmed) < self.min_length:
                    return

                # 5. Agenda timer
                self.pending_timer_query = query
                self.current_controller = MockAbortController()

            def advance_time(self):
                """Simula a passagem do tempo de debounce (~300ms) sem novas teclas."""
                if self.pending_timer_query is not None and self.current_controller is not None:
                    q = self.pending_timer_query
                    sig = self.current_controller.signal
                    self.pending_timer_query = None
                    self.fn(q, sig)

        def mock_fetch(query, signal):
            if not signal.aborted:
                dispatched_queries.append(query)

        searcher = PythonDebouncedSearch(mock_fetch, delay=300, min_length=2, immediate_on_empty=True)

        # Simula a digitação da palavra "notebook" tecla por tecla
        keystrokes = ["n", "no", "not", "note", "noteb", "notebo", "noteboo", "notebook"]
        for key in keystrokes:
            searcher.trigger(key)
            # Durante a digitação rápida, nenhuma requisição foi despachada
            self.assertEqual(len(dispatched_queries), 0, f"Nenhuma busca deve ser disparada enquanto digita '{key}'")

        # Usuário para de digitar e o timer de 300ms expira
        searcher.advance_time()

        # Validação crucial: exatamente 1 requisição com "notebook", e não 8!
        self.assertEqual(len(dispatched_queries), 1)
        self.assertEqual(dispatched_queries[0], "notebook")

        # Teste de esvaziamento imediato (backspace completo)
        searcher.trigger("")
        self.assertEqual(len(dispatched_queries), 2)
        self.assertEqual(dispatched_queries[1], "")

if __name__ == "__main__":
    unittest.main()
