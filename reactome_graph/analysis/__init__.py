import networkx as nx
import multiprocessing as mp
from typing import Dict, Union, Callable
from .centrality import CentralityAnalyzer


class GraphAnalyzer(object):

    def __init__(self, graph: nx.MultiDiGraph):
        self.graph = graph

    def analyze_centrality(self) -> Dict[str, Dict[str, Union[int, float]]]:
        """
        Applies centrality measures on all nodes.

        Returns
        -------
        results: dict
            Dictionary containing reasults for each centrality measure.
            Each result set is a dictionary with id - value pairs
            for each node.
        """

        def _worker(name: str, task: Callable, results: dict):
            results[name] = task()

        analyzer = CentralityAnalyzer(self.graph)

        tasks = {
            'closeness': analyzer.calculate_closeness,
            'degree': analyzer.calculate_degree,
            'laplacian': analyzer.calculate_laplacian,
            'leverage': analyzer.calculate_leverage,
            'h_index': analyzer.calculate_h_index
            # TODO: add more centrality measures
        }

        manager = mp.Manager()
        results = manager.dict()

        processes = []
        for name, task in tasks.items():
            p = mp.Process(target=_worker, args=(name, task, results))
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

        return results

    def analyze_components(self):
        pass
