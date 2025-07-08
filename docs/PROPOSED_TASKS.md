# Additional Analysis Tasks

This file proposes additional time series analysis tasks that could extend tseapy. Each proposal outlines the goal of the task and a possible approach for implementation.

## 1. Trend and Seasonality Decomposition

**Objective:** Separate a time series into trend, seasonal, and residual components. This helps users better understand underlying patterns before applying other analyses.

**Possible Implementation:**
- Add a new task class `TrendDecomposition` under `tseapy/tasks/trend_decomposition/`.
- Create a backend using `statsmodels`' `STL` or `seasonal_decompose` for the decomposition computation.
- Expose parameters such as the seasonal period and decomposition model (additive or multiplicative).
- Register the new backend in `app.py` similarly to existing tasks and update templates if custom interaction is required.

## 2. Forecasting

**Objective:** Provide simple forecasting capabilities, for example using ARIMA models. Users could forecast future data points based on past observations.

**Possible Implementation:**
- Create a new task `Forecasting` with backends such as `ARIMA` or `SimpleExponentialSmoothing` from `statsmodels`.
- Implement parameters for forecast horizon and model order.
- Add a `Forecasting` task in `app.py` so that users can select this analysis from the interface.

## 3. Outlier Detection

**Objective:** Identify anomalous observations within a time series. This can highlight unusual events or data quality issues.

**Possible Implementation:**
- Create a task `OutlierDetection` in `tseapy/tasks/outlier_detection/`.
- Implement backends such as Z-score thresholding or machine-learning based approaches like Isolation Forest.
- Provide parameters to tune sensitivity (e.g., z-score threshold or contamination rate).
- Once implemented, register the task in `app.py`.

## Adding a New Task

Adding any of these tasks follows the pattern already used in the project:
1. Create a new folder under `tseapy/tasks/` and implement a subclass of `Task`.
2. Define one or more subclasses of `AnalysisBackend` within that folder to perform the computations. Each backend should expose a `callback_url` and parameters as demonstrated in existing tasks.
3. In `app.py`, instantiate your task and its backends, then register the task with the global `TasksList`.
4. Optionally provide HTML templates or interaction scripts if the task requires custom UI elements.
