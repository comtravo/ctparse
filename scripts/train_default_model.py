"""Train a default multinomial bayes classifier"""
import argparse
from ctparse.corpus import run_corpus, make_partial_rule_dataset, load_timeparse_corpus
from ctparse.time import corpus, auto_corpus

from ctparse.nb_scorer import train_naive_bayes, save_naive_bayes
from ctparse.loader import DEFAULT_MODEL_FILE
import logging

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--legacy",
        help="Use legacy dataset (ctparse.time.corpus and ctparse.time.auto_corpus as training data)",
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
        X, y = zip(*make_partial_rule_dataset(entries, timeout=10.0, progress=True))
        X_combined.extend(X)
        y_combined.extend(y)

    if len(X) == 0:
        raise ValueError("Need to specify at least a dataset for training")

    mdl = train_naive_bayes(X_combined, y_combined)
    save_naive_bayes(mdl, DEFAULT_MODEL_FILE)


if __name__ == "__main__":
    main()
