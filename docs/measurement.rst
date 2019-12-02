=====================
Measurement interface
=====================

**This software is pre-production and should not be deployed to production servers.**

.. contents:: Table of Contents

Introduction
------------
MeasurementRunner run iterations to collect platform, resource, task measurements from ``node`` and store them in ``metrics_storage`` component.

Configuration
-------------

Example of configuration that uses ``MeasurementRunner``:

.. code:: yaml

        runner: !MeasurementRunner
          node: !StaticNode
            tasks:
              - task1
          metrics_storage: !LogStorage
            output_filename: 'metrics.prom'
            overwrite: true

.. code:: python


        class MeasurementRunner(Runner):
            """MeasurementRunner run iterations to collect platform, resource, task measurements
            and store them in metrics_storage component.

            Arguments:
                node: Component used for tasks discovery.
                metrics_storage: Storage to store platform, internal, resource and task metrics.
                    (defaults to DEFAULT_STORAGE/LogStorage to output for standard error)
                action_delay: Iteration duration in seconds (None disables wait and iterations).
                    (defaults to 1 second)
                rdt_enabled: Enables or disabled support for RDT monitoring.
                    (defaults to None(auto) based on platform capabilities)
                gather_hw_mm_topology: Gather hardware/memory topology based on lshw and ipmctl.
                    (defaults to False)
                extra_labels: Additional labels attached to every metrics.
                    (defaults to empty dict)
                event_names: Perf counters to monitor.
                    (defaults to instructions, cycles, cache-misses, memstalls)
                enable_derived_metrics: Enable derived metrics ips, ipc and cache_hit_ratio.
                    (based on enabled_event names, default to False)
                enable_perf_uncore: Enable perf event uncore metrics.
                    (defaults to True)
                task_label_generators: Component to generate additional labels for tasks.
                    (optional)
                allocation_configuration: Allows fine grained control over allocations.
                    (defaults to AllocationConfiguration() instance)
                wss_reset_interval: Interval of reseting wss.
                    (defaults to 0, every iteration)
            """

            def __init__(
                    self,
                    node: Node,
                    metrics_storage: Storage = DEFAULT_STORAGE,
                    action_delay: Numeric(0, 60) = 1.,
                    rdt_enabled: Optional[bool] = None,
                    gather_hw_mm_topology: bool = False,
                    extra_labels: Optional[Dict[Str, Str]] = None,
                    event_names: List[str] = DEFAULT_EVENTS,
                    enable_derived_metrics: bool = False,
                    enable_perf_uncore: bool = True,
                    task_label_generators: Optional[Dict[str, TaskLabelGenerator]] = None,
                    allocation_configuration: Optional[AllocationConfiguration] = None,
                    wss_reset_interval: int = 0
                    ):
