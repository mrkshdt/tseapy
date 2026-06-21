"""Data model for autonomous agent findings.

A :class:`Finding` is a single, deterministic observation produced by an
analyzer (e.g. "feature X has a strong upward trend"). Findings are pure data:
they hold enough metadata for the frontend to render a summary card and to
rebuild a Plotly figure *on demand*, without re-running the analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


# Severity buckets used by the UI to colour-code finding cards.
SEVERITY_INFO = "info"
SEVERITY_NOTABLE = "notable"
SEVERITY_HIGH = "high"


def severity_for_score(score: float) -> str:
    """Map a 0..1 importance score to a coarse severity bucket."""
    if score >= 0.66:
        return SEVERITY_HIGH
    if score >= 0.33:
        return SEVERITY_NOTABLE
    return SEVERITY_INFO


@dataclass
class Finding:
    """A single deterministic observation about the dataset.

    Attributes:
        id: Stable identifier, unique within a single agent run.
        kind: Analyzer category, e.g. ``"trend"`` or ``"correlation"``.
        title: Short human-readable headline.
        detail: One or two sentences explaining the observation.
        score: Importance in ``[0, 1]``; drives ranking and severity.
        features: Feature column name(s) the finding concerns.
        figure_spec: Opaque, JSON-serialisable metadata the figure builder
            uses to reconstruct the Plotly figure on demand.
        metrics: Extra numeric facts surfaced on the card (key -> value).
    """

    id: str
    kind: str
    title: str
    detail: str
    score: float
    features: list[str] = field(default_factory=list)
    figure_spec: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def severity(self) -> str:
        return severity_for_score(self.score)

    def to_summary(self) -> dict[str, Any]:
        """Return the JSON payload used to render the finding card."""
        data = asdict(self)
        # The figure_spec is an internal reconstruction hint, not needed by the
        # card; the figure itself is fetched lazily via a dedicated endpoint.
        data.pop("figure_spec", None)
        data["severity"] = self.severity
        return data
