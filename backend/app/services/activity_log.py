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

    def log_interaction(
        self,
        ip: str,
        message: str,
        cached: bool,
        response_sources: list[str] | None = None,
        response_time_ms: int | None = None,
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
        # Construct RequestRecord internally from individual arguments
        record = RequestRecord(
            request_id=request_id,
            timestamp=utc_now_iso(),
            ip_hash=hash_ip(ip, self._ip_hash_salt),
            session_id=session_id,
            original_query=message, # Assuming message is the original query
            normalized_query=message, # Assuming message is also the normalized query if not explicitly passed
            intent_route=intent_route,
            matched_alias=matched_alias,
            similarity_score=similarity_score,
            match_type=match_type,
            cache_hit=cached,
            # cache_lookup_ms is not passed, will be default None
            retrieval_latency_ms=retrieval_latency_ms,
            # embedding_latency_ms is not passed, will be default None
            llm_latency_ms=llm_latency_ms,
            tts_latency_ms=tts_latency_ms,
            response_sources=response_sources or [],
            response_length=len(message), # Approximating response_length from message
            retrieved_chunks=retrieved_chunks,
            status=status,
            error=error,
            # total_latency_ms is not passed, will be default None
            # prompt_tokens is not passed, will be default None
            # completion_tokens is not passed, will be default None
        )
        self._append_jsonl(
            "ai_interactions.jsonl",
            {"type": "ai_interaction", **record.__dict__},
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
