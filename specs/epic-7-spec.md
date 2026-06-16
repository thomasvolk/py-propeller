# 7 · Packaging & Public API — Technical Specification

## Overview

Epic 7 produces a pip-installable `py-propeller` package by adding `pyproject.toml` to the
repository root, updating `propeller/__init__.py` to expose the controlled public API (`project`
and `track`), and shipping a minimal `examples/` script. The sdist includes `examples/`; the
wheel does not install it into site-packages. PyPI publishing is out of scope.

**Confidence Level:** 92% — All decisions resolved; the only residual uncertainty is runtime
dependencies (F-5) which cannot be pinned until Epics 1–6 implementations are complete — a
PRD-acknowledged constraint, not a spec gap.

---

## Architecture Overview

Three artefacts are introduced or updated:

- **`pyproject.toml`** (new) — build system declaration using `hatchling`, project metadata
  (`name`, `version`, `requires-python`, `dependencies`), and sdist include configuration for
  `examples/`. The concrete `[build-system]` table is:

  ```toml
  [build-system]
  requires = ["hatchling"]
  build-backend = "hatchling.build"
  ```

  The sdist include is declared as:

  ```toml
  [tool.hatch.build.targets.sdist]
  include = ["examples/**"]
  ```

- **`propeller/__init__.py`** (updated) — currently exposes `track = Track` and
  `project = Project` per Epic 3. This epic locks down the public surface by adding an explicit
  `__all__ = ["project", "track"]` so that `from propeller import *` and
  `from propeller import project, track` expose exactly the documented DSL entry points and
  nothing else (NF-2).

- **`examples/play_example.py`** (new) — a standalone script that uses
  `from propeller.notes import *` and `from propeller import project, track`, builds a minimal
  project, and calls `.play()`. It must produce no import or attribute errors when run against
  an installed package (AC-4). The exact musical content is left to the implementer; the
  script does not need a running engine to satisfy the import-level AC.

**Pip distribution name vs. import name:** `pyproject.toml` sets `name = "py-propeller"`;
the importable namespace remains `propeller` (NF-3). Hatchling resolves this automatically
from the `propeller/` source directory — no extra mapping config is needed.

**`examples/` sdist inclusion:** The examples directory lives at the repository root and is
included in sdist via `[tool.hatch.build.targets.sdist] include = ["examples/**"]`. The wheel
target defaults to `propeller/` package content only, so no examples land in site-packages.

---

## Components

### `pyproject.toml`

Top-level packaging manifest. Key sections:

- `[build-system]` — `requires = ["hatchling"]`, `build-backend = "hatchling.build"`.
- `[project]` — `name = "py-propeller"`, `version`, `requires-python = ">=3.11"`,
  `dependencies = [...]` (populated once Epics 1–6 implementations confirm runtime deps; likely
  empty or stdlib-only given no third-party I/O libraries are used).
- `[tool.hatch.build.targets.sdist]` — `include = ["examples/**"]`.

### `propeller/__init__.py`

Updated from Epic 3. Currently sets `track = Track` and `project = Project`. This epic adds:

```python
__all__ = ["project", "track"]
```

No other public symbols are added. Internal modules (`notes`, `errors`, `composition`,
`serializer`, `transport`) remain accessible via their full dotted paths but are not
re-exported from the top-level `propeller` namespace.

### `examples/play_example.py`

Minimal usage demonstration. Template:

```python
from propeller.notes import *
from propeller import project, track

p = project(
    bpm=120,
    time_signature=(4, 4),
    bars=1,
    tracks=[
        track(name="Piano", channel=0, instrument=0, notes=[C4, D4, E4, F4]),
    ],
)
p.play()
```

The script must be runnable as `python examples/play_example.py` without raising
`ImportError` or `AttributeError` (a live engine is not required for the import-level AC).

---

## Data Model

