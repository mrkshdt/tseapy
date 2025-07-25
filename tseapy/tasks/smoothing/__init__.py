import abc
import plotly.express as px

from tseapy.core.analysis_backends import AnalysisBackend
from tseapy.core.tasks import Task


class Smoothing(Task):
    def __init__(self):
        short_description = "Apply smoothing algorithms to reduce noise."
        long_description = ""
        super().__init__('smoothing', short_description, long_description)

    def get_interaction_script(self, algo):
        return ""

    def get_interaction_view(self, algo: str):
        return ""

    def get_analysis_results(self, data, feature, algo, **kwargs):
        assert feature in data.columns
        backend = self.analysis_backend_factory.get_analysis_backend(algo=algo)
        smoothed = backend.do_analysis(data, feature, **kwargs)
        fig = px.line(x=data.index, y=data[feature], markers=True)
        fig.add_scatter(x=data.index, y=smoothed, name='smoothed')
        fig.update_yaxes(title={'text': feature})
        return fig


class SmoothingBackend(AnalysisBackend):
    @abc.abstractmethod
    def do_analysis(self, data, feature, **kwargs):
        pass
