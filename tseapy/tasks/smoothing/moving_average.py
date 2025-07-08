import pandas as pd

from tseapy.core import create_callback_url
from tseapy.core.parameters import NumberParameter
from tseapy.tasks.smoothing import SmoothingBackend


class MovingAverage(SmoothingBackend):
    def __init__(self):
        short_description = "Simple moving average smoothing."
        long_description = ""
        super().__init__(
            'moving-average',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('smoothing', 'moving-average'),
            parameters=[
                NumberParameter(
                    name='window',
                    label='window',
                    description='Window size',
                    minimum=1,
                    maximum=100,
                    step=1,
                    default=5,
                    onclick='',
                    disabled=False
                )
            ]
        )

    def do_analysis(self, data: pd.DataFrame, feature: str, **kwargs):
        window = int(kwargs['window'])
        return data[feature].rolling(window=window, min_periods=1).mean()
