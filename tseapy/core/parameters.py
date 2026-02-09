import abc


def _is_number(value) -> bool:
    return isinstance(value, (int, float, complex)) and not isinstance(value, bool)


class AnalysisBackendParameter:
    """
    A class for defining AnalysisBackend parameters
    """

    def __init__(self, name, label=None, description='', onclick: str = '', disabled: bool = False):
        self.name = name
        self.label = label if label is not None else name
        self.description = description
        self.onclick = onclick
        self.disabled = disabled

    def _disabled_attr(self) -> str:
        return ' disabled' if self.disabled else ''


class NumberParameter(AnalysisBackendParameter):

    def __init__(self, name, label=None, description='', minimum: float = 0.0, maximum: float = 1.0, step: float = 1.0,
                 default: float = 0.0, onclick: str = '', disabled: bool = False):
        super().__init__(name, label, description, onclick, disabled)
        if not _is_number(minimum):
            raise TypeError("minimum must be a number")
        if not _is_number(maximum):
            raise TypeError("maximum must be a number")
        if not _is_number(step):
            raise TypeError("step must be a number")
        if not _is_number(default):
            raise TypeError("default must be a number")
        if not minimum < default < maximum:
            raise ValueError("default must be strictly between minimum and maximum")
        if not step < (maximum - minimum):
            raise ValueError("step must be less than the parameter range")
        self.min = minimum
        self.max = maximum
        self.step = step
        self.value = default

    def get_view(self) -> str:
        return (
            f'<label for="{self.name}" class="form-label">{self.label}</label>'
            f'\n<input type="number" id="{self.name}" class="form-control" '
            f'min="{self.min}" max="{self.max}" value="{self.value}", '
            f'step="{self.step}" onclick="{self.onclick}"{self._disabled_attr()}>'
        )


class RangeParameter(AnalysisBackendParameter):
    """
    A class for representing parameters having a range of numerical values

    The corresponding HTML component is a slider
    """

    def __init__(self, name, label=None, description='', minimum=0, maximum=1, step=1, onclick='', disabled=False):
        super().__init__(name, label, description, onclick, disabled)
        if not _is_number(minimum):
            raise TypeError("minimum must be a number")
        if not _is_number(maximum):
            raise TypeError("maximum must be a number")
        if not _is_number(step):
            raise TypeError("step must be a number")
        if not minimum < maximum:
            raise ValueError("minimum must be less than maximum")
        self.min = minimum
        self.max = maximum
        self.step = step

    def get_view(self) -> str:
        return (
            f'<label for="{self.name}" class="form-label">{self.label}</label>'
            f'\n<input id="{self.name}" type="range" class="form-range" '
            f'min="{self.min}" max="{self.max}" step="{self.step}" '
            f'onclick="{self.onclick}"{self._disabled_attr()}>'
        )


class ListParameter(AnalysisBackendParameter):
    """
    A class for representing parameters having a list of non-numerical values

    The corresponding HTML component is a dropdown
    """

    def __init__(self, name, label=None, description='', values=None, onclick='', disabled=False):
        if values is None:
            values = []
        super().__init__(name, label, description, onclick, disabled)
        self.values = values

    def get_view(self) -> str:
        options = ''.join(f'\n\t<option value="{v}">' for v in self.values)
        return (
            f'<label for="{self.name}" class="form-label">{self.label}</label>'
            f'\n<input class="form-control" list="list_{self.name}" name="{self.name}" id="{self.name}" '
            f'onclick="{self.onclick}"{self._disabled_attr()}>'
            f'\n<datalist id="list_{self.name}">' +
            options +
            '\n</datalist>'
        )


class BooleanParameter(AnalysisBackendParameter):
    """
    A class for representing parameters having a boolean value

    The corresponding HTML component is a checkbox
    """

    def __init__(self, name, label=None, description='', default=False, onclick='', disabled=False):
        super().__init__(name, label, description, onclick, disabled)
        if not isinstance(default, bool):
            raise TypeError("default must be a bool")
        self.default = default

    def get_view(self) -> str:
        checked = ' checked' if self.default else ''
        return (
            f'<label for="{self.name}" class="form-label">{self.label}</label>'
            f'\n<input type="checkbox" id="{self.name}" class="form-check-input" '
            f'value="" name="{self.name}" onclick="{self.onclick}"'
            f'{checked}{self._disabled_attr()}>'
        )
