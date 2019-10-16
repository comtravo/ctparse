"""Utilities to manage the naive bayes scorer"""
import bz2
import math
import pickle
from datetime import datetime
from typing import Sequence, Tuple

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

from .build_corpus import make_partial_prod_corpus
from .scorer import ProductionScorer
from .time import corpus as corpus_time
from .types import Artifact


class NaiveBayesScorer(ProductionScorer):

    def __init__(self, nb_model):
        self._model = nb_model

    @classmethod
    def from_model_file(cls, fname: str):
        with bz2.open(fname, 'rb') as fd:
            return cls(pickle.load(fd))

    def score(self, txt: str, ts: datetime, productions: Tuple[Artifact, ...]) -> float:
        # Penalty for partial matches
        max_covered_chars = productions[-1].mend - productions[0].mstart
        len_score = math.log(max_covered_chars/len(txt))

        # TODO: Make the _feature_extractor customizable
        X = _feature_extractor(txt, ts, productions)
        pred = self._model.predict_log_proba([X])

        # NOTE: the prediction is log-odds, or logit
        model_score = pred[:, 1] - pred[:, 0]

        return model_score + len_score


def _feature_extractor(txt: str, ts: datetime, productions: Tuple[Artifact, ...]) -> Sequence[str]:
    return [str(p.id) for p in productions]


def train_naive_bayes(fname):

    # Make corpus on-the-fly
    X, y = make_partial_prod_corpus(corpus_time, _feature_extractor)

    # Create and train the pipeline
    model = make_pipeline(
        CountVectorizer(ngram_range=(1, 3), lowercase=False,
                        tokenizer=_identity),
        MultinomialNB(alpha=1.0))
    model.fit(X, y)

    # Make sure that class order is -1, 1
    assert model.classes_[0] == -1

    # Save the model to disk
    with bz2.open(fname, 'wb') as fd:
        pickle.dump(model, fd)


def _identity(x):
    return x
