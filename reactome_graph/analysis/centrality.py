import scipy as sp
import numpy as np
import multiprocessing as mp
import networkx as nx
from .base import GraphAnalyzer
from multiprocessing.shared_memory import SharedMemory
from os import cpu_count
from functools import partial
from typing import Tuple, Sequence, Dict


class CentralityAnalyzer(GraphAnalyzer):

    def calculate_laplacian(self) -> Dict[str, float]:
        out = {}
        for n in self.graph.nodes:
            d = self.graph.out_degree(n)
            value = d * d + d + 2 * sum(self.graph.out_degree(adj)
                                        for adj in self.graph[n])
            out[n] = value
        return out

    def calculate_closeness(self) -> Dict[str, float]:
        return nx.bipartite.closeness_centrality(
            self.graph, self.graph.event_nodes, normalized=True)

    def calculate_degree(self) -> Dict[str, float]:
        return nx.bipartite.degree_centrality(self.graph, self.event_nodes)

    def calculate_leverage(self) -> Dict[str, float]:
        out = {}
        degrees = self.graph.out_degree(self.graph.nodes)
        for n in self.graph.nodes:
            d = degrees[n]
            if d == 0:
                value = 0
                continue
            value = sum((d - degrees[adj])/(d + degrees[adj])
                        for adj in self.graph[n]) / d
            out[n] = value
        return out

    def calculate_h_index(self) -> Dict[str, float]:
        out = {}
        degrees = self.graph.out_degree(self.graph.nodes)
        for n in self.graph.nodes:
            d = degrees[n]
            value = 0
            for h in range(1, d + 1):
                adjs_h = [adj for adj in self.graph[n] if degrees[adj] > h]
                h_value = min(len(adjs_h), h)
                value = max(value, h_value)
            out[n] = value
        return out

    def calculate_subgraph(self) -> Dict[str, float]:
        out = {}
        A = self.adjacency_matrix
        e_A = sp.linalg.expm(A)
        for i, n in enumerate(self.graph.nodes):
            out[n] = e_A[i][i]
        return out

    def _information_setup(self, D_mem: str, A_mem: str,
                           node_t: Tuple[int, str]):
        shape = len(self.graph.nodes), len(self.graph.nodes)

        D_shared = SharedMemory(name=D_mem)
        A_shared = SharedMemory(name=A_mem)

        D = np.ndarray(shape, dtype=np.int8, buffer=D_shared.buf)
        A = np.ndarray(shape, dtype=np.int8, buffer=A_shared.buf)

        i1, n1 = node_t
        D[i1][i1] = self.graph.out_degree(n1)
        for i2, n2 in enumerate(self.graph.nodes):
            A[i1][i2] = self.graph.number_of_edges(u=n1, v=n2)

        D_shared.close()
        A_shared.close()

    def _information_value(self, C_mem: str, d_sum: float,
                           node_t: Tuple[int, str]) -> Tuple[str, float]:

        shape = len(self.graph.nodes), len(self.graph.nodes)

        C_shared = SharedMemory(name=C_mem)
        C = np.ndarray(shape, dtype=np.float16, buffer=C_shared.buf)

        i, n = node_t
        l_sum = sum(C[i][j] for j, _ in enumerate(self.graph.nodes))
        value = 1 / (C[i][i] + (d_sum - 2 * l_sum) / shape[0])

        C_shared.close()
        return n, value

    def calculate_information(self) -> Sequence[Tuple[str, float]]:

        shape = len(self.graph.nodes), len(self.graph.nodes)

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
        pool.map(partial(self._information_setup, D_shared.name,
                         A_shared.name), enumerate(self.graph.nodes))
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
        d_sum = sum(C[j][j] for j, _ in enumerate(self.graph.nodes))

        # run information centrality calculation jobs
        out = pool.map(partial(self._information_value, C_shared.name, d_sum),
                       enumerate(self.graph.nodes))
        # cleanup
        C_shared.close()
        C_shared.unlink()
        pool.terminate()
        pool.join()

        return out
