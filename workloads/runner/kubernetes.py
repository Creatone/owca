from workloads.runner import Orchestrator


class Kubernetes(Orchestrator):
    """K8s orchestrator"""

    def create_workloads(self):
        print('k8s')
