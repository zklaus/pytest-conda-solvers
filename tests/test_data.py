from pytest_conda_solvers import data


def test_load_data_file():
    index = data.load_data_file("index.json")
    assert len(index) == 1149
    random_entry_key = "numpy-1.7.0rc1-py33_p0.tar.bz2"
    random_entry_value = {
        "build": "py33_p0",
        "build_number": 0,
        "depends": [
            "mkl 10.3",
            "nose",
            "python 3.3*",
        ],
        "features": "mkl",
        "md5": "4976525dda67fb55578b8763dd2c04b1",
        "name": "numpy",
        "pub_date": "2013-01-29",
        "requires": [
            "mkl 10.3",
            "nose 1.2.1",
            "python 3.3",
        ],
        "version": "1.7.0rc1",
    }
    assert index[random_entry_key] == random_entry_value
