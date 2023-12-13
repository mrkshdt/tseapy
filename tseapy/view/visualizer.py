import itertools
from tkinter import Button

from bokeh.layouts import column
from bokeh.models import ColumnDataSource, BoxAnnotation, BoxSelectTool, Circle, Slider, TextInput
from bokeh.palettes import Dark2_5 as palette
from bokeh.plotting import figure


class Visualizer:
    input_global = ColumnDataSource({'index': [1, 2, 3, 4, 5],
                                     'values': [1, 1, 1, 1, 1]})

    result = ColumnDataSource({'index': [1, 2, 3, 4, 5],
                               'values': [1, 1, 1, 1, 1]})

    t_source = ColumnDataSource({'index': [1, 2, 3, 4, 5],
                                 'values': [1, 1, 1, 1, 1]})

    r_tmp = 0

    def get_input_data(self, input):
        self.data = input

    def select_and_color(self, new, loader):
        try:
            tmp = []
            for i in new:
                tmp.append(loader.cds.loc[i])
            green_box = BoxAnnotation(left=new[0], right=new[-1], fill_color='green', name='annotator')
            self.global_plot.add_layout(green_box)

        except Exception as some:
            print('Failure:', some)

    def plot_similar(self, df_tmp):
        print("plot start")
        colors = itertools.cycle(palette)
        self.t_source.data = df_tmp
        print("allocation: ", df_tmp)

        for i in df_tmp.columns:
            self.t_plot.line(x='index', y=i, source=viz.t_source, color=next(colors), name="old")

    def result_coloring(self, idxs, snippet, entire):
        """
        Algorithm to color patterns and anomalies; Unclear which one should prevail?
        Needs review and further work
        """

        self.r_tmp = entire

        self.r_tmp['pattern'] = pd.DataFrame([np.nan for x in self.r_tmp.iterrows()])

        for idx in idxs:
            try:
                self.r_tmp['pattern'][idx:idx + snippet] = self.r_tmp['values'][idx:idx + snippet].values
            except:
                print("Overflow")
        self.result.data = self.r_tmp

    """
    Global Plot
    """
    global_plot = figure(plot_width=1200, plot_height=250, title='Initial Time Series', background_fill_color="#efefef",
                         tools="xpan,reset", sizing_mode='stretch_width')  # ,x_range=window_range)
    global_plot.add_tools(BoxSelectTool(dimensions="width"))
    g_line = global_plot.line(x='index', y='values', source=input_global)
    g_circle = global_plot.circle(x='index', y='values', source=input_global, alpha=0)
    g_circle.nonselection_glyph = Circle(line_color="grey", fill_color=None)

    """
    MP/MASS Plot
    """
    t_plot = figure(plot_height=250, title='Similar Subsequences', background_fill_color="#efefef", tools="",
                    toolbar_location=None, sizing_mode="stretch_width")
    tmp_t = {'index': [1, 2, 3, 4, 5],
             'values': [1, 1, 1, 1, 1]}
    t_source = ColumnDataSource(data=tmp_t)
    t_line = t_plot.line(x='index', y='values', source=t_source)

    """
    Result Plot
    """
    r_plot = figure(plot_height=250, title='Result', background_fill_color="#efefef", tools="", toolbar_location=None,
                    sizing_mode="stretch_width")
    tmp_r = {'index': [1, 2, 3, 4, 5],
             'values': [1, 1, 1, 1, 1]}
    r_source = ColumnDataSource(data=tmp_r)
    r_line = r_plot.line(x='index', y='values', source=result)
    r_pattern = r_plot.line(x='index', y='pattern', source=result, line_color="green")

    """
    User Input
    """
    pattern_val = Slider(start=0, end=200, value=20, step=1, title="Amount of similar ")
    export_button = Button(label="Export Model", button_type="success")
    label_text = TextInput(value="")
    export_row = column(label_text, export_button)
