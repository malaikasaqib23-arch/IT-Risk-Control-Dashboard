
"""Unit tests for synthetic control alert rules."""

import pandas as pd

from alerts import consecutive_failures


def make_tests(results):
    """Create synthetic test records for one control."""
    return pd.DataFrame({
        "control_id": ["CTRL-TEST"] * len(results),
        "test_id": [
            f"TEST-{i:03d}"
            for i in range(1, len(results) + 1)
        ],
        "test_date": pd.date_range(
            "2026-01-01",
            periods=len(results),
            freq="D"
        ),
        "result": results,
    })


def test_two_latest_failures_trigger():
    tests = make_tests(["Pass", "Fail", "Fail"])

    result = consecutive_failures(tests, "2026-10-31")

    assert result == ["CTRL-TEST"]


def test_interrupted_failures_do_not_trigger():
    tests = make_tests(["Fail", "Pass", "Fail"])

    result = consecutive_failures(tests, "2026-10-31")

    assert result == []


def test_latest_pass_does_not_trigger():
    tests = make_tests(["Fail", "Fail", "Pass"])

    result = consecutive_failures(tests, "2026-10-31")

    assert result == []


def test_single_failure_does_not_trigger():
    tests = make_tests(["Fail"])

    result = consecutive_failures(tests, "2026-10-31")

    assert result == []


def test_future_tests_are_excluded():
    tests = pd.DataFrame({
        "control_id": ["CTRL-TEST"] * 3,
        "test_id": ["TEST-001", "TEST-002", "TEST-003"],
        "test_date": [
            "2026-10-01",
            "2026-10-02",
            "2026-11-01"
        ],
        "result": ["Fail", "Fail", "Pass"],
    })

    result = consecutive_failures(tests, "2026-10-31")

    assert result == ["CTRL-TEST"]
