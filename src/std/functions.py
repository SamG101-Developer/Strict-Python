import typing


def virtual_method(f: typing.Callable) -> typing.Callable:
    f.__is_virtual__ = True
    return f


def abstract_method(f: typing.Callable) -> typing.Callable:
    f.__is_abstract__ = True
    return f


def override_method(f: typing.Callable) -> typing.Callable:
    f.__is_override__ = True
    return f


__all__ = [
    "virtual_method",
    "abstract_method",
    "override_method"
]
