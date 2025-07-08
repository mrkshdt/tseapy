import pandas as pd
from statsmodels.tsa.seasonal import STL

from tseapy.core import create_callback_url
from tseapy.core.parameters import NumberParameter
from tseapy.tasks.trend_decomposition import TrendDecompositionBackend


class STLDecomposition(TrendDecompositionBackend):
    def __init__(self):
        short_description = "STL decomposition"
        long_description = ""
        super().__init__(
            'stl',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('trend-decomposition', 'stl'),
            parameters=[
                NumberParameter(
                    name='period',
                    label='period',
                    description='Seasonal period',
                    minimum=2,
                    maximum=365,
                    step=1,
                    default=12,
                    onclick='',
                    disabled=False
                )
            ]
        )

    def do_analysis(self, data: pd.DataFrame, feature: str, **kwargs):
        period = int(kwargs['period'])
        stl = STL(data[feature], period=period)
        result = stl.fit()
        return result.trend, result.seasonal
