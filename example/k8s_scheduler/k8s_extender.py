import http.server
import json
import logging
import socketserver
from typing import Dict, List

import math
import requests
from dataclasses import dataclass

log = logging.getLogger(__name__)

# PUBLIC CONFIG
PORT = 12345
PROMETHEUS = 'http://100.64.176.36:9090'
NAMESPACE = 'default'
LEVEL = logging.INFO
FIT_MODE = "rsswss"

# CONSTANTS
_PROMETHEUS_QUERY_PATH = "/api/v1/query"
_PROMETHEUS_QUERY_RANGE_PATH = "/api/v1/query_range"
_PROMETHEUS_URL_TPL = '{prometheus}{path}?query={name}'
_PROMETHEUS_RANGE_TPL = '&start={start}&end={end}&step=1s'
_PROMETHEUS_TIME_TPL = '&time={time}'
_PROMETHEUS_TAG_TPL = '{key}="{value}"'


def _build_raw_query(prometheus, query, time=None):
    path = _PROMETHEUS_QUERY_PATH
    url = _PROMETHEUS_URL_TPL.format(
        prometheus=prometheus,
        path=path,
        name=query,
    )
    if time:
        url += _PROMETHEUS_TIME_TPL.format(time=time)
    return url


# def _build_prometheus_url(prometheus, name, tags=None, start=None, end=None, time=None):
#     tags = tags or dict()
#
#     # Some variables need to be overwritten for range queries.
#     if start and end:
#         path = _PROMETHEUS_QUERY_RANGE_PATH
#         time_range = _PROMETHEUS_RANGE_TPL.format(start=start, end=end)
#     elif time:
#         path = _PROMETHEUS_QUERY_PATH
#         time_range = _PROMETHEUS_TIME_TPL % time
#     else:
#         path = _PROMETHEUS_QUERY_PATH
#         time_range = ''
#
#     url_and_query_without_tags = _PROMETHEUS_URL_TPL.format(
#         prometheus=prometheus,
#         path=path,
#         name=name,
#     )
#
#     # Build final URL from all the components.
#     if tags:
#         # Prepare additional tags for query.
#         query_tags = []
#         for k, v in tags.items():
#             query_tags.append(_PROMETHEUS_TAG_TPL.format(key=k, value=v))
#         query_tags_str = ','.join(query_tags)
#         url = ''.join([url_and_query_without_tags, "{", query_tags_str, "}", time_range])
#     else:
#         url = ''.join([url_and_query_without_tags, time_range])
#
#     return url


# def do_query(name, result_tag, tags=None, time=None):
#     url = _build_prometheus_url(PROMETHEUS, name, tags=tags, time=time)
#     response = requests.get(url)
#     response = response.json()
#     if response['status'] == 'error':
#         raise Exception(response['error'])
#     assert response['data']['resultType'] == 'vector'
#     result = response['data']['result']
#     return {pair['metric'][result_tag]: float(pair['value'][1]) for pair in result}


def do_raw_query(query, result_tag, time):
    url = _build_raw_query(PROMETHEUS, query, time)
    response = requests.get(url)
    response = response.json()
    if response['status'] == 'error':
        raise Exception(response['error'])
    assert response['data']['resultType'] == 'vector'
    result = response['data']['result']
    return {pair['metric'][result_tag]: float(pair['value'][1]) for pair in result}

TIME = '2019-09-09T20:08:00Z'
PRIORITY_QUERY = 'avg_over_time(fit_avg{app="%s"}[8m])'
# http://100.64.176.12:3000/d/D-6RTCSWz/aep-demo1?orgId=1&from=1568059380211&to=1568059679940

def _get_priorities(app, nodes):
    """ in range 0 - 1 from query """
    priorities = {}
    query = PRIORITY_QUERY %(app)
    nodes_fit = do_raw_query(query, 'node', TIME)
    log.debug('nodes_fit for %r: %r', app, nodes_fit)
    for node in nodes:
        if node in nodes_fit:
            value = nodes_fit[node]
            if math.isnan(value):
                logging.debug('NaN fit value for %s - ignored')
                continue
            priorities[node] = value
        else:
            logging.debug('missing fit for %s - ignored')
            continue

    return priorities

