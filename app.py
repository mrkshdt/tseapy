import json
import secrets

import pandas as pd
import plotly.utils
from flask import Flask, render_template, request, session, abort, jsonify, redirect, url_for
from werkzeug.exceptions import RequestEntityTooLarge
from flask_caching import Cache

from tseapy.core.analysis_backends import AnalysisBackend
from tseapy.core.tasks import Task, TasksList
from tseapy.data.examples import get_air_quality_uci
from tseapy.data.upload import CSVUploadError, parse_csv_upload
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
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
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

ALLOWED_EXTENSIONS = {"csv"}
UPLOAD_STEPS = ("upload", "preview", "configure", "analysis")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def infer_column_type(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "date"
    sample = series.dropna().head(50)
    if sample.empty:
        return "text"
    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    if parsed.notna().mean() >= 0.8:
        return "date"
    return "text"


def build_preview_context(dataframe: pd.DataFrame, message: str = "") -> dict:
    column_types = {column: infer_column_type(dataframe[column]) for column in dataframe.columns}
    numeric_columns = [column for column, kind in column_types.items() if kind == "numeric"]
    date_columns = [column for column, kind in column_types.items() if kind == "date"]
    date_summary = "Not available"
    if date_columns:
        parsed = pd.to_datetime(dataframe[date_columns[0]], errors="coerce", format="mixed")
        parsed = parsed.dropna()
        if not parsed.empty:
            date_summary = f"{parsed.min().strftime('%Y-%m-%d')} to {parsed.max().strftime('%Y-%m-%d')}"
    return {
        "preview_table": dataframe.head(10).to_html(
            classes="table table-striped table-sm table-bordered align-middle mb-0",
            index=False,
            border=0
        ),
        "columns": dataframe.columns.tolist(),
        "column_types": column_types,
        "numeric_columns": numeric_columns,
        "row_count": len(dataframe),
        "date_summary": date_summary,
        "message": message,
        "steps": UPLOAD_STEPS,
        "current_step": "preview"
    }


def get_data_or_abort() -> pd.DataFrame:
    """Retrieve cached data or abort with HTTP 400."""
    data = cache.get('data')
    if data is None:
        abort(400, description='No dataset loaded. Please load data first.')
    return data


def get_task_or_abort(task_name: str) -> Task:
    try:
        return tasks.get_tasks(task_name)
    except ValueError as exc:
        abort(404, description=str(exc))


def get_backend_or_abort(task_obj: Task, algo_name: str) -> AnalysisBackend:
    try:
        return task_obj.analysis_backend_factory.get_analysis_backend(algo_name)
    except ValueError as exc:
        abort(404, description=str(exc))


def get_feature_to_display():
    data = get_data_or_abort()
    return session.get('feature_to_display', data.columns[0])


def render_algo_template(t: Task, a: AnalysisBackend):
    """
    Utility function to render a specific algorithm template
    """
    data: pd.DataFrame = get_data_or_abort()
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
    if cache.get("data") is None:
        return redirect(url_for("upload"))

    upload_notice = session.pop("upload_notice", None)
    html = render_template(
        'index.html',
        tasks=[(t.name, t.short_description) for t in tasks._tasks.values()],
        upload_notice=upload_notice,
    )
    return html


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        error = request.args.get("error", "")
        message = request.args.get("message", "")
        return render_template(
            "upload.html",
            error=error,
            message=message,
            max_upload_mb=app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024),
            steps=UPLOAD_STEPS,
            current_step="upload"
        )

    if request.form.get("use_demo_dataset"):
        demo_data = get_air_quality_uci().reset_index()
        cache.set("raw_data", demo_data)
        return redirect(url_for("upload_preview"))

    uploaded_file = request.files.get("file")
    if uploaded_file is None or uploaded_file.filename is None or uploaded_file.filename == "":
        return render_template(
            "upload.html",
            error="Please choose a CSV file first.",
            max_upload_mb=app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024),
            steps=UPLOAD_STEPS,
            current_step="upload"
        ), 400

    if not allowed_file(uploaded_file.filename):
        return render_template(
            "upload.html",
            error="Invalid file type. Please upload a .csv file.",
            max_upload_mb=app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024),
            steps=UPLOAD_STEPS,
            current_step="upload"
        ), 400

    try:
        dataframe = parse_csv_upload(uploaded_file)
    except CSVUploadError as exc:
        return render_template(
            "upload.html",
            error=str(exc),
            max_upload_mb=app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024),
            steps=UPLOAD_STEPS,
            current_step="upload"
        ), 400

    cache.set("raw_data", dataframe)
    return redirect(url_for("upload_preview"))


@app.route('/upload/preview', methods=['GET'])
def upload_preview():
    dataframe = cache.get("raw_data")
    if dataframe is None:
        return redirect(url_for("upload", error="Session expired. Upload a CSV file again."))

    return render_template("upload_preview.html", **build_preview_context(dataframe))


