from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any


def _hash_ip(ip: str, salt: str) -> str:
    """16-char hex digest — matches observability.hash_ip format exactly."""
    return sha256(f"{salt}{ip}".encode()).hexdigest()[:16]


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
                "timestamp": self._utc_now(),
                "path": path,
                "ip_hash": _hash_ip(ip, self._ip_hash_salt),
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
        # Extended observability fields
        request_id: str | None = None,
        session_id: str | None = None,
        intent_route: str | None = None,
        matched_alias: str | None = None,
        match_type: str | None = None,
        similarity_score: float | None = None,
        retrieval_latency_ms: float | None = None,
        llm_latency_ms: float | None = None,
        tts_latency_ms: float | None = None,
        retrieved_chunks: int = 0,
        status: str = "ok",
        error: str | None = None,
    ) -> None:
        self._append_jsonl(
            "ai_interactions.jsonl",
            {
                "type": "ai_interaction",
                "timestamp": self._utc_now(),
                "request_id": request_id,
                "ip_hash": _hash_ip(ip, self._ip_hash_salt),
                "session_id": session_id,
                "message": message,
                "cached": cached,
                "response_sources": response_sources or [],
                "response_time_ms": response_time_ms,
                "intent_route": intent_route,
                "matched_alias": matched_alias,
                "match_type": match_type,
                "similarity_score": similarity_score,
                "retrieval_latency_ms": retrieval_latency_ms,
                "llm_latency_ms": llm_latency_ms,
                "tts_latency_ms": tts_latency_ms,
                "retrieved_chunks": retrieved_chunks,
                "status": status,
                "error": error,
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


# Module-level singleton — salt injected lazily in main.py lifespan after
# settings are resolved, so we start with an empty salt here. In tests,
# construct ActivityLogger(ip_hash_salt="test-salt") directly.
activity_logger = ActivityLogger()
