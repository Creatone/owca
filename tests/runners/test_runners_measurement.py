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

from unittest.mock import Mock

import pytest

from owca import storage
from owca.mesos import MesosNode
from owca.runners.measurement import MeasurementRunner, _build_tasks_metrics
from owca.testing import assert_metric, redis_task_with_default_labels, prepare_runner_patches, \
    TASK_CPU_USAGE, OWCA_MEMORY_USAGE, metric, DEFAULT_METRIC_VALUE


@prepare_runner_patches
def test_measurements_runner():
    # Node mock
    t1 = redis_task_with_default_labels('t1')
    t2 = redis_task_with_default_labels('t2')

    runner = MeasurementRunner(
        node=Mock(spec=MesosNode,
                  get_tasks=Mock(return_value=[t1, t2])),
        metrics_storage=Mock(spec=storage.Storage, store=Mock()),
        rdt_enabled=False,
        extra_labels=dict(extra_label='extra_value')  # extra label with some extra value
    )

    # Mock to finish after one iteration.
    runner._wait = Mock()
    runner._finish = True
    runner.run()

    # Check output metrics.
    got_metrics = runner._metrics_storage.store.call_args[0][0]

    # Internal owca metrics are generated (owca is running, number of task under control,
    # memory usage and profiling information)
    assert_metric(got_metrics, 'owca_up', dict(extra_label='extra_value'))
    assert_metric(got_metrics, 'owca_tasks', expected_metric_value=2)
    # owca & its children memory usage (in bytes)
    assert_metric(got_metrics, 'owca_memory_usage_bytes',
                  expected_metric_value=OWCA_MEMORY_USAGE * 2 * 1024)
    assert_metric(got_metrics, 'owca_duration_seconds', dict(function='profiled_function'),
                  expected_metric_value=1)

    # Measurements metrics about tasks, based on get_measurements mocks.
    assert_metric(got_metrics, 'cpu_usage', dict(task_id=t1.task_id),
                  expected_metric_value=TASK_CPU_USAGE)
    assert_metric(got_metrics, 'cpu_usage', dict(task_id=t2.task_id),
                  expected_metric_value=TASK_CPU_USAGE)


@pytest.mark.parametrize('tasks_labels, tasks_measurements, expected_metrics', [
    ({}, {}, []),
    ({'t1_task_id': {'app': 'redis'}}, {}, []),
    ({'t1_task_id': {'app': 'redis'}}, {'t1_task_id': {'cpu_usage': DEFAULT_METRIC_VALUE}},
     [metric('cpu_usage', {'app': 'redis'})]),
])
def test_build_tasks_metrics(tasks_labels, tasks_measurements, expected_metrics):
    assert expected_metrics == _build_tasks_metrics(tasks_labels, tasks_measurements)
