
==============================
Workload Collocation Agent API
==============================

**This software is pre-production and should not be deployed to production servers.**

.. contents:: Table of Contents


MeasurementRunner
=================

	    MeasurementRunner run iterations to collect platform, resource, task measurements
	    and store them in metrics_storage component.
	
	    Arguments:
	
	    node (Node): Component used for tasks discovery.
	
	    metrics_storage (Storage): Storage to store platform, internal, resource and task metrics.
	        (defaults to DEFAULT_STORAGE/LogStorage to output for standard error)
	
	    action_delay (int <0;60>): Iteration duration in seconds (None disables wait and iterations).
	        (defaults to 1 second)
	
	    rdt_enabled (bool): Enables or disabled support for RDT monitoring.
	        (defaults to None[auto] based on platform capabilities)
	
	    gather_hw_mm_topology (bool): Gather hardware/memory topology based on lshw and ipmctl.
	        (defaults to False)
	
	    extra_labels (Dict[str, str]): Additional labels attached to every metrics.
	        (defaults to empty dict)
	
	    event_names (List[str]): Perf counters to monitor.
	        (defaults to instructions, cycles, cache-misses, memstalls)
	
	    enable_derived_metrics (bool): Enable derived metrics ips, ipc and cache_hit_ratio based on
	        enabled event names. (default to False)
	
	    enable_perf_uncore (bool): Enable perf event uncore metrics.
	        (defaults to None - auto)
	
	    task_label_generators (Dict[str, TaskLabelGenerator]): Component to generate additional labels
	        for tasks.
	        (optional)
	
	    allocation_configuration: Allows fine grained control over allocations.
	        (defaults to AllocationConfiguration() instance)
	
	    wss_reset_interval: Interval of reseting wss.
	        (defaults to 0, not measured)
	
	    include_optional_labels: Include optional labels like: sockets, cpus, cpu_model.
	        (defaults to False)
	    

AllocationRunner
================

	    Runner is responsible for getting information about tasks from node,
	    calling allocate() callback on allocator, performing returning allocations
	    and storing all allocation related metrics in allocations_storage.
	
	    Because Allocator interface is also detector, we store serialized detected anomalies
	    in anomalies_storage and all other measurements in metrics_storage.
	
	    Arguments:
	        measurement_runner (MeasurementRunner): Measurement runner object.
	
	        allocator (Allocator): Component that provides allocation logic.
	
	        anomalies_storage (Storage): Storage to store serialized anomalies and extra metrics.
	            (defaults to DEFAULT_STORAGE/LogStorage to output for standard error)
	
	        allocations_storage (Storage): Storage to store serialized resource allocations.
	            (defaults to DEFAULT_STORAGE/LogStorage to output for standard error)
	
	        rdt_mb_control_required (bool): Indicates that MB control is required,
	            if the platform does not support this feature the WCA will exit.
	
	        rdt_cache_control_required (bool): Indicates tha L3 control is required,
	            if the platform does not support this feature the WCA will exit.
	
	        remove_all_resctrl_groups (bool): Remove all RDT controls groups upon starting.
	            (defaults to False)
	    

DetectionRunner
===============

	    DetectionRunner extends MeasurementRunner with ability to callback Detector,
	    serialize received anomalies and storing them in anomalies_storage.
	
	    Arguments:
	        config: Runner configuration object.
	    

MesosNode
=========

	MesosNode(mesos_agent_endpoint:<function Url at 0x7f0ccd911ae8>='https://127.0.0.1:5051', timeout:wca.config.Numeric=5.0, ssl:Union[wca.security.SSL, NoneType]=None)

KubernetesNode
==============

	KubernetesNode(cgroup_driver:wca.kubernetes.CgroupDriverType=<CgroupDriverType.CGROUPFS: 'cgroupfs'>, ssl:Union[wca.security.SSL, NoneType]=None, client_token_path:Union[wca.config.Path, NoneType]='/var/run/secrets/kubernetes.io/serviceaccount/token', server_cert_ca_path:Union[wca.config.Path, NoneType]='/var/run/secrets/kubernetes.io/serviceaccount/ca.crt', kubelet_enabled:bool=False, kubelet_endpoint:<function Url at 0x7f0ccd911ae8>='https://127.0.0.1:10250', kubeapi_host:<function Str at 0x7f0ccd9118c8>=None, kubeapi_port:<function Str at 0x7f0ccd9118c8>=None, node_ip:<function Str at 0x7f0ccd9118c8>=None, timeout:wca.config.Numeric=5, monitored_namespaces:List[Str]=<factory>)

