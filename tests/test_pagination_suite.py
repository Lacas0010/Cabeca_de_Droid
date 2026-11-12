import unittest
from fastapi.testclient import TestClient
from server import app
import database


class TestPaginationSuite(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_code_redemption_history_pagination(self):
        # Insert a few dummy records in promo_code_history
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM promo_code_history WHERE code LIKE 'TESTPAG_%'")
            for i in range(10):
                cursor.execute(
                    """
                    INSERT INTO promo_code_history (game_id, uid, code, status, message, redeemed_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now', ?))
                    """,
                    ("hsr", "999999999", f"TESTPAG_{i}", "success", "OK", f"-{i} minutes"),
                )
            conn.commit()

        # Query database directly with limit and offset
        page1 = database.get_code_redemption_history("hsr", limit=3, offset=0)
        self.assertEqual(len(page1), 3)

        page2 = database.get_code_redemption_history("hsr", limit=3, offset=3)
        self.assertEqual(len(page2), 3)
        self.assertNotEqual(page1[0]["code"], page2[0]["code"])

        # Test endpoint
        resp = self.client.get("/api/codes/history/hsr?limit=4&offset=0")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["limit"], 4)
        self.assertEqual(data["offset"], 0)
        self.assertLessEqual(len(data["history"]), 4)

        # Cleanup
        with database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM promo_code_history WHERE code LIKE 'TESTPAG_%'")
            conn.commit()

    def test_account_history_endpoint_pagination(self):
        resp = self.client.get("/api/history/hsr?limit=10&offset=0")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["limit"], 10)
        self.assertEqual(data["offset"], 0)
        self.assertIn("history", data)


if __name__ == "__main__":
    unittest.main()
