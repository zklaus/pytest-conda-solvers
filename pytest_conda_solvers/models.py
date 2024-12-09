from enum import Enum

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


class TestInput(Struct):
    channels: TestChannel | list[TestChannel] | None = None
    subdirs: TestSubdir | list[TestSubdir] | None = None
    specs_to_add: str | list[str] | None = None
    prefix: str | list[str] | None = None
    history_specs: str | list[str] | None = None
    add_pip: bool = False
    pinned_packages: str | list[str] = []


class TestOutput(Struct):
    final_state: str | list[str] | None = None


class UnsatisfiableTestError(Struct, tag_field="exception", tag="UnsatisfiableError"):
    entries: str | list[str | list[str]]


class ResolvePackageNotFoundTestError(
    Struct, tag_field="exception", tag="ResolvePackageNotFound"
):
    entries: str | list[str | list[str]]


class SpecsConfigurationConflictTestError(
    Struct, tag_field="exception", tag="SpecsConfigurationConflictError"
):
    requested_specs: str | list[str | list[str]]
    pinned_specs: str | list[str | list[str]]


type TestError = (
    UnsatisfiableTestError
    | ResolvePackageNotFoundTestError
    | SpecsConfigurationConflictTestError
)


class SolveTestSpec(Struct, tag_field="kind", tag="solve"):
    name: str
    id: str
    input: TestInput
    output: TestOutput
    test_function: str = "test_solve"


class UnsatisfiableTestSpec(Struct, tag_field="kind", tag="unsatisfiable"):
    name: str
    id: str
    input: TestInput
    error: TestError
    test_function: str = "test_unsatisfiable"


type TestSpec = SolveTestSpec | UnsatisfiableTestSpec


class TestModule(Struct):
    tests: list[TestSpec]
