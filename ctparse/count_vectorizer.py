from collections import defaultdict
from typing import Dict, Sequence, Tuple, Optional


class CountVectorizer:
    def __init__(self, ngram_range: Tuple[int, int]):
        """Create new count vectorizer that also counts n-grams.

        A count vectorizer builds an internal vocabulary and embeds each input
        by counting for each term in the document how often it appearsin the vocabulary.
        Here also n-grams are considered to be part of the vocabulary and the document terms,
        respectively

        Parameters
        ----------
        ngram_range : Tuple[int, int]
            n-gram range to consider
        """
        self.ngram_range = ngram_range
        self.vocabulary: Optional[Dict[str, int]] = None

    def _create_ngrams(
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

    def _create_feature_matrix(
        self, documents: Sequence[Sequence[str]], set_vocabulary: bool
    ) -> Sequence[Dict[int, int]]:
        """Map documents (sequences of tokens) to numerical data (sparse maps of
        `{feature_index: count}`). Here `feature_index` is relative to the vocabulary of
        this very vectorizer.

        Parameters
        ----------
        documents : Sequence[Sequence[str]]
            Sequence of tokenized input documents
        set_vocabulary : bool
            If `True`, set the vectorizer vocabulary to the ones
            extracted from documents

        Returns
        -------
        Sequence[Dict[int, int]]
            For each document a mapping of `feature_index` to a count how often this
            feature appeared in the document.
        """
        documents = self._create_ngrams(documents)
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

    def fit(self, documents: Sequence[Sequence[str]]) -> "CountVectorizer":
        """Learn a vocabulary dictionary of all tokens in the raw documents.

        Parameters
        ----------
        documents : Sequence[Sequence[str]]
            Sequence of documents, each as a sequence of tokens

        Returns
        -------
        CountVectorizer
            The updated vectorizer, i.e. this updates the internal vocabulary
        """
        self.fit_transform(documents)
        return self

    def fit_transform(
        self, documents: Sequence[Sequence[str]]
    ) -> Sequence[Dict[int, int]]:
        """Learn the vocabulary dictionary and return term-document matrix. Updates
        the internal vocabulary state of the vectorizer.

        Parameters
        ----------
        documents : Sequence[Sequence[str]
            Sequence of documents, each as a sequence of tokens

        Returns
        -------
        Sequence[Dict[int, int]]
            Document-term matrix.
        """
        X = self._create_feature_matrix(documents, set_vocabulary=True)
        return X

    def transform(
        self, documents: Sequence[Sequence[str]]
    ) -> Sequence[Dict[int, int]]:
        """Create term-document matrix based on pre-generated vocabulary. Does *not*
        update the internal state of the vocabulary.

        Parameters
        ----------
        documents : Sequence[Sequence[str]]
            Sequence of documents, each as a sequence of tokens

        Returns
        -------
        Sequence[Dict[int, int]]
            Document-term matrix.
        """
        X = self._create_feature_matrix(documents, set_vocabulary=False)
        return X
