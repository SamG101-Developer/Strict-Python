from __future__ import annotations

import builtins
import typing
import types
import typeguard
import functools
import inspect


def force_static_typing(function: typing.Callable | types.MethodType):
    @functools.wraps(function)
    def _impl(*function_args, **function_kwargs):
        # Get the annotations from the function. Separate the return annotation from the parameter annotations. Only the
        # values are kept, as the keys are the parameter names, and matching is done by indexing.
        function_annotations = typing.get_type_hints(function).copy()
        if "return" in function_annotations.keys():
            return_annotation = function_annotations.pop("return") or typing.NoReturn
        else:
            raise AnnotationException(f"Missing return type annotation for function {function.__name__}")
        parameter_annotations = function_annotations.values()

        methods = inspect.getmembers(function_args[0], inspect.ismethod)
        head = builtins.any([function.__name__ == method[0] for method in methods])

        # The parameter annotations are checked against the arguments passed to the function. If the type is wrong, a
        # TypeError is raised.
        # Check every parameter (except self) has a type annotation
        if len(parameter_annotations) < len(function_args[head:]):
            raise AnnotationException(f"Missing type annotation for parameter {function_args[head:][len(parameter_annotations)]}")
        for argument, expected_argument_type in zip(function_args[head:], parameter_annotations):
            try: typeguard.check_type(argument, expected_argument_type)
            except typeguard.TypeCheckError:
                raise TypeMismatchException(f"Expected {expected_argument_type} but got {type(argument)}")

        # The return annotation is checked against the return value of the function. If the type is wrong, a TypeError
        # is raised.
        if return_annotation:
            return_value = function(*function_args, **function_kwargs)
            try:
                # NoReturn check
                if return_annotation == typing.NoReturn and return_value is not None:
                    raise TypeMismatchException(f"Expected no return value but got {type(return_value)}")
                elif return_annotation != typing.NoReturn:
                    typeguard.check_type(return_value, return_annotation)
            except typeguard.TypeCheckError:
                raise TypeMismatchException(f"Expected {return_annotation} but got {type(return_value)}")
            return return_value
    return _impl


class AnnotationException(Exception):
    # This exception is raised when a method or class is missing a type annotation
    pass


class AccessModifierException(Exception):
    # This exception is raised when a non friendly method or class tries to access a protected / private attribute or
    # method of a class that inherits the DOMBaseClass
    pass


class TypeMismatchException(Exception):
    # This exception is thrown when a type mismatch is detected in the type checking of a parameter, return value or
    # attribute
    pass


class ConstModifierException(Exception):
    # This exception is thrown when a const attribute is modified
    pass


# Base object meta class that handles the friends being inherited (C++ doesn't allow this)
class base_object_metaclass(type):
    def __new__(cls, name, bases, dictionary):
        # Make sure all methods are static typed - this is done by wrapping the method in a decorator that checks the
        # types of the arguments and return value, and raises a TypeError if they are wrong.
        blacklist = ["__getattr__", "__setattr__", "__getattribute__"]

        for attr_name, attr_value in dictionary.items():
            if builtins.callable(attr_value) and attr_name not in blacklist:
                dictionary[attr_name] = force_static_typing(attr_value)
        return super().__new__(cls, name, bases, dictionary)

    def __init__(cls, name, bases, dictionary):
        # The meta class is implemented so that friends are inherited into subclasses (in the __friends__ attribute),
        # acting like the __slots__ attribute does (although the value of the attribute behaves differently: __slots__
        # registers superclass __slots__ but doesn't output them in the set; __friends__ shows all class and superclass
        # friends)
        cls.__friends__ = cls.__friends__.union(cls.__mro__[-2].__friends__)
        super(base_object_metaclass, cls).__init__(name, bases, dictionary)


