# -*- coding: utf-8 -*-

import numpy as np
import pytest
import pyls

rs = np.random.RandomState(1234)


def test_zscore():
    out = pyls.compute.zscore([[1]] * 10)
    assert np.allclose(out, 0)

    out = pyls.compute.zscore(rs.rand(10, 10))
    assert out.shape == (10, 10)
    assert not np.allclose(out, 0)


def test_normalize():
    X = rs.rand(10, 10)
    out = pyls.compute.normalize(X, axis=0)
    assert np.allclose(np.sum(out**2, axis=0), 1)

    out = pyls.compute.normalize(X, axis=1)
    assert np.allclose(np.sum(out**2, axis=1), 1)


def test_xcorr():
    X = rs.rand(20, 200)
    Y = rs.rand(20, 25)

    xcorr = pyls.compute.xcorr(X, Y)
    assert xcorr.shape == (25, 200)
    xcorr = pyls.compute.xcorr(X, Y, norm=False)
    assert xcorr.shape == (25, 200)

    with pytest.raises(ValueError):
        pyls.compute.xcorr(X[:, 0], Y)
    with pytest.raises(ValueError):
        pyls.compute.xcorr(X[:, 0], Y[:, 0])
    with pytest.raises(ValueError):
        pyls.compute.xcorr(X[0:10], Y)
