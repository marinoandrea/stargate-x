from reactome_graph.utils.builder import ReactomeGraphBuilder
from reactome_graph import Species
import pickle


def main():
    def chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    for chunk in chunks([
        getattr(Species, name).value
        for name in dir(Species)
        if not name.startswith('_')
    ], 20):

        b = ReactomeGraphBuilder(species=chunk)
        graphs = b.build()

        for species in graphs:
            with open(f'./reactome_graph/data/{species}.pickle', 'wb') as f:
                pickle.dump(graphs[species], f)


if __name__ == "__main__":
    main()
