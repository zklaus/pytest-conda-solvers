import pytest

from .helpers import SimpleEnvironment

pytest_plugins = "pytest_conda_solvers.server"


@pytest.fixture
def solver():
    from conda_libmamba_solver.solver import LibMambaSolver

    yield LibMambaSolver


@pytest.fixture()
def env(tmp_path, solver):
    myenv = SimpleEnvironment(tmp_path, solver, ("linux-64",))
    yield myenv
