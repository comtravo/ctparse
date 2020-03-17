from collections import defaultdict
from typing import Dict, Sequence, Tuple

from .nb_estimator import MultinomialNaiveBayes


class CustomCountVectorizer:
    def __init__(self,
                 ngram_range: Tuple[int, int],
                 vocabulary: Dict[str, int] = None,
                 fixed_vocab: bool = False):
        self.ngram_range = ngram_range
        self.vocabulary = vocabulary
        self.fixed_vocab = fixed_vocab

    def create_ngrams(self, documents: Sequence[Sequence[str]]) -> Sequence[Sequence[str]]:
        """For each document in documents, replace original tokens by a list of
        all min_n:max_n = self.ngram_rangengrams in that document.
        """
        min_n, max_n = self.ngram_range
        space_join = " ".join

        def _create(document: Sequence[str]) -> Sequence[str]:
            doc_len = len(document)
            doc_max_n = min(max_n, doc_len) + 1
            if min_n == 1:
                ngrams = list(document)
                min_nn = min_n + 1
            else:
                ngrams = []
                min_nn = 1

            for n in range(min_nn, doc_max_n):
                for i in range(0, doc_len - n + 1):
                    ngrams.append(space_join(document[i:i+n]))
            return ngrams
        return [_create(d) for d in documents]

    def create_feature_matrix(self, documents: Sequence[Sequence[str]], set_vocabulary: bool) \
            -> Sequence[Dict[int, int]]:
        """Create feature matrix"""
        document_features = self.create_ngrams(documents)
        all_features = set()
        count_matrix = []

        for document_feature in document_features:
            feature_counts: Dict[str, int] = {}
            for feature in document_feature:
                if feature in feature_counts:
                    feature_counts[feature] += 1
                else:
                    all_features.add(feature)
                    feature_counts[feature] = 1
            count_matrix.append(feature_counts)
        if set_vocabulary or not self.vocabulary:
            self.vocabulary = {word: idx for idx, word in enumerate(all_features)}
        len_vocab = len(self.vocabulary)
        count_vectors_matrix = []
        # Build document frequency matrix
        for count_dict in count_matrix:
            doc_vector: Dict[int, int] = defaultdict(int)
            for word, cnt in count_dict.items():
                idx = self.vocabulary.get(word, None)
                if idx is not None:
                    doc_vector[idx] = cnt
            count_vectors_matrix.append(doc_vector)
        # add vocab length in first element
        count_vectors_matrix[0][len_vocab - 1] = count_vectors_matrix[0][len_vocab - 1]
        return count_vectors_matrix

    def fit(self, raw_documents: Sequence[Sequence[str]]) -> 'CustomCountVectorizer':
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

    def fit_transform(self, raw_documents: Sequence[Sequence[str]]) -> Sequence[Dict[int, int]]:
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

    def transform(self, raw_documents: Sequence[Sequence[str]]) -> Sequence[Dict[int, int]]:
        """Create term-document matrix based on pre-generated vocabulary"""
        X = self.create_feature_matrix(raw_documents, set_vocabulary=False)
        return X


class CTParsePipeline:
    def __init__(self, transformer: CustomCountVectorizer, estimator: MultinomialNaiveBayes):
        self.transformer = transformer
        self.estimator = estimator

    def fit(self, X: Sequence[Sequence[str]], y: Sequence[int]) -> 'CTParsePipeline':
        """ Fit the transformer and then fit the Naive Bayes model on the transformed data"""
        X_transformed = self.transformer.fit_transform(X)
        self.estimator = self.estimator.fit(X_transformed, y)
        return self

    def predict_log_proba(self, X: Sequence[Sequence[str]]) -> Sequence[Tuple[float, float]]:
        """ Apply the transforms and get probability predictions from the estimator"""
        X_transformed = self.transformer.transform(X)
        return self.estimator.predict_log_probability(X_transformed)
