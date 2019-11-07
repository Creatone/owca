# Copyright (c) 2019 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from wca.metrics import METRICS_METADATA, MetricGranurality, MetricSource


def prepare_csv_table(data):
    table = '.. csv-table::\n'
    table += '\t:header: "Name", "Help", "Unit", "Type"\n'
    table += '\t:widths: 10, 20, 10, 10\n\n\t'

    table += '\n\t'.join(['"{}", "{}", "{}", "{}"'.format(*row) for row in data])

    return table


def generate_title(title):
    return title + '\n' + ''.join(['=' for _ in range(len(title))])


def generate_subtitle(subtitle):
    return subtitle + '\n' + ''.join(['-' for _ in range(len(subtitle))])


METRICS_DOC_PATH = 'docs/metrics.rst'

INTRO = """
================================
Available metrics
================================

**This software is pre-production and should not be deployed to production servers.**

.. contents:: Table of Contents

"""

PERF_BASED = generate_title("Perf event based") + """
To collect metrics you need to provide `event_names` list (defaults to instructions,
cycles, cache-misses, memstalls) to runner object in config file.

**You can only collect 4 additional perf events!**

"""

RESCTRL_BASED = generate_title("Resctrl based") + """
To collect metrics you need to set `rdt_enabled` in config file.

"""


def generate_docs():

    task_data = {
            MetricSource.PERF_EVENT: [],
            MetricSource.CGROUP: [],
            MetricSource.RESCTRL: [],
            MetricSource.PROC: [],
            MetricSource.INTERNAL: [],
            MetricSource.GENERIC: []
            }

    platform_data = {
            MetricSource.PERF_EVENT: [],
            MetricSource.CGROUP: [],
            MetricSource.RESCTRL: [],
            MetricSource.PROC: [],
            MetricSource.INTERNAL: [],
            MetricSource.GENERIC: []
            }

    internal_data = []

    for metric, metadata in sorted(METRICS_METADATA.items()):
        data = (metric, metadata.help, metadata.unit, metadata.type)

        if metadata.granularity == MetricGranurality.TASK:
            task_data[metadata.source].append(data)
        elif metadata.granularity == MetricGranurality.PLATFORM:
            platform_data[metadata.source].append(data)
        elif metadata.granularity == MetricGranurality.INTERNAL:
            internal_data.append(data)

    perf = PERF_BASED + '\n\n'
    perf += generate_subtitle("Task's metrics") + '\n\n'
    perf += prepare_csv_table(task_data[MetricSource.PERF_EVENT]) + '\n\n'
    perf += generate_subtitle("Platform's metrics") + '\n\n'
    perf += prepare_csv_table(platform_data[MetricSource.PERF_EVENT]) + '\n\n'

    resctrl = RESCTRL_BASED + '\n\n'
    resctrl += generate_subtitle("Task's metrics") + '\n\n'
    resctrl += prepare_csv_table(task_data[MetricSource.RESCTRL]) + '\n\n'
    resctrl += generate_subtitle("Platform's metrics") + '\n\n'
    resctrl += prepare_csv_table(platform_data[MetricSource.RESCTRL]) + '\n\n'

    internal = generate_title("Internal metrics") + '\n\n'
    internal += prepare_csv_table(internal_data) + '\n\n'

    return perf + '\n\n' + resctrl + '\n\n' + internal


if __name__ == '__main__':
    with open(METRICS_DOC_PATH, 'w') as f:
        f.write(INTRO)
        f.write(generate_docs())
