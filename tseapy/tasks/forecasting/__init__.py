import abc

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from tseapy.core.analysis_backends import AnalysisBackend
from tseapy.core.tasks import Task


class Forecasting(Task):
    def __init__(self):
        short_description = "Forecast future values using statistical models."
        long_description = ""
        super().__init__('forecasting', short_description, long_description)

    def get_interaction_script(self, algo):
        return ""

    def get_interaction_view(self, algo: str):
        return ""

    def get_analysis_results(self, data, feature, algo, **kwargs):
        assert feature in data.columns
        backend = self.analysis_backend_factory.get_analysis_backend(algo=algo)
        forecast_df = backend.do_analysis(data, feature, **kwargs)

        fig = go.Figure()

        # Historical data trace
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data[feature],
            mode='lines',
            name='Historical',
            line=dict(color='blue')
        ))

        # Lower confidence interval (invisible, used as base for fill)
        fig.add_trace(go.Scatter(
            x=forecast_df['ds'],
            y=forecast_df['lo'],
            mode='lines',
            line=dict(width=0),
            showlegend=False,
            name='Lower CI'
        ))

        # Upper confidence interval with fill to lower
        fig.add_trace(go.Scatter(
            x=forecast_df['ds'],
            y=forecast_df['hi'],
            mode='lines',
            line=dict(width=0),
            fill='tonexty',
            fillcolor='rgba(255, 0, 0, 0.2)',
            name='95% Confidence Interval'
        ))

        # Forecast line
        fig.add_trace(go.Scatter(
            x=forecast_df['ds'],
            y=forecast_df['forecast'],
            mode='lines',
            name='Forecast',
            line=dict(color='red')
        ))

        fig.update_yaxes(title={'text': feature})
        return fig


class ForecastingBackend(AnalysisBackend):
    @abc.abstractmethod
    def do_analysis(self, data, feature, **kwargs):
        pass
