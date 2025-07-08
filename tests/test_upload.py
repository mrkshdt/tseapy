import io
from unittest import TestCase

from app import app, cache

class TestUpload(TestCase):
    def setUp(self):
        self.client = app.test_client()
        cache.clear()

    def test_upload_valid_csv(self):
        csv = "date,value\n2021-01-01,1\n2021-01-02,2\n"
        response = self.client.post('/upload-data', data={'file': (io.BytesIO(csv.encode()), 'data.csv')}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 302)
        df = cache.get('data')
        self.assertIsNotNone(df)
        self.assertEqual(df.iloc[0]['value'], 1)

    def test_upload_invalid_csv(self):
        csv = "a,b\n1,2\n3,4\n"
        response = self.client.post('/upload-data', data={'file': (io.BytesIO(csv.encode()), 'data.csv')}, content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
