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
        if feature not in data.columns:
            raise ValueError("Unknown feature column")
        backend = self.analysis_backend_factory.get_analysis_backend(algo=algo)
        result = backend.do_analysis(data, feature, **kwargs)

        if isinstance(result, dict) and result.get('kind') == 'comparison':
            fig = make_subplots(
                rows=2,
                cols=1,
                specs=[[{"type": "scatter"}], [{"type": "table"}]],
                row_heights=[0.7, 0.3],
                vertical_spacing=0.08,
                subplot_titles=("Forecast Comparison", "Accuracy Metrics"),
            )

            fig.add_trace(
                go.Scatter(
                    x=result['history_x'],
                    y=result['history_y'],
                    mode='lines',
                    name='Historical',
                    line=dict(color='steelblue'),
                ),
                row=1,
                col=1,
            )

            for forecast in result['forecasts']:
                fig.add_trace(
                    go.Scatter(
                        x=forecast['x'],
                        y=forecast['y'],
                        mode='lines',
                        name=forecast['name'],
                    ),
                    row=1,
                    col=1,
                )

            metrics = result['metrics']
            fig.add_trace(
                go.Table(
                    header=dict(values=["Model", "MAE", "RMSE", "MAPE (%)"]),
                    cells=dict(
                        values=[
                            [row['Model'] for row in metrics],
                            [f"{row['MAE']:.4f}" for row in metrics],
                            [f"{row['RMSE']:.4f}" for row in metrics],
                            [f"{row['MAPE (%)']:.2f}" if row['MAPE (%)'] == row['MAPE (%)'] else "NaN" for row in metrics],
                        ]
                    ),
                ),
                row=2,
                col=1,
            )
            fig.update_yaxes(title={'text': feature}, row=1, col=1)
            fig.update_layout(height=800)
            return fig

        forecast_df = result
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data[feature],
                mode='lines',
                name='Historical',
                line=dict(color='blue'),
            )
        )

        has_ci = (
            'lo' in forecast_df
            and 'hi' in forecast_df
            and forecast_df['lo'].notna().any()
            and forecast_df['hi'].notna().any()
        )
        if has_ci:
            fig.add_trace(
                go.Scatter(
                    x=forecast_df['ds'],
                    y=forecast_df['lo'],
                    mode='lines',
                    line=dict(width=0),
                    showlegend=False,
                    name='Lower CI',
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=forecast_df['ds'],
                    y=forecast_df['hi'],
                    mode='lines',
                    line=dict(width=0),
                    fill='tonexty',
                    fillcolor='rgba(255, 0, 0, 0.2)',
                    name='95% Confidence Interval',
                )
            )

        fig.add_trace(
            go.Scatter(
                x=forecast_df['ds'],
                y=forecast_df['forecast'],
                mode='lines',
                name='Forecast',
                line=dict(color='red'),
            )
        )

        fig.update_yaxes(title={'text': feature})
        return fig


class ForecastingBackend(AnalysisBackend):
    @abc.abstractmethod
    def do_analysis(self, data, feature, **kwargs):
        pass
