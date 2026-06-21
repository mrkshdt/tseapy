import pandas as pd

from tseapy.core import create_callback_url
from tseapy.core.parameters import BooleanParameter, NumberParameter
from tseapy.tasks.forecasting import ForecastingBackend
from tseapy.tasks.forecasting.common import point_metrics, run_backend, select_backends


class ForecastComparisonBackend(ForecastingBackend):
    def __init__(self):
        short_description = "Compare multiple forecasting methods side-by-side with error metrics."
        long_description = ""
        super().__init__(
            'forecast-comparison',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('forecasting', 'forecast-comparison'),
            parameters=[
                NumberParameter(
                    name='horizon',
                    label='Forecast Horizon',
                    description='Number of steps to forecast and evaluate',
                    minimum=1,
                    maximum=365,
                    step=1,
                    default=30,
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
                BooleanParameter(name='use_auto_arima', label='AutoARIMA', default=True),
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
    def _selected_backends(kwargs):
        return select_backends(kwargs, minimum=2)

    @staticmethod
    def _run_backend(backend_cls, data, feature, horizon, season_length):
        return run_backend(backend_cls, data, feature, horizon, season_length)

    def do_analysis(self, data: pd.DataFrame, feature: str, **kwargs):
        horizon = int(kwargs['horizon'])
        season_length = int(kwargs['season_length'])

        series = data[feature].dropna()
        if len(series) <= horizon + 5:
            raise ValueError('Need more data points than horizon + 5 for comparison.')

        selected = self._selected_backends(kwargs)
        train = series.iloc[:-horizon]
        valid = series.iloc[-horizon:]

        train_data = pd.DataFrame({feature: train.values}, index=train.index)
        full_data = pd.DataFrame({feature: series.values}, index=series.index)

        forecasts = []
        metrics_rows = []

        for display_name, backend_cls in selected:
            validation_forecast = self._run_backend(
                backend_cls=backend_cls,
                data=train_data,
                feature=feature,
                horizon=horizon,
                season_length=season_length,
            )
            pred = validation_forecast['forecast'].to_numpy()
            truth = valid.to_numpy()
            n = min(len(pred), len(truth))
            metric_values = point_metrics(actual=truth[:n], predicted=pred[:n])

            future_forecast = self._run_backend(
                backend_cls=backend_cls,
                data=full_data,
                feature=feature,
                horizon=horizon,
                season_length=season_length,
            )

            forecasts.append(
                {
                    'name': display_name,
                    'x': future_forecast['ds'].to_numpy(),
                    'y': future_forecast['forecast'].to_numpy(),
                }
            )
            metrics_rows.append(
                {
                    'Model': display_name,
                    'MAE': metric_values['mae'],
                    'RMSE': metric_values['rmse'],
                    'MAPE (%)': metric_values['mape'],
                }
            )

        return {
            'kind': 'comparison',
            'history_x': series.index.to_numpy(),
            'history_y': series.to_numpy(),
            'forecasts': forecasts,
            'metrics': metrics_rows,
            'horizon': horizon,
        }
