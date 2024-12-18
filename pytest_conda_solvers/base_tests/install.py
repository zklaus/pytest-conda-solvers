import re
import sys
from contextlib import contextmanager, nullcontext
from unittest.mock import patch

import pytest
from boltons.setutils import IndexedSet
from conda.base.context import conda_tests_ctxt_mgmt_def_pol
from conda.common.io import env_vars
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
from conda.plugins.virtual_packages import cuda
from conda.resolve import MatchSpec

from ..models import (
    ResolvePackageNotFoundTestError,
    SpecsConfigurationConflictTestError,
    TestInput,
    UnsatisfiableTestError,
)

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
        env_vars(
            {"CONDA_ADD_PIP_AS_PYTHON_DEPENDENCY": str(add_pip).lower()},
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
    def get_env_pair(raw_solver_input, name, join_str=None):
        var_name = f"CONDA_{name.upper()}"
        val = getattr(raw_solver_input, name)
        if isinstance(val, list):
            val = join_str.join(val)
        return var_name, str(val) if val is not None else None

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
    env_vars = {
        name: val
        for name, val in (
            get_env_pair(raw_solver_input, "pinned_packages", "&"),
            get_env_pair(raw_solver_input, "aggressive_update_packages", ","),
            get_env_pair(raw_solver_input, "auto_update_conda"),
            get_env_pair(raw_solver_input, "channel_priority"),
            get_env_pair(raw_solver_input, "override_cuda"),
        )
        if val is not None
    }
    bool_flags = ("ignore_pinned",)
    enum_flags = ("update_modifier",)
    flags = {
        flag: v
        for flag in bool_flags
        if (v := getattr(raw_solver_input, flag)) is not None
    } | {
        flag: v.value
        for flag in enum_flags
        if (v := getattr(raw_solver_input, flag)) is not None
    }
    return solver_input, env_vars, flags


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
    @contextmanager
    def _setup_solver(self, solver_backend, channel_server, tmpdir, test_input):
        solver_input, env, flags = prepare_solver_input(
            test_input,
            channel_server,
            "linux-64",
        )
        with (
            env_vars(
                env,
                stack_callback=conda_tests_ctxt_mgmt_def_pol,
            )
            if len(env) > 0
            else nullcontext()
        ):
            if test_input.set_sys_prefix:
                saved_sys_prefix = sys.prefix
                sys.prefix = tmpdir
            if "CONDA_OVERRIDE_CUDA" in env:
                cuda.cached_cuda_version.cache_clear()
            with get_solver(
                solver_backend,
                tmpdir,
                channel_server,
                **solver_input,
            ) as solver:
                yield solver, flags
            if test_input.set_sys_prefix:
                sys.prefix = saved_sys_prefix

    @pytest.mark.conda_solver_test
    def test_solve(self, env, tmpdir, solver_backend, test, channel_server):
        with self._setup_solver(solver_backend, channel_server, tmpdir, test.input) as (
            solver,
            flags,
        ):
            final_state = solver.solve_final_state(**flags)

        ref = add_base_url(
            channel_server.get_base_url(), "linux-64", test.output.final_state
        )
        assert sorted(list(convert_to_dist_str(final_state))) == sorted(list(ref))
        assert convert_to_dist_str(final_state) == ref

    @pytest.mark.conda_solver_test
    def test_solve_for_diff(self, env, tmpdir, solver_backend, test, channel_server):
        with self._setup_solver(
            solver_backend,
            channel_server,
            tmpdir,
            test.input,
        ) as (
            solver,
            flags,
        ):
            unlink_precs, link_precs = solver.solve_for_diff(**flags)

        unlink_ref = add_base_url(
            channel_server.get_base_url(), "linux-64", test.output.unlink_precs
        )
        link_ref = add_base_url(
            channel_server.get_base_url(), "linux-64", test.output.link_precs
        )
        assert sorted(list(convert_to_dist_str(unlink_precs))) == sorted(
            list(unlink_ref)
        )
        assert convert_to_dist_str(unlink_precs) == unlink_ref
        assert sorted(list(convert_to_dist_str(link_precs))) == sorted(list(link_ref))
        assert convert_to_dist_str(link_precs) == link_ref

    @pytest.mark.conda_solver_test
    def test_unsatisfiable(self, env, tmpdir, solver_backend, test, channel_server):
        error_info = prepare_error_information(test.error)
        with (
            self._setup_solver(solver_backend, channel_server, tmpdir, test.input) as (
                solver,
                flags,
            ),
            pytest.raises(error_info["exception"]) as exc_info,
        ):
            solver.solve_final_state(**flags)

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
