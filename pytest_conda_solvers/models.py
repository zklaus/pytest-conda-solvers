from enum import Enum

from conda.core.solve import UpdateModifier
from msgspec import Struct, field


class TestChannel(Enum):
    CHANNEL_1 = "channel-1"
    CHANNEL_2 = "channel-2"
    CHANNEL_4 = "channel-4"

    def __str__(self):
        return self.value


class TestSubdir(Enum):
    NOARCH = "noarch"
    LINUX_64 = "linux-64"

    def __str__(self):
        return self.value


class ChannelPriority(Enum):
    STRICT = "strict"
    FLEXIBLE = "flexible"
    DISABLED = "disabled"

    def __str__(self):
        return self.value


class TestInput(
    Struct,
    frozen=True,
    forbid_unknown_fields=True,
):
    channels: TestChannel | list[TestChannel] | None = None
    subdirs: TestSubdir | list[TestSubdir] = field(
        default_factory=lambda: ["linux-64", "noarch"]
    )
    specs_to_add: str | list[str] | None = None
    prefix: str | list[str] | None = None
    history_specs: str | list[str] | None = None
    add_pip: bool = False
    ignore_pinned: bool | None = None
    pinned_packages: str | list[str] | None = None
    aggressive_update_packages: str | list[str] | None = None
    auto_update_conda: bool | None = None
    update_modifier: UpdateModifier | None = None
    channel_priority: ChannelPriority | None = None
    set_sys_prefix: bool | None = None
    override_cuda: str | None = None
    override_glibc: str | None = None


class TestOutput(
    Struct,
    frozen=True,
    forbid_unknown_fields=True,
):
    final_state: str | list[str] | None = None


class DiffTestOutput(
    Struct,
    frozen=True,
    forbid_unknown_fields=True,
):
    unlink_precs: str | list[str] | None = None
    link_precs: str | list[str] | None = None


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


class SolveForDiffTestSpec(
    Struct,
    tag_field="kind",
    tag="solve_for_diff",
    frozen=True,
    forbid_unknown_fields=True,
):
    name: str
    id: str
    provenance: str
    input: TestInput
    output: DiffTestOutput
    test_function: str = "test_solve_for_diff"


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


type TestSpec = SolveTestSpec | SolveForDiffTestSpec | UnsatisfiableTestSpec


class TestModule(Struct):
    tests: list[TestSpec]
