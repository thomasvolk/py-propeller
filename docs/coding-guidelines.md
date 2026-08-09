# Python Coding Guidelines (PEP 8)

Source: https://peps.python.org/pep-0008/

## Philosophy

Code is read much more often than it is written. Consistency within a module matters most, then within a project, then with this guide. Valid reasons to deviate:

- Making code less readable for those familiar with PEP 8
- Matching surrounding code that already breaks the rule
- Code predating the guideline with no other modification reasons
- Compatibility with older Python versions

Never break backwards compatibility just to comply.

---

## Code Layout

### Indentation

- 4 spaces per indentation level (no tabs)
- Continuation lines: align vertically using implicit line joining inside parentheses/brackets/braces, or use a hanging indent
- Hanging indent: no arguments on first line; extra indentation to distinguish continuation lines

```python
# Correct — aligned with opening delimiter
foo = long_function_name(var_one, var_two,
                         var_three, var_four)

# Correct — hanging indent (4 extra spaces)
foo = long_function_name(
    var_one, var_two,
    var_three, var_four)
```

- Closing delimiter may align under first non-whitespace of last list line, or under first character of the multiline construct

### Tabs or Spaces

- Spaces are preferred
- Use tabs only to remain consistent with existing tab-indented code
- Python 3 disallows mixing tabs and spaces

### Maximum Line Length

- Maximum 79 characters for code
- Docstrings and comments: 72 characters
- Teams may agree on up to 99 characters if comments/docstrings stay at 72
- Prefer implicit continuation inside parentheses/brackets/braces over backslashes

### Line Break Around Binary Operators

Break **before** binary operators (Knuth style):

```python
# Correct
income = (gross_wages
          + taxable_interest
          + (dividends - qualified_dividends)
          - ira_deduction
          - student_loan_interest)
```

### Blank Lines

- Two blank lines around top-level function and class definitions
- One blank line around method definitions inside a class
- Extra blank lines may separate groups of related functions (use sparingly)

### Source File Encoding

- UTF-8; no encoding declaration needed
- Non-ASCII characters only for places, human names — use sparingly
- All stdlib identifiers must be ASCII-only

### Imports

- One import per line (exception: `from subprocess import Popen, PIPE`)
- Import order (separated by blank lines):
  1. Standard library
  2. Related third-party
  3. Local application/library
- Prefer absolute imports; explicit relative imports acceptable for complex layouts
- Avoid wildcard imports (`from module import *`)

### Module-Level Dunders

Place `__all__`, `__author__`, `__version__`, etc. after the module docstring and before imports (except `from __future__`).

---

## String Quotes

- Single and double quotes are equivalent — pick one and be consistent
- Use the other style when the string contains quote characters to avoid backslashes
- Triple-quoted strings: always use double quotes (`"""`)

---

## Whitespace in Expressions and Statements

### Avoid Extraneous Whitespace

```python
# Correct
spam(ham[1], {eggs: 2})
foo = (0,)
if x == 4: print(x, y); x, y = y, x
ham[1:9], ham[lower+offset : upper+offset]
spam(1)
dct['key'] = lst[index]
x = 1
y = 2

# Wrong
spam( ham[ 1 ], { eggs: 2 } )
bar = (0, )
if x == 4 : print(x , y) ; x , y = y , x
ham[lower + offset:upper + offset]
spam (1)
dct ['key'] = lst [index]
x             = 1  # alignment padding
```

- Avoid trailing whitespace anywhere
- No multiple spaces around assignment for alignment

### Operators

```python
# Correct
i = i + 1
submitted += 1
x = x*2 - 1
hypot2 = x*x + y*y
c = (a+b) * (a-b)

# Wrong
i=i+1
submitted +=1
x = x * 2 - 1
```

### Function Annotations

```python
# Correct
def munge(input: AnyStr): ...
def munge() -> PosInt: ...

# Wrong
def munge(input:AnyStr): ...
def munge()->PosInt: ...
```

### Default Values and Keyword Arguments

```python
# Correct — no spaces around = for defaults/kwargs
def complex(real, imag=0.0):
    return magic(r=real, i=imag)

# Correct — spaces around = when combining annotation + default
def munge(sep: AnyStr = None): ...

# Wrong
def complex(real, imag = 0.0): ...
def munge(input: AnyStr=None): ...
```

### Compound Statements

Avoid multiple statements on one line:

```python
# Correct
if foo == 'blah':
    do_blah_thing()

# Wrong
if foo == 'blah': do_blah_thing()
do_one(); do_two(); do_three()
```

---

## Trailing Commas

Required for single-element tuples: `FILES = ('setup.cfg',)`

For multi-line collections, trailing comma + closing delimiter on its own line:

