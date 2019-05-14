from abc import ABC


class Orchestrator(ABC):
    metadata: dict

    def __init__(self, metadata):
        self.metadata = metadata

    def create_workload(self, workload):
        ...

    def clean_workloads(self):
        ...


def get_orchestrator(meta_inventory: dict):

    from workloads import kubernetes
    from workloads import mesos

    orchestrator: str = meta_inventory['orchestrator']
    orchestrator = orchestrator.lower()

    if orchestrator == 'kubernetes':
        return kubernetes.Kubernetes(meta_inventory)

    if orchestrator == 'mesos':
        return mesos.Mesos(meta_inventory)

    raise NotImplementedError('"{}" orchestrator'.format(orchestrator))
