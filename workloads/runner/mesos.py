from workloads.runner import Orchestrator


class Mesos(Orchestrator):
    def create_workload(self):
        ...

    def clean_workloads(self):
        ...
