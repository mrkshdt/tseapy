from __future__ import annotations

import numpy as np
import pandas as pd

from tseapy.core import create_callback_url
from tseapy.core.parameters import BooleanParameter, ListParameter, NumberParameter
from tseapy.tasks.forecasting import ForecastingBackend
from tseapy.tasks.forecasting.common import (
    parse_bool,
    point_metrics,
    run_backend,
    select_backends,
)

# Metrics exposed to the user for ranking. Keys map metric label -> point_metrics key.
RANKING_METRICS = {'RMSE': 'rmse', 'MAE': 'mae', 'MAPE': 'mape'}
DEFAULT_METRIC = 'RMSE'


def _normalize_metric(raw) -> str:
    """Map a user-supplied metric label to a canonical key, defaulting safely."""
    if raw is None:
        return DEFAULT_METRIC
    normalized = str(raw).strip().upper()
    if normalized in {'MAPE (%)', 'MAPE%'}:
        normalized = 'MAPE'
    return normalized if normalized in RANKING_METRICS else DEFAULT_METRIC


def rolling_origin_splits(n: int, horizon: int, n_windows: int, step: int, *, min_train: int):
    """Return ``(window_size, cutoffs)`` for a rolling-origin backtest.

    ``cutoffs`` are training-set end indices (exclusive). For each cutoff the
    test set is ``series[cutoff:cutoff + horizon]``. The number of windows is
    clamped to whatever the series length supports.

    ``window_size`` is the fixed training length used for sliding windows; the
    smallest (first) training window drives it so every fold trains on the same
    amount of data.
    """
    if horizon < 1:
        raise ValueError('horizon must be at least 1.')
    if n_windows < 1:
        raise ValueError('Number of windows must be at least 1.')
    if step < 1:
        raise ValueError('Window step must be at least 1.')

    max_windows = (n - horizon - min_train) // step + 1
    if max_windows < 1:
        raise ValueError(
            'Not enough data for backtesting. Reduce the horizon, the number of '
            'windows, or the step size.'
        )

    effective_windows = min(n_windows, max_windows)
    first_cutoff = n - horizon - (effective_windows - 1) * step
    cutoffs = [first_cutoff + i * step for i in range(effective_windows)]
    window_size = first_cutoff
    return window_size, cutoffs