```python
# Correct
FILES = [
    'setup.cfg',
    'tox.ini',
    ]

# Wrong
FILES = ['setup.cfg', 'tox.ini',]
```

---

## Comments

- Comments that contradict code are worse than no comments
- Keep comments current when code changes
- Write complete sentences; capitalize first word (except identifiers)
- Write in English

### Block Comments

- Indented to same level as surrounding code
- Each line: `# ` followed by text
- Separate paragraphs with a line containing only `#`

### Inline Comments

- Use sparingly; separated from statement by at least two spaces
- Don't state the obvious

```python
x = x + 1                 # Compensate for border  (useful)
x = x + 1                 # Increment x            (unnecessary)
```

### Docstrings

- Write for all public modules, functions, classes, methods
- Follow PEP 257
- Multiline: closing `"""` on its own line
- One-liner: closing `"""` on the same line

```python
"""Return a foobang

Optional plotz says to frobnicate the bizbaz first.
"""

"""Return an ex-parrot."""
```

---

## Naming Conventions

### Styles

| Style | Use |
|---|---|
| `lowercase` / `lower_case_with_underscores` | functions, methods, variables, modules |
| `UPPER_CASE_WITH_UNDERSCORES` | constants |
| `CapWords` | classes, type variables, exceptions |
| `_single_leading_underscore` | internal / non-public |
| `single_trailing_underscore_` | avoid keyword clash (`class_`) |
| `__double_leading_underscore` | name mangling in classes |
| `__dunder__` | magic/special objects only (as documented) |

### Names to Avoid

Never use as single-character names: `l` (el), `O` (oh), `I` (eye) — easily confused with `1` and `0`.

### Packages and Modules

Short, all-lowercase; underscores permitted in modules if it improves readability, discouraged in packages.

### Classes

CapWords. Exceptions: use "Error" suffix for error exceptions.

### Type Variables

CapWords, short names (`T`, `AnyStr`, `Num`). Covariant: `_co` suffix; contravariant: `_contra` suffix.

### Functions and Variables

`lowercase_with_underscores`. `mixedCase` only where already prevailing for backwards compatibility.

### Method Arguments

- Instance methods: first argument is `self`
- Class methods: first argument is `cls`
- Keyword clash: append trailing underscore (`class_` not `clss`)

### Constants

Module-level, `ALL_CAPS_WITH_UNDERSCORES` (e.g., `MAX_OVERFLOW`).

### Designing for Inheritance

- Default to non-public; easier to make public later
- Simple public data attributes: expose name directly, not via property accessors
- Use `__double_leading` only to avoid accidental clashes in subclasses
- Use `__all__` to explicitly declare public API

---

## Programming Recommendations

**Singleton comparisons** — use `is` / `is not`, never `==`:

```python
if x is not None:      # Correct
if not x is None:      # Wrong
```

**Lambda assignment** — use `def` instead:

```python
def f(x): return 2*x   # Correct
f = lambda x: 2*x      # Wrong
```

**Exceptions** — derive from `Exception` (not `BaseException`); use "Error" suffix for errors; use `raise X from Y` for chaining.

**Bare `except`** — avoid; catches `SystemExit`/`KeyboardInterrupt`. Use `except Exception:` or a specific type.

**Try clause** — keep it as small as possible; use `else` clause:

```python
# Correct
try:
    value = collection[key]
except KeyError:
    return key_not_found(key)
else:
    return handle_value(value)
```

**Resource management** — prefer `with` statements.

**Return consistency** — if any branch returns an expression, all branches must return explicitly:

```python
# Correct
def foo(x):
    if x >= 0:
        return math.sqrt(x)
    else:
        return None
```

**String checks** — use `startswith()`/`endswith()`:

```python
if foo.startswith('bar'):   # Correct
if foo[:3] == 'bar':        # Wrong
```

**Type checks** — use `isinstance()`:

```python
if isinstance(obj, int):        # Correct
if type(obj) is type(1):        # Wrong
```

**Empty sequences** — rely on truthiness:

```python
if seq:        # Correct
if len(seq):   # Wrong
```

**Boolean comparisons**:

```python
if greeting:           # Correct
if greeting == True:   # Wrong
if greeting is True:   # Worse
```

**`finally` flow control** — don't use `return`/`break`/`continue` in a `finally` block that would jump outside it; implicitly cancels active exceptions.

---

## Type Annotations

Follow PEP 484 (functions) and PEP 526 (variables):

```python
# Correct
code: int
class Point:
    coords: Tuple[int, int]
    label: str = '<unknown>'

# Wrong
code:int
code : int
class Test:
    result: int=0
```

- Type checkers are optional separate tools; the interpreter must not alter behaviour based on annotations
- Stub files (`.pyi`) are the recommended distribution format for type information
