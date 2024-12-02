from importlib import util
from typing import Any, Iterable, Union

import pytest
from pytest import (
    Collector,
    Config,
    Item,
    Metafunc,
    Parser,
    PytestPluginManager,
    Session,
)
from ruamel.yaml import YAML

from conda.gateways.logging import initialize_logging

initialize_logging()

pytest_plugins = "pytest_conda_solvers.fixtures"


def pytest_addoption(parser: Parser, pluginmanager: PytestPluginManager) -> None:
    group = parser.getgroup("conda_solver")
    group.addoption("--conda-solver", default="libmamba")


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        "markers", "conda_solver_test: marks the test for parametrization"
    )


def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".yaml":
        return CondaSolverYamlFile.from_parent(parent, path=file_path)


def pytest_generate_tests(metafunc: Metafunc) -> None:
    is_conda_solver_test = metafunc.definition.get_closest_marker("conda_solver_test")
    if is_conda_solver_test:
        test_entry = metafunc.definition.parent.parent.test_entry
        if f"test_{test_entry['kind']}" == metafunc.definition.name:
            ids = (test_entry["name"].replace(" ", "_"),)
            metafunc.parametrize("test", (test_entry,), ids=ids)


def pytest_collection_modifyitems(
    session: Session, config: Config, items: list[Item]
) -> None:
    remaining = []
    deselected = []
    for colitem in items:
        cst = colitem.get_closest_marker("conda_solver_test")
        if cst:
            if colitem.name == colitem.originalname:
                deselected.append(colitem)
            else:
                remaining.append(colitem)
                # original_id = item._nodeid
                # base_id, detail_id = original_id.rsplit("::", 1)
                # item._nodeid = base_id  # .replace(".yaml", ".py")
        else:
            remaining.append(colitem)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = remaining


class CondaSolverYamlFile(pytest.File):
    def collect(self):
        yield from self._collect_path()

    def _collect_path(self):
        yaml = YAML(typ="safe")
        raw = yaml.load(self.path.open(encoding="utf-8"))
        for item in raw["tests"]:
            module = load_module()
            yield CondaSolverTestFile.from_parent(
                self,
                path=self.path,
                obj=module,
                test_entry=item,
                name=f"{item['name']}-file",
            )


def load_module():
    module_name = "pytest_conda_solvers.base_tests.install"
    spec = util.find_spec(module_name)
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CondaSolverTestFile(pytest.Module):
    def __init__(self, obj: Any, test_entry: Any, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.obj = obj
        self.test_entry = test_entry

    def collect(self) -> Iterable[Union[Item, Collector]]:
        """
        Collects a single NutsTestClass instance from this NutsTestFile.
        At the start inject setup_module fixture and parse all fixtures from the module.
        This is directly adopted from pytest.Module.
        """

        self._register_setup_module_fixture()
        self._register_setup_function_fixture()
        self.session._fixturemanager.parsefactories(self)

        name = self.test_entry["name"].replace(" ", "_")

        yield CondaSolverTestClass.from_parent(
            self,
            name=name,
            class_name="TestBasic",
        )


class CondaSolverTestClass(pytest.Class):
    def __init__(
        self, parent: CondaSolverTestFile, name: str, class_name: str, **kw: Any
    ):
        super().__init__(name, parent=parent)
        self.params: Any = kw
        self.name: str = name
        self.class_name: str = class_name

    def _getobj(self) -> Any:
        """
        Get the underlying Python object.
        Overwritten from PyobjMixin to separate name and classname.
        This allows to group multiple tests of the same class with
        different parameters to be grouped separately.
        """
        # cf. https://github.com/pytest-dev/pytest/blob/master/src/_pytest/python.py
        assert self.parent is not None
        obj = self.parent.obj  # type: ignore[attr-defined]
        return getattr(obj, self.class_name)
