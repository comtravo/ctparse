import math

from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Tuple

from .stack_element import StackElement
from .types import Artifact


class Scorer(metaclass=ABCMeta):
    """Interface for scoring intermediate productions"""

    @abstractmethod
    def score(self, txt: str, ts: datetime, stack_element: StackElement) -> float:
        """Produce a score for a partial productions.

        :param txt: the text that is being parsed
        """


class LengthScorer(Scorer):

    def score(self, txt: str, ts: datetime, stack_element: StackElement) -> float:
        max_covered_chars = stack_element.prod[-1].mend - stack_element.prod[0].mstart
        return math.log(max_covered_chars/len(txt))
