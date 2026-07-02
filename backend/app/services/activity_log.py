import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ActivityLogger:
    def __init__(self, log_dir: Path | None = None):
        self.log_dir = log_dir or Path(__file__).resolve().parents[1] / "data" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_visit(self, path: str, ip: str, user_agent: str | None = None) -> None:
        self._append_jsonl(
            "visits.jsonl",
            {
                "type": "visit",
                "timestamp": self._utc_now(),
                "path": path,
                "ip": ip,
                "user_agent": user_agent,
            },
        )

    def log_interaction(
        self,
        ip: str,
        message: str,
        cached: bool,
        response_sources: list[str] | None = None,
        response_time_ms: int | None = None,
    ) -> None:
        self._append_jsonl(
            "ai_interactions.jsonl",
            {
                "type": "ai_interaction",
                "timestamp": self._utc_now(),
                "ip": ip,
                "message": message,
                "cached": cached,
                "response_sources": response_sources or [],
                "response_time_ms": response_time_ms,
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

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


activity_logger = ActivityLogger()
