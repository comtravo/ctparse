"""Utility to load default model in ctparse"""

import bz2
import logging
import os
import pickle

from ctparse.scorer import Scorer, DummyScorer
from ctparse.nb_scorer import NaiveBayesScorer

logger = logging.getLogger(__name__)

# Location of the default model, included with ctparse
DEFAULT_MODEL_FILE = os.path.join(os.path.dirname(__file__), "models", "model.pbz")


def load_default_scorer() -> Scorer:
    """Load the scorer shipped with ctparse.

    If the scorer is not found, the scorer defaults to `DummyScorer`.
    """
    if os.path.exists(DEFAULT_MODEL_FILE):
        logger.info("Loading model from {}".format(DEFAULT_MODEL_FILE))
        with bz2.open(DEFAULT_MODEL_FILE, "rb") as fd:
            mdl = pickle.load(fd)
        return NaiveBayesScorer(mdl)

    else:
        logger.warning("No model found, initializing empty scorer")
        return DummyScorer()
