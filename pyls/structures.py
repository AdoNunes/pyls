# -*- coding: utf-8 -*-

from textwrap import dedent
from .utils import ResDict

_pls_input_docs = dict(
    decomposition_narrative=dedent("""\
    The singular value decomposition generates mutually orthogonal latent
    variables (LVs), comprised of left and right singular vectors and a
    diagonal matrix of singular values. The `i`-th pair of singular vectors
    detail the contributions of individual input features to an overall,
    multivariate pattern (the `i`-th LV), and the singular values explain the
    amount of variance captured by that pattern.

    Statistical significance of the LVs is determined via permutation testing.
    Bootstrap resampling is used to examine the contribution and reliability of
    the input features to each LV. Split-half resampling can optionally be used
    to assess the reliability of the LVs. A cross-validated framework can
    optionally be used to examine how accurate the decomposition is when
    employed in a predictive framework.\
    """),
    input_matrix=dedent("""\
    X : (S, B) array_like
        Input data matrix, where `S` is samples and `B` is features\
    """),
    groups=dedent("""\
    groups : (G,) list of int
        List with the number of subjects present in each of `G` groups. Input
        data should be organized as subjects within groups (i.e., groups should
        be vertically stacked). If there is only one group this can be left
        blank.\
    """),
    conditions=dedent("""\
    n_cond : int
        Number of conditions observed in data. Note that all subjects must have
        the same number of conditions. If both conditions and groups are
        present then the input data should be organized as subjects within
        conditions within groups (i.e., g1c1s[1-S], g1c2s[1-S], g2c1s[1-S],
        g2c2s[1-S]).\
    """),
    mean_centering=dedent("""\
    mean_centering : {0, 1, 2}, optional
        Mean-centering method to use. This will determine how the mean-centered
        matrix is generated and what effects are "boosted" during the SVD.
        Default: 0\
    """),
    # perms / resampling / crossval
    stat_test=dedent("""\
    n_perm : int, optional
        Number of permutations to use for testing significance of latent
        variables. Default: 5000
    n_boot : int, optional
        Number of bootstraps to use for testing reliability of features.
        Default: 5000
    n_split : int, optional
        Number of split-half resamples to assess during permutation testing.
        This also controls the number of train/test splits examined during
        cross-validation if :attr:`test_size` is not zero. Default: 100
    test_size : [0, 1) float, optional
        Proportion of data to partition to test set during cross-validation.
        Default: 0.25\
    """),
    rotate=dedent("""\
    rotate : bool, optional
        Whether to perform Procrustes rotations during permutation testing. Can
        inflate false-positive rates; see Kovacevic et al., (2013) for more
        information. Default: True\
    """),
    ci=dedent("""\
    ci : [0, 100] float, optional
        Confidence interval to use for assessing bootstrap results. This
        roughly corresponds to an alpha rate; e.g., the 95%ile CI is
        approximately equivalent to a two-tailed p <= 0.05. Default: 95\
    """),
    seed=dedent("""\
    seed : {int, :obj:`numpy.random.RandomState`, None}, optional
        Seed to use for random number generation. Helps ensure reproducibility
        of results. Default: None\
    """),
    verbose=dedent("""\
    verbose : bool, optional
        Whether to print status messages about the progress of the PLS analysis
        as it progresses. Default: True
    """),
    pls_results=dedent("""\
    results : :obj:`pyls.PLSResults`
        Dictionary-like object containing results from the PLS analysis\
    """),
    references=dedent("""\
    McIntosh, A. R., Bookstein, F. L., Haxby, J. V., & Grady, C. L. (1996).
    Spatial pattern analysis of functional brain images using partial least
    squares. NeuroImage, 3(3), 143-157.

    McIntosh, A. R., & Lobaugh, N. J. (2004). Partial least squares analysis of
    neuroimaging data: applications and advances. NeuroImage, 23, S250-S263.

    Krishnan, A., Williams, L. J., McIntosh, A. R., & Abdi, H. (2011). Partial
    Least Squares (PLS) methods for neuroimaging: a tutorial and review.
    NeuroImage, 56(2), 455-475.

    Kovacevic, N., Abdi, H., Beaton, D., & McIntosh, A. R. (2013). Revisiting
    PLS resampling: comparing significance versus reliability across range of
    simulations. In New Perspectives in Partial Least Squares and Related
    Methods (pp. 159-170). Springer, New York, NY. Chicago\
    """)
)


