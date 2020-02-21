import datetime
import itertools
import logging
import os
import pprint
import statistics
from collections import Counter
from functools import partial
from typing import Dict, List, Any

import numpy as np
import pandas as pd
from dataclasses import dataclass
from matplotlib import pyplot as plt

from wca.scheduler.cluster_simulator import Resources, Node, AssignmentsCounts, ClusterSimulator
from wca.scheduler.types import ResourceType as rt

log = logging.getLogger(__name__)

CHARTS = False


@dataclass
class IterationData:
    cluster_resource_usage: Resources
    per_node_resource_usage: Dict[Node, Resources]
    broken_assignments: Dict[Node, int]
    assignments_counts: AssignmentsCounts
    tasks_types_count: Dict[str, int]
    metrics: Dict[str, List[float]]


def generate_subexperiment_report(
        title: str, subtitle: str, run_params: Dict[str, Any],
        iterations_data: List[IterationData],
        reports_root_directory: str = 'experiments_results',
        filter_metrics=None, task_gen=None, scheduler=None) -> dict:
    """
        Results will be saved to location:
        {reports_root_directory}/{title}/{subtitle}.{extension}
        where extensions='png'|'txt'

        >>run_params<< is dict of params used to run experiment
    """
    filter_metrics = filter_metrics or []
    # experiment directory
    exp_dir = '{}/{}'.format(reports_root_directory, title)

    plt.style.use('ggplot')
    iterd = iterations_data

    iterations = np.arange(0, len(iterd))
    cpu_usage = np.array([iter_.cluster_resource_usage.data[rt.CPU] for iter_ in iterd])
    mem_usage = np.array([iter_.cluster_resource_usage.data[rt.MEM] for iter_ in iterd])

    if rt.MEMBW_READ in iterd[0].cluster_resource_usage.data:
        membw_usage = np.array([iter_.cluster_resource_usage.data[rt.MEMBW_READ]
                                for iter_ in iterd])
    else:
        membw_usage = np.array([iter_.cluster_resource_usage.data[rt.MEMBW] for iter_ in iterd])
    # ---
    if not os.path.isdir(exp_dir):
        os.makedirs(exp_dir)
    if CHARTS:
        number_of_metrics = len(filter_metrics)
        fig, axs = plt.subplots(2 + number_of_metrics)
        fig.set_size_inches(20, 20 + 6*number_of_metrics)
        axs[0].plot(iterations, cpu_usage, 'r--')
        axs[0].plot(iterations, mem_usage, 'b--')
        axs[0].plot(iterations, membw_usage, 'g--')
        axs[0].legend(['cpu usage', 'mem usage', 'membw usage'])
        # ---
        axs[0].set_title('{} {}'.format(title, subtitle), fontsize=10)
        # ---
        axs[0].set_xlim(iterations.min(), iterations.max())
        axs[0].set_ylim(0, 1)

        broken_assignments = \
            np.array([sum(list(iter_.broken_assignments.values())) for iter_ in iterd])
        axs[1].plot(iterations, broken_assignments, 'g--')
        axs[1].legend(['broken assignments'])
        axs[1].set_ylabel('')
        axs[1].set_xlim(iterations.min(), iterations.max())
        axs[1].set_ylim(broken_assignments.min() - 1, broken_assignments.max() + 1)

        # Visualize metrics
        try:
            import seaborn as sns
            import pandas as pd
            for pidx, filter in enumerate(filter_metrics):
                dicts = []
                for iteration, idata in enumerate(iterations_data):
                    d = {k.split('{')[1][:-1]: v
                         for k, v in idata.metrics.items() if k.startswith(filter)}
                    if not d:
                        log.warning('metric %s not found: available: %s', filter,
                                    ', '.join([m.split('{')[0] for m in idata.metrics.keys()]))
                    dicts.append(d)

                from matplotlib.markers import MarkerStyle
                df = pd.DataFrame(dicts)
                try:
                    x = sns.lineplot(data=df,
                                     markers=MarkerStyle.filled_markers,
                                     dashes=False,
                                     ax=axs[2+pidx])
                except ValueError:
                    x = sns.lineplot(data=df,
                                     dashes=False,
                                     ax=axs[2+pidx])
                x.set_title(filter)
                x.set_xlim(iterations.min(), iterations.max())

            # plt.show()
        except ImportError:
            log.warning('missing seaborn and pandas')

        fig.savefig('{}/{}.png'.format(exp_dir, subtitle))

    with open('{}/{}.txt'.format(exp_dir, subtitle), 'w') as fref:
        t_ = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_%H%M')
        total_tasks_dict = dict(iterations_data[-1].tasks_types_count)
        fref.write("Scheduled tasks (might not be successfully assigned): {}\n"
                   .format(total_tasks_dict))

        scheduled_tasks = sum(total_tasks_dict.values())
        assignments_counts = iterations_data[-1].assignments_counts
        fref.write("Unassigned tasks: {}\n".format(dict(assignments_counts.unassigned)))
        broken_assignments = sum(iterations_data[-1].broken_assignments.values())
        fref.write("Broken assignments: {}\n".format(broken_assignments))

        total_nodes = len(assignments_counts.per_node.keys())
        node_names = assignments_counts.per_node.keys()
        nodes_info = ','.join('%s=%d'%(node_type, len(list(nodes))) for node_type, nodes
            in itertools.groupby(sorted(node_names), lambda x: x.split('_')[0]))
        fref.write("\nAssigned tasks per cluster: {}\n".format(dict(assignments_counts.per_cluster)))

        assigned_tasks = dict(assignments_counts.per_cluster)['__ALL__']

        fref.write("Assigned tasks per node:\n")
        for node, counters in assignments_counts.per_node.items():
            fref.write("   {}: {}\n".format(node, dict(counters)))


        rounded_last_iter_resources = \
            map(partial(round, ndigits=2), (cpu_usage[-1], mem_usage[-1], membw_usage[-1],))
        cpu_util, mem_util, bw_util = rounded_last_iter_resources
        fref.write("\nresource_usage(cpu, mem, membw_flat) = ({}, {}, {})\n".format(
            cpu_util, mem_util, bw_util))
        nodes_avg_var = []
        nodes_utilization = []
        nodes_utilization_avg = []
        for node, usages in iterations_data[-1].per_node_resource_usage.items():
            rounded_last_iter_resources = map(
                partial(round, ndigits=2),
                (usages.data[rt.CPU], usages.data[rt.MEM], usages.data[rt.MEMBW_READ],))
            fref.write(
                "  {}: = ({}, {}, {})\n".format(
                    node.name, *rounded_last_iter_resources))
            nodes_utilization.extend([usages.data[rt.CPU], usages.data[rt.MEM], usages.data[rt.MEMBW_READ]])
            nodes_utilization_avg.append((usages.data[rt.CPU] + usages.data[rt.MEM] + usages.data[rt.MEMBW_READ])/3)
            nodes_avg_var.append(statistics.variance([usages.data[rt.CPU], usages.data[rt.MEM], usages.data[rt.MEMBW_READ]]))

        util_var_avg = statistics.variance(nodes_utilization_avg)
        util_avg_var = statistics.mean(nodes_avg_var)
        util_var = statistics.variance(nodes_utilization)

        available_metrics = {m.split('{')[0] for iterdata in iterations_data for m in iterdata.metrics}
        fref.write("\n\nAvailable metrics: {}\n".format(', '.join(sorted(available_metrics))))
        fref.write("Start of experiment: {}\n".format(t_))
        fref.write("Run params: {}\n".format(pprint.pformat(run_params, indent=4)))
        fref.write("Iterations: {}\n".format(len(iterations_data)))

    with open('{}/README.txt'.format(exp_dir), 'a') as fref:
        fref.write("Subexperiment: {}\n".format(subtitle))
        fref.write("Run params: {}\n\n".format(pprint.pformat(run_params, indent=4)))

    stats = {}
    stats['TASKS'] = str(task_gen) # sum(total_tasks_dict.values())
    stats['NODES'] = '%s(%s)' % (total_nodes, nodes_info)
    stats['ALGO'] = str(scheduler)
    stats['balance'] = 1 - util_var
    stats['cpu_util%'] = cpu_util * 100
    stats['mem_util%'] = mem_util * 100
    stats['bw_util%'] = bw_util * 100

    if any('aep' in node.name for node, _ in iterations_data[-1].per_node_resource_usage.items()):
        stats['cpu_util(AEP)%'] = 100 * statistics.mean(
            resources.data[rt.CPU] for node, resources in 
            iterations_data[-1].per_node_resource_usage.items() if 'aep' in node.name)
        stats['mem_util(AEP)%'] = 100 * statistics.mean(
            resources.data[rt.MEM] for node, resources in 
            iterations_data[-1].per_node_resource_usage.items() if 'aep' in node.name)
        stats['bw_util(AEP)%'] = 100 * statistics.mean(
            resources.data[rt.MEMBW_READ] for node, resources in 
            iterations_data[-1].per_node_resource_usage.items() if 'aep' in node.name)
    else:
        stats['cpu_util(AEP)%'] = float('nan')
        stats['mem_util(AEP)%'] = float('nan')
        stats['bw_util(AEP)%'] = float('nan')

    stats['scheduled'] = scheduled_tasks
    stats['assigned%'] = int((assigned_tasks/scheduled_tasks) * 100)
    stats['assigned_broken%'] = int((broken_assignments / scheduled_tasks) * 100)
    stats['utilization%'] = int(((cpu_util + mem_util + bw_util) / 3) * 100)

    return stats


