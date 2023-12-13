from unittest import TestCase

from tseapy.core.parameters import RangeParameter, ListParameter


class TestAnalysisBackendParameter(TestCase):

    def test_range_parameter(self):
        p = RangeParameter(name='p', description='desc', minimum=0, maximum=10, step=1, onclick="", disabled=False)

        expected_html = '<label for="p" class="form-label">p</label>\n<input id="p" type="range" class="form-range" min="0" max="10" step="1" onclick="">'
        actual_html = p.get_view()
        self.assertEqual(expected_html, actual_html)

    def test_list_parameter(self):
        p = ListParameter(name='p', description='desc', values=['a', 'b', 'c'], onclick="", disabled=False)

        expected_html = f'<label for="p" class="form-label">p</label>' + \
                        f'\n<input class="form-control" list="list_p" name="p" id="p" onclick="">' + \
                        f'\n<datalist id="list_p">' + \
                        f'\n\t<option value="a">' + \
                        f'\n\t<option value="b">' + \
                        f'\n\t<option value="c">' + \
                        f'\n</datalist>'
        actual_html = p.get_view()
        self.maxDiff = None
        self.assertEqual(expected_html, actual_html)
