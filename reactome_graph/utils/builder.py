import neo4j
import networkx as nx
import multiprocessing.dummy as mp
from multiprocessing import cpu_count
from typing import Sequence, Dict, Tuple
from reactome_graph import ReactomeGraph
from reactome_graph.utils.neo4j import Neo4jClient
from reactome_graph.constants import (
    ENTITY,
    EVENT,
    COMPARTMENTS_QUERY,
    EDGES_QUERY,
    PATHWAYS_QUERY
)


class ReactomeGraphBuilder:

    def __init__(
        self,
        species: Sequence[str] = None,
        relationships: Sequence[str] = None,
        options: Dict = {}
    ):
        self._load_queries()
        self.relationships = relationships
        self.options = options
        if species is None:
            self._load_species()
        else:
            self.species = species

    def _load_queries(self):
        with open(EDGES_QUERY, 'r') as f1,\
             open(PATHWAYS_QUERY, 'r') as f2,\
             open(COMPARTMENTS_QUERY, 'r') as f3:
            self._query_edges = f1.read()
            self._query_pathways = f2.read()
            self._query_compartments = f3.read()

    def _load_species(self):
        client = Neo4jClient(
            uri=self.options.get('neo4j_uri', 'bolt://localhost:7687'))
        result = client.make_query(
            'match (s:Species) return s.abbreviation as code;')
        self.species = [str(s['code']) for s in result]
        client.close()

    def _parse_edges_records(self, records: neo4j.Result) -> (
        Tuple[Dict[str, dict], Sequence[Tuple]]
    ):

        nodes, edges = {}, []

        for record in records:

            try:
                source = dict(record['source']['data'])
                target = dict(record['target']['data'])
                relationship = {
                    **dict(record['relationship']['data']),
                    'type': record['type']
                }

            except (ValueError, TypeError, KeyError):
                continue

            if (self.relationships is not None
                    and relationship['type'] not in self.relationships):
                continue

            # change edge direction
            if relationship['type'] in ['input',
                                        'catalyst',
                                        'positiveRegulator',
                                        'negativeRegulator',
                                        'catalystActiveUnit',
                                        'regulatorActiveUnit',
                                        'requiredInputComponent']:
                t = {**source}
                source = {**target}
                target = t

            # bipartite networkx convention
            source['bipartite'] = (EVENT if 'Event'
                                   in record['source']['labels'] else ENTITY)
            target['bipartite'] = (EVENT if 'Event'
                                   in record['target']['labels'] else ENTITY)

            nodes[source['stId']] = source
            nodes[target['stId']] = target
            edges.append((source['stId'], target['stId'], relationship))

        return nodes, edges

    def _parse_records(self,
                       records_edges: neo4j.Result,
                       records_pathways: neo4j.Result,
                       records_compartments: neo4j.Result):

        nodes, edges = self._parse_edges_records(records_edges)
        pathways, compartments = {}, {}

        for record in records_pathways:

            reaction = record['reaction']
            pathway = {
                'id': record['pathway']['data']['stId'],
                'name': record['pathway']['data']['displayName'],
                'is_top_level':  record['pathway']['isTopLevel'],
                'in_disease': record['pathway']['data']['isInDisease'],
            }

            pathways[pathway['id']] = ReactomeGraph.Pathway(**pathway)

            if reaction not in nodes:
                continue

            if 'pathways' not in nodes[reaction]:
                nodes[reaction]['pathways'] = set()

            nodes[reaction]['pathways'].add(pathway['id'])

        for record in records_compartments:

            node = record['node']
            compartment = {
                'name': record['compartment']['data']['name'],
                'is_top_level':  record['compartment']['isTopLevel'],
            }

            compartments[compartment['name']] = (
                ReactomeGraph.Compartment(**compartment))

            if node not in nodes:
                continue

            if 'compartments' not in nodes[node]:
                nodes[node]['compartments'] = set()

            nodes[node]['compartments'].add(compartment['name'])

        graph = ReactomeGraph(
            list(pathways.values()),
            list(compartments.values())
        )

        for edge in edges:
            source, target, rel_data = edge
            graph.add_node(source, **nodes[source])
            graph.add_node(target, **nodes[target])
            graph.add_edge(source, target, **rel_data)

        return graph

    def _extract_species(self, s: str):
        client = Neo4jClient(
            uri=self.options.get('neo4j_uri', 'bolt://localhost:7687'))

        query_edges = self._query_edges.replace('$species', s)
        query_pathways = self._query_pathways.replace('$species', s)
        query_compartments = self._query_compartments.replace('$species', s)

        result_edges = client.make_query(query_edges)
        result_pathways = client.make_query(query_pathways)
        result_compartments = client.make_query(query_compartments)

        graph = self._parse_records(
            result_edges, result_pathways, result_compartments)
        nx.freeze(graph)

        client.close()
        return s, graph

    def _extract(self):
        pool = mp.Pool(cpu_count())
        out = pool.map(self._extract_species, self.species)
        pool.close()
        pool.join()
        return out

    def build(self):
        return {species: graph for species, graph in self._extract()}
