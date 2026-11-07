import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import main


class LeadApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test-leads.db")
        self.database_patch = patch.object(main, "DATABASE", self.db_path)
        self.database_patch.start()
        main.create_database()
        self.client = TestClient(main.app)
        self.ai_patch = patch(
            "main.analyze_lead_with_ai",
            return_value=(
                "LEAD_SCORE: 82\nCATEGORY: Web Development\n"
                "PRIORITY: HIGH\nINTENT: Ready to buy\n"
                "RECOMMENDED_ACTION: Schedule a discovery call"
            ),
        )
        self.ai_patch.start()

    def tearDown(self):
        self.ai_patch.stop()
        self.database_patch.stop()
        self.temp_dir.cleanup()

    def create_lead(self):
        response = self.client.post(
            "/leads",
            json={
                "name": "Ajay Test",
                "email": "ajay@example.com",
                "company": "Example Labs",
                "requirement": "Build a business website",
                "budget": 75000,
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["lead"]["id"]

    def test_health_and_lead_create_list_read(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        lead_id = self.create_lead()
        self.assertEqual(self.client.get(f"/leads/{lead_id}").status_code, 200)
        listed = self.client.get("/leads").json()
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["priority"], "HIGH")

    def test_dashboard_stats_and_lead_update(self):
        lead_id = self.create_lead()
        stats = self.client.get("/dashboard/stats")
        self.assertEqual(stats.status_code, 200)
        self.assertEqual(stats.json()["total_leads"], 1)
        updated = self.client.put(
            f"/leads/{lead_id}", json={"status": "CONTACTED"}
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["status"], "CONTACTED")

    def test_email_requires_explicit_approval(self):
        lead_id = self.create_lead()
        response = self.client.post(f"/leads/{lead_id}/send-email")
        self.assertEqual(response.status_code, 403)

    def test_approval_allows_email_workflow_to_continue(self):
        lead_id = self.create_lead()
        approved = self.client.post(f"/leads/{lead_id}/approve")
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(
            self.client.get(f"/leads/{lead_id}").json()["email_approved"], 1
        )

    def test_delete_lead(self):
        lead_id = self.create_lead()
        deleted = self.client.delete(f"/leads/{lead_id}")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.client.get(f"/leads/{lead_id}").status_code, 404)


if __name__ == "__main__":
    unittest.main()
