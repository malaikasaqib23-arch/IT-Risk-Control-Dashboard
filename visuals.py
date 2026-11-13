"""Presentation only: neon palette and charts over existing SYNTHETIC measures."""
import plotly.graph_objects as go
import plotly.io as pio
from plotly.colors import sample_colorscale

CYAN = "#22D3EE"
VIOLET = "#8B5CF6"
PINK = "#F472B6"
AMBER = "#FBBF24"
PALETTE = [CYAN, VIOLET, PINK, "#3B82F6", "#2DD4BF", AMBER]
SEVERITY = {"Low": CYAN, "Medium": VIOLET, "High": AMBER, "Critical": PINK}
RESULTS = {"Pass": CYAN, "Partial": AMBER, "Fail": PINK, "Never tested": "#64748B"}

pio.templates["risk_neon"] = go.layout.Template(layout=dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Segoe UI, Arial, sans-serif", color="#E8ECFF", size=12),
    colorway=PALETTE, margin=dict(l=35, r=25, t=35, b=40),
    xaxis=dict(gridcolor="#252A48", zerolinecolor="#343A60", linecolor="#343A60"),
    yaxis=dict(gridcolor="#252A48", zerolinecolor="#343A60", linecolor="#343A60"),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.12, x=0),
    hoverlabel=dict(bgcolor="#191D38", bordercolor=VIOLET, font_color="#F4F6FF"),
    polar=dict(bgcolor="rgba(0,0,0,0)",
               radialaxis=dict(gridcolor="#303553", linecolor="#303553", range=[0, 100]),
               angularaxis=dict(gridcolor="#303553", linecolor="#303553"))
))


def style_chart(figure):
    figure.update_layout(template="risk_neon")
    return figure


def outcome_donut(health):
    """Latest results, one count per selected control; not historical pass rate."""
    labels = list(RESULTS)
    results = health["result"].fillna("Never tested")
    values = [int(results.eq(label).sum()) for label in labels]
    figure = go.Figure(go.Pie(labels=labels, values=values, hole=.74, sort=False,
                              marker=dict(colors=list(RESULTS.values()), line=dict(color="#10142B", width=4)),
                              textinfo="none", hovertemplate="%{label}: %{value} controls<extra></extra>"))
    figure.update_layout(height=340, annotations=[dict(text=f"<b>{len(health)}</b><br>controls",
                                                        x=.5, y=.5, font_size=22, showarrow=False)])
    return style_chart(figure)


def incident_area(trend):
    figure = go.Figure(go.Scatter(x=trend["Month"], y=trend["Total"], mode="lines+markers",
                                  line=dict(color=CYAN, width=3), marker=dict(size=7, color=CYAN),
                                  fill="tozeroy", fillcolor="rgba(34,211,238,.13)",
                                  hovertemplate="%{x}: %{y} incidents<extra></extra>"))
    figure.update_layout(height=300, yaxis_title="Incident count", xaxis_title="Month")
    return style_chart(figure)


def function_radar(by_function):
    names = by_function["csf_function"].tolist()
    values = by_function["health_score"].tolist()
    figure = go.Figure()
    if names:
        figure.add_trace(go.Scatterpolar(theta=names + names[:1], r=values + values[:1],
                                          fill="toself", fillcolor="rgba(139,92,246,.2)",
                                          line=dict(color=VIOLET, width=3), marker=dict(color=CYAN, size=7),
                                          mode="lines+markers", hovertemplate="%{theta}: %{r:.2f}%<extra></extra>"))
    figure.update_layout(height=360, showlegend=False)
    return style_chart(figure)


def risk_donut(open_risks):
    bands = list(SEVERITY)
    figure = go.Figure(go.Pie(labels=bands, values=[int(open_risks["risk_level"].eq(b).sum()) for b in bands],
                              hole=.72, sort=False, textinfo="none",
                              marker=dict(colors=[SEVERITY[b] for b in bands], line=dict(color="#10142B", width=4)),
                              hovertemplate="%{label}: %{value} open risks<extra></extra>"))
    figure.update_layout(height=330, annotations=[dict(text=f"<b>{len(open_risks)}</b><br>open risks",
                                                        x=.5, y=.5, font_size=22, showarrow=False)])
    return style_chart(figure)


