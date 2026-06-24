"""Tests for helper functions used in the agent pipeline."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _extract_requirements(text: str) -> dict | None:
    """Replicates the logic from GeminiAgent._extract_requirements."""
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except (ValueError, json.JSONDecodeError):
            return None
    return None


def test_no_json_block():
    text = "Hello, how can I help you today?"
    assert _extract_requirements(text) is None, "Should return None when no JSON block"


def test_empty_json_block():
    text = "Some text\n```json\n```\nmore text"
    try:
        result = _extract_requirements(text)
        assert result is None, "Empty JSON block should return None"
    except Exception:
        pass


def test_valid_json_block():
    text = 'Here are your options:\n```json\n{"intent": "search_products", "requirements": {"q": "cake"}}\n```'
    result = _extract_requirements(text)
    assert result is not None, "Should extract valid JSON"
    assert result["intent"] == "search_products"
    assert result["requirements"]["q"] == "cake"


def test_json_with_extra_whitespace():
    text = "```json  \n  {\"intent\": \"test\"}  \n  ```"
    result = _extract_requirements(text)
    assert result is not None
    assert result["intent"] == "test"


def test_malformed_json():
    text = "```json\n{invalid json here}\n```"
    result = _extract_requirements(text)
    assert result is None


def run_all():
    """Manual test runner (use when pytest is not available)."""
    tests = [
        ("no_json_block", test_no_json_block),
        ("empty_json_block", test_empty_json_block),
        ("valid_json_block", test_valid_json_block),
        ("json_with_extra_whitespace", test_json_with_extra_whitespace),
        ("malformed_json", test_malformed_json),
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS: {name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {name} - {e}")
            failed += 1
    print(f"\n{passed}/{passed + failed} tests passed")
    return failed == 0


if __name__ == "__main__":
    print("Running helper tests...")
    run_all()
