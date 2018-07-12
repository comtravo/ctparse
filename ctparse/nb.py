import logging
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

logger = logging.getLogger(__name__)


def _id(x):
    # can not pickle models if using a lambda below
    return x


class NB:
    def __init__(self):
        self._model = None

    @property
    def hasModel(self):
        return self._model is not None

    def fit(self, X, y):
        # X, y = self._prepare_data(X, y)
        self._model = make_pipeline(
            CountVectorizer(ngram_range=(1, 3), lowercase=False,
                            tokenizer=_id),
            MultinomialNB(alpha=1.0))
        self._model.fit(X, y)
        # Make sure that class order is -1, 1
        assert self._model.classes_[0] == -1
        return self

    def predict(self, X):
        """wrapper to predict - if no model is fitted, return 0.0 for all samples"""
        if self._model is None:
            return [0.0 for x in X]
        pred = self._model.predict_log_proba(X)
        return pred[:, 1] - pred[:, 0]

    def map_prod(self, prod, y=None):
        """given one production, transform it into all sub-sequences of len 1 - len(prod)"""
        Xs = []
        ys = []
        for i in range(1, len(prod)):
            Xs.append([str(w) for w in prod[:i]])
            ys.append(1 if y else -1)
        if not Xs:
            return [[]], [-1]
        return Xs, ys

    def apply(self, x):
        """apply model to a single data point"""
        return self.predict([[str(w) for w in x]])[0]
