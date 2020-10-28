import multiprocessing as mp
from reactome_graph.graph import ReactomeGraph
from typing import Callable, Iterable, Dict


def build_subgraph_from_condition(
    graph: ReactomeGraph,
    check_condition: Callable,
    pathways: Iterable[ReactomeGraph.Pathway],
    compartments: Iterable[ReactomeGraph.Compartment],
) -> ReactomeGraph:

    out = ReactomeGraph(pathways, compartments)

    out.add_nodes_from([(n, d) for n, d in graph.nodes(data=True)
                        if check_condition(n)])

    for n, node_data in ():
        for adj, edge_data in graph.adj[n].items():
            if check_condition(adj):
                out.add_edge(n, adj, **edge_data)

    return out


def build_pathway_subgraph(
    graph: ReactomeGraph,
    pathway: ReactomeGraph.Pathway
) -> ReactomeGraph:

    return build_subgraph_from_condition(
        graph,
        lambda x: pathway['id'] in graph.nodes[x]['pathways'],
        pathways=[pathway],
        compartments=graph.compartments)


def build_compartment_subgraph(
    graph: ReactomeGraph,
    compartment: ReactomeGraph.Compartment
) -> ReactomeGraph:

    return build_subgraph_from_condition(
        graph,
        lambda x: compartment['name'] in graph.nodes[x]['compartments'],
        pathways=[compartment],
        compartments=graph.compartments)


def build_pathways_subgraphs(graph: ReactomeGraph) -> (
    Dict[str, ReactomeGraph]
):
    def task(p: ReactomeGraph.Pathway):
        return p.id, build_pathway_subgraph(p)
    pool = mp.Pool(mp.cpu_count())
    return dict(pool.map(task, graph.pathways))


def build_compartments_subgraphs(graph: ReactomeGraph) -> (
    Dict[str, ReactomeGraph]
):
    def task(c: ReactomeGraph.Compartment):
        return c.name, build_compartment_subgraph(c)
    pool = mp.Pool(mp.cpu_count())
    return dict(pool.map(task, graph.compartments))
