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

from typing import Dict, Tuple, Optional, List

from wca.allocations import AllocationValue, BoxedNumeric
from wca.allocators import AllocationType
from wca.containers import ContainerInterface
from wca.cgroups import QUOTA_NORMALIZED_MAX
from wca.metrics import Metric


class QuotaAllocationValue(BoxedNumeric):

    def __init__(self, normalized_quota: float, container: ContainerInterface, common_labels: dict):
        self.normalized_quota = normalized_quota
        self.cgroup = container.get_cgroup()
        self.subcgroups = container.get_subcgroups()
        super().__init__(value=normalized_quota, common_labels=common_labels,
                         min_value=0, max_value=1.0)

    def generate_metrics(self):
        metrics = super().generate_metrics()
        for metric in metrics:
            metric.labels.update(allocation_type=AllocationType.QUOTA)
            metric.name = 'allocation_%s' % AllocationType.QUOTA.value
        return metrics

    def perform_allocations(self):
        self.cgroup.set_quota(self.value)
        for subcgroup in self.subcgroups:
            subcgroup.set_quota(QUOTA_NORMALIZED_MAX)


class SharesAllocationValue(BoxedNumeric):

    def __init__(self, normalized_shares: float, container: ContainerInterface,
                 common_labels: Dict[str, str]):
        self.normalized_shares = normalized_shares
        self.cgroup = container.get_cgroup()
        super().__init__(value=normalized_shares, common_labels=common_labels, min_value=0)

    def generate_metrics(self):
        metrics = super().generate_metrics()
        for metric in metrics:
            metric.labels.update(allocation_type=AllocationType.SHARES)
            metric.name = 'allocation_%s' % AllocationType.SHARES.value
        return metrics

    def perform_allocations(self):
        self.cgroup.set_shares(self.value)


class CPUSetAllocationValue(AllocationValue):

    def __init__(self, value: str, container: ContainerInterface):
        assert isinstance(value, str)
        self.cgroup = container.get_cgroup()
        self.value = _parse_cpuset_string(value)

    def __repr__(self):
        return repr(self.value)

    def calculate_changeset(self, current: 'CPUSetAllocationValue') \
            -> Tuple['CPUSetAllocationValue', Optional['CPUSetAllocationValue']]:
        raise NotImplementedError

    def generate_metrics(self) -> List[Metric]:
        raise NotImplementedError

    def validate(self):
        raise NotImplementedError

    def perform_allocations(self):
        self.validate()
        self.cgroup.set_cpusets(self.value)


def _parse_cpuset_string(value: str):
    cores = set()

    if not value:
        return cores

    ranges = value.split(',')

    for r in ranges:
        boundaries = r.split('-')

        if len(boundaries) == 1:
            cores.add(int(boundaries[0]))
        elif len(boundaries) == 2:
            start = int(boundaries[0])
            end = int(boundaries[1])

            for i in range(start, end):
                cores.add(i)

    return cores
