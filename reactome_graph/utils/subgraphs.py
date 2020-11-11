import multiprocessing as mp
from reactome_graph.graph import ReactomeGraph
from typing import Callable, Iterable, Dict
from functools import partial


def build_subgraph_from_condition(
    graph: ReactomeGraph,
    check_condition: Callable,
    pathways: Iterable[ReactomeGraph.Pathway],
    compartments: Iterable[ReactomeGraph.Compartment],
) -> ReactomeGraph:
    out = ReactomeGraph()
    out.pathways = pathways
    out.compartments = compartments

    for node, data in graph.nodes(data=True):
        try:
            if check_condition(node):
                out.add_node(node, **data)
        except Exception:
            continue

    for u, v, data in graph.edges(data=True):
        if (u in out.nodes and v in out.nodes):
            out.add_edge(u, v, **data)

    return out


def build_pathway_subgraph(
    graph: ReactomeGraph,
    pathway: str
) -> ReactomeGraph:

    _pathway = next(p for p in graph.pathways if p.id == pathway)

    return build_subgraph_from_condition(
        graph,
        lambda x: pathway in graph.nodes[x]['pathways'],
        pathways=[_pathway],
        compartments=graph.compartments)


def build_compartment_subgraph(
    graph: ReactomeGraph,
    compartment: str
) -> ReactomeGraph:

    _compartment = next(c for c in graph.compartments if c.id == compartment)

    return build_subgraph_from_condition(
        graph,
        lambda x: compartment in graph.nodes[x]['compartments'],
        pathways=graph.pathways,
        compartments=[_compartment])


def _pathways_task(graph, p: str):
    return p, build_pathway_subgraph(graph, p)


def build_pathways_subgraphs(
    graph: ReactomeGraph,
    pathways: Iterable[str]
) -> Dict[str, ReactomeGraph]:
    pool = mp.Pool(mp.cpu_count())
    return dict(pool.map(partial(_pathways_task, graph), pathways))


def _compartments_task(graph, c: str):
    return c, build_compartment_subgraph(graph, c)


def build_compartments_subgraphs(
    graph: ReactomeGraph,
    compartments: Iterable[str]
) -> Dict[str, ReactomeGraph]:
    pool = mp.Pool(mp.cpu_count())
    return dict(pool.map(partial(_compartments_task, graph), compartments))
