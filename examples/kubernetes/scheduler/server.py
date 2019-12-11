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
import logging

from flask import Flask, request
from typing import Dict

from scheduler.algorithms.test_algorithms import TestAlgorithms
from scheduler.utils import ExtenderArgs

from wca.config import register


app = Flask('k8s scheduler extender')

log = logging.getLogger(__name__)


class Server:
    def __init__(self, configuration: Dict[str, str]):
        app = Flask('k8s scheduler extender')
        self.app = app
        self.host = configuration.get('host', 'localhost')
        self.port = configuration.get('port', '12345')
        self.prometheus_ip = configuration.get('prometheus_ip', 'localhost:30900')
        self.k8s_namespace = configuration.get('k8s_namespace', 'default')
        self._algorithms = configuration['algorithms']

        @app.route('/api/scheduler/test')
        def hello():
            return "Hello World"

        @app.route('/api/scheduler/filter', methods=['POST'])
        def filter():
            extender_args = ExtenderArgs(**request.get_json())
            return self._algorithms.filter(extender_args, self.k8s_namespace)

        @app.route('/api/scheduler/prioritize')
        def prioritize():
            return self._algorithms.prioritize()

    def run(self):
        self.app.run(host=self.host, port=self.port, debug=True)


def register_algorithms():
    register(TestAlgorithms)
