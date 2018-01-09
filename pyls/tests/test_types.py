# -*- coding: utf-8 -*-

import numpy as np
import pytest
import pyls

brain    = 1000
behavior = 100
subj     = 20
n_perm   = 50
n_boot   = 10
n_split  = 5
seed     = 1234

np.random.rand(seed)
behavmat  = np.random.rand(subj, behavior)
braindata = np.random.rand(subj, brain)
grouping  = np.hstack([[1] * int(np.ceil(subj / 2)),
                       [2] * int(np.floor(subj / 2))])

attrs = ['X', 'Y', 'groups',
         'U', 'd', 'V',
         'd_pvals', 'd_kaiser', 'd_varexp',
         'U_bci', 'V_bci',
         'U_bsr', 'V_bsr',
         'U_sig', 'V_sig']


def test_behavioral_pls():
    o1 = pyls.types.BehavioralPLS(braindata, behavmat,
                                  n_perm=n_perm, n_boot=n_boot,
                                  n_split=None, seed=seed)
    o2 = pyls.types.BehavioralPLS(behavmat, braindata,
                                  n_perm=n_perm, n_boot=n_boot,
                                  n_split=None, seed=seed+1)
    for f in attrs: assert hasattr(o1, f)

    with pytest.raises(ValueError):
        pyls.types.BehavioralPLS(behavmat[:, 0], braindata)
    with pytest.raises(ValueError):
        pyls.types.BehavioralPLS(behavmat[:, 0], braindata[:, 0])
    with pytest.raises(ValueError):
        pyls.types.BehavioralPLS(behavmat[:-1], braindata)

def test_group_behavioral_pls():
    pyls.types.BehavioralPLS(braindata, behavmat, grouping=grouping,
                             n_perm=n_perm, n_boot=n_boot,
                             n_split=None,
                             seed=seed)


def test_behavioral_split_half():
    split_attrs = ['ucorr', 'vcorr', 'u_pvals', 'v_pvals']

    o1 = pyls.types.BehavioralPLS(braindata, behavmat,
                                  n_perm=n_perm, n_boot=n_boot,
                                  n_split=n_split, seed=seed)
    o2 = pyls.types.BehavioralPLS(braindata, behavmat, grouping=grouping,
                                  n_perm=n_perm, n_boot=n_boot,
                                  n_split=n_split, seed=seed)
    for f in split_attrs: assert hasattr(o1, f)


def test_mean_center_pls():
    o1 = pyls.types.MeanCenteredPLS(braindata, grouping,
                                    n_perm=n_perm, n_boot=n_boot,
                                    n_split=None, seed=seed)
    o2 = pyls.types.MeanCenteredPLS(braindata, grouping,
                                    n_perm=n_perm, n_boot=n_boot,
                                    n_split=n_split, seed=seed+1)
