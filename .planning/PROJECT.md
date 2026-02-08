# tseapy — Time Series Analysis Platform

## What This Is

A web-based time series analysis tool that lets users upload CSV files, select a time series column, and run analysis algorithms (change point detection, pattern recognition, motif detection, smoothing) with interactive Plotly visualizations. Built on an existing Python/Flask codebase that already has working algorithm implementations but is locked to a single hardcoded demo dataset.

## Core Value

Users can upload their own CSV data and immediately analyze any time series column using the built-in algorithms — no coding required.

## Requirements

### Validated

<!-- Shipped and confirmed valuable — inferred from existing codebase. -->

- ✓ Change point detection via PELT and Sliding Window algorithms — existing
- ✓ Pattern recognition via MASS algorithm with interactive selection — existing
- ✓ Motif detection via Matrix Profile algorithm — existing
- ✓ Smoothing via Moving Average algorithm — existing
- ✓ Interactive Plotly visualizations for all analysis results — existing
- ✓ Parameter controls per algorithm (number, range, boolean, list inputs) — existing
- ✓ Feature/column switching within a loaded dataset — existing
- ✓ Task-Backend architecture for extensible algorithm registration — existing

### Active

<!-- Current scope. Building toward these. -->

- [x] User can upload a CSV file through a data wizard UI
- [x] Data wizard shows a preview of the uploaded CSV (first N rows)
- [x] User can select which column is the time/date index
- [x] User can select which column contains the values to analyze
- [x] Uploaded data replaces the hardcoded demo dataset in the analysis pipeline
- [x] User can navigate from data upload → column selection → task selection → algorithm → results
- [x] UI is clean, functional, and consistent across all pages
- [x] App handles common CSV issues gracefully (missing values, wrong delimiters, non-numeric columns)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Multi-column simultaneous analysis — adds complexity, one column at a time is sufficient for v1
- User authentication / multi-user support — single-user local tool for v1
- Database persistence / saving results — in-memory is fine for v1
- React/Vue frontend — Flask + HTML keeps things simple and builds on existing code
- Automated "run all algorithms" mode — user picks analysis one at a time
- Export functionality — stub exists but not needed for minimum working version
- Mobile responsiveness — desktop-first tool
- Cloud deployment — runs locally

## Context

**Existing codebase:** Python/Flask app with a well-structured Task-Backend pattern. Four analysis tasks already work (change-in-mean, pattern-recognition, motif-detection, smoothing) with multiple algorithm backends. The main gap is data loading — currently hardcoded to a single Air Quality UCI dataset loaded on app startup.

**Key concern from codebase audit:** Several outdated dependencies (NumPy 1.21, Flask 2.0, scikit-learn 1.1), bare exception handlers in motif detection, unused code (Bokeh visualizer, validation module), and XSS risks in parameter rendering. These should be addressed but are secondary to the core data wizard feature.

**Architecture:** The existing Task/AnalysisBackend/Parameter abstraction is solid and should be preserved. The data wizard plugs into the existing pipeline by replacing the hardcoded `get_air_quality_uci()` call with user-uploaded data stored in Flask cache.

## Constraints

- **Tech stack**: Python/Flask with Plotly — build on existing codebase, no framework change
- **Scope**: Minimum working version — data wizard + existing analysis pipeline working end-to-end
- **Data format**: Flexible CSV — user picks time index column and value column after upload
- **Deployment**: Local only — `python app.py` starts everything

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep Flask + server-rendered HTML | Fastest path to working version, existing code already works this way | Implemented |
| One column at a time analysis | Simplest UX, matches existing architecture | Implemented |
| Flexible CSV format (user picks columns) | Real-world CSVs are messy, auto-detection is fragile | Implemented |
| No database / no auth for v1 | Keep scope minimal for first working version | Implemented |

---
*Last updated: 2026-02-08 after milestone completion*
