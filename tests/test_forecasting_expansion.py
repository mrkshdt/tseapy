import pytest
import pandas as pd

from tseapy.tasks.forecasting import Forecasting
from tseapy.tasks.forecasting.backtest import BacktestBackend, rolling_origin_splits
from tseapy.tasks.forecasting.comparison import ForecastComparisonBackend
from tseapy.tasks.forecasting.historic_average import HistoricAverageBackend
from tseapy.tasks.forecasting.naive import NaiveBackend
from tseapy.tasks.forecasting.seasonal_naive import SeasonalNaiveBackend


def sample_data(n=60):
    idx = pd.date_range('2024-01-01', periods=n, freq='D')
    values = pd.Series(range(n), index=idx, dtype='float64')
    return pd.DataFrame({'value': values})


def test_naive_backend_repeats_last_value():
    backend = NaiveBackend()
    data = sample_data(20)

    result = backend.do_analysis(data=data, feature='value', horizon=5)

    assert len(result) == 5
    assert result['forecast'].tolist() == [19.0] * 5


def test_seasonal_naive_backend_repeats_last_cycle():
    backend = SeasonalNaiveBackend()
    data = sample_data(12)

    result = backend.do_analysis(data=data, feature='value', horizon=5, season_length=3)

    assert result['forecast'].tolist() == [9.0, 10.0, 11.0, 9.0, 10.0]


def test_historic_average_backend_uses_series_mean():
    backend = HistoricAverageBackend()
    data = sample_data(10)

    result = backend.do_analysis(data=data, feature='value', horizon=4)

    assert result['forecast'].tolist() == [4.5, 4.5, 4.5, 4.5]


def test_forecast_comparison_returns_metrics_and_forecasts():
    backend = ForecastComparisonBackend()
    data = sample_data(50)

    result = backend.do_analysis(
        data=data,
        feature='value',
        horizon=6,
        season_length=3,
        use_auto_arima='false',
        use_auto_ets='false',
        use_auto_theta='false',
        use_naive='true',
        use_seasonal_naive='false',
        use_historic_average='true',
        use_lightgbm='false',
        use_xgboost='false',
    )

    assert result['kind'] == 'comparison'
    assert len(result['forecasts']) == 2
    assert len(result['metrics']) == 2


def test_forecasting_task_builds_comparison_figure_with_table():
    forecasting = Forecasting()
    forecasting.add_analysis_backend(ForecastComparisonBackend())

    data = sample_data(50)
    fig = forecasting.get_analysis_results(
        data=data,
        feature='value',
        algo='forecast-comparison',
        horizon=6,
        season_length=3,
        use_auto_arima='false',
        use_auto_ets='false',
        use_auto_theta='false',
        use_naive='true',
        use_seasonal_naive='false',
        use_historic_average='true',
        use_lightgbm='false',
        use_xgboost='false',
    )

    trace_types = {trace.type for trace in fig.data}
    assert 'scatter' in trace_types
    assert 'table' in trace_types


def _backtest_kwargs(**overrides):
    kwargs = dict(
        horizon=4,
        n_windows=3,
        step=2,
        season_length=3,
        metric='RMSE',
        sliding_window='false',
        use_auto_arima='false',
        use_auto_ets='false',
        use_auto_theta='false',
        use_naive='true',
        use_seasonal_naive='true',
        use_historic_average='true',
        use_lightgbm='false',
        use_xgboost='false',
    )
    kwargs.update(overrides)
    return kwargs


def test_rolling_origin_splits_clamps_to_available_data():
    window_size, cutoffs = rolling_origin_splits(60, horizon=4, n_windows=3, step=2, min_train=10)

    assert len(cutoffs) == 3
    assert cutoffs[-1] == 60 - 4  # last window tests the final horizon points
    assert all(b - a == 2 for a, b in zip(cutoffs, cutoffs[1:]))
    assert window_size == cutoffs[0]


def test_rolling_origin_splits_reduces_windows_when_short():
    _, cutoffs = rolling_origin_splits(20, horizon=4, n_windows=10, step=2, min_train=10)

    # only a few windows fit: (20 - 4 - 10) // 2 + 1 == 4
    assert 1 <= len(cutoffs) <= 4


def test_rolling_origin_splits_raises_when_insufficient():
    with pytest.raises(ValueError):
        rolling_origin_splits(12, horizon=10, n_windows=3, step=2, min_train=10)


def test_backtest_backend_ranks_methods_and_picks_winner():
    backend = BacktestBackend()
    data = sample_data(80)

    result = backend.do_analysis(data=data, feature='value', **_backtest_kwargs())

    assert result['kind'] == 'backtest'
    assert result['n_windows'] == 3
    assert result['window_type'] == 'expanding'
    assert len(result['folds']) == 3
    # three selected methods evaluated in every fold
    assert len(result['leaderboard']) == 3
    assert {row['Rank'] for row in result['leaderboard']} == {1, 2, 3}
    assert result['best_model'] == result['leaderboard'][0]['Model']
    for name, values in result['per_model_metric'].items():
        assert len(values) == 3
    total_wins = sum(row['Wins'] for row in result['leaderboard'])
    assert total_wins == 3  # one winner per fold


def test_backtest_sliding_window_uses_fixed_train_size():
    backend = BacktestBackend()
    data = sample_data(80)

    result = backend.do_analysis(
        data=data, feature='value', **_backtest_kwargs(sliding_window='true')
    )

    assert result['window_type'] == 'sliding'


def test_backtest_requires_at_least_one_method():
    backend = BacktestBackend()
    data = sample_data(80)

    with pytest.raises(ValueError):
        backend.do_analysis(
            data=data,
            feature='value',
            **_backtest_kwargs(use_naive='false', use_seasonal_naive='false', use_historic_average='false'),
        )


def test_forecasting_task_builds_backtest_figure_with_table():
    forecasting = Forecasting()
    forecasting.add_analysis_backend(BacktestBackend())

    data = sample_data(80)
    fig = forecasting.get_analysis_results(
        data=data, feature='value', algo='cross-validation-backtest', **_backtest_kwargs()
    )

    trace_types = {trace.type for trace in fig.data}
    assert 'scatter' in trace_types
    assert 'table' in trace_types
    assert 'Recommended' in fig.layout.title.text
