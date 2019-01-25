.. testsetup::

    import numpy as np
    np.set_printoptions(suppress=True)

.. _usage_behavioral:

Behavioral PLS
==============

What we call behavioral PLS in the ``pyls`` package is actually the more
traditional form of PLS (and is generally not prefixed with "behavioral" ---
more on that later). This form of PLS, at its core, attempts to find shared
information between two sets of features from a common set of samples. However,
as with all things, there are a number of ever-so-slightly different kinds of
PLS that exist in the wild, so to be thorough we're going to briefly explain
the exact flavor implemented here before diving into a more illustrative
example.

What *exactly* is behavioral PLS?
---------------------------------

:py:func:`pyls.behavioral_pls` employs a symmetrical, singular value
decomposition (SVD) based form of PLS, and is sometimes referred to as
PLS-correlation (PLS-C) or PLS-SVD. Notably, it is **not** the same as PLS
regression (PLS-R). Indeed, you can think of the differences between PLS-C and
PLS-R similar to how you might consider the differences between a Pearson
correlation and a simple linear regression. Though this analogy is a bit of a
simplification, the primary difference to take away is that behavioral PLS
(PLS-C) does *not assess directional relationships between sets of data* (e.g.,
X → Y), but rather how the two sets generally covary (e.g., X ↔ Y).

To understand this a bit more we can walk through a detailed example.

An exercise in calisthenics
---------------------------

.. note::
    Descriptions of PLS are almost always accompanied by a litany of equations,
    and for good reason: understanding PLS requires understanding the math
    behind it. As such, this example is going to rely on these equations, but
    will always do so in the context of real data. The hope is that this
    approach will help make the more abstract mathematical concepts a bit more
    concrete (and easier to apply to new data sets!).

We'll start by loading the example dataset [1]_:

.. doctest::

    >>> from pyls.examples import load_dataset
    >>> data = load_dataset('linnerud')

This is the same dataset as in :py:func:`sklearn.datasets.load_linnerud`; the
formatting has just been lightly modified to better suit our purposes.

Our ``data`` object can be treated as a dictionary, containing all the
information necessary to run a PLS analysis. The keys can be accessed as
attributes, so we can take a quick look at our input matrices
:math:`\textbf{X}` and :math:`\textbf{Y}`:

.. doctest::

    >>> data.keys()
    dict_keys(['X', 'Y', 'n_perm', 'n_boot'])
    >>> data.X.shape
    (20, 3)
    >>> data.X.head()
       Chins  Situps  Jumps
    0    5.0   162.0   60.0
    1    2.0   110.0   60.0
    2   12.0   101.0  101.0
    3   12.0   105.0   37.0
    4   13.0   155.0   58.0

The rows of our :math:`\textbf{X}_{n \times p}` matrix here represent *n*
subjects, and the columns indicate *p* different types of exercises these
subjects were able to perform. So the first subject was able to do 5 chin-ups,
162 situps, and 60 jumping jacks.

.. doctest::

    >>> data.Y.shape
    (20, 3)
    >>> data.Y.head()
       Weight  Waist  Pulse
    0   191.0   36.0   50.0
    1   189.0   37.0   52.0
    2   193.0   38.0   58.0
    3   162.0   35.0   62.0
    4   189.0   35.0   46.0

The rows of our :math:`\textbf{Y}_{n \times q}` matrix *also* represent *n*
subjects (critically, the same subjects as in :math:`\textbf{X}`), and the
columns indicate *q* physiological measurements taken for each subject. That
same subject referenced above thus has a weight of 191 pounds, a 36 inch waist,
and a resting pulse of 50 beats per minute.

Behavioral PLS will attempt to establish whether a relationship exists between
the exercises performed and these physiological variables. If we wanted to run
the full analysis right away, we could do so with:

.. doctest::

    >>> from pyls import behavioral_pls
    >>> results = behavioral_pls(**data)

If you're comfortable with the down-and-dirty of PLS and want to go ahead and
start understanding the ``results`` object, feel free to jump ahead to
:ref:`usage_results`. Otherwise, read on for more about what's happening behind
the scenes of :py:func:`~.behavioral_pls`

The cross-covariance matrix
---------------------------

Behavioral PLS works by decomposing the cross-covariance matrix
:math:`\textbf{R}_{q \times p}` generated from the input matrices, where
:math:`\textbf{R} = \textbf{Y}^{T} \textbf{X}`. The results of PLS are a
bit easier to interpret when :math:`\textbf{R}` is the cross-correlation matrix
instead of the cross-covariance matrix, which means that we should z-score each
feature in :math:`\textbf{X}` and :math:`\textbf{Y}` before multiplying them;
this is done automatically by the :py:func:`~.behavioral_pls` function.

