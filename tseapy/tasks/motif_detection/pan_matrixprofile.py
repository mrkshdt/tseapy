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
        min = int(kwargs['minimum_width'])
        max = float(kwargs['maximum_width'])
        percent = int(kwargs['percentage'])

        eog = stumpy.stimp(data[feature], min_m=min, max_m=max, percentage=percent)
        n = np.ceil((max - min) * percent).astype(int)

        for _ in range(n):
            eog.update()

        return False, eog, []
