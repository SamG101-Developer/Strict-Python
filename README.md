# Strict-Python
Strict Python is a small libary that enforces several concepts from other language, reducing the flexibility and ensuring better safety in certain areas of Python code.

### Functionality
- Type checking on function parameters -> checked against annotations
- Type checking on function return value -> checked against annotation
- Type checking on attributes being set -> checked against annotation
- All attributes must be declared at the top of the class with their associated type
- Attributes defined as a typing.Final[T] are not modifiable, except from the constructor
- Access modifiers are enforced via naming conventions (\_protected, \_\_private)
- Can declare friend functions, classes or methods to allow access to non-public members

### Areas that need work on
- Decorators -> these change the name of the functions in the inspect stack, causing issues on function name checks
- Haven't tested overloads or anything relating to them, so not sure how these hold out


---


```python
class TestClass(base_object):
    __friends__ = frozenset({"main"})
    __slots__ = frozenset({"_a", "_b", "_c"})
    
    _a: str
    _b: int
    _c: std.final[int]

    def __init__(self):
        base_object.__init__(self)
        self._a = ""

    def _b(self, a: int):
        self._b = 100  # Fine
        self._a = a  # TypeMismatchException
        self._c = 123  # ConstModificationException
```
