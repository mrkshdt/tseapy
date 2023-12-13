import abc

import plotly.express as px

from tseapy.core.analysis_backends import AnalysisBackend
from tseapy.core.tasks import Task


class ChangeInMean(Task):

    def __init__(self):
        short_description = "Change in mean is the task of finding abrupt changes in the mean of a time series"
        long_description = """
        Change in mean (changepoint detection) is the task of finding abrupt changes in the mean of a time series
        """
        super().__init__('change-in-mean', short_description, long_description)

    def get_interaction_script(self, algo):
        return ""


    def get_interaction_view(self, algo: str):
        return ""

    def get_analysis_results(self, data, feature, algo, **kwargs):
        assert feature in data.columns

        a = self.analysis_backend_factory.get_analysis_backend(algo=algo)
        changepoints = a.do_analysis(data, feature, **kwargs)

        # make results plot
        fig = px.line(x=data.index, y=data[feature], markers=True)
        fig.update_yaxes(title={'text': feature})
        for cpt in changepoints:
            fig.add_vline(x=cpt, line_width=3, line_dash="dash", line_color="green")
        return fig

class ChangeInMeanBackend(AnalysisBackend):
    @abc.abstractmethod
    def do_analysis(self, data, feature, **kwargs):
        pass
