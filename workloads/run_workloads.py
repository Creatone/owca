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

from owca import config
from workloads.runner import Runner


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
            '--inventory',
            help="Path to inventory file.", default=None, required=True)

    parser.add_argument(
            '--meta-inventory',
            help="Path to meta-inventory file.", default=None, required=True)

    args = parser.parse_args()

    inventory = config.load_config(args.inventory)

    meta_inventory = config.load_config(args.meta_inventory)

    runner = Runner(inventory, meta_inventory)

    exit_code = runner.run()
    exit(exit_code)


if __name__ == '__main__':
    main()
