'''
transforming (:mod:`calour.transforming`)
=========================================

.. currentmodule:: calour.transforming

Functions
^^^^^^^^^
.. autosummary::
   :toctree: generated

   normalize
   normalize_by_subset_features
   normalize_compositional
   scale
   random_permute_data
   binarize
   log_n
   transform
'''

# ----------------------------------------------------------------------------
# Copyright (c) 2016--,  Calour development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from logging import getLogger
from copy import deepcopy
from collections import defaultdict

import numpy as np
from sklearn import preprocessing

from .experiment import Experiment


logger = getLogger(__name__)


@Experiment._record_sig
def normalize(exp, total=10000, axis=0, inplace=False):
    '''Normalize the sum of each sample (axis=0) or feature (axis=1) to sum total

    Parameters
    ----------
    exp : Experiment
    total : float
        the sum (along axis) to normalize to
    axis : 0, 1, 's', or 'f', optional
        the axis to normalize. 0 or 's' (default) is normalize each sample;
        1 or 'f' to normalize each feature
    inplace : bool (optional)
        False (default) to create a copy, True to replace values in exp

    Returns
    -------
    ``Experiment``
        the normalized experiment
    '''
    if isinstance(total, bool):
        raise ValueError('Normalization total (%s) not numeric' % total)
    if total <= 0:
        raise ValueError('Normalization total (%s) must be positive' % total)
    if not inplace:
        exp = deepcopy(exp)
    exp.data = preprocessing.normalize(exp.data, norm='l1', axis=1-axis) * total
    # store the normalization depth into the experiment metadata
    exp.exp_metadata['normalized'] = total
    return exp


@Experiment._record_sig
def rescale(exp, total=10000, axis=0, inplace=False):
    '''Rescale the data to mean sum of all samples (axis=0) or features (axis=1) to be total.

    This function rescales by multiplying ALL entries in exp.data by same number.

    Parameters
    ----------
    exp : Experiment
    total : float
        the mean sum (along axis) to normalize to
    axis : 0, 1, 's', or 'f', optional
        the axis to normalize. 0 or 's' (default) is normalize each sample;
        1 or 'f' to normalize each feature
    inplace : bool (optional)
        False (default) to create a copy, True to replace values in exp

    Returns
    -------
    ``Experiment``
        the normalized experiment
    '''
    if isinstance(total, bool):
        raise ValueError('Rescaling total (%s) not numeric' % total)
    if not inplace:
        exp = deepcopy(exp)
    current_mean = np.mean(exp.data.sum(axis=1-axis))
    exp.data = exp.data * total / current_mean
    return exp


@Experiment._record_sig
def scale(exp, axis=0, inplace=False):
    '''Standardize a dataset along an axis

    .. warning:: It will convert the ``Experiment.data`` from the sparse matrix to dense array.

    Parameters
    ----------
    axis : 0, 1, 's', or 'f'
        0 or 's'  means scaling occur sample-wise; 1 or 'f' feature-wise.

    Returns
    -------
    ``Experiment``
    '''
    logger.debug('scaling the data, axis=%d' % axis)
    if not inplace:
        exp = deepcopy(exp)
    if exp.sparse:
        exp.sparse = False
    preprocessing.scale(exp.data, axis=1-axis, copy=False)
    return exp


@Experiment._record_sig
def binarize(exp, threshold=1, inplace=False):
    '''Binarize the data with a threshold.

    It calls scikit-learn to do the real work.

    Parameters
    ----------
    threshold : Numeric
        the cutoff value. Any values below or equal to this will be replaced by 0,
        above it by 1.

    Returns
    -------
    ``Experiment``
    '''
    logger.debug('binarizing the data. threshold=%f' % threshold)
    if not inplace:
        exp = deepcopy(exp)
    preprocessing.binarize(exp.data, threshold=threshold, copy=False)
    return exp


@Experiment._record_sig
def log_n(exp, n=1, inplace=False):
    '''Log transform the data

    Parameters
    ----------
    n : numeric, optional
        cap the tiny values and then log transform the data.
    inplace : bool, optional

    Returns
    -------
    ``Experiment``
    '''
    logger.debug('log_n transforming the data, min. threshold=%f' % n)
    if not inplace:
        exp = deepcopy(exp)

    if exp.sparse:
        exp.sparse = False

    exp.data[exp.data < n] = n
    exp.data = np.log2(exp.data)

    return exp


