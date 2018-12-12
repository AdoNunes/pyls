# -*- coding: utf-8 -*-

import warnings
import numpy as np
from sklearn.utils.extmath import randomized_svd
from sklearn.utils.validation import check_random_state
from . import compute, structures, utils


def gen_permsamp(groups, n_cond, n_perm, seed=None, verbose=True):
    """
    Generates permutation arrays for PLS permutation testing

    Parameters
    ----------
    groups : (G,) list
        List with number of subjects in each of `G` groups
    n_cond : int
        Number of conditions, for each subject. Default: 1
    n_perm : int
        Number of permutations for which to generate resampling arrays
    seed : {int, :obj:`numpy.random.RandomState`, None}, optional
        Seed for random number generation. Default: None
    verbose : bool, optional
        Whether to print status updates as permutations are generated.
        Default: True

    Returns
    -------
    permsamp : (S, P) `numpy.ndarray`
        Subject permutation arrays, where `S` is the number of subjects and `P`
        is the requested number of permutations (i.e., `P = n_perm`)
    """
    Y = utils.dummy_code(groups, n_cond)
    permsamp = np.zeros(shape=(len(Y), n_perm), dtype=int)
    subj_inds = np.arange(np.sum(groups), dtype=int)
    rs = check_random_state(seed)
    warned = False

    # calculate some variables for permuting conditions within subject
    # do this here to save on calculation time
    indices, grps = np.where(Y)
    grp_conds = np.split(indices, np.where(np.diff(grps))[0] + 1)
    to_permute = [np.vstack(grp_conds[i:i + n_cond]) for i in
                  range(0, Y.shape[-1], n_cond)]
    splitinds = np.cumsum(groups)[:-1]
    check_grps = utils.dummy_code(groups).T.astype(bool)

    # can only use tqdm progress bar if not parallel processing
    for i in utils.trange(n_perm, verbose=verbose, desc='Making permutations'):
        count, duplicated = 0, True
        while duplicated and count < 500:
            count, duplicated = count + 1, False
            # generate conditions permuted w/i subject
            inds = np.hstack([utils.permute_cols(i, seed=rs) for i
                              in to_permute])
            # generate permutation of subjects across groups
            perm = rs.permutation(subj_inds)
            # confirm subjects *are* mixed across groups
            if len(groups) > 1:
                for grp in check_grps:
                    if np.all(np.sort(perm[grp]) == subj_inds[grp]):
                        duplicated = True
            # permute conditions w/i subjects across groups and stack
            perminds = np.hstack([f.flatten('F') for f in
                                  np.split(inds[:, perm].T, splitinds)])
            # make sure permuted indices are not a duplicate sequence
            dupe_seq = perminds[:, None] == permsamp[:, :i]
            if dupe_seq.all(axis=0).any():
                duplicated = True
        # if we broke out because we tried 500 permutations and couldn't
        # generate a new one, just warn that we're using duplicate
        # permutations and give up
        if count == 500 and not warned:
            warnings.warn('WARNING: Duplicate permutations used.')
            warned = True
        # store the permuted indices
        permsamp[:, i] = perminds

    return permsamp


