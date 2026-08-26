Beside the `to` method there will be three new functions how to
generate a slide effect: `sin`, `cos`, `gauss`, plus support for a
plain custom function.

## Unified curve abstraction

`to`, `sin`, `cos`, `gauss` and a custom function all become instances
of one unified curve abstraction that `Slide`'s target parameter
accepts. `to()` is the linear special case of this abstraction: it
keeps its exact public signature and endpoint behavior (still ramps
from 0 to `value`, where `value` is in `[-1.0, 1.0]` excluding `0.0`),
but its `steps` parameter changes meaning from "max pitch-bend value
increment" to the same time-domain sampling interval used by the new
curve types. Existing tests need updating to reflect the new event
ticks/counts, though not different endpoint values.

Every curve is evaluated as a function of `p`, the slide's progress
fraction from `0.0` to `1.0` across its duration (independent of the
slide's actual beat length), sampled at intervals of `steps` (default
`0.01`, meaning roughly 100 evenly-spaced samples across the slide by
default).

Any curve value falling outside `[-1.0, 1.0]` (from amp/y_offset
combinations, or from a custom function) is clipped to the nearest
boundary rather than raising a validation error.

## sin / cos

The pitch bend events will be generated according to a sin/cos function.

```python
from propeller.notes.Slide import sin, cos

Slide(C4, sin(amp=1, period=2, y_offset=0, steps=0.01)) * 4
Slide(C4, cos(amp=1, period=2, y_offset=0, steps=0.01)) * 4

```

- amp: is the amplitude of the wave - default: 2 (there is no enforced
  upper bound)
- period: is the period - this value is a float which will be
  multiplied with pi - 2 is a full period - default: 1
- y_offset: if amp is 2 and y_offset 0, the wave is between -1 and 1 -
  if amp is 1 and the y_offset is 1 the wave is between 0 and 1 -
  default: 0

The generated value at progress `p` is:

```
amp * sin(p * period * pi) + y_offset   # sin
amp * cos(p * period * pi) + y_offset   # cos
```

## gauss

This uses a Standard normal distribution to slide from pitch bend 0 to 1 and back.

```python
from propeller.notes.Slide import gauss

Slide(C4, gauss(u=0, o=1, steps=0.01)) * 4

```

`gauss(u=0, o=1, steps=0.01)` evaluates the standard normal PDF for
`N(u, o)`, normalized so its peak equals 1. Progress `p=0` maps to
`x = u - 3*o` and `p=1` maps to `x = u + 3*o` (a linear mapping across
that fixed ±3σ window, regardless of what `u`/`o` are set to), so the
curve always starts near 0, peaks near 1, and returns near 0 within
the slide.

## custom

Also it must be possible to add a custom function.

```python

def my_func(ctx):
    ...

Slide(C4, my_func) * 4

```

A custom curve is a plain function `my_func(ctx)` passed directly as
`Slide`'s second argument (not wrapped in a builder call like
`sin()`/`cos()`/`gauss()`). `ctx` is simply the progress fraction `p`
(a float between `0.0` and `1.0`), and it's sampled at the same
default `steps` interval (`0.01`) as the built-in curves.
