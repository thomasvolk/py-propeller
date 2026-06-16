# Epic 7 · Packaging & Public API — PRD

## Overview

Epic 7 ensures that py-propeller is properly packaged and installable as a standalone Python library. It covers the packaging configuration (`pyproject.toml`), verifies that the public API surface is importable exactly as shown in the briefing DSL (`from propeller.notes import *` and `from propeller import project, track`), and ships a minimal usage example in the `examples/` directory at the repository root. The pip distribution name is `py-propeller`; the importable module name remains `propeller`. This epic depends on Epic 5 (Play Loop) being complete and can run in parallel with Epic 6 (Validation & Error Feedback). PyPI publishing is out of scope.

**Confidence Level:** 92% — All four previously open questions are resolved. Remaining uncertainty: runtime dependencies are not yet enumerable (they depend on other epics completing) and the precise filename/content of the example script is not pinned by the PRD.

---

## User Journeys

### UJ-1 · Installing the package

A developer clones the py-propeller repository and runs `pip install .` from the project root in a clean virtual environment. The package installs without errors and the `propeller` namespace becomes immediately importable.

### UJ-2 · Writing a first composition

After installation, a musician or developer writes a Python script using `from propeller.notes import *` and `from propeller import project, track`. They compose a musical project using the note DSL and call `.play()` to stream it to a running propeller-engine instance.

### UJ-3 · Following the shipped example

A new user browses the repository and opens a file in the `examples/` directory. They run it directly to confirm their installation is working, then use it as a starting point for their own compositions.

---

## Functional Requirements

| ID  | Requirement |
|-----|-------------|
| F-1 | The package must provide a valid `pyproject.toml` that enables `pip install .` from the project root. |
| F-2 | `from propeller.notes import *` must expose all note constants (C4, Cs4, Ef4, Z, and the full set defined in Epic 1). |
| F-3 | `from propeller import project, track` must expose the `project()` and `track()` DSL entry points defined in Epics 3 and 5. |
| F-4 | A minimal usage example script must be present in an `examples/` directory at the repository root. |
| F-5 | The `pyproject.toml` must declare all runtime dependencies required by the installed package. |
| F-6 | The `pyproject.toml` `name` field must be set to `py-propeller`. |
| F-7 | The `examples/` directory must be included in the sdist via `pyproject.toml` include configuration; example files must not be installed into site-packages. |
| F-8 | The `pyproject.toml` must declare `requires-python = ">=3.11"`. |

---

## Non-Functional Requirements

| ID   | Requirement |
|------|-------------|
| NF-1 | Installation must succeed in a clean virtual environment with no packages pre-installed beyond pip. |
| NF-2 | The `propeller` top-level namespace must not leak internal implementation modules — only `project`, `track`, and any other explicitly public symbols should be importable directly from `propeller`. |
| NF-3 | The pip distribution name (`py-propeller`) and the importable Python module name (`propeller`) are intentionally distinct; installing `py-propeller` must make `import propeller` work. |
| NF-4 | PyPI publishing is out of scope for this epic; the distribution target is local install (`pip install .`) only. |

---

## Acceptance Criteria

| ID   | Given | When | Then |
|------|-------|------|------|
| AC-1 | A clean Python 3.11+ virtual environment with pip | `pip install .` is run from the project root | The package installs without errors and the `propeller` namespace becomes importable |
| AC-2 | The package is installed | `from propeller.notes import *` is executed | Note constants (e.g., `C4`, `Cs4`, `Ef4`, `Z`) are present in the caller's namespace |
| AC-3 | The package is installed | `from propeller import project, track` is executed | `project` and `track` are available and callable |
| AC-4 | The package is installed | The minimal usage example script in `examples/` is executed | The script runs to the point of calling `.play()` without any import or attribute errors |
| AC-5 | An sdist is built from the project root | The archive contents are listed | At least one file under `examples/` is present in the archive |
| AC-6 | The `pyproject.toml` is inspected | Its metadata fields are read | The `name` field reads `py-propeller` and `requires-python` reads `>=3.11` |
| AC-7 | The package is installed into a virtual environment | Site-packages is inspected | No file from the `examples/` directory is present under site-packages |

---

## Open Questions

*No open questions remain. All previously identified ambiguities have been resolved.*

---

## Refinement Log

### Cycle 1 — Confidence: 55%
- Reconciled: (none — initial PRD created from roadmap)
- Added: Q1 (package name), Q2 (example location), Q3 (distribution target), Q4 (minimum Python version)

### Cycle 2 — Confidence: 92%
- Reconciled: Q1 → F-6 (pyproject.toml name = py-propeller) + NF-3 (pip name vs import name distinction); Q2 → F-4 updated + F-7 (examples/ at repo root, sdist only, not installed) + AC-7 (site-packages check); Q3 → NF-4 (local install only, PyPI out of scope); Q4 → F-8 (requires-python >=3.11) + AC-1 updated + AC-6 (metadata check)
- Added: none — confidence reached 92%, no new questions required
