import pickle
import json
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
from reactome_graph import ReactomeGraph
from pathlib import Path
from collections import OrderedDict
from typing import Sequence

DATA_DIR = './data/species'
SPECIES = ['HSA']

# styles
PRIMARY_CLR = '#0f7770'


def _create_centrality_histogram(ax, s: str, measure: str, title: str = ''):
    file = f'{DATA_DIR}/{s}/analysis/centrality/{measure}.tsv'
    df = pd.read_csv(file, sep='\t', names=['node', 'value'])

    ax.set_yscale('log')
    ax.hist(df['value'], 50,  histtype='bar',
            edgecolor='white', color='royalblue')
    ax.set_title(title, fontsize='small')


def _plot_centrality_measure(s: str):
    fig, axs = plt.subplots(3, 2, dpi=300)
    fig.text(0.75, 0.20, '(y) # of nodes', ha='center', va='center')
    fig.text(0.75, 0.15, '(x) Centrality value', ha='center', va='center')

    _create_centrality_histogram(
        axs[0, 0], s, 'degree', title='Degree (DC)')
    _create_centrality_histogram(
        axs[0, 1], s, 'h_index', title='H-Index (HC)')
    _create_centrality_histogram(
        axs[1, 0], s, 'laplacian', title='Laplacian (LAPC)')
    _create_centrality_histogram(
        axs[1, 1], s, 'closeness', title='Shortest-path Closeness (CC)')
    _create_centrality_histogram(
        axs[2, 0], s, 'leverage', title='Leverage (LC)')
    fig.delaxes(axs[2, 1])

    plt.tight_layout()

    out_dir = f'{DATA_DIR}/{s}/plots/centrality'
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_file = f'{out_dir}/matrix.png'
    fig.savefig(out_file)
    plt.close(fig=fig)


def _create_centrality_stats_histogram():
    pass


def _plot_degree_centrality_stats(graph: ReactomeGraph, s: str):
    file = f'{DATA_DIR}/{s}/analysis/centrality/degree.tsv'
    data = pd.read_csv(file, sep='\t', names=['node', 'value'])

    values = {}
    for _, row in data.iterrows():
        node, value = row['node'], row['value']
        schema_class = graph.nodes[node]['schemaClass']
        if schema_class not in values:
            values[schema_class] = []
        values[schema_class].append(value)

    means = [(0, '') for _ in values]
    for i, schema_class in enumerate(values):
        mean = sum(values[schema_class]) / len(values[schema_class])
        means[i] = (mean, schema_class)
    means.sort()

    fig = plt.figure(dpi=300)
    for i in range(len(means)):
        is_event = means[i][1] in ['Polymerisation', 'FailedReaction',
                                   'BlackBoxEvent', 'Reaction',
                                   'Depolymerisation']
        plt.bar(means[i][1], means[i][0],
                color='royalblue' if is_event else 'maroon',
                label='events' if is_event else 'entities')

    plt.legend(loc='upper left')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    out_dir = f'{DATA_DIR}/{s}/plots/centrality'
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_file = f'{out_dir}/degree_means.png'
    fig.savefig(out_file)
    plt.close(fig=fig)


def _create_pie_chart(x: Sequence,
                      labels: Sequence[str],
                      colors: Sequence[str] = None,
                      title: str = '') -> matplotlib.figure.Figure:

    fig = plt.figure(dpi=300, figsize=(7, 7))
    plt.title(title)
    _, texts, autotexts = plt.pie(x, labels=labels,
                                  autopct=lambda v: str(v)[:4] + '%',
                                  colors=colors)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize('large')
    return fig


def _plot_stats_charts(graph: ReactomeGraph, s: str):
    # plot bipartition
    x_nodes = [len(graph.event_nodes), len(graph.entity_nodes)]
    labels_nodes = ['Events', 'Entities']
    fig_nodes = _create_pie_chart(
        x_nodes, labels_nodes, colors=['royalblue', 'maroon'])

    # plot edges
    with open(f'{DATA_DIR}/{s}/analysis/stats.json', 'r') as f:
        data = json.load(f)
    x_edges = [*data['edges']['types'].values()]
    labels_edges = [*data['edges']['types'].keys()]
    fig_edges = _create_pie_chart(x_edges, labels_edges)

    # store plot
    out_dir = f'{DATA_DIR}/{s}/plots/stats'
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_edges = f'{out_dir}/edges.png'
    out_nodes = f'{out_dir}/nodes.png'
    fig_edges.savefig(out_edges, bbox_inches="tight")
    fig_nodes.savefig(out_nodes, bbox_inches="tight")
    plt.close(fig=fig_edges)
    plt.close(fig=fig_nodes)


