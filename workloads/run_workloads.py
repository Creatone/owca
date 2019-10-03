import argparse
import colorlog
import logging
import os
import sys
import time

from ansible.parsing.dataloader import DataLoader
from ruamel import yaml



log = logging.getLogger('run_workloads')


def init_logging(level: str, log):
    TRACE = 9
    logging.captureWarnings(True)
    logging.addLevelName(TRACE, 'TRACE')
    log_colors = dict(colorlog.default_log_colors, **dict(TRACE='cyan'))

    # formatter and handler
    formatter = colorlog.ColoredFormatter(
        log_colors=log_colors,
        fmt='%(asctime)s %(log_color)s%(levelname)-4s%(reset)s'
        ' %(blue)s[%(name)s]%(reset)s : %(message)s',
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    log.addHandler(handler)
    log.propagate = False  # Because we have own handler.
    log.setLevel(level)

    # Inform about tracing level (because of number of metrics).
    log.log(TRACE, 'Package logger trace messages enabled.')


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-c', '--config',
        help="Configuration", default=None, required=True)

    parser.add_argument(
        '-i', '--inventory',
        help="Inventory", default=None, required=True)

    parser.add_argument(
        '-l',
        '--log-level',
        help='Log level',
        default=logging.INFO,
        dest='log_level',
    )

    args = parser.parse_args()

    init_logging(args.log_level, log)

    loader = DataLoader()
    loader.load_from_file(args.config)
    loader.load_from_file(args.inventory)

    import IPython; IPython.embed()
    pass

def run(config, inventory):
    loader = DataLoader()
    pass


if __name__ == '__main__':
    main()
