import typeguard


class StandardException(BaseException):
    def __init__(self, message: str, filename: str = "", lineno: int = -1):
        super().__init__(message)
        self.filename = filename
        self.lineno = lineno


class MissingTypeAnnotationException(StandardException):
    """
    This exception is raised for attributes and methods. For attributes, it is raised when an attribute is missing a
    type annotation. Every attribute must have a type annotation for type checking inside the __setattr__ method. For
    methods, this exception can be raised for 2 instances: either a parameter or return type is missing an annotation,
    or an annotation is provided to a parameter that should not have one (self, *args, **kwargs).
    """


class MissingParameterTypeAnnotationException(MissingTypeAnnotationException):
    """
    This exception is raised when a parameter is missing a type annotation in a method.
    """


class MissingReturnTypeAnnotationException(MissingTypeAnnotationException):
    """
    This exception is raised when a return type is missing a type annotation in a method.
    """


class MissingAttributeTypeAnnotationException(MissingTypeAnnotationException):
    """
    This exception is raised when an attribute is missing a type annotation.
    """


class UnnecessaryParameterTypeAnnotationException(BaseException):
    """
    This exception is raised when a parameter has a type annotation that should not have one (self, *args, **kwargs).
    """


class ConstModifierException(BaseException):
    """
    This exception is raised when a constant attribute is modified. Const attributes can only be set in their
    definition, or in the __init__ method.
    """


class VirtualMethodException(Exception):
    """
    This exception is thrown when an overridden method is not marked as virtual or abstract, or a non-virtual method is
    marked as override.
    """


class OverrideMethodException(Exception):
    """
    This exception is thrown either when an overriding method is not marked as override, or when an override method is
    overriding a method that doesn't exist.
    """


class AbstractMethodException(Exception):
    """
    This exception is thrown when an abstract method is not implemented in a subclass. Abstract methods must be
    implemented in all subclasses.
    """


class AccessModifierException(Exception):
    """
    This exception is raised when a non-friendly method or class tries to access a protected / private attribute or
    method.
    """


TypeMismatchException = typeguard.TypeCheckError

__all__ = [
    "MissingParameterTypeAnnotationException",
    "MissingReturnTypeAnnotationException",
    "MissingAttributeTypeAnnotationException",
    "UnnecessaryParameterTypeAnnotationException",
    "TypeMismatchException",
    "ConstModifierException",
    "VirtualMethodException",
    "OverrideMethodException",
    "AbstractMethodException",
    "AccessModifierException",
]
