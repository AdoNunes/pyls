#!/usr/bin/env python

import pytest
import numpy as np
import pyls

brain    = 1000
behavior = 100
comp     = 20
n_perm   = 50
n_boot   = 10
n_split  = 5
groups   = 2

behavmat  = np.random.rand(comp, behavior)
braindata = np.random.rand(comp, brain)

groupbehavmat  = np.random.rand(comp, behavior, groups)
groupbraindata = np.random.rand(comp, brain, groups)

attrs = ['U', 'd', 'V',
         'd_pvals', 'd_kaiser', 'd_varexp',
         'U_bci', 'V_bci',
         'U_bsr', 'V_bsr',
         'U_sig', 'V_sig']


def test_behavioral_pls():
    o1 = pyls.types.behavioral_pls(braindata, behavmat,
                                   n_perm=n_perm, n_boot=n_boot,
                                   verbose=False)
    _ = pyls.types.behavioral_pls(behavmat, braindata,
                                  n_perm=n_perm, n_boot=n_boot,
                                  verbose=False)
    for f in attrs: assert hasattr(o1, f)

    with pytest.raises(ValueError):
        pyls.types.behavioral_pls(behavmat[:, 0], braindata,
                                  verbose=False)
    with pytest.raises(ValueError):
        pyls.types.behavioral_pls(behavmat[:, 0], braindata[:, 0],
                                  verbose=False)


def test_group_behavioral_pls():
    pyls.types.behavioral_pls(groupbraindata, groupbehavmat,
                              n_perm=n_perm, n_boot=n_boot,
                              verbose=False)

    onecol = np.stack([np.ones([comp, 1]), np.ones([comp, 1]) * 2], axis=2)

    pyls.types.behavioral_pls(groupbraindata, onecol,
                              n_perm=n_perm, n_boot=n_boot,
                              verbose=False)


def test_behavioral_split_half():
    split_attrs = ['ucorr', 'vcorr', 'u_pvals', 'v_pvals']

    o1 = pyls.types.behavioral_pls(braindata, behavmat,
                                   n_perm=n_perm, n_boot=n_boot,
                                   n_split=n_split,
                                   verbose=False)
    for f in split_attrs: assert hasattr(o1, f)
