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

    with open(args.config) as f:
        config = yaml.load(f.read())
    with open(args.inventory) as f:
        inventory = yaml.load(f.read())

    run(config, inventory)


def run(config, inventory):
    name = config['name']

    hosts = config['hosts']
    if isinstance(hosts, str):
        hosts = inventory[config['hosts']]

    tasks = config['tasks']
    log.info('Run %r', name)

    for task in tasks:
        log.info('Start %r', task['name'])
        run_task(task, inventory)
        log.info('End %r', task['name'])


def run_task(task, inventory):
    for block in task['block']:
        if 'shell' in block:
            command = block['shell']
            print(command)
        # os.system(command)
    return


if __name__ == '__main__':
    main()
