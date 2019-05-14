from workloads.orchestrator import Orchestrator


class Mesos(Orchestrator):

    def create_workload(self, workload):
        raise NotImplementedError()

    def clean_workloads(self):
        raise NotImplementedError()
