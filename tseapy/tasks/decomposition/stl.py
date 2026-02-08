import pandas as pd

from tseapy.core import create_callback_url
from tseapy.core.parameters import NumberParameter, BooleanParameter
from tseapy.tasks.decomposition import DecompositionBackend


class STLBackend(DecompositionBackend):
    def __init__(self):
        short_description = "STL decomposition using LOESS smoothing."
        long_description = ""
        super().__init__(
            'stl',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('decomposition', 'stl'),
            parameters=[
                NumberParameter(
                    name='period',
                    label='Seasonal period',
                    description='Number of samples per seasonal cycle',
                    minimum=2,
                    maximum=5000,
                    step=1,
                    default=24,
                    onclick='',
                    disabled=False,
                ),
                BooleanParameter(
                    name='robust',
                    label='Robust fitting',
                    description='Use robust STL to reduce outlier impact',
                    default=True,
                    onclick='',
                    disabled=False,
                ),
            ],
        )

    def do_analysis(self, data: pd.DataFrame, feature: str, **kwargs):
        try:
            from statsmodels.tsa.seasonal import STL
        except ImportError as exc:
            raise ValueError('statsmodels is required for STL decomposition.') from exc

        period = int(kwargs['period'])
        robust_raw = str(kwargs.get('robust', 'true')).lower()
        if robust_raw not in {'true', 'false'}:
            raise ValueError('robust must be true or false.')
        robust = robust_raw == 'true'

        series = data[feature].dropna()
        if len(series) < 8:
            raise ValueError('Need at least 8 non-null samples for STL decomposition.')
        if period < 2:
            raise ValueError('period must be at least 2.')
        if period * 2 >= len(series):
            raise ValueError(f'period must satisfy 2*period < data length ({len(series)}).')

        result = STL(series, period=period, robust=robust).fit()
        return {
            'observed': series,
            'trend': result.trend,
            'seasonal': result.seasonal,
            'residual': result.resid,
        }
