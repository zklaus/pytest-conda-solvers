import collections
import json
from pathlib import Path

from conda.models.channel import Channel


def default_subdir():
    return "linux-64"


def package_string(record):
    return f"{record.channel.name}::{record.name}-{record.version}-{record.build}"


def package_string_set(packages):
    """Transforms package container in package string set."""
    return {package_string(record) for record in packages}


def package_dict(packages):
    """Transforms package container into a dictionary."""
    return {record.name: record for record in packages}


class SimpleEnvironment:
    """Helper environment object."""

    REPO_DATA_KEYS = (
        "build",
        "build_number",
        "depends",
        "license",
        "md5",
        "name",
        "sha256",
        "size",
        "subdir",
        "timestamp",
        "version",
        "track_features",
        "features",
    )

    def __init__(self, path, solver_class, subdirs):
        self._path = Path(path)
        self._prefix_path = self._path / "prefix"
        self._channels_path = self._path / "channels"
        self._solver_class = solver_class
        self.subdirs = subdirs
        self.installed_packages = []
        # if repo_packages is a list, the packages will be put in a `test` channel
        # if it is a dictionary, it the keys are the channel name and the value
        # the channel packages
        self.repo_packages: list[str] | dict[str, list[str]] = []

    def solver(self, add, remove):
        """Writes ``repo_packages`` to the disk and creates a solver instance."""
        channels = []
        self._write_installed_packages()
        for channel_name, packages in self._channel_packages.items():
            self._write_repo_packages(channel_name, packages)
            channel = Channel(str(self._channels_path / channel_name))
            channels.append(channel)
        return self._solver_class(
            prefix=self._prefix_path,
            subdirs=self.subdirs,
            channels=channels,
            specs_to_add=add,
            specs_to_remove=remove,
        )

    def solver_transaction(self, add=(), remove=(), as_specs=False):
        packages = self.solver(add=add, remove=remove).solve_final_state()
        if as_specs:
            return packages
        return package_string_set(packages)

    def install(self, *specs, as_specs=False):
        return self.solver_transaction(add=specs, as_specs=as_specs)

    def remove(self, *specs, as_specs=False):
        return self.solver_transaction(remove=specs, as_specs=as_specs)

    @property
    def _channel_packages(self):
        """Helper that unfolds the ``repo_packages`` into a dictionary."""
        if isinstance(self.repo_packages, dict):
            return self.repo_packages
        return {"test": self.repo_packages}

    def _package_data(self, record):
        """Turn record into data, to be written in the JSON environment/repo files."""
        data = {
            key: value
            for key, value in vars(record).items()
            if key in self.REPO_DATA_KEYS
        }
        if "subdir" not in data:
            data["subdir"] = default_subdir()
        return data

    def _write_installed_packages(self):
        if not self.installed_packages:
            return
        conda_meta = self._prefix_path / "conda-meta"
        conda_meta.mkdir(exist_ok=True, parents=True)
        # write record files
        for record in self.installed_packages:
            record_path = (
                conda_meta / f"{record.name}-{record.version}-{record.build}.json"
            )
            record_data = self._package_data(record)
            record_data["channel"] = record.channel.name
            record_path.write_text(json.dumps(record_data))
        # write history file
        history_path = conda_meta / "history"
        history_path.write_text(
            "\n".join(
                (
                    "==> 2000-01-01 00:00:00 <==",
                    *map(package_string, self.installed_packages),
                )
            )
        )

    def _write_repo_packages(self, channel_name, packages):
        """Write packages to the channel path."""
        # build package data
        package_data = collections.defaultdict(dict)
        for record in packages:
            package_data[record.subdir][record.fn] = self._package_data(record)
        # write repodata
        assert set(self.subdirs).issuperset(set(package_data.keys()))
        for subdir in self.subdirs:
            subdir_path = self._channels_path / channel_name / subdir
            subdir_path.mkdir(parents=True, exist_ok=True)
            subdir_path.joinpath("repodata.json").write_text(
                json.dumps(
                    {
                        "info": {
                            "subdir": subdir,
                        },
                        "packages": package_data.get(subdir, {}),
                    }
                )
            )
