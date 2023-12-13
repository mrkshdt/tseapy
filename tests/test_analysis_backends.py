from unittest import TestCase

from tseapy.core.analysis_backends import AnalysisBackendsList, AnalysisBackend
from tseapy.core.parameters import RangeParameter


class TestAnalysisBackendsList(TestCase):
    def test_register_creator(self):
        factory = AnalysisBackendsList()
        factory.add_analysis_backend(
            AnalysisBackend(
                'sliding-l2', 'short description', 'long description', 'url', [
                    RangeParameter(name='p', description='desc', minimum=0, maximum=10, step=1, onclick="",
                                   disabled=False)]
            )
        )
        factory.add_analysis_backend(
            AnalysisBackend('sliding-l1', 'short description', 'long description', 'url', [
                RangeParameter(name='p', description='desc', minimum=0, maximum=10, step=1, onclick="",
                               disabled=False)])
        )
        factory.add_analysis_backend(
            AnalysisBackend('sliding-zscore', 'short description', 'long description', 'url', [
                RangeParameter(name='p', description='desc', minimum=0, maximum=10, step=1, onclick="",
                               disabled=False)])
        )
        factory.add_analysis_backend(
            AnalysisBackend('isolation-forest', 'short description', 'long description', 'url', [
                RangeParameter(name='p', description='desc', minimum=0, maximum=10, step=1, onclick="",
                               disabled=False)])
        )
        factory.add_analysis_backend(
            AnalysisBackend('matrix-profile', 'short description', 'long description', 'url', [
                RangeParameter(name='p', description='desc', minimum=0, maximum=10, step=1, onclick="",
                               disabled=False)])
        )

        self.assertListEqual(
            sorted(list(factory._backends.keys())),
            sorted(['sliding-l1', 'sliding-l2', 'sliding-zscore', 'isolation-forest', 'matrix-profile'])
        )

    def test_get_backend(self):
        factory = AnalysisBackendsList()
        factory.add_analysis_backend(
            AnalysisBackend(
                name='sliding-l2',
                short_description='',
                long_description='long description',
                callback_url='url',
                parameters=[
                    RangeParameter(name='p', description='desc', minimum=0, maximum=10, step=1, onclick="",
                                   disabled=False)
                ]
            )
        )

        # The function should return an instance of the corresponding registered type
        backend = factory.get_analysis_backend('sliding-l2')
        self.assertIsInstance(backend, AnalysisBackend)

        # The function should raise an exception when the task is not registered
        with self.assertRaises(ValueError) as e:
            factory.get_analysis_backend('sliding-foobar')
            self.assertEquals(str(e), 'Algo "sliding-foobar" is unknown')

    def test_create_callback_url(self):
        url = AnalysisBackend.create_callback_url('task', 'algo')
        self.assertEqual(url, "'/task/algo/compute?'")

        url = AnalysisBackend.create_callback_url('task', 'algo', 'foo')
        self.assertEqual(url, "'/task/algo/compute?foo='+foo")

        url = AnalysisBackend.create_callback_url('task', 'algo', 'foo', 'bar')
        self.assertEqual(url, "'/task/algo/compute?foo='+foo+'&bar='+bar")

        url = AnalysisBackend.create_callback_url('task', 'algo', 'foo', 'foo', 'bar')
        self.assertEqual(url, "'/task/algo/compute?foo='+foo+'&foo='+foo+'&bar='+bar")

        url = AnalysisBackend.create_callback_url('task', 'algo', 'foo', 'foo', 'bar')
        self.assertEqual(url, "'/task/algo/compute?foo='+foo+'&foo='+foo+'&bar='+bar")
