import json
import pickle
import os
import networkx as nx
import multiprocessing as mp
from functools import partial
from typing import Sequence

ENTITY = 0
EVENT = 1
DATA_DIR = './data/species'
REL_TYPES = ['input', 'output', 'catalyst',
             'positiveRegulator', 'negativeRegulator']


def _parse_graph(edges_tsv: str, nodes_json: str,
                 rel_types: Sequence[str]) -> nx.MultiDiGraph:

    with open(edges_tsv, 'r') as f1, open(nodes_json, 'r') as f2:
        lines = f1.readlines()
        nodes = json.load(f2)

    graph = nx.MultiDiGraph()

    for line in lines:

        if not line.startswith('R'):
            continue

        source_id, target_id, rel_type, order, stoichiometry = line.strip().split('\t')
        order = int(order) if order != 'None' else None
        stoichiometry = int(stoichiometry) if stoichiometry != 'None' else None

        if rel_types is not None:
            if rel_type not in rel_types:
                continue

        # switch specific edges direction
        if rel_type in ['input', 'catalyst', 'positiveRegulator',
                        'negativeRegulator', 'catalystActiveUnit',
                        'regulatorActiveUnit']:
            t = source_id
            source_id = target_id
            target_id = t

        try:
            source, target = nodes[source_id], nodes[target_id]
            source['bipartite'] = EVENT if 'Event' in source['labels'] else ENTITY
            target['bipartite'] = EVENT if 'Event' in target['labels'] else ENTITY
            graph.add_node(source['stId'], **source)
            graph.add_node(target['stId'], **target)
            graph.add_edge(source_id, target_id,
                           relType=rel_type,
                           order=order,
                           stoichiometry=stoichiometry)
        except KeyError:
            continue

    return graph


def build_graph_species(data_dir: str, rel_types: Sequence[str],
                        species: str) -> nx.MultiDiGraph:
    """
    Build a `networkx.MultiDiGraph` from data. The built graph will also
    be stored in the species' data folder.

    Parameters
    ----------

    data_dir : str
        Path to a data folder storing data for all species.
        Each species must have a corresponding folder in which
        an edges.tsv file and a nodes.json file can be found.
        Specific formats for the two files can be found in documentation
        for the 'generate_data.py' script.

    rel_types: list
        List of relationship types to include represented as strings.

    species: str
        The name/code of the species, must be the same name of the
        species data folder.

    Returns
    -------

    graph: `networkx.MultiDiGraph`
        The bipartite directed multigraph representing the species' pathways.
    """
    edges_file = f'{data_dir}/{species}/edges.tsv'
    nodes_file = f'{data_dir}/{species}/nodes.json'
    graph = _parse_graph(edges_file, nodes_file, rel_types)

    graph_file = f'{data_dir}/{species}/graph.pickle'
    with open(graph_file, 'wb') as f:
        pickle.dump(graph, f)

    return graph


def build_graphs(data_dir: str, rel_types: Sequence[str]):
    """
    Build `networkx.MultiDiGraph` for all species contained in the data folder.
    Built graphs will also be stored in the species' data folder.

    Parameters
    ----------

    data_dir : str
        Path to a data folder storing data for all species.
        Each species must have a corresponding folder in which
        an edges.tsv file and a nodes.json file can be found.
        Specific formats for the two files can be found in documentation
        for the 'generate_data.py' script.

    rel_types: list
        List of relationship types to include represented as strings.
    """
    pool = mp.Pool(os.cpu_count())
    _, species, _ = next(os.walk(data_dir))
    pool.map(partial(build_graph_species, data_dir, rel_types), species)
    pool.close()
    pool.join()


def main():

    build_graphs(DATA_DIR, REL_TYPES)


if __name__ == '__main__':
    main()
