import os
import sys
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import auth
import build
from core import paths


class TestPackagingPaths(unittest.TestCase):
    def setUp(self):
        self._orig_env = os.environ.get("CABECA_DE_DROID_DATA_DIR")

    def tearDown(self):
        if self._orig_env is None:
            os.environ.pop("CABECA_DE_DROID_DATA_DIR", None)
        else:
            os.environ["CABECA_DE_DROID_DATA_DIR"] = self._orig_env

    def test_dev_mode_uses_project_root(self):
        os.environ.pop("CABECA_DE_DROID_DATA_DIR", None)
        with patch.object(sys, "frozen", False, create=True):
            self.assertFalse(paths.is_frozen())
            self.assertEqual(paths.get_data_dir(), paths.PROJECT_ROOT)
            self.assertEqual(paths.get_bundle_root(), paths.PROJECT_ROOT)

    def test_frozen_windows_uses_appdata_not_meipass(self):
        os.environ.pop("CABECA_DE_DROID_DATA_DIR", None)
        with tempfile.TemporaryDirectory() as tmpdir:
            meipass_dir = os.path.join(tmpdir, "meipass_tmp")
            appdata_dir = os.path.join(tmpdir, "AppDataRoaming")
            os.makedirs(meipass_dir, exist_ok=True)
            os.makedirs(appdata_dir, exist_ok=True)

            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "_MEIPASS", meipass_dir, create=True),
                patch.object(paths.sys, "platform", "win32"),
                patch.dict(os.environ, {"APPDATA": appdata_dir}, clear=False),
            ):
                self.assertTrue(paths.is_frozen())
                data_dir = paths.get_data_dir()
                expected = os.path.abspath(os.path.join(appdata_dir, paths.APP_NAME))
                self.assertEqual(data_dir, expected)
                self.assertNotEqual(data_dir, meipass_dir)
                self.assertTrue(os.path.isdir(data_dir))

                # Bundled read-only static dir falls back to _MEIPASS when not overridden
                static_path = paths.get_resource_path("static")
                self.assertEqual(static_path, os.path.join(meipass_dir, "static"))

                # Writable override inside data_dir takes precedence over _MEIPASS
                custom_manifest_dir = os.path.join(data_dir, "static_data")
                os.makedirs(custom_manifest_dir, exist_ok=True)
                custom_manifest = os.path.join(custom_manifest_dir, "hsr_manifest.json")
                with open(custom_manifest, "w", encoding="utf-8") as f:
                    f.write("{}")

                resolved = paths.get_resource_path(os.path.join("static_data", "hsr_manifest.json"))
                self.assertEqual(resolved, custom_manifest)

    def test_seed_bundled_resources_copies_missing_without_overwriting(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            meipass_dir = os.path.join(tmpdir, "meipass")
            appdata_dir = os.path.join(tmpdir, "appdata")
            os.makedirs(os.path.join(meipass_dir, "static_data"), exist_ok=True)
            os.makedirs(os.path.join(appdata_dir, paths.APP_NAME, "static_data"), exist_ok=True)

            bundled_a = os.path.join(meipass_dir, "static_data", "a.json")
            bundled_b = os.path.join(meipass_dir, "static_data", "b.json")
            existing_b = os.path.join(appdata_dir, paths.APP_NAME, "static_data", "b.json")

            with open(bundled_a, "w", encoding="utf-8") as f:
                f.write('{"seeded": true}')
            with open(bundled_b, "w", encoding="utf-8") as f:
                f.write('{"stale": true}')
            with open(existing_b, "w", encoding="utf-8") as f:
                f.write('{"user_synced": true}')

            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "_MEIPASS", meipass_dir, create=True),
                patch.object(paths.sys, "platform", "win32"),
                patch.dict(os.environ, {"APPDATA": appdata_dir}, clear=False),
            ):
                os.environ.pop("CABECA_DE_DROID_DATA_DIR", None)
                paths.seed_bundled_resources(["static_data"])

            seeded_a = os.path.join(appdata_dir, paths.APP_NAME, "static_data", "a.json")
            self.assertTrue(os.path.isfile(seeded_a))
            with open(existing_b, "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), '{"user_synced": true}')


class TestBuildAndReleaseConfig(unittest.TestCase):
    def test_package_zip_creates_clean_archive(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            fake_exe = tmp / "Cabeca_de_Droid.exe"
            fake_exe.write_bytes(b"MZ-TEST")
            out_zip = tmp / "Cabeca_de_Droid-Windows-x64.zip"

            result = build.package_zip(fake_exe, out_zip)
            self.assertEqual(result, out_zip)
            self.assertTrue(out_zip.is_file())

            with zipfile.ZipFile(out_zip, "r") as zf:
                names = set(zf.namelist())
                self.assertIn("Cabeca_de_Droid.exe", names)
                if (build.ROOT_DIR / ".env.example").is_file():
                    self.assertIn(".env.example", names)

    def test_release_workflow_contains_required_triggers_and_actions(self):
        wf_path = build.ROOT_DIR / ".github" / "workflows" / "release.yml"
        self.assertTrue(wf_path.is_file(), "Workflow release.yml não encontrado")
        content = wf_path.read_text(encoding="utf-8")
        self.assertIn("windows-latest", content)
        self.assertIn("v*.*.*", content)
        self.assertIn("workflow_dispatch", content)
        self.assertIn("contents: write", content)
        self.assertIn("softprops/action-gh-release@v2", content)
        self.assertIn("generate_release_notes: true", content)
        self.assertIn("dist/Cabeca_de_Droid-Windows-x64.zip", content)


class TestPlaywrightLoginFallbackAndSettingsLayout(unittest.TestCase):
    def test_launch_login_browser_falls_back_to_system_msedge_when_bundled_missing(self):
        import asyncio

        async def _run():
            fake_browser = MagicMock()
            fake_p = MagicMock()
            fake_p.chromium.executable_path = "/nonexistent/ms-playwright/chromium-1255/chrome.exe"

            async def fake_launch(*args, **kwargs):
                if kwargs.get("channel") == "chrome":
                    raise RuntimeError("Chrome not found")
                if kwargs.get("channel") == "msedge":
                    return fake_browser
                raise RuntimeError("Unexpected launch call")

            fake_p.chromium.launch = AsyncMock(side_effect=fake_launch)
            browser = await auth._launch_login_browser(fake_p)
            self.assertIs(browser, fake_browser)
            calls = [c.kwargs for c in fake_p.chromium.launch.call_args_list]
            self.assertEqual(
                calls,
                [
                    {"channel": "chrome", "headless": False},
                    {"channel": "msedge", "headless": False},
                ],
            )

        asyncio.run(_run())

    def test_launch_login_browser_uses_bundled_when_present(self):
        import asyncio

        async def _run():
            with tempfile.NamedTemporaryFile() as tmp_exe:
                fake_browser = MagicMock()
                fake_p = MagicMock()
                fake_p.chromium.executable_path = tmp_exe.name
                fake_p.chromium.launch = AsyncMock(return_value=fake_browser)

                browser = await auth._launch_login_browser(fake_p)
                self.assertIs(browser, fake_browser)
                fake_p.chromium.launch.assert_called_once_with(headless=False)

        asyncio.run(_run())

    def test_settings_tab_uses_responsive_horizontal_grid(self):
        html = (build.ROOT_DIR / "static" / "index.html").read_text(encoding="utf-8")
        css = (build.ROOT_DIR / "static" / "style.css").read_text(encoding="utf-8")
        self.assertIn('class="config-sections-grid"', html)
        self.assertIn('class="config-section config-section--wide"', html)
        self.assertIn('class="config-notif-channels-grid"', html)
        self.assertIn(".config-sections-grid", css)
        self.assertIn("max-width: 768px", css)


class TestBrowserLifecycleShutdown(unittest.TestCase):
    def test_disabled_watchdog_never_triggers_shutdown(self):
        from services.browser_lifecycle_service import BrowserLifecycleManager

        called = threading.Event()
        mgr = BrowserLifecycleManager(disconnect_grace_sec=0.05, heartbeat_timeout_sec=0.1)
        mgr.configure(enabled=False, on_shutdown=called.set)
        try:
            hb = mgr.register_heartbeat("tab-1", is_loopback=True)
            self.assertFalse(hb["watchdog"])
            dc = mgr.register_disconnect("tab-1", is_loopback=True)
            self.assertFalse(dc["shutdown_scheduled"])
            self.assertFalse(called.wait(0.15))
        finally:
            mgr.shutdown()

    def test_closing_last_local_tab_triggers_shutdown_after_grace_period(self):
        from services.browser_lifecycle_service import BrowserLifecycleManager

        called = threading.Event()
        mgr = BrowserLifecycleManager(disconnect_grace_sec=0.05, heartbeat_timeout_sec=10.0)
        mgr.configure(enabled=True, on_shutdown=called.set)
        try:
            mgr.register_heartbeat("tab-1", is_loopback=True)
            dc = mgr.register_disconnect("tab-1", is_loopback=True)
            self.assertTrue(dc["shutdown_scheduled"])
            self.assertTrue(called.wait(1.0))
        finally:
            mgr.shutdown()

    def test_f5_reload_or_second_tab_cancels_shutdown(self):
        from services.browser_lifecycle_service import BrowserLifecycleManager

        called = threading.Event()
        mgr = BrowserLifecycleManager(disconnect_grace_sec=0.15, heartbeat_timeout_sec=10.0)
        mgr.configure(enabled=True, on_shutdown=called.set)
        try:
            mgr.register_heartbeat("tab-1", is_loopback=True)
            mgr.register_disconnect("tab-1", is_loopback=True)
            # Simula nova página após F5 enviando heartbeat antes do grace timeout
            hb2 = mgr.register_heartbeat("tab-2", is_loopback=True)
            self.assertEqual(hb2["active_clients"], 1)
            self.assertFalse(called.wait(0.25))
        finally:
            mgr.shutdown()

    def test_api_endpoints_and_frontend_beacon_present(self):
        from fastapi.testclient import TestClient
        import server
        from services.browser_lifecycle_service import browser_lifecycle_manager

        called = threading.Event()
        browser_lifecycle_manager.configure(enabled=True, on_shutdown=called.set)
        try:
            client = TestClient(server.app)
            r1 = client.post("/api/system/heartbeat", json={"client_id": "test-tab"})
            self.assertEqual(r1.status_code, 200)
            self.assertTrue(r1.json()["watchdog"])
            r2 = client.post("/api/system/disconnect", json={"client_id": "test-tab"})
            self.assertEqual(r2.status_code, 200)
            self.assertTrue(r2.json()["shutdown_scheduled"])
        finally:
            browser_lifecycle_manager.configure(enabled=False, on_shutdown=None)
            browser_lifecycle_manager.shutdown()

        app_js = (build.ROOT_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
        self.assertIn("/api/system/heartbeat", app_js)
        self.assertIn("/api/system/disconnect", app_js)
        self.assertIn("sendBeacon", app_js)

    def test_browser_watchdog_enabled_only_in_frozen_releases(self):
        import main

        with patch.object(main, "is_frozen", return_value=False):
            self.assertFalse(main.should_enable_browser_watchdog(True))
            self.assertFalse(main.should_enable_browser_watchdog(False))

        with patch.object(main, "is_frozen", return_value=True):
            self.assertTrue(main.should_enable_browser_watchdog(True))
            self.assertFalse(main.should_enable_browser_watchdog(False))

    def test_unfocused_tab_never_triggers_heartbeat_timeout_shutdown(self):
        from services.browser_lifecycle_service import BrowserLifecycleManager

        called = threading.Event()
        mgr = BrowserLifecycleManager(disconnect_grace_sec=0.05)
        self.assertIsNone(mgr.heartbeat_timeout_sec)
        mgr.configure(enabled=True, on_shutdown=called.set)
        try:
            hb = mgr.register_heartbeat("tab-bg", is_loopback=True)
            self.assertEqual(hb["active_clients"], 1)
            # Simula 10 horas fora de foco com timers congelados pelo navegador
            future = mgr.active_clients["tab-bg"] + 36000.0
            self.assertFalse(mgr.check_stale_clients(now=future))
            self.assertIn("tab-bg", mgr.active_clients)
            self.assertFalse(called.is_set())

            # Deve fechar somente quando a aba realmente dispara disconnect
            dc = mgr.register_disconnect("tab-bg", is_loopback=True)
            self.assertTrue(dc["shutdown_scheduled"])
            self.assertTrue(called.wait(1.0))
        finally:
            mgr.shutdown()


class TestSakugaVfxOfflineIntegration(unittest.TestCase):
    def test_vendor_assets_exist_and_verify(self):
        vendor_dir = build.verify_sakuga_vendor_assets()
        self.assertTrue(vendor_dir.is_dir())
        for filename in build.REQUIRED_SAKUGA_COMPONENTS:
            path = vendor_dir / filename
            self.assertTrue(path.is_file(), f"Arquivo ausente: {filename}")
            self.assertGreater(path.stat().st_size, 1024)

    def test_fastapi_serves_sakuga_vendor_scripts_and_index(self):
        from fastapi.testclient import TestClient
        import server

        client = TestClient(server.app)
        root_res = client.get("/")
        self.assertEqual(root_res.status_code, 200)
        self.assertIn("/static/vendor/sakuga-vfx/button.js", root_res.text)

        for filename in build.REQUIRED_SAKUGA_COMPONENTS:
            tag_name = f"sakuga-{Path(filename).stem}"
            res = client.get(f"/static/vendor/sakuga-vfx/{filename}")
            self.assertEqual(res.status_code, 200, f"Falha ao servir {filename}")
            self.assertIn(tag_name, res.text)

        for vendor_path in (
            "/static/vendor/marked/marked.min.js",
            "/static/vendor/html2canvas/html2canvas.min.js",
            "/static/vendor/fontawesome/css/all.min.css",
            "/assets/elements/zzz_physical.png",
        ):
            vres = client.get(vendor_path)
            self.assertEqual(vres.status_code, 200, f"Falha ao servir {vendor_path}")

    def test_element_icons_normalization_validation_and_offline_fallback(self):
        import tempfile
        from services import media_service

        # Rejeita HTML 403 como imagem válida
        self.assertEqual(media_service._detect_valid_image_mime(b"<!DOCTYPE html><html>403</html>"), "")
        self.assertEqual(media_service._normalize_element_filename("hsr_gelo.png"), "hsr_ice.png")
        self.assertEqual(media_service._normalize_element_filename("zzz_element 300.png"), "zzz_lumiflux.png")

        # Verifica cache local PNG válido + conversão/escrita segura
        png_stub = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
        with (
            tempfile.TemporaryDirectory() as tmpdir,
            patch.object(media_service, "get_data_path", side_effect=lambda p: str(Path(tmpdir) / p)),
            patch.object(media_service, "get_resource_path", side_effect=lambda p: str(Path(tmpdir) / p)),
        ):
            dest = str(Path(tmpdir) / "assets" / "elements" / "hsr_ice.png")
            self.assertTrue(media_service._save_element_png(png_stub, dest))
            data, mime = media_service.get_element_icon_asset("hsr_gelo.png")
            self.assertEqual(mime, "image/png")
            self.assertEqual(data, png_stub)

            # Fallback SVG quando ausente e offline
            with patch("curl_cffi.requests.get", side_effect=OSError("offline")):
                svg_data, svg_mime = media_service.get_element_icon_asset("genshin_pyro.png")
                self.assertEqual(svg_mime, "image/svg+xml")
                self.assertIn(b"<svg", svg_data)

    def test_index_and_css_configured_for_offline_dark_theme(self):
        html = (build.ROOT_DIR / "static" / "index.html").read_text(encoding="utf-8")
        css = (build.ROOT_DIR / "static" / "style.css").read_text(encoding="utf-8")

        self.assertNotIn("raw.githubusercontent.com/finktheartist/sakuga-vfx", html)
        self.assertNotIn("cdn.jsdelivr.net", html)
        self.assertNotIn("cdnjs.cloudflare.com", html)
        self.assertNotIn("<button", html)
        self.assertIn('/static/vendor/marked/marked.min.js', html)
        self.assertIn('/static/vendor/html2canvas/html2canvas.min.js', html)
        self.assertIn('/static/vendor/fontawesome/css/all.min.css', html)
        self.assertTrue((build.ROOT_DIR / "static" / "vendor" / "marked" / "marked.min.js").is_file())
        self.assertTrue((build.ROOT_DIR / "static" / "vendor" / "html2canvas" / "html2canvas.min.js").is_file())
        self.assertTrue((build.ROOT_DIR / "static" / "vendor" / "fontawesome" / "css" / "all.min.css").is_file())
        self.assertTrue((build.ROOT_DIR / "static" / "vendor" / "fontawesome" / "webfonts" / "fa-solid-900.woff2").is_file())

        import re
        for filename in build.REQUIRED_SAKUGA_COMPONENTS:
            pattern = rf'<script src="/static/vendor/sakuga-vfx/{re.escape(filename)}(?:\?v=[^"]+)?"></script>'
            self.assertRegex(html, pattern, f"Tag offline ausente para {filename}")

        for tag_name in (
            "<sakuga-button",
            "<sakuga-tabs",
            "<sakuga-input",
            "<sakuga-toggle",
            "<sakuga-checkbox",
            "<sakuga-radio",
            "<sakuga-slider",
            "<sakuga-progress",
            "<sakuga-tooltip",
            "<sakuga-toast",
        ):
            self.assertIn(tag_name, html)

        for css_var in ("--sk-card:", "--sk-ink:", "--sk-pri:", "--sk-acc:", "--sk-fill:"):
            self.assertIn(css_var, css)
        self.assertIn("overflow: visible;", css)
        self.assertNotIn(".modal-card-content {\n    overflow: visible !important;", css.replace("\r\n", "\n"))
        self.assertIn("flex: 1 1 auto;\n    min-height: 0;\n    overflow-y: auto;", css.replace("\r\n", "\n"))

        progress_js = (build.ROOT_DIR / "static" / "vendor" / "sakuga-vfx" / "progress.js").read_text(encoding="utf-8")
        button_js = (build.ROOT_DIR / "static" / "vendor" / "sakuga-vfx" / "button.js").read_text(encoding="utf-8")
        self.assertIn("r.width > 0 && r.height > 0", progress_js)
        self.assertIn("b.w <= 0 || b.h <= 0", progress_js)
        self.assertIn("q.w <= 0 || q.h <= 0", button_js)
        self.assertIn("fx.isOccluded", progress_js)
        self.assertIn("clearTransient", button_js)


if __name__ == "__main__":
    unittest.main()
