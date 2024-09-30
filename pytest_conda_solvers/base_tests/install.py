import pytest


class TestBasic:
    @pytest.mark.conda_solver_test
    def test_empty(self, env, index_packages):
        env.repo_packages = index_packages
        assert env.install() == set()
