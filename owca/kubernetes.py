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

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List
from urllib.parse import urljoin
import logging
import requests

from owca import logger
from owca.metrics import MetricName
from owca.nodes import Node, Task

DEFAULT_EVENTS = (MetricName.INSTRUCTIONS, MetricName.CYCLES, MetricName.CACHE_MISSES)

log = logging.getLogger(__name__)


@dataclass
class KubernetesTask(Task):
    qos: str

    def __hash__(self):
        return super().__hash__()

    def get_summary(self) -> str:
        """Short representation of task. Used for logging."""
        return "({} {} -> {})".format(self.name,
                                      self.task_id,
                                      self.subcgroups_paths)


class CgroupDriverType(str, Enum):
    SYSTEMD = "systemd"
    CGROUPFS = "cgroupfs"


@dataclass
class KubernetesNode(Node):
    # We need to know what cgroup driver is used to properly build cgroup paths for pods.
    #   Reference in source code for kubernetes version stable 1.13:
    #   https://github.com/kubernetes/kubernetes/blob/v1.13.3/pkg/kubelet/cm/cgroup_manager_linux.go#L207

    cgroup_driver: CgroupDriverType = field(
        default_factory=lambda: CgroupDriverType(CgroupDriverType.CGROUPFS))

    # By default use localhost, however kubelet may not listen on it.
    kubelet_endpoint: str = 'https://127.0.0.1:10250'

    # Key and certificate to access kubelet API.
    client_private_key: str = None
    client_cert: str = None

    # List of namespaces to monitor pods in.
    monitored_namespaces: List[str] = field(default_factory=lambda: ["default"])

    def _request_kubelet(self):
        PODS_PATH = '/pods'

        full_url = urljoin(self.kubelet_endpoint, PODS_PATH)
        r = requests.get(full_url, json=dict(type='GET_STATE'),
                         verify=False, cert=(self.client_cert, self.client_private_key))
        r.raise_for_status()
        return r.json()

    def get_tasks(self) -> List[Task]:
        """Returns only running tasks."""
        kubelet_json_response = self._request_kubelet()

        tasks = []
        for pod in kubelet_json_response.get('items'):
            container_statuses = pod.get('status').get('containerStatuses')
            if not container_statuses:
                # Lacking needed information.
                continue

            # Ignore pods in not monitored namespaces.
            if pod.get('metadata').get('namespace') not in self.monitored_namespaces:
                continue

            # Read into variables essential information about pod.
            pod_id = pod.get('metadata').get('uid')
            pod_name = pod.get('metadata').get('name')
            qos = pod.get('status').get('qosClass')
            if pod.get('metadata').get('labels'):
                labels = {_sanitize_label(key): value
                          for key, value in
                          pod.get('metadata').get('labels').items()}
            else:
                labels = {}

            # Apart from obvious part of the loop it checks whether all
            # containers are in ready state -
            # if at least one is not ready then skip this pod.
            containers_cgroups = []
            are_all_containers_ready = True
            for container in container_statuses:
                if not container.get('ready'):
                    are_all_containers_ready = False
                    container_state = list(container.get('state').keys())[0]
                    log.debug('Ignore pod with uid={} name={}. Container {} is in state={} .'
                              .format(pod_id, pod_name, container.get('name'), container_state))
                    break

                container_id = container.get('containerID').split('docker://')[1]
                containers_cgroups.append(
                    _build_cgroup_path(self.cgroup_driver, qos,
                                       pod_id, container_id))
            if not are_all_containers_ready:
                continue

            log.debug('Pod with uid={} name={} is ready and monitored by the system.'
                      .format(pod_id, pod_name))

            container_spec = pod.get('spec').get('containers')
            tasks.append(KubernetesTask(name=pod_name, task_id=pod_id,
                                        qos=qos.lower(), labels=labels,
                                        resources=_calculate_pod_resources(container_spec),
                                        cgroup_path=_build_cgroup_path(self.cgroup_driver,
                                                                       qos, pod_id),
                                        subcgroups_paths=containers_cgroups))

        _log_found_tasks(tasks)
        return tasks


def _build_cgroup_path(cgroup_driver, qos, pod_id, container_id=None):
    """Return cgroup path for pod or a pod container."""
    if container_id is None:
        container_subdirectory = '/'

    if cgroup_driver == CgroupDriverType.SYSTEMD:
        pod_id = pod_id.replace('-', '_')
        if container_id is not None:
            container_subdirectory = '/docker-{container_id}.scope/'.format(
                container_id=container_id)

        return ('/kubepods.slice/'
                'kubepods-{qos}.slice/'
                'kubepods-{qos}-pod{pod_id}.slice'
                '{container_subdirectory}'.format(
                            qos=qos.lower(),
                            pod_id=pod_id,
                            container_subdirectory=container_subdirectory))

    elif cgroup_driver == CgroupDriverType.CGROUPFS:
        if container_id is not None:
            container_subdirectory = '/' + container_id + '/'

        return ('/kubepods/'
                '{qos}/'
                'pod{pod_id}'
                '{container_subdirectory}'.format(
                            qos=qos.lower(),
                            pod_id=pod_id,
                            container_subdirectory=container_subdirectory))


_MEMORY_UNITS = {'Ki': 1024, 'Mi': 1024**2, 'Gi': 1024**3, }
_CPU_UNITS = {'m': 0.001}
_RESOURCE_TYPES = ['requests', 'limits']


def _calculate_pod_resources(containers_spec: List[Dict[str, str]]):
    resources = dict()

    units = {'memory': _MEMORY_UNITS, 'cpu': _CPU_UNITS}

    for container in containers_spec:
        container_resources = container.get('resources')
        if not container_resources:
            continue

        for resource_type in _RESOURCE_TYPES:
            if resource_type not in container_resources:
                continue

            for resource_name, resource_value in \
                    container_resources.get(resource_type).items():
                value = resource_value
                for unit, multiplier in units.get(resource_name).items():
                    if resource_value.endswith(unit):
                        value = float(resource_value.split(unit)[0]) * multiplier
                        break

                resource_key = resource_type + '_' + resource_name
                if resource_key in resources:
                    resources[resource_key] += float(value)
                else:
                    resources[resource_key] = float(value)

    return resources


def _sanitize_label(label_key):
    return label_key.replace('.', '_').replace('-', '_')


def _log_found_tasks(tasks):
    log.debug("Found %d kubernetes tasks (cumulatively %d cgroups leafs).",
              len(tasks), sum([len(task.subcgroups_paths) for task in tasks]))
    log.log(logger.TRACE, "Found kubernetes tasks with (name, task_id, subcgroups_paths): %s.",
            ", ".join([task.get_summary() for task in tasks]))
