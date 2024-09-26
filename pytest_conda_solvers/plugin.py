from importlib import util
from typing import Iterable, Union, Any

import pytest
from pytest import Item, Collector
from ruamel.yaml import YAML

# import fixtures here to actually make them available
from .fixtures import (  # noqa: F401
    env,
    index_packages,
)


def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".yaml":
        return CondaSolverYamlFile.from_parent(parent, path=file_path)


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

        name = "test-label"

        yield CondaSolverTestFunction.from_parent(
            self,
            name=name,
            function_name="test_empty",
        )


class CondaSolverTestFunction(pytest.Function):
    def __init__(
        self, parent: CondaSolverTestFile, name: str, function_name: str, **kw: Any
    ):
        self.params: Any = kw
        self.name: str = name
        self.function_name: str = function_name
        super().__init__(name, parent=parent)

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
        return getattr(obj, self.function_name)

    @classmethod
    def from_parent(  # type: ignore[override]
        cls, parent, *, name: str, obj: Any = None, **kw: Any
    ) -> Any:
        """The public constructor."""
        # mypy throws an error because the parent class (pytest.Class) does not accept
        # additional **kw.
        # This has been fixed in: https://github.com/pytest-dev/pytest/pull/8367
        # and will be part of a future pytest release. Until then, mypy is instructed
        # to ignore this error
        return cls._create(parent=parent, name=name, obj=obj, **kw)
