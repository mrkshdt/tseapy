import io

import pandas as pd
from app import app, cache


def reset_cache_state():
    cache.delete('data')
    cache.delete('raw_data')


def test_index_redirects_to_upload_without_data():
    with app.test_client() as client:
        reset_cache_state()
        resp = client.get('/')
        assert resp.status_code == 302
        assert resp.headers['Location'].endswith('/upload')


def test_upload_page_available():
    with app.test_client() as client:
        reset_cache_state()
        resp = client.get('/upload')
        assert resp.status_code == 200
        assert b'Upload CSV' in resp.data


def test_healthz_is_available_without_dataset():
    with app.test_client() as client:
        reset_cache_state()
        resp = client.get('/healthz')
        assert resp.status_code == 200
        assert resp.get_json() == {"status": "ok"}


def test_index_lists_new_tasks():
    with app.test_client() as client:
        reset_cache_state()
        cache.set('data', pd.DataFrame({'f': [1, 2, 3]}, index=pd.date_range('2020-01-01', periods=3, freq='D')))
        resp = client.get('/')
        assert resp.status_code == 200
        assert b'decomposition' in resp.data
        assert b'frequency-analysis' in resp.data


def test_new_task_pages_available():
    with app.test_client() as client:
        reset_cache_state()
        assert client.get('/decomposition').status_code == 200
        assert client.get('/frequency-analysis').status_code == 200
        assert client.get('/forecasting').status_code == 200


def test_forecasting_comparison_page_available():
    with app.test_client() as client:
        reset_cache_state()
        cache.set('data', pd.DataFrame({'f': list(range(60))}, index=pd.date_range('2020-01-01', periods=60, freq='D')))
        resp = client.get('/forecasting/forecast-comparison')
        assert resp.status_code == 200
        assert b'forecast-comparison' in resp.data


def test_upload_rejects_non_csv():
    with app.test_client() as client:
        reset_cache_state()
        data = {'file': (io.BytesIO(b'not,csv'), 'sample.txt')}
        resp = client.post('/upload', data=data, content_type='multipart/form-data')
        assert resp.status_code == 400
        assert b'Invalid file type' in resp.data


def test_upload_preview_roundtrip():
    with app.test_client() as client:
        reset_cache_state()
        payload = b"time;value\n2024-01-01;10\n2024-01-02;20\n"
        data = {'file': (io.BytesIO(payload), 'sample.csv')}
        resp = client.post('/upload', data=data, content_type='multipart/form-data')
        assert resp.status_code == 302
        assert resp.headers['Location'].endswith('/upload/preview')

        preview = client.get('/upload/preview')
        assert preview.status_code == 200
        assert b'Preview and Configure' in preview.data
        assert b'value (numeric)' in preview.data


def test_demo_dataset_flow():
    with app.test_client() as client:
        reset_cache_state()
        resp = client.post('/upload', data={'use_demo_dataset': '1'})
        assert resp.status_code == 302
        assert resp.headers['Location'].endswith('/upload/preview')


def test_upload_preview_requires_raw_data():
    with app.test_client() as client:
        reset_cache_state()
        resp = client.get('/upload/preview')
        assert resp.status_code == 302
        assert resp.headers['Location'].endswith('/upload?error=Session+expired.+Upload+a+CSV+file+again.')


def test_upload_configure_invalid_datetime():
    with app.test_client() as client:
        reset_cache_state()
        cache.set('raw_data', pd.DataFrame({'t': ['abc', 'def'], 'v': [1, 2]}))
        resp = client.post('/upload/configure', data={
            'time_column': 't',
            'value_column': 'v',
            'confirm_selection': 'on'
        })
        assert resp.status_code == 400
        assert b'Invalid datetime column.' in resp.data


def test_upload_configure_success_sets_data():
    with app.test_client() as client:
        reset_cache_state()
        cache.set('raw_data', pd.DataFrame({'t': ['2024-01-01', '2024-01-02'], 'v': ['1', '2']}))
        resp = client.post('/upload/configure', data={
            'time_column': 't',
            'value_column': 'v',
            'confirm_selection': 'on'
        })
        assert resp.status_code == 302
        assert resp.headers['Location'].endswith('/')
        configured = cache.get('data')
        assert configured is not None
        assert configured.columns.tolist() == ['v']