### ------------------------------ FILTERING (predicates) ----------------------

FILTER_FIT_THRESHOLD = 0.5

def _filter_logic(app, nodes, namespace):
    if namespace != NAMESPACE:
        log.debug('ignoring pods not from %r namespace (got %r)', NAMESPACE, namespace)
        return nodes

    priorities = _get_priorities(app, nodes)
    if len(priorities) == 0:
        log.debug('"%s" priorities not found - ignoring', app)
        return nodes
    else:
        log.debug('"%s" priorities for filter %r', app, priorities)
        nodes = list({node for node in nodes if node in priorities and priorities[node] > FILTER_FIT_THRESHOLD})

    return nodes

### ------------------------------ PRIORITIES ------------------------------

WEIGHT_MULTIPLER = 30.0

def _prioritize_logic(app, nodes, namespace):
    if namespace != NAMESPACE:
        log.debug('ignoring pods not from %r namespace (got %r)', NAMESPACE, namespace)
        return {}
    unweighted_priorities = _get_priorities(app, nodes)
    priorities = {node:(priority * WEIGHT_MULTIPLER) for node, priority in unweighted_priorities.items()}
    return priorities


@dataclass
class ExtenderArgs:
    Nodes: List[Dict]
    Pod: dict
    NodeNames: List[str]


class K8SHandler(http.server.BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        args = json.loads(self.rfile.read(content_length).decode())
        extender_args = ExtenderArgs(**args)

        if self.path == "/api/scheduler/filter":
            result_simple = self._filter(extender_args)
        elif self.path == "/api/scheduler/prioritize":
            result_simple = self._prioritize(extender_args)
        else:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.end_headers()

        result_as_json = json.dumps(result_simple).encode()
        log.debug('%s %s', self.path, result_as_json)
        self.wfile.write(result_as_json)

    def log_request(self, code='-', size='-'):
        pass

    def _extract_common_input(self, extender_args):
        """ :returns app, nodes, namespace"""
        nodes = extender_args.NodeNames
        labels = extender_args.Pod['metadata']['labels']
        # generic input
        namespace = extender_args.Pod['metadata']['namespace']
        # specific workloads input
        app = labels.get('app', None)
        return app, nodes, namespace

    def _filter(self, extender_args):
        # Logic
        log.debug('Pod: \n%s:', json.dumps(extender_args.Pod, indent=4))
        app, nodes, namespace = self._extract_common_input(extender_args)
        self._extract_common_input(extender_args)
        nodes = _filter_logic(app, nodes, namespace)
        log.info('"%s" allowed nodes= %s', app, ', '.join(nodes))
        # Encode
        return dict(
            NodeNames=nodes,
            FailedNodes={},
            Error='',
        )

    def _prioritize(self, extender_args: ExtenderArgs):
        # Logic
        app, nodes, namespace = self._extract_common_input(extender_args)
        priorities = _prioritize_logic(app, nodes, namespace)
        log.info('"%s" priorities=  %r', app, ', '.join('%s:%d' %(k,v) for k,v in sorted(priorities.items(), key=lambda x: x[0])))
        # Encode as PriorityList
        priority_list = [dict(Host=node, Score=priorities.get(node, 0)) for node in nodes]
        log.debug('priority list = %s', ', '.join('%s=%s' % (d['Host'], d['Score']) for d in sorted(priority_list, key=lambda d: d['Host'])))
        return priority_list


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def main(level, port):
    logging.basicConfig(level=level)
    with http.server.HTTPServer(('', port), K8SHandler) as httpd:
        log.info('serving at port: %s', port)
        httpd.serve_forever()


if __name__ == '__main__':
    main(LEVEL, PORT)
