# Reactome-graph

The package is a python implementation of a bipartite directed multigraph extracted from the Reactome database. Its underlying implementation uses `networkx`.

The graph represents **reactions** and **physical entities** as nodes, edges are classified into 5 categories:

- input
- output
- catalyst
- positiveRegulator
- negativeRegulator

The package provides a wrapper for the `networkx.MultiDiGraph` class: the `ReactomeGraph`. Each graph instance is associated with a certain species and can either be:

- loaded from pre-built binaries shipped alongside the package
- built directly from a Neo4j instance running on the user’s machine

> NOTE: the user may prefer the latter option in order to control which specific version of Reactome’s database is used to generate the graphs. The latest supported version for this package will be periodically updated.

When building from a Neo4j instance, the package extracts data from the [Reactome graph database](https://reactome.org/download-data) and produces a _bipartite directed multi-graph_.

## Installation

```bash
git clone https://github.com/marinoandrea/reactome-graph.git
cd reactome-graph
pip install .
```

## Usage

In order to use the pre-built graphs, just call the `load` method specifying the species:

```python
from reactome_graph import ReactomeGraph, Species

hsa_graph = ReactomeGraph.load('Homo sapiens')
# or
hsa_graph = ReactomeGraph.load(Species.HSA)
```

In order to build a graph directly from Reactome's Neo4j database, an active Neo4j instance hosting the Reactome database is required.
The connection URI can be specified in the `options` (it defaults to `bolt://localhost:7687`):

```python
from reactome_graph import ReactomeGraph, Species

hsa_graph = ReactomeGraph.build('Homo sapiens', options={'neo4j_uri': 'bolt://<YOUR_HOST>:<YOUR_PORT>'})
# or
hsa_graph = ReactomeGraph.build(Species.HSA, options={'neo4j_uri': 'bolt://<YOUR_HOST>:<YOUR_PORT>'})

```

## API Reference

### ReactomeGraph

Represents a graph for a certain species.

#### Properties:

| PROPERTY             | TYPE                    | DESCRIPTION                                                |
| -------------------- | ----------------------- | ---------------------------------------------------------- |
| `event_nodes`        | `Set[str]`              | Set containing all the event nodes identifiers.            |
| `entity_nodes`       | `Set[str]`              | Set containing all the entity nodes identifiers.           |
| `compartments`       | `Iterable[Compartment]` | List of all cellular compartments for this graph instance. |
| `pathways`           | `Iterable[Pathway]`     | List of all pathways for this graph instance.              |
| `top_level_pathways` | `Iterable[Pathway]`     | List of all top level pathways for this graph instance.    |

#### Methods:

| METHOD                     | ARGUMENTS                                                       | RETURNS       | DESCRIPTION                                                                                          |
| -------------------------- | --------------------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------- |
| `get_pathway_subgraph`     | pathway: `str` - pathway identifier                             | ReactomeGraph | Generate subgraph using nodes from the given pathway.                                                |
| `get_compartment_subgraph` | compartment: `str` - compartment GO identifier (eg: GO:0005886) | ReactomeGraph | Generate subgraph using nodes from the given compartment.                                            |
| `load`                     | species: `Union[Species, str]` - species name or enumeration    | ReactomeGraph | Factory method, builds a Reactome graph from a pickled python object.                                |
| `build`                    | species: `Union[Species, str]` - species name or enumeration    | ReactomeGraph | Factory method, builds a Reactome graph. Requires a working Neo4j instance containing Reactome data. |

### Species

Enumeration with valid Reactome species ([source](reactome_graph/species.py)).

### Pathway

Dataclass containing basic pathway information.

#### Properties:

| PROPERTY       | TYPE   | DESCRIPTION                                 |
| -------------- | ------ | ------------------------------------------- |
| `id`           | `str`  | Reactome pathway identifier.                |
| `name`         | `str`  | Reactome display name.                      |
| `is_top_level` | `bool` | Whether the pathway is a top level pathway. |
| `in_disease`   | `bool` | Whether the pathway is part of a disease.   |

### Compartment

Dataclass containing basic cellulare compartment information.

#### Properties:

| PROPERTY | TYPE  | DESCRIPTION                                      |
| -------- | ----- | ------------------------------------------------ |
| `id`     | `str` | GO compartment identifier (starting with 'GO:'). |
| `name`   | `str` | Reactome display name.                           |

## Examples

Obtain a subgraph relative to a specific pathway:

```python
from reactome_graph import ReactomeGraph

hsa_graph = ReactomeGraph.load('Homo sapiens')
signal_transduction_subgraph = hsa_graph.get_pathway_subgraph('R-HSA-162582')
```

or to a specific cellular compartment:

```python
from reactome_graph import ReactomeGraph

hsa_graph = ReactomeGraph.load('Homo sapiens')
plasma_membrane_subgraph = hsa_graph.get_compartment_subgraph('GO:0005886')
```

## Authors

- **Andrea Marino** - ([marinoandrea](https://github.com/marinoandrea))

See also the list of [contributors](https://github.com/marinoandrea/reactome-graph/contributors) who participated in this project.
