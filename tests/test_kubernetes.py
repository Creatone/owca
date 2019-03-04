# Copyright (c) 2018 Intel Corporation
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

import json
from unittest.mock import patch, Mock

from owca.kubernetes import KubernetesNode, KubernetesTask, _calculate_pod_resources, \
    _build_cgroup_path
from owca.testing import relative_module_path


def create_json_fixture_mock(name, status_code=200):
    """ Helper function to shorten the notation. """
    return Mock(json=Mock(
        return_value=json.load(
            open(relative_module_path(__file__, 'fixtures/' + name + '.json'))),
        status_code=status_code))


@patch('requests.get', return_value=create_json_fixture_mock('kubernetes_get_state', 200))
def test_get_tasks(get_mock):
    node = KubernetesNode()
    tasks = node.get_tasks()
    assert len(tasks) == 2
    task = KubernetesTask(name='test',
                          task_id='4d6a81df-3448-11e9-8e1d-246e96663c22',
                          qos='burstable',
                          labels={'exampleKey': 'value'},
                          resources={'requests_cpu': 0.25,
                                     'requests_memory': 64*1024**2},
                          cgroup_path='/kubepods/burstable/pod4d6a81df'
                                      '-3448-11e9-8e1d-246e96663c22/',
                          subcgroups_paths=['/kubepods/burstable/pod4d'
                                            '6a81df-3448-11e9-8e1d-246'
                                            'e96663c22/eb9c378219b6a4e'
                                            'fc034ea8898b19faa0e27c7b2'
                                            '0b8eb254fda361cceacf8e90/'])
    assert tasks[0] == task

    task = KubernetesTask(name='test2',
                          task_id='567975a0-3448-11e9-8e1d-246e96663c22',
                          qos='besteffort',
                          labels={},
                          resources={},
                          cgroup_path='/kubepods/besteffort/pod567975a0-3448-'
                                      '11e9-8e1d-246e96663c22/',
                          subcgroups_paths=['/kubepods/besteffort/pod5'
                                            '67975a0-3448-11e9-8e1d-24'
                                            '6e96663c22/e90bbbb3b060ba'
                                            'a1d354cd9b26f353d66fbb08d'
                                            '785abd32f4f6ec52ac843a2e7/'])
    assert tasks[1] == task


@patch('requests.get', return_value=create_json_fixture_mock('kubernetes_get_state_not_ready', 200))
def test_get_tasks_not_all_ready(get_mock):
    node = KubernetesNode()
    tasks = node.get_tasks()
    assert len(tasks) == 0


def test_calculate_resources_empty():
    container_spec = [{'resources': {}}]
    assert {} == _calculate_pod_resources(container_spec)


def test_calculate_resources_with_requests_and_limits():
    container_spec = [
        {'resources': {'limits':
                       {'cpu': '250m',
                        'memory': '64Mi'},
                       'requests':
                       {'cpu': '250m',
                        'memory': '64Mi'}}}]
    assert {'limits_cpu': 0.25, 'limits_memory': 64*1024**2,
            'requests_cpu': 0.25, 'requests_memory':
                64*1024**2} == _calculate_pod_resources(container_spec)


def test_calculate_resources_multiple_containers():
    container_spec = [{'resources': {'requests': {'cpu': '250m',
                                                  'memory': '67108864'}}},
                      {'resources': {'requests': {'cpu': '100m',
                                                  'memory': '32Mi'}}}]
    assert {'requests_cpu': 0.35, 'requests_memory':
            67108864 + 32 * 1024 ** 2} == _calculate_pod_resources(container_spec)


def test_find_cgroup_path_for_pod_systemd():
    cgroup_driver = 'systemd'
    qos = 'burstable'
    pod_id = '12345-67890'
    assert '/kubepods.slice/kubepods-burstable.slice/' \
           'kubepods-burstable-pod12345_67890.slice/' == \
           _build_cgroup_path(cgroup_driver, qos, pod_id)


def test_find_cgroup_path_pod_cgroupfs():
    cgroup_driver = 'cgroupfs'
    qos = 'burstable'
    pod_id = '12345-67890'
    assert '/kubepods/burstable/' \
           'pod12345-67890/' == \
           _build_cgroup_path(cgroup_driver, qos, pod_id)