def generate_experiment_report(stats_dicts, exp_dir):
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)
    df = pd.DataFrame(stats_dicts)
    output = df.to_string(formatters={
        'balance': '{:,.2f}'.format,
        'assigned_broken%': '{:,.0f}%'.format,
        'assigned%': '{:,.0f}%'.format,
        'cpu_util(AEP)%': '{:,.0f}%'.format,
        'mem_util(AEP)%': '{:,.0f}%'.format,
        'bw_util(AEP)%': '{:,.0f}%'.format,
        'cpu_util%': '{:,.0f}%'.format,
        'mem_util%': '{:,.0f}%'.format,
        'bw_util%': '{:,.0f}%'.format,
        'scheduled': '{:,.0f}'.format,
        'util_var_avg': '{:,.0%}'.format,
        'util_avg_var': '{:,.0%}'.format,
        'util_var': '{:,.0%}'.format,
        'utilization%': '{:,.0f}%'.format,
    })
    print(output)
    df.reset_index()
    def p(val, aggr):
        _pivot_ui(
            df,
            totals=True,
            rowTotals=False,
            rows=['TASKS', 'NODES'],
            cols=['ALGO'],
            vals=[val], aggregatorName=aggr,
            rendererName='Heatmap',
            outfile_path=os.path.join(exp_dir, 'summary_%s.html' % val.replace('%', '')),
            rendererOptions = dict(
                rowTotals=False,
                colTotals=False,
            )
        )
    p('utilization%', 'Average')
    p('balance', 'Average')
    p('broken%', 'Average')



