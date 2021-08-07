import warnings


class EasyPySpinWarning(Warning):
    pass


def warn(
    message: str, category: Warning = EasyPySpinWarning, stacklevel: int = 2
) -> None:
    """Default EasyPySpin warn"""
    warnings.warn(message, category, stacklevel + 1)
