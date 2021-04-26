import pkgutil
from multiprocessing.pool import Pool, ThreadPool
from os import cpu_count
from typing import Dict, Mapping, Sequence, Tuple

import networkx as nx
from reactome_graph.constants import (COMPARTMENTS_QUERY, EDGES_QUERY, ENTITY,
                                      EVENT, PATHWAYS_QUERY)
from reactome_graph.data import Compartment, Pathway
from reactome_graph.graph import ReactomeGraph
from reactome_graph.utils.neo4j import Neo4jClient

import neo4j


class ReactomeGraphBuilder:

    def __init__(
        self,
        species: Sequence[str] = None,
        options: Dict = {}
    ):
        self.options = options
        self._load_queries()
        if species is None:
            self._load_species()
        else:
            self.species = species

    def _load_queries(self):
        edges = pkgutil.get_data('reactome_graph', EDGES_QUERY)
        pathways = pkgutil.get_data('reactome_graph', PATHWAYS_QUERY)
        compartments = pkgutil.get_data('reactome_graph', COMPARTMENTS_QUERY)

        # NOTE(andrea): this should never happen, it would mean
        # that packaging has gone wrong.
        if (edges is None or pathways is None or compartments is None):
            raise RuntimeError('Queries have not been imported correctly.')

        self._query_edges = edges.decode('utf-8')
        self._query_pathways = pathways.decode('utf-8')
        self._query_compartments = compartments.decode('utf-8')

    def _load_species(self):
        client = Neo4jClient(
            uri=self.options.get('neo4j_uri', 'bolt://localhost:7687'))
        result = client.make_query(
            'match (s:Species) return s.displayName as name;')
        self.species = [str(s['name']) for s in result]
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
                    'type': record['relationship']['type']
                }

            except (ValueError, TypeError, KeyError):
                continue

            # change edge direction
            if relationship['type'] in [
                'input',
                'catalyst',
                'positiveRegulator',
                'negativeRegulator'
            ]:
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

            pathways[pathway['id']] = Pathway(**pathway)

            if reaction not in nodes:
                continue

            if 'pathways' not in nodes[reaction]:
                nodes[reaction]['pathways'] = set()

            nodes[reaction]['pathways'].add(pathway['id'])

        for record in records_compartments:

            node = record['node']
            compartment = {
                'id': f"GO:{record['compartment']['accession']}",
                'name': record['compartment']['name'],
            }

            compartments[compartment['name']] = Compartment(**compartment)

            if node not in nodes:
                continue

            if 'compartments' not in nodes[node]:
                nodes[node]['compartments'] = set()

            nodes[node]['compartments'].add(compartment['id'])

        graph = ReactomeGraph()
        graph.pathways = list(pathways.values())
        graph.compartments = list(compartments.values())

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

        tasks = [query_edges, query_pathways, query_compartments]
        pool = ThreadPool(3)
        results = pool.map(client.make_query, tasks)
        pool.close()
        pool.join()

        result_edges = results[0]
        result_pathways = results[1]
        result_compartments = results[2]

        graph = self._parse_records(
            result_edges, result_pathways, result_compartments)
        nx.freeze(graph)

        client.close()
        return s, graph

    def _extract(self):
        if len(self.species) == 1:
            return [self._extract_species(self.species[0])]
        pool = Pool(min(len(self.species), cpu_count()))
        out = pool.map(self._extract_species, self.species)
        pool.close()
        pool.join()
        return out

    def build(self) -> Mapping[str, ReactomeGraph]:
        return {species: graph for species, graph in self._extract()}
