from typing import Sequence, Tuple

from ctparse.nb_estimator import MultinomialNaiveBayes
from ctparse.count_vectorizer import CountVectorizer


class CTParsePipeline:
    def __init__(self, transformer: CountVectorizer, estimator: MultinomialNaiveBayes):
        """Setup a pipeline of feature extraction and naive bayes. Overkill for what it
        does but leaves room to use different models/features in the future

        Parameters
        ----------
        transformer : CountVectorizer
            feature extraction step
        estimator : MultinomialNaiveBayes
            naive bayes model
        """
        self.transformer = transformer
        self.estimator = estimator

    def fit(self, X: Sequence[Sequence[str]], y: Sequence[int]) -> "CTParsePipeline":
        """Fit the transformer and then fit the Naive Bayes model on the transformed
        data

        Returns
        -------
        CTParsePipeline
            Returns the fitted pipeline
        """
        X_transformed = self.transformer.fit_transform(X)
        self.estimator = self.estimator.fit(X_transformed, y)
        return self

    def predict_log_proba(
        self, X: Sequence[Sequence[str]]
    ) -> Sequence[Tuple[float, float]]:
        """Apply the transforms and get probability predictions from the estimator

        Parameters
        ----------
        X : Sequence[Sequence[str]]
            Sequence of documents, each as sequence of tokens. In ctparse case there are
            just the names of the regex matches and rules applied

        Returns
        -------
        Sequence[Tuple[float, float]]
            For each document the tuple of negative/positive log probability from the
            naive bayes model
        """
        X_transformed = self.transformer.transform(X)
        return self.estimator.predict_log_probability(X_transformed)