| Type / Field | Value | Notes |
|---|---|---|
| `pyproject.toml` → `name` | `"py-propeller"` | pip install name; distinct from import name `propeller` (NF-3). |
| `pyproject.toml` → `requires-python` | `">=3.11"` | F-8. |
| `pyproject.toml` → `build-backend` | `"hatchling.build"` | D-1 resolved to hatchling. |
| `pyproject.toml` → `dependencies` | `[]` (TBD) | Runtime deps enumerable only after other epics complete (F-5). |
| `propeller.__all__` | `["project", "track"]` | Controls star-import and signals the public API surface (NF-2). |

---

## Implementation Tasks

Tasks are ordered TDD-first: every test task must appear before the impl task it covers.

| ID | Task | Type | PRD ref | Depends on |
|----|------|------|---------|------------|
| T-1 | Test: parse `pyproject.toml` with `tomllib` (stdlib); assert `project.name == "py-propeller"` and `project.requires-python == ">=3.11"` | test | AC-6, F-6, F-8 | — |
| I-1 | Create `pyproject.toml` with `[build-system]` (`requires = ["hatchling"]`, `build-backend = "hatchling.build"`), `[project]` metadata: `name = "py-propeller"`, `version`, `requires-python = ">=3.11"`, `dependencies = []` | impl | F-1, F-5, F-6, F-8 | T-1 |
| T-2 | Test: `from propeller import project, track` succeeds; both are callable (`callable(project)` and `callable(track)`) | test | AC-3, F-3 | — |
| I-2 | Add `__all__ = ["project", "track"]` to `propeller/__init__.py`; confirm `track` and `project` are already imported from Epic 3 | impl | F-3, NF-2 | T-2 |
| T-3 | Test: `from propeller.notes import *` in a subprocess; assert `C4`, `Cs4`, `Ef4`, `Z` are present in the resulting namespace | test | AC-2, F-2 | — |
| T-4 | Test: `examples/` directory exists at repository root and contains at least one `.py` file | test | F-4, AC-4 | — |
| I-3 | Create `examples/play_example.py` using the minimal template above | impl | F-4 | T-4 |
| T-5 | Test: `examples/play_example.py` can be imported without `ImportError` or `AttributeError` (run as subprocess or via `importlib`; no live engine required) | test | AC-4 | I-3 |
| T-6 | Test: build sdist and inspect archive with `tarfile`; assert at least one member path starts with `examples/` | test | AC-5, F-7 | I-1, I-3 |
| I-4 | Add `[tool.hatch.build.targets.sdist]` with `include = ["examples/**"]` to `pyproject.toml` | impl | F-7 | T-6 |
| T-7 | Test: after `pip install .` in a temp venv, inspect `site-packages`; assert no path under it contains `examples/` | test | AC-7, F-7 | I-4 |
| T-8 | Integration test: create a temp venv, run `pip install .`, assert `python -c "import propeller"` exits 0 and `python -c "from propeller import project, track; from propeller.notes import *; assert callable(project)"` exits 0 | test | AC-1, AC-2, AC-3, NF-1, NF-3 | I-1, I-2, I-4 |

---

## Open Questions

*None — all questions resolved.*

---

## Open Decisions

*None — all decisions resolved.*

---

## Revision Log

### Cycle 1 — Confidence: 72%
- Reconciled: nothing (spec created fresh from PRD)
- Added: D-1 (build backend choice)

### Cycle 2 — Confidence: 92%
- Reconciled: D-1 → B (hatchling); `[build-system]` and sdist include syntax concretised in Architecture Overview, Data Model (`build-backend` row added), `pyproject.toml` component, I-1, and I-4; D-1 removed from Open Decisions
- Added: nothing (confidence ≥ 90%; no open questions or decisions remain)

### Cycle 3 — Confidence: 92%
- Reconciled: nothing (no answered questions or checked decisions)
- Added: nothing (confidence ≥ 90%; specification is complete)
