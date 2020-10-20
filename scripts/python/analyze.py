import pickle
import json
import argparse as ap
import multiprocessing as mp
import networkx as nx
from pathlib import Path
from reactome_graph import (
    CentralityAnalyzer, ConnectivityAnalyzer, ReactomeGraph)
from typing import Callable, Dict, Union
from functools import partial

DATA_DIR = './data/species'
SPECIES = ['HSA']


def _worker(name: str, task: Callable, results: dict):
    results[name] = task()


def _get_subgraph_connectivity(graph: ReactomeGraph):
    out = {'compartments': {}, 'pathways': {}}

    compartment_subgraphs = graph.get_compartments_subgraphs()
    for c in compartment_subgraphs:
        out['compartments'][c] = {}
        subgraph = compartment_subgraphs[c]
        scc = list(nx.strongly_connected_components(subgraph))
        wcc = list(nx.weakly_connected_components(subgraph))

        out['compartments'][c]['scc'] = {'total': len(scc)}
        scc_sizes = {}
        for c_size in [*map(len, scc)]:
            scc_sizes[c_size] = scc_sizes.get(c_size, 0) + 1
        out['compartments'][c]['scc']['sizes'] = scc_sizes

        out['compartments'][c]['wcc'] = {'total': len(wcc)}
        wcc_sizes = {}
        for c_size in [*map(len, wcc)]:
            wcc_sizes[c_size] = wcc_sizes.get(c_size, 0) + 1
        out['compartments'][c]['wcc']['sizes'] = wcc_sizes

    pathway_subgraphs = graph.get_pathways_subgraphs()
    for c in pathway_subgraphs:
        out['pathways'][c] = {}
        subgraph = pathway_subgraphs[c]
        scc = list(nx.strongly_connected_components(subgraph))
        wcc = list(nx.weakly_connected_components(subgraph))

        out['pathways'][c]['scc'] = {'total': len(scc)}
        scc_sizes = {}
        for c_size in [*map(len, scc)]:
            scc_sizes[c_size] = scc_sizes.get(c_size, 0) + 1
        out['pathways'][c]['scc']['sizes'] = scc_sizes

        out['pathways'][c]['wcc'] = {'total': len(wcc)}
        wcc_sizes = {}
        for c_size in [*map(len, wcc)]:
            wcc_sizes[c_size] = wcc_sizes.get(c_size, 0) + 1
        out['pathways'][c]['wcc']['sizes'] = wcc_sizes

    return out


def _analyze_stats(graph: ReactomeGraph, s: str):
    data = {}

    # bipartition
    data['bipartition'] = {
        'events': len(graph.event_nodes),
        'entities': len(graph.entity_nodes),
    }

    # pathways
    data['pathways'] = [p['name'] for p in graph.top_level_pathways.values()]

    # compartments
    data['compartments'] = [p for p in graph.compartments]

    # count node classes
    classes = {}
    for node in graph.nodes:
        s_class = graph.nodes[node]['schemaClass']
        classes[s_class] = classes.get(s_class, 0) + 1

    # count edge types
    edges = {}
    for u, v, d in graph.edges(data=True):
        rel_type = d['type']
        edges[rel_type] = edges.get(rel_type, 0) + 1

    data = {
        **data,
        'edges': {'total': nx.number_of_edges(graph), 'types': edges},
        'nodes': {'total': nx.number_of_nodes(graph), 'classes': classes},
    }

    # count strongly connected components by size
    scc = list(nx.strongly_connected_components(graph))
    data['scc'] = {'total': len(scc)}
    scc_sizes = {}
    for c_size in [*map(len, scc)]:
        scc_sizes[c_size] = scc_sizes.get(c_size, 0) + 1
    data['scc']['sizes'] = scc_sizes

    # count weakly connected components by size
    wcc = list(nx.weakly_connected_components(graph))
    data['wcc'] = {'total': len(wcc)}
    wcc_sizes = {}
    for c_size in [*map(len, wcc)]:
        wcc_sizes[c_size] = wcc_sizes.get(c_size, 0) + 1
    data['wcc']['sizes'] = wcc_sizes

    data['subgraphs'] = _get_subgraph_connectivity(graph)

    out_dir = f'{DATA_DIR}/{s}/analysis'
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    with open(f'{out_dir}/stats.json', 'w+') as f:
        json.dump(data, f)


def _store_centrality_measures(name: str, s: str,
                               results: Dict[str, Union[int, float]]):
    out_dir = f'{DATA_DIR}/{s}/analysis/centrality'
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    with open(f'{out_dir}/{name}.tsv', 'w+') as f:
        for node, value in results.items():
            f.write(f'{node}\t{value}\n')


def _analyze_centrality(graph: ReactomeGraph, s: str):

    analyzer = CentralityAnalyzer(graph)
    tasks = {
        'closeness': analyzer.calculate_closeness,
        'degree': analyzer.calculate_degree,
        'laplacian': analyzer.calculate_laplacian,
        'leverage': analyzer.calculate_leverage,
        'h_index': analyzer.calculate_h_index
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

    for measure in results:
        _store_centrality_measures(measure, s, results[measure])


def _analyze_connectivity(graph: ReactomeGraph, s: str):

    analyzer = ConnectivityAnalyzer(graph)
    tasks = {
        'wcc_pathways_intersection': partial(analyzer.intersection_components_pathways, weakly=True),  # noqa: E501
        'scc_pathways_intersection': partial(analyzer.intersection_components_pathways, weakly=False),  # noqa: E501
        # TODO: add more connectivity measures
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

    out_dir = f'{DATA_DIR}/{s}/analysis/connectivity'
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for measure in results:
        with open(f'{out_dir}/{measure}.json', 'w') as f:
            json.dump(results[measure], f)


def _parse_args() -> ap.ArgumentParser:
    parser = ap.ArgumentParser()
    parser.add_argument('--species')


def main():
    for s in SPECIES:
        print(f'Loading graph data for {s}...', end='\t')
        graph_pickle = f'{DATA_DIR}/{s}/graph.pickle'
        with open(graph_pickle, 'rb') as f:
            graph = pickle.load(f)
        print('✓')

        print('Analyzing graph statistics...', end='\t')
        _analyze_stats(graph, s)
        print('✓')
        print('Analyzing nodes centrality...', end='\t')
        _analyze_centrality(graph, s)
        print('✓')
        print('Analyzing connectivity...', end='\t')
        _analyze_connectivity(graph, s)
        print('✓')

        print(
            f'Analysis complete, data stored in \'{DATA_DIR}/{s}/analysis\'')


if __name__ == '__main__':
    main()
