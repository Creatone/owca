
================================
Available metrics
================================

**This software is pre-production and should not be deployed to production servers.**

.. contents:: Table of Contents

Task's metrics
==============

Perf event based
----------------

.. csv-table::
	:header: "Name", "Help", "Unit", "Type"
	:widths: 10, 20, 10, 10

	"cache_hit_ratio", "Cache hit ratio, based on cache-misses and cache-references.", "numeric", "gauge"
	"cache_misses", "Linux Perf counter for cache-misses per container.", "numeric", "counter"
	"cache_misses_per_kilo_instructions", "Cache misses per kilo instructions.", "numeric", "gauge"
	"cache_references", "Cache references.", "numeric", "counter"
	"cycles", "Linux Perf counter for cycles per container.", "numeric", "counter"
	"instructions", "Linux Perf counter for instructions per container.", "numeric", "counter"
	"ipc", "Instructions per cycle.", "numeric", "gauge"
	"ips", "Instructions per second.", "numeric", "gauge"
	"offcore_requests_l3_miss_demand_data_rd", "Increment each cycle of the number of offcore outstanding demand data read requests from SQ that missed L3.", "numeric", "counter"
	"offcore_requests_outstanding_l3_miss_demand_data_rd", "Demand data read requests that missed L3.", "numeric", "counter"
	"stalls_mem_load", "Mem stalled loads.", "numeric", "counter"

Resctrl based
-------------

.. csv-table::
	:header: "Name", "Help", "Unit", "Type"
	:widths: 10, 20, 10, 10

	"llc_occupancy", "LLC occupancy.", "bytes", "gauge"
	"memory_bandwidth", "Total memory bandwidth using Memory Bandwidth Monitoring.", "bytes", "counter"
	"memory_bandwidth_local", "Total local memory bandwidth using Memory Bandwidth Monitoring.", "bytes", "counter"
	"memory_bandwidth_remote", "Total remote memory bandwidth using Memory Bandwidth Monitoring.", "bytes", "counter"



Platform's metrics
==================

Perf event based
----------------

.. csv-table::
	:header: "Name", "Help", "Unit", "Type"
	:widths: 10, 20, 10, 10

	"scaling_factor_avg", "Perf metric scaling factor, average from all CPUs.", "numeric", "gauge"
	"scaling_factor_max", "Perf metric scaling factor, MAX value.", "numeric", "gauge"

Resctrl based
-------------

.. csv-table::
	:header: "Name", "Help", "Unit", "Type"
	:widths: 10, 20, 10, 10

	



Internal metrics
================

.. csv-table::
	:header: "Name", "Help", "Unit", "Type"
	:widths: 10, 20, 10, 10

	"up", "Time the WCA was last seen.", "numeric", "counter"

