
"""Rule-based alerts for SYNTHETIC control-test data."""

import pandas as pd

from monitoring import normalized, OPEN


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


def missing_risk_owners(risks):
    """Open High/Critical records with a blank risk owner (no control-owner fallback)."""
    return risks.loc[normalized(risks["status"]).isin(OPEN)
                     & risks["risk_level"].isin(["High", "Critical"])
                     & normalized(risks["owner"]).eq("")].copy()


def incident_spikes(incidents, report_date, observation_start, multiplier=2.0, minimum=10):
    """Full months only; >= minimum and >= multiplier times previous 3-month mean.

    Design choices pending supervisor approval. Use full observed history before
    applying the UI event range to the returned month, so filters do not change
    the reference average. Months without three fully observed predecessors skip.
    """
    if multiplier <= 1 or minimum < 1:
        raise ValueError("Spike multiplier must exceed 1 and minimum must be positive")
    end = pd.Timestamp(report_date).normalize()
    start = pd.Timestamp(observation_start).normalize()
    first = start.to_period("M")
    if start.day != 1:
        first += 1
    last = end.to_period("M")
    if end < last.end_time.normalize():
        last -= 1
    periods = pd.period_range(first, last, freq="M")
    dates = pd.to_datetime(incidents["incident_date"])
    counts = dates.loc[dates.between(start, end)].dt.to_period("M").value_counts().reindex(periods, fill_value=0)
    rows = []
    for i in range(3, len(periods)):
        previous = counts.iloc[i-3:i]
        baseline = float(previous.sum() / 3)
        count = int(counts.iloc[i])
        if count >= minimum and count >= multiplier * baseline:
            rows.append({"month": str(periods[i]), "count": count,
                         "previous_3_total": int(previous.sum()),
                         "baseline": baseline, "threshold": max(minimum, multiplier * baseline)})
    return pd.DataFrame(rows, columns=["month", "count", "previous_3_total", "baseline", "threshold"])
