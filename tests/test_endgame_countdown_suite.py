import asyncio
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

import endgame_extractor
from server import app
from services import endgame_service


class TestEndgameCountdownSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        endgame_service.invalidate_endgame_cache()

    def tearDown(self):
        endgame_service.invalidate_endgame_cache()

    def test_server_timezone_and_to_utc_iso(self):
        """Valida conversão de PartialTime, datetime naive/aware e epoch Unix para ISO-8601 UTC por região de UID."""
        self.assertEqual(endgame_extractor.get_server_timezone("hsr", "600156277").utcoffset(None), timedelta(hours=-5))
        self.assertEqual(endgame_extractor.get_server_timezone("hsr", "701710621").utcoffset(None), timedelta(hours=1))
        self.assertEqual(endgame_extractor.get_server_timezone("hsr", "800111222").utcoffset(None), timedelta(hours=8))
        self.assertEqual(endgame_extractor.get_server_timezone("zzz", "1000135767").utcoffset(None), timedelta(hours=-5))
        self.assertEqual(endgame_extractor.get_server_timezone("zzz", "1500135767").utcoffset(None), timedelta(hours=1))
        self.assertEqual(endgame_extractor.get_server_timezone("zzz", "1300135767").utcoffset(None), timedelta(hours=8))

        # HSR PartialTime (naive server time America UTC-5 -> +5h em UTC)
        partial = SimpleNamespace(datetime=datetime(2026, 12, 14, 4, 0, 0))
        self.assertEqual(endgame_extractor.to_utc_iso(partial, "hsr", "600156277"), "2026-12-14T09:00:00Z")

        # Genshin Teatro Unix epoch (int -> UTC direto)
        self.assertEqual(endgame_extractor.to_utc_iso(1796115599, "genshin", "615929016"), "2026-12-01T08:59:59Z")

        # ZZZ Shiyu aware datetime UTC-5 -> UTC
        aware_dt = datetime(2026, 11, 27, 3, 59, 59, tzinfo=timezone(timedelta(hours=-5)))
        self.assertEqual(endgame_extractor.to_utc_iso(aware_dt, "zzz", "1000135767"), "2026-11-27T08:59:59Z")

    def test_extract_endgame_schedules_all_games_mocked(self):
        """Valida extract_endgame_schedules para HSR, Genshin e ZZZ com cliente HoYoLAB mockado."""
        mock_client = MagicMock()
        mock_client.get_starrail_challenge = AsyncMock(
            return_value=SimpleNamespace(
                seasons=[SimpleNamespace(begin_time=SimpleNamespace(datetime=datetime(2026, 11, 2, 4, 0)), end_time=SimpleNamespace(datetime=datetime(2026, 12, 14, 4, 0)))]
            )
        )
        mock_client.get_starrail_pure_fiction = AsyncMock(
            return_value=SimpleNamespace(
                seasons=[SimpleNamespace(begin_time=SimpleNamespace(datetime=datetime(2026, 10, 19, 4, 0)), end_time=SimpleNamespace(datetime=datetime(2026, 11, 30, 4, 0)))]
            )
        )
        mock_client.get_starrail_apc_shadow = AsyncMock(
            return_value=SimpleNamespace(
                seasons=[SimpleNamespace(begin_time=SimpleNamespace(datetime=datetime(2026, 11, 16, 4, 0)), end_time=SimpleNamespace(datetime=datetime(2026, 12, 28, 4, 0)))]
            )
        )
        hsr_sched = asyncio.run(endgame_extractor.extract_endgame_schedules(mock_client, "hsr", 600156277))
        self.assertEqual(hsr_sched["moc"]["reset_at"], "2026-12-14T09:00:00Z")
        self.assertEqual(hsr_sched["pure_fiction"]["reset_at"], "2026-11-30T09:00:00Z")
        self.assertEqual(hsr_sched["apocalyptic_shadow"]["reset_at"], "2026-12-28T09:00:00Z")

        mock_client.get_genshin_spiral_abyss = AsyncMock(
            return_value=SimpleNamespace(
                start_time=datetime(2026, 11, 16, 6, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 12, 16, 5, 59, 59, tzinfo=timezone.utc),
            )
        )
        mock_client.get_imaginarium_theater = AsyncMock(
            return_value=SimpleNamespace(
                datas=[SimpleNamespace(schedule=SimpleNamespace(start_time=1793523600, end_time=1796115599))]
            )
        )
        gen_sched = asyncio.run(endgame_extractor.extract_endgame_schedules(mock_client, "genshin", 615929016))
        self.assertEqual(gen_sched["spiral_abyss"]["reset_at"], "2026-12-16T05:59:59Z")
        self.assertEqual(gen_sched["imaginarium_theater"]["reset_at"], "2026-12-01T08:59:59Z")

        mock_client.get_shiyu_defense = AsyncMock(
            return_value=SimpleNamespace(
                begin_time=datetime(2026, 11, 13, 4, 0, tzinfo=timezone(timedelta(hours=-5))),
                end_time=datetime(2026, 11, 27, 3, 59, 59, tzinfo=timezone(timedelta(hours=-5))),
            )
        )
        mock_client.get_deadly_assault = AsyncMock(
            return_value=SimpleNamespace(
                start_time=datetime(2026, 11, 20, 4, 0),
                end_time=datetime(2026, 12, 2, 3, 59, 59),
            )
        )
        zzz_sched = asyncio.run(endgame_extractor.extract_endgame_schedules(mock_client, "zzz", 1000135767))
        self.assertEqual(zzz_sched["shiyu_defense"]["reset_at"], "2026-11-27T08:59:59Z")
        self.assertEqual(zzz_sched["deadly_assault"]["reset_at"], "2026-12-02T08:59:59Z")

    def test_genshin_extractor_keeps_current_reset_when_falling_back_to_previous_season(self):
        """Se o Abismo atual estiver sem pisos concluídos, reset_at deve manter o prazo da temporada atual."""
        current_abyss = SimpleNamespace(
            floors=[],
            start_time=datetime(2026, 11, 16, 6, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 12, 16, 5, 59, 59, tzinfo=timezone.utc),
        )
        prev_chamber = SimpleNamespace(chamber=3, battles=[])
        prev_floor = SimpleNamespace(floor=12, stars=9, max_stars=9, chambers=[prev_chamber])
        prev_abyss = SimpleNamespace(
            floors=[prev_floor],
            start_time=datetime(2026, 10, 16, 6, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 11, 16, 5, 59, 59, tzinfo=timezone.utc),
        )

        mock_client = MagicMock()
        mock_client.get_genshin_spiral_abyss = AsyncMock(side_effect=[current_abyss, prev_abyss])
        mock_client.get_imaginarium_theater = AsyncMock(return_value=SimpleNamespace(datas=[]))

        _, modes = asyncio.run(endgame_extractor.extrair_endgame_genshin_data(mock_client, 615929016))
        self.assertEqual(len(modes), 1)
        self.assertEqual(modes[0]["id"], "spiral_abyss")
        self.assertEqual(modes[0]["reset_at"], "2026-12-16T05:59:59Z")

    def test_endgame_service_returns_reset_schedules_and_offline_projection(self):
        """Valida enriquecimento com reset_schedules, projeção offline de ciclos expirados e tradução EN."""
        future_iso = (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        expired_iso = (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")

        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("services.endgame_service._schedules_disk_path", return_value=os.path.join(tmpdir, "sched.json")),
            patch("services.endgame_service.get_cookies", return_value=None),
            patch("services.endgame_service.database.get_active_uid", return_value="600156277"),
            patch(
                "services.endgame_service.database.get_endgame_data",
                return_value={
                    "uid": "600156277",
                    "updated_at": "2026-11-23T09:00:00",
                    "modes": [
                        {"id": "moc", "name": "Caos da Memória (MoC)", "reset_at": future_iso, "teams": []},
                        {"id": "pure_fiction", "name": "Ficção Pura", "reset_at": expired_iso, "teams": []},
                    ],
                },
            ),
            patch("services.endgame_service.get_roster", new=AsyncMock(return_value=[])),
        ):
            res_en = asyncio.run(endgame_service.get_endgame("hsr", lang="en"))

        self.assertEqual(len(res_en["reset_schedules"]), 3)
        sched_map = {s["id"]: s for s in res_en["reset_schedules"]}
        self.assertEqual(sched_map["moc"]["name"], "Memory of Chaos (MoC)")
        self.assertEqual(sched_map["moc"]["reset_at"], future_iso)
        self.assertEqual(sched_map["moc"]["source"], "hoyolab")
        # Expirado há 5 dias -> projetado +42 dias para o futuro
        self.assertEqual(sched_map["pure_fiction"]["source"], "estimated")
        proj_dt = datetime.fromisoformat(sched_map["pure_fiction"]["reset_at"].replace("Z", "+00:00"))
        self.assertGreater(proj_dt, datetime.now(timezone.utc))

    def test_api_endgame_endpoint_returns_reset_schedules_contract(self):
        """Valida que GET /api/endgame/genshin retorna reset_schedules mesmo sem cookies (calendário mensal)."""
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch("services.endgame_service._schedules_disk_path", return_value=os.path.join(tmpdir, "sched.json")),
            patch("services.endgame_service.get_cookies", return_value=None),
            patch("services.endgame_service.database.get_active_uid", return_value="615929016"),
            patch("services.endgame_service.database.get_endgame_data", return_value=None),
            patch("os.path.exists", return_value=False),
        ):
            resp = self.client.get("/api/endgame/genshin?lang=pt")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("reset_schedules", body)
        ids = [s["id"] for s in body["reset_schedules"]]
        self.assertEqual(ids, ["spiral_abyss", "imaginarium_theater"])
        for item in body["reset_schedules"]:
            self.assertTrue(item["reset_at"].endswith("Z"))

    def test_frontend_endgame_countdown_wiring_and_responsive_css(self):
        """Valida helpers de countdown, pausa em document.hidden e responsividade mobile no CSS."""
        root = Path(__file__).resolve().parent.parent
        endgame_js = (root / "static" / "js" / "modules" / "endgame.js").read_text(encoding="utf-8")
        endgame_css = (root / "static" / "css" / "endgame_strategy.css").read_text(encoding="utf-8")

        for token in [
            "function formatEndgameCountdown",
            "function renderEndgameResetStrip",
            "function renderModeResetChip",
            "function tickEndgameCountdowns",
            "if (document.hidden) return;",
            'document.addEventListener("visibilitychange"',
            "data-reset-at=",
        ]:
            self.assertIn(token, endgame_js)

        self.assertIn(".endgame-reset-strip", endgame_css)
        self.assertIn(".endgame-reset-card", endgame_css)
        self.assertIn(".endgame-metric-chip.reset-countdown", endgame_css)
        self.assertIn("@media (max-width: 768px)", endgame_css)


if __name__ == "__main__":
    unittest.main()
