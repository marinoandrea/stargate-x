import io
import pickle
import pkgutil
from functools import lru_cache
from multiprocessing.pool import ThreadPool
from typing import Callable, Iterable, List, Set, Union

import networkx as nx

from stargate_x.constants import (COMPARTMENTS_QUERY, DATA_FOLDER, EDGES_QUERY,
                                  ENTITY, EVENT, PATHWAYS_QUERY, PKG_NAME)
from stargate_x.data import Compartment, Pathway
from stargate_x.neo4j import Neo4jClient
from stargate_x.species import Species


class ReactomeGraph(nx.MultiDiGraph):
    """
    Reactome directed multigraph. Its underlying implementation
    uses `networkx.MultiDiGraph`.
    """
    pathways: List[Pathway]
    compartments: List[Compartment]

    @property
    def event_nodes(self) -> Set[str]:
        """
        Set containing all the event nodes identifiers.
        """
        return {n for n, d in self.nodes(data=True)
                if d['bipartite'] == EVENT}

    @property
    def entity_nodes(self) -> Set[str]:
        """
        Set containing all the entity nodes identifiers.
        """
        return {n for n, d in self.nodes(data=True)
                if d['bipartite'] == ENTITY}

    @property
    def top_level_pathways(self) -> Iterable[Pathway]:
        return list(filter(lambda x: x.is_top_level, self.pathways))

    def get_pathway_subgraph(self, pathway: str) -> 'ReactomeGraph':
        """
        Generate subgraph using nodes from the given pathway.

        Parameters
        ----------
        G: `ReactomeGraph`

        pathway: `str`
        A Reactome stId identifier for a pathway.

        Returns
        -------
        `ReactomeGraph`
        """
        try:
            pathway_data = next(p for p in self.pathways if p.id == pathway)
            return self._build_subgraph_from_condition(
                lambda x: pathway in self.nodes[x]['pathways'],
                pathways=[pathway_data],
                compartments=self.compartments
            )
        except StopIteration:
            raise ValueError(f'Pathway \'{pathway}\' is not present')

    def get_compartment_subgraph(self, compartment: str) -> 'ReactomeGraph':
        """
        Generate subgraph using nodes from the given compartment.

        Parameters
        ----------
        G: `ReactomeGraph`

        compartment: `str`
        A GO identifier for a compartment.

        Returns
        -------
        `ReactomeGraph`
        """
        try:
            compartment_data = next(
                c for c in self.compartments if c.id == compartment)
            return self._build_subgraph_from_condition(
                lambda x: compartment in self.nodes[x]['compartments'],
                pathways=self.pathways,
                compartments=[compartment_data]
            )
        except StopIteration:
            raise ValueError(f'Compartment \'{compartment}\' is not present')

    @staticmethod
    def load(species: Union[Species, str]) -> 'ReactomeGraph':
        """
        Factory method, builds a Reactome graph from
        pickled python object.

        Parameters
        ----------
        species: `Union[reactome_graph.Species, str]`

        Returns
        -------
        ReactomeGraph
        The returned graph is a freezed instance of `networkx.MultiDiGraph` so
        it cannot be changed without unfreezing first.
        """
        s_name = species.value if isinstance(species, Species) else species
        data = pkgutil.get_data(__name__, f'{DATA_FOLDER}/{s_name}.pickle')
        if data is None:
            raise RuntimeError(
                f'Graph for the species {s_name} is not available. ' +
                'You may consider building it using `reactome_graph.build`'
            )
        out: ReactomeGraph = pickle.load(io.BytesIO(data))
        return out

    @staticmethod
    def build(
        species: Union[Species, str], options: dict = {}
    ) -> 'ReactomeGraph':
        """
        Factory method, builds a Reactome graph.
        Requires a working Neo4j instance containing Reactome data.

        Parameters
        ----------
        species: `Union[reactome_graph.Species, str]`

        options: dict\n
        configuration options:\n
        `neo4j_uri` specifies to the driver where your Neo4j instance
        is running

        Returns
        -------
        ReactomeGraph
        The returned graph is a freezed instance of `networkx.MultiDiGraph` so
        it cannot be changed without unfreezing first.
        """
        s_name = species.value if isinstance(species, Species) else species

        @lru_cache
        def load_query(path: str, species: str) -> str:
            data = pkgutil.get_data(PKG_NAME, path)
            if data is None:
                # NOTE(andrea): this should never happen, it would mean
                # that packaging has gone wrong.
                raise ImportError(
                    'Cypher query has not been imported correctly.')
            return data\
                .decode('utf-8')\
                .replace('$species', species)

        q_edges = load_query(EDGES_QUERY, s_name)
        q_pathways = load_query(PATHWAYS_QUERY, s_name)
        q_compartments = load_query(COMPARTMENTS_QUERY, s_name)

        db_uri = options.get('neo4j_uri', 'bolt://localhost:7687')
        client = Neo4jClient(uri=db_uri)

        tasks = [q_edges, q_pathways, q_compartments]
        pool = ThreadPool(len(tasks))
        result_edges, result_pathways, result_compartments = (
            pool.map(client.make_query, tasks))
        pool.close()
        pool.join()

        nodes, edges = {}, []
        for record in result_edges:
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
            source['bipartite'] = (
                EVENT if 'Event' in record['source']['labels']
                else ENTITY)

            if relationship['type'] == 'referenceEntity':
                source['referenceEntity'] = target
                nodes[source['stId']] = source
            else:
                target['bipartite'] = (
                    EVENT if 'Event' in record['target']['labels']
                    else ENTITY)

                nodes[source['stId']] = source
                nodes[target['stId']] = target
                edges.append((source['stId'], target['stId'], relationship))

        pathways, compartments = {}, {}
        for record in result_pathways:
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

        for record in result_compartments:
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

        nx.freeze(graph)
        client.close()
        return graph

    def _build_subgraph_from_condition(
        self,
        check_condition: Callable,
        pathways: List[Pathway],
        compartments: List[Compartment],
    ) -> 'ReactomeGraph':
        out = ReactomeGraph()
        out.pathways = pathways
        out.compartments = compartments
        for node, data in self.nodes(data=True):
            try:
                if check_condition(node):
                    out.add_node(node, **data)
            except Exception:
                continue
        for u, v, data in self.edges(data=True):
            if (u in out.nodes and v in out.nodes):
                out.add_edge(u, v, **data)
        return out
