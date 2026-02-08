import pandas as pd

from tseapy.core import create_callback_url
from tseapy.core.parameters import NumberParameter, ListParameter
from tseapy.tasks.decomposition import DecompositionBackend


class ClassicalDecompositionBackend(DecompositionBackend):
    def __init__(self):
        short_description = "Classical additive/multiplicative decomposition."
        long_description = ""
        super().__init__(
            'classical-decomposition',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('decomposition', 'classical-decomposition'),
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
                ListParameter(
                    name='model',
                    label='Model',
                    description='Decomposition model type',
                    values=['additive', 'multiplicative'],
                    onclick='',
                    disabled=False,
                ),
            ],
        )

    def do_analysis(self, data: pd.DataFrame, feature: str, **kwargs):
        try:
            from statsmodels.tsa.seasonal import seasonal_decompose
        except ImportError as exc:
            raise ValueError('statsmodels is required for classical decomposition.') from exc

        period = int(kwargs['period'])
        model = str(kwargs.get('model', 'additive')).strip().lower() or 'additive'
        if model not in {'additive', 'multiplicative'}:
            raise ValueError("model must be 'additive' or 'multiplicative'.")

        series = data[feature].dropna()
        if len(series) < 8:
            raise ValueError('Need at least 8 non-null samples for decomposition.')
        if period < 2:
            raise ValueError('period must be at least 2.')
        if period * 2 >= len(series):
            raise ValueError(f'period must satisfy 2*period < data length ({len(series)}).')
        if model == 'multiplicative' and (series <= 0).any():
            raise ValueError('Multiplicative model requires strictly positive values.')

        result = seasonal_decompose(series, model=model, period=period, extrapolate_trend='freq')
        return {
            'observed': series,
            'trend': result.trend,
            'seasonal': result.seasonal,
            'residual': result.resid,
        }
