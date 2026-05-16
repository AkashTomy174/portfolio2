import json
import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from google import genai
from google.genai import types


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
    gemini_api_key: str | None,
    embedding_model: str,
  ) -> None:
    self.knowledge_file = knowledge_file
    self.chroma_dir = chroma_dir
    self.gemini_api_key = gemini_api_key
    self.embedding_model = embedding_model
    self.client = None
    self.chunks = self._load_chunks()
    self.collection = None
    self._chunks_by_id = {chunk["id"]: chunk for chunk in self.chunks}

  @property
  def ready(self) -> bool:
    return bool(self.chunks)

  def initialize(self) -> None:
    if not self.gemini_api_key:
      logger.info("RAG initialized with curated keyword/topic retrieval only. chunks=%s", len(self.chunks))
      return

    try:
      import chromadb
    except ImportError as exc:
      logger.warning("Vector retrieval unavailable; using keyword retrieval only. error=%s", exc)
      return

    self.client = genai.Client(api_key=self.gemini_api_key)
    self.chroma_dir.mkdir(parents=True, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=str(self.chroma_dir))
    self.collection = chroma_client.get_or_create_collection(
      name="akash-knowledge-gemini",
      metadata={"description": "Akash portfolio knowledge chunks using Gemini embeddings"},
    )
    self._sync_collection()
    logger.info(
      "RAG initialized with hybrid retrieval. chunks=%s indexed=%s",
      len(self.chunks),
      self.collection.count(),
    )

  def search(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
    query = _normalize_query(query)
    keyword_results = self._keyword_search(query, top_k=max(top_k * 2, top_k))
    if not self.collection or not self.client:
      return keyword_results[:top_k]

    vector_results = self._vector_search(query, top_k=max(top_k * 2, top_k))
    return self._merge_results(keyword_results, vector_results, top_k)

  def _load_chunks(self) -> list[dict[str, Any]]:
    with self.knowledge_file.open("r", encoding="utf-8") as file:
      data = json.load(file)
    return data["chunks"]

  def _embed(self, text: str) -> list[float]:
    assert self.client is not None
    response = self.client.models.embed_content(
      model=self.embedding_model,
      contents=text,
      config=types.EmbedContentConfig(output_dimensionality=768),
    )
    return response.embeddings[0].values

  def _embed_many(self, texts: list[str]) -> list[list[float]]:
    assert self.client is not None
    response = self.client.models.embed_content(
      model=self.embedding_model,
      contents=texts,
      config=types.EmbedContentConfig(output_dimensionality=768),
    )
    return [item.values for item in response.embeddings]

  def _sync_collection(self) -> None:
    assert self.collection is not None
    ids = [chunk["id"] for chunk in self.chunks]
    existing_ids = set(self.collection.get().get("ids", []))
    stale_ids = sorted(existing_ids - set(ids))
    if stale_ids:
      self.collection.delete(ids=stale_ids)

    documents = [chunk["text"] for chunk in self.chunks]
    metadatas = [
      {
        "source": chunk["source"],
        "topic": chunk["topic"],
      }
      for chunk in self.chunks
    ]
    embeddings = self._embed_many(documents)
    self.collection.upsert(
      ids=ids,
      embeddings=embeddings,
      documents=documents,
      metadatas=metadatas,
    )

  def _vector_search(self, query: str, top_k: int) -> list[RetrievedChunk]:
    assert self.collection is not None
    query_embedding = self._embed(query)
    results = self.collection.query(
      query_embeddings=[query_embedding],
      n_results=top_k,
      include=["documents", "metadatas", "distances"],
    )

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    retrieved: list[RetrievedChunk] = []

    for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
      chunk = self._chunks_by_id.get(chunk_id)
      if not chunk:
        continue
      retrieved.append(
        RetrievedChunk(
          text=document or chunk["text"],
          source=(metadata or {}).get("source", chunk["source"]),
          topic=(metadata or {}).get("topic", chunk["topic"]),
          score=_distance_to_similarity(distance),
        )
      )
    return retrieved

  def _merge_results(
    self,
    keyword_results: list[RetrievedChunk],
    vector_results: list[RetrievedChunk],
    top_k: int,
  ) -> list[RetrievedChunk]:
    merged: dict[tuple[str, str, str], RetrievedChunk] = {}

    for item in vector_results:
      key = (item.text, item.source, item.topic)
      merged[key] = RetrievedChunk(
        text=item.text,
        source=item.source,
        topic=item.topic,
        score=item.score * 0.7,
      )

    for item in keyword_results:
      key = (item.text, item.source, item.topic)
      if key in merged:
        merged[key].score += item.score * 0.3
      else:
        merged[key] = RetrievedChunk(
          text=item.text,
          source=item.source,
          topic=item.topic,
          score=item.score * 0.3,
        )

    return sorted(merged.values(), key=lambda item: item.score, reverse=True)[:top_k]

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


def _distance_to_similarity(distance: float | None) -> float:
  if distance is None:
    return 0.0
  return 1 / (1 + max(distance, 0.0))


def _normalize_query(query: str) -> str:
  normalized = " ".join(query.lower().split())
  replacements = {
    "heworth": "he worth",
    "worth my time": "why should we hire akash",
    "main strengths": "strongest technical skill",
    "main strength": "strongest technical skill",
  }
  for source, target in replacements.items():
    normalized = normalized.replace(source, target)
  return normalized
