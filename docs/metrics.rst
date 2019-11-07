
================================
Available metrics
================================

**This software is pre-production and should not be deployed to production servers.**

.. contents:: Table of Contents

# Task's metrics


## Perf event based

To collect metrics you need to provide `event_names` list (defaults to instructions,
cycles, cache-misses, memstalls) to runner object in config file.

**You can only collect 4 additional perf events!**

.. csv-table::
	:header: "Name", "Help", "Unit", "Type", "Source"
	:widths: 10, 20, 10, 10, 10

	"instructions", "Linux Perf counter for instructions per container.", "numeric", "counter", "perf event"
	"cycles", "Linux Perf counter for cycles per container.", "numeric", "counter", "perf event"
	"cache_misses", "Linux Perf counter for cache-misses per container.", "numeric", "counter", "perf event"
	"cache_references", "Cache references.", "numeric", "counter", "perf event"
	"offcore_requests_l3_miss_demand_data_rd", "Increment each cycle of the number of offcore outstanding demand data read requests from SQ that missed L3.", "numeric", "counter", "perf event"
	"offcore_requests_outstanding_l3_miss_demand_data_rd", "Demand data read requests that missed L3.", "numeric", "counter", "perf event"
	"ipc", "Instructions per cycle.", "numeric", "gauge", "perf event"
	"ips", "Instructions per second.", "numeric", "gauge", "perf event"
	"cache_hit_ratio", "Cache hit ratio, based on cache-misses and cache-references.", "numeric", "gauge", "perf event"
	"cache_misses_per_kilo_instructions", "Cache misses per kilo instructions.", "numeric", "gauge", "perf event"