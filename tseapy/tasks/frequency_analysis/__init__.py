import abc

import plotly.graph_objects as go

from tseapy.core.analysis_backends import AnalysisBackend
from tseapy.core.tasks import Task


class FrequencyAnalysis(Task):
    def __init__(self):
        short_description = "Analyze periodic patterns in the frequency domain."
        long_description = ""
        super().__init__('frequency-analysis', short_description, long_description)

    def get_interaction_script(self, algo):
        return ""

    def get_interaction_view(self, algo: str):
        return ""

    def get_analysis_results(self, data, feature, algo, **kwargs):
        assert feature in data.columns
        backend = self.analysis_backend_factory.get_analysis_backend(algo=algo)
        result = backend.do_analysis(data, feature, **kwargs)

        if result['kind'] == 'line':
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=result['x'],
                    y=result['y'],
                    mode='lines',
                    name=result.get('name', algo),
                )
            )
            fig.update_layout(
                xaxis_title=result.get('x_title', 'Frequency'),
                yaxis_title=result.get('y_title', 'Power'),
            )
            return fig

        if result['kind'] == 'heatmap':
            fig = go.Figure(
                data=go.Heatmap(
                    x=result['x'],
                    y=result['y'],
                    z=result['z'],
                    colorscale='Viridis',
                    colorbar={'title': result.get('z_title', 'Magnitude')},
                )
            )
            fig.update_layout(
                xaxis_title=result.get('x_title', 'Time'),
                yaxis_title=result.get('y_title', 'Frequency'),
            )
            return fig

        raise ValueError('Unsupported frequency analysis result format.')


class FrequencyAnalysisBackend(AnalysisBackend):
    @abc.abstractmethod
    def do_analysis(self, data, feature, **kwargs):
        pass
