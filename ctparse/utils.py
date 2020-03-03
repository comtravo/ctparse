import regex as re


class CustomCountVectorizer:
    _white_space = re.compile(r"\s+")

    def __init__(self, ngram_range, tokenizer, vocabulary=None, fixed_vocab=False):
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
        return lambda doc: self._char_ngrams(doc)

    def create_feature_matrix(self, documents):
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

    def fit(self, raw_documents, y=None):
        """Learn a vocabulary dictionary of all tokens in the raw documents.

        Parameters
        ----------
        raw_documents : iterable
            An iterable which yields either str, unicode or file objects.

        Returns
        -------
        self
        """
        self.fit_transform(raw_documents)
        return self

    def fit_transform(self, raw_documents, y=None):
        """Learn the vocabulary dictionary and return term-document matrix.

        This is equivalent to fit followed by transform, but more efficiently
        implemented.

        Parameters
        ----------
        raw_documents : iterable
            An iterable which yields either str, unicode or file objects.

        Returns
        -------
        X : array, [n_samples, n_features]
            Document-term matrix.
        """

        X = self.create_feature_matrix(raw_documents)
        return X

