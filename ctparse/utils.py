from .nb_estimator import MultinomialNaiveBayes
import regex as re
from math import exp


class CustomCountVectorizer:
    _white_space = re.compile(r"\s+")

    def __init__(self, ngram_range, vocabulary=None, fixed_vocab=False):
        self.ngram_range = ngram_range
        self.vocabulary = vocabulary
        self.fixed_vocab = fixed_vocab

    def create_ngrams(self, text):
        """Return ngrams"""

        tokens = text

        # handle token n-grams
        min_n, max_n = self.ngram_range
        if max_n != 1:
            original_tokens = tokens
            if min_n == 1:
                # no need to do any slicing for unigrams
                # just iterate through the original tokens
                tokens = list(original_tokens)
                min_n += 1
            else:
                tokens = []

            n_original_tokens = len(original_tokens)

            # bind method outside of loop to reduce overhead
            tokens_append = tokens.append
            space_join = " ".join

            for n in range(min_n,
                           min(max_n + 1, n_original_tokens + 1)):
                for i in range(n_original_tokens - n + 1):
                    tokens_append(space_join(original_tokens[i: i + n]))
        return tokens

    def preprocess(self):
        """Return a callable to preprocess text and perform tokenization"""
        return lambda doc: self.create_ngrams(str(doc))

    def create_feature_matrix(self, documents, set_vocabulary):
        """ Create feature matrix"""
        build_features = self.preprocess()

        all_features = []
        count_matrix = []
        for doc in documents:
            feature_counts = {}
            for feature in build_features(doc):
                if feature in feature_counts:
                    feature_counts[feature] += 1
                else:
                    all_features.append(feature)
                    feature_counts[feature] = 1
            count_matrix.append(feature_counts)
        if set_vocabulary:
            self.vocabulary = sorted(set(all_features))
        count_vectors_matrix = []
        # Build document frequency matrix
        for count_dict in count_matrix:
            doc_vectors = []
            for word in self.vocabulary:
                if word in count_dict.keys():
                    doc_vectors.append(count_dict[word])
                else:
                    doc_vectors.append(0)
            count_vectors_matrix.append(doc_vectors)

        return count_vectors_matrix

    def fit(self, raw_documents):
        """Learn a vocabulary dictionary of all tokens in the raw documents.

        Parameters
        ----------
        raw_documents : iterable of str

        Returns
        -------
        self
        """
        self.fit_transform(raw_documents)
        return self

    def fit_transform(self, raw_documents):
        """Learn the vocabulary dictionary and return term-document matrix.

        Parameters
        ----------
        raw_documents : iterable of str

        Returns
        -------
        X : array, [n_samples, n_features]
            Document-term matrix.
        """
        X = self.create_feature_matrix(raw_documents, set_vocabulary=True)
        return X

    def transform(self, raw_documents):
        """Create term-document matrix based on pre-generated vocabulary"""
        X = self.create_feature_matrix(raw_documents, set_vocabulary=False)
        return X


class CtParsePipeline:
    def __init__(self, transformer: CustomCountVectorizer, estimator: MultinomialNaiveBayes):
        self.transformer = transformer
        self.estimator = estimator

    def fit(self, X, y=None):
        """ Fit the transformer and then fit the Naive Bayes model on the transformed data"""
        X_transformed = self.transformer.fit_transform(X)
        self.estimator = self.estimator.fit(X_transformed, y)
        return self

    def predict_probability(self, X):
        """ Apply the transforms and get probability predictions from the estimator"""
        X_transformed = self.transformer.transform(X)
        log_preds = self.estimator.predict_log_probability(X_transformed)
        preds = [exp(log_pred) for log_pred in log_preds]
        return preds
