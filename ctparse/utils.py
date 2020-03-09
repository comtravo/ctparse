from .nb_estimator import MultinomialNaiveBayes
import regex as re


class CustomCountVectorizer:
    _white_space = re.compile(r"\s+")

    def __init__(self, ngram_range, vocabulary=None, fixed_vocab=False):
        self.ngram_range = ngram_range
        self.vocabulary = vocabulary
        self.fixed_vocab = fixed_vocab

    def create_ngrams(self, text):
        """ Return ngrams"""

        text = self._white_space.sub("", text)
        txt_len = len(text)
        min_r, max_r = self.ngram_range

        if min_r == 1:
            # iterate through str for unigrams
            ngrams = list(text)
            min_r += 1
        else:
            ngrams = []

        # bind method outside of loop to reduce overhead
        ngrams_append = ngrams.append

        for n in range(min_r, min(max_r + 1, txt_len + 1)):
            for i in range(txt_len - n + 1):
                ngrams_append(text[i: i + n])
        return ngrams

    def preprocess(self):
        """ Return a callable to preprocess text and perform tokenization"""
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

        This is equivalent to fit followed by transform, but more efficiently
        implemented.

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
        """ Create term-document matrix based on pre-generated vocabulary"""

        X = self.create_feature_matrix(raw_documents, set_vocabulary=False)
        return X


class CtParsePipeline:
    def __init__(self, transformer: CustomCountVectorizer, estimator: MultinomialNaiveBayes):
        self.transformer = transformer
        self.estimator = estimator

    def fit(self, X, y=None):
        """ Fit the transformer and then fit the Naive Bayes model on the transformed data"""
        X_transformed = self.transformer.fit(X)
        model = self.estimator.fit(X_transformed, y)

        return model

    def predict_probability(self, X):
        """ Apply the transforms and get probability predictions from the estimator"""
        X_transformed = self.transformer.transform(X)
        preds = self.estimator.predict_log_probability(X_transformed)
        return preds
