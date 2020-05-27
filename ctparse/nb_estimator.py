from typing import Sequence, Dict, Tuple, List
from math import log, exp


def _log_sum_exp(x: Sequence[float]) -> float:
    max_value = max(x)
    sum_of_exp = sum(exp(x_i - max_value) for x_i in x)
    return max_value + log(sum_of_exp)


class MultinomialNaiveBayes:
    """Implements a multinomial naive Bayes classifier. For background information
    (and what has inspired this, see e.g. https://scikit-learn.org/stable/...
        ...modules/generated/sklearn.naive_bayes.MultinomialNB.html)
    """

    def __init__(self, alpha: float = 1.0):
        """Create new un-trained model

        Parameters
        ----------
        alpha : Optional[float]
            Additive (Laplace/Lidstone) smoothing parameter (0 for no smoothing),
            defaults to 1.0
        """
        self.alpha = alpha
        self.class_prior = (0.0, 0.0)
        self.log_likelihood: Dict[str, List[float]] = {}

    @staticmethod
    def _construct_log_class_prior(y: Sequence[int]) -> Tuple[float, float]:
        # Input classes are -1 and 1
        neg_class_count = sum(1 if y_i == -1 else 0 for y_i in y)
        pos_class_count = len(y) - neg_class_count

        neg_log_prior = log(neg_class_count / (pos_class_count + neg_class_count))
        pos_log_prior = log(pos_class_count / (pos_class_count + neg_class_count))
        return (neg_log_prior, pos_log_prior)

    @staticmethod
    def _construct_log_likelihood(
        X: Sequence[Dict[int, int]], y: Sequence[int], alpha: float
    ) -> Dict[str, List[float]]:
        # Token counts
        # implicit assumption from vectorizer: first element has count for #vocab
        # size set
        vocabulary_len = max(X[0].keys()) + 1
        token_counts_negative = [alpha] * vocabulary_len
        token_counts_positive = [alpha] * vocabulary_len
        for x, y_ in zip(X, y):
            for idx, cnt in x.items():
                if y_ == 1:
                    token_counts_positive[idx] += cnt
                else:
                    token_counts_negative[idx] += cnt

        token_pos_class_sum = sum(token_counts_positive)
        token_neg_class_sum = sum(token_counts_negative)

        log_likelihood_negative = []
        log_likelihood_positive = []
        for token_ind in range(vocabulary_len):
            log_likelihood_positive.append(
                log(token_counts_positive[token_ind]) - log(token_pos_class_sum)
            )

            log_likelihood_negative.append(
                log(token_counts_negative[token_ind]) - log(token_neg_class_sum)
            )
        return {
            "negative_class": log_likelihood_negative,
            "positive_class": log_likelihood_positive,
        }

    def fit(
        self, X: Sequence[Dict[int, int]], y: Sequence[int]
    ) -> "MultinomialNaiveBayes":
        """Fit a naive Bayes model from a count of feature matrix

        Parameters
        ----------
        X : Sequence[Dict[int, int]]
            Sequence of sparse {feature_index: count} dictionaries
        y : Sequence[int]
            Labels +1/-1

        Returns
        -------
        MultinomialNaiveBayes
            The fitted model
        """
        self.class_prior = self._construct_log_class_prior(y)
        self.log_likelihood = self._construct_log_likelihood(X, y, self.alpha)
        return self

    def predict_log_probability(
        self, X: Sequence[Dict[int, int]]
    ) -> Sequence[Tuple[float, float]]:
        """Calculate the posterior log probability of new sample X

        Parameters
        ----------
        X : Sequence[Dict[int, int]]
            Sequence of data to predict on as sparse {feature_index: count} dictionarie

        Returns
        -------
        Sequence[Tuple[float, float]]
            Tuple of (negative-class, positive-class) log likelihoods
        """
        scores = []
        for x in X:
            # Initialise the scores with priors of positive and negative class
            neg_score = self.class_prior[0]
            pos_score = self.class_prior[1]
            for idx, cnt in x.items():
                pos_score += self.log_likelihood["positive_class"][idx] * cnt
                neg_score += self.log_likelihood["negative_class"][idx] * cnt
            joint_log_likelihood = [neg_score, pos_score]
            # Normalize the scores
            log_prob_x = _log_sum_exp(joint_log_likelihood)
            scores.append((neg_score - log_prob_x, pos_score - log_prob_x))
        return scores
