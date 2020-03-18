from collections import defaultdict
from typing import Dict, Sequence, Tuple, Optional

from .nb_estimator import MultinomialNaiveBayes


class CustomCountVectorizer:
    def __init__(self, ngram_range: Tuple[int, int]):
        """Create new count vectorizer that also counts n-grams.

        A count vectorizer builds an internal vocabulary and embeds each input
        by counting for each term in the document how often it appeary in the vocabulary.
        Here also n-grams are considered to be part of the vocabulary and the document terms,
        respectively

        Parameters
        ----------
        ngram_range : Tuple[int, int]
            n-gram range to consider
        """
        self.ngram_range = ngram_range
        self.vocabulary: Optional[Dict[str, int]] = None

    def create_ngrams(
        self, documents: Sequence[Sequence[str]]
    ) -> Sequence[Sequence[str]]:
        """For each document in documents, replace original tokens by a list of
        all min_n:max_n = self.ngram_range ngrams in that document.

        Parameters
        ----------
        documents : Sequence[Sequence[str]]
            A sequence of already tokenized documents

        Returns
        -------
        Sequence[Sequence[str]]
            For each document all ngrams of tokens in the desired range
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
                    ngrams.append(space_join(document[i:i + n]))
            return ngrams

        return [_create(d) for d in documents]

    def create_feature_matrix(
        self, documents: Sequence[Sequence[str]], set_vocabulary: bool
    ) -> Sequence[Dict[int, int]]:
        """Map documents (sequences of tokens) to numerical data (sparse maps of
        {feature_index: count})

        Parameters
        ----------
        documents : Sequence[Sequence[str]]
            sequence of tokenized input documents
        set_vocabulary : bool
            if True, set the vectorizer vocabulary to the ones
            extracted from documents

        Returns
        -------
        Sequence[Dict[int, int]]
            for each document a mapping of feature_index -> counts
        """
        documents = self.create_ngrams(documents)
        all_features = set()
        count_matrix = []

        for document in documents:
            # This is 5x faster than using a build in Counter
            feature_counts: Dict[str, int] = {}
            for feature in document:
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

    def fit(self, raw_documents: Sequence[Sequence[str]]) -> "CustomCountVectorizer":
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

    def fit_transform(
        self, raw_documents: Sequence[Sequence[str]]
    ) -> Sequence[Dict[int, int]]:
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

    def transform(
        self, raw_documents: Sequence[Sequence[str]]
    ) -> Sequence[Dict[int, int]]:
        """Create term-document matrix based on pre-generated vocabulary"""
        X = self.create_feature_matrix(raw_documents, set_vocabulary=False)
        return X


class CTParsePipeline:
    def __init__(
        self, transformer: CustomCountVectorizer, estimator: MultinomialNaiveBayes
    ):
        """Setup a pipeline of feature extraction and naive bayes. Overkill for what it does
        but leaves room to use different models/features in the future

        Parameters
        ----------
        transformer : CustomCountVectorizer
            feature extraction step
        estimator : MultinomialNaiveBayes
            naive bayes model
        """
        self.transformer = transformer
        self.estimator = estimator

    def fit(self, X: Sequence[Sequence[str]], y: Sequence[int]) -> "CTParsePipeline":
        """Fit the transformer and then fit the Naive Bayes model on the transformed data

        Returns
        -------
        CTParsePipeline
            Returns the fitter pipeline
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
            For each document the tuple of negative/positive log probability from the naive
            bayes model
        """
        X_transformed = self.transformer.transform(X)
        return self.estimator.predict_log_probability(X_transformed)
