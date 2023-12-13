import ruptures as rpt

from tseapy.core import create_callback_url
from tseapy.core.analysis_backends import AnalysisBackend
from tseapy.core.parameters import NumberParameter
from tseapy.tasks.change_in_mean import ChangeInMeanBackend


class SlidingWindowL2(ChangeInMeanBackend):
    def __init__(self):
        short_description = ""
        long_description = """
        """
        super().__init__(
            'sliding-window-l2',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('change-in-mean', 'sliding-window-l2'),
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
                    name='width',
                    label='width',
                    description='The width of the sliding window',
                    disabled=False,
                    onclick="",
                    minimum=5,
                    maximum=1000,
                    step=1,
                    default=30
                ),
                NumberParameter(
                    name='min_size',
                    label='min_size',
                    description='Minimum segment size (in data points)',
                    disabled=False,
                    onclick="",
                    minimum=5,
                    maximum=1000,
                    step=1,
                    default=10
                ),
                NumberParameter(
                    name='jump',
                    label='jump',
                    description='Subsample (one every jump points)',
                    disabled=False,
                    onclick="",
                    minimum=1,
                    maximum=1000,
                    step=1,
                    default=5
                )
            ])

    def do_analysis(self, data, feature, **kwargs):
        penalty = float(kwargs['penalty'])
        width = int(kwargs['width'])
        min_size = int(kwargs['min_size'])
        jump = int(kwargs['jump'])
        algo = rpt.Window(model='l2', width=width, jump=jump, min_size=min_size).fit(data[feature].values)
        changepoints = algo.predict(pen=penalty)
        return data.index[changepoints[:-1]]
