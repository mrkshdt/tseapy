import numpy as np
import pandas as pd

from tseapy.agent.analyzers import (
    detect_anomalies,
    detect_changepoints,
    detect_correlations,
    detect_lagged_correlations,
    detect_seasonality,
    detect_trends,
)
from tseapy.agent.engine import InsightsEngine, STATUS_DONE
from tseapy.agent.figures import build_figure


def _index(n):
    return pd.date_range("2024-01-01", periods=n, freq="h")


def _trend_corr_anom_frame(seed=0, n=300):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    trend = 0.05 * t + rng.normal(0, 1, n)
    corr = 2 * trend + rng.normal(0, 0.3, n)
    anom = rng.normal(0, 1, n)
    anom[40] = 40.0
    anom[210] = -38.0
    season = 8 * np.sin(2 * np.pi * t / 24) + rng.normal(0, 0.5, n)
    shift = np.concatenate([np.zeros(n // 2), np.full(n - n // 2, 9.0)]) + rng.normal(0, 0.4, n)
    return pd.DataFrame(
        {"trend": trend, "corr": corr, "anom": anom, "season": season, "shift": shift},
        index=_index(n),
    )


def test_detect_trends_finds_upward_trend():
    df = _trend_corr_anom_frame()
    findings = detect_trends(df)
    trend = next(f for f in findings if f.features == ["trend"])
    assert trend.kind == "trend"
    assert trend.figure_spec["slope"] > 0
    assert trend.score > 0.5


def test_detect_anomalies_flags_outliers():
    df = _trend_corr_anom_frame()
    findings = detect_anomalies(df)
    anom = next(f for f in findings if f.features == ["anom"])
    assert anom.metrics["outliers"] >= 2
    assert anom.figure_spec["outlier_x"]


def test_detect_changepoints_finds_shift():
    df = _trend_corr_anom_frame()
    findings = detect_changepoints(df)
    shift = next(f for f in findings if f.features == ["shift"])
    assert shift.metrics["changepoints"] >= 1


def test_detect_correlations_surfaces_pair_and_heatmap():
    df = _trend_corr_anom_frame()
    findings = detect_correlations(df)
    pairs = {tuple(sorted(f.features)) for f in findings if f.kind == "correlation" and len(f.features) == 2}
    assert ("corr", "trend") in pairs
    assert any(f.id == "correlation::heatmap" for f in findings)


def test_detect_seasonality_finds_period():
    df = _trend_corr_anom_frame()
    findings = detect_seasonality(df)
    season = next(f for f in findings if f.features == ["season"])
    # True period is 24 samples; allow tolerance.
    assert 20 <= season.metrics["period"] <= 28


def test_detect_seasonality_ignores_pure_trend():
    # A monotonic trend has no real cycle (fewer than 2 periods observed).
    df = pd.DataFrame({"x": np.arange(100, dtype=float)}, index=_index(100))
    assert detect_seasonality(df) == []


def test_lagged_correlation_detects_lead():
    n = 300
    rng = np.random.default_rng(3)
    base = np.sin(np.arange(n) / 5.0) + rng.normal(0, 0.05, n)
    leader = pd.Series(base, index=_index(n))
    follower = leader.shift(5).fillna(0)
    df = pd.DataFrame({"leader": leader.to_numpy(), "follower": follower.to_numpy()}, index=_index(n))
    findings = detect_lagged_correlations(df)
    assert any(f.kind == "lag" for f in findings)


def test_short_series_yields_no_findings():
    df = pd.DataFrame({"x": [1.0, 2.0, 3.0]}, index=_index(3))
    assert detect_trends(df) == []
    assert detect_anomalies(df) == []
    assert detect_changepoints(df) == []
    assert detect_seasonality(df) == []


def test_engine_runs_synchronously_and_ranks():
    df = _trend_corr_anom_frame()
    eng = InsightsEngine()
    eng.start(df, background=False)
    status = eng.status()
    assert status["status"] == STATUS_DONE
    assert status["completed"] == status["total"]
    findings = eng.findings()
    assert findings, "expected at least one finding"
    # Findings are ranked by descending score.
    scores = [f.score for f in findings]
    assert scores == sorted(scores, reverse=True)


def test_engine_skips_identical_rerun():
    df = _trend_corr_anom_frame()
    eng = InsightsEngine()
    eng.start(df, background=False)
    first = eng.findings()
    # A second run on the same data is a no-op (no duplicate accumulation).
    eng.start(df, background=False)
    assert len(eng.findings()) == len(first)


def test_engine_get_finding_and_build_figure():
    df = _trend_corr_anom_frame()
    eng = InsightsEngine()
    eng.start(df, background=False)
    for finding in eng.findings():
        fig = build_figure(finding, eng.data())
        assert fig.data, f"empty figure for {finding.id}"


def test_finding_summary_excludes_figure_spec():
    df = _trend_corr_anom_frame()
    findings = detect_trends(df)
    summary = findings[0].to_summary()
    assert "figure_spec" not in summary
    assert "severity" in summary
