import pytest
from ctparse.count_vectorizer import CountVectorizer


@pytest.mark.parametrize(
    "ngrams,doc,result",
    [
        ((1, 1), ["a", "b", "c"], ["a", "b", "c"]),
        ((1, 2), ["a", "b", "c"], ["a", "b", "c", "a b", "b c"]),
        ((2, 2), ["a", "b", "c"], ["a b", "b c"]),
        ((1, 3), ["a", "b"], ["a", "b", "a b"]),
        ((2, 3), ["a", "b"], ["a b"]),
    ],
)
def test_ngrams(ngrams, doc, result):
    assert CountVectorizer._create_ngrams(ngrams, [doc]) == [result]


def test_count_vectorizer_fit_and_transform():
    cv = CountVectorizer((1, 2))
    cv = cv.fit([["a", "b", "c"], ["c", "d"]])
    assert cv.vocabulary
    assert cv.transform([["b"]]) == [{cv.vocabulary["b"]: 1, 6: 0}]


def test_count_vectorizer_fit_transform():
    cv = CountVectorizer((1, 2))
    X = cv.fit_transform([["a", "b"], ["b", "c"]])
    assert cv.vocabulary
    assert X == [
        {
            cv.vocabulary["a"]: 1,
            cv.vocabulary["b"]: 1,
            cv.vocabulary["a b"]: 1,
            len(cv.vocabulary) - 1: 0,
        },
        {cv.vocabulary["b"]: 1, cv.vocabulary["c"]: 1, cv.vocabulary["b c"]: 1},
    ]


def test_count_vectorizer_transform_no_fit():
    cv = CountVectorizer((1, 2))
    with pytest.raises(ValueError):
        cv.transform([["a"]])
