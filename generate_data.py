import json
import neo4j
import multiprocessing as mp
from typing import Sequence, Tuple
from functools import partial
from pathlib import Path
from os import cpu_count
from reactome_graph.utils.neo4j import Neo4jClient

QUERY_EDGES = './queries/edges.cypher'
QUERY_PATHWAYS = './queries/pathways.cypher'


def _query_species_data(query: str, species_name: str, species_code: str,
                        client: Neo4jClient = None) -> neo4j.Result:
    if client is None:
        client = Neo4jClient()
    query = query.replace('$species_name', species_name)
    query = query.replace('$species_code', species_code)
    out = client.make_query(query)
    return out


def _parse_nodes_and_edges(result: neo4j.Result) -> Tuple[dict, Sequence[str]]:
    nodes = {}
    edges = []

    for edge in result:
        try:
            source = dict(edge['source'])
            target = dict(edge['target'])
            source['labels'] = list(edge['sourceLabels'])
            target['labels'] = list(edge['targetLabels'])
            data = dict(edge['relData']) if edge['relData'] is not None else {}
        except (ValueError, TypeError):
            continue

        order = data.get('order', None)
        stoichiometry = data.get('stoichiometry', None)

        try:
            rel_type = edge['relType']
            nodes[source['stId']] = source
            nodes[target['stId']] = target
        except KeyError:
            continue

        edges.append(f"{source['stId']}\t" + f"{target['stId']}\t" +
                     f"{rel_type}\t" + f"{order}\t" + f"{stoichiometry}\n")

    return nodes, edges


def generate_data_species(query_edges: str, query_pathways: str,
                          species: dict):
    species_name, species_code = species['name'], species['code']

    out_dir = f"./data/species/{species['code']}"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    client = Neo4jClient()

    result_edges = _query_species_data(
        query_edges, species_name, species_code, client=client)
    result_pathways = _query_species_data(
        query_pathways, species_name, species_code, client=client)

    nodes, edges = _parse_nodes_and_edges(result_edges)
    for reaction in result_pathways:
        rid = reaction['id']
        if rid in nodes:
            if 'pathways' not in nodes[rid]:
                nodes[rid]['pathways'] = []
            nodes[rid]['pathways'].append(dict(reaction['pathway']))

    client.close()

    with open(f"{out_dir}/edges.tsv", 'w+') as f:
        f.write('source\ttarget\ttype\torder\tstoichiometry\n')
        f.writelines(edges)

    with open(f"{out_dir}/nodes.json", 'w+') as f:
        json.dump(nodes, f, indent=True)

    print(species['code'], species['name'], 'generated')


def generate_data(query_edges: str, query_pathways: str,
                  species: Sequence[dict] = None):
    """
    Generates  data for all species based on a cypher query.

    Parameters
    ----------

    query_edges: str
        Cypher query returning a list of edge-records,
        the query must use '$species_name' and '$species_code' placeholders.
        The result set must contain for each row:

        - source node as source
        - source labels as sourceLabels
        - target node as target
        - target labels as targetLabels
        - relationship type as relType
        - relationship data (order, stoichiometry etc.) as relData

    query_pathway: str
        Cypher query returning a list of reaction-pathway
        records , the query must use '$species_name' and '$species_code'
        placeholders. The result set must contain for each row:

        - reaction id as reaction
        - pathway node as pathway

    species: list
        List of species to generate. Each entry must be implement the
        dict protocol and contain the keys 'code' and 'name'.

        - code is the Reactome abbreviation for the given species
        - name is the Reactome display name for the given species

        If species is not specified the script will generate data for
        every species in the Reactome database.
    """
    if species is None:
        client = Neo4jClient()
        result = client.make_query(
            """
            match (s:Species)
            return s.abbreviation as code, s.displayName as name;
            """)
        species = [dict(s) for s in result]
        client.close()

    # generate data for all species
    pool = mp.Pool(cpu_count())
    pool.map(
        partial(generate_data_species, query_edges, query_pathways), species)
    pool.close()
    pool.join()


def main():
    with open(QUERY_EDGES, 'r') as f:
        query_edges = f.read()
    with open(QUERY_PATHWAYS, 'r') as f:
        query_pathways = f.read()
    generate_data(query_edges, query_pathways)


if __name__ == '__main__':
    main()
