import pandas as pd
from app import app, cache


def test_compute_without_data():
    with app.test_client() as client:
        cache.delete('data')
        resp = client.get('/change-in-mean/pelt-l2/compute?penalty=1&min_size=10&jump=5')
        assert resp.status_code == 400
        assert b'No dataset loaded' in resp.data


def test_compute_missing_params():
    with app.test_client() as client:
        cache.set('data', pd.DataFrame({'f': [1, 2, 3]}, index=pd.date_range('2020', periods=3)))
        resp = client.get('/change-in-mean/pelt-l2/compute?penalty=1&min_size=10')
        assert resp.status_code == 400
        assert b'Missing query parameter' in resp.data


def test_display_feature_missing_param():
    with app.test_client() as client:
        cache.set('data', pd.DataFrame({'f': [1, 2]}, index=pd.date_range('2020', periods=2)))
        resp = client.get('/pattern-recognition/mass/display-feature')
        assert resp.status_code == 400
        assert b'Parameter "feature" is required' in resp.data


def test_display_feature_invalid_feature():
    with app.test_client() as client:
        cache.set('data', pd.DataFrame({'f': [1, 2]}, index=pd.date_range('2020', periods=2)))
        resp = client.get('/pattern-recognition/mass/display-feature?feature=x')
        assert resp.status_code == 400
        assert b'Unknown feature column' in resp.data
