"""This module contains the Scorer abstraction that can be used to
implement scoring strategies for ctparse.
"""

from abc import ABCMeta, abstractmethod
from datetime import datetime
from random import Random
from typing import Optional

from .partial_parse import PartialParse
from .types import Artifact


class Scorer(metaclass=ABCMeta):
    """Interface for scoring parses generated by ctparse"""

    @abstractmethod
    def score(self, txt: str, ts: datetime, partial_parse: PartialParse) -> float:
        """Produce a score for a partial production.

        :param txt:  the text that is being parsed
        :param ts: the reference time
        :param partial_parse: the partial parse that needs to be scored
        """

    @abstractmethod
    def score_final(
        self, txt: str, ts: datetime, partial_parse: PartialParse, prod: Artifact
    ) -> float:
        """Produce the final score for a production.

        :param txt: the text that is being parsed
        :param ts: the reference time
        :param partial_parse: the PartialParse object that generated the production
        :param prod: the production
        """


class DummyScorer(Scorer):
    """A scorer that always return a 0.0 score."""

    def score(self, txt: str, ts: datetime, partial_parse: PartialParse) -> float:
        return 0.0

    def score_final(
        self, txt: str, ts: datetime, partial_parse: PartialParse, prod: Artifact
    ) -> float:
        return 0.0


class RandomScorer(Scorer):
    def __init__(self, rng: Optional[Random] = None) -> None:
        """A score that returns a random number between 0 and 1.

        :param rng:
            the random number generator to use
        """
        self.rng = rng if rng is not None else Random()

    def score(self, txt: str, ts: datetime, partial_parse: PartialParse) -> float:
        return self.rng.random()

    def score_final(
        self, txt: str, ts: datetime, partial_parse: PartialParse, prod: Artifact
    ) -> float:
        return self.rng.random()
