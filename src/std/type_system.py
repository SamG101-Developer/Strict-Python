import builtins
import functools
import inspect
import typing
import re

import typeguard

from std.exceptions import *
from std.types import *


def enable_type_checking():
    """
    Enable the type checking options by allowing the BaseObject to be used. By default, the BaseObject type aliases
    "object", to avoid the slowdown of type checking. This function can be called to enable the BaseObject type checking
    by mapping BaseObject to the "_BaseObject" type.
    @return:
    """
    assert TypeChecker.BaseObject is object, "Type checking is already enabled."
    TypeChecker.BaseObject = _BaseObject
    print("Type checking enabled.")


def _method_type_checker(method: Callable | MethodType) -> Callable:
    """
    Check at runtime, every invocation of this function has arguments of the correct type (match parameters), and the
    value returned is the correct type (matches return type).
    @param method: The method to check.
    @return: A wrapper function that checks the types of the arguments and return value.
    """

    @functools.wraps(method)
    def _impl(*fn_args, **fn_kwargs) -> Any:
        # Check the arguments' annotations.
        method_annotations = typing.get_type_hints(method)
        method_signature   = inspect.signature(method)

        # Re-arrange the arguments based on the method signature.
        bound_arguments = method_signature.bind(*fn_args, **fn_kwargs)
        bound_arguments.apply_defaults()
        ordered_arguments = [bound_arguments.arguments[p] for p in method_signature.parameters]

        # Pop the self argument for non-static methods.
        if dict(method_signature.parameters).get("self") is not None:
            ordered_arguments.pop(0)

        # Check the arguments' types.
        for arg, param_type in zip(ordered_arguments, method_annotations.values()):
            typeguard.check_type(arg, param_type)

        # Call the method and check the return type.
        result = method(*fn_args, **fn_kwargs)
        return_type = method_annotations["return"]
        typeguard.check_type(result, return_type)
        return result

    return _impl


def _is_special_identifier(identifier: str) -> bool:
    """
    Check if the identifier is a special identifier, such as "__init__" or "__str__".
    @param identifier: The identifier to check.
    @return: True if the identifier is a special identifier, False otherwise.
    """
    return identifier.startswith("__") and identifier.endswith("__")


