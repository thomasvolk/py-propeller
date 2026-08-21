The propeller engine has a `get-position` command which return the current `tick`, `loop_duration` and `loop_count`.
Details can be found here: https://github.com/thomasvolk/propeller-engine/blob/main/docs/json-socket-interface.md

Goal is to add a new module which can run the command and deliver these values.§

```python
from propeller import loop

p = loop.get_position()
print(f"tick: {tick}")
print(f"loop_duration: {loop_duration}")
print(f"loop_count: {loop_count}")
```
