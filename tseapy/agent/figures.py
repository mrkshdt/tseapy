"""On-demand Plotly figure construction for agent findings.

The agent stores only lightweight :class:`~tseapy.agent.findings.Finding`
metadata. When the user opens a finding card, the frontend asks for its figure
and *this* module builds it lazily from the finding's ``figure_spec`` plus the
original dataset. Nothing is rendered until it is requested.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from tseapy.agent.findings import Finding


def _series(data: pd.DataFrame, feature: str) -> pd.Series:
    series = pd.to_numeric(data[feature], errors="coerce")
    return series.replace([np.inf, -np.inf], np.nan).dropna()


def build_figure(finding: Finding, data: pd.DataFrame) -> go.Figure:
    """Return a Plotly figure visualising ``finding`` against ``data``."""
    spec = finding.figure_spec or {}
    builder = _BUILDERS.get(spec.get("type"))
    if builder is None:
        raise ValueError(f"No figure builder for finding type {spec.get('type')!r}")
    fig = builder(spec, data)
    fig.update_layout(
        title=finding.title,
        template="plotly_white",
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def _line(series: pd.Series, name: str) -> go.Scatter:
    return go.Scatter(x=series.index, y=series.to_numpy(), mode="lines", name=name)


def _build_anomaly(spec: dict, data: pd.DataFrame) -> go.Figure:
    feature = spec["feature"]
    series = _series(data, feature)
    fig = go.Figure()
    fig.add_trace(_line(series, feature))
    fig.add_trace(
        go.Scatter(
            x=pd.to_datetime(spec["outlier_x"], errors="coerce"),
            y=spec["outlier_y"],
            mode="markers",
            name="anomaly",
            marker=dict(color="crimson", size=9, symbol="x"),
        )
    )
    fig.update_yaxes(title_text=feature)
    return fig


def _build_trend(spec: dict, data: pd.DataFrame) -> go.Figure:
    feature = spec["feature"]
    series = _series(data, feature)
    x = np.arange(len(series), dtype=float)
    fit = spec["slope"] * x + spec["intercept"]
    fig = go.Figure()
    fig.add_trace(_line(series, feature))
    fig.add_trace(go.Scatter(x=series.index, y=fit, mode="lines", name="trend",
                             line=dict(color="firebrick", dash="dash")))
    fig.update_yaxes(title_text=feature)
    return fig


def _build_changepoint(spec: dict, data: pd.DataFrame) -> go.Figure:
    feature = spec["feature"]
    series = _series(data, feature)
    fig = go.Figure()
    fig.add_trace(_line(series, feature))
    for label in spec.get("changepoint_x", []):
        position = pd.to_datetime(label, errors="coerce")
        if pd.isna(position):
            position = label
        fig.add_vline(x=position, line_width=2, line_dash="dash", line_color="green")
    fig.update_yaxes(title_text=feature)
    return fig


def _build_scatter(spec: dict, data: pd.DataFrame) -> go.Figure:
    x_feature, y_feature = spec["x_feature"], spec["y_feature"]
    paired = pd.concat(
        [_series(data, x_feature).rename("x"), _series(data, y_feature).rename("y")],
        axis=1,
    ).dropna()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=paired["x"], y=paired["y"], mode="markers",
                             marker=dict(size=6, opacity=0.6), name="points"))
    fig.update_xaxes(title_text=x_feature)
    fig.update_yaxes(title_text=y_feature)
    return fig


def _build_heatmap(spec: dict, data: pd.DataFrame) -> go.Figure:
    features = spec["features"]
    fig = go.Figure(
        data=go.Heatmap(
            z=spec["matrix"],
            x=features,
            y=features,
            zmin=-1,
            zmax=1,
            colorscale="RdBu",
            reversescale=True,
            colorbar=dict(title="r"),
        )
    )
    return fig


def _build_lag(spec: dict, data: pd.DataFrame) -> go.Figure:
    leader, follower, lag = spec["leader"], spec["follower"], int(spec["lag"])
    lead_series = _series(data, leader)
    follow_series = _series(data, follower)
    fig = go.Figure()
    # Shift the leader forward by its lead so the aligned overlay is visible.
    fig.add_trace(go.Scatter(
        x=lead_series.index,
        y=lead_series.shift(-lag).to_numpy(),
        mode="lines",
        name=f"{leader} (shifted +{lag})",
    ))
    fig.add_trace(_line(follow_series, follower))
    return fig


def _build_periodogram(spec: dict, data: pd.DataFrame) -> go.Figure:
    freqs = np.asarray(spec["freqs"], dtype=float)
    power = np.asarray(spec["power"], dtype=float)
    # Plot against period (1/freq) which is more intuitive than raw frequency.
    with np.errstate(divide="ignore"):
        periods = np.where(freqs > 0, 1.0 / freqs, np.nan)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=periods, y=power, mode="lines", name="power"))
    peak_freq = spec.get("peak_freq")
    if peak_freq:
        fig.add_vline(x=1.0 / peak_freq, line_dash="dash", line_color="firebrick")
    fig.update_xaxes(title_text="period (samples)")
    fig.update_yaxes(title_text="spectral power")
    return fig


_BUILDERS = {
    "anomaly": _build_anomaly,
    "trend": _build_trend,
    "changepoint": _build_changepoint,
    "scatter": _build_scatter,
    "heatmap": _build_heatmap,
    "lag": _build_lag,
    "periodogram": _build_periodogram,
}
