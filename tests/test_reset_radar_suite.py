import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from server import app
from services import endgame_service


ROOT_DIR = Path(__file__).resolve().parent.parent


class TestResetRadarSuite(unittest.TestCase):
    """Testes unitários offline da Etapa 4: Radar Unificado de Resets na Home."""

    def setUp(self):
        endgame_service.invalidate_endgame_cache()

    def tearDown(self):
        endgame_service.invalidate_endgame_cache()

    def test_compute_server_cycle_resets_before_and_after_0400(self):
        tz_america = timezone(timedelta(hours=-5))

        # Domingo 02:30 (horário do servidor América UTC-5) -> Diário às 04:00 do mesmo dia, Semanal Segunda 04:00
        sunday_0230_srv = datetime(2026, 11, 22, 2, 30, 0, tzinfo=tz_america)
        res_before = endgame_service.compute_server_cycle_resets(
            now_utc=sunday_0230_srv.astimezone(timezone.utc),
            lang="pt",
            server_tz=tz_america,
            tz_label="UTC-5 (América)",
        )
        self.assertEqual(res_before["daily_reset_at"], "2026-11-22T09:00:00Z")
        self.assertEqual(res_before["weekly_reset_at"], "2026-11-23T09:00:00Z")

        # Segunda 04:05 (horário do servidor América UTC-5) -> Diário Terça 04:00, Semanal próxima Segunda 04:00
        monday_0405_srv = datetime(2026, 11, 23, 4, 5, 0, tzinfo=tz_america)
        res_after = endgame_service.compute_server_cycle_resets(
            now_utc=monday_0405_srv.astimezone(timezone.utc),
            lang="pt",
            server_tz=tz_america,
            tz_label="UTC-5 (América)",
        )
        self.assertEqual(res_after["daily_reset_at"], "2026-11-24T09:00:00Z")
        self.assertEqual(res_after["weekly_reset_at"], "2026-11-30T09:00:00Z")

    def test_evaluate_mode_completion_states(self):
        self.assertEqual(endgame_service._evaluate_mode_completion(None)[0], "pending")
        self.assertEqual(
            endgame_service._evaluate_mode_completion({"stars": 4, "max_stars": 4, "teams": [{"name": "Lado 1"}]})[0],
            "completed",
        )
        self.assertEqual(
            endgame_service._evaluate_mode_completion({"stars": 2, "max_stars": 3, "teams": [{"name": "Lado 1"}]})[0],
            "in_progress",
        )
        self.assertEqual(
            endgame_service._evaluate_mode_completion({"stars": None, "max_stars": None, "metric_value": "S", "teams": [{"name": "Lado 1"}]})[0],
            "completed",
        )

    def test_get_unified_reset_radar_aggregates_7_modes_and_sorts_by_urgency(self):
        now = datetime.now(timezone.utc)
        iso_in = lambda hours: (now + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")

        fake_hsr = {
            "modes": [
                {"id": "moc", "stars": 4, "max_stars": 4, "teams": [{"name": "Lado 1"}]},
                {"id": "pure_fiction", "stars": 4, "max_stars": 4, "teams": [{"name": "Lado 1"}]},
                {"id": "apocalyptic_shadow", "stars": 2, "max_stars": 4, "teams": [{"name": "Lado 1"}]},
            ],
            "reset_schedules": [
                {"id": "moc", "name": "Caos da Memória (MoC)", "badge": "MoC", "icon": "/assets/endgame/hsr_moc.png", "reset_at": iso_in(20), "source": "hoyolab"},
                {"id": "pure_fiction", "name": "Ficção Pura", "badge": "PF", "icon": "/assets/endgame/hsr_pure_fiction.png", "reset_at": iso_in(240), "source": "hoyolab"},
                {"id": "apocalyptic_shadow", "name": "Sombra Apocalíptica", "badge": "AS", "icon": "/assets/endgame/hsr_apocalyptic_shadow.png", "reset_at": iso_in(36), "source": "hoyolab"},
            ],
        }
        fake_genshin = {
            "modes": [
                {"id": "spiral_abyss", "stars": 9, "max_stars": 9, "teams": [{"name": "Metade 1"}]},
            ],
            "reset_schedules": [
                {"id": "spiral_abyss", "name": "Abismo Espiral", "badge": "Abyss", "icon": "/assets/endgame/genshin_spiral_abyss.png", "reset_at": iso_in(120), "source": "hoyolab"},
                {"id": "imaginarium_theater", "name": "Teatro Imaginário", "badge": "Teatro", "icon": "/assets/endgame/genshin_imaginarium_theater.png", "reset_at": iso_in(18), "source": "hoyolab"},
            ],
        }
        fake_zzz = {
            "modes": [
                {"id": "shiyu_defense", "stars": None, "max_stars": None, "metric_value": "S", "teams": [{"name": "Lado 1"}]},
            ],
            "reset_schedules": [
                {"id": "shiyu_defense", "name": "Defesa Shiyu", "badge": "Shiyu", "icon": "/assets/endgame/zzz_shiyu_defense.png", "reset_at": iso_in(96), "source": "hoyolab"},
                {"id": "deadly_assault", "name": "Assalto Mortal", "badge": "DA", "icon": "/assets/endgame/zzz_deadly_assault.png", "reset_at": iso_in(150), "source": "estimated"},
            ],
        }

        async def fake_get_endgame(game_id, lang="pt"):
            return {"hsr": fake_hsr, "genshin": fake_genshin, "zzz": fake_zzz}[game_id]

        with (
            patch("services.endgame_service.get_endgame", side_effect=fake_get_endgame),
            patch("services.endgame_service.database.get_active_uid", return_value="600156277"),
        ):
            radar = asyncio.run(endgame_service.get_unified_reset_radar(lang="pt"))

        self.assertEqual(radar["status"], "success")
        self.assertEqual(len(radar["items"]), 7)
        self.assertEqual(radar["summary"]["total_modes"], 7)
        self.assertEqual(radar["summary"]["completed_count"], 4)
        self.assertEqual(radar["summary"]["pending_count"], 3)
        self.assertEqual(radar["summary"]["urgent_pending_count"], 2)

        # Urgentes pendentes (<= 72h e não concluídos) devem liderar em ordem de menor tempo:
        # 1º Teatro Imaginário (18h, pendente), 2º Sombra Apocalíptica (36h, in_progress)
        self.assertEqual(radar["items"][0]["id"], "imaginarium_theater")
        self.assertTrue(radar["items"][0]["is_urgent_pending"])
        self.assertEqual(radar["items"][1]["id"], "apocalyptic_shadow")
        self.assertTrue(radar["items"][1]["is_urgent_pending"])

        # Em seguida os demais ordenados por menor tempo restante (MoC 20h já concluído vem antes de Shiyu 96h)
        self.assertEqual(radar["items"][2]["id"], "moc")
        self.assertEqual(radar["items"][2]["status"], "completed")
        self.assertFalse(radar["items"][2]["is_urgent_pending"])

    def test_reset_radar_endpoint_contract(self):
        sample_radar = {
            "status": "success",
            "generated_at": "2026-11-24T13:00:00Z",
            "server_resets": {
                "daily_reset_at": "2026-11-25T09:00:00Z",
                "weekly_reset_at": "2026-11-30T09:00:00Z",
                "server_tz_label": "UTC-5 (América)",
            },
            "summary": {"total_modes": 1, "completed_count": 0, "pending_count": 1, "urgent_pending_count": 1},
            "items": [
                {
                    "game_id": "hsr",
                    "game_label": "HSR",
                    "id": "moc",
                    "name": "Caos da Memória (MoC)",
                    "badge": "MoC",
                    "icon": "/assets/endgame/hsr_moc.png",
                    "begin_at": None,
                    "reset_at": "2026-11-25T09:00:00Z",
                    "source": "hoyolab",
                    "status": "pending",
                    "stars": None,
                    "max_stars": None,
                    "metric_value": None,
                    "has_record": False,
                    "seconds_remaining": 36000,
                    "is_urgent_pending": True,
                }
            ],
        }
        client = TestClient(app)
        with patch("routers.endgame.get_unified_reset_radar", new=AsyncMock(return_value=sample_radar)):
            resp = client.get("/api/endgame/reset-radar?lang=pt")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["summary"]["urgent_pending_count"], 1)
        self.assertEqual(body["items"][0]["id"], "moc")
        self.assertIn("daily_reset_at", body["server_resets"])
        self.assertIn("weekly_reset_at", body["server_resets"])

    def test_build_active_banner_resets_groups_by_end_time_and_flags_under_48h(self):
        now = datetime(2026, 11, 24, 13, 0, 0, tzinfo=timezone.utc)
        fake_defaults = {
            "genshin": {
                "patch_info": "Patch 7.2 Phase 1",
                "banner_time": "20:00",
                "available_banners": [
                    {
                        "character_name": "Mitya",
                        "is_primary": True,
                        "patch_label": "Patch 7.2 Phase 1",
                        "duration_type": "phase_1",
                        "phase": 1,
                        "banner_time": "20:00",
                        "end_date": "2026-11-24",
                        "end_at": "2026-11-24T23:00:00Z",
                        "character_info": {"icon": "/api/proxy_image?url=mitya"},
                    },
                    {
                        "character_name": "Furina",
                        "is_primary": False,
                        "patch_label": "Patch 7.2 Phase 1",
                        "duration_type": "phase_1",
                        "phase": 1,
                        "banner_time": "20:00",
                        "end_date": "2026-11-24",
                        "end_at": "2026-11-24T23:00:00Z",
                        "character_info": {"icon": "/api/proxy_image?url=furina"},
                    },
                ],
            },
            "hsr": {
                "patch_info": "Patch 4.7",
                "banner_time": "14:00",
                "available_banners": [
                    {
                        "character_name": "Aha",
                        "is_primary": True,
                        "patch_label": "Patch 4.7",
                        "duration_type": "full_patch",
                        "phase": None,
                        "banner_time": "23:30",
                        "end_date": "2026-12-22",
                        "end_at": "2026-12-23T02:30:00Z",
                        "character_info": {"icon": "/api/proxy_image?url=aha"},
                    },
                    {
                        "character_name": "Sparxie",
                        "is_primary": False,
                        "patch_label": "Patch 4.7 Phase 1",
                        "duration_type": "phase_1",
                        "phase": 1,
                        "banner_time": "14:00",
                        "end_date": "2026-12-02",
                        "end_at": "2026-12-02T17:00:00Z",
                        "character_info": {"icon": "/api/proxy_image?url=sparxie"},
                    },
                    {
                        "character_name": "Gilgamesh",
                        "is_primary": False,
                        "patch_label": "Patch 4.4",
                        "duration_type": "collab",
                        "phase": None,
                        "banner_time": "23:30",
                        "end_date": None,
                        "end_at": None,
                        "character_info": {"icon": "/assets/banners/gil.webp"},
                    },
                ],
            },
            "zzz": {
                "patch_info": "Patch 3.3 Phase 2",
                "banner_time": "23:30",
                "available_banners": [
                    {
                        "character_name": "Severian",
                        "is_primary": True,
                        "patch_label": "Patch 3.3 Phase 2",
                        "duration_type": "phase_2",
                        "phase": 2,
                        "banner_time": "23:30",
                        "end_date": "2026-12-01",
                        "end_at": "2026-12-02T02:30:00Z",
                        "character_info": {"icon": "/api/proxy_image?url=sev"},
                    }
                ],
            },
        }

        with patch(
            "services.gacha_service.get_gacha_simulator_defaults",
            side_effect=lambda gid, banner_type="character": fake_defaults[gid],
        ):
            banners = endgame_service._build_active_banner_resets(now)

        # 4 grupos temporizados (collab sem end_at excluído; HSR full_patch separado de HSR phase_1)
        self.assertEqual(len(banners), 4)
        # 1º: Genshin Phase 1 (10h restantes -> is_ending_soon=True, agrupando Mitya + Furina)
        self.assertEqual(banners[0]["game_id"], "genshin")
        self.assertEqual(banners[0]["title"], "Mitya · Furina")
        self.assertEqual(banners[0]["primary_character"], "Mitya")
        self.assertTrue(banners[0]["is_ending_soon"])
        # 2º: ZZZ Phase 2 (1 dez), 3º: HSR Phase 1 (2 dez), 4º: HSR Full Patch (22 dez)
        self.assertEqual([b["game_id"] for b in banners[1:]], ["zzz", "hsr", "hsr"])
        self.assertEqual(banners[2]["duration_type"], "phase_1")
        self.assertEqual(banners[3]["duration_type"], "full_patch")
        self.assertFalse(banners[3]["is_ending_soon"])

    def test_prydwen_fallback_icons_use_valid_hsr_path_clean_slugs_and_zzz_card(self):
        from services.gacha_tracker_service import get_gacha_item_icon
        from services.media_service import get_raw_url

        sw_url = get_raw_url(get_gacha_item_icon("hsr", "Silver Wolf • Lv. 999", db_icons_map={}))
        self.assertEqual(
            sw_url,
            "https://cdn.prydwen.gg/images/honkai-star-rail/characters/silver-wolf-lv-999_icon.webp",
        )
        aha_url = get_raw_url(get_gacha_item_icon("hsr", "Aha", db_icons_map={}))
        self.assertEqual(
            aha_url,
            "https://cdn.prydwen.gg/images/honkai-star-rail/characters/aha_icon.webp",
        )
        sev_url = get_raw_url(get_gacha_item_icon("zzz", "Severian", db_icons_map={}))
        self.assertEqual(
            sev_url,
            "https://cdn.prydwen.gg/images/zenless-zone-zero/characters/severian_card.webp",
        )

    def test_legacy_banner_cache_triggers_schema_upgrade_from_bundle(self):
        import json, os, tempfile
        from services import gacha_service

        legacy_payload = {
            "genshin": {
                "game_id": "genshin",
                "patch_info": "Patch 7.2 Phase 1 Nov 4, 2026 – Nov 24, 2026",
                "banners": [{"character_name": "Mitya", "is_primary": True}],
                "last_updated": "2026-11-18T10:00:00",
            }
        }
        bundled_payload = {
            "genshin": {
                "game_id": "genshin",
                "patch_info": "Patch 7.2 Phase 1 Nov 4, 2026 – Nov 24, 2026",
                "banners": [
                    {
                        "character_name": "Mitya",
                        "is_primary": True,
                        "start_date": "2026-11-04",
                        "end_date": "2026-11-24",
                        "phase": 1,
                        "duration_type": "phase_1",
                    }
                ],
                "last_updated": "2026-11-24T10:00:00",
            }
        }
        self.assertTrue(gacha_service._banners_need_schema_upgrade(legacy_payload, "genshin"))
        self.assertFalse(gacha_service._banners_need_schema_upgrade(bundled_payload, "genshin"))

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "appdata")
            bundle_dir = os.path.join(tmpdir, "bundle")
            os.makedirs(os.path.join(data_dir, "static_data"), exist_ok=True)
            os.makedirs(os.path.join(bundle_dir, "static_data"), exist_ok=True)
            data_file = os.path.join(data_dir, "static_data", "current_banners.json")
            bundle_file = os.path.join(bundle_dir, "static_data", "current_banners.json")
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(legacy_payload, f)
            with open(bundle_file, "w", encoding="utf-8") as f:
                json.dump(bundled_payload, f)

            with (
                patch("services.gacha_service._resolve_static_file", return_value=data_file),
                patch("services.gacha_service.get_bundle_root", return_value=bundle_dir),
                patch("services.gacha_service.get_data_path", return_value=data_file),
            ):
                resolved = gacha_service.get_current_banners("genshin")

            self.assertEqual(resolved["banners"][0]["duration_type"], "phase_1")
            self.assertEqual(resolved["banners"][0]["end_date"], "2026-11-24")
            with open(data_file, "r", encoding="utf-8") as f:
                migrated = json.load(f)
            self.assertEqual(migrated["genshin"]["banners"][0]["duration_type"], "phase_1")

    def test_frontend_home_reset_radar_markup_js_and_css(self):
        html = (ROOT_DIR / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="home-reset-radar-card"', html)
        self.assertIn('id="home-reset-radar-strip"', html)
        self.assertIn('id="home-banner-reset-section"', html)
        self.assertIn('id="home-banner-reset-strip"', html)
        self.assertIn('id="radar-daily-countdown"', html)
        self.assertIn('id="radar-weekly-countdown"', html)

        endgame_js = (ROOT_DIR / "static" / "js" / "modules" / "endgame.js").read_text(encoding="utf-8")
        self.assertIn("function loadHomeResetRadar", endgame_js)
        self.assertIn("function renderHomeResetRadar", endgame_js)
        self.assertIn("function renderHomeBannerResets", endgame_js)
        self.assertIn("function navigateToBannerSimulator", endgame_js)
        self.assertIn("function navigateToEndgameMode", endgame_js)
        self.assertIn("/api/endgame/reset-radar", endgame_js)

        gacha_js = (ROOT_DIR / "static" / "js" / "modules" / "gacha_sim.js").read_text(encoding="utf-8")
        self.assertIn("window.prefillGachaBannerTarget", gacha_js)

        endgame_css = (ROOT_DIR / "static" / "css" / "endgame_strategy.css").read_text(encoding="utf-8")
        self.assertIn(".home-reset-radar-card", endgame_css)
        self.assertIn(".reset-radar-item.is-urgent-pending", endgame_css)
        self.assertIn(".reset-radar-strip", endgame_css)
        self.assertIn(".banner-reset-strip", endgame_css)
        self.assertIn(".banner-reset-item.is-ending-soon", endgame_css)


if __name__ == "__main__":
    unittest.main()