def gen_bootsamp(groups, n_cond, n_boot, seed=None, verbose=True):
    """
    Generates bootstrap arrays for PLS bootstrap resampling

    Parameters
    ----------
    groups : (G,) list
        List with number of subjects in each of `G` groups
    n_cond : int
        Number of conditions, for each subject. Default: 1
    n_boot : int
        Number of boostraps for which to generate resampling arrays
    seed : {int, :obj:`numpy.random.RandomState`, None}, optional
        Seed for random number generation. Default: None
    verbose : bool, optional
        Whether to print status updates as bootstrap samples are genereated.
        Default: True

    Returns
    -------
    bootsamp : (S, B) `numpy.ndarray`
        Subject bootstrap arrays, where `S` is the number of subjects and `B`
        is the requested number of bootstraps (i.e., `B = n_boot`)
    """
    Y = utils.dummy_code(groups, n_cond)
    bootsamp = np.zeros(shape=(len(Y), n_boot), dtype=int)
    subj_inds = np.arange(np.sum(groups), dtype=int)
    rs = check_random_state(seed)
    warned = False
    min_subj = int(np.ceil(Y.sum(axis=0).min() * 0.5))

    # calculate some variables for ensuring we resample with replacement
    # subjects across all their conditions. do this here to save on
    # calculation time
    indices, grps = np.where(Y)
    grp_conds = np.split(indices, np.where(np.diff(grps))[0] + 1)
    inds = np.hstack([np.vstack(grp_conds[i:i + n_cond]) for i
                      in range(0, len(grp_conds), n_cond)])
    splitinds = np.cumsum(groups)[:-1]
    check_grps = utils.dummy_code(groups).T.astype(bool)

    for i in utils.trange(n_boot, verbose=verbose, desc='Making bootstraps'):
        count, duplicated = 0, True
        while duplicated and count < 500:
            count, duplicated = count + 1, False
            # empty container to store current bootstrap attempt
            boot = np.zeros(shape=(subj_inds.size), dtype=int)
            # iterate through and resample from w/i groups
            for grp in check_grps:
                curr_grp, all_same = subj_inds[grp], True
                while all_same:
                    num_subj = curr_grp.size
                    boot[curr_grp] = np.sort(rs.choice(curr_grp,
                                                       size=num_subj,
                                                       replace=True),
                                             axis=0)
                    # make sure bootstrap has enough unique subjs
                    if np.unique(boot[curr_grp]).size >= min_subj:
                        all_same = False
            # resample subjects (with conditions) and stack groups
            bootinds = np.hstack([f.flatten('F') for f in
                                  np.split(inds[:, boot].T, splitinds)])
            # make sure bootstrap is not a duplicated sequence
            for grp in check_grps:
                curr_grp = subj_inds[grp]
                check = bootinds[curr_grp, None] == bootsamp[curr_grp, :i]
                if check.all(axis=0).any():
                    duplicated = True
        # if we broke out because we tried 500 bootstraps and couldn't
        # generate a new one, just warn that we're using duplicate
        # bootstraps and give up
        if count == 500 and not warned:
            warnings.warn('WARNING: Duplicate bootstraps used.')
            warned = True
        # store the bootstrapped indices
        bootsamp[:, i] = bootinds

    return bootsamp


def gen_splits(groups, n_cond, n_split, seed=None, test_size=0.5):
    """
    Generates splitting arrays for PLS split-half resampling and CV

    Parameters
    ----------
    groups : (G,) list
        List with number of subjects in each of `G` groups
    n_cond : int
        Number of conditions, for each subject. Default: 1
    n_split : int
        Number of splits for which to generate resampling arrays
    seed : {int, :obj:`numpy.random.RandomState`, None}, optional
        Seed for random number generation. Default: None
    test_size : (0, 1) float, optional
        Percent of subjects to include in the split halves. Default: 0.5

    Returns
    -------
    splitsamp : (S, I) `numpy.ndarray`
        Subject split arrays, where `S` is the number of subjects and `I`
        is the requested number of splits (i.e., `I = n_split`)
    """
    Y = utils.dummy_code(groups, n_cond)
    splitsamp = np.zeros(shape=(len(Y), n_split), dtype=bool)
    subj_inds = np.arange(np.sum(groups), dtype=int)
    rs = check_random_state(seed)
    warned = False

    # calculate some variables for permuting conditions within subject
    # do this here to save on calculation time
    indices, grps = np.where(Y)
    grp_conds = np.split(indices, np.where(np.diff(grps))[0] + 1)
    inds = np.hstack([np.vstack(grp_conds[i:i + n_cond]) for i
                      in range(0, len(grp_conds), n_cond)])
    splitinds = np.cumsum(groups)[:-1]
    check_grps = utils.dummy_code(groups).T.astype(bool)

    for i in range(n_split):
        count, duplicated = 0, True
        while duplicated and count < 500:
            count, duplicated = count + 1, False
            # empty containter to store current split half attempt
            split = np.zeros(shape=(subj_inds.size), dtype=bool)
            # iterate through and split each group separately
            for grp in check_grps:
                curr_grp = subj_inds[grp]
                take = rs.choice([np.ceil, np.floor])
                num_subj = int(take(curr_grp.size * (1 - test_size)))
                splinds = rs.choice(curr_grp,
                                    size=num_subj,
                                    replace=False)
                split[splinds] = True
            # split subjects (with conditions) and stack groups
            half = np.hstack([f.flatten('F') for f in
                              np.split(((inds + 1).astype(bool)
                                        * [split[None]]).T,
                                       splitinds)])
            # make sure split half is not a duplicated sequence
            dupe_seq = half[:, None] == splitsamp[:, :i]
            if dupe_seq.all(axis=0).any():
                duplicated = True
        if count == 500 and not warned:
            warnings.warn('WARNING: Duplicate split halves used.')
            warned = True
        splitsamp[:, i] = half

    return splitsamp


