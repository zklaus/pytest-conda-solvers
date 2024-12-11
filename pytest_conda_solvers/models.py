from enum import Enum

from conda.core.solve import UpdateModifier
from msgspec import Struct


class TestChannel(Enum):
    CHANNEL_1 = "channel-1"

    def __str__(self):
        return self.value


class TestSubdir(Enum):
    NOARCH = "noarch"
    LINUX_64 = "linux-64"

    def __str__(self):
        return self.value


class TestInput(
    Struct,
    frozen=True,
    forbid_unknown_fields=True,
):
    channels: TestChannel | list[TestChannel] | None = None
    subdirs: TestSubdir | list[TestSubdir] | None = None
    specs_to_add: str | list[str] | None = None
    prefix: str | list[str] | None = None
    history_specs: str | list[str] | None = None
    add_pip: bool = False
    ignore_pinned: bool | None = None
    pinned_packages: str | list[str] | None = None
    aggressive_update_packages: str | list[str] | None = None
    update_modifier: UpdateModifier | None = None


class TestOutput(
    Struct,
    frozen=True,
    forbid_unknown_fields=True,
):
    final_state: str | list[str] | None = None


class UnsatisfiableTestError(
    Struct,
    tag_field="exception",
    tag="UnsatisfiableError",
    frozen=True,
    forbid_unknown_fields=True,
):
    entries: str | list[str | list[str]]


class ResolvePackageNotFoundTestError(
    Struct,
    tag_field="exception",
    tag="ResolvePackageNotFound",
    frozen=True,
    forbid_unknown_fields=True,
):
    entries: str | list[str | list[str]]


class SpecsConfigurationConflictTestError(
    Struct,
    tag_field="exception",
    tag="SpecsConfigurationConflictError",
    frozen=True,
    forbid_unknown_fields=True,
):
    requested_specs: str | list[str | list[str]]
    pinned_specs: str | list[str | list[str]]


type TestError = (
    UnsatisfiableTestError
    | ResolvePackageNotFoundTestError
    | SpecsConfigurationConflictTestError
)


class SolveTestSpec(
    Struct,
    tag_field="kind",
    tag="solve",
    frozen=True,
    forbid_unknown_fields=True,
):
    name: str
    id: str
    provenance: str
    input: TestInput
    output: TestOutput
    test_function: str = "test_solve"


class UnsatisfiableTestSpec(
    Struct,
    tag_field="kind",
    tag="unsatisfiable",
    frozen=True,
    forbid_unknown_fields=True,
):
    name: str
    id: str
    provenance: str
    input: TestInput
    error: TestError
    test_function: str = "test_unsatisfiable"


type TestSpec = SolveTestSpec | UnsatisfiableTestSpec


class TestModule(Struct):
    tests: list[TestSpec]
