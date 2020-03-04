from math import log


class MultinomialNaiveBayes:
    def __init__(self, alpha=1.0, class_prior=None, likelihood=None):
        self.alpha = alpha
        self.class_prior = class_prior
        self.likelihood = likelihood

    @staticmethod
    def validate_xy(X, y):
        # Validate dimensions of X and y
        if any(isinstance(y_i, list) for y_i in y):
            raise ValueError('Expected 1D array')
        if len(X) <= 0 and not all(len(X[i]) != 0 for i in range(len(X))):
            raise ValueError('Expected 2D array')

    def construct_log_class_prior(self, y):
        # Input classes are -1 and 1
        neg_class_count = sum(1 if y_i == -1 else 0 for y_i in y)
        pos_class_count = len(y) - neg_class_count

        neg_log_prior = log(neg_class_count / (pos_class_count + neg_class_count))
        pos_log_prior = log(pos_class_count / (pos_class_count + neg_class_count))

        self.class_prior = [neg_log_prior, pos_log_prior]

    def construct_log_likelihood(self, X, y):
        # Token counts
        token_dict = {'positive': {}, 'negative': {}}
        pos_class_tokens = neg_class_tokens = 0
        len_vocabulary = len(X[0])
        for token_index in range(len(X[0])):
            token_pos_count = sum(doc[token_index] if y[token_index] == 1 else 0 for doc in X)
            token_neg_count = len(y) - token_pos_count
            token_dict['positive'][token_index] = token_pos_count
            token_dict['negative'][token_index] = token_neg_count
            pos_class_tokens = pos_class_tokens + (1 if token_pos_count > 0 else 0)
            neg_class_tokens = neg_class_tokens + (1 if token_neg_count > 0 else 0)

        likelihood = {'positive_features': {}, 'negative_features': {}}
        for token in token_dict['positive']:
            likelihood['positive_features'][token] = log(
                (token_dict['positive'][token] + self.alpha) /
                (token_dict['positive'][token] + len_vocabulary)
            )

        for token in token_dict['negative']:
            likelihood['negative_features'][token] = log(
                (token_dict['negative'][token] + self.alpha) /
                (token_dict['negative'][token] + len_vocabulary)
            )
        self.likelihood = likelihood

    def fit(self, X, y):
        self.validate_xy(X, y)
        self.construct_log_class_prior(y)
        self.construct_log_likelihood(X, y)

        return self

    def predict_log_probability(self):
        """ Calculate the posterior log probability of new sample X"""
