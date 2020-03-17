from typing import Sequence, Dict
from math import log, exp


def log_sum_exp(x):
    max_value = max(x)
    sum_of_exp = sum([exp(x_i - max_value) for x_i in x])
    return max_value + log(sum_of_exp)


class MultinomialNaiveBayes:
    def __init__(self, alpha: float = 1.0, class_prior=None, log_likelihood=None):
        self.alpha = alpha
        self.class_prior = class_prior
        self.log_likelihood = log_likelihood

    @staticmethod
    def validate_xy(X: Sequence[Dict[int, int]], y: Sequence[int]):
        # ToDo SMA: the usefulness of this function is complete unclear to me
        # Validate dimensions of X and y
        if any(isinstance(y_i, list) for y_i in y):
            raise ValueError('Expected 1D array')
        if len(X) and not all(len(X[i]) != 0 for i in range(len(X))):
            raise ValueError('Expected 2D array')

    # @staticmethod
    # def binarize_y(y):
    #     return [1 if y_i == 1 else 0 for y_i in y]

    def construct_log_class_prior(self, y: Sequence[int]):
        # Input classes are -1 and 1
        neg_class_count = sum(1 if y_i == -1 else 0 for y_i in y)
        pos_class_count = len(y) - neg_class_count

        neg_log_prior = log(neg_class_count / (pos_class_count + neg_class_count))
        pos_log_prior = log(pos_class_count / (pos_class_count + neg_class_count))
        self.class_prior = [neg_log_prior, pos_log_prior]

    def construct_log_likelihood(self, X: Sequence[Dict[int, int]], y: Sequence[int]):
        # Token counts
        # implicit assumption from vectorizer: first element has count for #vocab size set
        vocabulary_len = max(X[0].keys()) + 1
        token_counts_negative = [self.alpha] * vocabulary_len
        token_counts_positive = [self.alpha] * vocabulary_len
        for x, y_ in zip(X, y):
            for idx, cnt in x.items():
                if y_ == 1:
                    token_counts_positive[idx] += cnt
                else:
                    token_counts_negative[idx] += cnt
        # for token_index in range(vocabulary_len):
        #     token_pos_count = token_neg_count = 0
        #     for x, y_ in zip(X, y):
        #         if y_== 1:
        #             token_pos_count += x[token_index]
        #         else:
        #             token_neg_count += x[token_index]
        #     token_counts_positive.append(token_pos_count + self.alpha)
        #     token_counts_negative.append(token_neg_count + self.alpha)

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
        self.log_likelihood = {'negative_class': log_likelihood_negative,
                               'positive_class': log_likelihood_positive}

    def fit(self, X: Sequence[Dict[int, int]], y: Sequence[int]):
        self.validate_xy(X, y)
        self.construct_log_class_prior(y)
        self.construct_log_likelihood(X, y)

        return self

    def predict_log_probability(self, X):
        """ Calculate the posterior log probability of new sample X"""
        scores = []
        for x in X:
            # Initialise the scores with priors of positive and negative class
            neg_score = self.class_prior[0]
            pos_score = self.class_prior[1]
            for idx, cnt in x.items():
                pos_score += self.log_likelihood['positive_class'][idx] * cnt
                neg_score += self.log_likelihood['negative_class'][idx] * cnt
            joint_log_likelihood = [neg_score, pos_score]
            # Normalize the scores
            log_prob_x = log_sum_exp(joint_log_likelihood)
            scores.append([neg_score - log_prob_x, pos_score - log_prob_x])
        return scores
