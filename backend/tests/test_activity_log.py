import hashlib
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

            # ip_hash should be stored, not raw ip
            self.assertIn("ip_hash", visit_payload)
            self.assertNotIn("ip", visit_payload)
            self.assertEqual(len(visit_payload["ip_hash"]), 16)
            self.assertNotEqual(visit_payload["ip_hash"], "1.2.3.4")

            self.assertEqual(interaction_payload["type"], "ai_interaction")
            self.assertEqual(interaction_payload["message"], "hello")
            self.assertFalse(interaction_payload["cached"])

    def test_ip_is_hashed_with_salt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ActivityLogger(log_dir=Path(tmpdir), ip_hash_salt="test-salt")
            logger.log_visit(path="/", ip="1.2.3.4", user_agent="test-agent")

            visit_path = Path(tmpdir) / "visits.jsonl"
            visit_payload = json.loads(visit_path.read_text(encoding="utf-8").strip())

            expected_hash = hashlib.sha256(b"test-salt1.2.3.4").hexdigest()[:16]
            unsalted_hash = hashlib.sha256(b"1.2.3.4").hexdigest()[:16]

            self.assertEqual(visit_payload["ip_hash"], expected_hash)
            # Verify that the salt is actually mixed in (different from unsalted)
            self.assertNotEqual(visit_payload["ip_hash"], unsalted_hash)

    def test_different_salts_produce_different_hashes(self):
        with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
            logger1 = ActivityLogger(log_dir=Path(tmpdir1), ip_hash_salt="salt-a")
            logger2 = ActivityLogger(log_dir=Path(tmpdir2), ip_hash_salt="salt-b")

            logger1.log_visit(path="/", ip="1.2.3.4")
            logger2.log_visit(path="/", ip="1.2.3.4")

            payload1 = json.loads((Path(tmpdir1) / "visits.jsonl").read_text(encoding="utf-8").strip())
            payload2 = json.loads((Path(tmpdir2) / "visits.jsonl").read_text(encoding="utf-8").strip())

            self.assertNotEqual(payload1["ip_hash"], payload2["ip_hash"])

    def test_interaction_ip_is_hashed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = ActivityLogger(log_dir=Path(tmpdir), ip_hash_salt="test-salt")
            logger.log_interaction(
                ip="1.2.3.4",
                message="test message",
                cached=False,
                response_sources=["about"],
                response_time_ms=100,
            )

            interaction_path = Path(tmpdir) / "ai_interactions.jsonl"
            payload = json.loads(interaction_path.read_text(encoding="utf-8").strip())

            expected_hash = hashlib.sha256(b"test-salt1.2.3.4").hexdigest()[:16]

            self.assertIn("ip_hash", payload)
            self.assertNotIn("ip", payload)
            self.assertEqual(payload["ip_hash"], expected_hash)
            self.assertNotEqual(payload["ip_hash"], "1.2.3.4")


if __name__ == "__main__":
    unittest.main()
