import re
from contextlib import contextmanager
from unittest.mock import patch

import pytest
from boltons.setutils import IndexedSet
from conda.base.context import conda_tests_ctxt_mgmt_def_pol
from conda.common.io import env_var
from conda.core.prefix_data import PrefixData
from conda.core.subdir_data import SubdirData
from conda.exceptions import (
    ResolvePackageNotFound,
    SpecsConfigurationConflictError,
    UnsatisfiableError,
)
from conda.history import History
from conda.models.channel import Channel
from conda.models.records import PackageRecord, PrefixRecord
from conda.resolve import MatchSpec

from ..models import (
    ResolvePackageNotFoundTestError,
    SpecsConfigurationConflictTestError,
    TestInput,
    UnsatisfiableTestError,
)
from ..server import ChannelServer

EXCEPTION_MAPPING = {
    ResolvePackageNotFoundTestError: ResolvePackageNotFound,
    SpecsConfigurationConflictTestError: SpecsConfigurationConflictError,
    UnsatisfiableTestError: UnsatisfiableError,
}


@contextmanager
def get_solver(
    solver_backend,
    tmpdir,
    channel_server,
    channels,
    subdirs,
    specs_to_add=(),
    specs_to_remove=(),
    prefix_records=(),
    history_specs=(),
    add_pip=False,
):
    channels = [
        Channel(channel_server.get_channel_url(channel_name))
        for channel_name in channels
    ]
    tmpdir = tmpdir.strpath
    pd = PrefixData(tmpdir)
    pd._PrefixData__prefix_records = {
        rec.name: PrefixRecord.from_objects(rec) for rec in prefix_records
    }
    spec_map = {spec.name: spec for spec in history_specs}
    with (
        patch.object(History, "get_requested_specs_map", return_value=spec_map),
        env_var(
            "CONDA_ADD_PIP_AS_PYTHON_DEPENDENCY",
            str(add_pip).lower(),
            stack_callback=conda_tests_ctxt_mgmt_def_pol,
        ),
    ):
        if add_pip:
            SubdirData._cache_.clear()
        try:
            yield solver_backend(tmpdir, channels, subdirs, specs_to_add=specs_to_add)
        finally:
            if add_pip:
                SubdirData._cache_.clear()


def convert_to_dist_str(state: IndexedSet[PackageRecord]) -> IndexedSet[str]:
    return IndexedSet(prec.dist_str() for prec in state)


def ensure_str_tuple(entry):
    if entry is None:
        return ()
    if isinstance(entry, str):
        return (entry,)
    if isinstance(entry, list):
        return tuple(str(e) for e in entry)
    return (str(entry),)


def ensure_tuple(entry):
    if entry is None:
        return ()
    if isinstance(entry, list):
        return tuple(entry)
    return (entry,)


def add_base_url(base_url, arch, dist_strs):
    return type(dist_strs)(
        f"{base_url}/{dist_str.replace('${{ arch }}', arch)}" for dist_str in dist_strs
    )


def package_record_from_dist_str(dist_str):
    DIST_STR_RE = re.compile(
        "(?P<channel>.*)/(?P<subdir>.*)::(?P<name>.*)-(?P<version>.*)-(?P<build>.*?_?(?P<build_number>[0-9]+))"
    )
    spec = DIST_STR_RE.fullmatch(dist_str).groupdict()
    spec["build_number"] = int(spec["build_number"])
    return PackageRecord.from_objects(**spec)


def prepare_solver_input(raw_solver_input: TestInput, channel_server, arch):
    solver_input = {}
    for simple_key in ("channels", "subdirs"):
        solver_input[simple_key] = ensure_str_tuple(
            getattr(raw_solver_input, simple_key)
        )
    solver_input["prefix_records"] = tuple(
        package_record_from_dist_str(dist_str)
        for dist_str in add_base_url(
            channel_server.get_base_url(),
            arch,
            ensure_str_tuple(raw_solver_input.prefix),
        )
    )
    for spec_key in ("specs_to_add", "history_specs"):
        solver_input[spec_key] = tuple(
            MatchSpec(s) for s in ensure_str_tuple(getattr(raw_solver_input, spec_key))
        )
    solver_input["add_pip"] = raw_solver_input.add_pip
    pins = "&".join(raw_solver_input.pinned_packages)
    return solver_input, pins


def prepare_error_information(error):
    exception_class = EXCEPTION_MAPPING[type(error)]
    error_info = {
        "exception": exception_class,
    }
    if exception_class in (UnsatisfiableError, ResolvePackageNotFound):
        error_info["entries"] = set(
            tuple(map(MatchSpec, ensure_tuple(entries))) for entries in error.entries
        )
        assert len(error.entries) == len(error_info["entries"])
    elif exception_class == SpecsConfigurationConflictError:
        error_info["requested_specs"] = ensure_str_tuple(error.requested_specs)
        error_info["pinned_specs"] = ensure_str_tuple(error.pinned_specs)
    return error_info


class TestBasic:
    @pytest.mark.conda_solver_test
    def test_empty(self, env, test, channel_server: ChannelServer):
        assert True
        # env.repo_packages = index_packages
        # assert env.install() == set()

    @pytest.mark.conda_solver_test
    def test_solve(self, env, tmpdir, solver_backend, test, channel_server):
        solver_input, pins = prepare_solver_input(
            test.input, channel_server, "linux-64"
        )
        with env_var(
            "CONDA_PINNED_PACKAGES",
            pins,
            stack_callback=conda_tests_ctxt_mgmt_def_pol,
        ):
            with get_solver(
                solver_backend,
                tmpdir,
                channel_server,
                **solver_input,
            ) as solver:
                final_state = solver.solve_final_state()

        ref = add_base_url(
            channel_server.get_base_url(), "linux-64", test.output.final_state
        )
        assert sorted(list(convert_to_dist_str(final_state))) == sorted(list(ref))
        assert convert_to_dist_str(final_state) == ref

    @pytest.mark.conda_solver_test
    def test_unsatisfiable(self, env, tmpdir, solver_backend, test, channel_server):
        solver_input, pins = prepare_solver_input(
            test.input,
            channel_server,
            "linux-64",
        )
        error_info = prepare_error_information(test.error)
        with env_var(
            "CONDA_PINNED_PACKAGES",
            pins,
            stack_callback=conda_tests_ctxt_mgmt_def_pol,
        ):
            with (
                get_solver(
                    solver_backend,
                    tmpdir,
                    channel_server,
                    **solver_input,
                ) as solver,
                pytest.raises(error_info["exception"]) as exc_info,
            ):
                solver.solve_final_state()

        if exc_info.type == UnsatisfiableError:
            assert set(exc_info.value.unsatisfiable) == set(error_info["entries"])
        elif exc_info.type == ResolvePackageNotFound:
            assert set((exc_info.value.bad_deps,)) == set(error_info["entries"])
        elif exc_info.type == SpecsConfigurationConflictError:
            kwargs = exc_info.value._kwargs
            assert set(kwargs["requested_specs"]) == set(error_info["requested_specs"])
            assert set(kwargs["pinned_specs"]) == set(error_info["pinned_specs"])
        else:
            raise exc_info.value
