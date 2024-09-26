def test_empty(env, index_packages):
    env.repo_packages = index_packages
    assert env.install() == set()
