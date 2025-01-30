from __future__ import annotations
import unittest
import std


class TestStrictPython(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        std.enable_type_checking()

    def test_missing_parameter_annotation(self) -> None:
        with self.assertRaises(std.MissingParameterTypeAnnotationException):
            class Test(std.TypeChecker.BaseObject):
                def method(self, param) -> None:
                    pass

    def test_missing_parameter_annotation_static_method(self) -> None:
        with self.assertRaises(std.MissingParameterTypeAnnotationException):
            class Test(std.TypeChecker.BaseObject):
                @staticmethod
                def method(param) -> None:
                    pass

    def test_missing_parameter_annotation_class_method(self) -> None:
        with self.assertRaises(std.MissingParameterTypeAnnotationException):
            class Test(std.TypeChecker.BaseObject):
                @classmethod
                def method(cls) -> None:
                    pass

    def test_missing_parameter_annotation_with_star_args(self) -> None:
        with self.assertRaises(std.MissingParameterTypeAnnotationException):
            class Test(std.TypeChecker.BaseObject):
                def method(self, param, *args) -> None:
                    pass

    def test_missing_parameter_annotation_with_star_kwargs(self) -> None:
        with self.assertRaises(std.MissingParameterTypeAnnotationException):
            class Test(std.TypeChecker.BaseObject):
                def method(self, param, **kwargs) -> None:
                    pass

    def test_missing_return_annotation(self) -> None:
        with self.assertRaises(std.MissingReturnTypeAnnotationException):
            class Test(std.TypeChecker.BaseObject):
                def method(self):
                    pass

    def test_missing_property_return_annotation(self) -> None:
        with self.assertRaises(std.MissingReturnTypeAnnotationException):
            class Test(std.TypeChecker.BaseObject):
                @property
                def prop(self):
                    pass

    def test_non_required_self_parameter_annotation(self) -> None:
        with self.assertRaises(std.UnnecessaryParameterTypeAnnotationException):
            class Test(std.TypeChecker.BaseObject):
                def method(self: Test) -> None:
                    pass

    def test_non_required_star_args_parameter_annotation(self) -> None:
        with self.assertRaises(std.UnnecessaryParameterTypeAnnotationException):
            class Test(std.TypeChecker.BaseObject):
                def method(self, *args: tuple) -> None:
                    pass

    def test_non_required_star_kwargs_parameter_annotation(self) -> None:
        with self.assertRaises(std.UnnecessaryParameterTypeAnnotationException):
            class Test(std.TypeChecker.BaseObject):
                def method(self, **kwargs: dict) -> None:
                    pass

    def test_missing_attribute_annotation(self) -> None:
        with self.assertRaises(std.MissingAttributeTypeAnnotationException):
            class Test(std.TypeChecker.BaseObject):
                attr = None

    def test_parameter_annotations(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            def method(self, param: int) -> None:
                pass

    def test_parameter_annotations_static_method(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            @staticmethod
            def method(param: int) -> None:
                pass

    def test_parameter_annotations_class_method(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            @classmethod
            def method(cls, param: int) -> None:
                pass

    def test_parameter_annotations_with_star_args(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            def method(self, param: int, *args) -> None:
                pass

    def test_parameter_annotations_with_star_kwargs(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            def method(self, param: int, **kwargs) -> None:
                pass

    def test_parameter_annotations_passing_star_args(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            def method(self, *args) -> None:
                pass

        t = Test()
        t.method(0, 1, 2)

    def test_parameter_annotations_passing_star_kwargs(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            def method(self, **kwargs) -> None:
                pass

        t = Test()
        t.method(key1=0, key2=1, key3=2)

    def test_return_annotation(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            def method(self) -> int:
                pass

    def test_property_return_annotation(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            @property
            def prop(self) -> int:
                return 1

    def test_attribute_annotations(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            attr: int = None

    def test_param_type_mismatch(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            def method(self, param: int) -> None:
                pass

        with self.assertRaises(std.TypeMismatchException):
            t = Test()
            t.method("string")

    def test_param_type_mismatch_static_method(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            @staticmethod
            def method(param: int) -> None:
                pass

        with self.assertRaises(std.TypeMismatchException):
            Test.method("string")

    def test_param_type_mismatch_class_method(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            @classmethod
            def method(cls, param: int) -> None:
                pass

        with self.assertRaises(std.TypeMismatchException):
            Test.method("string")

    def test_param_type_mismatch_with_star_args(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            def method(self, param: int, *args) -> None:
                pass

        with self.assertRaises(std.TypeMismatchException):
            t = Test()
            t.method("0", "string")

    def test_param_type_mismatch_with_star_kwargs(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            def method(self, param: int, **kwargs) -> None:
                pass

        with self.assertRaises(std.TypeMismatchException):
            t = Test()
            t.method("0", key="string")

    def test_return_type_mismatch(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            def method(self) -> int:
                return "string"

        with self.assertRaises(std.TypeMismatchException):
            t = Test()
            t.method()

    def test_return_type_mismatch_static_method(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            @staticmethod
            def method() -> int:
                return "string"

        with self.assertRaises(std.TypeMismatchException):
            Test.method()

    def test_return_type_mismatch_class_method(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            @classmethod
            def method(cls) -> int:
                return "string"

        with self.assertRaises(std.TypeMismatchException):
            Test.method()

    def test_param_type_match(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            def method(self, param: int) -> None:
                pass

        t = Test()
        t.method(0)

    def test_param_type_match_static_method(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            @staticmethod
            def method(param: int) -> None:
                pass

        Test.method(0)

    def test_param_type_match_class_method(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            @classmethod
            def method(cls, param: int) -> None:
                pass

        Test.method(0)

    def test_missing_virtual_annotation(self) -> None:
        with self.assertRaises(std.VirtualMethodException):
            class Base(std.TypeChecker.BaseObject):
                def method(self) -> int:
                    return 0

            class Derived(Base):
                @std.override_method
                def method(self) -> int:
                    return 1

    def test_missing_override_annotation(self) -> None:
        with self.assertRaises(std.OverrideMethodException):
            class Base(std.TypeChecker.BaseObject):
                @std.virtual_method
                def method(self) -> int:
                    return 0

            class Derived(Base):
                def method(self) -> int:
                    return 1

    def test_missing_abstract_method_implementation(self) -> None:
        with self.assertRaises(std.AbstractMethodException):
            class Base(std.TypeChecker.BaseObject):
                @std.abstract_method
                def method(self) -> int:
                    return 0

            class Derived(Base):
                ...

    def test_overriding_non_existent_method(self) -> None:
        with self.assertRaises(std.OverrideMethodException):
            class Base(std.TypeChecker.BaseObject):
                ...

            class Derived(Base):
                @std.override_method
                def method(self) -> int:
                    return 1

    def test_virtual_method_override(self) -> None:
        class Base(std.TypeChecker.BaseObject):
            @std.virtual_method
            def method(self) -> int:
                return 0

        class Derived(Base):
            @std.override_method
            def method(self) -> int:
                return 1

        d = Derived()
        self.assertEqual(d.method(), 1)

    def test_abstract_method_implementation(self) -> None:
        class Base(std.TypeChecker.BaseObject):
            @std.abstract_method
            def method(self) -> int:
                return 0

        class Derived(Base):
            @std.override_method
            def method(self) -> int:
                return 1

        d = Derived()
        self.assertEqual(d.method(), 1)

    def test_unrelated_class_private_access(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            __attr: int

            def __init__(self) -> None:
                self.__attr = 0

        class Other:
            def method(self, test: Test) -> int:
                return test.__attr

        with self.assertRaises(std.AccessModifierException):
            t = Test()
            o = Other()
            o.method(t)

    def test_unrelated_function_private_access(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            __attr: int

            def __init__(self) -> None:
                self.__attr = 0

        def function(test: Test) -> int:
            return test.__attr

        with self.assertRaises(std.AccessModifierException):
            t = Test()
            function(t)

    def test_unrelated_class_protected_access(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            _attr: int

            def __init__(self) -> None:
                self._attr = 0

        class Other:
            def method(self, test: Test) -> int:
                return test._attr

        with self.assertRaises(std.AccessModifierException):
            t = Test()
            o = Other()
            o.method(t)

    def test_unrelated_function_protected_access(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            _attr: int

            def __init__(self) -> None:
                self._attr = 0

        def function(test: Test) -> int:
            return test._attr

        with self.assertRaises(std.AccessModifierException):
            t = Test()
            function(t)

    def test_private_access(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            __attribute: int

            def __init__(self) -> None:
                self.__attribute = 0

            def method(self) -> int:
                return self.__attribute

        t = Test()
        self.assertEqual(t.method(), 0)

    def test_protected_access(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            _attribute: int

            def __init__(self) -> None:
                self._attribute = 0

            @std.virtual_method
            def method(self) -> int:
                return self._attribute

        class Derived(Test):
            @std.override_method
            def method(self) -> int:
                return self._attribute

        t = Test()
        d = Derived()
        self.assertEqual(t.method(), 0)
        self.assertEqual(d.method(), 0)

    def test_public_access(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            attribute: int

            def __init__(self) -> None:
                self.attribute = 0

            @std.virtual_method
            def method(self) -> int:
                return self.attribute

        class Derived(Test):
            @std.override_method
            def method(self) -> int:
                return self.attribute

        t = Test()
        d = Derived()
        self.assertEqual(t.method(), 0)
        self.assertEqual(d.method(), 0)
        self.assertEqual(t.attribute, 0)

    def test_friended_class_private_access(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            __attribute: int
            __friends__ = {"Friend"}

            def __init__(self) -> None:
                self.__attribute = 0

        class Friend(std.TypeChecker.BaseObject):
            def method(self) -> int:
                return Test().__attribute

        f = Friend()
        self.assertEqual(f.method(), 0)

    def test_friended_class_protected_access(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            _attribute: int
            __friends__ = {"Friend"}

            def __init__(self) -> None:
                self._attribute = 0

        class Friend(std.TypeChecker.BaseObject):
            def method(self) -> int:
                return Test()._attribute

        f = Friend()
        self.assertEqual(f.method(), 0)

    def test_friended_method_private_access(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            __attribute: int
            __friends__ = {"Friend.method"}

            def __init__(self) -> None:
                self.__attribute = 0

        class Friend(std.TypeChecker.BaseObject):
            def method(self) -> int:
                return Test().__attribute

        f = Friend()
        self.assertEqual(f.method(), 0)

    def test_friended_method_protected_access(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            _attribute: int
            __friends__ = {"Friend.method"}

            def __init__(self) -> None:
                self._attribute = 0

        class Friend(std.TypeChecker.BaseObject):
            def method(self) -> int:
                return Test()._attribute

        f = Friend()
        self.assertEqual(f.method(), 0)

    def test_friended_function_private_access(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            __attribute: int
            __friends__ = {"function"}

            def __init__(self) -> None:
                self.__attribute = 0

        def function() -> int:
            return Test().__attribute

        self.assertEqual(function(), 0)

    def test_friended_function_protected_access(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            _attribute: int
            __friends__ = {"function"}

            def __init__(self) -> None:
                self._attribute = 0

        def function() -> int:
            return Test()._attribute

        self.assertEqual(function(), 0)

    def test_inheriting_friendship(self) -> None:
        class Test(std.TypeChecker.BaseObject):
            _attribute: int
            __friends__ = {"function"}

            def __init__(self) -> None:
                self._attribute = 0

        class Derived(Test):
            _other_attribute: int

            def __init__(self) -> None:
                super().__init__()
                self._other_attribute = 1

        def function() -> int:
            return Derived()._attribute

    def test_deeper_inheritance(self) -> None:
        class X(std.TypeChecker.BaseObject):
            @std.virtual_method
            def method(self) -> None:...

        class Y(X):
            @std.override_method
            @std.virtual_method
            def method(self) -> None:...

        class Z(Y):
            @std.override_method
            def method(self) -> None:...

        z = Z()
        z.method()