def wrapper_iteration_finished_callback(iterations_data: List[IterationData]):
    def iteration_finished_callback(iteration: int, simulator: ClusterSimulator):
        per_node_resource_usage = simulator.per_node_resource_usage(True)
        cluster_resource_usage = simulator.cluster_resource_usage(True)
        broken_assignments = simulator.rough_assignments_per_node.copy()
        assignments_counts = simulator.assignments_counts()
        tasks_types_count = Counter([task.get_core_name() for task in simulator.tasks])

        metrics_registry = simulator.scheduler.get_metrics_registry()
        if metrics_registry is not None:
            metrics = metrics_registry.as_dict()
        else:
            metrics = {}

        iterations_data.append(IterationData(
            cluster_resource_usage, per_node_resource_usage,
            broken_assignments, assignments_counts, tasks_types_count,
            metrics=metrics,
        ))

    return iteration_finished_callback


def _pivot_ui(df, totals=True, rowTotals=True, **options):
    """ Interactive pivot table for data analysis.
    # Example options:
    rows=['x', 'y'),
    cols=['z, 'v'),
    vals=['percentile/99th',],
    aggregatorName='First',
    rendererName='Heatmap'
    """
    try:
        from pivottablejs import pivot_ui
    except ImportError:
        print("Error: cannot import pivottablejs, please install 'pip install pivottablejs'!")
        return
    iframe = pivot_ui(df, **options)
    if not totals:
        with open(iframe.src) as f:
            replacedHtml = f.read().replace( '</style>', '.pvtTotal, .pvtTotalLabel, .pvtGrandTotal {display: none}</style>' )
        with open(iframe.src, "w") as f:
            f.write(replacedHtml)
    if not rowTotals:
        with open(iframe.src) as f:
            replacedHtml = f.read().replace('</style>', '.rowTotal, .pvtRowTotalLabel, .pvtGrandTotal {display: none}</style>')
        with open(iframe.src, "w") as f:
            f.write(replacedHtml)
    return iframe
