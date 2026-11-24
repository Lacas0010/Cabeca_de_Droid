import io
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient

import server
import updater
import version as app_version


def _reset_updater_state() -> None:
    updater._set_state(
        running=False,
        stage="idle",
        progress=0.0,
        message="Pronto para verificar atualizações.",
        target_version=None,
        release_url=updater.GITHUB_RELEASES_PAGE_URL,
        error=None,
    )


class TestUpdaterSuite(unittest.TestCase):
    def setUp(self) -> None:
        _reset_updater_state()

    def tearDown(self) -> None:
        _reset_updater_state()

    def test_semver_comparisons(self) -> None:
        self.assertTrue(updater.is_newer_version("v1.1.0", "1.0.0"))
        self.assertTrue(updater.is_newer_version("1.10.0", "1.2.0"))
        self.assertTrue(updater.is_newer_version("v2.0.0", "1.9.9"))
        self.assertFalse(updater.is_newer_version("v1.1.0", "1.1.0"))
        self.assertFalse(updater.is_newer_version("1.0.9", "1.1.0"))

    def test_api_updater_check_update_available_and_uptodate(self) -> None:
        client = TestClient(server.app)

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "tag_name": "v9.9.9",
            "body": "- Novo suporte offline\n- Correções Sakuga",
            "html_url": "https://github.com/Lacas0010/Cabeca_de_Droid/releases/tag/v9.9.9",
            "assets": [
                {
                    "name": "Cabeca_de_Droid-Windows-x64.zip",
                    "browser_download_url": "https://github.com/Lacas0010/Cabeca_de_Droid/releases/download/v9.9.9/Cabeca_de_Droid-Windows-x64.zip",
                    "size": 12345678,
                }
            ],
        }

        async_client_instance = MagicMock()
        async def _fake_get(*args, **kwargs):
            return mock_resp
        async_client_instance.get = _fake_get

        async_cm = MagicMock()
        async def _aenter(*args):
            return async_client_instance
        async def _aexit(*args):
            return False
        async_cm.__aenter__ = _aenter
        async_cm.__aexit__ = _aexit

        with patch("updater.httpx.AsyncClient", return_value=async_cm):
            res = client.get("/api/updater/check")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["update_available"])
            self.assertEqual(data["latest_version"], "9.9.9")
            self.assertEqual(data["asset_size"], 12345678)
            self.assertIn("Cabeca_de_Droid-Windows-x64.zip", data["download_url"])

        mock_resp.json.return_value["tag_name"] = f"v{app_version.__version__}"
        with patch("updater.httpx.AsyncClient", return_value=async_cm):
            res = client.get("/api/updater/check")
            self.assertEqual(res.status_code, 200)
            self.assertFalse(res.json()["update_available"])

    def test_api_updater_check_offline_timeout_is_graceful(self) -> None:
        client = TestClient(server.app)

        async_client_instance = MagicMock()
        async def _timeout_get(*args, **kwargs):
            raise httpx.ConnectTimeout("timed out")
        async_client_instance.get = _timeout_get

        async_cm = MagicMock()
        async def _aenter(*args):
            return async_client_instance
        async def _aexit(*args):
            return False
        async_cm.__aenter__ = _aenter
        async_cm.__aexit__ = _aexit

        with patch("updater.httpx.AsyncClient", return_value=async_cm):
            res = client.get("/api/updater/check")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertFalse(data["update_available"])
            self.assertEqual(data["current_version"], updater.get_current_version())
            self.assertTrue(data["error"])

    def test_api_updater_check_falls_back_to_web_redirect_on_403_rate_limit(self) -> None:
        client = TestClient(server.app)

        rate_limit_resp = MagicMock()
        rate_limit_resp.status_code = 403
        rate_limit_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403 rate limit exceeded",
            request=httpx.Request("GET", updater.GITHUB_RELEASES_LATEST_URL),
            response=httpx.Response(403),
        )

        web_resp = MagicMock()
        web_resp.status_code = 200
        web_resp.url = "https://github.com/Lacas0010/Cabeca_de_Droid/releases/tag/v9.8.7"
        web_resp.raise_for_status.return_value = None

        head_resp = MagicMock()
        head_resp.status_code = 200
        head_resp.headers = {"Content-Length": "42000000"}

        async_client_instance = MagicMock()

        async def _fake_get(url, *args, **kwargs):
            if "api.github.com" in str(url):
                return rate_limit_resp
            return web_resp

        async def _fake_head(url, *args, **kwargs):
            return head_resp

        async_client_instance.get = _fake_get
        async_client_instance.head = _fake_head

        async_cm = MagicMock()
        async def _aenter(*args):
            return async_client_instance
        async def _aexit(*args):
            return False
        async_cm.__aenter__ = _aenter
        async_cm.__aexit__ = _aexit

        with patch("updater.httpx.AsyncClient", return_value=async_cm):
            res = client.get("/api/updater/check")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIsNone(data["error"])
            self.assertTrue(data["update_available"])
            self.assertEqual(data["latest_version"], "9.8.7")
            self.assertEqual(data["asset_size"], 42000000)
            self.assertEqual(
                data["download_url"],
                "https://github.com/Lacas0010/Cabeca_de_Droid/releases/download/v9.8.7/Cabeca_de_Droid-Windows-x64.zip",
            )

    def test_api_updater_start_dev_mode(self) -> None:
        client = TestClient(server.app)
        with patch("updater.is_app_frozen", return_value=False):
            res = client.post(
                "/api/updater/start",
                json={
                    "download_url": "https://github.com/Lacas0010/Cabeca_de_Droid/releases/download/v2.0.0/Cabeca_de_Droid-Windows-x64.zip",
                    "target_version": "2.0.0",
                },
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["stage"], "dev_mode")
            self.assertFalse(data["is_frozen"])
            self.assertEqual(data["progress"], 1.0)

            status_res = client.get("/api/updater/status")
            self.assertEqual(status_res.status_code, 200)
            self.assertEqual(status_res.json()["stage"], "dev_mode")

    def test_safe_extract_zip_rejects_zipslip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            bad_zip = tmp_path / "bad.zip"
            with zipfile.ZipFile(bad_zip, "w") as zf:
                zf.writestr("../evil.exe", b"malware")
            with self.assertRaises(ValueError):
                updater.safe_extract_zip(bad_zip, tmp_path / "out")

    def test_frozen_update_worker_extracts_builds_bat_and_launches(self) -> None:
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            zf.writestr("Cabeca_de_Droid/Cabeca_de_Droid.exe", b"MZ_FAKE_NEW_EXE")
            zf.writestr("Cabeca_de_Droid/static/index.html", b"<html>new</html>")
        zip_bytes = zip_buf.getvalue()

        mock_stream_resp = MagicMock()
        mock_stream_resp.raise_for_status.return_value = None
        mock_stream_resp.headers = {"Content-Length": str(len(zip_bytes))}
        mock_stream_resp.iter_bytes.return_value = [zip_bytes[:32], zip_bytes[32:]]
        stream_cm = MagicMock()
        stream_cm.__enter__.return_value = mock_stream_resp
        stream_cm.__exit__.return_value = False

        sync_client = MagicMock()
        sync_client.stream.return_value = stream_cm
        client_cm = MagicMock()
        client_cm.__enter__.return_value = sync_client
        client_cm.__exit__.return_value = False

        captured_bat_scripts: list[str] = []
        captured_popen_kwargs: list[dict] = []

        def _fake_popen(cmd, **kwargs):
            captured_popen_kwargs.append(kwargs)
            bat_file = Path(cmd[2])
            if bat_file.exists():
                captured_bat_scripts.append(bat_file.read_text(encoding="utf-8"))
                bat_file.unlink(missing_ok=True)
            return MagicMock()

        with tempfile.TemporaryDirectory() as app_tmp:
            fake_exe = Path(app_tmp) / "Cabeca_de_Droid.exe"
            fake_exe.write_bytes(b"MZ_OLD")
            fake_mei = str(Path(app_tmp) / "_MEI_FAKE")

            with (
                patch("updater.httpx.Client", return_value=client_cm),
                patch.object(sys, "executable", str(fake_exe)),
                patch.object(sys, "_MEIPASS", fake_mei, create=True),
                patch.dict(
                    os.environ,
                    {
                        "_PYI_ARCHIVE_FILE": str(fake_exe),
                        "_PYI_PARENT_PROCESS_LEVEL": "1",
                        "_MEIPASS2": fake_mei,
                        "PATH": fake_mei + os.pathsep + os.environ.get("PATH", ""),
                    },
                ),
                patch("updater.time.sleep"),
                patch("updater.subprocess.Popen", side_effect=_fake_popen) as mock_popen,
                patch("updater.os._exit") as mock_exit,
            ):
                updater._run_frozen_update_worker(
                    "https://github.com/Lacas0010/Cabeca_de_Droid/releases/download/v2.0.0/Cabeca_de_Droid-Windows-x64.zip",
                    "2.0.0",
                )

            mock_popen.assert_called_once()
            mock_exit.assert_called_once_with(0)
            self.assertEqual(len(captured_bat_scripts), 1)
            bat = captured_bat_scripts[0]
            self.assertIn(f"set PID={os.getpid()}", bat)
            self.assertIn("set PPID=", bat)
            self.assertIn(".env", bat)
            self.assertIn("hoyo_app.db", bat)
            self.assertIn("*.db *.sqlite", bat)
            self.assertIn("/R:3 /W:1", bat)
            self.assertIn(":copy_exe_loop", bat)
            self.assertIn('start "" /D "%DST_DIR%" "%EXE_PATH%"', bat)
            self.assertIn('del "%~f0"', bat)

            popen_env = captured_popen_kwargs[0].get("env", {})
            self.assertNotIn("_PYI_ARCHIVE_FILE", popen_env)
            self.assertNotIn("_PYI_PARENT_PROCESS_LEVEL", popen_env)
            self.assertNotIn("_MEIPASS2", popen_env)
            self.assertNotIn(fake_mei.lower(), popen_env.get("PATH", "").lower())

            status = updater.get_updater_status()
            self.assertEqual(status["stage"], "applying")
            self.assertEqual(status["progress"], 1.0)

    def test_packaging_and_frontend_wiring(self) -> None:
        root = Path(__file__).resolve().parent.parent
        self.assertTrue(bool(app_version.__version__))

        reqs = (root / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("packaging", reqs)
        self.assertIn("httpx", reqs)

        build_src = (root / "build.py").read_text(encoding="utf-8")
        for hidden in ('"packaging"', '"version"', '"updater"'):
            self.assertIn(hidden, build_src)

        workflow_src = (root / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn("Stamp release version into version.py", workflow_src)

        index_html = (root / "static" / "index.html").read_text(encoding="utf-8")
        for token in (
            'id="app-version-badge"',
            'id="btn-check-updates"',
            'id="modal-sakuga-updater"',
            'id="btn-updater-install"',
            'id="btn-updater-later"',
            '<sakuga-progress class="sk-sync-progress" id="updater-progress-bar"',
        ):
            self.assertIn(token, index_html)

        app_js = (root / "static" / "js" / "app.js").read_text(encoding="utf-8")
        self.assertIn("updater_ui.js", app_js)
        self.assertTrue((root / "static" / "js" / "modules" / "updater_ui.js").exists())


if __name__ == "__main__":
    unittest.main()
