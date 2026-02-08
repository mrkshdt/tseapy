import stumpy
from sklearn.preprocessing import minmax_scale
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
        series = data[feature].astype(np.float64)
        if len(series) < 4:
            raise ValueError("Dataset is too short for motif detection. Need at least 4 rows.")
        width = max(3, min(width, len(series) - 1))

        algo = stumpy.stump(series, width)

        mp = np.asarray([x[0] for x in algo], dtype=np.float64)
        finite_mask = np.isfinite(mp)
        if finite_mask.any():
            fill_value = np.max(mp[finite_mask])
            safe_mp = np.where(finite_mask, mp, fill_value)
            profile = minmax_scale(safe_mp, feature_range=(0, 1))
        else:
            profile = np.zeros_like(mp)

        motifs = [True if x <= penalty else False for x in profile]
        
        tmp = data.copy()
        motif_mask = np.zeros(len(tmp), dtype=bool)
        for j, is_motif in enumerate(motifs):
            if is_motif:
                end = min(j + width, len(tmp))
                motif_mask[j:end] = True

        values = tmp[feature].astype(np.float64)
        tmp["motif"] = np.where(motif_mask, values, np.nan)
        tmp["normal"] = np.where(motif_mask, np.nan, values)


        
        return True, profile, tmp 
