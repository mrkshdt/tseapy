import abc

from tseapy.core.analysis_backends import AnalysisBackendsList, AnalysisBackend


class Task(abc.ABC):
    """

    """

    def __init__(self, task_name, short_description, long_description):
        self.name = task_name
        self.short_description = short_description
        self.long_description = long_description
        self.analysis_backend_factory = AnalysisBackendsList()

    @staticmethod
    def get_visualization_view(data, feature_to_display: str):
        """Return a Plotly line plot for the given feature."""
        import pandas as pd  # Local import to avoid hard dependency for tests
        from plotly import express as px

        if not isinstance(data, pd.DataFrame):
            raise TypeError('data must be a pandas.DataFrame')

        fig = px.line(x=data.index, y=data[feature_to_display], markers=True)
        fig.update_yaxes(title={'text': feature_to_display})
        return fig

    @abc.abstractmethod
    def get_analysis_results(self, data, feature, algo, **kwargs):
        pass

    @abc.abstractmethod
    def get_interaction_script(self, algo):
        pass

    @abc.abstractmethod
    def get_interaction_view(self, algo: str):
        pass

    def get_parameter_view(self, algo: str):
        return ""

    def get_parameter_script(self, algo: str, analysis_url: str, extra_query_params=None):
        extra_query_params = extra_query_params or []
        a: AnalysisBackend = self.get_analysis_backend(algo)
        extra_params_js = ""
        for param_name in extra_query_params:
            # Query param names are controlled by backend definitions; keep script simple.
            extra_params_js += (
                f"""
            if (typeof {param_name} !== 'undefined') {{
                params.push('{param_name}=' + encodeURIComponent({param_name}));
            }}
                """
            )
        base_url_literal = repr(analysis_url)
        script = """
        function doAnalysis() {
            if (typeof window.validateAnalysisRequest === 'function') {
                const validationMessage = window.validateAnalysisRequest();
                if (validationMessage) {
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = '<div class="alert alert-warning mt-3" role="alert">' + validationMessage + '</div>';
                    return;
                }
            }
            var analysisUrl = """ + base_url_literal + """;
            var params = [];
            """ + extra_params_js + """
            for (let e of document.getElementById('parameters').elements) { 
                if (e.tagName == 'INPUT') {
                    if (e.type == 'checkbox') {
                        params.push(e.id + '=' + encodeURIComponent(e.checked));
                    } else {
                        params.push(e.id + '=' + encodeURIComponent(e.value));
                    }
                }
            } 
            var url = analysisUrl;
            if (params.length > 0) {
                url += '?' + params.join('&');
            }
            fetch(url, {method: 'GET'})
                    .then(response => {
                        if (!response.ok) {
                            return response.text().then(raw => {
                                try {
                                    const err = JSON.parse(raw);
                                    throw new Error(err.error || 'Analysis failed');
                                } catch (_parseError) {
                                    throw new Error(raw || 'Analysis failed');
                                }
                            })
                        }
                        return response.json();
                    })
                    .then(resultsPlot => {
                        const resultsDiv = document.getElementById('results');
                        const data = resultsPlot.data || [];
                        const layout = resultsPlot.layout || {};
                        const config = {};
                        if (resultsDiv.classList.contains('js-plotly-plot')) {
                            Plotly.react(resultsDiv, data, layout, config);
                        } else {
                            Plotly.newPlot(resultsDiv, data, layout, config);
                        }
                    })
                    .catch(err => {
                        const resultsDiv = document.getElementById('results');
                        resultsDiv.innerHTML = '<div class="alert alert-danger mt-3" role="alert">' + err.message + '</div>';
                    });  
        }
        """
        return script

    def add_analysis_backend(self, analysis_backend: AnalysisBackend):
        self.analysis_backend_factory.add_analysis_backend(analysis_backend)

    def get_analysis_backend(self, algo: str):
        try:
            return self.analysis_backend_factory.get_analysis_backend(algo)
        except ValueError as e:
            raise ValueError(f'Algorithm "{algo}" is unknown for task "{self.name}"\n\n{e}')


class TasksList:
    """
    A class for storing Tasks
    """

    def __init__(self):
        self._tasks = dict()

    def add_task(self, analysis_task: Task):
        self._tasks[analysis_task.name] = analysis_task

    def get_tasks(self, task: str):
        if task not in self._tasks.keys():
            raise ValueError(f'Task "{task}" is unknown')
        else:
            return self._tasks.get(task)

    def iter_tasks(self):
        return self._tasks.values()