class BasePLS():
    """
    Base PLS class to be subclassed

    Contains most of the math required for PLS, leaving a few functions for PLS
    subclasses to implement. This will not run without those implementations.

    Parameters
    ----------
    {input_matrix}
    {groups}
    {conditions}
    **kwargs : optional
        Additional key-value pairs; see :obj:`pyls.PLSInputs` for more info

    References
    ----------

    {references}
    """.format(**structures._pls_input_docs)

    def __init__(self, X, groups=None, n_cond=1, **kwargs):
        # if groups aren't provided or are provided wrong, fix them
        if groups is None:
            groups = [len(X)]
        elif not isinstance(groups, (list, np.ndarray)):
            groups = [groups]

        # coerce groups to integers
        groups = [int(g) for g in groups]

        # check that X / groups + n_cond inputs jibe
        n_samples = sum([g * n_cond for g in groups])
        if len(X) != n_samples:
            raise ValueError('Number of samples specified by `groups` and '
                             '`n_cond` does not match expected number of '
                             'samples in input array(s).\n'
                             '    EXPECTED: {}\n'
                             '    ACTUAL:   {} (groups: {} * n_cond: {})'
                             .format(len(X), n_samples, groups, n_cond))

        self.inputs = structures.PLSInputs(X=X, groups=groups, n_cond=n_cond,
                                           **kwargs)
        self.rs = check_random_state(self.inputs.get('seed'))
        n_proc = self.inputs.get('n_proc')
        if n_proc is not None and n_proc > 1 and not utils.joblib_avail:
            self.inputs.n_proc = 1
            warnings.warn('Setting n_proc > 1 requires the joblib module. '
                          'Considering installing joblib and re-running this '
                          'if you would like parallelization. Resetting '
                          'n_proc to 1 for now.')

    def gen_covcorr(self, X, Y, groups):
        """
        Should generate cross-covariance array to be used in `self._svd()`

        Must accept the listed parameters and return one array

        Parameters
        ----------
        X : (S, B) array_like
            Input data matrix, where `S` is observations and `B` is features
        Y : (S, T) array_like
            Input data matrix, where `S` is observations and `T` is features
        groups : (G,) array_like
            Array with number of subjects in each of `G` groups

        Returns
        -------
        crosscov : np.ndarray
            Covariance array for decomposition
        """

        raise NotImplementedError

    def run_pls(self, X, Y):
        """
        Runs PLS analysis

        Parameters
        ----------
        X : (S, B) array_like
            Input data matrix, where `S` is observations and `B` is features
        Y : (S, T) array_like
            Input data matrix, where `S` is observations and `T` is features
        groups : (G,) array_like
            Array with number of subjects in each of `G` groups
        """

        res = structures.PLSResults(inputs=self.inputs)

        # get original singular vectors / values and variance explained
        res.u, res.s, res.v = self.svd(X, Y, seed=self.rs)

        # compute permutations and get LV significance; store permsamp
        if self.inputs.n_perm > 0:
            d_perm, ucorrs, vcorrs = self.permutation(X, Y, seed=self.rs)
            res.permres.pvals = compute.perm_sig(res.s, d_perm)
            res.permres.permsamples = self.permsamp

            # get split half reliability results
            if self.inputs.n_split is not None:
                di = np.linalg.inv(res.s)
                orig_ucorr, orig_vcorr = self.split_half(X, Y,
                                                         res.u @ di,
                                                         res.v @ di,
                                                         seed=self.rs)
                # get probabilties for ucorr/vcorr
                ucorr_prob = compute.perm_sig(np.diag(orig_ucorr), ucorrs)
                vcorr_prob = compute.perm_sig(np.diag(orig_vcorr), vcorrs)
                # get confidence intervals for ucorr/vcorr
                ucorr_ll, ucorr_ul = compute.boot_ci(ucorrs, ci=self.inputs.ci)
                vcorr_ll, vcorr_ul = compute.boot_ci(vcorrs, ci=self.inputs.ci)
                # update results object
                res.splitres.update(dict(ucorr=orig_ucorr,
                                         vcorr=orig_vcorr,
                                         ucorr_pvals=ucorr_prob,
                                         vcorr_pvals=vcorr_prob,
                                         ucorr_lolim=ucorr_ll,
                                         vcorr_lolim=vcorr_ll,
                                         ucorr_uplim=ucorr_ul,
                                         vcorr_uplim=vcorr_ul))

        return res

    def svd(self, X, Y, dummy=None, seed=None):
        """
        Runs SVD on cross-covariance matrix computed from `X` and `Y`

        Parameters
        ----------
        X : (S, B) array_like
            Input data matrix, where `S` is observations and `B` is features
        Y : (S, T) array_like
            Input data matrix, where `S` is observations and `T` is features
        seed : {int, :obj:`numpy.random.RandomState`, None}, optional
            Seed for random number generation. Default: None

        Returns
        -------
        U : (B, L) `numpy.ndarray`
            Left singular vectors
        d : (L, L) `numpy.ndarray`
            Diagonal array of singular values
        V : (J, L) `numpy.ndarray`
            Right singular vectors
        """

        if dummy is None:
            dummy = utils.dummy_code(self.inputs.groups, self.inputs.n_cond)
        crosscov = self.gen_covcorr(X, Y, groups=dummy)
        n_comp = min(min(dummy.squeeze().shape), min(crosscov.shape))
        U, d, V = randomized_svd(crosscov.T,
                                 n_components=n_comp,
                                 random_state=check_random_state(seed))

        return U, np.diag(d), V.T

    def bootstrap(self, X, Y, seed=None):
        """
        Bootstraps `X` and `Y` (w/replacement) and recomputes SVD

        Parameters
        ----------
        X : (S, B) array_like
            Input data matrix, where `S` is observations and `B` is features
        Y : (S, T) array_like
            Input data matrix, where `S` is observations and `T` is features
        seed : {int, :obj:`numpy.random.RandomState`, None}, optional
            Seed for random number generation. Default: None

        Returns
        -------
        U_boot : (B, L, R) `numpy.ndarray`
            Left singular vectors, where `R` is the number of bootstraps
        V_boot : (J, L, R) `numpy.ndarray`
            Right singular vectors, where `R` is the number of bootstraps
        """

        # generate bootstrap resampled indices (unless already provided)
        self.bootsamp = self.inputs.get('bootsamples', None)
        if self.bootsamp is None:
            self.bootsamp = gen_bootsamp(self.inputs.groups,
                                         self.inputs.n_cond,
                                         self.inputs.n_boot,
                                         seed=seed,
                                         verbose=self.inputs.verbose)

        # get original values
        U_orig, *rest = self.svd(X, Y, seed=seed)

        # get bootstrapped values (parallelizing as requested)
        parallel, func = utils.get_par_func(self.inputs.n_proc,
                                            self.__class__._single_boot)
        gen = utils.trange(self.inputs.n_boot, verbose=self.inputs.verbose,
                           desc='Running bootstraps')
        out = parallel(func(self, X=X, Y=Y, inds=self.bootsamp[:, i],
                            original=U_orig, seed=i) for i in gen)
        U_boot, V_boot = [np.stack(o, axis=-1) for o in zip(*out)]

        return U_boot, V_boot

    def _single_boot(self, X, Y, inds, original, seed=None):
        """
        Bootstraps `X` and `Y` (w/replacement) and recomputes SVD

        Parameters
        ----------
        X : (S, B) array_like
            Input data matrix, where `S` is observations and `B` is features
        Y : (S, T) array_like
            Input data matrix, where `S` is observations and `T` is features
        inds : (S,) array_like
            Bootstrap resampling array
        original : (B, L) array_like
            Left singular vector from original decomposition of `X` and `Y`.
            Used to perform Procrustes rotation on permuted singular vectors
        seed : {int, :obj:`numpy.random.RandomState`, None}, optional
            Seed for random number generation. Default: None

        Returns
        -------
        U_boot : (B, L, R) `numpy.ndarray`
            Left singular vectors, where `R` is the number of bootstraps
        V_boot : (J, L, R) `numpy.ndarray`
            Right singular vectors, where `R` is the number of bootstraps
        """
        # perform SVD of bootstrapped arrays
        U, d, V = self.svd(X[inds], Y[inds], seed=seed)

        # get rotated singular vectors
        U_boot, rotate = compute.procrustes(original, U, d)
        V_boot = V @ d @ rotate

        return U_boot, V_boot

    def permutation(self, X, Y, seed=None):
        """
        Permutes `X` (w/o replacement) and recomputes SVD

        Parameters
        ----------
        X : (S, B) array_like
            Input data matrix, where `S` is observations and `B` is features
        Y : (S, T) array_like
            Input data matrix, where `S` is observations and `T` is features
        seed : {int, :obj:`numpy.random.RandomState`, None}, optional
            Seed for random number generation. Default: None

        Returns
        -------
        d_perm : (L, P) `numpy.ndarray`
            Permuted singular values, where `L` is the number of singular
            values and `P` is the number of permutations
        ucorrs : (L, P) `numpy.ndarray`
            Split-half correlations of left singular values. Only set if
            `self.inputs.n_split != 0`
        vcorrs : (L, P) `numpy.ndarray`
            Split-half correlations of right singular values. Only set if
            `self.inputs.n_split != 0`
        """

        # generate permuted indices (unless already provided)
        self.permsamp = self.inputs.get('permsamples')
        if self.permsamp is None:
            self.permsamp = gen_permsamp(self.inputs.groups,
                                         self.inputs.n_cond,
                                         self.inputs.n_perm,
                                         seed=seed,
                                         verbose=self.inputs.verbose)

        # get original values
        *rest, V_orig = self.svd(X, Y, seed=seed)

        # get permuted values (parallelizing as requested)
        parallel, func = utils.get_par_func(self.inputs.n_proc,
                                            self.__class__._single_perm)
        gen = utils.trange(self.inputs.n_perm, verbose=self.inputs.verbose,
                           desc='Running permutations')
        out = parallel(func(self, X=X, Y=Y, inds=self.permsamp[:, i],
                            original=V_orig, seed=i) for i in gen)
        d_perm, ucorrs, vcorrs = [np.stack(o, axis=-1) for o in zip(*out)]

        return d_perm, ucorrs, vcorrs

    def _single_perm(self, X, Y, inds, original, seed=None):
        """
        Permutes `X` (w/o replacement) and recomputes SVD

        Parameters
        ----------
        X : (S, B) array_like
            Input data matrix, where `S` is observations and `B` is features
        Y : (S, T) array_like
            Input data matrix, where `S` is observations and `T` is features
        inds : (S,) array_like
            Permutation resampling array
        original : (J, L) array_like
            Right singular vector from original decomposition of `X` and `Y`.
            Used to perform Procrustes rotation on permuted singular values,
            if desired
        seed : {int, :obj:`numpy.random.RandomState`, None}, optional
            Seed for random number generation. Default: None

        Returns
        -------
        d_perm : (L,) `numpy.ndarray`
            Permuted singular values, where `L` is the number of singular
            values
        ucorrs : (L,) `numpy.ndarray`
            Split-half correlations of left singular values. Only set if
            `self.inputs.n_split != 0`
        vcorrs : (L,) `numpy.ndarray`
            Split-half correlations of right singular values. Only set if
            `self.inputs.n_split != 0`
        """

        # perform SVD of permuted array
        X = X[inds]
        U, d, V = self.svd(X, Y, seed=seed)

        # optionally get rotated/rescaled singular values (or not)
        if self.inputs.rotate:
            ssd = np.sqrt(np.sum(compute.procrustes(original, V, d)[0]**2,
                          axis=0))
        else:
            ssd = np.diag(d)

        # get ucorr/vcorr if split-half resampling requested
        if self.inputs.n_split is not None:
            di = np.linalg.inv(d)
            ucorr, vcorr = self.split_half(X, Y, U @ di, V @ di, seed=seed)
        else:
            ucorr, vcorr = None, None

        return ssd, ucorr, vcorr

    def split_half(self, X, Y, ud, vd, seed=None):
        """
        Parameters
        ----------
        X : (S, B) array_like
            Input data matrix, where `S` is observations and `B` is features
        Y : (S, T) array_like
            Input data matrix, where `S` is observations and `T` is features
        ud : (B, L) array_like
            Left singular vectors, scaled by singular values
        vd : (J, L) array_like
            Right singular vectors, scaled by singular values
        seed : {int, :obj:`numpy.random.RandomState`, None}, optional
            Seed for random number generation. Default: None

        Returns
        -------
        ucorr : (L,) `numpy.ndarray`
            Average correlation of left singular vectors across split-halves
        vcorr : (L,) `numpy.ndarray`
            Average correlation of right singular vectors across split-halves
        """

        # generate splits
        splitsamp = gen_splits(self.inputs.groups,
                               self.inputs.n_cond,
                               self.inputs.n_split,
                               seed=seed,
                               test_size=0.5).astype(bool)

        # empty arrays to hold split-half correlations
        ucorr = np.zeros(shape=(ud.shape[-1], self.inputs.n_split))
        vcorr = np.zeros(shape=(vd.shape[-1], self.inputs.n_split))

        for i in range(self.inputs.n_split):
            spl = splitsamp[:, i]
            grps = utils.dummy_code(self.inputs.groups, self.inputs.n_cond)

            D1 = self.gen_covcorr(X[spl], Y[spl], groups=grps[spl])
            D2 = self.gen_covcorr(X[~spl], Y[~spl], groups=grps[~spl])

            # project cross-covariance matrices onto original SVD to obtain
            # left & right singular vector and correlate between split halves
            ucorr[:, i] = compute.efficient_corr(D1.T @ vd, D2.T @ vd)
            vcorr[:, i] = compute.efficient_corr(D1 @ ud, D2 @ ud)

        # return average correlations for singular vectors across `n_split`
        return ucorr.mean(axis=-1), vcorr.mean(axis=-1)
