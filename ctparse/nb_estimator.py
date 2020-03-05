from math import log


class MultinomialNaiveBayes:
    def __init__(self, alpha=1.0, class_prior=None, likelihood=None, neg_class_count=None,
                 pos_class_count=None, vocab_size=None):
        self.alpha = alpha
        self.class_prior = class_prior
        self.likelihood = likelihood
        self.neg_class_count = neg_class_count
        self.pos_class_count = pos_class_count
        self.neg_class_count = neg_class_count
        self.len_vocabulary = vocab_size

    @staticmethod
    def validate_xy(X, y):
        # Validate dimensions of X and y
        if any(isinstance(y_i, list) for y_i in y):
            raise ValueError('Expected 1D array')
        if len(X) <= 0 and not all(len(X[i]) != 0 for i in range(len(X))):
            raise ValueError('Expected 2D array')

    def construct_log_class_prior(self, y):
        # Input classes are -1 and 1
        self.neg_class_count = sum(1 if y_i == -1 else 0 for y_i in y)
        self.pos_class_count = len(y) - self.neg_class_count

        neg_log_prior = log(self.neg_class_count / (self.pos_class_count + self.neg_class_count))
        pos_log_prior = log(self.pos_class_count / (self.pos_class_count + self.neg_class_count))

        self.class_prior = [neg_log_prior, pos_log_prior]

    def construct_log_likelihood(self, X, y):
        # Token counts
        token_dict = {'positive': {}, 'negative': {}}
        pos_class_tokens = neg_class_tokens = 0
        self.len_vocabulary = len(X[0])
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
                (token_dict['positive'][token] + self.len_vocabulary)
            )

        for token in token_dict['negative']:
            likelihood['negative_features'][token] = log(
                (token_dict['negative'][token] + self.alpha) /
                (token_dict['negative'][token] + self.len_vocabulary)
            )
        self.likelihood = likelihood

    def fit(self, X, y):
        self.validate_xy(X, y)
        self.construct_log_class_prior(y)
        self.construct_log_likelihood(X, y)

        return self

    def predict_log_probability(self, xtest):
        """ Calculate the posterior log probability of new sample X"""
        # Assign the scores with priors of positive and negative class
        neg_score = self.class_prior[0]
        pos_score = self.class_prior[1]

        # Smoothed probabilities are calculated below, these are used when a
        # word in the test document is not found in the given class but is found
        # in another class's feature dict
        smooth_pos = log(1 / (self.pos_class_count + self.len_vocabulary))
        smooth_neg = log(1 / (self.neg_class_count + self.len_vocabulary))

        for token in xtest:
            if token in self.likelihood['positive_features']:
                pos_score += self.likelihood['positive_features'][token]
                neg_score += smooth_neg
            elif token in self.likelihood['negative_features']:
                neg_score += self.likelihood['negative_features'][token]
                pos_score += smooth_pos

        return [neg_score, pos_score]
