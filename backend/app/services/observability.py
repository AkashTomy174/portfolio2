"""
app/services/observability.py

Structured observability for the AI Akash backend.

Two responsibilities:
  1. RequestRecord / ObservabilityLogger  — emit one JSON log line per request
     containing every field needed for production debugging and auditing.
  2. MetricsCollector                     — maintain in-process counters and a
     latency reservoir for p95/p99 computation; exposed via /metrics.

Design notes
------------
- The logger writes to the standard Python logging system (JSON lines at INFO
  level on the "ai-akash.obs" logger).  Operators can redirect that logger to
  a file, stdout, or a log aggregator without touching application code.
- MetricsCollector is intentionally not thread-safe at the reservoir level
  (uses a plain list with a fixed cap).  For a single-process uvicorn deployment
  this is fine.  A multi-worker deployment should use Redis counters instead.
- IP addresses are hashed before storage so no PII appears in logs.
"""
from __future__ import annotations

import json
import logging
import math
import time
import uuid
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

_obs_logger = logging.getLogger("ai-akash.obs")


# ---------------------------------------------------------------------------
# Request record
# ---------------------------------------------------------------------------

@dataclass
class RequestRecord:
    """
    One record per /api/ai-chat request.

    All timing fields are in milliseconds.  None means the stage was skipped
    (e.g. tts_latency_ms is None when voice=False).
    """
    request_id: str
    timestamp: str                          # ISO-8601 UTC
    ip_hash: str                            # sha256[:16] of client IP
    session_id: str | None

    original_query: str
    normalized_query: str

    # Routing
    intent_route: str | None = None         # shortcut name or None
    matched_alias: str | None = None
    similarity_score: float | None = None
    match_type: str | None = None           # "exact" | "similarity" | None

    # Cache
    cache_hit: bool = False
    cache_lookup_ms: float | None = None

    # Pipeline latencies
    retrieval_latency_ms: float | None = None
    embedding_latency_ms: float | None = None
    llm_latency_ms: float | None = None
    tts_latency_ms: float | None = None
    total_latency_ms: float | None = None

    # LLM token usage
    prompt_tokens: int | None = None
    completion_tokens: int | None = None

    # Response
    response_sources: list[str] = field(default_factory=list)
    response_length: int = 0
    retrieved_chunks: int = 0

    # Status
    status: str = "ok"                      # "ok" | "rate_limited" | "error"
    error: str | None = None

    def emit(self) -> None:
        """Write one JSON log line."""
        _obs_logger.info(json.dumps(asdict(self), ensure_ascii=False))


# ---------------------------------------------------------------------------
# Metrics collector
# ---------------------------------------------------------------------------

_RESERVOIR_CAP = 2_000   # keep last N latency samples for percentile math


