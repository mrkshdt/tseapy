# Changelog

All notable changes to this project are documented in this file.

The format is inspired by Keep a Changelog.

## [Unreleased]

### Added
- Autonomous **Insights Agent** (`tseapy/agent/`) that analyses a loaded
  dataset in a background thread without being prompted, running deterministic
  analyzers for anomalies, trends, mean shifts, cross-feature correlations,
  lead/lag relationships and seasonality, then ranking the findings by score.
- `/agent` dashboard that polls agent progress and renders one card per finding,
  building each finding's Plotly figure on demand.
- Agent JSON endpoints: `/agent/status`, `/agent/findings`, and
  `/agent/findings/<id>/figure`.
- Agent links in the home page and header navigation.

### Changed
- Upload configuration now retains a multi-feature numeric frame (`agent_data`)
  alongside the single-feature analysis frame so the agent can find
  cross-feature correlations, and auto-launches the agent once data is loaded.

## [1.2.0a0] - 2026-02-09

### Added
- Python packaging metadata in `pyproject.toml`.
- CLI entrypoint (`tseapy`) and WSGI entrypoint (`wsgi.py`).
- Package-distributed templates and static assets.
- Docker runtime (`Dockerfile`, `docker-compose.yml`).
- CI workflow for tests, build, wheel smoke test, and Docker build.
- Trusted publishing workflows:
  - `publish-testpypi.yml`
  - `publish-pypi.yml`
- Release and maintenance documentation:
  - `RELEASE.md`
  - `CONTRIBUTING.md`
  - `TROUBLESHOOTING.md`
  - `VERSIONING.md`

### Changed
- App bootstrap moved to `create_app(...)` with environment-driven config.
- Debug behavior made explicit through CLI flags and env variables.
- Core abstractions (`Task`, `AnalysisBackend`) formalized as abstract bases.
- Route and packaging tests expanded.

### Fixed
- Export endpoint now returns explicit `501` message instead of unhandled exception.
- Plotly deprecation usage in affected tasks.
- Wheel/package install behavior and runtime path consistency.
