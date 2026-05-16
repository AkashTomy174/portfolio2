import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.main import (
  _is_assistant_identity_question,
  _is_availability_question,
  _is_greeting,
  _is_profile_identity_question,
)


BASE_DIR = Path(__file__).resolve().parent
CASES_FILE = BASE_DIR / "shortcut_regression.json"


def _classify(query: str) -> str:
  lowered = query.lower()
  if _is_greeting(lowered):
    return "greeting"
  if _is_assistant_identity_question(lowered):
    return "assistant_identity"
  if _is_profile_identity_question(lowered):
    return "profile_identity"
  if _is_availability_question(lowered):
    return "availability"
  if any(keyword in lowered for keyword in ["cv", "resume", "curriculum", "download"]):
    return "resume"
  if any(
    keyword in lowered
    for keyword in ["github", "git hub", "linkedin", "linkedln", "linked in", "contact", "social", "reach", "email", "connect", "phone", "whatsapp"]
  ):
    return "contact"
  return "<none>"


def main() -> int:
  cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
  failures: list[str] = []

  for case in cases:
    actual = _classify(case["query"])
    expected = case["expected_intent"]
    status = "PASS" if actual == expected else "FAIL"
    print(f"{status} | {case['query']} | expected={expected} | actual={actual}")
    if actual != expected:
      failures.append(case["query"])

  if failures:
    print(f"\n{len(failures)} shortcut regression case(s) failed.")
    return 1

  print(f"\nAll {len(cases)} shortcut regression cases passed.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