class BacktestBackend(ForecastingBackend):
    """Rolling-origin cross-validation across multiple forecasting methods.

    Evaluates every selected method over several sliding/expanding windows,
    aggregates the per-window errors into a leaderboard, and recommends the
    best-performing method (AutoML-style model selection).
    """

    def __init__(self):
        short_description = (
            "Cross-validation backtest: rank forecasting methods over rolling windows "
            "and auto-select the best."
        )
        long_description = ""
        super().__init__(
            'cross-validation-backtest',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('forecasting', 'cross-validation-backtest'),
            parameters=[
                NumberParameter(
                    name='horizon',
                    label='Forecast Horizon',
                    description='Number of steps forecast and evaluated in each window',
                    minimum=1,
                    maximum=365,
                    step=1,
                    default=14,
                    onclick='',
                    disabled=False,
                ),
                NumberParameter(
                    name='n_windows',
                    label='Number of Windows',
                    description='How many rolling backtest windows to evaluate',
                    minimum=1,
                    maximum=50,
                    step=1,
                    default=5,
                    onclick='',
                    disabled=False,
                ),
                NumberParameter(
                    name='step',
                    label='Window Step',
                    description='Gap (in steps) between consecutive window cutoffs',
                    minimum=1,
                    maximum=365,
                    step=1,
                    default=7,
                    onclick='',
                    disabled=False,
                ),
                NumberParameter(
                    name='season_length',
                    label='Season Length',
                    description='Season length used by seasonal models',
                    minimum=1,
                    maximum=365,
                    step=1,
                    default=12,
                    onclick='',
                    disabled=False,
                ),
                ListParameter(
                    name='metric',
                    label='Ranking Metric',
                    description='Metric used to rank methods and pick the winner',
                    values=list(RANKING_METRICS.keys()),
                ),
                BooleanParameter(
                    name='sliding_window',
                    label='Sliding Window (fixed train size)',
                    description='Use a fixed-size sliding training window instead of an expanding one',
                    default=False,
                ),
                BooleanParameter(name='use_auto_arima', label='AutoARIMA', default=False),
                BooleanParameter(name='use_auto_ets', label='AutoETS', default=True),
                BooleanParameter(name='use_auto_theta', label='AutoTheta', default=True),
                BooleanParameter(name='use_naive', label='Naive', default=True),
                BooleanParameter(name='use_seasonal_naive', label='SeasonalNaive', default=True),
                BooleanParameter(name='use_historic_average', label='HistoricAverage', default=True),
                BooleanParameter(name='use_lightgbm', label='LightGBM (mlforecast)', default=False),
                BooleanParameter(name='use_xgboost', label='XGBoost (mlforecast)', default=False),
            ],
        )

    @staticmethod
    def _cutoff_label(index: pd.Index, cutoff: int) -> str:
        """Human-readable label for the last in-sample timestamp of a window."""
        last = index[cutoff - 1]
        if isinstance(index, pd.DatetimeIndex):
            return pd.Timestamp(last).strftime('%Y-%m-%d')
        return str(last)

    def do_analysis(self, data: pd.DataFrame, feature: str, **kwargs):
        horizon = int(kwargs['horizon'])
        season_length = int(kwargs['season_length'])
        n_windows = int(kwargs['n_windows'])
        step = int(kwargs.get('step') or horizon)
        sliding = parse_bool(kwargs.get('sliding_window', 'false'), name='sliding_window')
        metric_label = _normalize_metric(kwargs.get('metric'))
        metric_key = RANKING_METRICS[metric_label]

        series = data[feature].dropna()
        min_train = max(2 * season_length, 10)
        if len(series) < min_train + horizon:
            raise ValueError(
                f'Need at least {min_train + horizon} observations to backtest with '
                f'this horizon and season length.'
            )

        selected = select_backends(kwargs, minimum=1)
        window_size, cutoffs = rolling_origin_splits(
            len(series), horizon, n_windows, step, min_train=min_train
        )

        index = series.index
        values = series.to_numpy(dtype=np.float64)

        folds = []
        # per_model[name] -> list of primary-metric values aligned with folds
        per_model_metric = {name: [] for name, _ in selected}
        # accumulate every metric per model for leaderboard aggregation
        per_model_all = {name: {'mae': [], 'rmse': [], 'mape': []} for name, _ in selected}
        win_counts = {name: 0 for name, _ in selected}

        for fold_number, cutoff in enumerate(cutoffs, start=1):
            train_start = cutoff - window_size if sliding else 0
            train = series.iloc[train_start:cutoff]
            test = series.iloc[cutoff:cutoff + horizon]
            train_data = pd.DataFrame({feature: train.to_numpy()}, index=train.index)

            test_x = test.index.to_numpy()
            test_y = test.to_numpy(dtype=np.float64)

            fold_models = {}
            best_in_fold = (None, np.inf)
            for display_name, backend_cls in selected:
                try:
                    forecast_df = run_backend(
                        backend_cls=backend_cls,
                        data=train_data,
                        feature=feature,
                        horizon=horizon,
                        season_length=season_length,
                    )
                    pred = forecast_df['forecast'].to_numpy(dtype=np.float64)
                    forecast_x = forecast_df['ds'].to_numpy()
                    n = min(len(pred), len(test_y))
                    metric_values = point_metrics(actual=test_y[:n], predicted=pred[:n])
                except Exception:  # noqa: BLE001 - a single model must not abort the backtest
                    pred = np.array([], dtype=np.float64)
                    forecast_x = np.array([])
                    metric_values = {'mae': float('nan'), 'rmse': float('nan'), 'mape': float('nan')}

                fold_models[display_name] = {
                    'forecast_x': forecast_x,
                    'forecast_y': pred,
                    'mae': metric_values['mae'],
                    'rmse': metric_values['rmse'],
                    'mape': metric_values['mape'],
                }
                primary = metric_values[metric_key]
                per_model_metric[display_name].append(primary)
                for key in ('mae', 'rmse', 'mape'):
                    per_model_all[display_name][key].append(metric_values[key])
                if primary == primary and primary < best_in_fold[1]:  # not NaN and lower
                    best_in_fold = (display_name, primary)

            if best_in_fold[0] is not None:
                win_counts[best_in_fold[0]] += 1

            folds.append(
                {
                    'fold': fold_number,
                    'cutoff_label': self._cutoff_label(index, cutoff),
                    'train_start_label': self._cutoff_label(index, train_start + 1),
                    'test_x': test_x,
                    'test_y': test_y,
                    'models': fold_models,
                    'best_model': best_in_fold[0],
                }
            )

        leaderboard = self._build_leaderboard(
            per_model_all, win_counts, metric_key, metric_label
        )
        best_model = leaderboard[0]['Model'] if leaderboard else None

        return {
            'kind': 'backtest',
            'feature': feature,
            'history_x': index.to_numpy(),
            'history_y': values,
            'folds': folds,
            'leaderboard': leaderboard,
            'best_model': best_model,
            'metric_label': metric_label,
            'fold_labels': [fold['cutoff_label'] for fold in folds],
            'per_model_metric': per_model_metric,
            'n_windows': len(folds),
            'horizon': horizon,
            'window_type': 'sliding' if sliding else 'expanding',
        }

    @staticmethod
    def _build_leaderboard(per_model_all, win_counts, metric_key, metric_label):
        rows = []
        for name, metrics in per_model_all.items():
            row = {
                'Model': name,
                'MAE': float(np.nanmean(metrics['mae'])) if metrics['mae'] else float('nan'),
                'RMSE': float(np.nanmean(metrics['rmse'])) if metrics['rmse'] else float('nan'),
                'MAPE (%)': float(np.nanmean(metrics['mape'])) if metrics['mape'] else float('nan'),
                'Std': float(np.nanstd(metrics[metric_key])) if metrics[metric_key] else float('nan'),
                'Wins': win_counts.get(name, 0),
            }
            rows.append(row)

        ranking_lookup = {'MAE': 'MAE', 'RMSE': 'RMSE', 'MAPE': 'MAPE (%)'}
        sort_column = ranking_lookup[metric_label]

        def sort_key(row):
            value = row[sort_column]
            return (value != value, value)  # push NaN to the bottom

        rows.sort(key=sort_key)
        for position, row in enumerate(rows, start=1):
            row['Rank'] = position
        return rows
