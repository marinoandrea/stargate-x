import networkx as nx
import scipy as sp
import numpy as np
from reactome_graph import EVENT, ENTITY
from reactome_graph.utils.cache import cached
from typing import Dict, Set, Union


class ReactomeGraph(nx.MultiDiGraph):

    def __init__(self, **kwargs):
        """
        Reactome directed multigraph. Its underlying implementation
        uses `networkx.MultiDiGraph`.
        """
        super().__init__(**kwargs)
        self._cache = {}

    @property
    @cached
    def adjacency_matrix(self) -> sp.sparse.csc_matrix:
        out = nx.adjacency_matrix(self)
        out = sp.sparse.csc_matrix(out, dtype=np.int8)
        return out

    @property
    @cached
    def event_nodes(self) -> Set[str]:
        return {n for n, d in self.nodes(data=True)
                if d['bipartite'] == EVENT}

    @property
    @cached
    def entity_nodes(self) -> Set[str]:
        return {n for n, d in self.nodes(data=True)
                if d['bipartite'] == ENTITY}

    @property
    @cached
    def pathways(self) -> Dict[str, Dict[str, Union[int, Set[str]]]]:
        """
        A dictionary containing information about pathways
        represented in the graph.
        The dictionary has pathway stIds as keys and for each
        pathway contains its depth level and a set of reaction
        nodes contained in the pathway.

        Returns
        -------
        Dict[str, Dict[str, Union[int, Set[str]]]]
            The dictionary containing pathway information.
        """
        out = {}
        for n, data in self.nodes(data=True):
            try:
                for p in data['pathways']:
                    st_id, lvl = p['stId'], p['level']
                    if st_id not in out:
                        out[st_id] = {'level': lvl, 'nodes': set()}
                    out[st_id]['nodes'].add(n)
            except KeyError:
                continue
        return out