# Base object class for every object that will be used in Python for anything (ie a replacement for object)
class base_object(metaclass=base_object_metaclass):
    __friends__ = frozenset({"inspect._getmembers"})
    __slots__   = frozenset({})

    def __init__(self) -> None:
        object.__init__(self)

    def __setattr__(self, key, value) -> typing.NoReturn:
        # Enforce type checking for the attributes of this class, and make sure the attribute was declared in the class
        # (ie not a dynamic attribute) => enforces a type is available
        type_hints = typing.get_type_hints(self.__class__)

        try:
            assert key in typing.get_type_hints(self.__class__)
            # cant modify a Final[T], unless from a constructor
            if typing.get_origin(type_hints[key]) == typing.Final and not inspect.stack()[1].function == "__init__":
                raise ConstModifierException(f"Attribute {self.__class__.__name__}.{key} is final and cannot be changed")
            typeguard.check_type(value, type_hints[key])
        except typeguard.TypeCheckError:
            raise TypeMismatchException(f"Attribute{self.__class__.__name__}.{key} expected type {type_hints[key]} but got {type(value)}")
        except AssertionError:
            raise AnnotationException(f"Attribute {self.__class__.__name__}.{key} does not exist or hasn't been type-defined")
        object.__setattr__(self, key, value)

    def __getattribute__(self, item):
        # Handle the access to underscore prefixed attributes, to ensure that only friend classes and functions can
        # access them. The 4 cases to check are:
        #   1. The calling function is a friend function (global scope function)
        #   2. The caller is an instance of this class or subclass
        #   3. The calling method belongs to a friend class
        #   4. The calling method is a friend method (method of a friend class)

        # Magic methods are accessible
        if item.startswith("__") and item.endswith("__"):
            return object.__getattribute__(self, item)

        # Protected attribute access
        if item[0] == "_":
            # Get the current caller frame and the base classes of this class
            current_frame = inspect.currentframe().f_back
            bases = object.__getattribute__(self, "__class__").__mro__[:-1]

            # Check if the calling global function is a friend function
            function_name = current_frame.f_code.co_name
            if function_name in object.__getattribute__(self, "__friends__") and "self" not in current_frame.f_locals:
                return object.__getattribute__(self, item)

            if "self" in current_frame.f_locals:
                # Check if the caller is an instance of this class or subclass
                is_sub_class = object.__getattribute__(current_frame.f_locals["self"], "__class__") in bases
                if is_sub_class:
                    return object.__getattribute__(self, item)

                # Check if the calling method belongs to a friend class
                class_name = object.__getattribute__(current_frame.f_locals["self"], "__class__").__name__
                if class_name in object.__getattribute__(self, "__friends__"):
                    return object.__getattribute__(self, item)

                # Check if the calling method is a friend function
                method_name = ".".join([class_name, function_name])
                if method_name in object.__getattribute__(self, "__friends__"):
                    return object.__getattribute__(self, item)

            # Check all the same but for module specific functions ie for each scoped friend, remove check if the
            # first part (before first dot) is the module of the caller, and if so, remove the module part of the
            # name and call this method with the remaining part of the name
            for friend in object.__getattribute__(self, "__friends__"):
                module = friend.split(".")[0]
                friend = ".".join(friend.split(".")[1:])

                class_name = ""
                method_name = ""
                if "self" in current_frame.f_locals:
                    class_name = object.__getattribute__(current_frame.f_locals["self"], "__class__").__name__
                    method_name = ".".join([class_name, function_name])

                if builtins.any([friend == x for x in [function_name, class_name, method_name]]):
                    if module == current_frame.f_globals["__name__"]:
                        return object.__getattribute__(self, item)

        else:
            # Return public attributes as usual
            return object.__getattribute__(self, item)

        # If the attribute hasn't been returned, then an enemy class is trying to access a member of this class
        raise AccessModifierException(f"Non-Friendly callers cannot access protected member {self.__class__.__name__}.{item}")


def is_function_empty(f: typing.Callable) -> bool:
    def function_that_passes() -> std.no_return:
        pass

    def function_empty() -> std.no_return:
        ...

    def function_only_docstring() -> std.no_return:
        """ This is a docstring """

    def function_return() -> std.no_return:
        return None

    lambda_empty = lambda: None
    lambda_only_docstring = lambda: None
    lambda_only_docstring.__doc__ = "This is a docstring"

    def constants(g: typing.Callable):
        return tuple(x for x in g.__code__.co_consts if x != f.__doc__)

    return any([
        f.__code__.co_code == function_that_passes.__code__.co_code and constants(f) == constants(function_that_passes),
        f.__code__.co_code == function_empty.__code__.co_code and constants(f) == constants(function_empty),
        f.__code__.co_code == function_only_docstring.__code__.co_code and constants(f) == constants(function_only_docstring),
        f.__code__.co_code == function_return.__code__.co_code and constants(f) == constants(function_return),
        f.__code__.co_code == lambda_empty.__code__.co_code and constants(f) == constants(lambda_empty),
        f.__code__.co_code == lambda_only_docstring.__code__.co_code and constants(f) == constants(lambda_only_docstring),
    ])
