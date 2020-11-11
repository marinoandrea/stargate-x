import scipy as sp
import numpy as np
import networkx as nx
import pickle
from typing import Set, Iterable
from dataclasses import dataclass
from reactome_graph.utils.cache import cached
from reactome_graph.constants import ENTITY, EVENT


class ReactomeGraph(nx.MultiDiGraph):
    """
    Reactome directed multigraph. Its underlying implementation
    uses `networkx.MultiDiGraph`.
    """

    @dataclass(frozen=True, eq=True)
    class Pathway:
        id: str
        name: str
        is_top_level: bool
        in_disease: bool

    @dataclass(frozen=True, eq=True)
    class Compartment:
        id: str
        name: str

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
            out = nx.freeze(pickle.load(f))
        return out

    @property
    @cached
    def adjacency_matrix(self) -> sp.sparse.csc_matrix:
        out = nx.adjacency_matrix(self)
        return sp.sparse.csc_matrix(out, dtype=np.int8)

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
    def top_level_pathways(self) -> Iterable[Pathway]:
        return list(filter(lambda x: x.is_top_level, self.pathways))