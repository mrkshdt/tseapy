from unittest import TestCase

from tseapy.core.analysis_backends import AnalysisBackend
from tseapy.core.tasks import Task, TasksList


class TestTasksList(TestCase):
    def test_register(self):
        factory = TasksList()
        factory.add_task(Task('change-point-detection', 'some short description', 'some long description'))
        factory.add_task(Task('outlier-detection', 'some short description', 'some long description'))
        factory.add_task(Task('motifs-discovery', 'some short description', 'some long description'))

        self.assertListEqual(
            sorted(list(factory._tasks.keys())),
            sorted(['change-point-detection', 'outlier-detection', 'motifs-discovery'])
        )

    def test_get_backend(self):
        factory = TasksList()
        factory.add_task(Task('change-point-detection', 'some short description', 'some long description'))

        # The function should return an instance of the corresponding registered type
        cpt_detector = factory.get_tasks('change-point-detection')
        self.assertIsInstance(cpt_detector, Task)

        # The function should raise an exception when the task is not registered
        with self.assertRaises(ValueError) as e:
            factory.get_tasks('outlier-detection', )
            self.assertEquals(str(e), 'Task "outlier-detection" is unknown')


class TestTask(TestCase):

    def test_get_parameter_script(self):
        task = Task(task_name='task', short_description='', long_description='')
        task.add_analysis_backend(
            AnalysisBackend(
                name='algo',
                short_description='short description',
                long_description='long description',
                callback_url="'/task/algo/compute?param1='+param1+'&param2='+param2",
                parameters=[]
            )
        )
        expected_javascript = """
        function doAnalysis() {
            var url = '/task/algo/compute?param1='+param1+'&param2='+param2;
            for (let e of document.getElementById('parameters').elements) { 
                if (e.tagName == 'INPUT') {
                    if (e.type == 'checkbox') {
                        url += '&' + e.id +'=' + e.checked;
                    } else {
                        url += '&' + e.id +'=' + e.value;
                    }
                }
            } 
            fetch(url, {method: 'GET'})
                    .then(response => response.json())
                    .then(resultsPlot => Plotly.newPlot('results', resultsPlot, {}));  
        }
        """
        actual_javascript = task.get_parameter_script('algo')
        self.assertEqual(expected_javascript, actual_javascript)

