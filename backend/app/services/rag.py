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
    try:
      import chromadb
    except ImportError:
      return

    self.chroma_dir.mkdir(parents=True, exist_ok=True)
    chroma = chromadb.PersistentClient(path=str(self.chroma_dir))
    self.collection = chroma.get_or_create_collection(name="ai_akash")

    existing = self.collection.count()
    if existing >= len(self.chunks):
      return

    ids = [chunk["id"] for chunk in self.chunks]
    texts = [chunk["text"] for chunk in self.chunks]
    metadatas = [{"source": chunk["source"], "topic": chunk["topic"]} for chunk in self.chunks]
    try:
      embeddings = self._embed_many(texts)
    except OpenAIError as exc:
      logger.warning("OpenAI embeddings failed during RAG initialization; using keyword search. error=%s", exc)
      self.collection = None
      return

    self.collection.upsert(
      ids=ids,
      documents=texts,
      metadatas=metadatas,
      embeddings=embeddings,
    )

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
    scored: list[RetrievedChunk] = []

    for chunk in self.chunks:
      chunk_terms = set(_terms(chunk["text"]))
      metadata_terms = set(_terms(f"{chunk['source']} {chunk['topic']}"))
      overlap = len(query_terms & chunk_terms)
      metadata_overlap = len(query_terms & metadata_terms)
      score = (overlap / math.sqrt(max(len(chunk_terms), 1))) + (metadata_overlap * 2)
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
