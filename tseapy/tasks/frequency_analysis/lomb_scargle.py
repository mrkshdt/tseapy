import numpy as np
import pandas as pd

from tseapy.core import create_callback_url
from tseapy.core.parameters import NumberParameter
from tseapy.tasks.frequency_analysis import FrequencyAnalysisBackend


class LombScargleBackend(FrequencyAnalysisBackend):
    def __init__(self):
        short_description = "Lomb-Scargle periodogram for uneven sampling."
        long_description = ""
        super().__init__(
            'lomb-scargle',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('frequency-analysis', 'lomb-scargle'),
            parameters=[
                NumberParameter(
                    name='min_frequency',
                    label='Min frequency',
                    description='Lower bound of frequency grid',
                    minimum=0.000001,
                    maximum=1000,
                    step=0.000001,
                    default=0.001,
                    onclick='',
                    disabled=False,
                ),
                NumberParameter(
                    name='max_frequency',
                    label='Max frequency',
                    description='Upper bound of frequency grid',
                    minimum=0.001,
                    maximum=10000,
                    step=0.001,
                    default=1.0,
                    onclick='',
                    disabled=False,
                ),
                NumberParameter(
                    name='num_frequencies',
                    label='Frequency samples',
                    description='Number of frequencies to evaluate',
                    minimum=11,
                    maximum=100000,
                    step=1,
                    default=2000,
                    onclick='',
                    disabled=False,
                ),
            ],
        )

    def do_analysis(self, data: pd.DataFrame, feature: str, **kwargs):
        try:
            from scipy.signal import lombscargle
        except ImportError as exc:
            raise ValueError('scipy is required for Lomb-Scargle analysis.') from exc

        min_frequency = float(kwargs['min_frequency'])
        max_frequency = float(kwargs['max_frequency'])
        num_frequencies = int(kwargs['num_frequencies'])

        series = data[feature].dropna().astype(float)
        if len(series) < 8:
            raise ValueError('Need at least 8 non-null samples for Lomb-Scargle.')
        if min_frequency <= 0:
            raise ValueError('min_frequency must be positive.')
        if max_frequency <= min_frequency:
            raise ValueError('max_frequency must be greater than min_frequency.')

        index = series.index
        if isinstance(index, pd.DatetimeIndex):
            times = (index - index[0]).total_seconds().to_numpy(dtype=np.float64)
        else:
            times = np.arange(len(series), dtype=np.float64)

        values = series.to_numpy(dtype=np.float64)
        values = values - np.mean(values)

        frequencies = np.linspace(min_frequency, max_frequency, num_frequencies, dtype=np.float64)
        angular = 2.0 * np.pi * frequencies
        power = lombscargle(times, values, angular, normalize=True)

        return {
            'kind': 'line',
            'name': 'Lomb-Scargle',
            'x': frequencies,
            'y': power,
            'x_title': 'Frequency',
            'y_title': 'Normalized power',
        }
