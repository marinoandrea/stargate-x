import pickle
from typing import Iterable, Set

import networkx as nx
import numpy as np
import scipy as sp

from reactome_graph.constants import ENTITY, EVENT
from reactome_graph.data import Pathway
from reactome_graph.utils.cache import cached


class ReactomeGraph(nx.MultiDiGraph):
    """
    Reactome directed multigraph. Its underlying implementation
    uses `networkx.MultiDiGraph`.
    """

    @staticmethod
    def from_pickle(file_path: str) -> 'ReactomeGraph':
        """
        Loads a ReactomeGraph from a pickle file.

        Parameters
        ----------
        file_path: `str`
        File path to a pickled ReactomeGraph.

        Returns
        -------
        `ReactomeGraph`
        The returned graph is a freezed instance of `networkx.MultiDiGraph` so
        it cannot be changed without unfreezing first.
        """
        with open(file_path, 'rb') as f:
            out: ReactomeGraph = nx.freeze(pickle.load(f))
        return out

    @property  # type: ignore
    @cached
    def adjacency_matrix(self) -> sp.sparse.csc_matrix:
        out = nx.adjacency_matrix(self)
        return sp.sparse.csc_matrix(out, dtype=np.int8)

    @property  # type: ignore
    @cached
    def event_nodes(self) -> Set[str]:
        return {n for n, d in self.nodes(data=True)
                if d['bipartite'] == EVENT}

    @property  # type: ignore
    @cached
    def entity_nodes(self) -> Set[str]:
        return {n for n, d in self.nodes(data=True)
                if d['bipartite'] == ENTITY}

    @property  # type: ignore
    @cached
    def top_level_pathways(self) -> Iterable[Pathway]:
        return list(filter(lambda x: x.is_top_level, self.pathways))
