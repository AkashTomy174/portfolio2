import json
import tempfile
from pathlib import Path
import unittest

from app.services.activity_log import ActivityLogger


class ActivityLoggerTests(unittest.TestCase):
    def test_logs_visits_and_ai_interactions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ActivityLogger(log_dir=Path(tmpdir))
            logger.log_visit(path="/", ip="1.2.3.4", user_agent="test-agent")
            logger.log_interaction(
                ip="1.2.3.4",
                message="hello",
                cached=False,
                response_sources=["about"],
                response_time_ms=42,
            )

            visit_path = Path(tmpdir) / "visits.jsonl"
            interaction_path = Path(tmpdir) / "ai_interactions.jsonl"

            self.assertTrue(visit_path.exists())
            self.assertTrue(interaction_path.exists())

            visit_payload = json.loads(visit_path.read_text(encoding="utf-8").strip())
            interaction_payload = json.loads(interaction_path.read_text(encoding="utf-8").strip())

            self.assertEqual(visit_payload["type"], "visit")
            self.assertEqual(visit_payload["path"], "/")
            self.assertEqual(interaction_payload["type"], "ai_interaction")
            self.assertEqual(interaction_payload["message"], "hello")
            self.assertFalse(interaction_payload["cached"])


if __name__ == "__main__":
    unittest.main()
