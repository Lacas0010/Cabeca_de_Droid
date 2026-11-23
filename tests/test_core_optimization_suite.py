import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import core.security as core_security
import core.static_cache as static_cache
import database
import routers.system as system_router
import security_vault
import server
import updater


class TestCoreOptimizationSuite(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp_dir.name)
        self.orig_db_name = database.DATABASE_NAME
        database.DATABASE_NAME = str(self.tmp_path / "test_opt.db")
        database.invalidate_security_settings_cache()
        database.init_db()
        self.client = TestClient(server.app)

    def tearDown(self) -> None:
        database.DATABASE_NAME = self.orig_db_name
        database.invalidate_security_settings_cache()
        self.tmp_dir.cleanup()

    # 1. Security Vault & Config Masking
    def test_config_encryption_roundtrip_and_legacy_migration(self) -> None:
        enc_path = str(self.tmp_path / "config.enc")
        legacy_path = str(self.tmp_path / "config.json")
        secret_cfg = {
            "notifications_enabled": True,
            "discord_webhook_url": "https://discord.com/api/webhooks/111/secret_hook",
            "telegram_bot_token": "999999:SECRET_TG_TOKEN",
        }
        with open(legacy_path, "w", encoding="utf-8") as f:
            json.dump(secret_cfg, f)

        loaded = security_vault.load_secure_config(filepath=enc_path, legacy_file=legacy_path)
        self.assertEqual(loaded["discord_webhook_url"], secret_cfg["discord_webhook_url"])
        self.assertEqual(loaded["telegram_bot_token"], secret_cfg["telegram_bot_token"])
        self.assertFalse(os.path.exists(legacy_path))
        self.assertTrue(os.path.exists(enc_path))

        raw_bytes = Path(enc_path).read_bytes()
        self.assertNotIn(b"secret_hook", raw_bytes)
        self.assertNotIn(b"SECRET_TG_TOKEN", raw_bytes)

        loaded_again = security_vault.load_secure_config(filepath=enc_path, legacy_file=legacy_path)
        self.assertEqual(loaded_again["discord_webhook_url"], secret_cfg["discord_webhook_url"])

    def test_config_masks_discord_over_lan_and_preserves_masked_secrets_on_save(self) -> None:
        enc_path = str(self.tmp_path / "cfg_route.enc")
        legacy_path = str(self.tmp_path / "cfg_route.json")

        with (
            patch.object(security_vault, "CONFIG_ENC_FILE", enc_path),
            patch.object(security_vault, "CONFIG_LEGACY_FILE", legacy_path),
            patch("database.is_lan_access_allowed", return_value=True),
        ):
            save_res = self.client.post(
                "/api/config",
                json={
                    "discord_webhook_url": "https://discord.com/api/webhooks/123456/real_secret_token",
                    "telegram_bot_token": "123456:REAL_TG_TOKEN",
                },
            )
            self.assertEqual(save_res.status_code, 200)

            token = core_security.create_session()
            lan_client = TestClient(server.app, client=("192.168.1.50", 50123))
            lan_get = lan_client.get("/api/config", headers={"X-Session-Token": token})
            self.assertEqual(lan_get.status_code, 200)
            lan_data = lan_get.json()
            self.assertIn("***", lan_data["discord_webhook_url"])
            self.assertNotIn("real_secret_token", lan_data["discord_webhook_url"])
            self.assertIn("***", lan_data["telegram_bot_token"])
            self.assertNotIn("REAL_TG_TOKEN", lan_data["telegram_bot_token"])

            # Posting masked values back must preserve stored secrets
            resave = lan_client.post(
                "/api/config",
                headers={"X-Session-Token": token},
                json={
                    "notifications_enabled": True,
                    "discord_webhook_url": lan_data["discord_webhook_url"],
                    "telegram_bot_token": lan_data["telegram_bot_token"],
                },
            )
            self.assertEqual(resave.status_code, 200)
            stored = security_vault.load_secure_config()
            self.assertEqual(stored["discord_webhook_url"], "https://discord.com/api/webhooks/123456/real_secret_token")
            self.assertEqual(stored["telegram_bot_token"], "123456:REAL_TG_TOKEN")

    # 2. Core Security & LAN Mutating Endpoint Auth
    def test_is_loopback_ip_and_lan_mutating_endpoints_require_session(self) -> None:
        self.assertTrue(core_security.is_loopback_ip("127.0.0.1"))
        self.assertTrue(core_security.is_loopback_ip("::1"))
        self.assertTrue(core_security.is_loopback_ip("localhost"))
        self.assertTrue(core_security.is_loopback_ip("testclient"))
        self.assertFalse(core_security.is_loopback_ip("192.168.1.10"))

        with patch("database.is_lan_access_allowed", return_value=True):
            lan_client = TestClient(server.app, client=("192.168.1.99", 45678))
            protected_calls = [
                ("POST", "/api/security/pin/set", {"pin": "1234"}),
                ("POST", "/api/auth/manual_cookies", {"cookie_string": "ltuid_v2=1; ltoken_v2=2"}),
                ("POST", "/api/notifications/test", {}),
                ("DELETE", "/api/accounts/123456", None),
                ("POST", "/api/updater/start", {}),
                ("POST", "/api/reset-data", None),
            ]
            for method, url, body in protected_calls:
                res = lan_client.request(method, url, json=body, headers={"Origin": "http://localhost:8000"})
                self.assertEqual(res.status_code, 401, f"{method} {url} should require LAN session")
                # CORSMiddleware must be outermost so 401 still includes CORS headers
                self.assertIn("access-control-allow-origin", res.headers)

            # With valid session, /api/updater/start (dev mode) proceeds
            token = core_security.create_session()
            with patch("updater.is_app_frozen", return_value=False):
                ok_res = lan_client.post(
                    "/api/updater/start",
                    json={"target_version": "9.9.9"},
                    headers={"X-Session-Token": token},
                )
                self.assertEqual(ok_res.status_code, 200)

    # 3. Updater ZipSlip & Expected EXE Resolution
    def test_updater_zipslip_and_expected_exe_preference(self) -> None:
        extract_dir = self.tmp_path / "extracted"
        sibling_evil = self.tmp_path / "extracted_evil"
        sibling_evil.mkdir()

        bad_zip = self.tmp_path / "sibling_bypass.zip"
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("../extracted_evil/evil.exe", b"bad")
        with self.assertRaises(ValueError):
            updater.safe_extract_zip(bad_zip, extract_dir)

        good_zip = self.tmp_path / "good.zip"
        with zipfile.ZipFile(good_zip, "w") as zf:
            zf.writestr("app/aaa_helper.exe", b"helper")
            zf.writestr("app/Cabeca_de_Droid.exe", b"main")
        root = updater.safe_extract_zip(good_zip, self.tmp_path / "valid_out")
        resolved_dir = updater.resolve_extracted_payload_dir(root)
        self.assertTrue((resolved_dir / "Cabeca_de_Droid.exe").is_file())

    # 4. System Router: /api/reset-data methods + SSRF + size cap + thread-local session
    def test_reset_data_rejects_get_and_allows_post_delete(self) -> None:
        get_res = self.client.get("/api/reset-data")
        self.assertIn(get_res.status_code, (404, 405))

        with (
            patch("routers.system.get_data_path", side_effect=lambda f: str(self.tmp_path / f)),
            patch("database.reset_database") as mock_reset,
        ):
            (self.tmp_path / "hsr").mkdir(exist_ok=True)
            post_res = self.client.post("/api/reset-data")
            self.assertEqual(post_res.status_code, 200)
            self.assertFalse((self.tmp_path / "hsr").exists())
            mock_reset.assert_called_once()

            mock_reset.reset_mock()
            del_res = self.client.delete("/api/reset-data")
            self.assertEqual(del_res.status_code, 200)
            mock_reset.assert_called_once()

    def test_proxy_image_blocks_ssrf_caps_size_and_caches_atomically(self) -> None:
        for ssrf_url in (
            "http://127.0.0.1/secret.png",
            "http://localhost/secret.png",
            "http://169.254.169.254/latest/meta-data/",
            "http://10.0.0.5/internal.png",
            "http://[::1]/secret.png",
        ):
            res = self.client.get("/api/proxy_image", params={"url": ssrf_url})
            self.assertEqual(res.status_code, 400, f"Expected 400 SSRF block for {ssrf_url}")

        # DNS resolving to private IP must also be blocked
        with patch("routers.system.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("192.168.0.10", 0))]):
            dns_res = self.client.get("/api/proxy_image", params={"url": "https://evil.example.com/a.png"})
            self.assertEqual(dns_res.status_code, 400)

        # Oversized Content-Length rejected with 413
        oversized_resp = MagicMock()
        oversized_resp.status_code = 200
        oversized_resp.headers = {"Content-Length": str(system_router.MAX_PROXY_IMAGE_BYTES + 1)}
        oversized_resp.content = b""
        oversized_resp.url = "https://cdn.example.com/huge.png"
        fake_session = MagicMock()
        fake_session.get.return_value = oversized_resp

        with (
            patch.object(system_router, "_IMAGE_CACHE_DIR", str(self.tmp_path / "img_cache")),
            patch("routers.system.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 0))]),
            patch("routers.system._get_proxy_session", return_value=fake_session),
        ):
            res_413 = self.client.get("/api/proxy_image", params={"url": "https://cdn.example.com/huge.png"})
            self.assertEqual(res_413.status_code, 413)

        # Valid image (>100 bytes after WebP encode) caches atomically and hits on second request
        from PIL import Image

        img = Image.new("RGBA", (128, 128))
        pixels = [(x * 2 % 256, y * 3 % 256, (x ^ y) % 256, 255) for y in range(128) for x in range(128)]
        img.putdata(pixels)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        valid_png = buf.getvalue()

        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.headers = {"Content-Length": str(len(valid_png))}
        ok_resp.content = valid_png
        ok_resp.url = "https://cdn.example.com/icon.png"
        fake_session.get.return_value = ok_resp

        with (
            patch.object(system_router, "_IMAGE_CACHE_DIR", str(self.tmp_path / "img_cache")),
            patch("routers.system.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 0))]),
            patch("routers.system._get_proxy_session", return_value=fake_session),
        ):
            miss_res = self.client.get("/api/proxy_image", params={"url": "https://cdn.example.com/icon.png"})
            self.assertEqual(miss_res.status_code, 200)
            self.assertEqual(miss_res.headers.get("x-cache-status"), "MISS")

            hit_res = self.client.get("/api/proxy_image", params={"url": "https://cdn.example.com/icon.png"})
            self.assertEqual(hit_res.status_code, 200)
            self.assertEqual(hit_res.headers.get("x-cache-status"), "HIT")

    def test_proxy_session_is_thread_local(self) -> None:
        sessions = []
        barrier = threading.Barrier(2)

        def _worker():
            sess = system_router._get_proxy_session()
            sessions.append(sess)
            barrier.wait(timeout=5)

        t1 = threading.Thread(target=_worker)
        t2 = threading.Thread(target=_worker)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        self.assertEqual(len(sessions), 2)
        self.assertIsNot(sessions[0], sessions[1])

    # 5. Database Optimizations, Schema Version, Batch & Cleanup
    def test_database_does_not_init_on_import_sets_wal_indexes_and_closes_connections(self) -> None:
        # Check user_version, WAL, and composite indexes
        with database.get_connection() as conn:
            ver = conn.execute("PRAGMA user_version").fetchone()[0]
            self.assertEqual(ver, database.CURRENT_DB_VERSION)
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            self.assertEqual(str(mode).lower(), "wal")
            indexes = {
                r[0]
                for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
            }
            self.assertIn("idx_gacha_pulls_game_uid_time", indexes)
            self.assertIn("idx_snapshots_uid_created", indexes)

        # Connection closes explicitly when exiting context
        captured_conn = None
        with database.get_connection() as conn:
            captured_conn = conn
        with self.assertRaises(sqlite3.ProgrammingError):
            captured_conn.execute("SELECT 1")

        # Fresh subprocess importing database must not create hoyo_app.db at import time
        fresh_dir = self.tmp_path / "fresh_import_data"
        fresh_dir.mkdir(exist_ok=True)
        env = dict(os.environ, CABECA_DE_DROID_DATA_DIR=str(fresh_dir))
        proc = subprocess.run(
            [sys.executable, "-c", "import database; print(database.DATABASE_NAME)"],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("hoyo_app.db", proc.stdout)
        self.assertFalse((fresh_dir / "hoyo_app.db").exists())

    def test_reset_database_cleans_all_15_tables_and_delete_account_cleans_orphans(self) -> None:
        uid = "900111222"
        database.save_game_account(uid, "hsr", "Tester", 70)
        database.set_active_account("hsr", uid)
        database.save_character(uid, "hsr", "Acheron", 80, 5, "E0", "Lightning", "", "Na Noite", 80, 1, "", "")
        database.save_relics_batch(
            uid,
            "Acheron",
            [
                {"name": "Piece 1", "slot": "Cabeça", "main_stat": "PV", "sub_stats": "CRIT", "icon": ""},
                {"name": "Piece 2", "slot": "Mãos", "main_stat": "ATQ", "sub_stats": "SPD", "icon": ""},
            ],
            clear_existing=True,
        )
        database.save_checkin_log("hsr", uid, "ok", "checked")
        database.save_code_redemption("hsr", uid, "CODE1", "success", "ok")
        database.save_chat_message("hsr", "user", "msg 1")
        database.save_chat_message("hsr", "assistant", "msg 2")
        database.save_chat_message("hsr", "user", "msg 3")
        database.save_static_data_manifest("hsr", "1.0", 50, "success", "seed")
        database.set_farm_task_completed("2026-11-19", "hsr", "task1", True)
        database.save_gacha_goal("hsr", "Acheron", "E2", 10, 0, False, 21, False, 50.0, 100)
        database.save_gacha_pulls(
            "hsr",
            uid,
            [
                {"name": "Flechas", "rarity": 3, "time": "2026-01-01 00:00:00", "gacha_type": "11"},
                {"name": "Flechas", "rarity": 3, "time": "2026-01-01 00:00:00", "gacha_type": "11"},
            ],
        )
        with database.get_connection() as conn:
            conn.execute(
                "INSERT INTO account_snapshots (uid, game_id, character_count, five_star_count, average_build_score, snapshot_json, created_at) VALUES (?, ?, 1, 1, 80.0, '{}', '2026-01-01 00:00:00')",
                (uid, "hsr"),
            )

        # Latest 2 chat messages returned chronologically
        latest_chat = database.get_chat_history("hsr", limit=2)
        self.assertEqual([m["content"] for m in latest_chat], ["msg 2", "msg 3"])

        # Two identical pulls in same second without id both saved
        self.assertEqual(len(database.get_gacha_pulls("hsr", uid=uid)), 2)

        # delete_account_profile removes snapshots, checkin logs, promo_code_history orphans
        database.delete_account_profile(uid)
        with database.get_connection() as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM account_snapshots WHERE uid = ?", (uid,)).fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM daily_checkin_logs WHERE uid = ?", (uid,)).fetchone()[0], 0)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM promo_code_history WHERE uid = ?", (uid,)).fetchone()[0], 0)

        # reset_database clears all remaining tables too
        database.reset_database()
        with database.get_connection() as conn:
            for tbl in (
                "game_accounts",
                "active_accounts",
                "characters",
                "character_relics",
                "daily_notes_cache",
                "daily_checkin_logs",
                "account_snapshots",
                "endgame_records",
                "promo_code_history",
                "static_data_manifests",
                "daily_farm_tasks_completed",
                "gacha_forecast_goals",
                "chat_history",
                "gacha_pulls_history",
            ):
                cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
                self.assertEqual(cnt, 0, f"Table {tbl} should be empty after reset_database()")

    def test_security_settings_memory_cache_invalidation(self) -> None:
        s1 = database.get_security_settings()
        self.assertFalse(s1["pin_enabled"])
        with patch("database.get_connection", side_effect=AssertionError("Should read from memory cache")):
            s2 = database.get_security_settings()
            self.assertFalse(s2["pin_enabled"])

        self.assertTrue(database.set_security_pin("4321"))
        s3 = database.get_security_settings()
        self.assertTrue(s3["pin_enabled"])

        database.set_lan_access(True)
        self.assertTrue(database.get_security_settings()["allow_lan_access"])

        self.assertTrue(database.disable_security_pin("4321"))
        self.assertFalse(database.get_security_settings()["pin_enabled"])

    # 6. Static Asset Cache TTL
    def test_static_cache_ttl_and_invalidation(self) -> None:
        static_dir = self.tmp_path / "static"
        mods_dir = static_dir / "js" / "modules"
        mods_dir.mkdir(parents=True)
        app_js = static_dir / "js" / "app.js"
        mod_js = mods_dir / "i18n.js"
        app_js.write_text('import "./modules/i18n.js";', encoding="utf-8")
        mod_js.write_text("export const x = 1;", encoding="utf-8")

        static_cache.invalidate_static_cache()
        tok1 = static_cache.get_asset_version_token(str(static_dir), "js/app.js")
        with patch("core.static_cache.os.scandir", side_effect=AssertionError("Should hit TTL cache")):
            tok2 = static_cache.get_asset_version_token(str(static_dir), "js/app.js")
        self.assertEqual(tok1, tok2)

        static_cache.invalidate_static_cache()
        tok3 = static_cache.get_asset_version_token(str(static_dir), "js/app.js")
        self.assertEqual(tok1, tok3)

    def test_static_data_sync_invalidates_roster_cache(self) -> None:
        mock_results = {"hsr": {"character_count": 10, "status": "success", "source": "seed"}}
        with (
            patch("routers.static_data.static_data_manager.sync_upstream_data", return_value=mock_results) as mock_sync,
            patch("routers.static_data.database.save_static_data_manifests") as mock_save,
            patch("routers.static_data.invalidate_roster_cache") as mock_inv,
            patch("scrapers.scraper_prydwen.PrydwenScraper.get_current_banners", return_value={}),
        ):
            res = self.client.post("/api/static-data/sync", json={"game_id": "hsr"})
            self.assertEqual(res.status_code, 200)
            mock_sync.assert_called_once_with("hsr")
            mock_save.assert_called_once_with(mock_results)
            mock_inv.assert_called_once_with("hsr")


if __name__ == "__main__":
    unittest.main()
