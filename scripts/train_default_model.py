"""Train a default multinomial bayes classifier"""
import argparse
import logging

from ctparse.corpus import (load_timeparse_corpus, make_partial_rule_dataset,
                            run_corpus)
from ctparse.loader import DEFAULT_MODEL_FILE
from ctparse.nb_scorer import save_naive_bayes, train_naive_bayes
from ctparse.scorer import DummyScorer
from ctparse.time import auto_corpus, corpus

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--legacy",
        help="Use legacy dataset (ctparse.time.corpus and ctparse.time.auto_corpus)",
        action='store_true'
    )
    parser.add_argument(
        "--dataset", help="Dataset file")
    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

    X_combined = []
    y_combined = []

    if args.legacy:
        logger.info("Loading legacy dataset")
        X, y = run_corpus(corpus.corpus + auto_corpus.corpus)
        X_combined.extend(X)
        y_combined.extend(y)

    if args.dataset:
        logger.info("Loading dataset {}".format(args.dataset))
        entries = load_timeparse_corpus(args.dataset)
        X, y = zip(*make_partial_rule_dataset(
            entries, scorer=DummyScorer(), timeout=0,
            max_stack_depth=100, progress=True))
        X_combined.extend(X)
        y_combined.extend(y)

        if len(X) == 0:
            raise ValueError("Need to specify at least a dataset for training")

    mdl = train_naive_bayes(X_combined, y_combined)
    save_naive_bayes(mdl, DEFAULT_MODEL_FILE)


if __name__ == "__main__":
    main()
