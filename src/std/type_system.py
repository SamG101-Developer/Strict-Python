import builtins
import functools
import inspect
import typing
import types
import typeguard


class AnnotationException(Exception):
    """
    This exception is raised when an attribute is missing a type annotation on a class. Every attribute must have an
    annotation for type-checking.
    """
    pass


class TypeMismatchException(Exception):
    """
    This exception is raised when a parameter, return value or attribute has a type mismatch with the expected type.
    """
    pass


class AccessModifierException(Exception):
    """
    This exception is raised when a non-friendly method or class tries to access a protected / private attribute or
    method.
    """
    pass


class ConstModifierException(Exception):
    """
    This exception is raised when a const attribute is modified.
    """
    pass


def ForceStaticTyping(function: typing.Callable | types.MethodType):
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
            raise AnnotationException(
                f"Missing type annotation for parameter {function_args[head:][len(parameter_annotations)]}")
        for argument, expected_argument_type in zip(function_args[head:], parameter_annotations):
            try:
                typeguard.check_type(argument, expected_argument_type)
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


# Base object meta class that handles the friends being inherited (C++ doesn't allow this)
class BaseObjectMetaClass(type):
    """
    The BaseObjectMetaClass is a metaclass that is used to allow the inheritance of special properties. Specifically, it
    allows for friends to be inherited into subclasses, acting like the __slots__ attribute does. This metaclass also
    enforces that all methods are static typed, by wrapping them in a decorator that checks the types of the arguments
    and return value, and raises a TypeMismatchException if they are wrong.
    """

    def __new__(cls, name, bases, dictionary):
        """
        Create a new class with the given name, bases and dictionary. This method is overridden to ensure that all
        methods are wrapped in a decorator that enforces static typing. There is a small blacklist of methods that are
        exempt from this, as they are special methods that are not called directly by the user.
        :param name: The name of the class.
        :param bases: The base classes of the class.
        :param dictionary: A dictionary of the class attributes.
        """

        blacklist = ["__getattr__", "__setattr__", "__getattribute__"]

        for attr_name, attr_value in dictionary.items():
            if builtins.callable(attr_value) and attr_name not in blacklist:
                dictionary[attr_name] = ForceStaticTyping(attr_value)
        return super().__new__(cls, name, bases, dictionary)

    def __init__(cls, name, bases, dictionary):
        """
        Inherit the friends from the superclass into the subclass. The "__friends__" attribute of the superclasses are
        all union-ed into the current class's __friends__.
        :param name: The name of the class.
        :param bases: The base classes of the class.
        :param dictionary: A dictionary of the class attributes.
        """

        cls.__friends__ = set(cls.__friends__).union(cls.__mro__[-2].__friends__)
        super(BaseObjectMetaClass, cls).__init__(name, bases, dictionary)


