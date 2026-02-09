import pandas as pd

from tseapy.core import create_callback_url
from tseapy.core.parameters import NumberParameter
from tseapy.tasks.forecasting import ForecastingBackend
from tseapy.tasks.forecasting.common import future_index, make_result_frame


class SeasonalNaiveBackend(ForecastingBackend):
    def __init__(self):
        short_description = "Seasonal naive baseline using last seasonal cycle values."
        long_description = ""
        super().__init__(
            'seasonal-naive',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('forecasting', 'seasonal-naive'),
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
                    disabled=False,
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
                    disabled=False,
                ),
            ],
        )

    def do_analysis(self, data: pd.DataFrame, feature: str, **kwargs):
        horizon = int(kwargs['horizon'])
        season_length = int(kwargs['season_length'])

        series = data[feature].dropna()
        if len(series) == 0:
            raise ValueError('Series is empty after dropping missing values.')
        if season_length < 1:
            raise ValueError('season_length must be at least 1.')
        if len(series) < season_length:
            raise ValueError('Need at least season_length observations for seasonal naive forecasting.')

        ds = future_index(series.index, horizon)
        tail = series.iloc[-season_length:].to_list()
        forecast = [float(tail[i % season_length]) for i in range(horizon)]
        return make_result_frame(ds=ds, forecast=forecast)
