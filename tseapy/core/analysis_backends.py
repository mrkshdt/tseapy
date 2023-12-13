import abc
from typing import List

from tseapy.core.parameters import AnalysisBackendParameter


class AnalysisBackend:
    """
    A class for defining AnalysisBackend interfaces
    """

    def __init__(self, name: str, short_description: str, long_description: str, callback_url: str,
                 parameters: List[AnalysisBackendParameter]):
        self.name = name
        self.short_description = short_description
        self.long_description = long_description
        self.callback_url = callback_url
        self.parameters = parameters

    @abc.abstractmethod
    def do_analysis(self, data, feature, **kwargs):
        pass



class AnalysisBackendsList:
    """
    """

    def __init__(self):
        self._backends = dict()

    def add_analysis_backend(self, analysis_backend: AnalysisBackend):
        self._backends[analysis_backend.name] = analysis_backend

    def get_analysis_backend(self, algo: str):
        if algo not in self._backends.keys():
            raise ValueError(f'Algorithm "{algo}" is unknown')
        else:
            return self._backends.get(algo)