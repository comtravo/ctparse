"""Train a default multinomial bayes classifier"""
from ctparse.corpus import run_corpus
from ctparse.time import corpus, auto_corpus

from ctparse.nb_scorer import train_naive_bayes, save_naive_bayes
from ctparse.loader import DEFAULT_MODEL_FILE


def main():
    X, y = run_corpus(corpus.corpus + auto_corpus.corpus)
    mdl = train_naive_bayes(X, y)
    save_naive_bayes(mdl, DEFAULT_MODEL_FILE)


if __name__ == "__main__":
    main()
