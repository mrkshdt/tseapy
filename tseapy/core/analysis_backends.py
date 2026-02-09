import abc
from typing import List

from tseapy.core.parameters import AnalysisBackendParameter
from tseapy.core import create_callback_url


class AnalysisBackend(abc.ABC):
    """Base class for analysis backends."""

    def __init__(self, name: str, short_description: str, long_description: str,
                 callback_url: str, parameters: List[AnalysisBackendParameter], required_query_params=None):
        self.name = name
        self.short_description = short_description
        self.long_description = long_description
        self.callback_url = callback_url
        self.parameters = parameters
        self.required_query_params = list(required_query_params or [])

    @abc.abstractmethod
    def do_analysis(self, data, feature, **kwargs):
        """Perform the analysis on ``data`` for ``feature``."""
        pass

    @staticmethod
    def create_callback_url(task: str, algo: str, *args) -> str:
        """Return a callback URL for the given task and algorithm."""
        return create_callback_url(task, algo, *args)


class AnalysisBackendsList:
    """Container for registered backends."""

    def __init__(self):
        self._backends = {}

    def add_analysis_backend(self, analysis_backend: AnalysisBackend):
        self._backends[analysis_backend.name] = analysis_backend

    def get_analysis_backend(self, algo: str):
        if algo not in self._backends:
            raise ValueError(f'Algorithm "{algo}" is unknown')
        return self._backends.get(algo)

    def iter_backends(self):
        return self._backends.values()
