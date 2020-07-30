import scipy as sp
import numpy as np
import networkx as nx
from typing import Set
from reactome_graph import EVENT, ENTITY


class GraphAnalyzer(object):

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph
        self._cache = {}

    @property
    def adjacency_matrix(self) -> sp.sparse.csc_matrix:
        if 'adjacency_matrix' in self._cache:
            return self._cache['adjacency_matrix']
        out = nx.adjacency_matrix(self._graph)
        out = sp.sparse.csc_matrix(out, dtype=np.int8)
        self._cache['adjacency_matrix'] = out
        return out

    @property
    def event_nodes(self) -> Set[str]:
        if 'event_nodes' in self._cache:
            return self._cache['event_nodes']
        if 'entity_nodes' in self._cache:
            return set(self._graph) - self._cache['entity_nodes']
        out = {n for n, d in self._graph.nodes(data=True)
               if d['bipartite'] == EVENT}
        self._cache['event_nodes'] = out
        return out

    @property
    def entity_nodes(self) -> Set[str]:
        if 'entity_nodes' in self._cache:
            return self._cache['entity_nodes']
        if 'event_nodes' in self._cache:
            return set(self._graph) - self._cache['event_nodes']
        out = {n for n, d in self._graph.nodes(data=True)
               if d['bipartite'] == ENTITY}
        self._cache['entity_nodes'] = out
        return out
