import statistics
from collections import Counter, defaultdict
from functools import reduce
from itertools import combinations
from typing import Tuple, List, Dict
import logging
import operator

from wca.logger import TRACE
from wca.metrics import Metric
from wca.scheduler.algorithms.least_used_bar import LeastUsedBAR
from wca.scheduler.algorithms.base import used_free_requested, divide_resources, \
    calculate_read_write_ratio, sum_resources, substract_resources
from wca.scheduler.data_providers import DataProvider
from wca.scheduler.types import ResourceType as rt, NodeName, Resources
from wca.scheduler.types import ResourceType

log = logging.getLogger(__name__)


def calc_average_resources_of_nodes(nodes: List[Resources]) -> Resources:
    """ sum resources of all nodes and divied by number of nodes
    return new resources
    """
    sum_resources_of_nodes = reduce(sum_resources, nodes)
    averaged_resources_of_class = divide_resources(
        sum_resources_of_nodes,
        {r: len(nodes) for r in sum_resources_of_nodes.keys()},
    )
    return averaged_resources_of_class

def resources_to_shape(resources: Dict[rt, float]):
    # for visualization reasons always normalized to 1 cpu
    # cpus = resources[rt.CPU]
    return tuple(sorted({r: int(v) for r, v in resources.items()}.items()))


def less_shapes(shapes_to_nodes, nodes_capacities, merge_threshold):
    def shape_diff(shape1, shape2):
        res1 = dict(shape1)
        res2 = dict(shape2)
        resdiff = substract_resources(res1, res2)
        diffvariance = statistics.stdev(resdiff.values())
        # log.log(TRACE, '[Filter2][less_shapes] shape1=%s shape=%s shape_diff=%s', shape1, shape2, diffvariance)
        return diffvariance

    def create_new_shape(*shapes):
        node_names_for_new_shape = []
        for shape in shapes:
            node_names_for_new_shape.extend(shapes_to_nodes[shape])
        nodes = [nodes_capacities[n] for n in node_names_for_new_shape]
        avg_resources = calc_average_resources_of_nodes(nodes)
        new_shape = resources_to_shape(avg_resources)
        # log.log(TRACE, '[Filter2][less_shapes] shapes=%s  new_shape=%s with nodes=%s', shapes, new_shape, node_names_for_new_shape)
        return new_shape, node_names_for_new_shape

    new_shapes_to_nodes = {}
    diffs = []

    def merge_shapes(shapes):
        if len(shapes) < 2:
            return
        elif len(shapes) == 2:
            d = shape_diff(*shapes)
            diffs.append(d)
            if d < merge_threshold:
                shape, node_names = create_new_shape(*shapes)
                new_shapes_to_nodes[shape] = node_names
        else:  # >2
            for cl in range(2, len(shapes)):
                for shapes in combinations(shapes_to_nodes.keys(), cl):
                    # log.log(TRACE, '[Filter2][less shapes] comparing shapes:  %s', shapes)
                    merge_shapes(shapes)

    # Do the recursive merging
    merge_shapes(shapes_to_nodes.keys())

    log.log(TRACE, '[Filter2][less shapes] found diffs: %s', list(set(diffs)))

    # All node names.
    all_new_nodes = reduce(operator.add, new_shapes_to_nodes.values(), [])

    # Retain all shapes if not used in new merged shapes
    for shape, nodes in shapes_to_nodes.items():
        if not set(nodes) & set(all_new_nodes):
            new_shapes_to_nodes[shape] = nodes

    return new_shapes_to_nodes


def shape_to_str(shape):
    return ','.join('%r=%.0f'%(r,v) for r, v in shape)