@Experiment._record_sig
def transform(exp, steps=[], inplace=False, **kwargs):
    '''Chain transformations together.

    Parameters
    ----------
    steps : list of callable
        each callable is a transformer that takes ``Experiment`` object as
        its 1st argument and has a boolean parameter of ``inplace``. Each
        callable should return an ``Experiment`` object.
    inplace : bool
        transformation occuring in the original data or a copy
    kwargs : dict
        keyword arguments to pass to each transformers. The key should
        be in the form of "<transformer_name>__<param_name>". For
        example, "transform(exp, steps=[log_n], log_n__n=3)" will set
        "n" of function "log_n" to 3

    Returns
    -------
    ``Experiment``
        with its data transformed

    '''
    if not inplace:
        exp = deepcopy(exp)
    params = defaultdict(dict)
    for k, v in kwargs.items():
        transformer, param_name = k.split('__')
        if param_name == 'inplace':
            raise ValueError('You should not give %s argument. It should be '
                             'set thru `inplace` argument for this function.')
        params[transformer][param_name] = v
    for step in steps:
        step(exp, inplace=True, **params[step.__name__])
    return exp


@Experiment._record_sig
def normalize_by_subset_features(exp, features, total=10000, negate=True, inplace=False):
    '''Normalize each sample by their total sums without a list of features

    Normalizes all features (including in the exclude list) by the
    total sum calculated without the excluded features. This is to
    alleviate the compositionality in the data set by only keeping the
    features that you think are not changing across samples.

    .. note:: sum is not identical in all samples after normalization
       (since also keeps the excluded features)

    Parameters
    ----------
    features : list of str
        The feature IDs to exclude (or include if negate=False)
    total : int (optional)
        The total abundance for the non-excluded features per sample
    negate : bool (optional)
        True (default) to calculate normalization factor without features in features list.
        False to calculate normalization factor only with features in features list.
    inplace : bool (optional)
        False (default) to create a new experiment, True to normalize in place

    Returns
    -------
    ``Experiment``
        The normalized experiment
    '''
    feature_pos = exp.feature_metadata.index.isin(features)
    if negate:
        feature_pos = np.invert(feature_pos)
    data = exp.get_data(sparse=False)
    use_reads = np.sum(data[:, feature_pos], axis=1)
    if inplace:
        newexp = exp
    else:
        newexp = deepcopy(exp)
    newexp.data = total * data / use_reads[:, None]
    # store the normalization depth into the experiment metadata
    newexp.exp_metadata['normalized'] = total
    return newexp


def normalize_compositional(exp, min_frac=0.05, total=10000, inplace=False):
    '''Normalize each sample by ignoring the features with mean>=min_frac in all the experiment

    This assumes that the majority of features have less than min_frac mean, and that the majority of features don't change
    between samples in a constant direction

    Parameters
    ----------
    min_frac : float (optional)
        ignore features with mean (over all samples) >= min_frac.
    total : int (optional)
        The total abundance for the non-excluded features per sample
    inplace : bool (optional)
        False (default) to create a new experiment, True to normalize in place

    Returns
    -------
    ``Experiment``
        The normalized experiment. Note that all features are normalized (including the ones with mean>=min_frac)
    '''
    comp_features = exp.filter_mean(min_frac)
    logger.info('ignoring %d features' % comp_features.shape[1])
    newexp = exp.normalize_by_subset_features(comp_features.feature_metadata.index.values,
                                              total=total, negate=True, inplace=inplace)
    return newexp


def random_permute_data(exp, normalize=True):
    '''Shuffle independently the reads of each feature

    Creates a new experiment with no dependence between the features.

    Parameters
    ----------
    normalize : bool (optional)
        True (default) to normalize each sample after completing the feature shuffling.
        False to not normalize

    Returns
    -------
    ``Experiment``
        With each feature shuffled independently
    '''
    newexp = exp.copy()
    newexp.sparse = False
    for cfeature in range(newexp.shape[1]):
        np.random.shuffle(newexp.data[:, cfeature])
    if normalize:
        newexp.normalize(np.mean(exp.data.sum(axis=1)), inplace=True)
    return newexp
