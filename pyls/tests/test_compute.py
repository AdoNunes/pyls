#!/usr/bin/env python

import pytest
import numpy as np
import pyls

brain    = 100
behavior = 50
comp     = 20
n_perm   = 10
n_boot   = 5
groups   = 2

X = np.random.rand(comp, brain)
Y = np.random.rand(comp, behavior)


def test_svd():
    U, d, V = pyls.compute.svd(X, Y, comp)
    assert d.shape == (comp, comp)
    assert U.shape == (behavior, comp)
    assert V.shape == (brain, comp)

    U2, d2, V2 = pyls.compute.svd(X, Y)
    assert np.allclose(U, U2)
    assert np.allclose(d, d2)
    assert np.allclose(V, V2)

    with pytest.raises(ValueError):
        pyls.compute.svd(np.random.rand(20, 10), np.random.rand(20, 100), comp)

    Xc, Yc = X.copy(), Y.copy()
    Xc[:, 10], Yc[:, 10] = 0, 0
    U2, d2, V2 = pyls.compute.svd(Xc, Yc, comp)


def test_serial_permute():
    U, d, V = pyls.compute.svd(X, Y, comp)

    perms = pyls.compute.serial_permute(X, Y, comp, U, n_perm=n_perm)
    assert perms.shape == (n_perm, comp)
    pyls.compute.serial_permute(Y, X, comp, U, n_perm=n_perm)

    pvals = pyls.compute.perm_sig(perms, d)
    assert pvals.size == comp


def test_bootstrap():
    U, d, V = pyls.compute.svd(X, Y, comp)

    U_boot, V_boot = pyls.compute.bootstrap(X, Y, comp, U, V, n_boot=n_boot)
    assert U_boot.shape == (behavior, comp, n_boot)
    assert V_boot.shape == (brain, comp, n_boot)

    U_bci, V_bci = pyls.compute.boot_ci(U_boot, V_boot)
    assert U_bci.shape == (behavior, comp, 2)
    assert V_bci.shape == (brain, comp, 2)

    U_rel, V_rel = pyls.compute.boot_rel(U, V, U_boot, V_boot)
    assert U_rel.shape == (behavior, comp)
    assert V_rel.shape == (brain, comp)

    pyls.compute.boot_sig(U_bci[:, 0, :])
    pyls.compute.kaiser_criterion(d)
