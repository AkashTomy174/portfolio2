import json
import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


logger = logging.getLogger("ai-akash")

@dataclass
class RetrievedChunk:
  text: str
  source: str
  topic: str
  score: float


class RagService:
  def __init__(
    self,
    knowledge_file: Path,
    chroma_dir: Path,
    openai_api_key: str | None,
    embedding_model: str,
  ) -> None:
    self.knowledge_file = knowledge_file
    self.chroma_dir = chroma_dir
    self.embedding_model = embedding_model
    self.client = None
    self.chunks = self._load_chunks()
    self.collection = None

  @property
  def ready(self) -> bool:
    return bool(self.chunks)

  def initialize(self) -> None:
    logger.info("RAG initialized with curated keyword/topic retrieval. chunks=%s", len(self.chunks))

  def search(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
    return self._keyword_search(query, top_k)

  def _load_chunks(self) -> list[dict[str, Any]]:
    with self.knowledge_file.open("r", encoding="utf-8") as file:
      data = json.load(file)
    return data["chunks"]

  def _embed(self, text: str) -> list[float]:
    assert self.client is not None
    response = self.client.embeddings.create(model=self.embedding_model, input=text)
    return response.data[0].embedding

  def _embed_many(self, texts: list[str]) -> list[list[float]]:
    assert self.client is not None
    response = self.client.embeddings.create(model=self.embedding_model, input=texts)
    return [item.embedding for item in response.data]

  def _keyword_search(self, query: str, top_k: int) -> list[RetrievedChunk]:
    query_terms = set(_terms(query))
    query_text = query.lower()
    scored: list[RetrievedChunk] = []

    for chunk in self.chunks:
      searchable = f"{chunk['id']} {chunk['source']} {chunk['topic']} {chunk['text']}"
      searchable_lower = searchable.lower()
      chunk_terms = set(_terms(chunk["text"]))
      metadata_terms = set(_terms(f"{chunk['id']} {chunk['source']} {chunk['topic']}"))
      overlap = len(query_terms & chunk_terms)
      metadata_overlap = len(query_terms & metadata_terms)
      phrase_boost = sum(3 for phrase in _phrases(query_text) if phrase in searchable_lower)
      score = (overlap / math.sqrt(max(len(chunk_terms), 1))) + (metadata_overlap * 2) + phrase_boost
      scored.append(
        RetrievedChunk(
          text=chunk["text"],
          source=chunk["source"],
          topic=chunk["topic"],
          score=score,
        )
      )

    scored.sort(key=lambda item: item.score, reverse=True)
    return [item for item in scored[:top_k] if item.score > 0]


def _terms(text: str) -> list[str]:
  return [term for term in re.findall(r"[a-z0-9]+", text.lower()) if len(term) >= 2]


def _phrases(text: str) -> list[str]:
  aliases = {
    "ai judge": ["ai project judge", "project judge", "evaluation system"],
    "project judge": ["ai project judge", "repository evaluation"],
    "token budget": ["token budgeting", "15k token", "ranked file selection"],
    "repo ingestion": ["repository ingestion", "github ingestion", "monorepo"],
    "static analysis": ["deterministic static analysis", "ruff", "eslint", "radon"],
    "celery": ["async worker", "queue", "long-running"],
    "redis": ["cache", "broker", "ttl"],
    "backend judgment": ["select_for_update", "race condition", "query optimization"],
    "easybuy": ["payment", "overselling", "e-commerce"],
  }

  phrases = [text.strip()]
  for key, values in aliases.items():
    if key in text:
      phrases.extend(values)
  return [phrase for phrase in phrases if phrase]
