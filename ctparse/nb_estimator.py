from math import log, exp


def log_sum_exp(x):
    max_value = max(x)
    x_normalized = [x_i - max_value for x_i in x]
    sum_of_exp = sum([exp(xn_i) for xn_i in x_normalized])
    return max_value + log(sum_of_exp)


class MultinomialNaiveBayes:
    def __init__(self, alpha=1.0, class_prior=None, log_likelihood=None, token_count=None):
        self.alpha = alpha
        self.class_prior = class_prior
        self.log_likelihood = log_likelihood
        self.token_counts = token_count

    @staticmethod
    def validate_xy(X, y):
        # Validate dimensions of X and y
        if any(isinstance(y_i, list) for y_i in y):
            raise ValueError('Expected 1D array')
        if len(X) <= 0 and not all(len(X[i]) != 0 for i in range(len(X))):
            raise ValueError('Expected 2D array')

    # @staticmethod
    # def binarize_y(y):
    #     return [1 if y_i == 1 else 0 for y_i in y]

    def construct_log_class_prior(self, y):
        # Input classes are -1 and 1
        neg_class_count = sum(1 if y_i == -1 else 0 for y_i in y)
        pos_class_count = len(y) - neg_class_count

        neg_log_prior = log(neg_class_count / (pos_class_count + neg_class_count))
        pos_log_prior = log(pos_class_count / (pos_class_count + neg_class_count))
        self.class_prior = [neg_log_prior, pos_log_prior]

    def construct_log_likelihood(self, X, y):
        # Token counts
        vocabulary_len = len(X[0])
        token_counts = {'negative_class': [], 'positive_class': []}
        for token_index in range(vocabulary_len):
            token_pos_count = sum(doc[token_index] if y[doc_index] == 1
                                  else 0 for doc_index, doc in enumerate(X))
            token_neg_count = sum(doc[token_index] if y[doc_index] == -1
                                  else 0 for doc_index, doc in enumerate(X))
            token_counts['positive_class'].append(token_pos_count + self.alpha)
            token_counts['negative_class'].append(token_neg_count + self.alpha)

        self.token_counts = token_counts
        token_pos_class_sum = sum(token_counts['positive_class'])
        token_neg_class_sum = sum(token_counts['negative_class'])

        log_likelihood = {'negative_class': [], 'positive_class': []}
        for token_ind in range(vocabulary_len):
            log_likelihood['positive_class'].append(
                log(token_counts['positive_class'][token_ind]) - log(token_pos_class_sum)
            )

            log_likelihood['negative_class'].append(
                log(token_counts['negative_class'][token_ind]) - log(token_neg_class_sum)
            )
        self.log_likelihood = log_likelihood

    def fit(self, X, y):
        self.validate_xy(X, y)
        self.construct_log_class_prior(y)
        self.construct_log_likelihood(X, y)

        return self

    def predict_log_probability(self, xtest):
        """ Calculate the posterior log probability of new sample X"""
        # Initialise the scores with priors of positive and negative class
        neg_score = self.class_prior[0]
        pos_score = self.class_prior[1]
        ll = []
        for word in xtest:
            for token_index in range(len(word)):
                pos_score += (self.log_likelihood['positive_class'][token_index] *
                              word[token_index])

                neg_score += (self.log_likelihood['negative_class'][token_index] *
                              word[token_index])
                ll.append([self.log_likelihood['negative_class'][token_index],
                           self.log_likelihood['positive_class'][token_index]])
        joint_log_likelihood = [neg_score, pos_score]
        # Normalize the scores
        log_prob_x = log_sum_exp(joint_log_likelihood)
        return [score - log_prob_x for score in joint_log_likelihood]
