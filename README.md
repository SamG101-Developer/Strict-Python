# Strict-Python
Strict Python is a small library that enforces several concepts from other language, reducing the flexibility and ensuring better safety in certain areas of Python code.

### Functionality
- Type checking on function parameters -> checked against annotations
- Type checking on function return value -> checked against annotation
- Type checking on attributes being set -> checked against annotation
- All parameters and return types are required
- All attributes must be declared at the top of the class with their associated type
- Attributes defined as a typing.Final[T] are not modifiable, except from the constructor
- Access modifiers are enforced via naming conventions (\_protected, \_\_private)
- Can declare friend functions, classes or methods to allow access to non-public members
- For non-class methods, just apply the decorator `force_static_typing` directly

### Areas that need work on
- Decorators -> these change the name of the functions in the inspect stack, causing issues on function name checks
- Haven't tested overloads or anything relating to them, so not sure how these hold out
- Haven't tested optional parameters

### Throwable exceptions
- `AnnotationException`: Function parameter, return type, or an attribute is missing a type annotation
- `AccessModificationException`: A non-friend object is trying to access a non-public member of the class
- `TypeMismatchException`: Incorrect argument/returned type to/from a method
- `ConstModificationException`: A Final[T] attribute is being modified from a non-constructor context
- `VirtualMethodException`: Non-virtual method being overridden.
- `AbstractMethodException`: Abstract method not being implemented in a subclass
- `OverrideMethodException`: Override method not marked as override.

### Notes
- Annotate any constructor's return type as `None`
- Annotate other non-returning methods as `std.NoReturn`
- The `__friends__` attribute must be a set (can be a frozenset)
---


```python
import std

class TestClass(std.BaseObject):
    __friends__ = frozenset({"main"})
    __slots__ = frozenset({"_a", "_b", "_c"})
    
    _a: std.Str
    _b: std.Int
    _c: std.Const[std.Int] = 123 

    def __init__(self) -> None:
        self._a = ""

    def _b(self, a: int) -> std.NoReturn:
        self._b = 100  # Fine
        self._a = a  # TypeMismatchException
        self._c = 123  # ConstModificationException
```
