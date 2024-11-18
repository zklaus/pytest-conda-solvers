from importlib import util
from typing import Any, Iterable, Union

import pytest
from pytest import Collector, Config, Item, Metafunc, Session
from ruamel.yaml import YAML

# import fixtures here to actually make them available
from .fixtures import (  # noqa: F401
    env,
    index_packages,
)


def pytest_configure(config: Config) -> None:
    config.addinivalue_line(
        "markers", "conda_solver_test: marks the test for parametrization"
    )


def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".yaml":
        return CondaSolverYamlFile.from_parent(parent, path=file_path)


def pytest_generate_tests(metafunc: Metafunc) -> None:
    cst = metafunc.definition.get_closest_marker("conda_solver_test")
    if cst:
        te = metafunc.definition.parent.parent.test_entry
        ids = (te["name"].replace(" ", "_"),)
        metafunc.parametrize("test", ids, ids=ids)


def pytest_collection_modifyitems(
    session: Session, config: Config, items: list[Item]
) -> None:
    for item in items:
        cst = item.get_closest_marker("conda_solver_test")
        if cst:
            original_id = item._nodeid
            base_id, detail_id = original_id.rsplit("::", 1)
            item._nodeid = base_id


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
