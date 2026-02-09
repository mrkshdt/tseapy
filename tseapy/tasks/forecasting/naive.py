import pandas as pd

from tseapy.core import create_callback_url
from tseapy.core.parameters import NumberParameter
from tseapy.tasks.forecasting import ForecastingBackend
from tseapy.tasks.forecasting.common import future_index, make_result_frame


class NaiveBackend(ForecastingBackend):
    def __init__(self):
        short_description = "Naive baseline forecast using the last observed value."
        long_description = ""
        super().__init__(
            'naive',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('forecasting', 'naive'),
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
                )
            ],
        )

    def do_analysis(self, data: pd.DataFrame, feature: str, **kwargs):
        horizon = int(kwargs['horizon'])

        series = data[feature].dropna()
        if len(series) == 0:
            raise ValueError('Series is empty after dropping missing values.')

        ds = future_index(series.index, horizon)
        forecast = [float(series.iloc[-1])] * horizon
        return make_result_frame(ds=ds, forecast=forecast)
