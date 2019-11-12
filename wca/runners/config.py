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

from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, List

from wca.allocators import AllocationConfiguration
from wca.config import Numeric, Str
from wca.metrics import MetricName
from wca.nodes import Node, Task
from wca.storage import Storage, DEFAULT_STORAGE


DEFAULT_EVENTS = (MetricName.INSTRUCTIONS, MetricName.CYCLES,
                  MetricName.CACHE_MISSES, MetricName.CACHE_REFERENCES, MetricName.MEMSTALL)


class TaskLabelGenerator:
    @abstractmethod
    def generate(self, task: Task) -> Optional[str]:
        """Generate new label value based on `task` object
        (e.g. based on other label value or one of task resource).
        `task` input parameter should not be modified."""
        ...


@dataclass
class Config():
    """Config for Runners object.
        node: Component used for tasks discovery.
        metrics_storage: Storage to store platform, internal, resource and task metrics.
            (defaults to DEFAULT_STORAGE/LogStorage to output for standard error)
        action_delay: Iteration duration in seconds (None disables wait and iterations).
            (defaults to 1 second)
        rdt_enabled: Enables or disabled support for RDT monitoring.
            (defaults to None(auto) based on platform capabilities)
        gather_hw_mm_topology: Gather hardware/memory topology based on lshw and ipmctl.
            (defaults to False)
        extra_labels: Additional labels attached to every metrics.
            (defaults to empty dict)
        event_names: Perf counters to monitor.
            (defaults to instructions, cycles, cache-misses, memstalls)
        enable_derived_metrics: Enable derived metrics ips, ipc and cache_hit_ratio.
            (based on enabled_event names, default to False)
        enable_perf_uncore: Enable perf event uncore metrics.
            (defaults to True)
        task_label_generators: Component to generate additional labels for tasks.
            (optional)
        allocation_configuration: Allows fine grained control over allocations.
            (defaults to AllocationConfiguration() instance)
        wss_reset_interval: Interval of reseting wss.
            (defaults to 0, every iteration)
    """
    node: Node
    metrics_storage: Storage = DEFAULT_STORAGE
    action_delay: Numeric(0, 60) = 1.
    rdt_enabled: Optional[bool] = None
    gather_hw_mm_topology: Optional[bool] = False
    extra_labels: Dict[Str, Str] = None
    event_names: List[str] = DEFAULT_EVENTS
    enable_derived_metrics: bool = False
    enable_perf_uncore: bool = True
    task_label_generators: Dict[str, TaskLabelGenerator] = None
    allocation_configuration: Optional[AllocationConfiguration] = None
    wss_reset_interval: int = 0
