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
import kubernetes.client
import kubernetes.config
import os

from owca import config
from typing import Dict


def _start_workload(name, data):
    kubernetes.config.load_kube_config()
    k8s_client = kubernetes.client.CoreV1Api()

    namespace = os.getenv('k8s_namespace', 'default')

    body = kubernetes.client.V1Pod()
    body.metadata = {
            "namespace": namespace,
            "name": 'example_pod_name',
            "labels": 'example_labels'
            }

    k8s_client.create_namespaced_pod(namespace, body)


def run(inventory: Dict, meta_inventory: Dict):
    for workload in inventory['workloads'].keys():
        _start_workload(workload, inventory['workloads'][workload])


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

    run(inventory, meta_inventory)


if __name__ == '__main__':
    main()
