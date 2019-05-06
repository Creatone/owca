from workloads.runner.kubernetes import Kubernetes
from workloads.runner.mesos import Mesos


def get_orchestrator(meta_inventory: dict):
    orchestrator: str = meta_inventory['orchestrator']
    orchestrator = orchestrator.lower()

    if orchestrator == 'kubernetes':
        return Kubernetes(meta_inventory)

    if orchestrator == 'mesos':
        return Mesos(meta_inventory)

    raise NotImplementedError('"{}" orchestrator'.format(orchestrator))
