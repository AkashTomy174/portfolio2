import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.intents import match_intent, normalize_query


BASE_DIR = Path(__file__).resolve().parent
CASES_FILE = BASE_DIR / "shortcut_regression.json"

def main() -> int:
  cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
  failures: list[str] = []

  for case in cases:
    normalized = normalize_query(case["query"])
    match = match_intent(normalized)
    actual = match.route.name if match else "<none>"
    expected = case["expected_intent"]
    status = "PASS" if actual == expected else "FAIL"
    print(f"{status:4} | {case['query']:<40} | expected={expected:<20} | actual={actual:<20}")
    if actual != expected:
      failures.append(case["query"])

  if failures:
    print(f"\n{len(failures)} shortcut regression case(s) failed.")
    return 1

  print(f"\nAll {len(cases)} shortcut regression cases passed.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
