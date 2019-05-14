# Copyright (c) 2019 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
import logging

from owca import config
from owca import logger

from workloads import runner


log = logging.getLogger('owca.run_workloads')


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
            '--inventory',
            help="Path to inventory file.", default=None, required=True)

    parser.add_argument(
            '--meta-inventory',
            help="Path to meta-inventory file.", default=None, required=True)

    parser.add_argument(
        '-l',
        '--log-level',
        help='Log level for modules (by default for owca) in [module:]level form,'
             'where level can be one of: CRITICAL,ERROR,WARNING,INFO,DEBUG,TRACE'
             'Example -l debug -l example:debug. Defaults to owca:INFO.'
             'Can be overridden at runtime with config.yaml "loggers" section.',
        default=[],
        action='append',
        dest='levels',
    )

    args = parser.parse_args()

    # Initialize logging subsystem from command line options.
    log_levels = logger.parse_loggers_from_list(args.levels)
    log_levels.setdefault(logger.DEFAULT_MODULE, 'info')
    logger.configure_loggers_from_dict(log_levels)

    log.info('Start running workloads')

    inventory = config.load_config(args.inventory)

    meta_inventory = config.load_config(args.meta_inventory)

    workload_runner = runner.Runner(inventory, meta_inventory)

    exit_code = workload_runner.run()
    exit(exit_code)


if __name__ == '__main__':
    main()
