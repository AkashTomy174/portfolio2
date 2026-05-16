import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.services.rag import RagService


BASE_DIR = Path(__file__).resolve().parent
CASES_FILE = BASE_DIR / "retrieval_regression.json"


def main() -> int:
  cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
  rag = RagService(
    knowledge_file=settings.knowledge_file,
    chroma_dir=settings.chroma_dir,
    gemini_api_key=settings.gemini_api_key,
    embedding_model=settings.gemini_embedding_model,
  )
  rag.initialize()

  failures: list[str] = []
  for case in cases:
    results = rag.search(case["query"], top_k=1)
    actual = results[0].topic if results else "<none>"
    expected = case["expected_top_topic"]
    status = "PASS" if actual == expected else "FAIL"
    print(f"{status} | {case['query']} | expected={expected} | actual={actual}")
    if actual != expected:
      failures.append(case["query"])

  if failures:
    print(f"\n{len(failures)} retrieval regression case(s) failed.")
    return 1

  print(f"\nAll {len(cases)} retrieval regression cases passed.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
