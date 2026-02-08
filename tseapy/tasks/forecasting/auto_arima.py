import pandas as pd

from tseapy.core import create_callback_url
from tseapy.core.parameters import NumberParameter
from tseapy.tasks.forecasting import ForecastingBackend


class AutoArimaBackend(ForecastingBackend):
    def __init__(self):
        short_description = "Automatic ARIMA model selection and forecasting."
        long_description = ""
        super().__init__(
            'auto-arima',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('forecasting', 'auto-arima'),
            parameters=[
                NumberParameter(
                    name='horizon',
                    label='Forecast Horizon',
                    description='Number of steps to forecast',
                    minimum=1,
                    maximum=365,
                    step=1,
                    default=30,
                    onclick='',
                    disabled=False
                ),
                NumberParameter(
                    name='season_length',
                    label='Season Length',
                    description='Length of the seasonal cycle',
                    minimum=1,
                    maximum=365,
                    step=1,
                    default=12,
                    onclick='',
                    disabled=False
                )
            ]
        )

    def do_analysis(self, data: pd.DataFrame, feature: str, **kwargs):
        horizon = int(kwargs['horizon'])
        season_length = int(kwargs['season_length'])

        sf_df = pd.DataFrame({
            'unique_id': ['series_1'] * len(data),
            'ds': data.index,
            'y': data[feature].values
        })

        try:
            from statsforecast import StatsForecast
            from statsforecast.models import AutoARIMA

            sf = StatsForecast(
                models=[AutoARIMA(season_length=season_length)],
                freq=pd.infer_freq(data.index) or 'D'
            )
            sf.fit(sf_df)
            forecast = sf.predict(h=horizon, level=[95])
        except Exception as e:
            raise ValueError(f"Forecasting failed: {e}")

        result = pd.DataFrame({
            'ds': forecast['ds'].values,
            'forecast': forecast['AutoARIMA'].values,
            'lo': forecast['AutoARIMA-lo-95'].values,
            'hi': forecast['AutoARIMA-hi-95'].values
        })
        return result