class MetricsCollector:
    """
    In-process counters and latency reservoir.

    All public attributes are plain ints/floats so they can be read without
    locking.  Writes are GIL-protected in CPython; this is sufficient for a
    single-process deployment.
    """

    def __init__(self) -> None:
        self.total_requests: int = 0
        self.shortcut_hits: int = 0
        self.rag_hits: int = 0
        self.cache_hits: int = 0
        self.rate_limited: int = 0
        self.llm_failures: int = 0
        self.embedding_failures: int = 0
        self.tts_failures: int = 0
        self.errors: int = 0

        self._latencies: deque[float] = deque(maxlen=_RESERVOIR_CAP)   # total_latency_ms samples
        self._chunk_counts: deque[int] = deque(maxlen=_RESERVOIR_CAP)
        self._prompt_sizes: deque[int] = deque(maxlen=_RESERVOIR_CAP)  # prompt_tokens samples

    # --- record helpers ---

    def record_request(self, record: RequestRecord) -> None:
        self.total_requests += 1

        if record.status == "rate_limited":
            self.rate_limited += 1
            return
        if record.status == "error":
            self.errors += 1

        if record.cache_hit:
            self.cache_hits += 1
        elif record.intent_route is not None:
            self.shortcut_hits += 1
        else:
            self.rag_hits += 1

        if record.total_latency_ms is not None:
            self._latencies.append(record.total_latency_ms)

        if record.retrieved_chunks:
            self._chunk_counts.append(record.retrieved_chunks)

        if record.prompt_tokens is not None:
            self._prompt_sizes.append(record.prompt_tokens)

    def record_llm_failure(self) -> None:
        self.llm_failures += 1

    def record_embedding_failure(self) -> None:
        self.embedding_failures += 1

    def record_tts_failure(self) -> None:
        self.tts_failures += 1

    # --- computed metrics ---

    def _percentile(self, data, p: float) -> float | None:
        if not data:
            return None
        sorted_data = sorted(data)
        idx = math.ceil(p / 100 * len(sorted_data)) - 1
        return round(sorted_data[max(idx, 0)], 2)

    @property
    def avg_latency_ms(self) -> float | None:
        if not self._latencies:
            return None
        return round(sum(self._latencies) / len(self._latencies), 2)

    @property
    def p95_latency_ms(self) -> float | None:
        return self._percentile(self._latencies, 95)

    @property
    def p99_latency_ms(self) -> float | None:
        return self._percentile(self._latencies, 99)

    @property
    def avg_retrieved_chunks(self) -> float | None:
        if not self._chunk_counts:
            return None
        return round(sum(self._chunk_counts) / len(self._chunk_counts), 2)

    @property
    def avg_prompt_tokens(self) -> float | None:
        if not self._prompt_sizes:
            return None
        return round(sum(self._prompt_sizes) / len(self._prompt_sizes), 2)

    @property
    def shortcut_hit_rate(self) -> float:
        served = self.total_requests - self.rate_limited
        if served == 0:
            return 0.0
        return round(self.shortcut_hits / served, 4)

    @property
    def rag_hit_rate(self) -> float:
        served = self.total_requests - self.rate_limited
        if served == 0:
            return 0.0
        return round(self.rag_hits / served, 4)

    @property
    def cache_hit_ratio(self) -> float:
        served = self.total_requests - self.rate_limited
        if served == 0:
            return 0.0
        return round(self.cache_hits / served, 4)

    def snapshot(self) -> dict[str, Any]:
        """Return all metrics as a plain dict (used by /metrics JSON)."""
        return {
            "total_requests": self.total_requests,
            "shortcut_hits": self.shortcut_hits,
            "rag_hits": self.rag_hits,
            "cache_hits": self.cache_hits,
            "rate_limited": self.rate_limited,
            "llm_failures": self.llm_failures,
            "embedding_failures": self.embedding_failures,
            "tts_failures": self.tts_failures,
            "errors": self.errors,
            "shortcut_hit_rate": self.shortcut_hit_rate,
            "rag_hit_rate": self.rag_hit_rate,
            "cache_hit_ratio": self.cache_hit_ratio,
            "avg_latency_ms": self.avg_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "avg_retrieved_chunks": self.avg_retrieved_chunks,
            "avg_prompt_tokens": self.avg_prompt_tokens,
        }

    def prometheus_text(self) -> str:
        """
        Render metrics in Prometheus exposition format.

        Each metric gets a HELP comment, a TYPE declaration, and a value line.
        Suitable for scraping by a Prometheus server or Grafana agent.
        """
        snap = self.snapshot()
        lines: list[str] = []

        _metric_meta: list[tuple[str, str, str]] = [
            ("ai_akash_requests_total",        "counter", "Total requests received"),
            ("ai_akash_shortcut_hits_total",   "counter", "Requests answered by shortcut router"),
            ("ai_akash_rag_hits_total",        "counter", "Requests answered by RAG pipeline"),
            ("ai_akash_cache_hits_total",      "counter", "Requests served from LRU cache"),
            ("ai_akash_rate_limited_total",    "counter", "Requests rejected by rate limiter"),
            ("ai_akash_llm_failures_total",    "counter", "LLM generation failures"),
            ("ai_akash_embedding_failures_total", "counter", "Embedding generation failures"),
            ("ai_akash_tts_failures_total",    "counter", "TTS generation failures"),
            ("ai_akash_errors_total",          "counter", "Unhandled errors"),
            ("ai_akash_shortcut_hit_rate",     "gauge",   "Fraction of served requests answered by shortcut"),
            ("ai_akash_rag_hit_rate",          "gauge",   "Fraction of served requests answered by RAG"),
            ("ai_akash_cache_hit_ratio",       "gauge",   "Fraction of served requests from cache"),
            ("ai_akash_avg_latency_ms",        "gauge",   "Average total response latency in ms"),
            ("ai_akash_p95_latency_ms",        "gauge",   "p95 total response latency in ms"),
            ("ai_akash_p99_latency_ms",        "gauge",   "p99 total response latency in ms"),
            ("ai_akash_avg_retrieved_chunks",  "gauge",   "Average number of RAG chunks retrieved"),
            ("ai_akash_avg_prompt_tokens",     "gauge",   "Average prompt token count"),
        ]

        key_map = {
            "ai_akash_requests_total":           "total_requests",
            "ai_akash_shortcut_hits_total":      "shortcut_hits",
            "ai_akash_rag_hits_total":           "rag_hits",
            "ai_akash_cache_hits_total":         "cache_hits",
            "ai_akash_rate_limited_total":       "rate_limited",
            "ai_akash_llm_failures_total":       "llm_failures",
            "ai_akash_embedding_failures_total": "embedding_failures",
            "ai_akash_tts_failures_total":       "tts_failures",
            "ai_akash_errors_total":             "errors",
            "ai_akash_shortcut_hit_rate":        "shortcut_hit_rate",
            "ai_akash_rag_hit_rate":             "rag_hit_rate",
            "ai_akash_cache_hit_ratio":          "cache_hit_ratio",
            "ai_akash_avg_latency_ms":           "avg_latency_ms",
            "ai_akash_p95_latency_ms":           "p95_latency_ms",
            "ai_akash_p99_latency_ms":           "p99_latency_ms",
            "ai_akash_avg_retrieved_chunks":     "avg_retrieved_chunks",
            "ai_akash_avg_prompt_tokens":        "avg_prompt_tokens",
        }

        for prom_name, prom_type, help_text in _metric_meta:
            value = snap.get(key_map[prom_name])
            if value is None:
                value = 0
            lines.append(f"# HELP {prom_name} {help_text}")
            lines.append(f"# TYPE {prom_name} {prom_type}")
            lines.append(f"{prom_name} {value}")

        return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

metrics = MetricsCollector()


def hash_ip(ip: str, salt: str = "") -> str:
    """Return a 16-char hex digest of the IP address mixed with a salt.

    The salt prevents rainbow-table reversal of the small IPv4 address space.
    In production, salt is sourced from settings.ip_hash_salt (required).
    In dev/tests, the default empty salt is accepted.
    """
    return sha256(f"{salt}{ip}".encode()).hexdigest()[:16]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]
