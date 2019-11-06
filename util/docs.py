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

from wca.metrics import METRICS_METADATA, MetricGranurality


METRICS_DOC_PATH = 'docs/metrics.rst'

INTRO = """
================================
Available metrics
================================

**This software is pre-production and should not be deployed to production servers.**

.. contents:: Table of Contents

"""


def prepare_csv_table(data):
    table = '.. csv-table::\n'
    table += '\t:header: "Name", "Help", "Unit", "Type", "Source", "Granularity"\n'
    table += '\t:widths: 10, 20, 10, 10, 10, 10\n\n\t'

    table += '\n\t'.join(['"{}", "{}", "{}", "{}", "{}", "{}"'.format(*row) for row in data])

    return table


def generate_title(title):
    return title + '\n' + ''.join(['=' for _ in range(len(title))])


def generate_docs():

    task_data = []
    platform_data = []
    internal_data = []

    for metric in METRICS_METADATA:
        data = (metric,
                METRICS_METADATA[metric].help,
                METRICS_METADATA[metric].unit,
                METRICS_METADATA[metric].type,
                METRICS_METADATA[metric].source,
                METRICS_METADATA[metric].granularity)

        if data[-1] == MetricGranurality.TASK:
            task_data.append(data)
        elif data[-1] == MetricGranurality.PLATFORM:
            platform_data.append(data)
        elif data[-1] == MetricGranurality.INTERNAL:
            internal_data.append(data)

    task_table = prepare_csv_table(task_data)
    platform_table = prepare_csv_table(platform_data)
    internal_table = prepare_csv_table(internal_data)

    task_title = generate_title("Task's metrics")
    platform_title = generate_title("Platforms's metrics")
    internal_title = generate_title("Internal metrics")

    docs = task_title + '\n' + task_table + '\n' + platform_title + '\n' + platform_table + \
        '\n' + internal_title + '\n' + internal_table

    return docs


if __name__ == '__main__':
    with open(METRICS_DOC_PATH, 'w') as f:
        f.write(INTRO)
        f.write(generate_docs())
