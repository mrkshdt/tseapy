import numpy as np
import pandas as pd

from tseapy.core import create_callback_url
from tseapy.core.parameters import NumberParameter, ListParameter
from tseapy.tasks.frequency_analysis import FrequencyAnalysisBackend


class STFTBackend(FrequencyAnalysisBackend):
    def __init__(self):
        short_description = "Short-time Fourier transform spectrogram."
        long_description = ""
        super().__init__(
            'stft',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('frequency-analysis', 'stft'),
            parameters=[
                NumberParameter(
                    name='sampling_rate',
                    label='Sampling rate',
                    description='Samples per time unit',
                    minimum=0.001,
                    maximum=100000,
                    step=0.001,
                    default=1.0,
                    onclick='',
                    disabled=False,
                ),
                NumberParameter(
                    name='nperseg',
                    label='Window length',
                    description='Samples per STFT window',
                    minimum=8,
                    maximum=100000,
                    step=1,
                    default=256,
                    onclick='',
                    disabled=False,
                ),
                NumberParameter(
                    name='noverlap',
                    label='Overlap',
                    description='Number of overlapping samples',
                    minimum=0,
                    maximum=99999,
                    step=1,
                    default=128,
                    onclick='',
                    disabled=False,
                ),
                ListParameter(
                    name='window',
                    label='Window function',
                    description='FFT window function',
                    values=['hann', 'hamming', 'blackman'],
                    onclick='',
                    disabled=False,
                ),
            ],
        )

    def do_analysis(self, data: pd.DataFrame, feature: str, **kwargs):
        try:
            from scipy.signal import stft
        except ImportError as exc:
            raise ValueError('scipy is required for STFT analysis.') from exc

        sampling_rate = float(kwargs['sampling_rate'])
        nperseg = int(kwargs['nperseg'])
        noverlap = int(kwargs['noverlap'])
        window = str(kwargs.get('window', 'hann')).strip() or 'hann'

        series = data[feature].dropna().to_numpy(dtype=np.float64)
        if len(series) < 8:
            raise ValueError('Need at least 8 non-null samples for STFT.')
        if sampling_rate <= 0:
            raise ValueError('sampling_rate must be positive.')
        nperseg = min(max(8, nperseg), len(series))
        if noverlap < 0:
            raise ValueError('noverlap must be non-negative.')
        if noverlap >= nperseg:
            noverlap = max(0, nperseg // 2)

        frequencies, times, zxx = stft(
            series,
            fs=sampling_rate,
            window=window,
            nperseg=nperseg,
            noverlap=noverlap,
        )

        return {
            'kind': 'heatmap',
            'x': times,
            'y': frequencies,
            'z': np.abs(zxx),
            'x_title': 'Time',
            'y_title': 'Frequency',
            'z_title': 'Magnitude',
        }