LogStorage
==========

	    Outputs metrics encoded in Prometheus exposition format
	    to standard error (default) or provided file (output_filename).
	    

KafkaStorage
============

	    Storage for saving metrics in Kafka.
	
	    Args:
	        topic: name of a kafka topic where message should be saved
	        brokers_ips:  list of addresses with ports of all kafka brokers (kafka nodes)
	        max_timeout_in_seconds: if a message was not delivered in maximum_timeout seconds
	            self.store will throw FailedDeliveryException
	        extra_config: additionall key value pairs that will be passed to kafka driver
	            https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
	            e.g. {'debug':'broker,topic,msg'} to enable logging for kafka producer threads
	        ssl: secure socket layer object
	    

FilterStorage
=============

	FilterStorage(storages:List[wca.storage.Storage], filter:Union[List[str], NoneType]=None)

NOPAnomalyDetector
==================

	None

NOPAllocator
============

	None

AllocationConfiguration
=======================

	AllocationConfiguration(cpu_quota_period:wca.config.Numeric=1000, cpu_shares_unit:wca.config.Numeric=1000, default_rdt_l3:<function Str at 0x7f0ccd9118c8>=None, default_rdt_mb:<function Str at 0x7f0ccd9118c8>=None)

CgroupDriverType
================

	An enumeration.

StaticNode
==========

	    Simple implementation of Node that returns tasks based on
	    provided list on tasks names.
	
	    Tasks are returned only if corresponding cgroups exists:
	    - /sys/fs/cgroup/cpu/(task_name)
	    - /sys/fs/cgroup/cpuacct/(task_name)
	    - /sys/fs/cgroup/perf_event/(task_name)
	
	    Otherwise, the item is ignored.
	    

NUMAAllocator
=============

	NUMAAllocator(algorithm:wca.extra.numa_allocator.NUMAAlgorithm=<NUMAAlgorithm.FILL_BIGGEST_FIRST: 'fill_biggest_first'>, loop_min_task_balance:float=0.0, free_space_check:bool=False, migrate_pages:bool=True, migrate_pages_min_task_balance:Union[float, NoneType]=0.95, cgroups_cpus_binding:bool=True, cgroups_memory_binding:bool=False, cgroups_memory_migrate:bool=False, dryrun:bool=False)

NUMAAlgorithm
=============

	solve bin packing problem by heuristic which takes the biggest first

StaticAllocator
===============

	    Simple allocator based on rules defining relation between task labels
	    and allocation definition (set of concrete values).
	
	    The allocator reads allocation rules from a yaml file and directly
	    from constructor argument (passed as python dictionary).
	    Refer to configs/extra/static_allocator_config.yaml to see sample
	    input file for StaticAllocator.
	
	    A rule is an object with three fields:
	    - name,
	    - labels (optional),
	    - allocations.
	
	    First field is just a helper to name a rule.
	    Second field contains a dictionary, where each key is a task's label name and
	    the value is a regex defining the matching set of label values. If the field
	    is not included then all tasks match the rule.
	    The third field is a dictionary of allocations which should be applied to
	    matching tasks.
	
	    If there are multiple matching rules then the rules' allocations are merged and applied.
	    

SSL
===

	    Common configuration for SSL communication.
	
	    * server_verify: Union[bool, Path(absolute=True, mode=os.R_OK)] = True
	    * client_cert_path: Optional[Path(absolute=True, mode=os.R_OK)] = None
	    * client_key_path: Optional[Path(absolute=True, mode=os.R_OK)] = None
	
	    

TaskLabelRegexGenerator
=======================

	Generate new label value based on other label value.

DefaultDerivedMetricsGenerator
==============================

	None

UncoreDerivedMetricsGenerator
=============================

	None

