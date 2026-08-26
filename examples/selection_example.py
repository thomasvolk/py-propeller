# Run this with the py-propeller watch script (`py-propeller examples/selection_example.py`).
# loop_count is only read once, when this module is evaluated, so it needs the watcher's
# periodic reload to pick up the new value on every loop — running it once via plain `python`
# freezes the outcome for the whole playback.
from propeller.notes import C4, D4, E4, F4
from propeller.func import selection
from propeller import project, track
from propeller import loop

loop_count = loop.get_position().loop_count

piano_line = (
    selection(loop_count)
    .before(5,  [C4, D4, E4, F4])
    .after(5,   [C4, D4, E4, F4])
    .after(6,   [C4, D4, D4, C4])
    .after(20,  [C4, D4, E4, C4])
    .default(   [C4, D4, E4, C4])
    .select()
)

p = project(
    bpm=100,
    time_signature=(4, 4),
    bars=1,
    tracks=[
        track(name="Piano",
              channel=1,
              instrument=0,
              notes=piano_line
        ),
    ],
)
p.play()