In our example, :math:`\textbf{R}` ends up being a 3 x 3 matrix:

.. doctest::

    >>> from pyls.compute import xcorr
    >>> R = xcorr(data.X, data.Y)
    >>> R
    array([[-0.38969365, -0.49308365, -0.22629556],
           [-0.55223213, -0.64559803, -0.19149937],
           [ 0.15064802,  0.22503808,  0.03493306]])

The :math:`q` rows of this matrix correspond to the physiological measurements
and the :math:`p` columns to the exercises. Examining the first row, we can see
that ``-0.38969365`` is the correlation between ``Weight`` and ``Chins`` across
all the subjects, ``-0.49308365`` the correlation between ``Weight`` and
``Situps``, and so on.

Singular value decomposition
----------------------------

Once we have generated our correlation matrix :math:`\textbf{R}` we subject it
to a singular value decomposition, where :math:`\textbf{R} = \textbf{USV}^{T}`:

.. doctest::

    >>> from pyls.compute import svd
    >>> U, S, V = svd(R)
    >>> U.shape, S.shape, V.shape
    ((3, 3), (3, 3), (3, 3))

The outputs of this decomposition are two arrays of left and right singular
vectors (:math:`\textbf{U}_{p \times l}` and :math:`\textbf{V}_{q \times l}`)
and a diagonal matrix of singular values (:math:`\textbf{S}_{l \times l}`). The
rows of :math:`\textbf{U}` correspond to the exercises from our input matrix
:math:`\textbf{X}`, and the rows of :math:`\textbf{V}` correspond to the
physiological measurements from our input matrix :math:`\textbf{Y}`. The
columns of :math:`\textbf{U}` and :math:`\textbf{V}`, on the other hand,
represent new dimensions or components that have been "discovered" in the data.

The :math:`i^{th}` columns of :math:`\textbf{U}` and :math:`\textbf{V}` weigh
the contributions of these exercises and physiological measurements,
respectively. Taken together, the :math:`i^{th}` left and right singular
vectors and singular value represent a *latent variable*, a multivariate
pattern that weighs the original exercise and physiological measurements such
that they maximally covary with each other.

The :math:`i^{th}` singular value is proportional to the total
exercise-physiology covariance accounted for by the latent variable. The
effect size (:math:`\eta`) associated with a particular latent variable can be
estimated as the ratio of the squared singular value (:math:`\sigma`) to the
sum of all the squared singular values:

.. math::

    \eta_{i} = \sigma_{i}^{2} \big/ \sum \limits_{j=1}^{l} \sigma_{j}^{2}

We can use the helper function :py:func:`pyls.compute.varexp` to calculate this
for us:

.. doctest::

    >>> from pyls.compute import varexp
    >>> varexp(S)[0, 0]
    0.99471333682479335

Taking a look at the variance explained, we see that a whopping ~99.5% of the
covariance between the exercises and physiological measurements in
:math:`\textbf{X}` and :math:`\textbf{Y}` are explained by this latent
variable, suggesting that the relationship between these variable can be
effectively explained by a single dimension.

Examining the weights from the singular vectors:

.. doctest::

    >>> U[:, 0]
    array([ 0.61330742,  0.7469717 ,  0.25668519])
    >>> V[:, 0]
    array([-0.58989118, -0.77134059,  0.23887675])

we see that all the exercises (``U[:, 0]``) are positively weighted, but that
the physiological measurements (``V[:, 0]``) are split, with  ``Weight`` and
``Waist`` measurements negatively weighted and ``Pulse`` positively weighted.
(Note that the order of the weights is the same as the order of the original
columns in our :math:`\textbf{X}` and :math:`\textbf{Y}` matrices.) Taken
together this suggests that, for the subjects in this dataset, individuals who
completed more of a given exercise tended to:

1. Complete more of the other exercises, and
2. Have a lower weight, smaller waist, and higher heart rate.

It is also worth examining how correlated the projections of the original
variables on this latent variable are. To do that, we can multiply the original
data matrices by the relevant singular vectors and then correlate the results:

.. doctest::

    >>> from scipy.stats import pearsonr
    >>> XU = np.dot(data.X, U)
    >>> YV = np.dot(data.Y, V)
    >>> pearsonr(XU[:, 0], YV[:, 0])
    (0.48997247845503833, 0.028304653097330421)

The correlation value of this latent variable (~ ``0.49`` ) suggests that our
interpretation of the singular vectors weights, above, is moderately true.

Latent variable significance testing
------------------------------------

How can we check that these latent variables are significant? That is, that
the likelihood of them explaining *this much* variance is greater than chance
(to some prespecified alpha)?

Reliability of the singular vectors
-----------------------------------


.. [1] Tenenhaus, M. (1998). La régression PLS: théorie et pratique. Editions
   technip.
