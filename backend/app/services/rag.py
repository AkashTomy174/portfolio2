from __future__ import annotations

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

# ---------------------------------------------------------------------------
# Relevance thresholds
# ---------------------------------------------------------------------------
# Chunks scoring below these values are considered noise and dropped before
# being passed to the LLM.  The LLM receives an empty list → short-circuit
# fallback fires in llm.py → no hallucination is possible.
#
# How to tune:
#   Enable DEBUG logging and watch the "rag_search" log lines in production.
#   Collect top_score values for:
#     - Known on-topic queries  ("where did he intern", "what is easybuy")
#     - Known off-topic queries ("what's the weather", "who is his mother")
#   Pick the cutoff that cleanly separates the two distributions.
#
# A relative threshold is used to adapt to different query types.
RELATIVE_THRESHOLD_RATIO: float = 0.8

# Hybrid mode  (vector + keyword merged, _merge_results output):
MIN_RELEVANCE_SCORE: float = 0.35
# Keyword-only mode (no Gemini API key or ChromaDB available):
MIN_KEYWORD_SCORE: float = 1.0


@dataclass
class RetrievedChunk:
  id: str
  text: str
  source: str
  score: float
  category: str | None = None
  project: str | None = None
  type: str | None = None
  importance: int = 1
  status: str | None = None
  tags: list[str] | None = None
  aliases: list[str] | None = None


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
    except Exception as exc:
      logger.warning("Vector retrieval unavailable; using keyword retrieval only. error=%s", exc)
      return

    try:
      self.client = genai.Client(api_key=self.gemini_api_key)
      self.chroma_dir.mkdir(parents=True, exist_ok=True)
      chroma_client = chromadb.PersistentClient(path=str(self.chroma_dir))
      self.collection = chroma_client.get_or_create_collection(
        name="akash-knowledge-gemini",
        metadata={"description": "Akash portfolio knowledge chunks using Gemini embeddings"},
      )
      self._sync_collection()
    except Exception:
      logger.exception("Vector retrieval initialization failed; using keyword retrieval only.")
      self.client = None
      self.collection = None
      return

    logger.info(
      "RAG initialized with hybrid retrieval. chunks=%s indexed=%s",
      len(self.chunks),
      self.collection.count(),
    )

  def search(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
    query = _normalize_query(query)
    keyword_results = self._keyword_search(query, top_k=max(top_k * 2, top_k))
    if not self.collection or not self.client:
      results = [c for c in keyword_results[:top_k] if c.score >= MIN_KEYWORD_SCORE]
    else:
      vector_results = self._vector_search(query, top_k=max(top_k * 2, 8))
      merged = self._merge_results(keyword_results, vector_results, top_k)
      if not merged:
          results = []
      else:
          top_score = merged[0].score
          min_score = max(MIN_RELEVANCE_SCORE, top_score * RELATIVE_THRESHOLD_RATIO)
          results = [c for c in merged if c.score >= min_score]

    top_score = results[0].score if results else 0.0
    logger.debug(
      "rag_search query=%r chunks_returned=%d top_score=%.3f threshold=%s",
      query,
      len(results),
      top_score,
      f"relative > {top_score * RELATIVE_THRESHOLD_RATIO:.2f}" if self.collection and self.client else f"keyword > {MIN_KEYWORD_SCORE}",
    )
    return results

  def _load_chunks(self) -> list[dict[str, Any]]:
    with self.knowledge_file.open("r", encoding="utf-8") as file:
      data = json.load(file)
    return data["chunks"]

  def _embed(self, text: str) -> list[float]:
    if self.client is None:
      raise RuntimeError(
        "RagService._embed called but Gemini client is not initialised. "
        "Call initialize() first and ensure GEMINI_API_KEY is set."
      )
    response = self.client.models.embed_content(
      model=self.embedding_model,
      contents=text,
      config=types.EmbedContentConfig(output_dimensionality=768),
    )
    return response.embeddings[0].values

  def _embed_many(self, texts: list[str]) -> list[list[float]]:
    if self.client is None:
      raise RuntimeError(
        "RagService._embed_many called but Gemini client is not initialised. "
        "Call initialize() first and ensure GEMINI_API_KEY is set."
      )
    response = self.client.models.embed_content(
      model=self.embedding_model,
      contents=texts,
      config=types.EmbedContentConfig(output_dimensionality=768),
    )
    return [item.values for item in response.embeddings]

  def _sync_collection(self) -> None:
    if self.collection is None:
      raise RuntimeError(
        "RagService._sync_collection called but ChromaDB collection is not "
        "initialised. Call initialize() first."
      )
    ids = [chunk["id"] for chunk in self.chunks]
    existing_ids = set(self.collection.get().get("ids", []))
    stale_ids = sorted(existing_ids - set(ids))
    if stale_ids:
      self.collection.delete(ids=stale_ids)

    documents = [chunk["text"] for chunk in self.chunks]
    metadatas = [
      {
        # ChromaDB metadata values must be str, int, float, or bool.
        # We serialize lists into JSON strings.
        "source": chunk["source"],
        "category": chunk.get("category"),
        "project": chunk.get("project"),
        "type": chunk.get("type"),
        "importance": chunk.get("importance", 1),
        "status": chunk.get("status"),
        "tags": json.dumps(chunk.get("tags", [])),
        "aliases": json.dumps(chunk.get("aliases", [])),
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
    if self.collection is None:
      raise RuntimeError(
        "RagService._vector_search called but ChromaDB collection is not "
        "initialised. Call initialize() first."
      )
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
      
      # Safely deserialize tags and aliases from metadata
      tags_str = (metadata or {}).get("tags", "[]")
      aliases_str = (metadata or {}).get("aliases", "[]")
      
      retrieved.append(
        RetrievedChunk(
          id=chunk_id,
          text=document or chunk["text"],
          source=(metadata or {}).get("source", chunk["source"]),
          score=_distance_to_similarity(distance),
          category=(metadata or {}).get("category"),
          importance=(metadata or {}).get("importance", 1),
          tags=json.loads(tags_str) if tags_str else [],
          aliases=json.loads(aliases_str) if aliases_str else [],
        )
      )
    return retrieved

  def _merge_results(
    self,
    keyword_results: list[RetrievedChunk],
    vector_results: list[RetrievedChunk],
    top_k: int,
  ) -> list[RetrievedChunk]:
    # Reciprocal Rank Fusion (RRF)
    # See: https://plg.uwaterloo.ca/~gvcormac/cormack_fusion.pdf
    k = 60  # RRF constant, typically 60
    
    ranked_lists = [keyword_results, vector_results]
    rrf_scores: dict[str, float] = {}
    
    for ranked_list in ranked_lists:
        for rank, chunk in enumerate(ranked_list, start=1):
            if chunk.id not in rrf_scores:
                rrf_scores[chunk.id] = 0.0
            rrf_scores[chunk.id] += 1 / (k + rank)
            
    # Create a unified set of chunks from both lists
    all_chunks = {chunk.id: chunk for chunk in keyword_results}
    all_chunks.update({chunk.id: chunk for chunk in vector_results})
    
    # Assign the new RRF score to each chunk
    for chunk_id, score in rrf_scores.items():
        if chunk_id in all_chunks:
            all_chunks[chunk_id].score = score
            
    merged_chunks = list(all_chunks[chunk_id] for chunk_id in rrf_scores)
    return sorted(merged_chunks, key=lambda c: c.score, reverse=True)[:top_k]

  def _keyword_search(self, query: str, top_k: int) -> list[RetrievedChunk]:
    query_terms = set(_terms(query))
    query_text = query.lower()
    scored: list[RetrievedChunk] = []

    for chunk in self.chunks:
      tags = chunk.get("tags", [])
      aliases = chunk.get("aliases", [])
      searchable = f"{chunk['id']} {chunk['source']} {chunk.get('project', '')} {chunk.get('category', '')} {chunk.get('type', '')} {' '.join(tags)} {' '.join(aliases)} {chunk['text']}"
      searchable_lower = searchable.lower()
      chunk_terms = set(_terms(chunk["text"]))
      tag_terms = set(_terms(' '.join(tags)))
      alias_terms = set(_terms(' '.join(aliases)))

      overlap = len(query_terms & chunk_terms)
      tag_overlap = len(query_terms & tag_terms)
      alias_overlap = len(query_terms & alias_terms)
      phrase_boost = sum(3 for phrase in _phrases(query_text) if phrase in searchable_lower)
      
      # New scoring: heavily weight alias and tag matches
      score = (
          (overlap / math.sqrt(max(len(chunk_terms), 1)))  # Text overlap (normalized)
          + (tag_overlap * 3)  # High weight for tag matches
          + (alias_overlap * 5)  # Highest weight for alias matches
          + phrase_boost
          + (chunk.get("importance", 1) * 0.3) # Boost for importance
      )
      
      scored.append(
        RetrievedChunk(
            id=chunk["id"],
            text=chunk["text"],
            source=chunk["source"],
            score=score,
            category=chunk.get("category"),
            project=chunk.get("project"),
            type=chunk.get("type"),
            importance=chunk.get("importance", 1),
            status=chunk.get("status"),
            tags=chunk.get("tags", []),
            aliases=chunk.get("aliases", []),
        )
      )

    scored.sort(key=lambda item: item.score, reverse=True)
    return [item for item in scored[:top_k] if item.score > 0]


def _terms(text: str) -> list[str]:
  return [term for term in re.findall(r"[a-z0-9]+", text.lower()) if len(term) >= 2]


def _phrases(text: str) -> list[str]:
  phrases = [text.strip()]
  return [phrase for phrase in phrases if phrase]


def _distance_to_similarity(distance: float | None) -> float:
  if distance is None:
    return 0.0
  return 1 / (1 + max(distance, 0.0))


def _load_query_aliases() -> dict[str, str]:
    alias_path = Path(__file__).parent.parent.parent / "knowledge_base" / "query_aliases.json"
    if not alias_path.exists():
        return {}
    with alias_path.open("r", encoding="utf-8") as f:
        return json.load(f)

_query_aliases = _load_query_aliases()

def _normalize_query(query: str) -> str:
  normalized = " ".join(query.lower().split())
  replacements = _query_aliases
  for source, target in replacements.items():
    normalized = normalized.replace(source, target)
  return normalized
