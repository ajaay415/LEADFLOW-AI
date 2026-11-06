import unittest
from unittest.mock import patch

import requests

from ai_service import (
    _fallback_analysis,
    analyze_lead_with_ai,
    generate_customer_response,
)


class LeadAnalysisTests(unittest.TestCase):
    def test_fallback_returns_required_fields(self):
        result = _fallback_analysis(
            requirement="Build an AI website and CRM dashboard",
            company="Example Ltd",
            budget=100000,
        )
        for label in (
            "LEAD_SCORE:",
            "CATEGORY:",
            "PRIORITY:",
            "INTENT:",
            "RECOMMENDED_ACTION:",
        ):
            self.assertIn(label, result)

    def test_fallback_score_is_bounded(self):
        result = _fallback_analysis("AI automation website CRM", "Company", 9999999)
        score_line = next(line for line in result.splitlines() if line.startswith("LEAD_SCORE:"))
        score = int(score_line.split(":", 1)[1].strip())
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    @patch("ai_service.requests.post", side_effect=requests.ConnectionError("Ollama offline"))
    def test_ollama_unavailable_uses_fallback(self, mocked_post):
        result = analyze_lead_with_ai(
            name="Ajay",
            company="Example Ltd",
            requirement="Need a business website",
            budget=50000,
        )
        self.assertIn("LEAD_SCORE:", result)
        mocked_post.assert_called_once()

    def test_customer_response_contains_customer_and_requirement(self):
        result = generate_customer_response(
            name="Ajay",
            company="Example Ltd",
            requirement="Build a website",
            budget=50000,
            priority="HIGH",
            category="Web Development",
        )
        self.assertIn("Ajay", result)
        self.assertIn("Build a website", result)
        self.assertIn("Web Development", result)


if __name__ == "__main__":
    unittest.main()
