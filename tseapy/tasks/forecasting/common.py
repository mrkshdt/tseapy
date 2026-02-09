from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def parse_bool(raw: Any, *, name: str) -> bool:
    if isinstance(raw, bool):
        return raw
    normalized = str(raw).strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"{name} must be true or false.")
    return normalized == "true"


def infer_series_freq(index: pd.Index):
    if isinstance(index, pd.DatetimeIndex):
        inferred = pd.infer_freq(index)
        if inferred:
            return inferred
        if len(index) >= 2:
            deltas = pd.Series(index).diff().dropna()
            if not deltas.empty:
                median_delta = deltas.median()
                try:
                    return pd.tseries.frequencies.to_offset(median_delta).freqstr
                except ValueError:
                    pass
        return "D"
    return 1


def to_statsforecast_df(data: pd.DataFrame, feature: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "unique_id": ["series_1"] * len(data),
            "ds": data.index,
            "y": data[feature].values,
        }
    )


def make_result_frame(ds, forecast, lo=None, hi=None) -> pd.DataFrame:
    forecast_arr = np.asarray(forecast, dtype=np.float64)
    n = len(forecast_arr)
    if lo is None:
        lo = np.full(shape=n, fill_value=np.nan)
    if hi is None:
        hi = np.full(shape=n, fill_value=np.nan)

    return pd.DataFrame(
        {
            "ds": ds,
            "forecast": forecast_arr,
            "lo": np.asarray(lo, dtype=np.float64),
            "hi": np.asarray(hi, dtype=np.float64),
        }
    )


def point_metrics(actual, predicted) -> dict[str, float]:
    actual_arr = np.asarray(actual, dtype=np.float64)
    pred_arr = np.asarray(predicted, dtype=np.float64)
    if len(actual_arr) == 0 or len(pred_arr) == 0:
        raise ValueError("Cannot compute metrics on empty arrays.")

    n = min(len(actual_arr), len(pred_arr))
    actual_arr = actual_arr[:n]
    pred_arr = pred_arr[:n]

    error = actual_arr - pred_arr
    mae = float(np.mean(np.abs(error)))
    rmse = float(np.sqrt(np.mean(np.square(error))))

    non_zero = np.abs(actual_arr) > 1e-12
    if np.any(non_zero):
        mape = float(np.mean(np.abs(error[non_zero] / actual_arr[non_zero])) * 100.0)
    else:
        mape = float("nan")

    return {"mae": mae, "rmse": rmse, "mape": mape}


def future_index(index: pd.Index, horizon: int):
    if horizon < 1:
        raise ValueError("horizon must be at least 1.")

    if isinstance(index, pd.DatetimeIndex):
        freq = infer_series_freq(index)
        start = index[-1]
        return pd.date_range(start=start, periods=horizon + 1, freq=freq)[1:]

    start = int(index[-1]) if len(index) > 0 else 0
    return np.arange(start + 1, start + horizon + 1)
