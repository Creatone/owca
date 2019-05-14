from dataclasses import dataclass
from workloads.orchestrator import get_orchestrator, Orchestrator


@dataclass
class Runner():
    inventory: dict
    meta_inventory: dict

    def run(self):
        orchestrator: Orchestrator = get_orchestrator(self.meta_inventory)

        orchestrator.clean_workloads()

        for workload in self.inventory['workloads']:
            orchestrator.create_workload(self.inventory['workloads'][workload])

        # Successful exit code.
        return 0
