import pytest
from ruamel.yaml import YAML


def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".yaml":
        return YamlFile.from_parent(parent, path=file_path)


class YamlFile(pytest.File):
    def collect(self):
        yaml = YAML(typ="safe")
        raw = yaml.load(self.path.open(encoding="utf-8"))
        for item in raw["tests"]:
            name = item.pop("name")
            yield YamlItem.from_parent(self, name=name, **item)


class YamlItem(pytest.Item):
    def __init__(self, *, id, input, **kwargs):
        super().__init__(**kwargs)

    def runtest(self):
        pass

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