def _should_ignore_parameter(name: str, parameter: inspect.Parameter) -> bool:
    """
    Check if the parameter should be ignored for type checking.
    @param name: The name of the parameter.
    @param parameter: The parameter object.
    @return: True if the parameter should be ignored, False otherwise.
    """
    var_parameter_types = {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
    return parameter.kind in var_parameter_types or name == "self"


class _BaseObjectMetaClass(type):
    """
    Compile time checks, such as annotation checking are done here. No class instantiation is needed for these tests to
    take place. There is no effect on runtime performance. Friend classes are inherited from superclasses.
    1. Check all parameters, except "self", "*..." and "**..." arguments have type annotations.
    2. Check "self", "*..." and "**..." arguments don't have type annotations (uniform coding).
    3. Check all methods have return type annotations.
    4. Check all attributes have type annotations.
    5. All overridden methods must be marked as "@abstract_method" or "@virtual_method".
    6. All overriding methods must be marked as "@override_method".
    7. All abstract methods must be implemented in derived classes.
    """

    def __new__(cls, name, bases, dictionary):

        # Methods to not wrap, to avoid recursion.
        ignore_method_names = {"__getattr__", "__setattr__", "__delattr__", "__getattribute__"}

        # Analyse each member of the class.
        for field_name, field_value in dictionary.items():

            if builtins.callable(field_value):

                # Check methods for virtual/abstract/override issues.
                for base_class in filter(lambda x: x is not _BaseObject, bases):
                    if field_name in base_class.__dict__:
                        if base_field_value := base_class.__dict__.get(field_name, None):

                            # Check if a method is overridden, it is virtual or abstract.
                            if not hasattr(base_field_value, "__is_virtual__") and not hasattr(base_field_value, "__is_abstract__") and not _is_special_identifier(field_name):
                                raise VirtualMethodException(f"Method '{base_class.__name__}.{field_name}' must be marked as '@virtual_method' or '@abstract_method'.")

                            # Check if a method is overriding, it is marked as override.
                            if not hasattr(field_value, "__is_override__") and not _is_special_identifier(field_name):
                                raise OverrideMethodException(f"Method '{name}.{field_name}' must be marked as '@override_method'.")

                # Check if an @override_method is overriding a method that doesn't exist.
                if hasattr(field_value, "__is_override__") and not any(field_name in base_class.__dict__ for base_class in bases):
                    raise OverrideMethodException(f"Method '{name}.{field_name}' is marked as '@override_method', but no method to override exists.")

                # Check the return type is annotated.
                method_annotations = field_value.__annotations__.copy()
                if method_annotations.pop("return", None) is None:
                    raise MissingReturnTypeAnnotationException(f"Method '{name}.{field_name}' has no return type annotation.")

                # Check all the parameters are annotated.
                method_parameters = dict(inspect.signature(field_value).parameters)
                method_parameters = {k: v for k, v in method_parameters.items() if not _should_ignore_parameter(k, v)}
                for p_name, p in method_parameters.items():
                    if p.annotation is inspect.Parameter.empty:
                        raise MissingParameterTypeAnnotationException(f"Parameter '{p_name}' in method '{field_name}' has no type annotation.")

                # Check no unnecessary annotations are present.
                for p_name, p in inspect.signature(field_value).parameters.items():
                    if _should_ignore_parameter(p_name, p) and p.annotation is not inspect.Parameter.empty:
                        raise UnnecessaryParameterTypeAnnotationException(f"Parameter '{p_name}' in method '{field_name}' should not have a type annotation.")

                # Wrap the function in the runtime checker.
                if field_name not in ignore_method_names:
                    dictionary[field_name] = _method_type_checker(field_value)

            # Property return type annotation check.
            elif isinstance(field_value, property):
                if not hasattr(field_value.fget, "__annotations__") or "return" not in field_value.fget.__annotations__:
                    raise MissingReturnTypeAnnotationException(f"Property '{name}.{field_name}' has no return type annotation.")

            # Cached property return type annotation check.
            elif isinstance(field_value, functools.cached_property):
                if not hasattr(field_value.func, "__annotations__") or "return" not in field_value.func.__annotations__:
                    raise MissingReturnTypeAnnotationException(f"Cached property '{name}.{field_name}' has no return type annotation.")

            # Attribute analysis code.
            else:
                if not _is_special_identifier(field_name) and field_name not in dictionary.get("__annotations__", {}):
                    raise MissingAttributeTypeAnnotationException(f"Attribute '{name}.{field_name}' has no type annotation.")

        # Check all the abstract methods are implemented.
        for base_class in filter(lambda x: x is not _BaseObject, bases):
            for b_field_name, b_field_value in base_class.__dict__.items():
                if builtins.callable(b_field_value) and hasattr(b_field_value, "__is_abstract__"):
                    if b_field_name not in dictionary:
                        raise AbstractMethodException(f"Abstract method '{base_class.__name__}.{b_field_name}' must be implemented in class {name}.")

        return super(_BaseObjectMetaClass, cls).__new__(cls, name, bases, dictionary)

    def __init__(cls, name, bases, dictionary):
        cls.__friends__ = cls.__friends__.union(*[base.__friends__ for base in bases if hasattr(base, "__friends__")])
        super(_BaseObjectMetaClass, cls).__init__(name, bases, dictionary)


class _BaseObject(metaclass=_BaseObjectMetaClass):
    """
    Runtime checks, such as type-checking function calls and attribute assignment. High impact on runtime performance,
    don't call "enable_type_checking" for release builds. Effectively a drop-in replacement for the "object" type.
    1. Check all function arguments have the correct types.
    2. Check the function return values have the correct type.
    3. Check all the attributes are assigned the correct type.
    4. Check access modifiers for getting attributes and functions.
    """

    __friends__: set[str] = {"inspect._getmembers"}
    __slots__ = {}

    def __setattr__(self, key: str, value: Any) -> type(None):
        """
        Check the type of the attribute being assigned.
        @param key: The attribute name.
        @param value: The value to assign to the attribute.
        @return: None (Doesnt work with "-> None").
        """

        name = self.__class__.__name__
        attribute_annotations = typing.get_type_hints(self.__class__)

        # Check the attribute has been type-defined.
        if key not in self.__annotations__:
            raise MissingAttributeTypeAnnotationException(f"Attribute '{name}.{key}' has no type annotation.")

        # Check the attribute isn't const/final (allow setting in __init__).
        if typing.get_origin(attribute_annotations[key]) is Const and inspect.stack()[1].function != "__init__":
            raise ConstModifierException(f"Attribute '{key}' is const and cannot be modified.")

        # Check the type of the attribute.
        typeguard.check_type(value, self.__annotations__[key])
        super().__setattr__(key, value)

    def __getattribute__(self, item: str) -> Any:
        """
        The main checks in the get attribute function are to manage the access modifiers. There are 4 cases to consider
        for accessing protected and private members:
        1. The calling context is an instance of this class or a subclass.
        2. The calling context belongs to a friend class: __friends__ = {"Type"}, Type().function().
        3. The calling context is a friend method: __friends__ = {"Type.function"}, Type.function().
        4. The calling context is a free function: __friends__ = {"function"}, function().
        @param item: The name of the attribute or method to access.
        @return: The attribute or method.
        """

        # Bypass magic method/attribute access and "inspect" code.
        caller_context = inspect.currentframe().f_back
        if _is_special_identifier(item) or caller_context.f_globals["__name__"] == "inspect":
            return super().__getattribute__(item)

        # Handle public member access.
        if not item.startswith("_"):
            return super().__getattribute__(item)

        # Handle protected and private member access.
        base_classes = super().__getattribute__("__class__").__mro__[:-1]
        this_class_identifier = f"_{self.__class__.__name__}__"
        private_identifier_regex = re.compile(r"^_[a-zA-Z0-9_]+[a-zA-Z0-9]__")

        # Handle possible friended free function.
        if "self" not in caller_context.f_locals:
            free_function_name = caller_context.f_code.co_name
            if free_function_name in super().__getattribute__("__friends__"):
                return super().__getattribute__(private_identifier_regex.sub(this_class_identifier, item))
                # return super().__getattribute__(item)

        # Handle class access (matching class means access to all members).
        if "self" in caller_context.f_locals:
            is_same_class = caller_context.f_locals["self"].__class__ is self.__class__
            if is_same_class:
                return super().__getattribute__(item)

        # Handle possible subclass access (protected only); note private looks like "_Type__member".
        if "self" in caller_context.f_locals:
            is_subclass = caller_context.f_locals["self"].__class__ in base_classes
            if is_subclass and not item.removeprefix(f"_{self.__class__.__name__}").startswith("__"):
                return super().__getattribute__(item)

        # Handle possible friend class access (calling function belongs to a friend class).
        if "self" in caller_context.f_locals:
            caller_context_class_name = caller_context.f_locals["self"].__class__.__name__
            if caller_context_class_name in super().__getattribute__("__friends__"):
                return super().__getattribute__(private_identifier_regex.sub(this_class_identifier, item))

        # Handle possible friend method access (calling function is a friend method).
        if "self" in caller_context.f_locals:
            caller_context_method_name = f"{caller_context.f_locals['self'].__class__.__name__}.{caller_context.f_code.co_name}"
            if caller_context_method_name in super().__getattribute__("__friends__"):
                return super().__getattribute__(private_identifier_regex.sub(this_class_identifier, item))

        raise AccessModifierException(f"Access to protected/private member '{self.__class__.__name__}.{item}' is not allowed.")


class TypeChecker:
    BaseObject: type[object | _BaseObject] = object


__all__ = [
    "enable_type_checking",
    "TypeChecker"
]
