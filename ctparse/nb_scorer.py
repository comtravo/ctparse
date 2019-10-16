"""Utilities to manage the naive bayes scorer"""
import math
from datetime import datetime
from typing import Sequence, Tuple

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

from .scorer import ProductionScorer
from .types import Artifact


class NaiveBayesScorer(ProductionScorer):

    def __init__(self, nb_model):
        self._model = nb_model

    def score(self, txt: str, ts: datetime, productions: Tuple[Artifact, ...]) -> float:
        # Penalty for partial matches
        max_covered_chars = productions[-1].mend - productions[0].mstart
        len_score = math.log(max_covered_chars/len(txt))

        X = [str(p.id) for p in productions]
        pred = self._model.predict_log_proba([X])
        # NOTE: the prediction is log-odds, or logit
        model_score = pred[:, 1] - pred[:, 0]

        return model_score + len_score


def train_model(X: Sequence[Sequence[str]], y: Sequence[bool]):
    # NOTE: _identity has to be toplevel in order to be pickleable
    model = make_pipeline(
        CountVectorizer(ngram_range=(1, 3), lowercase=False,
                        tokenizer=_identity),
        MultinomialNB(alpha=1.0))
    model.fit(X, y)
    return model


def _identity(x):
    return x