class BaseObject(metaclass=BaseObjectMetaClass):
    """
    The BaseObject class is a drop-in substitute for the "object" type. It must be explicitly inherited into all classes
    however, to enforce its properties such as type-checking.
    """

    __friends__ = frozenset({"inspect._getmembers"})
    __slots__ = frozenset({})

    def __setattr__(self, key, value) -> typing.NoReturn:
        """
        The attribute setter method is overridden to perform type checking. It enforces that all attributes have a type
        annotation, and that the type of the value being set matches the expected type. It also prevents const
        attributes from being set in non-constructor methods.
        :param key: The name of the attribute being set.
        :param value: The value being set.
        :return: None.
        """

        type_hints = typing.get_type_hints(self.__class__)

        try:
            # The assertion checks for the existence of the attribute in the type hints of the class. If the attribute
            # is not in the type hints, it means that the attribute was not declared in the class, or was declared but
            # without a type annotation.
            assert key in typing.get_type_hints(self.__class__)

            # Check if the type hint is a Final type, the attribute is being set in the constructor. This prevents const#
            # attributes from being set in methods.
            if typing.get_origin(type_hints[key]) == typing.Final and not inspect.stack()[1].function == "__init__":
                raise ConstModifierException(f"Attribute {self.__class__.__name__}.{key} is final and cannot be changed")

            # Run the type checker to ensure that the value being set matches the expected type.
            typeguard.check_type(value, type_hints[key])

        except typeguard.TypeCheckError:
            # Handle an incorrect type error by raising a TypeMismatchException.
            raise TypeMismatchException(f"Attribute{self.__class__.__name__}.{key} expected type {type_hints[key]} but got {type(value)}")

        except AssertionError:
            # Handle a missing type annotation by raising an AnnotationException.
            raise AnnotationException(f"Attribute {self.__class__.__name__}.{key} does not exist or hasn't been type-defined")

        # If all checks pass, set the attribute as usual.
        object.__setattr__(self, key, value)

    def __getattribute__(self, item):
        """
        The attribute getter is overridden to check for access modifier violations. If a type is not the class, subclass
        or friend, an AccessModifierException is raised. There are 4 cases to check:
        1. The calling context is a friend function (global scope function).
        2. The calling context is an instance of this class or subclass.
        3. The calling context is a method of a friend class.
        4. The calling context is a friend method.
        :param item: The name of the attribute being accessed.
        :return: The value of the attribute.
        """

        # Bypass any checks that are for accessing magic methods or "inspect" code. Magic methods and private attributes
        # both start with "__", so the bypass is needed here.
        current_frame = inspect.currentframe().f_back
        if item.startswith("__") and item.endswith("__") or current_frame.f_globals["__name__"] == "inspect":
            return object.__getattribute__(self, item)

        # Protected and private attribute access is handed here.
        if item[0] == "_":

            # Get the base classes of this class. "This class" refers to the owner of the attribute being accessed,
            # ie "self".
            bases = object.__getattribute__(self, "__class__").__mro__[:-1]

            # Check if the calling context is a global function, and a friend function. If it is, then allow access to
            # the attribute.
            function_name = current_frame.f_code.co_name
            if function_name in object.__getattribute__(self, "__friends__") and "self" not in current_frame.f_locals:
                return object.__getattribute__(self, item)

            # If the "self" argument exists in the local variables of the calling context, assume it is a method of a
            # class.
            if "self" in current_frame.f_locals:

                # If the caller context is a method that belongs to this class or a subclass, attempt to get the
                # variable from this class. In the case that a subclass is attempting to access a private class
                # attribute, the check fails.
                is_sub_class = object.__getattribute__(current_frame.f_locals["self"], "__class__") in bases
                if is_sub_class and not item.removeprefix(f"_{self.__class__.__name__}").startswith("__"):
                    return object.__getattribute__(self, item)

                # Check if the calling context is a method belongs to a friend class. Get the attribute if this is the
                # case.
                class_name = object.__getattribute__(current_frame.f_locals["self"], "__class__").__name__
                if class_name in object.__getattribute__(self, "__friends__"):
                    return object.__getattribute__(self, item.replace(f"_{class_name}", f"_{self.__class__.__name__}"))

                # Check if the calling context is friend method. This means the calling context's class isn't friended,
                # but the specific method is.
                method_name = ".".join([class_name, function_name])
                if method_name in object.__getattribute__(self, "__friends__"):
                    return object.__getattribute__(self, item)

            # # Check all the same but for module specific functions ie for each scoped friend, remove check if the
            # # first part (before first dot) is the module of the caller, and if so, remove the module part of the
            # # name and call this method with the remaining part of the name
            # for friend in object.__getattribute__(self, "__friends__"):
            #     module = friend.split(".")[0]
            #     friend = ".".join(friend.split(".")[1:])
            #
            #     class_name = ""
            #     method_name = ""
            #     if "self" in current_frame.f_locals:
            #         class_name = object.__getattribute__(current_frame.f_locals["self"], "__class__").__name__
            #         method_name = ".".join([class_name, function_name])
            #
            #     if builtins.any([friend == x for x in [function_name, class_name, method_name]]):
            #         if module == current_frame.f_globals["__name__"]:
            #             return object.__getattribute__(self, item)

        else:
            # Return public attributes as usual
            return object.__getattribute__(self, item)

        # If the attribute hasn't been returned, then an enemy class is trying to access a member of this class
        raise AccessModifierException(
            f"Non-Friendly callers cannot access protected member {self.__class__.__name__}.{item}")


__all__ = [
    "AnnotationException",
    "TypeMismatchException",
    "AccessModifierException",
    "ConstModifierException",
    "BaseObject"
]