def rounded_risk_heatmap(grid):
    """Rounded tiles; the blue/white/coral scale encodes counts, never severity."""
    scale = [[0, "#275C83"], [.25, "#62B8DB"], [.5, "#F3F6F7"],
             [.75, "#F7B9C3"], [1, "#ED6B83"]]
    impacts = [1, 2, 3, 4, 5]
    likelihoods = [5, 4, 3, 2, 1]
    values = grid.reindex(index=likelihoods, columns=impacts, fill_value=0).fillna(0)
    maximum = max(1, int(values.to_numpy().max()))
    # A transparent heatmap preserves full-cell hover targets and exact values.
    figure = go.Figure(go.Heatmap(
        x=impacts, y=likelihoods, z=values.to_numpy(), showscale=False,
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
        hovertemplate="Impact: %{x}<br>Likelihood: %{y}<br>Open risks: %{z}<extra></extra>"))
    xs, ys, counts = [], [], []
    for likelihood in likelihoods:
        for impact in impacts:
            count = int(values.loc[likelihood, impact])
            ratio = count / maximum
            fill = sample_colorscale(scale, [ratio])[0]
            x0, x1 = impact - .445, impact + .445
            y0, y1 = likelihood - .445, likelihood + .445
            radius = .14
            path = (f"M {x0+radius},{y0} L {x1-radius},{y0} "
                    f"Q {x1},{y0} {x1},{y0+radius} L {x1},{y1-radius} "
                    f"Q {x1},{y1} {x1-radius},{y1} L {x0+radius},{y1} "
                    f"Q {x0},{y1} {x0},{y1-radius} L {x0},{y0+radius} "
                    f"Q {x0},{y0} {x0+radius},{y0} Z")
            figure.add_shape(type="path", path=path, fillcolor=fill,
                             line=dict(width=0), layer="below")
            figure.add_annotation(x=impact, y=likelihood, text=str(count),
                                  showarrow=False, font=dict(size=17,
                                      color="#F6FAFF" if ratio < .2 else "#182C44"))
            xs.append(impact)
            ys.append(likelihood)
            counts.append(count)
    # Invisible markers supply the continuous count legend without square tiles.
    figure.add_trace(go.Scatter(x=xs, y=ys, mode="markers", hoverinfo="skip",
        marker=dict(size=.1, opacity=0, color=counts, colorscale=scale,
                    cmin=0, cmax=maximum, showscale=True,
                    colorbar=dict(title="Open risk<br>count", thickness=11, len=.84,
                                  outlinewidth=0, dtick=max(1, (maximum + 4) // 5), tickformat="d")), showlegend=False))
    # Large, almost transparent point targets add native Plotly cell selection.
    # The dropdowns remain an accessible fallback; the matrix values are unchanged.
    figure.add_trace(go.Scatter(x=xs, y=ys, mode="markers",
        customdata=list(zip(ys, xs)), text=counts,
        marker=dict(size=48, symbol="square", color="rgba(255,255,255,0.005)"),
        selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1)),
        hovertemplate="Impact: %{x}<br>Likelihood: %{y}<br>Open risks: %{text}<extra></extra>",
        showlegend=False))
    figure.update_layout(height=430, margin=dict(l=55, r=45, t=20, b=45),
        clickmode="event+select", dragmode=False,
        xaxis=dict(title="Impact", tickmode="array", tickvals=impacts,
                   range=[.45, 5.55], showgrid=False, zeroline=False, fixedrange=True),
        yaxis=dict(title="Likelihood", tickmode="array", tickvals=impacts,
                   range=[.45, 5.55], showgrid=False, zeroline=False, fixedrange=True))
    return style_chart(figure)
