import pytest

from .helpers import SimpleEnvironment


@pytest.fixture()
def env(tmp_path):
    from conda_libmamba_solver.solver import LibMambaSolver

    myenv = SimpleEnvironment(tmp_path, LibMambaSolver, ("linux-64",))
    yield myenv


@pytest.fixture()
def index_packages():
    return tuple()
