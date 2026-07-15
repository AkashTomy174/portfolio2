import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.services.llm import _looks_incomplete


BASE_DIR = Path(__file__).resolve().parent
CASES_FILE = BASE_DIR / "generation_quality_regression.json"


def main() -> int:
  cases = json.loads(CASES_FILE.read_text(encoding="utf-8"))
  failures: list[str] = []

  for case in cases:
    actual = _looks_incomplete(case["text"])
    expected = case["expected_incomplete"]
    status = "PASS" if actual == expected else "FAIL"
    print(f"{status} | {case['label']} | expected={expected} | actual={actual}")
    if actual != expected:
      failures.append(case["label"])

  if failures:
    print(f"\n{len(failures)} generation quality regression case(s) failed.")
    return 1

  print(f"\nAll {len(cases)} generation quality regression cases passed.")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
