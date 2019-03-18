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


"""Module for independent simple helper functions."""

import os
from typing import List, Dict, Union, Optional
from unittest.mock import mock_open, Mock, patch, MagicMock

from owca import platforms
from owca.allocators import AllocationConfiguration
from owca.containers import Container
from owca.detectors import ContendedResource, ContentionAnomaly, LABEL_WORKLOAD_INSTANCE
from owca.metrics import Metric, MetricType
from owca.nodes import TaskId, Task
from owca.platforms import RDTInformation
from owca.resctrl import ResGroup
from owca.runners import Runner


def relative_module_path(module_file, relative_path):
    """Returns path relative to current python module."""
    dir_path = os.path.dirname(os.path.realpath(module_file))
    return os.path.join(dir_path, relative_path)


def create_open_mock(paths: Dict[str, Mock]):
    """Creates open_mocks registry based on multiple path.

    You can access created open_mocks by using __getitem__ functions like this:
    OpenMock({'path':'body')['path']. Useful for write mocks assertions.

    For typical example of usage, check tests/test_testing:test_create_open_mock()

    """

    class OpenMock:
        def __init__(self, paths: Dict[str, Union[str, Mock]]):
            self.paths = {os.path.normpath(k): v for k, v in paths.items()}
            self._mocks = {}

        def __call__(self, path, mode='rb'):
            """Used instead of open function."""
            path = os.path.normpath(path)
            if path not in self.paths:
                raise Exception('opening %r is not mocked with OpenMock!' % path)
            mock_or_str = self.paths[path]
            if isinstance(mock_or_str, str) or isinstance(mock_or_str, bytes):
                mock = mock_open(read_data=mock_or_str)
                self._mocks[path] = mock
            else:
                mock = self.paths[path]
            return mock(path, mode)

        def __getitem__(self, path):
            path = os.path.normpath(path)
            if path not in self._mocks:
                raise Exception('mock %r was not open!' % path)

            return self._mocks[path]

    return OpenMock(paths)


def anomaly(contended_task_id: TaskId, contending_task_ids: List[TaskId],
            metrics: List[Metric] = None):
    """Helper method to create simple anomaly for single task.
    It is always about memory contention."""
    return ContentionAnomaly(
        contended_task_id=contended_task_id,
        contending_task_ids=contending_task_ids,
        resource=ContendedResource.MEMORY_BW,
        metrics=metrics or [],
    )


def task(cgroup_path, labels=None, resources=None):
    """Helper method to create task with default values."""
    prefix = cgroup_path.replace('/', '')
    return Task(
        cgroup_path=cgroup_path,
        name=prefix + '_tasks_name',
        task_id=prefix + '_task_id',
        labels=labels or dict(),
        resources=resources or dict()
    )


def container(cgroup_path, resgroup_name=None, with_config=False):
    """Helper method to create container with patched subsystems."""
    with patch('owca.containers.ResGroup'), patch('owca.containers.PerfCounters'):
        return Container(
            cgroup_path,
            rdt_enabled=False, platform_cpus=1,
            allocation_configuration=AllocationConfiguration() if with_config else None,
            resgroup=ResGroup(name=resgroup_name) if resgroup_name is not None else None
        )


def metric(name, labels=None):
    """Helper method to create metric with default values. Value is ignored during tests."""
    return Metric(name=name, value=1234, labels=labels or {})


def allocation_metric(allocation_type, value, **labels):
    """Helper to create allocation typed like metric"""

    name = labels.pop('name', 'allocation')

    if allocation_type is not None:
        labels = dict(allocation_type=allocation_type, **(labels or dict()))

    return Metric(
        name='%s_%s' % (name, allocation_type),
        type=MetricType.GAUGE,
        value=value,
        labels=labels
    )


class DummyRunner(Runner):

    def run(self):
        pass


platform_mock = Mock(
    spec=platforms.Platform,
    sockets=1,
    rdt_information=RDTInformation(
        cbm_mask='fffff',
        min_cbm_bits='1',
        rdt_mb_control_enabled=False,
        num_closids=2,
        mb_bandwidth_gran=None,
        mb_min_bandwidth=None,
    ))


