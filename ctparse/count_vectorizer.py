from collections import defaultdict
from typing import Dict, Sequence, Tuple, Optional


class CountVectorizer:
    def __init__(self, ngram_range: Tuple[int, int]):
        """Create new count vectorizer that also counts n-grams.

        A count vectorizer builds an internal vocabulary and embeds each input
        by counting for each term in the document how often it appearsin the vocabulary.
        Here also n-grams are considered to be part of the vocabulary and the document
        terms, respectively

        Parameters
        ----------
        ngram_range : Tuple[int, int]
            n-gram range to consider
        """
        self.ngram_range = ngram_range
        self.vocabulary: Optional[Dict[str, int]] = None

    @staticmethod
    def _create_ngrams(
        ngram_range: Tuple[int, int], documents: Sequence[Sequence[str]]
    ) -> Sequence[Sequence[str]]:
        """For each document in documents, replace original tokens by a list of
        all min_n:max_n = self.ngram_range ngrams in that document.

        Parameters
        ----------
        ngram_range : Tuple[int, int]
            Min and max number of ngrams to generate

        documents : Sequence[Sequence[str]]
            A sequence of already tokenized documents

        Returns
        -------
        Sequence[Sequence[str]]
            For each document all ngrams of tokens in the desired range
        """
        min_n, max_n = ngram_range
        space_join = " ".join

        def _create(document: Sequence[str]) -> Sequence[str]:
            doc_len = len(document)
            doc_max_n = min(max_n, doc_len) + 1
            if min_n == 1:
                ngrams = list(document)
                min_nn = min_n + 1
            else:
                ngrams = []
                min_nn = min_n

            for n in range(min_nn, doc_max_n):
                for i in range(0, doc_len - n + 1):
                    ngrams.append(space_join(document[i : i + n]))
            return ngrams

        return [_create(d) for d in documents]

    @staticmethod
    def _get_feature_counts(
        ngram_range: Tuple[int, int], documents: Sequence[Sequence[str]]
    ) -> Sequence[Dict[str, int]]:
        """Count (ngram) features appearing in each document

        Parameters
        ----------
        ngram_range : Tuple[int, int]
            Min and max number of ngrams to generate

        documents : Sequence[Sequence[str]]
            Sequence of documents tokenized as sequence of string

        Returns
        -------
        Tuple[Sequence[Dict[str, int]], Set[str]]
            For each document a dictionary counting how often which feature appeared and
            a set of all features in all documents. Features are according to this
            vectorizers n-gram settings.
        """
        documents = CountVectorizer._create_ngrams(ngram_range, documents)
        count_matrix = []

        for document in documents:
            # This is 5x faster than using a build in Counter
            feature_counts: Dict[str, int] = defaultdict(int)
            for feature in document:
                feature_counts[feature] += 1
            count_matrix.append(feature_counts)
        return count_matrix

    @staticmethod
    def _build_vocabulary(count_matrix: Sequence[Dict[str, int]]) -> Dict[str, int]:
        """Build the vocabulary from feature counts

        Parameters
        ----------
        count_matrix : Sequence[Dict[str, int]]
            Sequence of dicts with counts (values) per feature (keys)

        Returns
        -------
        Dict[str, int]
            The vocabulary as {feature: index} pairs
        """
        all_features = set()
        for feature_counts in count_matrix:
            for feature in feature_counts.keys():
                all_features.add(feature)
        return {word: idx for idx, word in enumerate(sorted(all_features))}

    @staticmethod
    def _create_feature_matrix(
        vocabulary: Dict[str, int], count_matrix: Sequence[Dict[str, int]]
    ) -> Sequence[Dict[int, int]]:
        """Map counts of string features to numerical data (sparse maps of
        `{feature_index: count}`). Here `feature_index` is relative to the vocabulary of
        this vectorizer.

        Parameters
        ----------
        vocabulary : Dict[str, int]
            Vocabulary with {feature: index} mappings

        count_matrix : Sequence[Dict[str, int]]
            Sequence of dictionaries with feature counts

        Returns
        -------
        Sequence[Dict[int, int]]
            For each document a mapping of `feature_index` to a count how often this
            feature appeared in the document.
        """
        len_vocab = len(vocabulary)
        count_vectors_matrix = []
        # Build document frequency matrix
        for count_dict in count_matrix:
            doc_vector: Dict[int, int] = defaultdict(int)
            for word, cnt in count_dict.items():
                idx = vocabulary.get(word, None)
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
        """Learn the vocabulary dictionary and return a term-document matrix. Updates
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
        count_matrix = CountVectorizer._get_feature_counts(self.ngram_range, documents)
        self.vocabulary = CountVectorizer._build_vocabulary(count_matrix)
        return CountVectorizer._create_feature_matrix(self.vocabulary, count_matrix)

    def transform(self, documents: Sequence[Sequence[str]]) -> Sequence[Dict[int, int]]:
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
        if not self.vocabulary:
            raise ValueError("no vocabulary - vectorizer not fitted?")
        count_matrix = CountVectorizer._get_feature_counts(self.ngram_range, documents)
        return CountVectorizer._create_feature_matrix(self.vocabulary, count_matrix)
