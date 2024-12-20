from enum import Enum

from conda.core.solve import UpdateModifier
from conda.models.enums import PackageType
from conda.models.match_spec import MatchSpec
from msgspec import Struct, field


class TestChannel(Enum):
    CHANNEL_1 = "channel-1"
    CHANNEL_2 = "channel-2"
    CHANNEL_4 = "channel-4"
    CONDA_FORMAT_REPO = "conda_format_repo"
    TEST = "test"

    def __str__(self):
        return self.value


class TestSubdir(Enum):
    NOARCH = "noarch"
    LINUX_64 = "linux-64"
    CONDA_TEST = "conda-test"

    def __str__(self):
        return self.value


class ChannelPriority(Enum):
    STRICT = "strict"
    FLEXIBLE = "flexible"
    DISABLED = "disabled"

    def __str__(self):
        return self.value


class PrefixRecord(
    Struct,
    tag_field="record_type",
    tag="prefix",
    frozen=True,
    forbid_unknown_fields=True,
    kw_only=True,
):
    package_type: PackageType | None = None
    name: str
    version: str
    channel: str
    subdir: str
    fn: str
    build: str = "0"
    build_number: int = 0
    paths_data: list[str] | None = None
    files: list[str] | None = None
    depends: list[str] = []
    constrains: list[str] = []


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
    solution_records: PrefixRecord | list[PrefixRecord] | None = None
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


class Constriction(
    Struct,
    frozen=True,
    forbid_unknown_fields=True,
):
    package: str
    constricting_match_spec: str


class DeterminingConstrictingSpecsTestOutput(
    Struct,
    frozen=True,
    forbid_unknown_fields=True,
):
    constrictions: list[Constriction] | None = None

    def constrictions_as_list(self):
        return (
            None
            if self.constrictions is None
            else [
                (c.package, MatchSpec(c.constricting_match_spec))
                for c in self.constrictions
            ]
        )


class DetermineConstrictingSpecsTestSpec(
    Struct,
    tag_field="kind",
    tag="determine_constricting_specs",
    frozen=True,
    forbid_unknown_fields=True,
):
    name: str
    id: str
    provenance: str
    input: TestInput
    output: DeterminingConstrictingSpecsTestOutput
    test_function: str = "test_determine_constricting_specs"


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


type TestSpec = (
    SolveTestSpec
    | SolveForDiffTestSpec
    | DetermineConstrictingSpecsTestSpec
    | UnsatisfiableTestSpec
)


class TestModule(Struct):
    tests: list[TestSpec]
