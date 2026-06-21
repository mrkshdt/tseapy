"""Deterministic analyzers for the autonomous insights agent.

Every analyzer is a pure function ``(DataFrame) -> list[Finding]``. They never
mutate their input and never touch Flask/session state, which keeps them easy to
unit test and safe to run inside a background thread.

The results are *deterministic*: given the same data the same findings come out,
with the same scores. The agent's job is to run these without being asked; the
frontend then renders them and builds figures on demand.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tseapy.agent.findings import Finding

# A series shorter than this carries too little signal to analyze meaningfully.
MIN_POINTS = 12
# Robust z-score threshold for flagging outliers (modified z, MAD based).
OUTLIER_Z = 3.5
# Absolute Pearson correlation above which a feature pair is "strongly related".
STRONG_CORR = 0.6


def _numeric_frame(data: pd.DataFrame) -> pd.DataFrame:
    """Return the numeric columns of ``data`` with all-NaN columns dropped."""
    numeric = data.select_dtypes(include="number")
    return numeric.dropna(axis=1, how="all")


def _clean_series(data: pd.DataFrame, feature: str) -> pd.Series:
    """Return a finite-valued, NaN-free copy of ``data[feature]``."""
    series = pd.to_numeric(data[feature], errors="coerce")
    return series.replace([np.inf, -np.inf], np.nan).dropna()


def _index_labels(index: pd.Index) -> list[str]:
    """Stringify an index for JSON-friendly figure specs."""
    if isinstance(index, pd.DatetimeIndex):
        return index.strftime("%Y-%m-%d %H:%M:%S").tolist()
    return [str(value) for value in index]


def detect_anomalies(data: pd.DataFrame) -> list[Finding]:
    """Flag outliers per feature using a robust (median/MAD) z-score."""
    findings: list[Finding] = []
    numeric = _numeric_frame(data)
    for feature in numeric.columns:
        series = _clean_series(numeric, feature)
        if len(series) < MIN_POINTS:
            continue
        median = float(series.median())
        mad = float((series - median).abs().median())
        if mad == 0:
            continue
        modified_z = 0.6745 * (series - median) / mad
        mask = modified_z.abs() > OUTLIER_Z
        count = int(mask.sum())
        if count == 0:
            continue
        fraction = count / len(series)
        # Many outliers or even a few extreme ones are worth surfacing; cap at 1.
        score = float(min(1.0, fraction * 10 + 0.3))
        outlier_index = series.index[mask.to_numpy()]
        findings.append(
            Finding(
                id=f"anomaly::{feature}",
                kind="anomaly",
                title=f"{count} anomaly(ies) in '{feature}'",
                detail=(
                    f"{count} point(s) ({fraction:.1%} of the series) deviate "
                    f"more than {OUTLIER_Z} robust z-scores from the median."
                ),
                score=score,
                features=[feature],
                metrics={"outliers": count, "fraction": round(fraction, 4)},
                figure_spec={
                    "type": "anomaly",
                    "feature": feature,
                    "outlier_x": _index_labels(outlier_index),
                    "outlier_y": series[mask.to_numpy()].tolist(),
                },
            )
        )
    return findings


def detect_trends(data: pd.DataFrame) -> list[Finding]:
    """Detect statistically significant linear trends per feature."""
    from scipy import stats

    findings: list[Finding] = []
    numeric = _numeric_frame(data)
    for feature in numeric.columns:
        series = _clean_series(numeric, feature)
        if len(series) < MIN_POINTS:
            continue
        x = np.arange(len(series), dtype=float)
        result = stats.linregress(x, series.to_numpy())
        # Require both a meaningful correlation and statistical significance.
        if not np.isfinite(result.rvalue) or abs(result.rvalue) < 0.3 or result.pvalue >= 0.05:
            continue
        direction = "upward" if result.slope > 0 else "downward"
        score = float(min(1.0, abs(result.rvalue)))
        findings.append(
            Finding(
                id=f"trend::{feature}",
                kind="trend",
                title=f"{direction.capitalize()} trend in '{feature}'",
                detail=(
                    f"'{feature}' shows a significant {direction} trend "
                    f"(R²={result.rvalue ** 2:.2f}, p={result.pvalue:.1e})."
                ),
                score=score,
                features=[feature],
                metrics={
                    "r_squared": round(float(result.rvalue ** 2), 4),
                    "slope": float(result.slope),
                    "p_value": float(result.pvalue),
                },
                figure_spec={
                    "type": "trend",
                    "feature": feature,
                    "slope": float(result.slope),
                    "intercept": float(result.intercept),
                },
            )
        )
    return findings


def detect_changepoints(data: pd.DataFrame) -> list[Finding]:
    """Detect abrupt mean shifts per feature using ruptures PELT (L2)."""
    import ruptures as rpt

    findings: list[Finding] = []
    numeric = _numeric_frame(data)
    for feature in numeric.columns:
        series = _clean_series(numeric, feature)
        if len(series) < max(MIN_POINTS, 20):
            continue
        values = series.to_numpy()
        try:
            algo = rpt.Pelt(model="l2", jump=max(1, len(values) // 200), min_size=5).fit(values)
            breaks = algo.predict(pen=np.log(len(values)) * float(np.var(values)) + 1e-9)
        except (ValueError, RuntimeError):
            continue
        # ruptures appends the series length as the final "breakpoint"; drop it.
        changepoints = [b for b in breaks if 0 < b < len(values)]
        if not changepoints:
            continue
        score = float(min(1.0, 0.3 + 0.15 * len(changepoints)))
        labels = _index_labels(series.index[changepoints])
        findings.append(
            Finding(
                id=f"changepoint::{feature}",
                kind="changepoint",
                title=f"{len(changepoints)} mean shift(s) in '{feature}'",
                detail=(
                    f"Detected {len(changepoints)} abrupt change(s) in the mean "
                    f"level of '{feature}'."
                ),
                score=score,
                features=[feature],
                metrics={"changepoints": len(changepoints)},
                figure_spec={
                    "type": "changepoint",
                    "feature": feature,
                    "changepoint_x": labels,
                },
            )
        )
    return findings


def detect_correlations(data: pd.DataFrame) -> list[Finding]:
    """Surface strongly correlated feature pairs and an overview heatmap."""
    findings: list[Finding] = []
    numeric = _numeric_frame(data)
    # Keep only columns with enough variation and observations.
    usable = [c for c in numeric.columns if _clean_series(numeric, c).shape[0] >= MIN_POINTS]
    if len(usable) < 2:
        return findings

    corr = numeric[usable].corr(method="pearson", numeric_only=True)
    columns = list(corr.columns)

    # One finding per strong, non-trivial pair (upper triangle only).
    for i, a in enumerate(columns):
        for b in columns[i + 1:]:
            r = corr.loc[a, b]
            if not np.isfinite(r) or abs(r) < STRONG_CORR:
                continue
            relation = "positively" if r > 0 else "negatively"
            findings.append(
                Finding(
                    id=f"correlation::{a}::{b}",
                    kind="correlation",
                    title=f"'{a}' and '{b}' are {relation} correlated",
                    detail=(
                        f"'{a}' and '{b}' move {relation} together "
                        f"(Pearson r={r:.2f})."
                    ),
                    score=float(min(1.0, abs(r))),
                    features=[a, b],
                    metrics={"r": round(float(r), 4)},
                    figure_spec={"type": "scatter", "x_feature": a, "y_feature": b},
                )
            )

    # A single overview heatmap is always useful when several features exist.
    findings.append(
        Finding(
            id="correlation::heatmap",
            kind="correlation",
            title="Correlation heatmap",
            detail=f"Pairwise Pearson correlation across {len(columns)} numeric features.",
            score=0.3,
            features=columns,
            metrics={"features": len(columns)},
            figure_spec={
                "type": "heatmap",
                "features": columns,
                "matrix": corr.round(4).fillna(0).values.tolist(),
            },
        )
    )
    return findings


def detect_lagged_correlations(data: pd.DataFrame) -> list[Finding]:
    """Find lead/lag relationships between strongly correlated feature pairs."""
    findings: list[Finding] = []
    numeric = _numeric_frame(data)
    usable = [c for c in numeric.columns if _clean_series(numeric, c).shape[0] >= MIN_POINTS]
    if len(usable) < 2:
        return findings

    aligned = numeric[usable].apply(pd.to_numeric, errors="coerce")
    max_lag = min(30, len(aligned) // 4)
    if max_lag < 2:
        return findings

    columns = list(aligned.columns)
    for i, a in enumerate(columns):
        for b in columns[i + 1:]:
            best_lag, best_corr = _best_lag(aligned[a], aligned[b], max_lag)
            if best_lag == 0 or not np.isfinite(best_corr) or abs(best_corr) < STRONG_CORR:
                continue
            leader, follower = (a, b) if best_lag > 0 else (b, a)
            findings.append(
                Finding(
                    id=f"lag::{a}::{b}",
                    kind="lag",
                    title=f"'{leader}' leads '{follower}' by {abs(best_lag)} step(s)",
                    detail=(
                        f"Cross-correlation peaks when '{leader}' is shifted ahead "
                        f"of '{follower}' by {abs(best_lag)} step(s) (r={best_corr:.2f})."
                    ),
                    score=float(min(1.0, abs(best_corr))),
                    features=[a, b],
                    metrics={"lag": int(best_lag), "r": round(float(best_corr), 4)},
                    figure_spec={
                        "type": "lag",
                        "leader": leader,
                        "follower": follower,
                        "lag": int(abs(best_lag)),
                    },
                )
            )
    return findings


def _best_lag(a: pd.Series, b: pd.Series, max_lag: int) -> tuple[int, float]:
    """Return the lag (in steps) maximising |corr(a.shift(lag), b)| and its corr.

    A positive lag means ``a`` leads ``b``.
    """
    best_lag = 0
    best_corr = 0.0
    for lag in range(-max_lag, max_lag + 1):
        shifted = a.shift(lag)
        paired = pd.concat([shifted, b], axis=1).dropna()
        if len(paired) < MIN_POINTS:
            continue
        r = paired.iloc[:, 0].corr(paired.iloc[:, 1])
        if np.isfinite(r) and abs(r) > abs(best_corr):
            best_corr = float(r)
            best_lag = lag
    return best_lag, best_corr


def detect_seasonality(data: pd.DataFrame) -> list[Finding]:
    """Detect a dominant periodicity per feature via the periodogram."""
    from scipy import signal

    findings: list[Finding] = []
    numeric = _numeric_frame(data)
    for feature in numeric.columns:
        series = _clean_series(numeric, feature)
        if len(series) < max(MIN_POINTS, 24):
            continue
        values = series.to_numpy() - series.to_numpy().mean()
        if np.allclose(values, 0):
            continue
        freqs, power = signal.periodogram(values)
        # Ignore the zero-frequency (DC) component.
        if len(freqs) <= 2:
            continue
        freqs, power = freqs[1:], power[1:]
        peak = int(np.argmax(power))
        if freqs[peak] <= 0 or power[peak] <= 0:
            continue
        period = float(1.0 / freqs[peak])
        # Score by how much the dominant peak dominates the average power.
        prominence = power[peak] / (power.mean() + 1e-12)
        # Require a real cycle: at least 2 periods observed (rejects the
        # low-frequency component of a pure trend) and a clearly dominant peak.
        if prominence < 3 or period < 2 or period > len(values) / 2:
            continue
        score = float(min(1.0, 0.2 + prominence / 50))
        findings.append(
            Finding(
                id=f"seasonality::{feature}",
                kind="seasonality",
                title=f"Periodicity ~{period:.1f} steps in '{feature}'",
                detail=(
                    f"'{feature}' has a dominant cycle of about {period:.1f} "
                    f"samples (peak/mean power ≈ {prominence:.1f})."
                ),
                score=score,
                features=[feature],
                metrics={"period": round(period, 2), "prominence": round(float(prominence), 2)},
                figure_spec={
                    "type": "periodogram",
                    "feature": feature,
                    "freqs": freqs.tolist(),
                    "power": power.tolist(),
                    "peak_freq": float(freqs[peak]),
                },
            )
        )
    return findings


# Ordered registry of analyzers the engine runs. Each entry is (label, function);
# the label is surfaced in the agent's progress display.
ANALYZERS = [
    ("Scanning for anomalies", detect_anomalies),
    ("Detecting trends", detect_trends),
    ("Finding mean shifts", detect_changepoints),
    ("Correlating features", detect_correlations),
    ("Searching lead/lag links", detect_lagged_correlations),
    ("Measuring seasonality", detect_seasonality),
]
