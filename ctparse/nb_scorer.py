"""This module cointains the naive bayes scorer predictions"""
import bz2
import math
import pickle
from datetime import datetime
from typing import Sequence, Tuple

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

from .scorer import Scorer
from .stack_element import StackElement
from .time import corpus as corpus_time
from .types import Artifact


class NaiveBayesScorer(Scorer):

    def __init__(self, nb_model):
        self._model = nb_model

    @classmethod
    def from_model_file(cls, fname: str, version="legacy"):
        with bz2.open(fname, 'rb') as fd:
            return cls(pickle.load(fd)._model)

    def score(self, txt: str, ts: datetime, stack_element: StackElement) -> float:
        # Penalty for partial matches
        max_covered_chars = stack_element.prod[-1].mend - stack_element.prod[0].mstart
        len_score = math.log(max_covered_chars/len(txt))

        # TODO: Make the _feature_extractor customizable
        X = _feature_extractor(txt, ts, stack_element)
        pred = self._model.predict_log_proba([X])

        # NOTE: the prediction is log-odds, or logit
        model_score = float(pred[:, 1] - pred[:, 0])

        return model_score + len_score


def _feature_extractor(txt: str, ts: datetime, stack_element: StackElement) -> Sequence[str]:
    return [str(r) for r in stack_element.rules]


def _identity(x):
    return x


def train_naive_bayes(fname: str) -> None:
    # TODO: circular dependency, bring it somewhere else
    from .build_corpus import make_partial_rule_corpus

    # Make corpus on-the-fly
    X, y = make_partial_rule_corpus(corpus_time)

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
