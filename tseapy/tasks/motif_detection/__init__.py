import abc

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from tseapy.core.analysis_backends import AnalysisBackend
from tseapy.core.tasks import Task

class MotifDetection(Task):

    def __init__(self):
        short_description = "Motif Detection is the task of finding subsequences of a time series that appear recurrently."
        long_description = """
        """
        super().__init__('motif-detection', short_description, long_description)

    def get_interaction_script(self, algo):
        return ""


    def get_interaction_view(self, algo: str):
        return ""

    def get_analysis_results(self, data, feature, algo, **kwargs):
        assert feature in data.columns

        a = self.analysis_backend_factory.get_analysis_backend(algo=algo)
        mutex, mp, motifs = a.do_analysis(data, feature, **kwargs)
        
        fig = make_subplots(rows=2, cols=1, subplot_titles=("Distance Profile", "Result"))
        colors = px.colors.qualitative.Plotly

        if mutex:
            fig.append_trace(go.Scatter(
                x=list(range(len(mp))),
                y=mp,
                name="Distance Profile",
                marker={'color': colors[0]}
                ),  row=1,col=1)
        else:
            fig.append_trace(go.Heatmap(
                z = mp.PAN_.tolist(),
                colorscale = [[0, colors[0]], [1, 'rgb(255, 255, 255, 255)']]
                ),  row=1,col=1)

        fig.append_trace(go.Scatter(
            x=list(range(len(data[feature]))),
            y=data[feature],
            name="Input Time-Series",
            marker={'color': colors[0]}),  row=2,col=1)

        if mutex:
            fig.append_trace(go.Scatter(
                x=list(range(len(data[feature]))),
                y=motifs['motif'],
                name="Motifs",
                marker={'color': colors[2]}),  row=2,col=1)
        else:
            # result plot for PMP based on how dense the matrix is?
            pass

        return fig

class MotifDetectionBackend(AnalysisBackend):
    @abc.abstractmethod
    def do_analysis(self, data, feature, **kwargs):
        pass
