import argparse
import json
import re
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.services.rag import RagService, RetrievedChunk


BASE_DIR = Path(__file__).resolve().parent
CASES_FILE = BASE_DIR / "retrieval_regression.json"

# A case passes if at least this fraction of the expected topic's significant
# words appear in the retrieved chunk's combined metadata/text. The cases
# file stores a descriptive bag-of-words per topic (see retrieval_regression.json),
# not a literal chunk id, so exact-id equality is the wrong comparison here.
OVERLAP_THRESHOLD = 0.5


def _words(text: str) -> set[str]:
  return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 2}


def _chunk_bag(chunk: RetrievedChunk) -> set[str]:
  parts = [
    chunk.id,
    chunk.text,
    chunk.category or "",
    chunk.project or "",
    chunk.type or "",
    " ".join(chunk.tags or []),
    " ".join(chunk.aliases or []),
  ]
  return _words(" ".join(parts))


def _topic_overlap(expected_topic: str, chunk: RetrievedChunk | None) -> float:
  if chunk is None:
    return 0.0
  expected_words = _words(expected_topic)
  if not expected_words:
    return 0.0
  return len(expected_words & _chunk_bag(chunk)) / len(expected_words)


def main() -> int:
  parser = argparse.ArgumentParser(description="Run retrieval regression prompts.")
  parser.add_argument(
    "--keyword-only",
    action="store_true",
    help="Skip Gemini/Chroma initialization and test the offline keyword fallback only.",
  )
  args = parser.parse_args()

  cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
  rag = RagService(
    knowledge_file=settings.knowledge_file,
    chroma_dir=settings.chroma_dir,
    gemini_api_key=None if args.keyword_only else settings.gemini_api_key,
    embedding_model=settings.gemini_embedding_model,
  )
  rag.initialize()

  failures: list[str] = []
  for case in cases:
    results = rag.search(case["query"], top_k=1)
    top = results[0] if results else None
    actual_id = top.id if top else "<none>"
    expected_topic = case["expected_top_topic"]
    overlap = _topic_overlap(expected_topic, top)
    status = "PASS" if overlap >= OVERLAP_THRESHOLD else "FAIL"
    print(
      f"{status:4} | {case['query']:<45} | overlap={overlap:.2f} | "
      f"top={actual_id:<25} | expected_topic={expected_topic}"
    )
    if status == "FAIL":
      failures.append(case["query"])

  if failures:
    print(f"\n{len(failures)} retrieval regression case(s) failed.")
    return 1

  print(f"\nAll {len(cases)} retrieval regression cases passed.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())