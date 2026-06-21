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


def get_candidate_backends():
    """Return the registry of selectable forecasting backends.

    Imports are performed lazily to avoid a circular import: each backend
    module imports helpers from this module.
    """
    from tseapy.tasks.forecasting.auto_arima import AutoArimaBackend
    from tseapy.tasks.forecasting.auto_ets import AutoEtsBackend
    from tseapy.tasks.forecasting.auto_theta import AutoThetaBackend
    from tseapy.tasks.forecasting.historic_average import HistoricAverageBackend
    from tseapy.tasks.forecasting.lightgbm_mlforecast import LightGBMMLForecastBackend
    from tseapy.tasks.forecasting.naive import NaiveBackend
    from tseapy.tasks.forecasting.seasonal_naive import SeasonalNaiveBackend
    from tseapy.tasks.forecasting.xgboost_mlforecast import XGBoostMLForecastBackend

    return [
        ('AutoARIMA', 'use_auto_arima', AutoArimaBackend),
        ('AutoETS', 'use_auto_ets', AutoEtsBackend),
        ('AutoTheta', 'use_auto_theta', AutoThetaBackend),
        ('Naive', 'use_naive', NaiveBackend),
        ('SeasonalNaive', 'use_seasonal_naive', SeasonalNaiveBackend),
        ('HistoricAverage', 'use_historic_average', HistoricAverageBackend),
        ('LightGBM', 'use_lightgbm', LightGBMMLForecastBackend),
        ('XGBoost', 'use_xgboost', XGBoostMLForecastBackend),
    ]


def select_backends(kwargs, *, minimum: int = 1):
    """Resolve the user-selected backends from boolean ``use_*`` flags."""
    selected = []
    for display_name, flag_name, backend_cls in get_candidate_backends():
        raw_flag = kwargs.get(flag_name, 'false')
        if parse_bool(raw_flag, name=flag_name):
            selected.append((display_name, backend_cls))

    if len(selected) < minimum:
        noun = 'method' if minimum == 1 else 'methods'
        raise ValueError(f'Select at least {minimum} forecasting {noun}.')
    return selected


def run_backend(backend_cls, data, feature, horizon, season_length):
    """Instantiate ``backend_cls`` and run a single forecast.

    ``season_length`` is only forwarded to backends that accept it.
    """
    backend = backend_cls()
    param_names = {p.name for p in backend.parameters}
    model_kwargs = {'horizon': horizon}
    if 'season_length' in param_names:
        model_kwargs['season_length'] = season_length
    return backend.do_analysis(data=data, feature=feature, **model_kwargs)


def future_index(index: pd.Index, horizon: int):
    if horizon < 1:
        raise ValueError("horizon must be at least 1.")

    if isinstance(index, pd.DatetimeIndex):
        freq = infer_series_freq(index)
        start = index[-1]
        return pd.date_range(start=start, periods=horizon + 1, freq=freq)[1:]

    start = int(index[-1]) if len(index) > 0 else 0
    return np.arange(start + 1, start + horizon + 1)
