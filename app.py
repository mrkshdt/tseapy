import json
import secrets

import pandas as pd
import plotly.utils
from flask import Flask, render_template, request, session
from flask_caching import Cache

from tseapy.core.analysis_backends import AnalysisBackend
from tseapy.core.tasks import Task, TasksList
from tseapy.data.examples import get_air_quality_uci
from tseapy.tasks import motif_detection
from tseapy.tasks.change_in_mean import ChangeInMean
from tseapy.tasks.change_in_mean.pelt_l2 import PeltL2
from tseapy.tasks.change_in_mean.sliding_window_l2 import SlidingWindowL2
from tseapy.tasks.pattern_recognition import PatternRecognition
from tseapy.tasks.pattern_recognition.mass import Mass
from tseapy.tasks.motif_detection import MotifDetection
from tseapy.tasks.motif_detection.matrixprofile import Matrixprofile
from tseapy.tasks.motif_detection.pan_matrixprofile import PanMatrixprofile
from tseapy.tasks.smoothing import Smoothing
from tseapy.tasks.smoothing.moving_average import MovingAverage
from tseapy.core.parameters import NumberParameter, BooleanParameter, ListParameter, RangeParameter

cache = Cache(
    config={
        "DEBUG": True,  # some Flask specific configs
        "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
        "CACHE_DEFAULT_TIMEOUT": 3600
    }
)
app = Flask(__name__)
app.secret_key = secrets.token_hex()
cache.init_app(app)

pattern_recognition = PatternRecognition()
pattern_recognition.add_analysis_backend(Mass())

change_in_mean = ChangeInMean()
change_in_mean.add_analysis_backend(PeltL2())
change_in_mean.add_analysis_backend(SlidingWindowL2())

smoothing = Smoothing()
smoothing.add_analysis_backend(MovingAverage())

motif_detection = MotifDetection()
motif_detection.add_analysis_backend(Matrixprofile())
motif_detection.add_analysis_backend(PanMatrixprofile())

tasks = TasksList()
tasks.add_task(pattern_recognition)
tasks.add_task(change_in_mean)
tasks.add_task(motif_detection)
tasks.add_task(smoothing)

def get_feature_to_display():
    return session.get('feature_to_display', cache.get('data').columns[0])


def render_algo_template(t: Task, a: AnalysisBackend):
    """
    Utility function to render a specific algorithm template
    """
    data: pd.DataFrame = cache.get('data')
    data_view = t.get_visualization_view(data=data, feature_to_display=get_feature_to_display())
    interaction_script = t.get_interaction_script(algo=a.name)
    interaction_view = t.get_interaction_view(algo=a.name)
    parameter_script = t.get_parameter_script(algo=a.name)
    html = render_template(
        'algo.html',
        task=t.name,
        algo=a.name,
        graphJSON=json.dumps(data_view, cls=plotly.utils.PlotlyJSONEncoder),
        features=data.columns.tolist(),
        interactionScript=interaction_script,
        interactionView=interaction_view,
        parameterScript=parameter_script,
        parameters=a.parameters
    )
    return html


# create index page function
@app.route('/')
def index():
    # TODO create a menu + route for setting up data!
    data = get_air_quality_uci()[:1000]
    cache.set("data", data)
    session['feature_to_display'] = data.columns[0]
    html = render_template(
        'index.html',
        tasks=[(t.name, t.short_description) for t in tasks._tasks.values()],
    )
    return html


@app.route('/<task>', methods=['GET'])
def display_task(task):
    t: Task = tasks.get_tasks(task)
    html = render_template(
        'task.html',
        task=task,
        description=t.short_description,
        algorithms=[(a.name, a.short_description) for a in t.analysis_backend_factory._backends.values()]
    )
    return html


@app.route('/<task>/<algo>', methods=['GET'])
def display_algo(task, algo):
    """

    """
    t: Task = tasks.get_tasks(task)
    a: AnalysisBackend = t.analysis_backend_factory.get_analysis_backend(algo)
    html = render_algo_template(t=t, a=a)
    return html


@app.route('/<task>/<algo>/compute', methods=['GET'])
def perform_analysis(task, algo):
    t: Task = tasks.get_tasks(task)
    fig = t.get_analysis_results(data=cache.get('data'), feature=get_feature_to_display(), algo=algo,
                                 **request.args)

    response = app.response_class(
        response=json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route('/<task>/<algo>/display-feature', methods=['GET'])
def display_feature(task, algo):
    t: Task = tasks.get_tasks(task)
    a: AnalysisBackend = t.analysis_backend_factory.get_analysis_backend(algo)
    data: pd.DataFrame = cache.get('data')

    feature_to_display: str = request.args.get('feature')
    assert feature_to_display in data.columns
    session['feature_to_display'] = feature_to_display

    response = app.response_class(
        response=json.dumps(
            {
                'data': {
                    'x': [data[feature_to_display].index.strftime("%Y-%m-%d %H:%M:%S").tolist()],
                    'y': [data[feature_to_display].to_list()]
                },
                'layout': {
                    'yaxis': {'title': {'text': feature_to_display}}
                }
            }),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route('/<task>/<algo>/export', methods=['GET'])
def export(task, algo):
    t: Task = tasks.get_tasks(task)
    a: AnalysisBackend = t.analysis_backend_factory.get_analysis_backend(algo)

    # get data

    # get task name

    # get backend name, library used, version, method, parameters name, values

    # get results

    raise NotImplementedError()

#make function available to templates
@app.context_processor
def utility_processor():
    def is_instance(object, type):
        return isinstance(object, type)
    return dict(is_instance=is_instance,
                BooleanParameter=BooleanParameter,
                NumberParameter=NumberParameter,
                RangeParameter=RangeParameter,
                ListParameter=ListParameter)

if __name__ == "__main__":
    app.run(debug=True)
