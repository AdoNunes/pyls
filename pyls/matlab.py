# -*- coding: utf-8 -*-

import numpy as np
import scipy.io as sio
from pyls.base import PLSResults

_result_mapping = (
    ('Y', 'stacked_behavdata'),
    ('groups', 'num_subj_lst'),
    ('n_cond', 'num_conditions'),
    ('n_perm', ('perm_result', 'num_perm')),
    ('n_boot', ('boot_result', 'num_boot')),
    ('n_split', ('perm_splithalf', 'num_split')),
    ('ci', ('boot_result', 'clim')),
    ('mean_centering', ('other_input', 'meancentering_type')),
    ('n_proc', ''),
    ('seed', '')
)


def coerce_void(value):
    """
    Converts ``value`` to ``value.dtype``

    Parameters
    ----------
    value : array_like

    Returns
    -------
    value : dtype
        ``Value`` coerced to ``dtype``
    """
    if np.squeeze(value).ndim == 0:
        return value.dtype.type(value.squeeze())
    else:
        return np.squeeze(value)


def import_matlab_result(fname):
    """
    Imports ``fname`` PLS result from Matlab

    Parameters
    ----------
    fname : str
        Filepath to output mat file obtained by Matlab PLS toolbox. Should
        contain at least a result "struct".

    Returns
    -------
    results : pyls.base.PLSResults
        Matlab results in a Python-friendly format
    """

    def get_labels(fields):
        labels = [k for k, v in sorted(fields.items(),
                                       key=lambda x: x[-1][-1])]
        return labels

    # load mat file using scipy.io
    matfile = sio.loadmat(fname)
    # if 'result' key is missing then consider a malformed input
    try:
        result = matfile.get('result')[0, 0]
    except (IndexError, TypeError) as e:
        raise ValueError('Cannot get result struct from provided mat file')

    # convert result structure to a dictionary using dtypes as keys
    labels = get_labels(result.dtype.fields)
    result = {labels[n]: value for n, value in enumerate(result)}

    # convert sub-structures to dictionaries using dtypes as keys
    structs = ['boot_result', 'perm_result', 'perm_splithalf', 'other_input']
    for attr in structs:
        if result.get(attr) is not None:
            labels = get_labels(result[attr].dtype.fields)
            result[attr] = {labels[n]: coerce_void(value) for n, value
                            in enumerate(result[attr][0, 0])}

    # squeeze all the values so they're a bit more interpretable
    for key, val in result.items():
        if isinstance(val, np.ndarray):
            result[key] = coerce_void(val)

    # add an inputs dictionary baesd on ``_result_mapping``
    try:
        result['inputs'] = dict(X=np.vstack(matfile.get('datamat_lst')[:, 0]))
    except TypeError:
        result['inputs'] = dict()
    for key, val in _result_mapping:
        if isinstance(val, tuple):
            result['inputs'][key] = result.get(val[0], {}).get(val[1])
        else:
            result['inputs'][key] = result.get(val)

    # pack it into a pyls.base.PLSResults class instance for attribute access
    return PLSResults(**result)


def comp_python_matlab(python, matlab, atol=1e-4):
    """
    Compares ``python`` and ``matlab`` PLS results

    Parameters
    ----------
    python : array_like
    matlab : array_like
    atol : float, optional
        Tolerance for differences between ``python`` and ``matlab``

    Returns
    -------
    close : bool
        Whether the input arrays are close within ``atol``
    maxdiff : float
        Maximum absolute difference between input arrays
    """

    # signs may be flipped so just take difference of absolute values
    diff = np.abs(python) - np.abs(matlab)
    # the last LV is always screwed up so ignore it
    if diff.ndim > 1:
        diff = diff[:, :-1]
    else:
        diff = diff[:-1]

    return np.allclose(diff, 0, atol=atol), np.abs(diff).max()
