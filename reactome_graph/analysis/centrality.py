import networkx as nx
import scipy as sp
import numpy as np
import multiprocessing as mp
from multiprocessing.shared_memory import SharedMemory
from os import cpu_count
from functools import partial
from typing import Tuple, Sequence, Dict, Set


class CentralityAnalyzer(object):

    def __init__(self, graph: nx.MultiDiGraph):
        self._graph = graph
        self._cache = {}
        self._pool = mp.Pool(cpu_count())

    @property
    def adjacency_matrix(self) -> sp.sparse.csc_matrix:
        if 'adjacency_matrix' in self._cache:
            return self._cache['adjacency_matrix']
        out = nx.adjacency_matrix(self._graph)
        out = sp.sparse.csc_matrix(out, dtype=np.int8)
        self._cache['adjacency_matrix'] = out
        return out

    @property
    def top_nodes(self) -> Set[str]:
        if 'top_nodes' in self._cache:
            return self._cache['top_nodes']
        if 'bottom_nodes' in self._cache:
            return set(self._graph) - self._cache['bottom_nodes']
        out = {n for n, d in self._graph.nodes(data=True)
               if d['bipartite'] == 0}
        self._cache['top_nodes'] = out
        return out

    @property
    def bottom_nodes(self) -> Set[str]:
        if 'bottom_nodes' in self._cache:
            return self._cache['bottom_nodes']
        if 'top_nodes' in self._cache:
            return set(self._graph) - self._cache['top_nodes']
        out = {n for n, d in self._graph.nodes(data=True)
               if d['bipartite'] == 1}
        self._cache['bottom_nodes'] = out
        return out

    def calculate_laplacian(self) -> Dict[str, float]:
        out = {}
        for n in self._graph.nodes:
            d = self._graph.out_degree(n)
            value = d * d + d + 2 * sum(self._graph.out_degree(adj)
                                        for adj in self._graph[n])
            out[n] = value
        return out

    def calculate_closeness(self) -> Dict[str, float]:
        return nx.bipartite.closeness_centrality(
            self._graph, self.top_nodes, normalized=True)

    def calculate_degree(self) -> Dict[str, float]:
        return nx.bipartite.degree_centrality(self._graph, self.top_nodes)

    def calculate_leverage(self) -> Dict[str, float]:
        out = {}
        degrees = self._graph.out_degree(self._graph.nodes)
        for n in self._graph.nodes:
            d = degrees[n]
            if d == 0:
                value = 0
                continue
            value = sum((d - degrees[adj])/(d + degrees[adj])
                        for adj in self._graph[n]) / d
            out[n] = value
        return out

    def calculate_h_index(self) -> Dict[str, float]:
        out = {}
        degrees = self._graph.out_degree(self._graph.nodes)
        for n in self._graph.nodes:
            d = degrees[n]
            value = 0
            for h in range(1, d + 1):
                adjs_h = [adj for adj in self._graph[n] if degrees[adj] > h]
                h_value = min(len(adjs_h), h)
                value = max(value, h_value)
            out[n] = value
        return out

    def calculate_subgraph(self) -> Dict[str, float]:
        out = {}
        A = self.adjacency_matrix
        e_A = sp.linalg.expm(A)
        for i, n in enumerate(self._graph.nodes):
            out[n] = e_A[i][i]
        return out


def _information_setup(G: nx.MultiDiGraph, D_mem: str, A_mem: str, node_t: Tuple[int, str]):
    shape = len(G.nodes), len(G.nodes)

    D_shared = SharedMemory(name=D_mem)
    A_shared = SharedMemory(name=A_mem)

    D = np.ndarray(shape, dtype=np.int8, buffer=D_shared.buf)
    A = np.ndarray(shape, dtype=np.int8, buffer=A_shared.buf)

    i1, n1 = node_t
    D[i1][i1] = G.out_degree(n1)
    for i2, n2 in enumerate(G.nodes):
        A[i1][i2] = G.number_of_edges(u=n1, v=n2)

    D_shared.close()
    A_shared.close()


def _information_value(G: nx.MultiDiGraph, C_mem: str, d_sum: float,
                       node_t: Tuple[int, str]) -> Tuple[str, float]:

    shape = len(G.nodes), len(G.nodes)

    C_shared = SharedMemory(name=C_mem)
    C = np.ndarray(shape, dtype=np.float16, buffer=C_shared.buf)

    i, n = node_t
    l_sum = sum(C[i][j] for j, _ in enumerate(G.nodes))
    value = 1 / (C[i][i] + (d_sum - 2 * l_sum) / shape[0])

    C_shared.close()
    return n, value


def calculate_information(G: nx.MultiDiGraph) -> Sequence[Tuple[str, float]]:

    shape = len(G.nodes), len(G.nodes)

    pool = mp.Pool(cpu_count())

    # memory init
    templatei = np.zeros(shape, dtype=np.int8)
    templatef = np.zeros(shape, dtype=np.float16)
    D_shared = SharedMemory(create=True, size=templatei.nbytes)
    A_shared = SharedMemory(create=True, size=templatei.nbytes)
    C_shared = SharedMemory(create=True, size=templatef.nbytes)
    del templatei, templatef

    D = np.ndarray(shape, dtype=np.int8, buffer=D_shared.buf)
    A = np.ndarray(shape, dtype=np.int8, buffer=A_shared.buf)
    C = np.ndarray(shape, dtype=np.float16, buffer=C_shared.buf)

    # run setup jobs
    pool.map(partial(_information_setup, G, D_shared.name,
                     A_shared.name), enumerate(G.nodes))
    # cleanup
    L = D - A
    del D, A
    D_shared.close()
    A_shared.close()
    D_shared.unlink()
    A_shared.unlink()

    # C = (L + A)^-1
    L = L + np.ones(shape, dtype=np.int8)
    np.copyto(C, L, casting='safe')
    del L
    C = C ** -1

    # diagonal sum
    d_sum = sum(C[j][j] for j, _ in enumerate(G.nodes))

    # run information centrality calculation jobs
    out = pool.map(partial(_information_value, G,
                           C_shared.name, d_sum), enumerate(G.nodes))
    # cleanup
    C_shared.close()
    C_shared.unlink()
    pool.terminate()
    pool.join()

    return out