class PLSInputs(ResDict):
    allowed = [
        'X', 'Y', 'groups', 'n_cond', 'n_perm', 'n_boot', 'n_split',
        'test_size', 'mean_centering', 'method', 'rotate', 'ci', 'seed',
        'bootsamples', 'permsamples', 'verbose'
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.get('n_split', 0) == 0:
            self['n_split'] = None
        ts = self.get('test_size', None)
        if ts is not None and (ts < 0 or ts >= 1):
            raise ValueError('test_size must be in [0, 1). Provided value: {}'
                             .format(ts))


PLSInputs.__doc__ = dedent("""\
    PLS input information

    Attributes
    ----------
    X : (S, B) array_like
        Input data matrix, where `S` is observations and `B` is features.
    Y : (S, T) array_like
        Behavioral matrix, where `S` is observations and `T` is features.
        If from :obj:`.behavioral_pls`, this is the provided behavior matrix;
        if from :obj:`.meancentered_pls`, this is a dummy-coded group/condition
        matrix.
    {groups}
    {conditions}
    {mean_centering}
    {stat_test}
    {rotate}
    {ci}
    {seed}
    {verbose}
    """).format(**_pls_input_docs)


class PLSResults(ResDict):
    r"""
    Dictionary-like object containing results of PLS analysis

    Attributes
    ----------
    u : (B, L) `numpy.ndarray`
        Left singular vectors from original singular value decomposition.
    s : (L, L) `numpy.ndarray`
        Singular values from original singular value decomposition.
    v : (J, L) `numpy.ndarray`
        Right singular vectors from original singular value decomposition.
    brainscores : (S, L) `numpy.ndarray`
        Brain scores (:math:`X \times v`), where `X` is :attr:`inputs.X`.
    designscores : (S, L) `numpy.ndarray`
        Design scores (:math:`Y \times u`), where `Y` is :attr:`inputs.Y`.
        Only obtained from :obj:`.meancentered_pls`.
    behavscores : (S, L) `numpy.ndarray`
        Behavior scores (:math:`Y \times u`), where `Y` is :attr:`inputs.Y`.
        Only obtained from :obj:`.behavioral_pls`.
    brainscores_dm : (S, L) `numpy.ndarray`
        Demeaned brain scores (:math:`(X - \bar{{X}}) \times v`), where `X` is
        :attr:`inputs.X`. Only obtained from :obj:`.meancentered_pls`.
    behavcorr : (J, L) `numpy.ndarray`
        Correlation of :attr:`brainscores` with :attr:`inputs.Y`. Only
        obtained from :obj:`.behavioral_pls`.
    permres : :obj:`~.structures.PLSPermResults`
        Results of permutation testing
    bootres : :obj:`~.structures.PLSBootResults`
        Results of bootstrap resampling
    splitres : :obj:`~.structures.PLSSplitHalfResults`
        Results of split-half resampling
    cvres : :obj:`~.structures.PLSCrossValidationResults`
        Results of cross-validation testing
    inputs : :obj:`~.structures.PLSInputs`
        Inputs provided to original PLS
    """
    allowed = [
        'u', 's', 'v',
        'brainscores', 'brainscores_dm', 'designscores', 'behavscores',
        'behavcorr', 'permres', 'bootres', 'splitres', 'cvres', 'inputs'
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # create all sub-dictionaries
        self.inputs = PLSInputs(**kwargs.get('inputs', kwargs))
        self.bootres = PLSBootResults(**kwargs.get('bootres', kwargs))
        self.permres = PLSPermResults(**kwargs.get('permres', kwargs))
        self.splitres = PLSSplitHalfResults(**kwargs.get('splitres', kwargs))
        self.cvres = PLSCrossValidationResults(**kwargs.get('cvres', kwargs))


class PLSBootResults(ResDict):
    """
    Dictionary-like object containing results of PLS bootstrap resampling

    Attributes
    ----------
    bootstrapratios : (B, L) `numpy.ndarray`
        Left singular vectors normalized by their standard error obtained
        from bootstrapping (:attr:`uboot_se`). Often referred to as BSRs, these
        can be interpreted as a z-score (assuming a Gaussian distribution).
    uboot_se : (B, L) `numpy.ndarray`
        Standard error of bootstrapped distribution of left singular vectors
        vectors
    contrast : (J, L) `numpy.ndarray`
        Group x condition averages of :attr:`brainscores_demeaned`. Can be
        treated as a contrast indicating group x condition differences. Only
        obtained from :obj:`.meancentered_pls`.
    contrast_boot : (J, L, R) `numpy.ndarray`
        Bootstrapped distribution of :attr:`contrast`. Only obtained from
        :obj:`.meancentered_pls`.
    contrast_uplim : (J, L) `numpy.ndarray`
        Upper bound of confidence interval for :attr:`contrast`. Only obtained
        from :obj:`.meancentered_pls`.
    contrast_lolim : (J, L) `numpy.ndarray`
        Lower bound of confidence interval for :attr:`contrast`. Only obtained
        from :obj:`.meancentered_pls`.
    behavcorr : (J, L) `numpy.ndarray`
        Correlation of :attr:`brainscores` with :attr:`Y`. Only obtained from
        :obj:`.behavioral_pls`.
    behavcorr_boot : (J, L, R) `numpy.ndarray`
        Bootstrapped distribution of :attr:`behavcorr`. Only obtained from
        :obj:`.behavioral_pls`.
    behavcorr_uplim : (J, L) `numpy.ndarray`
        Upper bound of confidence interval for :attr:`behavcorr`. Only obtained
        from :obj:`.behavioral_pls`.
    behavcorr_lolim : (J, L) `numpy.ndarray`
        Lower bound of confidence interval for :attr:`behavcorr`. Only obtained
        from :obj:`.behavioral_pls`.
    bootsamples : (S, R) `numpy.ndarray`
        Indices of bootstrapped samples `S` across `R` resamples.
    """
    allowed = [
        'bootstrapratios', 'uboot_se', 'bootsamples',
        'behavcorr', 'behavcorr_boot', 'behavcorr_uplim', 'behavcorr_lolim',
        'contrast', 'contrast_boot', 'contrast_uplim', 'contrast_lolim'
    ]


class PLSPermResults(ResDict):
    """
    Dictionary-like object containing results of PLS permutation testing

    Attributes
    ----------
    pvals : (L,) `numpy.ndarray`
        Non-parametric p-values of latent variables from PLS decomposition.
    permsamples : (S, P) `numpy.ndarray`
        Indices of permuted samples `S` across `P` permutations.
    """
    allowed = [
        'pvals', 'permsamples'
    ]


class PLSSplitHalfResults(ResDict):
    """
    Dictionary-like object containing results of PLS split-half resampling

    Attributes
    ----------
    ucorr, vcorr : (L,) `numpy.ndarray`
        Average correlations between split-half resamples in original (non-
        permuted) data for left/right singular vectors. Can be interpreted
        as reliability of `L` latent variables
    ucorr_pvals, vcorr_pvals : (L,) `numpy.ndarray`
        Number of permutations where correlation between split-half
        resamples exceeded original correlations, normalized by the total
        number of permutations. Can be interpreted as the statistical
        significance of the reliability of `L` latent variables
    ucorr_uplim, vcorr_uplim : (L,) `numpy.ndarray`
        Upper bound of confidence interval for correlations between split
        halves for left/right singular vectors
    ucorr_lolim, vcorr_lolim : (L,) `numpy.ndarray`
        Lower bound of confidence interval for correlations between split
        halves for left/right singular vectors
    """
    allowed = [
        'ucorr', 'vcorr',
        'ucorr_pvals', 'vcorr_pvals',
        'ucorr_uplim', 'vcorr_uplim',
        'ucorr_lolim', 'vcorr_lolim'
    ]


class PLSCrossValidationResults(ResDict):
    """
    Dictionary-like object containing results of PLS cross-validation testing

    Attributes
    ----------
    r_squared : (T, I) `numpy.ndarray`
        R-squared ("determination coefficient") for each of `T` predicted
        behavioral scores against true behavioral scores across `I` train /
        test split
    pearson_r : (T, I) `numpy.ndarray`
        Pearson's correlation for each of `T` predicted behavioral scores
        against true behavioral scores across `I` train / test split
    """
    allowed = [
        'pearson_r', 'r_squared'
    ]
