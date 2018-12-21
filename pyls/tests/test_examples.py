# -*- coding: utf-8 -*-

import os
import pytest
import pyls

DATASETS = [
    'mirchi_2018', 'whitaker_vertes_2016'
]


def test_available_datasets():
    # make sure we get a list of strings when called with no arguments
    avail = pyls.examples.available_datasets()
    assert isinstance(avail, list)
    assert all([isinstance(f, str) for f in avail])

    # check that we get all expected datasets back
    assert len(set(DATASETS) - set(avail)) == 0

    # check that we can supply dataset names to function to confirm validity
    for f in DATASETS:
        assert f == pyls.examples.available_datasets(f)

    # check that providing non-valid dataset name errors
    with pytest.raises(ValueError):
        pyls.examples.available_datasets('thisisnotadataset')
        pyls.exampleipyts.available_datasets(10)


@pytest.mark.parametrize(('dataset', 'keys'), [
    ('mirchi_2018', [
        'description', 'reference', 'urls', 'X', 'Y',
        'n_perm', 'n_boot', 'test_size', 'test_split', 'parcellation'
    ]),
    ('whitaker_vertes_2016', [
        'description', 'reference', 'urls', 'X', 'Y', 'n_perm'
    ])
])
def test_query_dataset(dataset, keys):
    # check that default return string (description)
    assert isinstance(pyls.examples.query_dataset(dataset), str)
    # check that supplying None returns all available keys
    assert pyls.examples.query_dataset(dataset, None) == keys
    # check that all valid keys return something
    for k in keys:
        assert pyls.examples.query_dataset(dataset, k) is not None
    # check nonsense keys
    for k in ['notakey', 10, 20.5132]:
        with pytest.raises(KeyError):
            pyls.examples.query_dataset(dataset, k)


def test_get_data_dir(tmpdir):
    # check that default (no arguments) returns valid default directory
    data_dir = pyls.examples.datasets._get_data_dir()
    assert isinstance(data_dir, str)
    assert os.path.exists(data_dir)
    assert os.path.basename(data_dir) == 'pyls-data'

    # check supplying directory returns same directory
    assert pyls.examples.datasets._get_data_dir(tmpdir) == str(tmpdir)
    assert os.path.exists(str(tmpdir))

    # check that _get_data_dir() pulls from environmental variable correctly
    os.environ['PYLS_DATA'] = str(tmpdir)
    assert pyls.examples.datasets._get_data_dir() == str(tmpdir)


@pytest.mark.parametrize(('dataset', 'keys'), [
    ('mirchi_2018', ['X', 'Y', 'n_perm', 'n_boot', 'test_size', 'test_split']),
    ('whitaker_vertes_2016', ['X', 'Y', 'n_perm'])
])
def test_load_dataset(tmpdir, dataset, keys):
    ds = pyls.examples.load_dataset(dataset, tmpdir)
    assert isinstance(ds, pyls.structures.PLSInputs)
    for k in keys:
        assert hasattr(ds, k) and getattr(ds, k) is not None
