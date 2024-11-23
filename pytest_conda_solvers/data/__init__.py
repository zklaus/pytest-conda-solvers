import json
import os
import sys

from conda.models.channel import Channel
from conda.core.subdir_data import SubdirData

if sys.version_info < (3, 12):
    from importlib_resources import files
else:
    from importlib.resources import files


# This package contains datafiles converted from the original index*.json files with
# jq '.|to_entries|map(select((.value.subdir=="noarch" or (.value | has("noarch")))))|from_entries' index4.json >channel-4_noarch.json
# jq '.|to_entries|map(select((.value.subdir=="noarch" or (.value | has("noarch")))|not))|from_entries' index4.json >channel-4_non-noarch.json


def load_data_file(filename):
    with open(files().joinpath(filename)) as ifh:
        data = json.load(ifh)
    return data


def _get_index_r_base(
    json_filename_or_packages,
    channel_name,
    subdir,
    arch_name,
    platform,
    add_pip=False,
    merge_noarch=False,
):
    if isinstance(json_filename_or_packages, (str, os.PathLike)):
        all_packages = load_data_file(json_filename_or_packages)
    elif isinstance(json_filename_or_packages, dict):
        all_packages = json_filename_or_packages
    else:
        raise ValueError("'json_filename_or_data' must be path-like or dict")

    if merge_noarch:
        packages = {subdir: all_packages}
    else:
        packages = {subdir: {}, "noarch": {}}
        for key, pkg in all_packages.items():
            if pkg.get("subdir") == "noarch" or pkg.get("noarch"):
                packages["noarch"][key] = pkg
            else:
                packages[subdir][key] = pkg

    subdir_datas = []
    channels = []
    for subchannel, subchannel_pkgs in packages.items():
        repodata = {
            "info": {
                "subdir": subchannel,
                "arch": arch_name,
                "platform": platform,
            },
            "packages": subchannel_pkgs,
        }

        channel = Channel(f"https://conda.anaconda.org/{channel_name}/{subchannel}")
        channels.append(channel)
        sd = SubdirData(channel)
        subdir_datas.append(sd)
        # with env_var(
        #     "CONDA_ADD_PIP_AS_PYTHON_DEPENDENCY",
        #     str(add_pip).lower(),
        #     stack_callback=conda_tests_ctxt_mgmt_def_pol,
        # ):
        #     sd._process_raw_repodata_str(json.dumps(repodata))
        sd._process_raw_repodata_str(json.dumps(repodata))
        sd._loaded = True
        SubdirData._cache_[channel.url(with_credentials=True)] = sd
        # _patch_for_local_exports(channel_name, sd)

    # this is for the classic solver only,
    # which is fine with a single collapsed index
    index = {}
    for sd in subdir_datas:
        index.update({prec: prec for prec in sd.iter_records()})
    # r = Resolve(index, channels=channels)

    # return index, r
    return index
