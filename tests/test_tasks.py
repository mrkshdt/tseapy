from unittest import TestCase

from tseapy.core.analysis_backends import AnalysisBackend
from tseapy.core.tasks import Task, TasksList


class DummyBackend(AnalysisBackend):
    def do_analysis(self, data, feature, **kwargs):
        return None


class DummyTask(Task):
    def get_analysis_results(self, data, feature, algo, **kwargs):
        return {}

    def get_interaction_script(self, algo):
        return ""

    def get_interaction_view(self, algo: str):
        return ""

    def get_parameter_view(self, algo: str):
        return ""


class TestTasksList(TestCase):
    def test_register(self):
        factory = TasksList()
        factory.add_task(DummyTask('change-point-detection', 'some short description', 'some long description'))
        factory.add_task(DummyTask('outlier-detection', 'some short description', 'some long description'))
        factory.add_task(DummyTask('motifs-discovery', 'some short description', 'some long description'))

        self.assertListEqual(
            sorted(list(t.name for t in factory.iter_tasks())),
            sorted(['change-point-detection', 'outlier-detection', 'motifs-discovery'])
        )

    def test_get_backend(self):
        factory = TasksList()
        factory.add_task(DummyTask('change-point-detection', 'some short description', 'some long description'))

        cpt_detector = factory.get_tasks('change-point-detection')
        self.assertIsInstance(cpt_detector, Task)

        with self.assertRaises(ValueError):
            factory.get_tasks('outlier-detection')


class TestTask(TestCase):
    def test_get_parameter_script(self):
        task = DummyTask(task_name='task', short_description='', long_description='')
        task.add_analysis_backend(
            DummyBackend(
                name='algo',
                short_description='short description',
                long_description='long description',
                callback_url="'/task/algo/compute'",
                parameters=[],
                required_query_params=["param1", "param2"],
            )
        )
        actual_javascript = task.get_parameter_script(
            'algo',
            analysis_url="/task/algo/compute",
            extra_query_params=["param1", "param2"],
        )
        self.assertIn("var analysisUrl = '/task/algo/compute';", actual_javascript)
        self.assertIn("if (typeof param1 !== 'undefined')", actual_javascript)
        self.assertIn("if (typeof param2 !== 'undefined')", actual_javascript)
        self.assertIn("fetch(url, {method: 'GET'})", actual_javascript)
        self.assertIn("Plotly.newPlot(resultsDiv, data, layout, config);", actual_javascript)
        self.assertIn("Plotly.react(resultsDiv, data, layout, config);", actual_javascript)
