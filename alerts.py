
"""Rule-based alerts for SYNTHETIC control-test data."""

import pandas as pd


def consecutive_failures(tests, report_date):
    """Return control IDs whose two latest tests both failed."""

    report_date = pd.Timestamp(report_date)

    history = tests.copy()
    history["test_date"] = pd.to_datetime(
        history["test_date"],
        errors="raise"
    )

    # Exclude tests occurring after the reporting date.
    history = history.loc[
        history["test_date"].le(report_date)
    ]

    # Put each control's tests in chronological order.
    history = history.sort_values(
        ["control_id", "test_date", "test_id"]
    )

    # Keep the most recent two tests for each control.
    latest_two = history.groupby(
        "control_id",
        group_keys=False
    ).tail(2)

    # Trigger only when there are two tests and both failed.
    summary = latest_two.groupby("control_id").agg(
        test_count=("result", "size"),
        fail_count=("result", lambda x: x.eq("Fail").sum())
    )

    return summary.loc[
        summary["test_count"].eq(2)
        &
        summary["fail_count"].eq(2)
    ].index.tolist()
