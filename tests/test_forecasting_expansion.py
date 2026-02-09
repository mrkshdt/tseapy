import pandas as pd

from tseapy.tasks.forecasting import Forecasting
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
