import logging
from kubernetes import client, config

from workloads.orchestrator import Orchestrator

log = logging.getLogger(__name__)


def _get_body(workload):
    pod = client.V1Pod()
    pod.metadata = {
            'name': workload
            }

    return pod


class Kubernetes(Orchestrator):
    """K8s orchestrator"""
    namespace: str = 'default'
    api: str = None

    def __init__(self, metadata):
        super().__init__(metadata)

        self.namespace = metadata['k8s_namespace']

        config.load_kube_config()
        self.api = client.CoreV1Api()

    def create_workload(self, workload):
        try:
            body = _get_body(workload)
            self.api.create_namespaced_pod(self.namespace, body)
        except client.rest.ApiException as e:
            log.error('Exception on cleaning workloads: {}'.format(e))
        raise NotImplementedError()

    # TODO: Implement wait for delete pod completion
    def clean_workloads(self):
        log.info('Trying to clean workloads')
        try:
            self.api.delete_collection_namespaced_pod(namespace=self.namespace)
        except client.rest.ApiException as e:
            log.error('Exception on cleaning workloads: {}'.format(e))
