import pickle
import pkgutil
import io
from reactome_graph.graph import ReactomeGraph
from reactome_graph.utils.builder import ReactomeGraphBuilder
from reactome_graph.utils.subgraphs import (
    build_compartment_subgraph,
    build_compartments_subgraphs,
    build_pathway_subgraph,
    build_pathways_subgraphs
)
from typing import Iterable, Dict, Union
from reactome_graph.species import Species
from reactome_graph.constants import DATA_FOLDER


def load(species: Union[Species, str]) -> ReactomeGraph:
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
    s_name = species if type(species) is str else species.value
    data = pkgutil.get_data(__name__, f'{DATA_FOLDER}/{s_name}.pickle')
    return pickle.load(io.BytesIO(data))


def build(species: Union[Species, str], options={}) -> ReactomeGraph:
    """
    Factory method, builds a Reactome graph.
    Requires a working Neo4j instance containing Reactome data.

    Parameters
    ----------
    species: `Union[reactome_graph.Species, str]`

    options: dict
    configuration options:
    `neo4j_uri` specifies to the driver where your Neo4j instance
    is running

    Returns
    -------
    ReactomeGraph
    The returned graph is a freezed instance of `networkx.MultiDiGraph` so
    it cannot be changed without unfreezing first.
    """
    s_name = species if type(species) is str else species.value
    builder = ReactomeGraphBuilder(species=[s_name], options=options)
    return builder.build()[species]


def build_all(species: Iterable[str], options={}) -> (
    Dict[str, ReactomeGraph]
):
    """
    Factory method, builds Reactome graphs for every species
    in the arguments concurrently. Requires a working Neo4j instance
    containing Reactome data.

    Parameters
    ----------
    species: Iterable[str]
    Identifiers (3 letters) for all Reactome taxons of interest.

    options: dict
    configuration options:
    `neo4j_uri` specifies to the driver where your Neo4j instance
    is running

    Returns
    -------
    Dict
    Dictionary containing the resulting graphs.
    Keys are species identifiers and values are `ReactomeGraph` instances.
    The returned graphs are freezed instances of `networkx.MultiDiGraph` so
    they cannot be changed without unfreezing first.
    """
    out = []
    for s in species:
        s_name = species if type(species) is str else species.value
        out.append(s_name)
    builder = ReactomeGraphBuilder(species=out, options=options)
    return builder.build()


def get_pathway_subgraph(
    G: ReactomeGraph,
    pathway: str
) -> ReactomeGraph:
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
        next(p.id for p in G.pathways if p.id == pathway)
    except StopIteration:
        raise ValueError(f'Pathway \'{pathway}\' not present')
    return build_pathway_subgraph(G, pathway)


def get_compartment_subgraph(
    G: ReactomeGraph,
    compartment: str
) -> ReactomeGraph:
    """
    Generate subgraph using nodes from the given compartment.

    Parameters
    ----------
    G: `ReactomeGraph`

    compartment: `str`
    A Reactome name identifier for a compartment.

    Returns
    -------
    `ReactomeGraph`
    """
    try:
        next(c.name for c in G.compartments if c.name == compartment)
    except StopIteration:
        raise ValueError(f'Compartment \'{compartment}\' not present')
    return build_compartment_subgraph(G, compartment)


def get_all_compartment_subgraphs(
    G: ReactomeGraph,
    compartments: Iterable[str]
) -> Dict[str, ReactomeGraph]:
    """
    Generate subgraphs using nodes for all compartments in the graph.

    Parameters
    ----------
    G: `ReactomeGraph`

    compartments: `Iterable[str]`

    Returns
    -------
    `Dict[str, ReactomeGraph]`
    Dictionary containing subgraphs as values, keys are
    compartments' names.
    """
    for c in compartments:
        try:
            next(dc.name for dc in G.compartments if dc.name == c)
        except StopIteration:
            raise ValueError(f'Compartment \'{c}\' not present')
    return build_compartments_subgraphs(G, compartments)


def get_all_pathway_subgraphs(
    G: ReactomeGraph,
    pathways: Iterable[str]
) -> Dict[str, ReactomeGraph]:
    """
    Generate subgraphs using nodes for all pathways specified.

    Parameters
    ----------
    G: `ReactomeGraph`

    pathways: `Iterable[str]`

    Returns
    -------
    `Dict[str, ReactomeGraph]`
    Dictionary containing subgraphs as values, keys are pathways' stIds.
    """
    for p in pathways:
        try:
            next(dc for dc in G.pathways if dc.id == p)
        except StopIteration:
            raise ValueError(f'Pathway \'{p}\' not present')
    return build_pathways_subgraphs(G, pathways)
