import abc

import plotly.express as px
import plotly.graph_objects as go
from pandas import to_datetime
from plotly.subplots import make_subplots
from typing import List

from tseapy.core.analysis_backends import AnalysisBackend
from tseapy.core.tasks import Task
from tseapy.core.parameters import AnalysisBackendParameter, NumberParameter


class PatternRecognition(Task):

    def __init__(self):
        short_description = "Pattern recognition is the task of finding similar patterns to a given one"
        long_description = """
        Pattern recognition is the task of finding similar patterns to a given one.
        """
        super(PatternRecognition, self).__init__(
            task_name='pattern-recognition',
            short_description=short_description,
            long_description=long_description)

    def get_interaction_script(self, algo):
        script = """
        var data = [{
          x: [],
          y: [],
          type: 'scatter',
          visible: true
        }];

        var layout = {
          title: 'Selected Pattern',
          width: 500,
          height: 500,
          xaxis: {
            title: 'x',
            type: 'date',
            autorange: true
          },
          yaxis: {
            title: 'y',
            autorange: true
          }
        };

        Plotly.newPlot('selectedPattern', data, layout, [0]);

        var start = 0;
        var end = 0;
        var graphDiv = document.getElementById('visualization');
        graphDiv.on('plotly_selected', function(eventData)
        {
            // save start and end
            start = eventData.range.x[0];
            end = eventData.range.x[1];
            if (start > end) {
                let tmp = end;
                end = start;
                start = tmp;
            }
            // update the selected pattern plot
            data[0].x = [];
            data[0].y = [];
            // gather selected data
            eventData.points.forEach(function(pt) {
                data[0].x.push(pt.x);
                data[0].y.push(pt.y);
            });
            Plotly.update('selectedPattern', data, layout, [0]);
        });
        """
        return script

    def get_interaction_view(self, algo: str):
        html = f'<div id="selectedPattern" class="col"></div>'
        return html

    def get_analysis_results(self, data, feature, algo, **kwargs):
        assert feature in data.columns
        # check parameters
        start = kwargs['start']
        end = kwargs['end']
        start = to_datetime(start)
        end = to_datetime(end)
        if start > end:
            tmp = start
            start = end
            end = tmp
            del tmp
        nb_similar_patterns = int(kwargs.pop('nb_similar_patterns'))
        pattern = data.loc[start:end, feature]
        a = self.analysis_backend_factory.get_analysis_backend(algo=algo)
        similar_patterns = a.do_analysis(data, feature, pattern=pattern, nb_similar_patterns=nb_similar_patterns,
                                         **kwargs)

        # make results plot
        fig = make_subplots(rows=2, cols=1, subplot_titles=("Patterns", "Patterns over time"))
        colors = px.colors.qualitative.Plotly

        # plots selected pattern
        fig.append_trace(go.Scatter(
            x=list(range(len(pattern))),
            y=pattern.values,
            mode='lines',
            name='selected pattern',
            legendgroup='selected pattern',
            marker={'color': colors[0]},
        ), row=1, col=1)
        fig.append_trace(go.Scatter(
            x=pattern.index,
            y=pattern.values,
            mode='lines',
            name='selected pattern',
            legendgroup='selected pattern',
            marker={'color': colors[0]},
        ), row=2, col=1)

        for i, similar_pattern in enumerate(similar_patterns, start=1):
            name = f'similar pattern {i}'
            color = colors[i % len(colors)]
            fig.append_trace(go.Scatter(
                x=list(range(len(pattern))),
                y=similar_pattern.values,
                mode='lines',
                name=name,
                legendgroup=name,
                marker={'color': color},
            ), row=1, col=1)
            fig.append_trace(go.Scatter(
                x=similar_pattern.index,
                y=similar_pattern.values,
                mode='lines',
                name=name,
                legendgroup=name,
                marker={'color': color},
            ), row=2, col=1)
        fig.update_layout(height=800)
        return fig


class PatternRecognitionBackend(AnalysisBackend):
    def __init__(self, name: str, short_description: str, long_description: str, callback_url: str,
                 parameters: List[AnalysisBackendParameter]):
        parameters.append(
            NumberParameter(
                name='nb_similar_patterns',
                label='Number of similar patterns',
                description="",
                minimum=1,
                maximum=25,
                step=1,
                default=5,
                onclick="",
                disabled=False
            )
        )
        super().__init__(
            name = name,
            short_description = short_description,
            long_description = long_description,
            callback_url = callback_url,
            parameters = parameters
        )

    @abc.abstractmethod
    def do_analysis(self, data, feature, pattern=None, nb_similar_patterns=5, **kwargs):
        pass
