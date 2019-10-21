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
import re


from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, List

from wca.allocators import AllocationConfiguration
from wca.config import Numeric, Str
from wca.metrics import MetricName
from wca.nodes import Task
from wca.nodes.nodes import Node
from wca.storage import Storage, DEFAULT_STORAGE


DEFAULT_EVENTS = (MetricName.INSTRUCTIONS, MetricName.CYCLES,
                  MetricName.CACHE_MISSES, MetricName.CACHE_REFERENCES, MetricName.MEMSTALL)


log = logging.getLogger(__name__)


class TaskLabelGenerator:
    @abstractmethod
    def generate(self, task: Task) -> Optional[str]:
        """Generate new label value based on `task` object
        (e.g. based on other label value or one of task resource).
        `task` input parameter should not be modified."""
        ...


@dataclass
class TaskLabelRegexGenerator(TaskLabelGenerator):
    """Generate new label value based on other label value."""
    pattern: str
    repl: str
    source: str = 'task_name'  # by default use `task_name`

    def __post_init__(self):
        # Verify whether syntax for pattern and repl is correct.
        re.sub(self.pattern, self.repl, "")

    def generate(self, task: Task) -> Optional[str]:
        source_val = task.labels.get(self.source, None)
        if source_val is None:
            err_msg = "Source label {} not found in task {}".format(self.source, task.name)
            log.warning(err_msg)
            return None
        return re.sub(self.pattern, self.repl, source_val)


@dataclass
class TaskLabelResourceGenerator(TaskLabelGenerator):
    """Add label based on initial resource assignment of a task."""
    resource_name: str

    def generate(self, task: Task) -> Optional[str]:
        return str(task.resources.get(self.resource_name, "unknown"))


@dataclass
class Config():
    """
    Arguments:
        node: component used for tasks discovery
        metrics_storage: storage to store platform, internal, resource and task metrics
            (defaults to DEFAULT_STORAGE/LogStorage to output for standard error)
        action_delay: iteration duration in seconds (None disables wait and iterations)
            (defaults to 1 second)
        rdt_enabled: enables or disabled support for RDT monitoring
            (defaults to None(auto) based on platform capabilities)
        gather_hw_mm_topology: gather hardware/memory topology based on lshw and ipmctl
            (defaults to None)
        extra_labels: additional labels attached to every metrics
            (defaults to empty dict)
        event_names: perf counters to monitor
            (defaults to instructions, cycles, cache-misses, memstalls)
        enable_derived_metrics: enable derived metrics ips, ipc and cache_hit_ratio
            (based on enabled_event names), default to False
        task_label_generators: component to generate additional labels for tasks
    """
    node: Node
    metrics_storage: Storage = DEFAULT_STORAGE
    action_delay: Numeric(0, 60) = 1.  # [s]
    rdt_enabled: Optional[bool] = None  # Defaults(None) - auto configuration.
    rdt_mb_control_required: bool = False
    rdt_mb_cache_control_required: bool = False
    gather_hw_mm_topology: Optional[bool] = None
    extra_labels: Optional[Dict[Str, Str]] = None
    event_names: List[str] = DEFAULT_EVENTS
    enable_derived_metrics: bool = False
    enable_perf_pmu: bool = True
    task_label_generators: Dict[str, TaskLabelGenerator] = None
    _allocation_configuration: Optional[AllocationConfiguration] = None
    wss_reset_interval: int = 0

    def __post__init(self):
        self.extra_labels = {
                k: str(v) for k, v in self.extra_labels.items()} if self.extra_labels else {}
        pass
