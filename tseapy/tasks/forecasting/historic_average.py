import pandas as pd

from tseapy.core import create_callback_url
from tseapy.core.parameters import NumberParameter
from tseapy.tasks.forecasting import ForecastingBackend
from tseapy.tasks.forecasting.common import future_index, make_result_frame


class HistoricAverageBackend(ForecastingBackend):
    def __init__(self):
        short_description = "Historic average baseline using the historical mean value."
        long_description = ""
        super().__init__(
            'historic-average',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('forecasting', 'historic-average'),
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
        mean_value = float(series.mean())
        forecast = [mean_value] * horizon
        return make_result_frame(ds=ds, forecast=forecast)