def _create_intersection_matrix(matrix: np.ndarray, ticks: list,
                                title: str = '') -> matplotlib.figure.Figure:
    fig = plt.figure(dpi=300)
    plt.title(title)
    plt.imshow(matrix, interpolation='nearest', cmap='cividis')
    plt.colorbar()
    plt.xticks(range(len(ticks)), ticks, rotation=90, fontsize='x-small')
    plt.yticks(range(len(ticks)), ticks, fontsize='x-small')
    return fig


def _plot_intersection(graph: ReactomeGraph, s: str, property: str):
    properties = getattr(graph, property, {})

    if property == 'top_level_pathways':
        names = [p['name'] for p in properties.values()]
    else:
        names = [p for p in properties]
    names.sort()
    out = OrderedDict()
    for name in names:
        if property == 'top_level_pathways':
            p = next(
                filter(lambda x: properties[x]['name'] == name, properties))
        else:
            p = name
        out[p] = properties[p]
    properties = out

    shape = (len(properties), len(properties))
    events = np.zeros(shape, dtype=np.float)
    entities = np.zeros(shape, dtype=np.float)
    p_map = {p: i for i, p in enumerate(properties)}

    for p1 in properties:
        for p2 in properties:
            p1_idx, p2_idx = p_map[p1], p_map[p2]
            p1_events, p2_events = (
                properties[p1]['events'], properties[p2]['events'])
            p1_entities, p2_entities = (
                properties[p1]['entities'], properties[p2]['entities'])
            try:
                events[p1_idx][p2_idx] = (len(p1_events & p2_events) /
                                          max(len(p1_events), len(p2_events)))
            except ZeroDivisionError:
                events[p1_idx][p2_idx] = 0
            try:
                entities[p1_idx][p2_idx] = (len(p1_entities & p2_entities) /
                                            max(len(p1_entities),
                                                len(p2_entities)))
            except ZeroDivisionError:
                entities[p1_idx][p2_idx] = 0

            if 1 > events[p1_idx][p2_idx] > 0.1:
                print(property, events[p1_idx][p2_idx], p1, p2)
            if 1 > entities[p1_idx][p2_idx] > 0.1:
                print(property, entities[p1_idx][p2_idx], p1, p2)

    # plot events
    fig_events = _create_intersection_matrix(events, names)
    # plot entities
    fig_entities = _create_intersection_matrix(entities, names)

    # store plot
    out_dir = f'{DATA_DIR}/{s}/plots/{property}'
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_events = f'{out_dir}/events_intersection.png'
    out_entities = f'{out_dir}/entities_intersection.png'
    fig_events.savefig(out_events, bbox_inches="tight")
    fig_entities.savefig(out_entities, bbox_inches="tight")
    plt.close(fig=fig_events)
    plt.close(fig=fig_entities)


def _plot_pathways_intersection(graph: ReactomeGraph, s: str):
    nlvl = max(graph.pathways[p]['level'] for p in graph.pathways) + 1
    for lvl in range(nlvl):
        pathways = {p for p in graph.pathways if
                    (graph.pathways[p]['level'] == lvl)}
        p_map = {p: i for i, p in enumerate(pathways)}

        shape = (len(pathways), len(pathways))
        a = np.zeros(shape, dtype=np.float)

        for p1 in pathways:
            for p2 in pathways:
                p1_idx, p2_idx = p_map[p1], p_map[p2]
                p1_nodes, p2_nodes = (graph.pathways[p1]['nodes'],
                                      graph.pathways[p2]['nodes'])
                a[p1_idx][p2_idx] = (len(p1_nodes & p2_nodes) /
                                     max(len(p1_nodes), len(p2_nodes)))

        # plot
        fig = plt.figure(dpi=600)
        ax = fig.add_subplot(111)
        plt.axis('off')
        ax.matshow(a)

        # store plot
        out_dir = f'{DATA_DIR}/{s}/plots/pathways'
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        out_file = f'{out_dir}/intersection_{lvl}.png'
        fig.savefig(out_file)
        plt.close(fig=fig)


def _create_components_biostructure_scatter():
    pass


