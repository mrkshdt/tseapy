import pandas as pd

from tseapy.core import create_callback_url
from tseapy.core.parameters import BooleanParameter, NumberParameter
from tseapy.tasks.forecasting import ForecastingBackend
from tseapy.tasks.forecasting.auto_arima import AutoArimaBackend
from tseapy.tasks.forecasting.auto_ets import AutoEtsBackend
from tseapy.tasks.forecasting.auto_theta import AutoThetaBackend
from tseapy.tasks.forecasting.historic_average import HistoricAverageBackend
from tseapy.tasks.forecasting.lightgbm_mlforecast import LightGBMMLForecastBackend
from tseapy.tasks.forecasting.naive import NaiveBackend
from tseapy.tasks.forecasting.seasonal_naive import SeasonalNaiveBackend
from tseapy.tasks.forecasting.xgboost_mlforecast import XGBoostMLForecastBackend
from tseapy.tasks.forecasting.common import parse_bool, point_metrics


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
        candidates = [
            ('AutoARIMA', 'use_auto_arima', AutoArimaBackend),
            ('AutoETS', 'use_auto_ets', AutoEtsBackend),
            ('AutoTheta', 'use_auto_theta', AutoThetaBackend),
            ('Naive', 'use_naive', NaiveBackend),
            ('SeasonalNaive', 'use_seasonal_naive', SeasonalNaiveBackend),
            ('HistoricAverage', 'use_historic_average', HistoricAverageBackend),
            ('LightGBM', 'use_lightgbm', LightGBMMLForecastBackend),
            ('XGBoost', 'use_xgboost', XGBoostMLForecastBackend),
        ]

        selected = []
        for display_name, flag_name, backend_cls in candidates:
            raw_flag = kwargs.get(flag_name, 'false')
            if parse_bool(raw_flag, name=flag_name):
                selected.append((display_name, backend_cls))

        if len(selected) < 2:
            raise ValueError('Select at least 2 forecasting methods for comparison.')
        return selected

    @staticmethod
    def _run_backend(backend_cls, data, feature, horizon, season_length):
        backend = backend_cls()
        param_names = {p.name for p in backend.parameters}
        model_kwargs = {'horizon': horizon}
        if 'season_length' in param_names:
            model_kwargs['season_length'] = season_length
        return backend.do_analysis(data=data, feature=feature, **model_kwargs)

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
