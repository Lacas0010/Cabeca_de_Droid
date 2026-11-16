import os
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from server import app


class TestSnapshotsAndHistorySuite(unittest.TestCase):
    """Testes offline garantindo persistência manual de snapshots, ordenação recente (>50) e contratos REST."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_db_path = os.path.join(self.tmp_dir.name, "test_snapshots.db")
        self.db_patch = patch.object(database, "DATABASE_NAME", self.tmp_db_path)
        self.db_patch.start()
        database.init_db()
        self.client = TestClient(app)

    def tearDown(self):
        self.db_patch.stop()
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def _sample_roster(self, level=80):
        return [
            {
                "id": "1308",
                "uid": "600156277",
                "name": "Acheron",
                "level": level,
                "rarity": 5,
                "rank_str": "E2",
                "element": "Lightning",
                "weapon": {"name": "Along the Passing Shore", "level": 80, "rank": 1},
                "relics": [
                    {
                        "slot": "Cabeça",
                        "name": "Pioneer Helmet",
                        "main": "PV (705)",
                        "sub": "Taxa CRIT: 9.0%, Dano CRIT: 18.0%",
                    }
                ],
                "skills": [],
                "ex_ranks": [],
                "stats": {},
            }
        ]

    def test_get_account_history_returns_newest_50_when_more_than_50_exist(self):
        # Insere 55 snapshots com timestamps crescentes simulando > 50 registros históricos
        with database.get_connection() as conn:
            cur = conn.cursor()
            for i in range(1, 56):
                cur.execute(
                    """
                    INSERT INTO account_snapshots
                    (uid, game_id, character_count, five_star_count, average_build_score, snapshot_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "600156277",
                        "hsr",
                        67,
                        45,
                        float(i),
                        '{"all_characters": [], "five_stars": 45, "four_stars": 22}',
                        f"2026-10-{(i // 24) + 1:02d} {i % 24:02d}:00:00",
                    ),
                )

        self.assertEqual(database.get_account_history_count("hsr"), 55)
        history = database.get_account_history("hsr", limit=50, offset=0)
        self.assertEqual(len(history), 50)
        # Deve retornar os 50 MAIS RECENTES (scores 6.0 .. 55.0), ordenados cronologicamente do mais antigo ao mais novo do bloco
        self.assertEqual(history[0]["average_build_score"], 6.0)
        self.assertEqual(history[-1]["average_build_score"], 55.0)

    def test_save_account_snapshot_dedup_vs_force(self):
        roster = self._sample_roster(level=80)
        snap1 = database.save_account_snapshot("600156277", "hsr", roster, force=False)
        snap2 = database.save_account_snapshot("600156277", "hsr", roster, force=False)
        self.assertEqual(snap1, snap2)
        self.assertEqual(database.get_account_history_count("hsr"), 1)

        snap3 = database.save_account_snapshot("600156277", "hsr", roster, force=True)
        self.assertIsNotNone(snap3)
        self.assertNotEqual(snap3, snap1)
        self.assertEqual(database.get_account_history_count("hsr"), 2)

    @patch("services.history_service.MultiGameExtractor")
    @patch("services.history_service.get_cookies", return_value={"ltuid_v2": "123", "ltoken_v2": "abc"})
    def test_manual_snapshot_endpoint_and_total_count(self, _mock_cookies, mock_extractor_cls):
        mock_instance = MagicMock()
        mock_instance.extrair_jogo = AsyncMock(return_value="hsr/roster_hsr.md")
        mock_extractor_cls.return_value = mock_instance

        with patch("database.get_roster_data", return_value=self._sample_roster(level=80)):
            resp = self.client.post("/api/history/hsr/snapshot", json={"refresh_from_hoyolab": True})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["game_id"], "hsr")
        self.assertIsNotNone(data["snapshot_id"])
        self.assertTrue(data["refreshed_from_hoyolab"])

        hist_resp = self.client.get("/api/history/hsr")
        self.assertEqual(hist_resp.status_code, 200)
        hist_data = hist_resp.json()
        self.assertEqual(hist_data["total_count"], 1)
        self.assertEqual(len(hist_data["history"]), 1)

    @patch("services.history_service.MultiGameExtractor")
    @patch("services.history_service.get_cookies", return_value=None)
    def test_sync_global_endpoint_exists_and_handles_offline_roster(self, _mock_cookies, _mock_extractor):
        with patch(
            "database.get_roster_data",
            side_effect=lambda g: self._sample_roster(level=80) if g == "hsr" else [],
        ):
            resp = self.client.post("/api/sync/global")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["success"])
        self.assertIn("hsr", body["results"])
        self.assertTrue(body["results"]["hsr"]["success"])

    def test_manual_snapshot_invalid_game_returns_400(self):
        resp = self.client.post("/api/history/invalid_game/snapshot")
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
