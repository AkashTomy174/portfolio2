from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from app.services.observability import RequestRecord, hash_ip, utc_now_iso


class ActivityLogger:
    def __init__(self, log_dir: Path | None = None, ip_hash_salt: str = "") -> None:
        self.log_dir = log_dir or Path(__file__).resolve().parents[1] / "data" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._ip_hash_salt = ip_hash_salt

    def log_visit(self, path: str, ip: str, user_agent: str | None = None) -> None:
        self._append_jsonl(
            "visits.jsonl",
            {
                "type": "visit",
                "timestamp": utc_now_iso(),
                "path": path,
                "ip_hash": hash_ip(ip, self._ip_hash_salt),
                "user_agent": user_agent,
            },
        )

    def log_interaction(self, record: RequestRecord) -> None:
        self._append_jsonl(
            "ai_interactions.jsonl",
            {
                "type": "ai_interaction",
                **record.__dict__,
            },
        )

    def read_recent(self, filename: str, limit: int = 50) -> list[dict[str, Any]]:
        path = self.log_dir / filename
        if not path.exists():
            return []

        entries: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))

        return entries[-limit:]

    def _append_jsonl(self, filename: str, payload: dict[str, Any]) -> None:
        path = self.log_dir / filename
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False))
            handle.write("\n")


activity_logger = ActivityLogger()
