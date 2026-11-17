import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

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


if __name__ == "__main__":
    unittest.main()
