import argparse
import colorlog
import logging
import os
import sys
import time

from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager

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

    inventory = InventoryManager(loader=loader, sources=args.inventory)
    variables = VariableManager(loader=loader, inventory=inventory)

    with open(args.config) as f:
        playbooks = yaml.load(f)

    for playbook in playbooks:
        play = Play().load(playbook, variables, loader)
        log.info('Start %s', play.get_name())

        try:
            task_queue_manager = TaskQueueManager(
                        inventory=inventory,
                        variable_manager=variables,
                        loader=loader,
                        passwords={},
                    )

            result = task_queue_manager.run(play)
            print(result)
        finally:
            task_queue_manager.cleanup()


if __name__ == '__main__':
    main()
