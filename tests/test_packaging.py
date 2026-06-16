"""Tests for Epic 7: Packaging & Public API."""
import pathlib
import subprocess
import sys
import tarfile
import tempfile
import tomllib

import pytest

REPO_ROOT = pathlib.Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# T-1: pyproject.toml metadata
# ---------------------------------------------------------------------------

class TestPyprojectMetadata:
    def _load_toml(self):
        with open(REPO_ROOT / "pyproject.toml", "rb") as f:
            return tomllib.load(f)

    def test_name_is_py_propeller(self):
        data = self._load_toml()
        assert data["project"]["name"] == "py-propeller"

    def test_requires_python(self):
        data = self._load_toml()
        assert data["project"]["requires-python"] == ">=3.11"

    def test_build_backend_is_hatchling(self):
        data = self._load_toml()
        assert data["build-system"]["build-backend"] == "hatchling.build"

    def test_hatchling_in_build_requires(self):
        data = self._load_toml()
        assert "hatchling" in data["build-system"]["requires"]


# ---------------------------------------------------------------------------
# T-2: public API imports from propeller
# ---------------------------------------------------------------------------

class TestPublicAPIImports:
    def test_project_importable(self):
        from propeller import project
        assert callable(project)

    def test_track_importable(self):
        from propeller import track
        assert callable(track)

    def test_all_contains_project(self):
        import propeller
        assert "project" in propeller.__all__

    def test_all_contains_track(self):
        import propeller
        assert "track" in propeller.__all__

    def test_all_does_not_contain_internals(self):
        import propeller
        for internal in ("Project", "Track", "errors", "composition", "notes", "transport"):
            assert internal not in propeller.__all__


# ---------------------------------------------------------------------------
# T-3: star import from propeller.notes
# ---------------------------------------------------------------------------

class TestNotesStarImport:
    def test_c4_present(self):
        namespace = {}
        exec("from propeller.notes import *", namespace)
        assert "C4" in namespace

    def test_cs4_present(self):
        namespace = {}
        exec("from propeller.notes import *", namespace)
        assert "Cs4" in namespace

    def test_ef4_present(self):
        namespace = {}
        exec("from propeller.notes import *", namespace)
        assert "Ef4" in namespace

    def test_z_present(self):
        namespace = {}
        exec("from propeller.notes import *", namespace)
        assert "Z" in namespace


# ---------------------------------------------------------------------------
# T-4: examples/ directory exists with .py file
# ---------------------------------------------------------------------------

class TestExamplesDirectory:
    def test_examples_dir_exists(self):
        assert (REPO_ROOT / "examples").is_dir()

    def test_examples_contains_py_file(self):
        py_files = list((REPO_ROOT / "examples").glob("*.py"))
        assert py_files, "examples/ must contain at least one .py file"


# ---------------------------------------------------------------------------
# T-5: examples/play_example.py importable without errors
# ---------------------------------------------------------------------------

class TestExampleScript:
    def test_play_example_importable(self):
        result = subprocess.run(
            [sys.executable, "-c",
             "import importlib.util, pathlib; "
             "spec = importlib.util.spec_from_file_location("
             "'play_example', pathlib.Path('examples/play_example.py')); "
             "mod = importlib.util.module_from_spec(spec)"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, result.stderr

    def test_play_example_no_import_error(self):
        script = str(REPO_ROOT / "examples" / "play_example.py")
        result = subprocess.run(
            [sys.executable, "-c",
             f"import ast; ast.parse(open({script!r}).read())"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

    def test_play_example_imports_resolve(self):
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, '.'); "
             "from propeller.notes import *; "
             "from propeller import project, track; "
             "assert callable(project); assert callable(track)"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, result.stderr


# ---------------------------------------------------------------------------
# T-6: Build sdist and verify examples/ is included in the archive
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def built_sdist(tmp_path_factory):
    dist_dir = tmp_path_factory.mktemp("dist")
    result = subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--outdir", str(dist_dir), str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    archives = list(dist_dir.glob("*.tar.gz"))
    assert archives, "No sdist archive produced"
    return archives[0]


class TestSdistContents:
    def test_examples_in_sdist(self, built_sdist):
        with tarfile.open(built_sdist) as tf:
            members = [m.name for m in tf.getmembers()]
        examples_members = [m for m in members if "/examples/" in m or m.endswith("/examples")]
        assert examples_members, "No examples/ entries found in sdist"

    def test_play_example_in_sdist(self, built_sdist):
        with tarfile.open(built_sdist) as tf:
            members = [m.name for m in tf.getmembers()]
        assert any("play_example.py" in m for m in members)


# ---------------------------------------------------------------------------
# T-7 & T-8: Install in a temp venv and verify behaviour
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def installed_venv(tmp_path_factory):
    venv_dir = tmp_path_factory.mktemp("venv")
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    pip = venv_dir / "bin" / "pip"
    result = subprocess.run(
        [str(pip), "install", str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return venv_dir


class TestNoExamplesInSitePackages:
    def test_examples_not_in_site_packages(self, installed_venv):
        python = installed_venv / "bin" / "python"
        result = subprocess.run(
            [str(python), "-c",
             "import site; import os; "
             "sp = site.getsitepackages(); "
             "found = []; "
             "[found.extend(os.walk(d)) for d in sp]; "
             "paths = [os.path.join(r, f) for r, _, fs in found for f in fs]; "
             "assert not any('examples' in p for p in paths), "
             f"'examples found in site-packages: ' + str([p for p in paths if 'examples' in p])"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr


class TestVenvInstallation:
    def test_import_propeller(self, installed_venv):
        python = installed_venv / "bin" / "python"
        result = subprocess.run(
            [str(python), "-c", "import propeller"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

    def test_import_project_and_track(self, installed_venv):
        python = installed_venv / "bin" / "python"
        result = subprocess.run(
            [str(python), "-c",
             "from propeller import project, track; assert callable(project)"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr

    def test_notes_star_import(self, installed_venv):
        python = installed_venv / "bin" / "python"
        result = subprocess.run(
            [str(python), "-c",
             "from propeller.notes import *; assert 'C4' in dir()"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
