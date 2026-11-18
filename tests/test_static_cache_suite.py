import re
import unittest
from fastapi.testclient import TestClient

import server
from version import __version__


class TestStaticCacheSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(server.app)

    def test_index_html_injects_version_and_mtime_cache_busters(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("no-cache", res.headers.get("cache-control", "").lower())
        html = res.text
        self.assertRegex(html, rf'href="style\.css\?v={re.escape(__version__)}-\d+"')
        self.assertRegex(html, rf'src="js/app\.js\?v={re.escape(__version__)}-\d+"')
        self.assertRegex(html, rf'src="/static/vendor/sakuga-vfx/button\.js\?v={re.escape(__version__)}-\d+"')

    def test_app_js_injects_module_cache_busters_and_no_cache(self):
        res = self.client.get("/js/app.js")
        self.assertEqual(res.status_code, 200)
        self.assertIn("no-cache", res.headers.get("cache-control", "").lower())
        self.assertRegex(res.text, rf'import "\./modules/i18n\.js\?v={re.escape(__version__)}-\d+"')
        self.assertRegex(res.text, rf'import\("\./modules/gacha_sim\.js\?v={re.escape(__version__)}-\d+"\)')


if __name__ == "__main__":
    unittest.main()
