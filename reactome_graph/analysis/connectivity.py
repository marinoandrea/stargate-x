import networkx as nx
from .base import GraphAnalyzer
from reactome_graph import EVENT
from typing import Dict


class ConnectivityAnalyzer(GraphAnalyzer):

    def intersection_components_pathways(self, weakly: bool = False) -> (
            Dict[str, Dict[int, float]]):

        ccs = (nx.weakly_connected_components(self.graph) if weakly
               else nx.strongly_connected_components(self.graph))
        ccs = {i: set(n for n in cc
                      if self.graph.nodes[n]['bipartite'] == EVENT)
               for i, cc in enumerate(ccs)}

        out = {}
        for p in self.graph.pathways:
            out[p] = {}
            for cc in ccs:
                perc = (len(self.graph.pathways[p]['nodes'] & ccs[cc])
                        / len(self.graph.pathways[p]['nodes']))
                if perc > 0:
                    out[p][cc] = perc

        return out
