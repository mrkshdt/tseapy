import stumpy
from sklearn.preprocessing import minmax_scale
import pandas as pd
import numpy as np

import plotly.express as px

from tseapy.core import create_callback_url
from tseapy.core.analysis_backends import AnalysisBackend
from tseapy.core.parameters import NumberParameter
from tseapy.tasks.motif_detection import MotifDetectionBackend


class Matrixprofile(MotifDetectionBackend):
    def __init__(self):
        short_description = ""
        long_description = """
        """
        super().__init__(
            'matrixprofile',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('motif-detection', 'matrixprofile'),
            parameters=[
                NumberParameter(
                    name='penalty',
                    label='penalty',
                    description='penalty value (>0)',
                    disabled=False,
                    onclick="",
                    minimum=0,
                    maximum=1,
                    step=0.01,
                    default=0.4
                ),
                NumberParameter(
                    name='width',
                    label='width',
                    description='The width of the sliding window',
                    disabled=False,
                    onclick="",
                    minimum=5,
                    maximum=1000,
                    step=2,
                    default=100
                )
            ])

    def do_analysis(self, data, feature, **kwargs):
        penalty = float(kwargs['penalty'])
        width = int(kwargs['width'])
        algo = stumpy.stump(data[feature],width)

        mp = [x[0] for x in algo]
        profile = minmax_scale(mp, feature_range=[0,1])

        motifs = [True if x <= penalty else False for x in profile]
        
        # Very unprecise solution
        tmp = data
        nan_list = [np.nan for x in data.iterrows()]
        nan_df = pd.DataFrame(nan_list)
        tmp['motif'] = nan_df
        tmp['normal'] = nan_df

        for j, i in enumerate(motifs):
            if i==True:
                try:
                    tmp['motif'].iloc[j:j+width]=data[feature].iloc[j:j+width]
                    tmp['normal'].iloc[j:j+width]=np.nan

                except:
                    tmp['motif'].iloc[j:]=data[feature].iloc[j:]
                    tmp['normal'].iloc[j:]=np.nan
            else:
                try:
                    tmp['motif'].iloc[j:j+width]=np.nan
                    tmp['normal'].iloc[j:j+width]=data[feature].iloc[j:j+width]

                except:
                    tmp['motif'].iloc[j:j+width]=np.nan
                    tmp['normal'].iloc[j:j+width]=data[feature].iloc[j:]


        
        return True, profile, tmp 
