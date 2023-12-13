import abc

from flask import Flask, render_template


class AnalysisBackendParameter:
    """
    A class for defining AnalysisBackend parameters
    """

    def __init__(self, name, label, description, onclick:str, disabled:bool):
        self.name = name
        self.label = label
        self.description = description
        self.onclick = onclick
        self.disabled = disabled


class NumberParameter(AnalysisBackendParameter):

    def __init__(self, name, label, description, minimum: float, maximum: float, step: float, default: float, onclick: str,
                 disabled: bool):
        super().__init__(name, label, description, onclick, disabled)
        assert isinstance(minimum, (int, float, complex)) and not isinstance(minimum, bool)
        assert isinstance(maximum, (int, float, complex)) and not isinstance(maximum, bool)
        assert isinstance(step, (int, float, complex)) and not isinstance(step, bool)
        assert isinstance(default, (int, float, complex)) and not isinstance(default, bool)
        assert minimum < default < maximum
        assert step < (maximum - minimum)
        self.min = minimum
        self.max = maximum
        self.step = step
        self.value = default


class RangeParameter(AnalysisBackendParameter):
    """
    A class for representing parameters having a range of numerical values

    The corresponding HTML component is a slider
    """

    def __init__(self, name, label, description, minimum, maximum, step, onclick, disabled):
        super().__init__(name, label, description, onclick, disabled)
        assert isinstance(minimum, (int, float, complex)) and not isinstance(minimum, bool)
        assert isinstance(maximum, (int, float, complex)) and not isinstance(maximum, bool)
        assert isinstance(step, (int, float, complex)) and not isinstance(step, bool)
        assert minimum < maximum
        self.min = minimum
        self.max = maximum
        self.step = step


class ListParameter(AnalysisBackendParameter):
    """
    A class for representing parameters having a list of non-numerical values

    The corresponding HTML component is a dropdown
    """

    def __init__(self, name, label, description, values, onclick, disabled):
        super().__init__(name, label, description, onclick, disabled)
        self.values = values


class BooleanParameter(AnalysisBackendParameter):
    """
    A class for representing parameters having a boolean value

    The corresponding HTML component is a checkbox
    """

    def __init__(self, name, label, description, default, onclick, disabled):
        super().__init__(name, label, description, onclick, disabled)
        assert type(default) is bool
        self.default = default
