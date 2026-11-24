import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from server import app
from services import checkin_service


ROOT_DIR = Path(__file__).resolve().parent.parent


class TestDailyNotesSuite(unittest.TestCase):
    """Testes unitários offline da Etapa 5: Daily Notes completo e horário exato de lotação da energia."""

    def test_parse_duration_seconds_handles_all_hoyolab_formats(self):
        self.assertEqual(checkin_service.parse_duration_seconds(timedelta(hours=2, minutes=15)), 8100)
        self.assertEqual(checkin_service.parse_duration_seconds(3600), 3600)
        self.assertEqual(checkin_service.parse_duration_seconds("7200"), 7200)
        self.assertEqual(checkin_service.parse_duration_seconds("1 day, 2:30:15"), 86400 + 7200 + 1800 + 15)
        self.assertEqual(checkin_service.parse_duration_seconds("04:10:05"), 4 * 3600 + 10 * 60 + 5)
        self.assertEqual(checkin_service.parse_duration_seconds("P1DT1H2M4S"), 86400 + 3600 + 120 + 4)
        self.assertEqual(checkin_service.parse_duration_seconds("PT0S"), 0)
        self.assertEqual(checkin_service.parse_duration_seconds(None), 0)

    def test_compute_future_utc_iso_exact_cap_time(self):
        ref = datetime(2026, 11, 24, 13, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(checkin_service.compute_future_utc_iso(3660, ref), "2026-11-24T14:01:00Z")
        self.assertIsNone(checkin_service.compute_future_utc_iso(0, ref))

    def test_fetch_realtime_notes_extracts_full_daily_notes_for_all_3_games(self):
        fake_accounts = [
            SimpleNamespace(game_biz="hk4e_global", uid=615929016, nickname="Lumine", level=60),
            SimpleNamespace(game_biz="hkrpg_global", uid=600156277, nickname="Stelle", level=70),
            SimpleNamespace(game_biz="nap_global", uid=1000135767, nickname="Belle", level=60),
        ]
        gi_notes = SimpleNamespace(
            current_resin=140,
            max_resin=200,
            remaining_resin_recovery_time=timedelta(hours=8),
            current_realm_currency=2200,
            max_realm_currency=2400,
            remaining_realm_currency_recovery_time=timedelta(hours=6),
            completed_commissions=4,
            max_commissions=4,
            claimed_commission_reward=True,
            remaining_resin_discounts=1,
            max_resin_discounts=3,
            remaining_transformer_recovery_time=timedelta(0),
            max_expeditions=5,
            expeditions=[
                SimpleNamespace(character_icon="https://cdn/fischl.png", status="Finished", remaining_time=timedelta(0)),
                SimpleNamespace(character_icon="https://cdn/bennett.png", status="Ongoing", remaining_time=timedelta(hours=2)),
            ],
        )
        hsr_notes = SimpleNamespace(
            current_stamina=180,
            max_stamina=300,
            stamina_recover_time=timedelta(hours=12),
            accepted_expedition_num=4,
            total_expedition_num=4,
            expeditions=[
                SimpleNamespace(name="Expedição A", status="Ongoing", remaining_time=timedelta(hours=3)),
            ],
            current_train_score=500,
            max_train_score=500,
            current_rogue_score=18000,
            max_rogue_score=18000,
            remaining_weekly_discounts=2,
            max_weekly_discounts=3,
            current_reserve_stamina=640,
            is_reserve_stamina_full=False,
        )
        zzz_notes = SimpleNamespace(
            battery_charge=SimpleNamespace(current=260, max=240, seconds_till_full=0),
            engagement=SimpleNamespace(current=300, max=400),
            scratch_card_completed=False,
            video_store_state="SaleStateDone",
            hollow_zero=SimpleNamespace(bounty_commission=SimpleNamespace(cur_completed=4000, total=8000)),
            weekly_task=SimpleNamespace(cur_point=1200, max_point=2100),
        )

        saved_store = {}

        def fake_save_daily_notes(uid, game_id, nickname, current_energy, max_energy, recovery_time, extra_info):
            saved_store[game_id] = {
                "uid": uid,
                "nickname": nickname,
                "current_energy": current_energy,
                "max_energy": max_energy,
                "recovery_time": recovery_time,
                "extra_info": extra_info,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

        fake_client = MagicMock()
        fake_client.get_game_accounts = AsyncMock(return_value=fake_accounts)
        fake_client.get_genshin_notes = AsyncMock(return_value=gi_notes)
        fake_client.get_starrail_notes = AsyncMock(return_value=hsr_notes)
        fake_client.get_zzz_notes = AsyncMock(return_value=zzz_notes)

        with (
            patch("services.checkin_service.get_cookies", return_value={"ltuid_v2": "1", "ltoken_v2": "x"}),
            patch("services.checkin_service.genshin.Client", return_value=fake_client),
            patch("services.checkin_service.database.save_game_account"),
            patch("services.checkin_service.database.save_daily_notes", side_effect=fake_save_daily_notes),
            patch("services.checkin_service.database.get_cached_daily_notes", side_effect=lambda: saved_store),
        ):
            res = asyncio.run(checkin_service.fetch_realtime_notes())

        # Genshin
        gi_ex = res["genshin"]["extra_info"]
        self.assertEqual(gi_ex["completed_commissions"], 4)
        self.assertTrue(gi_ex["claimed_commission_reward"])
        self.assertEqual(gi_ex["remaining_resin_discounts"], 1)
        self.assertTrue(gi_ex["transformer_available"])
        self.assertEqual(gi_ex["transformer_seconds"], 0)
        self.assertEqual(gi_ex["current_realm_currency"], 2200)
        self.assertIsNotNone(gi_ex["full_at"])
        self.assertEqual(gi_ex["expeditions"][1]["remaining_seconds"], 7200)

        # HSR
        hsr_ex = res["hsr"]["extra_info"]
        self.assertEqual(hsr_ex["current_reserve_stamina"], 640)
        self.assertEqual(hsr_ex["current_train_score"], 500)
        self.assertEqual(hsr_ex["current_rogue_score"], 18000)
        self.assertEqual(hsr_ex["remaining_weekly_discounts"], 2)
        self.assertEqual(hsr_ex["expeditions"][0]["remaining_seconds"], 10800)
        self.assertIsNotNone(hsr_ex["full_at"])

        # ZZZ
        zzz_ex = res["zzz"]["extra_info"]
        self.assertEqual(zzz_ex["engagement"], 300)
        self.assertEqual(zzz_ex["max_engagement"], 400)
        self.assertFalse(zzz_ex["scratch_card_completed"])
        self.assertEqual(zzz_ex["video_store_state"], "SaleStateDone")
        self.assertEqual(zzz_ex["coffee_state"], "overcap")
        self.assertEqual(zzz_ex["hollow_zero_bounty_current"], 4000)
        self.assertIsNone(zzz_ex["full_at"])

    def test_api_notes_endpoint_returns_enriched_payload(self):
        sample = {
            "hsr": {
                "current_energy": 120,
                "max_energy": 300,
                "recovery_time": "64800",
                "recovery_seconds": 64800,
                "full_at": "2026-11-25T07:00:00Z",
                "extra_info": {"current_reserve_stamina": 120, "current_train_score": 500, "max_train_score": 500},
            }
        }
        client = TestClient(app)
        with patch("routers.checkin.fetch_realtime_notes", new=AsyncMock(return_value=sample)):
            r = client.get("/api/notes")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["hsr"]["recovery_seconds"], 64800)
        self.assertEqual(body["hsr"]["full_at"], "2026-11-25T07:00:00Z")

    def test_frontend_daily_notes_js_and_css_contracts(self):
        sync_js = (ROOT_DIR / "static" / "js" / "modules" / "sync_manager.js").read_text(encoding="utf-8")
        self.assertIn("function renderDailyNotesPills", sync_js)
        self.assertIn("function formatEnergyFullAt", sync_js)
        self.assertIn("daily-notes-slot-", sync_js)
        self.assertIn("energy-full-at", sync_js)
        self.assertIn("REVENUE_AVAILABLE", sync_js)
        self.assertIn("WAITING_TO_OPEN", sync_js)

        style_css = (ROOT_DIR / "static" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".energy-full-at", style_css)
        self.assertIn(".dn-pill", style_css)
        self.assertIn(".dn-pill.dn-alert", style_css)
        self.assertIn(".dn-pill.dn-done", style_css)


if __name__ == "__main__":
    unittest.main()