@app.route('/upload/configure', methods=['POST'])
def upload_configure():
    dataframe = cache.get("raw_data")
    if dataframe is None:
        return redirect(url_for("upload", error="Session expired. Upload a CSV file again."))

    time_column = request.form.get("time_column", "").strip()
    value_column = request.form.get("value_column", "").strip()
    confirmation = request.form.get("confirm_selection")

    if time_column not in dataframe.columns or value_column not in dataframe.columns:
        context = build_preview_context(dataframe, message="Please choose valid columns from the dropdown lists.")
        return render_template("upload_preview.html", error="Selected columns are invalid.", **context), 400

    if confirmation != "on":
        context = build_preview_context(dataframe, message="Confirm your selections before proceeding.")
        return render_template("upload_preview.html", error="Please confirm your selections.", **context), 400

    parsed_index = pd.to_datetime(dataframe[time_column], errors="coerce", format="mixed")
    if parsed_index.notna().sum() == 0:
        context = build_preview_context(dataframe, message="The selected time column cannot be parsed as datetime.")
        return render_template("upload_preview.html", error="Invalid datetime column.", **context), 400

    parsed_value = pd.to_numeric(dataframe[value_column], errors="coerce")
    configured = pd.DataFrame({value_column: parsed_value.to_numpy()}, index=parsed_index)
    total_rows = len(configured)
    configured = configured.dropna(axis=0, how="any").sort_index()
    removed_rows = total_rows - len(configured)
    if configured.empty:
        context = build_preview_context(
            dataframe,
            message="No valid rows remained after parsing datetime and numeric values."
        )
        return render_template("upload_preview.html", error="Configuration produced an empty dataset.", **context), 400

    cache.set("data", configured)
    cache.delete("raw_data")
    session["feature_to_display"] = value_column
    if removed_rows > 0:
        session["upload_notice"] = f"{removed_rows} rows were removed due to missing values."
    else:
        session["upload_notice"] = "Dataset loaded successfully."

    return redirect(url_for("index"))


@app.route('/<task>', methods=['GET'])
def display_task(task):
    t: Task = get_task_or_abort(task)
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
    t: Task = get_task_or_abort(task)
    a: AnalysisBackend = get_backend_or_abort(t, algo)
    html = render_algo_template(t=t, a=a)
    return html


def _expected_params(backend: AnalysisBackend):
    params = [p.name for p in backend.parameters]
    callback = backend.callback_url.strip("'")
    if 'compute?' in callback:
        query = callback.split('compute?')[1]
        if query:
            for part in query.split('&'):
                if part:
                    name = part.split('=')[0]
                    if name and name not in params:
                        params.append(name)
    return params


@app.route('/<task>/<algo>/compute', methods=['GET'])
def perform_analysis(task, algo):
    t: Task = get_task_or_abort(task)
    backend = get_backend_or_abort(t, algo)
    data = get_data_or_abort()
    expected = _expected_params(backend)
    missing = [p for p in expected if p not in request.args]
    if missing:
        abort(400, description=f"Missing query parameter(s): {', '.join(missing)}")
    feature = request.args.get('feature', get_feature_to_display())
    if feature not in data.columns:
        abort(400, description='Unknown feature column')
    analysis_kwargs = dict(request.args)
    analysis_kwargs.pop("feature", None)
    try:
        fig = t.get_analysis_results(data=data, feature=feature, algo=algo, **analysis_kwargs)
    except ValueError as exc:
        abort(400, description=str(exc))
    except (TypeError, IndexError, RuntimeError) as exc:
        abort(400, description=f"Algorithm input error: {exc}")

    response = app.response_class(
        response=json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder),
        status=200,
        mimetype='application/json'
    )
    return response


@app.route('/<task>/<algo>/display-feature', methods=['GET'])
def display_feature(task, algo):
    t: Task = get_task_or_abort(task)
    a: AnalysisBackend = get_backend_or_abort(t, algo)
    data: pd.DataFrame = get_data_or_abort()

    feature_to_display: str = request.args.get('feature')
    if feature_to_display is None:
        abort(400, description='Parameter "feature" is required')
    if feature_to_display not in data.columns:
        abort(400, description='Unknown feature column')
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
    t: Task = get_task_or_abort(task)
    a: AnalysisBackend = get_backend_or_abort(t, algo)

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


@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': error.description}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': error.description if getattr(error, "description", None) else "Not found"}), 404


@app.errorhandler(RequestEntityTooLarge)
def file_too_large(_error):
    return render_template(
        "upload.html",
        error=f"File is too large. Maximum size is {app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)} MB.",
        max_upload_mb=app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024),
        steps=UPLOAD_STEPS,
        current_step="upload"
    ), 413


@app.route("/favicon.ico")
def favicon():
    return "", 204

if __name__ == "__main__":
    app.run(debug=True)
