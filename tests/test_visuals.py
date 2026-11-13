"""Verify chart totals and scales against hand-checkable examples."""
import pandas as pd
import pytest

from visuals import outcome_donut, risk_donut, incident_area, function_radar
from visuals import rounded_risk_heatmap


@pytest.mark.parametrize("results,expected", [
    (["Pass", "Pass", "Partial"], [2, 1, 0, 0]),
    (["Fail", None, "Pass"], [1, 0, 1, 1]),
    ([], [0, 0, 0, 0]),
])
def test_outcome_chart_counts(results, expected):
    fig = outcome_donut(pd.DataFrame({"result": results}))
    assert list(fig.data[0].values) == expected
    assert sum(fig.data[0].values) == len(results)


@pytest.mark.parametrize("bands,expected", [
    (["Low", "High", "High"], [1, 0, 2, 0]),
    (["Critical", "Medium"], [0, 1, 0, 1]),
    ([], [0, 0, 0, 0]),
])
def test_risk_chart_counts(bands, expected):
    fig = risk_donut(pd.DataFrame({"risk_level": bands}))
    assert list(fig.data[0].values) == expected


def test_area_uses_exact_monthly_totals():
    trend = pd.DataFrame({"Month": ["2026-08", "2026-09", "2026-10"], "Total": [7, 30, 5]})
    fig = incident_area(trend)
    assert list(fig.data[0].y) == [7, 30, 5]
    assert fig.data[0].line.shape is None  # Straight lines do not invent intermediate peaks.


def test_radar_preserves_averages_and_fixed_scale():
    data = pd.DataFrame({"csf_function": ["Detect", "Protect", "Govern"], "health_score": [0, 50, 100]})
    fig = function_radar(data)
    assert list(fig.data[0].r) == [0, 50, 100, 0]
    assert list(fig.data[0].theta) == ["Detect", "Protect", "Govern", "Detect"]
    assert list(fig.layout.template.layout.polar.radialaxis.range) == [0, 100]


def test_empty_radar_does_not_fail():
    assert not function_radar(pd.DataFrame(columns=["csf_function", "health_score"])).data


@pytest.mark.parametrize("count", [0, 2, 5])
def test_rounded_heatmap_keeps_exact_cell_counts_and_hover(count):
    grid = pd.DataFrame(0, index=[5, 4, 3, 2, 1], columns=[1, 2, 3, 4, 5])
    grid.loc[5, 1] = count
    figure = rounded_risk_heatmap(grid)
    assert figure.data[0].z[0][0] == count
    assert sum(sum(row) for row in figure.data[0].z) == count
    assert figure.layout.annotations[0].text == str(count)
    assert len(figure.layout.shapes) == 25
    assert all("Q" in shape.path for shape in figure.layout.shapes)
    assert "%{z}" in figure.data[0].hovertemplate
    assert figure.data[1].marker.colorbar.dtick >= 1
