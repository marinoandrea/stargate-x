import pickle
from pathlib import Path
from reactome_graph import GraphBuilder


DATA_DIR = './data/species'
REL_TYPES = ['input', 'output', 'catalyst',
             'positiveRegulator', 'negativeRegulator']


def main():
    graphs = GraphBuilder(relationships=REL_TYPES).build()
    for species, graph in graphs.items():
        graph_dir = f'{DATA_DIR}/{species}'
        Path(graph_dir).mkdir(parents=True, exist_ok=True)
        graph_file = f'{graph_dir}/graph.pickle'
        with open(graph_file, 'wb') as f:
            pickle.dump(graph, f)


if __name__ == '__main__':
    main()
