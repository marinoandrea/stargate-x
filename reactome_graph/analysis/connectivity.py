import networkx as nx
from .base import GraphAnalyzer
from reactome_graph import EVENT
from typing import Dict, Set


class ConnectivityAnalyzer(GraphAnalyzer):

    @property
    def pathways(self) -> Dict[str, Set[str]]:
        if 'pathways' in self._cache:
            return self._cache['pathways']
        pathways = {}
        for n in self.graph.nodes():
            if 'pathways' not in self.graph.nodes[n]:
                continue
            for p in self.graph.nodes[n]['pathways']:
                st_id = p['stId']
                if st_id not in pathways:
                    pathways[st_id] = set()
                pathways[st_id].add(n)
        self._cache['pathways'] = pathways
        return pathways

    def intersection_components_pathways(self, weakly: bool = False) -> (
            Dict[str, Dict[int, float]]):

        ccs = (nx.weakly_connected_components(self.graph) if weakly
               else nx.strongly_connected_components(self.graph))
        ccs = {i: set(n for n in cc
                      if self.graph.nodes[n]['bipartite'] == EVENT)
               for i, cc in enumerate(ccs)}

        out = {}
        for p in self.pathways:
            out[p] = {}
            for cc in ccs:
                perc = (len(self.pathways[p] & ccs[cc])
                        / len(self.pathways[p]))
                if perc > 0:
                    out[p][cc] = perc

        return out
