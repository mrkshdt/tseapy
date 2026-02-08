import stumpy
import numpy as np

from tseapy.core import create_callback_url
from tseapy.core.parameters import NumberParameter, BooleanParameter
from tseapy.tasks.pattern_recognition import PatternRecognitionBackend


class Mass(PatternRecognitionBackend):

    def __init__(self):
        short_description = "Computes the distance profile using the stumpy implementation of the MASS algorithm."
        long_description = """
        Computes the distance profile using the stumpy implementation of the MASS algorithm.  
        
        References:
        - https://stumpy.readthedocs.io/en/latest/api.html#stumpy.mass
        - Time series joins, motifs, discords and shapelets: a unifying view that exploits the matrix profile. Yeh, C. M., Zhu, Y., Ulanova, L., Begum, N., Ding, Y., Dau, H. A., Zimmerman, Z., Silva, D. F., Mueen, A., & Keogh, E. Data Mining and Knowledge Discovery, Springer, 2017. 
        """
        super().__init__(
            name='mass',
            short_description=short_description,
            long_description=long_description,
            callback_url=create_callback_url('pattern-recognition', 'mass', *['start', 'end']),
            parameters=[
                BooleanParameter(
                    name='normalize',
                    label='normalize',
                    description='Stumpy Mass normalize parameter (see https://stumpy.readthedocs.io/en/latest/api.html#stumpy.mass)',
                    default=True,
                    onclick="document.getElementById('p').disabled=this.checked;",
                    disabled=False
                ),
                NumberParameter(
                    name='p',
                    label='p',
                    description='p (float, default 2.0) – The p-norm to apply for computing the Minkowski distance. This parameter is ignored when normalize == True. /see https://stumpy.readthedocs.io/en/latest/api.html#stumpy.mass)',
                    minimum=0.01,
                    maximum=10,
                    step=0.01,
                    default=2.,
                    onclick="",
                    disabled=True,
                )
            ])

    def do_analysis(self, data, feature, pattern=None, nb_similar_patterns=5, **kwargs):
        normalize = kwargs['normalize']
        assert normalize in ['true', 'false']
        normalize = normalize.lower() == 'true'
        p = float(kwargs['p'])
        if pattern is None or len(pattern) == 0:
            raise ValueError("Selected range is empty. Please select a valid interval on the chart.")

        data_series = data[feature].astype(np.float64)
        pattern_series = pattern.astype(np.float64)

        # compute distance profile
        distance_profile = stumpy.mass(pattern_series, data_series, normalize=normalize, p=p)
        # get the indices (sorted) of the similar patterns
        idxs = np.argpartition(distance_profile, nb_similar_patterns+1)[:nb_similar_patterns+1]
        idxs = idxs[np.argsort(distance_profile[idxs])]
        # return similar patterns
        similar_patterns = [
            data.iloc[idx:idx + len(pattern), :][feature]
            for idx in idxs[1:]
        ]

        return similar_patterns
