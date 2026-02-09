from unittest import TestCase

from tseapy.core.analysis_backends import AnalysisBackendsList, AnalysisBackend
from tseapy.core.parameters import RangeParameter


class DummyBackend(AnalysisBackend):
    def do_analysis(self, data, feature, **kwargs):
        return None


class TestAnalysisBackendsList(TestCase):
    def test_register_creator(self):
        factory = AnalysisBackendsList()
        factory.add_analysis_backend(
            DummyBackend(
                'sliding-l2', 'short description', 'long description', 'url', [
                    RangeParameter(name='p', description='desc', minimum=0, maximum=10, step=1, onclick="",
                                   disabled=False)]
            )
        )
        factory.add_analysis_backend(
            DummyBackend('sliding-l1', 'short description', 'long description', 'url', [
                RangeParameter(name='p', description='desc', minimum=0, maximum=10, step=1, onclick="",
                               disabled=False)])
        )
        factory.add_analysis_backend(
            DummyBackend('sliding-zscore', 'short description', 'long description', 'url', [
                RangeParameter(name='p', description='desc', minimum=0, maximum=10, step=1, onclick="",
                               disabled=False)])
        )
        factory.add_analysis_backend(
            DummyBackend('isolation-forest', 'short description', 'long description', 'url', [
                RangeParameter(name='p', description='desc', minimum=0, maximum=10, step=1, onclick="",
                               disabled=False)])
        )
        factory.add_analysis_backend(
            DummyBackend('matrix-profile', 'short description', 'long description', 'url', [
                RangeParameter(name='p', description='desc', minimum=0, maximum=10, step=1, onclick="",
                               disabled=False)])
        )

        self.assertListEqual(
            sorted(list(a.name for a in factory.iter_backends())),
            sorted(['sliding-l1', 'sliding-l2', 'sliding-zscore', 'isolation-forest', 'matrix-profile'])
        )

    def test_get_backend(self):
        factory = AnalysisBackendsList()
        factory.add_analysis_backend(
            DummyBackend(
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

        backend = factory.get_analysis_backend('sliding-l2')
        self.assertIsInstance(backend, AnalysisBackend)

        with self.assertRaises(ValueError):
            factory.get_analysis_backend('sliding-foobar')

    def test_create_callback_url(self):
        url = AnalysisBackend.create_callback_url('task', 'algo')
        self.assertEqual(url, "'/task/algo/compute'")

        url = AnalysisBackend.create_callback_url('task', 'algo', 'foo')
        self.assertEqual(url, "'/task/algo/compute'")

        url = AnalysisBackend.create_callback_url('task', 'algo', 'foo', 'bar')
        self.assertEqual(url, "'/task/algo/compute'")
