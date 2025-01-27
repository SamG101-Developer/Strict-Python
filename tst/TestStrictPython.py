from __future__ import annotations
from unittest import TestCase
import std


class TestStrictPython(TestCase):
    def test_attribute_type_match(self):
        class Test(std.BaseObject):
            attribute: int

            def __init__(self):
                self.attribute: int = 0

    def test_attribute_type_mismatch(self):
        class Test(std.BaseObject):
            attribute: int

            def __init__(self) -> None:
                self.attribute: int = 0

        with self.assertRaises(std.TypeMismatchException):
            t = Test()
            t.attribute = "string"

    def test_attribute_final_overwrite(self):
        class Test(std.BaseObject):
            attribute: std.Const[int] = 0

        with self.assertRaises(std.ConstModifierException):
            t = Test()
            t.attribute = 2

    def test_parameter_type_mismatch(self):
        class Test(std.BaseObject):
            def method(self, param: int) -> None:
                pass

        with self.assertRaises(std.TypeMismatchException):
            t = Test()
            t.method("string")

    def test_return_type_mismatch(self):
        class Test(std.BaseObject):
            def method(self) -> int:
                return "string"

        with self.assertRaises(std.TypeMismatchException):
            t = Test()
            t.method()

    def test_return_no_return(self):
        class Test(std.BaseObject):
            def method(self) -> std.NoReturn:
                return 0

        with self.assertRaises(std.TypeMismatchException):
            t = Test()
            t.method()

    def test_invalid_private_access(self):
        class Test(std.BaseObject):
            __attribute: int

            def __init__(self) -> None:
                self.__attribute = 0

        class Derived(Test):
            def method(self) -> int:
                return self.__attribute

        with self.assertRaises(std.AccessModifierException):
            d = Derived()
            d.method()

    def test_invalid_protected_access(self):
        class Test(std.BaseObject):
            _attribute: int

        def test():
            return Test()._attribute

        with self.assertRaises(std.AccessModifierException):
            test()

    def test_valid_protected_access(self):
        class Test(std.BaseObject):
            _attribute: int

            def __init__(self) -> None:
                self._attribute = 0

        class Derived(Test):
            def method(self) -> int:
                return self._attribute

        d = Derived()
        d.method()

    def test_valid_private_access_friend(self):
        class Test(std.BaseObject):
            __attribute: int
            __friends__ = {"Friend"}

            def __init__(self) -> None:
                self.__attribute = 0

        class Friend(std.BaseObject):
            def method(self) -> int:
                return Test().__attribute

        f = Friend()
        f.method()

    def test_valid_protected_access_friend(self):
        class Test(std.BaseObject):
            _attribute: int
            __friends__ = {"Friend"}

            def __init__(self) -> None:
                self._attribute = 0

        class Friend(std.BaseObject):
            def method(self) -> int:
                return Test()._attribute

        f = Friend()
        f.method()

    def test_non_override_non_virtual_method(self):
        class Test(std.BaseObject):
            def method(self) -> int:
                return 0

        with self.assertRaises(std.VirtualMethodException):
            class Derived(Test):
                def method(self) -> int:
                    return 1

    def test_override_non_virtual_method(self):
        class Test(std.BaseObject):
            def method(self) -> int:
                return 0

        with self.assertRaises(std.VirtualMethodException):
            class Derived(Test):
                @std.override_method
                def method(self) -> int:
                    return 1

    def test_non_override_virtual_method(self):
        class Test(std.BaseObject):
            @std.virtual_method
            def method(self) -> int:
                return 0

        with self.assertRaises(std.VirtualMethodException):
            class Derived(Test):
                def method(self) -> int:
                    return 1

    def test_override_virtual_method(self):
        class Test(std.BaseObject):
            @std.virtual_method
            def method(self) -> int:
                return 0

        class Derived(Test):
            @std.override_method
            def method(self) -> int:
                return 1

        d = Derived()
        self.assertEqual(d.method(), 1)

    def test_missing_abstract_method_implementation(self):
        class Test(std.BaseObject):
            @std.abstract_method
            def method(self) -> int:
                return 0

        with self.assertRaises(std.AbstractMethodException):
            class Derived(Test):
                ...

    def test_override_abstract_method(self):
        class Test(std.BaseObject):
            @std.abstract_method
            def method(self) -> int:
                pass

        class Derived(Test):
            @std.override_method
            def method(self) -> int:
                return 1

        d = Derived()
        self.assertEqual(d.method(), 1)
