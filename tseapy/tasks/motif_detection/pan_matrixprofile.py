import stumpy
import numpy as np

from tseapy.core import create_callback_url
from tseapy.core.analysis_backends import AnalysisBackend
from tseapy.core.parameters import NumberParameter
from tseapy.tasks.motif_detection import MotifDetectionBackend


class PanMatrixprofile(MotifDetectionBackend):
    def __init__(self):
        short_description = ""
        long_description = """
        """
        super().__init__(
            'panmatrixprofile',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('motif-detection', 'panmatrixprofile'),
            parameters=[
                NumberParameter(
                    name='penalty',
                    label='penalty',
                    description='penalty value (>0)',
                    disabled=False,
                    onclick="",
                    minimum=0.1,
                    maximum=1000,
                    step=0.01,
                    default=10
                ),
                NumberParameter(
                    name='minimum_width',
                    label='minimum_width',
                    description='The minimum width of the sliding window',
                    disabled=False,
                    onclick="",
                    minimum=5,
                    maximum=1000,
                    step=1,
                    default=50
                ),
                NumberParameter(
                    name='maximum_width',
                    label='maximum_width',
                    description='The maximum width of the sliding window',
                    disabled=False,
                    onclick="",
                    minimum=5,
                    maximum=1000,
                    step=1,
                    default=150
                ),
                NumberParameter(
                    name='percentage',
                    label='percentage',
                    description='This percentage controls the extent of `stumpy.scrump` completion',
                    disabled=False,
                    onclick="",
                    minimum=1,
                    maximum=100,
                    step=1,
                    default=2
                )
            ])

    def do_analysis(self, data, feature, **kwargs):
        penalty = float(kwargs['penalty'])
        min_width = int(kwargs['minimum_width'])
        max_width = int(kwargs['maximum_width'])
        percent = int(kwargs['percentage'])
        series = data[feature].astype(np.float64)
        series_len = len(series)
        if series_len < 6:
            raise ValueError("Dataset is too short for pan matrix profile. Need at least 6 rows.")
        if min_width < 3:
            min_width = 3
        upper_bound = series_len - 1
        if min_width >= upper_bound:
            raise ValueError(f"minimum_width must be less than {upper_bound}.")
        max_width = min(max_width, upper_bound)
        if max_width <= min_width:
            raise ValueError("maximum_width must be greater than minimum_width.")
        if percent < 1 or percent > 100:
            raise ValueError("percentage must be between 1 and 100.")

        eog = stumpy.stimp(series, min_m=min_width, max_m=max_width, percentage=percent / 100)
        n = max(1, int(np.ceil((max_width - min_width) * (percent / 100))))
        for _ in range(n):
            try:
                eog.update()
            except Exception:
                break

        return False, eog, []
