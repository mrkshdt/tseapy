"""Autonomous insights agent for tseapy.

This package turns tseapy from a manual, click-to-run tool into a proactive
agent: when a dataset is loaded it runs a suite of deterministic time-series
analyzers in the background and surfaces ranked findings, whose figures are
built on demand.
"""

from tseapy.agent.engine import InsightsEngine, engine
from tseapy.agent.figures import build_figure
from tseapy.agent.findings import Finding

__all__ = ["InsightsEngine", "engine", "build_figure", "Finding"]
