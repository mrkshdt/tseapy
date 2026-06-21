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

        if isinstance(result, dict) and result.get('kind') == 'backtest':
            return self._build_backtest_figure(result, feature)

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

    @staticmethod
    def _build_backtest_figure(result, feature):
        palette = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        ]
        model_names = list(result['per_model_metric'].keys())
        colors = {name: palette[i % len(palette)] for i, name in enumerate(model_names)}
        best_model = result['best_model']
        metric_label = result['metric_label']

        fig = make_subplots(
            rows=3,
            cols=1,
            specs=[[{"type": "scatter"}], [{"type": "scatter"}], [{"type": "table"}]],
            row_heights=[0.45, 0.27, 0.28],
            vertical_spacing=0.07,
            subplot_titles=(
                "Backtest windows: actuals vs. forecasts",
                f"{metric_label} per window (lower is better)",
                "Leaderboard report",
            ),
        )

        # Row 1: historical series with each model's forecast overlaid per window.
        fig.add_trace(
            go.Scatter(
                x=result['history_x'],
                y=result['history_y'],
                mode='lines',
                name='Actual',
                line=dict(color='#444444', width=1.5),
                legendgroup='actual',
            ),
            row=1,
            col=1,
        )

        legend_shown = set()
        for fold in result['folds']:
            cutoff_x = fold['test_x'][0] if len(fold['test_x']) else None
            if cutoff_x is not None:
                fig.add_vline(
                    x=cutoff_x,
                    line=dict(color='rgba(120,120,120,0.4)', width=1, dash='dot'),
                    row=1,
                    col=1,
                )
            for name in model_names:
                model_result = fold['models'].get(name)
                if not model_result or len(model_result['forecast_y']) == 0:
                    continue
                show = name not in legend_shown
                legend_shown.add(name)
                fig.add_trace(
                    go.Scatter(
                        x=model_result['forecast_x'],
                        y=model_result['forecast_y'],
                        mode='lines',
                        name=name,
                        legendgroup=name,
                        showlegend=show,
                        line=dict(color=colors[name], width=1.6),
                        hovertemplate=(
                            f"{name}<br>window {fold['fold']} (cutoff {fold['cutoff_label']})"
                            "<br>%{x}: %{y:.4f}<extra></extra>"
                        ),
                    ),
                    row=1,
                    col=1,
                )

        # Row 2: ranking metric per window, one line per model.
        for name in model_names:
            fig.add_trace(
                go.Scatter(
                    x=result['fold_labels'],
                    y=result['per_model_metric'][name],
                    mode='lines+markers',
                    name=name,
                    legendgroup=name,
                    showlegend=False,
                    line=dict(color=colors[name]),
                ),
                row=2,
                col=1,
            )

        # Row 3: aggregated leaderboard with the recommended model highlighted.
        leaderboard = result['leaderboard']

        def _fmt(value, spec):
            return format(value, spec) if value == value else 'NaN'

        highlight = 'rgba(44, 160, 44, 0.18)'
        row_fill = [
            highlight if row['Model'] == best_model else 'white' for row in leaderboard
        ]
        fig.add_trace(
            go.Table(
                columnwidth=[1, 3, 2, 2, 2, 2.5, 1.5],
                header=dict(
                    values=[
                        'Rank', 'Model', 'MAE', 'RMSE', 'MAPE (%)',
                        f'{metric_label} Std', 'Wins',
                    ],
                    fill_color='#2c3e50',
                    font=dict(color='white'),
                    align='left',
                ),
                cells=dict(
                    values=[
                        [row['Rank'] for row in leaderboard],
                        [row['Model'] for row in leaderboard],
                        [_fmt(row['MAE'], '.4f') for row in leaderboard],
                        [_fmt(row['RMSE'], '.4f') for row in leaderboard],
                        [_fmt(row['MAPE (%)'], '.2f') for row in leaderboard],
                        [_fmt(row['Std'], '.4f') for row in leaderboard],
                        [row['Wins'] for row in leaderboard],
                    ],
                    fill_color=[row_fill],
                    align='left',
                ),
            ),
            row=3,
            col=1,
        )

        fig.update_yaxes(title={'text': feature}, row=1, col=1)
        fig.update_yaxes(title={'text': metric_label}, row=2, col=1)
        fig.update_xaxes(title={'text': 'Window cutoff'}, row=2, col=1)

        recommendation = (
            f"Recommended: {best_model} — lowest mean {metric_label} over "
            f"{result['n_windows']} {result['window_type']} window(s), horizon {result['horizon']}"
            if best_model
            else "No model could be evaluated."
        )
        fig.update_layout(
            height=1000,
            title={'text': recommendation},
            legend=dict(orientation='h', yanchor='bottom', y=-0.04, xanchor='left', x=0),
        )
        return fig


class ForecastingBackend(AnalysisBackend):
    @abc.abstractmethod
    def do_analysis(self, data, feature, **kwargs):
        pass
