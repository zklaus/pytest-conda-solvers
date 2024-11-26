import pytest
from conda.base.context import context
from pytest import FixtureRequest

from .helpers import SimpleEnvironment

pytest_plugins = "pytest_conda_solvers.server"


@pytest.fixture
def solver_backend(request: FixtureRequest):
    solver_name = request.config.option.conda_solver
    yield context.plugin_manager.get_solver_backend(name=solver_name)


@pytest.fixture()
def env(tmp_path, solver_backend):
    myenv = SimpleEnvironment(tmp_path, solver_backend, ("linux-64",))
    yield myenv
