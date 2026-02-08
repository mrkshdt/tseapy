import abc

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tseapy.core.analysis_backends import AnalysisBackend
from tseapy.core.tasks import Task


class Decomposition(Task):
    def __init__(self):
        short_description = "Split a series into trend, seasonal, and residual components."
        long_description = ""
        super().__init__('decomposition', short_description, long_description)

    def get_interaction_script(self, algo):
        return ""

    def get_interaction_view(self, algo: str):
        return ""

    def get_analysis_results(self, data, feature, algo, **kwargs):
        assert feature in data.columns
        backend = self.analysis_backend_factory.get_analysis_backend(algo=algo)
        components = backend.do_analysis(data, feature, **kwargs)

        fig = make_subplots(
            rows=4,
            cols=1,
            shared_xaxes=True,
            subplot_titles=("Observed", "Trend", "Seasonal", "Residual"),
            vertical_spacing=0.04,
        )

        fig.add_trace(
            go.Scatter(x=components['observed'].index, y=components['observed'].values, mode='lines', name='Observed'),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=components['trend'].index, y=components['trend'].values, mode='lines', name='Trend'),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=components['seasonal'].index, y=components['seasonal'].values, mode='lines', name='Seasonal'),
            row=3,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=components['residual'].index, y=components['residual'].values, mode='lines', name='Residual'),
            row=4,
            col=1,
        )
        fig.update_layout(height=900, showlegend=False)
        return fig


class DecompositionBackend(AnalysisBackend):
    @abc.abstractmethod
    def do_analysis(self, data, feature, **kwargs):
        pass