class HierBAR(LeastUsedBAR):

    def __init__(self,
                 data_provider: DataProvider,
                 dimensions: List[ResourceType] = [rt.CPU, rt.MEM, rt.MEMBW_READ, rt.MEMBW_WRITE],
                 alias=None,
                 merge_threshold: float = None,
                 max_node_score: float = 10.
                 ):
        LeastUsedBAR.__init__(self, data_provider, dimensions, alias=alias)
        self.merge_threshold = merge_threshold

    def __str__(self):
        if self.alias:
            return super().__str__()
        return '%s(%d%s)' % (self.__class__.__name__, len(self.dimensions),
                             ',merge=%s'%self.merge_threshold if self.merge_threshold is not None else '')
    def app_fit_nodes(self, node_names, app_name, data_provider_queried
                      ) -> Tuple[List[NodeName], Dict[NodeName, str]]:

        log.log(TRACE, '[Filter2] -> nodes_names=[%s]', ','.join(node_names))
        # TODO: optimize this context should be calculated eariler (add passed for every node)
        nodes_capacities, assigned_apps_counts, apps_spec, _ = data_provider_queried

        # Reverse node_capacities to find type of node
        node_shapes = {node_name: resources_to_shape(node_capacity) for node_name, node_capacity in nodes_capacities.items()}

        shapes_to_nodes = defaultdict(list)
        for node_name, shape in node_shapes.items():
            shapes_to_nodes[shape].append(node_name)
        shapes_to_nodes = dict(shapes_to_nodes)

        # Merging similar node shapes (less_shapes)
        if self.merge_threshold is not None:
            old_number_of_shapes = len(shapes_to_nodes)
            shapes_to_nodes = less_shapes(shapes_to_nodes, nodes_capacities, self.merge_threshold)

            # after shape merging build inverse relation node->shape
            node_shapes = {}
            for shape, nodes in shapes_to_nodes.items():
                for node in nodes:
                    node_shapes[node] = shape
            if old_number_of_shapes != len(shapes_to_nodes):
                log.debug('[Filter2] Merged shapes: %s->%s, new_shapes: %s', old_number_of_shapes , len(shapes_to_nodes), shapes_to_nodes)

        # Number of nodes of each class
        number_of_nodes_each_shape = dict(Counter(node_shapes.values()))
        log.log(TRACE, '[Filter2] Number of nodes in classes: %r', number_of_nodes_each_shape)

        requested = apps_spec[app_name]
        # Calculate all classes bar (fitness) score
        class_bar_variances = {}  # class_shape: fit
        for class_shape, node_names_of_this_shape in shapes_to_nodes.items():
            nodes_capacities_of_this_shape = [nodes_capacities[node_name] for node_name in node_names_of_this_shape]
            averaged_resources_of_class = calc_average_resources_of_nodes(nodes_capacities_of_this_shape)
            requested_empty_fraction = divide_resources(
                requested,
                averaged_resources_of_class,
                calculate_read_write_ratio(averaged_resources_of_class)
            )

            variance = statistics.stdev(requested_empty_fraction.values())
            # log.log(TRACE, '[Prioritize] class_shape=%s average_resources_of_class=%s requested=%s requested_fraction=%s variance=%s', class_shape, averaged_resources_of_class, requested, requested_empty_fraction, variance)
            class_bar_variances[class_shape] = variance

            class_shape_str = shape_to_str(class_shape)
            self.metrics.extend([
                Metric(
                    name='wca_scheduler_hierbar_node_shape_app_variance',
                    labels=dict(app=app_name, shape=class_shape_str),
                    value=variance
                ),
                Metric(
                    name='wca_scheduler_hierbar_node_shape_numbers',
                    labels=dict(shape=class_shape),
                    value=number_of_nodes_each_shape[class_shape]
                )
            ])

            log.log(TRACE, '[Filter2][app=%s] app_shape=%s scores for each class of nodes: %s',
                  app_name, resources_to_shape(requested), class_bar_variances)


        # Start with best class (least variance)
        failed = {} # node_name to error string
        for class_shape, class_bar_variance in sorted(class_bar_variances.items(), key=lambda x:x[1]):
            best_node_names_according_shape = shapes_to_nodes[class_shape]

            accepted_node_names = list(set(node_names) & set(best_node_names_according_shape))
            # if we found at least on node is this class then leave
            if accepted_node_names:
                break
            else:
                log.debug('[Filter2][app=%s] no enough nodes in best class (shape=%s, nodes=[%s]), take next class',
                          app_name, class_shape, ','.join(best_node_names_according_shape))
        else:
            assert False, 'last class has to match!'

        failed_names = set(node_names) - set(accepted_node_names)
        for failed_node_name in failed_names:
            failed_node_variance = class_bar_variances[node_shapes[failed_node_name]]
            failed[failed_node_name] = 'Not best class (best_variance=%.2f this=%.2f)' % (class_bar_variance,  failed_node_variance)

        log.info(
            '[Filter2][app=%s] nodes=[%s] best_class=%r best_class_variance=%.3f best_nodes=[%s]',
            app_name, ','.join(node_names), dict(class_shape),
            class_bar_variance, ','.join(accepted_node_names))

        log.log(TRACE, '[Filter2] <- accepted_node_names=[%s]', ','.join(accepted_node_names))
        return accepted_node_names, failed