def test_favicon_is_not_routed_as_task():
    with app.test_client() as client:
        resp = client.get('/favicon.ico')
        assert resp.status_code == 204


def test_unknown_task_returns_404():
    with app.test_client() as client:
        resp = client.get('/not-a-task')
        assert resp.status_code == 404
        assert b'Task \\"not-a-task\\" is unknown' in resp.data


def test_pattern_recognition_requires_selected_range():
    with app.test_client() as client:
        reset_cache_state()
        cache.set('data', pd.DataFrame({'f': [1, 2, 3, 4]}, index=pd.date_range('2020-01-01', periods=4, freq='D')))
        resp = client.get('/pattern-recognition/mass/compute?start=0&end=0&normalize=true&p=2.0&nb_similar_patterns=2&feature=f')
        assert resp.status_code == 400
        assert b'Select a date range on the main chart' in resp.data


def test_matrixprofile_oversized_width_is_clamped():
    with app.test_client() as client:
        reset_cache_state()
        cache.set('data', pd.DataFrame({'f': list(range(20))}, index=pd.date_range('2020-01-01', periods=20, freq='D')))
        resp = client.get('/motif-detection/matrixprofile/compute?penalty=0.4&width=100&feature=f')
        assert resp.status_code == 200


def test_panmatrixprofile_invalid_bounds_returns_400():
    with app.test_client() as client:
        reset_cache_state()
        cache.set('data', pd.DataFrame({'f': list(range(20))}, index=pd.date_range('2020-01-01', periods=20, freq='D')))
        resp = client.get('/motif-detection/panmatrixprofile/compute?penalty=10&minimum_width=50&maximum_width=150&percentage=2&feature=f')
        assert resp.status_code == 400
        assert b'minimum_width must be less than' in resp.data


def test_compute_without_data():
    with app.test_client() as client:
        reset_cache_state()
        resp = client.get('/change-in-mean/pelt-l2/compute?penalty=1&min_size=10&jump=5')
        assert resp.status_code == 400
        assert b'No dataset loaded' in resp.data


def test_compute_missing_params():
    with app.test_client() as client:
        reset_cache_state()
        cache.set('data', pd.DataFrame({'f': [1, 2, 3]}, index=pd.date_range('2020', periods=3)))
        resp = client.get('/change-in-mean/pelt-l2/compute?penalty=1&min_size=10')
        assert resp.status_code == 400
        assert b'Missing query parameter' in resp.data


def test_forecasting_comparison_compute_with_baselines():
    with app.test_client() as client:
        reset_cache_state()
        cache.set('data', pd.DataFrame({'f': list(range(60))}, index=pd.date_range('2020-01-01', periods=60, freq='D')))
        resp = client.get(
            '/forecasting/forecast-comparison/compute'
            '?horizon=5&season_length=3'
            '&use_auto_arima=false&use_auto_ets=false&use_auto_theta=false'
            '&use_naive=true&use_seasonal_naive=false&use_historic_average=true'
            '&use_lightgbm=false&use_xgboost=false'
            '&feature=f'
        )
        assert resp.status_code == 200


def test_display_feature_missing_param():
    with app.test_client() as client:
        reset_cache_state()
        cache.set('data', pd.DataFrame({'f': [1, 2]}, index=pd.date_range('2020', periods=2)))
        resp = client.get('/pattern-recognition/mass/display-feature')
        assert resp.status_code == 400
        assert b'Parameter \\"feature\\" is required' in resp.data


def test_display_feature_invalid_feature():
    with app.test_client() as client:
        reset_cache_state()
        cache.set('data', pd.DataFrame({'f': [1, 2]}, index=pd.date_range('2020', periods=2)))
        resp = client.get('/pattern-recognition/mass/display-feature?feature=x')
        assert resp.status_code == 400
        assert b'Unknown feature column' in resp.data


def test_export_returns_clear_not_available_message():
    with app.test_client() as client:
        resp = client.get('/pattern-recognition/mass/export')
        assert resp.status_code == 501
        assert b'Export is not available' in resp.data
