from abc import ABCMeta, abstractmethod
from datetime import datetime
import math
from typing import Tuple

from .types import Artifact


class ProductionScorer(metaclass=ABCMeta):
    """Interface for scoring intermediate productions"""

    @abstractmethod
    def score(self, txt: str, ts: datetime, productions: Tuple[Artifact, ...]) -> float:
        """Produce a score for a partial productions.

        :param txt: the text that is being parsed
        :param productions: the partial set of productions
        """


class DummyScorer(ProductionScorer):

    def score(self, txt: str, ts: datetime, productions: Tuple[Artifact, ...]) -> float:
        return 0.0


class NaiveBayesScorer(ProductionScorer):

    def __init__(self, model):
        self._model = model

    def score(self, txt: str, ts: datetime, productions: Tuple[Artifact, ...]) -> float:
        # Penalization for partial matches
        max_covered_chars = productions[-1].mend - productions[0].mstart
        len_score = math.log(max_covered_chars/len(txt))

        X = [str(p.id) for p in productions]
        pred = self._model.predict_log_proba([X])
        model_score = pred[:, 1] - pred[:, 0]  # NOTE(glanaro): the prediction is log-odds

        return model_score + len_score
