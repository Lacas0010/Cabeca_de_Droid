import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from schemas.team_matcher import EndgameTeamMatchResponse
from services.team_matcher_service import (
    match_endgame_teams,
    categorize_role,
    infer_char_role,
    find_functional_substitutes,
)


class TestTeamMatcherSuite(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # Roster simulado de teste para HSR
        self.mock_hsr_roster = [
            {
                "name": "Acheron",
                "level": 80,
                "rarity": 5,
                "rank_str": "E0",
                "element": "Lightning",
                "icon": "/icon/acheron.png",
                "role": "DPS Principal",
            },
            {
                "name": "Pela",
                "level": 80,
                "rarity": 4,
                "rank_str": "E6",
                "element": "Ice",
                "icon": "/icon/pela.png",
                "role": "Debuffer / Inexistência",
            },
            {
                "name": "Gallagher",
                "level": 80,
                "rarity": 4,
                "rank_str": "E6",
                "element": "Fire",
                "icon": "/icon/gallagher.png",
                "role": "Sustento / Cura",
            },
            # Jiaoqiu NÃO está no roster (falta 1 para fechar o Acheron Nihility Blast)
            # Mas o jogador tem outros debuffers que podem substituir:
            {
                "name": "Silver Wolf",
                "level": 80,
                "rarity": 5,
                "rank_str": "E0",
                "element": "Quantum",
                "icon": "/icon/silver_wolf.png",
                "role": "Debuffer / Inexistência",
            },
            {
                "name": "Guinaifen",
                "level": 70,
                "rarity": 4,
                "rank_str": "E4",
                "element": "Fire",
                "icon": "/icon/guinaifen.png",
                "role": "Debuffer / Inexistência",
            },
            # E tem outros sustentos
            {
                "name": "Aventurine",
                "level": 80,
                "rarity": 5,
                "rank_str": "E0",
                "element": "Imaginary",
                "icon": "/icon/aventurine.png",
                "role": "Sustento / Escudo",
            },
        ]

        # Roster simulado para ZZZ
        self.mock_zzz_roster = [
            {
                "name": "Ellen Joe",
                "level": 60,
                "rarity": 5,
                "rank_str": "M0",
                "element": "Ice",
                "icon": "/icon/ellen.png",
                "role": "DPS Principal",
            },
            {
                "name": "Lycaon",
                "level": 60,
                "rarity": 5,
                "rank_str": "M0",
                "element": "Ice",
                "icon": "/icon/lycaon.png",
                "role": "Atordoamento (Stun)",
            },
            {
                "name": "Soukaku",
                "level": 60,
                "rarity": 4,
                "rank_str": "M6",
                "element": "Ice",
                "icon": "/icon/soukaku.png",
                "role": "Suporte / Buffer",
            },
        ]

    def test_categorize_role(self):
        """Valida que papéis e classes são mapeados para categorias fundamentais."""
        self.assertEqual(categorize_role("Sustento / Cura"), "SUSTAIN")
        self.assertEqual(categorize_role("Preservation", path="Preservation"), "SUSTAIN")
        self.assertEqual(categorize_role("Atordoamento (Stun)"), "STUNNER")
        self.assertEqual(categorize_role("Buffer / Harmonia"), "BUFFER")
        self.assertEqual(categorize_role("Debuffer / Inexistência"), "DEBUFFER")
        self.assertEqual(categorize_role("DPS Principal"), "DPS")

    @patch("services.team_matcher_service.database.get_active_uid")
    @patch("services.team_matcher_service.database.get_roster_data")
    def test_team_matcher_75_percent_match_with_substitute(self, mock_roster, mock_uid):
        """Testa time com 75% de posse (3/4) e geração de substituto funcional no roster."""
        mock_uid.return_value = "700111222"
        mock_roster.return_value = self.mock_hsr_roster

        res = match_endgame_teams("hsr", uid="700111222")
        self.assertIsInstance(res, EndgameTeamMatchResponse)
        self.assertEqual(res.status, "success")
        self.assertGreater(res.total_teams, 0)

        # Localiza o time da Acheron
        acheron_team = next((t for t in res.teams if "Acheron" in t.team_name), None)
        self.assertIsNotNone(acheron_team)
        self.assertEqual(acheron_team.total_count, 4)
        self.assertEqual(acheron_team.owned_count, 3)  # Acheron, Pela, Gallagher
        self.assertEqual(acheron_team.match_percentage, 75.0)

        # Verifica membro faltante: Jiaoqiu
        jiaoqiu_member = next((m for m in acheron_team.members if m.name == "Jiaoqiu"), None)
        self.assertIsNotNone(jiaoqiu_member)
        self.assertFalse(jiaoqiu_member.is_owned)
        self.assertGreater(len(jiaoqiu_member.substitutes), 0)

        # O substituto recomendado deve ser Guinaifen ou Silver Wolf do roster
        sub_names = [s.name for s in jiaoqiu_member.substitutes]
        self.assertTrue("Silver Wolf" in sub_names or "Guinaifen" in sub_names)
        self.assertTrue(len(jiaoqiu_member.substitutes[0].synergy_reason) > 0)

    @patch("services.team_matcher_service.database.get_active_uid")
    @patch("services.team_matcher_service.database.get_roster_data")
    def test_team_matcher_zzz_100_percent_match(self, mock_roster, mock_uid):
        """Testa composição de 3 membros de ZZZ com 100% de compatibilidade."""
        mock_uid.return_value = "100222333"
        mock_roster.return_value = self.mock_zzz_roster

        res = match_endgame_teams("zzz", uid="100222333")
        self.assertIsInstance(res, EndgameTeamMatchResponse)
        self.assertEqual(res.status, "success")

        ellen_team = next((t for t in res.teams if "Ellen" in t.team_name), None)
        self.assertIsNotNone(ellen_team)
        self.assertEqual(ellen_team.total_count, 3)
        self.assertEqual(ellen_team.owned_count, 3)
        self.assertEqual(ellen_team.match_percentage, 100.0)
        self.assertTrue(ellen_team.is_ready)
        self.assertGreater(ellen_team.readiness_score, 90.0)

    @patch("services.team_matcher_service.database.get_active_uid")
    @patch("services.team_matcher_service.database.get_roster_data")
    def test_team_matcher_mode_filter(self, mock_roster, mock_uid):
        """Garante que a filtragem por modo de endgame funcione corretamente."""
        mock_uid.return_value = "700111222"
        mock_roster.return_value = self.mock_hsr_roster

        res_moc = match_endgame_teams("hsr", mode="Memory of Chaos")
        for t in res_moc.teams:
            self.assertIn("Memory of Chaos", t.mode)

        res_pf = match_endgame_teams("hsr", mode="Pure Fiction")
        for t in res_pf.teams:
            self.assertIn("Pure Fiction", t.mode)

    @patch("services.team_matcher_service.database.get_active_uid")
    @patch("services.team_matcher_service.database.get_roster_data")
    def test_team_matcher_min_match_filter(self, mock_roster, mock_uid):
        """Garante que equipes abaixo do limiar min_match sejam filtradas."""
        mock_uid.return_value = "700111222"
        mock_roster.return_value = self.mock_hsr_roster

        res_all = match_endgame_teams("hsr", min_match=0.0)
        res_filtered = match_endgame_teams("hsr", min_match=75.0)

        self.assertLessEqual(len(res_filtered.teams), len(res_all.teams))
        for t in res_filtered.teams:
            self.assertGreaterEqual(t.match_percentage, 75.0)

    @patch("services.team_matcher_service.database.get_active_uid")
    @patch("services.team_matcher_service.database.get_roster_data")
    def test_team_matcher_empty_roster(self, mock_roster, mock_uid):
        """Verifica resiliência com conta vazia sem quebrar a execução."""
        mock_uid.return_value = "999999999"
        mock_roster.return_value = []

        res = match_endgame_teams("hsr", uid="999999999")
        self.assertEqual(res.status, "success")
        self.assertEqual(res.ready_teams_count, 0)
        for t in res.teams:
            self.assertEqual(t.owned_count, 0)
            self.assertEqual(t.match_percentage, 0.0)

    @patch("routers.endgame.match_endgame_teams")
    def test_api_endgame_team_match_endpoint(self, mock_matcher):
        """Valida que o endpoint REST responde com status 200 e contrato Pydantic correto."""
        mock_matcher.return_value = EndgameTeamMatchResponse(
            status="success",
            game_id="hsr",
            uid="700111222",
            total_teams=1,
            ready_teams_count=1,
            teams=[],
            available_modes=["Memory of Chaos"],
        )

        response = self.client.get("/api/endgame/team-match/hsr?uid=700111222&mode=Memory")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["game_id"], "hsr")
        self.assertEqual(data["uid"], "700111222")

    def test_api_endgame_invalid_game(self):
        """Verifica tratamento de erro para jogo inválido."""
        response = self.client.get("/api/endgame/team-match/invalido")
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
