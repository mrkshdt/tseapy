import ruptures as rpt

from tseapy.core import create_callback_url
from tseapy.core.parameters import NumberParameter
from tseapy.tasks.change_in_mean import ChangeInMeanBackend


class PeltL2(ChangeInMeanBackend):
    def __init__(self):
        short_description = ""
        long_description = """
        """
        super().__init__(
            'pelt-l2',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('change-in-mean', 'pelt-l2'),
            parameters=[
                NumberParameter(
                    name='penalty',
                    label='penalty',
                    description='The number of changepoints to find',
                    disabled=False,
                    onclick="",
                    minimum=0,
                    maximum=10,
                    step=0.01,
                    default=1
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
        pen = float(kwargs['penalty'])
        min_size = int(kwargs['min_size'])
        jump = int(kwargs['jump'])
        algo = rpt.Pelt(model='l2', jump=jump, min_size=min_size).fit(data[feature].values)
        changepoints = algo.predict(pen)
        return data.index[changepoints[:-1]]