def assert_subdict(got_dict: dict, expected_subdict: dict):
    """Assert that one dict is a subset of another dict in recursive manner.
    """
    for expected_key, expected_value in expected_subdict.items():
        if expected_key not in got_dict:
            raise AssertionError('key %r not found in %r' % (expected_key, got_dict))
        got_value = got_dict[expected_key]
        if isinstance(expected_value, dict):
            # for dict use subsets
            if not isinstance(got_value, dict):
                raise AssertionError('expected dict type at %r key, got %r' % (
                    expected_key, type(got_value)))
            assert_subdict(got_value, expected_value)
        else:
            # for other types check ordinary equality operator
            assert got_value == expected_value, \
                'value differs got=%r expected=%r at key=%r' % (
                    got_value, expected_value, expected_key)


def _is_dict_match(got_dict: dict, expected_subdict: dict):
    """Match values and keys from dict (non recursive)."""
    for expected_key, expected_value in expected_subdict.items():
        if expected_key not in got_dict:
            return False
        else:
            if got_dict[expected_key] != expected_value:
                return False
    return True


def assert_metric(got_metrics: List[Metric],
                  expected_metric_name: str,
                  expected_metric_some_labels: Optional[Dict] = None,
                  expected_metric_value: Optional[Union[float, int]] = None,
                  ):
    """Assert that given metrics exists in given set of metrics."""
    found_metric = None
    for got_metric in got_metrics:
        if got_metric.name == expected_metric_name:
            # found by name, should we check labels ?
            if expected_metric_some_labels is not None:
                # yes check by labels
                if _is_dict_match(got_metric.labels, expected_metric_some_labels):
                    found_metric = got_metric
                    break
            else:
                found_metric = got_metric
                break
    if not found_metric:
        raise AssertionError('metric %r not found' % expected_metric_name)
    # Check values as well
    if expected_metric_value is not None:
        assert found_metric.value == expected_metric_value, 'metric value differs'


def redis_task_with_default_labels(task_id):
    """Returns task instance and its labels."""
    task_labels = {
        'org.apache.aurora.metadata.load_generator': 'rpc-perf-%s' % task_id,
        'org.apache.aurora.metadata.name': 'redis-6792-%s' % task_id,
        LABEL_WORKLOAD_INSTANCE: 'redis_6792_%s' % task_id
    }
    return task('/%s' % task_id, resources=dict(cpus=8.), labels=task_labels)


TASK_CPU_USAGE = 23
OWCA_MEMORY_USAGE = 100


def prepare_runner_patches(fun):
    def _decorated_function():
        with patch('owca.cgroups.Cgroup.get_pids', return_value=['123']), \
             patch('owca.cgroups.Cgroup.set_quota'), \
             patch('owca.cgroups.Cgroup.set_shares'), \
             patch('owca.containers.Cgroup.get_measurements',
                   return_value=dict(cpu_usage=TASK_CPU_USAGE)), \
             patch('owca.containers.PerfCounters'), \
             patch('owca.platforms.collect_platform_information',
                   return_value=(platform_mock, [metric('platform-cpu-usage')], {})), \
             patch('owca.platforms.collect_topology_information', return_value=(1, 1, 1)), \
             patch('owca.profiling._durations',
                   new=MagicMock(items=Mock(return_value=[('profiled_function', 1.)]))), \
             patch('owca.resctrl.ResGroup.add_pids'), \
             patch('owca.resctrl.ResGroup.get_measurements'), \
             patch('owca.resctrl.ResGroup.get_mon_groups'), \
             patch('owca.resctrl.ResGroup.remove'), \
             patch('owca.resctrl.ResGroup.write_schemata'), \
             patch('owca.runners.measurement.are_privileges_sufficient', return_value=True), \
             patch('resource.getrusage', return_value=Mock(ru_maxrss=OWCA_MEMORY_USAGE)), \
             patch('owca.resctrl.read_mon_groups_relation', return_value={'': []}), \
             patch('owca.runners.measurement.check_resctrl', return_value=True), \
             patch('owca.runners.measurement.are_privileges_sufficient', return_value=True), \
             patch('owca.runners.allocation.cleanup_resctrl'):
            fun()

    return _decorated_function
