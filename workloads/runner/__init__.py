from abc import ABC
from dataclasses import dataclass
from workloads.runner.orchestrator import get_orchestrator


class Orchestrator(ABC):

    def create_workload(self):
        ...

    def clean_workloads(self):
        ...

@dataclass
class Runner():
    inventory: dict
    meta_inventory: dict

    def run(self):
        orchestrator: Orchestrator = get_orchestrator(self.meta_inventory)
        orchestrator.clean_workloads()

        # Successful exit code.
        return 0
