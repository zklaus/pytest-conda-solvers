from contextlib import contextmanager
from unittest.mock import patch

import pytest
from boltons.setutils import IndexedSet
from conda.base.context import conda_tests_ctxt_mgmt_def_pol
from conda.common.io import env_var
from conda.core.prefix_data import PrefixData
from conda.history import History
from conda.models.channel import Channel
from conda.models.records import PackageRecord, PrefixRecord
from conda.resolve import MatchSpec

from ..server import ChannelServer


@contextmanager
def get_solver(
    solver_backend,
    tmpdir,
    channel_server,
    channel_names,
    subdirs,
    specs_to_add=(),
    specs_to_remove=(),
    prefix_records=(),
    history_specs=(),
):
    channels = [
        Channel(channel_server.get_channel_url(channel_name))
        for channel_name in channel_names
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
            str(False).lower(),
            stack_callback=conda_tests_ctxt_mgmt_def_pol,
        ),
    ):
        yield solver_backend(tmpdir, channels, subdirs, specs_to_add=specs_to_add)


def convert_to_dist_str(state: IndexedSet[PackageRecord]) -> IndexedSet[str]:
    return IndexedSet(prec.dist_str() for prec in state)


class TestBasic:
    @pytest.mark.conda_solver_test
    def test_empty(self, env, test, channel_server: ChannelServer):
        assert True
        # env.repo_packages = index_packages
        # assert env.install() == set()

    @pytest.mark.conda_solver_test
    def test_solve(self, env, tmpdir, solver_backend, test, channel_server):
        specs = (MatchSpec("numpy"),)

        with get_solver(
            solver_backend,
            tmpdir,
            channel_server,
            ["channel-1"],
            ["linux-64"],
            specs,
        ) as solver:
            final_state = solver.solve_final_state()
            prefix = f"{channel_server.get_channel_url("channel-1")}/linux-64"
            order = (
                f"{prefix}::openssl-1.0.1c-0",
                f"{prefix}::readline-6.2-0",
                f"{prefix}::sqlite-3.7.13-0",
                f"{prefix}::system-5.8-1",
                f"{prefix}::tk-8.5.13-0",
                f"{prefix}::zlib-1.2.7-0",
                f"{prefix}::python-3.3.2-0",
                f"{prefix}::numpy-1.7.1-py33_0",
            )
            assert convert_to_dist_str(final_state) == order

        specs_to_add = (MatchSpec("python=2"),)
        with get_solver(
            solver_backend,
            tmpdir,
            channel_server,
            ["channel-1"],
            ["linux-64"],
            specs_to_add=specs_to_add,
            prefix_records=final_state,
            history_specs=specs,
        ) as solver:
            final_state = solver.solve_final_state()
            prefix = f"{channel_server.get_channel_url("channel-1")}/linux-64"
            order = (
                f"{prefix}::openssl-1.0.1c-0",
                f"{prefix}::readline-6.2-0",
                f"{prefix}::sqlite-3.7.13-0",
                f"{prefix}::system-5.8-1",
                f"{prefix}::tk-8.5.13-0",
                f"{prefix}::zlib-1.2.7-0",
                f"{prefix}::python-2.7.5-0",
                f"{prefix}::numpy-1.7.1-py27_0",
            )
            assert convert_to_dist_str(final_state) == order
