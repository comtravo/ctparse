"""Train a default multinomial bayes classifier"""
from ctparse.corpus import run_corpus
from ctparse.time import corpus, auto_corpus

from ctparse.nb_scorer import train_naive_bayes, save_naive_bayes
# TODO: place handling for the default model file in a separate
# module.
from ctparse.nb import _model_file


def main():
    X, y = run_corpus(corpus.corpus + auto_corpus.corpus)
    mdl = train_naive_bayes(X, y)
    save_naive_bayes(mdl, _model_file)


if __name__ == "__main__":
    main()
