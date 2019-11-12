===========================
Runner configuration object
===========================

**This software is pre-production and should not be deployed to production servers.**

.. contents:: Table of Contents

Introduction
============
There is runner configuration object called ``Config``. It's consists of necessary information
for runners object. ``AllocationRunner`` and ``DetectionRunner`` extends this by providing additional information.

Runner ``Config`` class:
.. code:: python

        class Config():
            """Config for Runners object.
                node: component used for tasks discovery
                metrics_storage: storage to store platform, internal, resource and task metrics
                    (defaults to DEFAULT_STORAGE/LogStorage to output for standard error)
                action_delay: iteration duration in seconds (None disables wait and iterations)
                    (defaults to 1 second)
                rdt_enabled: enables or disabled support for RDT monitoring
                    (defaults to None(auto) based on platform capabilities)
                gather_hw_mm_topology: gather hardware/memory topology based on lshw and ipmctl
                    (defaults to False)
                extra_labels: additional labels attached to every metrics
                    (defaults to empty dict)
                event_names: perf counters to monitor
                    (defaults to instructions, cycles, cache-misses, memstalls)
                enable_derived_metrics: enable derived metrics ips, ipc and cache_hit_ratio
                    (based on enabled_event names), default to False
                enable_perf_uncore: enable perf event uncore metrics
                    (defaults to True)
                task_label_generators: component to generate additional labels for tasks
                    (optional)
                allocation_configuration: allows fine grained control over allocations
                    (defaults to AllocationConfiguration() instance)
                wss_reset_interval: interval of reseting wss
                    (defaults to 0, every iteration)
            """
            node: Node
            metrics_storage: Storage = DEFAULT_STORAGE
            action_delay: Numeric(0, 60) = 1.
            rdt_enabled: Optional[bool] = None
            gather_hw_mm_topology: Optional[bool] = False
            extra_labels: Dict[Str, Str] = None
            event_names: List[str] = DEFAULT_EVENTS
            enable_derived_metrics: bool = False
            enable_perf_uncore: bool = True
            task_label_generators: Dict[str, TaskLabelGenerator] = None
            allocation_configuration: Optional[AllocationConfiguration] = None
            wss_reset_interval: int = 0


Example usage
=============
Configuration file

.. code:: yaml

        runner: ...
          config: !Config
            node: ...
            metrics_storage: ...
            action_delay: ...
            ...
         ...
