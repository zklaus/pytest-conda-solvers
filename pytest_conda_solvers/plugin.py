from tempfile import TemporaryDirectory

import pytest
from ruamel.yaml import YAML

from .helpers import SimpleEnvironment


def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".yaml":
        return CondaSolverTestFile.from_parent(parent, path=file_path)


@pytest.fixture()
def env():
    solver_class = None
    with TemporaryDirectory(prefix="conda-test-repo-") as tmpdir:
        myenv = SimpleEnvironment(tmpdir, solver_class)
        yield myenv


class CondaSolverTestFile(pytest.File):
    def collect(self):
        yaml = YAML(typ="safe")
        raw = yaml.load(self.path.open(encoding="utf-8"))
        for item in raw["tests"]:
            yield CondaSolverTestItem.from_parent(self, **item)


class CondaSolverTestItem(pytest.Item):
    def setup(self) -> None:
        print("Hello, world!")

    def runtest(self):
        pass

    def teardown(self) -> None:
        return super().teardown()

    def repr_failure(self, excinfo):
        """Called when self.runtest() raises an exception."""
        if isinstance(excinfo.value, YamlException):
            return "\n".join(
                [
                    "usecase execution failed",
                    "   spec failed: {1!r}: {2!r}".format(*excinfo.value.args),
                    "   no further details known at this point.",
                ]
            )
        return super().repr_failure(excinfo)

    def reportinfo(self):
        return self.path, 0, f"usecase: {self.name}"


class YamlException(Exception):
    """Custom exception for error reporting."""


def pytest_addoption(parser):
    group = parser.getgroup("conda-solvers")
    group.addoption(
        "--foo",
        action="store",
        dest="dest_foo",
        default="2024",
        help='Set the value for the fixture "bar".',
    )

    parser.addini("HELLO", "Dummy pytest.ini setting")


@pytest.fixture
def bar(request):
    return request.config.option.dest_foo
