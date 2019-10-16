import math

from abc import ABCMeta, abstractmethod
from datetime import datetime
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
