import pickle
from pathlib import Path
from reactome_graph import GraphAnalyzer

DATA_DIR = './data/species'
SPECIES = 'HSA'


def main():

    # load graph
    graph_pickle = f'{DATA_DIR}/{SPECIES}/graph.pickle'
    with open(graph_pickle, 'rb') as f:
        graph = pickle.load(f)

    # analysis
    analyzer = GraphAnalyzer(graph)
    centrality = analyzer.analyze_centrality()
    # components = analyzer.analyze_components()

    # store centrality measures
    out_dir = f'{DATA_DIR}/{SPECIES}/analysis/centrality'
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    for measure in centrality:
        with open(f'{out_dir}/{measure}.tsv', 'w+') as f:
            for node, value in centrality[measure].items():
                f.write(f'{node}\t{value}\n')

    """
    # count node classes
    classes = {}
    for node in graph.nodes:
        s_class = graph.nodes[node]['schemaClass']
        classes[s_class] = classes.get(s_class, 0) + 1

    # count edge types
    edges = {}
    for edge in graph.edges:
        rel_type = graph.edges[edge]['relType']
        edges[rel_type] = edges.get(rel_type, 0) + 1

    data = {
        'edges': {'total': nx.number_of_edges(graph), 'types': edges},
        'nodes': {'total': nx.number_of_nodes(graph), 'classes': classes},
        'planar': nx.check_planarity(graph)[0],
    }

    # count strongly connected components by size
    scc_sizes = {}
    for c_size in [*map(len, nx.strongly_connected_components(graph))]:
        scc_sizes[c_size] = scc_sizes.get(c_size, 0) + 1
    data['SCC'] = scc_sizes

    # count weakly connected components by size
    wcc_sizes = {}
    for c_size in [*map(len, nx.weakly_connected_components(graph))]:
        wcc_sizes[c_size] = wcc_sizes.get(c_size, 0) + 1
    data['WCC'] = wcc_sizes
    """


if __name__ == '__main__':
    main()