def _plot_component_biostructure(graph: ReactomeGraph, s: str,
                                 s_type: str = 'top_level_pathways'):

    structures = getattr(graph, s_type)
    temp = {}
    for struct in structures:
        nodes = (structures[struct]['events'] | structures[struct]['entities'])
        temp[struct] = nodes
    structures = temp

    scc_components = nx.strongly_connected_components(graph)
    wcc_components = nx.weakly_connected_components(graph)

    fig = plt.figure(dpi=300)
    plt.tight_layout()
    plt.xscale('log')
    plt.xlabel('# of nodes in component')

    if s_type == 'top_level_pathways':
        plt.title('(a)')
        plt.ylabel('# of pathways intersection')
    else:
        plt.title('(b)')
        plt.ylabel('# of compartments intersection')

    first_scc = True
    for i, c in enumerate(scc_components):
        if len(c) <= 1:
            continue
        n_structures = 0
        for struct in structures:
            if len(c & structures[struct]) > 0:
                n_structures += 1
        if first_scc:
            plt.scatter(len(c), n_structures, color='maroon',
                        alpha=0.4, label='Strongly Connected')
            first_scc = False
        else:
            plt.scatter(len(c), n_structures, color='maroon', alpha=0.4)

    first_wcc = True
    for i, c in enumerate(wcc_components):
        if len(c) <= 1:
            continue
        n_structures = 0
        for struct in structures:
            if len(c & structures[struct]) > 0:
                n_structures += 1
        if first_wcc:
            plt.scatter(len(c), n_structures, color='royalblue',
                        alpha=0.4, label='Weakly Connected')
            first_wcc = False
        else:
            plt.scatter(len(c), n_structures, color='royalblue', alpha=0.4)

    plt.legend()

    out_dir = f'{DATA_DIR}/{s}/plots/connectivity'
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_file = f'{out_dir}/{s_type}.png'
    fig.savefig(out_file)
    plt.close(fig=fig)


def _plot_subgraphs_components(graph: ReactomeGraph, s: str,
                               s_type: str = 'pathways'):
    subgraphs = (graph.get_pathways_subgraphs() if s_type == 'pathways'
                 else graph.get_compartments_subgraphs())

    fig = plt.figure(dpi=300)
    plt.tight_layout()
    plt.yscale('log')
    plt.xscale('log')
    plt.ylabel('# of components')
    plt.xlabel('# of nodes')
    plt.title('(b)' if s_type == 'pathways' else '(a)')

    legend = True
    for s_name, s_graph in subgraphs.items():
        scc_components = nx.number_strongly_connected_components(s_graph)
        wcc_components = nx.number_weakly_connected_components(s_graph)
        n_nodes = len(s_graph.nodes())
        if legend:
            plt.scatter(n_nodes, scc_components, alpha=0.6, color='maroon',
                        label='Strongly Connected')
            plt.scatter(n_nodes, wcc_components, alpha=0.6, color='royalblue',
                        label='Weakly Connected')
            legend = False
        else:
            plt.scatter(n_nodes, scc_components, alpha=0.6, color='maroon')
            plt.scatter(n_nodes, wcc_components, alpha=0.6, color='royalblue')

    plt.legend()

    out_dir = f'{DATA_DIR}/{s}/plots/connectivity'
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    out_file = f'{out_dir}/subgraphs_{s_type}.png'
    fig.savefig(out_file)
    plt.close(fig=fig)


def main():
    for s in SPECIES:
        print(f'Loading graph data for {s}...', end='\t')
        graph_pickle = f'{DATA_DIR}/{s}/graph.pickle'
        with open(graph_pickle, 'rb') as f:
            graph = pickle.load(f)
        print('✓')

        print(graph.nodes(data=True))

        print('Plotting statistical data...', end='\t')
        _plot_intersection(graph, s, 'top_level_compartments')
        _plot_intersection(graph, s, 'top_level_pathways')
        _plot_stats_charts(graph, s)
        print('✓')

        print('Plotting centrality data...', end='\t')
        _plot_centrality_measure(s)
        _plot_degree_centrality_stats(graph, s)
        print('✓')

        print('Plotting connectivity data...', end='\t')
        _plot_component_biostructure(graph, s, 'top_level_pathways')
        _plot_component_biostructure(graph, s, 'top_level_compartments')
        _plot_subgraphs_components(graph, s, 'pathways')
        _plot_subgraphs_components(graph, s, 'compartments')
        print('✓')

        print(f'Done, plots were saved at \'{DATA_DIR}/{s}/plots\'')


if __name__ == '__main__':
    main()
