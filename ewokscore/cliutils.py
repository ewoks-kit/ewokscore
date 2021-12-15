import sys
import logging

LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def add_log_parameters(parser):
    parser.add_argument(
        "--log",
        type=str.lower,
        choices=list(LEVELS),
        default="warning",
        help="Log level",
    )


def apply_log_parameters(args):
    logger = logging.getLogger()
    logger.setLevel(LEVELS[args.log])
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)-8s - %(message)s"
    )

    class StdOutFilter(logging.Filter):
        def filter(self, record):
            return record.levelno < logging.WARNING

    class StdErrFilter(logging.Filter):
        def filter(self, record):
            return record.levelno >= logging.WARNING

    h = logging.StreamHandler(sys.stdout)
    h.addFilter(StdOutFilter())
    h.setLevel(logging.DEBUG)
    if formatter is not None:
        h.setFormatter(formatter)
    logger.addHandler(h)

    h = logging.StreamHandler(sys.stderr)
    h.addFilter(StdErrFilter())
    h.setLevel(logging.WARNING)
    if formatter is not None:
        h.setFormatter(formatter)
    logger.addHandler(h)
