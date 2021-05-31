from typing import Dict

import networkx as nx


def leverage_centrality(
    graph: nx.DiGraph, deg_type: str = 'out_degree'
) -> Dict[str, float]:
    """
    Compute leverage centrality for graph.
    """
    out: Dict[str, float] = {}
    for n in graph.nodes:
        d = getattr(graph, deg_type)(n)
        if d == 0:
            value = 0
        else:
            value = sum((d - getattr(graph, deg_type)(adj)) /
                        (d + getattr(graph, deg_type)(adj)
                         ) for adj in graph[n]) / d
        out[n] = value
    return out


def h_index_centrality(
    graph: nx.DiGraph, deg_type: str = 'out_degree'
) -> Dict[str, float]:
    """
    Compute h-index centrality for graph.
    """
    out: Dict[str, float] = {}
    for n in graph.nodes:
        d = getattr(graph, deg_type)(n)
        value = 0
        for h in range(1, d + 1):
            adjs_h = [
                adj for adj in graph[n]
                if getattr(graph, deg_type)(adj) > h
            ]
            h_value = min(len(adjs_h), h)
            value = max(value, h_value)
        out[n] = value
    return out


def laplacian_centrality(
    graph: nx.DiGraph, deg_type: str = 'out_degree'
) -> Dict[str, float]:
    """
    Compute laplacian centrality for graph.
    """
    out: Dict[str, float] = {}
    for n in graph.nodes:
        d = getattr(graph, deg_type)(n)
        value = (
            d * d + d + 2 *
            sum(
                getattr(graph, deg_type)(adj)
                for adj in graph[n]
            )
        )
        out[n] = value
    return out
